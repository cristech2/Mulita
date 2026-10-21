## v0.3.0 (2026-10-21)

### Feat

- **plan-storage**: guardar y cargar planes de organización en JSON, y
  localizar planes disponibles para ejecutarlos
- **executor**: verificar los traslados, intentar revertir operaciones
  fallidas y señalar cuándo se requiere recuperación manual
- **reporting**: registrar el resultado detallado por archivo y exportar
  reportes JSON de auditoría
- **cli**: agregar `mulita run` con selección de planes, simulación
  predeterminada (`--dry-run`) y ejecución real confirmada (`--ejecutar`)

## v0.2.0 (2026-10-20)

### Feat

- **planner**: implementar planificación de organización, resolución de colisiones y exportación a JSON
- **asociaciones**: implementar asociacion de sidecars xmp y modelos de dominio
- **metadata**: integrar extraccion de metadatos EXIF con ExifTool y resolucion de fechas

## v0.1.0 (2026-10-20)

### Feat

- **core**: establecer andamiaje inicial, modulo de escaneo y sistema de logs
- initialize Mulita MVP scaffold
