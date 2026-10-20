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
DIRECTORIO_REPORTES_DEFAULT = Path("reportes")


def rotar_logs_antiguos(directorio: Path, max_archivos: int = 5) -> None:
    """Conserva únicamente los 'max_archivos' más recientes en el directorio."""
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
    """Genera la ruta del archivo de log incluyendo fecha y hora (timestamp)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Si se pasa '.' o un directorio, usamos ese directorio. Si pasa un nombre de archivo, tomamos su carpeta contenedora.
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
    """
    Configura el sistema de logging desacoplando la consola del archivo de log.

    Parameters:
        dev (bool): Si es True, el log registra desde DEBUG, consola limpia.
        debug (bool): Si es True, tanto log como consola registran desde DEBUG.
        log_file (Path | None): Ruta o carpeta base para guardar el log. Si es None,
                                se utiliza la carpeta 'reportes/' por defecto.

    Returns:
        logging.Logger: Instancia del logger configurada.
    """
    logger = logging.getLogger(LOGGER_NAME)

    if logger.hasHandlers():
        logger.handlers.clear()

    # El logger principal debe aceptar DEBUG si dev o debug están activos
    nivel_general = logging.DEBUG if (dev or debug) else logging.INFO
    logger.setLevel(nivel_general)

    formato = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler de consola: en pantalla solo se muestra ERROR salvo en modo --debug
    consola_handler = logging.StreamHandler()
    nivel_consola = logging.DEBUG if debug else logging.ERROR
    consola_handler.setLevel(nivel_consola)
    consola_handler.setFormatter(formato)
    logger.addHandler(consola_handler)

    # Si no se especifica --log-file, la carpeta por defecto siempre es 'reportes/'
    destino_log = log_file if log_file is not None else DIRECTORIO_REPORTES_DEFAULT

    ruta_log_real = generar_ruta_log(destino_log)
    archivo_handler = logging.FileHandler(ruta_log_real, encoding="utf-8")
    nivel_archivo = logging.DEBUG if (dev or debug) else logging.INFO
    archivo_handler.setLevel(nivel_archivo)
    archivo_handler.setFormatter(formato)
    logger.addHandler(archivo_handler)

    return logger


def obtener_logger() -> logging.Logger:
    """Recupera el logger principal de Mulita."""
    return logging.getLogger(LOGGER_NAME)


def exportar_json(datos: dict[str, Any], ruta_salida: Path) -> None:
    """Guarda un diccionario como archivo JSON de forma legible."""
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    with ruta_salida.open("w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)
