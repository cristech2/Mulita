"""Ejecución segura y trazable del plan de organización de archivos."""

import shutil
from pathlib import Path

from mulita.models import (
    AccionPlan,
    FalloOperacion,
    OperacionPlan,
    PlanOrganizacion,
    ResultadoEjecucion,
)


def _validar_existencia_origen_y_destino(origen: Path, destino: Path) -> None:
    """Verifica que el origen exista y el destino no esté ocupado.

    Args:
        origen (Path): Ruta del archivo original.
        destino (Path): Ruta donde se trasladará el archivo.

    Raises:
        FileNotFoundError: Si el archivo origen no existe en disco.
        FileExistsError: Si el archivo destino ya existe en disco.
    """
    if not origen.exists():
        raise FileNotFoundError(
            f"El archivo origen no existe en el sistema: {origen}"
        )

    if destino.exists():
        raise FileExistsError(
            f"El archivo destino ya existe para evitar sobrescritura: {destino}"
        )


def _ejecutar_operacion_individual(operacion: OperacionPlan) -> None:
    """Realiza el traslado del archivo principal y sus sidecars asociados.

    Args:
        operacion (OperacionPlan): Instrucción detallada de movimiento.

    Raises:
        FileNotFoundError: Si algún origen no existe en el sistema.
        FileExistsError: Si algún destino ya existe en el sistema.
        OSError: En caso de errores de permisos o fallos de E/S.
    """
    _validar_existencia_origen_y_destino(operacion.origen, operacion.destino)

    for origen_sidecar, destino_sidecar in operacion.sidecars_asociados:
        _validar_existencia_origen_y_destino(origen_sidecar, destino_sidecar)

    operacion.destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(operacion.origen, operacion.destino)

    for origen_sidecar, destino_sidecar in operacion.sidecars_asociados:
        destino_sidecar.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(origen_sidecar, destino_sidecar)


def ejecutar_plan(plan: PlanOrganizacion) -> ResultadoEjecucion:
    """Ejecuta de forma segura las operaciones autorizadas dentro del plan.

    Procesa cada operación de forma independiente, garantizando que un error
    individual en un archivo o sidecar no detenga la ejecución del resto
    del lote.

    Args:
        plan (PlanOrganizacion): Plan de organización previamente generado.

    Returns:
        ResultadoEjecucion: Resumen consolidado con contadores y errores.
    """
    exitosos = 0
    fallidos = 0
    lista_fallos: list[FalloOperacion] = []

    for operacion in plan.operaciones:
        if operacion.accion == AccionPlan.OMITIR:
            continue

        try:
            _ejecutar_operacion_individual(operacion)
            exitosos += 1
        except Exception as err:
            fallidos += 1
            lista_fallos.append(
                FalloOperacion(
                    operacion=operacion,
                    error=str(err),
                )
            )

    return ResultadoEjecucion(
        procesados_exitosamente=exitosos,
        fallidos=fallidos,
        errores=lista_fallos,
    )
