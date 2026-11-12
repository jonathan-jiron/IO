"use strict";
const $ = (id) => document.getElementById(id);
let state = null; // ultimo analisis del servidor

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const f2 = (n) => Number(n).toFixed(2);
const cfg = () => ({ team_size: +$("team").value || 4, deadline: +$("deadline").value || 0, names: getNames() });

/* ------------------------------------------------ nombres del equipo */
function getNames() {
  return [...document.querySelectorAll("#nameFields input")].map((i) => i.value.trim());
}
function renderNameFields() {
  const n = Math.max(1, Math.min(30, +$("team").value || 4));
  let saved = [];
  try { saved = JSON.parse(localStorage.getItem("teamNames") || "[]"); } catch (e) {}
  const cur = getNames();
  const box = $("nameFields");
  box.innerHTML = "";
  for (let i = 0; i < n; i++) {
    const inp = document.createElement("input");
    inp.placeholder = `Desarrollador ${i + 1}`;
    inp.value = cur[i] ?? saved[i] ?? "";
    inp.addEventListener("change", () => {
      try { localStorage.setItem("teamNames", JSON.stringify(getNames())); } catch (e) {}
      if (state) recompute(state.activities);
    });
    box.appendChild(inp);
  }
}
renderNameFields();

fetch("/api/config").then((r) => r.json()).then((c) => {
  $("aiDot").className = "dot " + (c.has_key ? "ok" : "bad");
  $("aiText").textContent = c.has_key ? `IA lista (${c.model.split(",")[0]}${c.model.includes(",") ? " +" + (c.model.split(",").length - 1) + " de respaldo" : ""})` : "Falta la API key en el servidor (archivo .env)";
}).catch(() => { $("aiText").textContent = "Sin conexión con el servidor"; });

async function api(path, body) {
  let r;
  try {
    r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  } catch (e) {
    throw new Error("No se pudo contactar con el servidor local. Abre ejecutar.bat, deja su ventana abierta y entra a http://127.0.0.1:8765 (no abras el archivo index.html directamente).");
  }
  const data = await r.json().catch(() => ({}));
  if (!r.ok) { const err = new Error(data.error || "Error " + r.status); err.hints = data.hints || []; throw err; }
  return data;
}

