"use strict";

/* =====================================================================
   Mostrador · interfaz
   Una sola página, sin librerías. Habla con el servidor local (/api/...).
   ===================================================================== */

const CLAVE = document.querySelector('meta[name="clave"]').content;
const VERSION = document.querySelector('meta[name="version"]').content;
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/* ------------------------------------------------------------ íconos */
const ICONOS = {
  inicio: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M10 21v-6h4v6"/>',
  caja: '<path d="M21 8 12 3 3 8v8l9 5 9-5z"/><path d="m3 8 9 5 9-5"/><path d="M12 13v8"/>',
  mas: '<path d="M12 5v14M5 12h14"/>',
  etiqueta: '<path d="M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
  planilla: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18"/>',
  escudo: '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/>',
  ajustes: '<path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1"/><circle cx="15" cy="6" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="17" cy="18" r="2"/>',
  buscar: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  recargar: '<path d="M21 12a9 9 0 1 1-2.6-6.4"/><path d="M21 4v5h-5"/>',
  check: '<path d="M5 12.5 10 17 19 7"/>',
  x: '<path d="M6 6l12 12M18 6 6 18"/>',
  subir: '<path d="M12 16V4"/><path d="m7 9 5-5 5 5"/><path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>',
  bajar: '<path d="M12 4v12"/><path d="m7 11 5 5 5-5"/><path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>',
  ojo: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  ojoNo: '<path d="M3 3l18 18"/><path d="M10.6 5.1A10.5 10.5 0 0 1 12 5c6.5 0 10 7 10 7a17 17 0 0 1-3.2 4.1M6.6 6.6C3.8 8.4 2 12 2 12s3.5 7 10 7a9.7 9.7 0 0 0 5.4-1.6"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/>',
  infinito: '<path d="M12 12c-2-2.7-3.6-4-5.5-4a4 4 0 0 0 0 8c1.9 0 3.5-1.3 5.5-4zm0 0c2 2.7 3.6 4 5.5 4a4 4 0 0 0 0-8c-1.9 0-3.5 1.3-5.5 4z"/>',
  basura: '<path d="M4 7h16"/><path d="M10 11v6M14 11v6"/><path d="M6 7l1 13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-13"/><path d="M9 7V4h6v3"/>',
  porcentaje: '<path d="M19 5 5 19"/><circle cx="7" cy="7" r="2.5"/><circle cx="17" cy="17" r="2.5"/>',
  externo: '<path d="M14 4h6v6"/><path d="M20 4 10 14"/><path d="M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5"/>',
  alerta: '<path d="M12 3.5 2.5 20h19z"/><path d="M12 10v4.5M12 17.5h.01"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
  ayuda: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6v.6M12 17h.01"/>',
  derecha: '<path d="m9 6 6 6-6 6"/>',
  izquierda: '<path d="m15 6-6 6 6 6"/>',
  flecha: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  carpeta: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  archivo: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h4"/>',
  imagen: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="m21 16-5-5-9 9"/>',
  tienda: '<path d="M4 9 5.5 4h13L20 9"/><path d="M4 9a2.7 2.7 0 0 0 5.3 0 2.7 2.7 0 0 0 5.4 0 2.7 2.7 0 0 0 5.3 0"/><path d="M5 11v9h14v-9"/><path d="M10 20v-5h4v5"/>',
  llave: '<circle cx="8" cy="15" r="4"/><path d="m11 12 9-9M17 6l3 3"/>',
  salir: '<path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3"/><path d="M10 16l-4-4 4-4M6 12h10"/>',
  sol: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  luna: '<path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z"/>',
  monitor: '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
  reloj: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  lista: '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
  lapiz: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="m13.5 6.5 4 4"/>',
  sube: '<path d="M7 17 17 7M9 7h8v8"/>',
  baja: '<path d="M7 7l10 10M17 9v8H9"/>',
  enlace: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
  rayo: '<path d="M13 3 4 14h7l-1 7 9-11h-7z"/>',
  estrella: '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
};
const ico = (n, cls = "") => `<svg class="ico ${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICONOS[n] || ""}</svg>`;

