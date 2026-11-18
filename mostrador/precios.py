"""
Actualizar precios desde la lista de cualquier proveedor (Excel, CSV o PDF).

EL CIRCUITO
    1. leer(archivo)            -> las hojas/tablas y el texto del documento
    2. el usuario elige COMO leerla:
         "columnas"  tabla con una columna de codigo y una de precio
                     (Excel, CSV, PDF con tablas de verdad)
         "buscar"    PDF tipo catalogo, sin tablas: se buscan los SKU de la
                     tienda dentro del texto y se toma el precio mas cercano
    3. regla: descuentos en cascada, margen, IVA, cotizacion, redondeo
    4. vista_previa()           -> que variante cambia, de cuanto a cuanto
    5. aplicar()                -> respaldo automatico y despues los cambios

Emparejar es siempre por codigo "compacto" (sin espacios, guiones ni
mayusculas): "VK - Trou P4" en la lista encuentra al SKU "vk-trou-p4".
"""

import csv
import io
import math
import re
from pathlib import Path

from . import respaldos
from .productos import compacto, nombre, numero, precio, valores

MAX_FILAS_MUESTRA = 60

PAT_ENCABEZADO = re.compile(r"(?i)c[oó]d|sku|art[ií]culo|ref|modelo|precio|price|importe|valor|"
                            r"descrip|producto|nombre|detalle|lista|unit")
PAT_CODIGO = re.compile(r"(?i)c[oó]d|sku|art[ií]culo|^ref|modelo|item")
PAT_PRECIO = re.compile(r"(?i)precio|price|importe|valor|lista|p\.?\s*unit|\$|pvp|neto")
PAT_DESC = re.compile(r"(?i)descrip|producto|nombre|detalle")

# un precio: "$ 1.221.000,00", "$430000.-", "USD 27,50", o un numero con miles "1.221.000"
PAT_PRECIO_TEXTO = re.compile(
    r"(?:(?:\$|U\$S|USD|ARS)\s*(\d[\d.,]*\d|\d))"
    r"|(?<![\w.,])(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?)(?![\w.,]*\d)")


# ================================================================ leer

def _celda(x):
    if x is None:
        return ""
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x).strip()


def _sin_vacias(filas):
    filas = [[_celda(c) for c in f] for f in filas]
    filas = [f for f in filas if any(f)]
    if not filas:
        return []
    ancho = max(len(f) for f in filas)
    # sacar columnas vacias del final
    while ancho and not any(len(f) >= ancho and f[ancho - 1] for f in filas):
        ancho -= 1
    return [(f + [""] * ancho)[:ancho] for f in filas]


def leer(ruta):
    """Devuelve {"hojas": [{"nombre", "filas"}], "lineas": [texto], "tipo"}."""
    ruta = Path(ruta)
    ext = ruta.suffix.lower()
    if ext in (".xlsx", ".xlsm"):
        import openpyxl
        wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
        hojas = []
        for ws in wb.worksheets:
            filas = _sin_vacias(ws.iter_rows(values_only=True))
            if filas:
                hojas.append({"nombre": ws.title, "filas": filas})
        wb.close()
        lineas = ["  ".join(c for c in f if c) for h in hojas for f in h["filas"]]
        return {"tipo": "planilla", "hojas": hojas, "lineas": lineas}
    if ext == ".xls":
        raise ValueError("Los .xls viejos no se pueden leer. Abrilo en Excel y guardalo como .xlsx.")
    if ext in (".csv", ".txt", ".tsv"):
        crudo = ruta.read_bytes()
        for cod in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                texto = crudo.decode(cod)
                break
            except UnicodeDecodeError:
                continue
        try:
            dialecto = csv.Sniffer().sniff(texto[:5000], delimiters=",;\t|")
        except csv.Error:
            dialecto = csv.excel
        filas = _sin_vacias(csv.reader(io.StringIO(texto), dialecto))
        return {"tipo": "planilla", "hojas": [{"nombre": ruta.stem, "filas": filas}] if filas else [],
                "lineas": ["  ".join(c for c in f if c) for f in filas]}
    if ext == ".pdf":
        import pdfplumber
        tablas, lineas = [], []
        with pdfplumber.open(ruta) as pdf:
            for pag in pdf.pages:
                for t in pag.extract_tables() or []:
                    tablas += [[(c or "").replace("\n", " ") for c in f] for f in t]
                lineas += (pag.extract_text() or "").splitlines()
        tablas = _sin_vacias(tablas)
        hojas = [{"nombre": "Tablas del PDF", "filas": tablas}] if tablas and len(tablas[0]) >= 2 else []
        return {"tipo": "pdf", "hojas": hojas, "lineas": [x for x in lineas if x.strip()]}
    raise ValueError("Formato no soportado. Usá Excel (.xlsx), CSV o PDF.")


