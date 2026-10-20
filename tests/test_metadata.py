"""
Pruebas unitarias para el módulo de extracción de metadatos.
"""

from pathlib import Path
from unittest.mock import patch

from mulita.metadata import extraer_metadatos, verificar_exiftool


def test_verificar_exiftool_presente() -> None:
    """Verifica la respuesta cuando ExifTool está en el PATH."""
    with patch("shutil.which", return_value="/usr/bin/exiftool"):
        assert verificar_exiftool() is True


def test_verificar_exiftool_ausente() -> None:
    """Verifica la respuesta cuando ExifTool no está en el PATH."""
    with patch("shutil.which", return_value=None):
        assert verificar_exiftool() is False


def test_extraer_metadatos_sin_exiftool(tmp_path: Path) -> None:
    """Comprueba que retorne diccionarios vacíos si ExifTool no está disponible."""
    archivo = tmp_path / "prueba.jpg"
    archivo.write_text("dummy")

    with patch("mulita.metadata.verificar_exiftool", return_value=False):
        resultado = extraer_metadatos([archivo])
        assert resultado == {archivo: {}}
