"""
Módulo para el recorrido recursivo, clasificación y análisis inicial de archivos.
"""

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

from mulita.dates import FechaResultado, resolver_fecha_archivo
from mulita.metadata import extraer_metadatos
from mulita.reporting import obtener_logger


class TipoArchivo(Enum):
    """Enumeración de los tipos de archivos soportados."""

    IMAGEN = auto()
    RAW = auto()
    VIDEO = auto()
    AUXILIAR = auto()
    DESCONOCIDO = auto()


EXTENSIONES_IMAGEN: set[str] = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".af"}
EXTENSIONES_RAW: set[str] = {
    ".cr2",
    ".cr3",
    ".nef",
    ".arw",
    ".dng",
    ".orf",
    ".rw2",
    ".raf",
}
EXTENSIONES_VIDEO: set[str] = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".3gp"}
EXTENSIONES_AUX: set[str] = {".xmp", ".rrdata", ".rrexif"}


@dataclass
class ArchivoEscaneado:
    """
    Representa un archivo encontrado durante el escaneo con su tipo clasificado.
    """

    ruta: Path
    tipo: TipoArchivo


@dataclass
class ArchivoAnalizado:
    """
    Representa un archivo escaneado con su resolución de fecha y metadatos.
    """

    archivo: ArchivoEscaneado
    fecha_resultado: FechaResultado
    metadatos: dict[str, str]


def clasificar_extension(extension: str) -> TipoArchivo:
    """Clasifica una extensión de archivo en su categoría correspondiente."""
    ext = extension.lower()
    if ext in EXTENSIONES_IMAGEN:
        return TipoArchivo.IMAGEN
    elif ext in EXTENSIONES_RAW:
        return TipoArchivo.RAW
    elif ext in EXTENSIONES_VIDEO:
        return TipoArchivo.VIDEO
    elif ext in EXTENSIONES_AUX:
        return TipoArchivo.AUXILIAR

    return TipoArchivo.DESCONOCIDO


def escanear_directorio(
    origen: Path, destino_ignorar: Path | None = None
) -> list[ArchivoEscaneado]:
    """Recorre el directorio origen de forma recursiva buscando archivos."""
    logger = obtener_logger()
    archivos_encontrados: list[ArchivoEscaneado] = []

    if not origen.exists() or not origen.is_dir():
        return archivos_encontrados

    origen_abs = origen.resolve()
    destino_abs = destino_ignorar.resolve() if destino_ignorar else None

    for ruta in origen_abs.rglob("*"):
        if not ruta.is_file():
            continue

        if any(part.startswith(".") for part in ruta.parts if part != "."):
            logger.debug(f"Omitiendo archivo/carpeta oculta: {ruta}")
            continue

        if destino_abs and destino_abs in ruta.parents:
            logger.debug(f"Omitiendo ruta dentro del destino excluido: {ruta}")
            continue

        tipo = clasificar_extension(ruta.suffix)
        archivos_encontrados.append(ArchivoEscaneado(ruta=ruta, tipo=tipo))

    return archivos_encontrados


def analizar_directorio(
    origen: Path, destino_ignorar: Path | None = None
) -> list[ArchivoAnalizado]:
    """
    Orquesta el escaneo, la consulta de metadatos
    y la resolución explícita de fechas.
    """
    logger = obtener_logger()
    archivos = escanear_directorio(origen, destino_ignorar)

    # Filtrar únicamente los archivos compatibles para la extracción de metadatos
    multimedia_rutas = [
        a.ruta
        for a in archivos
        if a.tipo in (TipoArchivo.IMAGEN, TipoArchivo.RAW, TipoArchivo.VIDEO)
    ]

    # Extraer metadatos solo de archivos válidos
    metadatos_map = extraer_metadatos(multimedia_rutas)

    resultados: list[ArchivoAnalizado] = []
    for item in archivos:
        meta = metadatos_map.get(item.ruta, {})
        res_fecha = resolver_fecha_archivo(item.ruta, item.tipo, meta)

        if item.tipo == TipoArchivo.DESCONOCIDO:
            logger.warning(f"Archivo desconocido/no reconocido: {item.ruta}")
        else:
            logger.debug(
                f"Encontrado: {item.ruta} [{item.tipo.name}] -> "
                f"Fecha: {res_fecha.fecha.strftime('%Y-%m-%d %H:%M:%S')} "
                f"({res_fecha.fuente})"
            )

        resultados.append(
            ArchivoAnalizado(archivo=item, fecha_resultado=res_fecha, metadatos=meta)
        )

    return resultados
