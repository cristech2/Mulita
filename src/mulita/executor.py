"""Ejecución segura y trazable del plan de organización de archivos."""

import shutil
from datetime import datetime
from pathlib import Path

from mulita.models import (
    AccionPlan,
    EstadoEjecucionOperacion,
    FalloOperacion,
    OperacionPlan,
    PlanOrganizacion,
    RegistroOperacionArchivo,
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


def _trasladar_y_verificar(origen: Path, destino: Path) -> None:
    """Traslada un archivo a su destino y confirma su integridad básica.

    Args:
        origen (Path): Ruta del archivo original.
        destino (Path): Ruta de destino.

    Raises:
        FileNotFoundError: Si el origen no existe.
        FileExistsError: Si el destino ya existe.
        OSError: Si el traslado o la verificación post-movimiento fallan.
    """
    _validar_existencia_origen_y_destino(origen, destino)

    tamano_esperado = origen.stat().st_size
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(origen, destino)

    if not destino.exists() or not destino.is_file():
        raise OSError(
            f"El archivo trasladado no existe en el destino tras el movimiento: {destino}"
        )

    tamano_destino = destino.stat().st_size
    if tamano_destino != tamano_esperado:
        raise OSError(
            f"Inconsistencia en tamaño tras traslado para {destino}: "
            f"esperado {tamano_esperado} bytes, obtenido {tamano_destino} bytes."
        )


def _revertir_movimientos(
    movimientos_realizados: list[tuple[Path, Path]],
) -> list[str]:
    """Intenta revertir los traslados realizados devolviendo archivos a su origen.

    Args:
        movimientos_realizados (list[tuple[Path, Path]]): Lista de tuplas
            (origen_original, destino_actual) en el orden en que se movieron.

    Returns:
        list[str]: Lista de errores ocurridos durante la reversión si los hubiere.
    """
    errores_reversion: list[str] = []

    # Revertir en orden inverso
    for origen_original, destino_actual in reversed(movimientos_realizados):
        try:
            if destino_actual.exists():
                origen_original.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(destino_actual, origen_original)
        except Exception as e:
            errores_reversion.append(
                f"No se pudo restaurar {destino_actual} a {origen_original}: {e}"
            )

    return errores_reversion


def _ejecutar_operacion_individual(
    operacion: OperacionPlan,
) -> list[RegistroOperacionArchivo]:
    """Realiza el traslado del archivo principal y sus sidecars con soporte de rollback.

    Args:
        operacion (OperacionPlan): Instrucción detallada de movimiento.

    Returns:
        list[RegistroOperacionArchivo]: Historial detallado de los traslados efectuados.

    Raises:
        RuntimeError: Si ocurre un error durante el traslado y/o la reversión.
    """
    movimientos_exitosos: list[tuple[Path, Path]] = []
    registros: list[RegistroOperacionArchivo] = []
    ahora = datetime.now()

    # Validaciones previas para todo el conjunto antes de mover
    _validar_existencia_origen_y_destino(operacion.origen, operacion.destino)
    for origen_sidecar, destino_sidecar in operacion.sidecars_asociados:
        _validar_existencia_origen_y_destino(origen_sidecar, destino_sidecar)

    try:
        # 1. Trasladar archivo principal
        _trasladar_y_verificar(operacion.origen, operacion.destino)
        movimientos_exitosos.append((operacion.origen, operacion.destino))
        registros.append(
            RegistroOperacionArchivo(
                origen=operacion.origen,
                destino=operacion.destino,
                estado=EstadoEjecucionOperacion.EXITOSO,
                timestamp=ahora,
                es_sidecar=False,
            )
        )

        # 2. Trasladar sidecars asociados
        for origen_sidecar, destino_sidecar in operacion.sidecars_asociados:
            _trasladar_y_verificar(origen_sidecar, destino_sidecar)
            movimientos_exitosos.append((origen_sidecar, destino_sidecar))
            registros.append(
                RegistroOperacionArchivo(
                    origen=origen_sidecar,
                    destino=destino_sidecar,
                    estado=EstadoEjecucionOperacion.EXITOSO,
                    timestamp=ahora,
                    es_sidecar=True,
                )
            )

        return registros

    except Exception as err:
        # Intentar reversión automatizada (Rollback)
        errores_reversion = _revertir_movimientos(movimientos_exitosos)

        if errores_reversion:
            msg_error = (
                f"Fallo durante traslado ({err}). Rollback incompleto: "
                f"{'; '.join(errores_reversion)}"
            )
            raise RuntimeError(msg_error) from err

        raise RuntimeError(
            f"Fallo durante traslado ({err}). Operación revertida exitosamente."
        ) from err


def ejecutar_plan(plan: PlanOrganizacion) -> ResultadoEjecucion:
    """Ejecuta de forma segura las operaciones autorizadas dentro del plan.

    Procesa cada operación de forma independiente con verificación y rollback,
    garantizando que un error individual no detenga la ejecución del lote.

    Args:
        plan (PlanOrganizacion): Plan de organización previamente generado.

    Returns:
        ResultadoEjecucion: Resumen consolidado con contadores, registros y errores.
    """
    exitosos = 0
    fallidos = 0
    lista_fallos: list[FalloOperacion] = []
    todos_los_registros: list[RegistroOperacionArchivo] = []

    for operacion in plan.operaciones:
        ahora = datetime.now()

        if operacion.accion == AccionPlan.OMITIR:
            todos_los_registros.append(
                RegistroOperacionArchivo(
                    origen=operacion.origen,
                    destino=operacion.destino,
                    estado=EstadoEjecucionOperacion.OMITIDO,
                    timestamp=ahora,
                    es_sidecar=False,
                )
            )
            for origen_s, destino_s in operacion.sidecars_asociados:
                todos_los_registros.append(
                    RegistroOperacionArchivo(
                        origen=origen_s,
                        destino=destino_s,
                        estado=EstadoEjecucionOperacion.OMITIDO,
                        timestamp=ahora,
                        es_sidecar=True,
                    )
                )
            continue

        try:
            registros_op = _ejecutar_operacion_individual(operacion)
            todos_los_registros.extend(registros_op)
            exitosos += 1
        except Exception as err:
            fallidos += 1
            es_manual = "Rollback incompleto" in str(err)
            estado_fallo = (
                EstadoEjecucionOperacion.FALLIDO_RECUPERACION_MANUAL
                if es_manual
                else EstadoEjecucionOperacion.FALLIDO_REVERTIDO
            )

            todos_los_registros.append(
                RegistroOperacionArchivo(
                    origen=operacion.origen,
                    destino=operacion.destino,
                    estado=estado_fallo,
                    timestamp=ahora,
                    es_sidecar=False,
                    detalle_error=str(err),
                )
            )

            lista_fallos.append(
                FalloOperacion(
                    operacion=operacion,
                    error=str(err),
                    requiere_recuperacion_manual=es_manual,
                )
            )

    return ResultadoEjecucion(
        procesados_exitosamente=exitosos,
        fallidos=fallidos,
        errores=lista_fallos,
        registros_detallados=todos_los_registros,
    )
