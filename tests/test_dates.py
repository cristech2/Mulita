"""
Pruebas unitarias para la resolución y priorización de fechas (dates.py).
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from mulita.dates import FechaResultado, resolver_fecha_archivo
from mulita.models import TipoArchivo


def test_resolver_fecha_imagen_con_datetime_original() -> None:
    """
    Verifica que se priorice DateTimeOriginal sobre otras fuentes en imágenes.
    """
    # Arrange
    ruta = Path("/fotos/foto.jpg")
    metadatos = {"DateTimeOriginal": "2023:05:15 14:30:00"}

    # Act
    res = resolver_fecha_archivo(ruta, TipoArchivo.IMAGEN, metadatos)

    # Assert
    assert isinstance(res, FechaResultado)
    assert res.fecha == datetime(2023, 5, 15, 14, 30, 0)
    assert res.fuente == "DateTimeOriginal"
    assert not res.es_respaldo


def test_resolver_fecha_video_prioriza_mediacreatedate() -> None:
    """
    Verifica que en videos se priorice MediaCreateDate frente a CreateDate.
    """
    # Arrange
    ruta = Path("/videos/clip.mp4")
    metadatos = {
        "MediaCreateDate": "2022:01:01 10:00:00",
        "CreateDate": "2022:01:02 10:00:00",
    }

    # Act
    res = resolver_fecha_archivo(ruta, TipoArchivo.VIDEO, metadatos)

    # Assert
    assert res.fecha == datetime(2022, 1, 1, 10, 0, 0)
    assert res.fuente == "MediaCreateDate"
    assert not res.es_respaldo


def test_resolver_fecha_respaldo_filemodifydate(tmp_path: Path) -> None:
    """
    Verifica que ante la ausencia de metadatos EXIF se utilice
    la fecha de modificación del archivo (FileModifyDate) como respaldo.
    """
    # Arrange
    archivo_tmp = tmp_path / "imagen_sin_exif.jpg"
    archivo_tmp.touch()
    metadatos: dict[str, str] = {}

    fecha_ficticia = datetime(2025, 11, 7, 8, 30, 0)

    # Act
    with patch("mulita.dates._obtener_fecha_modificacion", return_value=fecha_ficticia):
        res = resolver_fecha_archivo(archivo_tmp, TipoArchivo.IMAGEN, metadatos)

    # Assert
    assert res.fecha == fecha_ficticia
    assert res.fuente == "FileModifyDate"
    assert res.es_respaldo
