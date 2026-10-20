## Unreleased

### Feat

- **planner**: implementar generación de plan de organización determinista, resolución de colisiones y validación de rutas
- **cli**: conectar comando `plan` con resumen visual de operaciones y exportación a JSON (`--salida`)
- **models**: agregar modelos `PlanOrganizacion`, `OperacionPlan` y enum `AccionPlan`
- **reporting**: agregar `exportar_plan_json` con serialización de tipos nativos, Dataclasses, Enums y Path
- **associations**: implementar asociacion de sidecars (.xmp, .rrdata, .rrexif), deteccion de huerfanos y ambiguos
- **cli**: integrar desglose de sidecars asociados, huérfanos y ambiguos en la salida de `scan`
- **metadata**: integrar extraccion de metadatos EXIF con ExifTool y resolucion de fechas

## v0.1.0 (2026-10-20)

### Feat

- **core**: establecer andamiaje inicial, modulo de escaneo y sistema de logs
- initialize Mulita MVP scaffold