# ====================================================== adivinar columnas

def adivinar(filas):
    """Donde esta el encabezado y cuales son las columnas de codigo, precio y descripcion."""
    # la fila de titulos tiene al menos dos titulos cortos ("Codigo", "Precio"...):
    # un titulo suelto como "LISTA DE PRECIOS AGOSTO" no cuenta
    enc = None
    mejor = 1
    for i, f in enumerate(filas[:30]):
        n = sum(1 for c in f if c and len(c) <= 25 and PAT_ENCABEZADO.search(c))
        if n > mejor:
            enc, mejor = i, n
    ancho = len(filas[0]) if filas else 0
    datos = filas[(enc + 1) if enc is not None else 0:][:200]

    def columna(pat, excluir=()):
        if enc is None:
            return None
        for j, c in enumerate(filas[enc]):
            if j not in excluir and c and pat.search(c):
                return j
        return None

    def numerica(j):
        n = 0
        for f in datos:
            try:
                x = numero(f[j])
                n += 1 if x and x > 0 else 0
            except ValueError:
                pass
        return n

    col_precio = columna(PAT_PRECIO)
    col_codigo = columna(PAT_CODIGO, excluir=(col_precio,))
    col_desc = columna(PAT_DESC, excluir=(col_precio, col_codigo))
    # si el encabezado de precio no tiene numeros abajo, buscar la columna mas numerica
    if col_precio is None or numerica(col_precio) < len(datos) * 0.3:
        candidatas = [(numerica(j), j) for j in range(ancho) if j != col_codigo]
        if candidatas and max(candidatas)[0] > 0:
            col_precio = max(candidatas)[1]
    if col_codigo is None:
        # la columna con mas valores cortos alfanumericos y distintos
        puntaje = []
        for j in range(ancho):
            if j == col_precio:
                continue
            vals = [f[j] for f in datos if f[j]]
            cortos = [v for v in vals if 2 <= len(v) <= 25 and re.search(r"\d", v) and re.search(r"[A-Za-z]", v)]
            puntaje.append((len(set(cortos)), j))
        if puntaje and max(puntaje)[0] > 0:
            col_codigo = max(puntaje)[1]
    return {"fila_encabezado": enc, "col_codigo": col_codigo, "col_precio": col_precio, "col_desc": col_desc}


def precios_sugeridos(doc, h, g):
    """Cuantos renglones con codigo y precio salen de la hoja con las columnas adivinadas."""
    if g["col_codigo"] is None or g["col_precio"] is None:
        return 0
    return len(items_de_columnas(doc, h["nombre"], g["col_codigo"], g["col_precio"], g["fila_encabezado"]))


def muestra(doc):
    """Lo que se le manda a la interfaz para elegir columnas (sin mandar todo).

    Cada hoja dice cuantos precios se leen con lo adivinado, y "mejor" es la
    hoja con mas: los Excel de proveedores suelen traer un indice o una
    caratula en la primera hoja.
    """
    hojas = []
    for h in doc["hojas"]:
        g = adivinar(h["filas"])
        hojas.append({"nombre": h["nombre"], "filas": h["filas"][:MAX_FILAS_MUESTRA], "total": len(h["filas"]),
                      "sugerido": g, "precios": precios_sugeridos(doc, h, g)})
    mejor = max(range(len(hojas)), key=lambda i: hojas[i]["precios"]) if hojas else None
    return {
        "tipo": doc["tipo"],
        "hojas": hojas,
        "mejor": mejor,
        "lineas": len(doc["lineas"]),
        "precios_en_texto": sum(1 for x in doc["lineas"] if PAT_PRECIO_TEXTO.search(x)),
    }


# ============================================================ items

def items_de_columnas(doc, hoja, col_codigo, col_precio, fila_encabezado=None, col_desc=None):
    """[(codigo, precio_lista, descripcion, texto_origen)] de una tabla."""
    h = next((x for x in doc["hojas"] if x["nombre"] == hoja), None)
    if not h:
        raise ValueError("No encuentro esa hoja en el archivo.")
    filas = h["filas"][(fila_encabezado + 1) if fila_encabezado is not None else 0:]
    salida = []
    for f in filas:
        cod = f[col_codigo].strip() if col_codigo is not None and col_codigo < len(f) else ""
        try:
            p = numero(f[col_precio]) if col_precio is not None and col_precio < len(f) else None
        except ValueError:
            p = None
        if not cod or not p or p <= 0:
            continue
        desc = f[col_desc] if col_desc is not None and col_desc < len(f) else ""
        salida.append((cod, p, desc, "  ".join(c for c in f if c)[:160]))
    return salida


