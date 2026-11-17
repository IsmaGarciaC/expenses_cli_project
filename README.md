# Expenses CLI - Gestor de Gastos Personales

Una herramienta de terminal en Python para registrar gastos personales, consultar
el historial y saber cuánto has gastado. Está diseñada para personas que usan la
terminal y quieren llevar un registro sencillo, con datos guardados localmente en
JSON entre ejecuciones.

## Características

El paquete instala el comando `expenses`, con cinco subcomandos:

| Comando | Función |
| --- | --- |
| `add --amount IMPORTE --description "DESCRIPCIÓN"` | Registrar un gasto con ID y fecha local asignados automáticamente. |
| `list` | Mostrar el historial con ID, fecha, descripción e importe. |
| `get ID` | Consultar el detalle de un gasto. |
| `delete ID` | Eliminar un gasto por su ID. |
| `total` | Calcular el total de los gastos que siguen registrados. |

Los importes se guardan como centavos enteros de USD. La descripción debe contener
texto y el importe debe ser positivo, con un máximo de dos decimales. Usa punto
decimal (`1.50`); la coma (`1,50`) y valores como `1.230` se rechazan. Los IDs son
enteros positivos.

## Requisitos

- Python **3.10 o superior**, según `pyproject.toml`.
- Git para clonar el repositorio y un Python con `pip` y `venv` disponibles.
- Permiso de escritura en el directorio de datos del usuario.

La aplicación utiliza la biblioteca estándar de Python y no declara dependencias
de ejecución externas. La instalación usa `setuptools>=61` como backend de
construcción; `pip` lo obtiene automáticamente si hace falta.

## Instalación

Desde una terminal en Linux:

```bash
git clone https://github.com/IsmaGarciaC/expenses_cli_project.git
cd expenses_cli_project
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

La instalación editable permite usar el código del repositorio mediante el
comando `expenses`. Mantén el entorno virtual activado al ejecutar los ejemplos.

```bash
expenses --help
expenses add --help
```

## Uso

La siguiente sesión supone un historial inicialmente vacío. La fecha
`2026-11-16` es ilustrativa: cada gasto recibe la fecha local del día en que se
registra. Si ya tienes gastos, utiliza los IDs que devuelva tu instalación.

### Registrar gastos: `add`

```console
$ expenses add --amount 1.50 --description "Café"
Gasto 1 Café agregado correctamente
$ expenses add --amount 15.25 --description "Almuerzo"
Gasto 2 Almuerzo agregado correctamente
```

### Listar el historial: `list`

```console
$ expenses list
Historial de Gastos

#1 | 2026-11-16 | Café | $1.50
#2 | 2026-11-16 | Almuerzo | $15.25
```

### Consultar un gasto: `get`

```console
$ expenses get 1
Detalle del gasto:

ID: 1
Fecha: 2026-11-16
Descripción: Café
Importe: $1.50
```

### Calcular el total: `total`

```console
$ expenses total
El total de los gastos es: $16.75
```

### Eliminar un gasto: `delete`

La eliminación es inmediata y no pide confirmación.

```console
$ expenses delete 1
Gasto #1 eliminado correctamente
$ expenses total
El total de los gastos es: $15.25
```

Con un historial vacío, `list` muestra `No hay gastos registrados` y `total`
muestra `El total de los gastos es: $0.00`. Un ID inexistente al consultar o
eliminar produce el error `Gasto no encontrado`. Los errores de argumentos,
validación o acceso al almacenamiento se muestran en la terminal y finalizan con
código de salida `2`.

## Almacenamiento

En Linux, los datos se guardan en:

```text
~/.local/share/expenses_tracker_cli/expenses.json
```

La ruta se calcula a partir del directorio personal del usuario y es independiente
del directorio desde el que ejecutes `expenses`. El primer gasto válido crea el
directorio y el archivo si no existen. Consultar un historial vacío no crea el
JSON.

El archivo contiene `next_id` y una lista `expenses`; cada gasto guarda `id`,
`description`, `amount_cents` y `date` (formato `AAAA-MM-DD`). Los IDs empiezan en
`1` y el contador se conserva al eliminar registros para no reutilizarlos.

Cada alta o eliminación guarda el historial completo mediante un archivo temporal
y un reemplazo atómico. Las ejecuciones posteriores cargan los datos guardados.
Si el JSON está corrupto o su estructura es inválida, la aplicación informa del
problema y conserva el archivo sin sobrescribirlo.

## Pruebas

Desde la raíz del repositorio, con el entorno virtual activado:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

El extra `dev` instala `pytest`. Las pruebas cubren las validaciones, las
operaciones sobre gastos, la persistencia y la CLI. Usan rutas temporales y aíslan
el directorio personal en las pruebas de CLI para no modificar el historial real.

## Estructura del proyecto

| Ruta | Responsabilidad |
| --- | --- |
| `pyproject.toml` | Metadatos, empaquetado, comando `expenses` y configuración de pytest. |
| `src/expenses_cli/cli.py` | Argumentos, salida de terminal, errores y ruta del JSON. |
| `src/expenses_cli/expenses.py` | Modelo, validaciones y las cinco operaciones sobre gastos. |
| `src/expenses_cli/storage.py` | Lectura, validación del historial y guardado atómico del JSON. |
| `tests/` | Pruebas de la CLI, la lógica de gastos y el almacenamiento. |
| `docs/` | [Requerimientos](docs/requirements.md) y [arquitectura](docs/architecture.md). |

## Limitaciones

- No hay edición de gastos ni selección manual de la fecha de registro.
- No hay categorías, filtros, presupuestos, importación ni exportación.
- Los importes se manejan en USD; no hay selección ni conversión de monedas.
- No hay cuentas de usuario, sincronización ni interfaz gráfica.
- El almacenamiento es JSON: no hay SQLite, configuración de la ruta ni copias de
  seguridad automáticas. No se coordinan escrituras simultáneas; ejecuta las
  operaciones de una en una.
- Las instrucciones se han verificado en Linux. La compatibilidad con otros
  sistemas operativos no se ha verificado.
