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


def validate_data(data):
    if not isinstance(data, dict):
        raise ValueError("La estructura principal debe ser un diccionario")

    if "next_id" not in data:
        raise ValueError("Hace falta el campo next_id")

    next_id = data["next_id"]

    if not type(next_id) is int or not next_id > 0:
        raise ValueError("El id no es valido ya que no es entero o mayor a 0")
