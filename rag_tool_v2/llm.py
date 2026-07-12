"""Duenner Ollama-Wrapper: Generierung + Embeddings, alles lokal.

Wenn Ollama nicht laeuft, faellt enrich/rag in einen Stub-Modus zurueck,
sodass die uebrige Pipeline (Harmonisierung, Cleaning, Dashboard) trotzdem
getestet werden kann.
"""
import json
import requests
import config

_session = requests.Session()


def ollama_available() -> bool:
    try:
        _session.get(f"{config.OLLAMA_HOST}/api/tags", timeout=2)
        return True
    except Exception:
        return False


def generate(prompt: str, system: str = "", model: str | None = None,
             json_mode: bool = False, temperature: float = 0.1) -> str:
    """Eine Textantwort vom lokalen LLM."""
    payload = {
        "model": model or config.LLM_MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if json_mode:
        payload["format"] = "json"
    r = _session.post(f"{config.OLLAMA_HOST}/api/generate", json=payload, timeout=300)
    r.raise_for_status()
    return r.json().get("response", "").strip()


def generate_json(prompt: str, system: str = "", model: str | None = None) -> dict:
    """Antwort als Dict (robust gegen kaputtes JSON)."""
    raw = generate(prompt, system=system, json_mode=True, model=model)
    try:
        return json.loads(raw)
    except Exception:
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(raw[start:end + 1])
            except Exception:
                pass
        return {}


def embed(text: str, model: str | None = None) -> list[float]:
    """Embedding-Vektor fuer einen Text."""
    r = _session.post(
        f"{config.OLLAMA_HOST}/api/embeddings",
        json={"model": model or config.EMBED_MODEL, "prompt": text},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["embedding"]
