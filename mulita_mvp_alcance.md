# Mulita — Alcance del MVP inicial

**Estado:** propuesta inicial  
**Producto:** organizador de fotos y videos  
**Interfaz inicial:** CLI multiplataforma  
**Objetivo:** validar la lógica de análisis, planificación y organización en Python, sin depender de scripts específicos de un sistema operativo.

## 1. Objetivo y principios

Mulita analizará una carpeta de medios y propondrá una estructura de destino basada en metadatos y reglas explícitas de respaldo.

Principios:
- **Multiplataforma:** sin dependencia de PowerShell, Bash ni comandos propios de un sistema.
- **Seguro por defecto:** simulación antes de modificar archivos; nunca sobrescribir silenciosamente.
- **Trazable:** registrar decisiones, operaciones y errores.
- **Conservador:** ante fechas o asociaciones ambiguas, informar en lugar de adivinar.
- **Separación de responsabilidades:** escaneo, metadatos, fechas, asociaciones, planificación y ejecución son módulos diferenciados.

El MVP no incluye interfaz gráfica, base de datos persistente ni análisis visual mediante IA.

## 2. Requisitos funcionales

### RF-01 — Escaneo recursivo
Recorrer el origen y detectar archivos compatibles en sus subdirectorios, sin volver a incluir accidentalmente el destino.

### RF-02 — Formatos iniciales
Clasificar extensiones configuradas:
- **Imágenes:** JPG/JPEG, PNG, TIFF/TIF, af.
- **RAW:** CR2, CR3, NEF, ARW, DNG, ORF, RW2, RAF.
- **Video:** MP4, MOV, M4V, AVI, MKV, 3GP.
- **Auxiliares:** XMP, rrdata, rrexif
La lista debe centralizarse y poder ampliarse. La disponibilidad de metadatos varía según formato y archivo.

### RF-03 — Extracción de metadatos
Usar ExifTool para leer metadatos disponibles, incluyendo según el tipo de archivo:
- `DateTimeOriginal`
- `CreateDate`
- `MediaCreateDate` y campos equivalentes para video
- `FileModifyDate` como posible respaldo

Conservar el valor leído, la fecha elegida y la regla que justificó la decisión.

### RF-04 — Resolución de fecha
Aplicar una política explícita y testeable para seleccionar la fecha de organización. La prioridad puede variar entre fotos y videos. Si no hay una fecha de captura utilizable, usar una alternativa configurable —inicialmente, la modificación del archivo— y marcarla como respaldo.

### RF-05 — Asociación de XMP
Detectar y asociar XMP antes de mover archivos.
- Considerar nombre, ubicación original y extensiones en mayúsculas/minúsculas.
- No confundir archivos con igual nombre en carpetas distintas.
- No elegir automáticamente entre varios candidatos plausibles.
- Informar XMP huérfanos o ambiguos y dejarlos sin mover en el MVP salvo que exista una regla segura.

### RF-06 — Plan de organización
Generar por archivo un plan con origen, destino, categoría, fecha seleccionada y fuente, sidecars asociados, acción prevista y advertencias. La estructura inicial será `AÑO/MES/DIA/CATEGORÍA/`, por ejemplo `2026/10/20/RAW/`. Conservar los nombres originales salvo que haya colisiones.

### RF-07 — Colisiones
Detectar archivos que producirían el mismo destino o que ya existan allí. No sobrescribir en silencio. Resolver con sufijo incremental determinista o marcar el caso para revisión. Los sidecars deben seguir al archivo principal sin perder su asociación. 

### RF-08 — Simulación
El modo de simulación será el comportamiento predeterminado y no modificará archivos.

### RF-09 — Ejecución
Permitir ejecutar el plan explícitamente. Verificar cada operación y registrar fallos por archivo para que un error no detenga innecesariamente todo el lote.

### RF-10 — Registros y resumen
Generar logs con fecha/hora, archivo, operación y resultado. Mostrar cantidades detectadas, organizables, omitidas, ambiguas, procesadas y fallidas.

### RF-11 — Validación de rutas
Comprobar que el origen existe y que origen y destino no sean iguales ni estén anidados de forma que provoquen un recorrido recursivo accidental.

### RF-12 — CLI
Implementar comandos con Typer:
- `scan`: inspeccionar archivos y resumir resultados.
- `plan`: generar y mostrar o guardar un plan sin modificar archivos.
- `run`: ejecutar la organización de forma explícita.
- Opciones previstas: `--destino` para la carpeta de destino, `--ejecutar` para confirmar la ejecucion real, `--plan` para pasar la direccion del plan.

La convención final de confirmación debe ser única y documentada; ejecutar cambios no debe confundirse con una simulación.

## 3. Requisitos no funcionales

