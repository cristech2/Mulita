"""Escaneo recursivo, clasificación y análisis inicial de archivos."""

import sqlite3
from collections.abc import Callable
from pathlib import Path

from mulita.associations import asociar_sidecars
from mulita.dates import resolver_fecha_archivo
from mulita.metadata import (
    MENSAJE_EXIFTOOL_AUSENTE,
    extraer_metadatos,
    verificar_exiftool,
)
from mulita.metadata_cache import CacheMetadatos
from mulita.models import (
    TIPO_ARCHIVO_POR_EXTENSION,
    ArchivoAnalizado,
    ArchivoEscaneado,
    ResultadoEscaneo,
    TipoArchivo,
)
from mulita.reporting import obtener_logger


def clasificar_extension(extension: str) -> TipoArchivo:
    """Clasifica una extensión en su tipo de archivo correspondiente.

    Args:
        extension (str): Extensión del archivo, por ejemplo ``.jpg``.

    Returns:
        TipoArchivo: Tipo asociado a la extensión.
    """
    ext = extension.lower()
    return TIPO_ARCHIVO_POR_EXTENSION.get(ext, TipoArchivo.DESCONOCIDO)


def escanear_directorio(
    origen: Path,
    destino_ignorar: Path | None = None,
    progreso: Callable[[str, int, int | None], None] | None = None,
) -> list[ArchivoEscaneado]:
    """Recorre recursivamente un directorio y devuelve archivos válidos.

    Args:
        origen (Path): Directorio raíz a recorrer.
        destino_ignorar (Path | None): Directorio a excluir del escaneo.

    Returns:
        list[ArchivoEscaneado]: Archivos encontrados y clasificados.
    """
    logger = obtener_logger()
    archivos_encontrados: list[ArchivoEscaneado] = []

    if not origen.exists() or not origen.is_dir():
        return archivos_encontrados

    origen_abs = origen.resolve()
    destino_abs = destino_ignorar.resolve() if destino_ignorar else None

    if progreso is not None:
        progreso("Buscando archivos...", 0, None)

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
        if progreso is not None:
            progreso("Buscando archivos...", len(archivos_encontrados), None)

    return archivos_encontrados


def analizar_directorio(
    origen: Path,
    destino_ignorar: Path | None = None,
    progreso: Callable[[str, int, int | None], None] | None = None,
    usar_cache: bool = True,
    ruta_cache: Path | None = None,
    exiftool_disponible: bool | None = None,
) -> ResultadoEscaneo:
    """Ejecuta el procesamiento completo de la fase de escaneo.

    Args:
        origen (Path): Directorio raíz a analizar.
        destino_ignorar (Path | None): Directorio a ignorar durante el escaneo.
        progreso (Callable | None): Función para informar el avance.
        usar_cache (bool): Indica si se debe reutilizar el caché persistente.
        ruta_cache (Path | None): Ruta de la base SQLite, principalmente útil
            para pruebas.
        exiftool_disponible (bool | None): Disponibilidad comprobada de
            ExifTool; ``None`` la comprueba antes de recorrer el origen.

    Returns:
        ResultadoEscaneo: Resultado consolidado del análisis.
    """
    logger = obtener_logger()
    if exiftool_disponible is None:
        exiftool_disponible = verificar_exiftool()
        if not exiftool_disponible:
            logger.error("%s\n", MENSAJE_EXIFTOOL_AUSENTE)

    archivos = escanear_directorio(
        origen,
        destino_ignorar,
        progreso=progreso,
    )

    multimedia_rutas = [
        a.ruta
        for a in archivos
        if a.tipo in (TipoArchivo.IMAGEN, TipoArchivo.RAW, TipoArchivo.VIDEO)
    ]

    cache: CacheMetadatos | None = None
    metadatos_map: dict[Path, dict[str, str]] = {}
    if usar_cache and multimedia_rutas:
        try:
            cache = CacheMetadatos(ruta_cache)
            metadatos_map = cache.obtener(multimedia_rutas)
        except (OSError, sqlite3.Error, ValueError) as err:
            logger.warning(
                "No se pudo leer el caché de metadatos; se analizarán "
                "los archivos sin reutilizarlo: %s",
                err,
            )
            if cache is not None:
                cache.cerrar()
                cache = None

    rutas_pendientes = [
        ruta for ruta in multimedia_rutas if ruta not in metadatos_map
    ]
    metadatos_nuevos = (
        extraer_metadatos(
            rutas_pendientes,
            progreso=progreso,
            exiftool_disponible=exiftool_disponible,
        )
        if rutas_pendientes
        else {}
    )
    metadatos_map.update(metadatos_nuevos)
    if cache is not None:
        try:
            cache.guardar(metadatos_nuevos)
        except (OSError, sqlite3.Error, ValueError) as err:
            logger.warning(
                "No se pudo actualizar el caché de metadatos: %s", err
            )
        finally:
            cache.cerrar()

    resultados: list[ArchivoAnalizado] = []
    desconocidos: list[ArchivoAnalizado] = []

    total_archivos = len(archivos)
    if progreso is not None:
        progreso(
            "Analizando fechas y clasificando archivos...", 0, total_archivos
        )

    for indice, item in enumerate(archivos, start=1):
        meta = metadatos_map.get(item.ruta, {})
        res_fecha = resolver_fecha_archivo(item.ruta, item.tipo, meta)
        analizado = ArchivoAnalizado(
            archivo=item,
            fecha_resultado=res_fecha,
            metadatos=meta,
        )

        if item.tipo == TipoArchivo.DESCONOCIDO:
            logger.warning(f"Archivo desconocido/no reconocido: {item.ruta}")
            desconocidos.append(analizado)
        else:
            logger.debug(
                f"Encontrado: {item.ruta} [{item.tipo.name}] -> "
                f"Fecha: {res_fecha.fecha.strftime('%Y-%m-%d %H:%M:%S')} "
                f"({res_fecha.fuente})"
            )

        resultados.append(analizado)
        if progreso is not None:
            progreso(
                "Analizando fechas y clasificando archivos...",
                indice,
                total_archivos,
            )

    grupos, sidecars_no_asociados = asociar_sidecars(resultados)

    return ResultadoEscaneo(
        grupos=grupos,
        sidecars_no_asociados=sidecars_no_asociados,
        desconocidos=desconocidos,
    )
