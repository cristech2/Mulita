"""
Pruebas unitarias para el módulo de escaneo y clasificación (scanner.py).
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mulita.models import EstadoAsociacion, ResultadoEscaneo, TipoArchivo
from mulita.scanner import (
    analizar_directorio,
    clasificar_extension,
    escanear_directorio,
)


@pytest.mark.parametrize(
    "extension, tipo_esperado",
    [
        (".jpg", TipoArchivo.IMAGEN),
        (".JPEG", TipoArchivo.IMAGEN),
        (".cr2", TipoArchivo.RAW),
        (".ARW", TipoArchivo.RAW),
        (".mp4", TipoArchivo.VIDEO),
        (".MOV", TipoArchivo.VIDEO),
        (".xmp", TipoArchivo.AUXILIAR),
        (".RRDATA", TipoArchivo.AUXILIAR),
        (".pdf", TipoArchivo.DESCONOCIDO),
        (".txt", TipoArchivo.DESCONOCIDO),
    ],
)
def test_clasificar_extension_tipos_soportados(
    extension: str, tipo_esperado: TipoArchivo
) -> None:
    """
    Verifica la correcta clasificación de extensiones soportadas
    y desconocidas, tanto en mayúsculas como en minúsculas.
    """
    # Act
    tipo_obtenido = clasificar_extension(extension)

    # Assert
    assert tipo_obtenido == tipo_esperado


def test_escanear_directorio_ruta_inexistente() -> None:
    """
    Verifica que escanear una ruta inexistente devuelva una lista vacía.
    """
    # Arrange
    ruta_inexistente = Path("/ruta/que/no/existe/en/sistema")

    # Act
    archivos = escanear_directorio(ruta_inexistente)

    # Assert
    assert archivos == []


def test_escanear_directorio_omite_ocultos(tmp_path: Path) -> None:
    """
    Verifica que el escaneo omita archivos y directorios ocultos (que inicien
    con '.').
    """
    # Arrange
    foto_normal = tmp_path / "foto.jpg"
    foto_normal.touch()

    foto_oculta = tmp_path / ".foto_oculta.jpg"
    foto_oculta.touch()

    dir_oculto = tmp_path / ".carpeta_oculta"
    dir_oculto.mkdir()
    foto_en_dir_oculto = dir_oculto / "imagen.png"
    foto_en_dir_oculto.touch()

    # Act
    archivos = escanear_directorio(tmp_path)

    # Assert
    rutas_encontradas = [a.ruta for a in archivos]
    assert foto_normal.resolve() in rutas_encontradas
    assert foto_oculta.resolve() not in rutas_encontradas
    assert foto_en_dir_oculto.resolve() not in rutas_encontradas


def test_escanear_directorio_excluye_destino_anidado(tmp_path: Path) -> None:
    """
    Verifica que el escaneo ignore el contenido del directorio de destino si
    se encuentra anidado dentro del directorio de origen.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()

    destino = origen / "organizado"
    destino.mkdir()

    foto_origen = origen / "foto1.jpg"
    foto_origen.touch()

    foto_destino = destino / "foto_organizada.jpg"
    foto_destino.touch()

    # Act
    archivos = escanear_directorio(origen, destino_ignorar=destino)

    # Assert
    rutas_encontradas = [a.ruta for a in archivos]
    assert foto_origen.resolve() in rutas_encontradas
    assert foto_destino.resolve() not in rutas_encontradas


@patch("mulita.scanner.extraer_metadatos")
def test_analizar_directorio_retorna_resultado_escaneo_completo(
    mock_extraer_metadatos: MagicMock, tmp_path: Path
) -> None:
    """
    Verifica que analizar_directorio retorne una estructura ResultadoEscaneo
    con los grupos de medios, sidecars asociados y archivos desconocidos.
    """
    # Arrange
    mock_extraer_metadatos.return_value = {}

    foto = tmp_path / "foto1.jpg"
    foto.touch()

    sidecar = tmp_path / "foto1.xmp"
    sidecar.touch()

    video = tmp_path / "clip.mp4"
    video.touch()

    desconocido = tmp_path / "documento.pdf"
    desconocido.touch()

    # Act
    resultado = analizar_directorio(tmp_path)

    # Assert
    assert isinstance(resultado, ResultadoEscaneo)
    assert len(resultado.grupos) == 2

    grupo_foto = next(
        g for g in resultado.grupos if g.principal.archivo.ruta == foto.resolve()
    )
    assert len(grupo_foto.sidecars) == 1
    assert grupo_foto.sidecars[0].archivo.ruta == sidecar.resolve()

    assert len(resultado.desconocidos) == 1
    assert resultado.desconocidos[0].archivo.ruta == desconocido.resolve()
    assert len(resultado.sidecars_no_asociados) == 0


@patch("mulita.scanner.extraer_metadatos")
def test_analizar_directorio_clasifica_sidecars_huerfanos(
    mock_extraer_metadatos: MagicMock, tmp_path: Path
) -> None:
    """
    Verifica que los sidecars sin archivo principal en el directorio sean
    registrados en la lista sidecars_no_asociados con estado HUERFANO.
    """
    # Arrange
    mock_extraer_metadatos.return_value = {}

    sidecar_huerfano = tmp_path / "huerfano.xmp"
    sidecar_huerfano.touch()

    # Act
    resultado = analizar_directorio(tmp_path)

    # Assert
    assert len(resultado.grupos) == 0
    assert len(resultado.sidecars_no_asociados) == 1
    assert (
        resultado.sidecars_no_asociados[0].archivo.archivo.ruta
        == sidecar_huerfano.resolve()
    )
    assert resultado.sidecars_no_asociados[0].estado == EstadoAsociacion.HUERFANO


@patch("mulita.scanner.extraer_metadatos")
def test_analizar_directorio_filtra_rutas_para_metadatos(
    mock_extraer_metadatos: MagicMock, tmp_path: Path
) -> None:
    """
    Verifica que la extracción de metadatos mediante ExifTool se consulte
    únicamente para archivos de tipo IMAGEN, RAW y VIDEO.
    """
    # Arrange
    mock_extraer_metadatos.return_value = {}

    foto = tmp_path / "foto.jpg"
    foto.touch()

    raw = tmp_path / "foto.cr2"
    raw.touch()

    auxiliar = tmp_path / "foto.xmp"
    auxiliar.touch()

    desconocido = tmp_path / "notas.txt"
    desconocido.touch()

    # Act
    analizar_directorio(tmp_path)

    # Assert
    mock_extraer_metadatos.assert_called_once()
    rutas_enviadas = mock_extraer_metadatos.call_args[0][0]

    assert len(rutas_enviadas) == 2
    assert foto.resolve() in rutas_enviadas
    assert raw.resolve() in rutas_enviadas
    assert auxiliar.resolve() not in rutas_enviadas
    assert desconocido.resolve() not in rutas_enviadas
