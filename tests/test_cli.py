"""
Pruebas de integración para la interfaz de línea de comandos (CLI).
"""

from typer.testing import CliRunner

from mulita.cli import app

runner = CliRunner()


def test_cli_ayuda_base() -> None:
    """
    Verifica que la ayuda principal de la CLI muestre los tres subcomandos
    del alcance del MVP: scan, plan y run.
    """
    # Se fija el ancho de columna en el entorno simulado para evitar que Rich
    # trunca la tabla de comandos durante la ejecución de pytest.
    result = runner.invoke(app, ["--help"], env={"COLUMNS": "120"})

    assert result.exit_code == 0
    assert "Mulita" in result.stdout
    assert "scan" in result.stdout
    assert "plan" in result.stdout
    assert "run" in result.stdout
