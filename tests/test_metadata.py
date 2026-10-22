"""Pruebas para extracción y validación de metadatos."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mulita.metadata import extraer_metadatos, verificar_exiftool


def test_verificar_exiftool_presente() -> None:
    """Verifica que se detecte ExifTool cuando está disponible."""
    with patch("shutil.which", return_value="/usr/bin/exiftool"):
        resultado = verificar_exiftool()

    assert resultado is True


def test_verificar_exiftool_ausente() -> None:
    """Verifica que se informe cuando ExifTool no está disponible."""
    # Arrange & Act
    with patch("shutil.which", return_value=None):
        resultado = verificar_exiftool()

    # Assert
    assert resultado is False


def test_extraer_metadatos_sin_exiftool(tmp_path: Path) -> None:
    """Verifica que no haya metadatos si ExifTool no está disponible.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    archivo = tmp_path / "prueba.jpg"
    archivo.write_text("dummy")

    # Act
    with patch("mulita.metadata.verificar_exiftool", return_value=False):
        resultado = extraer_metadatos([archivo])

    # Assert
    assert resultado == {archivo: {}}


def test_extraer_metadatos_exito_mock_subprocess(tmp_path: Path) -> None:
    """Verifica que la salida JSON de ExifTool se asigne a cada ruta.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    foto = tmp_path / "foto.jpg"
    foto.touch()

    # Las barras inclinadas evitan escapes inválidos en JSON en Windows.
    ruta_posix = foto.resolve().as_posix()

    json_salida = f"""[
      {{
        "SourceFile": "{ruta_posix}",
        "DateTimeOriginal": "2023:10:20 12:00:00",
        "CreateDate": "2023:10:20 12:00:00"
      }}
    ]"""

    mock_process = MagicMock()
    mock_process.stdout = json_salida

    # Act
    with (
        patch("mulita.metadata.verificar_exiftool", return_value=True),
        patch("subprocess.run", return_value=mock_process),
    ):
        resultado = extraer_metadatos([foto])

    # Assert
    assert foto in resultado
    assert resultado[foto]["DateTimeOriginal"] == "2023:10:20 12:00:00"
    assert "SourceFile" not in resultado[foto]


def test_extraer_metadatos_informa_avance_por_lote(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Actualiza el avance a medida que ExifTool completa cada lote."""
    rutas = [tmp_path / "foto1.jpg", tmp_path / "foto2.jpg"]
    monkeypatch.setattr("mulita.metadata.TAMANO_LOTE_METADATOS", 1)
    avances: list[tuple[str, int, int | None]] = []

    with (
        patch("mulita.metadata.verificar_exiftool", return_value=True),
        patch(
            "mulita.metadata.subprocess.run",
            return_value=MagicMock(stdout="[]"),
        ) as ejecutar,
    ):
        resultado = extraer_metadatos(
            rutas,
            progreso=lambda etapa, completados, total: avances.append(
                (etapa, completados, total)
            ),
        )

    assert ejecutar.call_count == 2
    assert resultado == {ruta: {} for ruta in rutas}
    assert [avance[1:] for avance in avances] == [
        (0, 2),
        (1, 2),
        (2, 2),
    ]
