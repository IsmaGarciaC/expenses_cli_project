"""Pruebas del modelo, sus validaciones y el registro con archivos aislados."""

import json
from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path

import pytest

from expenses_cli import expenses, storage
from expenses_cli.expenses import (
    add_expense,
    create_expense,
    get_expense,
    list_expenses,
    validate_amount,
    validate_description,
)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("Almuerzo", "Almuerzo"),
        ("  Café con leche  ", "Café con leche"),
        ("\t Transporte\n", "Transporte"),
        ("Dos  espacios", "Dos  espacios"),
        ("0", "0"),
    ],
)
def test_accepts_text_and_trims_outer_whitespace(value: object, expected: str) -> None:
    assert validate_description(value) == expected


@pytest.mark.parametrize(
    "value", ("", "   ", "\t\n", None, True, False, 0, 15, b"Cafe", [], {})
)
def test_rejects_empty_or_non_text_values(value: object) -> None:
    with pytest.raises(ValueError):
        validate_description(value)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("15", 1500),
        ("15.5", 1550),
        ("15.50", 1550),
        ("0.01", 1),
        ("0.29", 29),
        (" 2.50 ", 250),
        ("1e-2", 1),
        ("1E+2", 10000),
        (15, 1500),
        (0.29, 29),
        (Decimal("10.20"), 1020),
    ],
)
def test_converts_valid_amounts_to_integer_cents(value: object, expected: int) -> None:
    result = validate_amount(value)
    assert type(result) is int
    assert result == expected


@pytest.mark.parametrize(
    "value", (0, 0.0, "0.00", "-0", "-0.00", -1, -0.01, Decimal("-2.50"))
)
def test_rejects_zero_and_negative_values(value: object) -> None:
    with pytest.raises(ValueError):
        validate_amount(value)


@pytest.mark.parametrize(
    "value", ("1.001", "0.001", "1.230", 1.234, "1e-3", Decimal("2.000"))
)
def test_rejects_more_than_two_decimal_places_without_rounding(value: object) -> None:
    with pytest.raises(ValueError):
        validate_amount(value)


@pytest.mark.parametrize(
    "value",
    (
        "NaN",
        "sNaN",
        "Infinity",
        "-Infinity",
        float("nan"),
        float("inf"),
        float("-inf"),
        Decimal("NaN"),
        Decimal("sNaN"),
        Decimal("Infinity"),
    ),
)
def test_rejects_non_finite_values(value: object) -> None:
    with pytest.raises(ValueError):
        validate_amount(value)


@pytest.mark.parametrize(
    "value", (True, False, None, "", " ", "abc", "1,50", "1.2.3", b"15", [], {}, 1j)
)
def test_rejects_invalid_values_and_booleans(value: object) -> None:
    with pytest.raises(ValueError):
        validate_amount(value)


def test_preserves_large_amounts_exactly() -> None:
    assert (
        validate_amount("123456789012345678901234567890.12")
        == 12345678901234567890123456789012
    )


def test_does_not_depend_on_or_change_decimal_precision() -> None:
    with localcontext() as context:
        context.prec = 2
        assert validate_amount("1234.56") == 123456
        assert context.prec == 2


def test_returns_expected_dictionary_with_local_iso_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FixedDate(date):
        @classmethod
        def today(cls) -> date:
            return date(2026, 11, 13)

    monkeypatch.setattr("expenses_cli.expenses.date", FixedDate)
    expense = create_expense(1, "  Almuerzo  ", "15.50")

    assert expense == {
        "id": 1,
        "description": "Almuerzo",
        "amount_cents": 1550,
        "date": "2026-11-13",
    }


def test_uses_current_local_date() -> None:
    before = date.today().isoformat()
    expense = create_expense(2, "Café", "0.01")
    after = date.today().isoformat()
    assert expense["date"] in (before, after)


@pytest.mark.parametrize(
    "value", (0, -1, True, False, "1", 1.0, Decimal("1"), None, [], {})
)
def test_rejects_invalid_ids_including_booleans(value: object) -> None:
    with pytest.raises(ValueError):
        create_expense(value, "Almuerzo", "15")


@pytest.mark.parametrize("value", ("", "   ", None, 15))
def test_rejects_invalid_descriptions(value: object) -> None:
    with pytest.raises(ValueError):
        create_expense(1, value, "15")


