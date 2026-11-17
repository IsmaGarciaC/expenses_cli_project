"""Procesa los comandos de gastos y muestra sus resultados en la terminal."""

import argparse
from pathlib import Path

from .expenses import (
    add_expense,
    delete_expense,
    get_expense,
    list_expenses,
    total_expenses,
)


def main() -> None:
    """Procesa los argumentos e imprime el resultado del comando solicitado.

    Convierte ValueError y OSError del comando en errores de argparse.
    Lanza SystemExit con código 2 ante errores de argumentos, validación
    o almacenamiento, y con código 0 cuando se solicita ayuda.
    """
    parser = argparse.ArgumentParser(
        prog="expenses", description="CLI para gestionar gastos personales"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="Listar gastos")

    add_parser = subparsers.add_parser("add", help="Añadir gasto")
    add_parser.add_argument("--amount", required=True)
    add_parser.add_argument("--description", required=True)

    get_parser = subparsers.add_parser("get", help="Buscar gasto por ID")
    get_parser.add_argument("id", type=int)

    delete_parser = subparsers.add_parser("delete", help="Borrar gasto por ID")
    delete_parser.add_argument("id", type=int)

    subparsers.add_parser("total", help="Mostrar el total de los gastos")

    args = parser.parse_args()

    try:
        path = get_data_path()
        if args.command == "list":
            show_expenses = list_expenses(path)
            if not show_expenses:
                print("No hay gastos registrados")
            else:
                print("Historial de Gastos")
                print()
                for expense in show_expenses:
                    print(
                        f"#{expense['id']} | {expense['date']} | {expense['description']} | ${expense['amount_cents'] / 100:.2f}"
                    )
        elif args.command == "add":
            new_expense = add_expense(path, args.description, args.amount)
            print(
                f"Gasto {new_expense['id']} {new_expense['description']} agregado correctamente"
            )
        elif args.command == "get":
            expense = get_expense(path, args.id)
            print("Detalle del gasto:")
            print()
            print(f"ID: {expense['id']}")
            print(f"Fecha: {expense['date']}")
            print(f"Descripción: {expense['description']}")
            print(f"Importe: ${expense['amount_cents'] / 100:.2f}")

        elif args.command == "delete":
            delete_expense(path, args.id)
            print(f"Gasto #{args.id} eliminado correctamente")
        elif args.command == "total":
            total = total_expenses(path) / 100
            print(f"El total de los gastos es: ${total:.2f}")
    except ValueError as exc:
        parser.error(str(exc))
    except OSError as exc:
        parser.error(f"No se pudo acceder al almacenamiento: {exc}")


def get_data_path() -> Path:
    """Devuelve la ruta del JSON bajo el directorio personal sin crearla.

    Propaga RuntimeError si no se puede resolver el directorio personal.
    """
    path = Path.home() / ".local" / "share" / "expenses_tracker_cli" / "expenses.json"
    return path
