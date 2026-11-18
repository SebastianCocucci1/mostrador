"""Pruebas del actualizador automatico y del arranque, sin conectarse a GitHub."""

import hashlib
import io
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mostrador import arranque  # noqa: E402
from mostrador.actualizador import Actualizador, es_mas_nueva, version_a_tupla  # noqa: E402


def armar_zip(archivos: dict) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for nombre, contenido in archivos.items():
            z.writestr(nombre, contenido)
    return buffer.getvalue()


def paquete_app(version="1.5", marca="libA"):
    return armar_zip({"Mostrador.pyw": f"# v{version}", "mostrador/__init__.py": f'VERSION = "{version}"',
                      "web/index.html": "<html>", "lib.txt": marca})


PAQUETE = paquete_app()
LIB_B = armar_zip({"lib.txt": "libB", "flask/__init__.py": "# flask nuevo"})


def release(version="v1.5", con_sha=True, con_lib=True):
    activos = [{"name": "Mostrador-app.zip", "browser_download_url": "https://x/app"}]
    if con_sha:
        activos.append({"name": "Mostrador-app.zip.sha256", "browser_download_url": "https://x/app.sha"})
    if con_lib:
        activos += [{"name": "Mostrador-lib.zip", "browser_download_url": "https://x/lib"},
                    {"name": "Mostrador-lib.zip.sha256", "browser_download_url": "https://x/lib.sha"}]
    return {"tag_name": version, "assets": activos}


# ------------------------------------------------------------- versiones

def test_parseo():
    assert version_a_tupla("v1.12") == (1, 12)
    assert version_a_tupla("1.2") == (1, 2)
    assert version_a_tupla("0.0-dev") is None


def test_comparacion_numerica():
    assert es_mas_nueva("1.10", "1.9")          # 10 > 9, no comparacion de texto
    assert not es_mas_nueva("1.9", "1.10")
    assert not es_mas_nueva("1.5", "1.5")
    assert not es_mas_nueva("1.5", "0.0-dev")   # en desarrollo no se actualiza


# ------------------------------------------------------------- instalacion

class Caso:
    def __init__(self, raiz: Path):
        self.raiz = raiz
        app = raiz / "app"
        (app / "mostrador").mkdir(parents=True)
        (app / "Mostrador.pyw").write_text("# v1.4")
        (app / "lib.txt").write_text("libA")
        (raiz / "lib").mkdir()
        (raiz / "lib" / "lib.txt").write_text("libA")
        self.reinicios = []
        self.ocupado = False

    def crear(self, datos=None, app=PAQUETE, lib=LIB_B, sha_app=None, version="1.4",
              automatica=True, raiz="usar"):
        archivos = {"https://x/app": app, "https://x/lib": lib}
        shas = {"https://x/app.sha": sha_app or hashlib.sha256(app).hexdigest(),
                "https://x/lib.sha": hashlib.sha256(lib).hexdigest()}
        return Actualizador(
            version, "dueno/repo", 15, automatica,
            al_instalar=lambda: self.reinicios.append(True),
            raiz=self.raiz if raiz == "usar" else raiz,
            ocupado=lambda: self.ocupado,
            obtener_json=lambda url: datos or release(),
            descargar=lambda url, destino: destino.write_bytes(archivos[url]),
            obtener_texto=lambda url: f"{shas[url]}  archivo.zip",
        )

    def entrada(self):
        return (self.raiz / "app" / "Mostrador.pyw").read_text()


@pytest.fixture
def caso(tmp_path):
    return Caso(tmp_path)


def test_instala_version_nueva(caso):
    a = caso.crear()
    a.revisar()
    assert a.estado.estado == "reiniciando", a.estado.mensaje
    assert caso.entrada() == "# v1.5"
    assert (caso.raiz / "app.old" / "Mostrador.pyw").read_text() == "# v1.4"
    assert not (caso.raiz / "app.new").exists()
    assert not (caso.raiz / "app.new.zip").exists()
    assert not (caso.raiz / "lib.new").exists()      # mismas librerias: no las baja
    assert caso.reinicios == [True]


def test_librerias_nuevas_quedan_en_lib_new(caso):
    a = caso.crear(app=paquete_app(marca="libB"))
    a.revisar()
    assert a.estado.estado == "reiniciando", a.estado.mensaje
    assert (caso.raiz / "lib.new" / "lib.txt").read_text() == "libB"
    assert (caso.raiz / "lib" / "lib.txt").read_text() == "libA"   # las cambia el arranque
    assert not (caso.raiz / "lib.new.zip").exists()


def test_librerias_que_no_coinciden_no_instala(caso):
    a = caso.crear(app=paquete_app(marca="libC"))           # pide libC y el release trae libB
    a.revisar()
    assert a.estado.estado == "error"
    assert caso.entrada() == "# v1.4"
    assert not (caso.raiz / "lib.new").exists()


