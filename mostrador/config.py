"""
Donde guarda sus cosas la app y la conexion con la tienda.

Todo va a la carpeta del usuario, no al lado del programa, asi el .exe se
puede instalar en "Archivos de programa" y cada usuario de Windows tiene
su propia tienda:

    %APPDATA%\\Mostrador\\config.json     la conexion (id de tienda y token)
    %APPDATA%\\Mostrador\\respaldos\\      copias de la tienda
    %APPDATA%\\Mostrador\\temporales\\     archivos subidos para leer
    Documentos\\Mostrador\\                las planillas que exporta

Para desarrollo se puede pisar con variables de entorno:
    MOSTRADOR_DATOS=otra/carpeta
    TN_STORE_ID=... TN_TOKEN=...       (si estan, ganan sobre config.json)
"""

import json
import os
from pathlib import Path

from . import NOMBRE


def carpeta_datos():
    if os.environ.get("MOSTRADOR_DATOS"):
        base = Path(os.environ["MOSTRADOR_DATOS"])
    elif os.environ.get("APPDATA"):
        base = Path(os.environ["APPDATA"]) / NOMBRE
    else:
        base = Path.home() / f".{NOMBRE.lower()}"
    base.mkdir(parents=True, exist_ok=True)
    return base


def carpeta(nombre):
    d = carpeta_datos() / nombre
    d.mkdir(parents=True, exist_ok=True)
    return d


def carpeta_exportaciones():
    """Documentos\\Mostrador: donde el usuario va a buscar sus planillas."""
    docs = Path.home() / "Documents"
    if not docs.is_dir():
        docs = Path.home()
    d = docs / NOMBRE
    d.mkdir(parents=True, exist_ok=True)
    return d


def _archivo():
    return carpeta_datos() / "config.json"


def leer():
    try:
        return json.loads(_archivo().read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def guardar(datos):
    ruta = _archivo()
    tmp = ruta.with_suffix(".tmp")
    tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ruta)


def tienda():
    """La conexion guardada: {"id", "token", "nombre", "url"} o None."""
    if os.environ.get("TN_STORE_ID") and os.environ.get("TN_TOKEN"):
        return {"id": os.environ["TN_STORE_ID"], "token": os.environ["TN_TOKEN"],
                "nombre": os.environ.get("TN_NOMBRE", ""), "url": ""}
    t = leer().get("tienda")
    return t if t and t.get("id") and t.get("token") else None


def guardar_tienda(datos_tienda):
    c = leer()
    c["tienda"] = datos_tienda
    guardar(c)


def olvidar_tienda():
    c = leer()
    c.pop("tienda", None)
    guardar(c)


def preferencia(clave, defecto=None):
    return leer().get("preferencias", {}).get(clave, defecto)


def guardar_preferencia(clave, valor):
    c = leer()
    c.setdefault("preferencias", {})[clave] = valor
    guardar(c)
