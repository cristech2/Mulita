"""
Módulo para la asociación de archivos auxiliares (sidecars)
con sus correspondientes archivos principales de medios.
"""

from pathlib import Path

from mulita.models import (
    ArchivoAnalizado,
    EstadoAsociacion,
    GrupoArchivo,
    SidecarAsociado,
    TipoArchivo,
)
from mulita.reporting import obtener_logger


def _buscar_candidatos_principales(
    sidecar: ArchivoAnalizado,
    principales: list[ArchivoAnalizado],
) -> list[ArchivoAnalizado]:
    """
    Encuentra archivos principales en la misma carpeta que coinciden
    con el nombre base o nombre completo del sidecar.

    Parameters:
    sidecar (ArchivoAnalizado): El archivo auxiliar a vincular.
    principales (list[ArchivoAnalizado]): Candidatos principales.

    Returns:
    list[ArchivoAnalizado]: Lista de archivos principales coincidentes.
    """
    candidatos: list[ArchivoAnalizado] = []
    stem_sidecar = sidecar.archivo.ruta.stem.lower()

    for principal in principales:
        nombre_principal = principal.archivo.ruta.name.lower()
        stem_principal = principal.archivo.ruta.stem.lower()

        # Coincidencia directa por stem (ej: foto1.xmp <-> foto1.jpg)
        # o por nombre completo (ej: foto1.jpg.xmp <-> foto1.jpg)
        if stem_sidecar in (stem_principal, nombre_principal):
            candidatos.append(principal)

    return candidatos


def asociar_sidecars(
    analizados: list[ArchivoAnalizado],
) -> tuple[list[GrupoArchivo], list[SidecarAsociado]]:
    """
    Asocia archivos sidecar con sus correspondientes archivos principales
    dentro de una misma carpeta de origen.

    Parameters:
    analizados (list[ArchivoAnalizado]): Lista de archivos analizados.

    Returns:
    tuple[list[GrupoArchivo], list[SidecarAsociado]]:
        - Lista de grupos con archivo principal y sus sidecars.
        - Lista de sidecars no asociados (huérfanos o ambiguos).
    """
    logger = obtener_logger()

    # Agrupar archivos por directorio contenedor (parent)
    carpetas: dict[Path, list[ArchivoAnalizado]] = {}
    for item in analizados:
        parent = item.archivo.ruta.parent
        carpetas.setdefault(parent, []).append(item)

    grupos: list[GrupoArchivo] = []
    sidecars_no_asociados: list[SidecarAsociado] = []

    for carpeta, items in carpetas.items():
        principales_map: dict[Path, GrupoArchivo] = {}
        principales_list: list[ArchivoAnalizado] = []
        auxiliares_list: list[ArchivoAnalizado] = []

        for item in items:
            if item.archivo.tipo in (
                TipoArchivo.IMAGEN,
                TipoArchivo.RAW,
                TipoArchivo.VIDEO,
            ):
                grupo = GrupoArchivo(principal=item)
                principales_map[item.archivo.ruta] = grupo
                principales_list.append(item)
            elif item.archivo.tipo == TipoArchivo.AUXILIAR:
                auxiliares_list.append(item)

        # Evaluar cada archivo auxiliar en la carpeta actual
        for sidecar in auxiliares_list:
            candidatos = _buscar_candidatos_principales(sidecar, principales_list)

            if not candidatos:
                motivo = f"Sin archivo principal en {carpeta}"
                logger.warning(
                    f"Sidecar huérfano detectado: "
                    f"{sidecar.archivo.ruta.name} ({motivo})"
                )
                sidecars_no_asociados.append(
                    SidecarAsociado(
                        archivo=sidecar,
                        estado=EstadoAsociacion.HUERFANO,
                        motivo=motivo,
                    )
                )
            elif len(candidatos) == 1:
                candidato = candidatos[0]
                principales_map[candidato.archivo.ruta].sidecars.append(sidecar)
                logger.debug(
                    f"Sidecar asociado: {sidecar.archivo.ruta.name} "
                    f"-> {candidato.archivo.ruta.name}"
                )
            else:
                nombres_cand = ", ".join(c.archivo.ruta.name for c in candidatos)
                motivo = f"Múltiples candidatos encontrados: {nombres_cand}"
                logger.warning(
                    f"Sidecar ambiguo detectado: {sidecar.archivo.ruta.name} ({motivo})"
                )
                sidecars_no_asociados.append(
                    SidecarAsociado(
                        archivo=sidecar,
                        estado=EstadoAsociacion.AMBIGUO,
                        motivo=motivo,
                    )
                )

        grupos.extend(principales_map.values())

    return grupos, sidecars_no_asociados
