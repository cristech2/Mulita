## [Unreleased]

### Feat

- **scanner**: reutilizar metadatos mediante un caché SQLite persistente,
  invalidar entradas cuando cambia el archivo y permitir omitir el caché con
  `--sin-cache`
- **scanner**: reconocer y organizar proyectos de edición, y validar que cada
  extensión corresponda a una sola categoría
- **cli**: mostrar etapas claras y progreso medible durante escaneos,
  extracción de metadatos y ejecución de operaciones

### Fix

- **cli**: validar la salida del plan antes del escaneo, pedir confirmación
  para sobrescribir y evitar guardar dentro del origen
- **executor**: prevalidar las operaciones y preparar la auditoría antes de
  confirmar y ejecutar movimientos
- **plan-storage**: guardar los JSON de forma atómica y preservar auditorías
  anteriores

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
