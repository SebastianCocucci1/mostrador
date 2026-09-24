"""
El servidor local que usa la interfaz. Solo escucha en 127.0.0.1.

Seguridad: el token de la tienda vive aca, asi que cualquier pagina web que
el usuario tenga abierta podria intentar pegarle a http://127.0.0.1:<puerto>.
Para que no pueda:
    - cada pedido a /api/ tiene que traer el header X-Clave con una clave
      aleatoria que se genera al arrancar y solo conoce la pagina de la app
      (un sitio ajeno no la puede leer ni mandar headers propios sin CORS);
    - el Host tiene que ser 127.0.0.1:<puerto> (evita el DNS rebinding).
"""

import json
import logging
import os
import secrets
import sys
import tempfile
import threading
import time
import uuid
import webbrowser
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory
from werkzeug.serving import make_server

from . import NOMBRE, VERSION, config, excel, fotos, precios, respaldos, tareas
from .productos import caminos_categorias, cuerpo_stock, nombre, numero, precio, resumen, slug
from .tiendanube import ErrorApi, Tiendanube, canjear_codigo, link_autorizar


def carpeta_web():
    # empaquetado con PyInstaller los archivos quedan en sys._MEIPASS
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / "web"


class Estado:
    def __init__(self):
        self.candado = threading.RLock()
        self.tn = None
        self.tienda = None
        self.productos = []
        self.categorias = []
        self.cargado = 0.0
        self.listas = {}        # id -> {"ruta", "nombre", "doc"}
        self.vistas = {}        # id -> vista previa de precios
        self.planillas = {}     # id -> comparacion de excel
        self.conectar_guardada()

    def conectar_guardada(self):
        t = config.tienda()
        if t:
            self.tn = Tiendanube(t["id"], t["token"])
            self.tienda = t

    def requiere_tn(self):
        if not self.tn:
            raise ErrorApi("Primero conectá tu tienda (Configuración → Conectar tienda).", 401)
        return self.tn

    def cargar(self, forzar=False):
        with self.candado:
            if forzar or not self.cargado:
                tn = self.requiere_tn()
                self.productos = tn.productos()
                self.categorias = tn.categorias()
                self.cargado = time.time()
            return self.productos

    def caminos(self):
        return caminos_categorias(self.categorias)

    def reemplazar(self, p):
        with self.candado:
            self.productos = [p if x["id"] == p["id"] else x for x in self.productos]
            if not any(x["id"] == p["id"] for x in self.productos):
                self.productos.append(p)

    def quitar(self, pid):
        with self.candado:
            self.productos = [x for x in self.productos if x["id"] != pid]