@pytest.mark.parametrize("value", ("abc", "0", "-1", "1.001", "NaN", "Infinity", True))
def test_rejects_invalid_amounts(value: object) -> None:
    with pytest.raises(ValueError):
        create_expense(1, "Almuerzo", value)


def test_add_expense_creates_first_expense_when_file_is_missing(tmp_path: Path) -> None:
    path = tmp_path / "expenses.json"
    assert not path.exists()

    before = date.today().isoformat()
    expense = add_expense(path, "  Café  ", "1.50")
    after = date.today().isoformat()

    assert expense == {
        "id": 1,
        "description": "Café",
        "amount_cents": 150,
        "date": expense["date"],
    }
    assert expense["date"] in (before, after)
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "next_id": 2,
        "expenses": [expense],
    }


def test_add_expense_assigns_consecutive_ids(tmp_path: Path) -> None:
    path = tmp_path / "expenses.json"
    created = [
        add_expense(path, "Café", "1.50"),
        add_expense(path, "Almuerzo", "15"),
        add_expense(path, "Transporte", "0.75"),
    ]

    assert [expense["id"] for expense in created] == [1, 2, 3]
    saved_data = json.loads(path.read_text(encoding="utf-8"))
    assert [expense["id"] for expense in saved_data["expenses"]] == [1, 2, 3]
    assert saved_data["next_id"] == 4


def test_add_expense_persists_complete_expenses_between_calls(tmp_path: Path) -> None:
    path = tmp_path / "expenses.json"
    first = add_expense(path, "Café", "1.50")
    first_saved_data = json.loads(path.read_text(encoding="utf-8"))
    assert first_saved_data == {"next_id": 2, "expenses": [first]}

    second = add_expense(Path(str(path)), "Almuerzo", "15.50")
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "next_id": 3,
        "expenses": [first_saved_data["expenses"][0], second],
    }


def test_add_expense_uses_saved_next_id_and_preserves_existing_history(tmp_path: Path) -> None:
    path = tmp_path / "expenses.json"
    previous_expense = {
        "id": 3,
        "description": "Compra anterior",
        "amount_cents": 250,
        "date": "2024-02-29",
    }
    path.write_text(
        json.dumps({"next_id": 8, "expenses": [previous_expense]}),
        encoding="utf-8",
    )

    expense = add_expense(path, "Café", "1.50")

    assert expense["id"] == 8
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "next_id": 9,
        "expenses": [previous_expense, expense],
    }


@pytest.mark.parametrize("existing", (False, True))
@pytest.mark.parametrize(
    "description, amount",
    [
        ("", "15"),
        ("   ", "15"),
        (None, "15"),
        (15, "15"),
        (True, "15"),
        ("Almuerzo", "abc"),
        ("Almuerzo", "0"),
        ("Almuerzo", "-1"),
        ("Almuerzo", "1.001"),
        ("Almuerzo", "NaN"),
        ("Almuerzo", "Infinity"),
        ("Almuerzo", True),
    ],
)
def test_add_expense_rejects_invalid_input_without_changing_file(
    tmp_path: Path, existing: bool, description: object, amount: object,
) -> None:
    path = tmp_path / "expenses.json"
    if existing:
        add_expense(path, "Compra anterior", "2.50")
        original = path.read_bytes()

    with pytest.raises(ValueError):
        add_expense(path, description, amount)

    if existing:
        assert path.read_bytes() == original
        assert list(tmp_path.iterdir()) == [path]
    else:
        assert not path.exists()
        assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("existing", (False, True))
@pytest.mark.parametrize("operation", ("load_data", "save_data"))
def test_add_expense_propagates_storage_errors_without_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, existing: bool, operation: str,
) -> None:
    path = tmp_path / "expenses.json"
    if existing:
        add_expense(path, "Compra anterior", "2.50")
        original = path.read_bytes()
    failure = OSError(f"simulated {operation} failure")

    def failing_storage(*args, **kwargs):
        raise failure

    monkeypatch.setattr(expenses, operation, failing_storage)

    with pytest.raises(OSError) as error:
        add_expense(path, "Café", "1.50")

    assert error.value is failure
    if existing:
        assert path.read_bytes() == original
    else:
        assert not path.exists()


def test_add_expense_propagates_replace_failure_and_preserves_original(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "expenses.json"
    add_expense(path, "Compra anterior", "2.50")
    original = path.read_bytes()
    failure = OSError("simulated replace failure")

    def failing_replace(source, destination):
        raise failure

    monkeypatch.setattr(storage.os, "replace", failing_replace)

    with pytest.raises(OSError) as error:
        add_expense(path, "Café", "1.50")

    assert error.value is failure
    assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]


