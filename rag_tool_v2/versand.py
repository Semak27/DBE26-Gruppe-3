"""Versand der Feedback-Einladungen per Gmail (SMTP).

Zugangsdaten kommen aus .streamlit/secrets.toml:
    gmail_user = "deinname@gmail.com"
    gmail_app_password = "xxxx xxxx xxxx xxxx"   # App-Passwort, NICHT dein normales

Aufruf:  py versand.py            (an alle in data/empfaenger.csv)
Der Link zeigt auf die aktuelle ngrok-URL (falls laufend), sonst FALLBACK_URL.
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from pathlib import Path
import pandas as pd

import config
import feedback_utils as fb

SECRETS = config.BASE_DIR / ".streamlit" / "secrets.toml"
FALLBACK_URL = f"http://localhost:{config.FORM_PORT}"   # falls ngrok nicht laeuft


def load_secrets() -> tuple[str, str]:
    if not SECRETS.exists():
        raise SystemExit(f"Keine Zugangsdaten. Lege {SECRETS} an mit gmail_user und "
                         f"gmail_app_password (Google App-Passwort).")
    import tomllib
    data = tomllib.loads(SECRETS.read_text(encoding="utf-8"))
    try:
        return data["gmail_user"], data["gmail_app_password"]
    except KeyError:
        raise SystemExit("secrets.toml braucht die Schluessel gmail_user und gmail_app_password.")


def _build_mail(absender: str, empfaenger: str, link: str) -> MIMEText:
    text = (
        "Hallo,\n\n"
        "deine Meinung als Nordzucker-Mitarbeiter:in ist uns wichtig. "
        "Bitte nimm dir 3 Minuten Zeit fuer unser anonymes Feedback:\n\n"
        f"{link}\n\n"
        "Der Link ist persoenlich und nur einmal gueltig. Vielen Dank!\n\n"
        "Nordzucker AG · Mitarbeiterfeedback"
    )
    msg = MIMEText(text, "plain", "utf-8")
    msg["Subject"] = "Deine Meinung zaehlt – Nordzucker Mitarbeiterfeedback"
    msg["From"] = absender
    msg["To"] = empfaenger
    return msg


def send_invitations(base_url: str | None = None) -> tuple[int, str]:
    """Verschickt an alle Adressen aus empfaenger.csv. Rueckgabe: (anzahl, verwendete_url)."""
    if not config.EMPFAENGER_CSV.exists():
        raise SystemExit("Keine Empfaenger. Bitte im Dashboard Adressen eintragen.")
    emails = pd.read_csv(config.EMPFAENGER_CSV)["email"].dropna().astype(str).tolist()
    if not emails:
        return 0, ""

    base = base_url or fb.ngrok_url() or FALLBACK_URL
    tokens = fb.create_tokens(emails)
    user, pw = load_secrets()

    ctx = ssl.create_default_context()
    gesendet = 0
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
        server.login(user, pw)
        for e in emails:
            e = e.strip().lower()
            link = fb.form_link(base, tokens.get(e))
            server.send_message(_build_mail(user, e, link))
            gesendet += 1
    return gesendet, base


def main():
    n, url = send_invitations()
    print(f"{n} Einladung(en) versendet. Link-Basis: {url}")


if __name__ == "__main__":
    main()
