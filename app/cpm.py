"""Motor determinista PERT-CPM.

La IA solo propone actividades, precedencias y estimaciones; todo el calculo
(te, varianza, ES/EF/LS/LF, holguras, ruta critica, probabilidad) se hace aqui,
de forma reproducible y verificable a mano.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class Activity:
    id: str
    name: str
    preds: list[str]
    a: float  # optimista
    m: float  # mas probable
    b: float  # pesimista
    people: int = 1
    phase: str = ""
    owner: str = ""   # responsable fijo (p. ej. un especialista); vacio = reparto automatico

    @property
    def te(self) -> float:
        return (self.a + 4 * self.m + self.b) / 6

    @property
    def var(self) -> float:
        return ((self.b - self.a) / 6) ** 2


class NetworkError(ValueError):
    pass


def validate(acts: list[Activity]) -> None:
    ids = [x.id for x in acts]
    if len(set(ids)) != len(ids):
        raise NetworkError("Hay identificadores de actividad repetidos.")
    s = set(ids)
    for x in acts:
        if not (0 <= x.a <= x.m <= x.b):
            raise NetworkError(f"{x.id}: se requiere 0 <= a <= m <= b.")
        for p in x.preds:
            if p not in s:
                raise NetworkError(f"{x.id}: predecesora inexistente '{p}'.")
            if p == x.id:
                raise NetworkError(f"{x.id}: no puede ser predecesora de si misma.")
    topo_order(acts)  # detecta ciclos


def topo_order(acts: list[Activity]) -> list[Activity]:
    by_id = {x.id: x for x in acts}
    indeg = {x.id: len(set(x.preds)) for x in acts}
    succ: dict[str, list[str]] = {x.id: [] for x in acts}
    for x in acts:
        for p in set(x.preds):
            succ[p].append(x.id)
    queue = [i for i in (x.id for x in acts) if indeg[i] == 0]
    out: list[Activity] = []
    while queue:
        i = queue.pop(0)
        out.append(by_id[i])
        for s in succ[i]:
            indeg[s] -= 1
            if indeg[s] == 0:
                queue.append(s)
    if len(out) != len(acts):
        raise NetworkError("La red contiene un ciclo; revise las precedencias.")
    return out


@dataclass
class Result:
    rows: list[dict]
    duration: float
    critical_path: list[str]
    critical_ids: set[str]
    sigma: float  # desviacion estandar del proyecto (suma de varianzas criticas)
    all_critical_paths: list[list[str]] = field(default_factory=list)

    def prob_by(self, deadline: float) -> float:
        if self.sigma == 0:
            return 1.0 if deadline >= self.duration else 0.0
        z = (deadline - self.duration) / self.sigma
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))


EPS = 1e-9


def compute(acts: list[Activity]) -> Result:
    validate(acts)
    order = topo_order(acts)
    by_id = {x.id: x for x in acts}
    succ: dict[str, list[str]] = {x.id: [] for x in acts}
    for x in acts:
        for p in set(x.preds):
            succ[p].append(x.id)

    es: dict[str, float] = {}
    ef: dict[str, float] = {}
    for x in order:
        es[x.id] = max((ef[p] for p in x.preds), default=0.0)
        ef[x.id] = es[x.id] + x.te
    duration = max(ef.values())

    lf: dict[str, float] = {}
    ls: dict[str, float] = {}
    for x in reversed(order):
        lf[x.id] = min((ls[s] for s in succ[x.id]), default=duration)
        ls[x.id] = lf[x.id] - x.te

    rows = []
    crit = set()
    for x in order:
        slack = ls[x.id] - es[x.id]
        is_crit = abs(slack) < 1e-7 * max(1.0, duration)
        if is_crit:
            crit.add(x.id)
        rows.append(
            dict(
                id=x.id, name=x.name, phase=x.phase,
                preds=", ".join(x.preds) or "-",
                a=x.a, m=x.m, b=x.b,
                te=round(x.te, 6), var=round(x.var, 6),
                ES=round(es[x.id], 6), EF=round(ef[x.id], 6),
                LS=round(ls[x.id], 6), LF=round(lf[x.id], 6),
                slack=0.0 if is_crit else round(slack, 6),
                critical=is_crit, people=x.people,
            )
        )

    paths = _critical_paths(order, by_id, crit, es, ef)
    main = paths[0] if paths else []
    sigma = math.sqrt(sum(by_id[i].var for i in main))
    return Result(rows, duration, main, crit, sigma, paths)


def _critical_paths(order, by_id, crit, es, ef) -> list[list[str]]:
    starts = [x.id for x in order if x.id in crit and not x.preds]
    succ_c: dict[str, list[str]] = {i: [] for i in crit}
    for x in order:
        if x.id not in crit:
            continue
        for p in x.preds:
            if p in crit and abs(ef[p] - es[x.id]) < 1e-7:
                succ_c[p].append(x.id)
    paths: list[list[str]] = []

    def dfs(i: str, path: list[str]) -> None:
        path.append(i)
        if not succ_c[i]:
            paths.append(path.copy())
        else:
            for s in succ_c[i]:
                dfs(s, path)
        path.pop()

    for s in starts:
        dfs(s, [])
    return paths


def add_activity(
    acts: list[Activity], new: Activity, pred: str | None, succ: str | None
) -> list[Activity]:
    """Inserta un paso entre `pred` y `succ`.

    - new.preds = [pred] (si se indica)
    - `succ` pasa a depender de `new`; si dependia directamente de `pred`,
      ese enlace se reemplaza (new queda entre ambas, sin arista redundante).
    Devuelve una nueva lista (no modifica la original) y valida la red.
    """
    if any(x.id == new.id for x in acts):
        raise NetworkError(f"Ya existe una actividad con id '{new.id}'.")
    out = [Activity(**{**x.__dict__, "preds": list(x.preds)}) for x in acts]
    new = Activity(**{**new.__dict__, "preds": [pred] if pred else []})
    for x in out:
        if succ and x.id == succ:
            if pred and pred in x.preds:
                x.preds.remove(pred)
            x.preds.append(new.id)
    out.append(new)
    validate(out)
    return out


def remove_activity(acts: list[Activity], act_id: str) -> list[Activity]:
    """Elimina un paso; sus sucesoras heredan las predecesoras del eliminado (la red sigue conectada)."""
    victim = next((a for a in acts if a.id == act_id), None)
    if victim is None:
        raise NetworkError(f"No existe el paso '{act_id}'.")
    if len(acts) <= 1:
        raise NetworkError("No se puede eliminar la unica actividad.")
    out: list[Activity] = []
    inherited: set[str] = set()
    for a in acts:
        if a.id == act_id:
            continue
        c = Activity(**{**a.__dict__, "preds": list(a.preds)})
        preds: list[str] = []
        for p in c.preds:
            if p == act_id:
                inherited.add(c.id)
            preds += victim.preds if p == act_id else [p]
        c.preds = list(dict.fromkeys(preds))
        out.append(c)
    validate(out)
    # solo en las que heredaron: se quitan aristas redundantes (p -> x cuando ya hay otro camino p -> ... -> x)
    by = {a.id: a for a in out}
    memo: dict[str, set[str]] = {}

    def anc(i: str) -> set[str]:
        if i not in memo:
            s: set[str] = set()
            for q in by[i].preds:
                s.add(q)
                s |= anc(q)
            memo[i] = s
        return memo[i]

    for i in inherited:
        ps = by[i].preds
        by[i].preds = [p for p in ps if not any(p in anc(q) for q in ps if q != p)]
    return out


def move_activity(acts: list[Activity], act_id: str, pred: str | None, succ: str | None) -> list[Activity]:
    """Reubica un paso: lo saca de su lugar actual (reconectando la red) y lo inserta entre `pred` y `succ`.

    Conserva su id, nombre, tiempos, personas y responsable. Si la nueva posicion crea un ciclo, falla
    y la red original no se modifica.
    """
    me = next((a for a in acts if a.id == act_id), None)
    if me is None:
        raise NetworkError(f"No existe el paso '{act_id}'.")
    if pred == act_id or succ == act_id:
        raise NetworkError("Un paso no puede ser predecesor ni posterior de si mismo.")
    if not pred and not succ:
        raise NetworkError("Elige al menos un predecesor o un posterior para la nueva posicion.")
    rest = remove_activity(acts, act_id)
    ids = {a.id for a in rest}
    for ref in (pred, succ):
        if ref and ref not in ids:
            raise NetworkError(f"No existe el paso '{ref}'.")
    return add_activity(rest, Activity(**{**me.__dict__, "preds": []}), pred or None, succ or None)


def normalize_names(names: list[str] | None, team_size: int) -> list[str]:
    out = [str(n).strip() or f"Desarrollador {i+1}" for i, n in enumerate(list(names or [])[:team_size])]
    out += [f"Desarrollador {i+1}" for i in range(len(out), team_size)]
    seen: dict[str, int] = {}
    for i, n in enumerate(out):
        seen[n] = seen.get(n, 0) + 1
        if seen[n] > 1:
            out[i] = f"{n} ({seen[n]})"
    return out


def assign_team(acts: list[Activity], res: Result, team_size: int, names: list[str] | None = None):
    """Asigna desarrolladores concretos segun el calendario ES/EF.

    Recorre las actividades por ES (y, a igual inicio, las de mayor esfuerzo primero).
    Cada una toma hasta `people` personas libres; entre las libres se prefiere a quien
    lleva menos carga acumulada (dias-persona) para equilibrar el trabajo.
    Devuelve (asignaciones, advertencias, pico_de_concurrencia).
    """
    names = normalize_names(names, team_size)
    free_at = {n: 0.0 for n in names}
    load = {n: 0.0 for n in names}
    assignment: dict[str, list[str]] = {}
    warnings: list[str] = []
    order = sorted(res.rows, key=lambda r: (r["ES"], -(r["te"] * r["people"]), r["id"]))
    owners = {a.id: a.owner for a in acts if getattr(a, "owner", "")}
    for r in order:
        total = min(max(1, r["people"]), team_size)
        if r["people"] > team_size:
            warnings.append(
                f"{r['id']}: se pidieron {r['people']} personas pero el equipo es de {team_size}."
            )
        # responsable fijo (especialista): se asigna primero; el resto se reparte automaticamente
        owner = owners.get(r["id"])
        fixed = [owner] if owner in free_at else []
        if fixed and free_at[owner] > r["ES"] + 1e-4:
            warnings.append(
                f"Conflicto: {owner} es responsable de {r['id']} pero esta ocupado hasta el dia "
                f"{free_at[owner]:.1f} (la tarea empieza el dia {r['ES']:.1f})."
            )
        want = total - len(fixed)

        # personas libres al inicio; si faltan, se espera hasta LS (la holgura lo permite)
        def pick(limit):
            return sorted((d for d, t in free_at.items() if t <= limit + 1e-4 and d not in fixed),
                          key=lambda d: (load[d], free_at[d]))
        chosen = pick(r["ES"])[:want]
        start = r["ES"]
        if len(chosen) < want and r["LS"] > r["ES"] + 1e-6:
            later = pick(r["LS"])[:want]
            if len(later) > len(chosen):
                chosen = later
                start = max(r["ES"], max(free_at[d] for d in chosen))
                if start > r["ES"] + 1e-6:
                    warnings.append(
                        f"Ajuste: {r['id']} puede iniciar hasta el dia {start:.1f} "
                        f"(dentro de su holgura) para esperar a una persona libre."
                    )
        if len(chosen) < want:
            warnings.append(
                f"{r['id']}: solo {len(chosen)} de {want} personas libres al inicio "
                f"(dia {r['ES']:.1f}); hay sobreasignacion en paralelo."
            )
            if not chosen and not fixed:
                chosen = [min(free_at, key=lambda d: (free_at[d], load[d]))]
        chosen = fixed + chosen
        for d in chosen:
            free_at[d] = max(free_at[d], start + r["te"])
            load[d] += r["te"]
        assignment[r["id"]] = chosen
    events = []
    for r in res.rows:
        events += [(r["ES"], r["people"]), (r["EF"], -r["people"])]
    events.sort(key=lambda e: (e[0], e[1]))
    cur = peak = 0
    for _, d in events:
        cur += d
        peak = max(peak, cur)
    return assignment, warnings, peak


def workload(res: Result, assignment: dict[str, list[str]], names: list[str]):
    """Resumen por persona: tareas, dias-persona y porcentaje del cronograma."""
    per: dict[str, dict] = {}
    for tid, devs in assignment.items():
        row = next(r for r in res.rows if r["id"] == tid)
        for d in devs:
            e = per.setdefault(d, dict(name=d, tasks=[], days=0.0, critical=0))
            e["tasks"].append(tid)
            e["days"] += row["te"]
            e["critical"] += 1 if row["critical"] else 0
    out = []
    for n in names:
        e = per.get(n, dict(name=n, tasks=[], days=0.0, critical=0))
        e["days"] = round(e["days"], 2)
        e["utilization"] = round(e["days"] / res.duration * 100, 1) if res.duration else 0.0
        out.append(e)
    return out
