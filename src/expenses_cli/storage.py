"""Capa de persistencia leyendo el modelo proveniente de expenses.py y guardandolo en disco
en formato JSON."""

import json

path = "gastos.json"


# Leer el archivo JSON si existe
def load_data(path):
    try:
        with open("gastos.json", encoding="utf-8") as f:
            json.load(f)
            try:
                with open("gastos.json", encoding="utf-8") as f:
                    json.load(f)
            except json.JSONDecodeError as error:
                print(error)

            json.dump(f)

    except FileNotFoundError as error:
        print({"next_id": 1, "expenses": []})
