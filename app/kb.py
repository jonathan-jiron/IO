"""Base de conocimiento: proyectos de software de referencia + recuperacion.

Cada proyecto lleva descripcion, complejidad (1-10) y su red de actividades con
estimaciones PERT (dias): (id, nombre, fase, predecesoras, a, m, b, personas).
La recuperacion usa TF-IDF + coseno (sin dependencias externas) para encontrar
los proyectos mas parecidos al que ingresa el usuario.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter

P = lambda *a: a  # noqa: E731  (tupla de actividad)

KB: list[dict] = [
    {
        "id": "KB1", "name": "Sitio web institucional / landing page",
        "complexity": 2, "team": 2,
        "description": "Sitio web estatico informativo con pocas paginas, formulario de contacto, diseno responsive y publicacion en un hosting.",
        "tags": "web sitio estatico landing pagina informativa contacto responsive hosting simple",
        "acts": [
            P("A", "Levantamiento de requerimientos", "Requerimientos", [], 1, 2, 3, 1),
            P("B", "Definicion de contenidos y arquitectura de informacion", "Requerimientos", ["A"], 1, 2, 4, 1),
            P("C", "Diseno de mockups y guia visual", "Diseno", ["B"], 2, 3, 5, 1),
            P("D", "Aprobacion del diseno con el cliente", "Diseno", ["C"], 1, 1, 3, 1),
            P("E", "Maquetacion HTML/CSS responsive", "Desarrollo", ["D"], 2, 4, 6, 1),
            P("F", "Formulario de contacto y envio de correo", "Desarrollo", ["D"], 1, 2, 3, 1),
            P("G", "Integracion de contenidos y SEO basico", "Desarrollo", ["E", "F"], 1, 2, 3, 1),
            P("H", "Pruebas en navegadores y dispositivos", "Pruebas", ["G"], 1, 2, 3, 1),
            P("I", "Publicacion en hosting y dominio", "Despliegue", ["H"], 1, 1, 2, 1),
            P("J", "Capacitacion al cliente y entrega", "Entrega", ["I"], 1, 1, 2, 1),
        ],
    },
    {
        "id": "KB2", "name": "Aplicacion web CRUD de gestion (inventario, citas, tareas)",
        "complexity": 4, "team": 3,
        "description": "Aplicacion web con login, roles de usuario, base de datos relacional, modulos de registro, edicion, consulta y reportes simples.",
        "tags": "web crud gestion inventario base de datos login usuarios roles reportes modulos sistema",
        "acts": [
            P("A", "Levantamiento de requerimientos y alcance", "Requerimientos", [], 2, 3, 5, 2),
            P("B", "Especificacion de historias de usuario", "Requerimientos", ["A"], 2, 3, 4, 1),
            P("C", "Diseno de arquitectura y modelo de datos", "Diseno", ["B"], 2, 4, 6, 2),
            P("D", "Diseno de interfaces (UX/UI)", "Diseno", ["B"], 3, 5, 7, 1),
            P("E", "Configuracion de entorno, repositorio y CI", "Desarrollo", ["C"], 1, 2, 3, 1),
            P("F", "Modulo de autenticacion y roles", "Desarrollo", ["E"], 2, 4, 6, 1),
            P("G", "Modulos CRUD principales (backend)", "Desarrollo", ["E"], 5, 8, 12, 1),
            P("H", "Interfaz de usuario (frontend)", "Desarrollo", ["D", "E"], 5, 8, 12, 1),
            P("I", "Integracion frontend-backend y reportes", "Desarrollo", ["G", "H"], 2, 3, 5, 1),
            P("J", "Pruebas unitarias e integracion", "Pruebas", ["F", "G", "H"], 3, 4, 6, 2),
            P("K", "Pruebas de aceptacion con usuario", "Pruebas", ["I", "J"], 2, 3, 5, 2),
            P("L", "Despliegue en servidor", "Despliegue", ["K"], 1, 2, 3, 1),
            P("M", "Manual y capacitacion a usuarios", "Entrega", ["L"], 2, 3, 4, 1),
        ],
    },
    {
        "id": "KB3", "name": "Aplicacion movil con backend y notificaciones",
        "complexity": 6, "team": 4,
        "description": "Aplicacion movil multiplataforma conectada a una API propia, con autenticacion, geolocalizacion o camara, notificaciones push y publicacion en tiendas.",
        "tags": "movil android ios app api rest notificaciones push geolocalizacion tienda flutter react native backend",
        "acts": [
            P("A", "Levantamiento de requerimientos", "Requerimientos", [], 3, 4, 6, 2),
            P("B", "Historias de usuario y backlog priorizado", "Requerimientos", ["A"], 2, 3, 5, 2),
            P("C", "Arquitectura movil y de la API", "Diseno", ["B"], 3, 4, 6, 2),
            P("D", "Prototipo UX/UI y validacion", "Diseno", ["B"], 4, 6, 9, 1),
            P("E", "Modelo de datos y base de datos", "Diseno", ["C"], 2, 3, 5, 1),
            P("F", "Backend: API de autenticacion y usuarios", "Desarrollo", ["E"], 3, 5, 8, 2),
            P("G", "Backend: logica de negocio y endpoints", "Desarrollo", ["F"], 6, 9, 14, 2),
            P("H", "App: navegacion y pantallas base", "Desarrollo", ["D", "C"], 5, 8, 12, 2),
            P("I", "App: integracion con la API", "Desarrollo", ["G", "H"], 4, 6, 9, 2),
            P("J", "Notificaciones push y servicios nativos", "Desarrollo", ["I"], 3, 5, 8, 1),
            P("K", "Pruebas funcionales y de rendimiento", "Pruebas", ["J"], 4, 6, 9, 2),
            P("L", "Pruebas en dispositivos reales (beta)", "Pruebas", ["K"], 3, 5, 8, 2),
            P("M", "Despliegue del backend en la nube", "Despliegue", ["K"], 2, 3, 4, 1),
            P("N", "Publicacion en tiendas (revision)", "Despliegue", ["L", "M"], 3, 5, 10, 1),
            P("O", "Capacitacion y entrega al cliente", "Entrega", ["N"], 1, 2, 3, 1),
        ],
    },
    {
        "id": "KB4", "name": "Tienda en linea / e-commerce con pagos",
        "complexity": 7, "team": 5,
        "description": "Plataforma de comercio electronico con catalogo, carrito, pasarela de pagos, gestion de pedidos, panel administrativo, inventario y seguridad.",
        "tags": "ecommerce tienda linea pagos pasarela carrito catalogo pedidos inventario administrativo seguridad web",
        "acts": [
            P("A", "Levantamiento de requerimientos y reglas de negocio", "Requerimientos", [], 4, 6, 9, 2),
            P("B", "Especificacion funcional y no funcional", "Requerimientos", ["A"], 3, 4, 6, 2),
            P("C", "Arquitectura y modelo de datos", "Diseno", ["B"], 3, 5, 7, 2),
            P("D", "Diseno UX/UI de la tienda", "Diseno", ["B"], 5, 7, 10, 2),
            P("E", "Entorno, repositorio y pipeline CI/CD", "Desarrollo", ["C"], 2, 3, 5, 1),
            P("F", "Modulo de catalogo y busqueda", "Desarrollo", ["E"], 5, 8, 12, 2),
            P("G", "Carrito y proceso de compra", "Desarrollo", ["F", "D"], 5, 7, 10, 2),
            P("H", "Integracion con pasarela de pagos", "Desarrollo", ["G"], 4, 6, 10, 1),
            P("I", "Gestion de pedidos e inventario", "Desarrollo", ["F"], 5, 8, 12, 2),
            P("J", "Panel administrativo", "Desarrollo", ["I"], 5, 7, 10, 2),
            P("K", "Notificaciones por correo y facturacion", "Desarrollo", ["H", "I"], 3, 4, 6, 1),
            P("L", "Pruebas funcionales e integracion", "Pruebas", ["J", "K"], 5, 7, 10, 3),
            P("M", "Pruebas de seguridad y carga", "Pruebas", ["L"], 3, 5, 8, 2),
            P("N", "Correccion de defectos", "Pruebas", ["M"], 3, 4, 7, 3),
            P("O", "Despliegue en produccion y monitoreo", "Despliegue", ["N"], 2, 3, 5, 2),
            P("P", "Capacitacion y entrega", "Entrega", ["O"], 2, 3, 4, 1),
        ],
    },
    {
        "id": "KB5", "name": "Sistema de informacion institucional / ERP para pyme",
        "complexity": 9, "team": 9,
        "description": "Sistema integral con multiples modulos (contabilidad, inventario, nomina, ventas), migracion de datos, integraciones, roles complejos, auditoria y capacitacion extensa.",
        "tags": "erp sistema informacion institucional contabilidad nomina ventas inventario modulos migracion datos auditoria integracion complejo pyme",
        "acts": [
            P("A", "Analisis de procesos y requerimientos", "Requerimientos", [], 8, 12, 18, 3),
            P("B", "Especificacion de requerimientos y alcance", "Requerimientos", ["A"], 5, 7, 10, 2),
            P("C", "Arquitectura de solucion y seguridad", "Diseno", ["B"], 5, 8, 12, 3),
            P("D", "Modelo de datos integral", "Diseno", ["C"], 4, 6, 9, 2),
            P("E", "Diseno UX/UI de modulos", "Diseno", ["B"], 7, 10, 15, 2),
            P("F", "Entorno, repositorio y CI/CD", "Desarrollo", ["C"], 3, 4, 6, 1),
            P("G", "Nucleo: usuarios, roles y auditoria", "Desarrollo", ["D", "F"], 6, 9, 14, 3),
            P("H", "Modulo de contabilidad", "Desarrollo", ["G"], 12, 18, 26, 2),
            P("I", "Modulo de inventario", "Desarrollo", ["G"], 10, 14, 20, 2),
            P("J", "Modulo de ventas y facturacion", "Desarrollo", ["G", "E"], 10, 15, 22, 2),
            P("K", "Modulo de nomina", "Desarrollo", ["G"], 8, 12, 18, 2),
            P("L", "Integraciones externas (bancos, SRI, etc.)", "Desarrollo", ["H", "J"], 6, 9, 14, 2),
            P("M", "Migracion de datos historicos", "Desarrollo", ["D"], 6, 9, 14, 2),
            P("N", "Pruebas integrales del sistema", "Pruebas", ["H", "I", "J", "K", "L"], 8, 12, 18, 4),
            P("O", "Pruebas de aceptacion (UAT)", "Pruebas", ["N", "M"], 6, 9, 14, 3),
            P("P", "Correccion de defectos", "Pruebas", ["O"], 4, 6, 10, 3),
            P("Q", "Despliegue en produccion", "Despliegue", ["P"], 3, 4, 6, 2),
            P("R", "Capacitacion por modulos", "Entrega", ["Q"], 5, 8, 12, 2),
            P("S", "Soporte inicial y cierre", "Entrega", ["R"], 3, 5, 8, 2),
        ],
    },
    {
        "id": "KB6", "name": "Chatbot / asistente con inteligencia artificial",
        "complexity": 6, "team": 4,
        "description": "Asistente conversacional con modelo de lenguaje, base de conocimiento, integracion con canales (web, WhatsApp), evaluacion de respuestas y monitoreo.",
        "tags": "chatbot asistente inteligencia artificial ia llm modelo lenguaje conocimiento rag whatsapp conversacional api evaluacion",
        "acts": [
            P("A", "Definicion de casos de uso y alcance", "Requerimientos", [], 2, 3, 5, 2),
            P("B", "Recoleccion y limpieza de la base de conocimiento", "Requerimientos", ["A"], 4, 6, 10, 2),
            P("C", "Diseno de arquitectura y prompts", "Diseno", ["A"], 2, 4, 6, 1),
            P("D", "Diseno de la interfaz de conversacion", "Diseno", ["A"], 2, 3, 5, 1),
            P("E", "Indexacion y recuperacion (RAG)", "Desarrollo", ["B", "C"], 4, 6, 9, 2),
            P("F", "Backend/API del asistente", "Desarrollo", ["C"], 4, 6, 9, 1),
            P("G", "Integracion con canal (web/WhatsApp)", "Desarrollo", ["D", "F"], 3, 5, 8, 1),
            P("H", "Integracion de recuperacion con generacion", "Desarrollo", ["E", "F"], 3, 4, 7, 2),
            P("I", "Evaluacion de calidad de respuestas", "Pruebas", ["G", "H"], 3, 5, 8, 2),
            P("J", "Pruebas de seguridad y limites", "Pruebas", ["I"], 2, 3, 5, 1),
            P("K", "Despliegue y monitoreo", "Despliegue", ["J"], 2, 3, 4, 1),
            P("L", "Capacitacion y entrega", "Entrega", ["K"], 1, 2, 3, 1),
        ],
    },
    {
        "id": "KB7", "name": "Migracion de infraestructura o base de datos a la nube",
        "complexity": 7, "team": 4,
        "description": "Migracion de sistema o base de datos legada a la nube: inventario, plan de migracion, pruebas de datos, corte controlado, respaldo y plan de reversa.",
        "tags": "migracion nube cloud base de datos legado infraestructura corte respaldo reversa datos aws azure",
        "acts": [
            P("A", "Inventario y analisis del sistema legado", "Requerimientos", [], 5, 7, 10, 2),
            P("B", "Estrategia y plan de migracion", "Diseno", ["A"], 3, 5, 7, 2),
            P("C", "Diseno de arquitectura cloud y costos", "Diseno", ["A"], 3, 5, 8, 2),
            P("D", "Aprovisionamiento del entorno cloud", "Desarrollo", ["C"], 3, 4, 7, 2),
            P("E", "Migracion de esquema y datos de prueba", "Desarrollo", ["B", "D"], 4, 6, 10, 2),
            P("F", "Adaptacion de aplicaciones y conexiones", "Desarrollo", ["D"], 5, 8, 12, 2),
            P("G", "Validacion de integridad de datos", "Pruebas", ["E"], 3, 4, 6, 2),
            P("H", "Pruebas de rendimiento y seguridad", "Pruebas", ["F", "G"], 3, 5, 8, 2),
            P("I", "Plan de reversa y respaldos", "Despliegue", ["H"], 2, 3, 4, 1),
            P("J", "Corte controlado a produccion", "Despliegue", ["I"], 1, 2, 3, 3),
            P("K", "Monitoreo post-migracion y cierre", "Entrega", ["J"], 3, 5, 7, 2),
        ],
    },
]

from kb_extra import EXTRA  # noqa: E402

KB.extend(EXTRA)

_STOP = set(
    "de la el los las un una unos unas y o en para por con sin que se del al "
    "a es son como mas muy su sus lo le les este esta estos estas ser tener "
    "debe permite permitir sistema aplicacion proyecto software desarrollar "
    "desarrollo construir crear hacer quiero necesito".split()
)


def _tok(text: str) -> list[str]:
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return [w for w in re.findall(r"[a-z0-9]+", t) if w not in _STOP and len(w) > 2]


def _docs() -> list[list[str]]:
    return [_tok(p["name"] + " " + p["description"] + " " + p["tags"]) for p in KB]


def retrieve(query: str, k: int = 3) -> list[tuple[dict, float]]:
    docs = _docs()
    q = _tok(query)
    n = len(docs)
    df: Counter = Counter()
    for d in docs:
        df.update(set(d))
    idf = lambda w: math.log((n + 1) / (df.get(w, 0) + 1)) + 1  # noqa: E731

    def vec(tokens: list[str]) -> dict[str, float]:
        c = Counter(tokens)
        return {w: (1 + math.log(f)) * idf(w) for w, f in c.items()}

    def cos(a: dict, b: dict) -> float:
        dot = sum(v * b.get(w, 0) for w, v in a.items())
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        return dot / (na * nb) if na and nb else 0.0

    qv = vec(q)
    scored = [(KB[i], cos(qv, vec(docs[i]))) for i in range(n)]
    scored.sort(key=lambda x: -x[1])
    return scored[:k]


def kb_context(matches: list[tuple[dict, float]]) -> str:
    """Serializa los proyectos recuperados para el prompt (few-shot)."""
    blocks = []
    for proj, sim in matches:
        lines = [
            f"### {proj['name']} (similitud {sim:.2f}, complejidad {proj['complexity']}/10, "
            f"equipo tipico {proj['team']})",
            f"Descripcion: {proj['description']}",
            "Actividades (id | nombre | fase | predecesoras | a,m,b dias | personas):",
        ]
        for i, n, ph, pr, a, m, b, pe in proj["acts"]:
            lines.append(f"{i} | {n} | {ph} | {','.join(pr) or '-'} | {a},{m},{b} | {pe}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)
