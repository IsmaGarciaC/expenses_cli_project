"""Integración de la CLI con el dominio y almacenamiento aislados del usuario."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from expenses_cli import cli, storage


@pytest.fixture
def data_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # HOME aísla los procesos hijos; Path.home aísla las llamadas a main().
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return cli.get_data_path()


@pytest.fixture
def run_cli(tmp_path: Path, data_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PYTHONPATH", str(Path(cli.__file__).resolve().parents[1]))

    def run(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-c",
                "from expenses_cli.cli import main; main()",
                *arguments,
            ],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
            check=False,
        )

    return run


@pytest.fixture
def saved_data(data_path: Path) -> bytes:
    storage.save_data(
        data_path,
        {
            "next_id": 2,
            "expenses": [
                {
                    "id": 1,
                    "description": "Café",
                    "amount_cents": 150,
                    "date": "2026-11-14",
                }
            ],
        },
    )
    return data_path.read_bytes()


def test_five_commands_preserve_output_and_persist_changes(run_cli, data_path: Path):
    result = run_cli("add", "--amount", "1.50", "--description", "Café")
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == "Gasto 1 Café agregado correctamente\n"
    first = json.loads(data_path.read_text(encoding="utf-8"))["expenses"][0]

    result = run_cli("add", "--amount", "15.25", "--description", "Almuerzo")
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == "Gasto 2 Almuerzo agregado correctamente\n"
    second = json.loads(data_path.read_text(encoding="utf-8"))["expenses"][1]

    result = run_cli("list")
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == (
        "Historial de Gastos\n\n"
        f"#1 | {first['date']} | Café | $1.50\n"
        f"#2 | {second['date']} | Almuerzo | $15.25\n"
    )

    result = run_cli("get", "1")
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == (
        "Detalle del gasto:\n\n"
        "ID: 1\n"
        f"Fecha: {first['date']}\n"
        "Descripción: Café\n"
        "Importe: $1.50\n"
    )

    result = run_cli("total")
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == "El total de los gastos es: $16.75\n"

    result = run_cli("delete", "1")
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == "Gasto #1 eliminado correctamente\n"
    assert json.loads(data_path.read_text(encoding="utf-8")) == {
        "next_id": 3,
        "expenses": [second],
    }

    result = run_cli("total")
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == "El total de los gastos es: $15.25\n"


@pytest.mark.parametrize(
    "command, expected",
    [
        ("list", "No hay gastos registrados\n"),
        ("total", "El total de los gastos es: $0.00\n"),
    ],
)
def test_empty_history_preserves_output(run_cli, data_path: Path, command, expected):
    result = run_cli(command)

    assert result.returncode == 0
    assert result.stdout == expected
    assert result.stderr == ""
    assert not data_path.exists()


@pytest.mark.parametrize(
    "arguments, message",
    [
        (("get", "999"), "Gasto no encontrado"),
        (("delete", "999"), "Gasto no encontrado"),
        (("get", "0"), "ID no valido"),
        (("get", "-1"), "ID no valido"),
        (("delete", "0"), "ID no valido"),
        (("delete", "-1"), "ID no valido"),
        (("get", "abc"), "invalid int value"),
        (("get", "1.5"), "invalid int value"),
        (("delete", "abc"), "invalid int value"),
    ],
)
def test_invalid_or_missing_id_reports_error_without_changes(
    run_cli, data_path: Path, saved_data: bytes, arguments, message,
):
    result = run_cli(*arguments)

    assert result.returncode == 2
    assert result.stdout == ""
    assert "usage:" in result.stderr
    assert "error:" in result.stderr
    assert message in result.stderr
    assert "Traceback" not in result.stderr
    assert data_path.read_bytes() == saved_data


@pytest.mark.parametrize("amount", ("abc", "0", "-1", "1.001", "NaN", "Infinity"))
def test_invalid_amount_reports_error_without_success_or_changes(
    run_cli, data_path: Path, saved_data: bytes, amount: str,
):
    result = run_cli("add", "--amount", amount, "--description", "Almuerzo")

    assert result.returncode == 2
    assert result.stdout == ""
    assert "error: El importe debe ser un número positivo" in result.stderr
    assert "Traceback" not in result.stderr
    assert data_path.read_bytes() == saved_data


@pytest.mark.parametrize(
    "arguments",
    [
        ("add", "--amount", "2.50", "--description", "Almuerzo"),
        ("list",),
        ("get", "1"),
        ("delete", "1"),
        ("total",),
    ],
)
def test_storage_read_error_reports_error_for_every_command(
    run_cli, data_path: Path, arguments,
):
    # Un directorio en lugar del JSON provoca OSError sin depender de permisos.
    data_path.mkdir(parents=True)

    result = run_cli(*arguments)

    assert result.returncode == 2
    assert result.stdout == ""
    assert "error: No se pudo acceder al almacenamiento:" in result.stderr
    assert str(data_path) in result.stderr
    assert "Traceback" not in result.stderr
    assert data_path.is_dir()
    assert list(data_path.iterdir()) == []


@pytest.mark.parametrize("command", ("list", "total"))
def test_corrupt_storage_reports_error_without_overwriting_history(
    run_cli, data_path: Path, command: str,
):
    data_path.parent.mkdir(parents=True)
    original = b'{"next_id": '
    data_path.write_bytes(original)

    result = run_cli(command)

    assert result.returncode == 2
    assert result.stdout == ""
    assert "error: El archivo esta Corrupto" in result.stderr
    assert "Traceback" not in result.stderr
    assert data_path.read_bytes() == original


@pytest.mark.parametrize(
    "arguments",
    [
        ("add", "--amount", "2.50", "--description", "Almuerzo"),
        ("delete", "1"),
    ],
)
def test_storage_write_error_exits_without_success_or_changes(
    data_path: Path, saved_data: bytes, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], arguments,
):
    def failing_replace(source, destination):
        assert destination == data_path
        raise PermissionError("Permiso de escritura denegado")

    monkeypatch.setattr(storage.os, "replace", failing_replace)
    monkeypatch.setattr(sys, "argv", ["expenses", *arguments])

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert (
        "error: No se pudo acceder al almacenamiento: Permiso de escritura denegado"
        in captured.err
    )
    assert "Traceback" not in captured.err
    assert data_path.read_bytes() == saved_data
    assert list(data_path.parent.iterdir()) == [data_path]


def test_unexpected_programming_error_is_not_caught(
    data_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    def broken_operation(path):
        raise RuntimeError("Fallo inesperado de programación")

    monkeypatch.setattr(cli, "list_expenses", broken_operation)
    monkeypatch.setattr(sys, "argv", ["expenses", "list"])

    with pytest.raises(RuntimeError, match="Fallo inesperado de programación"):
        cli.main()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
