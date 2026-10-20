"""
Módulo para el registro de operaciones, errores y exportación de resúmenes.

Implementa los requisitos RF-10 (Registros y resumen) y RNF-07 (Observabilidad).
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

LOGGER_NAME = "mulita"


def rotar_logs_antiguos(directorio: Path, max_archivos: int = 5) -> None:
    """
    Conserva únicamente los 'max_archivos' más recientes en el directorio.
    Elimina los archivos .log antiguos en caso de superar el límite.
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
    """
    Genera la ruta del archivo de log incluyendo fecha y hora (timestamp).

    Si ruta_base es un directorio, crea mulita_YYYYMMDD_HHMMSS.log dentro.
    Si ruta_base es un archivo, genera nombre_YYYYMMDD_HHMMSS.log.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if ruta_base.is_dir() or ruta_base.suffix == "":
        directorio = ruta_base
        nombre_archivo = f"mulita_{timestamp}.log"
    else:
        directorio = ruta_base.parent
        nombre_archivo = f"{ruta_base.stem}_{timestamp}.log"

    directorio.mkdir(parents=True, exist_ok=True)
    rotar_logs_antiguos(directorio, max_archivos=4)  # Deja espacio para el nuevo
    return directorio / nombre_archivo


def configurar_logging(
    verbose: bool = False, log_file: Path | None = None
) -> logging.Logger:
    """
    Configura el sistema de logging centralizado para la aplicación.

    Parameters:
    verbose (bool):
        - False (Producción): registra INFO+ en log, ERROR en consola.
        - True (Debug): registra DEBUG+ en log y en consola.
    log_file (Path | None): Ruta o carpeta base para guardar el log.

    Returns:
    logging.Logger: Instancia del logger configurada.
    """
    logger = logging.getLogger(LOGGER_NAME)

    if logger.hasHandlers():
        logger.handlers.clear()

    # Nivel base del logger principal
    nivel_general = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(nivel_general)

    formato = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler para la consola
    consola_handler = logging.StreamHandler()
    consola_handler.setLevel(logging.DEBUG if verbose else logging.ERROR)
    consola_handler.setFormatter(formato)
    logger.addHandler(consola_handler)

    # Handler para archivo
    if log_file:
        ruta_log_real = generar_ruta_log(log_file)
        archivo_handler = logging.FileHandler(ruta_log_real, encoding="utf-8")
        # En producción guarda INFO y superior; en debug guarda desde DEBUG
        archivo_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        archivo_handler.setFormatter(formato)
        logger.addHandler(archivo_handler)

    return logger


def obtener_logger() -> logging.Logger:
    """
    Recupera el logger configurado de Mulita.

    Returns:
    logging.Logger: Instancia del logger principal.
    """
    return logging.getLogger(LOGGER_NAME)


def exportar_json(datos: dict[str, Any], ruta_salida: Path) -> None:
    """
    Guarda un diccionario como un archivo JSON de forma legible.
    Utilizado para el plan de organización (RF-06).
    """
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    with ruta_salida.open("w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)
