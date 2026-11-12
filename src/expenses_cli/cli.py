import argparse


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