function showError(id, msg, hints) {
  const el = $(id);
  el.innerHTML = msg
    ? esc(msg) + (hints && hints.length
        ? `<div class="hints"><b>Para poder planificar, indica:</b><ul>${hints.map((h) => `<li>${esc(h)}</li>`).join("")}</ul></div>` : "")
    : "";
  el.hidden = !msg;
  if (msg) el.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

/* ------------------------------------------------------------ generar */
$("btnGen").addEventListener("click", async () => {
  showError("error", "");
  const btn = $("btnGen");
  btn.disabled = true;
  btn.classList.add("loading");
  btn.querySelector(".btxt").textContent = "Generando plan…";
  $("status").textContent = "Consultando a la IA… puede tardar hasta un par de minutos.";
  try {
    const data = await api("/api/generate", {
      description: $("desc").value, ...cfg(),
    });
    state = data;
    render(data, true);
    $("results").hidden = false;
    $("empty").hidden = true;
    gZoom = null; pick = 0;
    showTab("plan");
    $("results").scrollIntoView({ behavior: "smooth" });
  } catch (e) {
    showError("error", e.message, e.hints);
  } finally {
    btn.disabled = false;
    btn.classList.remove("loading");
    btn.querySelector(".btxt").textContent = state ? "Volver a generar plan" : "Generar plan";
    $("status").textContent = "";
  }
});

async function recompute(activities) {
  try {
    const data = await api("/api/compute", { activities, ...cfg() });
    keepMeta(data);
    state = data;
    render(data, false);
  } catch (e) {
    alert(e.message);
    render(state, false); // restaura valores previos en la tabla
  }
}
function keepMeta(data) {
  if (state) { data.meta = state.meta; data.matches = state.matches; }
}

$("deadline").addEventListener("change", () => { if (state) recompute(state.activities); });
$("team").addEventListener("change", () => { renderNameFields(); if (state) recompute(state.activities); });

/* ------------------------------------------------------------- render */
function render(d, full) {
  if (full) renderTop(d);
  renderCritical(d);
  renderTable(d);
  renderGantt(d);
  renderTeam(d);
  renderAssignment(d);
  renderAddSelects(d);
  renderGraph(d);
  renderNotice(d);
  refreshEditPanel();
}

function renderTop(d) {
  const m = d.meta || {};
  $("kpis").innerHTML = [
    [m.complexity_score != null ? m.complexity_score + "/10" : "—", "Complejidad estimada"],
    [d.activities.length, "Actividades"],
    [f2(d.duration) + " d", "Duración esperada"],
    [f2(d.sigma) + " d", "Desviación estándar (σ)"],
  ].map(([v, l]) => `<div class="kpi"><b>${esc(v)}</b><span>${l}</span></div>`).join("");
  $("rationale").textContent = m.complexity_rationale || "";
  $("rationale").hidden = !m.complexity_rationale;
  const ic = m.input_check;
  let icHtml = "";
  if (ic) {
    if (ic.ignored_text)
      icHtml += `<div class="alert info"><b>Se ignoró contenido que no es de software:</b> ${esc(ic.ignored_text)}</div>`;
    if (ic.detail_level === "bajo" || (ic.detail_level === "medio" && ic.missing_info.length))
      icHtml += `<div class="alert warn"><b>${ic.detail_level === "bajo" ? "Descripción poco detallada" : "Descripción con detalle medio"}:</b> el plan se apoya en supuestos y puede variar mucho.` +
        (ic.missing_info.length ? ` Para afinarlo, aclara:<ul>${ic.missing_info.map((q) => `<li>${esc(q)}</li>`).join("")}</ul>` : "") + `</div>`;
  }
  $("inputcheck").innerHTML = icHtml;
  const q = m.quality;
  $("quality").innerHTML = !q ? "" : q.passed
    ? `<div class="alert ok">✔ El plan pasó las verificaciones de calidad${q.attempts > 1 ? ` tras ${q.attempts} intento(s): la IA corrigió ${q.initial_problems.length} observación(es)` : " al primer intento"}.</div>`
    : `<div class="alert warn"><b>Observaciones de calidad pendientes</b> (tras ${q.attempts} intentos). Revísalas o corrígelas con "Añadir paso":<ul>${q.remaining_problems.map((p) => `<li>${esc(p)}</li>`).join("")}</ul></div>`;
  $("matches").innerHTML =
    "<tr><th>Proyecto de referencia</th><th>Similitud</th><th>Complejidad</th><th>Actividades</th></tr>" +
    (d.matches || []).map((x) =>
      `<tr><td>${esc(x.name)}</td><td>${x.similarity}</td><td>${x.complexity}/10</td><td>${x.activities}</td></tr>`).join("");
  const ul = $("assumptions").querySelector("ul");
  ul.innerHTML = (m.assumptions || []).map((a) => `<li>${esc(a)}</li>`).join("");
  $("assumptions").hidden = !(m.assumptions || []).length;
}

function renderCritical(d) {
  const names = Object.fromEntries(d.activities.map((a) => [a.id, a.name]));
  $("critical").innerHTML = d.critical_path
    .map((id) => `<span class="chip" title="${esc(names[id])}">${esc(id)}</span>`)
    .join('<span class="arrow">→</span>');
  $("critNote").textContent = `Tiempo total de la ruta crítica: ${f2(d.duration)} días` +
    (d.n_critical_paths > 1 ? ` · Existen ${d.n_critical_paths} rutas críticas paralelas.` : "");
  $("prob").innerHTML = d.probability == null ? "" :
    `<div class="prob">Probabilidad de terminar en ≤ ${d.deadline} días <b>${(d.probability * 100).toFixed(1)} %</b></div>`;
}

function renderTable(d) {
  const head = ["ID", "Actividad", "Fase", "Predec.", "a", "m", "b", "te", "σ²", "ES", "EF", "LS", "LF", "Holgura", "Pers.", ""];
  const body = d.rows.map((r) => `
    <tr class="${r.critical ? "crit" : ""}">
      <td><b>${esc(r.id)}</b></td><td class="name">${esc(r.name)}</td><td>${esc(r.phase)}</td><td>${esc(r.preds)}</td>
      <td><input data-id="${esc(r.id)}" data-f="a" type="number" min="0" step="0.5" value="${+r.a.toFixed(2)}"></td>
      <td><input data-id="${esc(r.id)}" data-f="m" type="number" min="0" step="0.5" value="${+r.m.toFixed(2)}"></td>
      <td><input data-id="${esc(r.id)}" data-f="b" type="number" min="0" step="0.5" value="${+r.b.toFixed(2)}"></td>
      <td>${f2(r.te)}</td><td>${f2(r.var)}</td><td>${f2(r.ES)}</td><td>${f2(r.EF)}</td><td>${f2(r.LS)}</td><td>${f2(r.LF)}</td>
      <td>${r.critical ? "<b>0.00</b>" : f2(r.slack)}</td>
      <td><input data-id="${esc(r.id)}" data-f="people" type="number" min="1" step="1" value="${r.people}"></td>
      <td style="white-space:nowrap"><button class="xbtn ed" data-edit="${esc(r.id)}" title="Editar o reubicar en el grafo">✎</button><button class="xbtn" data-del="${esc(r.id)}" title="Eliminar paso">✕</button></td>
    </tr>`).join("");
  $("table").innerHTML = `<tr>${head.map((h) => `<th>${h}</th>`).join("")}</tr>${body}`;
}

$("table").addEventListener("change", (e) => {
  const t = e.target;
  if (!t.dataset.f) return;
  const acts = state.activities.map((a) => ({ ...a }));
  const a = acts.find((x) => x.id === t.dataset.id);
  a[t.dataset.f] = +t.value;
  if (a.a > a.m || a.m > a.b) { alert("Se requiere a ≤ m ≤ b."); render(state, false); return; }
  recompute(acts);
});

$("table").addEventListener("click", async (e) => {
  const id = e.target.dataset.del;
  if (!id) return;
  if (!confirm(`¿Eliminar el paso ${id}? Sus sucesores heredarán sus predecesoras.`)) return;
  try {
    const data = await api("/api/delete", { activities: state.activities, id, ...cfg() });
    keepMeta(data); state = data; render(data, false); renderTop(data);
  } catch (err) { alert(err.message); }
});

/* -------------------------------------------------------------- Gantt */
function renderGantt(d) {
  const rows = d.rows;
  const rowH = 30, left = 270, right = 20, top = 30, W = 1000;
  const maxT = Math.max(...rows.map((r) => Math.max(r.EF, r.LF)));
  const sx = (W - left - right) / maxT;
  const H = top + rows.length * rowH + 10;
  const step = niceStep(maxT);
  let s = `<svg style="width:100%;min-width:760px;height:auto" viewBox="0 0 ${W} ${H}" font-family="Segoe UI,sans-serif" font-size="12">`;
  for (let t = 0; t <= maxT + 1e-9; t += step) {
    const x = left + t * sx;
    s += `<line x1="${x}" x2="${x}" y1="${top - 6}" y2="${H - 6}" stroke="#e6e9f2"/>`;
    s += `<text x="${x}" y="${top - 12}" text-anchor="middle" fill="#6b7385">${Math.round(t * 10) / 10}</text>`;
  }
  rows.forEach((r, i) => {
    const y = top + i * rowH;
    const label = `${r.id} · ${r.name}`;
    s += `<text x="${left - 10}" y="${y + 19}" text-anchor="end" fill="#1c2333">${esc(label.length > 38 ? label.slice(0, 37) + "…" : label)}<title>${esc(label)}</title></text>`;
    const slackW = (r.LF - r.EF) * sx;
    if (!r.critical && slackW > 0.5)
      s += `<rect x="${left + r.EF * sx}" y="${y + 7}" width="${slackW}" height="16" rx="3" fill="#cbd2e0" opacity=".6"/>`;
    const w = Math.max(2, r.te * sx);
    const devs = (d.assignment[r.id] || []).join(", ");
    s += `<rect x="${left + r.ES * sx}" y="${y + 5}" width="${w}" height="20" rx="4" fill="${r.critical ? "#f0554a" : "#3b82f6"}">` +
         `<title>${esc(label)}\nInicio ${f2(r.ES)} · Fin ${f2(r.EF)} · ${f2(r.te)} d\n${esc(devs)}</title></rect>`;
    if (w > 46 && devs) {
      const txt = devs.length * 6.2 < w - 8 ? devs : (d.assignment[r.id] || []).length + " pers.";
      s += `<text x="${left + r.ES * sx + 6}" y="${y + 19}" fill="#fff" font-size="11">${esc(txt)}</text>`;
    }
  });
  s += "</svg>";
  $("gantt").innerHTML = s;
}
function niceStep(max) {
  const raw = max / 10, p = Math.pow(10, Math.floor(Math.log10(raw)));
  for (const m of [1, 2, 5, 10]) if (raw <= m * p) return m * p;
  return p * 10;
}

function renderTeam(d) {
  let h = `<p><b>Pico de personas en paralelo:</b> ${d.peak} (equipo disponible: ${d.team})</p>`;
  h += d.warnings.map((w) => `<div class="alert warn">${esc(w)}</div>`).join("");
  if (!d.warnings.length && d.peak <= d.team)
    h += '<div class="alert ok">La asignación en paralelo es factible con el equipo indicado.</div>';
  $("team-info").innerHTML = h;
}

/* ------------------------------------------------------- añadir paso */
function renderAddSelects(d) {
  const opts = '<option value="">— ninguno —</option>' +
    d.activities.map((a) => `<option value="${esc(a.id)}">${esc(a.id)} · ${esc(a.name)}</option>`).join("");
  const p = $("nPred").value, s = $("nSucc").value;
  $("nPred").innerHTML = opts; $("nSucc").innerHTML = opts;
  $("nPred").value = p; $("nSucc").value = s;
}

$("addForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  showError("addError", "");
  const a = +$("nA").value, m = +$("nM").value, b = +$("nB").value;
  if (!(a <= m && m <= b)) return showError("addError", "Se requiere a ≤ m ≤ b.");
  if (!$("nPred").value && !$("nSucc").value) return showError("addError", "Elige al menos un predecesor o un posterior.");
  try {
    const data = await api("/api/add", {
      activities: state.activities, ...cfg(),
      new: { name: $("nName").value, phase: $("nPhase").value, people: +$("nPeople").value, a, m, b },
      pred: $("nPred").value, succ: $("nSucc").value,
    });
    keepMeta(data); state = data; render(data, false); renderTop(data);
    $("addForm").reset(); $("nA").value = 1; $("nM").value = 2; $("nB").value = 4; $("nPeople").value = 1;
    pick = 0; renderGraph(state);
  } catch (err) { showError("addError", err.message); }
});

