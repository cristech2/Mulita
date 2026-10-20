# Mulita — Estado de Cumplimiento de Requisitos (TODO)

Este documento realiza un seguimiento detallado del estado de implementación de los Requisitos Funcionales (RF) y Requisitos No Funcionales (RNF) definidos en `mulita_mvp_alcance.md`.

---

## 📊 Resumen General
- **Estado global del MVP:** En desarrollo (Hito 0, Hito 1, Hito 2 e Hito 3 completados + Sistema de Observabilidad/Reportes).
- **Módulos activos:** `cli.py`, `scanner.py`, `metadata.py`, `dates.py`, `associations.py`, `models.py`, `reporting.py`.
- **Módulos pendientes:** `planner.py`, `executor.py`.

---

## 1. Requisitos Funcionales (RF)

| ID        | Requisito                   |     Estado      | Notas de Implementación                                                                                                                                                   |
| :-------- | :-------------------------- | :-------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **RF-01** | **Escaneo recursivo**       | `[x] Cumplido`  | Implementado en `scanner.escanear_directorio`. Excluye archivos/carpetas ocultas y el directorio destino si está anidado.                                                 |
| **RF-02** | **Formatos iniciales**      | `[x] Cumplido`  | Centralizado en `scanner.py` con conjuntos (`set`) para `IMAGEN`, `RAW`, `VIDEO` y `AUXILIAR` (XMP). Normaliza a minúsculas.                                              |
| **RF-03** | **Extracción de metadatos** | `[x] Cumplido`  | Implementado en `metadata.py`. Verificación de disponibilidad de ExifTool y extracción optimizada por lotes mediante archivo temporal (`-@ argfile`).                     |
| **RF-04** | **Resolución de fecha**     | `[x] Cumplido`  | Implementado en `dates.py`. Reglas de prioridad explícitas según categoría (`IMAGEN` vs `VIDEO`) con respaldo a `FileModifyDate`.                                         |
| **RF-05** | **Asociación de XMP**       | `[x] Cumplido`  | Implementado en `associations.py`. Detección por stem/nombre completo, aislamiento por carpeta contenedora y clasificación de `HUERFANO` y `AMBIGUO`.                     |
| **RF-06** | **Plan de organización**    | `[ ] Pendiente` | Pendiente de implementación en `planner.py`. Definirá la estructura `AÑO/MES/CATEGORÍA/`. `exportar_json` ya está listo en `reporting.py`.                                |
| **RF-07** | **Colisiones**              | `[ ] Pendiente` | Pendiente de implementación en `planner.py`. Manejo determinista de nombres duplicados mediante sufijos.                                                                  |
| **RF-08** | **Simulación**              |  `[/] Parcial`  | Interfaz y bandera `--dry-run`/`--ejecutar` definida en `cli.py`. Pendiente de integración completa con el ejecutor real.                                                 |
| **RF-09** | **Ejecución**               | `[ ] Pendiente` | Pendiente de implementación en `executor.py`. Movimiento real seguro con validación individual de operaciones.                                                            |
| **RF-10** | **Registros y resumen**     | `[x] Cumplido`  | Implementado en `reporting.py`. Resumen de escaneo integrado con contadores de grupos principales, sidecars asociados, huérfanos y ambiguos.                              |
| **RF-11** | **Validación de rutas**     |  `[/] Parcial`  | Validado por Typer en CLI (existencia de origen) y prevención de recursividad del destino en `scanner.py`. Falta validación completa origen==destino en planner/executor. |
| **RF-12** | **CLI**                     |  `[/] Parcial`  | Comandos `scan`, `plan` y `run` declarados con Typer en `cli.py`. Soporte para `--dev`, `--debug` y `--log-file`. `scan` 100% funcional con análisis completo de medios.  |

---

## 2. Requisitos No Funcionales (RNF)

| ID         | Requisito                 |     Estado      | Notas de Implementación                                                                                                                                                         |
| :--------- | :------------------------ | :-------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **RNF-01** | **Multiplataforma**       | `[x] Cumplido`  | Desarrollo basado exclusivamente en `pathlib.Path` de Python 3.11+. Probado e integrado en entorno Windows/Linux con soporte `as_posix()` para JSON.                            |
| **RNF-02** | **Integridad**            |  `[/] Parcial`  | El escaneo y análisis no modifican archivos. Pendiente garantizar en movimiento real (`executor.py`).                                                                           |
| **RNF-03** | **Determinismo**          | `[ ] Pendiente` | Depende de la implementación de `planner.py`.                                                                                                                                   |
| **RNF-04** | **Resiliencia**           | `[x] Cumplido`  | El escáner y la extracción de metadatos toleran fallos, formatos no soportados o ausencia de ExifTool sin detener la ejecución.                                                 |
| **RNF-05** | **Rendimiento**           | `[x] Cumplido`  | Extracción de metadatos por lotes con ExifTool mediante `argfile` para evitar sobrecarga por proceso individual.                                                                |
| **RNF-06** | **Mantenibilidad**        | `[x] Cumplido`  | Módulos desacoplados (`scanner`, `metadata`, `dates`, `associations`, `models`, `reporting`, `cli`). Tipado estricto con `-> None` en pruebas y dataclasses explícitas.         |
| **RNF-07** | **Observabilidad**        | `[x] Cumplido`  | Trazabilidad completa con `logging`, logs limpios en consola y detallados en archivo con timestamps. Desacople mediante banderas `--dev` y `--debug`.                           |
| **RNF-08** | **Pruebas**               | `[x] Cumplido`  | Tests unitarios e integración implementados en `tests/` (`test_cli`, `test_dates`, `test_metadata`, `test_scanner`, `test_associations`) usando `pytest` y mocks para ExifTool. |
| **RNF-09** | **Dependencias mínimas**  | `[x] Cumplido`  | Proyecto liviano (`typer` como dependencia Python). Verificación dinámica de la binaria ExifTool en el PATH del sistema.                                                        |
| **RNF-10** | **Errores comprensibles** | `[x] Cumplido`  | Mensajes claros en consola con advertencias sobre falta de ExifTool y códigos de salida correctos en Typer.                                                                     |

---

## 📌 Próximos Pasos (Hito 4: Plan y Simulación)

1. **Crear `src/mulita/planner.py` (RF-06, RF-07, RF-11):**
   - [ ] Diseñar la estructura de carpetas destino: `AÑO/MES/CATEGORÍA/`.
   - [ ] Garantizar que los sidecars sigan al archivo principal en la misma estructura de carpetas.
   - [ ] Implementar resolución determinista de colisiones de nombres con sufijos numéricos.
   - [ ] Generar la estructura de datos del plan de organización exportable a JSON mediante `reporting.exportar_json`.
2. **Escribir pruebas unitarias:**
   - [ ] Habilitar y completar las pruebas en `tests/test_planner.py`.