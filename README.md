# Mostrador

**Gestor de productos para tiendas Tiendanube.** Una app de escritorio para Windows que hace en
minutos lo que en el panel de Tiendanube lleva horas: actualizar precios desde la lista del
proveedor, editar cientos de productos con Excel y cargar productos con variantes y fotos.

Todo se prueba antes de aplicar, y antes de cada cambio masivo se guarda un respaldo automático.

## Qué hace

| | |
|---|---|
| **Inicio** | Resumen de la tienda y lo que hay que revisar: productos sin precio, sin fotos, sin stock, sin categoría o sin descripción. |
| **Productos** | La tienda entera con búsqueda y filtros. Editar nombre, marca, precios, precio promocional, stock y SKU de cada variante. Acciones en masa: publicar, ocultar, stock infinito, ajustar precio en %, borrar. |
| **Nuevo producto** | Hasta 3 desplegables (color, tamaño…) con todas las combinaciones, precio y stock por variante, categorías y fotos arrastrando. La foto principal se sube cuadrada 1280×1280 para que la grilla de la tienda quede pareja. |
| **Actualizar precios** | Se sube la lista del proveedor (Excel, CSV o PDF) y se calcula el precio de venta con descuentos en cascada, margen, IVA, dólar y redondeo. Muestra qué sube, qué baja y cuánto, y avisa de los cambios sospechosos. |
| **Edición con Excel** | Exporta la tienda a una planilla, se edita en Excel y se vuelve a subir: muestra cada cambio antes de aplicarlo. |
| **Copias de seguridad** | Copia completa de la tienda cuando se quiera, más copias automáticas antes de cada cambio masivo. |

### Cómo lee las listas de precios

Cada proveedor arma su lista distinto, así que hay dos maneras de leerla:

- **Por columnas** (Excel, CSV, PDF con tablas): el usuario elige qué columna es el código y cuál
  el precio. La app detecta sola la fila de títulos y adivina las columnas.
- **Buscando los códigos en el texto** (catálogos en PDF sin tablas): se busca cada SKU de la
  tienda dentro del documento y se toma el precio que aparece al lado o en las líneas de abajo.
  En la revisión se ve el renglón exacto de donde salió cada precio.

Los códigos se comparan "compactos" (sin mayúsculas, espacios ni guiones): `VK - Fan 10`
encuentra a `vk-fan-10`.

## Para el usuario final

No necesita Python ni nada instalado: el paquete trae el Python oficial.

1. Bajar `Mostrador.zip` de la última versión en **Releases**. Antes de descomprimirlo: clic
   derecho > Propiedades > tildar **Desbloquear** > Aceptar.
2. Descomprimirlo en `C:\` (queda `C:\Mostrador`) y abrir **Abrir Mostrador**. Se abre la página
   en el navegador y aparece el ícono **Mostrador** en el escritorio y en el menú Inicio. De ahí
   en adelante se abre desde ese ícono (si ya está corriendo, solo vuelve a mostrar la página).
3. Pegar el **número de tienda** y el **token** que le mandó el vendedor (o el mensaje
   entero en un solo campo: se separan solos). La app los prueba, muestra el nombre de la tienda
   y queda conectada. La conexión no vence.

El zip trae un `LEEME.txt` con estos pasos.

Quien prefiera crear su propia aplicación de Tiendanube tiene el asistente de antes en
"Conexión avanzada".

## Alta de un cliente (para el vendedor)

Tiendanube no le da el token al comerciante: sale de autorizar una aplicación. Lo saca el
vendedor con su propia app de partners (distribución *para comerciantes específicos*, URL de
redirección `https://localhost/`, permisos de productos; el nombre es el que ve el cliente al
aceptar):

```
python vendedor/alta_cliente.py
```

Te da un mensaje con el link para mandarle al cliente; él acepta y te devuelve la dirección a la
que lo llevó; la pegás y te da el mensaje con su número de tienda y su token. La primera vez pide
el App ID y el Client secret y los guarda en `vendedor/.env`. `vendedor/` no va en el instalador
y ni `.env` ni `clientes.json` van al repositorio.

