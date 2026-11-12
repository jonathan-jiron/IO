"""Cliente de Gemini (REST) que devuelve el plan de proyecto en JSON estricto.

Mejora de calidad en tres capas:
  1. responseSchema: Gemini esta obligado a devolver exactamente el formato esperado.
  2. rules.check: reglas de sentido comun verificadas por codigo.
  3. Reintento: si alguna regla falla, se devuelve el error concreto a Gemini para que corrija.
"""
from __future__ import annotations

import json
import re
import time

import requests

import rules
from cpm import Activity, validate, NetworkError

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MAX_ATTEMPTS = 3
TEMPERATURE = 0.2

SYSTEM = """Eres un gerente de proyectos de software experto en PERT-CPM.
Recibes la descripcion de un proyecto y, como referencia, proyectos similares de una base de conocimiento.
Debes producir el plan completo de inicio a fin: requerimientos, diseno, desarrollo, pruebas,
despliegue y entrega/capacitacion al cliente.

Reglas estrictas:
- Usa la base de conocimiento como calibracion de escala: mas complejo => mas actividades y mas dias.
  Un proyecto trivial (complejidad 1-2) tiene ~6-10 actividades y pocos dias; uno muy complejo (8-10) tiene 18 o mas.
- Cada actividad: id corto unico (A, B, C... o A1...), nombre claro, fase, lista de predecesoras (ids),
  estimaciones PERT en DIAS LABORABLES: a (optimista) <= m (mas probable) <= b (pesimista), y people
  (personas asignadas, entero >= 1 y <= tamano del equipo).
- La capacitacion al usuario final y la entrega SIEMPRE forman parte de un proyecto de software. Si la descripcion
  menciona capacitacion, soporte inicial, migracion de datos, manuales/documentacion, respaldos o monitoreo,
  incluye una actividad explicita para cada uno.
- La red debe ser un grafo aciclico, con UNA sola actividad final (cierre/entrega) y precedencias reales.
- El entorno de servidor/nube se prepara ANTES de las pruebas de aceptacion (idealmente en paralelo al desarrollo).
- El frontend depende del backend/API, o ambos convergen en una actividad de integracion.
- Introduce paralelismo cuando sea razonable y reparte las personas para que sea factible con el equipo.
- No infles las personas por actividad solo para usar a todo el equipo: asigna lo que cada tarea realmente necesita.
- Ajusta las duraciones al tamano del equipo: mas personas reduce la duracion solo si la tarea es paralelizable.
- team_assessment: evalua con honestidad si el equipo indicado es adecuado. verdict: "adecuado", "sobra" (demasiados
  integrantes: algunos quedarian ociosos) o "falta" (faltan personas). recommended_team es el tamano ideal (entero >= 1).
- complexity_score: entero 1-10 de la complejidad del proyecto ingresado, comparada con la base.
- Responde SOLO con el JSON del esquema indicado."""

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "complexity_score": {"type": "INTEGER"},
        "complexity_rationale": {"type": "STRING"},
        "assumptions": {"type": "ARRAY", "items": {"type": "STRING"}},
        "team_assessment": {
            "type": "OBJECT",
            "properties": {
                "verdict": {"type": "STRING", "enum": ["adecuado", "sobra", "falta"]},
                "recommended_team": {"type": "INTEGER"},
                "comment": {"type": "STRING"},
            },
            "required": ["verdict", "recommended_team", "comment"],
        },
        "activities": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "name": {"type": "STRING"},
                    "phase": {"type": "STRING"},
                    "preds": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "a": {"type": "NUMBER"},
                    "m": {"type": "NUMBER"},
                    "b": {"type": "NUMBER"},
                    "people": {"type": "INTEGER"},
                    "rationale": {"type": "STRING"},
                },
                "required": ["id", "name", "phase", "preds", "a", "m", "b", "people", "rationale"],
            },
        },
    },
    "required": ["complexity_score", "complexity_rationale", "assumptions", "team_assessment", "activities"],
}


class GeminiError(RuntimeError):
    pass


def _clean_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    return json.loads(text)


class QuotaError(GeminiError):
    """Limite de uso (429). daily=True si es el limite diario (esperar no sirve)."""
    def __init__(self, msg: str, daily: bool = False):
        super().__init__(msg)
        self.daily = daily


class ModelNotFound(GeminiError):
    pass


class ModelBusy(GeminiError):
    """Saturacion pasajera del modelo (5xx): conviene probar otro."""


_blocked: dict[str, float] = {}   # modelo -> instante hasta el que se omite (cuota agotada)


def _is_daily(r) -> bool:
    t = r.text
    return "PerDay" in t or "per day" in t


