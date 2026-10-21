"""Planificación de organización y resolución de colisiones."""

from pathlib import Path

from mulita.models import (
    AccionPlan,
    GrupoArchivo,
    OperacionPlan,
    PlanOrganizacion,
    ResultadoEscaneo,
)


def validar_rutas(directorio_origen: Path, directorio_destino: Path) -> None:
    """Valida la coherencia y relación entre las rutas de origen y destino.

    Args:
        directorio_origen (Path): Ruta del directorio de origen.
        directorio_destino (Path): Ruta del directorio de destino.

    Raises:
        ValueError: Si el origen no existe, no es directorio, si las rutas son
            idénticas o si están anidadas generando recursión.
    """
    origen_abs = directorio_origen.resolve()

    if not origen_abs.exists():
        raise ValueError(
            f"El directorio de origen no existe: {directorio_origen}"
        )

    if not origen_abs.is_dir():
        raise ValueError(
            f"La ruta de origen no es un directorio: {directorio_origen}"
        )

    destino_abs = directorio_destino.resolve()

    if origen_abs == destino_abs:
        raise ValueError(
            "El directorio de origen y de destino no pueden ser el mismo."
        )

    if destino_abs.is_relative_to(origen_abs):
        raise ValueError(
            "El directorio de destino no puede estar contenido "
            "dentro del origen."
        )

    if origen_abs.is_relative_to(destino_abs):
        raise ValueError(
            "El directorio de origen no puede estar contenido "
            "dentro del destino."
        )


def _calcular_nuevo_nombre_sidecar(
    origen_principal: Path,
    destino_principal: Path,
    origen_sidecar: Path,
) -> str:
    """Calcula el nombre del sidecar a partir del principal renombrado.

    Args:
        origen_principal (Path): Ruta original del archivo principal.
        destino_principal (Path): Ruta asignada de destino para el principal.
        origen_sidecar (Path): Ruta original del sidecar.

    Returns:
        str: Nombre del archivo sidecar para el destino.
    """
    stem_orig_principal = origen_principal.stem
    stem_nuevo_principal = destino_principal.stem

    if origen_sidecar.stem == stem_orig_principal:
        return f"{stem_nuevo_principal}{origen_sidecar.suffix}"

    nombre_orig_principal = origen_principal.name
    nombre_orig_sidecar = origen_sidecar.name

    if nombre_orig_sidecar.startswith(nombre_orig_principal):
        sufijo_extra = nombre_orig_sidecar[len(nombre_orig_principal) :]
        return f"{destino_principal.name}{sufijo_extra}"

    if nombre_orig_sidecar.startswith(stem_orig_principal):
        sufijo_extra = nombre_orig_sidecar[len(stem_orig_principal) :]
        return f"{stem_nuevo_principal}{sufijo_extra}"

    return origen_sidecar.name


def _resolver_destino_unico(
    directorio_base: Path,
    nombre_archivo: str,
    destinos_reservados: set[Path],
) -> Path:
    """Calcula un destino único resolviendo colisiones con sufijos numéricos.

    Args:
        directorio_base (Path): Directorio de destino para la categoría.
        nombre_archivo (str): Nombre deseado del archivo.
        destinos_reservados (set[Path]): Conjunto de rutas ya reservadas.

    Returns:
        Path: Ruta de destino única no colisionante.
    """
    destino_propuesto = directorio_base / nombre_archivo

    if (
        destino_propuesto not in destinos_reservados
        and not destino_propuesto.exists()
    ):
        destinos_reservados.add(destino_propuesto)
        return destino_propuesto

    path_temp = Path(nombre_archivo)
    stem = path_temp.stem
    suffix = path_temp.suffix

    contador = 1
    while True:
        nuevo_nombre = f"{stem}_{contador}{suffix}"
        nuevo_destino = directorio_base / nuevo_nombre
        if (
            nuevo_destino not in destinos_reservados
            and not nuevo_destino.exists()
        ):
            destinos_reservados.add(nuevo_destino)
            return nuevo_destino
        contador += 1


