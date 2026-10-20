# Mulita — Estado de Cumplimiento de Requisitos (TODO)

Este documento realiza un seguimiento detallado del estado de implementación de los Requisitos Funcionales (RF) y Requisitos No Funcionales (RNF) definidos en `mulita_mvp_alcance.md`.

---

## 📊 Resumen General
- **Estado global del MVP:** En desarrollo (Hito 0 e Hito 1 completados + Sistema de Observabilidad/Reportes).
- **Módulos activos:** `cli.py`, `scanner.py`, `reporting.py`.
- **Módulos pendientes:** `metadata.py`, `dates.py`, `associations.py`, `planner.py`, `executor.py`.

---

## 1. Requisitos Funcionales (RF)

| ID | Requisito | Estado | Notas de Implementación |
| :--- | :--- | :---: | :--- |
| **RF-01** | **Escaneo recursivo** | `[x] Cumplido` | Implementado en `scanner.escanear_directorio`. Excluye archivos/carpetas ocultas y el directorio destino si está anidado. |
| **RF-02** | **Formatos iniciales** | `[x] Cumplido` | Centralizado en `scanner.py` con conjuntos (`set`) para `IMAGEN`, `RAW`, `VIDEO` y `AUXILIAR` (XMP). Normaliza a minúsculas. |
| **RF-03** | **Extracción de metadatos** | `[ ] Pendiente` | Pendiente de implementación en `metadata.py`. Requerirá integración externa con ExifTool. |
| **RF-04** | **Resolución de fecha** | `[ ] Pendiente` | Pendiente de implementación en `dates.py`. Requerirá lógica de priorización de fechas y fechas de respaldo (*fallback*). |
| **RF-05** | **Asociación de XMP** | `[ ] Pendiente` | Pendiente de implementación en `associations.py`. Requerirá detección de sidecars y detección de ambigüedades. |
| **RF-06** | **Plan de organización** | `[ ] Pendiente` | Pendiente de implementación en `planner.py`. Definirá la estructura `AÑO/MES/CATEGORÍA/`. `exportar_json` ya está listo en `reporting.py`. |
| **RF-07** | **Colisiones** | `[ ] Pendiente` | Pendiente de implementación en `planner.py`. Manejo determinista de nombres duplicados mediante sufijos. |
| **RF-08** | **Simulación** | `[/] Parcial` | Interfaz y bandera `--dry-run`/`--ejecutar` definida en `cli.py`. Pendiente de integración completa con el ejecutor real. |
| **RF-09** | **Ejecución** | `[ ] Pendiente` | Pendiente de implementación en `executor.py`. Movimiento real seguro con validación individual de operaciones. |
| **RF-10** | **Registros y resumen** | `[x] Cumplido` | Implementado en `reporting.py`. Formato con timestamp, archivo `.log` dedicado, niveles diferenciados (Info/Debug), rotación a máximo 5 archivos y resumen en pantalla. |
| **RF-11** | **Validación de rutas** | `[/] Parcial` | Validado por Typer en CLI (existencia de origen) y prevención de recursividad del destino en `scanner.py`. Falta validación completa origen==destino en planner/executor. |
| **RF-12** | **CLI** | `[/] Parcial` | Comandos `scan`, `plan` y `run` declarados con Typer en `cli.py`. Soporte para `--verbose` y `--log-file`. `scan` 100% funcional. |

---

## 2. Requisitos No Funcionales (RNF)

| ID | Requisito | Estado | Notas de Implementación |
| :--- | :--- | :---: | :--- |
| **RNF-01** | **Multiplataforma** | `[x] Cumplido` | Desarrollo basado exclusivamente en `pathlib.Path` de Python 3.11+. Probado e integrado en entorno Windows/Linux sin comandos de OS. |
| **RNF-02** | **Integridad** | `[/] Parcial` | El escaneo no modifica archivos. Pendiente garantizar en movimiento real (`executor.py`). |
| **RNF-03** | **Determinismo** | `[ ] Pendiente` | Depende de la implementación de `planner.py`. |
| **RNF-04** | **Resiliencia** | `[/] Parcial` | El escáner tolera archivos desconocidos o sin permisos sin detener la ejecución. |
| **RNF-05** | **Rendimiento** | `[x] Cumplido` | `scanner.py` evalúa solo la metadata del sistema de archivos (`rglob`, `suffix`) sin cargar contenido binario en memoria. |
| **RNF-06** | **Mantenibilidad** | `[x] Cumplido` | Módulos desacoplados (`scanner`, `reporting`, `cli`). La CLI no contiene reglas de negocio. Tipado estricto con Python 3.11 (`dict`, `list`, `Path \| None`). |
| **RNF-07** | **Observabilidad** | `[x] Cumplido` | Trazabilidad completa con `logging`, logs limpios en consola y detallados en archivo con timestamps. |
| **RNF-08** | **Pruebas** | `[x] Cumplido` | Tests unitarios e integración implementados en `tests/` usando `pytest` y `tmp_path` (fixtures de carpetas temporales). |
| **RNF-09** | **Dependencias mínimas** | `[/] Parcial` | Proyecto liviano (`typer` como única dependencia principal en runtime). Pendiente verificación de presencia de ExifTool. |
| **RNF-10** | **Errores comprensibles** | `[x] Cumplido` | Mensajes claros en consola con códigos de salida correctos en Typer. |

---

## 📌 Próximos Pasos (Hito 2: Metadatos y Fechas)

1. **Crear `src/mulita/metadata.py`:**
   - [ ] Implementar la función de detección de disponibilidad de ExifTool en el sistema (RNF-09).
   - [ ] Diseñar la lectura de metadatos por lotes con ExifTool.
   - [ ] Normalizar la extracción de `DateTimeOriginal`, `CreateDate`, `MediaCreateDate` y `FileModifyDate`.
2. **Crear `src/mulita/dates.py`:**
   - [ ] Definir la política explícita para resolver qué fecha usar según la categoría (`IMAGEN` vs `VIDEO`).
   - [ ] Documentar el origen/criterio de la fecha seleccionada.
3. **Escribir pruebas unitarias:**
   - [ ] Pruebas en `tests/test_metadata.py` y `tests/test_dates.py`.