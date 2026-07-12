"""Nordzucker Mitarbeiter-Feedbackformular (eigene App, Port 8502).

Start:  streamlit run formular.py --server.port 8502 --server.address 0.0.0.0
Link :  http://<PC-IP-oder-ngrok>/?token=XXXX

Schreibt Antworten ins kanonische Schema (data/submissions.csv, Quelle 'intern').
Token wird NICHT mit der Antwort gespeichert -> anonym.
"""
import datetime as dt
import streamlit as st

import config
import feedback_utils as fb

st.set_page_config(page_title="Nordzucker · Mitarbeiterfeedback", page_icon="🌿",
                   layout="centered")

BLUE = "#0033A0"
LEAF = ('<svg width="34" height="34" viewBox="0 0 24 24" fill="none">'
        '<path d="M4 20c0-7 6-13 16-15-1 9-6 15-13 15-1 0-3-.3-3-.3z" fill="#7AB51D"/>'
        '<path d="M3 21c3-5 7-7 9-8" stroke="#0033A0" stroke-width="1.6" stroke-linecap="round"/></svg>')

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family:'Inter','Segoe UI',sans-serif; }
.stApp { background:#F4F6F9; }
#MainMenu, footer { visibility:hidden; }
.head { display:flex; align-items:center; gap:12px; margin-bottom:4px; }
.head .t { font-size:24px; font-weight:800; color:#0033A0; }
.sub { color:#667085; margin-bottom:8px; }
.stButton button { background:#0033A0; color:#fff; border:none; border-radius:10px; font-weight:600; }
</style>
""", unsafe_allow_html=True)

RATINGS = {
    "arbeitsatmosphaere": "Arbeitsatmosphäre", "work_life_balance": "Work-Life-Balance",
    "gehalt": "Gehalt / Sozialleistungen", "karriere": "Karriere & Weiterbildung",
    "vorgesetzte": "Vorgesetztenverhalten", "kommunikation": "Kommunikation",
    "arbeitsbedingungen": "Arbeitsbedingungen", "kollegen": "Kollegenzusammenhalt",
    "gleichberechtigung": "Gleichberechtigung", "interessante_aufgaben": "Interessante Aufgaben",
}
BEREICHE = ["Produktion", "Administration / Verwaltung", "IT",
            "Personal / Aus- und Weiterbildung", "Logistik / Materialwirtschaft",
            "Finanzen / Controlling", "Vertrieb / Verkauf", "Sonstiges"]
ORTE = ["Braunschweig", "Schladen", "Hohenhameln", "Nordstemmen", "Uelzen",
        "Klein Wanzleben", "Sonstiges"]

st.markdown(f'<div class="head">{LEAF}<span class="t">Nordzucker · Mitarbeiterfeedback</span></div>',
            unsafe_allow_html=True)

# --- Token pruefen ---
token = st.query_params.get("token")
if token and not fb.validate_token(token):
    st.error("Dieser Link ist ungültig oder wurde bereits verwendet. "
             "Bitte wende dich an die Personalabteilung.")
    st.stop()

st.markdown('<div class="sub">Dein Feedback ist anonym und hilft uns, Nordzucker als '
            'Arbeitgeber zu verbessern. Bitte bewerte die folgenden Bereiche von 1 (schlecht) '
            'bis 5 (sehr gut).</div>', unsafe_allow_html=True)

with st.form("feedback"):
    c1, c2 = st.columns(2)
    typ = c1.selectbox("Ich bin …", ["Mitarbeiter", "Azubi"])
    empfehlung = c2.selectbox("Würdest du Nordzucker weiterempfehlen?", ["Empfohlen", "Nicht empfohlen"])
    c3, c4 = st.columns(2)
    bereich = c3.selectbox("Bereich", BEREICHE)
    ort = c4.selectbox("Standort", ORTE)
    position = st.text_input("Position (optional)", "")

    st.markdown("**Bewertung der Bereiche**")
    werte = {}
    cols = st.columns(2)
    for i, (key, label) in enumerate(RATINGS.items()):
        werte[key] = cols[i % 2].slider(label, 1, 5, 3)

    titel = st.text_input("Kurze Überschrift zu deiner Bewertung", "")
    gut = st.text_area("Gut am Arbeitgeber", "")
    schlecht = st.text_area("Schlecht am Arbeitgeber", "")
    verbess = st.text_area("Verbesserungsvorschläge", "")

    abgeschickt = st.form_submit_button("Feedback absenden")

if abgeschickt:
    gesamt = round(sum(werte.values()) / len(werte), 1)
    daten = {
        "typ": typ, "datum": dt.date.today().isoformat(), "titel": titel or None,
        "gesamt_score": gesamt, "empfehlung": empfehlung, "position": position or None,
        "bereich": bereich, "ort": ort, "sprache": "de",
        "text_positiv": gut or None, "text_negativ": schlecht or None,
        "text_verbesserung": verbess or None, "text_freitext": None,
    }
    daten.update(werte)
    fb.append_submission(daten)
    if token:
        fb.mark_used(token)
    st.success("Vielen Dank! Dein Feedback wurde anonym gespeichert.")
    st.balloons()