def test_add_expense_rejects_corrupt_history_without_overwriting_it(tmp_path: Path) -> None:
    path = tmp_path / "expenses.json"
    original = b'{"next_id": '
    path.write_bytes(original)

    with pytest.raises(ValueError):
        add_expense(path, "Café", "1.50")

    assert path.read_bytes() == original


@pytest.fixture
def saved_expenses() -> list[dict]:
    return [
        {"id": 5, "description": "Café", "amount_cents": 150, "date": "2024-02-29"},
        {"id": 2, "description": "Almuerzo", "amount_cents": 1550, "date": "2026-11-14"},
        {"id": 7, "description": "Transporte", "amount_cents": 75, "date": "2026-11-15"},
    ]


def test_list_expenses_returns_empty_list_when_file_is_missing(tmp_path: Path) -> None:
    path = tmp_path / "missing" / "expenses.json"

    assert list_expenses(path) == []
    assert not path.exists()
    assert not path.parent.exists()


@pytest.mark.parametrize("count", (0, 1, 3))
def test_list_expenses_returns_all_saved_expenses(
    tmp_path: Path, saved_expenses: list[dict], count: int,
) -> None:
    path = tmp_path / "expenses.json"
    expected = saved_expenses[:count]
    path.write_text(
        json.dumps({"next_id": 8, "expenses": expected}, ensure_ascii=False),
        encoding="utf-8",
    )

    assert list_expenses(path) == expected


def test_list_expenses_does_not_modify_json_or_save_data(
    tmp_path: Path, saved_expenses: list[dict], monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "expenses.json"
    data = {"next_id": 8, "expenses": saved_expenses}
    original = (json.dumps(data, ensure_ascii=True, indent=4) + "\n").encode("utf-8")
    path.write_bytes(original)

    def unexpected_save(*args, **kwargs):
        pytest.fail("Consultar gastos no debe llamar a save_data")

    monkeypatch.setattr(expenses, "save_data", unexpected_save)

    for _ in range(2):
        assert list_expenses(path) == saved_expenses
        assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize(
    "failure", (OSError("simulated read failure"), PermissionError("access denied"))
)
def test_list_expenses_propagates_storage_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: OSError,
) -> None:
    path = tmp_path / "expenses.json"
    original = b'{"next_id": 1, "expenses": []}'
    path.write_bytes(original)

    def failing_load(received_path):
        assert received_path == path
        raise failure

    monkeypatch.setattr(expenses, "load_data", failing_load)

    with pytest.raises(type(failure)) as error:
        list_expenses(path)

    assert error.value is failure
    assert path.read_bytes() == original


@pytest.mark.parametrize("content", ("", "{", '{"expenses": []', "not json"))
def test_list_expenses_propagates_corrupt_json_error_without_changing_file(
    tmp_path: Path, content: str,
) -> None:
    path = tmp_path / "expenses.json"
    original = content.encode("utf-8")
    path.write_bytes(original)

    with pytest.raises(ValueError, match="Corrupto") as error:
        list_expenses(path)

    assert isinstance(error.value.__cause__, json.JSONDecodeError)
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    "data", ({}, {"next_id": 1, "expenses": {}}, {"next_id": 1, "expenses": [{}]})
)
def test_list_expenses_propagates_invalid_history_error_without_changing_file(
    tmp_path: Path, data: dict,
) -> None:
    path = tmp_path / "expenses.json"
    original = json.dumps(data).encode("utf-8")
    path.write_bytes(original)

    with pytest.raises(ValueError):
        list_expenses(path)

    assert path.read_bytes() == original


@pytest.mark.parametrize("index", (0, 1, 2), ids=("first", "middle", "last"))
def test_get_expense_returns_complete_expense_by_id(
    tmp_path: Path, saved_expenses: list[dict], index: int,
) -> None:
    path = tmp_path / "expenses.json"
    path.write_text(
        json.dumps({"next_id": 8, "expenses": saved_expenses}, ensure_ascii=False),
        encoding="utf-8",
    )
    expected = saved_expenses[index]

    assert get_expense(path, expected["id"]) == expected


