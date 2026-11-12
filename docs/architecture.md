# Arquitectura del proyecto

El MVP será una CLI instalable en Python para registrar y consultar gastos personales. Esta arquitectura describe la implementación inicial a partir de los [requerimientos](requirements.md).

## Estructura propuesta

```text
pyproject.toml
docs/
  requirements.md
  architecture.md
src/
  expenses_cli/
    __init__.py
    cli.py
    expenses.py
    storage.py
```

| Archivo | Responsabilidad |
| --- | --- |
| `pyproject.toml` | Configurar el empaquetado y registrar el comando `expenses` como punto de entrada a `expenses_cli.cli:main`. |
| `cli.py` | Interpretar los argumentos con `argparse`, invocar la operación correspondiente y mostrar resultados o errores en la terminal. |
| `expenses.py` | Definir el modelo de gasto y sus validaciones. Implementar el registro, el listado, la consulta y la eliminación por ID, y el cálculo del total. |
| `storage.py` | Resolver la ruta del archivo local, leer y validar el JSON y guardar el historial completo de forma atómica. |

## Decisiones técnicas

- **Flujo de ejecución.** La CLI delega cada operación a `expenses.py`, que usa las operaciones de carga y guardado de `storage.py`. La CLI confirma un registro o una eliminación después de que se complete el guardado. La lectura y escritura quedan encapsuladas en `storage.py` para facilitar la futura migración a SQLite.
- **Importes y fechas.** Validar el texto del importe con `Decimal` y guardar el valor como un entero de centavos de USD para sumar con exactitud. Cada gasto recibe la fecha local al registrarse y se guarda en formato ISO `AAAA-MM-DD`. El total se calcula sobre los gastos vigentes y vale cero si el historial está vacío.
- **Archivo e identificadores.** Guardar `expenses.json` en un directorio de datos del usuario, con una lista de gastos y el siguiente ID positivo. El historial vacío comienza con ID 1. Cada registro incrementa el contador y las eliminaciones lo conservan para evitar reutilizar IDs. Si el archivo no existe, se crea al guardar el primer gasto válido.
- **Integridad de los datos.** Validar la estructura y los registros antes de aceptar el historial. Si el JSON está corrupto o contiene datos inválidos, informar del error y conservar el archivo. Para guardar, escribir primero en un temporal del mismo directorio y reemplazar el archivo con `os.replace` tras completar la escritura. El MVP asume que las operaciones de escritura se ejecutan de una en una.
