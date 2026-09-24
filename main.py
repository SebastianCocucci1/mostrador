"""
Arranca Mostrador: el servidor local y la ventana.

    python main.py              abre la ventana de la app
    python main.py --navegador  la abre en el navegador (para desarrollo)
    python main.py --puerto 8765

Si la ventana nativa no se puede abrir (falta WebView2 en Windows viejos),
abre el navegador de siempre.
"""

import argparse
import sys
import time
import webbrowser

from mostrador import NOMBRE, VERSION, config
from mostrador.servidor import arrancar


def main():
    ap = argparse.ArgumentParser(description=f"{NOMBRE} {VERSION}")
    ap.add_argument("--navegador", action="store_true", help="abrir en el navegador en vez de en una ventana")
    ap.add_argument("--puerto", type=int, default=0, help="puerto fijo (por defecto, uno libre)")
    args = ap.parse_args()

    srv, url = arrancar(args.puerto)

    if not args.navegador:
        try:
            import webview
            webview.create_window(NOMBRE, url, width=1360, height=880, min_size=(1040, 680),
                                  background_color="#F6F7F9", text_select=True)
            # private_mode=False: que recuerde el tema y el ultimo calculo de precios
            webview.start(private_mode=False, storage_path=str(config.carpeta("navegador")))
            srv.shutdown()
            return 0
        except Exception as e:       # noqa: BLE001  (sin ventana nativa, va el navegador)
            print(f"No pude abrir la ventana ({e}); abro el navegador.", file=sys.stderr)

    print(f"{NOMBRE} corriendo en {url}  (Ctrl+C para cerrar)")
    webbrowser.open(url)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        srv.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
