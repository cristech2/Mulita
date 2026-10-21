# Mulita

Mulita es una herramienta CLI para organizar fotos y videos de forma segura y trazable a partir de metadatos y reglas explícitas. Está pensada para recorrer directorios de origen, reconocer archivos de medios y generar un plan de organización sin sobrescribir datos ni decidir sin evidencia.

El proyecto sigue una lógica de MVP orientada a medios fotográficos y audiovisuales, con énfasis en:

- escaneo recursivo de carpetas;
- clasificación por tipo de archivo;
- lectura de metadatos con ExifTool;
- determinación de fecha de origen para organizar;
- asociación de sidecars como XMP;
- generación de un plan previo a la ejecución.

## Estado actual

Mulita está en desarrollo. Las versiones 0.1.0 y 0.2.0 establecieron el escaneo, la extracción de metadatos, la asociación de sidecars y la planificación con resolución de colisiones y exportación JSON. El siguiente hito es implementar la ejecución segura de ese plan; `run` todavía no mueve archivos.

## Requisitos

- Python 3.11+
- ExifTool instalado y disponible en PATH
- pip o uv para instalar el paquete

## Instalación

```bash
python -m pip install -e ".[dev]"
```

O con uv:

```bash
uv sync --group dev
```

## Uso

### 1) Escaneo de un directorio

```bash
mulita scan "C:/ruta/origen"
```

Este comando analiza el contenido del directorio y muestra un resumen de:

- imágenes detectadas;
- RAWs;
- videos;
- sidecars auxiliares;
- grupos principales de medios;
- archivos desconocidos o ambiguos.

### 2) Generación de plan

```bash
mulita plan "C:/ruta/origen" --destino "C:/ruta/destino" --salida "C:/ruta/plan.json"
```

Genera un plan de organización sin mover archivos. Permite revisar el resultado antes de que se implemente la ejecución real.

### 3) Ejecución (en desarrollo)

```bash
mulita run "C:/ruta/origen" --destino "C:/ruta/destino" --dry-run
```

El comando está registrado, pero todavía no ejecuta ni simula el flujo; su integración corresponde al Hito 5.

## Funcionalidades principales

### Implementado

- Escaneo recursivo y clasificación de extensiones configuradas como imagen, RAW, video, auxiliar o desconocido; omite rutas ocultas y el módulo permite excluir una ruta de destino cuando se indica.
- Extracción de fechas disponibles con ExifTool y selección de fecha según prioridad para fotos y videos. Si no hay una fecha utilizable, usa la fecha de modificación del archivo y la marca como respaldo.
- Asociación de archivos auxiliares (XMP, RRDATA y RREXIF) con medios de la misma carpeta. Los sidecars huérfanos o ambiguos y los archivos desconocidos se informan y se omiten del plan.
- Plan para organizar los medios por `AÑO/MES/DÍA/CATEGORÍA`, con sufijos incrementales para evitar colisiones y sidecars asociados al archivo principal.
- Validación de rutas de origen y destino; resumen de escaneo y plan en la CLI, exportación opcional del plan a JSON y registro de la operación.

### Pendiente para completar el MVP

- El módulo `executor.py` todavía no implementa movimientos.
- El comando `run` todavía no conecta escaneo, planificación y ejecución. La simulación y la ejecución real desde ese comando, con modo de simulación por defecto, quedan pendientes.
- Faltan las pruebas del ejecutor para validar movimientos reales y errores por operación con directorios temporales.

## Estructura del proyecto

```text
Mulita/
├── README.md
├── CHANGELOG.md
├── TODO.md
├── pyproject.toml
├── mulita_mvp_alcance.md
├── src/
│   └── mulita/
│       ├── __init__.py
│       ├── __main__.py
│       ├── associations.py
│       ├── cli.py
│       ├── dates.py
│       ├── executor.py
│       ├── metadata.py
│       ├── models.py
│       ├── planner.py
│       ├── reporting.py
│       └── scanner.py
├── tests/
│   ├── test_associations.py
│   ├── test_cli.py
│   ├── test_dates.py
│   ├── test_executor.py
│   ├── test_metadata.py
│   ├── test_planner.py
│   ├── test_reporting.py
│   └── test_scanner.py
└── uv.lock
```

## Convenciones de diseño

- La ejecución real todavía no está disponible; `--dry-run` será el modo predeterminado.
- No sobrescribir silenciosamente archivos existentes.
- Mantener decisiones explícitas y registradas.
- Priorizar metadatos confiables y dejar reliquias o casos ambiguos para revisión.
- Separar responsabilidades en módulos (escaneo, fechas, metadatos, planificación, ejecución, CLI).

## Roadmap

### Hito 5: ejecución segura (pendiente)

- Completar `src/mulita/executor.py` para mover archivos según el plan y crear los directorios de destino necesarios.
- Trasladar cada archivo principal junto con sus sidecars asociados.
- Manejar errores por operación sin abortar el resto del lote y preservar la integridad de los archivos.
- Conectar `run` al flujo escaneo → planificación → ejecución, manteniendo `--dry-run` como opción segura por defecto.
- Añadir pruebas del ejecutor con directorios temporales para verificar movimientos y errores.

## Participación e ideas

¡Toda colaboración es bienvenida! Puedes ayudar probando el MVP, reportando errores, sugiriendo mejoras o proponiendo ideas para organizar fotos y videos de forma más segura y clara.

Antes de proponer una funcionalidad, revisa el [alcance del MVP](mulita_mvp_alcance.md) y el [TODO](TODO.md) para ver qué está previsto y qué queda pendiente. Para compartir una propuesta, abre una issue describiendo el problema que resolvería, el comportamiento que esperas y, si es posible, un ejemplo de uso. Las ideas que amplíen el alcance actual también son bienvenidas: se pueden conversar antes de incorporarlas al roadmap.

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta [LICENSE](LICENSE) para ver sus términos.
