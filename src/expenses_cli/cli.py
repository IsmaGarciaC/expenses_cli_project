import argparse

def main():
    parser = argparse.ArgumentParser(
        prog="expenses",
        description="CLI para gestionar gastos personales"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    subparsers.add_parser("list", help="Listar gastos")

    subparsers.add_parser("add", help="Añadir gasto")

    subparsers.add_parser("get", help="Buscar gasto por ID")

    subparsers.add_parser("delete", help="Borrar gasto por ID")

    subparsers.add_parser("total", help="Mostrar el total de los gastos")

    args = parser.parse_args()