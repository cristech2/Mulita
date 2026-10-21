"""Pruebas para la planificación de organización y resolución de colisiones."""

from datetime import datetime
from pathlib import Path

import pytest

from mulita.models import (
    AccionPlan,
    ArchivoAnalizado,
    ArchivoEscaneado,
    EstadoAsociacion,
    FechaResultado,
    GrupoArchivo,
    PlanOrganizacion,
    ResultadoEscaneo,
    SidecarAsociado,
    TipoArchivo,
)
from mulita.planner import (
    _calcular_nuevo_nombre_sidecar,
    _resolver_destino_unico,
    generar_plan,
    validar_rutas,
)


def test_validar_rutas_origen_inexistente(tmp_path: Path) -> None:
    """Verifica que un origen inexistente produzca ValueError.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen_inexistente = tmp_path / "no_existe"
    destino = tmp_path / "destino"
    destino.mkdir()

    # Act & Assert
    with pytest.raises(ValueError, match="El directorio de origen no existe"):
        validar_rutas(origen_inexistente, destino)


def test_validar_rutas_origen_no_es_directorio(tmp_path: Path) -> None:
    """Verifica que un origen que sea archivo lance ValueError.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen_archivo = tmp_path / "archivo.txt"
    origen_archivo.touch()
    destino = tmp_path / "destino"
    destino.mkdir()

    # Act & Assert
    with pytest.raises(ValueError, match="no es un directorio"):
        validar_rutas(origen_archivo, destino)


def test_validar_rutas_origen_igual_a_destino(tmp_path: Path) -> None:
    """Verifica que origen y destino iguales produzcan ValueError.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    directorio = tmp_path / "mismo_dir"
    directorio.mkdir()

    # Act & Assert
    with pytest.raises(ValueError, match="no pueden ser el mismo"):
        validar_rutas(directorio, directorio)


def test_validar_rutas_destino_contenido_en_origen(tmp_path: Path) -> None:
    """Verifica que el destino no esté contenido dentro del origen.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = origen / "destino"
    destino.mkdir()

    # Act & Assert
    with pytest.raises(
        ValueError, match="no puede estar contenido dentro del origen"
    ):
        validar_rutas(origen, destino)


def test_validar_rutas_origen_contenido_en_destino(tmp_path: Path) -> None:
    """Verifica que el origen no esté contenido dentro del destino.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    destino = tmp_path / "destino"
    destino.mkdir()
    origen = destino / "origen"
    origen.mkdir()

    # Act & Assert
    with pytest.raises(
        ValueError, match="no puede estar contenido dentro del destino"
    ):
        validar_rutas(origen, destino)


def test_validar_rutas_validas(tmp_path: Path) -> None:
    """Verifica que directorios independientes sean válidos.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()

    # Act & Assert
    validar_rutas(origen, destino)


@pytest.mark.parametrize(
    "origen_p, destino_p, origen_s, esperado",
    [
        (
            Path("foto.jpg"),
            Path("foto_1.jpg"),
            Path("foto.xmp"),
            "foto_1.xmp",
        ),
        (
            Path("foto.jpg"),
            Path("foto_1.jpg"),
            Path("foto.jpg.xmp"),
            "foto_1.jpg.xmp",
        ),
        (
            Path("IMG_0001.JPG"),
            Path("IMG_0001_1.JPG"),
            Path("IMG_0001.xmp"),
            "IMG_0001_1.xmp",
        ),
        (
            Path("foto.jpg"),
            Path("foto.jpg"),
            Path("otro.xmp"),
            "otro.xmp",
        ),
    ],
)
def test_calcular_nuevo_nombre_sidecar(
    origen_p: Path, destino_p: Path, origen_s: Path, esperado: str
) -> None:
    """Verifica el cálculo del nombre de sidecar según el principal.

    Args:
        origen_p (Path): Ruta origen del principal.
        destino_p (Path): Ruta destino del principal.
        origen_s (Path): Ruta origen del sidecar.
        esperado (str): Nombre esperado del sidecar en destino.
    """
    # Act
    nuevo_nombre = _calcular_nuevo_nombre_sidecar(
        origen_p, destino_p, origen_s
    )

    # Assert
    assert nuevo_nombre == esperado


