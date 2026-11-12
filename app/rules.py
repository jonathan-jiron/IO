"""Reglas de sentido comun que debe cumplir un plan de software.

Se aplican sobre el plan que propone la IA. Si alguna falla, el mensaje se
devuelve a Gemini para que corrija (ver gemini_client.generate_plan).
Todas las reglas son deterministas y se pueden explicar en el informe.
"""
from __future__ import annotations

import re
import unicodedata

import cpm
from cpm import Activity


def _n(text: str) -> str:
    t = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def _ancestors(acts: list[Activity]) -> dict[str, set[str]]:
    by_id = {a.id: a for a in acts}
    memo: dict[str, set[str]] = {}

    def anc(i: str) -> set[str]:
        if i in memo:
            return memo[i]
        out: set[str] = set()
        for p in by_id[i].preds:
            out.add(p)
            out |= anc(p)
        memo[i] = out
        return out

    for a in acts:
        anc(a.id)
    return memo


RE_FRONT = re.compile(r"frontend|front-end|interfaz de usuario|pantallas|portal|cliente web|ui\b")
RE_BACK = re.compile(r"backend|back-end|api\b|servicios|endpoints|logica de negocio|base de datos")
RE_INTEG = re.compile(r"integraci")
RE_ACCEPT = re.compile(r"aceptaci|uat")
RE_PROVISION = re.compile(
    r"(configur|aprovision|prepar|provision).{0,40}(servidor|nube|cloud|infraestructura|hosting|produccion)"
)
RE_TEST = re.compile(r"prueba|testing|qa\b")


# (que menciona el usuario, que debe aparecer en alguna actividad, nombre para el mensaje)
REQUIRED = [
    (r"capacit|entrenamiento|induccion", r"capacit|entrenamiento|induccion|formacion", "capacitacion a los usuarios"),
    (r"soporte|garantia", r"soporte|garantia|mantenimiento", "soporte inicial"),
    (r"migra", r"migra", "migracion de datos"),
    (r"manual|documentacion", r"manual|document", "manual o documentacion"),
    (r"respaldo|backup", r"respaldo|backup", "respaldos"),
    (r"seguridad|proteccion de datos", r"seguridad|proteccion", "pruebas o medidas de seguridad"),
]


def check(acts: list[Activity], team: int, complexity: int | None, description: str | None = None) -> list[str]:
    problems: list[str] = []
    ids = {a.id for a in acts}
    anc = _ancestors(acts)
    txt = {a.id: _n(f"{a.name} {a.phase}") for a in acts}

    # 0. lo que el usuario menciona debe estar en el plan
    if description:
        d = _n(description)
        plan_txt = " ".join(txt.values())
        for mention, present, label in REQUIRED:
            if re.search(mention, d) and not re.search(present, plan_txt):
                problems.append(
                    f"La descripcion menciona {label} pero el plan no tiene ninguna actividad de {label}. "
                    f"Agrega una actividad explicita para ello (con su predecesora y sucesora)."
                )

    # 1. una sola actividad final
    has_succ = {p for a in acts for p in a.preds}
    sinks = [a.id for a in acts if a.id not in has_succ]
    if len(sinks) != 1:
        problems.append(
            f"La red debe terminar en UNA sola actividad final (cierre/entrega); ahora terminan {len(sinks)}: "
            + ", ".join(sinks) + ". Conecta las ramas sueltas hacia una actividad final."
        )

    # 2. configuracion de servidor/nube no puede depender de las pruebas de aceptacion
    for a in acts:
        if RE_PROVISION.search(_n(a.name)):
            late = [p for p in anc[a.id] if RE_ACCEPT.search(_n(next(x.name for x in acts if x.id == p)))]
            if late:
                problems.append(
                    f"{a.id} ('{a.name}') prepara el entorno de servidor/nube pero depende de las pruebas de "
                    f"aceptacion ({late[0]}). El entorno debe prepararse ANTES de las pruebas (por ejemplo en "
                    f"paralelo al desarrollo), no despues."
                )

    # 3. frontend y backend en paralelo requieren una integracion posterior
    not_design = lambda i: not re.search(r"diseno|requerimiento|prueba", txt[i])  # noqa: E731
    fronts = [a.id for a in acts if RE_FRONT.search(txt[a.id]) and not RE_BACK.search(txt[a.id]) and not_design(a.id)]
    backs = [a.id for a in acts if RE_BACK.search(txt[a.id]) and not RE_FRONT.search(txt[a.id]) and not_design(a.id)]
    integ = [a.id for a in acts if RE_INTEG.search(txt[a.id]) and not RE_TEST.search(txt[a.id])]
    for f in fronts:
        for b in backs:
            related = b in anc[f] or f in anc[b]
            joined = any(f in anc[i] and b in anc[i] for i in integ)
            # tambien vale que una prueba/actividad posterior dependa de ambas con 'integracion' en el nombre
            if not related and not joined:
                problems.append(
                    f"El frontend {f} y el backend {b} se desarrollan en paralelo sin relacion. Haz que {f} dependa "
                    f"de {b} (o de su contrato de API) o agrega una actividad de integracion posterior que "
                    f"dependa de ambos."
                )
                break
        else:
            continue
        break

    # 4. las pruebas deben venir despues de algun desarrollo
    dev = {a.id for a in acts if re.search(r"desarroll|implement|codific|backend|frontend|modulo", txt[a.id])}
    for a in acts:
        if RE_TEST.search(txt[a.id]) and not RE_ACCEPT.search(txt[a.id]) and dev and a.id not in dev:
            if not (anc[a.id] & dev):
                problems.append(f"{a.id} ('{a.name}') es una prueba pero no depende de ninguna actividad de desarrollo.")

    # 5. actividades demasiado largas
    for a in acts:
        if a.m > 45:
            problems.append(f"{a.id} ('{a.name}') dura {a.m:g} dias probables; dividela en sub-actividades.")

    # 6. escala segun complejidad
    try:
        res = cpm.compute(acts)
    except cpm.NetworkError as e:
        return problems + [str(e)]
    n = len(acts)
    if complexity is not None:
        if complexity <= 2 and (res.duration > 25 or n > 12):
            problems.append(
                f"El proyecto es de complejidad {complexity}/10 pero el plan tiene {n} actividades y "
                f"{res.duration:.0f} dias. Simplificalo: maximo ~12 actividades y ~25 dias."
            )
        elif complexity <= 4 and (res.duration > 60 or n > 18):
            problems.append(
                f"Complejidad {complexity}/10 pero el plan tiene {n} actividades y {res.duration:.0f} dias; reduce el alcance."
            )
        elif complexity >= 9 and n < 18:
            problems.append(
                f"Complejidad {complexity}/10 pero solo hay {n} actividades; detalla mas el plan: desglosa "
                f"cada modulo, integracion y etapa de pruebas en actividades propias (minimo ~18)."
            )
        elif complexity == 8 and n < 15:
            problems.append(
                f"Complejidad {complexity}/10 pero solo hay {n} actividades; detalla mas el plan (minimo ~15)."
            )

    # 7. factibilidad con el equipo
    _, warns, peak = cpm.assign_team(acts, res, team)
    hard = [w for w in warns if not w.startswith("Ajuste")]
    if hard:
        problems.append(
            f"Con un equipo de {team} personas hay sobreasignacion en paralelo (pico de {peak} personas). "
            f"Detalle: {hard[0]} Reduce 'people' o secuencia actividades con holgura para que quepan en el equipo."
        )
    return problems
