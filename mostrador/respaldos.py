"""
Copias de seguridad de la tienda.

Hay dos clases:
    completo    toda la tienda, cuando el usuario lo pide.
    automatico  solo los productos que se van a tocar, antes de cualquier
                cambio masivo (precios, planilla, borrar). Es lo que permite
                volver atras si algo sale mal.

Cada respaldo es una carpeta en %APPDATA%\\Mostrador\\respaldos\\<fecha>_<motivo>\\
    productos.json    lo que devuelve la API, entero (alcanza para rearmar todo)
    categorias.json   solo en los completos
    info.json         motivo, fecha, cantidad
"""

import json
import shutil
from datetime import datetime

from . import config
from .productos import slug


def crear(productos, motivo, categorias=None, completo=False):
    fecha = datetime.now()
    nombre = f"{fecha:%Y%m%d_%H%M%S}_{slug(motivo, 40)}"
    d = config.carpeta("respaldos") / nombre
    d.mkdir(parents=True, exist_ok=True)
    (d / "productos.json").write_text(json.dumps(productos, ensure_ascii=False), encoding="utf-8")
    if categorias is not None:
        (d / "categorias.json").write_text(json.dumps(categorias, ensure_ascii=False), encoding="utf-8")
    info = {"motivo": motivo, "fecha": fecha.isoformat(timespec="seconds"),
            "productos": len(productos), "completo": completo,
            "variantes": sum(len(p.get("variants") or []) for p in productos)}
    (d / "info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"carpeta": str(d), "nombre": nombre, **info}


def listar():
    base = config.carpeta("respaldos")
    salida = []
    for d in sorted(base.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        try:
            info = json.loads((d / "info.json").read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            info = {"motivo": d.name, "fecha": "", "productos": 0}
        tam = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
        salida.append({"nombre": d.name, "carpeta": str(d), "mb": round(tam / 1e6, 2), **info})
    return salida


def borrar(nombre):
    d = config.carpeta("respaldos") / nombre
    if d.parent != config.carpeta("respaldos") or not d.is_dir():
        raise ValueError("Ese respaldo no existe.")
    shutil.rmtree(d)
