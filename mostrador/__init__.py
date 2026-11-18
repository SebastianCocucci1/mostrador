"""
Mostrador: gestor de productos para tiendas Tiendanube.

El nombre, la version, el repositorio de las actualizaciones y el puerto
viven aca y en ningun otro lado. Este archivo usa solo la libreria estandar:
lo importa el arranque antes de que esten disponibles las librerias de lib\\.

La VERSION la pone el workflow de GitHub al armar el paquete ("1.<n>").
Corriendo desde el codigo fuente queda "0.0-dev", que nunca se actualiza sola.
"""

NOMBRE = "Mostrador"
VERSION = "0.0-dev"
REPO = "SebastianCocucci1/mostrador"     # de donde se bajan las actualizaciones (Releases)
PUERTO = 8642                            # fijo: asi una segunda copia encuentra a la primera
