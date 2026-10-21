"""Pruebas para el módulo de observabilidad y logging."""

import logging
import time
from datetime import datetime
from pathlib import Path

from mulita.models import (
    EstadoEjecucionOperacion,
    RegistroOperacionArchivo,
    ResultadoEjecucion,
)
from mulita.reporting import (
    configurar_logging,
    generar_ruta_log,
    obtener_logger,
    registrar_resultado_detallado_en_log,
    rotar_logs_antiguos,
)


def test_generar_ruta_log_crea_timestamp(tmp_path: Path) -> None:
    """Verifica que el nombre del log incluya marca temporal.

    Args:
        tmp_path (Path): Directorio temporal para crear archivos de prueba.
    """
    # Arrange
    ruta_base = tmp_path / "reportes" / "escaneo.log"

    # Act
    ruta_final = generar_ruta_log(ruta_base)

    # Assert
    assert ruta_final.parent == tmp_path / "reportes"
    assert "escaneo_" in ruta_final.name
    assert ruta_final.suffix == ".log"


def test_rotar_logs_antiguos_mantiene_maximo(tmp_path: Path) -> None:
    """Verifica que la rotación conserve solo la cantidad máxima de logs.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    directorio_logs = tmp_path / "logs"
    directorio_logs.mkdir()

    for i in range(7):
        archivo = directorio_logs / f"test_{i}.log"
        archivo.touch()
        time.sleep(0.01)

    # Act
    rotar_logs_antiguos(directorio_logs, max_archivos=5)

    # Assert
    archivos_restantes = list(directorio_logs.glob("*.log"))
    assert len(archivos_restantes) == 5
    nombres = [f.name for f in archivos_restantes]
    assert "test_0.log" not in nombres
    assert "test_1.log" not in nombres


def test_configurar_logging_modos_dev_y_debug(tmp_path: Path) -> None:
    """Verifica los niveles de logging en los modos normal y desarrollo.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    log_dir = tmp_path / "logs"

    # Act: Modo normal
    logger_normal = configurar_logging(
        dev=False, debug=False, log_file=log_dir
    )
    assert logger_normal.level == logging.INFO

    # Act: Modo dev
    logger_dev = configurar_logging(dev=True, debug=False, log_file=log_dir)
    assert logger_dev.level == logging.DEBUG


def test_configurar_logging_no_crea_archivo_hasta_registrar_evento(
    tmp_path: Path,
) -> None:
    """Evita archivos vacíos cuando el comando no alcanza a registrar eventos.

    Args:
        tmp_path (Path): Directorio temporal para los logs.
    """
    # Arrange
    log_dir = tmp_path / "logs"
    logger = configurar_logging(log_file=log_dir)

    # Act / Assert: configurar no crea la carpeta ni un archivo vacío.
    assert not log_dir.exists()

    logger.info("Inicio de operación")

    archivos_log = list(log_dir.glob("*.log"))
    assert len(archivos_log) == 1
    assert "Inicio de operación" in archivos_log[0].read_text(encoding="utf-8")


def test_obtener_logger_devuelve_instancia_correcta() -> None:
    """Verifica que obtener_logger devuelva el logger de la aplicación."""
    # Act
    logger = obtener_logger()

    # Assert
    assert logger.name == "mulita"


def test_registrar_resultado_detallado_en_log_escribe_eventos(
    tmp_path: Path,
) -> None:
    """Verifica que el registro detallado vuelque eventos por archivo en el log.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    log_dir = tmp_path / "logs"
    configurar_logging(dev=True, debug=False, log_file=log_dir)

    ahora = datetime.now()
    reg_ok = RegistroOperacionArchivo(
        origen=Path("foto.jpg"),
        destino=Path("dest/foto.jpg"),
        estado=EstadoEjecucionOperacion.EXITOSO,
        timestamp=ahora,
    )
    reg_rev = RegistroOperacionArchivo(
        origen=Path("err.jpg"),
        destino=Path("dest/err.jpg"),
        estado=EstadoEjecucionOperacion.FALLIDO_REVERTIDO,
        timestamp=ahora,
        detalle_error="Error E/S",
    )

    resultado = ResultadoEjecucion(
        procesados_exitosamente=1,
        fallidos=1,
        errores=[],
        registros_detallados=[reg_ok, reg_rev],
    )

    # Act
    registrar_resultado_detallado_en_log(resultado)

    # Assert
    archivos_log = list(log_dir.glob("*.log"))
    assert len(archivos_log) > 0
    contenido = archivos_log[0].read_text(encoding="utf-8")

    assert "[OK] Principal: 'foto.jpg' -> 'dest/foto.jpg'" in contenido
    assert "[REVERTIDO] Principal: 'err.jpg' - Error: Error E/S" in contenido
