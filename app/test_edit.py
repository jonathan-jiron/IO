"""Pruebas de eliminar, reubicar y responsable fijo: python test_edit.py"""
import math

import cpm
from cpm import Activity, NetworkError, compute, move_activity, remove_activity, assign_team


def A(i, preds, d, people=1, owner=""):
    return Activity(i, i, preds, d, d, d, people, "", owner)


def red():
    # A(3) -> B(2) -> D(4);  A -> C(6) -> D
    return [A("A", [], 3), A("B", ["A"], 2), A("C", ["A"], 6), A("D", ["B", "C"], 4)]


def test_eliminar_reconecta():
    out = remove_activity(red(), "C")
    d = next(x for x in out if x.id == "D")
    assert d.preds == ["B"]                      # A->D es redundante (ya llega por B): se limpia
    assert math.isclose(compute(out).duration, 3 + 2 + 4)


def test_eliminar_intermedio_hereda_predecesoras():
    out = remove_activity(red(), "B")
    assert next(x for x in out if x.id == "D").preds == ["C"]


def test_eliminar_inexistente_y_unica():
    for acts, i in ((red(), "Z"), ([A("A", [], 1)], "A")):
        try:
            remove_activity(acts, i)
        except NetworkError:
            continue
        raise AssertionError("debio fallar")


def test_reubicar_cambia_la_ruta():
    # mover B para que quede despues de C (A -> C -> B -> D): ahora B esta en la ruta critica
    out = move_activity(red(), "B", pred="C", succ="D")
    assert next(x for x in out if x.id == "B").preds == ["C"]
    r = compute(out)
    assert math.isclose(r.duration, 3 + 6 + 2 + 4)
    assert r.critical_path == ["A", "C", "B", "D"]


def test_reubicar_conserva_datos():
    base = red()
    base[1] = Activity("B", "Paso B", ["A"], 1, 2, 3, 2, "Fase", "Ana")
    out = move_activity(base, "B", pred="C", succ="D")
    b = next(x for x in out if x.id == "B")
    assert (b.name, b.a, b.m, b.b, b.people, b.owner) == ("Paso B", 1, 2, 3, 2, "Ana")


def test_reubicar_ciclo_no_modifica_la_original():
    base = red()
    antes = [(x.id, list(x.preds)) for x in base]
    try:
        move_activity(base, "A", pred="D", succ="B")   # A despues de D pero antes de B: ciclo
    except NetworkError:
        assert [(x.id, list(x.preds)) for x in base] == antes
        return
    raise AssertionError("debio detectar el ciclo")


def test_reubicar_a_si_mismo_o_sin_referencias():
    for kw in (dict(pred="B", succ="B"), dict(pred=None, succ=None), dict(pred="Z", succ=None)):
        try:
            move_activity(red(), "B", **kw)
        except NetworkError:
            continue
        raise AssertionError(f"debio fallar con {kw}")


def test_responsable_fijo_y_resto_automatico():
    acts = [A("A", [], 5, people=2, owner="Luis"), A("B", ["A"], 3, people=1, owner="Marta")]
    res = compute(acts)
    asg, warns, peak = assign_team(acts, res, 3, ["Ana", "Luis", "Marta"])
    assert "Luis" in asg["A"] and len(asg["A"]) == 2          # Luis fijo + 1 automatico
    assert asg["B"] == ["Marta"]
    assert not warns


def test_responsable_ocupado_avisa_conflicto():
    acts = [A("A", [], 5, owner="Luis"), A("B", [], 5, owner="Luis")]   # en paralelo, mismo responsable
    res = compute(acts)
    asg, warns, peak = assign_team(acts, res, 2, ["Ana", "Luis"])
    assert any("Conflicto" in w and "Luis" in w for w in warns)


def test_responsable_inexistente_se_ignora():
    acts = [A("A", [], 5, owner="Nadie")]
    res = compute(acts)
    asg, warns, peak = assign_team(acts, res, 2, ["Ana", "Luis"])
    assert len(asg["A"]) == 1 and asg["A"][0] in ("Ana", "Luis")


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("OK", n)
