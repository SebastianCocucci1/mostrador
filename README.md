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

1. Instalar con `Mostrador-<versión>-instalador.exe`.
2. Al abrir, un asistente explica cómo conectar la tienda: se crea una aplicación gratuita en
   [partners.tiendanube.com](https://partners.tiendanube.com) (distribución *para comerciantes
   específicos*, permisos de productos), se autoriza, y listo. La conexión no vence.

La conexión y los respaldos se guardan en `%APPDATA%\Mostrador\`; las planillas exportadas, en
`Documentos\Mostrador\`.

Necesita Windows 10 u 11 con WebView2 (viene instalado en Windows 11 y en los 10 actualizados).

## Desarrollo

Requiere Python 3.11 o más nuevo.

```
pip install -r requirements.txt -r requirements-dev.txt
python main.py                 abre la app
python main.py --navegador     la abre en el navegador (más cómodo para tocar la interfaz)
python -m pytest -q tests      pruebas del motor
```

Para desarrollar contra una tienda sin pasar por el asistente:

```
$env:TN_STORE_ID = "1234567"; $env:TN_TOKEN = "abc..."; $env:MOSTRADOR_DATOS = "datos-dev"
python main.py --navegador
```

### Armar el instalador

1. `construir.bat` → instala dependencias, corre las pruebas, arma el ícono y deja
   `dist\Mostrador\Mostrador.exe`.
2. Abrir `empaquetar\instalador.iss` con [Inno Setup 6](https://jrsoftware.org/isinfo.php) y
   compilar → `dist\Mostrador-<versión>-instalador.exe`.

Al sacar una versión nueva, cambiarla en `mostrador/__init__.py`, `empaquetar/version.txt` y
`empaquetar/instalador.iss`.

## Cómo está hecho

```
main.py                 arranca el servidor local y abre la ventana (pywebview / WebView2)
mostrador/
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
empaquetar/             PyInstaller, Inno Setup e ícono
tests/                  pruebas del motor (sin tocar ninguna tienda)
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
- Licencias y actualizaciones automáticas.

## Licencia

Software propietario. Ver [LICENSE](LICENSE).