def test_resolver_destino_unico_sin_colision(tmp_path: Path) -> None:
    """Verifica la resolución de un destino único sin conflictos.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    destinos_reservados: set[Path] = set()
    nombre = "imagen.jpg"

    # Act
    destino = _resolver_destino_unico(tmp_path, nombre, destinos_reservados)

    # Assert
    assert destino == tmp_path / "imagen.jpg"
    assert destino in destinos_reservados


def test_resolver_destino_unico_con_colision_existente(tmp_path: Path) -> None:
    """Verifica que una colisión genere un sufijo numérico.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    destinos_reservados: set[Path] = set()
    nombre = "imagen.jpg"

    existente = tmp_path / nombre
    existente.touch()

    # Act
    destino = _resolver_destino_unico(tmp_path, nombre, destinos_reservados)

    # Assert
    assert destino == tmp_path / "imagen_1.jpg"
    assert destino in destinos_reservados


def test_generar_plan_construye_estructura_correcta(tmp_path: Path) -> None:
    """Verifica la estructura ``YYYY/MM/DD/CATEGORIA`` del plan.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()

    foto_path = origen / "foto.jpg"
    foto_path.touch()

    fecha_res = FechaResultado(
        fecha=datetime(2026, 10, 20, 14, 30),
        fuente="DateTimeOriginal",
        es_respaldo=False,
    )

    principal = ArchivoAnalizado(
        archivo=ArchivoEscaneado(ruta=foto_path, tipo=TipoArchivo.IMAGEN),
        fecha_resultado=fecha_res,
        metadatos={},
    )

    resultado_escaneo = ResultadoEscaneo(
        grupos=[GrupoArchivo(principal=principal, sidecars=[])],
        sidecars_no_asociados=[],
        desconocidos=[],
    )

    # Act
    plan = generar_plan(resultado_escaneo, origen, destino)

    # Assert
    assert isinstance(plan, PlanOrganizacion)
    assert len(plan.operaciones) == 1

    op = plan.operaciones[0]
    assert op.origen == foto_path
    assert op.destino == destino / "2026" / "10" / "20" / "IMAGEN" / "foto.jpg"
    assert op.accion == AccionPlan.MOVER
    assert len(op.advertencias) == 0


def test_generar_plan_mantiene_sidecars_y_resuelve_colision_conjunta(
    tmp_path: Path,
) -> None:
    """Verifica que los sidecars sigan al principal renombrado.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()

    carpeta_colision = destino / "2026" / "10" / "20" / "IMAGEN"
    carpeta_colision.mkdir(parents=True)
    (carpeta_colision / "foto.jpg").touch()

    foto_path = origen / "foto.jpg"
    foto_path.touch()
    sidecar_path = origen / "foto.xmp"
    sidecar_path.touch()

    fecha_res = FechaResultado(
        fecha=datetime(2026, 10, 20, 14, 30),
        fuente="DateTimeOriginal",
        es_respaldo=False,
    )

    principal = ArchivoAnalizado(
        archivo=ArchivoEscaneado(ruta=foto_path, tipo=TipoArchivo.IMAGEN),
        fecha_resultado=fecha_res,
        metadatos={},
    )
    sidecar = ArchivoAnalizado(
        archivo=ArchivoEscaneado(ruta=sidecar_path, tipo=TipoArchivo.AUXILIAR),
        fecha_resultado=fecha_res,
        metadatos={},
    )

    resultado_escaneo = ResultadoEscaneo(
        grupos=[GrupoArchivo(principal=principal, sidecars=[sidecar])],
        sidecars_no_asociados=[],
        desconocidos=[],
    )

    # Act
    plan = generar_plan(resultado_escaneo, origen, destino)

    # Assert
    assert len(plan.operaciones) == 1
    op = plan.operaciones[0]
    assert op.destino == carpeta_colision / "foto_1.jpg"
    assert len(op.sidecars_asociados) == 1

    origen_s, destino_s = op.sidecars_asociados[0]
    assert origen_s == sidecar_path
    assert destino_s == carpeta_colision / "foto_1.xmp"
    assert any("Renombrado por colisión" in adv for adv in op.advertencias)


