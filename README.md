# Nordzucker Mitarbeiterfeedback — Lokales RAG + Dashboard

Lokale Pipeline, die Mitarbeiter-/Bewerberbewertungen aus mehreren Quellen
(**Kununu, Glassdoor, Indeed**) und mehreren Unternehmen (**Nordzucker** +
Wettbewerber **VW FS**) auf ein gemeinsames Schema bringt, per KI anreichert,
in einem RAG abfragbar macht und in einem Dashboard auswertet. Zusaetzlich lassen
sich ueber ein eigenes **Feedbackformular** neue, interne Bewertungen sammeln.
Alles laeuft lokal — die LLM-Teile ueber **Ollama**, keine Cloud noetig.

> Ausfuehrliche Schritt-fuer-Schritt-Installation: siehe **`INSTALLATION.md`**.
> Technische Details: siehe **`BACKEND_DOKUMENTATION.md`**.

## Architektur (entspricht den 4 Phasen aus der Zwischenpraesentation)

```
Rohdaten (xlsx, 3 Quellen x mehrere Unternehmen)
   │  01_harmonize.py   → Phase 0: gemeinsames Schema (alle Quellen vereinheitlicht)
   ▼  02_clean.py       → Phase 1: Cleaning (Standardisierung, Duplikate, Missing Values)
reviews_clean.csv
   │  03_enrich.py      → Phase 2: Prompt-Chain (Sentiment, Kategorien, Keywords, Summary)
   ▼
reviews_enriched.csv ──┬─ 04_build_index.py → Phase 3: ChromaDB-Vektorindex
                       │  05_rag.py         → Phase 3: faktenbasierte Antworten
                       └─ dashboard.py      → Phase 4: Streamlit-Dashboard (5 Tabs)

Formular-Zweig (optional):
formular.py  → sammelt interne Antworten  →  ingest.py  → haengt sie an
Index + reviews_enriched.csv an   (versand.py verschickt die Einladungen)
```

## Einmalig: Setup

1. **Python-Pakete:**
   ```
   pip install -r requirements.txt
   ```
2. **Ollama-Modelle** (Ollama muss installiert sein):
   ```
   ollama pull llama3.1          # RAG-Antworten (Qualitaet)
   ollama pull llama3.2          # Massen-Anreicherung (klein & schnell)
   ollama pull nomic-embed-text  # Embeddings
   ```
   Ollama muss laufen (`ollama serve`, bzw. die App im Hintergrund).
3. **Rohdaten:** liegen bereits im Projektordner. Welche Dateien genutzt werden,
   steht in `config.py` unter `DATA_SOURCES`. Neue Quellen/Unternehmen einfach
   dort ergaenzen.

## Pipeline ausfuehren (Reihenfolge wichtig)

```
python 01_harmonize.py      # alle Quellen -> reviews_unified.csv
python 02_clean.py          # Cleaning -> reviews_clean.csv
python 02_clean.py --llm    # optional: Freitexte per Ollama korrigieren/uebersetzen
python 03_enrich.py         # Anreicherung -> reviews_enriched.csv  (nutzt Ollama)
python 04_build_index.py    # Vektorindex in ChromaDB (nutzt Ollama)
```

Dann das Dashboard starten:
```
streamlit run dashboard.py
```

Einzelne RAG-Frage auch direkt im Terminal:
```
python 05_rag.py "Wie bewerten Bewerber den Bewerbungsprozess?"
```

## Dashboard — die 5 Tabs

| Tab | Inhalt |
|-----|--------|
| **Auswertung** | Kennzahlen, Sentiment und Kategorien fuer Nordzucker |
| **Wettbewerbsvergleich** | Nordzucker vs. VW FS ueber die gemeinsamen Sub-Ratings (Heatmap) |
| **Bewertungen** | Explorer: einzelne Bewertungen durchsuchen und filtern |
| **RAG-Chat** | faktenbasierte Fragen an die Bewertungen, z.B. „Welche Probleme treten in der Produktion besonders haeufig auf?" |
| **Befragung** | geschuetzter Admin-Bereich: interne Mitarbeiterbefragung steuern |

## Optional: eigenes Feedback sammeln

```
streamlit run formular.py --server.port 8502 --server.address 0.0.0.0   # Formular
python versand.py          # Einladungen per Gmail an data/empfaenger.csv
python ingest.py           # neue Antworten inkrementell einlesen (nutzt Ollama)
python ingest.py --no-llm  # dasselbe ohne KI (Sentiment regelbasiert)
```

Antworten werden anonym gespeichert (das Einmal-Token wird nicht mit abgelegt).
Der Gmail-Versand nutzt ein **App-Passwort** aus `.streamlit/secrets.toml`.

## Wichtig zu den Daten

- **Kununu** liefert v.a. Ratings + Titel — die Freitextfelder
  (Gut/Schlecht/Verbesserung) sind in der Rohdatei oft **leer**.
- **Glassdoor** und **Indeed** liefern echten Freitext (Pros/Cons/Advice).
- Das RAG arbeitet auf Freitext, ist also derzeit freitext-quellen-lastig.
  Sobald Kununu-Freitexte vorliegen, einfach in dieselben Spalten fuellen —
  die Pipeline nimmt sie automatisch mit.
- Ohne laufendes Ollama nutzt `03_enrich.py` einen regelbasierten Fallback
  (Sentiment aus Score), damit Cleaning + Dashboard trotzdem funktionieren.

## Gemeinsame Vergleichs-Dimensionen (Wettbewerbsvergleich)

`arbeitsatmosphaere, work_life_balance, gehalt, karriere, vorgesetzte,
gleichberechtigung` — nur diese sechs Sub-Ratings existieren in allen
Quellen und werden in der Heatmap unternehmens- und quellenuebergreifend
verglichen.
