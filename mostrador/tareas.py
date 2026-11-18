"""
Trabajos largos (aplicar precios, respaldar, acciones masivas) corren en un
hilo aparte y la interfaz les pregunta como van.

    t = lanzar("Actualizar precios", trabajo)      trabajo(t) -> resultado

Dentro del trabajo:
    t.avance(12, 340, "VK-FAN R")    progreso y que esta haciendo
    t.anotar("algo para el registro")
    if t.cancelada: ...              el usuario apreto "Cancelar"
"""

import threading
import time
import traceback
import uuid

from .tiendanube import ErrorApi

_tareas = {}
_candado = threading.Lock()


class Tarea:
    def __init__(self, titulo):
        self.id = uuid.uuid4().hex[:12]
        self.titulo = titulo
        self.estado = "corriendo"       # corriendo | listo | error | cancelada
        self.hecho = 0
        self.total = 0
        self.texto = "Empezando…"
        self.registro = []
        self.resultado = None
        self.error = ""
        self.cancelada = False
        self.inicio = time.time()
        self.fin = None

    def avance(self, hecho, total=None, texto=None):
        self.hecho = hecho
        if total is not None:
            self.total = total
        if texto is not None:
            self.texto = texto

    def anotar(self, linea):
        self.registro.append(linea)
        if len(self.registro) > 2000:
            del self.registro[:500]

    def como_dict(self, desde=0):
        return {
            "id": self.id, "titulo": self.titulo, "estado": self.estado,
            "hecho": self.hecho, "total": self.total, "texto": self.texto,
            "registro": self.registro[desde:], "largo_registro": len(self.registro),
            "resultado": self.resultado, "error": self.error,
            "segundos": round((self.fin or time.time()) - self.inicio),
        }


def lanzar(titulo, trabajo):
    t = Tarea(titulo)
    with _candado:
        _tareas[t.id] = t
        # no guardar para siempre las viejas
        viejas = sorted((x for x in _tareas.values() if x.fin and time.time() - x.fin > 3600),
                        key=lambda x: x.fin)
        for x in viejas:
            _tareas.pop(x.id, None)

    def correr():
        try:
            t.resultado = trabajo(t)
            t.estado = "cancelada" if t.cancelada else "listo"
        except ErrorApi as e:
            t.estado, t.error = "error", str(e)
            t.anotar(f"Error: {e}")
        except Exception as e:       # noqa: BLE001  (se muestra en pantalla)
            t.estado, t.error = "error", f"Algo salió mal: {e}"
            t.anotar(traceback.format_exc())
        finally:
            t.fin = time.time()
    threading.Thread(target=correr, daemon=True, name=f"tarea-{t.id}").start()
    return t


def hay_en_curso():
    """Hay algun trabajo corriendo? (el actualizador espera a que terminen)."""
    with _candado:
        return any(t.estado == "corriendo" for t in _tareas.values())


def buscar(tid):
    return _tareas.get(tid)


def cancelar(tid):
    t = _tareas.get(tid)
    if t and t.estado == "corriendo":
        t.cancelada = True
        t.texto = "Cancelando… (termina lo que está haciendo)"
    return t
