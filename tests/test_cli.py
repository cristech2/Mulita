"""Pruebas para la interfaz de línea de comandos."""

from datetime import datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mulita.cli import app
from mulita.models import (
    AccionPlan,
    FechaResultado,
    OperacionPlan,
    PlanOrganizacion,
    TipoArchivo,
)
from mulita.plan_storage import exportar_plan_json

runner = CliRunner()


def test_cli_ayuda_base() -> None:
    """Verifica que la ayuda principal muestre los comandos del MVP."""
    result = runner.invoke(app, ["--help"], env={"COLUMNS": "120"})

    assert result.exit_code == 0
    assert "Mulita" in result.stdout
    assert "scan" in result.stdout
    assert "plan" in result.stdout
    assert "run" in result.stdout


def test_cli_scan_ejecucion_exitosa(tmp_path: Path) -> None:
    """Verifica que ``scan`` analice un directorio y muestre métricas.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    (origen / "foto1.jpg").touch()
    (origen / "edicion.psd").touch()

    # Act
    result = runner.invoke(app, ["scan", str(origen)])

    # Assert
    assert result.exit_code == 0
    assert "Iniciando escaneo" in result.stdout
    assert "Resumen del escaneo" in result.stdout
    assert "Imágenes:         1" in result.stdout
    assert "Proyectos:        1" in result.stdout


def test_cli_scan_directorio_inexistente() -> None:
    """Verifica que Typer rechace una carpeta de origen inexistente."""
    # Act
    result = runner.invoke(app, ["scan", "/ruta/inexistente/xyz"])

    # Assert
    assert result.exit_code != 0
    assert (
        "does not exist" in result.output or "Invalid value" in result.output
    )


def test_cli_plan_ejecucion_exitosa(tmp_path: Path) -> None:
    """Verifica que ``plan`` genere un plan de organización correctamente.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()
    (origen / "foto.jpg").touch()

    # Act
    result = runner.invoke(
        app, ["plan", str(origen), "--destino", str(destino)]
    )

    # Assert
    assert result.exit_code == 0
    assert "Generando plan para organizar" in result.stdout
    assert "Resumen del plan de organización" in result.stdout
    assert "Archivos a mover:         1" in result.stdout


def test_cli_plan_con_exportacion_json(tmp_path: Path) -> None:
    """Verifica que ``plan`` exporte JSON cuando se especifica ``--salida``.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()
    (origen / "foto.jpg").touch()
    salida_json = tmp_path / "plan.json"

    # Act
    result = runner.invoke(
        app,
        ["plan", str(origen), "-d", str(destino), "-s", str(salida_json)],
    )

    # Assert
    assert result.exit_code == 0
    assert salida_json.exists()
    assert "Plan exportado exitosamente" in result.stdout


def test_cli_plan_confirma_sobrescritura_de_salida_existente(
    tmp_path: Path,
) -> None:
    """Solo reemplaza un plan existente después de confirmar.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()
    (origen / "foto.jpg").touch()
    salida = tmp_path / "plan.json"
    salida.write_text("contenido previo", encoding="utf-8")

    result = runner.invoke(
        app,
        ["plan", str(origen), "-d", str(destino), "-s", str(salida)],
        input="y\n",
    )

    assert result.exit_code == 0
    assert "¿Desea sobrescribirlo?" in result.output
    assert "directorio_origen" in salida.read_text(encoding="utf-8")


