"""Modelo de gasto y validaciones independientes de la CLI y el almacenamiento."""

from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
from typing import TypedDict


class Expense(TypedDict):
    id: int
    description: str
    amount_cents: int
    date: str


def validate_description(description: object) -> str:
    """Devuelve el texto sin espacios exteriores o lanza ValueError."""
    if not isinstance(description, str) or not description.strip():
        raise ValueError("La descripción debe ser texto no vacío.")
    return description.strip()


def validate_amount(amount: object) -> int:
    """Convierte str, int, float o Decimal positivo a centavos exactos.

    Se rechazan valores no finitos y más de dos cifras decimales,
    incluidos los ceros finales (por ejemplo, '1.230').
    """
    error = "El importe debe ser un número positivo con máximo dos decimales."
    if isinstance(amount, bool) or not isinstance(amount, (str, int, float, Decimal)):
        raise ValueError(error)

    try:
        value = Decimal(str(amount))
    except InvalidOperation as exc:
        raise ValueError(error) from exc

    if not value.is_finite() or value <= 0:
        raise ValueError(error)

    parts = value.as_tuple()
    if parts.exponent < -2:
        raise ValueError(error)

    # Evita redondear importes grandes por la precisión del contexto Decimal.
    with localcontext() as context:
        context.prec = max(28, len(parts.digits) + 2)
        return int(value * 100)


def create_expense(expense_id: object, description: object, amount: object) -> Expense:
    """Crea un gasto validado con la fecha local del día en formato ISO."""
    if (
        isinstance(expense_id, bool)
        or not isinstance(expense_id, int)
        or expense_id <= 0
    ):
        raise ValueError("El ID debe ser un entero positivo.")

    return {
        "id": expense_id,
        "description": validate_description(description),
        "amount_cents": validate_amount(amount),
        "date": date.today().isoformat(),
    }
