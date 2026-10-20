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
