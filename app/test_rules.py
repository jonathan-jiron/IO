"""Pruebas de las reglas de sentido comun: python test_rules.py"""
import rules
from cpm import Activity


def A(i, name, preds, d=2, phase=""):
    return Activity(i, name, preds, d, d, d, 1, phase)


def test_plan_sano():
    acts = [A("A", "Requerimientos", []), A("B", "Backend API", ["A"], phase="Desarrollo"),
            A("C", "Frontend", ["B"], phase="Desarrollo"), A("D", "Pruebas", ["C"]), A("E", "Cierre", ["D"])]
    assert rules.check(acts, 4, 4) == []


def test_varias_finales():
    acts = [A("A", "Req", []), A("B", "X", ["A"]), A("C", "Y", ["A"])]
    assert any("UNA sola actividad final" in p for p in rules.check(acts, 4, None))


def test_servidor_despues_de_aceptacion():
    acts = [A("A", "Req", []), A("B", "Pruebas de aceptacion", ["A"]),
            A("C", "Configuracion de servidor en la nube", ["B"]), A("D", "Cierre", ["C"])]
    assert any("ANTES de las pruebas" in p for p in rules.check(acts, 4, None))


def test_front_back_paralelo_sin_integracion():
    acts = [A("A", "Req", []), A("B", "Backend API", ["A"], phase="Desarrollo"),
            A("C", "Frontend", ["A"], phase="Desarrollo"), A("D", "Cierre", ["B", "C"])]
    assert any("paralelo sin relacion" in p for p in rules.check(acts, 4, None))
    acts[3] = A("D", "Integracion front y back", ["B", "C"])
    assert not any("paralelo sin relacion" in p for p in rules.check(acts, 4, None))


def test_escala_complejidad():
    acts = [A("A", "Req", []), A("B", "Todo", ["A"], d=30)]
    assert any("Simplificalo" in p for p in rules.check(acts, 2, 1))


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("OK", n)
