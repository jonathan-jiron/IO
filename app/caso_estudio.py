"""Caso de estudio: la construccion de ESTE proyecto, planificada con PERT-CPM.

Es la red que se resolvera a mano en el informe y que se carga en la app (sin IA) para contrastar.
Tiempos en dias laborables. Equipo: 4 integrantes. Plazo objetivo: 42 dias.
Los tiempos (a, m, b) son una propuesta: ajustenlos a su experiencia real antes de resolver a mano.
"""

TEAM = 4
DEADLINE = 42

# (id, nombre, fase, predecesoras, a, m, b, personas)
ACTIVIDADES = [
    ("A", "Levantamiento de requisitos y alcance", "Requisitos", [], 2, 3, 5, 2),
    ("B", "Diseño de la arquitectura y del flujo del sistema", "Diseño", ["A"], 2, 3, 4, 2),
    ("C", "Motor PERT-CPM (cálculo y asignación)", "Desarrollo", ["B"], 4, 5, 8, 1),
    ("D", "Base de conocimiento y búsqueda de referencias", "Desarrollo", ["B"], 3, 4, 6, 1),
    ("E", "Integración con la IA (cliente de Gemini)", "Desarrollo", ["B"], 3, 5, 8, 1),
    ("F", "Filtro de entrada y reglas de calidad", "Desarrollo", ["D", "E"], 3, 4, 6, 1),
    ("G", "Interfaz web: Gantt y tabla", "Desarrollo", ["C"], 4, 6, 9, 2),
    ("H", "Interfaz web: grafo y edición de la red", "Desarrollo", ["G"], 4, 6, 10, 2),
    ("I", "Integración del servidor con la interfaz", "Desarrollo", ["F", "H"], 2, 3, 5, 2),
    ("J", "Pruebas y ejemplos de demostración", "Pruebas", ["I"], 3, 4, 6, 2),
    ("K", "Informe, README y diapositivas", "Entrega", ["J"], 5, 7, 10, 3),
    ("L", "Presentación y demostración", "Entrega", ["K"], 1, 1, 2, 4),
]


def como_json():
    """Formato que entiende /api/compute."""
    return [dict(id=i, name=n, phase=ph, preds=p, a=a, m=m, b=b, people=pe)
            for i, n, ph, p, a, m, b, pe in ACTIVIDADES]
