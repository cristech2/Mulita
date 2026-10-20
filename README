# Mulita

**Mulita** es una aplicación para ordenar fotografías y videos de forma cronológica a partir de los metadatos de los archivos. Su mascota está inspirada en la mulita argentina: pequeña, resistente y siempre lista para explorar.

> Un lugar ordenado para cada recuerdo, sin perder de vista de qué dispositivo y proyecto viene.


## Propósito

La aplicación analiza un directorio de origen y organiza su contenido en una estructura fácil de recorrer. Además de formatos habituales de imagen y video, contempla archivos de trabajo fotográfico y sus archivos auxiliares (*sidecars*), para mantener juntos los materiales relacionados.

La organización busca reflejar, cuando los datos disponibles lo permiten:

- **Dispositivo** de captura o procedencia.
- **Año**, **mes** y **día** de la toma o creación.
- **Tipo de archivo**, como fotografía, video, proyecto de edición o sidecar.
- **Archivos idénticos**, comparando su hash digital para reconocer duplicados incluso si tienen nombres o ubicaciones diferentes.

## Tipos de archivos contemplados

Mulita está diseñada para reconocer y organizar formatos habituales de imagen y video, además de proyectos, recursos y archivos auxiliares de aplicaciones fotográficas. Las extensiones se reconocen sin distinguir entre mayúsculas y minúsculas.

### Imágenes y fotografías

| Extensiones                                                                            | Tipo / uso                                                         |
| -------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `.jpg`, `.jpeg`                                                                        | JPEG; fotografías y exportaciones habituales.                      |
| `.png`                                                                                 | PNG; imágenes sin pérdida, capturas y gráficos.                    |
| `.tif`, `.tiff`                                                                        | TIFF; fotografía de alta calidad e impresión.                      |
| `.webp`, `.gif`, `.bmp`                                                                | Formatos comunes para web, animaciones e imágenes de mapa de bits. |
| `.heic`, `.heif`                                                                       | Imágenes HEIF, frecuentes en teléfonos y cámaras recientes.        |
| `.avif`, `.jxl`                                                                        | Formatos modernos de imagen y distribución web.                    |
| `.dng`, `.cr2`, `.cr3`, `.nef`, `.nrw`, `.arw`, `.raf`, `.rw2`, `.orf`, `.pef`, `.srw` | Ejemplos de formatos RAW de distintas marcas y cámaras.            |
| `.svg`, `.ico`                                                                         | Gráficos vectoriales e iconos.                                     |

### Videos

| Extensiones                             | Tipo / uso                                                |
| --------------------------------------- | --------------------------------------------------------- |
| `.mp4`, `.m4v`                          | Video comprimido de uso general y dispositivos móviles.   |
| `.mov`                                  | Contenedor QuickTime, común en cámaras y productos Apple. |
| `.avi`, `.mkv`, `.wmv`, `.flv`, `.webm` | Contenedores de video de uso general o web.               |
| `.mpg`, `.mpeg`, `.3gp`                 | Formatos de video tradicionales y móviles.                |
| `.mts`, `.m2ts`, `.ts`                  | Grabaciones AVCHD y flujos de transporte.                 |

### Proyectos, recursos y sidecars

