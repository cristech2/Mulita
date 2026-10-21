"""Pruebas unitarias para el ejecutor seguro de planes de organización."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from mulita.executor import (
    _ejecutar_operacion_individual,
    _validar_existencia_origen_y_destino,
    ejecutar_plan,
)
from mulita.models import (
    AccionPlan,
    EstadoEjecucionOperacion,
    FechaResultado,
    OperacionPlan,
    PlanOrganizacion,
    ResultadoEjecucion,
    TipoArchivo,
)


@pytest.fixture
def fecha_dummy() -> FechaResultado:
    """Proporciona una instancia base de FechaResultado para pruebas.

    Returns:
        FechaResultado: Instancia dummy de fecha.
    """
    return FechaResultado(
        fecha=datetime(2026, 10, 20, 10, 0),
        fuente="DateTimeOriginal",
        es_respaldo=False,
    )


def test_validar_existencia_origen_inexistente(tmp_path: Path) -> None:
    """Verifica que un archivo de origen inexistente lance FileNotFoundError.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen_inexistente = tmp_path / "origen.jpg"
    destino = tmp_path / "destino.jpg"

    # Act & Assert
    with pytest.raises(FileNotFoundError, match="El archivo origen no existe"):
        _validar_existencia_origen_y_destino(origen_inexistente, destino)


