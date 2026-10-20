"""
Pruebas unitarias para el módulo reporting.py
"""

import time
from pathlib import Path

from mulita.reporting import generar_ruta_log, rotar_logs_antiguos


def test_generar_ruta_log_crea_timestamp(tmp_path: Path):
    """Verifica que se agregue un timestamp al nombre del archivo de log."""
    ruta_base = tmp_path / "reportes" / "escaneo.log"
    ruta_final = generar_ruta_log(ruta_base)

    assert ruta_final.parent == tmp_path / "reportes"
    assert "escaneo_" in ruta_final.name
    assert ruta_final.suffix == ".log"


def test_rotar_logs_antiguos_mantiene_maximo(tmp_path: Path):
    """Verifica que solo se conserven los 'max_archivos' más recientes."""
    directorio_logs = tmp_path / "logs"
    directorio_logs.mkdir()

    # Crear 7 archivos simulando distintas fechas
    for i in range(7):
        archivo = directorio_logs / f"test_{i}.log"
        archivo.touch()
        time.sleep(0.01)  # Pequeña pausa para diferenciar st_mtime

    rotar_logs_antiguos(directorio_logs, max_archivos=5)

    archivos_restantes = list(directorio_logs.glob("*.log"))
    assert len(archivos_restantes) == 5
    # Asegura que se borraron los dos primeros (más antiguos)
    nombres = [f.name for f in archivos_restantes]
    assert "test_0.log" not in nombres
    assert "test_1.log" not in nombres
