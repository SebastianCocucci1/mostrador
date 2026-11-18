"""
GitHub falso para probar la actualizacion automatica en el workflow.

La primera consulta de "ultima version" anuncia la v99.0 (siempre mas nueva);
las siguientes anuncian la v0.1, para que el programa reiniciado quede al dia
y no entre en un ciclo de actualizaciones. Registra lo que le piden en un log.

Uso: python servidor_releases_falso.py APP_ZIP LIB_ZIP PUERTO RUTA_LOG
"""

import hashlib
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

app = Path(sys.argv[1]).read_bytes()
lib = Path(sys.argv[2]).read_bytes()
puerto = int(sys.argv[3])
log = Path(sys.argv[4])
consultas = {"n": 0}
ARCHIVOS = {"/app": app, "/lib": lib}
SHAS = {"/app.sha": (app, "Mostrador-app.zip"), "/lib.sha": (lib, "Mostrador-lib.zip")}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _enviar(self, cuerpo: bytes, tipo="application/octet-stream"):
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        with open(log, "a", encoding="utf-8") as f:
            f.write(self.path + "\n")
        base = f"http://127.0.0.1:{puerto}"
        if self.path == "/releases/latest":
            consultas["n"] += 1
            version = "v99.0" if consultas["n"] == 1 else "v0.1"
            datos = {"tag_name": version, "assets": [
                {"name": "Mostrador-app.zip", "browser_download_url": base + "/app"},
                {"name": "Mostrador-app.zip.sha256", "browser_download_url": base + "/app.sha"},
                {"name": "Mostrador-lib.zip", "browser_download_url": base + "/lib"},
                {"name": "Mostrador-lib.zip.sha256", "browser_download_url": base + "/lib.sha"},
            ]}
            self._enviar(json.dumps(datos).encode(), "application/json")
        elif self.path in ARCHIVOS:
            self._enviar(ARCHIVOS[self.path])
        elif self.path in SHAS:
            contenido, nombre = SHAS[self.path]
            self._enviar(f"{hashlib.sha256(contenido).hexdigest()}  {nombre}".encode())
        else:
            self.send_response(404)
            self.end_headers()


ThreadingHTTPServer(("127.0.0.1", puerto), H).serve_forever()
