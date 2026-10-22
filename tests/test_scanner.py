"""Pruebas para el escaneo y la clasificación de archivos."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mulita.models import (
    EXTENSIONES_POR_TIPO,
    EstadoAsociacion,
    ResultadoEscaneo,
    TipoArchivo,
    _crear_mapa_extensiones,
)
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
        (".psd", TipoArchivo.PROYECTO),
        (".PSB", TipoArchivo.PROYECTO),
        (".aff", TipoArchivo.PROYECTO),
        (".afphoto", TipoArchivo.PROYECTO),
        (".afdesign", TipoArchivo.PROYECTO),
        (".afpub", TipoArchivo.PROYECTO),
        (".xcf", TipoArchivo.PROYECTO),
        (".kra", TipoArchivo.PROYECTO),
        (".ai", TipoArchivo.PROYECTO),
        (".indd", TipoArchivo.PROYECTO),
        (".xmp", TipoArchivo.AUXILIAR),
        (".RRDATA", TipoArchivo.AUXILIAR),
        (".pdf", TipoArchivo.DESCONOCIDO),
        (".txt", TipoArchivo.DESCONOCIDO),
    ],
)
def test_clasificar_extension_tipos_soportados(
    extension: str, tipo_esperado: TipoArchivo
) -> None:
    """Verifica la clasificación de extensiones conocidas y desconocidas.

    Args:
        extension (str): Extensión que se va a clasificar.
        tipo_esperado (TipoArchivo): Categoría esperada para la extensión.
    """
    # Act
    tipo_obtenido = clasificar_extension(extension)

    # Assert
    assert tipo_obtenido == tipo_esperado


@pytest.mark.parametrize(
    "extension, tipo_esperado",
    [
        (extension, tipo)
        for tipo, extensiones in EXTENSIONES_POR_TIPO.items()
        for extension in extensiones
    ],
)
def test_clasificar_todas_las_extensiones_declaradas(
    extension: str, tipo_esperado: TipoArchivo
) -> None:
    """Verifica que el clasificador devuelva el tipo esperado."""
    assert clasificar_extension(extension) == tipo_esperado


def test_mapa_extension_rechaza_una_extension_en_varios_tipos() -> None:
    """Verifica que el mapa rechace extensiones asignadas a dos categorías."""
    # Arrange
    extensiones_duplicadas = {
        TipoArchivo.IMAGEN: frozenset({".af"}),
        TipoArchivo.PROYECTO: frozenset({".af"}),
    }

    # Act & Assert
    with pytest.raises(
        ValueError,
        match=r"\.af está asignada a IMAGEN y PROYECTO",
    ):
        _crear_mapa_extensiones(extensiones_duplicadas)


def test_escanear_directorio_ruta_inexistente() -> None:
    """Verifica que una ruta inexistente produzca una lista vacía."""
    # Arrange
    ruta_inexistente = Path("/ruta/que/no/existe/en/sistema")

    # Act
    archivos = escanear_directorio(ruta_inexistente)

    # Assert
    assert archivos == []


def test_escanear_directorio_omite_ocultos(tmp_path: Path) -> None:
    """Verifica que se omitan los archivos y directorios ocultos.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
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


def test_escanear_directorio_informa_archivos_encontrados(
    tmp_path: Path,
) -> None:
    """Informa el conteo acumulado sin inventar un total durante el recorrido."""
    (tmp_path / "foto.jpg").touch()
    (tmp_path / "video.mp4").touch()
    avances: list[tuple[str, int, int | None]] = []

    archivos = escanear_directorio(
        tmp_path,
        progreso=lambda etapa, completados, total: avances.append(
            (etapa, completados, total)
        ),
    )

    assert len(archivos) == 2
    assert [avance[1:] for avance in avances] == [
        (0, None),
        (1, None),
        (2, None),
    ]


