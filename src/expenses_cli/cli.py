import argparse
from pathlib import Path

from .expenses import (
    add_expense,
    delete_expense,
    get_expense,
    list_expenses,
    total_expenses,
)


def main():
    parser = argparse.ArgumentParser(
        prog="expenses", description="CLI para gestionar gastos personales"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    # Comando list
    subparsers.add_parser("list", help="Listar gastos")

    # Comando add
    add_parser = subparsers.add_parser("add", help="Añadir gasto")
    add_parser.add_argument("--amount", required=True)
    add_parser.add_argument("--description", required=True)

    # Comando get
    get_parser = subparsers.add_parser("get", help="Buscar gasto por ID")
    get_parser.add_argument("id", type=int)

    # Comando delete
    delete_parser = subparsers.add_parser("delete", help="Borrar gasto por ID")
    delete_parser.add_argument("id", type=int)

    # Comando total - Listar el total de los gastos
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


def get_data_path():
    path = Path.home() / ".local" / "share" / "expenses_tracker_cli" / "expenses.json"
    return path
