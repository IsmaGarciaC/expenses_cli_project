"""Pruebas del modelo y sus validaciones, sin acceso a archivos."""

from datetime import date
from decimal import Decimal, localcontext

import pytest

from expenses_cli.expenses import (
    create_expense,
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
