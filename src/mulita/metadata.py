"""Extracción y validación de metadatos con ExifTool."""

import json
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

from mulita.reporting import obtener_logger

TAMANO_LOTE_METADATOS = 100


def verificar_exiftool() -> bool:
    """Comprueba si ExifTool está disponible en el PATH del sistema.

    Returns:
        bool: ``True`` si ExifTool está instalado y accesible.
    """
    return shutil.which("exiftool") is not None


def extraer_metadatos(
    rutas: list[Path],
    progreso: Callable[[str, int, int | None], None] | None = None,
) -> dict[Path, dict[str, str]]:
    """Extrae metadatos de fecha para las rutas indicadas usando ExifTool.

    Args:
        rutas (list[Path]): Lista de rutas a consultar.

    Returns:
        dict[Path, dict[str, str]]: Mapa de ruta a metadatos encontrados.
    """
    logger = obtener_logger()

    if not rutas:
        return {}

    if not verificar_exiftool():
        logger.warning(
            "ExifTool no está instalado o no se encuentra en el PATH. "
            "Se omitirá la extracción de metadatos EXIF."
        )
        if progreso is not None:
            progreso(
                "ExifTool no disponible; se usarán fechas de archivo.",
                len(rutas),
                len(rutas),
            )
        return {ruta: {} for ruta in rutas}

    metadatos_mapeados: dict[Path, dict[str, str]] = {}
    total = len(rutas)
    if progreso is not None:
        progreso("Extrayendo metadatos con ExifTool...", 0, total)

    for inicio in range(0, total, TAMANO_LOTE_METADATOS):
        lote = rutas[inicio : inicio + TAMANO_LOTE_METADATOS]
        tmp_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                delete=False,
                suffix=".txt",
            ) as tmp_file:
                for ruta in lote:
                    tmp_file.write(f"{ruta.resolve()}\n")
                tmp_path = Path(tmp_file.name)

            comando: list[str] = [
                "exiftool",
                "-j",
                "-DateTimeOriginal",
                "-CreateDate",
                "-MediaCreateDate",
                "-FileModifyDate",
                "-@",
                str(tmp_path),
            ]
            resultado = subprocess.run(
                comando,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            datos: list[dict[str, str]] = []
            if resultado.stdout.strip():
                datos = json.loads(resultado.stdout)

            datos_por_fuente = {
                Path(item.get("SourceFile", "")).resolve(): item
                for item in datos
            }
            for ruta in lote:
                info = datos_por_fuente.get(ruta.resolve(), {})
                metadatos_mapeados[ruta] = {
                    clave: str(valor)
                    for clave, valor in info.items()
                    if clave != "SourceFile"
                }
        except (json.JSONDecodeError, OSError) as err:
            logger.error(f"Error al procesar salida de ExifTool: {err}")
            metadatos_mapeados.update({ruta: {} for ruta in lote})
        finally:
            if tmp_path is not None and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

        if progreso is not None:
            progreso(
                "Extrayendo metadatos con ExifTool...",
                min(inicio + len(lote), total),
                total,
            )

    return metadatos_mapeados
