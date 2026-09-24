"""
Edicion masiva con Excel: exportar la tienda, editarla en Excel y volver
a importarla viendo antes exactamente que va a cambiar.

La planilla tiene una fila por variante. Las columnas grises son para
reconocer cada fila (no se editan); las verdes se pueden cambiar.

Los datos del producto (nombre, marca, publicado) se repiten en cada
variante. Si se cambian en una sola fila, vale ese cambio; si dos filas del
mismo producto dicen cosas distintas, se avisa y no se toca ese dato.
"""

from datetime import datetime

from . import respaldos
from .productos import cuerpo_stock, nombre, numero, precio, stock, texto_es, valores

HOJA = "Productos"

# (clave, titulo, ancho, editable)
COLUMNAS = [
    ("producto_id", "ID producto", 13, False),
    ("variante_id", "ID variante", 13, False),
    ("nombre", "Producto", 38, True),
    ("marca", "Marca", 16, True),
    ("publicado", "Publicado", 11, True),
    ("variante", "Variante", 26, False),
    ("sku", "SKU", 18, True),
    ("precio", "Precio", 14, True),
    ("promocional", "Precio promocional", 18, True),
    ("stock", "Stock", 10, True),
    ("categorias", "Categorías", 34, False),
]
TITULOS = {c[1].lower(): c[0] for c in COLUMNAS}
NOMBRES_CAMPO = {"nombre": "Nombre", "marca": "Marca", "publicado": "Publicado", "sku": "SKU",
                 "precio": "Precio", "promocional": "Precio promocional", "stock": "Stock"}

INSTRUCCIONES = [
    ("Cómo usar esta planilla", True),
    ("", False),
    ("1. Cambiá lo que quieras en las columnas VERDES: nombre, marca, publicado, SKU, precios y stock.", False),
    ("2. No toques las columnas GRISES (ID producto, ID variante): son las que dicen a qué producto va cada fila.", False),
    ("3. Guardá el archivo (tiene que seguir siendo .xlsx).", False),
    ("4. En la app, andá a «Edición con Excel» → «Importar» y elegí este archivo.", False),
    ("5. La app te muestra la lista de cambios ANTES de aplicarlos. Nada cambia hasta que confirmes.", False),
    ("", False),
    ("Detalles", True),
    ("• Stock vacío = stock infinito (el producto nunca se agota).", False),
    ("• Precio promocional vacío = sin promoción.", False),
    ("• Publicado: «Sí» o «No».", False),
    ("• Los precios se pueden escribir como 104720, 104.720 o 104.720,50.", False),
    ("• Podés borrar filas que no quieras tocar: las que no están en la planilla no se cambian.", False),
    ("• No se pueden agregar productos nuevos desde acá (usá «Nuevo producto» en la app).", False),
    ("• Antes de aplicar, la app guarda un respaldo automático de los productos que cambian.", False),
]


# ============================================================ exportar

def exportar(productos, ruta, caminos_cats=None, marca=None):
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation

    caminos_cats = caminos_cats or {}
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = HOJA

    gris = PatternFill("solid", fgColor="E7E9EE")
    cab_gris = PatternFill("solid", fgColor="5B6474")
    cab_verde = PatternFill("solid", fgColor="1F8A5B")
    blanco = Font(bold=True, color="FFFFFF")

    for j, (_, titulo, ancho, editable) in enumerate(COLUMNAS, 1):
        c = ws.cell(row=1, column=j, value=titulo)
        c.font = blanco
        c.fill = cab_verde if editable else cab_gris
        c.alignment = Alignment(vertical="center", horizontal="center")
        ws.column_dimensions[c.column_letter].width = ancho
    ws.row_dimensions[1].height = 24

    fila = 2
    n_prod = 0
    for p in sorted(productos, key=lambda x: nombre(x).lower()):
        if marca and (p.get("brand") or "").lower() != marca.lower():
            continue
        n_prod += 1
        cats = ", ".join(caminos_cats.get(c["id"], texto_es(c.get("name"))) for c in p.get("categories") or [])
        for v in p.get("variants") or []:
            s = stock(v)
            vals = {
                "producto_id": p["id"], "variante_id": v["id"], "nombre": nombre(p),
                "marca": p.get("brand") or "", "publicado": "Sí" if p.get("published") else "No",
                "variante": valores(v) or "Única", "sku": v.get("sku") or "",
                "precio": precio(v) or None, "promocional": precio(v, "promotional_price") or None,
                "stock": s, "categorias": cats,
            }
            for j, (clave, _, _, editable) in enumerate(COLUMNAS, 1):
                c = ws.cell(row=fila, column=j, value=vals[clave])
                if not editable:
                    c.fill = gris
                    c.font = Font(color="4A5160")
                if clave in ("precio", "promocional"):
                    c.number_format = '#,##0.00'
            fila += 1

    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{ws.cell(row=1, column=len(COLUMNAS)).column_letter}{max(fila - 1, 1)}"
    col_pub = next(i for i, c in enumerate(COLUMNAS, 1) if c[0] == "publicado")
    letra = ws.cell(row=1, column=col_pub).column_letter
    dv = DataValidation(type="list", formula1='"Sí,No"', allow_blank=False,
                        error="Escribí Sí o No", errorTitle="Publicado")
    ws.add_data_validation(dv)
    dv.add(f"{letra}2:{letra}{max(fila - 1, 2)}")

    ayuda = wb.create_sheet("Cómo usar")
    ayuda.column_dimensions["A"].width = 110
    for i, (texto, titulo) in enumerate(INSTRUCCIONES, 1):
        c = ayuda.cell(row=i, column=1, value=texto)
        if titulo:
            c.font = Font(bold=True, size=13)
    ayuda.cell(row=len(INSTRUCCIONES) + 2, column=1,
               value=f"Exportado el {datetime.now():%d/%m/%Y %H:%M}").font = Font(italic=True, color="888888")
    wb.active = 0          # que abra en la hoja de productos
    wb.save(ruta)
    return {"ruta": str(ruta), "productos": n_prod, "variantes": fila - 2}


