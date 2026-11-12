"""Configuracion del servidor (la API key NUNCA llega al navegador).

Orden de busqueda: variables de entorno -> archivo .env junto a este archivo.
"""
import os
from pathlib import Path

ENV_FILE = Path(__file__).with_name(".env")


def _load_env_file() -> dict[str, str]:
    out: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def get(name: str, default: str = "") -> str:
    # se relee en cada llamada: editar .env no exige reiniciar el servidor
    return os.environ.get(name) or _load_env_file().get(name) or default


def api_key() -> str:
    return get("GEMINI_API_KEY")


def model() -> str:
    return get("GEMINI_MODEL", "gemini-2.5-flash")
