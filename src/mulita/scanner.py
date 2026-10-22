"""Escaneo recursivo, clasificación y análisis inicial de archivos."""

from collections.abc import Callable
from pathlib import Path

from mulita.associations import asociar_sidecars
from mulita.dates import resolver_fecha_archivo
from mulita.metadata import extraer_metadatos
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
) -> ResultadoEscaneo:
    """Ejecuta el procesamiento completo de la fase de escaneo.

    Args:
        origen (Path): Directorio raíz a analizar.
        destino_ignorar (Path | None): Directorio a ignorar durante el escaneo.

    Returns:
        ResultadoEscaneo: Resultado consolidado del análisis.
    """
    logger = obtener_logger()
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

    metadatos_map = extraer_metadatos(multimedia_rutas, progreso=progreso)

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