| Extensión                               | Aplicación / grupo                                         | Tipo y utilidad                                                                                                                            |
| --------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `.rrdata`                               | RapidRAW                                                   | Sidecar JSON con ediciones no destructivas y copias virtuales.                                                                             |
| `.rrexif`                               | RapidRAW                                                   | Sidecar que conserva metadatos EXIF en procesos pesados, como HDR o reducción de ruido.                                                    |
| `.xmp`                                  | RapidRAW, digiKam, Lightroom, Adobe Camera Raw y Photoshop | Sidecar estándar para metadatos, etiquetas, valoraciones y parámetros de edición no destructiva, especialmente en RAW.                     |
| `.afphoto`                              | Affinity Photo                                             | Proyecto de fotografía con capas, filtros, texto y máscaras.                                                                               |
| `.afdesign`, `.afdesigner`              | Affinity Designer                                          | Proyecto de diseño gráfico y vectorial.                                                                                                    |
| `.afpub`                                | Affinity Publisher                                         | Proyecto de maquetación y publicación editorial.                                                                                           |
| `.af`                                   | Suite Affinity (v2)                                        | Documento unificado compatible con Photo, Designer y Publisher.                                                                            |
| `.afpalette`, `.afassets`, `.afbrushes` | Suite Affinity                                             | Recursos: paletas de color, bibliotecas de elementos y pinceles personalizados.                                                            |
| `.psd`                                  | Adobe Photoshop                                            | Proyecto con capas y objetos inteligentes.                                                                                                 |
| `.psb`                                  | Adobe Photoshop                                            | Proyecto de gran tamaño, para documentos que superan los 2 GB o los 30.000 píxeles por lado.                                               |
| `.atn`, `.abr`                          | Adobe Photoshop                                            | Recursos de Photoshop: acciones automatizadas y pinceles personalizados.                                                                   |
| `.lrcat`                                | Lightroom Classic                                          | Catálogo que indexa la biblioteca y registra cambios.                                                                                      |
| `.lrcat-data`                           | Lightroom Classic                                          | Datos auxiliares del catálogo, incluidas máscaras generadas con IA.                                                                        |
| `.lrprev`, `.lrdata`                    | Lightroom Classic                                          | Cachés de previsualizaciones y datos asociados para agilizar la exploración.                                                               |
| `.lrtemplate`                           | Lightroom                                                  | Formato heredado de presets de revelado.                                                                                                   |
| `.db`                                   | digiKam                                                    | Bases SQLite, por ejemplo `digikam4.db`, `recognition.db` y `similarity.db`, usadas para catálogo, reconocimiento y búsqueda de similitud. |

Los sidecars deben conservarse asociados a su archivo original o proyecto cuando corresponda. Los catálogos, bases de datos y cachés pueden depender de rutas internas o de una aplicación; por eso requieren un tratamiento cuidadoso y no deben reubicarse como si fueran fotografías independientes.

Esta lista describe los formatos que Mulita busca reconocer y organizar. La lectura de metadatos puede variar según el formato y las herramientas disponibles; cuando no se puedan extraer, se aplicarán las reglas de respaldo configuradas, sin descartar el archivo por su extensión.

## Organización prevista

La estructura de destino será configurable. Una posible organización es:

```text
Biblioteca/
└── Dispositivo/
	└── Año/
		└── Mes/
			└── Día/
				├── Imagenes/
				├── Videos/
				├── Proyectos/
				└── Sidecars/
```

Los nombres de las categorías son ilustrativos y podrán ajustarse a las opciones que ofrezca la aplicación. La fecha y el dispositivo se obtendrán de los metadatos disponibles; cuando falten o sean ambiguos, la aplicación deberá aplicar reglas de respaldo configurables y evitar clasificaciones silenciosamente incorrectas.

## Principios del proyecto

- **Cuidar los originales:** analizar antes de modificar y ofrecer un modo de vista previa.
- **Conservar asociaciones:** mantener juntos los archivos vinculados, incluidos sidecars y proyectos.
- **Ser transparente:** informar qué metadatos se usaron y cómo se resolvieron los casos incompletos.
- **Identificar duplicados:** calcular hashes digitales para detectar documentos con contenido idéntico y permitir gestionarlos de forma segura.
- **Evitar pérdidas:** detectar colisiones de nombres y no sobrescribir archivos sin una decisión explícita.
- **Adaptarse al flujo de trabajo:** permitir configurar criterios y estructura de salida.

## Estado

Este README describe el propósito y el alcance previsto de Mulita. Las funciones, formatos y opciones concretas dependerán de su implementación.

## Nombre y mascota

La mulita es el símbolo del proyecto y su guiño a Argentina. Representa una compañera paciente para la tarea de recorrer, reconocer y ordenar archivos sin dejar recuerdos atrás.
