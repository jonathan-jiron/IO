"""Servidor web (Flask) del planificador PERT-CPM asistido por IA.

Ejecutar:  python server.py   y abrir http://127.0.0.1:8765
"""
from __future__ import annotations

import webbrowser
from threading import Timer

from flask import Flask, jsonify, request, send_from_directory

import config
import cpm
import intake
from cpm import Activity, NetworkError
from gemini_client import GeminiError, analyze_request, generate_plan
from kb import KB, kb_context, retrieve

app = Flask(__name__, static_folder="static", static_url_path="/static")


def to_acts(items: list[dict]) -> list[Activity]:
    acts = []
    for x in items:
        acts.append(
            Activity(
                id=str(x["id"]), name=str(x.get("name", "")),
                preds=[str(p) for p in x.get("preds", [])],
                a=float(x["a"]), m=float(x["m"]), b=float(x["b"]),
                people=max(1, int(x.get("people", 1))), phase=str(x.get("phase", "")),
                owner=str(x.get("owner", "") or ""),
            )
        )
    return acts


def to_json(acts: list[Activity]) -> list[dict]:
    return [dict(id=a.id, name=a.name, preds=a.preds, a=a.a, m=a.m, b=a.b,
                 people=a.people, phase=a.phase, owner=a.owner) for a in acts]


def analysis(acts: list[Activity], team: int, deadline: float, names=None) -> dict:
    res = cpm.compute(acts)
    names = cpm.normalize_names(names, team)
    assign, warns, peak = cpm.assign_team(acts, res, team, names)
    wl = cpm.workload(res, assign, names)
    pdays = sum(r["te"] * r["people"] for r in res.rows)
    return dict(
        activities=to_json(acts),
        rows=res.rows,
        duration=res.duration,
        sigma=res.sigma,
        critical_path=res.critical_path,
        n_critical_paths=len(res.all_critical_paths),
        probability=res.prob_by(deadline) if deadline > 0 else None,
        deadline=deadline,
        assignment=assign,
        warnings=warns,
        peak=peak,
        team=team,
        names=names,
        workload=wl,
        team_stats=dict(
            person_days=round(pdays, 2),
            avg_parallel=round(pdays / res.duration, 2) if res.duration else 0,
            avg_util=round(sum(w["utilization"] for w in wl) / len(wl), 1) if wl else 0,
        ),
    )


def fail(msg: str, status: int = 400, **extra):
    return jsonify(error=msg, **extra), status


GENERIC_HINTS = [
    "Qué tipo de sistema es (web, móvil, escritorio, API, automatización...).",
    "Quiénes lo usarán (tipos de usuario o roles).",
    "Cuáles son sus funciones principales (al menos 2 o 3).",
    "Si requiere integraciones (pagos, correo, otros sistemas) y dónde se publicará.",
]
MIN_WORDS = 6        # menos palabras que esto: se rechaza sin gastar cuota de IA
MIN_KB_SIM = 0.03    # similitud minima con la base de conocimiento (casi cero = sin coincidencia)


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/api/config")
def get_config():
    return jsonify(has_key=bool(config.api_key()), model=config.model())


@app.get("/api/kb")
def kb_list():
    return jsonify([dict(name=p["name"], complexity=p["complexity"],
                         activities=len(p["acts"]), team=p["team"]) for p in KB])


