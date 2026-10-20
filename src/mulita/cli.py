"""CLI para Mulita.

Define los comandos, argumentos y opciones de Typer para el flujo principal
de la aplicación.
"""

from pathlib import Path

import typer

from mulita.models import AccionPlan, TipoArchivo
from mulita.planner import generar_plan
from mulita.reporting import (
    configurar_logging,
    exportar_plan_json,
    obtener_logger,
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
        "  🖼️  Imágenes:         "
        f"{resumen.conteo_por_tipo[TipoArchivo.IMAGEN]}"
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


@app.command()
def run(
    origen: Path = typer.Argument(  # noqa: B008
        ...,
        help="Ruta de la carpeta origen.",
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
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--ejecutar",
        help=(
            "Mantener activado para simular. Usar --ejecutar para mover "
            "archivos reales."
        ),
    ),
) -> None:
    """Ejecuta el plan de organización sobre los archivos.

    Args:
        origen (Path): Directorio a organizar.
        destino (Path): Destino final de la organización.
        dry_run (bool): Si es ``True`` se ejecuta en modo de simulación.
    """
    if dry_run:
        typer.secho(
            "🛡️ Modo simulación (--dry-run). No se modificará ningún archivo.",
            fg=typer.colors.CYAN,
        )
    else:
        typer.secho(
            "⚠️ MODO EJECUCIÓN: Se realizarán cambios "
            "en el sistema de archivos.",
            fg=typer.colors.YELLOW,
            bold=True,
        )