def precios_en(linea):
    """Los precios que aparecen en una linea de texto, con su posicion."""
    salida = []
    for m in PAT_PRECIO_TEXTO.finditer(linea):
        crudo = (m.group(1) or m.group(2)).rstrip(".,")
        try:
            x = numero(crudo)
        except ValueError:
            continue
        if x and x > 0:
            salida.append((m.start(), x))
    return salida


def patron_codigo(cod):
    """'HH11-02' encuentra 'HH11-02', 'HH11 02' y 'hh1102', pero no 'XHH11-021'."""
    trozos = re.findall(r"[A-Za-z0-9]+", cod)
    if not trozos:
        return None
    cuerpo = r"[\s\-_./]*".join(re.escape(t) for t in trozos)
    return re.compile(r"(?<![A-Za-z0-9])" + cuerpo + r"(?![A-Za-z0-9])", re.IGNORECASE)


def items_de_texto(doc, claves, lineas_alrededor=3):
    """Busca cada clave (SKU o nombre) en el texto. [(clave, precio, '', linea)].

    El precio es el primero que aparece despues de la clave en la misma linea;
    si no hay, el primero de las lineas siguientes (hasta lineas_alrededor).
    """
    lineas = doc["lineas"]
    precios = [precios_en(x) for x in lineas]
    salida = []
    for clave in claves:
        if len(compacto(clave)) < 3:
            continue
        pat = patron_codigo(clave)
        if not pat:
            continue
        for i, linea in enumerate(lineas):
            m = pat.search(linea)
            if not m:
                continue
            p = next((x for pos, x in precios[i] if pos >= m.end()), None)
            if p is None:
                for j in range(i + 1, min(len(lineas), i + 1 + lineas_alrededor)):
                    # puede ser de otro codigo: por eso la vista previa muestra la linea de origen
                    if precios[j]:
                        p = precios[j][0][1]
                        break
            if p:
                salida.append((clave, p, "", linea.strip()[:160]))
                break
    return salida


# ============================================================ la regla