def test_generar_plan_registra_advertencia_fecha_respaldo(
    tmp_path: Path,
) -> None:
    """Verifica que se advierta cuando la fecha utilizada sea de respaldo.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()

    foto_path = origen / "foto.jpg"
    foto_path.touch()

    fecha_res = FechaResultado(
        fecha=datetime(2026, 10, 20, 14, 30),
        fuente="FileModifyDate",
        es_respaldo=True,
    )

    principal = ArchivoAnalizado(
        archivo=ArchivoEscaneado(ruta=foto_path, tipo=TipoArchivo.IMAGEN),
        fecha_resultado=fecha_res,
        metadatos={},
    )

    resultado_escaneo = ResultadoEscaneo(
        grupos=[GrupoArchivo(principal=principal, sidecars=[])],
        sidecars_no_asociados=[],
        desconocidos=[],
    )

    # Act
    plan = generar_plan(resultado_escaneo, origen, destino)

    # Assert
    op = plan.operaciones[0]
    assert any("Fecha de respaldo utilizada" in adv for adv in op.advertencias)


def test_generar_plan_preserva_sidecars_omitidos_y_desconocidos(
    tmp_path: Path,
) -> None:
    """Verifica que se preserven los sidecars omitidos y desconocidos.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()

    huerfano_path = origen / "huerfano.xmp"
    huerfano_path.touch()

    desconocido_path = origen / "documento.pdf"
    desconocido_path.touch()

    fecha_res = FechaResultado(
        fecha=datetime(2026, 10, 20, 14, 30),
        fuente="Sistema",
        es_respaldo=False,
    )

    sidecar_na = SidecarAsociado(
        archivo=ArchivoAnalizado(
            archivo=ArchivoEscaneado(
                ruta=huerfano_path, tipo=TipoArchivo.AUXILIAR
            ),
            fecha_resultado=fecha_res,
            metadatos={},
        ),
        estado=EstadoAsociacion.HUERFANO,
        motivo="Sin principal",
    )

    desconocido = ArchivoAnalizado(
        archivo=ArchivoEscaneado(
            ruta=desconocido_path, tipo=TipoArchivo.DESCONOCIDO
        ),
        fecha_resultado=fecha_res,
        metadatos={},
    )

    resultado_escaneo = ResultadoEscaneo(
        grupos=[],
        sidecars_no_asociados=[sidecar_na],
        desconocidos=[desconocido],
    )

    # Act
    plan = generar_plan(resultado_escaneo, origen, destino)

    # Assert
    assert len(plan.operaciones) == 0
    assert len(plan.sidecars_omitidos) == 1
    assert plan.sidecars_omitidos[0] == sidecar_na
    assert len(plan.desconocidos) == 1
    assert plan.desconocidos[0] == desconocido


