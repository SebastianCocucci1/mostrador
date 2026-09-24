"""
Ayudas para leer y escribir productos y variantes tal como los da la API.
"""

import re
import unicodedata


def texto_es(campo, defecto=""):
    """Los textos de Tiendanube vienen por idioma: {"es": "...", "pt": "..."}."""
    if isinstance(campo, dict):
        return campo.get("es") or next((v for v in campo.values() if v), defecto)
    return campo or defecto


def nombre(p):
    return texto_es(p.get("name"), str(p.get("id", "")))


def precio(v, campo="price"):
    try:
        return float(v.get(campo) or 0)
    except (TypeError, ValueError):
        return 0.0


def es_infinito(v):
    return v.get("stock_management") is False or v.get("stock") in (None, "")


def stock(v):
    """None = infinito."""
    if es_infinito(v):
        return None
    try:
        return int(float(v.get("stock") or 0))
    except (TypeError, ValueError):
        return 0


def valores(v):
    return " · ".join(texto_es(x) for x in v.get("values") or [])


def cuerpo_stock(v, valor):
    """Lo que hay que mandar para cambiar el stock. valor None = infinito.

    stock_management es de solo lectura: el infinito se pide con stock "".
    Si la tienda tiene varias ubicaciones, va dentro de inventory_levels.
    """
    s = "" if valor is None else int(valor)
    niveles = v.get("inventory_levels") or []
    if niveles:
        return {"inventory_levels": [{"location_id": n["location_id"], "stock": s if i == 0 else n.get("stock")}
                                     for i, n in enumerate(niveles)]}
    return {"stock": s}


def numero(t):
    """Entiende como escribe la gente: '104.720', '$ 104.720,50', '104720.5', 'USD 27,50'.

    Devuelve float o None si esta vacio. Levanta ValueError si no es un numero.
    """
    if isinstance(t, (int, float)):
        return float(t)
    t = str(t or "").strip()
    t = re.sub(r"(?i)u\$s|usd|ars|\$|\s", "", t)
    t = t.strip(".-") if not re.match(r"^-\d", t) else t
    if not t:
        return None
    if "," in t and "." in t:
        # el ultimo separador es el decimal
        if t.rfind(",") > t.rfind("."):
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    elif "," in t:
        partes = t.split(",")
        if len(partes) == 2 and len(partes[1]) != 3:
            t = t.replace(",", ".")
        else:
            t = t.replace(",", "")
    elif t.count(".") > 1 or re.fullmatch(r"-?\d{1,3}(\.\d{3})+", t):
        t = t.replace(".", "")
    return float(t)


def pesos(x):
    """104720 -> '104.720'; 27.5 -> '27,50'."""
    if x is None:
        return ""
    if abs(x - round(x)) < 0.005:
        return f"{x:,.0f}".replace(",", ".")
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def sin_tildes(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t or "")) if unicodedata.category(c) != "Mn")


def compacto(t):
    """Para comparar codigos: 'VK - Trou P4' == 'vk-trou p4' == 'VKTROUP4'."""
    return re.sub(r"[^A-Z0-9]", "", sin_tildes(t).upper())


def slug(t, largo=60):
    return re.sub(r"[^a-z0-9]+", "-", sin_tildes(t).lower()).strip("-")[:largo] or "producto"


def resumen(p, cats=None):
    """Lo que necesita ver la interfaz de un producto (liviano para mandar al navegador)."""
    vs = p.get("variants") or []
    fotos = sorted(p.get("images") or [], key=lambda i: i.get("position") or 0)
    precios = sorted(precio(v) for v in vs if precio(v) > 0)
    stocks = [stock(v) for v in vs]
    cats = cats or {}
    return {
        "id": p["id"],
        "nombre": nombre(p),
        "marca": p.get("brand") or "",
        "publicado": bool(p.get("published")),
        "url": p.get("canonical_url") or "",
        "foto": fotos[0].get("src", "") if fotos else "",
        "fotos": len(fotos),
        "categorias": [cats.get(c["id"], texto_es(c.get("name"))) for c in p.get("categories") or []],
        "desplegables": [texto_es(a) for a in p.get("attributes") or []],
        "precio_min": precios[0] if precios else 0,
        "precio_max": precios[-1] if precios else 0,
        "sin_precio": any(precio(v) <= 0 for v in vs) or not vs,
        "sin_stock": any(s is not None and s <= 0 for s in stocks),
        "stock_infinito": all(s is None for s in stocks),
        "stock_total": sum(s for s in stocks if s is not None),
        "sin_descripcion": len(re.sub(r"<[^>]+>|\s", "", texto_es(p.get("description")))) < 20,
        "sin_categoria": not p.get("categories"),
        "actualizado": p.get("updated_at") or "",
        "variantes": [{
            "id": v["id"],
            "valores": valores(v) or "Única",
            "precio": precio(v),
            "promocional": precio(v, "promotional_price") or None,
            "stock": stock(v),
            "sku": v.get("sku") or "",
        } for v in vs],
    }


def caminos_categorias(cats):
    """id -> 'Padre > Hija' para mostrar."""
    por_id = {c["id"]: c for c in cats}

    def camino(c, vistos=()):
        padre = por_id.get(c.get("parent"))
        if padre and padre["id"] not in vistos:
            return camino(padre, vistos + (c["id"],)) + " › " + texto_es(c.get("name"))
        return texto_es(c.get("name"))
    return {c["id"]: camino(c) for c in cats}
