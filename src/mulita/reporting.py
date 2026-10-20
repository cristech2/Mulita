"""Registro, observabilidad y exportación de resúmenes para Mulita."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

LOGGER_NAME = "mulita"
DIRECTORIO_REPORTES_DEFAULT = Path("reportes")


def rotar_logs_antiguos(directorio: Path, max_archivos: int = 5) -> None:
    """Mantiene solo los archivos de log más recientes.

    Args:
        directorio (Path): Directorio donde se almacenan los logs.
        max_archivos (int): Cantidad máxima de archivos a conservar.
    """
    if not directorio.exists():
        return

    archivos_log = sorted(
        [f for f in directorio.glob("*.log") if f.is_file()],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    for log_viejo in archivos_log[max_archivos:]:
        try:
            log_viejo.unlink()
        except OSError:
            pass


def generar_ruta_log(ruta_base: Path) -> Path:
    """Genera la ruta del archivo de log con marca temporal.

    Args:
        ruta_base (Path): Ruta base del log o carpeta de destino.

    Returns:
        Path: Ruta completa del archivo a crear.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if ruta_base.is_dir() or ruta_base.suffix == "":
        directorio = ruta_base
        nombre_archivo = f"mulita_{timestamp}.log"
    else:
        directorio = ruta_base.parent
        nombre_archivo = f"{ruta_base.stem}_{timestamp}.log"

    directorio.mkdir(parents=True, exist_ok=True)
    rotar_logs_antiguos(directorio, max_archivos=4)
    return directorio / nombre_archivo


def configurar_logging(
    dev: bool = False,
    debug: bool = False,
    log_file: Path | None = None,
) -> logging.Logger:
    """Configura el sistema de logging para la aplicación.

    Args:
        dev (bool): Activa detalles de log manteniendo la consola limpia.
        debug (bool): Activa log detallado en consola y archivo.
        log_file (Path | None): Ruta base del archivo o carpeta de log.

    Returns:
        logging.Logger: Logger global configurado.
    """
    logger = logging.getLogger(LOGGER_NAME)

    if logger.hasHandlers():
        logger.handlers.clear()

    nivel_general = logging.DEBUG if (dev or debug) else logging.INFO
    logger.setLevel(nivel_general)

    formato = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    consola_handler = logging.StreamHandler()
    nivel_consola = logging.DEBUG if debug else logging.ERROR
    consola_handler.setLevel(nivel_consola)
    consola_handler.setFormatter(formato)
    logger.addHandler(consola_handler)

    destino_log = (
        log_file if log_file is not None else DIRECTORIO_REPORTES_DEFAULT
    )

    ruta_log_real = generar_ruta_log(destino_log)
    archivo_handler = logging.FileHandler(ruta_log_real, encoding="utf-8")
    nivel_archivo = logging.DEBUG if (dev or debug) else logging.INFO
    archivo_handler.setLevel(nivel_archivo)
    archivo_handler.setFormatter(formato)
    logger.addHandler(archivo_handler)

    return logger


def obtener_logger() -> logging.Logger:
    """Devuelve el logger principal de Mulita.

    Returns:
        logging.Logger: Logger global de la aplicación.
    """
    return logging.getLogger(LOGGER_NAME)


def exportar_json(datos: dict[str, Any], ruta_salida: Path) -> None:
    """Guarda un diccionario como JSON de salida.

    Args:
        datos (dict[str, Any]): Estructura a serializar.
        ruta_salida (Path): Ruta del archivo JSON de destino.
    """
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    with ruta_salida.open("w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)
