# Installationsguide — Nordzucker RAG-Tool v2

Schritt-für-Schritt-Anleitung, um das lokale RAG- und Dashboard-Tool auf einem
Rechner zum Laufen zu bringen. Alles läuft **lokal** — die KI-Teile über Ollama,
keine Cloud nötig.

---

## 0. Was du am Ende hast

- ein **Dashboard** mit Auswertungen (Streamlit)
- einen **RAG-Chat**, der Fragen faktenbasiert aus den Bewertungen beantwortet
- optional ein **Feedbackformular** zum Sammeln neuer Antworten + Mailversand

---

## 1. Voraussetzungen (einmalig)

| Was | Wozu | Prüfen mit |
|-----|------|------------|
| **Python 3.10+** | führt alle Skripte aus | `python --version` |
| **Ollama** | lokale KI (Anreicherung, Embeddings, RAG-Antworten) | `ollama --version` |
| **Projektordner** | der Ordner `rag_tool_v2` liegt lokal vor | — |

> Ollama gibt es unter https://ollama.com. Nach der Installation läuft es im
> Hintergrund (bzw. mit `ollama serve` starten).

---

## 2. Python-Pakete installieren

Im Ordner `rag_tool_v2` ein Terminal öffnen und:

```bash
pip install -r requirements.txt
```

Installiert u.a. `pandas`, `chromadb`, `streamlit`, `plotly`, `wordcloud`.

> Tipp: Am saubersten in einer virtuellen Umgebung:
> ```bash
> python -m venv .venv
> .venv\Scripts\activate        # Windows
> source .venv/bin/activate     # Mac/Linux
> pip install -r requirements.txt
> ```

---

## 3. Ollama-Modelle laden

Drei Modelle werden gebraucht (siehe `config.py`). Einmalig ziehen:

```bash
ollama pull llama3.1          # RAG-Antworten (Qualität)
ollama pull llama3.2          # Massen-Anreicherung (klein & schnell)
ollama pull nomic-embed-text  # Embeddings für den Vektorindex
```

**Wichtig:** Ollama muss laufen, während die Pipeline läuft. Test:

```bash
ollama list
```

> Läuft Ollama **nicht**, nutzt die Anreicherung einen regelbasierten Fallback
> (Sentiment aus der Bewertungszahl) — Cleaning und Dashboard funktionieren
> dann trotzdem, nur ohne echte KI-Anreicherung.

---

## 4. Rohdaten prüfen

Die Rohdaten (Excel-Dateien) liegen bereits im Projektordner. Welche Dateien
verwendet werden, steht in `config.py` unter `DATA_SOURCES` — z.B. Kununu-,
Glassdoor- und Indeed-Bewertungen für Nordzucker und VW FS.

Nichts zu tun, solange die dort genannten Dateien vorhanden sind. Neue Quellen
fügst du einfach in dieser Liste hinzu.

---

## 5. Pipeline ausführen (Reihenfolge wichtig!)

Nacheinander im Terminal, alles im Ordner `rag_tool_v2`:

```bash
python 01_harmonize.py      # 1) beide Quellen vereinheitlichen -> reviews_unified.csv
python 02_clean.py          # 2) Cleaning (Duplikate, Standardisierung) -> reviews_clean.csv
python 03_enrich.py         # 3) KI-Anreicherung (Sentiment, Kategorien, Keywords) -> reviews_enriched.csv
python 04_build_index.py    # 4) Vektorindex in ChromaDB aufbauen
```

Optionaler Schritt:

```bash
python 02_clean.py --llm    # Freitexte zusätzlich per Ollama korrigieren/übersetzen
```

Was jeder Schritt macht:

1. **harmonize** – bringt alle Quellen auf ein gemeinsames Schema
2. **clean** – entfernt Duplikate, standardisiert Felder, füllt Lücken
3. **enrich** – lässt die KI Sentiment, Kategorien und Keywords ergänzen
4. **build_index** – legt den durchsuchbaren Vektorindex an (Basis fürs RAG)

---

## 6. Dashboard starten

```bash
streamlit run dashboard.py
```

Öffnet sich im Browser (meist http://localhost:8501). Im Tab **RAG-Chat**
kannst du Fragen stellen, z.B.:

> „Welche Probleme treten in der Produktion besonders häufig auf?"

Einzelne RAG-Frage auch direkt im Terminal:

```bash
python 05_rag.py "Wie bewerten Bewerber den Bewerbungsprozess?"
```

---

## 7. Optional: Feedbackformular + Mailversand

Wenn du eigene, neue Bewertungen sammeln willst.

**a) Formular starten** (eigene App auf Port 8502):

```bash
streamlit run formular.py --server.port 8502 --server.address 0.0.0.0
```

Aufruf-Link: `http://<PC-IP-oder-ngrok>/?token=XXXX` — die Antwort wird anonym
gespeichert (das Token wird nicht mit gespeichert).

**b) Einladungen per Mail verschicken:**

Zugangsdaten in `.streamlit/secrets.toml` hinterlegen (Gmail **App-Passwort**,
nicht das normale Passwort):

```toml
gmail_user = "deinname@gmail.com"
gmail_app_password = "xxxx xxxx xxxx xxxx"
```

Empfänger in `data/empfaenger.csv` eintragen, dann:

```bash
python versand.py
```

**c) Neue Antworten einlesen** (ohne kompletten Neuaufbau):

```bash
python ingest.py            # nutzt Ollama, falls verfügbar
python ingest.py --no-llm   # Sentiment regelbasiert, ohne KI
```

Hängt neue Formular-Antworten an `reviews_enriched.csv` und den Index an.

---

## 8. Kurz-Checkliste

- [ ] Python 3.10+ installiert
- [ ] `pip install -r requirements.txt` gelaufen
- [ ] Ollama installiert + läuft (`ollama list` zeigt die 3 Modelle)
- [ ] Rohdaten aus `config.py` vorhanden
- [ ] Schritte 01 → 02 → 03 → 04 durchgelaufen
- [ ] `streamlit run dashboard.py` öffnet das Dashboard

---

## Häufige Stolperfallen

| Problem | Ursache / Lösung |
|---------|------------------|
| RAG antwortet nicht / Fehler bei Embeddings | Ollama läuft nicht oder Modell fehlt → `ollama serve`, `ollama pull nomic-embed-text` |
| Anreicherung ohne KI-Werte | Ollama war beim `03_enrich.py` nicht aktiv → Ollama starten und Schritt 3+4 wiederholen |
| Dashboard zeigt keine Daten | Pipeline (Schritte 1–4) noch nicht gelaufen → `reviews_enriched.csv` fehlt |
| „module not found" | Pakete fehlen → `pip install -r requirements.txt` (ggf. venv aktivieren) |
| Mailversand schlägt fehl | falsches Gmail-Passwort → **App-Passwort** in `secrets.toml` verwenden |
| Änderungen an Rohdaten wirken nicht | Pipeline muss neu laufen (Schritte 1–4), damit der Index aktualisiert wird |

---

*Mehr technische Details zur Architektur stehen in `README.md` und
`BACKEND_DOKUMENTATION.md` im selben Ordner.*
