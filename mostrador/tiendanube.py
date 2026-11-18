"""
Cliente de la API de Tiendanube.

COSAS QUE NO SON OBVIAS (aprendidas a los golpes)
    - El header de autenticacion es "Authentication: bearer <token>". Se manda
      tambien "Authorization" por si algun dia lo unifican.
    - La API corta con 429 si le pegas rapido (balde de 40 pedidos que se
      vacia a 2 por segundo). Se mira x-rate-limit-remaining y se espera.
    - La ultima pagina + 1 devuelve 404 "Last page is N", no una lista vacia.
    - El canje del codigo OAuth devuelve los errores con HTTP 200 y un campo
      "error".
"""

import re
import time
from urllib.parse import parse_qs, urlparse

import requests

from . import NOMBRE, VERSION

API = "https://api.tiendanube.com/v1/{tienda}/"
AUTORIZAR = "https://www.tiendanube.com/apps/{app_id}/authorize"
CANJE = "https://www.tiendanube.com/apps/authorize/token"
POR_PAGINA = 200


class ErrorApi(Exception):
    """Un error de la API explicado para una persona, no para un programador."""

    def __init__(self, mensaje, codigo=None, detalle=""):
        super().__init__(mensaje)
        self.codigo = codigo
        self.detalle = detalle


def _explicar(r, metodo, ruta):
    try:
        d = r.json()
    except ValueError:
        d = {}
    detalle = d.get("description") or d.get("message") or r.text[:300]
    if r.status_code == 401:
        return ErrorApi("La tienda rechazó la conexión: el token no es válido o la aplicación "
                        "se desinstaló. Volvé a conectar la tienda desde Configuración.", 401, detalle)
    if r.status_code == 403:
        return ErrorApi("La aplicación no tiene permiso para hacer esto. Revisá que tenga "
                        "permisos de lectura y escritura de productos.", 403, detalle)
    if r.status_code == 404:
        return ErrorApi("No se encontró lo que se buscaba en la tienda (puede que se haya borrado).",
                        404, detalle)
    if r.status_code == 422:
        errores = []
        for campo, msgs in (d.items() if isinstance(d, dict) else []):
            if campo in ("code", "message", "description"):
                continue
            errores.append(f"{campo}: {', '.join(map(str, msgs)) if isinstance(msgs, list) else msgs}")
        return ErrorApi("La tienda no aceptó los datos: " + ("; ".join(errores) or detalle), 422, detalle)
    if r.status_code >= 500:
        return ErrorApi("Tiendanube no responde bien en este momento. Probá de nuevo en unos minutos.",
                        r.status_code, detalle)
    return ErrorApi(f"Error {r.status_code} en {metodo} {ruta}: {detalle}", r.status_code, detalle)


class Tiendanube:
    def __init__(self, tienda_id, token):
        self.tienda_id = str(tienda_id)
        self.base = API.format(tienda=self.tienda_id)
        self.s = requests.Session()
        self.s.headers.update({
            "Authentication": f"bearer {token}",
            "Authorization": f"Bearer {token}",
            "User-Agent": f"{NOMBRE}/{VERSION}",
            "Content-Type": "application/json",
        })

    # ------------------------------------------------------------ bajo nivel
    def pedido(self, metodo, ruta, **kw):
        """Devuelve la respuesta cruda, con reintentos por 429 y errores de red."""
        r = None
        for intento in range(6):
            try:
                r = self.s.request(metodo, self.base + ruta, timeout=60, **kw)
            except requests.RequestException as e:
                if intento == 5:
                    raise ErrorApi("No hay conexión con Tiendanube. Revisá internet y probá de nuevo.",
                                   detalle=str(e)) from e
                time.sleep(2 + intento * 2)
                continue
            if r.status_code == 429:
                time.sleep(2 + intento * 2)
                continue
            try:
                quedan = int(r.headers.get("x-rate-limit-remaining", "10"))
            except ValueError:
                quedan = 10
            if quedan <= 4:
                time.sleep(1.2)
            return r
        return r

    def api(self, metodo, ruta, **kw):
        """Como pedido(), pero devuelve el JSON y levanta ErrorApi si falla."""
        r = self.pedido(metodo, ruta, **kw)
        if not r.ok:
            raise _explicar(r, metodo, ruta)
        return r.json() if r.text else {}

    def get(self, ruta, **params):
        return self.api("GET", ruta, params=params or None)

    def put(self, ruta, cuerpo):
        return self.api("PUT", ruta, json=cuerpo)

    def post(self, ruta, cuerpo):
        return self.api("POST", ruta, json=cuerpo)

    def delete(self, ruta):
        return self.api("DELETE", ruta)

    # ---------------------------------------------------------- alto nivel
    def tienda(self):
        return self.get("store")

    def productos(self, al_avanzar=None):
        todos, pagina = [], 1
        while True:
            r = self.pedido("GET", "products", params={"page": pagina, "per_page": POR_PAGINA})
            if r.status_code == 404:
                break
            if not r.ok:
                raise _explicar(r, "GET", "products")
            lote = r.json()
            todos += lote
            if al_avanzar:
                al_avanzar(len(todos))
            if len(lote) < POR_PAGINA:
                break
            pagina += 1
        return todos

    def producto(self, pid):
        return self.get(f"products/{pid}")

    def categorias(self):
        todas, pagina = [], 1
        while True:
            r = self.pedido("GET", "categories", params={"page": pagina, "per_page": POR_PAGINA})
            if r.status_code == 404 or not r.ok:
                break
            lote = r.json()
            todas += lote
            if len(lote) < POR_PAGINA:
                break
            pagina += 1
        return todas

    def actualizar_variante(self, pid, vid, cuerpo):
        return self.put(f"products/{pid}/variants/{vid}", cuerpo)


