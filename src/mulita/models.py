"""
Módulo de modelos de datos y enumeraciones del dominio para Mulita.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path


class TipoArchivo(Enum):
    """Enumeración de los tipos de archivos soportados."""

    IMAGEN = auto()
    RAW = auto()
    VIDEO = auto()
    AUXILIAR = auto()
    DESCONOCIDO = auto()


class EstadoAsociacion(Enum):
    """Estado de vinculación de un archivo auxiliar o sidecar."""

    ASOCIADO = auto()
    HUERFANO = auto()
    AMBIGUO = auto()


@dataclass
class FechaResultado:
    """
    Representa el resultado final del análisis de fecha de un archivo.
    """

    fecha: datetime
    fuente: str
    es_respaldo: bool


@dataclass
class ArchivoEscaneado:
    """
    Representa un archivo encontrado durante el escaneo con su tipo
    clasificado.
    """

    ruta: Path
    tipo: TipoArchivo


@dataclass
class ArchivoAnalizado:
    """
    Representa un archivo escaneado con su resolución de fecha y metadatos.
    """

    archivo: ArchivoEscaneado
    fecha_resultado: FechaResultado
    metadatos: dict[str, str]


@dataclass
class SidecarAsociado:
    """
    Representa un archivo auxiliar procesado y su estado de asociación.
    """

    archivo: ArchivoAnalizado
    estado: EstadoAsociacion
    motivo: str = ""


def _lista_sidecars_vacia() -> list[ArchivoAnalizado]:
    """Fábrica para inicializar la lista de sidecars con tipado explícito."""
    return []


@dataclass
class GrupoArchivo:
    """
    Representa un archivo principal junto con sus sidecars vinculados.
    """

    principal: ArchivoAnalizado
    sidecars: list[ArchivoAnalizado] = field(default_factory=_lista_sidecars_vacia)


@dataclass
class ResumenEscaneo:
    """Consolidado de métricas calculado a partir de un ResultadoEscaneo."""

    conteo_por_tipo: dict[TipoArchivo, int]
    total_grupos: int
    sidecars_asociados: int
    sidecars_huerfanos: int
    sidecars_ambiguos: int
    total_desconocidos: int
    total_archivos: int


@dataclass
class ResultadoEscaneo:
    """
    Resultado consolidado de la fase de escaneo, incluyendo grupos de medios,
    sidecars no asociados y archivos desconocidos.
    """

    grupos: list[GrupoArchivo]
    sidecars_no_asociados: list[SidecarAsociado]
    desconocidos: list[ArchivoAnalizado]

    def obtener_resumen(self) -> ResumenEscaneo:
        """Calcula y devuelve las métricas consolidadas de la fase de escaneo."""
        conteo: dict[TipoArchivo, int] = {tipo: 0 for tipo in TipoArchivo}

        huerfanos = 0
        ambiguos = 0
        asociados = 0

        # Contar archivos en grupos (principales y sidecars asociados)
        for grupo in self.grupos:
            conteo[grupo.principal.archivo.tipo] += 1
            for sidecar in grupo.sidecars:
                conteo[sidecar.archivo.tipo] += 1
                asociados += 1

        # Contar sidecars no asociados (huérfanos y ambiguos)
        for sidecar_na in self.sidecars_no_asociados:
            conteo[sidecar_na.archivo.archivo.tipo] += 1
            if sidecar_na.estado == EstadoAsociacion.HUERFANO:
                huerfanos += 1
            elif sidecar_na.estado == EstadoAsociacion.AMBIGUO:
                ambiguos += 1

        # Contar desconocidos
        for desc in self.desconocidos:
            conteo[desc.archivo.tipo] += 1

        total = sum(conteo.values())

        return ResumenEscaneo(
            conteo_por_tipo=conteo,
            total_grupos=len(self.grupos),
            sidecars_asociados=asociados,
            sidecars_huerfanos=huerfanos,
            sidecars_ambiguos=ambiguos,
            total_desconocidos=len(self.desconocidos),
            total_archivos=total,
        )