def test_cli_plan_solicita_nueva_salida_si_no_sobrescribe(
    tmp_path: Path,
) -> None:
    """Permite escoger otra ruta y conserva intacta la salida existente.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()
    (origen / "foto.jpg").touch()
    salida_existente = tmp_path / "plan.json"
    salida_existente.write_text("contenido previo", encoding="utf-8")
    nueva_salida = tmp_path / "plan_nuevo.json"

    result = runner.invoke(
        app,
        [
            "plan",
            str(origen),
            "-d",
            str(destino),
            "-s",
            str(salida_existente),
        ],
        input=f"n\n{nueva_salida}\n",
    )

    assert result.exit_code == 0
    assert salida_existente.read_text(encoding="utf-8") == "contenido previo"
    assert "directorio_origen" in nueva_salida.read_text(encoding="utf-8")


def test_cli_plan_cancela_salida_existente_antes_de_escanear(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cancelar la salida evita el escaneo y conserva el archivo original.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        monkeypatch (pytest.MonkeyPatch): Fixture para evitar el escaneo.
    """
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()
    salida = tmp_path / "plan.json"
    salida.write_text("contenido previo", encoding="utf-8")

    def escaneo_no_esperado(_: Path) -> None:
        pytest.fail("No se debe escanear después de cancelar.")

    monkeypatch.setattr("mulita.cli.analizar_directorio", escaneo_no_esperado)

    result = runner.invoke(
        app,
        ["plan", str(origen), "-d", str(destino), "-s", str(salida)],
        input="n\n\n",
    )

    assert result.exit_code == 0
    assert "Operación cancelada por el usuario" in result.output
    assert salida.read_text(encoding="utf-8") == "contenido previo"


