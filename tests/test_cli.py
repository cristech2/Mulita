"""Pruebas para la interfaz de línea de comandos."""

from datetime import datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mulita.cli import app
from mulita.models import (
    AccionPlan,
    FechaResultado,
    OperacionPlan,
    PlanOrganizacion,
    TipoArchivo,
)
from mulita.plan_storage import exportar_plan_json

runner = CliRunner()


def test_cli_ayuda_base() -> None:
    """Verifica que la ayuda principal muestre los comandos del MVP."""
    result = runner.invoke(app, ["--help"], env={"COLUMNS": "120"})

    assert result.exit_code == 0
    assert "Mulita" in result.stdout
    assert "scan" in result.stdout
    assert "plan" in result.stdout
    assert "run" in result.stdout


def test_cli_scan_ejecucion_exitosa(tmp_path: Path) -> None:
    """Verifica que ``scan`` analice un directorio y muestre métricas.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    (origen / "foto1.jpg").touch()

    # Act
    result = runner.invoke(app, ["scan", str(origen)])

    # Assert
    assert result.exit_code == 0
    assert "Iniciando escaneo" in result.stdout
    assert "Resumen del escaneo" in result.stdout
    assert "Imágenes:         1" in result.stdout


def test_cli_scan_directorio_inexistente() -> None:
    """Verifica que Typer rechace una carpeta de origen inexistente."""
    # Act
    result = runner.invoke(app, ["scan", "/ruta/inexistente/xyz"])

    # Assert
    assert result.exit_code != 0
    assert (
        "does not exist" in result.output or "Invalid value" in result.output
    )


def test_cli_plan_ejecucion_exitosa(tmp_path: Path) -> None:
    """Verifica que ``plan`` genere un plan de organización correctamente.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()
    (origen / "foto.jpg").touch()

    # Act
    result = runner.invoke(
        app, ["plan", str(origen), "--destino", str(destino)]
    )

    # Assert
    assert result.exit_code == 0
    assert "Generando plan para organizar" in result.stdout
    assert "Resumen del plan de organización" in result.stdout
    assert "Archivos a mover:         1" in result.stdout


def test_cli_plan_con_exportacion_json(tmp_path: Path) -> None:
    """Verifica que ``plan`` exporte JSON cuando se especifica ``--salida``.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()
    (origen / "foto.jpg").touch()
    salida_json = tmp_path / "plan.json"

    # Act
    result = runner.invoke(
        app,
        ["plan", str(origen), "-d", str(destino), "-s", str(salida_json)],
    )

    # Assert
    assert result.exit_code == 0
    assert salida_json.exists()
    assert "Plan exportado exitosamente" in result.stdout


def test_cli_plan_error_rutas_invalidas(tmp_path: Path) -> None:
    """Verifica que ``plan`` rechace origen y destino coincidentes.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()

    # Act
    result = runner.invoke(
        app, ["plan", str(origen), "--destino", str(origen)]
    )

    # Assert
    assert result.exit_code == 1
    assert "Error:" in result.output