def _planificar_grupo(
    grupo: GrupoArchivo,
    directorio_destino: Path,
    destinos_reservados: set[Path],
) -> OperacionPlan:
    """Planifica la operación para un archivo principal y sus sidecars.

    Args:
        grupo (GrupoArchivo): Grupo a procesar.
        directorio_destino (Path): Ruta base del directorio de destino.
        destinos_reservados (set[Path]): Rutas de destino ya reservadas.

    Returns:
        OperacionPlan: Operación de organización resultante.
    """
    principal = grupo.principal
    fecha = principal.fecha_resultado.fecha

    anio = f"{fecha.year:04d}"
    mes = f"{fecha.month:02d}"
    dia = f"{fecha.day:02d}"
    categoria = principal.archivo.tipo.name

    carpeta_destino = directorio_destino / anio / mes / dia / categoria
    origen_principal = principal.archivo.ruta
    nombre_principal = origen_principal.name

    destino_principal = _resolver_destino_unico(
        carpeta_destino, nombre_principal, destinos_reservados
    )

    advertencias: list[str] = []
    if principal.fecha_resultado.es_respaldo:
        advertencias.append(
            "Fecha de respaldo utilizada "
            f"({principal.fecha_resultado.fuente})."
        )

    if destino_principal.name != nombre_principal:
        advertencias.append(
            f"Renombrado por colisión: '{nombre_principal}' -> "
            f"'{destino_principal.name}'."
        )

    sidecars_asociados: list[tuple[Path, Path]] = []

    # Ordenamiento estable de sidecars por ruta de origen
    sidecars_ordenados = sorted(
        grupo.sidecars,
        key=lambda s: s.archivo.ruta.as_posix(),
    )

    for sidecar in sidecars_ordenados:
        origen_sidecar = sidecar.archivo.ruta
        nombre_sidecar_propuesto = _calcular_nuevo_nombre_sidecar(
            origen_principal, destino_principal, origen_sidecar
        )
        destino_sidecar = _resolver_destino_unico(
            carpeta_destino, nombre_sidecar_propuesto, destinos_reservados
        )
        sidecars_asociados.append((origen_sidecar, destino_sidecar))

    return OperacionPlan(
        origen=origen_principal,
        destino=destino_principal,
        categoria=principal.archivo.tipo,
        fecha_resultado=principal.fecha_resultado,
        sidecars_asociados=sidecars_asociados,
        accion=AccionPlan.MOVER,
        advertencias=advertencias,
    )


def generar_plan(
    resultado_escaneo: ResultadoEscaneo,
    directorio_origen: Path,
    directorio_destino: Path,
) -> PlanOrganizacion:
    """Genera un plan determinista a partir del resultado del escaneo.

    Args:
        resultado_escaneo (ResultadoEscaneo): Resultado del análisis previo
            de archivos.
        directorio_origen (Path): Directorio origen escaneado.
        directorio_destino (Path): Directorio base de destino.

    Returns:
        PlanOrganizacion: Operaciones y advertencias de organización.
    """
    validar_rutas(directorio_origen, directorio_destino)

    destinos_reservados: set[Path] = set()
    operaciones: list[OperacionPlan] = []

    # Ordenamiento estable de grupos por la ruta del archivo principal
    grupos_ordenados = sorted(
        resultado_escaneo.grupos,
        key=lambda g: g.principal.archivo.ruta.as_posix(),
    )

    for grupo in grupos_ordenados:
        operacion = _planificar_grupo(
            grupo, directorio_destino, destinos_reservados
        )
        operaciones.append(operacion)

    return PlanOrganizacion(
        directorio_origen=directorio_origen,
        directorio_destino=directorio_destino,
        operaciones=operaciones,
        sidecars_omitidos=list(resultado_escaneo.sidecars_no_asociados),
        desconocidos=list(resultado_escaneo.desconocidos),
    )