# ============================================================ importar

def _leer_filas(ruta):
    import openpyxl
    wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
    ws = wb[HOJA] if HOJA in wb.sheetnames else wb.worksheets[0]
    filas = list(ws.iter_rows(values_only=True))
    wb.close()
    enc = None
    for i, f in enumerate(filas[:10]):
        titulos = [str(x or "").strip().lower() for x in f]
        if "id variante" in titulos:
            enc = i
            break
    if enc is None:
        raise ValueError("Esta planilla no tiene la columna «ID variante». Usá una planilla exportada "
                         "desde la app (Edición con Excel → Exportar).")
    cols = {}
    for j, t in enumerate(filas[enc]):
        clave = TITULOS.get(str(t or "").strip().lower())
        if clave:
            cols[clave] = j
    salida = []
    for n, f in enumerate(filas[enc + 1:], enc + 2):
        if not any(x not in (None, "") for x in f):
            continue
        salida.append((n, {k: (f[j] if j < len(f) else None) for k, j in cols.items()}))
    return salida, cols


def _texto(x):
    if x is None:
        return ""
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x).strip()


def _si_no(x):
    t = _texto(x).lower()
    if t in ("sí", "si", "s", "yes", "true", "1", "x"):
        return True
    if t in ("no", "n", "false", "0", ""):
        return False
    raise ValueError(f"«{x}» no es Sí ni No")


def _precio(x, vacio_ok=True):
    if x in (None, ""):
        if vacio_ok:
            return None
        raise ValueError("está vacío")
    v = numero(x)
    if v is None:
        return None
    if v < 0:
        raise ValueError("es negativo")
    return round(v, 2)


def _stock(x):
    t = _texto(x).lower()
    if t in ("", "∞", "infinito", "inf"):
        return None
    v = numero(t)
    if v is None:
        return None
    if v < 0 or v != int(v):
        raise ValueError("tiene que ser un número entero, o vacío para infinito")
    return int(v)