def crear_app():
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = 80 * 1024 * 1024
    app.config["JSON_AS_ASCII"] = False
    clave = secrets.token_urlsafe(24)
    app.config["CLAVE"] = clave
    est = Estado()
    temporales = Path(tempfile.gettempdir()) / f"{NOMBRE.lower()}-subidas"
    temporales.mkdir(exist_ok=True)

    # ------------------------------------------------------------ seguridad
    @app.before_request
    def controlar():
        permitido = app.config.get("HOST_PERMITIDO")
        if permitido and request.host != permitido:
            abort(403)
        if request.path.startswith("/api/") and request.headers.get("X-Clave") != clave:
            abort(403)

    @app.errorhandler(ErrorApi)
    def error_api(e):
        return jsonify(error=str(e), detalle=e.detalle), 401 if e.codigo == 401 else 502

    @app.errorhandler(ValueError)
    def error_valor(e):
        return jsonify(error=str(e)), 400

    @app.errorhandler(413)
    def muy_grande(_e):
        return jsonify(error="El archivo es demasiado grande (máximo 80 MB)."), 413

    def cuerpo():
        return request.get_json(silent=True) or {}

    def tarea_json(t):
        return jsonify(tarea=t.id)

    # ------------------------------------------------------------ la pagina
    @app.get("/")
    def inicio():
        html = (carpeta_web() / "index.html").read_text(encoding="utf-8")
        html = html.replace("{{CLAVE}}", clave).replace("{{VERSION}}", VERSION).replace("{{NOMBRE}}", NOMBRE)
        return html, 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}

    @app.get("/web/<path:archivo>")
    def estaticos(archivo):
        r = send_from_directory(carpeta_web(), archivo)
        r.headers["Cache-Control"] = "no-store"
        return r

    # ------------------------------------------------------------ conexion
    @app.get("/api/estado")
    def estado():
        if est.tn and not (est.tienda or {}).get("nombre"):
            # conexion vieja o por variables de entorno: completar el nombre una vez
            try:
                info = est.tn.tienda()
                nom = info.get("name")
                est.tienda = {**est.tienda, "nombre": (nom.get("es") if isinstance(nom, dict) else nom) or "",
                              "url": info.get("url_with_protocol") or est.tienda.get("url", "")}
            except ErrorApi:
                pass
        return jsonify(nombre=NOMBRE, version=VERSION, conectado=bool(est.tn),
                       tienda={k: v for k, v in (est.tienda or {}).items() if k != "token"},
                       cargado=bool(est.cargado), carpeta_datos=str(config.carpeta_datos()))

    def guardar_conexion(tienda_id, token):
        tn = Tiendanube(tienda_id, token)
        info = tn.tienda()          # valida el token de paso
        datos = {"id": str(tienda_id), "token": token,
                 "nombre": (info.get("name") or {}).get("es") if isinstance(info.get("name"), dict)
                 else info.get("name") or "",
                 "url": info.get("url_with_protocol") or (f"https://{info['original_domain']}"
                                                          if info.get("original_domain") else ""),
                 "email": info.get("email") or "", "conectada": datetime.now().isoformat(timespec="seconds")}
        config.guardar_tienda(datos)
        with est.candado:
            est.tn, est.tienda = tn, datos
            est.productos, est.categorias, est.cargado = [], [], 0.0
        return jsonify(ok=True, tienda={k: v for k, v in datos.items() if k != "token"})

    @app.post("/api/conexion/token")
    def conectar_token():
        d = cuerpo()
        tid, token = str(d.get("tienda_id") or "").strip(), str(d.get("token") or "").strip()
        if not tid.isdigit() or not token:
            raise ValueError("Completá el número de tienda (solo números) y el token.")
        return guardar_conexion(tid, token)

    @app.post("/api/conexion/link")
    def conectar_link():
        app_id = str(cuerpo().get("app_id") or "").strip()
        if not app_id.isdigit():
            raise ValueError("El App ID son solo números.")
        return jsonify(url=link_autorizar(app_id))

    @app.post("/api/conexion/codigo")
    def conectar_codigo():
        d = cuerpo()
        tid, token = canjear_codigo(d.get("app_id", ""), d.get("secret", ""), d.get("codigo", ""))
        return guardar_conexion(tid, token)

    @app.post("/api/conexion/salir")
    def desconectar():
        config.olvidar_tienda()
        with est.candado:
            est.tn = est.tienda = None
            est.productos, est.categorias, est.cargado = [], [], 0.0
        return jsonify(ok=True)

    # ------------------------------------------------------------ productos
    def paquete_productos():
        caminos = est.caminos()
        return {
            "productos": [resumen(p, caminos) for p in est.productos],
            "categorias": sorted(({"id": i, "camino": c} for i, c in caminos.items()), key=lambda x: x["camino"]),
            "marcas": sorted({p.get("brand") or "" for p in est.productos} - {""}, key=str.lower),
            "actualizado": datetime.fromtimestamp(est.cargado).strftime("%H:%M") if est.cargado else "",
        }

    @app.get("/api/productos")
    def listar_productos():
        est.cargar(forzar=request.args.get("recargar") == "1")
        return jsonify(paquete_productos())

    @app.get("/api/inicio")
    def panel():
        est.cargar(forzar=request.args.get("recargar") == "1")
        rs = [resumen(p) for p in est.productos]
        return jsonify(
            total=len(rs),
            publicados=sum(r["publicado"] for r in rs),
            ocultos=sum(not r["publicado"] for r in rs),
            variantes=sum(len(r["variantes"]) for r in rs),
            sin_precio=sum(r["sin_precio"] for r in rs),
            sin_fotos=sum(r["fotos"] == 0 for r in rs),
            sin_stock=sum(r["sin_stock"] for r in rs),
            sin_categoria=sum(r["sin_categoria"] for r in rs),
            sin_descripcion=sum(r["sin_descripcion"] for r in rs),
            marcas=len({r["marca"] for r in rs if r["marca"]}),
            ultimos_respaldos=respaldos.listar()[:3],
            actualizado=datetime.fromtimestamp(est.cargado).strftime("%H:%M") if est.cargado else "",
        )

    @app.put("/api/productos/<int:pid>")
    def guardar_producto(pid):
        tn = est.requiere_tn()
        d = cuerpo()
        p = tn.producto(pid)
        variantes = {v["id"]: v for v in p.get("variants") or []}
        cambio = {}
        if d.get("nombre") is not None and d["nombre"].strip() and d["nombre"].strip() != nombre(p):
            cambio["name"] = {**(p.get("name") or {}), "es": d["nombre"].strip()}
        if d.get("marca") is not None and d["marca"].strip() != (p.get("brand") or ""):
            cambio["brand"] = d["marca"].strip()
        if d.get("publicado") is not None and bool(d["publicado"]) != bool(p.get("published")):
            cambio["published"] = bool(d["publicado"])
        if cambio:
            tn.put(f"products/{pid}", cambio)
        for dv in d.get("variantes") or []:
            v = variantes.get(int(dv["id"]))
            if not v:
                continue
            b = {}
            if "precio" in dv:
                x = numero(dv["precio"]) if dv["precio"] not in (None, "") else None
                if x is None or x < 0:
                    raise ValueError(f"Precio inválido en la variante {dv['id']}.")
                b["price"] = x
            if "promocional" in dv:
                x = numero(dv["promocional"]) if dv["promocional"] not in (None, "") else None
                b["promotional_price"] = x
            if "sku" in dv:
                b["sku"] = str(dv["sku"] or "").strip()
            if "stock" in dv:
                s = dv["stock"]
                b.update(cuerpo_stock(v, None if s in (None, "", "∞") else int(numero(s))))
            if b:
                tn.actualizar_variante(pid, v["id"], b)
        nuevo = tn.producto(pid)
        est.reemplazar(nuevo)
        return jsonify(producto=resumen(nuevo, est.caminos()))

    @app.post("/api/productos")
    def crear_producto():
        tn = est.requiere_tn()
        d = json.loads(request.form.get("datos") or "{}")
        archivos = request.files.getlist("fotos")
        nom = (d.get("nombre") or "").strip()
        if not nom:
            raise ValueError("Falta el nombre del producto.")
        desplegables = [x for x in d.get("desplegables") or [] if x.get("nombre") and x.get("valores")][:3]
        variantes = []
        for v in d.get("variantes") or [{"valores": []}]:
            x = {"values": [{"es": str(val)} for val in v.get("valores") or []]}
            try:
                x["price"] = numero(v.get("precio")) if v.get("precio") not in (None, "") else None
            except ValueError:
                raise ValueError(f"No entendí el precio «{v.get('precio')}».") from None
            s = v.get("stock")
            x["stock"] = None if s in (None, "", "∞") else int(numero(s))
            if v.get("sku"):
                x["sku"] = str(v["sku"]).strip()
            variantes.append(x)
        if len(variantes) > 1000:
            raise ValueError("Tiendanube acepta hasta 1000 variantes por producto.")
        cats = set()
        padres = {c["id"]: c.get("parent") for c in est.categorias}
        for cid in d.get("categorias") or []:
            cid = int(cid)
            while cid and cid not in cats:
                cats.add(cid)
                cid = padres.get(cid)
        desc = (d.get("descripcion") or "").strip()
        if desc and not desc.startswith("<"):
            desc = "".join(f"<p>{x.strip()}</p>".replace("\n", "<br>") for x in desc.split("\n\n") if x.strip())
        cuerpo_p = {"name": {"es": nom}, "description": {"es": desc}, "published": bool(d.get("publicado")),
                    "brand": (d.get("marca") or "").strip(), "tags": (d.get("tags") or "").strip(),
                    "categories": sorted(cats), "variants": variantes}
        if desplegables:
            cuerpo_p["attributes"] = [{"es": x["nombre"]} for x in desplegables]
        fotos_datos = [(f.filename or "foto.jpg", f.read()) for f in archivos]

        def trabajo(t):
            t.avance(0, 1 + len(fotos_datos), "Creando el producto…")
            p = tn.post("products", cuerpo_p)
            t.anotar(f"✓ Producto creado: {nombre(p)}")
            malas = []
            for pos, (fn, datos) in enumerate(fotos_datos, 1):
                t.avance(pos, 1 + len(fotos_datos), f"Subiendo foto {pos} de {len(fotos_datos)}…")
                try:
                    fotos.subir(tn, p["id"], datos, fn, posicion=pos)
                    t.anotar(f"✓ Foto {pos}: {fn}")
                except Exception as e:      # noqa: BLE001  (una foto rota no frena el resto)
                    malas.append(f"{fn}: {e}")
                    t.anotar(f"✗ Foto {pos}: {fn}: {e}")
            nuevo = tn.producto(p["id"])
            est.reemplazar(nuevo)
            return {"producto": resumen(nuevo, est.caminos()), "errores": malas}
        return tarea_json(tareas.lanzar(f"Crear «{nom}»", trabajo))

    @app.post("/api/masivo")
    def masivo():
        tn = est.requiere_tn()
        d = cuerpo()
        accion = d.get("accion")
        ids = [int(i) for i in d.get("ids") or []]
        if not ids:
            raise ValueError("No elegiste ningún producto.")
        por_id = {p["id"]: p for p in est.productos}
        elegidos = [por_id[i] for i in ids if i in por_id]
        titulos = {"publicar": "Publicar", "ocultar": "Ocultar", "infinito": "Stock infinito",
                   "precio": "Ajustar precios", "borrar": "Borrar productos"}
        if accion not in titulos:
            raise ValueError("Acción desconocida.")
        pct = float(d.get("pct") or 0)
        paso = float(d.get("redondeo") or 0)

        def trabajo(t):
            resp = None
            if accion in ("precio", "borrar", "infinito"):
                t.avance(0, len(elegidos), "Guardando respaldo…")
                frescos = [tn.producto(p["id"]) for p in elegidos]
                resp = respaldos.crear(frescos, f"antes de {titulos[accion].lower()}")
                t.anotar(f"Respaldo guardado: {resp['nombre']}")
            hechos, errores = 0, []
            for i, p in enumerate(elegidos, 1):
                if t.cancelada:
                    break
                t.avance(i - 1, len(elegidos), nombre(p))
                try:
                    if accion in ("publicar", "ocultar"):
                        quiero = accion == "publicar"
                        if bool(p.get("published")) != quiero:
                            tn.put(f"products/{p['id']}", {"published": quiero})
                    elif accion == "infinito":
                        for v in p.get("variants") or []:
                            if not (v.get("stock_management") is False or v.get("stock") in (None, "")):
                                tn.actualizar_variante(p["id"], v["id"], cuerpo_stock(v, None))
                    elif accion == "precio":
                        for v in p.get("variants") or []:
                            if precio(v) > 0:
                                nuevo = precios.redondear(precio(v) * (1 + pct / 100), paso or 0.01)
                                tn.actualizar_variante(p["id"], v["id"], {"price": nuevo})
                    elif accion == "borrar":
                        tn.delete(f"products/{p['id']}")
                    hechos += 1
                    t.anotar(f"✓ {nombre(p)}")
                except Exception as e:      # noqa: BLE001
                    errores.append(f"{nombre(p)}: {e}")
                    t.anotar(f"✗ {nombre(p)}: {e}")
            t.avance(len(elegidos), len(elegidos), "Actualizando la lista…")
            for p in elegidos:
                if accion == "borrar":
                    est.quitar(p["id"])
                else:
                    try:
                        est.reemplazar(tn.producto(p["id"]))
                    except ErrorApi:
                        est.quitar(p["id"])
            return {"hechos": hechos, "errores": errores, "respaldo": resp["nombre"] if resp else None}
        return tarea_json(tareas.lanzar(f"{titulos[accion]} ({len(elegidos)})", trabajo))

    # ------------------------------------------------------------ precios
    def guardar_subida(archivo, permitidas):
        if not archivo or not archivo.filename:
            raise ValueError("No llegó ningún archivo.")
        ext = Path(archivo.filename).suffix.lower()
        if ext not in permitidas:
            raise ValueError(f"Formato no soportado ({ext or 'sin extensión'}). Usá: {', '.join(permitidas)}.")
        ruta = temporales / f"{uuid.uuid4().hex[:10]}{ext}"
        archivo.save(ruta)
        return ruta

    @app.post("/api/precios/archivo")
    def subir_lista():
        f = request.files.get("archivo")
        ruta = guardar_subida(f, (".xlsx", ".xlsm", ".csv", ".txt", ".tsv", ".pdf", ".xls"))
        doc = precios.leer(ruta)
        if not doc["hojas"] and not doc["lineas"]:
            raise ValueError("No pude leer nada de ese archivo. Si es un PDF escaneado (una foto), "
                             "no tiene texto para leer.")
        lid = uuid.uuid4().hex[:10]
        est.listas[lid] = {"ruta": ruta, "nombre": f.filename, "doc": doc}
        return jsonify(lista_id=lid, nombre=f.filename, **precios.muestra(doc))

    @app.post("/api/precios/vista")
    def vista_precios():
        d = cuerpo()
        lista = est.listas.get(d.get("lista_id"))
        if not lista:
            raise ValueError("La lista ya no está cargada. Volvé a subir el archivo.")
        productos = est.cargar()
        marca = d.get("marca") or None
        por = d.get("por") or "sku"
        if d.get("modo") == "buscar":
            claves = set()
            for p in productos:
                if marca and (p.get("brand") or "").lower() != marca.lower():
                    continue
                if por == "sku":
                    claves |= {v.get("sku") for v in p.get("variants") or [] if v.get("sku")}
                else:
                    claves.add(nombre(p))
            items = precios.items_de_texto(lista["doc"], sorted(claves, key=len, reverse=True))
        else:
            def col(k):
                return None if d.get(k) in (None, "") else int(d[k])
            if col("col_codigo") is None or col("col_precio") is None:
                raise ValueError("Elegí qué columna tiene el código y cuál el precio.")
            items = precios.items_de_columnas(lista["doc"], d.get("hoja"), col("col_codigo"), col("col_precio"),
                                              col("fila_encabezado"), col("col_desc"))
        regla = d.get("regla") or {}
        for k in ("multiplicador", "iva", "cotizacion", "redondeo"):
            if regla.get(k) not in (None, ""):
                regla[k] = numero(regla[k])
        regla["descuentos"] = [numero(x) for x in regla.get("descuentos") or [] if str(x).strip()]
        vista = precios.vista_previa(productos, items, regla, por=por, marca=marca,
                                     no_bajar=bool(d.get("no_bajar")))
        vid = uuid.uuid4().hex[:10]
        est.vistas[vid] = vista
        return jsonify(vista_id=vid, **vista)

    @app.post("/api/precios/aplicar")
    def aplicar_precios():
        tn = est.requiere_tn()
        d = cuerpo()
        vista = est.vistas.get(d.get("vista_id"))
        if not vista:
            raise ValueError("La vista previa venció. Volvé a generarla.")
        claves = set(d.get("claves") or [])
        elegidos = [c for c in vista["cambios"] if c["clave"] in claves and c["estado"] != "igual"]
        if not elegidos:
            raise ValueError("No hay ningún cambio elegido.")

        def trabajo(t):
            r = precios.aplicar(tn, elegidos, t)
            est.cargar(forzar=True)
            return r
        return tarea_json(tareas.lanzar(f"Actualizar {len(elegidos)} precios", trabajo))

    # ------------------------------------------------------------ excel
    @app.post("/api/excel/exportar")
    def exportar_excel():
        productos = est.cargar(forzar=True)
        marca = cuerpo().get("marca") or None
        nombre_t = slug((est.tienda or {}).get("nombre") or "tienda", 30)
        ruta = config.carpeta_exportaciones() / f"{nombre_t}_{datetime.now():%Y-%m-%d_%H%M}" \
                                                f"{'_' + slug(marca, 20) if marca else ''}.xlsx"
        r = excel.exportar(productos, ruta, est.caminos(), marca)
        return jsonify(**r, carpeta=str(ruta.parent))

    @app.post("/api/excel/importar")
    def importar_excel():
        ruta = guardar_subida(request.files.get("archivo"), (".xlsx", ".xlsm"))
        productos = est.cargar(forzar=True)
        comp = excel.comparar(ruta, productos)
        iid = uuid.uuid4().hex[:10]
        est.planillas[iid] = comp
        return jsonify(importacion_id=iid, **comp)

    @app.post("/api/excel/aplicar")
    def aplicar_excel():
        tn = est.requiere_tn()
        d = cuerpo()
        comp = est.planillas.get(d.get("importacion_id"))
        if not comp:
            raise ValueError("La importación venció. Volvé a subir la planilla.")
        indices = set(int(i) for i in d.get("indices") or [])
        elegidos = [c for i, c in enumerate(comp["cambios"]) if i in indices]
        if not elegidos:
            raise ValueError("No hay ningún cambio elegido.")

        def trabajo(t):
            r = excel.aplicar(tn, elegidos, t)
            est.cargar(forzar=True)
            return r
        return tarea_json(tareas.lanzar(f"Importar planilla ({len(elegidos)} cambios)", trabajo))

    # ------------------------------------------------------------ respaldos
    @app.get("/api/respaldos")
    def listar_respaldos():
        return jsonify(respaldos=respaldos.listar(), carpeta=str(config.carpeta("respaldos")))

    @app.post("/api/respaldos")
    def crear_respaldo():
        tn = est.requiere_tn()

        def trabajo(t):
            t.avance(0, 0, "Leyendo todos los productos…")
            productos = tn.productos(al_avanzar=lambda n: t.avance(n, 0, f"{n} productos leídos…"))
            cats = tn.categorias()
            r = respaldos.crear(productos, "respaldo completo", cats, completo=True)
            t.anotar(f"✓ {r['productos']} productos y {r['variantes']} variantes guardados.")
            return r
        return tarea_json(tareas.lanzar("Copia de seguridad", trabajo))

    @app.post("/api/respaldos/borrar")
    def borrar_respaldo():
        respaldos.borrar(cuerpo().get("nombre", ""))
        return jsonify(ok=True)

    # ------------------------------------------------------------ tareas
    @app.get("/api/tareas/<tid>")
    def ver_tarea(tid):
        t = tareas.buscar(tid)
        if not t:
            return jsonify(error="Esa tarea ya no existe."), 404
        return jsonify(t.como_dict(int(request.args.get("desde") or 0)))

    @app.post("/api/tareas/<tid>/cancelar")
    def cancelar_tarea(tid):
        tareas.cancelar(tid)
        return jsonify(ok=True)

    # ------------------------------------------------------------ abrir cosas
    @app.post("/api/abrir")
    def abrir():
        d = cuerpo()
        destino = d.get("ruta") or ""
        if destino.startswith("https://"):
            webbrowser.open(destino)
            return jsonify(ok=True)
        ruta = Path(destino).resolve()
        permitidas = [config.carpeta_exportaciones().resolve(), config.carpeta_datos().resolve()]
        if not any(ruta == b or b in ruta.parents for b in permitidas) or not ruta.exists():
            raise ValueError("No se puede abrir esa ubicación.")
        if d.get("carpeta") and ruta.is_file():
            ruta = ruta.parent
        if hasattr(os, "startfile"):
            os.startfile(ruta)       # noqa: S606  (ruta validada arriba)
        else:
            webbrowser.open(ruta.as_uri())
        return jsonify(ok=True)

    return app


def arrancar(puerto=0):
    """Levanta el servidor en un hilo. Devuelve (servidor, url)."""
    # sin consola (el .exe) no hay donde escribir el registro de cada pedido
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")      # noqa: SIM115
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")      # noqa: SIM115
    app = crear_app()
    srv = make_server("127.0.0.1", puerto, app, threaded=True)
    app.config["HOST_PERMITIDO"] = f"127.0.0.1:{srv.server_port}"
    threading.Thread(target=srv.serve_forever, daemon=True, name="servidor").start()
    return srv, f"http://127.0.0.1:{srv.server_port}/"
