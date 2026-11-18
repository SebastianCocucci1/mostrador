"""
Integracion con Windows: donde esta instalado, accesos directos y avisos.

El programa corre con el Python oficial (pythonw.exe, firmado por la Python
Software Foundation) y su codigo son archivos .py. No hay un .exe propio, para
que los antivirus no lo confundan con algo peligroso.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from . import NOMBRE

NOMBRE_ACCESO = NOMBRE
SIN_VENTANA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
APP = Path(__file__).resolve().parent.parent       # <raiz>\app (o la carpeta del codigo fuente)


def es_windows() -> bool:
    return os.name == "nt"


@dataclass(frozen=True)
class Instalacion:
    raiz: Path
    pythonw: Path
    script: Path
    icono: Path

    @property
    def comando(self) -> list[str]:
        return [str(self.pythonw), str(self.script)]


def instalacion() -> Instalacion | None:
    """Datos de la instalacion, o None si corre desde el codigo fuente."""
    raiz = APP.parent
    pythonw = raiz / "python" / "pythonw.exe"
    script = APP / "Mostrador.pyw"
    if APP.name != "app" or not pythonw.exists() or not script.exists():
        return None
    return Instalacion(raiz, pythonw, script, APP / "recursos" / "icono.ico")


def comando_actual() -> list[str]:
    """Como volver a abrir el programa (instalado o desde el codigo fuente)."""
    inst = instalacion()
    if inst:
        return inst.comando
    return [sys.executable, str(APP / "Mostrador.pyw")]


# ------------------------------------------------------------ accesos directos
def _ps(texto: str) -> str:
    return texto.replace("'", "''")


def hay_acceso_en_escritorio() -> bool:
    escritorio = Path(os.environ.get("USERPROFILE", "~")).expanduser() / "Desktop"
    return (escritorio / f"{NOMBRE_ACCESO}.lnk").exists()


def crear_accesos_directos() -> list[str]:
    """Crea 'Mostrador' en el escritorio y en el menu Inicio. Devuelve donde los creo."""
    inst = instalacion()
    if not es_windows() or not inst:
        return []
    script = f"""
$ws = New-Object -ComObject WScript.Shell
$destinos = @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))
foreach ($d in $destinos) {{
  if (-not $d) {{ continue }}
  $s = $ws.CreateShortcut((Join-Path $d '{_ps(NOMBRE_ACCESO)}.lnk'))
  $s.TargetPath = '{_ps(str(inst.pythonw))}'
  $s.Arguments = '"{_ps(str(inst.script))}"'
  $s.WorkingDirectory = '{_ps(str(inst.raiz))}'
  $s.IconLocation = '{_ps(str(inst.icono))}'
  $s.Description = 'Mostrador: gestioná los productos de tu tienda Tiendanube'
  $s.Save()
  Write-Output $d
}}
"""
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                       capture_output=True, text=True, timeout=60, creationflags=SIN_VENTANA)
    if r.returncode != 0:
        raise OSError(r.stderr.strip() or "No se pudieron crear los accesos directos")
    return [l for l in r.stdout.splitlines() if l.strip()]


# ------------------------------------------------------------ avisos
def aviso(titulo: str, mensaje: str, error: bool = True) -> None:
    """Ventana de aviso de Windows si no hay consola (pythonw); si hay, se escribe ahi."""
    consola = sys.stdout is not None and getattr(sys.stdout, "isatty", lambda: False)()
    if es_windows() and not consola:
        import ctypes
        icono = 0x10 if error else 0x40  # MB_ICONERROR / MB_ICONINFORMATION
        ctypes.windll.user32.MessageBoxW(None, mensaje, titulo, icono | 0x40000)  # MB_TOPMOST
    else:
        print(f"{titulo}: {mensaje}", file=sys.stderr)