def test_escanear_directorio_excluye_destino_anidado(tmp_path: Path) -> None:
    """Verifica que el escaneo excluya el destino anidado en el origen.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
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
    """Verifica el resultado completo del análisis de un directorio.

    Args:
        mock_extraer_metadatos (MagicMock): Mock de la extracción de metadatos.
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    mock_extraer_metadatos.return_value = {}

    foto = tmp_path / "foto1.jpg"
    foto.touch()

    sidecar = tmp_path / "foto1.xmp"
    sidecar.touch()

    video = tmp_path / "clip.mp4"
    video.touch()

    proyecto = tmp_path / "edicion.psd"
    proyecto.touch()

    desconocido = tmp_path / "documento.pdf"
    desconocido.touch()

    # Act
    resultado = analizar_directorio(tmp_path, usar_cache=False)

    # Assert
    assert isinstance(resultado, ResultadoEscaneo)
    assert len(resultado.grupos) == 3

    grupo_foto = next(
        g
        for g in resultado.grupos
        if g.principal.archivo.ruta == foto.resolve()
    )
    assert len(grupo_foto.sidecars) == 1
    assert grupo_foto.sidecars[0].archivo.ruta == sidecar.resolve()

    grupo_proyecto = next(
        g
        for g in resultado.grupos
        if g.principal.archivo.ruta == proyecto.resolve()
    )
    assert grupo_proyecto.principal.archivo.tipo == TipoArchivo.PROYECTO

    assert len(resultado.desconocidos) == 1
    assert resultado.desconocidos[0].archivo.ruta == desconocido.resolve()
    assert len(resultado.sidecars_no_asociados) == 0


@patch("mulita.scanner.extraer_metadatos")
def test_analizar_directorio_clasifica_sidecars_huerfanos(
    mock_extraer_metadatos: MagicMock, tmp_path: Path
) -> None:
    """Verifica que los sidecars sin principal queden como huérfanos.

    Args:
        mock_extraer_metadatos (MagicMock): Mock de la extracción de metadatos.
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    mock_extraer_metadatos.return_value = {}

    sidecar_huerfano = tmp_path / "huerfano.xmp"
    sidecar_huerfano.touch()

    # Act
    resultado = analizar_directorio(tmp_path, usar_cache=False)

    # Assert
    assert len(resultado.grupos) == 0
    assert len(resultado.sidecars_no_asociados) == 1
    assert (
        resultado.sidecars_no_asociados[0].archivo.archivo.ruta
        == sidecar_huerfano.resolve()
    )
    assert (
        resultado.sidecars_no_asociados[0].estado == EstadoAsociacion.HUERFANO
    )


@patch("mulita.scanner.extraer_metadatos")
def test_analizar_directorio_filtra_rutas_para_metadatos(
    mock_extraer_metadatos: MagicMock, tmp_path: Path
) -> None:
    """Verifica que los metadatos se soliciten solo para archivos multimedia.

    Args:
        mock_extraer_metadatos (MagicMock): Mock de la extracción de metadatos.
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    mock_extraer_metadatos.return_value = {}

    foto = tmp_path / "foto.jpg"
    foto.touch()

    raw = tmp_path / "foto.cr2"
    raw.touch()

    auxiliar = tmp_path / "foto.xmp"
    auxiliar.touch()

    proyecto = tmp_path / "edicion.psd"
    proyecto.touch()

    desconocido = tmp_path / "notas.txt"
    desconocido.touch()

    # Act
    analizar_directorio(tmp_path, usar_cache=False)

    # Assert
    mock_extraer_metadatos.assert_called_once()
    rutas_enviadas = mock_extraer_metadatos.call_args[0][0]

    assert len(rutas_enviadas) == 2
    assert foto.resolve() in rutas_enviadas
    assert raw.resolve() in rutas_enviadas
    assert auxiliar.resolve() not in rutas_enviadas
    assert proyecto.resolve() not in rutas_enviadas
    assert desconocido.resolve() not in rutas_enviadas