- **RNF-01 Multiplataforma:** funcionar en Windows y Linux con Python y ExifTool instalados.
- **RNF-02 Integridad:** no borrar ni sobrescribir archivos silenciosamente; comprobar el resultado antes de dar una operación por exitosa.
- **RNF-03 Determinismo:** la misma entrada y configuración deben producir el mismo plan y resolver colisiones de forma predecible.
- **RNF-04 Resiliencia:** archivos corruptos, sin metadatos o con datos inesperados no deben detener todo el lote si se puede continuar de forma segura.
- **RNF-05 Rendimiento:** recorrer colecciones grandes sin cargar el contenido binario de todos los archivos en memoria; usar consultas por lotes cuando convenga. y cachar resultados de scan para no repetir operaciones costosas en la misma ejecución. 
- **RNF-06 Mantenibilidad:** módulos pequeños y testeables; la CLI no debe contener reglas de negocio. Cada modulo debe tener una responsabilidad clara y documentada.
- **RNF-07 Observabilidad:** logs útiles para comprender y reproducir fallos.
- **RNF-08 Pruebas:** cubrir fechas, XMP, colisiones, rutas y ejecución con carpetas temporales, nunca con la biblioteca personal real. Seguir buenas prácticas de pytest y no depender de la ejecución en un orden específico.
- **RNF-09 Dependencias mínimas:** pocas dependencias Python; detectar si falta ExifTool y explicar cómo instalarlo.
- **RNF-10 Errores comprensibles:** mensajes accionables y códigos de salida apropiados para la CLI.

## 4. Bloque tecnológico mínimo

| Área             | Tecnología                                      | Uso                                               |
| ---------------- | ----------------------------------------------- | ------------------------------------------------- |
| Lenguaje         | Python 3.11+                                    | Lógica multiplataforma                            |
| CLI              | **Typer** (Sebastián Ramírez, `tiangolo/typer`) | Comandos, argumentos, opciones y ayuda automática |
| Metadatos        | ExifTool                                        | Lectura de metadatos de fotos y videos            |
| Archivos         | `pathlib`, `shutil`, `os`                       | Rutas, recorrido y operaciones                    |
| Modelos          | `dataclasses`, `enum`, `typing`                 | Datos tipados del análisis y plan                 |
| Logs             | `logging`                                       | Registro de operaciones y errores                 |
| Plan serializado | `json` estándar                                 | Guardar y revisar planes                          |
| Pruebas          | `pytest`                                        | Pruebas unitarias e integración                   |
| Empaquetado      | `pyproject.toml`                                | Dependencias y comando instalable                 |

### Pospuesto deliberadamente
- **SQLite:** no es necesaria si el plan puede generarse en memoria y guardarse en JSON. Evaluarla para indexación persistente o análisis incremental.
- **Pillow:** posponer hasta necesitar miniaturas, dimensiones o análisis de imagen.
- **FFmpeg:** posponer hasta necesitar inspección o transformación audiovisual adicional.
- **Hashing:** posponer la detección de duplicados por contenido hasta que sea un requisito concreto.
- **GUI, nube e IA:** fuera del MVP.

ExifTool se invocará como proceso externo desde Python, sin construir comandos de shell con rutas interpoladas. La aplicación debe capturar salida, errores y código de retorno.

## 5. Estructura del proyecto

```text
mulita/
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── LICENSE
├── uv.lock
├── mulita_mvp_alcance.md
├── TODO.md
├── src/
│   └── mulita/
│       ├── __init__.py        # Inicialización del paquete
|       ├── __main__.py        # Punto de entrada para `python -m mulita`
│       ├── associations.py    # Asociación de XMP y sidecars
│       ├── cli.py             # Comandos Typer y presentación
│       ├── dates.py           # Política de fechas
│       ├── executor.py        # Ejecución controlada
│       ├── metadata.py        # ExifTool y normalización
|       ├── models.py          # Clases de datos tipadas
|       ├── plan_storage.py      # Guardar y cargar planes en JSON
│       ├── planner.py         # Destinos, colisiones y plan
│       ├── reporting.py       # Logs, resúmenes y JSON
│       └── scanner.py         # Recorrido y clasificación
└── tests/
    ├── test_associations.py   # Pruebas de asociaciones
    ├── test_cli.py            # Pruebas de CLI
    ├── test_dates.py          # Pruebas de fechas
    ├── test_executor.py       # Pruebas de ejecución
    ├── test_metadata.py       # Pruebas de metadatos
    ├── test_plan_storage.py   # Pruebas de plan_storage
    ├── test_planner.py        # Pruebas de planificación
    ├── test_reporting.py       # Pruebas de reporting
    └── test_scanner.py        # Pruebas de escaneo

```

### Responsabilidad de los módulos
- `associations.py`: asociar sidecars XMP y otros auxiliares a archivos principales.
- `cli.py`: comandos Typer, argumentos y ayuda.
- `dates.py`: política de selección de fecha y fuente.
- `executor.py`: ejecutar el plan de forma segura, registrar errores.
- `metadata.py`: invocar ExifTool y normalizar metadatos.
- `models.py`: clases de datos tipadas para archivos, planes y resultados.
- `plan_storage.py`: guardar y cargar planes en JSON.
- `planner.py`: generar destinos, resolver colisiones y construir el plan.
- `reporting.py`: registrar operaciones, errores y generar resúmenes.
- `scanner.py`: recorrer carpetas, clasificar extensiones y validar rutas.

