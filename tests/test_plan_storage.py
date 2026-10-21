"""Pruebas para la persistencia, carga y búsqueda de planes en JSON."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from mulita.models import (
    AccionPlan,
    EstadoEjecucionOperacion,
    FechaResultado,
    OperacionPlan,
    PlanOrganizacion,
    RegistroOperacionArchivo,
    ResultadoEjecucion,
    TipoArchivo,
)
from mulita.plan_storage import (
    _convertir_a_json_compatible,
    buscar_archivos_plan,
    cargar_plan_json,
    exportar_plan_json,
    exportar_resultado_ejecucion_json,
)


def test_convertir_a_json_compatible_tipos_complejos() -> None:
    """Verifica la conversión de objetos complejos a tipos JSON nativos."""
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


def test_exportar_y_cargar_plan_json_ciclo_completo(tmp_path: Path) -> None:
    """Verifica la serialización y posterior deserialización exacta de un plan.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    salida_json = tmp_path / "plan.json"

    fecha_res = FechaResultado(
        fecha=datetime(2026, 10, 20, 12, 0),
        fuente="DateTimeOriginal",
        es_respaldo=False,
    )

    origen_p = origen / "foto.jpg"
    destino_p = destino / "2026" / "10" / "20" / "IMAGEN" / "foto.jpg"
    origen_s = origen / "foto.xmp"
    destino_s = destino / "2026" / "10" / "20" / "IMAGEN" / "foto.xmp"

    operacion = OperacionPlan(
        origen=origen_p,
        destino=destino_p,
        categoria=TipoArchivo.IMAGEN,
        fecha_resultado=fecha_res,
        sidecars_asociados=[(origen_s, destino_s)],
        accion=AccionPlan.MOVER,
        advertencias=["Advertencia test"],
    )

    plan_original = PlanOrganizacion(
        directorio_origen=origen,
        directorio_destino=destino,
        operaciones=[operacion],
        sidecars_omitidos=[],
        desconocidos=[],
    )

    # Act: Exportar y Cargar
    exportar_plan_json(plan_original, salida_json)
    plan_cargado = cargar_plan_json(salida_json)

    # Assert
    assert isinstance(plan_cargado, PlanOrganizacion)
    assert plan_cargado.directorio_origen == origen
    assert plan_cargado.directorio_destino == destino
    assert len(plan_cargado.operaciones) == 1

    op = plan_cargado.operaciones[0]
    assert op.origen == origen_p
    assert op.destino == destino_p
    assert op.categoria == TipoArchivo.IMAGEN
    assert op.accion == AccionPlan.MOVER
    assert op.fecha_resultado.fecha == datetime(2026, 10, 20, 12, 0)
    assert len(op.sidecars_asociados) == 1
    assert op.sidecars_asociados[0] == (origen_s, destino_s)


def test_exportar_resultado_ejecucion_json_guarda_estructura(
    tmp_path: Path,
) -> None:
    """Verifica que el reporte de auditoría de ejecución se exporte a JSON.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    salida_json = tmp_path / "reporte_ejecucion.json"
    ahora = datetime(2026, 10, 20, 15, 30, 0)

    registro = RegistroOperacionArchivo(
        origen=tmp_path / "foto.jpg",
        destino=tmp_path / "destino.jpg",
        estado=EstadoEjecucionOperacion.EXITOSO,
        timestamp=ahora,
        es_sidecar=False,
    )

    resultado = ResultadoEjecucion(
        procesados_exitosamente=1,
        fallidos=0,
        errores=[],
        registros_detallados=[registro],
    )

    # Act
    exportar_resultado_ejecucion_json(resultado, salida_json)

    # Assert
    assert salida_json.exists()
    with salida_json.open("r", encoding="utf-8") as f:
        contenido = json.load(f)

    assert contenido["procesados_exitosamente"] == 1
    assert contenido["fallidos"] == 0
    assert len(contenido["registros_detallados"]) == 1
    reg_json = contenido["registros_detallados"][0]
    assert reg_json["estado"] == "EXITOSO"
    assert reg_json["timestamp"] == "2026-10-20T15:30:00"


def test_cargar_plan_json_archivo_inexistente(tmp_path: Path) -> None:
    """Verifica que un archivo JSON inexistente lance FileNotFoundError.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    ruta_inexistente = tmp_path / "no_existe.json"

    # Act & Assert
    with pytest.raises(FileNotFoundError, match="no existe"):
        cargar_plan_json(ruta_inexistente)


def test_cargar_plan_json_formato_invalido(tmp_path: Path) -> None:
    """Verifica que un JSON con formato o claves incorrectas lance ValueError.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    json_invalido = tmp_path / "invalido.json"
    json_invalido.write_text('{"clave": "valor"}', encoding="utf-8")

    # Act & Assert
    with pytest.raises(ValueError, match="no tiene un formato de plan válido"):
        cargar_plan_json(json_invalido)


def test_buscar_archivos_plan_encuentra_solo_json_validos(
    tmp_path: Path,
) -> None:
    """Verifica la localización automática de archivos JSON de plan válidos.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    plan_valido = tmp_path / "plan_1.json"
    contenido_valido = {
        "directorio_origen": "/origen",
        "directorio_destino": "/destino",
        "operaciones": [],
    }
    plan_valido.write_text(json.dumps(contenido_valido), encoding="utf-8")

    otro_json = tmp_path / "datos.json"
    otro_json.write_text('{"usuario": "test"}', encoding="utf-8")

    # Act
    planes_encontrados = buscar_archivos_plan(tmp_path)

    # Assert
    assert len(planes_encontrados) == 1
    assert planes_encontrados[0] == plan_valido