def comparar(ruta, productos):
    """Lee la planilla y la compara con la tienda. No cambia nada."""
    filas, cols = _leer_filas(ruta)
    por_prod = {p["id"]: p for p in productos}
    por_var = {v["id"]: (p, v) for p in productos for v in p.get("variants") or []}
    cambios, errores = [], []
    nuevos_prod = {}          # pid -> campo -> {valor: [filas]}

    def cambio(p, v, campo, antes, despues):
        cambios.append({
            "producto_id": p["id"], "variante_id": v["id"] if v else None,
            "producto": nombre(p), "variante": (valores(v) or "Única") if v else "(todo el producto)",
            "campo": campo, "campo_texto": NOMBRES_CAMPO[campo], "antes": antes, "despues": despues,
        })

    for n, f in filas:
        try:
            vid = int(float(f.get("variante_id")))
        except (TypeError, ValueError):
            errores.append({"fila": n, "mensaje": "No tiene «ID variante»: no sé a qué producto va."})
            continue
        if vid not in por_var:
            errores.append({"fila": n, "mensaje": f"La variante {vid} ya no existe en la tienda "
                                                  "(¿se borró?). Esa fila se saltea."})
            continue
        p, v = por_var[vid]

        for campo, lector in (("nombre", _texto), ("marca", _texto), ("publicado", _si_no)):
            if campo not in cols:
                continue
            try:
                val = lector(f.get(campo))
            except ValueError as e:
                errores.append({"fila": n, "mensaje": f"{NOMBRES_CAMPO[campo]}: {e}"})
                continue
            if campo == "nombre" and not val:
                continue
            nuevos_prod.setdefault(p["id"], {}).setdefault(campo, {}).setdefault(val, []).append(n)

        for campo, lector, actual in (
                ("sku", _texto, v.get("sku") or ""),
                ("precio", lambda x: _precio(x), precio(v) or None),
                ("promocional", _precio, precio(v, "promotional_price") or None),
                ("stock", _stock, stock(v))):
            if campo not in cols:
                continue
            try:
                val = lector(f.get(campo))
            except ValueError as e:
                errores.append({"fila": n, "mensaje": f"{NOMBRES_CAMPO[campo]}: {e}"})
                continue
            if campo == "precio" and val is None:
                continue        # precio vacio: no se toca (no se puede "sacar" el precio)
            if campo in ("precio", "promocional"):
                igual = (val or 0) == (actual or 0) or (val is not None and actual is not None
                                                        and abs(val - actual) < 0.01)
            else:
                igual = val == actual
            if not igual:
                cambio(p, v, campo, actual, val)

    actuales = {"nombre": nombre, "marca": lambda p: p.get("brand") or "",
                "publicado": lambda p: bool(p.get("published"))}
    for pid, campos in nuevos_prod.items():
        p = por_prod[pid]
        for campo, por_valor in campos.items():
            actual = actuales[campo](p)
            distintos = [val for val in por_valor if val != actual]
            if len(distintos) == 1:
                cambio(p, None, campo, actual, distintos[0])
            elif len(distintos) > 1:
                filas_txt = ", ".join(str(x) for val in distintos for x in por_valor[val])
                errores.append({"fila": min(x for val in distintos for x in por_valor[val]),
                                "mensaje": f"«{nombre(p)}»: las filas {filas_txt} tienen distinto "
                                           f"{NOMBRES_CAMPO[campo].lower()}. No se cambia; dejalo igual en todas."})

    cambios.sort(key=lambda c: (c["producto"].lower(), c["variante_id"] or 0, c["campo"]))
    return {
        "cambios": cambios, "errores": errores, "filas": len(filas),
        "resumen": {
            "productos": len({c["producto_id"] for c in cambios}),
            "cambios": len(cambios),
            "precios": sum(c["campo"] in ("precio", "promocional") for c in cambios),
            "stock": sum(c["campo"] == "stock" for c in cambios),
            "otros": sum(c["campo"] not in ("precio", "promocional", "stock") for c in cambios),
            "errores": len(errores),
        },
    }


def aplicar(tn, cambios, tarea):
    """Aplica los cambios de comparar() (ya filtrados por el usuario)."""
    por_prod = {}
    for c in cambios:
        por_prod.setdefault(c["producto_id"], []).append(c)
    tarea.avance(0, len(por_prod), "Leyendo la tienda para hacer el respaldo…")
    frescos = {p["id"]: p for p in tn.productos()}
    resp = respaldos.crear([frescos[i] for i in por_prod if i in frescos], "antes de importar planilla")
    tarea.anotar(f"Respaldo guardado: {resp['nombre']}")

    hechos, errores = 0, []
    for i, (pid, cs) in enumerate(por_prod.items(), 1):
        if tarea.cancelada:
            tarea.anotar(f"Cancelado. Se llegaron a actualizar {i - 1} de {len(por_prod)} productos.")
            break
        p = frescos.get(pid)
        tarea.avance(i - 1, len(por_prod), nombre(p) if p else str(pid))
        if not p:
            errores.append(f"El producto {pid} ya no existe.")
            continue
        variantes = {v["id"]: v for v in p.get("variants") or []}
        try:
            cuerpo = {}
            for c in cs:
                if c["variante_id"] is None:
                    if c["campo"] == "nombre":
                        cuerpo["name"] = {**(p.get("name") or {}), "es": c["despues"]}
                    elif c["campo"] == "marca":
                        cuerpo["brand"] = c["despues"]
                    elif c["campo"] == "publicado":
                        cuerpo["published"] = c["despues"]
            if cuerpo:
                tn.put(f"products/{pid}", cuerpo)
            por_var = {}
            for c in cs:
                if c["variante_id"] is not None:
                    por_var.setdefault(c["variante_id"], []).append(c)
            for vid, vcs in por_var.items():
                v = variantes.get(vid)
                if not v:
                    errores.append(f"{nombre(p)}: la variante {vid} ya no existe.")
                    continue
                b = {}
                for c in vcs:
                    if c["campo"] == "precio":
                        b["price"] = c["despues"]
                    elif c["campo"] == "promocional":
                        b["promotional_price"] = c["despues"]
                    elif c["campo"] == "sku":
                        b["sku"] = c["despues"]
                    elif c["campo"] == "stock":
                        b.update(cuerpo_stock(v, c["despues"]))
                tn.actualizar_variante(pid, vid, b)
            hechos += 1
            tarea.anotar(f"✓ {nombre(p)} ({len(cs)} cambio(s))")
        except Exception as e:      # noqa: BLE001  (sigue con el resto)
            errores.append(f"{nombre(p)}: {e}")
            tarea.anotar(f"✗ {nombre(p)}: {e}")
    tarea.avance(len(por_prod), len(por_prod), "Listo")
    return {"hechos": hechos, "errores": errores, "respaldo": resp["nombre"]}