Esta estructura orienta el diseño, pero no obliga a crear todos los módulos desde el primer día. Se puede empezar por lo esencial y dividir cuando la lógica lo justifique.

## 6. Hitos por etapas

Estimaciones orientativas para una persona trabajando a tiempo parcial. Cada etapa termina con un resultado verificable.

### Hito 0 — Preparar entorno
**Estimación:** medio día
- Crear el proyecto y `pyproject.toml`.
- Configurar Typer y pytest.
- Documentar la instalación y detección de ExifTool.
- Crear una pequeña carpeta de muestras de prueba.

**Salida:** `mulita --help` funciona y se detecta si ExifTool está instalado.

### Hito 1 — Escaneo y clasificación
**Estimación:** 0,5–1 día
- Recorrer carpetas recursivamente.
- Clasificar extensiones y listar desconocidos.
- Validar las rutas de origen y destino.

**Salida:** `scan` informa de manera estable qué archivos encontró sin modificarlos.

### Hito 2 — Metadatos y fechas
**Estimación:** 1–2 días
- Consultar ExifTool.
- Definir prioridades de fecha para fotos y videos.
- Implementar el respaldo de fecha de modificación.
- Marcar fuente y fiabilidad de la fecha elegida.

**Salida:** cada decisión de fecha se puede explicar y está cubierta por pruebas.

### Hito 3 — Asociaciones XMP
**Estimación:** 1–2 días
- Asociar sidecars antes de mover nada.
- Cubrir mayúsculas/minúsculas y nombres repetidos en carpetas diferentes.
- Identificar huérfanos y ambigüedades.

**Salida:** las pruebas no producen asociaciones cruzadas ni pierden XMP.

### Hito 4 — Plan y simulación
**Estimación:** 1–2 días
- Construir la estructura `AÑO/MES/CATEGORÍA`.
- Resolver colisiones de forma determinista.
- Mostrar resumen y exportar JSON.
- Mantener la simulación como modo predeterminado.

**Salida:** revisar el plan completo sin cambiar archivos.

### Hito 5 — Ejecución segura
**Estimación:** 1–2 días
- Ejecutar movimientos autorizados.
- Mantener juntos medios y sidecars asociados.
- Registrar resultado por operación y gestionar errores.
- Probar una segunda ejecución y destinos existentes.

**Salida:** una carpeta de prueba queda organizada sin sobrescrituras silenciosas ni pérdida de archivos.

### Hito 6 — Validación del MVP
**Estimación:** 1–2 días
- Completar pruebas unitarias y de integración.
- Probar lotes pequeños y medianos en Windows y Linux.
- Revisar logs, mensajes de error y documentación.
- Documentar limitaciones y recuperación ante fallos.

**Salida:** el MVP se puede probar sobre una copia de una biblioteca real, con resultados revisables y repetibles.

**Estimación total:** aproximadamente **5–10 días de trabajo**. La variedad de metadatos y los casos especiales de XMP son las principales fuentes de incertidumbre.

## 7. Comandos previstos

```bash
# Inspeccionar una carpeta
mulita scan ./Fotos

# Generar y mostrar un plan sin modificar archivos
mulita plan ./Fotos --destino ./Fotos_Ordenadas

# Guardar el plan para revisarlo
mulita plan ./Fotos --destino ./Fotos_Ordenadas --salida plan.json

# Ejecutar el plan tras revisarlo
mulita run ./Fotos --destino ./Fotos_Ordenadas

# Simular explícitamente
mulita run ./Fotos --destino ./Fotos_Ordenadas --dry-run
```

Los ejemplos son una propuesta de interfaz, no comandos implementados. Durante el desarrollo se elegirá una convención clara para confirmar la ejecución real.

## 8. Criterios globales de aceptación

- [ ] Escanea recursivamente los formatos definidos.
- [ ] Informa archivos desconocidos o problemáticos.
- [ ] Selecciona fechas consistentemente y registra su origen.
- [ ] Asocia XMP sin confundir nombres repetidos en carpetas diferentes.
- [ ] Informa XMP huérfanos o ambiguos.
- [ ] Genera un plan reproducible y revisable.
- [ ] La simulación no modifica archivos.
- [ ] La ejecución no sobrescribe silenciosamente.
- [ ] Los errores individuales quedan registrados.
- [ ] Hay pruebas para fechas, asociaciones, colisiones y errores.
- [ ] Se valida en Windows y Linux.

## 9. Fuera del alcance del MVP

- Detección de fotos borrosas, memes o contenido mediante IA.
- Detección de duplicados por similitud visual o hash.
- Miniaturas, visor o edición de metadatos.
- Base de datos e indexación incremental.
- Interfaz gráfica o servidor web.
- Sincronización en la nube.
- Plantillas avanzadas de renombrado.
- Gestión completa de catálogos de Lightroom, Darktable u otras aplicaciones.

La prioridad del MVP es validar el núcleo: **encontrar archivos, interpretar metadatos, asociar auxiliares, proponer destinos y ejecutar el plan con seguridad**.
