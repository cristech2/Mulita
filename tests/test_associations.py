"""Pruebas para la asociación de sidecars."""

from datetime import datetime
from pathlib import Path

import pytest

from mulita.associations import asociar_sidecars
from mulita.models import (
    ArchivoAnalizado,
    ArchivoEscaneado,
    EstadoAsociacion,
    FechaResultado,
    TipoArchivo,
)


def _crear_analizado(ruta: Path, tipo: TipoArchivo) -> ArchivoAnalizado:
    """Crea una instancia con datos mínimos de prueba.

    Args:
        ruta (Path): Ruta del archivo a crear.
        tipo (TipoArchivo): Tipo del archivo.

    Returns:
        ArchivoAnalizado: Resultado de análisis con datos de prueba.
    """
    return ArchivoAnalizado(
        archivo=ArchivoEscaneado(ruta=ruta, tipo=tipo),
        fecha_resultado=FechaResultado(
            fecha=datetime(2026, 10, 20, 12, 0, 0),
            fuente="prueba",
            es_respaldo=False,
        ),
        metadatos={},
    )


def test_asociar_sidecar_coincidencia_directa_stem(tmp_path: Path) -> None:
    """Verifica la asociación de un sidecar por nombre base.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    base_dir = tmp_path / "fotos"
    foto = _crear_analizado(base_dir / "foto.jpg", TipoArchivo.IMAGEN)
    sidecar = _crear_analizado(base_dir / "foto.xmp", TipoArchivo.AUXILIAR)

    # Act
    grupos, no_asociados = asociar_sidecars([foto, sidecar])

    # Assert
    assert len(grupos) == 1
    assert grupos[0].principal.archivo.ruta == foto.archivo.ruta
    assert len(grupos[0].sidecars) == 1
    assert grupos[0].sidecars[0].archivo.ruta == sidecar.archivo.ruta
    assert len(no_asociados) == 0


def test_asociar_sidecar_coincidencia_nombre_completo(tmp_path: Path) -> None:
    """Verifica la asociación cuando el sidecar incluye el nombre completo.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    base_dir = tmp_path / "fotos"
    raw = _crear_analizado(base_dir / "foto.cr2", TipoArchivo.RAW)
    sidecar = _crear_analizado(base_dir / "foto.cr2.xmp", TipoArchivo.AUXILIAR)

    # Act
    grupos, no_asociados = asociar_sidecars([raw, sidecar])

    # Assert
    assert len(grupos) == 1
    assert len(grupos[0].sidecars) == 1
    assert grupos[0].sidecars[0].archivo.ruta == sidecar.archivo.ruta
    assert len(no_asociados) == 0


def test_asociar_sidecar_case_insensitive(tmp_path: Path) -> None:
    """Verifica que la asociación ignore mayúsculas y minúsculas.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    base_dir = tmp_path / "fotos"
    raw = _crear_analizado(base_dir / "DSC_0001.NEF", TipoArchivo.RAW)
    sidecar = _crear_analizado(base_dir / "dsc_0001.XMP", TipoArchivo.AUXILIAR)

    # Act
    grupos, no_asociados = asociar_sidecars([raw, sidecar])

    # Assert
    assert len(grupos) == 1
    assert len(grupos[0].sidecars) == 1
    assert grupos[0].sidecars[0].archivo.ruta == sidecar.archivo.ruta
    assert len(no_asociados) == 0


def test_asociar_multiples_sidecars_mismo_principal(tmp_path: Path) -> None:
    """Verifica que varios sidecars se asocien al mismo archivo principal.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    base_dir = tmp_path / "fotos"
    foto = _crear_analizado(base_dir / "foto.jpg", TipoArchivo.IMAGEN)
    xmp = _crear_analizado(base_dir / "foto.xmp", TipoArchivo.AUXILIAR)
    rrdata = _crear_analizado(base_dir / "foto.rrdata", TipoArchivo.AUXILIAR)

    # Act
    grupos, no_asociados = asociar_sidecars([foto, xmp, rrdata])

    # Assert
    assert len(grupos) == 1
    assert len(grupos[0].sidecars) == 2
    rutas_sidecars = [s.archivo.ruta for s in grupos[0].sidecars]
    assert xmp.archivo.ruta in rutas_sidecars
    assert rrdata.archivo.ruta in rutas_sidecars
    assert len(no_asociados) == 0