@pytest.mark.parametrize("expense_id", (1, 3, 8, 999))
def test_get_expense_raises_when_id_is_missing(
    tmp_path: Path, saved_expenses: list[dict], expense_id: int,
) -> None:
    path = tmp_path / "expenses.json"
    path.write_text(
        json.dumps({"next_id": 8, "expenses": saved_expenses}), encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Gasto no encontrado"):
        get_expense(path, expense_id)


@pytest.mark.parametrize("next_id", (1, 20))
def test_get_expense_raises_for_empty_history(tmp_path: Path, next_id: int) -> None:
    path = tmp_path / "expenses.json"
    original = json.dumps({"next_id": next_id, "expenses": []}).encode("utf-8")
    path.write_bytes(original)

    with pytest.raises(ValueError, match="Gasto no encontrado"):
        get_expense(path, 1)

    assert path.read_bytes() == original


def test_get_expense_raises_for_missing_file_without_creating_it(tmp_path: Path) -> None:
    path = tmp_path / "missing" / "expenses.json"

    with pytest.raises(ValueError, match="Gasto no encontrado"):
        get_expense(path, 1)

    assert not path.parent.exists()


@pytest.mark.parametrize("expense_id", (5, 2, 7, 999))
def test_get_expense_does_not_modify_json_or_save_data(
    tmp_path: Path, saved_expenses: list[dict], monkeypatch: pytest.MonkeyPatch,
    expense_id: int,
) -> None:
    path = tmp_path / "expenses.json"
    data = {"next_id": 8, "expenses": saved_expenses}
    original = (json.dumps(data, ensure_ascii=True, indent=4) + "\n").encode("utf-8")
    path.write_bytes(original)

    def unexpected_save(*args, **kwargs):
        pytest.fail("Consultar un gasto no debe llamar a save_data")

    monkeypatch.setattr(expenses, "save_data", unexpected_save)

    for _ in range(2):
        if expense_id == 999:
            with pytest.raises(ValueError, match="Gasto no encontrado"):
                get_expense(path, expense_id)
        else:
            expected = next(item for item in saved_expenses if item["id"] == expense_id)
            assert get_expense(path, expense_id) == expected
        assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize(
    "failure", (OSError("simulated read failure"), PermissionError("access denied"))
)
def test_get_expense_propagates_storage_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: OSError,
) -> None:
    path = tmp_path / "expenses.json"
    original = b'{"next_id": 1, "expenses": []}'
    path.write_bytes(original)

    def failing_load(received_path):
        assert received_path == path
        raise failure

    monkeypatch.setattr(expenses, "load_data", failing_load)

    with pytest.raises(type(failure)) as error:
        get_expense(path, 1)

    assert error.value is failure
    assert path.read_bytes() == original


@pytest.mark.parametrize("content", ("", "{", '{"expenses": []', "not json"))
def test_get_expense_propagates_corrupt_json_error_without_changing_file(
    tmp_path: Path, content: str,
) -> None:
    path = tmp_path / "expenses.json"
    original = content.encode("utf-8")
    path.write_bytes(original)

    with pytest.raises(ValueError, match="Corrupto") as error:
        get_expense(path, 1)

    assert isinstance(error.value.__cause__, json.JSONDecodeError)
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    "data", ({}, {"next_id": 1, "expenses": {}}, {"next_id": 1, "expenses": [{}]})
)
def test_get_expense_propagates_invalid_history_error_without_changing_file(
    tmp_path: Path, data: dict,
) -> None:
    path = tmp_path / "expenses.json"
    original = json.dumps(data).encode("utf-8")
    path.write_bytes(original)

    with pytest.raises(ValueError):
        get_expense(path, 1)

    assert path.read_bytes() == original


@pytest.mark.parametrize(
    "expense_id", (0, -1, True, False, "1", 1.0, Decimal("1"), None, [], {}),
    ids=("zero", "negative", "true", "false", "string", "float", "decimal",
         "none", "list", "dict"),
)
def test_get_expense_rejects_invalid_id_types(
    tmp_path: Path, saved_expenses: list[dict], expense_id: object,
) -> None:
    path = tmp_path / "expenses.json"
    expense = dict(saved_expenses[0], id=1)
    original = json.dumps({"next_id": 2, "expenses": [expense]}).encode("utf-8")
    path.write_bytes(original)

    # Mismo contrato de entero positivo que create_expense y storage.validate_data.
    with pytest.raises(ValueError):
        get_expense(path, expense_id)

    assert path.read_bytes() == original
