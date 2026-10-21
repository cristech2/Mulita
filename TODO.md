## Mulita: estado de requisitos y tareas pendientes

Seguimiento de los requisitos funcionales (RF) y no funcionales (RNF)
definidos en [mulita_mvp_alcance.md](mulita_mvp_alcance.md).

## Resumen

- **Estado del MVP:** En desarrollo. Los hitos 0 a 5 están implementados y
  el flujo se probó de extremo a extremo en Windows con una copia de una
  biblioteca real de 20 GB. El Hito 6 sigue pendiente de validación en Linux
  y de cerrar las brechas técnicas anotadas abajo.
- **Módulos principales:** `cli.py`, `scanner.py`, `metadata.py`,
  `dates.py`, `associations.py`, `planner.py`, `plan_storage.py`,
  `executor.py`, `models.py` y `reporting.py`.
- **Validación manual registrada:** `scan`, `plan` y `run` funcionaron según
  lo esperado en Windows. El plan adjunto contiene 1.893 operaciones
  principales y 171 pares de sidecars; el árbol antes/después muestra la
  organización resultante.
- **Próximo objetivo:** repetir la validación en Linux y cerrar las brechas de
  rendimiento, dependencias y errores comprensibles.

## Requisitos funcionales

| ID        | Requisito               | Estado         | Notas                                                                                                                                                                                                                                     |
| --------- | ----------------------- | -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **RF-01** | Escaneo recursivo       | `[x] Cumplido` | `scanner.py` recorre el origen y omite elementos ocultos; admite excluir la ruta de destino.                                                                                                                                              |
| **RF-02** | Formatos iniciales      | `[x] Cumplido` | Clasifica imágenes, RAW, videos y auxiliares; normaliza las extensiones.                                                                                                                                                                  |
| **RF-03** | Extracción de metadatos | `[x] Cumplido` | Usa ExifTool y procesa metadatos por lotes.                                                                                                                                                                                               |
| **RF-04** | Resolución de fecha     | `[x] Cumplido` | Aplica prioridades por categoría y recurre a la fecha de modificación cuando es necesario.                                                                                                                                                |
| **RF-05** | Asociación de sidecars  | `[x] Cumplido` | Asocia XMP, RRDATA y RREXIF; identifica sidecars huérfanos o ambiguos.                                                                                                                                                                    |
| **RF-06** | Plan de organización    | `[x] Cumplido` | `planner.py` calcula operaciones y `plan_storage.py` permite exportar y cargar el plan JSON.                                                                                                                                              |
| **RF-07** | Colisiones              | `[x] Cumplido` | El planificador ordena los grupos y sidecars de forma estable antes de asignar destinos y sufijos incrementales; hay pruebas con distinto orden de entrada.                                                                                |
| **RF-08** | Simulación              | `[x] Cumplido` | `plan` no mueve archivos; `run` simula por defecto y no modifica el sistema de archivos.                                                                                                                                                  |
| **RF-09** | Ejecución               | `[x] Cumplido` | `executor.py` verifica cada traslado, intenta revertir los movimientos de una operación fallida y señala los casos que requieren recuperación manual. El lote continúa ante fallos.                                                      |
| **RF-10** | Registros y resumen     | `[x] Cumplido` | La CLI presenta resúmenes, registra por archivo el estado de cada operación y exporta los resultados detallados a JSON de auditoría.                                                                                                    |
| **RF-11** | Validación de rutas     | `[x] Cumplido` | `planner.py` valida origen y destino para evitar configuraciones no permitidas.                                                                                                                                                           |
| **RF-12** | CLI                     | `[x] Cumplido` | `scan`, `plan` y `run` se probaron en Windows según lo esperado. `run` recibe la ruta del JSON como argumento posicional; el alcance describe la opción `--plan`, por lo que esa diferencia de interfaz debe quedar documentada.          |

## Requisitos no funcionales

| ID         | Requisito             | Estado         | Notas                                                                                                                                                                                                                     |
| ---------- | --------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **RNF-01** | Multiplataforma       | `[/] Parcial`  | Usa `pathlib.Path` y serializa rutas JSON en formato portable. Falta validar el flujo completo tanto en Windows como en Linux.                                                                                            |
| **RNF-02** | Integridad            | `[/] Parcial`  | El ejecutor verifica los traslados e intenta revertir los movimientos ante fallos; si la reversión falla, informa que se requiere recuperación manual. El movimiento de varios archivos no es atómico.                    |
| **RNF-03** | Determinismo          | `[x] Cumplido` | El planificador ordena grupos y sidecars antes de resolver colisiones; las pruebas verifican resultados idénticos ante distinto orden de entrada.                                                                        |
| **RNF-04** | Resiliencia           | `[x] Cumplido` | Los fallos de ejecución se registran por operación para continuar procesando el lote.                                                                                                                                     |
| **RNF-05** | Rendimiento           | `[/] Parcial`  | Se validó el flujo con una copia de una biblioteca de 20 GB en Windows y la extracción usa procesamiento por lotes. No hay caché de resultados de escaneo; falta medir/documentar tiempos y validar en Linux.             |
| **RNF-06** | Mantenibilidad        | `[x] Cumplido` | Las responsabilidades se distribuyen entre módulos de escaneo, metadatos, fechas, asociaciones, planificación, persistencia, ejecución y CLI.                                                                             |
| **RNF-07** | Observabilidad        | `[x] Cumplido` | Hay registros configurables con marca de tiempo, estados detallados por archivo en el log y reportes JSON de auditoría.                                                                                                  |
| **RNF-08** | Pruebas               | `[/] Parcial`  | La suite automatizada (82 pruebas) pasó en Windows y se hizo una prueba manual de extremo a extremo con una copia de 20 GB. Falta ejecutar la suite y el flujo manual en Linux.                                            |
| **RNF-09** | Dependencias mínimas  | `[/] Parcial`  | Typer es la dependencia Python de ejecución y se detecta ExifTool, pero el aviso cuando falta no explica cómo instalarlo.                                                                                                 |
| **RNF-10** | Errores comprensibles | `[/] Parcial`  | La CLI informa errores de carga y movimiento; el aviso por falta de ExifTool no es accionable y debe explicar cómo resolverlo.                                                                                            |

## Próximos pasos: Hito 6, validación del MVP

- [x] Ejecutar `scan`, `plan` y `run` en Windows sobre una copia de una
  biblioteca real de 20 GB; comparar la estructura antes/después.
- [x] Generar el plan JSON y completar la ejecución real en esa prueba:
  1.893 operaciones principales y 171 pares de sidecars.
- [x] Ejecutar la suite automatizada en Windows: 82 pruebas aprobadas.
- [ ] Ejecutar la suite completa de pruebas y repetir el flujo de extremo a
  extremo en Linux.
- [x] Verificar cada traslado antes de declararlo exitoso y probar fallos
  parciales de medio/sidecar; decidir e implementar la recuperación o
  documentar claramente la recuperación manual.
- [x] Ordenar de forma estable los archivos antes de asignar destinos y añadir
  pruebas que comprueben planes idénticos ante colisiones; la prueba de una
  sola ejecución no confirma determinismo entre ejecuciones.
- [x] Registrar por archivo la operación y su resultado en el log y en un
  reporte JSON de auditoría.
- [ ] Hacer que el aviso de ExifTool ausente indique cómo instalarlo.
- [ ] Evaluar e implementar la caché de resultados de escaneo que pide RNF-05.
- [x] Documentar en el README las limitaciones conocidas y los pasos seguros
  para probar el MVP sobre copias de archivos.
