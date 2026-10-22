## Mulita

Mulita es una herramienta de línea de comandos para analizar y organizar
fotografías, videos y proyectos de edición según sus fechas y metadatos.
Genera un plan JSON que puede revisarse antes de usarlo; por defecto, su
ejecución es una simulación y no modifica archivos.

La versión actual es **0.3.0** y el proyecto sigue en desarrollo.

## Contenido

- [Capacidades](#capacidades)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Inicio rápido](#inicio-rápido)
- [Opciones de la CLI](#opciones-de-la-cli)
- [Caché y metadatos](#caché-y-metadatos)
- [Ejecución segura](#ejecución-segura)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Desarrollo y pruebas](#desarrollo-y-pruebas)
- [Documentación relacionada](#documentación-relacionada)

## Capacidades

- Recorre directorios de forma recursiva y clasifica imágenes, archivos RAW,
  videos, proyectos de edición, auxiliares y extensiones desconocidas.
- Extrae fechas de metadatos con ExifTool y aplica prioridades distintas para
  fotografías y videos. Si no encuentra una fecha utilizable, usa la fecha de
  modificación del archivo e identifica ese respaldo en el plan.
- Asocia sidecars compatibles (XMP, RRDATA y RREXIF) con sus archivos
  principales. Los archivos desconocidos y sidecars huérfanos o ambiguos se
  informan, pero no se incluyen como operaciones de movimiento.
- Propone destinos con la estructura
  `AÑO/MES/DÍA/CATEGORÍA` y evita colisiones asignando sufijos numéricos.
- Exporta y carga planes JSON; puede simularlos o ejecutarlos con validaciones,
  confirmación y registro de resultados.
- Mantiene en caché los metadatos para reducir extracciones repetidas.

## Requisitos

- Python 3.11 o posterior.
- ExifTool instalado y disponible en `PATH` para leer metadatos EXIF y de
  video. Es opcional: si no está disponible, Mulita utiliza la fecha de
  modificación del archivo como respaldo.

## Instalación

Desde la raíz del repositorio, instala el paquete y las herramientas de
desarrollo con `pip`:

```bash
python -m pip install -e ".[dev]"
```

O con `uv`:

```bash
uv sync --group dev
```

Comprueba que la CLI esté disponible:

```bash
mulita --help
```

También puedes invocarla como módulo:

```bash
python -m mulita --help
```

## Inicio rápido

Con Mulita instalada, consulta la ayuda:

```bash
mulita --help
```

El flujo recomendado es analizar el origen, crear un plan, simularlo y solo
después confirmar la ejecución real:

1. [Analiza el directorio de origen](#1-analizar-un-origen).
2. [Genera y guarda un plan JSON](#2-generar-y-guardar-un-plan).
3. [Revisa la simulación](#3-revisar-la-simulación).
4. [Ejecuta el plan tras revisarlo](#4-confirmar-la-ejecución-real).

Los ejemplos siguientes usan rutas de muestra. Sustitúyelas por rutas
adecuadas a tu sistema y prueba primero con una copia de tus archivos.

### 1. Analizar un origen

```bash
mulita scan "C:/fotos/origen"
```

El escaneo resume los archivos encontrados, los grupos de medios, los
sidecars asociados y los elementos que requieren revisión. Para volver a
extraer metadatos en lugar de reutilizar el caché:

```bash
mulita scan "C:/fotos/origen" --sin-cache
```

### 2. Generar y guardar un plan

```bash
mulita plan "C:/fotos/origen" --destino "C:/fotos/organizadas" --salida "C:/fotos/plan.json"
```

`plan` no mueve archivos. Calcula nuevamente destinos y colisiones cada vez
que se ejecuta, aunque reutilice metadatos en caché. No se puede guardar el
JSON dentro del origen; si el archivo de salida ya existe, se solicita
confirmación antes de reemplazarlo.

Para generar el plan sin reutilizar metadatos:

```bash
mulita plan "C:/fotos/origen" --destino "C:/fotos/organizadas" --salida "C:/fotos/plan.json" --sin-cache
```

### 3. Revisar la simulación

```bash
mulita run "C:/fotos/plan.json"
```

Este es el modo predeterminado: informa el origen, el destino y la cantidad
prevista de movimientos, sin cambiar archivos. Si se omite la ruta del plan,
Mulita busca archivos JSON de plan en el directorio actual y, si encuentra
varios, permite seleccionar uno.

### 4. Confirmar la ejecución real

```bash
mulita run "C:/fotos/plan.json" --ejecutar
```

Antes de mover archivos, Mulita valida el plan, las rutas de origen y los
destinos, prepara una ruta para la auditoría y solicita confirmación. No
sobrescribe destinos existentes. Verifica cada traslado y, ante fallos,
intenta revertir los movimientos de esa operación. Al finalizar guarda un
reporte JSON en `reportes/ejecucion_<plan>.json`; si ese nombre ya existe,
elige un nombre alternativo para conservar los reportes anteriores.

## Opciones de la CLI

Consulta `mulita --help`, `mulita scan --help`, `mulita plan --help` o
`mulita run --help` para obtener la referencia completa de la versión
instalada.

| Comando u opción | Descripción |
| --- | --- |
| `scan ORIGEN` | Analiza un directorio y presenta un resumen. |
| `plan ORIGEN --destino DESTINO` | Genera un plan sin modificar archivos. |
| `plan ... --salida ARCHIVO.json` | Guarda el plan en formato JSON. |
| `scan` / `plan` `--sin-cache` | Fuerza una nueva extracción de metadatos. |
| `run [PLAN.json]` | Simula el plan; puede buscar planes en el directorio actual. |
| `run PLAN.json --ejecutar` | Ejecuta movimientos reales tras validación y confirmación. |
| `--dev` | Registra detalles en el log y mantiene la consola menos verbosa. |
| `--debug`, `-v`, `--verbose` | Muestra detalles de depuración en consola y log. |
| `--log-file RUTA` | Define el archivo base o el directorio para los logs. |

Las opciones globales de logging se indican antes del comando, por ejemplo:

```bash
mulita --debug scan "C:/fotos/origen"
mulita --log-file "C:/logs/mulita.log" plan "C:/fotos/origen" --destino "C:/fotos/organizadas"
```

## Caché y metadatos

El caché SQLite contiene metadatos extraídos y se almacena en el perfil local
del usuario:

- Windows: `%LOCALAPPDATA%/Mulita/.cache/metadatos.sqlite3`
- macOS: `~/Library/Caches/Mulita/.cache/metadatos.sqlite3`
- Linux y otros: `$XDG_CACHE_HOME/Mulita/.cache/metadatos.sqlite3` o
  `~/.cache/Mulita/.cache/metadatos.sqlite3`

Una entrada se reutiliza mientras coincidan el tamaño y la fecha de
modificación de alta precisión del archivo. `--sin-cache` omite la lectura y
la actualización del caché durante `scan` o `plan`; no cambia el cálculo de
destinos.

Para las fechas organizativas, los videos priorizan `MediaCreateDate`,
`CreateDate` y `DateTimeOriginal`; las imágenes priorizan `DateTimeOriginal`
y `CreateDate`. Si no hay una fecha válida, se utiliza `FileModifyDate`.

## Ejecución segura

Antes de ejecutar un plan sobre archivos reales:

1. Trabaja con una copia del origen y un destino de prueba separado.
2. Guarda el plan JSON fuera del origen y del destino.
3. Ejecuta `mulita run PLAN.json` y revisa las rutas y el resumen.
4. Usa `--ejecutar` solo después de verificar el plan y acepta la confirmación
   únicamente si las rutas mostradas son las esperadas.

Un plan representa el estado observado al generarlo. Si el origen cambia,
vuelve a crear y revisar el plan antes de ejecutarlo. El movimiento no es
atómico: ante un error, Mulita intenta revertir los archivos trasladados en
esa operación, pero una reversión fallida puede requerir recuperación manual.
Revisa el resultado y el reporte de auditoría después de cada ejecución real.
Si una operación no se completa, revisa el mensaje de error y el log; cuando
la reversión no sea posible, la CLI lo indica como recuperación manual
requerida.

## Estructura del proyecto

```text
src/mulita/
├── cli.py              # Comandos y presentación en terminal
├── scanner.py          # Recorrido y análisis de archivos
├── metadata.py         # Extracción de metadatos con ExifTool
├── metadata_cache.py   # Caché SQLite
├── dates.py            # Resolución y prioridad de fechas
├── associations.py     # Asociación de sidecars
├── planner.py          # Cálculo de destinos y colisiones
├── plan_storage.py     # Persistencia de planes y auditorías JSON
├── executor.py         # Validación y ejecución de movimientos
├── reporting.py        # Logs y registro de resultados
└── models.py           # Modelos y tipos del dominio

tests/                  # Pruebas automatizadas con pytest
```

## Desarrollo y pruebas

Instala las dependencias de desarrollo con uno de los comandos de instalación
anteriores. Ejecuta la suite de pruebas con:

```bash
python -m pytest
```

El proyecto configura Ruff y Black. Para revisar el código:

```bash
ruff check src tests
black --check src tests
```

## Documentación relacionada

- [CHANGELOG](CHANGELOG.md): cambios por versión.
- [TODO](TODO.md): trabajo pendiente.
- [Alcance del MVP](mulita_mvp_alcance.md): requisitos y alcance iniciales.
- [Licencia](LICENSE): licencia MIT.