/* ------------------------------------------------------------ utilidades */
const AR = "es-AR";
function plata(x) {
  if (x === null || x === undefined || x === "" || Number.isNaN(Number(x))) return "—";
  const n = Number(x);
  const dec = Math.abs(n - Math.round(n)) > 0.004 ? 2 : 0;
  return "$ " + n.toLocaleString(AR, { minimumFractionDigits: dec, maximumFractionDigits: dec });
}
const entero = (n) => Number(n || 0).toLocaleString(AR);
const plural = (n, uno, varios) => `${entero(n)} ${n === 1 ? uno : varios}`;
const porc = (x) => (x > 0 ? "+" : "") + Number(x).toLocaleString(AR, { maximumFractionDigits: 1 }) + "%";
const sinTildes = (s) => String(s ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const letra = (j) => { let s = ""; j += 1; while (j > 0) { const m = (j - 1) % 26; s = String.fromCharCode(65 + m) + s; j = Math.floor((j - 1) / 26); } return s; };

/** Entiende como escribe la gente: 104.720 · $ 104.720,50 · 104720.5 · 1,7 */
function numAR(t) {
  if (typeof t === "number") return t;
  t = String(t ?? "").trim().replace(/u\$s|usd|ars|\$|\s/gi, "");
  if (!t) return null;
  if (t.includes(",") && t.includes(".")) {
    t = t.lastIndexOf(",") > t.lastIndexOf(".") ? t.replace(/\./g, "").replace(",", ".") : t.replace(/,/g, "");
  } else if (t.includes(",")) {
    const p = t.split(",");
    t = p.length === 2 && p[1].length !== 3 ? t.replace(",", ".") : t.replace(/,/g, "");
  } else if ((t.match(/\./g) || []).length > 1 || /^-?\d{1,3}(\.\d{3})+$/.test(t)) {
    t = t.replace(/\./g, "");
  }
  const x = Number(t);
  return Number.isFinite(x) ? x : NaN;
}

function duracion(s) {
  if (s < 60) return `${s} s`;
  return `${Math.floor(s / 60)} min ${String(s % 60).padStart(2, "0")} s`;
}

const guardado = {
  leer(k, d) { try { const v = localStorage.getItem("mostrador." + k); return v == null ? d : JSON.parse(v); } catch { return d; } },
  escribir(k, v) { try { localStorage.setItem("mostrador." + k, JSON.stringify(v)); } catch { /* sin almacenamiento: no pasa nada */ } },
};

async function api(metodo, ruta, cuerpo, form) {
  const op = { method: metodo, headers: { "X-Clave": CLAVE } };
  if (form) op.body = form;
  else if (cuerpo !== undefined) { op.headers["Content-Type"] = "application/json"; op.body = JSON.stringify(cuerpo); }
  let r;
  try { r = await fetch(ruta, op); } catch { throw new Error("La app no responde. Cerrala y volvé a abrirla."); }
  let d = {};
  try { d = await r.json(); } catch { /* respuesta sin cuerpo */ }
  if (!r.ok) { const e = new Error(d.error || `Error ${r.status}`); e.status = r.status; throw e; }
  return d;
}

const abrirWeb = (url) => api("POST", "/api/abrir", { ruta: url }).catch((e) => avisar(e.message, "error"));
const abrirRuta = (ruta, carpeta = false) => api("POST", "/api/abrir", { ruta, carpeta }).catch((e) => avisar(e.message, "error"));

/* ------------------------------------------------------------ avisos y modales */
function avisar(texto, tipo = "") {
  const t = document.createElement("div");
  t.className = `toast ${tipo}`;
  t.innerHTML = ico(tipo === "error" ? "alerta" : tipo === "exito" ? "check" : "info") + `<div>${esc(texto)}</div>`;
  $("#avisos").append(t);
  setTimeout(() => t.remove(), tipo === "error" ? 8000 : 4000);
}

function modal({ titulo, html = "", icono = null, tono = "", botones = [{ texto: "Aceptar", clase: "primario", valor: true }], ancho = false, alAbrir }) {
  return new Promise((resolver) => {
    const capa = document.createElement("div");
    capa.className = "modal-fondo";
    capa.innerHTML = `<div class="modal ${ancho ? "ancho" : ""}" role="dialog" aria-modal="true">
      <div class="cab">${icono ? `<div class="ic ${tono}">${ico(icono)}</div>` : ""}
        <div style="flex:1;min-width:0;padding-top:${icono ? 8 : 0}px"><h2>${esc(titulo)}</h2></div></div>
      <div class="cuerpo">${html}</div>
      <div class="pie">${botones.map((b, i) => `<button class="btn ${b.clase || ""}" data-i="${i}">${esc(b.texto)}</button>`).join("")}</div></div>`;
    const cerrar = (v) => { capa.remove(); document.removeEventListener("keydown", tecla); resolver(v); };
    const tecla = (e) => {
      if (e.key === "Escape") cerrar(null);
      if (e.key === "Enter" && e.target.tagName === "INPUT") $(".pie .btn.primario, .pie .btn.peligro", capa)?.click();
    };
    document.addEventListener("keydown", tecla);
    capa.addEventListener("mousedown", (e) => { if (e.target === capa) cerrar(null); });
    $$(".pie .btn", capa).forEach((b) => b.addEventListener("click", () => {
      const def = botones[+b.dataset.i];
      if (def.validar && def.validar(capa) === false) return;
      cerrar(typeof def.valor === "function" ? def.valor(capa) : def.valor);
    }));
    $("#capa-modal").append(capa);
    alAbrir?.(capa);
    ($("input, select, textarea", capa) || $(".pie .btn.primario, .pie .btn.peligro", capa))?.focus();
  });
}

function confirmar(titulo, html, { texto = "Confirmar", peligro = false, icono } = {}) {
  return modal({
    titulo, html, icono: icono || (peligro ? "alerta" : "info"), tono: peligro ? "peligro" : "",
    botones: [{ texto: "Cancelar", valor: false }, { texto, clase: peligro ? "peligro" : "primario", valor: true }],
  });
}

/** Muestra el progreso de una tarea del servidor hasta que termina. Devuelve la tarea final. */
function seguirTarea(tid, titulo, { exito } = {}) {
  return new Promise((resolver) => {
    const capa = document.createElement("div");
    capa.className = "modal-fondo";
    capa.innerHTML = `<div class="modal ancho" role="dialog" aria-modal="true">
      <div class="cab"><div class="ic" data-ic>${ico("reloj")}</div>
        <div style="flex:1;min-width:0;padding-top:2px"><h2>${esc(titulo)}</h2><p class="tenue" data-texto style="margin-top:2px">Empezando…</p></div></div>
      <div class="cuerpo pila">
        <div class="progreso indeterminado"><div style="width:0"></div></div>
        <div class="fila tenue" style="font-size:13px;margin-top:-4px"><span data-cuenta></span><span class="espacio"></span><span data-tiempo></span></div>
        <div data-final></div>
        <details class="ayuda-plegable"><summary>${ico("lista")} Ver el detalle de lo que va haciendo</summary>
          <div class="contenido"><div class="registro" data-registro></div></div></details>
      </div>
      <div class="pie"><button class="btn" data-cancelar>Cancelar</button><button class="btn primario oculto" data-cerrar>Listo</button></div></div>`;
    $("#capa-modal").append(capa);
    let desde = 0;
    let final = null;
    const reg = $("[data-registro]", capa);
    $("[data-cancelar]", capa).onclick = async (e) => {
      e.target.disabled = true;
      e.target.textContent = "Cancelando…";
      await api("POST", `/api/tareas/${tid}/cancelar`).catch(() => {});
    };
    $("[data-cerrar]", capa).onclick = () => { capa.remove(); resolver(final); };

    const tick = async () => {
      let t;
      try { t = await api("GET", `/api/tareas/${tid}?desde=${desde}`); } catch { setTimeout(tick, 1200); return; }
      if (t.registro.length) {
        reg.textContent += t.registro.join("\n") + "\n";
        reg.scrollTop = reg.scrollHeight;
        desde = t.largo_registro;
      }
      $("[data-texto]", capa).textContent = t.texto;
      $("[data-tiempo]", capa).textContent = duracion(t.segundos);
      const barra = $(".progreso", capa);
      if (t.total > 0) {
        barra.classList.remove("indeterminado");
        barra.firstElementChild.style.width = Math.min(100, (t.hecho / t.total) * 100) + "%";
        $("[data-cuenta]", capa).textContent = `${entero(t.hecho)} de ${entero(t.total)}`;
      }
      if (t.estado === "corriendo") { setTimeout(tick, 450); return; }

      final = t;
      barra.classList.remove("indeterminado");
      barra.firstElementChild.style.width = "100%";
      const r = t.resultado || {};
      const errores = r.errores || [];
      let html = "";
      const ic = $("[data-ic]", capa);
      if (t.estado === "error") {
        ic.className = "ic peligro"; ic.innerHTML = ico("alerta");
        $("[data-texto]", capa).textContent = "No se pudo terminar";
        html = `<div class="aviso-caja peligro">${ico("alerta")}<div>${esc(t.error)}</div></div>`;
      } else {
        const cancelada = t.estado === "cancelada";
        ic.className = `ic ${cancelada || errores.length ? "alerta" : "exito"}`;
        ic.innerHTML = ico(cancelada || errores.length ? "alerta" : "check");
        $("[data-texto]", capa).textContent = cancelada ? "Cancelado" : "Terminado";
        const msj = exito ? exito(r) : (r.hechos !== undefined ? `Listo: ${plural(r.hechos, "cambio aplicado", "cambios aplicados")}.` : "Listo.");
        html = `<div class="aviso-caja ${cancelada ? "alerta" : "exito"}">${ico(cancelada ? "alerta" : "check")}<div>
          ${cancelada ? "Se canceló. Lo que ya estaba hecho quedó hecho. " : ""}${msj}
          ${r.respaldo ? `<div class="tenue" style="margin-top:4px;font-size:13px">Antes de cambiar se guardó un respaldo: <span class="mono">${esc(r.respaldo)}</span></div>` : ""}</div></div>`;
        if (errores.length) {
          html += `<div class="aviso-caja alerta" style="margin-top:10px">${ico("alerta")}<div><strong>${plural(errores.length, "cosa no se pudo hacer", "cosas no se pudieron hacer")}:</strong>
            <ul style="margin:6px 0 0;padding-left:18px">${errores.slice(0, 15).map((e) => `<li>${esc(e)}</li>`).join("")}</ul>
            ${errores.length > 15 ? `<div class="tenue">… y ${errores.length - 15} más (ver el detalle).</div>` : ""}</div></div>`;
        }
      }
      $("[data-final]", capa).innerHTML = html;
      $("[data-cancelar]", capa).classList.add("oculto");
      $("[data-cerrar]", capa).classList.remove("oculto");
      $("[data-cerrar]", capa).focus();
    };
    tick();
  });
}

/* ------------------------------------------------------------ estado general */
const E = { estado: null, paquete: null, pedido: null };

async function traerPaquete(desdeTienda = false) {
  E.pedido = api("GET", "/api/productos" + (desdeTienda ? "?recargar=1" : ""));
  try { E.paquete = await E.pedido; } finally { E.pedido = null; }
  return E.paquete;
}
async function paquete() {
  if (E.paquete) return E.paquete;
  if (E.pedido) return E.pedido;
  return traerPaquete();
}

function aplicarTema(t) {
  const r = document.documentElement;
  if (t === "claro") r.dataset.theme = "light";
  else if (t === "oscuro") r.dataset.theme = "dark";
  else delete r.dataset.theme;
}

const cargando = (t = "Cargando…") => `<div class="cargando"><div class="rueda"></div>${esc(t)}</div>`;
const cabecera = (titulo, texto, acciones = "") =>
  `<div class="cabecera"><div class="textos"><h1>${esc(titulo)}</h1>${texto ? `<p>${texto}</p>` : ""}</div>${acciones ? `<div class="fila">${acciones}</div>` : ""}</div>`;

function errorPagina(el, e) {
  el.innerHTML = `<div class="pagina"><div class="aviso-caja peligro">${ico("alerta")}<div>
    <strong>No se pudo cargar</strong><p>${esc(e.message)}</p>
    <div class="fila" style="margin-top:10px"><button class="btn chico" data-reintentar>${ico("recargar")} Reintentar</button>
    ${e.status === 401 ? '<a class="btn chico" href="#/config">Ir a Configuración</a>' : ""}</div></div></div></div>`;
  $("[data-reintentar]", el).onclick = render;
}

/* ------------------------------------------------------------ navegación */
const MENU = [
  { grupo: "Tienda" },
  { ruta: "inicio", texto: "Inicio", icono: "inicio" },
  { ruta: "productos", texto: "Productos", icono: "caja" },
  { ruta: "nuevo", texto: "Nuevo producto", icono: "mas" },
  { grupo: "Herramientas" },
  { ruta: "precios", texto: "Actualizar precios", icono: "etiqueta" },
  { ruta: "excel", texto: "Edición con Excel", icono: "planilla" },
  { ruta: "respaldos", texto: "Copias de seguridad", icono: "escudo" },
  { grupo: "Cuenta" },
  { ruta: "config", texto: "Configuración", icono: "ajustes" },
];

const rutaActual = () => location.hash.replace(/^#\/?/, "").split("?")[0] || "inicio";
const parametros = () => new URLSearchParams(location.hash.split("?")[1] || "");

function render() {
  cerrarCajon();
  const conectado = E.estado?.conectado;
  $("#lateral").classList.toggle("oculto", !conectado);
  const el = $("#principal");
  if (!conectado) return paginaBienvenida(el);
  const t = E.estado.tienda || {};
  $("#nombre-tienda").textContent = t.nombre || `Tienda ${t.id}`;
  const ruta = PAGINAS[rutaActual()] ? rutaActual() : "inicio";
  $("#menu").innerHTML = MENU.map((m) => m.grupo
    ? `<div class="grupo">${esc(m.grupo)}</div>`
    : `<a href="#/${m.ruta}" class="${m.ruta === ruta ? "activo" : ""}">${ico(m.icono)}<span>${esc(m.texto)}</span></a>`).join("");
  el.scrollTop = 0;
  PAGINAS[ruta](el);
}

/* =====================================================================
   Bienvenida: conectar la tienda
   ===================================================================== */
let modoConexion = "app";

function paginaBienvenida(el) {
  el.innerHTML = `<div class="bienvenida"><div class="caja">
    <div class="hero">
      <img src="/web/icono.svg" alt="">
      <h1>Bienvenido a ${esc(document.title)}</h1>
      <p>Gestioná los productos de tu tienda Tiendanube mucho más rápido: precios, stock y cargas masivas en minutos.</p>
    </div>
    <div class="beneficios">
      <div class="beneficio">${ico("etiqueta")}<div><strong>Precios desde la lista del proveedor</strong>Subí el Excel o PDF y se actualiza todo con tu margen.</div></div>
      <div class="beneficio">${ico("planilla")}<div><strong>Edición masiva con Excel</strong>Cambiá cientos de productos a la vez, viendo cada cambio antes.</div></div>
      <div class="beneficio">${ico("escudo")}<div><strong>Sin miedo a equivocarte</strong>Todo se prueba antes y se guarda un respaldo automático.</div></div>
    </div>
    <div class="tarjeta">
      <div class="cab"><h2>Conectá tu tienda</h2><span class="espacio"></span>
        <div class="pestanas">
          <button data-modo="app" class="${modoConexion === "app" ? "activo" : ""}">Paso a paso</button>
          <button data-modo="token" class="${modoConexion === "token" ? "activo" : ""}">Ya tengo un token</button>
        </div></div>
      <div class="cuerpo" id="conexion"></div>
    </div>
    <p class="tenue" style="text-align:center;margin-top:16px;font-size:12.5px">${ico("escudo")} La conexión se guarda solo en esta computadora. La app nunca manda tus datos a ningún otro lado.</p>
  </div></div>`;
  $$("[data-modo]", el).forEach((b) => b.onclick = () => { modoConexion = b.dataset.modo; paginaBienvenida(el); });
  const c = $("#conexion", el);
  if (modoConexion === "token") {
    c.innerHTML = `<div class="pila" style="max-width:560px">
      <p class="texto-2">Si ya tenés el número de tienda y el token de acceso (por ejemplo, porque te los pasó quien te instaló la app), pegalos acá.</p>
      <div class="campo"><label for="c-id">Número de tienda</label><input class="input" id="c-id" inputmode="numeric" placeholder="1234567">
        <span class="ayuda">Son solo números. Lo ves en el panel de Tiendanube, en la dirección: /admin/v2/… o en Mi cuenta.</span></div>
      <div class="campo"><label for="c-token">Token de acceso</label><input class="input mono" id="c-token" placeholder="abc123…" autocomplete="off"></div>
      <div><button class="btn primario grande" id="c-ok">${ico("enlace")} Conectar</button></div></div>`;
    $("#c-ok", c).onclick = () => conectar("/api/conexion/token", { tienda_id: $("#c-id", c).value, token: $("#c-token", c).value }, $("#c-ok", c));
    return;
  }
  c.innerHTML = `<ol class="instrucciones">
    <li><div><strong>Creá tu cuenta de socio en Tiendanube</strong> (es gratis y se hace una sola vez).
      <div style="margin-top:8px"><button class="btn chico" data-web="https://partners.tiendanube.com">${ico("externo")} Abrir partners.tiendanube.com</button></div></div></li>
    <li><div><strong>Creá una aplicación</strong> en <em>Aplicaciones → Crear aplicación</em>, con estos datos:
      <ul style="margin:6px 0 0;padding-left:18px">
        <li>Distribución: <strong>Para comerciantes específicos</strong> (así es privada y no necesita revisión).</li>
        <li>URL de redirección: <span class="mono">https://localhost/</span></li>
        <li>Permisos: <strong>Productos</strong> — lectura y escritura. Nada más.</li>
      </ul></div></li>
    <li><div><strong>Copiá las claves</strong> de la aplicación (botón «Claves de acceso») y pegalas acá:
      <div class="grilla-2" style="margin-top:10px">
        <div class="campo"><label for="c-app">App ID</label><input class="input" id="c-app" inputmode="numeric" placeholder="1234"></div>
        <div class="campo"><label for="c-secret">Client secret</label><input class="input mono" id="c-secret" autocomplete="off" placeholder="abc123…"></div>
      </div></div></li>
    <li><div><strong>Autorizá la app en tu tienda.</strong> Se abre el navegador; aceptá los permisos.
      <div style="margin-top:8px"><button class="btn" id="c-autorizar">${ico("externo")} Autorizar en mi tienda</button></div></div></li>
    <li><div><strong>Pegá la dirección a la que te llevó.</strong> Va a ser una página que no carga (es normal): copiá la dirección entera de la barra del navegador.
      <div class="campo" style="margin-top:8px"><input class="input mono" id="c-codigo" placeholder="https://localhost/?code=…"></div>
      <div style="margin-top:12px"><button class="btn primario grande" id="c-ok">${ico("enlace")} Conectar mi tienda</button></div></div></li>
  </ol>`;
  $$("[data-web]", c).forEach((b) => b.onclick = () => abrirWeb(b.dataset.web));
  $("#c-autorizar", c).onclick = async () => {
    try {
      const r = await api("POST", "/api/conexion/link", { app_id: $("#c-app", c).value });
      abrirWeb(r.url);
    } catch (e) { avisar(e.message, "error"); }
  };
  $("#c-ok", c).onclick = () => conectar("/api/conexion/codigo", {
    app_id: $("#c-app", c).value, secret: $("#c-secret", c).value, codigo: $("#c-codigo", c).value,
  }, $("#c-ok", c));
}

async function conectar(ruta, datos, boton) {
  const antes = boton.innerHTML;
  boton.disabled = true;
  boton.innerHTML = '<div class="rueda" style="width:16px;height:16px;border-width:2px"></div> Conectando…';
  try {
    const r = await api("POST", ruta, datos);
    E.estado = await api("GET", "/api/estado");
    E.paquete = null;
    avisar(`¡Listo! Conectado a ${r.tienda.nombre || "tu tienda"}.`, "exito");
    location.hash = "#/inicio";
    render();
  } catch (e) {
    avisar(e.message, "error");
    boton.disabled = false;
    boton.innerHTML = antes;
  }
}

/* =====================================================================
   Inicio
   ===================================================================== */
function saludo() {
  const h = new Date().getHours();
  return h < 13 ? "Buen día" : h < 20 ? "Buenas tardes" : "Buenas noches";
}

async function paginaInicio(el, recargar = false) {
  el.innerHTML = `<div class="pagina">${cargando("Leyendo tu tienda… (la primera vez tarda unos segundos)")}</div>`;
  let d;
  try { d = await api("GET", "/api/inicio" + (recargar ? "?recargar=1" : "")); } catch (e) { return errorPagina(el, e); }
  if (recargar) E.paquete = null;
  const t = E.estado.tienda || {};
  const revisar = [
    { k: "sin_precio", n: d.sin_precio, t: "Sin precio", s: "Alguna variante no tiene precio: no se puede comprar.", ic: "etiqueta", tono: "peligro" },
    { k: "sin_fotos", n: d.sin_fotos, t: "Sin fotos", s: "Los productos sin foto casi no se venden.", ic: "imagen", tono: "alerta" },
    { k: "sin_stock", n: d.sin_stock, t: "Sin stock", s: "Tienen alguna variante agotada.", ic: "caja", tono: "alerta" },
    { k: "sin_categoria", n: d.sin_categoria, t: "Sin categoría", s: "No aparecen al navegar la tienda por categorías.", ic: "carpeta", tono: "alerta" },
    { k: "sin_descripcion", n: d.sin_descripcion, t: "Sin descripción", s: "Una buena descripción ayuda a vender y a aparecer en Google.", ic: "archivo", tono: "" },
  ].filter((x) => x.n > 0);
  const tonos = { peligro: "background:var(--peligro-suave);color:var(--peligro)", alerta: "background:var(--alerta-suave);color:var(--alerta)", "": "background:var(--hundido);color:var(--texto-2)" };
  const ultimo = d.ultimos_respaldos[0];
  const accion = (ruta, icono, titulo, texto) => `<a class="tarjeta accion-rapida" href="#/${ruta}"><div class="ic">${ico(icono)}</div><div><h3>${titulo}</h3><p>${texto}</p></div></a>`;
  el.innerHTML = `<div class="pagina">
    ${cabecera(`${saludo()} 👋`, `Así está <strong>${esc(t.nombre || "tu tienda")}</strong>. Datos leídos a las ${esc(d.actualizado)}.`,
      `<button class="btn" data-recargar>${ico("recargar")} Actualizar</button>${t.url ? `<button class="btn" data-web="${esc(t.url)}">${ico("externo")} Ver mi tienda</button>` : ""}`)}
    <div class="grilla-4" style="margin-bottom:20px">
      <div class="tarjeta stat"><div class="etq">${ico("caja")} Productos</div><div class="valor">${entero(d.total)}</div><div class="sub">${plural(d.variantes, "variante", "variantes")}</div></div>
      <div class="tarjeta stat"><div class="etq">${ico("ojo")} Publicados</div><div class="valor">${entero(d.publicados)}</div><div class="sub">se ven en la tienda</div></div>
      <div class="tarjeta stat"><div class="etq">${ico("ojoNo")} Ocultos</div><div class="valor">${entero(d.ocultos)}</div><div class="sub">no se ven en la tienda</div></div>
      <div class="tarjeta stat"><div class="etq">${ico("estrella")} Marcas</div><div class="valor">${entero(d.marcas)}</div><div class="sub">distintas</div></div>
    </div>
    <div class="grilla-2" style="grid-template-columns:1.15fr 1fr;align-items:start">
      <div class="tarjeta">
        <div class="cab"><h2>Para revisar</h2><span class="espacio"></span><span class="tenue" style="font-size:13px">Tocá para ver cuáles son</span></div>
        ${revisar.length ? revisar.map((x) => `<div class="revisar" data-filtro="${x.k}">
            <div class="ic" style="${tonos[x.tono]}">${ico(x.ic)}</div>
            <div style="flex:1;min-width:0"><div><span class="cant">${entero(x.n)}</span> <strong>${x.t.toLowerCase()}</strong></div><div class="tenue" style="font-size:13px">${x.s}</div></div>
            ${ico("derecha", "tenue")}</div>`).join("")
          : `<div class="vacio"><div class="ic" style="background:var(--exito-suave);color:var(--exito)">${ico("check")}</div><h3>Todo en orden</h3><p>Todos tus productos tienen precio, fotos, stock y categoría.</p></div>`}
      </div>
      <div class="pila">
        ${accion("precios", "etiqueta", "Actualizar precios", "Desde la lista de tu proveedor (Excel o PDF).")}
        ${accion("excel", "planilla", "Edición con Excel", "Exportá, editá en Excel y volvé a subir.")}
        ${accion("nuevo", "mas", "Nuevo producto", "Con variantes, precios y fotos.")}
        <div class="tarjeta" style="padding:14px 18px"><div class="fila">${ico("escudo", "tenue")}
          <div style="flex:1;font-size:13px">${ultimo ? `Última copia de seguridad: <strong>${esc(fechaLinda(ultimo.fecha))}</strong><br><span class="tenue">${esc(ultimo.motivo)}</span>` : "Todavía no hiciste ninguna copia de seguridad."}</div>
          <a class="btn chico" href="#/respaldos">${ultimo ? "Ver" : "Hacer una"}</a></div></div>
      </div>
    </div></div>`;
  $("[data-recargar]", el).onclick = () => paginaInicio(el, true);
  $$("[data-web]", el).forEach((b) => b.onclick = () => abrirWeb(b.dataset.web));
  $$("[data-filtro]", el).forEach((r) => r.onclick = () => { PF.filtro = r.dataset.filtro; PF.pagina = 0; location.hash = "#/productos"; });
}

function fechaLinda(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const hoy = new Date();
  const ayer = new Date(Date.now() - 864e5);
  const hora = d.toLocaleTimeString(AR, { hour: "2-digit", minute: "2-digit" });
  if (d.toDateString() === hoy.toDateString()) return `hoy a las ${hora}`;
  if (d.toDateString() === ayer.toDateString()) return `ayer a las ${hora}`;
  return d.toLocaleDateString(AR, { day: "numeric", month: "short", year: d.getFullYear() !== hoy.getFullYear() ? "numeric" : undefined }) + ` · ${hora}`;
}

/* =====================================================================
   Productos
   ===================================================================== */
const FILTROS = [
  ["todos", "Todos"], ["publicados", "Publicados"], ["ocultos", "Ocultos"], ["sin_precio", "Sin precio"],
  ["sin_fotos", "Sin fotos"], ["sin_stock", "Sin stock"], ["sin_categoria", "Sin categoría"], ["sin_descripcion", "Sin descripción"],
];
const PF = { texto: "", marca: "", filtro: "todos", orden: "nombre", asc: true, pagina: 0, sel: new Set() };
const POR_PAGINA = 50;

function cumple(p, f) {
  switch (f) {
    case "publicados": return p.publicado;
    case "ocultos": return !p.publicado;
    case "sin_precio": return p.sin_precio;
    case "sin_fotos": return p.fotos === 0;
    case "sin_stock": return p.sin_stock;
    case "sin_categoria": return p.sin_categoria;
    case "sin_descripcion": return p.sin_descripcion;
    default: return true;
  }
}

function filtrarProductos() {
  const q = sinTildes(PF.texto.trim());
  const base = E.paquete.productos.filter((p) => {
    if (PF.marca && p.marca !== PF.marca) return false;
    if (!q) return true;
    return sinTildes(p.nombre).includes(q) || sinTildes(p.marca).includes(q) || p.variantes.some((v) => sinTildes(v.sku).includes(q));
  });
  const cuentas = Object.fromEntries(FILTROS.map(([k]) => [k, base.filter((p) => cumple(p, k)).length]));
  const lista = base.filter((p) => cumple(p, PF.filtro));
  const clave = {
    nombre: (p) => sinTildes(p.nombre), marca: (p) => sinTildes(p.marca), precio: (p) => p.precio_min,
    stock: (p) => (p.stock_infinito ? Infinity : p.stock_total), estado: (p) => (p.publicado ? 0 : 1),
  }[PF.orden];
  lista.sort((a, b) => { const x = clave(a), y = clave(b); return (x < y ? -1 : x > y ? 1 : 0) * (PF.asc ? 1 : -1); });
  return { lista, cuentas };
}

function textoPrecio(p) {
  if (!p.precio_max) return '<span class="insignia peligro">Sin precio</span>';
  const r = p.precio_min === p.precio_max ? plata(p.precio_min) : `${plata(p.precio_min)} – ${plata(p.precio_max).replace("$ ", "")}`;
  return r + (p.sin_precio ? ` <span title="Alguna variante no tiene precio">${ico("alerta", "sube")}</span>` : "");
}
function textoStock(p) {
  if (p.stock_infinito) return `<span class="tenue" title="Stock infinito: nunca se agota">∞</span>`;
  if (p.sin_stock) return `<span class="insignia alerta">${entero(p.stock_total)}</span>`;
  return entero(p.stock_total) + (p.variantes.some((v) => v.stock === null) ? ' <span class="tenue">+ ∞</span>' : "");
}

async function paginaProductos(el) {
  const f = parametros().get("filtro");
  if (f) { PF.filtro = f; PF.pagina = 0; }
  el.innerHTML = `<div class="pagina">${cabecera("Productos", "")}${cargando("Leyendo los productos de tu tienda…")}</div>`;
  try { await paquete(); } catch (e) { return errorPagina(el, e); }
  const pq = E.paquete;
  el.innerHTML = `<div class="pagina ancha" style="max-width:1500px">
    ${cabecera("Productos", `Todos los productos de tu tienda. Tocá uno para editar sus precios, stock y datos. Tildá varios para cambiarlos juntos. <span class="tenue">Actualizado a las ${esc(pq.actualizado)}.</span>`,
      `<button class="btn" data-recargar title="Volver a leer la tienda">${ico("recargar")} Actualizar</button><a class="btn primario" href="#/nuevo">${ico("mas")} Nuevo producto</a>`)}
    <div class="tarjeta">
      <div class="barra-herr">
        <div class="input-icono" style="width:300px">${ico("buscar")}<input class="input" id="p-buscar" placeholder="Buscar por nombre, marca o SKU" value="${esc(PF.texto)}"></div>
        <select class="input" id="p-marca" style="width:190px"><option value="">Todas las marcas</option>${pq.marcas.map((m) => `<option ${m === PF.marca ? "selected" : ""}>${esc(m)}</option>`).join("")}</select>
        <div class="chips" id="p-chips"></div>
      </div>
      <div id="p-tabla"></div>
    </div>
    <div id="p-masiva"></div>
  </div>`;
  let espera;
  $("#p-buscar", el).oninput = (e) => { clearTimeout(espera); espera = setTimeout(() => { PF.texto = e.target.value; PF.pagina = 0; dibujarProductos(); }, 150); };
  $("#p-marca", el).onchange = (e) => { PF.marca = e.target.value; PF.pagina = 0; dibujarProductos(); };
  $("[data-recargar]", el).onclick = async (e) => {
    e.currentTarget.disabled = true;
    try { await traerPaquete(true); avisar("Productos actualizados desde la tienda.", "exito"); } catch (err) { avisar(err.message, "error"); }
    render();
  };
  dibujarProductos();
  const abrir = parametros().get("abrir");
  if (abrir) { const p = pq.productos.find((x) => String(x.id) === abrir); if (p) abrirDetalle(p); }
}

function dibujarProductos() {
  if (!$("#p-tabla")) return;          // la pantalla de productos ya no está abierta
  const { lista, cuentas } = filtrarProductos();
  $("#p-chips").innerHTML = FILTROS.map(([k, t]) => (k === "todos" || cuentas[k] || PF.filtro === k)
    ? `<button class="chip ${PF.filtro === k ? "activo" : ""}" data-f="${k}">${t} <span class="cuenta">${entero(cuentas[k])}</span></button>` : "").join("");
  $$("#p-chips [data-f]").forEach((b) => b.onclick = () => { PF.filtro = b.dataset.f; PF.pagina = 0; dibujarProductos(); });

  const paginas = Math.max(1, Math.ceil(lista.length / POR_PAGINA));
  PF.pagina = Math.min(PF.pagina, paginas - 1);
  const pagina = lista.slice(PF.pagina * POR_PAGINA, (PF.pagina + 1) * POR_PAGINA);
  const todosElegidos = lista.length > 0 && lista.every((p) => PF.sel.has(p.id));
  const th = (k, t, cls = "") => `<th class="orden ${cls}" data-orden="${k}">${t}${PF.orden === k ? (PF.asc ? " ↑" : " ↓") : ""}</th>`;

  const c = $("#p-tabla");
  if (!lista.length) {
    c.innerHTML = `<div class="vacio"><div class="ic">${ico("buscar")}</div><h3>No hay productos para mostrar</h3><p>Probá con otra búsqueda o sacá los filtros.</p></div>`;
  } else {
    c.innerHTML = `<div class="tabla-caja"><table class="tabla">
      <thead><tr><th style="width:36px"><input type="checkbox" class="check" id="p-todos" ${todosElegidos ? "checked" : ""} title="Elegir todos los de la lista (${lista.length})"></th>
        ${th("nombre", "Producto")}${th("marca", "Marca")}${th("precio", "Precio", "num")}${th("stock", "Stock", "num")}${th("estado", "Estado")}<th></th></tr></thead>
      <tbody>${pagina.map((p) => `<tr class="clic ${PF.sel.has(p.id) ? "elegida" : ""}" data-id="${p.id}">
        <td><input type="checkbox" class="check" data-sel="${p.id}" ${PF.sel.has(p.id) ? "checked" : ""}></td>
        <td><div class="celda-prod">${p.foto ? `<img class="miniatura" src="${esc(p.foto)}" alt="" loading="lazy">` : `<div class="miniatura vacia">${ico("imagen")}</div>`}
          <div style="min-width:0"><div class="n">${esc(p.nombre)}</div><div class="s">${plural(p.variantes.length, "variante", "variantes")}${p.variantes[0]?.sku ? ` · ${esc(p.variantes[0].sku)}${p.variantes.length > 1 ? "…" : ""}` : ""}</div></div></div></td>
        <td>${esc(p.marca) || '<span class="tenue">—</span>'}</td>
        <td class="num">${textoPrecio(p)}</td>
        <td class="num">${textoStock(p)}</td>
        <td>${p.publicado ? '<span class="insignia exito"><span class="punto"></span>Publicado</span>' : '<span class="insignia"><span class="punto"></span>Oculto</span>'}</td>
        <td class="ajustar tenue">${ico("derecha")}</td></tr>`).join("")}</tbody></table></div>
      <div class="paginador"><span>${entero(lista.length)} productos${lista.length !== E.paquete.productos.length ? ` (de ${entero(E.paquete.productos.length)})` : ""}</span><span class="espacio"></span>
        ${paginas > 1 ? `<button class="btn chico icono" data-pag="-1" ${PF.pagina === 0 ? "disabled" : ""}>${ico("izquierda")}</button>
        <span>Página ${PF.pagina + 1} de ${paginas}</span>
        <button class="btn chico icono" data-pag="1" ${PF.pagina >= paginas - 1 ? "disabled" : ""}>${ico("derecha")}</button>` : ""}</div>`;
    $$("[data-orden]", c).forEach((h) => h.onclick = () => {
      if (PF.orden === h.dataset.orden) PF.asc = !PF.asc; else { PF.orden = h.dataset.orden; PF.asc = true; }
      dibujarProductos();
    });
    $$("[data-pag]", c).forEach((b) => b.onclick = () => { PF.pagina += +b.dataset.pag; dibujarProductos(); $("#principal").scrollTop = 0; });
    $("#p-todos", c).onchange = (e) => { lista.forEach((p) => (e.target.checked ? PF.sel.add(p.id) : PF.sel.delete(p.id))); dibujarProductos(); };
    $$("tbody tr", c).forEach((tr) => tr.onclick = (e) => {
      const id = +tr.dataset.id;
      if (e.target.matches("[data-sel]")) {
        e.target.checked ? PF.sel.add(id) : PF.sel.delete(id);
        tr.classList.toggle("elegida", e.target.checked);
        dibujarMasiva();
        return;
      }
      if (e.target.closest("td:first-child")) return;
      abrirDetalle(E.paquete.productos.find((p) => p.id === id));
    });
  }
  dibujarMasiva();
}

function dibujarMasiva() {
  const c = $("#p-masiva");
  if (!c) return;
  const ids = [...PF.sel].filter((id) => E.paquete.productos.some((p) => p.id === id));
  if (!ids.length) { c.innerHTML = ""; return; }
  c.innerHTML = `<div class="barra-masiva">
    <strong>${plural(ids.length, "elegido", "elegidos")}</strong>
    <button class="btn" data-m="publicar">${ico("ojo")} Publicar</button>
    <button class="btn" data-m="ocultar">${ico("ojoNo")} Ocultar</button>
    <button class="btn" data-m="precio">${ico("porcentaje")} Ajustar precio</button>
    <button class="btn" data-m="infinito">${ico("infinito")} Stock infinito</button>
    <button class="btn peligro-suave" data-m="borrar">${ico("basura")} Borrar</button>
    <button class="btn icono fantasma" data-m="limpiar" title="Quitar la selección">${ico("x")}</button></div>`;
  $$("[data-m]", c).forEach((b) => b.onclick = () => accionMasiva(b.dataset.m, ids));
}

async function accionMasiva(accion, ids) {
  if (accion === "limpiar") { PF.sel.clear(); dibujarProductos(); return; }
  const n = ids.length;
  const nombres = ids.slice(0, 6).map((id) => E.paquete.productos.find((p) => p.id === id)?.nombre).filter(Boolean);
  const listaHtml = `<ul style="margin:8px 0 0;padding-left:18px">${nombres.map((x) => `<li>${esc(x)}</li>`).join("")}${n > 6 ? `<li class="tenue">y ${n - 6} más</li>` : ""}</ul>`;
  let extra = {};
  if (accion === "publicar" || accion === "ocultar") {
    const ok = await confirmar(accion === "publicar" ? "Publicar productos" : "Ocultar productos",
      `${accion === "publicar" ? "Se van a ver en tu tienda" : "Dejan de verse en tu tienda (no se borran; los podés volver a publicar)"}:${listaHtml}`,
      { texto: accion === "publicar" ? `Publicar ${n}` : `Ocultar ${n}`, icono: accion === "publicar" ? "ojo" : "ojoNo" });
    if (!ok) return;
  } else if (accion === "infinito") {
    const ok = await confirmar("Stock infinito", `Todas las variantes de estos productos quedan con <strong>stock infinito</strong>: nunca se agotan. Sirve si vendés a pedido.${listaHtml}`, { texto: "Poner stock infinito", icono: "infinito" });
    if (!ok) return;
  } else if (accion === "borrar") {
    const ok = await confirmar(`¿Borrar ${plural(n, "producto", "productos")}?`,
      `Se borran de tu tienda <strong>para siempre</strong>, con sus fotos y variantes.${listaHtml}
       <div class="aviso-caja" style="margin-top:14px">${ico("info")}<div>Antes se guarda un respaldo con todos sus datos. Si solo querés que no se vean, usá <strong>Ocultar</strong>.</div></div>`,
      { texto: `Sí, borrar ${n}`, peligro: true });
    if (!ok) return;
  } else if (accion === "precio") {
    const r = await modal({
      titulo: "Ajustar precios", icono: "porcentaje", ancho: false,
      html: `<div class="pila"><p>Sube o baja el precio de todas las variantes de ${plural(n, "producto", "productos")}.</p>
        <div class="grilla-2">
          <div class="campo"><label for="m-pct">Porcentaje</label><div class="prefijo"><span>%</span><input class="input" id="m-pct" placeholder="10 o -5" inputmode="decimal"></div>
            <span class="ayuda">Positivo sube, negativo baja.</span></div>
          <div class="campo"><label for="m-red">Redondear</label><select class="input" id="m-red">
            <option value="0">Sin redondear</option><option value="10">a $10</option><option value="100" selected>a $100</option><option value="1000">a $1.000</option></select></div>
        </div>
        <div class="ejemplo-regla" id="m-ej">Escribí un porcentaje para ver un ejemplo.</div></div>`,
      botones: [{ texto: "Cancelar", valor: null }, {
        texto: "Aplicar", clase: "primario",
        validar: (m) => { const x = numAR($("#m-pct", m).value); if (!x || Number.isNaN(x)) { $("#m-pct", m).classList.add("error"); return false; } },
        valor: (m) => ({ pct: numAR($("#m-pct", m).value), redondeo: +$("#m-red", m).value }),
      }],
      alAbrir: (m) => {
        const ej = () => {
          const x = numAR($("#m-pct", m).value), red = +$("#m-red", m).value;
          if (!x || Number.isNaN(x)) { $("#m-ej", m).textContent = "Escribí un porcentaje para ver un ejemplo."; return; }
          let v = 10000 * (1 + x / 100);
          v = red ? Math.round(v / red) * red : Math.round(v * 100) / 100;
          $("#m-ej", m).innerHTML = `Ejemplo: ${plata(10000)} ${ico("flecha", "tenue")} <span class="final">${plata(v)}</span>`;
        };
        $("#m-pct", m).oninput = ej; $("#m-red", m).onchange = ej;
      },
    });
    if (!r) return;
    extra = r;
  }
  try {
    const { tarea } = await api("POST", "/api/masivo", { accion, ids, ...extra });
    const titulos = { publicar: "Publicando", ocultar: "Ocultando", infinito: "Poniendo stock infinito", precio: "Ajustando precios", borrar: "Borrando" };
    const t = await seguirTarea(tarea, `${titulos[accion]} ${plural(n, "producto", "productos")}`, {
      exito: (r) => `Listo: ${plural(r.hechos, "producto actualizado", "productos actualizados")}.`,
    });
    if (t && accion === "borrar") ids.forEach((id) => PF.sel.delete(id));
    await traerPaquete();
    dibujarProductos();
  } catch (e) { avisar(e.message, "error"); }
}

/* ------------------------------------------------------------ detalle (cajón) */
function cerrarCajon() { $("#capa-modal .cortina")?.remove(); $("#capa-modal .cajon")?.remove(); }

function abrirDetalle(p) {
  if (!p) return;
  cerrarCajon();
  const pq = E.paquete;
  const cambios = new Map();     // variante id -> {campo: valor}
  const cortina = document.createElement("div");
  cortina.className = "cortina";
  const cajon = document.createElement("div");
  cajon.className = "cajon";
  cajon.setAttribute("role", "dialog");
  cajon.innerHTML = `
    <div class="cab">${p.foto ? `<img class="miniatura" style="width:52px;height:52px" src="${esc(p.foto)}" alt="">` : `<div class="miniatura vacia" style="width:52px;height:52px">${ico("imagen")}</div>`}
      <div style="flex:1;min-width:0"><h2 style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(p.nombre)}</h2>
        <div class="tenue" style="font-size:13px">${plural(p.fotos, "foto", "fotos")} · ${plural(p.variantes.length, "variante", "variantes")}${p.desplegables.length ? ` (${esc(p.desplegables.join(" / "))})` : ""}</div></div>
      <button class="btn icono fantasma" data-cerrar title="Cerrar (Esc)">${ico("x")}</button></div>
    <div class="cuerpo">
      <div class="grilla-2" style="grid-template-columns:2fr 1fr">
        <div class="campo"><label for="d-nombre">Nombre</label><input class="input" id="d-nombre" value="${esc(p.nombre)}"></div>
        <div class="campo"><label for="d-marca">Marca</label><input class="input" id="d-marca" list="d-marcas" value="${esc(p.marca)}">
          <datalist id="d-marcas">${pq.marcas.map((m) => `<option value="${esc(m)}">`).join("")}</datalist></div>
      </div>
      <label class="interruptor"><input type="checkbox" id="d-pub" ${p.publicado ? "checked" : ""}><span><strong>Publicado</strong> <span class="tenue">— si está apagado, el producto no se ve en la tienda</span></span></label>
      <div class="texto-2" style="font-size:13px">${ico("carpeta", "tenue")} ${p.categorias.length ? esc(p.categorias.join(" · ")) : '<span class="insignia alerta">Sin categoría</span>'}</div>
      <div>
        <div class="fila" style="margin-bottom:8px"><h3>Variantes</h3><span class="espacio"></span>
          ${p.variantes.length > 1 ? `<button class="btn chico" data-todas="precio">${ico("etiqueta")} Mismo precio a todas</button>` : ""}
          <button class="btn chico" data-todas="infinito">${ico("infinito")} Todas infinito</button></div>
        <div class="tarjeta tabla-caja"><table class="tabla compacta">
          <thead><tr><th>Variante</th><th class="num">Precio</th><th class="num">Promoción</th><th class="num" title="Vacío = infinito">Stock</th><th>SKU</th></tr></thead>
          <tbody>${p.variantes.map((v) => `<tr data-v="${v.id}">
            <td>${esc(v.valores)}</td>
            <td style="width:130px"><input class="input chico num" data-c="precio" value="${v.precio ? esc(plata(v.precio).replace("$ ", "")) : ""}" placeholder="Sin precio"></td>
            <td style="width:120px"><input class="input chico num" data-c="promocional" value="${v.promocional ? esc(plata(v.promocional).replace("$ ", "")) : ""}" placeholder="—"></td>
            <td style="width:84px"><input class="input chico num" data-c="stock" value="${v.stock === null ? "" : v.stock}" placeholder="∞"></td>
            <td style="width:170px"><input class="input chico" data-c="sku" value="${esc(v.sku)}"></td></tr>`).join("")}</tbody></table></div>
        <p class="tenue" style="font-size:12.5px;margin-top:8px">Stock vacío = infinito (nunca se agota). Promoción vacía = sin precio promocional.</p>
      </div>
    </div>
    <div class="pie">
      ${p.url ? `<button class="btn" data-ver>${ico("externo")} Ver en la tienda</button>` : ""}
      <span class="espacio"></span><span class="tenue" data-cuenta style="font-size:13px"></span>
      <button class="btn" data-cerrar>Cancelar</button>
      <button class="btn primario" data-guardar disabled>${ico("check")} Guardar cambios</button></div>`;
  $("#capa-modal").append(cortina, cajon);

  const original = { nombre: p.nombre, marca: p.marca, publicado: p.publicado };
  const actualizar = () => {
    const prod = ($("#d-nombre", cajon).value.trim() !== original.nombre) + ($("#d-marca", cajon).value.trim() !== original.marca) + ($("#d-pub", cajon).checked !== original.publicado);
    const n = [...cambios.values()].reduce((a, c) => a + Object.keys(c).length, 0) + prod;
    $("[data-guardar]", cajon).disabled = n === 0;
    $("[data-cuenta]", cajon).textContent = n ? plural(n, "cambio sin guardar", "cambios sin guardar") : "";
    $("#d-nombre", cajon).classList.toggle("modificado", $("#d-nombre", cajon).value.trim() !== original.nombre);
    $("#d-marca", cajon).classList.toggle("modificado", $("#d-marca", cajon).value.trim() !== original.marca);
  };
  const valorOriginal = (v, campo) => ({ precio: v.precio || null, promocional: v.promocional || null, stock: v.stock, sku: v.sku })[campo];
  const leer = (campo, texto) => {
    const t = texto.trim();
    if (campo === "sku") return t;
    if (campo === "stock") { if (!t || t === "∞") return null; const x = numAR(t); return Number.isInteger(x) && x >= 0 ? x : NaN; }
    if (!t) return null;
    const x = numAR(t); return x >= 0 ? x : NaN;
  };
  $$("[data-c]", cajon).forEach((inp) => inp.oninput = () => {
    const vid = +inp.closest("tr").dataset.v;
    const v = p.variantes.find((x) => x.id === vid);
    const campo = inp.dataset.c;
    const val = leer(campo, inp.value);
    inp.classList.toggle("error", Number.isNaN(val) || (campo === "precio" && val === null && v.precio > 0));
    const c = cambios.get(vid) || {};
    const orig = valorOriginal(v, campo);
    const igual = campo === "sku" ? val === orig : (val === orig || (val !== null && orig !== null && Math.abs(val - orig) < 0.005));
    if (igual) delete c[campo]; else c[campo] = val;
    Object.keys(c).length ? cambios.set(vid, c) : cambios.delete(vid);
    inp.classList.toggle("modificado", !igual);
    actualizar();
  });
  ["#d-nombre", "#d-marca"].forEach((s) => $(s, cajon).oninput = actualizar);
  $("#d-pub", cajon).onchange = actualizar;

  $$("[data-todas]", cajon).forEach((b) => b.onclick = async () => {
    if (b.dataset.todas === "infinito") {
      $$('[data-c="stock"]', cajon).forEach((i) => { i.value = ""; i.dispatchEvent(new Event("input")); });
      return;
    }
    const r = await modal({
      titulo: "Mismo precio para todas", icono: "etiqueta",
      html: `<div class="campo"><label for="m-p">Precio</label><div class="prefijo"><span>$</span><input class="input" id="m-p" inputmode="decimal"></div></div>`,
      botones: [{ texto: "Cancelar", valor: null }, { texto: "Aplicar", clase: "primario", valor: (m) => $("#m-p", m).value }],
    });
    if (r) $$('[data-c="precio"]', cajon).forEach((i) => { i.value = r; i.dispatchEvent(new Event("input")); });
  });

  const cerrar = async () => {
    const pendientes = !$("[data-guardar]", cajon).disabled;
    if (pendientes && !(await confirmar("¿Descartar los cambios?", "Hay cambios sin guardar en este producto.", { texto: "Descartar", peligro: true }))) return;
    cerrarCajon();
    document.removeEventListener("keydown", tecla);
  };
  const tecla = (e) => { if (e.key === "Escape" && !$(".modal-fondo")) cerrar(); };
  document.addEventListener("keydown", tecla);
  cortina.onclick = cerrar;
  $$("[data-cerrar]", cajon).forEach((b) => b.onclick = cerrar);
  $("[data-ver]", cajon)?.addEventListener("click", () => abrirWeb(p.url));

  $("[data-guardar]", cajon).onclick = async (e) => {
    if ($(".input.error", cajon)) return avisar("Hay valores que no se entienden (marcados en rojo).", "error");
    const cuerpo = { variantes: [...cambios.entries()].map(([id, c]) => ({ id, ...c })) };
    if ($("#d-nombre", cajon).value.trim() !== original.nombre) cuerpo.nombre = $("#d-nombre", cajon).value.trim();
    if ($("#d-marca", cajon).value.trim() !== original.marca) cuerpo.marca = $("#d-marca", cajon).value.trim();
    if ($("#d-pub", cajon).checked !== original.publicado) cuerpo.publicado = $("#d-pub", cajon).checked;
    const b = e.currentTarget;
    b.disabled = true;
    b.innerHTML = '<div class="rueda" style="width:15px;height:15px;border-width:2px"></div> Guardando…';
    try {
      const r = await api("PUT", `/api/productos/${p.id}`, cuerpo);
      const i = E.paquete.productos.findIndex((x) => x.id === p.id);
      if (i >= 0) E.paquete.productos[i] = r.producto;
      cerrarCajon();
      document.removeEventListener("keydown", tecla);
      avisar(`Guardado: ${r.producto.nombre}`, "exito");
      if ($("#p-tabla")) dibujarProductos();
    } catch (err) {
      avisar(err.message, "error");
      b.disabled = false;
      b.innerHTML = `${ico("check")} Guardar cambios`;
    }
  };
}

/* =====================================================================
   Nuevo producto
   ===================================================================== */
const nuevoBorrador = () => ({
  nombre: "", descripcion: "", marca: "", tags: "", publicado: false, categorias: new Set(), buscarCat: "",
  fotos: [], desplegables: [{ nombre: "Color", valores: [] }], precioBase: "", stockBase: "", filas: {},
});
let NP = nuevoBorrador();

const combinaciones = () => {
  const ds = NP.desplegables.filter((d) => d.nombre.trim() && d.valores.length);
  return ds.reduce((acc, d) => acc.flatMap((c) => d.valores.map((v) => [...c, v])), [[]]);
};
const claveCombo = (c) => c.join("\u0001");
function fila(c) {
  const k = claveCombo(c);
  if (!NP.filas[k]) NP.filas[k] = { precio: NP.precioBase, stock: NP.stockBase, sku: "" };
  return NP.filas[k];
}

async function paginaNuevo(el) {
  el.innerHTML = `<div class="pagina">${cabecera("Nuevo producto", "")}${cargando()}</div>`;
  try { await paquete(); } catch (e) { return errorPagina(el, e); }
  const pq = E.paquete;
  el.innerHTML = `<div class="pagina">
    ${cabecera("Nuevo producto", "Completá los datos y el producto se crea directo en tu tienda. Solo el nombre es obligatorio; lo demás lo podés completar después.")}
    <div class="grilla-2" style="grid-template-columns:1.5fr 1fr;align-items:start">
      <div class="pila" style="gap:16px">
        <div class="tarjeta"><div class="cuerpo pila">
          <div class="campo"><label for="n-nombre">Nombre del producto *</label><input class="input" id="n-nombre" value="${esc(NP.nombre)}" placeholder="Ej: Lámpara colgante Nórdica"></div>
          <div class="campo"><label for="n-desc">Descripción</label><textarea class="input" id="n-desc" rows="6" placeholder="Contá qué es, medidas, materiales, para qué sirve…">${esc(NP.descripcion)}</textarea>
            <span class="ayuda">Separá los párrafos con una línea en blanco.</span></div>
        </div></div>
        <div class="tarjeta"><div class="cab"><h2>Fotos</h2><span class="espacio"></span><span class="tenue" style="font-size:13px">Arrastrá para ordenar</span></div>
          <div class="cuerpo pila"><div class="fotos-carga" id="n-fotos"></div>
            <p class="tenue" style="font-size:12.5px">${ico("info")} La primera es la principal: se sube cuadrada (1280×1280) para que la grilla de tu tienda quede pareja. Las demás van tal cual.</p></div></div>
        <div class="tarjeta"><div class="cab"><h2>Variantes</h2></div><div class="cuerpo pila">
          <p class="texto-2" style="font-size:13.5px">¿Se vende en distintos colores, tamaños o modelos? Agregá hasta 3 desplegables y se arman todas las combinaciones. Si es un producto único, dejalo vacío.</p>
          <div id="n-desp" class="pila chica"></div>
          <div class="grilla-3" style="align-items:end">
            <div class="campo"><label for="n-precio">Precio</label><div class="prefijo"><span>$</span><input class="input" id="n-precio" inputmode="decimal" value="${esc(NP.precioBase)}"></div></div>
            <div class="campo"><label for="n-stock">Stock</label><input class="input" id="n-stock" inputmode="numeric" placeholder="∞ infinito" value="${esc(NP.stockBase)}"></div>
            <button class="btn" id="n-a-todas">Aplicar a todas</button>
          </div>
          <div id="n-vars"></div>
        </div></div>
      </div>
      <div class="pila" style="gap:16px;position:sticky;top:20px">
        <div class="tarjeta"><div class="cuerpo pila">
          <label class="interruptor"><input type="checkbox" id="n-pub" ${NP.publicado ? "checked" : ""}><span><strong>Publicarlo ya</strong></span></label>
          <p class="tenue" style="font-size:13px;margin-top:-4px">Si lo dejás apagado se crea oculto: lo revisás en la tienda y lo publicás cuando quieras.</p>
        </div></div>
        <div class="tarjeta"><div class="cab"><h2>Organización</h2></div><div class="cuerpo pila">
          <div class="campo"><label for="n-marca">Marca</label><input class="input" id="n-marca" list="n-marcas" value="${esc(NP.marca)}">
            <datalist id="n-marcas">${pq.marcas.map((m) => `<option value="${esc(m)}">`).join("")}</datalist></div>
          <div class="campo"><label>Categorías</label>
            <div class="input-icono">${ico("buscar")}<input class="input chico" id="n-bcat" placeholder="Buscar categoría" value="${esc(NP.buscarCat)}"></div>
            <div class="lista-cats" id="n-cats"></div>
            <span class="ayuda">Si elegís una subcategoría, la categoría de arriba se agrega sola.</span></div>
          <div class="campo"><label for="n-tags">Etiquetas de búsqueda</label><input class="input" id="n-tags" value="${esc(NP.tags)}" placeholder="colgante, nórdico, madera">
            <span class="ayuda">Separadas por coma. Ayudan a que te encuentren en el buscador de la tienda.</span></div>
        </div></div>
        <div class="tarjeta"><div class="cuerpo pila">
          <button class="btn primario grande" id="n-crear">${ico("check")} Crear producto</button>
          <button class="btn fantasma" id="n-limpiar">Empezar de nuevo</button>
        </div></div>
      </div>
    </div></div>`;

  const bind = (sel, campo, ev = "input") => $(sel, el).addEventListener(ev, (e) => { NP[campo] = e.target.type === "checkbox" ? e.target.checked : e.target.value; });
  bind("#n-nombre", "nombre"); bind("#n-desc", "descripcion"); bind("#n-marca", "marca"); bind("#n-tags", "tags"); bind("#n-pub", "publicado", "change");
  $("#n-precio", el).oninput = (e) => { NP.precioBase = e.target.value; };
  $("#n-stock", el).oninput = (e) => { NP.stockBase = e.target.value; };
  $("#n-a-todas", el).onclick = () => {
    combinaciones().forEach((c) => { const f = fila(c); f.precio = NP.precioBase; f.stock = NP.stockBase; });
    dibujarVariantesNuevo();
  };
  $("#n-bcat", el).oninput = (e) => { NP.buscarCat = e.target.value; dibujarCategoriasNuevo(); };
  $("#n-limpiar", el).onclick = async () => {
    if (await confirmar("¿Empezar de nuevo?", "Se borra todo lo que cargaste en este formulario.", { texto: "Borrar formulario", peligro: true })) {
      NP.fotos.forEach((f) => URL.revokeObjectURL(f.url));
      NP = nuevoBorrador();
      paginaNuevo(el);
    }
  };
  $("#n-crear", el).onclick = crearProducto;
  dibujarFotosNuevo(); dibujarDesplegables(); dibujarVariantesNuevo(); dibujarCategoriasNuevo();
}

function dibujarCategoriasNuevo() {
  const q = sinTildes(NP.buscarCat);
  const cats = E.paquete.categorias.filter((c) => !q || sinTildes(c.camino).includes(q));
  const c = $("#n-cats");
  c.innerHTML = cats.length
    ? cats.map((x) => `<label><input type="checkbox" class="check" value="${x.id}" ${NP.categorias.has(x.id) ? "checked" : ""}><span>${esc(x.camino)}</span></label>`).join("")
    : `<div class="tenue" style="padding:8px">${E.paquete.categorias.length ? "Ninguna coincide." : "Tu tienda todavía no tiene categorías."}</div>`;
  $$("input", c).forEach((i) => i.onchange = () => { i.checked ? NP.categorias.add(+i.value) : NP.categorias.delete(+i.value); });
}

function dibujarFotosNuevo() {
  const c = $("#n-fotos");
  c.innerHTML = NP.fotos.map((f, i) => `<div class="foto-item" draggable="true" data-i="${i}">
      <img src="${f.url}" alt="">${i === 0 ? '<span class="etq-principal">Principal</span>' : ""}
      <button class="quitar" data-quitar="${i}" title="Quitar">${ico("x")}</button></div>`).join("")
    + `<label class="foto-agregar">${ico("subir")}<span>Agregar fotos</span><input type="file" accept="image/*" multiple hidden></label>`;
  const agregar = (files) => {
    [...files].filter((f) => f.type.startsWith("image/")).forEach((f) => NP.fotos.push({ archivo: f, url: URL.createObjectURL(f) }));
    dibujarFotosNuevo();
  };
  $("input[type=file]", c).onchange = (e) => agregar(e.target.files);
  $$("[data-quitar]", c).forEach((b) => b.onclick = (e) => {
    e.preventDefault();
    const [f] = NP.fotos.splice(+b.dataset.quitar, 1);
    URL.revokeObjectURL(f.url);
    dibujarFotosNuevo();
  });
  let desde = null;
  $$(".foto-item", c).forEach((it) => {
    it.ondragstart = (e) => { desde = +it.dataset.i; e.dataTransfer.effectAllowed = "move"; };
    it.ondragover = (e) => e.preventDefault();
    it.ondrop = (e) => {
      e.preventDefault();
      if (e.dataTransfer.files.length) return agregar(e.dataTransfer.files);
      const a = +it.dataset.i;
      if (desde === null || desde === a) return;
      const [f] = NP.fotos.splice(desde, 1);
      NP.fotos.splice(a, 0, f);
      desde = null;
      dibujarFotosNuevo();
    };
  });
  c.ondragover = (e) => e.preventDefault();
  c.ondrop = (e) => { if (e.target === c && e.dataTransfer.files.length) { e.preventDefault(); agregar(e.dataTransfer.files); } };
}

function dibujarDesplegables() {
  const c = $("#n-desp");
  c.innerHTML = NP.desplegables.map((d, i) => `<div class="fila" style="align-items:flex-start" data-d="${i}">
      <input class="input" style="width:150px" data-nombre value="${esc(d.nombre)}" placeholder="Ej: Color">
      <div class="valores-chips" style="flex:1">${d.valores.map((v, j) => `<span class="v">${esc(v)}<button data-quitar="${j}" title="Quitar">${ico("x")}</button></span>`).join("")}
        <input data-valor placeholder="${d.valores.length ? "Agregar otro…" : "Escribí un valor y Enter (ej: Negro, Blanco)"}"></div>
      <button class="btn icono fantasma" data-borrar title="Quitar desplegable">${ico("basura")}</button></div>`).join("")
    + (NP.desplegables.length < 3 ? `<div><button class="btn chico" id="n-mas-desp">${ico("mas")} Agregar desplegable</button></div>` : "");
  $$("[data-d]", c).forEach((row) => {
    const d = NP.desplegables[+row.dataset.d];
    $("[data-nombre]", row).oninput = (e) => { d.nombre = e.target.value; dibujarVariantesNuevo(); };
    const inp = $("[data-valor]", row);
    const agregar = (texto) => {
      texto.split(/[,;\n]/).map((x) => x.trim()).filter(Boolean).forEach((x) => { if (!d.valores.includes(x)) d.valores.push(x); });
      dibujarDesplegables(); dibujarVariantesNuevo();
      $(`[data-d="${row.dataset.d}"] [data-valor]`)?.focus();
    };
    inp.onkeydown = (e) => {
      if ((e.key === "Enter" || e.key === ",") && inp.value.trim()) { e.preventDefault(); agregar(inp.value); }
      if (e.key === "Backspace" && !inp.value && d.valores.length) { d.valores.pop(); dibujarDesplegables(); dibujarVariantesNuevo(); $(`[data-d="${row.dataset.d}"] [data-valor]`)?.focus(); }
    };
    inp.onblur = () => { if (inp.value.trim()) agregar(inp.value); };
    inp.onpaste = (e) => { const t = e.clipboardData.getData("text"); if (/[,;\n]/.test(t)) { e.preventDefault(); agregar(t); } };
    $(".valores-chips", row).onclick = (e) => { if (e.target.classList.contains("valores-chips")) inp.focus(); };
    $$("[data-quitar]", row).forEach((b) => b.onclick = () => { d.valores.splice(+b.dataset.quitar, 1); dibujarDesplegables(); dibujarVariantesNuevo(); });
    $("[data-borrar]", row).onclick = () => { NP.desplegables.splice(+row.dataset.d, 1); dibujarDesplegables(); dibujarVariantesNuevo(); };
  });
  $("#n-mas-desp")?.addEventListener("click", () => { NP.desplegables.push({ nombre: "", valores: [] }); dibujarDesplegables(); $$("[data-nombre]").at(-1)?.focus(); });
}

function dibujarVariantesNuevo() {
  const combos = combinaciones();
  const c = $("#n-vars");
  if (combos.length === 1 && !combos[0].length) {
    c.innerHTML = `<p class="tenue" style="font-size:13px">Producto único: se crea con una sola variante con el precio y stock de arriba.</p>`;
    return;
  }
  if (combos.length > 1000) {
    c.innerHTML = `<div class="aviso-caja peligro">${ico("alerta")}<div>Son ${entero(combos.length)} combinaciones: Tiendanube acepta hasta 1000.</div></div>`;
    return;
  }
  c.innerHTML = `<div class="tarjeta tabla-caja" style="max-height:420px"><table class="tabla compacta">
    <thead><tr><th>Variante</th><th class="num">Precio</th><th class="num">Stock</th><th>SKU</th></tr></thead>
    <tbody>${combos.map((cb) => { const f = fila(cb); return `<tr data-k="${esc(claveCombo(cb))}"><td>${esc(cb.join(" · "))}</td>
      <td style="width:130px"><input class="input chico num" data-c="precio" value="${esc(f.precio)}" placeholder="—"></td>
      <td style="width:90px"><input class="input chico num" data-c="stock" value="${esc(f.stock)}" placeholder="∞"></td>
      <td style="width:170px"><input class="input chico" data-c="sku" value="${esc(f.sku)}"></td></tr>`; }).join("")}</tbody></table></div>
    <p class="tenue" style="font-size:12.5px;margin-top:6px">${plural(combos.length, "variante", "variantes")}. Stock vacío = infinito.</p>`;
  $$("tr[data-k] input", c).forEach((i) => i.oninput = () => { NP.filas[i.closest("tr").dataset.k][i.dataset.c] = i.value; });
}

async function crearProducto() {
  const nombre = NP.nombre.trim();
  if (!nombre) { $("#n-nombre").classList.add("error"); $("#n-nombre").focus(); return avisar("Falta el nombre del producto.", "error"); }
  if (E.paquete.productos.some((p) => sinTildes(p.nombre) === sinTildes(nombre))
    && !(await confirmar("Ya existe un producto con ese nombre", `Ya hay un producto llamado <strong>${esc(nombre)}</strong>. ¿Crear otro igual?`, { texto: "Crear igual" }))) return;
  const combos = combinaciones();
  const unico = combos.length === 1 && !combos[0].length;
  const variantes = combos.map((cb) => {
    const f = unico ? { precio: NP.precioBase, stock: NP.stockBase, sku: "" } : fila(cb);
    return { valores: cb, precio: f.precio, stock: f.stock, sku: f.sku };
  });
  const malos = variantes.filter((v) => v.precio && Number.isNaN(numAR(v.precio)));
  if (malos.length) return avisar(`No entiendo el precio «${malos[0].precio}».`, "error");
  const sinPrecio = variantes.filter((v) => !numAR(v.precio)).length;
  if (sinPrecio && !(await confirmar("Hay variantes sin precio", `${plural(sinPrecio, "variante no tiene", "variantes no tienen")} precio: no se van a poder comprar hasta que se lo pongas. ¿Crear igual?`, { texto: "Crear igual" }))) return;

  const datos = {
    nombre, descripcion: NP.descripcion, marca: NP.marca, tags: NP.tags, publicado: NP.publicado,
    categorias: [...NP.categorias], desplegables: unico ? [] : NP.desplegables.filter((d) => d.nombre.trim() && d.valores.length),
    variantes: variantes.map((v) => ({ ...v, precio: v.precio ? numAR(v.precio) : null })),
  };
  const form = new FormData();
  form.append("datos", JSON.stringify(datos));
  NP.fotos.forEach((f) => form.append("fotos", f.archivo, f.archivo.name));
  try {
    const { tarea } = await api("POST", "/api/productos", undefined, form);
    const t = await seguirTarea(tarea, `Creando «${nombre}»`, {
      exito: (r) => `Se creó <strong>${esc(r.producto.nombre)}</strong> con ${plural(r.producto.variantes.length, "variante", "variantes")} y ${plural(r.producto.fotos, "foto", "fotos")}.`,
    });
    if (t?.estado === "listo") {
      NP.fotos.forEach((f) => URL.revokeObjectURL(f.url));
      NP = nuevoBorrador();
      await traerPaquete();
      const id = t.resultado.producto.id;
      const r = await modal({
        titulo: "¡Producto creado!", icono: "check", tono: "exito",
        html: "¿Qué querés hacer ahora?",
        botones: [{ texto: "Cargar otro", valor: "otro" }, { texto: "Ver el producto", clase: "primario", valor: "ver" }],
      });
      location.hash = r === "ver" ? `#/productos?abrir=${id}` : "#/nuevo";
      render();
    }
  } catch (e) { avisar(e.message, "error"); }
}

/* =====================================================================
   Actualizar precios
   ===================================================================== */
const reglaInicial = () => guardado.leer("regla", { descuentos: [], multiplicador: "", iva: "", cotizacion: "", redondeo: "100", modo_redondeo: "cercano" });
const nuevaSesionPrecios = () => ({
  paso: 1, lista: null, hoja: null, enc: null, cCod: null, cPre: null, cDesc: null, modo: "columnas", por: "sku",
  marca: "", regla: reglaInicial(), noBajar: false, vista: null, filtro: "cambios", elegidos: new Set(),
});
let PR = nuevaSesionPrecios();

function calcular(p, r) {
  let x = p;
  (r.descuentos || []).forEach((d) => { x *= 1 - (numAR(d) || 0) / 100; });
  x *= numAR(r.multiplicador) || 1;
  x *= 1 + (numAR(r.iva) || 0) / 100;
  x *= numAR(r.cotizacion) || 1;
  const paso = numAR(r.redondeo) || 0;
  if (paso > 0) {
    if (r.modo_redondeo === "arriba") x = Math.ceil(x / paso) * paso;
    else if (r.modo_redondeo === "abajo") x = Math.floor(x / paso) * paso;
    else x = Math.round(x / paso) * paso;
  } else x = Math.round(x * 100) / 100;
  return x;
}

function pasosPrecios() {
  const nombres = ["La lista", "Cómo leerla", "El cálculo", "Revisar y aplicar"];
  return `<div class="pasos">${nombres.map((n, i) => {
    const k = i + 1;
    const cls = k < PR.paso ? "hecho" : k === PR.paso ? "actual" : "";
    return `<div class="paso ${cls}"><span class="n">${k < PR.paso ? ico("check") : k}</span><span>${n}</span>${k < 4 ? '<span class="linea"></span>' : ""}</div>`;
  }).join("")}</div>`;
}

async function paginaPrecios(el) {
  const intro = "Subí la lista de precios de tu proveedor y la app calcula el precio de venta de cada producto con tu margen. Antes de cambiar nada, te muestra exactamente qué sube, qué baja y cuánto.";
  const cuerpo = (html) => { el.innerHTML = `<div class="pagina">${cabecera("Actualizar precios", intro, PR.paso > 1 ? `<button class="btn fantasma" data-reiniciar>${ico("recargar")} Empezar con otra lista</button>` : "")}${pasosPrecios()}${html}</div>`;
    $("[data-reiniciar]", el)?.addEventListener("click", () => { PR = nuevaSesionPrecios(); paginaPrecios(el); }); };

  if (PR.paso === 1) {
    cuerpo(`<label class="soltar" id="pr-soltar">
        <input type="file" accept=".xlsx,.xlsm,.csv,.txt,.pdf" hidden>
        <div class="ic">${ico("subir")}</div>
        <h2>Arrastrá la lista de precios acá</h2>
        <p class="tenue" style="margin-top:4px">o hacé clic para buscarla · Excel (.xlsx), CSV o PDF</p>
      </label>
      <details class="ayuda-plegable" style="margin-top:18px"><summary>${ico("ayuda")} ¿Cómo funciona?</summary><div class="contenido"><ol>
        <li><strong>Subís la lista</strong> tal como te la manda el proveedor: Excel, CSV o PDF.</li>
        <li><strong>Le decís cómo leerla:</strong> si es una tabla, qué columna es el código y cuál el precio. Si es un catálogo en PDF, la app busca los códigos de tus productos adentro del texto.</li>
        <li><strong>Ponés tu cálculo:</strong> descuentos del proveedor, tu margen, IVA, dólar y redondeo.</li>
        <li><strong>Revisás</strong> la lista de cambios producto por producto, destildás lo que no querés y aplicás. Antes de tocar nada se guarda un respaldo.</li></ol>
        <p style="margin-top:10px">Los productos se reconocen por el <strong>SKU</strong> de cada variante (o por el nombre), comparando sin importar mayúsculas, espacios ni guiones: «VK - Fan 10» encuentra «vk-fan-10».</p></div></details>`);
    const zona = $("#pr-soltar", el);
    const subir = async (archivo) => {
      if (!archivo) return;
      zona.innerHTML = `${cargando(`Leyendo «${archivo.name}»… (un PDF grande puede tardar)`)}`;
      const form = new FormData();
      form.append("archivo", archivo);
      try {
        const r = await api("POST", "/api/precios/archivo", undefined, form);
        PR.lista = r;
        if (r.hojas.length) {
          const h = r.hojas[0];
          Object.assign(PR, { modo: "columnas", hoja: h.nombre, enc: h.sugerido.fila_encabezado, cCod: h.sugerido.col_codigo, cPre: h.sugerido.col_precio, cDesc: h.sugerido.col_desc });
        } else PR.modo = "buscar";
        PR.paso = 2;
        await paquete().catch(() => {});
      } catch (e) { avisar(e.message, "error"); }
      paginaPrecios(el);
    };
    $("input", zona).onchange = (e) => subir(e.target.files[0]);
    zona.ondragover = (e) => { e.preventDefault(); zona.classList.add("encima"); };
    zona.ondragleave = () => zona.classList.remove("encima");
    zona.ondrop = (e) => { e.preventDefault(); zona.classList.remove("encima"); subir(e.dataTransfer.files[0]); };
    return;
  }

  if (PR.paso === 2) {
    const L = PR.lista;
    const hoja = L.hojas.find((h) => h.nombre === PR.hoja) || L.hojas[0];
    const marcas = E.paquete?.marcas || [];
    const opcionesCol = (sel, vacia) => {
      const ancho = hoja ? Math.max(...hoja.filas.map((f) => f.length)) : 0;
      const enc = PR.enc !== null && hoja ? hoja.filas[PR.enc] || [] : [];
      return (vacia ? `<option value="">${vacia}</option>` : "") + Array.from({ length: ancho }, (_, j) =>
        `<option value="${j}" ${sel === j ? "selected" : ""}>${letra(j)}${enc[j] ? ` · ${esc(String(enc[j]).slice(0, 28))}` : ""}</option>`).join("");
    };
    cuerpo(`<div class="tarjeta"><div class="cuerpo pila" style="gap:18px">
      <div class="fila tenue" style="font-size:13px">${ico("archivo")} <strong class="texto-2">${esc(L.nombre)}</strong></div>
      <div class="grilla-2">
        <label class="opcion-modo ${PR.modo === "columnas" ? "activo" : ""}" ${L.hojas.length ? "" : 'style="opacity:.5;pointer-events:none"'}>
          <input type="radio" name="modo" value="columnas" class="check" ${PR.modo === "columnas" ? "checked" : ""}>
          <div><strong>Es una tabla con columnas</strong><p>Hay una columna con el código y otra con el precio (Excel, CSV o PDF con tabla).${L.hojas.length ? "" : " <em>No encontré tablas en este archivo.</em>"}</p></div></label>
        <label class="opcion-modo ${PR.modo === "buscar" ? "activo" : ""}">
          <input type="radio" name="modo" value="buscar" class="check" ${PR.modo === "buscar" ? "checked" : ""}>
          <div><strong>Buscar mis códigos en el texto</strong><p>Para catálogos en PDF donde el precio aparece al lado de cada producto. La app busca cada SKU de tu tienda y toma su precio.</p></div></label>
      </div>
      ${PR.modo === "columnas" && hoja ? `
        <div class="grilla-4">
          ${L.hojas.length > 1 ? `<div class="campo"><label>Hoja</label><select class="input" id="pr-hoja">${L.hojas.map((h) => `<option ${h.nombre === hoja.nombre ? "selected" : ""}>${esc(h.nombre)}</option>`).join("")}</select></div>` : ""}
          <div class="campo"><label>Títulos en la fila</label><select class="input" id="pr-enc"><option value="">No tiene títulos</option>${hoja.filas.slice(0, 30).map((_, i) => `<option value="${i}" ${PR.enc === i ? "selected" : ""}>Fila ${i + 1}</option>`).join("")}</select></div>
          <div class="campo"><label><span class="insignia primario">Código</span> en la columna</label><select class="input" id="pr-cod">${opcionesCol(PR.cCod, "Elegí…")}</select></div>
          <div class="campo"><label><span class="insignia exito">Precio</span> en la columna</label><select class="input" id="pr-pre">${opcionesCol(PR.cPre, "Elegí…")}</select></div>
        </div>
        <div class="tarjeta tabla-caja" style="max-height:340px"><table class="tabla compacta muestra-tabla"><thead><tr><th>#</th>${Array.from({ length: Math.max(...hoja.filas.map((f) => f.length)) }, (_, j) => `<th class="${j === PR.cCod ? "col-codigo" : j === PR.cPre ? "col-precio" : ""}">${letra(j)}</th>`).join("")}</tr></thead>
          <tbody>${hoja.filas.map((f, i) => `<tr class="${i === PR.enc ? "enc" : PR.enc !== null && i < PR.enc ? "antes-enc" : ""}"><td class="tenue">${i + 1}</td>${f.map((x, j) => `<td class="${j === PR.cCod ? "col-codigo" : j === PR.cPre ? "col-precio" : ""}" title="${esc(x)}">${esc(x)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>
        <p class="tenue" style="font-size:12.5px;margin-top:-8px">Se muestran las primeras ${hoja.filas.length} filas de ${entero(hoja.total)}. La columna del código está en azul y la del precio en verde.</p>`
      : `<div class="aviso-caja">${ico("info")}<div>El documento tiene <strong>${entero(L.lineas)} líneas de texto</strong> y encontré <strong>${entero(L.precios_en_texto)} con precios</strong>.
          La app va a buscar cada código de tu tienda en el texto y tomar el primer precio que aparece al lado (o en las líneas de abajo). En la revisión vas a ver la línea exacta de donde salió cada precio.</div></div>`}
      <div class="grilla-2">
        <div class="campo"><label>Reconocer los productos por</label><select class="input" id="pr-por">
          <option value="sku" ${PR.por === "sku" ? "selected" : ""}>SKU de cada variante (recomendado)</option>
          <option value="nombre" ${PR.por === "nombre" ? "selected" : ""}>Nombre del producto (el precio va a todas sus variantes)</option></select>
          <span class="ayuda">El ${PR.modo === "columnas" ? "código de la lista" : "texto"} se compara sin importar mayúsculas, espacios ni guiones.</span></div>
        <div class="campo"><label>Solo productos de la marca</label><select class="input" id="pr-marca"><option value="">Todas las marcas</option>${marcas.map((m) => `<option ${m === PR.marca ? "selected" : ""}>${esc(m)}</option>`).join("")}</select>
          <span class="ayuda">Si la lista es de un solo proveedor, elegí su marca para no tocar productos de otros.</span></div>
      </div>
    </div><div class="pie"><button class="btn" data-atras>${ico("izquierda")} Cambiar de archivo</button><span class="espacio"></span><button class="btn primario" data-sig>Siguiente ${ico("derecha")}</button></div></div>`);
    $$("input[name=modo]", el).forEach((r) => r.onchange = () => { PR.modo = r.value; paginaPrecios(el); });
    $("#pr-hoja", el)?.addEventListener("change", (e) => {
      const h = L.hojas.find((x) => x.nombre === e.target.value);
      Object.assign(PR, { hoja: h.nombre, enc: h.sugerido.fila_encabezado, cCod: h.sugerido.col_codigo, cPre: h.sugerido.col_precio, cDesc: h.sugerido.col_desc });
      paginaPrecios(el);
    });
    const num = (v) => (v === "" ? null : +v);
    $("#pr-enc", el)?.addEventListener("change", (e) => { PR.enc = num(e.target.value); paginaPrecios(el); });
    $("#pr-cod", el)?.addEventListener("change", (e) => { PR.cCod = num(e.target.value); paginaPrecios(el); });
    $("#pr-pre", el)?.addEventListener("change", (e) => { PR.cPre = num(e.target.value); paginaPrecios(el); });
    $("#pr-por", el).onchange = (e) => { PR.por = e.target.value; };
    $("#pr-marca", el).onchange = (e) => { PR.marca = e.target.value; };
    $("[data-atras]", el).onclick = () => { PR = nuevaSesionPrecios(); paginaPrecios(el); };
    $("[data-sig]", el).onclick = () => {
      if (PR.modo === "columnas" && (PR.cCod === null || PR.cPre === null)) return avisar("Elegí qué columna tiene el código y cuál el precio.", "error");
      if (PR.modo === "columnas" && PR.cCod === PR.cPre) return avisar("El código y el precio no pueden estar en la misma columna.", "error");
      PR.paso = 3; paginaPrecios(el);
    };
    return;
  }

  if (PR.paso === 3) {
    const r = PR.regla;
    cuerpo(`<div class="tarjeta"><div class="cuerpo pila" style="gap:20px">
      <div class="grilla-3">
        <div class="campo"><label>Descuentos del proveedor</label>
          <div class="valores-chips" id="pr-desc">${r.descuentos.map((d, i) => `<span class="v">−${esc(d)}%<button data-q="${i}">${ico("x")}</button></span>`).join("")}<input placeholder="${r.descuentos.length ? "Otro…" : "Ej: 30 y Enter"}" inputmode="decimal"></div>
          <span class="ayuda">En cascada: 10 y 5 = −14,5%. Vacío si la lista ya es neta.</span></div>
        <div class="campo"><label for="pr-mult">Margen: multiplicar por</label><div class="prefijo"><span>×</span><input class="input" id="pr-mult" inputmode="decimal" placeholder="1,7" value="${esc(r.multiplicador)}"></div>
          <span class="ayuda" id="pr-mult-ayuda"></span></div>
        <div class="campo"><label for="pr-iva">Sumar IVA</label><div class="prefijo"><span>%</span><input class="input" id="pr-iva" inputmode="decimal" placeholder="0" value="${esc(r.iva)}"></div>
          <span class="ayuda">Si la lista es «+ IVA» y vendés con IVA incluido, poné 21.</span></div>
        <div class="campo"><label for="pr-cot">Cotización del dólar</label><div class="prefijo"><span>$</span><input class="input" id="pr-cot" inputmode="decimal" placeholder="1" value="${esc(r.cotizacion)}"></div>
          <span class="ayuda">Solo si la lista está en dólares. En pesos, dejalo vacío.</span></div>
        <div class="campo"><label for="pr-red">Redondear a</label><div class="fila">
          <select class="input" id="pr-red">${[["0", "Sin redondear"], ["1", "$1"], ["10", "$10"], ["50", "$50"], ["100", "$100"], ["500", "$500"], ["1000", "$1.000"]].map(([v, t]) => `<option value="${v}" ${String(r.redondeo) === v ? "selected" : ""}>${t}</option>`).join("")}</select>
          <select class="input" id="pr-modo-red">${[["cercano", "el más cercano"], ["arriba", "siempre arriba"], ["abajo", "siempre abajo"]].map(([v, t]) => `<option value="${v}" ${r.modo_redondeo === v ? "selected" : ""}>${t}</option>`).join("")}</select></div></div>
        <div class="campo"><label>&nbsp;</label><label class="interruptor"><input type="checkbox" id="pr-nobajar" ${PR.noBajar ? "checked" : ""}><span><strong>No bajar precios</strong></span></label>
          <span class="ayuda">Si la lista trae un precio menor al actual, esos quedan sin elegir.</span></div>
      </div>
      <div><div class="etiqueta" style="margin-bottom:8px">Así queda un producto de ejemplo</div><div class="ejemplo-regla" id="pr-ej"></div></div>
    </div><div class="pie"><button class="btn" data-atras>${ico("izquierda")} Atrás</button><span class="espacio"></span>
      <button class="btn primario" data-sig>${ico("buscar")} Ver qué cambia</button></div></div>`);
    const ej = () => {
      const base = 10000;
      const pasos = [`Lista ${plata(base)}`];
      r.descuentos.forEach((d) => pasos.push(`− ${d}%`));
      if (numAR(r.multiplicador)) pasos.push(`× ${r.multiplicador}`);
      if (numAR(r.iva)) pasos.push(`+ IVA ${r.iva}%`);
      if (numAR(r.cotizacion) && numAR(r.cotizacion) !== 1) pasos.push(`× dólar ${r.cotizacion}`);
      if (+r.redondeo) pasos.push(`redondeado`);
      $("#pr-ej", el).innerHTML = pasos.map((p, i) => (i ? `${ico("derecha", "tenue")} ` : "") + esc(p)).join(" ") + ` ${ico("flecha", "tenue")} <span class="final">${plata(calcular(base, r))}</span>`;
      const m = numAR(r.multiplicador);
      $("#pr-mult-ayuda", el).textContent = m && !Number.isNaN(m) ? `${porc((m - 1) * 100)} sobre el costo.` : "1,7 = ganás 70% sobre el costo.";
    };
    const bindR = (sel, campo, ev = "input") => $(sel, el).addEventListener(ev, (e) => { r[campo] = e.target.value; ej(); });
    bindR("#pr-mult", "multiplicador"); bindR("#pr-iva", "iva"); bindR("#pr-cot", "cotizacion"); bindR("#pr-red", "redondeo", "change"); bindR("#pr-modo-red", "modo_redondeo", "change");
    $("#pr-nobajar", el).onchange = (e) => { PR.noBajar = e.target.checked; };
    const desc = $("#pr-desc input", el);
    const agregarDesc = () => {
      const x = numAR(desc.value.replace("%", "").replace("-", ""));
      if (x && !Number.isNaN(x) && x < 100) { r.descuentos.push(String(x).replace(".", ",")); paginaPrecios(el); $("#pr-desc input")?.focus(); }
      desc.value = "";
    };
    desc.onkeydown = (e) => {
      if (e.key === "Enter" && desc.value.trim()) { e.preventDefault(); agregarDesc(); }
      if (e.key === "Backspace" && !desc.value && r.descuentos.length) { r.descuentos.pop(); paginaPrecios(el); $("#pr-desc input")?.focus(); }
    };
    desc.onblur = () => { if (desc.value.trim()) agregarDesc(); };
    $$("#pr-desc [data-q]", el).forEach((b) => b.onclick = () => { r.descuentos.splice(+b.dataset.q, 1); paginaPrecios(el); });
    $("[data-atras]", el).onclick = () => { PR.paso = 2; paginaPrecios(el); };
    $("[data-sig]", el).onclick = async (e) => {
      for (const [k, t] of [["multiplicador", "margen"], ["iva", "IVA"], ["cotizacion", "cotización"]]) {
        if (r[k] && Number.isNaN(numAR(r[k]))) return avisar(`No entiendo el valor de ${t}.`, "error");
      }
      guardado.escribir("regla", r);
      const b = e.currentTarget;
      b.disabled = true;
      b.innerHTML = '<div class="rueda" style="width:15px;height:15px;border-width:2px"></div> Comparando con tu tienda…';
      try {
        const v = await api("POST", "/api/precios/vista", {
          lista_id: PR.lista.lista_id, modo: PR.modo, hoja: PR.hoja, fila_encabezado: PR.enc, col_codigo: PR.cCod,
          col_precio: PR.cPre, col_desc: PR.cDesc, por: PR.por, marca: PR.marca, no_bajar: PR.noBajar, regla: r,
        });
        PR.vista = v;
        PR.elegidos = new Set(v.cambios.filter((c) => c.elegido).map((c) => c.clave));
        PR.filtro = v.resumen.con_aviso ? "aviso" : "cambios";
        PR.paso = 4;
      } catch (err) { avisar(err.message, "error"); }
      paginaPrecios(el);
    };
    ej();
    return;
  }

  // ---------------------------------------------------------------- paso 4
  const V = PR.vista;
  const R = V.resumen;
  const filtros = [
    ["cambios", "Con cambio", V.cambios.filter((c) => c.estado !== "igual").length],
    ["sube", "Suben", R.suben], ["baja", "Bajan", R.bajan], ["nuevo", "Sin precio antes", R.nuevos],
    ["aviso", "Para revisar", R.con_aviso], ["igual", "Sin cambio", R.iguales],
    ["sin", "En la lista, no en la tienda", V.total_sin_coincidencia], ["faltan", "En la tienda, no en la lista", V.total_faltan_en_lista],
  ];
  const visibles = V.cambios.filter((c) => ({
    cambios: c.estado !== "igual", sube: c.estado === "sube", baja: c.estado === "baja", nuevo: c.estado === "nuevo",
    aviso: c.avisos.length > 0, igual: c.estado === "igual",
  })[PR.filtro]);
  const elegidos = V.cambios.filter((c) => PR.elegidos.has(c.clave) && c.estado !== "igual");
  let tabla;
  if (PR.filtro === "sin") {
    tabla = V.sin_coincidencia.length ? `<p class="texto-2" style="padding:14px 16px 0;font-size:13px">Estos códigos están en la lista pero no hay ningún producto con ese ${PR.por === "sku" ? "SKU" : "nombre"} ${PR.marca ? `de la marca ${esc(PR.marca)} ` : ""}en tu tienda. Si el producto existe, revisá que su SKU coincida con el código de la lista.</p>
      <div class="tabla-caja" style="max-height:520px"><table class="tabla compacta"><thead><tr><th>Código</th><th class="num">Precio de lista</th><th>Renglón de la lista</th></tr></thead>
      <tbody>${V.sin_coincidencia.map((s) => `<tr><td class="mono">${esc(s.codigo)}</td><td class="num">${plata(s.precio_lista)}</td><td class="tenue" style="font-size:12.5px">${esc(s.origen)}</td></tr>`).join("")}</tbody></table></div>`
      : `<div class="vacio"><h3>Nada por acá</h3><p>Todos los códigos de la lista se encontraron en tu tienda.</p></div>`;
  } else if (PR.filtro === "faltan") {
    tabla = V.faltan_en_lista.length ? `<p class="texto-2" style="padding:14px 16px 0;font-size:13px">Estos productos de tu tienda${PR.marca ? ` (marca ${esc(PR.marca)})` : ""} no aparecen en la lista. No se tocan.</p>
      <div class="tabla-caja" style="max-height:520px"><table class="tabla compacta"><thead><tr><th>Producto</th><th>Variante</th><th>SKU</th></tr></thead>
      <tbody>${V.faltan_en_lista.map((s) => `<tr><td>${esc(s.producto)}</td><td>${esc(s.variante)}</td><td class="mono">${esc(s.sku) || '<span class="tenue">sin SKU</span>'}</td></tr>`).join("")}</tbody></table></div>`
      : `<div class="vacio"><h3>Nada por acá</h3><p>Todos tus productos aparecen en la lista.</p></div>`;
  } else if (!visibles.length) {
    tabla = `<div class="vacio"><h3>Nada por acá</h3><p>No hay productos en este grupo.</p></div>`;
  } else {
    const todos = visibles.filter((c) => c.estado !== "igual").every((c) => PR.elegidos.has(c.clave));
    tabla = `<div class="tabla-caja" style="max-height:560px"><table class="tabla compacta">
      <thead><tr><th style="width:34px">${PR.filtro !== "igual" ? `<input type="checkbox" class="check" id="pr-todos" ${todos ? "checked" : ""}>` : ""}</th>
        <th>Producto</th><th>Código en la lista</th><th class="num">Lista</th><th class="num">Precio actual</th><th class="num">Precio nuevo</th><th class="num">Cambio</th></tr></thead>
      <tbody>${visibles.slice(0, 800).map((c) => `<tr class="${PR.elegidos.has(c.clave) || c.estado === "igual" ? "" : "apagada"}" title="Renglón de la lista: ${esc(c.origen)}">
        <td>${c.estado !== "igual" ? `<input type="checkbox" class="check" data-k="${esc(c.clave)}" ${PR.elegidos.has(c.clave) ? "checked" : ""}>` : ""}</td>
        <td><div style="font-weight:560">${esc(c.producto)}</div><div class="tenue" style="font-size:12.5px">${esc(c.variante)}${c.sku ? ` · <span class="mono">${esc(c.sku)}</span>` : ""}</div>
          ${c.avisos.map((a) => `<div class="insignia alerta" style="margin-top:4px;white-space:normal;height:auto;padding:2px 8px">${ico("alerta")} ${esc(a)}</div>`).join("")}</td>
        <td class="mono">${esc(c.codigo)}</td>
        <td class="num tenue">${plata(c.precio_lista)}</td>
        <td class="num">${c.precio_actual ? plata(c.precio_actual) : '<span class="tenue">sin precio</span>'}</td>
        <td class="num"><strong>${plata(c.precio_nuevo)}</strong></td>
        <td class="num">${c.dif_pct === null ? '<span class="insignia primario">nuevo</span>' : c.estado === "igual" ? '<span class="tenue">=</span>'
          : `<span class="${c.estado}">${ico(c.estado === "sube" ? "sube" : "baja")} ${Math.abs(c.dif_pct) < 0.1
            ? (c.estado === "sube" ? "+" : "−") + plata(Math.abs(c.precio_nuevo - c.precio_actual)) : porc(c.dif_pct)}</span>`}</td></tr>`).join("")}</tbody></table></div>
      ${visibles.length > 800 ? `<p class="tenue" style="padding:10px 16px;font-size:13px">Se muestran 800 de ${entero(visibles.length)}. Los demás también se aplican si están elegidos.</p>` : ""}`;
  }
  cuerpo(`<div class="grilla-4" style="grid-template-columns:repeat(5,1fr);margin-bottom:16px">
      <div class="tarjeta stat"><div class="etq">Encontrados</div><div class="valor">${entero(R.encontrados)}</div><div class="sub">de ${entero(R.leidos)} códigos leídos</div></div>
      <div class="tarjeta stat"><div class="etq">${ico("sube", "sube")} Suben</div><div class="valor">${entero(R.suben)}</div></div>
      <div class="tarjeta stat"><div class="etq">${ico("baja", "baja")} Bajan</div><div class="valor">${entero(R.bajan)}</div></div>
      <div class="tarjeta stat"><div class="etq">${ico("etiqueta")} Sin precio antes</div><div class="valor">${entero(R.nuevos)}</div></div>
      <div class="tarjeta stat" ${R.con_aviso ? 'style="border-color:var(--alerta)"' : ""}><div class="etq">${ico("alerta")} Para revisar</div><div class="valor">${entero(R.con_aviso)}</div><div class="sub">cambian mucho: no se eligen solos</div></div>
    </div>
    ${R.encontrados === 0 ? `<div class="aviso-caja alerta" style="margin-bottom:16px">${ico("alerta")}<div><strong>No encontré ningún producto de la lista en tu tienda.</strong> Revisá que ${PR.por === "sku" ? "los SKU de tus variantes coincidan con los códigos de la lista" : "los nombres coincidan"}${PR.modo === "columnas" ? " y que la columna del código sea la correcta" : ""}. Podés volver atrás y cambiarlo.</div></div>` : ""}
    <div class="tarjeta">
      <div class="barra-herr"><div class="chips">${filtros.map(([k, t, n]) => (n || k === "cambios") ? `<button class="chip ${PR.filtro === k ? "activo" : ""}" data-f="${k}">${t} <span class="cuenta">${entero(n)}</span></button>` : "").join("")}</div></div>
      ${tabla}
      <div class="pie" style="position:sticky;bottom:0"><button class="btn" data-atras>${ico("izquierda")} Cambiar el cálculo</button><span class="espacio"></span>
        <span class="texto-2"><strong>${plural(elegidos.length, "precio", "precios")}</strong> para cambiar</span>
        <button class="btn primario" data-aplicar ${elegidos.length ? "" : "disabled"}>${ico("check")} Aplicar cambios</button></div>
    </div>`);
  $$("[data-f]", el).forEach((b) => b.onclick = () => { PR.filtro = b.dataset.f; paginaPrecios(el); });
  $$("[data-k]", el).forEach((c) => c.onchange = () => { c.checked ? PR.elegidos.add(c.dataset.k) : PR.elegidos.delete(c.dataset.k); paginaPrecios(el); });
  $("#pr-todos", el)?.addEventListener("change", (e) => { visibles.filter((c) => c.estado !== "igual").forEach((c) => (e.target.checked ? PR.elegidos.add(c.clave) : PR.elegidos.delete(c.clave))); paginaPrecios(el); });
  $("[data-atras]", el).onclick = () => { PR.paso = 3; paginaPrecios(el); };
  $("[data-aplicar]", el).onclick = async () => {
    const suben = elegidos.filter((c) => c.estado === "sube").length, bajan = elegidos.filter((c) => c.estado === "baja").length, nuevos = elegidos.filter((c) => c.estado === "nuevo").length;
    const ok = await confirmar(`¿Cambiar ${plural(elegidos.length, "precio", "precios")}?`,
      `<ul style="margin:0 0 12px;padding-left:18px">${suben ? `<li>${plural(suben, "sube", "suben")}</li>` : ""}${bajan ? `<li>${plural(bajan, "baja", "bajan")}</li>` : ""}${nuevos ? `<li>${plural(nuevos, "no tenía", "no tenían")} precio</li>` : ""}</ul>
       <div class="aviso-caja">${ico("escudo")}<div>Antes de cambiar se guarda un respaldo de estos productos.</div></div>`, { texto: "Aplicar cambios", icono: "etiqueta" });
    if (!ok) return;
    try {
      const { tarea } = await api("POST", "/api/precios/aplicar", { vista_id: V.vista_id, claves: elegidos.map((c) => c.clave) });
      const t = await seguirTarea(tarea, "Actualizando precios", { exito: (r) => `Listo: ${plural(r.hechos, "precio actualizado", "precios actualizados")} en tu tienda.` });
      if (t?.estado === "listo" || t?.estado === "cancelada") {
        E.paquete = null;
        PR = nuevaSesionPrecios();
        paginaPrecios(el);
      }
    } catch (e) { avisar(e.message, "error"); }
  };
}

/* =====================================================================
   Edición con Excel
   ===================================================================== */
const EX = { marca: "", exportado: null, comp: null, elegidos: new Set(), campo: "" };

function valorCampo(campo, v) {
  if (campo === "precio" || campo === "promocional") return v === null || v === undefined ? '<span class="tenue">vacío</span>' : plata(v);
  if (campo === "stock") return v === null ? '<span class="tenue">∞ infinito</span>' : entero(v);
  if (campo === "publicado") return v ? "Sí" : "No";
  return v === "" || v === null ? '<span class="tenue">vacío</span>' : esc(v);
}

async function paginaExcel(el) {
  el.innerHTML = `<div class="pagina">${cabecera("Edición con Excel", "")}${cargando()}</div>`;
  try { await paquete(); } catch (e) { return errorPagina(el, e); }
  const C = EX.comp;
  let revision = "";
  if (C) {
    const campos = [...new Set(C.cambios.map((c) => c.campo_texto))];
    const vis = C.cambios.map((c, i) => [c, i]).filter(([c]) => !EX.campo || c.campo_texto === EX.campo);
    const todos = vis.every(([, i]) => EX.elegidos.has(i));
    revision = `<div class="tarjeta" style="margin-top:20px">
      <div class="cab"><h2>Cambios encontrados en la planilla</h2><span class="espacio"></span><span class="tenue" style="font-size:13px">${plural(C.filas, "fila leída", "filas leídas")}</span></div>
      ${C.errores.length ? `<div style="padding:16px 20px 0"><div class="aviso-caja alerta">${ico("alerta")}<div><strong>${plural(C.errores.length, "fila tiene", "filas tienen")} algo raro (no se aplican):</strong>
        <ul style="margin:6px 0 0;padding-left:18px">${C.errores.slice(0, 12).map((e) => `<li>Fila ${e.fila}: ${esc(e.mensaje)}</li>`).join("")}</ul>${C.errores.length > 12 ? `<div class="tenue">… y ${C.errores.length - 12} más.</div>` : ""}</div></div></div>` : ""}
      ${C.cambios.length ? `
        <div class="barra-herr" style="border-bottom:1px solid var(--borde)"><div class="chips">
          <button class="chip ${!EX.campo ? "activo" : ""}" data-campo="">Todos <span class="cuenta">${entero(C.cambios.length)}</span></button>
          ${campos.map((k) => `<button class="chip ${EX.campo === k ? "activo" : ""}" data-campo="${esc(k)}">${esc(k)} <span class="cuenta">${entero(C.cambios.filter((c) => c.campo_texto === k).length)}</span></button>`).join("")}</div></div>
        <div class="tabla-caja" style="max-height:540px"><table class="tabla compacta">
        <thead><tr><th style="width:34px"><input type="checkbox" class="check" id="ex-todos" ${todos ? "checked" : ""}></th><th>Producto</th><th>Variante</th><th>Qué cambia</th><th class="num">Antes</th><th></th><th class="num">Después</th></tr></thead>
        <tbody>${vis.slice(0, 1000).map(([c, i]) => `<tr class="${EX.elegidos.has(i) ? "" : "apagada"}">
          <td><input type="checkbox" class="check" data-i="${i}" ${EX.elegidos.has(i) ? "checked" : ""}></td>
          <td style="font-weight:560">${esc(c.producto)}</td><td class="tenue">${esc(c.variante)}</td>
          <td><span class="insignia">${esc(c.campo_texto)}</span></td>
          <td class="num tenue">${valorCampo(c.campo, c.antes)}</td><td class="tenue" style="width:20px">${ico("flecha")}</td>
          <td class="num"><strong>${valorCampo(c.campo, c.despues)}</strong></td></tr>`).join("")}</tbody></table></div>
        <div class="pie"><button class="btn" data-descartar>Descartar</button><span class="espacio"></span>
          <span class="texto-2"><strong>${plural(EX.elegidos.size, "cambio", "cambios")}</strong> en ${plural(new Set([...EX.elegidos].map((i) => C.cambios[i].producto_id)).size, "producto", "productos")}</span>
          <button class="btn primario" data-aplicar ${EX.elegidos.size ? "" : "disabled"}>${ico("check")} Aplicar cambios</button></div>`
      : `<div class="vacio"><div class="ic">${ico("check")}</div><h3>No hay cambios</h3><p>La planilla dice lo mismo que tu tienda.</p><button class="btn" data-descartar style="margin-top:12px">Cerrar</button></div>`}
    </div>`;
  }
  el.innerHTML = `<div class="pagina">
    ${cabecera("Edición con Excel", "Cambiá precios, stock, nombres o SKU de muchos productos a la vez usando Excel (o Google Sheets). Exportás la planilla, la editás y la volvés a subir: antes de aplicar ves cada cambio.")}
    <div class="grilla-2">
      <div class="tarjeta"><div class="cab"><span class="insignia primario">1</span><h2>Exportar la planilla</h2></div><div class="cuerpo pila">
        <p class="texto-2">Una fila por variante, con todas las columnas listas para editar. Las columnas <strong style="color:var(--exito)">verdes</strong> se pueden cambiar; las grises no.</p>
        <div class="campo"><label>Productos</label><select class="input" id="ex-marca"><option value="">Toda la tienda (${plural(E.paquete.productos.length, "producto", "productos")})</option>
          ${E.paquete.marcas.map((m) => `<option ${m === EX.marca ? "selected" : ""}>${esc(m)}</option>`).join("")}</select></div>
        <div><button class="btn primario" id="ex-exportar">${ico("bajar")} Exportar planilla</button></div>
        ${EX.exportado ? `<div class="aviso-caja exito">${ico("check")}<div style="min-width:0"><strong>Planilla lista</strong> · ${plural(EX.exportado.productos, "producto", "productos")}, ${plural(EX.exportado.variantes, "variante", "variantes")}
          <div class="mono tenue" style="font-size:12px;word-break:break-all;margin:4px 0 8px">${esc(EX.exportado.ruta)}</div>
          <div class="fila"><button class="btn chico" data-abrir="archivo">${ico("externo")} Abrir en Excel</button><button class="btn chico" data-abrir="carpeta">${ico("carpeta")} Mostrar en la carpeta</button></div></div></div>` : ""}
      </div></div>
      <div class="tarjeta"><div class="cab"><span class="insignia primario">2</span><h2>Subir la planilla editada</h2></div><div class="cuerpo pila">
        <label class="soltar" id="ex-soltar" style="padding:30px 20px"><input type="file" accept=".xlsx,.xlsm" hidden>
          <div class="ic" style="width:46px;height:46px">${ico("subir")}</div><h3>Arrastrá la planilla acá</h3><p class="tenue" style="font-size:13px">o hacé clic para buscarla (.xlsx)</p></label>
        <p class="tenue" style="font-size:12.5px">${ico("info")} Nada cambia hasta que revises la lista y confirmes. Podés borrar filas que no quieras tocar.</p>
      </div></div>
    </div>
    ${revision}</div>`;

  $("#ex-marca", el).onchange = (e) => { EX.marca = e.target.value; };
  $("#ex-exportar", el).onclick = async (e) => {
    const b = e.currentTarget;
    b.disabled = true;
    b.innerHTML = '<div class="rueda" style="width:15px;height:15px;border-width:2px"></div> Armando la planilla…';
    try { EX.exportado = await api("POST", "/api/excel/exportar", { marca: EX.marca }); avisar("Planilla exportada.", "exito"); } catch (err) { avisar(err.message, "error"); }
    paginaExcel(el);
  };
  $$("[data-abrir]", el).forEach((b) => b.onclick = () => abrirRuta(EX.exportado.ruta, b.dataset.abrir === "carpeta"));
  const zona = $("#ex-soltar", el);
  const subir = async (archivo) => {
    if (!archivo) return;
    zona.innerHTML = cargando("Comparando la planilla con tu tienda…");
    const form = new FormData();
    form.append("archivo", archivo);
    try {
      EX.comp = await api("POST", "/api/excel/importar", undefined, form);
      EX.elegidos = new Set(EX.comp.cambios.map((_, i) => i));
      EX.campo = "";
    } catch (err) { avisar(err.message, "error"); }
    paginaExcel(el);
  };
  $("input", zona).onchange = (e) => subir(e.target.files[0]);
  zona.ondragover = (e) => { e.preventDefault(); zona.classList.add("encima"); };
  zona.ondragleave = () => zona.classList.remove("encima");
  zona.ondrop = (e) => { e.preventDefault(); zona.classList.remove("encima"); subir(e.dataTransfer.files[0]); };

  if (!C) return;
  $$("[data-campo]", el).forEach((b) => b.onclick = () => { EX.campo = b.dataset.campo; paginaExcel(el); });
  $$("[data-i]", el).forEach((c) => c.onchange = () => { c.checked ? EX.elegidos.add(+c.dataset.i) : EX.elegidos.delete(+c.dataset.i); paginaExcel(el); });
  $("#ex-todos", el)?.addEventListener("change", (e) => {
    C.cambios.forEach((c, i) => { if (!EX.campo || c.campo_texto === EX.campo) e.target.checked ? EX.elegidos.add(i) : EX.elegidos.delete(i); });
    paginaExcel(el);
  });
  $$("[data-descartar]", el).forEach((b) => b.onclick = () => { EX.comp = null; paginaExcel(el); });
  $("[data-aplicar]", el)?.addEventListener("click", async () => {
    const n = EX.elegidos.size;
    const ok = await confirmar(`¿Aplicar ${plural(n, "cambio", "cambios")}?`,
      `Se actualizan en tu tienda ahora.<div class="aviso-caja" style="margin-top:12px">${ico("escudo")}<div>Antes se guarda un respaldo de los productos que cambian.</div></div>`, { texto: "Aplicar cambios", icono: "planilla" });
    if (!ok) return;
    try {
      const { tarea } = await api("POST", "/api/excel/aplicar", { importacion_id: C.importacion_id, indices: [...EX.elegidos] });
      const t = await seguirTarea(tarea, "Aplicando la planilla", { exito: (r) => `Listo: ${plural(r.hechos, "producto actualizado", "productos actualizados")}.` });
      if (t?.estado === "listo" || t?.estado === "cancelada") { EX.comp = null; E.paquete = null; paginaExcel(el); }
    } catch (e) { avisar(e.message, "error"); }
  });
}

/* =====================================================================
   Copias de seguridad
   ===================================================================== */
async function paginaRespaldos(el) {
  el.innerHTML = `<div class="pagina">${cabecera("Copias de seguridad", "")}${cargando()}</div>`;
  let d;
  try { d = await api("GET", "/api/respaldos"); } catch (e) { return errorPagina(el, e); }
  el.innerHTML = `<div class="pagina">
    ${cabecera("Copias de seguridad", "Una copia guarda en tu computadora todos los datos de tus productos: nombres, descripciones, variantes, precios, stock, SKU, categorías y links de las fotos.",
      `<button class="btn primario" data-crear>${ico("escudo")} Hacer una copia ahora</button>`)}
    <div class="aviso-caja" style="margin-bottom:18px">${ico("info")}<div>Además, <strong>antes de cada cambio masivo</strong> (actualizar precios, importar planilla, borrar o ajustar precios) la app guarda sola una copia de los productos que va a tocar. Esas aparecen como «Automática».</div></div>
    <div class="tarjeta">${d.respaldos.length ? `<div class="tabla-caja"><table class="tabla">
      <thead><tr><th>Fecha</th><th>Qué es</th><th class="num">Productos</th><th class="num">Tamaño</th><th></th></tr></thead>
      <tbody>${d.respaldos.map((r) => `<tr>
        <td><strong>${esc(fechaLinda(r.fecha))}</strong></td>
        <td>${r.completo ? '<span class="insignia primario">Completa</span>' : '<span class="insignia">Automática</span>'} <span class="texto-2">${esc(r.motivo)}</span></td>
        <td class="num">${entero(r.productos)}</td><td class="num tenue">${r.mb < 1 ? "< 1" : r.mb.toLocaleString(AR, { maximumFractionDigits: 1 })} MB</td>
        <td class="ajustar"><button class="btn chico" data-abrir="${esc(r.carpeta)}">${ico("carpeta")} Abrir</button>
          <button class="btn chico icono fantasma" data-borrar="${esc(r.nombre)}" title="Borrar esta copia">${ico("basura")}</button></td></tr>`).join("")}</tbody></table></div>`
      : `<div class="vacio"><div class="ic">${ico("escudo")}</div><h3>Todavía no hay copias</h3><p>Hacé la primera: tarda menos de un minuto.</p></div>`}</div>
    <p class="tenue" style="font-size:12.5px;margin-top:12px">Se guardan en <span class="mono">${esc(d.carpeta)}</span></p></div>`;
  $("[data-crear]", el).onclick = async () => {
    try {
      const { tarea } = await api("POST", "/api/respaldos");
      await seguirTarea(tarea, "Haciendo la copia de seguridad", { exito: (r) => `Se guardaron ${plural(r.productos, "producto", "productos")} y ${plural(r.variantes, "variante", "variantes")}.` });
      paginaRespaldos(el);
    } catch (e) { avisar(e.message, "error"); }
  };
  $$("[data-abrir]", el).forEach((b) => b.onclick = () => abrirRuta(b.dataset.abrir));
  $$("[data-borrar]", el).forEach((b) => b.onclick = async () => {
    if (!(await confirmar("¿Borrar esta copia?", "No se puede recuperar.", { texto: "Borrar", peligro: true }))) return;
    try { await api("POST", "/api/respaldos/borrar", { nombre: b.dataset.borrar }); paginaRespaldos(el); } catch (e) { avisar(e.message, "error"); }
  });
}

/* =====================================================================
   Configuración
   ===================================================================== */
function paginaConfig(el) {
  const t = E.estado.tienda || {};
  const tema = guardado.leer("tema", "sistema");
  el.innerHTML = `<div class="pagina" style="max-width:860px">
    ${cabecera("Configuración", "")}
    <div class="pila" style="gap:16px">
      <div class="tarjeta"><div class="cab">${ico("tienda")}<h2>Tienda conectada</h2><span class="espacio"></span><span class="insignia exito"><span class="punto"></span>Conectada</span></div>
        <div class="cuerpo"><div class="grilla-2">
          <div><div class="tenue" style="font-size:12.5px">Nombre</div><strong>${esc(t.nombre || "—")}</strong></div>
          <div><div class="tenue" style="font-size:12.5px">Número de tienda</div><span class="mono">${esc(t.id)}</span></div>
          <div><div class="tenue" style="font-size:12.5px">Dirección</div>${t.url ? `<a href="#" data-web="${esc(t.url)}">${esc(t.url)}</a>` : "—"}</div>
          <div><div class="tenue" style="font-size:12.5px">Conectada</div>${esc(fechaLinda(t.conectada) || "—")}</div>
        </div></div>
        <div class="pie"><span class="tenue" style="font-size:13px;flex:1">El acceso se guarda solo en esta computadora, en tu usuario de Windows.</span>
          <button class="btn peligro-suave" data-salir>${ico("salir")} Desconectar</button></div></div>
      <div class="tarjeta"><div class="cab">${ico("sol")}<h2>Apariencia</h2></div><div class="cuerpo">
        <div class="pestanas">${[["sistema", "monitor", "Como Windows"], ["claro", "sol", "Claro"], ["oscuro", "luna", "Oscuro"]].map(([k, i, n]) => `<button data-tema="${k}" class="${tema === k ? "activo" : ""}">${ico(i)} ${n}</button>`).join("")}</div></div></div>
      <div class="tarjeta"><div class="cab">${ico("carpeta")}<h2>Tus datos</h2></div><div class="cuerpo pila">
        <p class="texto-2">Copias de seguridad y configuración:</p>
        <div class="fila"><span class="mono tenue" style="flex:1;word-break:break-all">${esc(E.estado.carpeta_datos)}</span><button class="btn chico" data-carpeta>${ico("carpeta")} Abrir</button></div>
        <p class="tenue" style="font-size:13px">Las planillas exportadas van a <span class="mono">Documentos\\${esc(document.title)}</span>.</p></div></div>
      <div class="tarjeta"><div class="cuerpo fila"><img src="/web/icono.svg" width="40" height="40" alt="">
        <div style="flex:1"><strong>${esc(document.title)}</strong> <span class="tenue">versión ${esc(VERSION)}</span><div class="tenue" style="font-size:13px">Gestor de productos para Tiendanube.</div></div></div></div>
    </div></div>`;
  $$("[data-web]", el).forEach((a) => a.onclick = (e) => { e.preventDefault(); abrirWeb(a.dataset.web); });
  $$("[data-tema]", el).forEach((b) => b.onclick = () => { guardado.escribir("tema", b.dataset.tema); aplicarTema(b.dataset.tema); paginaConfig(el); });
  $("[data-carpeta]", el).onclick = () => abrirRuta(E.estado.carpeta_datos);
  $("[data-salir]", el).onclick = async () => {
    if (!(await confirmar("¿Desconectar la tienda?", "La app deja de tener acceso a tu tienda en esta computadora. Tus productos no se tocan. Para volver a usarla vas a tener que conectarla de nuevo.", { texto: "Desconectar", peligro: true }))) return;
    await api("POST", "/api/conexion/salir");
    E.estado = await api("GET", "/api/estado");
    E.paquete = null;
    location.hash = "";
    render();
  };
}

/* =====================================================================
   Arranque
   ===================================================================== */
const PAGINAS = {
  inicio: paginaInicio, productos: paginaProductos, nuevo: paginaNuevo, precios: paginaPrecios,
  excel: paginaExcel, respaldos: paginaRespaldos, config: paginaConfig,
};

async function arrancar() {
  aplicarTema(guardado.leer("tema", "sistema"));
  try { E.estado = await api("GET", "/api/estado"); } catch (e) { $("#principal").innerHTML = `<div class="pagina"><div class="aviso-caja peligro">${ico("alerta")}<div>${esc(e.message)}</div></div></div>`; return; }
  window.addEventListener("hashchange", render);
  render();
}
arrancar();
