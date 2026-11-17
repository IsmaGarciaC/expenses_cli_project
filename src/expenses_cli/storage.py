"""Lee, valida y guarda el historial de gastos en formato JSON."""

import json
import os
from datetime import date
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, TypedDict, cast

if TYPE_CHECKING:
    from .expenses import Expense


class ExpenseHistory(TypedDict):
    """Representa el historial con el siguiente ID y sus gastos vigentes."""

    next_id: int
    expenses: list["Expense"]


def load_data(path: str | Path) -> ExpenseHistory:
    """Lee un historial validado o devuelve uno vacío si el archivo no existe.

    Lanza ValueError si el JSON está corrupto o el historial no es válido.
    Propaga OSError si ocurre otro error de lectura.
    """
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"next_id": 1, "expenses": []}
    except json.JSONDecodeError as exc:
        raise ValueError("El archivo esta Corrupto") from exc

    return validate_data(data)


def validate_data(data: object) -> ExpenseHistory:
    """Valida el historial completo y devuelve el mismo diccionario.

    Conserva los campos adicionales. Lanza ValueError si la estructura,
    los gastos o el siguiente ID no cumplen las reglas del historial.
    """

    if not isinstance(data, dict):
        raise ValueError("La estructura principal debe ser un diccionario")

    if "next_id" not in data:
        raise ValueError("Hace falta el campo next_id")

    next_id = data["next_id"]

    if type(next_id) is not int or next_id <= 0:
        raise ValueError("next_id debe ser un entero positivo")

    if "expenses" not in data:
        raise ValueError("Hace falta el campo expenses")

    if not isinstance(data["expenses"], list):
        raise ValueError("expenses no es una lista")

    required_fields = {"id", "description", "amount_cents", "date"}
    seen_ids: set[int] = set()

    for expense in data["expenses"]:
        if not isinstance(expense, dict):
            raise ValueError("Cada gasto debe ser un diccionario")

        missing_fields = required_fields - expense.keys()
        if missing_fields:
            raise ValueError(
                f"Faltan campos del gasto: {', '.join(sorted(missing_fields))}"
            )

        expense_id = expense["id"]
        if type(expense_id) is not int or expense_id <= 0:
            raise ValueError("El id de cada gasto debe ser un entero positivo")

        description = expense["description"]
        if not isinstance(description, str) or not description.strip():
            raise ValueError(
                f"El gasto {expense_id}: description debe ser texto no vacío"
            )

        amount_cents = expense["amount_cents"]
        if type(amount_cents) is not int or amount_cents <= 0:
            raise ValueError(
                f"El gasto {expense_id}: amount_cents debe ser un entero positivo"
            )

        expense_date = expense["date"]
        date_error = (
            f"El gasto {expense_id}: date debe ser una fecha real en formato YYYY-MM-DD"
        )
        if not isinstance(expense_date, str):
            raise ValueError(date_error)
        try:
            parsed_date = date.fromisoformat(expense_date)
        except ValueError as exc:
            raise ValueError(date_error) from exc
        if parsed_date.isoformat() != expense_date:
            raise ValueError(date_error)

        if expense_id in seen_ids:
            raise ValueError(f"ID duplicado: {expense_id}")
        seen_ids.add(expense_id)

    if seen_ids and next_id <= max(seen_ids):
        raise ValueError("next_id debe ser mayor que todos los IDs existentes")

    return cast(ExpenseHistory, data)


def save_data(path: str | Path, data: object) -> None:
    """Guarda un historial válido mediante un reemplazo atómico del destino.

    Crea los directorios necesarios y elimina el temporal al finalizar.
    Lanza ValueError si el historial no es válido, TypeError si contiene
    valores no serializables y propaga OSError de escritura o limpieza.
    """
    validated_data = validate_data(data)
    content = json.dumps(validated_data, ensure_ascii=False, indent=2)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)

        # El temporal ya está cerrado: el destino cambia solo en este punto.
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