# ------------------------------------------------------------- conexion

def limpiar_conexion(tienda_id, token):
    """Lo que pega la gente -> (tienda_id, token) limpios.

    Se aceptan como vengan de un mensaje o de un archivo:
        "Número de tienda: 1234567", "TN_STORE_ID=1234567", " 1234567 "
        "Token: abc123", "bearer abc123", "'abc123'", "TN_TOKEN=abc123"
    Y si en un campo pegaron el mensaje entero (con los dos datos), se
    separan solos.
    """
    tid, tok = str(tienda_id or "").strip(), str(token or "").strip()
    for texto in (tid, tok):
        m_id = re.search(r"(?:tienda|store[_ ]?id|user_id)\D{0,20}?(\d{3,})", texto, re.I)
        m_tok = re.search(r"(?:token|access_token)\W{0,10}(?:bearer\s+)?([A-Za-z0-9]{20,})", texto, re.I)
        if m_id and m_tok:
            return m_id.group(1), m_tok.group(1)
    digitos = re.findall(r"\d+", tid)
    tid = max(digitos, key=len) if digitos else ""
    tok = re.sub(r"(?i)^(tn_token\s*=|access_token\s*[:=]|token\s*(de acceso)?\s*[:=]?)", "", tok).strip()
    tok = re.sub(r"(?i)^bearer\s+", "", tok).strip().strip("'\"`").strip()
    return tid, tok


# ------------------------------------------------------------------ OAuth

def link_autorizar(app_id):
    return AUTORIZAR.format(app_id=str(app_id).strip())


def sacar_codigo(texto):
    """Acepta el codigo pelado o la URL entera a la que redirigio Tiendanube."""
    texto = (texto or "").strip()
    if not texto:
        return ""
    if texto.startswith("http"):
        return (parse_qs(urlparse(texto).query).get("code") or [""])[0]
    m = re.search(r"code=([^&\s]+)", texto)
    return m.group(1) if m else texto


def canjear_codigo(app_id, secret, codigo):
    """code -> (tienda_id, token). Levanta ErrorApi con una explicacion."""
    codigo = sacar_codigo(codigo)
    if not codigo:
        raise ErrorApi("No encontré ningún código en lo que pegaste. Copiá la dirección entera "
                       "de la barra del navegador después de autorizar.")
    try:
        r = requests.post(CANJE, json={"client_id": str(app_id).strip(), "client_secret": secret.strip(),
                                       "grant_type": "authorization_code", "code": codigo}, timeout=30)
    except requests.RequestException as e:
        raise ErrorApi("No hay conexión con Tiendanube. Revisá internet.", detalle=str(e)) from e
    try:
        d = r.json()
    except ValueError:
        d = {}
    if not r.ok or d.get("error"):
        err = d.get("error") or ""
        if err == "invalid_client":
            msg = "El App ID o el Client secret están mal copiados."
        elif err in ("invalid_grant", "invalid_request"):
            msg = ("Ese código ya se usó o venció (sirven una sola vez y por poco tiempo). "
                   "Volvé a abrir el link de autorización.")
        else:
            msg = "Tiendanube no aceptó el código: " + (d.get("error_description") or err or r.text[:200])
        raise ErrorApi(msg, r.status_code, str(d))
    if not d.get("access_token") or not d.get("user_id"):
        raise ErrorApi("La respuesta de Tiendanube no trajo el token.", detalle=str(d))
    return str(d["user_id"]), d["access_token"]
