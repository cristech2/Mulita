# Mulita

Mulita es una herramienta CLI para organizar fotos, videos y proyectos de
edición de forma segura y trazable a partir de metadatos y reglas explícitas.
Está pensada para recorrer directorios de origen, reconocer archivos de medios
y proyectos, y generar un plan de organización sin sobrescribir datos ni
decidir sin evidencia.

El proyecto sigue una lógica de MVP orientada a medios fotográficos y audiovisuales, con énfasis en:

- escaneo recursivo de carpetas;
- clasificación de imágenes, RAW, videos, proyectos de edición y auxiliares;
- lectura de metadatos con ExifTool;
- determinación de fecha de origen para organizar;
- asociación de sidecars como XMP;
- generación de un plan previo a la ejecución.

## Estado actual

Mulita está en desarrollo. La versión 0.3.0 incorpora la persistencia de planes en JSON y su ejecución segura. El comando `run` simula los cambios por defecto; para mover archivos reales requiere la opción `--ejecutar` y confirmación explícita.

## Requisitos

- Python 3.11+
- ExifTool instalado y disponible en PATH
- pip o uv para instalar el paquete y sus dependencias Python (Typer y Rich)

## Instalación

```bash
python -m pip install -e ".[dev]"
```

O con uv:

```bash
uv sync --group dev
```

## Uso

Durante las tareas que pueden tardar, la CLI explica qué está haciendo. En
terminales interactivos muestra una barra de Rich con el avance medible y un
spinner mientras espera operaciones cuyo progreso interno no está disponible.
Al redirigir la salida, muestra los mensajes de etapa sin animación.

En `scan` y `plan`, el conteo aumenta mientras se descubren archivos; como el
total no se conoce hasta terminar el recorrido, esa etapa no muestra un
porcentaje. Los metadatos se conservan en un caché SQLite del perfil del
usuario y se reutilizan mientras coincidan el tamaño y la fecha de
modificación del archivo. Los archivos nuevos o modificados se procesan por
lotes de hasta 100 con ExifTool. `plan` siempre vuelve a calcular los destinos
y las colisiones. Usa `--sin-cache` en `scan` o `plan` para forzar una nueva
extracción. En `run --ejecutar`, el avance corresponde a operaciones
completadas, incluidas las fallidas u omitidas; no representa el progreso
interno de mover un archivo individual.

### 1) Escaneo de un directorio

```bash
mulita scan "C:/ruta/origen"
```

Para ignorar el caché persistente y volver a extraer los metadatos:

