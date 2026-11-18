"""
Punto de entrada de Mostrador.

Instalado, lo abre el acceso directo con el Python oficial, sin consola:
    python\\pythonw.exe app\\Mostrador.pyw

Desde el codigo fuente (con consola, para desarrollar):
    python Mostrador.pyw
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Primero, con la libreria estandar sola: si una actualizacion dejo librerias
# nuevas, ponerlas en su lugar antes de cargarlas (ver mostrador/arranque.py).
from mostrador import arranque  # noqa: E402

_pid = 0
if "--esperar" in sys.argv:
    try:
        _pid = int(sys.argv[sys.argv.index("--esperar") + 1])
    except (IndexError, ValueError):
        _pid = 0
_nota = arranque.poner_librerias_nuevas(_pid)

from mostrador.app import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(nota_arranque=_nota))