def test_generar_plan_es_determinista_ante_diferente_orden_grupos(
    tmp_path: Path,
) -> None:
    """Verifica determinismo al asignar destinos en colisión con distinto orden de escaneo.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()

    fecha_fija = FechaResultado(
        fecha=datetime(2026, 10, 20, 10, 0),
        fuente="DateTimeOriginal",
        es_respaldo=False,
    )

    foto_a = origen / "foto_a.jpg"
    foto_b = origen / "foto_b.jpg"
    foto_c = origen / "foto_c.jpg"
    foto_a.touch()
    foto_b.touch()
    foto_c.touch()

    grupo_a = GrupoArchivo(
        principal=ArchivoAnalizado(
            archivo=ArchivoEscaneado(ruta=foto_a, tipo=TipoArchivo.IMAGEN),
            fecha_resultado=fecha_fija,
            metadatos={},
        )
    )
    grupo_b = GrupoArchivo(
        principal=ArchivoAnalizado(
            archivo=ArchivoEscaneado(ruta=foto_b, tipo=TipoArchivo.IMAGEN),
            fecha_resultado=fecha_fija,
            metadatos={},
        )
    )
    grupo_c = GrupoArchivo(
        principal=ArchivoAnalizado(
            archivo=ArchivoEscaneado(ruta=foto_c, tipo=TipoArchivo.IMAGEN),
            fecha_resultado=fecha_fija,
            metadatos={},
        )
    )

    escaneo_orden_1 = ResultadoEscaneo(
        grupos=[grupo_a, grupo_b, grupo_c],
        sidecars_no_asociados=[],
        desconocidos=[],
    )
    escaneo_orden_2 = ResultadoEscaneo(
        grupos=[grupo_c, grupo_a, grupo_b],
        sidecars_no_asociados=[],
        desconocidos=[],
    )

    # Act
    plan_1 = generar_plan(escaneo_orden_1, origen, destino)
    plan_2 = generar_plan(escaneo_orden_2, origen, destino)

    mapa_destinos_1 = {op.origen: op.destino for op in plan_1.operaciones}
    mapa_destinos_2 = {op.origen: op.destino for op in plan_2.operaciones}

    # Assert
    assert mapa_destinos_1 == mapa_destinos_2


def test_generar_plan_es_determinista_ante_diferente_orden_sidecars(
    tmp_path: Path,
) -> None:
    """Verifica determinismo en la asignación de sidecars sin importar su orden de entrada.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()

    fecha_fija = FechaResultado(
        fecha=datetime(2026, 10, 20, 10, 0),
        fuente="DateTimeOriginal",
        es_respaldo=False,
    )

    foto_path = origen / "foto.jpg"
    sidecar_a_path = origen / "foto.a.xmp"
    sidecar_b_path = origen / "foto.b.xmp"
    foto_path.touch()
    sidecar_a_path.touch()
    sidecar_b_path.touch()

    principal = ArchivoAnalizado(
        archivo=ArchivoEscaneado(ruta=foto_path, tipo=TipoArchivo.IMAGEN),
        fecha_resultado=fecha_fija,
        metadatos={},
    )
    sidecar_a = ArchivoAnalizado(
        archivo=ArchivoEscaneado(
            ruta=sidecar_a_path, tipo=TipoArchivo.AUXILIAR
        ),
        fecha_resultado=fecha_fija,
        metadatos={},
    )
    sidecar_b = ArchivoAnalizado(
        archivo=ArchivoEscaneado(
            ruta=sidecar_b_path, tipo=TipoArchivo.AUXILIAR
        ),
        fecha_resultado=fecha_fija,
        metadatos={},
    )

    grupo_orden_1 = GrupoArchivo(
        principal=principal,
        sidecars=[sidecar_a, sidecar_b],
    )
    grupo_orden_2 = GrupoArchivo(
        principal=principal,
        sidecars=[sidecar_b, sidecar_a],
    )

    escaneo_1 = ResultadoEscaneo(
        grupos=[grupo_orden_1],
        sidecars_no_asociados=[],
        desconocidos=[],
    )
    escaneo_2 = ResultadoEscaneo(
        grupos=[grupo_orden_2],
        sidecars_no_asociados=[],
        desconocidos=[],
    )

    # Act
    plan_1 = generar_plan(escaneo_1, origen, destino)
    plan_2 = generar_plan(escaneo_2, origen, destino)

    sidecars_asociados_1 = plan_1.operaciones[0].sidecars_asociados
    sidecars_asociados_2 = plan_2.operaciones[0].sidecars_asociados

    # Assert
    assert sidecars_asociados_1 == sidecars_asociados_2