La conexión, los respaldos y el registro (`mostrador.log`) se guardan en `%APPDATA%\Mostrador\`;
las planillas exportadas, en `Documentos\Mostrador\`. Las actualizaciones no los tocan.

## Actualizaciones automáticas

Cada vez que se sube un cambio a `main`, GitHub Actions corre las pruebas, arma el paquete en una
máquina Windows (bajando el Python embebido oficial y verificando su firma), prueba que arranque y
que se actualice solo, y lo publica en **Releases** con un número de versión nuevo (`1.<n>`). Para
generar de nuevo sin cambiar código: **Actions** > "Generar paquete" > **Run workflow**.

El programa se actualiza solo: cada 15 minutos consulta los Releases (o en el momento, con
**Configuración > Actualizaciones > Buscar actualizaciones**) y, si hay una versión nueva:

1. Descarga `Mostrador-app.zip` (solo el código, unos 120 KB) y verifica su SHA-256 contra el
   `.sha256` publicado. Si no coincide, no instala nada.
2. Si la versión nueva pide otras librerías (cambió `requirements.txt`), baja también
   `Mostrador-lib.zip` (unos 23 MB) y lo deja listo en `lib.new`.
3. Cambia la carpeta `app` por la nueva (si algo falla, vuelve todo como estaba) y se reinicia.
   Al arrancar, antes de cargar nada, pone las librerías nuevas en su lugar: tienen partes
   compiladas que Windows no deja mover mientras el programa viejo las usa.
4. La página abierta muestra "se está actualizando" y se recarga sola cuando vuelve.

No instala mientras haya un trabajo en curso (aplicando precios, un respaldo…): espera a que
termine. Con **Actualizar sola** apagado, solo avisa y se instala con el botón.

Instalado queda así:

```
C:\Mostrador\
  Abrir Mostrador.cmd   abre el programa (la primera vez crea los accesos directos)
  python\               Python oficial embebido (no cambia)
  lib\                  librerías (cambia solo si cambian)
  app\                  código del programa (es lo que se actualiza)
```

Ojo: el repositorio tiene que ser **público** para que los clientes puedan bajar los Releases, y
cualquiera con permiso de escritura puede publicar una versión que todas las PCs van a instalar
solas. Conviene tener la verificación en dos pasos en las cuentas de GitHub con acceso.

## Desarrollo

Requiere Python 3.11 o más nuevo.

```
pip install -r requirements.txt -r requirements-dev.txt
python main.py                 abre la página en el navegador (con consola)
python main.py --puerto 8765   en otro puerto, para no chocar con uno instalado
python -m pytest -q tests      pruebas (sin tocar ninguna tienda ni GitHub)
```

Desde el código fuente la versión es `0.0-dev` y no se actualiza sola.

Para desarrollar contra una tienda sin pasar por la bienvenida:

```
$env:TN_STORE_ID = "1234567"; $env:TN_TOKEN = "abc..."; $env:MOSTRADOR_DATOS = "datos-dev"
python main.py
```

Para armar el paquete a mano (con el mismo Python que el embebido):
`./scripts/armar_paquete.ps1 -PythonVersion 3.12.10` y después `./tests/probar_actualizacion.ps1`.

## Cómo está hecho

```
Mostrador.pyw           punto de entrada (lo abre el acceso directo con pythonw.exe)
main.py                 lo mismo, para desarrollar con consola
mostrador/
  app.py                arranque: servidor, abrir la página, una sola copia, reinicio al actualizar
  arranque.py           pone las librerías nuevas antes de cargarlas (solo librería estándar)
  actualizador.py       actualización automática desde los Releases
  sistema.py            Windows: dónde está instalado, accesos directos, avisos
  tiendanube.py         cliente de la API: reintentos, límite de pedidos, errores explicados
  productos.py          leer y escribir productos y variantes; números como los escribe la gente
  precios.py            leer listas, adivinar columnas, buscar códigos, calcular, vista previa
  excel.py              exportar e importar la planilla, con comparación antes de aplicar
  respaldos.py          copias completas y automáticas
  fotos.py              normalizar la foto principal a 1280×1280
  tareas.py             trabajos largos en segundo plano, con progreso y cancelar
  servidor.py           la API local que usa la interfaz (Flask)
  config.py             dónde se guarda cada cosa
web/                    la interfaz: HTML, CSS y JS sin librerías ni internet
recursos/               ícono de los accesos directos y LEEME.txt del paquete
vendedor/               alta de clientes (saca número de tienda y token); no va en el paquete
scripts/                armar el paquete (lo usa el workflow) y dibujar el ícono
tests/                  pruebas (sin tocar ninguna tienda) y prueba de punta a punta del paquete
.github/workflows/      arma, prueba y publica cada versión
```

**Seguridad.** El servidor escucha solo en `127.0.0.1`, exige en cada pedido una clave aleatoria
que se genera al abrir la app (así ninguna página web abierta en la computadora puede usar el
token) y rechaza cualquier `Host` que no sea el suyo.

**Cosas de la API que no son obvias** (están comentadas en el código): el stock infinito se pide
con `stock: ""` y, si la tienda tiene varias ubicaciones, dentro de `inventory_levels`; el
redondeo usa ".5 para arriba" porque `round()` de Python redondea al par.

## Hoja de ruta

- Restaurar productos desde un respaldo (hoy se guardan, falta el botón para volver atrás).
- Descripciones, títulos SEO y etiquetas con IA para los productos que no tienen.
- Varias tiendas en la misma app.
- App publicada en la tienda de apps de Tiendanube, para que el cliente instale con un clic en
  vez de crear su propia aplicación.
- Licencias.

## Licencia

Software propietario. Ver [LICENSE](LICENSE).
