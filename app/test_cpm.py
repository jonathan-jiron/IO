"""Pruebas del motor CPM: python test_cpm.py"""
import math
from cpm import Activity, compute, add_activity, NetworkError


def A(i, p, d, people=1):
    return Activity(i, i, p, d, d, d, people)


def test_basico():
    # A(3)->B(2)->D(4); A->C(6)->D ; ruta critica A-C-D = 13
    r = compute([A("A", [], 3), A("B", ["A"], 2), A("C", ["A"], 6), A("D", ["B", "C"], 4)])
    assert math.isclose(r.duration, 13)
    assert r.critical_path == ["A", "C", "D"]
    row = {x["id"]: x for x in r.rows}
    assert math.isclose(row["B"]["slack"], 4)
    assert math.isclose(row["B"]["ES"], 3) and math.isclose(row["B"]["LF"], 9)


def test_limite_dos_rutas_criticas():
    r = compute([A("A", [], 2), A("B", ["A"], 5), A("C", ["A"], 5), A("D", ["B", "C"], 1)])
    assert len(r.all_critical_paths) == 2 and all(x["slack"] == 0 for x in r.rows)


def test_pert():
    a = Activity("A", "A", [], 2, 4, 12)
    assert math.isclose(a.te, 5) and math.isclose(a.var, (10 / 6) ** 2)
    r = compute([a])
    assert math.isclose(r.prob_by(5), 0.5)


def test_insertar_paso():
    base = [A("A", [], 3), A("B", ["A"], 2), A("C", ["A"], 6), A("D", ["B", "C"], 4)]
    out = add_activity(base, A("N1", [], 10), pred="A", succ="B")  # A -> N1 -> B
    r = compute(out)
    assert math.isclose(r.duration, 3 + 10 + 2 + 4)  # ahora B (via N1) domina
    assert "N1" in r.critical_path
    b = next(x for x in out if x.id == "B")
    assert b.preds == ["N1"]  # sin arista redundante A->B


def test_ciclo():
    try:
        compute([A("A", ["B"], 1), A("B", ["A"], 1)])
    except NetworkError:
        return
    raise AssertionError("debio detectar ciclo")


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
            print("OK", n)
