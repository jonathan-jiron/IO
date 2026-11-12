"""Pruebas de que la capacitacion y demas ciclo de vida nunca se pierden: python test_intake.py"""
import intake
import rules
from cpm import Activity

ORIG = ("Plataforma de telemedicina con videoconsultas e historia clinica. Se migraran los datos antiguos. "
        "Al final se capacitara al personal y se dara un periodo de soporte inicial.")


def chk(**kw):
    base = dict(is_software=True, software_description="Plataforma de telemedicina con videoconsultas",
                ignored_text="", detail_level="alto", missing_info=[])
    base.update(kw)
    return base


def test_nada_ignorado_envia_texto_exacto():
    plan, retr, ign = intake.reconcile(ORIG, chk())
    assert plan == ORIG and ign == ""


def test_ia_ignora_capacitacion_se_corrige():
    # justo el fallo reportado: la IA dice que ignoro la capacitacion y el soporte
    plan, retr, ign = intake.reconcile(ORIG, chk(ignored_text="Capacitacion del personal y periodo de soporte inicial."))
    assert plan == ORIG and ign == ""
    assert "capacitara" in plan and "soporte" in plan


def test_ruido_real_si_se_ignora():
    orig = "App para reservar citas en una peluqueria. Manana debo comprar pan y llamar al dentista."
    plan, retr, ign = intake.reconcile(orig, chk(software_description="App para reservar citas en una peluqueria.",
                                                  ignored_text="Comprar pan y llamar al dentista"))
    assert "pan" not in plan and "pan" in ign


def test_resumen_que_pierde_capacitacion_vuelve_al_original():
    orig = "App de citas con pagos. Ademas hay que capacitar al personal. Debo comprar pan."
    plan, retr, ign = intake.reconcile(orig, chk(software_description="App de citas con pagos.",
                                                  ignored_text="Comprar pan"))
    assert "capacitar" in plan and "Comprar pan" in plan  # original + nota de lo ignorado
    assert ign == "Comprar pan"


def _plan(*nombres):
    acts = []
    prev = []
    for i, n in enumerate(nombres):
        acts.append(Activity(f"A{i}", n, list(prev), 1, 2, 3, 1, ""))
        prev = [f"A{i}"]
    return acts


def test_regla_exige_actividad_de_capacitacion():
    sin = _plan("Requerimientos", "Desarrollo del modulo", "Pruebas", "Entrega final")
    assert any("capacitacion" in p for p in rules.check(sin, 3, 3, ORIG))
    con = _plan("Requerimientos", "Desarrollo del modulo", "Pruebas", "Capacitacion del personal", "Soporte inicial",
                "Migracion de datos")
    probs = rules.check(con, 3, 3, ORIG)
    assert not any("capacitacion" in p or "soporte" in p or "migracion" in p for p in probs), probs


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("OK", n)