/* ---------------------------------------------------------------- CSV */
$("btnCsv").addEventListener("click", () => {
  const cols = ["id", "name", "phase", "preds", "a", "m", "b", "te", "var", "ES", "EF", "LS", "LF", "slack", "critical", "people"];
  const q = (v) => '"' + String(v).replace(/"/g, '""') + '"';
  const csv = [cols.join(",")].concat(state.rows.map((r) => cols.map((c) => q(r[c])).join(","))).join("\r\n");
  const url = URL.createObjectURL(new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url; a.download = "pert_cpm.csv"; a.click();
  URL.revokeObjectURL(url);
});

/* ------------------------------------------------ asignacion del equipo */
function teamEvaluation(d) {
  const st = d.team_stats, team = d.team;
  const peak = d.peak;
  const hard = d.warnings.filter((w) => !w.startsWith("Ajuste"));
  const items = [];
  const ai = state && state.meta && state.meta.team_assessment;
  if (ai && ai.verdict && ai.for_team === team) {
    items.push({ kind: ai.verdict, src: "Evaluación de la IA", rec: ai.recommended_team, txt: ai.comment });
  }
  // evaluacion calculada a partir del cronograma (siempre disponible)
  if (hard.length || peak > team) {
    items.push({ kind: "falta", src: "Análisis del cronograma", rec: peak,
      txt: `Hay tareas en paralelo que necesitan hasta ${peak} personas a la vez y el equipo es de ${team}.` });
  } else if (team > peak && st.avg_util < 50) {
    items.push({ kind: "sobra", src: "Análisis del cronograma", rec: Math.max(1, peak),
      txt: `Nunca se necesitan más de ${peak} persona(s) a la vez y la carga promedio es del ${st.avg_util}%: el resto del equipo quedaría ocioso.` });
  } else if (d.probability != null && d.probability < 0.5) {
    items.push({ kind: "falta", src: "Análisis del plazo", rec: null,
      txt: `Con este equipo solo hay ${(d.probability * 100).toFixed(0)}% de probabilidad de cumplir el plazo de ${d.deadline} días.` });
  } else {
    items.push({ kind: "adecuado", src: "Análisis del cronograma", rec: null,
      txt: `Carga promedio del ${st.avg_util}% con un pico de ${peak} persona(s) en paralelo.` });
  }
  // si la IA y el cronograma coinciden, basta una tarjeta (menos saturacion)
  return items.length === 2 && items[0].kind === items[1].kind ? [items[0]] : items;
}

function renderTeamEval(d) {
  const label = { adecuado: "Equipo adecuado", sobra: "Sobran integrantes", falta: "Faltan integrantes" };
  const icon = { adecuado: "✔", sobra: "▼", falta: "▲" };
  $("teamEval").innerHTML = teamEvaluation(d).map((e) => `
    <div class="eval ${e.kind}">
      <div class="eval-ic">${icon[e.kind] || "•"}</div>
      <div><b>${label[e.kind] || "Evaluación"}</b> <span class="src">${esc(e.src)}</span>
        <div>${esc(e.txt || "")}${e.rec ? ` <b>Equipo recomendado: ${e.rec}.</b>` : ""}</div></div>
    </div>`).join("");
}

function renderAssignment(d) {
  renderTeamEval(d);
  $("workload").innerHTML = d.workload.map((w, i) => `
    <div class="dev"><b data-i="${i + 1}">${esc(w.name)}</b>
      <div class="bar"><i style="width:${Math.min(100, w.utilization)}%"></i></div>
      <div class="tk">${f2(w.days)} días de trabajo · ${w.utilization}% del cronograma</div>
      <div class="tk">${w.tasks.length ? "Tareas: " + esc(w.tasks.join(", ")) : "Sin tareas asignadas"}${w.critical ? ` · ${w.critical} crítica(s)` : ""}</div>
    </div>`).join("");
  $("assignTable").innerHTML =
    "<tr><th>ID</th><th>Actividad</th><th>Inicio</th><th>Fin</th><th>Pers.</th><th>Responsables</th></tr>" +
    d.rows.map((r) => `<tr class="${r.critical ? "crit" : ""}"><td><b>${esc(r.id)}</b></td><td class="name">${esc(r.name)}</td>` +
      `<td>${f2(r.ES)}</td><td>${f2(r.EF)}</td><td>${r.people}</td><td>${esc((d.assignment[r.id] || []).join(", "))}</td></tr>`).join("");
}

/* ------------------------------------------------------------ pestañas */
function showTab(name) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  document.querySelectorAll(".tabpage").forEach((p) => { p.hidden = p.id !== "page-" + name; });
  if (name === "graph" && state) renderGraph(state); // recalcula el ajuste con el contenedor visible
}
document.querySelector(".tabs").addEventListener("click", (e) => {
  const t = e.target.closest(".tab");
  if (t) { showTab(t.dataset.tab); window.scrollTo({ top: 0, behavior: "smooth" }); }
});

/* ---------------------------------------- aviso compacto (pagina 1) */
function renderNotice(d) {
  const m = d.meta || {}, ic = m.input_check, q = m.quality;
  const n = [];
  if (ic && ic.ignored_text) n.push("se ignoró contenido que no es de software");
  if (ic && (ic.detail_level === "bajo" || (ic.detail_level === "medio" && ic.missing_info.length))) n.push("descripción poco detallada");
  if (q && !q.passed) n.push(`${q.remaining_problems.length} observación(es) de calidad`);
  const hard = d.warnings.filter((w) => !w.startsWith("Ajuste")).length;
  if (hard) n.push(`${hard} aviso(s) de equipo`);
  $("notice").innerHTML = n.length
    ? `<div class="notice"><span>ℹ ${esc(n.join(" · "))}</span><button class="linkbtn" id="goTeam">Ver detalles →</button></div>` : "";
  const b = $("goTeam");
  if (b) b.addEventListener("click", () => { showTab("team"); window.scrollTo({ top: 0, behavior: "smooth" }); });
}

/* ------------------------------------------------------------- grafo */
let gZoom = null;   // null = ajustar al ancho
let pick = 0;       // 0: siguiente clic = predecesor, 1: siguiente = posterior
const NW = 164, NH = 62, GX = 44, GY = 16, PAD = 22;
const MIN_READABLE = 0.8;   // zoom minimo por defecto para que el texto se lea (si no cabe, se desplaza)

function layoutGraph(d) {
  const preds = Object.fromEntries(d.activities.map((a) => [a.id, a.preds]));
  const level = {};
  const lv = (id) => (level[id] ??= preds[id].length ? 1 + Math.max(...preds[id].map(lv)) : 0);
  d.activities.forEach((a) => lv(a.id));
  const nLayers = Math.max(...Object.values(level)) + 1;
  const layers = Array.from({ length: nLayers }, () => []);
  d.rows.forEach((r) => layers[level[r.id]].push(r.id));   // d.rows viene en orden topologico
  const pos = {};
  layers[0].forEach((id, i) => (pos[id] = i));
  for (let l = 1; l < nLayers; l++) {                       // reduce cruces: baricentro de predecesoras
    const bc = (id) => { const p = preds[id].filter((x) => pos[x] !== undefined); return p.length ? p.reduce((s, x) => s + pos[x], 0) / p.length : 0; };
    layers[l].sort((a, b) => bc(a) - bc(b));
    layers[l].forEach((id, i) => (pos[id] = i));
  }
  const maxH = Math.max(...layers.map((L) => L.length));
  const W = PAD * 2 + nLayers * NW + (nLayers - 1) * GX;
  const H = PAD * 2 + maxH * NH + (maxH - 1) * GY;
  const xy = {};
  layers.forEach((L, l) => {
    const colH = L.length * NH + (L.length - 1) * GY;
    const off = (H - PAD * 2 - colH) / 2;
    L.forEach((id, i) => (xy[id] = { x: PAD + l * (NW + GX), y: PAD + off + i * (NH + GY) }));
  });
  return { xy, W, H, preds };
}

function renderGraph(d) {
  const { xy, W, H, preds } = layoutGraph(d);
  const row = Object.fromEntries(d.rows.map((r) => [r.id, r]));
  const selP = $("nPred").value, selS = $("nSucc").value;
  const trunc = (s, n) => (s.length > n ? s.slice(0, n - 1) + "…" : s);
  let s = `<defs>
    <marker id="arrN" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#9aa3bb"/></marker>
    <marker id="arrC" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#f0554a"/></marker></defs>`;
  let crit = "", norm = "";
  d.activities.forEach((a) => {
    preds[a.id].forEach((p) => {
      const x1 = xy[p].x + NW, y1 = xy[p].y + NH / 2, x2 = xy[a.id].x, y2 = xy[a.id].y + NH / 2;
      const dx = Math.max(24, (x2 - x1) / 2);
      const isCrit = row[p].critical && row[a.id].critical && Math.abs(row[p].EF - row[a.id].ES) < 1e-4;
      const path = `<path d="M${x1} ${y1} C${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2 - 1} ${y2}" fill="none" stroke="${isCrit ? "#f0554a" : "#b4bbd0"}" stroke-width="${isCrit ? 2.4 : 1.4}" marker-end="url(#${isCrit ? "arrC" : "arrN"})"/>`;
      if (isCrit) crit += path; else norm += path;
    });
  });
  s += norm + crit; // las criticas encima
  d.rows.forEach((r) => {
    const p = xy[r.id];
    const tag = gmode === "edit" ? (r.id === editId ? "edit" : "") : (r.id === selP ? "pred" : r.id === selS ? "succ" : "");
    s += `<g class="gnode ${tag}" data-id="${esc(r.id)}" transform="translate(${p.x},${p.y})" style="cursor:pointer">
      <title>${esc(r.id)} · ${esc(r.name)}\nte ${f2(r.te)} d · ES ${f2(r.ES)} · EF ${f2(r.EF)} · holgura ${f2(r.slack)}</title>
      <rect width="${NW}" height="${NH}" rx="10" fill="${r.critical ? "#fff1ef" : "#ffffff"}" stroke="${r.critical ? "#f0554a" : "#3b82f6"}" stroke-width="${r.critical ? 2 : 1.5}"/>
      <text x="12" y="19" font-size="13" font-weight="700" fill="${r.critical ? "#a3261f" : "#1d4ed8"}">${esc(r.id)}</text>
      <text x="${NW - 12}" y="19" font-size="12" text-anchor="end" fill="#1c2333" font-weight="600">${f2(r.te)} d</text>
      <text x="12" y="38" font-size="12" fill="#1c2333">${esc(trunc(r.name, 25))}</text>
      <text x="12" y="54" font-size="10.5" fill="#6b7385">ES ${f2(r.ES)} · EF ${f2(r.EF)} · H ${r.critical ? "0" : f2(r.slack)}</text>
    </g>`;
  });
  const box = $("graph");
  const avail = Math.max(300, box.clientWidth - 4);
  const z = gZoom ?? Math.max(MIN_READABLE, Math.min(1, avail / W));
  s = `<svg width="${Math.round(W * z)}" height="${Math.round(H * z)}" viewBox="0 0 ${W} ${H}" font-family="Segoe UI,sans-serif">${s}</svg>`;
  box.innerHTML = s;
  pickInfo();
}

function pickInfo() {
  if (gmode === "edit") {
    $("pickInfo").innerHTML = editId ? `Paso seleccionado: <b>${esc(editId)}</b>. Edítalo en el panel de abajo.` : "Ningún paso seleccionado.";
    return;
  }
  const p = $("nPred").value, q = $("nSucc").value;
  $("pickInfo").innerHTML = (p || q)
    ? `Seleccionado → predecesor: <b>${p || "—"}</b> · posterior: <b>${q || "—"}</b>. Completa el formulario de abajo.`
    : "Ningún nodo seleccionado.";
}

$("graph").addEventListener("click", (e) => {
  const g = e.target.closest(".gnode");
  if (!g) return;
  const id = g.dataset.id;
  if (gmode === "edit") { fillEdit(id); renderGraph(state); return; }
  if (pick === 0) { $("nPred").value = id; $("nSucc").value = ""; pick = 1; }
  else { if ($("nPred").value === id) { $("nPred").value = ""; pick = 0; } else { $("nSucc").value = id; pick = 0; } }
  renderGraph(state);
  if ($("nPred").value && $("nSucc").value) $("nName").focus();
});
["nPred", "nSucc"].forEach((id) => $(id).addEventListener("change", () => { if (state) renderGraph(state); }));

const fitZoom = () => Math.max(0.25, Math.min(1, ($("graph").clientWidth - 4) / layoutGraph(state).W));
const zoomBy = (f) => { const cur = gZoom ?? Math.max(MIN_READABLE, fitZoom()); gZoom = Math.max(0.25, Math.min(2, cur * f)); renderGraph(state); };
$("zIn").addEventListener("click", () => state && zoomBy(1.2));
$("zOut").addEventListener("click", () => state && zoomBy(1 / 1.2));
$("zFit").addEventListener("click", () => { if (state) { gZoom = fitZoom(); renderGraph(state); } });
$("zFit").title = "Ver todo el grafo en pantalla";
window.addEventListener("resize", () => { if (state && gZoom === null && !$("page-graph").hidden) renderGraph(state); });

/* ------------------------------------------------ ejemplos de demostracion */
fetch("/static/ejemplos.json").then((r) => r.json()).then((list) => {
  const sel = $("exSel");
  list.forEach((e, i) => {
    const o = document.createElement("option");
    o.value = i;
    o.textContent = `${e.tag} · ${e.label}`;
    sel.appendChild(o);
  });
  sel.addEventListener("change", async () => {
    if (sel.value === "") return;
    const e = list[+sel.value];
    $("desc").value = e.description;
    $("team").value = e.team;
    $("deadline").value = e.deadline;
    renderNameFields();
    showError("error", "");
    sel.value = "";            // permite volver a elegir el mismo ejemplo
    if (e.network) {
      // caso de estudio: la red viene dada, se calcula con el motor (sin IA ni cuota)
      try {
        const data = await api("/api/compute", { activities: e.network, ...cfg() });
        data.meta = {
          complexity_score: null,
          complexity_rationale: "Caso de estudio cargado directamente (sin IA): los tiempos y las precedencias son los del informe.",
          assumptions: [], quality: null, input_check: null,
        };
        data.matches = [];
        state = data; gZoom = null; pick = 0; editId = null;
        render(data, true);
        $("results").hidden = false; $("empty").hidden = true;
        showTab("plan");
        window.scrollTo({ top: 0, behavior: "smooth" });
      } catch (err) { showError("error", err.message); }
      return;
    }
    $("desc").focus();
  });
}).catch(() => { $("exSel").closest("label").hidden = true; });

/* ============================================================================
   Edicion de la red desde el grafo: añadir / editar / reubicar / eliminar
   ============================================================================ */
let gmode = "add";   // "add" | "edit"
let editId = null;

function setMode(m) {
  gmode = m;
  document.querySelectorAll(".segbtn").forEach((b) => b.classList.toggle("active", b.dataset.gmode === m));
  $("modeAdd").hidden = m !== "add";
  $("modeEdit").hidden = m !== "edit";
  $("graphHint").innerHTML = m === "add"
    ? "Cada nodo es una actividad (ID, duración esperada, nombre, ES · EF · holgura). Haz clic en un nodo para elegirlo como <b>predecesor</b> y en otro como <b>posterior</b> de un paso nuevo."
    : "Haz clic en un nodo para <b>seleccionar el paso</b> que quieres editar, reubicar o eliminar.";
  pick = 0;
  if (state) { renderGraph(state); }
}
document.querySelector(".seg").addEventListener("click", (e) => {
  const b = e.target.closest(".segbtn");
  if (b) setMode(b.dataset.gmode);
});

const actById = (id) => state.activities.find((a) => a.id === id);
const succsOf = (id) => state.activities.filter((a) => a.preds.includes(id)).map((a) => a.id);

function fillEdit(id) {
  const a = state && actById(id);
  if (!a) { editId = null; $("editBody").hidden = true; $("editHint").hidden = false; return; }
  editId = id;
  $("editHint").hidden = true;
  $("editBody").hidden = false;
  $("editTitle").textContent = `Editando ${a.id} · ${a.name}`;
  $("eName").value = a.name; $("ePhase").value = a.phase || ""; $("ePeople").value = a.people;
  $("eA").value = +a.a.toFixed(2); $("eM").value = +a.m.toFixed(2); $("eB").value = +a.b.toFixed(2);
  const names = state.names || [];
  $("eOwner").innerHTML = '<option value="">— reparto automático —</option>' +
    names.map((n) => `<option value="${esc(n)}">${esc(n)}</option>`).join("");
  $("eOwner").value = names.includes(a.owner) ? a.owner : "";
  const others = state.activities.filter((x) => x.id !== id);
  const opts = '<option value="">— ninguno —</option>' + others.map((x) => `<option value="${esc(x.id)}">${esc(x.id)} · ${esc(x.name)}</option>`).join("");
  $("mvPred").innerHTML = opts; $("mvSucc").innerHTML = opts;
  $("mvPred").value = a.preds[0] || "";
  $("mvSucc").value = succsOf(id)[0] || "";
  showError("editError", "");
}

function refreshEditPanel() {
  if (editId && state && actById(editId)) fillEdit(editId);
  else if (editId) { editId = null; $("editBody").hidden = true; $("editHint").hidden = false; }
}

// Aplica un cambio de la red (calculado en el servidor) y refresca todo
function applyResult(data) {
  keepMeta(data);
  state = data;
  render(data, false);
  renderTop(data);
}

async function editCall(path, body) {
  try {
    applyResult(await api(path, { activities: state.activities, ...cfg(), ...body }));
    showError("editError", "");
    return true;
  } catch (err) {
    showError("editError", err.message);
    return false;
  }
}

$("editForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const a = +$("eA").value, m = +$("eM").value, b = +$("eB").value, p = Math.max(1, Math.round(+$("ePeople").value || 1));
  if (!(a >= 0 && a <= m && m <= b)) return showError("editError", "Se requiere 0 ≤ a ≤ m ≤ b.");
  if (!$("eName").value.trim()) return showError("editError", "El nombre no puede quedar vacío.");
  const acts = state.activities.map((x) => ({ ...x }));
  Object.assign(acts.find((x) => x.id === editId), {
    name: $("eName").value.trim(), phase: $("ePhase").value.trim(), people: p, a, m, b, owner: $("eOwner").value,
  });
  const keep = editId;
  if (await editCall("/api/compute", { activities: acts })) fillEdit(keep);
});