def _call(api_key: str, model: str, contents: list, timeout: int, **kw) -> str:
    """`model` puede ser una lista separada por comas: se prueba en orden y se pasa al siguiente
    si un modelo no existe o agoto su cuota."""
    models = [m.strip() for m in str(model).split(",") if m.strip()]
    errors: list[str] = []
    now = time.time()
    # primero los modelos no bloqueados; los bloqueados quedan como ultimo recurso
    ordered = [m for m in models if _blocked.get(m, 0) <= now] + [m for m in models if _blocked.get(m, 0) > now]
    for m in ordered:
        try:
            return _call_one(api_key, m, contents, timeout, **kw)
        except QuotaError as e:
            _blocked[m] = time.time() + (3600 if e.daily else 90)
            errors.append(f"{m}: {'cuota diaria agotada' if e.daily else 'limite por minuto'}")
        except ModelNotFound:
            _blocked[m] = time.time() + 3600
            errors.append(f"{m}: modelo no disponible")
        except ModelBusy:
            _blocked[m] = time.time() + 45
            errors.append(f"{m}: saturado")
    raise GeminiError(
        "Ningun modelo de Gemini esta disponible ahora (" + "; ".join(errors) + "). "
        "Espera un minuto e intentalo de nuevo. Si es cuota diaria, agrega otros modelos en GEMINI_MODEL "
        "(separados por comas) en el archivo .env o usa una key con facturacion habilitada."
    )


def _call_one(api_key: str, model: str, contents: list, timeout: int,
              system: str = SYSTEM, schema: dict = RESPONSE_SCHEMA, temperature: float = TEMPERATURE) -> str:
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "responseMimeType": "application/json",
            "responseSchema": schema,
        },
    }
    r = None
    for intento in range(3):  # reintenta ante limite de uso (429) esperando un poco
        try:
            r = requests.post(
                ENDPOINT.format(model=model),
                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                json=body, timeout=timeout,
            )
        except requests.Timeout as e:
            raise ModelBusy(f"El modelo {model} tardo demasiado en responder.") from e
        except requests.RequestException as e:
            raise GeminiError(f"No se pudo conectar con Gemini: {e}") from e
        if r.status_code != 429 or intento == 2 or _is_daily(r):
            break      # con limite diario esperar no sirve
        time.sleep(20)
    if r.status_code == 429:
        raise QuotaError("Limite de uso de Gemini.", daily=_is_daily(r))
    if r.status_code == 404:
        raise ModelNotFound(f"El modelo {model} no existe o no esta disponible.")
    if r.status_code in (500, 502, 503, 504):
        raise ModelBusy(f"El modelo {model} esta saturado ({r.status_code}).")
    if r.status_code != 200:
        try:
            msg = r.json()["error"]["message"]
        except Exception:
            msg = r.text[:300]
        raise GeminiError(f"Gemini respondio {r.status_code}: {msg}")
    try:
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        raise GeminiError(f"Respuesta de Gemini sin contenido: {e}") from e


def generate_plan(
    api_key: str,
    model: str,
    description: str,
    team_size: int,
    kb_text: str,
    extra_steps: str = "",
    timeout: int = 90,
):
    user = (
        f"## Proyecto a planificar\n{description}\n\n"
        f"## Equipo de desarrollo disponible: {team_size} personas\n"
        + (f"## Pasos adicionales que el ingeniero exige incluir\n{extra_steps}\n\n" if extra_steps else "")
        + f"## Base de conocimiento (proyectos similares)\n{kb_text}\n"
    )
    contents = [{"role": "user", "parts": [{"text": user}]}]

    best = None  # (n_problemas, acts, meta, problemas)
    history: list[dict] = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        text = _call(api_key, model, contents, timeout)
        try:
            data = _clean_json(text)
            acts, meta = parse_plan(data, team_size)
            problems = rules.check(acts, team_size, _int(data.get("complexity_score")), description)
        except GeminiError as e:
            if attempt == MAX_ATTEMPTS and best is None:
                raise
            problems, acts, meta = [f"El plan no fue valido: {e}"], None, None
        history.append({"attempt": attempt, "problems": problems})
        if acts is not None and (best is None or len(problems) < best[0]):
            best = (len(problems), acts, meta, problems)
        if not problems:
            break
        if attempt < MAX_ATTEMPTS:
            contents += [
                {"role": "model", "parts": [{"text": text}]},
                {"role": "user", "parts": [{"text":
                    "Tu plan incumple estas reglas de verificacion. Corrige el plan COMPLETO y devuelvelo "
                    "otra vez con el mismo esquema, cambiando solo lo necesario:\n- " + "\n- ".join(problems)}]},
            ]
    if best is None:
        raise GeminiError("Gemini no devolvio un plan valido.")
    _, acts, meta, remaining = best
    meta["quality"] = {
        "attempts": len(history),
        "initial_problems": history[0]["problems"],
        "remaining_problems": remaining,
        "passed": not remaining,
    }
    return acts, meta


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def parse_plan(data: dict, team_size: int):
    acts: list[Activity] = []
    for x in data.get("activities", []):
        try:
            a, m, b = float(x["a"]), float(x["m"]), float(x["b"])
            a, m, b = sorted((a, m, b))  # tolera orden incorrecto
            acts.append(
                Activity(
                    id=str(x["id"]).strip(),
                    name=str(x["name"]).strip(),
                    preds=[str(p).strip() for p in x.get("preds", [])],
                    a=a, m=m, b=b,
                    people=max(1, min(int(x.get("people", 1)), team_size)),
                    phase=str(x.get("phase", "")).strip(),
                )
            )
        except (KeyError, TypeError, ValueError) as e:
            raise GeminiError(f"Actividad mal formada ({e}).") from e
    if not acts:
        raise GeminiError("Gemini no devolvio actividades.")
    try:
        validate(acts)
    except NetworkError as e:
        raise GeminiError(f"El plan generado es invalido: {e}") from e
    ta = data.get("team_assessment") or {}
    verdict = str(ta.get("verdict", "")).lower().strip()
    meta = {
        "team_assessment": {
            "verdict": verdict if verdict in ("adecuado", "sobra", "falta") else "",
            "recommended_team": ta.get("recommended_team"),
            "comment": str(ta.get("comment", "")),
            "for_team": team_size,
        },
        "complexity_score": data.get("complexity_score"),
        "complexity_rationale": data.get("complexity_rationale", ""),
        "assumptions": data.get("assumptions", []),
        "rationale": {str(x["id"]): x.get("rationale", "") for x in data["activities"]},
    }
    return acts, meta


