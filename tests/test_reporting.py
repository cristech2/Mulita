"""Pruebas para el módulo de reportes y logging."""

import logging
import time
from pathlib import Path

from mulita.reporting import (
    configurar_logging,
    generar_ruta_log,
    rotar_logs_antiguos,
)


def test_generar_ruta_log_crea_timestamp(tmp_path: Path) -> None:
    """Verifica que el nombre del log incluya marca temporal.

    Args:
        tmp_path (Path): Directorio temporal para crear archivos de prueba.
    """
    ruta_base = tmp_path / "reportes" / "escaneo.log"
    ruta_final = generar_ruta_log(ruta_base)

    assert ruta_final.parent == tmp_path / "reportes"
    assert "escaneo_" in ruta_final.name
    assert ruta_final.suffix == ".log"


def test_rotar_logs_antiguos_mantiene_maximo(tmp_path: Path) -> None:
    """Verifica que la rotación conserve solo la cantidad máxima de logs.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    directorio_logs = tmp_path / "logs"
    directorio_logs.mkdir()

    for i in range(7):
        archivo = directorio_logs / f"test_{i}.log"
        archivo.touch()
        time.sleep(0.01)

    rotar_logs_antiguos(directorio_logs, max_archivos=5)

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
    log_dir = tmp_path / "logs"

    # Act: Modo normal
    logger_normal = configurar_logging(
        dev=False, debug=False, log_file=log_dir
    )
    assert logger_normal.level == logging.INFO

    # Act: Modo dev
    logger_dev = configurar_logging(dev=True, debug=False, log_file=log_dir)
    assert logger_dev.level == logging.DEBUG
