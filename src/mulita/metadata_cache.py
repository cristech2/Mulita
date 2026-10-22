"""Caché SQLite para metadatos extraídos de archivos multimedia."""

import json
import os
import sqlite3
import sys
from pathlib import Path

from mulita.reporting import obtener_logger

TAMANO_LOTE_CONSULTA = 900


def obtener_ruta_cache() -> Path:
    """Devuelve la ruta persistente del caché en el perfil del usuario."""
    if os.name == "nt":
        raiz = Path(
            os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
        )
    elif sys.platform == "darwin":
        raiz = Path.home() / "Library" / "Caches"
    else:
        raiz = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))

    return raiz / "Mulita" / ".cache" / "metadatos.sqlite3"


def _clave_ruta(ruta: Path) -> str:
    """Normaliza una ruta para mantener una sola entrada por archivo."""
    return os.path.normcase(str(ruta.resolve()))


def _firma_archivo(ruta: Path) -> tuple[int, int]:
    """Obtiene el tamaño y la fecha de modificación de alta precisión."""
    datos = ruta.stat()
    return datos.st_size, datos.st_mtime_ns


class CacheMetadatos:
    """Lee y actualiza metadatos persistentes validados por firma del archivo."""

    def __init__(self, ruta_db: Path | None = None) -> None:
        """Abre o crea la base de datos SQLite del caché."""
        self.ruta_db = ruta_db or obtener_ruta_cache()
        self.ruta_db.parent.mkdir(parents=True, exist_ok=True)
        self._conexion = sqlite3.connect(self.ruta_db, timeout=30)
        self._conexion.execute("PRAGMA journal_mode=WAL")
        self._conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS metadatos (
                ruta TEXT PRIMARY KEY,
                tamano INTEGER NOT NULL,
                mtime_ns INTEGER NOT NULL,
                datos_json TEXT NOT NULL
            )
            """
        )
        self._firmas: dict[str, tuple[int, int]] = {}
        self._rutas: dict[str, Path] = {}

    def obtener(self, rutas: list[Path]) -> dict[Path, dict[str, str]]:
        """Devuelve las entradas cuya firma aún coincide con el archivo."""
        logger = obtener_logger()
        self._firmas = {}
        self._rutas = {}
        for ruta in rutas:
            clave = _clave_ruta(ruta)
            self._firmas[clave] = _firma_archivo(ruta)
            self._rutas[clave] = ruta

        resultados: dict[Path, dict[str, str]] = {}
        claves = list(self._firmas)
        for inicio in range(0, len(claves), TAMANO_LOTE_CONSULTA):
            lote = claves[inicio : inicio + TAMANO_LOTE_CONSULTA]
            marcadores = ",".join("?" for _ in lote)
            filas = self._conexion.execute(
                "SELECT ruta, tamano, mtime_ns, datos_json "
                f"FROM metadatos WHERE ruta IN ({marcadores})",
                lote,
            )
            for clave, tamano, mtime_ns, datos_json in filas:
                if self._firmas[clave] != (tamano, mtime_ns):
                    continue

                datos = json.loads(datos_json)
                if not isinstance(datos, dict) or any(
                    not isinstance(k, str) or not isinstance(v, str)
                    for k, v in datos.items()
                ):
                    raise ValueError(
                        f"Entrada inválida en el caché para: {clave}"
                    )
                resultados[self._rutas[clave]] = datos

        logger.debug(
            "Metadatos reutilizados desde caché: %s de %s.",
            len(resultados),
            len(rutas),
        )
        return resultados

    def guardar(self, metadatos: dict[Path, dict[str, str]]) -> None:
        """Guarda metadatos solo si el archivo no cambió durante el análisis."""
        filas: list[tuple[str, int, int, str]] = []
        for ruta, datos in metadatos.items():
            if not datos:
                continue

            clave = _clave_ruta(ruta)
            firma = self._firmas.get(clave)
            if firma is None or _firma_archivo(ruta) != firma:
                continue

            filas.append((clave, firma[0], firma[1], json.dumps(datos)))

        if filas:
            self._conexion.executemany(
                """
                INSERT INTO metadatos (ruta, tamano, mtime_ns, datos_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(ruta) DO UPDATE SET
                    tamano = excluded.tamano,
                    mtime_ns = excluded.mtime_ns,
                    datos_json = excluded.datos_json
                """,
                filas,
            )
            self._conexion.commit()

    def cerrar(self) -> None:
        """Cierra la conexión SQLite."""
        self._conexion.close()
