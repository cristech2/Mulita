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


def _validar_rutas_anidadas_en_plan(rutas: list[Path], tipo: str) -> None:
    """Rechaza rutas donde una ruta de archivo es antecesora de otra."""
    normalizadas = [
        Path(os.path.abspath(os.path.normpath(ruta))) for ruta in rutas
    ]
    conjunto = set(normalizadas)

    for ruta in conjunto:
        if any(padre in conjunto for padre in ruta.parents):
            raise ValueError(
                f"El plan JSON contiene rutas de {tipo} anidadas "
                f"incompatibles: {ruta}"
            )


def _validar_ruta_destino_plan(
    destino: Path,
    directorio_destino: Path,
    fecha: datetime,
    categoria: TipoArchivo,
    indice_operacion: int,
) -> None:
    """Valida la jerarquía YYYY/MM/DD/CATEGORIA/archivo del plan."""
    base = Path(os.path.abspath(os.path.normpath(directorio_destino)))
    ruta = Path(os.path.abspath(os.path.normpath(destino)))
    try:
        partes = ruta.relative_to(base).parts
    except ValueError as e:
        raise ValueError(
            f"el destino de la operación {indice_operacion} está fuera "
            f"de 'directorio_destino': {destino}"
        ) from e

    esperado = (
        f"{fecha.year:04d}",
        f"{fecha.month:02d}",
        f"{fecha.day:02d}",
        categoria.name,
    )
    if len(partes) != 5 or partes[:4] != esperado or not partes[4]:
        raise ValueError(
            f"el destino de la operación {indice_operacion} debe seguir "
            f"la estructura YYYY/MM/DD/CATEGORIA/archivo "
            f"({ '/'.join(esperado) }/{destino.name}): {destino}"
        )


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

    try:
        with ruta_json.open("r", encoding="utf-8") as f:
            datos = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"El archivo JSON no tiene un formato de plan válido: {e}"
        ) from e

    try:
        if not isinstance(datos, dict):
            raise TypeError("la raíz del JSON debe ser un objeto")

        directorio_origen = datos["directorio_origen"]
        directorio_destino = datos["directorio_destino"]
        operaciones_json = datos["operaciones"]
        if not isinstance(directorio_origen, str) or not directorio_origen:
            raise TypeError("'directorio_origen' debe ser una ruta no vacía")
        if not isinstance(directorio_destino, str) or not directorio_destino:
            raise TypeError("'directorio_destino' debe ser una ruta no vacía")
        if not isinstance(operaciones_json, list):
            raise TypeError("'operaciones' debe ser una lista")

        operaciones: list[OperacionPlan] = []
        origenes: list[Path] = []
        destinos: list[Path] = []
        for indice, op in enumerate(operaciones_json):
            if not isinstance(op, dict):
                raise TypeError(f"la operación {indice} debe ser un objeto")

            for nombre in ("origen", "destino", "categoria", "accion"):
                if not isinstance(op.get(nombre), str) or not op[nombre]:
                    raise TypeError(
                        f"'{nombre}' debe ser texto no vacío "
                        f"en la operación {indice}"
                    )

            fecha_dict = op["fecha_resultado"]
            if not isinstance(fecha_dict, dict):
                raise TypeError(
                    f"'fecha_resultado' debe ser un objeto "
                    f"en la operación {indice}"
                )
            if not isinstance(fecha_dict.get("fecha"), str):
                raise TypeError(
                    f"'fecha_resultado.fecha' debe ser texto "
                    f"en la operación {indice}"
                )
            if not isinstance(fecha_dict.get("fuente"), str):
                raise TypeError(
                    f"'fecha_resultado.fuente' debe ser texto "
                    f"en la operación {indice}"
                )
            if type(fecha_dict.get("es_respaldo")) is not bool:
                raise TypeError(
                    f"'fecha_resultado.es_respaldo' debe ser booleano "
                    f"en la operación {indice}"
                )

            fecha_res = FechaResultado(
                fecha=datetime.fromisoformat(fecha_dict["fecha"]),
                fuente=fecha_dict["fuente"],
                es_respaldo=fecha_dict["es_respaldo"],
            )

            sidecars_json = op.get("sidecars_asociados", [])
            if not isinstance(sidecars_json, list):
                raise TypeError(
                    f"'sidecars_asociados' debe ser una lista "
                    f"en la operación {indice}"
                )
            if any(
                not isinstance(sidecar, list)
                or len(sidecar) != 2
                or not all(isinstance(ruta, str) and ruta for ruta in sidecar)
                for sidecar in sidecars_json
            ):
                raise TypeError(
                    f"cada sidecar debe contener dos rutas de texto "
                    f"en la operación {indice}"
                )
            sidecars = [
                (Path(sidecar[0]), Path(sidecar[1]))
                for sidecar in sidecars_json
            ]

            advertencias = op.get("advertencias", [])
            if not isinstance(advertencias, list) or not all(
                isinstance(advertencia, str) for advertencia in advertencias
            ):
                raise TypeError(
                    f"'advertencias' debe ser una lista de textos "
                    f"en la operación {indice}"
                )

            accion = AccionPlan[op["accion"]]
            if accion == AccionPlan.MOVER:
                destino_principal = Path(op["destino"])
                _validar_ruta_destino_plan(
                    destino_principal,
                    Path(directorio_destino),
                    fecha_res.fecha,
                    TipoArchivo[op["categoria"]],
                    indice,
                )
                origenes.append(Path(op["origen"]))
                destinos.append(destino_principal)
                for origen_sidecar, destino_sidecar in sidecars:
                    _validar_ruta_destino_plan(
                        destino_sidecar,
                        Path(directorio_destino),
                        fecha_res.fecha,
                        TipoArchivo[op["categoria"]],
                        indice,
                    )
                    if destino_sidecar.parent != destino_principal.parent:
                        raise ValueError(
                            f"el destino del sidecar de la operación "
                            f"{indice} debe estar junto al archivo principal: "
                            f"{destino_sidecar}"
                        )
                    origenes.append(origen_sidecar)
                    destinos.append(destino_sidecar)

            operaciones.append(
                OperacionPlan(
                    origen=Path(op["origen"]),
                    destino=Path(op["destino"]),
                    categoria=TipoArchivo[op["categoria"]],
                    fecha_resultado=fecha_res,
                    sidecars_asociados=sidecars,
                    accion=accion,
                    advertencias=advertencias,
                )
            )

        plan = PlanOrganizacion(
            directorio_origen=Path(directorio_origen),
            directorio_destino=Path(directorio_destino),
            operaciones=operaciones,
            sidecars_omitidos=[],  # Omitidos en ejecución
            desconocidos=[],
        )
        _validar_rutas_anidadas_en_plan(origenes, "origen")
        _validar_rutas_anidadas_en_plan(destinos, "destino")
        return plan
    except (KeyError, TypeError, ValueError) as e:
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
