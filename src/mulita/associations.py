"""Asociación de sidecars con sus archivos principales."""

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
    """Busca candidatos principales para un sidecar en la misma carpeta.

    Args:
        sidecar (ArchivoAnalizado): Archivo auxiliar a asociar.
        principales (list[ArchivoAnalizado]): Archivos principales disponibles.

    Returns:
        list[ArchivoAnalizado]: Lista de candidatos válidos.
    """
    candidatos: list[ArchivoAnalizado] = []
    stem_sidecar = sidecar.archivo.ruta.stem.lower()

    for principal in principales:
        nombre_principal = principal.archivo.ruta.name.lower()
        stem_principal = principal.archivo.ruta.stem.lower()

        if stem_sidecar in (stem_principal, nombre_principal):
            candidatos.append(principal)

    return candidatos


def asociar_sidecars(
    analizados: list[ArchivoAnalizado],
) -> tuple[list[GrupoArchivo], list[SidecarAsociado]]:
    """Asocia sidecars con archivos principales dentro de cada carpeta.

    Args:
        analizados (list[ArchivoAnalizado]): Archivos ya analizados.

    Returns:
        tuple[list[GrupoArchivo], list[SidecarAsociado]]: Grupos creados y
            sidecars no asociados (huérfanos o ambiguos).
    """
    logger = obtener_logger()

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

        for sidecar in auxiliares_list:
            candidatos = _buscar_candidatos_principales(
                sidecar, principales_list
            )

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
                principales_map[candidato.archivo.ruta].sidecars.append(
                    sidecar
                )
                logger.debug(
                    f"Sidecar asociado: {sidecar.archivo.ruta.name} "
                    f"-> {candidato.archivo.ruta.name}"
                )
            else:
                nombres_cand = ", ".join(
                    c.archivo.ruta.name for c in candidatos
                )
                motivo = f"Múltiples candidatos encontrados: {nombres_cand}"
                logger.warning(
                    "Sidecar ambiguo detectado: "
                    f"{sidecar.archivo.ruta.name} ({motivo})"
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
