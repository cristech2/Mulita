"""Módulo de modelos de datos y enumeraciones del dominio para Mulita."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path


class TipoArchivo(Enum):
    """Tipos de archivos soportados por el sistema.

    Attributes:
        IMAGEN: Archivos de imagen estándar.
        RAW: Archivos RAW de cámaras.
        VIDEO: Archivos de video.
        AUXILIAR: Sidecars o archivos auxiliares.
        DESCONOCIDO: Archivos no reconocidos.
    """

    IMAGEN = auto()
    RAW = auto()
    VIDEO = auto()
    AUXILIAR = auto()
    DESCONOCIDO = auto()


class EstadoAsociacion(Enum):
    """Estado de asociación de un archivo auxiliar o sidecar.

    Attributes:
        ASOCIADO: El sidecar fue relacionado con un principal.
        HUERFANO: El sidecar no tiene principal asociado.
        AMBIGUO: El sidecar puede corresponder a varios archivos.
    """

    ASOCIADO = auto()
    HUERFANO = auto()
    AMBIGUO = auto()


@dataclass
class FechaResultado:
    """Resultado final del análisis de fecha de un archivo.

    Attributes:
        fecha (datetime): Fecha calculada o inferida.
        fuente (str): Origen de la fecha (EXIF, sistema, etc.).
        es_respaldo (bool): Indica si la fecha es de respaldo.
    """

    fecha: datetime
    fuente: str
    es_respaldo: bool


@dataclass
class ArchivoEscaneado:
    """Archivo encontrado durante el escaneo.

    Attributes:
        ruta (Path): Ruta completa del archivo.
        tipo (TipoArchivo): Tipo de archivo clasificado.
    """

    ruta: Path
    tipo: TipoArchivo


@dataclass
class ArchivoAnalizado:
    """Archivo ya analizado con metadatos y fecha resuelta.

    Attributes:
        archivo (ArchivoEscaneado): Archivo original escaneado.
        fecha_resultado (FechaResultado): Fecha calculada.
        metadatos (dict[str, str]): Metadatos extraídos del archivo.
    """

    archivo: ArchivoEscaneado
    fecha_resultado: FechaResultado
    metadatos: dict[str, str]


@dataclass
class SidecarAsociado:
    """Resultado de asociación de un sidecar con un archivo principal.

    Attributes:
        archivo (ArchivoAnalizado): Sidecar analizado.
        estado (EstadoAsociacion): Estado de asociación.
        motivo (str): Motivo de la asociación o falta de ella.
    """

    archivo: ArchivoAnalizado
    estado: EstadoAsociacion
    motivo: str = ""


def _lista_sidecars_vacia() -> list[ArchivoAnalizado]:
    """Crea una lista vacía tipada para sidecars.

    Returns:
        list[ArchivoAnalizado]: Lista vacía inicializada.
    """
    return []


@dataclass
class GrupoArchivo:
    """Agrupa un archivo principal con sus sidecars asociados.

    Attributes:
        principal (ArchivoAnalizado): Archivo principal del grupo.
        sidecars (list[ArchivoAnalizado]): Lista de sidecars vinculados.
    """

    principal: ArchivoAnalizado
    sidecars: list[ArchivoAnalizado] = field(
        default_factory=_lista_sidecars_vacia
    )


@dataclass
class ResumenEscaneo:
    """Resumen consolidado de métricas del escaneo.

    Attributes:
        conteo_por_tipo (dict[TipoArchivo, int]): Conteo por tipo de archivo.
        total_grupos (int): Cantidad total de grupos principales.
        sidecars_asociados (int): Cantidad de sidecars asociados.
        sidecars_huerfanos (int): Cantidad de sidecars huérfanos.
        sidecars_ambiguos (int): Cantidad de sidecars ambiguos.
        total_desconocidos (int): Cantidad de archivos desconocidos.
        total_archivos (int): Total de archivos contabilizados.
    """

    conteo_por_tipo: dict[TipoArchivo, int]
    total_grupos: int
    sidecars_asociados: int
    sidecars_huerfanos: int
    sidecars_ambiguos: int
    total_desconocidos: int
    total_archivos: int


@dataclass
class ResultadoEscaneo:
    """Resultado final del escaneo del directorio.

    Attributes:
        grupos (list[GrupoArchivo]): Grupos principales con sidecars.
        sidecars_no_asociados (list[SidecarAsociado]): Sidecars huérfanos o
            ambiguos.
        desconocidos (list[ArchivoAnalizado]): Archivos no reconocidos.
    """

    grupos: list[GrupoArchivo]
    sidecars_no_asociados: list[SidecarAsociado]
    desconocidos: list[ArchivoAnalizado]

    def obtener_resumen(self) -> ResumenEscaneo:
        """Calcula y devuelve un resumen agregado del escaneo.

        Returns:
            ResumenEscaneo: Métricas consolidadas del resultado.
        """
        conteo: dict[TipoArchivo, int] = {tipo: 0 for tipo in TipoArchivo}

        huerfanos = 0
        ambiguos = 0
        asociados = 0

        for grupo in self.grupos:
            conteo[grupo.principal.archivo.tipo] += 1
            for sidecar in grupo.sidecars:
                conteo[sidecar.archivo.tipo] += 1
                asociados += 1

        for sidecar_na in self.sidecars_no_asociados:
            conteo[sidecar_na.archivo.archivo.tipo] += 1
            if sidecar_na.estado == EstadoAsociacion.HUERFANO:
                huerfanos += 1
            elif sidecar_na.estado == EstadoAsociacion.AMBIGUO:
                ambiguos += 1

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


def _lista_advertencias_vacia() -> list[str]:
    """Crea una lista vacía tipada para advertencias.

    Returns:
        list[str]: Lista vacía inicializada.
    """
    return []


class AccionPlan(Enum):
    """Acción prevista a realizar sobre un archivo en el plan de organización.

    Attributes:
        MOVER: Operación de traslado del archivo a su nueva ubicación.
        OMITIR: El archivo no será procesado ni trasladado.
    """

    MOVER = auto()
    OMITIR = auto()


@dataclass
class OperacionPlan:
    """Representa la operación para un archivo principal y sus sidecars.

    Attributes:
        origen (Path): Ruta de origen del archivo principal.
        destino (Path): Ruta de destino propuesta para el archivo principal.
        categoria (TipoArchivo): Categoría del archivo.
        fecha_resultado (FechaResultado): Resultado del análisis de fecha.
        sidecars_asociados (list[tuple[Path, Path]]): Tuplas (origen, destino)
            de sidecars vinculados.
        accion (AccionPlan): Acción a ejecutar.
        advertencias (list[str]): Advertencias u observaciones acumuladas.
    """

    origen: Path
    destino: Path
    categoria: TipoArchivo
    fecha_resultado: FechaResultado
    sidecars_asociados: list[tuple[Path, Path]]
    accion: AccionPlan
    advertencias: list[str] = field(default_factory=_lista_advertencias_vacia)


@dataclass
class PlanOrganizacion:
    """Plan de organización completo generado para el lote de archivos.

    Attributes:
        directorio_origen (Path): Directorio de origen analizado.
        directorio_destino (Path): Directorio base de destino.
        operaciones (list[OperacionPlan]): Operaciones para los grupos
            principales.
        sidecars_omitidos (list[SidecarAsociado]): Sidecars huérfanos o
            ambiguos.
        desconocidos (list[ArchivoAnalizado]): Archivos no reconocidos
            omitidos.
    """

    directorio_origen: Path
    directorio_destino: Path
    operaciones: list[OperacionPlan]
    sidecars_omitidos: list[SidecarAsociado]
    desconocidos: list[ArchivoAnalizado]


def _lista_fallos_vacia() -> list["FalloOperacion"]:
    """Crea una lista vacía tipada para fallos de operaciones.

    Returns:
        list[FalloOperacion]: Lista vacía inicializada.
    """
    return []


@dataclass
class FalloOperacion:
    """Detalle de un fallo producido durante la ejecución de una operación.

    Attributes:
        operacion (OperacionPlan): Operación que presentó la falla.
        error (str): Mensaje descriptivo de la excepción o fallo.
    """

    operacion: OperacionPlan
    error: str


@dataclass
class ResultadoEjecucion:
    """Resumen cuantitativo y cualitativo de la ejecución del plan.

    Attributes:
        procesados_exitosamente (int): Cantidad de operaciones completadas.
        fallidos (int): Cantidad de operaciones que presentaron error.
        errores (list[FalloOperacion]): Lista detallada de fallos sucedidos.
    """

    procesados_exitosamente: int
    fallidos: int
    errores: list[FalloOperacion] = field(default_factory=_lista_fallos_vacia)
