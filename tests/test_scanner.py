"""
Pruebas unitarias para el módulo scanner.py
"""

from pathlib import Path

from mulita.scanner import TipoArchivo, clasificar_extension, escanear_directorio


def test_clasificar_extension_mayusculas():
    """Verifica que la clasificación sea insensible a mayúsculas/minúsculas."""
    assert clasificar_extension(".JPG") == TipoArchivo.IMAGEN
    assert clasificar_extension(".CR2") == TipoArchivo.RAW
    assert clasificar_extension(".mkv") == TipoArchivo.VIDEO
    assert clasificar_extension(".XMP") == TipoArchivo.AUXILIAR
    assert clasificar_extension(".txt") == TipoArchivo.DESCONOCIDO


def test_escanear_directorio_basico(tmp_path: Path):
    """Verifica que el escaneo detecte archivos válidos en subcarpetas."""
    # Crear estructura de prueba
    (tmp_path / "foto.jpg").touch()
    subdir = tmp_path / "viaje"
    subdir.mkdir()
    (subdir / "video.MP4").touch()
    (subdir / "documento.pdf").touch()  # Desconocido
    (subdir / ".oculto.jpg").touch()  # Debe ignorarse

    resultados = escanear_directorio(tmp_path)

    assert len(resultados) == 3  # foto, video, documento
    tipos = {res.tipo for res in resultados}
    assert TipoArchivo.IMAGEN in tipos
    assert TipoArchivo.VIDEO in tipos
    assert TipoArchivo.DESCONOCIDO in tipos


def test_escanear_ignora_destino(tmp_path: Path):
    """Verifica que no se escanee la carpeta de destino si está dentro del origen."""
    (tmp_path / "origen.jpg").touch()

    destino = tmp_path / "destino_ordenado"
    destino.mkdir()
    (destino / "no_escanear.jpg").touch()

    resultados = escanear_directorio(tmp_path, destino_ignorar=destino)

    assert len(resultados) == 1
    assert resultados[0].ruta.name == "origen.jpg"
