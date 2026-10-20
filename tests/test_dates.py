"""
Pruebas unitarias para el módulo de resolución de fechas.
"""

from datetime import datetime
from pathlib import Path

from mulita.dates import FechaResultado, resolver_fecha_archivo
from mulita.scanner import TipoArchivo


def test_resolver_fecha_imagen_exif(tmp_path: Path) -> None:
    """Comprueba la selección de DateTimeOriginal para imágenes."""
    archivo = tmp_path / "foto.jpg"
    archivo.touch()

    metadatos = {"DateTimeOriginal": "2024:05:15 10:30:00"}
    res: FechaResultado = resolver_fecha_archivo(archivo, TipoArchivo.IMAGEN, metadatos)

    assert res.fecha == datetime(2024, 5, 15, 10, 30, 0)
    assert res.fuente == "DateTimeOriginal"
    assert res.es_respaldo is False


def test_resolver_fecha_video_prioridad(tmp_path: Path) -> None:
    """Comprueba que MediaCreateDate tenga prioridad en videos."""
    archivo = tmp_path / "video.mp4"
    archivo.touch()

    metadatos = {
        "CreateDate": "2023:01:01 12:00:00",
        "MediaCreateDate": "2024:08:20 18:45:10",
    }
    res: FechaResultado = resolver_fecha_archivo(archivo, TipoArchivo.VIDEO, metadatos)

    assert res.fecha == datetime(2024, 8, 20, 18, 45, 10)
    assert res.fuente == "MediaCreateDate"
    assert res.es_respaldo is False


def test_resolver_fecha_fallback(tmp_path: Path) -> None:
    """Comprueba el respaldo a la fecha de modificación del sistema."""
    archivo = tmp_path / "sin_exif.jpg"
    archivo.touch()

    res: FechaResultado = resolver_fecha_archivo(archivo, TipoArchivo.IMAGEN, {})

    assert isinstance(res.fecha, datetime)
    assert res.fuente == "FileModifyDate"
    assert res.es_respaldo is True