def test_cli_plan_rechaza_salida_dentro_del_origen_antes_de_escanear(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Evita escanear o reemplazar contenido del directorio de origen.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        monkeypatch (pytest.MonkeyPatch): Fixture para evitar el escaneo.
    """
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()

    def escaneo_no_esperado(_: Path) -> None:
        pytest.fail("La salida dentro del origen debe rechazarse primero.")

    monkeypatch.setattr("mulita.cli.analizar_directorio", escaneo_no_esperado)

    result = runner.invoke(
        app,
        [
            "plan",
            str(origen),
            "-d",
            str(destino),
            "-s",
            str(origen / "plan.json"),
        ],
    )

    assert result.exit_code == 1
    assert "no puede ser el directorio de origen" in result.output


def test_cli_plan_error_rutas_invalidas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica que ``plan`` rechace origen y destino coincidentes.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        monkeypatch (pytest.MonkeyPatch): Fixture para evitar el escaneo.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    log_dir = tmp_path / "logs"

    def escaneo_no_esperado(_: Path) -> None:
        pytest.fail("No se debe escanear antes de validar las rutas.")

    monkeypatch.setattr("mulita.cli.analizar_directorio", escaneo_no_esperado)

    # Act
    result = runner.invoke(
        app,
        [
            "--log-file",
            str(log_dir),
            "plan",
            str(origen),
            "--destino",
            str(origen),
        ],
    )

    # Assert
    assert result.exit_code == 1
    assert "Error:" in result.output
    archivos_log = list(log_dir.glob("*.log"))
    assert len(archivos_log) == 1
    assert "no pueden ser el mismo" in archivos_log[0].read_text(
        encoding="utf-8"
    )


def test_cli_run_sin_plan_en_directorio_falla(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica que ``run`` informe error si no hay planes JSON en el directorio.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        monkeypatch (pytest.MonkeyPatch): Fixture para modificar el entorno.
    """
    # Arrange
    monkeypatch.chdir(tmp_path)

    # Act
    result = runner.invoke(app, ["run"])

    # Assert
    assert result.exit_code == 1
    assert "No se encontraron archivos de plan JSON" in result.output
    archivos_log = list((tmp_path / "reportes").glob("*.log"))
    assert len(archivos_log) == 1
    assert "No se encontraron archivos de plan JSON" in archivos_log[
        0
    ].read_text(encoding="utf-8")


def test_cli_run_simulacion_con_plan_explicito(tmp_path: Path) -> None:
    """Verifica la simulación (--dry-run) especificando la ruta al plan.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()
    foto = origen / "foto.jpg"
    foto.touch()

    salida_plan = tmp_path / "plan_test.json"
    plan = PlanOrganizacion(
        directorio_origen=origen,
        directorio_destino=destino,
        operaciones=[
            OperacionPlan(
                origen=foto,
                destino=destino / "2026" / "10" / "20" / "IMAGEN" / "foto.jpg",
                categoria=TipoArchivo.IMAGEN,
                fecha_resultado=FechaResultado(
                    fecha=datetime(2026, 10, 20),
                    fuente="DateTimeOriginal",
                    es_respaldo=False,
                ),
                sidecars_asociados=[],
                accion=AccionPlan.MOVER,
            )
        ],
        sidecars_omitidos=[],
        desconocidos=[],
    )
    exportar_plan_json(plan, salida_plan)

    # Act
    result = runner.invoke(app, ["run", str(salida_plan)])

    # Assert
    assert result.exit_code == 0
    assert "MODO SIMULACIÓN" in result.stdout
    assert foto.exists()


def test_cli_run_seleccion_interactiva_multiples_planes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica el prompt de selección cuando existen varios planes.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        monkeypatch (pytest.MonkeyPatch): Fixture para modificar el entorno.
    """
    # Arrange
    monkeypatch.chdir(tmp_path)
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()

    plan1 = PlanOrganizacion(
        directorio_origen=origen,
        directorio_destino=destino,
        operaciones=[],
        sidecars_omitidos=[],
        desconocidos=[],
    )
    exportar_plan_json(plan1, tmp_path / "plan1.json")
    exportar_plan_json(plan1, tmp_path / "plan2.json")

    # Act
    result = runner.invoke(app, ["run"], input="2\n")

    # Assert
    assert result.exit_code == 0
    assert "Se encontraron varios archivos de plan" in result.stdout
    assert "MODO SIMULACIÓN" in result.stdout


def test_cli_run_ejecucion_real_cancelada_por_usuario(tmp_path: Path) -> None:
    """Verifica que cancelar la confirmación en --ejecutar no altere archivos.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
    """
    # Arrange
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()

    plan = PlanOrganizacion(
        directorio_origen=origen,
        directorio_destino=destino,
        operaciones=[],
        sidecars_omitidos=[],
        desconocidos=[],
    )
    plan_file = tmp_path / "plan.json"
    exportar_plan_json(plan, plan_file)

    # Act
    result = runner.invoke(
        app, ["run", str(plan_file), "--ejecutar"], input="n\n"
    )

    # Assert
    assert result.exit_code == 0
    assert "Operación cancelada por el usuario" in result.stdout


def test_cli_run_prevalida_todo_el_plan_antes_de_mover(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Un origen ausente aborta antes de mover cualquier archivo del lote.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        monkeypatch (pytest.MonkeyPatch): Fixture para fijar el cwd.
    """
    monkeypatch.chdir(tmp_path)
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    primer_archivo = origen / "primero.jpg"
    primer_archivo.touch()
    origen_ausente = origen / "ausente.jpg"
    fecha = FechaResultado(
        fecha=datetime(2026, 10, 20),
        fuente="DateTimeOriginal",
        es_respaldo=False,
    )
    operaciones = [
        OperacionPlan(
            origen=ruta_origen,
            destino=destino / nombre,
            categoria=TipoArchivo.IMAGEN,
            fecha_resultado=fecha,
            sidecars_asociados=[],
            accion=AccionPlan.MOVER,
        )
        for ruta_origen, nombre in (
            (primer_archivo, "primero.jpg"),
            (origen_ausente, "ausente.jpg"),
        )
    ]
    plan_file = tmp_path / "plan.json"
    exportar_plan_json(
        PlanOrganizacion(
            directorio_origen=origen,
            directorio_destino=destino,
            operaciones=operaciones,
            sidecars_omitidos=[],
            desconocidos=[],
        ),
        plan_file,
    )

    result = runner.invoke(
        app, ["run", str(plan_file), "--ejecutar"], input="y\n"
    )

    assert result.exit_code == 1
    assert "no existe o no es un archivo" in result.output
    assert primer_archivo.exists()
    assert not (destino / "primero.jpg").exists()
    assert "¿Desea proceder" not in result.output


def test_cli_run_prevalida_destinos_duplicados_antes_de_mover(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Un destino repetido aborta antes de iniciar el movimiento del lote.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        monkeypatch (pytest.MonkeyPatch): Fixture para fijar el cwd.
    """
    monkeypatch.chdir(tmp_path)
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    foto_a = origen / "a.jpg"
    foto_b = origen / "b.jpg"
    foto_a.touch()
    foto_b.touch()
    fecha = FechaResultado(
        fecha=datetime(2026, 10, 20),
        fuente="DateTimeOriginal",
        es_respaldo=False,
    )
    destino_repetido = destino / "foto.jpg"
    operaciones = [
        OperacionPlan(
            origen=foto,
            destino=destino_repetido,
            categoria=TipoArchivo.IMAGEN,
            fecha_resultado=fecha,
            sidecars_asociados=[],
            accion=AccionPlan.MOVER,
        )
        for foto in (foto_a, foto_b)
    ]
    plan_file = tmp_path / "plan.json"
    exportar_plan_json(
        PlanOrganizacion(
            directorio_origen=origen,
            directorio_destino=destino,
            operaciones=operaciones,
            sidecars_omitidos=[],
            desconocidos=[],
        ),
        plan_file,
    )

    result = runner.invoke(
        app, ["run", str(plan_file), "--ejecutar"], input="y\n"
    )

    assert result.exit_code == 1
    assert "Destino repetido en el plan" in result.output
    assert foto_a.exists()
    assert foto_b.exists()
    assert "¿Desea proceder" not in result.output


def test_cli_run_no_mueve_archivos_si_no_se_puede_preparar_auditoria(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Un error preparando auditoría aborta antes de confirmar movimientos.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        monkeypatch (pytest.MonkeyPatch): Fixture para simular el error.
    """
    monkeypatch.chdir(tmp_path)
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    foto = origen / "foto.jpg"
    foto.touch()
    plan_file = tmp_path / "plan.json"
    exportar_plan_json(
        PlanOrganizacion(
            directorio_origen=origen,
            directorio_destino=destino,
            operaciones=[
                OperacionPlan(
                    origen=foto,
                    destino=destino / "foto.jpg",
                    categoria=TipoArchivo.IMAGEN,
                    fecha_resultado=FechaResultado(
                        fecha=datetime(2026, 10, 20),
                        fuente="DateTimeOriginal",
                        es_respaldo=False,
                    ),
                    sidecars_asociados=[],
                    accion=AccionPlan.MOVER,
                )
            ],
            sidecars_omitidos=[],
            desconocidos=[],
        ),
        plan_file,
    )

    def fallo_preparacion(_: Path) -> None:
        raise OSError("directorio de auditoría no escribible")

    monkeypatch.setattr(
        "mulita.cli.validar_ruta_exportacion", fallo_preparacion
    )

    result = runner.invoke(
        app, ["run", str(plan_file), "--ejecutar"], input="y\n"
    )

    assert result.exit_code == 1
    assert "directorio de auditoría no escribible" in result.output
    assert foto.exists()
    assert "¿Desea proceder" not in result.output


def test_cli_run_informa_si_falla_guardar_auditoria_tras_mover(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Explica claramente que el movimiento ocurrió si falla el reporte final.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        monkeypatch (pytest.MonkeyPatch): Fixture para simular el error.
    """
    monkeypatch.chdir(tmp_path)
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    foto = origen / "foto.jpg"
    foto.touch()
    destino_foto = destino / "foto.jpg"
    plan_file = tmp_path / "plan.json"
    exportar_plan_json(
        PlanOrganizacion(
            directorio_origen=origen,
            directorio_destino=destino,
            operaciones=[
                OperacionPlan(
                    origen=foto,
                    destino=destino_foto,
                    categoria=TipoArchivo.IMAGEN,
                    fecha_resultado=FechaResultado(
                        fecha=datetime(2026, 10, 20),
                        fuente="DateTimeOriginal",
                        es_respaldo=False,
                    ),
                    sidecars_asociados=[],
                    accion=AccionPlan.MOVER,
                )
            ],
            sidecars_omitidos=[],
            desconocidos=[],
        ),
        plan_file,
    )

    def fallo_exportacion(*_: object) -> None:
        raise OSError("fallo de disco simulado")

    monkeypatch.setattr(
        "mulita.cli.exportar_resultado_ejecucion_json", fallo_exportacion
    )

    result = runner.invoke(
        app, ["run", str(plan_file), "--ejecutar"], input="y\n"
    )

    assert result.exit_code == 1
    assert "La ejecución ya terminó" in result.output
    assert "fallo de disco simulado" in result.output
    assert not foto.exists()
    assert destino_foto.exists()


def test_cli_run_no_sobrescribe_auditoria_existente(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Conserva auditorías anteriores y genera un nombre alternativo.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        monkeypatch (pytest.MonkeyPatch): Fixture para fijar el cwd.
    """
    monkeypatch.chdir(tmp_path)
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()
    plan_file = tmp_path / "plan.json"
    exportar_plan_json(
        PlanOrganizacion(
            directorio_origen=origen,
            directorio_destino=destino,
            operaciones=[],
            sidecars_omitidos=[],
            desconocidos=[],
        ),
        plan_file,
    )

    directorio_reportes = tmp_path / "reportes"
    directorio_reportes.mkdir()
    auditoria_previa = directorio_reportes / "ejecucion_plan.json"
    auditoria_previa.write_text("auditoria anterior", encoding="utf-8")

    result = runner.invoke(
        app, ["run", str(plan_file), "--ejecutar"], input="y\n"
    )

    assert result.exit_code == 0
    assert auditoria_previa.read_text(encoding="utf-8") == "auditoria anterior"
    assert (directorio_reportes / "ejecucion_plan_1.json").exists()


@pytest.mark.parametrize(
    ("nombre_plan", "identificador_auditoria"),
    [
        ("plan_20261020", "20261020"),
        ("plan_plan_20261020", "plan_20261020"),
    ],
)
def test_cli_run_ejecucion_real_exitosa(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    nombre_plan: str,
    identificador_auditoria: str,
) -> None:
    """Verifica ejecución real y auditoría con varios nombres de plan.

    Args:
        tmp_path (Path): Directorio temporal de la prueba.
        monkeypatch (pytest.MonkeyPatch): Fixture para modificar el entorno.
        nombre_plan (str): Nombre del plan de entrada.
        identificador_auditoria (str): Identificador esperado del reporte.
    """
    # Arrange
    monkeypatch.chdir(tmp_path)
    origen = tmp_path / "origen"
    origen.mkdir()
    destino = tmp_path / "destino"
    destino.mkdir()
    foto = origen / "foto.jpg"
    foto.touch()

    destino_foto = destino / "2026" / "10" / "20" / "IMAGEN" / "foto.jpg"

    plan = PlanOrganizacion(
        directorio_origen=origen,
        directorio_destino=destino,
        operaciones=[
            OperacionPlan(
                origen=foto,
                destino=destino_foto,
                categoria=TipoArchivo.IMAGEN,
                fecha_resultado=FechaResultado(
                    fecha=datetime(2026, 10, 20),
                    fuente="DateTimeOriginal",
                    es_respaldo=False,
                ),
                sidecars_asociados=[],
                accion=AccionPlan.MOVER,
            )
        ],
        sidecars_omitidos=[],
        desconocidos=[],
    )
    plan_file = tmp_path / f"{nombre_plan}.json"
    exportar_plan_json(plan, plan_file)

    # Act
    result = runner.invoke(
        app, ["run", str(plan_file), "--ejecutar"], input="y\n"
    )

    # Assert
    assert result.exit_code == 0
    assert "Ejecutando plan de organización" in result.stdout
    assert "Procesados con éxito: 1" in result.stdout
    assert not foto.exists()
    assert destino_foto.exists()
    ruta_auditoria = (
        tmp_path / "reportes" / f"ejecucion_{identificador_auditoria}.json"
    )
    assert ruta_auditoria.exists()
