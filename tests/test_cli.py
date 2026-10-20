"""Pruebas para la interfaz de línea de comandos."""

from pathlib import Path

from typer.testing import CliRunner

from mulita.cli import app

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