def test_validar_existencia_destino_ya_existente(tmp_path: Path) -> None:
    """Verifica que un destino ya existente lance FileExistsError.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen.jpg"
    origen.touch()

    destino = tmp_path / "destino.jpg"
    destino.touch()

    # Act & Assert
    with pytest.raises(FileExistsError, match="El archivo destino ya existe"):
        _validar_existencia_origen_y_destino(origen, destino)


def test_ejecutar_operacion_individual_mueve_principal_y_sidecars(
    tmp_path: Path, fecha_dummy: FechaResultado
) -> None:
    """Verifica el movimiento físico exitoso del principal y sus sidecars.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        fecha_dummy (FechaResultado): Fixture de fecha de prueba.
    """
    # Arrange
    dir_origen = tmp_path / "origen"
    dir_origen.mkdir()
    dir_destino = tmp_path / "destino" / "2026" / "10" / "20" / "IMAGEN"

    origen_p = dir_origen / "foto.jpg"
    origen_p.write_bytes(b"contenido_imagen")
    origen_s = dir_origen / "foto.xmp"
    origen_s.write_bytes(b"contenido_sidecar")

    destino_p = dir_destino / "foto.jpg"
    destino_s = dir_destino / "foto.xmp"

    operacion = OperacionPlan(
        origen=origen_p,
        destino=destino_p,
        categoria=TipoArchivo.IMAGEN,
        fecha_resultado=fecha_dummy,
        sidecars_asociados=[(origen_s, destino_s)],
        accion=AccionPlan.MOVER,
    )

    # Act
    registros = _ejecutar_operacion_individual(operacion)

    # Assert
    assert not origen_p.exists()
    assert not origen_s.exists()
    assert destino_p.exists()
    assert destino_s.exists()
    assert len(registros) == 2
    assert all(r.estado == EstadoEjecucionOperacion.EXITOSO for r in registros)


def test_ejecutar_operacion_individual_falla_si_sidecar_origen_no_existe(
    tmp_path: Path, fecha_dummy: FechaResultado
) -> None:
    """Verifica que si un sidecar no existe en origen se aborte el traslado antes de mover nada.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        fecha_dummy (FechaResultado): Fixture de fecha de prueba.
    """
    # Arrange
    dir_origen = tmp_path / "origen"
    dir_origen.mkdir()
    dir_destino = tmp_path / "destino"

    origen_p = dir_origen / "foto.jpg"
    origen_p.touch()

    origen_s_inexistente = dir_origen / "foto.xmp"
    destino_p = dir_destino / "foto.jpg"
    destino_s = dir_destino / "foto.xmp"

    operacion = OperacionPlan(
        origen=origen_p,
        destino=destino_p,
        categoria=TipoArchivo.IMAGEN,
        fecha_resultado=fecha_dummy,
        sidecars_asociados=[(origen_s_inexistente, destino_s)],
        accion=AccionPlan.MOVER,
    )

    # Act & Assert
    with pytest.raises(FileNotFoundError):
        _ejecutar_operacion_individual(operacion)

    # Verificar que el principal no se haya movido si falló la validación previa
    assert origen_p.exists()
    assert not destino_p.exists()


def test_ejecutar_operacion_individual_rollback_exitoso_al_fallar_sidecar(
    tmp_path: Path, fecha_dummy: FechaResultado
) -> None:
    """Verifica que si falla el traslado de un sidecar, se revierta el traslado del principal.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        fecha_dummy (FechaResultado): Fixture de fecha de prueba.
    """
    # Arrange
    dir_origen = tmp_path / "origen"
    dir_origen.mkdir()
    dir_destino = tmp_path / "destino"

    origen_p = dir_origen / "foto.jpg"
    origen_p.write_bytes(b"imagen")
    origen_s = dir_origen / "foto.xmp"
    origen_s.write_bytes(b"sidecar")

    destino_p = dir_destino / "foto.jpg"
    destino_s = dir_destino / "foto.xmp"

    operacion = OperacionPlan(
        origen=origen_p,
        destino=destino_p,
        categoria=TipoArchivo.IMAGEN,
        fecha_resultado=fecha_dummy,
        sidecars_asociados=[(origen_s, destino_s)],
        accion=AccionPlan.MOVER,
    )

    # Simular fallo en el traslado del sidecar tras haber movido exitosamente el principal
    def efecto_traslado(orig, dest):
        if orig == origen_s:
            raise OSError("Error simulado de E/S al mover sidecar")
        dest.parent.mkdir(parents=True, exist_ok=True)
        orig.rename(dest)

    with patch(
        "mulita.executor._trasladar_y_verificar", side_effect=efecto_traslado
    ):
        with pytest.raises(
            RuntimeError, match="Operación revertida exitosamente"
        ):
            _ejecutar_operacion_individual(operacion)

    # Assert: El principal debe haber regresado a su origen gracias al rollback
    assert origen_p.exists()
    assert not destino_p.exists()


def test_ejecutar_plan_completado_con_exito_y_registros_detallados(
    tmp_path: Path, fecha_dummy: FechaResultado
) -> None:
    """Verifica la ejecución exitosa de un plan y la generación de registros detallados.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        fecha_dummy (FechaResultado): Fixture de fecha de prueba.
    """
    # Arrange
    dir_origen = tmp_path / "origen"
    dir_origen.mkdir()
    dir_destino = tmp_path / "destino"

    foto1_orig = dir_origen / "foto1.jpg"
    foto1_orig.write_bytes(b"1")
    foto2_orig = dir_origen / "foto2.jpg"
    foto2_orig.write_bytes(b"2")

    op1 = OperacionPlan(
        origen=foto1_orig,
        destino=dir_destino / "foto1.jpg",
        categoria=TipoArchivo.IMAGEN,
        fecha_resultado=fecha_dummy,
        sidecars_asociados=[],
        accion=AccionPlan.MOVER,
    )
    op2 = OperacionPlan(
        origen=foto2_orig,
        destino=dir_destino / "foto2.jpg",
        categoria=TipoArchivo.IMAGEN,
        fecha_resultado=fecha_dummy,
        sidecars_asociados=[],
        accion=AccionPlan.MOVER,
    )

    plan = PlanOrganizacion(
        directorio_origen=dir_origen,
        directorio_destino=dir_destino,
        operaciones=[op1, op2],
        sidecars_omitidos=[],
        desconocidos=[],
    )

    # Act
    resultado = ejecutar_plan(plan)

    # Assert
    assert isinstance(resultado, ResultadoEjecucion)
    assert resultado.procesados_exitosamente == 2
    assert resultado.fallidos == 0
    assert len(resultado.errores) == 0
    assert len(resultado.registros_detallados) == 2
    assert all(
        r.estado == EstadoEjecucionOperacion.EXITOSO
        for r in resultado.registros_detallados
    )


def test_ejecutar_plan_registra_operaciones_omitidas(
    tmp_path: Path, fecha_dummy: FechaResultado
) -> None:
    """Verifica que las operaciones marcadas como OMITIR generen registros OMITIDO.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        fecha_dummy (FechaResultado): Fixture de fecha de prueba.
    """
    # Arrange
    dir_origen = tmp_path / "origen"
    dir_origen.mkdir()
    dir_destino = tmp_path / "destino"

    foto_orig = dir_origen / "foto.jpg"
    foto_orig.touch()

    op_omitir = OperacionPlan(
        origen=foto_orig,
        destino=dir_destino / "foto.jpg",
        categoria=TipoArchivo.IMAGEN,
        fecha_resultado=fecha_dummy,
        sidecars_asociados=[],
        accion=AccionPlan.OMITIR,
    )

    plan = PlanOrganizacion(
        directorio_origen=dir_origen,
        directorio_destino=dir_destino,
        operaciones=[op_omitir],
        sidecars_omitidos=[],
        desconocidos=[],
    )

    # Act
    resultado = ejecutar_plan(plan)

    # Assert
    assert resultado.procesados_exitosamente == 0
    assert resultado.fallidos == 0
    assert len(resultado.registros_detallados) == 1
    assert (
        resultado.registros_detallados[0].estado
        == EstadoEjecucionOperacion.OMITIDO
    )


def test_ejecutar_plan_aisla_fallos_y_marca_recuperacion_manual_si_rollback_falla(
    tmp_path: Path, fecha_dummy: FechaResultado
) -> None:
    """Verifica que si el rollback falla, se marque requiere_recuperacion_manual = True.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        fecha_dummy (FechaResultado): Fixture de fecha de prueba.
    """
    # Arrange
    dir_origen = tmp_path / "origen"
    dir_origen.mkdir()
    dir_destino = tmp_path / "destino"

    foto_orig = dir_origen / "foto.jpg"
    foto_orig.write_bytes(b"data")

    op_fallida = OperacionPlan(
        origen=foto_orig,
        destino=dir_destino / "foto.jpg",
        categoria=TipoArchivo.IMAGEN,
        fecha_resultado=fecha_dummy,
        sidecars_asociados=[],
        accion=AccionPlan.MOVER,
    )

    plan = PlanOrganizacion(
        directorio_origen=dir_origen,
        directorio_destino=dir_destino,
        operaciones=[op_fallida],
        sidecars_omitidos=[],
        desconocidos=[],
    )

    # Simular un error en el traslado principal Y además en la reversión
    with (
        patch(
            "mulita.executor._trasladar_y_verificar",
            side_effect=OSError("Error al mover"),
        ),
        patch(
            "mulita.executor._revertir_movimientos",
            return_value=["Error crítico al deshacer"],
        ),
    ):
        resultado = ejecutar_plan(plan)

    # Assert
    assert resultado.procesados_exitosamente == 0
    assert resultado.fallidos == 1
    assert len(resultado.errores) == 1

    fallo = resultado.errores[0]
    assert fallo.requiere_recuperacion_manual is True
    assert "Rollback incompleto" in fallo.error
    assert (
        resultado.registros_detallados[0].estado
        == EstadoEjecucionOperacion.FALLIDO_RECUPERACION_MANUAL
    )
