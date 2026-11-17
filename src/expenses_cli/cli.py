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
    if args.command == "list":
        path = get_data_path()
        show_expenses = list_expenses(path)
        print(show_expenses)
    elif args.command == "add":
        path = get_data_path()
        new_expense = add_expense(path, args.description, args.amount)
        print(
            f"Gasto {new_expense['id']} {new_expense['description']} agregado correctamente"
        )
    elif args.command == "get":
        path = get_data_path()
        expense = get_expense(path, args.id)
        print(expense)
    elif args.command == "delete":
        path = get_data_path()
        delete_expense(path, args.id)
        print(f"Gasto #{args.id} eliminado correctamente")
    elif args.command == "total":
        path = get_data_path()
        total = total_expenses(path) / 100
        print(f"El total de los gastos es: ${total:.2f}")


def get_data_path():
    path = Path.home() / ".local" / "share" / "expenses_tracker_cli" / "expenses.json"
    return path
