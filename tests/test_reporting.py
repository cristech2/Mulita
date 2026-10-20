"""Pruebas para el módulo de reportes y logging."""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

from mulita.models import (
    AccionPlan,
    FechaResultado,
    OperacionPlan,
    PlanOrganizacion,
    TipoArchivo,
)
from mulita.reporting import (
    _convertir_a_json_compatible,
    configurar_logging,
    exportar_plan_json,
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


def test_convertir_a_json_compatible_tipos_complejos(tmp_path: Path) -> None:
    """Verifica la conversión de objetos complejos a tipos JSON nativos.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    fecha_dt = datetime(2026, 10, 20, 10, 0, 0)
    fecha_res = FechaResultado(
        fecha=fecha_dt, fuente="EXIF", es_respaldo=False
    )

    # Act
    resultado = _convertir_a_json_compatible(fecha_res)

    # Assert
    assert isinstance(resultado, dict)
    assert resultado["fecha"] == "2026-10-20T10:00:00"
    assert resultado["fuente"] == "EXIF"
    assert resultado["es_respaldo"] is False


def test_exportar_plan_json_crea_archivo_valido(tmp_path: Path) -> None:
    """Verifica que exportar_plan_json guarde un archivo JSON estructurado.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    salida_json = tmp_path / "reportes" / "plan.json"

    fecha_res = FechaResultado(
        fecha=datetime(2026, 10, 20, 12, 0),
        fuente="DateTimeOriginal",
        es_respaldo=False,
    )

    operacion = OperacionPlan(
        origen=origen / "foto.jpg",
        destino=destino / "2026" / "10" / "20" / "IMAGEN" / "foto.jpg",
        categoria=TipoArchivo.IMAGEN,
        fecha_resultado=fecha_res,
        sidecars_asociados=[],
        accion=AccionPlan.MOVER,
        advertencias=[],
    )

    plan = PlanOrganizacion(
        directorio_origen=origen,
        directorio_destino=destino,
        operaciones=[operacion],
        sidecars_omitidos=[],
        desconocidos=[],
    )

    # Act
    exportar_plan_json(plan, salida_json)

    # Assert
    assert salida_json.exists()
    contenido = json.loads(salida_json.read_text(encoding="utf-8"))
    assert contenido["directorio_origen"] == origen.as_posix()
    assert contenido["directorio_destino"] == destino.as_posix()
    assert len(contenido["operaciones"]) == 1
    assert contenido["operaciones"][0]["accion"] == "MOVER"