$("btnFactor").addEventListener("click", () => {
  const f = +$("eFactor").value;
  if (!(f > 0)) return showError("editError", "El factor debe ser mayor que 0.");
  ["eA", "eM", "eB"].forEach((id) => { $(id).value = +(+$(id).value * f).toFixed(2); });
  showError("editError", "");
});

$("btnMove").addEventListener("click", async () => {
  const pred = $("mvPred").value, succ = $("mvSucc").value;
  if (!pred && !succ) return showError("editError", "Elige al menos un predecesor o un posterior.");
  const keep = editId;
  if (await editCall("/api/move", { id: keep, pred, succ })) fillEdit(keep);
});

$("btnDel").addEventListener("click", async () => {
  const a = actById(editId);
  if (!a || !confirm(`¿Eliminar el paso ${a.id} · ${a.name}? Esta acción modifica la red.`)) return;
  if (await editCall("/api/delete", { id: a.id })) { editId = null; refreshEditPanel(); renderGraph(state); }
});

// desde la tabla: boton ✎ lleva al grafo con el paso seleccionado
$("table").addEventListener("click", (e) => {
  const id = e.target.dataset && e.target.dataset.edit;
  if (!id) return;
  showTab("graph");
  setMode("edit");
  fillEdit(id);
  renderGraph(state);
  window.scrollTo({ top: 0, behavior: "smooth" });
});
