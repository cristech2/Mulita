"""Persistencia, serialización y búsqueda de planes de organización en JSON."""

import json
import os
import tempfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from mulita.models import (
    AccionPlan,
    FechaResultado,
    OperacionPlan,
    PlanOrganizacion,
    ResultadoEjecucion,
    TipoArchivo,
)


def validar_ruta_exportacion(ruta_salida: Path) -> None:
    """Comprueba que el directorio de una salida permita crear archivos.

    Args:
        ruta_salida (Path): Ruta final prevista para la exportación.

    Raises:
        OSError: Si el directorio no se puede crear o no permite escribir.
        ValueError: Si la ruta de salida ya es un directorio.
    """
    if ruta_salida.exists() and ruta_salida.is_dir():
        raise ValueError(
            f"La ruta de salida corresponde a un directorio: {ruta_salida}"
        )

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=ruta_salida.parent,
        prefix=".mulita-validacion-",
        delete=True,
    ):
        pass


def _escribir_json_atomico(datos: Any, ruta_salida: Path) -> None:
    """Escribe JSON en un temporal y publica el archivo de forma atómica.

    Args:
        datos (Any): Estructura serializable que se debe guardar.
        ruta_salida (Path): Ruta final del archivo JSON.
    """
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    temporal: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=ruta_salida.parent,
            prefix=f".{ruta_salida.name}.",
            suffix=".tmp",
            delete=False,
        ) as archivo:
            temporal = Path(archivo.name)
            json.dump(datos, archivo, indent=4, ensure_ascii=False)
            archivo.flush()
            os.fsync(archivo.fileno())

        os.replace(temporal, ruta_salida)
    finally:
        if temporal is not None and temporal.exists():
            temporal.unlink()


def exportar_resultado_ejecucion_json(
    resultado: ResultadoEjecucion, ruta_salida: Path
) -> None:
    """Exporta el historial detallado por archivo a un JSON de auditoría.

    Args:
        resultado (ResultadoEjecucion): Resultado retornado por el ejecutor.
        ruta_salida (Path): Ruta donde se guardará el log JSON de ejecución.
    """
    datos = _convertir_a_json_compatible(resultado)
    _escribir_json_atomico(datos, ruta_salida)


def _convertir_a_json_compatible(obj: Any) -> Any:
    """Convierte objetos del dominio en tipos nativos serializables a JSON.

    Args:
        obj (Any): Objeto a convertir.

    Returns:
        Any: Estructura de datos nativa serializable.
    """
    if isinstance(obj, Path):
        return obj.as_posix()
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.name
    if hasattr(obj, "__dict__"):
        return {
            k: _convertir_a_json_compatible(v) for k, v in obj.__dict__.items()
        }
    if isinstance(obj, dict):
        return {
            str(k): _convertir_a_json_compatible(v) for k, v in obj.items()
        }
    if isinstance(obj, (list, tuple, set)):
        return [_convertir_a_json_compatible(i) for i in obj]
    return obj


def exportar_plan_json(plan: PlanOrganizacion, ruta_salida: Path) -> None:
    """Exporta una instancia de PlanOrganizacion a un archivo JSON.

    Args:
        plan (PlanOrganizacion): Plan de organización a exportar.
        ruta_salida (Path): Ruta donde se guardará el archivo JSON.
    """
    datos = _convertir_a_json_compatible(plan)
    _escribir_json_atomico(datos, ruta_salida)


def cargar_plan_json(ruta_json: Path) -> PlanOrganizacion:
    """Carga y reconstruye un PlanOrganizacion desde un archivo JSON.

    Args:
        ruta_json (Path): Ruta al archivo JSON del plan.

    Returns:
        PlanOrganizacion: Instancia del modelo de dominio reconstruida.

    Raises:
        FileNotFoundError: Si el archivo JSON no existe.
        ValueError: Si la estructura del JSON es inválida o incompatible.
    """
    if not ruta_json.exists():
        raise FileNotFoundError(
            f"El archivo de plan especificado no existe: {ruta_json}"
        )

    with ruta_json.open("r", encoding="utf-8") as f:
        datos = json.load(f)

    try:
        operaciones: list[OperacionPlan] = []
        for op in datos.get("operaciones", []):
            fecha_dict = op["fecha_resultado"]
            fecha_res = FechaResultado(
                fecha=datetime.fromisoformat(fecha_dict["fecha"]),
                fuente=fecha_dict["fuente"],
                es_respaldo=fecha_dict["es_respaldo"],
            )

            sidecars = [
                (Path(s[0]), Path(s[1]))
                for s in op.get("sidecars_asociados", [])
            ]

            operaciones.append(
                OperacionPlan(
                    origen=Path(op["origen"]),
                    destino=Path(op["destino"]),
                    categoria=TipoArchivo[op["categoria"]],
                    fecha_resultado=fecha_res,
                    sidecars_asociados=sidecars,
                    accion=AccionPlan[op["accion"]],
                    advertencias=op.get("advertencias", []),
                )
            )

        return PlanOrganizacion(
            directorio_origen=Path(datos["directorio_origen"]),
            directorio_destino=Path(datos["directorio_destino"]),
            operaciones=operaciones,
            sidecars_omitidos=[],  # Omitidos en ejecución
            desconocidos=[],
        )
    except (KeyError, TypeError) as e:
        raise ValueError(
            f"El archivo JSON no tiene un formato de plan válido: {e}"
        ) from e


def buscar_archivos_plan(directorio: Path) -> list[Path]:
    """Busca archivos JSON con estructura de plan dentro de un directorio.

    Args:
        directorio (Path): Directorio donde buscar planes.

    Returns:
        list[Path]: Lista de rutas a archivos JSON de plan válidos.
    """
    if not directorio.exists() or not directorio.is_dir():
        return []

    planes_encontrados: list[Path] = []
    for archivo in directorio.glob("*.json"):
        try:
            with archivo.open("r", encoding="utf-8") as f:
                contenido = json.load(f)
                if (
                    isinstance(contenido, dict)
                    and "directorio_origen" in contenido
                    and "directorio_destino" in contenido
                    and "operaciones" in contenido
                ):
                    planes_encontrados.append(archivo)
        except Exception:
            continue

    return planes_encontrados
