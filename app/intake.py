"""Reconcilia lo que decidio el filtro de entrada (IA) con el texto original del usuario.

Regla de fondo: lo que rodea al ciclo de vida del software (capacitacion, soporte, manuales, migracion, pruebas,
despliegue...) SIEMPRE forma parte del proyecto. Si la IA lo "ignora" o lo pierde al resumir, el codigo lo corrige.
"""
from __future__ import annotations

import re
import unicodedata

# raices (sin tildes) de lo que nunca debe ignorarse
LIFE_STEMS = [
    "capacit", "entrenamiento", "induccion", "soporte", "garantia", "mantenimiento", "manual", "document",
    "despliegue", "publicacion", "migraci", "prueba", "respaldo", "backup", "monitoreo", "seguridad",
    "proteccion de datos", "normativa", "cumplimiento", "requerimiento", "diseno", "instalacion",
    "produccion", "entrega", "integracion", "auditoria",
]
LIFECYCLE = re.compile("|".join(LIFE_STEMS))


def norm(text: str) -> str:
    t = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def reconcile(original: str, chk: dict) -> tuple[str, str, str]:
    """Devuelve (texto_para_planificar, texto_para_buscar_referencias, contenido_ignorado)."""
    ign = (chk.get("ignored_text") or "").strip()
    sw = (chk.get("software_description") or "").strip() or original
    orig_n = norm(original)

    if ign and LIFECYCLE.search(norm(ign)):
        # la IA descarto algo que es parte del proyecto: no se le hace caso
        return original, sw, ""
    if not ign:
        # no se ignoro nada: se envia el texto EXACTO del usuario, sin resumenes intermedios
        return original, sw, ""

    plan_text = sw
    plan_n = norm(plan_text)
    lost = [s for s in LIFE_STEMS if s in orig_n and s not in plan_n]
    if lost:
        # el resumen perdio contexto del ciclo de vida: se usa el original y se indica que ignorar
        plan_text = original + f"\n\nNota: ignora, por no ser parte del software, lo siguiente: {ign}"
    return plan_text, sw, ign
