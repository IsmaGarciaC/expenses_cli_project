"""Capa de persistencia leyendo el modelo proveniente de expenses.py y guardandolo en disco
en formato JSON."""

import json


# Leer el archivo JSON si existe
def load_data(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"next_id": 1, "expenses": []}
    except json.JSONDecodeError as exc:
        raise ValueError("El archivo esta Corrupto") from exc
