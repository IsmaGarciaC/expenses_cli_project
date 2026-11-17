"""Modelo de gasto y validaciones independientes de la CLI y el almacenamiento."""

from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import TypedDict

from .storage import load_data, save_data


class Expense(TypedDict):
    """Representa un gasto con importe en centavos y fecha ISO."""

    id: int
    description: str
    amount_cents: int
    date: str


def validate_description(description: object) -> str:
    """Devuelve la descripción sin espacios exteriores.

    Lanza ValueError si no es texto o queda vacía al quitar los espacios.
    """
    if not isinstance(description, str) or not description.strip():
        raise ValueError("La descripción debe ser texto no vacío.")
    return description.strip()


def validate_amount(amount: object) -> int:
    """Convierte str, int, float o Decimal positivo a centavos exactos.

    Se rechazan valores no finitos y más de dos cifras decimales,
    incluidos los ceros finales (por ejemplo, '1.230').
    Lanza ValueError si el tipo o el valor del importe no es válido.
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
    """Crea un gasto validado con la fecha local del día en formato ISO.

    Lanza ValueError si el ID, la descripción o el importe no es válido.
    """
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


def add_expense(path: str | Path, description: object, amount: object) -> Expense:
    """Registra y devuelve un gasto con el siguiente ID del historial.

    Incrementa el contador de IDs al guardar. Lanza ValueError si los datos
    o el historial no son válidos y propaga OSError del almacenamiento.
    """
    data = load_data(path)
    next_id = data["next_id"]
    new_expense = create_expense(next_id, description, amount)
    data["expenses"].append(new_expense)
    data["next_id"] += 1
    save_data(path, data)
    return new_expense


def list_expenses(path: str | Path) -> list[Expense]:
    """Devuelve los gastos en orden de almacenamiento, o [] si no hay archivo.

    Lanza ValueError si el historial no es válido y propaga OSError de lectura.
    """
    data = load_data(path)
    return data["expenses"]


def get_expense(path: str | Path, expense_id: object) -> Expense:
    """Devuelve el gasto identificado por un entero positivo.

    Lanza ValueError si el ID es inválido, no existe o el historial no es válido.
    Propaga OSError de lectura.
    """
    if type(expense_id) is not int or expense_id <= 0:
        raise ValueError("ID no valido")
    data = load_data(path)
    for expense in data["expenses"]:
        if expense["id"] == expense_id:
            return expense
    raise ValueError("Gasto no encontrado")


def delete_expense(path: str | Path, expense_id: object) -> bool:
    """Elimina el gasto indicado y devuelve True tras guardar el historial.

    Conserva el contador de IDs. Lanza ValueError si el ID es inválido,
    no existe o el historial no es válido y propaga OSError del almacenamiento.
    """
    if type(expense_id) is not int or expense_id <= 0:
        raise ValueError("ID no valido")
    data = load_data(path)
    for index, expense in enumerate(data["expenses"]):
        if expense["id"] == expense_id:
            data["expenses"].pop(index)
            save_data(path, data)
            return True
    raise ValueError("Gasto no encontrado")


def total_expenses(path: str | Path) -> int:
    """Devuelve el total en centavos, o cero si no hay gastos o archivo.

    Lanza ValueError si el historial no es válido y propaga OSError de lectura.
    """
    data = load_data(path)
    total = sum(expense["amount_cents"] for expense in data["expenses"])
    return total
