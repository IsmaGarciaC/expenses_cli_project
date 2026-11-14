"""Validación del historial y persistencia atómica usando archivos temporales."""

import copy
import json
from pathlib import Path

import pytest

from expenses_cli import storage


@pytest.fixture
def valid_data() -> dict:
    return {
        "next_id": 3,
        "expenses": [
            {"id": 1, "description": "Café", "amount_cents": 150, "date": "2024-02-29"},
            {"id": 2, "description": "Almuerzo", "amount_cents": 1550, "date": "2026-11-14"},
        ],
    }


def test_load_missing_file_returns_empty_history_without_creating_files(tmp_path: Path) -> None:
    path = tmp_path / "missing" / "expenses.json"
    assert storage.load_data(path) == {"next_id": 1, "expenses": []}
    assert not path.parent.exists()


def test_missing_file_returns_independent_empty_histories(tmp_path: Path) -> None:
    path = tmp_path / "expenses.json"
    first = storage.load_data(path)
    first["expenses"].append({"id": 1})
    assert storage.load_data(path) == {"next_id": 1, "expenses": []}


def test_load_valid_json_from_received_path(tmp_path: Path, valid_data: dict) -> None:
    path = tmp_path / "custom.json"
    original = json.dumps(valid_data, ensure_ascii=False).encode("utf-8")
    path.write_bytes(original)
    assert storage.load_data(str(path)) == valid_data
    assert path.read_bytes() == original


@pytest.mark.parametrize("content", ("", "{", '{"expenses": []', "not json"))
def test_load_corrupt_json_preserves_original_and_exception_chain(
    tmp_path: Path, content: str,
) -> None:
    path = tmp_path / "expenses.json"
    original = content.encode("utf-8")
    path.write_bytes(original)
    with pytest.raises(ValueError, match="Corrupto") as error:
        storage.load_data(path)
    assert isinstance(error.value.__cause__, json.JSONDecodeError)
    assert path.read_bytes() == original


@pytest.mark.parametrize("data", (None, [], "text", 1, True, {}))
def test_load_invalid_json_data_preserves_original(tmp_path: Path, data: object) -> None:
    path = tmp_path / "expenses.json"
    original = json.dumps(data).encode("utf-8")
    path.write_bytes(original)
    with pytest.raises(ValueError):
        storage.load_data(path)
    assert path.read_bytes() == original


@pytest.mark.parametrize("data", (None, [], "text", 1, 1.5, True, False))
def test_validate_rejects_non_dictionary_roots(data: object) -> None:
    with pytest.raises(ValueError, match="diccionario"):
        storage.validate_data(data)


@pytest.mark.parametrize("field", ("next_id", "expenses"))
def test_validate_requires_top_level_fields(valid_data: dict, field: str) -> None:
    del valid_data[field]
    with pytest.raises(ValueError, match=field):
        storage.validate_data(valid_data)


@pytest.mark.parametrize("value", (0, -1, True, False, 1.0, "1", None, [], {}))
def test_validate_rejects_invalid_next_id(valid_data: dict, value: object) -> None:
    valid_data["next_id"] = value
    with pytest.raises(ValueError, match="next_id"):
        storage.validate_data(valid_data)


@pytest.mark.parametrize("value", (None, {}, "text", 1, True, ()))
def test_validate_requires_expenses_list(valid_data: dict, value: object) -> None:
    valid_data["expenses"] = value
    with pytest.raises(ValueError, match="lista"):
        storage.validate_data(valid_data)


@pytest.mark.parametrize("value", (None, [], "text", 1, True))
def test_validate_requires_expense_dictionaries(valid_data: dict, value: object) -> None:
    valid_data["expenses"] = [value]
    with pytest.raises(ValueError, match="diccionario"):
        storage.validate_data(valid_data)


@pytest.mark.parametrize("field", ("id", "description", "amount_cents", "date"))
def test_validate_requires_expense_fields(valid_data: dict, field: str) -> None:
    del valid_data["expenses"][0][field]
    with pytest.raises(ValueError, match=field):
        storage.validate_data(valid_data)