# --------------------------------------------------------------------------
# Filtro de entrada: separa lo que es software de lo que no lo es
# --------------------------------------------------------------------------
INPUT_SYSTEM = """Eres un analista que filtra solicitudes para una herramienta que SOLO planifica proyectos de software
(aplicaciones web o moviles, sistemas de informacion, APIs, scripts de automatizacion, plataformas de datos, videojuegos,
integraciones, migraciones tecnologicas, etc.).

Dado el texto del usuario:
- Separa lo que describe un producto o proyecto de SOFTWARE de todo lo demas (eventos, cocina, construccion, tramites,
  tareas personales, compras, etc.), que debes ignorar.
- Si el usuario quiere un software para apoyar algo no tecnico (p. ej. "una app para administrar mi boda"), eso SI es software.
- Organizar una boda, una fiesta o cualquier actividad no tecnica, por mas detallada que sea, NO es software.
- Todo lo que rodea al ciclo de vida del software SI forma parte del proyecto y NO se ignora: requerimientos, diseno,
  pruebas, despliegue, migracion de datos, documentacion, manuales, capacitacion de usuarios, soporte inicial,
  cumplimiento normativo, seguridad y respaldos. Ignora solo lo que no tiene relacion con construir o entregar el software.
- software_description: reune UNICAMENTE lo que el usuario dijo sobre el software, con sus propias palabras.
  NO inventes ni agregues funcionalidades. Si no hay software, deja la cadena vacia.
- ignored_text: resumen breve (maximo 200 caracteres) de lo que ignoraste. Vacio si no ignoraste nada.
- detail_level, evaluado unicamente sobre la parte de software:
  "insuficiente": solo se menciona el tipo de sistema o una idea general, SIN ninguna funcion concreta, tipo de
     usuario, plataforma ni restriccion (ej.: "una app de ventas en linea", "quiero un sistema"). No alcanza para planificar.
  "bajo": se entiende el sistema y hay una o dos funciones o datos concretos, pero falta mucho.
  "medio": hay varias funciones o contexto, aunque faltan datos importantes.
  "alto": alcance bien definido (funciones, usuarios, integraciones, despliegue).
- missing_info: hasta 4 datos concretos que el usuario deberia anadir para poder planificar (plataforma, usuarios,
  funciones principales, integraciones, pagos, etc.), redactados como indicaciones breves. Vacio si detail_level es "alto".
- Responde SOLO con el JSON del esquema."""

INPUT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "is_software": {"type": "BOOLEAN"},
        "software_description": {"type": "STRING"},
        "ignored_text": {"type": "STRING"},
        "detail_level": {"type": "STRING", "enum": ["insuficiente", "bajo", "medio", "alto"]},
        "missing_info": {"type": "ARRAY", "items": {"type": "STRING"}},
        "reason": {"type": "STRING"},
    },
    "required": ["is_software", "software_description", "ignored_text", "detail_level", "missing_info", "reason"],
}


def analyze_request(api_key: str, model: str, description: str, timeout: int = 60) -> dict:
    """Clasifica la entrada. Devuelve is_software, software_description, ignored_text, detail_level, missing_info."""
    text = _call(
        api_key, model,
        [{"role": "user", "parts": [{"text": "Texto del usuario:\n<<<\n" + description + "\n>>>"}]}],
        timeout, system=INPUT_SYSTEM, schema=INPUT_SCHEMA, temperature=0.0,
    )
    try:
        d = _clean_json(text)
    except Exception as e:
        raise GeminiError(f"No se pudo interpretar el analisis de la solicitud: {e}") from e
    level = str(d.get("detail_level", "")).lower()
    soft = str(d.get("software_description", "")).strip()
    return {
        "is_software": bool(d.get("is_software")) and bool(soft),
        "software_description": soft,
        "ignored_text": str(d.get("ignored_text", "")).strip(),
        "detail_level": level if level in ("insuficiente", "bajo", "medio", "alto") else "medio",
        "missing_info": [str(q).strip() for q in (d.get("missing_info") or []) if str(q).strip()][:4],
        "reason": str(d.get("reason", "")).strip(),
    }
