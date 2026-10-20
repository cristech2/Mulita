"""
Pruebas de integración para la interfaz de línea de comandos (CLI).
"""

from typer.testing import CliRunner

from mulita.cli import app

runner = CliRunner()


def test_cli_ayuda_base():
    """
    Verifica que al ejecutar la CLI se muestre la ayuda correctamente.
    """
    # Invocamos explícitamente la bandera de ayuda
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Mulita: Organizador" in result.stdout
    assert "scan" in result.stdout
    assert "plan" in result.stdout
    assert "run" in result.stdout