@pytest.mark.parametrize("extension_aux", [".xmp", ".rrdata", ".rrexif"])
def test_asociar_extensiones_auxiliares_soportadas(
    extension_aux: str, tmp_path: Path
) -> None:
    """Valida el soporte de las extensiones auxiliares del MVP.

    Args:
        extension_aux (str): Extensión auxiliar que se prueba.
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    base_dir = tmp_path / "fotos"
    foto = _crear_analizado(base_dir / "imagen.png", TipoArchivo.IMAGEN)
    sidecar = _crear_analizado(
        base_dir / f"imagen{extension_aux}", TipoArchivo.AUXILIAR
    )

    # Act
    grupos, no_asociados = asociar_sidecars([foto, sidecar])

    # Assert
    assert len(grupos) == 1
    assert len(grupos[0].sidecars) == 1
    assert grupos[0].sidecars[0].archivo.ruta == sidecar.archivo.ruta
    assert len(no_asociados) == 0


def test_detectar_sidecar_huerfano(tmp_path: Path) -> None:
    """Verifica que un sidecar sin principal se clasifique como huérfano.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    base_dir = tmp_path / "fotos"
    huerfano = _crear_analizado(
        base_dir / "desconocido.xmp", TipoArchivo.AUXILIAR
    )

    # Act
    grupos, no_asociados = asociar_sidecars([huerfano])

    # Assert
    assert len(grupos) == 0
    assert len(no_asociados) == 1
    assert no_asociados[0].archivo == huerfano
    assert no_asociados[0].estado == EstadoAsociacion.HUERFANO


def test_detectar_sidecar_ambiguo(tmp_path: Path) -> None:
    """Verifica que un sidecar coincidente con varios archivos sea ambiguo.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    base_dir = tmp_path / "fotos"
    jpg = _crear_analizado(base_dir / "foto.jpg", TipoArchivo.IMAGEN)
    raw = _crear_analizado(base_dir / "foto.cr2", TipoArchivo.RAW)
    ambiguo = _crear_analizado(base_dir / "foto.xmp", TipoArchivo.AUXILIAR)

    # Act
    grupos, no_asociados = asociar_sidecars([jpg, raw, ambiguo])

    # Assert
    assert len(grupos) == 2
    assert len(grupos[0].sidecars) == 0
    assert len(grupos[1].sidecars) == 0

    assert len(no_asociados) == 1
    assert no_asociados[0].archivo == ambiguo
    assert no_asociados[0].estado == EstadoAsociacion.AMBIGUO


def test_aislamiento_entre_carpetas(tmp_path: Path) -> None:
    """Verifica que la asociación se limite a la carpeta del sidecar.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    folder_a = tmp_path / "fotos" / "evento_a"
    folder_b = tmp_path / "fotos" / "evento_b"

    foto_a = _crear_analizado(folder_a / "imagen.jpg", TipoArchivo.IMAGEN)
    sidecar_b = _crear_analizado(folder_b / "imagen.xmp", TipoArchivo.AUXILIAR)

    # Act
    grupos, no_asociados = asociar_sidecars([foto_a, sidecar_b])

    # Assert
    assert len(grupos) == 1
    assert grupos[0].principal.archivo.ruta == foto_a.archivo.ruta
    assert len(grupos[0].sidecars) == 0

    assert len(no_asociados) == 1
    assert no_asociados[0].archivo == sidecar_b
    assert no_asociados[0].estado == EstadoAsociacion.HUERFANO
