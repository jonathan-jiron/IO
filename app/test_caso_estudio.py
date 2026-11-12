"""Verifica el caso de estudio con un metodo INDEPENDIENTE del motor: python test_caso_estudio.py

El motor (cpm.py) calcula por pasadas hacia adelante y hacia atras. Aqui se enumeran TODOS los caminos de la
red y se calcula la duracion, la holgura y la ruta critica a partir de ellos. Si ambos metodos coinciden,
el calculo queda validado por dos vias distintas.
"""
import math

import caso_estudio as ce
from cpm import Activity, compute

TOL = 1e-6


def red():
    return [Activity(i, n, list(p), a, m, b, pe, ph) for i, n, ph, p, a, m, b, pe in ce.ACTIVIDADES]


def caminos(acts):
    """Todos los caminos inicio -> fin, como listas de ids."""
    succ = {a.id: [] for a in acts}
    for a in acts:
        for p in a.preds:
            succ[p].append(a.id)
    inicios = [a.id for a in acts if not a.preds]
    out = []

    def dfs(i, ruta):
        ruta = ruta + [i]
        if not succ[i]:
            out.append(ruta)
        for s in succ[i]:
            dfs(s, ruta)

    for i in inicios:
        dfs(i, [])
    return out


def independiente(acts):
    te = {a.id: a.te for a in acts}
    paths = caminos(acts)
    T = max(sum(te[i] for i in p) for p in paths)
    crit = [p for p in paths if abs(sum(te[i] for i in p) - T) < TOL]
    res = {}
    for a in acts:
        # mayor longitud de inicio hasta la actividad (inclusive) y de la actividad hasta el fin (exclusive)
        antes = max(sum(te[i] for i in p[: p.index(a.id)]) for p in paths if a.id in p)
        despues = max(sum(te[i] for i in p[p.index(a.id) + 1:]) for p in paths if a.id in p)
        es = antes
        holgura = T - (antes + te[a.id] + despues)
        res[a.id] = dict(ES=es, EF=es + te[a.id], slack=holgura)
    return T, crit, res


def test_coinciden_ambos_metodos():
    acts = red()
    r = compute(acts)
    T, crit, ind = independiente(acts)
    assert math.isclose(r.duration, T, abs_tol=TOL)
    assert sorted(r.critical_ids) == sorted({i for p in crit for i in p})
    for row in r.rows:
        i = row["id"]
        assert math.isclose(row["ES"], ind[i]["ES"], abs_tol=1e-4), i
        assert math.isclose(row["EF"], ind[i]["EF"], abs_tol=1e-4), i
        assert math.isclose(row["slack"], ind[i]["slack"], abs_tol=1e-4), i


def test_valores_conocidos_del_caso():
    r = compute(red())
    assert math.isclose(r.duration, 39.666667, abs_tol=1e-4)
    assert r.critical_path == list("ABCGHIJKL")
    holg = {x["id"]: x["slack"] for x in r.rows}
    assert math.isclose(holg["D"], 9.5, abs_tol=1e-4)
    assert math.isclose(holg["E"], 8.5, abs_tol=1e-4)
    assert math.isclose(holg["F"], 8.5, abs_tol=1e-4)
    assert all(holg[i] == 0 for i in "ABCGHIJKL")
    assert math.isclose(r.sigma, 1.929, abs_tol=1e-3)
    assert math.isclose(r.prob_by(ce.DEADLINE), 0.887, abs_tol=2e-3)


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("OK", n)