def aplicar_regla(p, regla):
    """precio de lista -> precio de venta."""
    x = float(p)
    for d in regla.get("descuentos") or []:
        x *= 1 - float(d) / 100
    x *= float(regla.get("multiplicador") or 1)
    x *= 1 + float(regla.get("iva") or 0) / 100
    x *= float(regla.get("cotizacion") or 1)
    paso = float(regla.get("redondeo") or 0)
    if paso > 0:
        modo = regla.get("modo_redondeo", "cercano")
        if modo == "arriba":
            x = -(-x // paso) * paso
        elif modo == "abajo":
            x = (x // paso) * paso
        else:
            x = redondear(x, paso)
    else:
        x = redondear(x, 0.01)
    return x


def redondear(x, paso):
    """Al multiplo mas cercano, con el .5 para arriba (round() de Python redondea al par:
    14500 a mil daria 14000, y la gente espera 15000)."""
    return math.floor(x / paso + 0.5) * paso if paso >= 1 else math.floor(x * 100 + 0.5) / 100


# ======================================================== vista previa

PAT_PARENTESIS_FINAL = re.compile(r"\s*[(\[][^()\[\]]*[)\]]\s*$")


def claves_de_codigo(cod):
    """Las formas de un codigo de la lista con las que se busca en la tienda.

    Muchos proveedores agregan al final, entre parentesis, la cantidad por caja
    o una nota: "ABUYA-S (1u)", "EMBU-1 (50u)". Primero se prueba el codigo
    entero y despues sin eso.
    """
    salida = [compacto(cod)]
    sin = PAT_PARENTESIS_FINAL.sub("", str(cod or ""))
    if sin != cod and compacto(sin):
        salida.append(compacto(sin))
    return salida


def _variantes(productos, marca=None):
    for p in productos:
        if marca and (p.get("brand") or "").strip().lower() != marca.strip().lower():
            continue
        for v in p.get("variants") or []:
            yield p, v


def vista_previa(productos, items, regla, por="sku", marca=None, no_bajar=False, alerta_pct=40):
    """Cruza los items de la lista con las variantes de la tienda.

    por: "sku" (el SKU de cada variante) o "nombre" (el nombre del producto:
         el precio va a todas sus variantes).
    """
    indice = {}
    for p, v in _variantes(productos, marca):
        clave = compacto(v.get("sku") if por == "sku" else nombre(p))
        if clave:
            indice.setdefault(clave, []).append((p, v))

    cambios, sin_coincidencia, usados = [], [], {}
    for cod, p_lista, desc, origen in items:
        encontrados = next((indice[k] for k in claves_de_codigo(cod) if k in indice), None)
        if not encontrados:
            sin_coincidencia.append({"codigo": cod, "precio_lista": p_lista, "descripcion": desc,
                                     "origen": origen})
            continue
        nuevo = aplicar_regla(p_lista, regla)
        for prod, v in encontrados:
            clave = f"{prod['id']}:{v['id']}"
            if clave in usados:
                if abs(usados[clave] - nuevo) > 0.01:
                    for c in cambios:
                        if c["clave"] == clave:
                            c["avisos"].append(f"La lista tiene el código repetido con otro precio "
                                               f"(${nuevo:,.0f}); se usa el primero.")
                continue
            usados[clave] = nuevo
            actual = precio(v)
            if actual <= 0:
                estado, dif = "nuevo", None
            elif abs(nuevo - actual) < 0.01:
                estado, dif = "igual", 0.0
            else:
                estado = "sube" if nuevo > actual else "baja"
                dif = round((nuevo - actual) / actual * 100, 1)
            avisos = []
            if dif is not None and abs(dif) >= alerta_pct:
                avisos.append(f"Cambia {dif:+.0f}%: revisá que sea el código correcto.")
            elegido = estado in ("sube", "nuevo") or (estado == "baja" and not no_bajar)
            cambios.append({
                "clave": clave, "producto_id": prod["id"], "variante_id": v["id"],
                "producto": nombre(prod), "variante": valores(v) or "Única", "sku": v.get("sku") or "",
                "codigo": cod, "precio_lista": p_lista, "precio_actual": actual, "precio_nuevo": nuevo,
                "dif_pct": dif, "estado": estado, "avisos": avisos,
                "elegido": elegido and not avisos, "origen": origen,
            })

    # variantes de la tienda (del filtro) que no aparecieron en la lista
    faltan = [{"producto": nombre(p), "variante": valores(v) or "Única", "sku": v.get("sku") or ""}
              for p, v in _variantes(productos, marca) if f"{p['id']}:{v['id']}" not in usados]
    orden = {"sube": 0, "baja": 1, "nuevo": 2, "igual": 3}
    cambios.sort(key=lambda c: (not c["avisos"], orden[c["estado"]], c["producto"].lower()))
    return {
        "cambios": cambios,
        "sin_coincidencia": sin_coincidencia[:500],
        "total_sin_coincidencia": len(sin_coincidencia),
        "faltan_en_lista": faltan[:500],
        "total_faltan_en_lista": len(faltan),
        "resumen": {
            "leidos": len(items),
            "encontrados": len(cambios),
            "suben": sum(c["estado"] == "sube" for c in cambios),
            "bajan": sum(c["estado"] == "baja" for c in cambios),
            "nuevos": sum(c["estado"] == "nuevo" for c in cambios),
            "iguales": sum(c["estado"] == "igual" for c in cambios),
            "con_aviso": sum(bool(c["avisos"]) for c in cambios),
        },
    }


# ============================================================= aplicar

def aplicar(tn, cambios, tarea):
    """cambios: los elegidos de la vista previa. Respalda y actualiza precio por precio."""
    ids = sorted({c["producto_id"] for c in cambios})
    tarea.avance(0, len(cambios), "Leyendo la tienda para hacer el respaldo…")
    frescos = {p["id"]: p for p in tn.productos()}
    resp = respaldos.crear([frescos[i] for i in ids if i in frescos], "antes de actualizar precios")
    tarea.anotar(f"Respaldo guardado: {resp['nombre']}")

    hechos, errores = 0, []
    for i, c in enumerate(cambios, 1):
        if tarea.cancelada:
            tarea.anotar(f"Cancelado. Se llegaron a cambiar {hechos} de {len(cambios)}.")
            break
        tarea.avance(i - 1, len(cambios), f"{c['producto']} · {c['variante']}")
        if c["producto_id"] not in frescos:
            errores.append(f"{c['producto']}: ya no existe en la tienda.")
            continue
        try:
            tn.actualizar_variante(c["producto_id"], c["variante_id"], {"price": c["precio_nuevo"]})
            hechos += 1
            tarea.anotar(f"✓ {c['producto']} · {c['variante']}: ${c['precio_actual']:,.0f} → "
                         f"${c['precio_nuevo']:,.0f}".replace(",", "."))
        except Exception as e:      # noqa: BLE001  (sigue con el resto)
            errores.append(f"{c['producto']} · {c['variante']}: {e}")
            tarea.anotar(f"✗ {c['producto']} · {c['variante']}: {e}")
    tarea.avance(hechos + len(errores), len(cambios), "Listo")
    return {"hechos": hechos, "errores": errores, "respaldo": resp["nombre"]}
