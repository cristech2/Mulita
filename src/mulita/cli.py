"""
Módulo CLI para Mulita.

Define los comandos, argumentos y opciones de Typer.
Delega la lógica de negocio a los módulos especializados (scanner, planner, etc.).
"""

from pathlib import Path

import typer

from mulita.reporting import configurar_logging, obtener_logger
from mulita.scanner import TipoArchivo, escanear_directorio

app = typer.Typer(
    help="Mulita: Organizador seguro e inspeccionable de fotos y videos.",
    no_args_is_help=True,
)


@app.callback()
def main(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Activa el modo debug con logs detallados."
    ),
    log_file: Path | None = typer.Option(  # noqa: B008
        None,
        "--log-file",
        help="Directorio o archivo base para guardar el registro de la operación.",
        file_okay=True,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """
    Configuración global antes de ejecutar cualquier comando.
    """
    configurar_logging(verbose=verbose, log_file=log_file)


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
    """
    Inspecciona recursivamente archivos compatibles y resume resultados.
    """
    logger = obtener_logger()
    logger.info(f"Iniciando escaneo en: {origen}")
    typer.echo(f"🔍 Iniciando escaneo en: {origen}\n")

    archivos = escanear_directorio(origen)

    conteo = {tipo: 0 for tipo in TipoArchivo}
    for archivo in archivos:
        conteo[archivo.tipo] += 1
        if archivo.tipo == TipoArchivo.DESCONOCIDO:
            logger.warning(f"Archivo desconocido/no reconocido: {archivo.ruta}")
        else:
            logger.debug(f"Encontrado: {archivo.ruta} [{archivo.tipo.name}]")

    typer.secho("📊 Resumen del escaneo:", bold=True)
    typer.echo(f"  🖼️  Imágenes: {conteo[TipoArchivo.IMAGEN]}")
    typer.echo(f"  📸 RAWs:     {conteo[TipoArchivo.RAW]}")
    typer.echo(f"  🎥 Videos:   {conteo[TipoArchivo.VIDEO]}")
    typer.echo(f"  📄 Auxiliares (XMP): {conteo[TipoArchivo.AUXILIAR]}")

    if conteo[TipoArchivo.DESCONOCIDO] > 0:
        typer.secho(
            f"  ❓ Desconocidos/Ignorados: {conteo[TipoArchivo.DESCONOCIDO]}",
            fg=typer.colors.YELLOW,
        )

    typer.echo(f"\nTotal de archivos analizados: {len(archivos)}")
    logger.info(f"Escaneo completado. Total encontrados: {len(archivos)}")


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
    """
    Genera y muestra un plan de organización sin modificar archivos.
    """
    typer.echo(f"📋 Generando plan para organizar desde {origen} hacia {destino}")
    if salida:
        typer.echo(f"El plan se guardará en: {salida}")


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
        help="Mantener activado para simular. Usar --ejecutar para mover archivos reales.",
    ),
) -> None:
    """
    Ejecuta el plan de organización sobre los archivos.
    """
    if dry_run:
        typer.secho(
            "🛡️ Modo simulación (--dry-run). No se modificará ningún archivo.",
            fg=typer.colors.CYAN,
        )
    else:
        typer.secho(
            "⚠️ MODO EJECUCIÓN: Se realizarán cambios en el sistema de archivos.",
            fg=typer.colors.YELLOW,
            bold=True,
        )
