"""Registro, observabilidad y administración de logs para Mulita."""

import logging
from datetime import datetime
from pathlib import Path

from mulita.models import EstadoEjecucionOperacion, ResultadoEjecucion

LOGGER_NAME = "mulita"
DIRECTORIO_REPORTES_DEFAULT = Path("reportes")


class _LazyFileHandler(logging.Handler):
    """Crea el archivo y prepara la rotación al registrar el primer evento."""

    def __init__(self, ruta_base: Path, level: int) -> None:
        """Inicializa un handler sin crear todavía el archivo de log.

        Args:
            ruta_base (Path): Ruta base del archivo o directorio de log.
            level (int): Nivel mínimo de eventos que debe registrar.
        """
        super().__init__(level)
        self._ruta_base = ruta_base
        self._file_handler: logging.FileHandler | None = None

    def emit(self, record: logging.LogRecord) -> None:
        """Escribe un evento, inicializando el archivo solo si hace falta.

        Args:
            record (logging.LogRecord): Evento que debe registrarse.
        """
        if self._file_handler is None:
            ruta_log = generar_ruta_log(self._ruta_base)
            self._file_handler = logging.FileHandler(
                ruta_log, encoding="utf-8"
            )
            self._file_handler.setFormatter(self.formatter)

        self._file_handler.emit(record)

    def close(self) -> None:
        """Cierra el archivo subyacente si llegó a crearse."""
        if self._file_handler is not None:
            self._file_handler.close()
        super().close()


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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

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

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

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

    nivel_archivo = logging.DEBUG if (dev or debug) else logging.INFO
    archivo_handler = _LazyFileHandler(destino_log, nivel_archivo)
    archivo_handler.setFormatter(formato)
    logger.addHandler(archivo_handler)

    return logger


def obtener_logger() -> logging.Logger:
    """Devuelve el logger principal de Mulita.

    Returns:
        logging.Logger: Logger global de la aplicación.
    """
    return logging.getLogger(LOGGER_NAME)


def registrar_resultado_detallado_en_log(
    resultado: ResultadoEjecucion,
) -> None:
    """Escribe en el log el detalle de cada archivo procesado para auditoría.

    Args:
        resultado (ResultadoEjecucion): Resultado de la ejecución del plan.
    """
    logger = obtener_logger()
    logger.info("--- INICIO DE REGISTRO DETALLADO POR ARCHIVO ---")

    for reg in resultado.registros_detallados:
        tipo = "Sidecar" if reg.es_sidecar else "Principal"
        origen_str = reg.origen.as_posix()
        destino_str = reg.destino.as_posix()

        if reg.estado == EstadoEjecucionOperacion.EXITOSO:
            logger.info(f"[OK] {tipo}: '{origen_str}' -> '{destino_str}'")
        elif reg.estado == EstadoEjecucionOperacion.OMITIDO:
            logger.info(f"[OMITIDO] {tipo}: '{origen_str}'")
        elif reg.estado == EstadoEjecucionOperacion.FALLIDO_REVERTIDO:
            logger.error(
                f"[REVERTIDO] {tipo}: '{origen_str}' - "
                f"Error: {reg.detalle_error}"
            )
        elif (
            reg.estado == EstadoEjecucionOperacion.FALLIDO_RECUPERACION_MANUAL
        ):
            logger.error(
                f"[RECUPERACION MANUAL REQUERIDA] {tipo}: '{origen_str}' "
                f"-> Destino fallido: '{destino_str}' - "
                f"Error: {reg.detalle_error}"
            )

    logger.info("--- FIN DE REGISTRO DETALLADO POR ARCHIVO ---")
