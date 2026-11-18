#!/usr/bin/env python3
"""
Alta de un cliente: le saca a su tienda el numero y el token para que los
pegue en Mostrador. Es para VOS (el que vende la app), no va en el instalador:
usa el client secret de tu aplicacion de Tiendanube, que el cliente nunca ve.

    python vendedor/alta_cliente.py

1. Te da un mensaje con un link para mandarle al cliente.
2. El cliente lo abre logueado en su tienda, toca "Aceptar" y te manda la
   direccion a la que lo llevo (una pagina que no carga: es normal).
3. Pegas esa direccion aca y te da el mensaje con su numero de tienda y su
   token, listo para mandarle. El lo pega en Mostrador y queda conectado.

Si ya tenes la direccion:   python vendedor/alta_cliente.py --codigo "https://localhost/?code=..."

LA PRIMERA VEZ te pide el App ID y el Client secret de tu aplicacion
(partners.tiendanube.com -> tu app -> Claves de acceso) y los guarda en
vendedor/.env, que no se sube al repositorio. La aplicacion tiene que tener
URL de redireccion https://localhost/ y permisos de productos; el nombre
que le pongas es el que ve el cliente al aceptar ("Mostrador", por ejemplo).

Lleva un registro en vendedor/clientes.json (tienda, nombre, fecha), sin
los tokens: si un cliente pierde el suyo, se repite el alta.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))

from mostrador.tiendanube import ErrorApi, Tiendanube, canjear_codigo, link_autorizar  # noqa: E402

ENV = AQUI / ".env"
REGISTRO = AQUI / "clientes.json"


def leer_env():
    datos = {}
    if ENV.exists():
        for linea in ENV.read_text(encoding="utf-8").splitlines():
            if "=" in linea and not linea.lstrip().startswith("#"):
                k, v = linea.split("=", 1)
                datos[k.strip()] = v.strip()
    return datos


def claves_de_la_app():
    d = leer_env()
    app_id, secret = d.get("APP_ID", ""), d.get("CLIENT_SECRET", "")
    if app_id and secret:
        return app_id, secret
    print("Primera vez: necesito las claves de TU aplicacion de Tiendanube")
    print("(partners.tiendanube.com -> tu app -> Claves de acceso).\n")
    app_id = input("App ID: ").strip()
    secret = input("Client secret: ").strip()
    if not app_id.isdigit() or not secret:
        sys.exit("El App ID son solo numeros y el secret no puede estar vacio.")
    ENV.write_text(f"# claves de la app de Tiendanube: no compartir\nAPP_ID={app_id}\n"
                   f"CLIENT_SECRET={secret}\n", encoding="utf-8")
    print(f"Guardadas en {ENV}\n")
    return app_id, secret


def registrar(tid, info):
    clientes = json.loads(REGISTRO.read_text(encoding="utf-8")) if REGISTRO.exists() else {}
    nombre = info.get("name")
    clientes[tid] = {
        "nombre": nombre.get("es") if isinstance(nombre, dict) else (nombre or ""),
        "url": info.get("url_with_protocol") or "",
        "email": info.get("email") or "",
        "alta": datetime.now().isoformat(timespec="seconds"),
    }
    REGISTRO.write_text(json.dumps(clientes, ensure_ascii=False, indent=2), encoding="utf-8")
    return clientes[tid]


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description="Saca el numero de tienda y el token de un cliente.")
    ap.add_argument("--codigo", help="la direccion (o el code) que te mando el cliente")
    args = ap.parse_args()

    app_id, secret = claves_de_la_app()
    codigo = args.codigo
    if not codigo:
        link = link_autorizar(app_id)
        print("=" * 64)
        print(" 1) MANDALE ESTO AL CLIENTE")
        print("=" * 64)
        print(f"""
Hola! Para conectar Mostrador a tu tienda:

1. Entrá al panel de tu tienda Tiendanube (logueado como siempre).
2. Abrí este link y tocá "Aceptar":
   {link}
3. Te va a llevar a una página que no carga (es normal).
   Copiá la dirección de arriba del navegador y mandámela por acá.
""")
        print("=" * 64)
        print(" 2) CUANDO TE LA MANDE, PEGALA ACA")
        print("=" * 64)
        print("(canjeala apenas te llegue: el codigo vence enseguida y sirve una sola vez)\n")
        codigo = input("Direccion: ").strip()

    try:
        tid, token = canjear_codigo(app_id, secret, codigo)
        info = Tiendanube(tid, token).tienda()
    except ErrorApi as e:
        print(f"\nNo se pudo: {e}")
        print("Si el codigo vencio, pedile al cliente que vuelva a abrir el link y te mande la nueva direccion.")
        return 1

    datos = registrar(tid, info)
    print("\n" + "=" * 64)
    print(f" LISTO: {datos['nombre'] or 'tienda'} ({datos['url'] or tid})")
    print(" 3) MANDALE ESTO AL CLIENTE")
    print("=" * 64)
    print(f"""
¡Listo! Abrí Mostrador y pegá este mensaje entero en el primer campo:

Número de tienda: {tid}
Token: {token}

No le pases estos datos a nadie: con ellos se pueden cambiar los productos de tu tienda.
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
