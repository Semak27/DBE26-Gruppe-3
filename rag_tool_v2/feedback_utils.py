"""Helfer fuer das Feedback-Formular: Token-System, Submissions, ngrok, QR.

Alles dateibasiert (CSV), damit es ohne Datenbank lokal laeuft.
"""
import io
import uuid
import datetime as dt
from pathlib import Path
import pandas as pd
import requests

import config
import schema

TOKEN_COLS = ["token", "email", "created", "used_at"]
SUBMISSION_COLS = schema.CANONICAL_COLUMNS + ["eingang", "processed"]


# ---------- CSV-Grundlagen ----------
def _load(path: Path, cols) -> pd.DataFrame:
    if Path(path).exists():
        return pd.read_csv(path)
    return pd.DataFrame(columns=cols)


def _save(df: pd.DataFrame, path: Path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


# ---------- Token-System ----------
def new_token() -> str:
    return uuid.uuid4().hex[:12]


def create_tokens(emails: list[str]) -> dict:
    """Legt fuer neue Mailadressen je ein Token an. Bestehende bleiben erhalten.
    Rueckgabe: {email: token}."""
    df = _load(config.TOKENS_CSV, TOKEN_COLS)
    vorhanden = dict(zip(df["email"], df["token"])) if len(df) else {}
    neue = []
    for e in emails:
        e = e.strip().lower()
        if not e or e in vorhanden:
            continue
        t = new_token()
        vorhanden[e] = t
        neue.append({"token": t, "email": e,
                     "created": dt.datetime.now().isoformat(timespec="seconds"), "used_at": ""})
    if neue:
        df = pd.concat([df, pd.DataFrame(neue)], ignore_index=True)
        _save(df, config.TOKENS_CSV)
    return vorhanden


def validate_token(token: str) -> bool:
    df = _load(config.TOKENS_CSV, TOKEN_COLS)
    row = df[df["token"] == token]
    if row.empty:
        return False
    return not str(row.iloc[0]["used_at"]).strip() or str(row.iloc[0]["used_at"]) == "nan"


def mark_used(token: str):
    df = _load(config.TOKENS_CSV, TOKEN_COLS)
    idx = df.index[df["token"] == token]
    if len(idx):
        df.loc[idx, "used_at"] = dt.datetime.now().isoformat(timespec="seconds")
        _save(df, config.TOKENS_CSV)


# ---------- Submissions ----------
def append_submission(daten: dict):
    """Haengt eine Formular-Antwort ans submissions.csv an (kanonisches Schema).
    Token/E-Mail werden NICHT gespeichert -> anonym."""
    df = _load(config.SUBMISSIONS_CSV, SUBMISSION_COLS)
    n = len(df) + 1
    row = {c: daten.get(c) for c in schema.CANONICAL_COLUMNS}
    row["review_id"] = f"intern_{n}"
    row["unternehmen"] = config.HAUPTUNTERNEHMEN
    row["source"] = config.FORM_QUELLE
    row["eingang"] = dt.datetime.now().isoformat(timespec="seconds")
    row["processed"] = False
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    _save(df, config.SUBMISSIONS_CSV)


def unverarbeitete() -> pd.DataFrame:
    df = _load(config.SUBMISSIONS_CSV, SUBMISSION_COLS)
    if df.empty:
        return df
    return df[~df["processed"].fillna(False).astype(bool)]


# ---------- ngrok ----------
def ngrok_url() -> str | None:
    """Aktuelle oeffentliche https-URL aus der lokalen ngrok-API, sonst None."""
    try:
        r = requests.get(config.NGROK_API, timeout=2)
        for t in r.json().get("tunnels", []):
            if t.get("public_url", "").startswith("https"):
                return t["public_url"]
    except Exception:
        return None
    return None


def form_link(base_url: str, token: str | None = None) -> str:
    base = base_url.rstrip("/")
    return f"{base}/?token={token}" if token else base


# ---------- QR ----------
def qr_png(data: str) -> bytes:
    import qrcode
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
