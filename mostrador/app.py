"""
Arranque de Mostrador.

Corre con pythonw.exe (sin consola): levanta el servidor local y abre la
pagina en el navegador. Si ya hay una copia corriendo, solo abre su pagina.
La primera vez crea los accesos directos (escritorio y menu Inicio). Busca
actualizaciones cada 15 minutos y, si instala una, se reinicia solo: la
pagina abierta se recarga sola cuando vuelve.

Los errores graves se muestran en una ventana de aviso de Windows y todo
queda registrado en %APPDATA%\\Mostrador\\mostrador.log.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import threading
import urllib.request
import webbrowser
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import NOMBRE, PUERTO, REPO, VERSION, config, sistema, tareas
from .actualizador import Actualizador, reiniciar, version_a_tupla
from .servidor import crear_servidor

log = logging.getLogger("mostrador")
CADA_MINUTOS = 15


def _configurar_salida() -> None:
    # Con pythonw.exe no hay consola: stdout y stderr no existen y se descartan
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115


def _configurar_log() -> None:
    log.setLevel(logging.INFO)
    formato = logging.Formatter("[%(asctime)s] %(message)s", "%d/%m %H:%M:%S")
    try:
        archivo = RotatingFileHandler(config.carpeta_datos() / "mostrador.log", maxBytes=1_000_000,
                                      backupCount=2, encoding="utf-8")
        archivo.setFormatter(formato)
        log.addHandler(archivo)
    except OSError:
        pass
    if getattr(sys.stdout, "isatty", lambda: False)():
        consola = logging.StreamHandler(sys.stdout)
        consola.setFormatter(formato)
        log.addHandler(consola)
    logging.getLogger("werkzeug").setLevel(logging.ERROR)


def _instancia_activa(puerto: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{puerto}/ping", timeout=2) as r:
            return json.loads(r.read()).get("app") == NOMBRE
    except Exception:       # noqa: BLE001
        return False


def _abrir_pagina(puerto: int) -> None:
    webbrowser.open(f"http://127.0.0.1:{puerto}/")


def main(argv: list[str] | None = None, nota_arranque: str = "") -> int:
    _configurar_salida()
    ap = argparse.ArgumentParser(prog=NOMBRE, description=f"{NOMBRE} {VERSION}")
    ap.add_argument("--no-abrir", action="store_true", help="no abrir la página en el navegador")
    ap.add_argument("--puerto", type=int, default=0, help=f"puerto (por defecto {PUERTO})")
    ap.add_argument("--esperar", type=int, default=0, help=argparse.SUPPRESS)   # lo usa el reinicio
    ap.add_argument("--escribir-version", metavar="ARCHIVO", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    if args.escribir_version:  # lo usa el workflow para comprobar que arranca
        Path(args.escribir_version).write_text(VERSION, encoding="utf-8")
        return 0

    _configurar_log()
    log.info(f"=== {NOMBRE} {VERSION} ===")
    if nota_arranque:
        log.info(nota_arranque)

    puerto = args.puerto or int(os.environ.get("MOSTRADOR_PUERTO") or config.preferencia("puerto", PUERTO))
    inst = sistema.instalacion()
    if inst:
        os.chdir(inst.raiz)   # que la carpeta app no quede "en uso" y se pueda reemplazar al actualizar

    if _instancia_activa(puerto):
        log.info("Ya hay una copia corriendo: se abre su página.")
        if not args.no_abrir:
            _abrir_pagina(puerto)
        return 0

    reinicio: dict = {}
    servidor = None

    def detener():
        if servidor:
            threading.Thread(target=servidor.shutdown, daemon=True).start()

    def al_instalar():
        reinicio["pedido"] = True
        detener()

    actualizador = Actualizador(VERSION, REPO, CADA_MINUTOS, config.preferencia("actualizar_solo", True),
                                al_instalar, raiz=inst.raiz if inst else None, ocupado=tareas.hay_en_curso)
    try:
        servidor = crear_servidor(puerto, actualizador=actualizador, al_cerrar=detener)
    except OSError as e:
        log.error(f"No se pudo abrir el puerto {puerto}: {e}")
        sistema.aviso(NOMBRE, f"No se pudo abrir {NOMBRE}: el puerto {puerto} lo está usando otro programa.\n\n"
                              f"Cerrá ese programa o reiniciá la computadora y probá de nuevo.")
        return 1

    if inst and not config.preferencia("accesos_creados") and not sistema.hay_acceso_en_escritorio():
        try:
            lugares = sistema.crear_accesos_directos()
            config.guardar_preferencia("accesos_creados", True)
            log.info(f"Accesos directos creados en: {', '.join(lugares)}")
        except Exception as e:      # noqa: BLE001
            log.warning(f"No se pudieron crear los accesos directos: {e}")

    if version_a_tupla(VERSION) is None:
        actualizador.estado.estado = "desactivado"
        actualizador.estado.mensaje = "Versión de desarrollo: no se actualiza sola."
    else:
        actualizador.iniciar()

    if not args.no_abrir:
        threading.Timer(0.8, lambda: _abrir_pagina(puerto)).start()

    log.info(f"Escuchando en http://127.0.0.1:{puerto}/")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()

    if reinicio.get("pedido"):
        log.info("Abriendo la versión nueva…")
        try:
            reiniciar(sistema.comando_actual() + ["--no-abrir", "--esperar", str(os.getpid())],
                      inst.raiz if inst else Path.cwd())
        except OSError as e:
            log.error(f"No se pudo abrir la versión nueva: {e}")
            sistema.aviso(NOMBRE, "Se instaló una versión nueva pero no se pudo abrir sola.\n"
                                  f"Abrí {NOMBRE} desde el acceso directo del escritorio.")
    log.info("Programa cerrado.")
    return 0
