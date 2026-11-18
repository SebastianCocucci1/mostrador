"""Pruebas del motor (sin tocar ninguna tienda de verdad)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mostrador import excel, precios  # noqa: E402
from mostrador.productos import compacto, cuerpo_stock, numero, pesos, resumen  # noqa: E402


# ------------------------------------------------------------ numeros

@pytest.mark.parametrize("texto,esperado", [
    ("104.720", 104720), ("104720", 104720), ("$ 104.720,50", 104720.5), ("104720.5", 104720.5),
    ("1.221.000,00", 1221000), ("27,50", 27.5), ("USD 27,50", 27.5), ("1,7", 1.7), ("1.7", 1.7),
    ("$430000.", 430000), ("", None), ("  ", None), (1540, 1540), ("-5", -5),
])
def test_numero(texto, esperado):
    assert numero(texto) == esperado


def test_numero_invalido():
    with pytest.raises(ValueError):
        numero("hola")


def test_pesos():
    assert pesos(104720) == "104.720"
    assert pesos(27.5) == "27,50"


def test_compacto():
    assert compacto("VK - Trou P4") == compacto("vk-trou-p4") == "VKTROUP4"


def test_cuerpo_stock_con_ubicaciones():
    v = {"inventory_levels": [{"location_id": "A", "stock": 3}, {"location_id": "B", "stock": 5}]}
    assert cuerpo_stock(v, None) == {"inventory_levels": [{"location_id": "A", "stock": ""},
                                                          {"location_id": "B", "stock": 5}]}
    assert cuerpo_stock({}, 7) == {"stock": 7}


# ------------------------------------------------------------ tienda de juguete

def producto(pid, nombre, variantes, marca="Acme", publicado=True):
    return {"id": pid, "name": {"es": nombre}, "brand": marca, "published": publicado, "images": [],
            "categories": [], "attributes": [{"es": "Color"}] if len(variantes) > 1 else [],
            "description": {"es": ""},
            "variants": [{"id": pid * 100 + i, "sku": sku, "price": str(pr), "promotional_price": None,
                          "stock": st, "stock_management": st is not None,
                          "values": [{"es": f"V{i}"}] if len(variantes) > 1 else []}
                         for i, (sku, pr, st) in enumerate(variantes)]}


TIENDA = [
    producto(1, "Lámpara Nube", [("VK-NUBE-N", 10000, None), ("VK-NUBE-B", 10000, None)]),
    producto(2, "Aplique Sol", [("AP-SOL", 5000, 3)]),
    producto(3, "Plafón Luna", [("PL-LUNA", 0, None)], marca="Otra"),
]


# ------------------------------------------------------------ precios

def test_regla():
    r = {"descuentos": [10, 5], "multiplicador": 1.6, "redondeo": 100, "modo_redondeo": "arriba"}
    assert precios.aplicar_regla(1221000, r) == 1670400
    assert precios.aplicar_regla(1000, {"multiplicador": 1.7, "iva": 21}) == pytest.approx(2057)
    assert precios.aplicar_regla(10, {"cotizacion": 1450, "redondeo": 1000}) == 15000
    assert precios.aplicar_regla(1234, {"redondeo": 100, "modo_redondeo": "abajo"}) == 1200


def test_vista_previa_por_sku():
    items = [("vk nube n", 7000, "", ""), ("AP SOL", 2000, "", ""), ("NO-EXISTE", 99, "", ""), ("PL-LUNA", 100, "", "")]
    v = precios.vista_previa(TIENDA, items, {"multiplicador": 2}, por="sku")
    por_sku = {c["sku"]: c for c in v["cambios"]}
    assert por_sku["VK-NUBE-N"]["precio_nuevo"] == 14000 and por_sku["VK-NUBE-N"]["estado"] == "sube"
    assert por_sku["AP-SOL"]["precio_nuevo"] == 4000 and por_sku["AP-SOL"]["estado"] == "baja"
    assert por_sku["PL-LUNA"]["estado"] == "nuevo"
    assert v["total_sin_coincidencia"] == 1
    assert v["total_faltan_en_lista"] == 1          # VK-NUBE-B
    # el 40% de suba no se elige solo: hay que mirarlo
    assert por_sku["VK-NUBE-N"]["avisos"] and not por_sku["VK-NUBE-N"]["elegido"]


def test_codigo_con_cantidad_entre_parentesis():
    # Dabor: "ABUYA-S (1u)" en la lista, "abuya-s" en la tienda
    tienda = [producto(9, "Abuya", [("abuya-s", 0, None), ("abuya-m", 0, None)])]
    items = [("ABUYA-S (1u)", 100, "", ""), ("ABUYA-M (50 u)", 200, "", ""), ("ABUYA-X [nuevo]", 5, "", "")]
    v = precios.vista_previa(tienda, items, {}, por="sku")
    assert {c["sku"]: c["precio_nuevo"] for c in v["cambios"]} == {"abuya-s": 100, "abuya-m": 200}
    assert precios.claves_de_codigo("A (1u)") == ["A1U", "A"]


def test_vista_previa_marca_y_no_bajar():
    items = [("AP-SOL", 2400, "", ""), ("PL-LUNA", 100, "", "")]
    v = precios.vista_previa(TIENDA, items, {"multiplicador": 2}, marca="acme", no_bajar=True)
    assert [c["sku"] for c in v["cambios"]] == ["AP-SOL"]
    assert v["cambios"][0]["elegido"] is False       # baja y no se quiere bajar


def test_vista_previa_por_nombre_va_a_todas_las_variantes():
    v = precios.vista_previa(TIENDA, [("LAMPARA NUBE", 6000, "", "")], {"multiplicador": 2}, por="nombre")
    assert len(v["cambios"]) == 2 and all(c["precio_nuevo"] == 12000 for c in v["cambios"])


def test_columnas_y_adivinar():
    doc = {"tipo": "planilla", "lineas": [], "hojas": [{"nombre": "Lista", "filas": [
        ["Lista de precios Octubre", "", ""],
        ["Código", "Descripción", "Precio de lista"],
        ["AP-SOL", "Aplique sol", "$ 2.500,00"],
        ["VK-NUBE-N", "Nube negra", "7.000"],
        ["", "Subtítulo", ""],
    ]}]}
    g = precios.adivinar(doc["hojas"][0]["filas"])
    assert g == {"fila_encabezado": 1, "col_codigo": 0, "col_precio": 2, "col_desc": 1}
    items = precios.items_de_columnas(doc, "Lista", g["col_codigo"], g["col_precio"], g["fila_encabezado"])
    assert [(c, p) for c, p, *_ in items] == [("AP-SOL", 2500), ("VK-NUBE-N", 7000)]


def test_elige_la_hoja_con_precios_y_no_el_indice():
    # como el Excel de Dabor: un indice (nombre -> pagina) antes de las listas
    doc = {"tipo": "planilla", "lineas": [], "hojas": [
        {"nombre": "INDICE", "filas": [["INDICE", "LISTA DE PRECIOS Nº76 AGOSTO 2025"],
                                       ["ABUYA", "6"], ["AKAKI", "6"], ["ALTOS", "9"]]},
        {"nombre": "LAMPARAS", "filas": [["CODIGO", "DESCRIPCION", "$"], ["L-E27-7W", "Lampara", "1052,50"]]},
        {"nombre": "ARTEFACTOS", "filas": [["ARTICULO", "DESCRIPCION", "PRECIO"], ["ABUYA-S", "Colgante", "58000"],
                                           ["AKAKI-M", "Colgante", "61000"]]},
    ]}
    m = precios.muestra(doc)
    assert [h["precios"] for h in m["hojas"]] == [0, 1, 2]
    assert m["mejor"] == 2
    # un titulo suelto no es la fila de titulos
    assert m["hojas"][0]["sugerido"]["fila_encabezado"] is None


def test_buscar_en_texto():
    doc = {"lineas": ["Aplique Sol", "Blanco AP-SOL $ 2.500,00", "Negro AP-SOLX $ 9.999",
                      "Lámpara VK-NUBE-N", "medidas 30 cm", "$ 7.000.-"]}
    items = dict((c, p) for c, p, *_ in precios.items_de_texto(doc, ["AP-SOL", "VK-NUBE-N", "ZZZ-1"]))
    assert items == {"AP-SOL": 2500, "VK-NUBE-N": 7000}


# ------------------------------------------------------------ excel

def test_excel_ida_y_vuelta(tmp_path):
    import openpyxl
    ruta = tmp_path / "tienda.xlsx"
    r = excel.exportar(TIENDA, ruta)
    assert r["variantes"] == 4

    wb = openpyxl.load_workbook(ruta)
    ws = wb["Productos"]
    cols = {c.value: c.column for c in ws[1]}
    filas = {ws.cell(row=i, column=cols["SKU"]).value: i for i in range(2, ws.max_row + 1)}
    ws.cell(row=filas["AP-SOL"], column=cols["Precio"], value="5.500")        # precio
    ws.cell(row=filas["AP-SOL"], column=cols["Stock"]).value = None           # a infinito
    ws.cell(row=filas["VK-NUBE-B"], column=cols["Publicado"], value="No")     # dato del producto
    ws.cell(row=filas["PL-LUNA"], column=cols["Stock"], value="dos")          # error
    wb.save(ruta)

    comp = excel.comparar(ruta, TIENDA)
    cambios = {(c["producto_id"], c["campo"]): c for c in comp["cambios"]}
    assert cambios[(2, "precio")]["despues"] == 5500
    assert cambios[(2, "stock")]["antes"] == 3 and cambios[(2, "stock")]["despues"] is None
    assert cambios[(1, "publicado")]["despues"] is False
    assert len(comp["cambios"]) == 3
    assert len(comp["errores"]) == 1 and "Stock" in comp["errores"][0]["mensaje"]


def test_excel_conflicto_en_dato_de_producto(tmp_path):
    import openpyxl
    ruta = tmp_path / "t.xlsx"
    excel.exportar(TIENDA, ruta)
    wb = openpyxl.load_workbook(ruta)
    ws = wb["Productos"]
    cols = {c.value: c.column for c in ws[1]}
    for i in range(2, ws.max_row + 1):
        sku = ws.cell(row=i, column=cols["SKU"]).value
        if sku == "VK-NUBE-N":
            ws.cell(row=i, column=cols["Producto"], value="Nube A")
        if sku == "VK-NUBE-B":
            ws.cell(row=i, column=cols["Producto"], value="Nube B")
    wb.save(ruta)
    comp = excel.comparar(ruta, TIENDA)
    assert not [c for c in comp["cambios"] if c["campo"] == "nombre"]
    assert any("distinto" in e["mensaje"] for e in comp["errores"])


def test_resumen():
    r = resumen(TIENDA[1])
    assert r["stock_total"] == 3 and not r["stock_infinito"] and not r["sin_precio"]
    assert resumen(TIENDA[2])["sin_precio"]
