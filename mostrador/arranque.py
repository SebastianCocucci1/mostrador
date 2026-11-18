"""
Lo primero que corre al abrir Mostrador, ANTES de cargar Flask y compañia.

Por eso usa solo la libreria estandar: si una actualizacion dejo librerias
nuevas en <raiz>\\lib.new, las pone en su lugar (lib.new -> lib) mientras
todavia nadie las cargo. Las librerias tienen partes compiladas (.pyd, .dll)
que Windows no deja mover mientras un programa las usa, asi que primero
espera a que termine el proceso viejo (--esperar <pid>).
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

APP = Path(__file__).resolve().parent.parent       # <raiz>\app (o la carpeta del codigo fuente)
RAIZ = APP.parent


def esperar_proceso(pid: int, segundos: float = 30) -> None:
    """Espera a que termine el proceso pid (el programa viejo, despues de actualizar)."""
    if os.name != "nt" or not pid:
        return
    import ctypes
    k32 = ctypes.windll.kernel32
    h = k32.OpenProcess(0x00100000, False, int(pid))   # SYNCHRONIZE
    if not h:
        return                                         # ya termino
    try:
        k32.WaitForSingleObject(h, int(segundos * 1000))
    finally:
        k32.CloseHandle(h)


def poner_librerias_nuevas(esperar_pid: int | None = None) -> str:
    """lib.new -> lib. Devuelve un texto para el registro ("" si no habia nada)."""
    nueva, actual, vieja = RAIZ / "lib.new", RAIZ / "lib", RAIZ / "lib.old"
    if APP.name != "app" or not nueva.is_dir():
        return ""
    esperar_proceso(esperar_pid or 0)
    ultimo = None
    for _ in range(15):
        try:
            if vieja.exists():
                shutil.rmtree(vieja, ignore_errors=True)
            if actual.exists():
                os.replace(actual, vieja)
            try:
                os.replace(nueva, actual)
            except OSError:
                if vieja.exists() and not actual.exists():
                    os.replace(vieja, actual)          # vuelta atras: quedan las de antes
                raise
            shutil.rmtree(vieja, ignore_errors=True)
            return "Librerías nuevas instaladas."
        except OSError as e:
            ultimo = e
            time.sleep(1)
    return f"No se pudieron poner las librerías nuevas (se reintenta en el próximo arranque): {ultimo}"
