"""
Actualizacion automatica desde los Releases de GitHub.

El programa instalado tiene esta forma:
    <raiz>\\python\\   Python oficial embebido (no cambia)
    <raiz>\\lib\\      librerias (Flask, pdfplumber, Pillow...): cambia solo si cambian
    <raiz>\\app\\      codigo del programa (es lo que se actualiza siempre)

Cada cierto tiempo consulta la ultima version publicada. Si es mas nueva que
la que esta corriendo:

1. Descarga "Mostrador-app.zip" (solo el codigo) a <raiz>\\app.new.zip.
2. Verifica su SHA-256 contra el .sha256 publicado junto al release.
   Si no coincide, lo borra y no instala nada.
3. Lo descomprime en <raiz>\\app.new y comprueba que este completo.
4. Si la version nueva pide otras librerias (su lib.txt no es el de la
   carpeta lib), baja tambien "Mostrador-lib.zip", lo verifica igual y lo
   deja descomprimido en <raiz>\\lib.new. Las librerias tienen partes
   compiladas que Windows deja "en uso" mientras el programa corre: las
   cambia el arranque (arranque.py) del proceso nuevo, antes de cargarlas.
5. Renombra app -> app.old y app.new -> app. Si algo falla en este paso,
   vuelve todo como estaba.
6. Avisa al programa para que se reinicie con el codigo nuevo.

No instala mientras haya un trabajo en curso (aplicando precios, un
respaldo...): avisa que hay version nueva y vuelve a probar al minuto.

Solo instala cuando corre instalado (con las carpetas app y python). Corriendo
desde el codigo fuente informa si hay version nueva, pero no instala nada.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

log = logging.getLogger("mostrador")

PAQUETE_APP = "Mostrador-app.zip"
PAQUETE_LIB = "Mostrador-lib.zip"
ARCHIVO_ENTRADA = "Mostrador.pyw"
MARCA_LIB = "lib.txt"            # huella de requirements.txt: dice que librerias trae cada uno
TIMEOUT = 60
MAX_TAMANO = 200 * 1024 * 1024   # el de librerias pesa unas decenas de MB
REINTENTO_OCUPADO = 60           # segundos: si hay un trabajo en curso, se vuelve a probar


def version_a_tupla(texto: str) -> tuple[int, ...] | None:
    """'v1.12' o '1.12' -> (1, 12). Devuelve None si no es una version numerica."""
    m = re.fullmatch(r"v?(\d+(?:\.\d+)*)", (texto or "").strip())
    return tuple(int(p) for p in m.group(1).split(".")) if m else None


def es_mas_nueva(disponible: str, actual: str) -> bool:
    d, a = version_a_tupla(disponible), version_a_tupla(actual)
    return bool(d and a and d > a)


def sha256_de(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer_marca(carpeta: Path) -> str:
    try:
        return (carpeta / MARCA_LIB).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _get(url: str, aceptar: str = "application/json") -> bytes:
    pedido = urllib.request.Request(url, headers={"Accept": aceptar, "User-Agent": "Mostrador-actualizador"})
    with urllib.request.urlopen(pedido, timeout=TIMEOUT) as r:
        return r.read()


def _descargar(url: str, destino: Path) -> None:
    pedido = urllib.request.Request(url, headers={"User-Agent": "Mostrador-actualizador"})
    total = 0
    with urllib.request.urlopen(pedido, timeout=TIMEOUT) as r, open(destino, "wb") as f:
        while True:
            bloque = r.read(1 << 20)
            if not bloque:
                break
            total += len(bloque)
            if total > MAX_TAMANO:
                raise ValueError("la descarga es más grande de lo esperado")
            f.write(bloque)


def _borrar(ruta: Path) -> None:
    if ruta.is_dir():
        shutil.rmtree(ruta)
    elif ruta.exists():
        ruta.unlink()


def extraer_seguro(zip_path: Path, destino: Path) -> None:
    """Descomprime sin permitir rutas que salgan de la carpeta destino."""
    destino.mkdir(parents=True)
    raiz = destino.resolve()
    with zipfile.ZipFile(zip_path) as z:
        for nombre in z.namelist():
            final = (raiz / nombre).resolve()
            if final != raiz and raiz not in final.parents:
                raise ValueError(f"el paquete tiene una ruta inválida: {nombre}")
        z.extractall(raiz)


@dataclass
class EstadoActualizacion:
    version_actual: str
    estado: str = "sin_revisar"   # sin_revisar | buscando | al_dia | disponible | instalando | reiniciando | error | desactivado
    version_disponible: str | None = None
    mensaje: str = ""
    ultima_revision: str | None = None
    automatica: bool = True

    def como_dict(self) -> dict:
        return dict(self.__dict__)


@dataclass
class Release:
    version: str
    url_app: str
    url_app_sha: str
    url_lib: str | None
    url_lib_sha: str | None


class Actualizador:
    def __init__(self, version_actual: str, repo: str, cada_minutos: int, automatica: bool,
                 al_instalar: Callable[[], None], raiz: Path | None = None,
                 ocupado: Callable[[], bool] | None = None,
                 obtener_json: Callable[[str], dict] | None = None,
                 descargar: Callable[[str, Path], None] | None = None,
                 obtener_texto: Callable[[str], str] | None = None):
        self.repo = repo.strip().strip("/")
        self.cada_segundos = max(5, cada_minutos) * 60
        self.al_instalar = al_instalar
        self.raiz = raiz                 # None = corriendo desde el codigo fuente: no instala
        self.ocupado = ocupado or (lambda: False)
        self.estado = EstadoActualizacion(version_actual=version_actual, automatica=automatica)
        self._obtener_json = obtener_json or (lambda url: json.loads(_get(url)))
        self._obtener_texto = obtener_texto or (lambda url: _get(url, "application/octet-stream").decode("utf-8", "replace"))
        self._descargar = descargar or _descargar
        self._lock = threading.Lock()
        self._parar = threading.Event()
        self._pospuesta = False

    # ------------------------------------------------------------- rutas
    def _ruta(self, nombre: str) -> Path:
        return self.raiz / nombre

    @property
    def app(self) -> Path:
        return self._ruta("app")

    def limpiar_restos(self) -> None:
        """Borra lo que haya quedado de una actualizacion anterior.
        (lib.new no: si quedo, la cambia el proximo arranque.)"""
        if not self.raiz:
            return
        for nombre in ("app.old", "app.new", "app.new.zip", "lib.old", "lib.new.zip"):
            for _ in range(5):
                try:
                    _borrar(self._ruta(nombre))
                    break
                except OSError:
                    time.sleep(2)

    # ------------------------------------------------------------- consulta
    def ultima_release(self) -> Release:
        # La variable de entorno solo se usa en la prueba automatica del workflow
        url = os.environ.get("MOSTRADOR_URL_RELEASES") or \
            f"https://api.github.com/repos/{self.repo}/releases/latest"
        datos = self._obtener_json(url)
        version = (datos.get("tag_name") or "").lstrip("v")
        activos = {a.get("name"): a.get("browser_download_url") for a in datos.get("assets") or []}
        url_app, url_sha = activos.get(PAQUETE_APP), activos.get(PAQUETE_APP + ".sha256")
        if not version or not url_app or not url_sha:
            raise ValueError("La última versión publicada todavía no trae el paquete y su .sha256.")
        return Release(version, url_app, url_sha,
                       activos.get(PAQUETE_LIB), activos.get(PAQUETE_LIB + ".sha256"))

    def revisar(self, instalar: bool | None = None) -> None:
        """Consulta GitHub y, si corresponde, instala. No lanza excepciones."""
        if not self._lock.acquire(blocking=False):
            return  # ya hay una revision o instalacion en curso
        try:
            e = self.estado
            self._pospuesta = False
            e.ultima_revision = datetime.now().isoformat(timespec="seconds")
            e.estado, e.mensaje = "buscando", "Buscando actualizaciones…"
            try:
                release = self.ultima_release()
            except Exception as ex:
                e.estado, e.mensaje = "error", f"No se pudo consultar si hay versiones nuevas: {ex}"
                log.warning(e.mensaje)
                return
            if not es_mas_nueva(release.version, e.version_actual):
                e.estado, e.version_disponible, e.mensaje = "al_dia", release.version, ""
                return
            e.estado, e.version_disponible = "disponible", release.version
            e.mensaje = f"Hay una versión nueva: {release.version}"
            log.info(e.mensaje)
            if instalar is None:
                instalar = e.automatica
            if not self.raiz:
                e.mensaje += " (corriendo desde el código fuente: no se instala sola)"
            elif instalar and self.ocupado():
                self._pospuesta = True
                e.mensaje = (f"Hay una versión nueva ({release.version}). Se instala sola "
                             f"cuando termine lo que se está haciendo.")
            elif instalar:
                self._instalar(release)
        finally:
            self._lock.release()

    # ------------------------------------------------------------- instalacion
    def _bajar_y_extraer(self, url: str, url_sha: str, zip_destino: Path, carpeta: Path) -> None:
        """Descarga, verifica el SHA-256 y descomprime aparte. Levanta si algo no da."""
        for r in (zip_destino, carpeta):
            _borrar(r)
        esperado = self._obtener_texto(url_sha).split()[0].lower()
        if not re.fullmatch(r"[0-9a-f]{64}", esperado):
            raise ValueError("el archivo .sha256 publicado no es válido")
        self._descargar(url, zip_destino)
        if sha256_de(zip_destino) != esperado:
            raise ValueError("el archivo descargado no coincide con el publicado (SHA-256 distinto)")
        extraer_seguro(zip_destino, carpeta)
        _borrar(zip_destino)

    def _instalar(self, release: Release) -> None:
        e = self.estado
        e.estado, e.mensaje = "instalando", f"Descargando la versión {release.version}…"
        log.info(e.mensaje)
        zip_app, nueva, vieja, actual = (self._ruta("app.new.zip"), self._ruta("app.new"),
                                         self._ruta("app.old"), self.app)
        zip_lib, lib_nueva = self._ruta("lib.new.zip"), self._ruta("lib.new")

        def fallar(texto: str) -> None:
            for r in (zip_app, nueva, zip_lib, lib_nueva):
                try:
                    _borrar(r)
                except OSError:
                    pass
            e.estado, e.mensaje = "error", f"No se instaló la versión {release.version}: {texto}"
            log.error(e.mensaje)

        # 1-4: descargar, verificar y descomprimir aparte (codigo y, si hace falta, librerias)
        try:
            self._bajar_y_extraer(release.url_app, release.url_app_sha, zip_app, nueva)
            if not (nueva / ARCHIVO_ENTRADA).is_file() or not (nueva / "mostrador").is_dir() \
                    or not (nueva / "web" / "index.html").is_file():
                raise ValueError("el paquete descargado está incompleto")
            marca = leer_marca(nueva)
            if marca and marca != leer_marca(self._ruta("lib")):
                if not release.url_lib or not release.url_lib_sha:
                    raise ValueError("la versión nueva necesita otras librerías y no vienen publicadas")
                e.mensaje = f"Descargando las librerías de la versión {release.version}…"
                log.info(e.mensaje)
                self._bajar_y_extraer(release.url_lib, release.url_lib_sha, zip_lib, lib_nueva)
                if leer_marca(lib_nueva) != marca:
                    raise ValueError("las librerías descargadas no son las que pide la versión nueva")
        except Exception as ex:
            fallar(str(ex))
            return

        # 5: cambiar carpetas, con vuelta atras si algo falla
        try:
            _borrar(vieja)
            os.replace(actual, vieja)
        except OSError as ex:
            fallar(f"no se pudo apartar la versión en uso ({ex})")
            return
        try:
            os.replace(nueva, actual)
        except OSError as ex:
            try:
                os.replace(vieja, actual)
            except OSError:
                pass
            fallar(f"no se pudo poner la versión nueva en su lugar ({ex})")
            return

        e.estado, e.mensaje = "reiniciando", f"Versión {release.version} instalada. Reiniciando…"
        log.info(e.mensaje)
        self.al_instalar()

    # ------------------------------------------------------------- ciclo
    def buscar_ahora(self) -> None:
        """Lo pide el boton "Buscar actualizaciones": revisa ya e instala si hay."""
        threading.Thread(target=self.revisar, kwargs={"instalar": True},
                         name="actualizador-manual", daemon=True).start()

    def iniciar(self) -> None:
        def ciclo():
            self.limpiar_restos()
            while not self._parar.is_set():
                self.revisar()
                if self.estado.estado == "reiniciando":
                    return
                self._parar.wait(REINTENTO_OCUPADO if self._pospuesta else self.cada_segundos)
        threading.Thread(target=ciclo, name="actualizador", daemon=True).start()

    def detener(self) -> None:
        self._parar.set()


def reiniciar(comando: list[str], carpeta: Path) -> None:
    """Abre el programa de nuevo como un proceso independiente y sin ventana."""
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen(comando, cwd=str(carpeta), creationflags=flags, close_fds=True)