def test_cli_run_sin_plan_en_directorio_falla(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica que ``run`` informe error si no hay planes JSON en el directorio.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        monkeypatch (pytest.MonkeyPatch): Fixture para modificar el entorno.
    """
    # Arrange
    monkeypatch.chdir(tmp_path)

    # Act
    result = runner.invoke(app, ["run"])

    # Assert
    assert result.exit_code == 1
    assert "No se encontraron archivos de plan JSON" in result.output


def test_cli_run_simulacion_con_plan_explicito(tmp_path: Path) -> None:
    """Verifica la simulación (--dry-run) especificando la ruta al plan.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()
    foto = origen / "foto.jpg"
    foto.touch()

    salida_plan = tmp_path / "plan_test.json"
    plan = PlanOrganizacion(
        directorio_origen=origen,
        directorio_destino=destino,
        operaciones=[
            OperacionPlan(
                origen=foto,
                destino=destino / "2026" / "10" / "20" / "IMAGEN" / "foto.jpg",
                categoria=TipoArchivo.IMAGEN,
                fecha_resultado=FechaResultado(
                    fecha=datetime(2026, 10, 20),
                    fuente="DateTimeOriginal",
                    es_respaldo=False,
                ),
                sidecars_asociados=[],
                accion=AccionPlan.MOVER,
            )
        ],
        sidecars_omitidos=[],
        desconocidos=[],
    )
    exportar_plan_json(plan, salida_plan)

    # Act
    result = runner.invoke(app, ["run", str(salida_plan)])

    # Assert
    assert result.exit_code == 0
    assert "MODO SIMULACIÓN" in result.stdout
    assert foto.exists()


def test_cli_run_seleccion_interactiva_multiples_planes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica el prompt de selección cuando existen varios planes.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        monkeypatch (pytest.MonkeyPatch): Fixture para modificar el entorno.
    """
    # Arrange
    monkeypatch.chdir(tmp_path)
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()

    plan1 = PlanOrganizacion(
        directorio_origen=origen,
        directorio_destino=destino,
        operaciones=[],
        sidecars_omitidos=[],
        desconocidos=[],
    )
    exportar_plan_json(plan1, tmp_path / "plan1.json")
    exportar_plan_json(plan1, tmp_path / "plan2.json")

    # Act
    result = runner.invoke(app, ["run"], input="2\n")

    # Assert
    assert result.exit_code == 0
    assert "Se encontraron varios archivos de plan" in result.stdout
    assert "MODO SIMULACIÓN" in result.stdout


def test_cli_run_ejecucion_real_cancelada_por_usuario(tmp_path: Path) -> None:
    """Verifica que cancelar la confirmación en --ejecutar no altere archivos.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()

    plan = PlanOrganizacion(
        directorio_origen=origen,
        directorio_destino=destino,
        operaciones=[],
        sidecars_omitidos=[],
        desconocidos=[],
    )
    plan_file = tmp_path / "plan.json"
    exportar_plan_json(plan, plan_file)

    # Act
    result = runner.invoke(
        app, ["run", str(plan_file), "--ejecutar"], input="n\n"
    )

    # Assert
    assert result.exit_code == 0
    assert "Operación cancelada por el usuario" in result.stdout


@pytest.mark.parametrize(
    ("nombre_plan", "identificador_auditoria"),
    [
        ("plan_20261020", "20261020"),
        ("plan_plan_20261020", "plan_20261020"),
    ],
)
def test_cli_run_ejecucion_real_exitosa(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    nombre_plan: str,
    identificador_auditoria: str,
) -> None:
    """Verifica ejecución real y auditoría con varios nombres de plan.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        monkeypatch (pytest.MonkeyPatch): Fixture para modificar el entorno.
        nombre_plan (str): Nombre del plan de entrada.
        identificador_auditoria (str): Identificador esperado del reporte.
    """
    # Arrange
    monkeypatch.chdir(tmp_path)
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()
    foto = origen / "foto.jpg"
    foto.touch()

    destino_foto = destino / "2026" / "10" / "20" / "IMAGEN" / "foto.jpg"

    plan = PlanOrganizacion(
        directorio_origen=origen,
        directorio_destino=destino,
        operaciones=[
            OperacionPlan(
                origen=foto,
                destino=destino_foto,
                categoria=TipoArchivo.IMAGEN,
                fecha_resultado=FechaResultado(
                    fecha=datetime(2026, 10, 20),
                    fuente="DateTimeOriginal",
                    es_respaldo=False,
                ),
                sidecars_asociados=[],
                accion=AccionPlan.MOVER,
            )
        ],
        sidecars_omitidos=[],
        desconocidos=[],
    )
    plan_file = tmp_path / f"{nombre_plan}.json"
    exportar_plan_json(plan, plan_file)

    # Act
    result = runner.invoke(
        app, ["run", str(plan_file), "--ejecutar"], input="y\n"
    )

    # Assert
    assert result.exit_code == 0
    assert "Ejecutando plan de organización" in result.stdout
    assert "Procesados con éxito: 1" in result.stdout
    assert not foto.exists()
    assert destino_foto.exists()
    ruta_auditoria = (
        tmp_path / "reportes" / f"ejecucion_{identificador_auditoria}.json"
    )
    assert ruta_auditoria.exists()
