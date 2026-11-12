"""Prueba las rutas de rechazo con respuestas SIMULADAS del modelo (sin gastar cuota): python test_server.py"""
import server


def post(desc):
    return server.app.test_client().post("/api/generate", json={"description": desc, "team_size": 3})


def fake(**kw):
    base = dict(is_software=True, software_description="app de ventas en linea con catalogo y pagos",
                ignored_text="", detail_level="medio", missing_info=[], reason="")
    base.update(kw)
    return lambda *a, **k: base


def test_muy_corta_sin_ia():
    server.analyze_request = lambda *a, **k: (_ for _ in ()).throw(AssertionError("no debe llamar a la IA"))
    r = post("quiero una app")
    assert r.status_code == 422 and r.get_json()["code"] == "insufficient" and r.get_json()["hints"]


def test_no_software():
    server.analyze_request = fake(is_software=False, software_description="", ignored_text="boda")
    r = post("Quiero organizar la boda de mi hermana con muchos invitados y comida")
    assert r.status_code == 422 and r.get_json()["code"] == "not_software"


def test_insuficiente_con_pistas():
    server.analyze_request = fake(detail_level="insuficiente", missing_info=["Plataforma", "Usuarios"])
    r = post("quiero hacer una aplicacion de ventas en linea para mi negocio")
    j = r.get_json()
    assert r.status_code == 422 and j["code"] == "insufficient" and j["hints"] == ["Plataforma", "Usuarios"]


def test_sin_coincidencia_kb():
    server.analyze_request = fake(software_description="zzzz qqqq xxxx", detail_level="medio")
    r = post("texto cualquiera suficientemente largo para pasar el minimo de palabras")
    assert r.status_code == 422 and r.get_json()["code"] == "no_kb_match"


def test_pasa_y_llama_al_plan():
    called = {}
    server.analyze_request = fake(detail_level="medio")
    def fake_plan(*a, **k):
        called["ok"] = True
        raise server.GeminiError("corte de prueba")
    server.generate_plan = fake_plan
    r = post("app de ventas en linea con catalogo de productos y pagos con tarjeta")
    assert called.get("ok") and r.status_code == 502


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("OK", n)