@app.post("/api/generate")
def generate():
    d = request.get_json(force=True)
    desc = (d.get("description") or "").strip()
    key = config.api_key()
    team = int(d.get("team_size") or 4)
    if len(desc.split()) < MIN_WORDS or len(desc) < 15:
        return fail("La descripción es demasiado corta para planificar el proyecto. Describe con más detalle "
                    "qué sistema quieres construir.", 422, code="insufficient", hints=GENERIC_HINTS)
    if not key:
        return fail("Falta la API key de Gemini en el servidor. Abre el archivo app/.env, "
                    "escribe GEMINI_API_KEY=tu_clave y vuelve a intentar (no hace falta reiniciar).")
    try:
        chk = analyze_request(key, config.model(), desc)
    except GeminiError as e:
        return fail(str(e), 502)
    if not chk["is_software"]:
        msg = ("No se detectó un proyecto de software en la descripción. Esta herramienta solo planifica "
               "software (aplicaciones, sistemas, APIs, automatizaciones...). Describe qué sistema o aplicación "
               "quieres construir.")
        if chk["ignored_text"]:
            msg += f" Contenido ignorado: {chk['ignored_text']}"
        return fail(msg, 422, code="not_software")
    if chk["detail_level"] == "insuficiente":
        return fail("El proyecto no está lo suficientemente descrito para hacer una planificación confiable: solo "
                    "se indica una idea general. Añade más detalle y vuelve a intentarlo.", 422,
                    code="insufficient", hints=chk["missing_info"] or GENERIC_HINTS)
    plan_text, sw_desc, ignored = intake.reconcile(desc, chk)
    matches = retrieve(sw_desc, 3)
    if matches[0][1] < MIN_KB_SIM and chk["detail_level"] != "alto":
        return fail("La descripción no coincide con ningún proyecto de la base de conocimiento, así que no hay "
                    "referencias para estimar con confianza. Añade más detalle (tipo de sistema, funciones, "
                    "usuarios) e inténtalo de nuevo.", 422, code="no_kb_match",
                    hints=chk["missing_info"] or GENERIC_HINTS)
    try:
        acts, meta = generate_plan(key, config.model(), plan_text, team,
                                   kb_context(matches))
        out = analysis(acts, team, float(d.get("deadline") or 0), d.get("names"))
    except GeminiError as e:
        return fail(str(e), 502)
    except NetworkError as e:
        return fail(str(e))
    meta["input_check"] = dict(
        ignored_text=ignored, detail_level=chk["detail_level"],
        missing_info=chk["missing_info"], software_description=sw_desc,
    )
    out["meta"] = meta
    out["matches"] = [dict(name=p["name"], similarity=round(s, 3), complexity=p["complexity"],
                           activities=len(p["acts"])) for p, s in matches]
    return jsonify(out)


@app.post("/api/compute")
def compute():
    d = request.get_json(force=True)
    try:
        return jsonify(analysis(to_acts(d["activities"]), int(d.get("team_size") or 4),
                                float(d.get("deadline") or 0), d.get("names")))
    except (NetworkError, ValueError, KeyError) as e:
        return fail(str(e))


@app.post("/api/add")
def add():
    d = request.get_json(force=True)
    try:
        acts = to_acts(d["activities"])
        n = d["new"]
        used = {a.id for a in acts}
        nid = next(f"N{i}" for i in range(1, 1000) if f"N{i}" not in used)
        new = Activity(nid, str(n.get("name", "")).strip(), [], float(n["a"]), float(n["m"]),
                       float(n["b"]), max(1, int(n.get("people", 1))), str(n.get("phase", "")))
        if not new.name:
            return fail("Indica el nombre del paso.")
        acts = cpm.add_activity(acts, new, d.get("pred") or None, d.get("succ") or None)
        return jsonify(analysis(acts, int(d.get("team_size") or 4), float(d.get("deadline") or 0), d.get("names")))
    except (NetworkError, ValueError, KeyError) as e:
        return fail(str(e))


@app.post("/api/delete")
def delete():
    d = request.get_json(force=True)
    try:
        out = cpm.remove_activity(to_acts(d["activities"]), d["id"])
        return jsonify(analysis(out, int(d.get("team_size") or 4), float(d.get("deadline") or 0), d.get("names")))
    except (NetworkError, ValueError, KeyError) as e:
        return fail(str(e))


@app.post("/api/move")
def move():
    """Reubica un paso existente entre un predecesor y un posterior."""
    d = request.get_json(force=True)
    try:
        out = cpm.move_activity(to_acts(d["activities"]), d["id"], d.get("pred") or None, d.get("succ") or None)
        return jsonify(analysis(out, int(d.get("team_size") or 4), float(d.get("deadline") or 0), d.get("names")))
    except (NetworkError, ValueError, KeyError) as e:
        return fail(str(e))


if __name__ == "__main__":
    Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:8765")).start()
    app.run(host="127.0.0.1", port=8765, debug=False)
