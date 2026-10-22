"""Pruebas del caché persistente de metadatos."""

from pathlib import Path
from unittest.mock import patch

from mulita.metadata_cache import CacheMetadatos
from mulita.scanner import analizar_directorio


def test_cache_reutiliza_metadatos_si_el_archivo_no_cambia(
    tmp_path: Path,
) -> None:
    """Recupera los metadatos almacenados cuando la firma coincide."""
    archivo = tmp_path / "foto.jpg"
    archivo.write_bytes(b"contenido")
    ruta_db = tmp_path / "cache.sqlite3"
    metadatos = {"DateTimeOriginal": "2024:01:02 03:04:05"}

    cache = CacheMetadatos(ruta_db)
    assert cache.obtener([archivo]) == {}
    cache.guardar({archivo: metadatos})
    cache.cerrar()

    cache = CacheMetadatos(ruta_db)
    assert cache.obtener([archivo]) == {archivo: metadatos}
    cache.cerrar()


def test_cache_invalida_metadatos_si_cambia_el_archivo(
    tmp_path: Path,
) -> None:
    """No reutiliza entradas cuando cambian tamaño o fecha de modificación."""
    archivo = tmp_path / "foto.jpg"
    archivo.write_bytes(b"original")
    ruta_db = tmp_path / "cache.sqlite3"

    cache = CacheMetadatos(ruta_db)
    cache.obtener([archivo])
    cache.guardar({archivo: {"DateTimeOriginal": "2024:01:02 03:04:05"}})
    cache.cerrar()

    archivo.write_bytes(b"contenido actualizado")
    cache = CacheMetadatos(ruta_db)
    assert cache.obtener([archivo]) == {}
    cache.cerrar()


def test_analizar_directorio_reutiliza_cache_entre_ejecuciones(
    tmp_path: Path,
) -> None:
    """Escaneos repetidos evitan volver a extraer metadatos sin cambios."""
    origen = tmp_path / "origen"
    origen.mkdir()
    foto = origen / "foto.jpg"
    foto.write_bytes(b"imagen")
    ruta_db = tmp_path / "cache.sqlite3"
    metadatos = {"DateTimeOriginal": "2024:01:02 03:04:05"}

    with patch(
        "mulita.scanner.extraer_metadatos",
        return_value={foto.resolve(): metadatos},
    ) as extraer:
        analizar_directorio(origen, ruta_cache=ruta_db)
        analizar_directorio(origen, ruta_cache=ruta_db)

    extraer.assert_called_once_with([foto.resolve()], progreso=None)
