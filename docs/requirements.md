# Requerimientos y alcance del proyecto

## Problema

La necesidad principal es registrar gastos cotidianos rápidamente. Las aplicaciones con muchas opciones pueden complicar ese registro, y mantener una hoja de cálculo requiere repetir tareas manuales. Una vez registrados los gastos, el usuario quiere consultar su historial y saber cuánto ha gastado.

## Solución propuesta

Una herramienta de terminal que almacene los gastos localmente y permita consultarlos en ejecuciones posteriores.

## Usuario objetivo

Personas que usan la terminal con frecuencia, conocen comandos básicos y quieren llevar un registro sencillo de sus gastos personales.

## Requisitos funcionales del MVP

- Registrar un gasto con su descripción e importe.
- Listar los gastos registrados.
- Consultar un gasto por su ID.
- Eliminar un gasto por su ID.
- Calcular el total de los gastos registrados. Si no hay gastos, el total es cero.

## Modelo conceptual del gasto

| Atributo | Obligatoriedad y restricciones |
| --- | --- |
| ID | Obligatorio. La aplicación lo asigna como entero positivo y único. |
| Descripción | Obligatoria. Debe contener al menos un carácter distinto de un espacio en blanco. |
| Importe | Obligatorio. Debe ser un número mayor que cero con hasta dos decimales. Todos los importes se expresan en USD. |
| Fecha | Obligatoria. La aplicación asigna la fecha local del día del registro. |
| Categoría | Fuera del modelo del MVP. |

## Historias de usuario y criterios de aceptación

### Registrar un gasto

Como persona que usa la terminal, quiero registrar un gasto con su descripción e importe para llevar un historial de mis compras.

- **Dado** un importe de 15 USD y la descripción «Almuerzo», **cuando** registro el gasto, **entonces** la aplicación confirma el registro y el listado muestra el gasto con su ID y la fecha local del día.
- **Dado** que la aplicación confirmó ese registro, **cuando** cierro la aplicación, la vuelvo a abrir y consulto el gasto por su ID, **entonces** aparecen la misma descripción, el mismo importe y la misma fecha.
- **Dado** que introduzco letras como importe, **cuando** intento registrar el gasto, **entonces** la aplicación indica que el importe es inválido y el historial se conserva.

### Eliminar un gasto

Como persona que lleva un historial de gastos, quiero eliminar un registro por su ID para corregir una entrada equivocada.

- **Dado** que existe un gasto con ID 3, **cuando** lo elimino, **entonces** desaparece del listado y de las consultas posteriores por ID, y su importe deja de contar en el total.
- **Dado** que el ID 25 no existe, **cuando** intento eliminarlo, **entonces** la aplicación informa que no encontró el gasto y conserva los demás registros.

## Comportamiento ante errores

| Situación | Comportamiento esperado |
| --- | --- |
| Descripción vacía o importe inválido | Indicar el campo y la restricción incumplida. Conservar los registros existentes. |
| ID inválido | Indicar que el ID debe ser un entero positivo. |
| ID inexistente al consultar o eliminar | Informar que el gasto no existe. Conservar los registros existentes. |
| Archivo JSON inexistente | Empezar con un historial vacío y crear el archivo al guardar el primer gasto válido. |
| Archivo JSON corrupto o con datos inválidos | Informar del problema y conservar el archivo original sin sobrescribirlo. |
| Error al guardar un registro o una eliminación | Informar que la operación falló y conservar los datos guardados previamente. |

## Requisitos técnicos y de entrega

- La aplicación se entrega como una CLI instalable y se usa desde la terminal.
- Los gastos se almacenan localmente en JSON y deben conservarse entre ejecuciones.
- Si falla una operación de escritura, los datos guardados previamente deben mantenerse íntegros.

## Fuera del alcance del MVP

- Filtros por categoría.
- Presupuestos mensuales.
- Cuentas de usuario.
- Interfaz gráfica.

## Entregas posteriores al MVP

- Migrar el almacenamiento a SQLite.
- Incorporar anotaciones de tipo al código.
- Añadir pruebas automatizadas que cubran los criterios de aceptación y los errores de almacenamiento.
- Documentar la instalación y el uso en un README.