def test_faltan_librerias_publicadas_no_instala(caso):
    a = caso.crear(datos=release(con_lib=False), app=paquete_app(marca="libB"))
    a.revisar()
    assert a.estado.estado == "error"
    assert caso.entrada() == "# v1.4"


def test_sha_distinto_no_instala(caso):
    a = caso.crear(sha_app="0" * 64)
    a.revisar()
    assert a.estado.estado == "error"
    assert caso.entrada() == "# v1.4"
    assert not (caso.raiz / "app.new.zip").exists()
    assert caso.reinicios == []


def test_paquete_incompleto_no_instala(caso):
    a = caso.crear(app=armar_zip({"LEEME.txt": "nada"}))
    a.revisar()
    assert a.estado.estado == "error"
    assert "incompleto" in a.estado.mensaje
    assert caso.entrada() == "# v1.4"
    assert not (caso.raiz / "app.new").exists()


def test_zip_con_rutas_peligrosas_no_instala(caso):
    malicioso = armar_zip({"../fuera.txt": "x", "Mostrador.pyw": "x", "mostrador/a.py": "",
                           "web/index.html": ""})
    a = caso.crear(app=malicioso)
    a.revisar()
    assert a.estado.estado == "error"
    assert not (caso.raiz / "fuera.txt").exists()
    assert caso.entrada() == "# v1.4"


def test_sin_archivo_sha_no_instala(caso):
    a = caso.crear(datos=release(con_sha=False))
    a.revisar()
    assert a.estado.estado == "error"
    assert caso.entrada() == "# v1.4"


def test_al_dia(caso):
    a = caso.crear(datos=release("v1.4"))
    a.revisar()
    assert a.estado.estado == "al_dia"
    assert caso.reinicios == []


def test_manual_solo_avisa(caso):
    a = caso.crear(automatica=False)
    a.revisar()
    assert a.estado.estado == "disponible"
    assert a.estado.version_disponible == "1.5"
    assert caso.entrada() == "# v1.4"


def test_pedido_a_mano_instala_aunque_no_sea_automatica(caso):
    a = caso.crear(automatica=False)
    a.revisar(instalar=True)
    assert a.estado.estado == "reiniciando"
    assert caso.entrada() == "# v1.5"


def test_con_un_trabajo_en_curso_espera(caso):
    caso.ocupado = True
    a = caso.crear()
    a.revisar()
    assert a.estado.estado == "disponible"
    assert "cuando termine" in a.estado.mensaje
    assert caso.entrada() == "# v1.4"
    caso.ocupado = False
    a.revisar()
    assert a.estado.estado == "reiniciando"


def test_desde_codigo_fuente_no_instala(caso):
    a = caso.crear(raiz=None)
    a.revisar()
    assert a.estado.estado == "disponible"
    assert caso.entrada() == "# v1.4"


def test_github_caido(caso):
    a = caso.crear()

    def falla(url):
        raise OSError("sin internet")
    a._obtener_json = falla
    a.revisar()
    assert a.estado.estado == "error"
    assert caso.entrada() == "# v1.4"


def test_limpia_restos(caso):
    a = caso.crear()
    (caso.raiz / "app.old" / "x").mkdir(parents=True)
    (caso.raiz / "app.new.zip").write_bytes(b"resto")
    (caso.raiz / "lib.new").mkdir()
    a.limpiar_restos()
    assert not (caso.raiz / "app.old").exists()
    assert not (caso.raiz / "app.new.zip").exists()
    assert (caso.raiz / "app").exists()
    assert (caso.raiz / "lib.new").exists()      # esa la cambia el arranque


# ------------------------------------------------------------- arranque

def test_arranque_pone_librerias_nuevas(caso, monkeypatch):
    (caso.raiz / "lib.new").mkdir()
    (caso.raiz / "lib.new" / "lib.txt").write_text("libB")
    monkeypatch.setattr(arranque, "APP", caso.raiz / "app")
    monkeypatch.setattr(arranque, "RAIZ", caso.raiz)
    assert "nuevas" in arranque.poner_librerias_nuevas()
    assert (caso.raiz / "lib" / "lib.txt").read_text() == "libB"
    assert not (caso.raiz / "lib.new").exists()
    assert not (caso.raiz / "lib.old").exists()


def test_arranque_sin_nada_que_hacer(caso, monkeypatch):
    monkeypatch.setattr(arranque, "APP", caso.raiz / "app")
    monkeypatch.setattr(arranque, "RAIZ", caso.raiz)
    assert arranque.poner_librerias_nuevas() == ""
    assert (caso.raiz / "lib" / "lib.txt").read_text() == "libA"
