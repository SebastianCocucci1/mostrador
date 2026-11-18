"""
Para desarrollar: abre Mostrador desde el codigo fuente, con consola.

    python main.py                 abre la pagina en el navegador
    python main.py --puerto 8765   en otro puerto (para no chocar con uno instalado)

Es lo mismo que Mostrador.pyw (que es lo que abre el acceso directo instalado).
"""

import sys

from mostrador.app import main

if __name__ == "__main__":
    sys.exit(main())
