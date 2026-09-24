"""
Fotos de producto: la principal se sube cuadrada (1280 x 1280 PNG) para que
la grilla de la tienda quede pareja; las demas, tal cual.

Si la foto no es cuadrada se completan los costados con el color del fondo
(si el borde es parejo, como en las fotos de estudio) o con blanco.
"""

import base64
import io
import re
import statistics
from pathlib import Path

import requests
from PIL import Image, ImageOps

LADO = 1280
H = {"User-Agent": "Mozilla/5.0 (compatible; Mostrador)"}


def color_de_fondo(im):
    w, h = im.size
    px = im.load()
    paso = max(1, max(w, h) // 200)
    borde = [px[x, 0] for x in range(0, w, paso)] + [px[x, h - 1] for x in range(0, w, paso)]
    borde += [px[0, y] for y in range(0, h, paso)] + [px[w - 1, y] for y in range(0, h, paso)]
    canales = list(zip(*borde))
    if all(statistics.pstdev(c) < 10 for c in canales):
        return tuple(int(statistics.median(c)) for c in canales)
    return (255, 255, 255)


def normalizar(datos, lado=LADO):
    """bytes de cualquier imagen -> bytes PNG de lado x lado."""
    im = Image.open(io.BytesIO(datos))
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        im = Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im)
    im = im.convert("RGB")
    ancho, alto = im.size
    escala = lado / max(ancho, alto)
    nuevo = (max(1, round(ancho * escala)), max(1, round(alto * escala)))
    if nuevo != im.size:
        im = im.resize(nuevo, Image.LANCZOS)
    if nuevo != (lado, lado):
        lienzo = Image.new("RGB", (lado, lado), color_de_fondo(im))
        lienzo.paste(im, ((lado - nuevo[0]) // 2, (lado - nuevo[1]) // 2))
        im = lienzo
    salida = io.BytesIO()
    im.save(salida, "PNG", optimize=True)
    return salida.getvalue()


def bajar(url):
    r = requests.get(url, headers=H, timeout=90)
    r.raise_for_status()
    return r.content


def original_de(src):
    """La direccion de la foto tal cual se subio (sin el '-1024-1024')."""
    return re.sub(r"-\d+-\d+(\.\w+)$", r"\1", src)


def subir(tn, pid, datos, nombre="foto.jpg", posicion=None, normalizar_esta=None):
    """Sube una foto (bytes, ruta o URL). La de la posicion 1 sale normalizada."""
    if isinstance(datos, str) and datos.startswith("http"):
        nombre = Path(datos.split("?")[0]).name or nombre
        datos = bajar(datos)
    elif isinstance(datos, (str, Path)):
        nombre = Path(datos).name
        datos = Path(datos).read_bytes()
    if normalizar_esta is None:
        normalizar_esta = posicion == 1
    if normalizar_esta:
        datos = normalizar(datos)
        nombre = Path(nombre).stem + ".png"
    cuerpo = {"filename": nombre, "attachment": base64.b64encode(datos).decode()}
    if posicion:
        cuerpo["position"] = posicion
    return tn.post(f"products/{pid}/images", cuerpo)
