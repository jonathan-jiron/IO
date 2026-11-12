"""Prueba la cadena de modelos con respuestas SIMULADAS (sin gastar cuota): python test_models.py"""
import gemini_client as g


def reset():
    g._blocked.clear()


def test_pasa_al_siguiente_si_cuota_diaria():
    reset()
    llamados = []

    def fake(api_key, model, contents, timeout, **kw):
        llamados.append(model)
        if model == "a":
            raise g.QuotaError("x", daily=True)
        return "ok-" + model

    g._call_one = fake
    assert g._call("k", "a,b,c", [], 5) == "ok-b"
    assert llamados == ["a", "b"]
    # la siguiente llamada ya no insiste con el modelo agotado
    llamados.clear()
    assert g._call("k", "a,b,c", [], 5) == "ok-b"
    assert llamados == ["b"]


def test_modelo_inexistente_se_omite():
    reset()

    def fake(api_key, model, contents, timeout, **kw):
        if model == "a":
            raise g.ModelNotFound("x")
        return "ok-" + model

    g._call_one = fake
    assert g._call("k", "a,b", [], 5) == "ok-b"


def test_todos_agotados_da_mensaje_claro():
    reset()

    def fake(api_key, model, contents, timeout, **kw):
        raise g.QuotaError("x", daily=True)

    g._call_one = fake
    try:
        g._call("k", "a,b", [], 5)
    except g.GeminiError as e:
        assert "Ningun modelo" in str(e) and "GEMINI_MODEL" in str(e)
        return
    raise AssertionError("debio fallar")


def test_un_solo_modelo_sigue_funcionando():
    reset()
    g._call_one = lambda api_key, model, contents, timeout, **kw: "ok-" + model
    assert g._call("k", "solo", [], 5) == "ok-solo"


def test_saturacion_pasa_al_siguiente():
    reset()

    def fake(api_key, model, contents, timeout, **kw):
        if model == "a":
            raise g.ModelBusy("503")
        return "ok-" + model

    g._call_one = fake
    assert g._call("k", "a,b", [], 5) == "ok-b"


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("OK", n)
