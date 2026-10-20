"""
Módulo para el recorrido recursivo y clasificación de archivos.

Se encarga del RF-01 (Escaneo recursivo) y RF-02 (Formatos iniciales).
"""

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

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


def clasificar_extension(extension: str) -> TipoArchivo:
    """
    Clasifica una extensión de archivo en su categoría correspondiente.

    Parameters:
    extension (str): La extensión del archivo, incluyendo el punto (ej: '.jpg').

    Returns:
    TipoArchivo: La categoría a la que pertenece el archivo.
    """
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
    """
    Recorre el directorio origen de forma recursiva buscando archivos.

    Omite carpetas y archivos ocultos (que empiezan con un punto) y
    excluye completamente el directorio de destino si está anidado en el origen.

    Parameters:
    origen (Path): La ruta del directorio base a escanear.
    destino_ignorar (Path | None): Ruta de destino a excluir para evitar recursividad.

    Returns:
    list[ArchivoEscaneado]: Lista de archivos escaneados y clasificados.
    """
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
