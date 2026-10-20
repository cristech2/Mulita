"""
Módulo para la resolución y priorización de fechas de archivos.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

FORMATOS_EXIF: list[str] = [
    "%Y:%m:%d %H:%M:%S",
    "%Y:%m:%d %H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S",
]


@dataclass
class FechaResultado:
    """
    Representa el resultado final del análisis de fecha de un archivo.
    """

    fecha: datetime
    fuente: str
    es_respaldo: bool


def _parsear_fecha_exif(cadena_fecha: str | None) -> datetime | None:
    if not cadena_fecha:
        return None

    cadena_limpia = cadena_fecha.split(".")[0].strip()

    for formato in FORMATOS_EXIF:
        try:
            return datetime.strptime(cadena_limpia, formato)
        except ValueError:
            continue

    return None


def _obtener_fecha_modificacion(ruta: Path) -> datetime:
    timestamp = ruta.stat().st_mtime
    return datetime.fromtimestamp(timestamp)


def resolver_fecha_archivo(
    ruta: Path, tipo: Any, metadatos: dict[str, str]
) -> FechaResultado:
    """
    Determina la fecha organizativa según las reglas de prioridad del TipoArchivo.
    """
    # Importación diferida o evaluación por atributo para evitar importación circular
    es_video = getattr(tipo, "name", "") == "VIDEO"

    if es_video:
        prioridades = ["MediaCreateDate", "CreateDate", "DateTimeOriginal"]
    else:
        prioridades = ["DateTimeOriginal", "CreateDate"]

    for tag in prioridades:
        valor_raw = metadatos.get(tag)
        if valor_raw:
            dt = _parsear_fecha_exif(valor_raw)
            if dt:
                return FechaResultado(fecha=dt, fuente=tag, es_respaldo=False)

    dt_mod = _obtener_fecha_modificacion(ruta)
    return FechaResultado(fecha=dt_mod, fuente="FileModifyDate", es_respaldo=True)
