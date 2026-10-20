# Mulita — Estado de Cumplimiento de Requisitos (TODO)

Este documento realiza un seguimiento detallado del estado de implementación de los Requisitos Funcionales (RF) y Requisitos No Funcionales (RNF) definidos en `mulita_mvp_alcance.md`.

---

## 📊 Resumen General
- **Estado global del MVP:** En desarrollo (Hito 0, Hito 1 e Hito 2 completados + Sistema de Observabilidad/Reportes).
- **Módulos activos:** `cli.py`, `scanner.py`, `metadata.py`, `dates.py`, `reporting.py`.
- **Módulos pendientes:** `associations.py`, `planner.py`, `executor.py`.

---

## 1. Requisitos Funcionales (RF)

| ID        | Requisito                   |     Estado      | Notas de Implementación                                                                                                                                                     |
| :-------- | :-------------------------- | :-------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **RF-01** | **Escaneo recursivo**       | `[x] Cumplido`  | Implementado en `scanner.escanear_directorio`. Excluye archivos/carpetas ocultas y el directorio destino si está anidado.                                                   |
| **RF-02** | **Formatos iniciales**      | `[x] Cumplido`  | Centralizado en `scanner.py` con conjuntos (`set`) para `IMAGEN`, `RAW`, `VIDEO` y `AUXILIAR` (XMP). Normaliza a minúsculas.                                                |
| **RF-03** | **Extracción de metadatos** | `[x] Cumplido`  | Implementado en `metadata.py`. Verificación de disponibilidad de ExifTool y extracción optimizada por lotes mediante archivo temporal (`-@ argfile`).                       |
| **RF-04** | **Resolución de fecha**     | `[x] Cumplido`  | Implementado en `dates.py`. Reglas de prioridad explícitas según categoría (`IMAGEN` vs `VIDEO`) con respaldo a `FileModifyDate`.                                           |
| **RF-05** | **Asociación de XMP**       | `[ ] Pendiente` | Pendiente de implementación en `associations.py`. Requerirá detección de sidecars y detección de ambigüedades.                                                              |
| **RF-06** | **Plan de organización**    | `[ ] Pendiente` | Pendiente de implementación en `planner.py`. Definirá la estructura `AÑO/MES/CATEGORÍA/`. `exportar_json` ya está listo en `reporting.py`.                                  |
| **RF-07** | **Colisiones**              | `[ ] Pendiente` | Pendiente de implementación en `planner.py`. Manejo determinista de nombres duplicados mediante sufijos.                                                                    |
| **RF-08** | **Simulación**              |  `[/] Parcial`  | Interfaz y bandera `--dry-run`/`--ejecutar` definida en `cli.py`. Pendiente de integración completa con el ejecutor real.                                                   |
| **RF-09** | **Ejecución**               | `[ ] Pendiente` | Pendiente de implementación en `executor.py`. Movimiento real seguro con validación individual de operaciones.                                                              |
| **RF-10** | **Registros y resumen**     | `[x] Cumplido`  | Implementado en `reporting.py`. Formato con timestamp, archivo `.log` dedicado, niveles diferenciados (Info/Debug), rotación a máximo 5 archivos y resumen en pantalla.     |
| **RF-11** | **Validación de rutas**     |  `[/] Parcial`  | Validado por Typer en CLI (existencia de origen) y prevención de recursividad del destino en `scanner.py`. Falta validación completa origen==destino en planner/executor.   |
| **RF-12** | **CLI**                     |  `[/] Parcial`  | Comandos `scan`, `plan` y `run` declarados con Typer en `cli.py`. Soporte para `--dev`, `--debug` y `--log-file`. `scan` 100% funcional con análisis de fechas y metadatos. |

---

## 2. Requisitos No Funcionales (RNF)

| ID         | Requisito                 |     Estado      | Notas de Implementación                                                                                                                                                            |
| :--------- | :------------------------ | :-------------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **RNF-01** | **Multiplataforma**       | `[x] Cumplido`  | Desarrollo basado exclusivamente en `pathlib.Path` de Python 3.11+. Probado e integrado en entorno Windows/Linux sin comandos de OS.                                               |
| **RNF-02** | **Integridad**            |  `[/] Parcial`  | El escaneo no modifica archivos. Pendiente garantizar en movimiento real (`executor.py`).                                                                                          |
| **RNF-03** | **Determinismo**          | `[ ] Pendiente` | Depende de la implementación de `planner.py`.                                                                                                                                      |
| **RNF-04** | **Resiliencia**           | `[x] Cumplido`  | El escáner y la extracción de metadatos toleran fallos, formatos no soportados o ausencia de ExifTool sin detener la ejecución.                                                    |
| **RNF-05** | **Rendimiento**           | `[x] Cumplido`  | Extracción de metadatos por lotes con ExifTool mediante `argfile` para evitar sobrecarga por proceso individual.                                                                   |
| **RNF-06** | **Mantenibilidad**        | `[x] Cumplido`  | Módulos desacoplados (`scanner`, `metadata`, `dates`, `reporting`, `cli`). La CLI no contiene reglas de negocio. Tipado estricto con Python 3.11 (`dict`, `list`, `Path \| None`). |
| **RNF-07** | **Observabilidad**        | `[x] Cumplido`  | Trazabilidad completa con `logging`, logs limpios en consola y detallados en archivo con timestamps. Desacople mediante banderas `--dev` y `--debug`.                              |
| **RNF-08** | **Pruebas**               | `[x] Cumplido`  | Tests unitarios e integración implementados en `tests/` (`test_cli`, `test_dates`, `test_metadata`, `test_scanner`) usando `pytest` y mocks para ExifTool.                         |
| **RNF-09** | **Dependencias mínimas**  | `[x] Cumplido`  | Proyecto liviano (`typer` como dependencia Python). Verificación dinámica de la binaria ExifTool en el PATH del sistema.                                                           |
| **RNF-10** | **Errores comprensibles** | `[x] Cumplido`  | Mensajes claros en consola con advertencias sobre falta de ExifTool y códigos de salida correctos en Typer.                                                                        |

---

## 📌 Próximos Pasos (Hito 3: Asociación de Sidecars y Planificación)

1. **Crear `src/mulita/associations.py` (RF-05):**
   - [ ] Implementar vinculación de archivos `.xmp` / `.rrdata` con sus archivos principales.
   - [ ] Gestionar ambigüedades cuando existen múltiples sidecars o coincidencia parcial de nombres.
2. **Crear `src/mulita/planner.py` (RF-06, RF-07, RF-11):**
   - [ ] Diseñar la estructura de carpetas destino: `AÑO/MES/CATEGORÍA/`.
   - [ ] Implementar resolución determinista de colisiones de nombres con sufijos numéricos.
   - [ ] Generar la estructura de datos del plan de organización exportable a JSON.
3. **Escribir pruebas unitarias:**
   - [ ] Pruebas en `tests/test_associations.py` y `tests/test_planner.py`.