@pytest.mark.parametrize("field", ("id", "amount_cents"))
@pytest.mark.parametrize("value", (0, -1, True, False, 1.0, "1", None, [], {}))
def test_validate_requires_positive_integer_expense_fields(
    valid_data: dict, field: str, value: object,
) -> None:
    valid_data["expenses"][0][field] = value
    with pytest.raises(ValueError, match=field):
        storage.validate_data(valid_data)


@pytest.mark.parametrize("value", ("", "   ", "\t\n", None, 1, True, [], {}))
def test_validate_rejects_invalid_descriptions(valid_data: dict, value: object) -> None:
    valid_data["expenses"][0]["description"] = value
    with pytest.raises(ValueError, match="description"):
        storage.validate_data(valid_data)


@pytest.mark.parametrize(
    "value",
    (
        None, 20261114, True, [], {}, "", "2023-02-29", "2024-02-30",
        "2026-13-01", "2026-00-01", "2026-11-00", "0000-01-01",
        "2026-1-01", "20261114", "2026-W46-6", "2026-11-14T00:00:00",
        " 2026-11-14", "2026-11-14 ",
    ),
)
def test_validate_rejects_invalid_or_non_canonical_dates(
    valid_data: dict, value: object,
) -> None:
    valid_data["expenses"][0]["date"] = value
    with pytest.raises(ValueError, match="date"):
        storage.validate_data(valid_data)


def test_validate_invalid_date_preserves_exception_chain(valid_data: dict) -> None:
    valid_data["expenses"][0]["date"] = "2023-02-29"
    with pytest.raises(ValueError) as error:
        storage.validate_data(valid_data)
    assert isinstance(error.value.__cause__, ValueError)


def test_validate_rejects_duplicate_ids(valid_data: dict) -> None:
    valid_data["expenses"][1]["id"] = 1
    with pytest.raises(ValueError, match="duplicado"):
        storage.validate_data(valid_data)


@pytest.mark.parametrize("next_id", (1, 2, 8))
def test_validate_next_id_must_exceed_every_existing_id(
    valid_data: dict, next_id: int,
) -> None:
    valid_data["expenses"][0]["id"] = 8
    valid_data["next_id"] = next_id
    with pytest.raises(ValueError, match="next_id"):
        storage.validate_data(valid_data)


def test_validate_returns_same_data_without_normalizing_or_dropping_fields(valid_data: dict) -> None:
    valid_data["expenses"].reverse()
    valid_data["expenses"][0]["description"] = "  Café  "
    valid_data["expenses"][0]["extra"] = "preserved"
    valid_data["extra"] = "preserved"
    valid_data["next_id"] = 10
    original = copy.deepcopy(valid_data)
    assert storage.validate_data(valid_data) is valid_data
    assert valid_data == original


@pytest.mark.parametrize("next_id", (1, 20))
def test_validate_accepts_empty_history_without_resetting_counter(next_id: int) -> None:
    data = {"next_id": next_id, "expenses": []}
    assert storage.validate_data(data) is data


@pytest.mark.parametrize("as_string", (False, True))
def test_save_creates_parent_directories_and_round_trips_data(
    tmp_path: Path, valid_data: dict, as_string: bool,
) -> None:
    path = tmp_path / "data" / "nested" / "custom.json"
    original = copy.deepcopy(valid_data)
    assert storage.save_data(str(path) if as_string else path, valid_data) is None
    assert storage.load_data(path) == valid_data
    assert valid_data == original
    assert "Café" in path.read_text(encoding="utf-8")
    assert list(path.parent.iterdir()) == [path]


