"""Capa de persistencia leyendo el modelo proveniente de expenses.py y guardandolo en disco
en formato JSON."""

import json


# Leer el archivo JSON si existe
def load_data(path):
    try:
        with open("gastos.json", encoding="utf-8") as f:
            json.load(f)
            return f
    except FileNotFoundError:
        return {"next_id": 1, "expenses": []}
    except json.JSONDecodeError:
        return "El archivo esta Corrupto"
