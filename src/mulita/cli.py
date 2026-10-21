"""CLI para Mulita.

Define los comandos, argumentos y opciones de Typer para el flujo principal
de la aplicación.
"""

from pathlib import Path

import typer

from mulita.executor import ejecutar_plan
from mulita.models import AccionPlan, TipoArchivo
from mulita.plan_storage import (
    buscar_archivos_plan,
    cargar_plan_json,
    exportar_plan_json,
    exportar_resultado_ejecucion_json,
)
from mulita.planner import generar_plan, validar_rutas
from mulita.reporting import (
    configurar_logging,
    obtener_logger,
    registrar_resultado_detallado_en_log,
)
from mulita.scanner import analizar_directorio

app = typer.Typer(
    help="Mulita: Organizador seguro e inspeccionable de fotos y videos.",
    no_args_is_help=True,
)


@app.callback()
def main(
    dev: bool = typer.Option(
        False,
        "--dev",
        help=(
            "Modo desarrollo: registra detalles en el log manteniendo la "
            "consola limpia."
        ),
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-v",
        "--verbose",
        help=(
            "Modo debug: muestra todos los detalles tanto en consola como en "
            "el log."
        ),
    ),
    log_file: Path | None = typer.Option(  # noqa: B008
        None,
        "--log-file",
        help=(
            "Directorio o archivo base para guardar el "
            "registro de la operación."
        ),
        file_okay=True,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """Configura la aplicación antes de ejecutar cualquier comando.

    Args:
        dev (bool): Habilita el modo de desarrollo.
        debug (bool): Habilita el modo verbose de depuración.
        log_file (Path | None): Ruta base del archivo o directorio de log.
    """
    configurar_logging(dev=dev, debug=debug, log_file=log_file)


@app.command()
def scan(
    origen: Path = typer.Argument(  # noqa: B008
        ...,
        help="Ruta de la carpeta origen a escanear.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """Inspecciona un directorio y resume el resultado del escaneo.

    Args:
        origen (Path): Ruta de la carpeta fuente a analizar.
    """
    logger = obtener_logger()
    logger.info(f"Iniciando escaneo en: {origen}")
    typer.echo(f"🔍 Iniciando escaneo en: {origen}\n")

    resultado = analizar_directorio(origen)
    resumen = resultado.obtener_resumen()

    typer.secho("📊 Resumen del escaneo:", bold=True)
    typer.echo(
        f"  🖼️  Imágenes:         {resumen.conteo_por_tipo[TipoArchivo.IMAGEN]}"
    )
    typer.echo(
        f"  📸 RAWs:             {resumen.conteo_por_tipo[TipoArchivo.RAW]}"
    )
    typer.echo(
        f"  🎥 Videos:           {resumen.conteo_por_tipo[TipoArchivo.VIDEO]}"
    )
    typer.echo(
        "  📄 Auxiliares (XMP): "
        f"{resumen.conteo_por_tipo[TipoArchivo.AUXILIAR]}"
    )

    if resumen.total_desconocidos > 0:
        typer.secho(
            f"  ❓ Desconocidos:     {resumen.total_desconocidos}",
            fg=typer.colors.YELLOW,
        )

    typer.echo(f"\n📦 Grupos de medios principales: {resumen.total_grupos}")
    typer.echo(
        f"🔗 Sidecars asociados:            {resumen.sidecars_asociados}"
    )

    if resumen.sidecars_huerfanos > 0:
        typer.secho(
            f"⚠️  Sidecars huérfanos:          {resumen.sidecars_huerfanos}",
            fg=typer.colors.YELLOW,
        )

    if resumen.sidecars_ambiguos > 0:
        typer.secho(
            f"⚠️  Sidecars ambiguos:           {resumen.sidecars_ambiguos}",
            fg=typer.colors.YELLOW,
        )

    typer.echo(f"\nTotal de archivos analizados: {resumen.total_archivos}")
    logger.info(
        f"Escaneo completado. Total procesados: {resumen.total_archivos} "
        f"({resumen.total_grupos} grupos de medios)"
    )


@app.command()
def plan(
    origen: Path = typer.Argument(  # noqa: B008
        ...,
        help="Ruta de la carpeta origen a organizar.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    destino: Path = typer.Option(  # noqa: B008
        ...,
        "--destino",
        "-d",
        help="Ruta de la carpeta destino.",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    salida: Path | None = typer.Option(  # noqa: B008
        None,
        "--salida",
        "-s",
        help="Ruta opcional para guardar el plan en formato JSON.",
        dir_okay=False,
        resolve_path=True,
    ),
) -> None:
    """Genera un plan de organización sin modificar archivos.

    Args:
        origen (Path): Directorio de origen a organizar.
        destino (Path): Directorio objetivo final.
        salida (Path | None): Ruta opcional para exportar el plan.
    """
    logger = obtener_logger()

    try:
        validar_rutas(origen, destino)
    except ValueError as e:
        logger.error(f"Error al validar las rutas del plan: {e}")
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e

    logger.info(f"Generando plan desde {origen} hacia {destino}")
    typer.echo(
        f"📋 Generando plan para organizar desde {origen} hacia {destino}\n"
    )

    try:
        resultado = analizar_directorio(origen)
        plan_org = generar_plan(resultado, origen, destino)
    except ValueError as e:
        logger.error(f"Error al generar el plan: {e}")
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e

    total_mover = sum(
        1 for op in plan_org.operaciones if op.accion == AccionPlan.MOVER
    )
    total_sidecars = sum(
        len(op.sidecars_asociados) for op in plan_org.operaciones
    )
    total_advertencias = sum(
        len(op.advertencias) for op in plan_org.operaciones
    )

    typer.secho("📊 Resumen del plan de organización:", bold=True)
    typer.echo(f"  📦 Archivos a mover:         {total_mover}")
    typer.echo(f"  🔗 Sidecars acompañantes:    {total_sidecars}")

    if len(plan_org.sidecars_omitidos) > 0:
        typer.secho(
            "  ⚠️  Sidecars omitidos:        "
            f"{len(plan_org.sidecars_omitidos)}",
            fg=typer.colors.YELLOW,
        )

    if len(plan_org.desconocidos) > 0:
        typer.secho(
            f"  ❓ Desconocidos omitidos:     {len(plan_org.desconocidos)}",
            fg=typer.colors.YELLOW,
        )

    if total_advertencias > 0:
        typer.secho(
            f"  ⚠️  Advertencias registradas:  {total_advertencias}",
            fg=typer.colors.YELLOW,
        )

    logger.info(
        f"Plan generado exitosamente. Mover: {total_mover}, "
        f"Sidecars: {total_sidecars}, Advertencias: {total_advertencias}"
    )

    if salida:
        exportar_plan_json(plan_org, salida)
        typer.echo(f"\n💾 Plan exportado exitosamente en: {salida}")
        logger.info(f"Plan exportado a JSON en: {salida}")


def _obtener_ruta_plan_seleccionado(plan_path: Path | None) -> Path:
    """Resuelve y valida la ruta del archivo de plan a procesar.

    Args:
        plan_path (Path | None): Ruta proporcionada desde la CLI.

    Returns:
        Path: Ruta confirmada del archivo de plan.

    Raises:
        typer.Exit: Si no existen planes o la selección es inválida.
    """
    if plan_path is not None:
        return plan_path

    planes: list[Path] = buscar_archivos_plan(Path.cwd())
    if not planes:
        logger = obtener_logger()
        logger.error("No se encontraron archivos de plan JSON.")
        typer.secho(
            "❌ No se encontraron archivos de plan JSON en el directorio "
            "actual. Ejecute primero 'mulita plan' para generar uno.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    if len(planes) == 1:
        seleccionado: Path = planes[0]
        typer.echo(
            f"📄 Plan seleccionado automáticamente: {seleccionado.name}"
        )
        return seleccionado

    typer.echo("📑 Se encontraron varios archivos de plan:")
    for i, p in enumerate(planes, 1):
        typer.echo(f"  [{i}] {p.name}")

    opcion_raw = typer.prompt(
        "Seleccione el número del plan que desea ejecutar",
        type=int,
    )
    opcion: int = int(opcion_raw)

    if opcion < 1 or opcion > len(planes):
        logger = obtener_logger()
        logger.error("Opción inválida seleccionada para el plan: %s", opcion)
        typer.secho(
            "❌ Opción inválida seleccionada.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    return planes[opcion - 1]


@app.command()
def run(
    plan_path: Path | None = typer.Argument(  # noqa: B008
        None,
        help=(
            "Ruta opcional al archivo JSON de plan. Si no se especifica, se "
            "buscarán planes en el directorio actual."
        ),
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--ejecutar",
        help=(
            "Mantener activado para simular. Usar --ejecutar para mover "
            "archivos reales."
        ),
    ),
) -> None:
    """Ejecuta un plan de organización guardado previamente.

    Args:
        plan_path (Path | None): Ruta al archivo de plan JSON.
        dry_run (bool): Si es ``True`` se ejecuta en modo de simulación.
    """
    logger = obtener_logger()
    archivo_plan: Path = _obtener_ruta_plan_seleccionado(plan_path)

    try:
        plan_org = cargar_plan_json(archivo_plan)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Error al cargar el plan desde {archivo_plan}: {e}")
        typer.secho(
            f"❌ Error al cargar el plan: {e}", fg=typer.colors.RED, err=True
        )
        raise typer.Exit(code=1) from e

    total_mover = sum(
        1 for op in plan_org.operaciones if op.accion == AccionPlan.MOVER
    )
    total_sidecars = sum(
        len(op.sidecars_asociados) for op in plan_org.operaciones
    )

    if dry_run:
        typer.secho(
            "\n🛡️ MODO SIMULACIÓN (--dry-run). No se modificará ningún archivo.",
            fg=typer.colors.CYAN,
            bold=True,
        )
        typer.echo(f"  Plan: {archivo_plan.name}")
        typer.echo(f"  Origen: {plan_org.directorio_origen}")
        typer.echo(f"  Destino: {plan_org.directorio_destino}")
        typer.echo(f"  Archivos previstos a mover: {total_mover}")
        typer.echo(f"  Sidecars acompañantes: {total_sidecars}\n")
        logger.info(
            f"Simulación de ejecución realizada para {archivo_plan.name}"
        )
        return

    typer.secho(
        "\n⚠️ MODO EJECUCIÓN REAL: Se moverán archivos en el disco.",
        fg=typer.colors.YELLOW,
        bold=True,
    )
    typer.echo(f"  Plan: {archivo_plan.name}")
    typer.echo(
        f"  Operaciones a realizar: {total_mover} archivos principales."
    )

    confirmar = typer.confirm("¿Desea proceder con la ejecución del plan?")
    if not confirmar:
        logger.info("Ejecución real cancelada por el usuario.")
        typer.echo("Operación cancelada por el usuario.")
        raise typer.Exit(code=0)

    typer.echo("\n🚀 Ejecutando plan de organización...")
    logger.info(f"Iniciando ejecución real del plan: {archivo_plan.name}")

    resultado = ejecutar_plan(plan_org)

    registrar_resultado_detallado_en_log(resultado)

    nombre_stem: str = str(archivo_plan.stem)
    identificador: str = nombre_stem.removeprefix("plan_")
    ruta_auditoria = Path("reportes") / f"ejecucion_{identificador}.json"
    exportar_resultado_ejecucion_json(resultado, ruta_auditoria)

    typer.secho("\n📊 Resumen de la ejecución:", bold=True)
    typer.secho(
        f"  ✅ Procesados con éxito: {resultado.procesados_exitosamente}",
        fg=typer.colors.GREEN,
    )

    if resultado.fallidos > 0:
        typer.secho(
            f"  ❌ Operaciones fallidas:  {resultado.fallidos}",
            fg=typer.colors.RED,
        )
        typer.echo("\nDetalle de errores y recuperaciones:")
        for fallo in resultado.errores:
            if fallo.requiere_recuperacion_manual:
                typer.secho(
                    f"  🚨 [RECUPERACIÓN MANUAL REQUERIDA] "
                    f"{fallo.operacion.origen.name}: {fallo.error}",
                    fg=typer.colors.RED,
                    bold=True,
                )
            else:
                typer.secho(
                    f"  🔄 [REVERTIDO OK] {fallo.operacion.origen.name}: "
                    f"{fallo.error}",
                    fg=typer.colors.YELLOW,
                )

    typer.echo(f"\n📄 Auditoría JSON guardada en: {ruta_auditoria}")
    logger.info(
        f"Ejecución finalizada. Éxitos: {resultado.procesados_exitosamente}, "
        f"Fallos: {resultado.fallidos}. Auditoría en {ruta_auditoria}"
    )
