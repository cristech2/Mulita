"""Extracción y validación de metadatos con ExifTool."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from mulita.reporting import obtener_logger


def verificar_exiftool() -> bool:
    """Comprueba si ExifTool está disponible en el PATH del sistema.

    Returns:
        bool: ``True`` si ExifTool está instalado y accesible.
    """
    return shutil.which("exiftool") is not None


def extraer_metadatos(rutas: list[Path]) -> dict[Path, dict[str, str]]:
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
        return {ruta: {} for ruta in rutas}

    tmp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            suffix=".txt",
        ) as tmp_file:
            for r in rutas:
                tmp_file.write(f"{r.resolve()}\n")
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

    except (json.JSONDecodeError, OSError) as err:
        logger.error(f"Error al procesar salida de ExifTool: {err}")
        return {ruta: {} for ruta in rutas}

    finally:
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass

    datos_por_fuente: dict[Path, dict[str, str]] = {
        Path(item.get("SourceFile", "")).resolve(): item for item in datos
    }

    metadatos_mapeados: dict[Path, dict[str, str]] = {}
    for ruta in rutas:
        ruta_resuelta = ruta.resolve()
        info = datos_por_fuente.get(ruta_resuelta, {})
        info_filtrada = {
            k: str(v) for k, v in info.items() if k != "SourceFile"
        }
        metadatos_mapeados[ruta] = info_filtrada

    return metadatos_mapeados