```bash
mulita scan "C:/ruta/origen" --sin-cache
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

Genera un plan de organización sin mover archivos. La opción `--salida` guarda
el plan en JSON para revisarlo o ejecutarlo después.
Si el archivo de salida ya existe, Mulita pregunta antes de reemplazarlo.
Si se rechaza la sobrescritura, se puede indicar otra ruta o cancelar; la
decisión ocurre antes del escaneo. No se permite guardar el plan dentro del
directorio de origen. La opción `--sin-cache` fuerza la extracción de
metadatos; el cálculo del plan siempre se realiza de nuevo.

### 3) Simulación del plan

```bash
mulita run "C:/ruta/plan.json"
```

`run` carga el plan indicado y muestra un resumen sin modificar archivos. Si no se indica un archivo, busca planes JSON válidos en el directorio actual y permite seleccionarlos.

### 4) Ejecución real

```bash
mulita run "C:/ruta/plan.json" --ejecutar
```

La ejecución real valida todas las operaciones del plan y prepara una ruta de
auditoría antes de solicitar confirmación y mover archivos. Si la ruta de
auditoría ya existe, se elige un nombre alternativo para conservar el reporte
anterior. Los destinos existentes no se sobrescriben; los errores se informan
por operación. `--dry-run` es el modo predeterminado.

## Prueba segura con una copia

No pruebes la ejecución real sobre tu biblioteca original. Prepara una copia
de prueba del origen y una carpeta de destino separada, preferentemente vacía.
Guarda también el archivo JSON del plan fuera de ambas carpetas.

1. Escanea la copia del origen:

   ```bash
   mulita scan "C:/pruebas/fotos-origen"
   ```

2. Genera y guarda un plan hacia el destino de prueba:

   ```bash
   mulita plan "C:/pruebas/fotos-origen" --destino "C:/pruebas/fotos-destino" --salida "C:/pruebas/plan.json"
   ```

3. Ejecuta primero la simulación, que es el modo predeterminado:

   ```bash
   mulita run "C:/pruebas/plan.json" --dry-run
   ```

   Revisa el resumen y el JSON; confirma que las rutas de origen y destino
   corresponden a las carpetas de prueba antes de continuar.

4. Solo cuando hayas revisado el plan, ejecuta sobre la copia:

   ```bash
   mulita run "C:/pruebas/plan.json" --ejecutar
   ```

   Lee la confirmación que muestra la CLI y cancela si las rutas no son las
   esperadas. Conserva intacta la biblioteca original y verifica el resultado
   de la prueba antes de usar Mulita con otros archivos.

## Limitaciones conocidas

- Un medio y sus sidecars se mueven en pasos separados. Si ocurre un error,
  Mulita intenta revertir los archivos que ya movió; si la reversión falla,
  informa que se requiere recuperación manual. El movimiento no es atómico.
- El plan es una fotografía de las rutas al momento de generarlo. Si cambian
  los archivos de origen o destino antes de `run`, vuelve a generar y revisar
  el plan.
- Si ExifTool no está disponible, Mulita continúa sin esos metadatos y puede
  usar la fecha de modificación del archivo como respaldo. Revisa el plan
  cuando las fechas sean importantes.
- La validación manual con una copia de una biblioteca de 20 GB y la suite de
  pruebas se realizaron en Windows. El flujo todavía debe validarse en Linux.
- El caché persistente reutiliza metadatos si tamaño y fecha de modificación
  no cambiaron; el plan se recalcula en cada ejecución.

## Funcionalidades principales

### Implementado

- Escaneo recursivo y clasificación de extensiones configuradas como imagen, RAW, video, proyecto de edición, auxiliar o desconocido; omite rutas ocultas y el módulo permite excluir una ruta de destino cuando se indica.
- Extracción de fechas disponibles con ExifTool y selección de fecha según prioridad para fotos y videos. Si no hay una fecha utilizable, usa la fecha de modificación del archivo y la marca como respaldo.
- Asociación de archivos auxiliares (XMP, RRDATA y RREXIF) con medios o
  proyectos de la misma carpeta. Los sidecars huérfanos o ambiguos y los
  archivos desconocidos se informan y se omiten del plan.
- Plan para organizar los medios y proyectos por `AÑO/MES/DÍA/CATEGORÍA`, con sufijos incrementales para evitar colisiones y sidecars asociados al archivo principal.
- Validación de rutas de origen y destino; resumen de escaneo y plan en la CLI, exportación y carga de planes JSON y registro de la operación.
- Ejecución de planes con simulación por defecto, confirmación antes de mover
  archivos y protección contra sobrescrituras. Verifica los traslados, intenta
  revertir operaciones fallidas y registra los resultados por archivo en el log
  y en reportes JSON de auditoría.

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
│       ├── metadata_cache.py
│       ├── cli.py
│       ├── dates.py
│       ├── executor.py
│       ├── metadata.py
│       ├── models.py
│       ├── plan_storage.py
│       ├── planner.py
│       ├── reporting.py
│       └── scanner.py
├── tests/
│   ├── test_associations.py
│   ├── test_metadata_cache.py
│   ├── test_cli.py
│   ├── test_dates.py
│   ├── test_executor.py
│   ├── test_metadata.py
│   ├── test_plan_storage.py
│   ├── test_planner.py
│   ├── test_reporting.py
│   └── test_scanner.py
└── uv.lock
```

## Convenciones de diseño

- La simulación es el modo predeterminado; la ejecución real requiere `--ejecutar` y confirmación.
- No sobrescribir silenciosamente archivos existentes.
- Mantener decisiones explícitas y registradas.
- Priorizar metadatos confiables y dejar reliquias o casos ambiguos para revisión.
- Separar responsabilidades en módulos (escaneo, fechas, metadatos, planificación, ejecución, CLI).

## Roadmap

La ejecución segura de planes prevista para el Hito 5 está implementada en la versión 0.3.0. Consulta el [TODO](TODO.md) para ver las tareas pendientes.

## Participación e ideas

¡Toda colaboración es bienvenida! Puedes ayudar probando el MVP, reportando errores, sugiriendo mejoras o proponiendo ideas para organizar fotos y videos de forma más segura y clara.

Antes de proponer una funcionalidad, revisa el [alcance del MVP](mulita_mvp_alcance.md) y el [TODO](TODO.md) para ver qué está previsto y qué queda pendiente. Para compartir una propuesta, abre una issue describiendo el problema que resolvería, el comportamiento que esperas y, si es posible, un ejemplo de uso. Las ideas que amplíen el alcance actual también son bienvenidas: se pueden conversar antes de incorporarlas al roadmap.

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta [LICENSE](LICENSE) para ver sus términos.
