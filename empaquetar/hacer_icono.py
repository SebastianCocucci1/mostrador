"""
Dibuja el icono de la app (el mismo de web/icono.svg) y lo guarda como .ico
con todos los tamaños que usa Windows.

    python empaquetar/hacer_icono.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
LADO = 512


def degradado(lado):
    im = Image.new("RGB", (lado, lado))
    a, b = (0x4C, 0x6F, 0xFF), (0x2A, 0x3F, 0xB8)
    px = im.load()
    for y in range(lado):
        for x in range(lado):
            t = (x + y) / (2 * (lado - 1))
            px[x, y] = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return im


def dibujar():
    s = LADO / 64
    fondo = degradado(LADO)
    mascara = Image.new("L", (LADO, LADO), 0)
    ImageDraw.Draw(mascara).rounded_rectangle([0, 0, LADO - 1, LADO - 1], radius=round(15 * s), fill=255)
    im = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
    im.paste(fondo, (0, 0), mascara)
    d = ImageDraw.Draw(im)
    blanco = (255, 255, 255, 255)
    g = round(3.5 * s)
    P = lambda x, y: (x * s, y * s)                     # noqa: E731
    d.line([P(14, 26), P(18, 16), P(46, 16), P(50, 26)], fill=blanco, width=g, joint="curve")
    for x0 in (14, 23, 32, 41):                        # el toldo
        d.arc([P(x0, 20), P(x0 + 9, 32)], start=0, end=180, fill=blanco, width=g)
    d.line([P(18, 32), P(18, 48), P(46, 48), P(46, 32)], fill=blanco, width=g, joint="curve")
    d.rounded_rectangle([P(28, 38), P(36, 48)], radius=round(1.5 * s), fill=blanco)
    return im


if __name__ == "__main__":
    im = dibujar()
    im.save(AQUI / "icono.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    im.save(AQUI / "icono.png")
    print("Listo:", AQUI / "icono.ico")