def test_save_replaces_existing_file_only_after_complete_temporary_write(
    tmp_path: Path, valid_data: dict, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "expenses.json"
    original = b'{"next_id": 1, "expenses": []}'
    path.write_bytes(original)
    real_replace = storage.os.replace
    replacements = []

    def checked_replace(source: Path, destination: Path) -> None:
        assert source.parent == path.parent
        assert source != path
        assert destination == path
        assert json.loads(source.read_text(encoding="utf-8")) == valid_data
        assert path.read_bytes() == original
        replacements.append(source)
        real_replace(source, destination)

    monkeypatch.setattr(storage.os, "replace", checked_replace)
    storage.save_data(path, valid_data)
    assert len(replacements) == 1
    assert storage.load_data(path) == valid_data
    assert list(tmp_path.iterdir()) == [path]


def test_save_invalid_data_preserves_original(tmp_path: Path, valid_data: dict) -> None:
    path = tmp_path / "expenses.json"
    original = b'original contents'
    path.write_bytes(original)
    valid_data["next_id"] = 1
    with pytest.raises(ValueError, match="next_id"):
        storage.save_data(path, valid_data)
    assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]


def test_save_invalid_data_does_not_create_directories(tmp_path: Path) -> None:
    path = tmp_path / "missing" / "expenses.json"
    with pytest.raises(ValueError):
        storage.save_data(path, {})
    assert not path.parent.exists()


def test_serialization_failure_preserves_original(tmp_path: Path, valid_data: dict) -> None:
    path = tmp_path / "expenses.json"
    original = b'original contents'
    path.write_bytes(original)
    valid_data["extra"] = object()
    with pytest.raises(TypeError):
        storage.save_data(path, valid_data)
    assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("existing", (False, True))
def test_partial_write_failure_cleans_temporary_and_preserves_original(
    tmp_path: Path, valid_data: dict, monkeypatch: pytest.MonkeyPatch, existing: bool,
) -> None:
    path = tmp_path / "expenses.json"
    original = b'{"next_id": 1, "expenses": []}'
    if existing:
        path.write_bytes(original)
    real_temporary_file = storage.NamedTemporaryFile
    failure = OSError("simulated write failure")
    temporary_paths = []

    def failing_temporary_file(*args, **kwargs):
        temporary = real_temporary_file(*args, **kwargs)
        temporary_paths.append(Path(temporary.name))

        def partial_write(content: str) -> None:
            temporary.file.write(content[:10])
            temporary.file.flush()
            raise failure

        monkeypatch.setattr(temporary, "write", partial_write)
        return temporary

    monkeypatch.setattr(storage, "NamedTemporaryFile", failing_temporary_file)
    with pytest.raises(OSError) as error:
        storage.save_data(path, valid_data)
    assert error.value is failure
    assert len(temporary_paths) == 1
    assert not temporary_paths[0].exists()
    if existing:
        assert path.read_bytes() == original
    else:
        assert not path.exists()
    assert list(tmp_path.iterdir()) == ([path] if existing else [])


@pytest.mark.parametrize("existing", (False, True))
def test_replace_failure_cleans_temporary_and_preserves_original(
    tmp_path: Path, valid_data: dict, monkeypatch: pytest.MonkeyPatch, existing: bool,
) -> None:
    path = tmp_path / "expenses.json"
    original = b'{"next_id": 1, "expenses": []}'
    if existing:
        path.write_bytes(original)
    failure = OSError("simulated replace failure")
    temporary_paths = []

    def failing_replace(source: Path, destination: Path) -> None:
        assert source.parent == destination.parent == path.parent
        assert json.loads(source.read_text(encoding="utf-8")) == valid_data
        temporary_paths.append(source)
        raise failure

    monkeypatch.setattr(storage.os, "replace", failing_replace)
    with pytest.raises(OSError) as error:
        storage.save_data(path, valid_data)
    assert error.value is failure
    assert len(temporary_paths) == 1
    assert not temporary_paths[0].exists()
    if existing:
        assert path.read_bytes() == original
    else:
        assert not path.exists()
    assert list(tmp_path.iterdir()) == ([path] if existing else [])
