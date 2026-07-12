# Nordzucker Mitarbeiterfeedback — Lokales RAG + Dashboard

Lokale Pipeline, die Mitarbeiter-/Bewerberbewertungen aus mehreren Quellen
(Kununu + Glassdoor) auf ein gemeinsames Schema bringt, per KI anreichert,
in einem RAG abfragbar macht und in einem Dashboard auswertet.
Alles laeuft lokal — die LLM-Teile ueber **Ollama**, keine Cloud noetig.

## Architektur (entspricht den 4 Phasen aus der Zwischenpraesentation)

```
Rohdaten (xlsx)
   │  01_harmonize.py   → gemeinsames Schema (beide Quellen vereinheitlicht)
   ▼  02_clean.py       → Phase 1: Cleaning (Standardisierung, Duplikate, Missing Values)
reviews_clean.csv
   │  03_enrich.py      → Phase 2: Prompt-Chain (Sentiment, Kategorien, Keywords, Summary)
   ▼
reviews_enriched.csv ──┬─ 04_build_index.py → Phase 3: ChromaDB-Vektorindex
                       │  05_rag.py         → Phase 3: faktenbasierte Antworten
                       └─ dashboard.py      → Phase 4: Streamlit-Dashboard
```

## Einmalig: Setup

1. **Python-Pakete:**
   ```
   pip install -r requirements.txt
   ```
2. **Ollama-Modelle** (Ollama hast du bereits installiert):
   ```
   ollama pull llama3.1
   ollama pull nomic-embed-text
   ```
   Ollama muss laufen (`ollama serve`, bzw. die App im Hintergrund).
3. **Rohdaten:** liegen bereits im Projektordner. Die Skripte finden sie
   automatisch (oder lege sie in `data/raw/`).

## Pipeline ausfuehren (Reihenfolge wichtig)

```
python 01_harmonize.py      # beide Quellen -> reviews_unified.csv
python 02_clean.py          # Cleaning -> reviews_clean.csv
python 02_clean.py --llm    # optional: Freitexte per Ollama korrigieren/uebersetzen
python 03_enrich.py         # Anreicherung -> reviews_enriched.csv  (nutzt Ollama)
python 04_build_index.py    # Vektorindex in ChromaDB (nutzt Ollama)
```

Dann das Dashboard starten:
```
streamlit run dashboard.py
```
Im Tab **RAG-Chat** kannst du Fragen stellen, z.B.
„Welche Probleme treten in der Produktion besonders haeufig auf?"

Einzelne RAG-Frage auch direkt im Terminal:
```
python 05_rag.py "Wie bewerten Bewerber den Bewerbungsprozess?"
```

## Wichtig zu den Daten

- **Kununu** liefert v.a. Ratings + Titel — die Freitextfelder
  (Gut/Schlecht/Verbesserung) sind in der Rohdatei **leer**.
- **Glassdoor** liefert echten Freitext (Pros/Cons/Advice).
- Das RAG arbeitet auf Freitext, ist also derzeit stark glassdoor-lastig.
  Sobald Kununu-Freitexte vorliegen, einfach in dieselben Spalten fuellen —
  die Pipeline nimmt sie automatisch mit.
- Ohne laufendes Ollama nutzt `03_enrich.py` einen regelbasierten Fallback
  (Sentiment aus Score), damit Cleaning + Dashboard trotzdem funktionieren.

## Gemeinsame Vergleichs-Dimensionen beider Quellen

`arbeitsatmosphaere, work_life_balance, gehalt, karriere, vorgesetzte,
gleichberechtigung` — nur diese sechs Sub-Ratings existieren in beiden
Quellen und werden in der Heatmap quellenuebergreifend verglichen.
```
```
