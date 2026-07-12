# Backend-Dokumentation — Nordzucker Mitarbeiterfeedback RAG-Tool

Stand: Juni 2026. Diese Dokumentation beschreibt die technische Architektur des
lokal laufenden RAG-Systems: die Verzeichnisstruktur, den Datenfluss und ganz
konkret, was jedes einzelne Python-Skript tut.

---

## 1. Überblick

Das Tool verarbeitet Mitarbeiter- und Bewerberbewertungen der Nordzucker AG aus
drei verschiedenen Quellen (Kununu, Glassdoor, Indeed), die jeweils ein anderes
Spaltenschema haben. Es vereinheitlicht sie, bereinigt und reichert sie per KI an,
macht sie über ein RAG-System abfragbar und stellt die Auswertung in einem
Dashboard dar.

Alles läuft **lokal** auf dem eigenen Rechner — die KI-Modelle über Ollama, die
Vektordatenbank über ChromaDB, das Dashboard über einen lokalen Streamlit-Server.
Es werden keine Daten an externe Dienste übertragen.

Die Verarbeitung folgt den vier Phasen aus dem Projektkonzept:

| Phase | Konzept | Skript |
|-------|---------|--------|
| 0 | Datenquellen vereinheitlichen | `01_harmonize.py` |
| 1 | Data Cleaning | `02_clean.py` |
| 2 | Prompt Chain (Anreicherung) | `03_enrich.py` |
| 3 | RAG-System | `04_build_index.py` + `05_rag.py` |
| 4 | Analytics Dashboard | `dashboard.py` |

---

## 2. Verzeichnisstruktur

```
rag_tool/
├── config.py              # zentrale Einstellungen (Pfade, Modelle, Parameter)
├── schema.py              # kanonisches Schema + Spalten-Mappings der 3 Quellen
├── llm.py                 # Ollama-Wrapper (Textgenerierung + Embeddings)
│
├── 01_harmonize.py        # Phase 0: Quellen -> gemeinsames Schema
├── 02_clean.py            # Phase 1: Cleaning
├── 03_enrich.py           # Phase 2: KI-Anreicherung
├── 04_build_index.py      # Phase 3: Vektorindex aufbauen
├── 05_rag.py              # Phase 3: RAG-Abfragelogik
├── dashboard.py           # Phase 4: Streamlit-Dashboard
│
├── requirements.txt       # Python-Abhängigkeiten
├── README.md              # Kurzanleitung
├── BACKEND_DOKUMENTATION.md
│
└── data/                  # wird von der Pipeline erzeugt
    ├── reviews_unified.csv     # nach 01
    ├── reviews_clean.csv       # nach 02
    ├── reviews_enriched.csv    # nach 03 (Datenbasis des Dashboards)
    └── chroma/                 # ChromaDB-Vektorindex (nach 04)
```

Die Excel-Rohdateien liegen im übergeordneten Projektordner und werden von der
Pipeline automatisch dort gefunden (alternativ in `data/raw/`).

---

## 3. Datenfluss

```
 Excel-Rohdaten (3 Quellen, unterschiedliche Schemata)
        │
        ▼  01_harmonize.py   ── liest die 3 xlsx, mappt auf 1 Schema
 reviews_unified.csv
        │
        ▼  02_clean.py       ── standardisieren, Duplikate, Missing Values
 reviews_clean.csv               (mit --llm zusätzlich Übersetzung/Korrektur)
        │
        ▼  03_enrich.py      ── Sentiment, Kategorien, Keywords, Summary (LLM)
 reviews_enriched.csv ────────┬───────────────┐
        │                     │               │
        ▼  04_build_index.py  │               │
 data/chroma/ (Vektorindex)   │               │
        │                     │               │
        ▼  05_rag.py          ▼               ▼
   RAG-Antworten        dashboard.py    dashboard.py
   (Terminal)           (RAG-Chat-Tab)  (Auswertungs-Tab)
```

Wichtig ist die **Reihenfolge**: Jedes Skript liest die Ausgabedatei des
vorherigen. Ändern sich die Rohdaten, muss die Pipeline ab `01` neu durchlaufen.

---

## 4. Das kanonische Schema

Definiert in `schema.py`. Da die drei Quellen unterschiedliche Spalten haben,
werden alle auf folgende gemeinsame Felder abgebildet:

**Stammdaten:** `review_id`, `source`, `typ`, `datum`, `titel`, `gesamt_score`,
`empfehlung`, `position`, `bereich`, `ort`, `sprache`

**Sub-Ratings, die in allen Quellen vorkommen** (`COMMON_RATINGS`, werden im
Dashboard quellenübergreifend verglichen):
`arbeitsatmosphaere`, `work_life_balance`, `gehalt`, `karriere`, `vorgesetzte`,
`gleichberechtigung`

**Weitere Sub-Ratings** (`EXTRA_RATINGS`, meist nur Kununu): `image`,
`umwelt_sozial`, `kollegen`, `umgang_aeltere`, `arbeitsbedingungen`,
`kommunikation`, `interessante_aufgaben`

**Freitextfelder:** `text_positiv`, `text_negativ`, `text_verbesserung`,
`text_freitext`

**Nach der Anreicherung (03) kommen hinzu:** `sentiment`, `kategorien`,
`keywords`, `summary`, sowie aus dem Cleaning `missing_ratings`, `has_freetext`,
`is_duplicate`.

Die Zuordnung Original-Spalte → kanonisches Feld erfolgt über drei
Mapping-Dictionaries: `KUNUNU_RATING_MAP`, `GLASSDOOR_RATING_MAP`,
`INDEED_RATING_MAP`. Die Beschäftigungstypen werden über `TYP_MAP`
normalisiert (z. B. „Full-time" → „Mitarbeiter", „Apprentice" → „Azubi").

---

## 5. Externe Komponenten

| Komponente | Rolle | Wo |
|------------|-------|-----|
| **Ollama** | Lokaler KI-Server: führt die Sprachmodelle aus | Hintergrunddienst auf `localhost:11434` |
| `llama3.1` | LLM für Anreicherung + RAG-Antworten | über Ollama |
| `nomic-embed-text` | Embedding-Modell (Text → Vektor) | über Ollama |
| **ChromaDB** | Lokale Vektordatenbank für die Ähnlichkeitssuche | Ordner `data/chroma/` |
| **Streamlit** | Web-Framework, das das Dashboard als lokale Webseite bereitstellt | `localhost:8501` |
| **pandas** | Tabellenverarbeitung in allen Skripten | Python-Bibliothek |
| **rapidfuzz** | Fuzzy-Textvergleich für Duplikaterkennung | Python-Bibliothek |
| **plotly / wordcloud** | Diagramme im Dashboard | Python-Bibliothek |

---

## 6. Die Skripte im Detail

### 6.1 `config.py` — zentrale Konfiguration

Enthält keine Logik, sondern alle Einstellungen an einer Stelle:

- **Pfade:** Speicherorte der Zwischendateien (`UNIFIED_CSV`, `CLEAN_CSV`,
  `ENRICHED_CSV`) und des ChromaDB-Ordners (`CHROMA_DIR`).
- **Rohdatei-Namen** der drei Quellen und die Funktion `find_raw()`, die eine
  Datei zuerst in `data/raw/`, dann im Projektordner sucht.
- **Ollama-Einstellungen:** Adresse (`OLLAMA_HOST`), Modellnamen (`LLM_MODEL`,
  `EMBED_MODEL`).
- **RAG-Parameter:** `COLLECTION_NAME` (Name der Vektor-Sammlung) und `RAG_TOP_K`
  (wie viele Belege pro Frage herangezogen werden, aktuell 6).

Alle anderen Skripte importieren `config`, sodass z. B. ein Modellwechsel nur
hier geändert werden muss.

### 6.2 `schema.py` — Schema und Mappings

Reine Definitionsdatei ohne ausführbaren Ablauf. Legt die Listen der kanonischen
Spalten und Ratings fest (siehe Abschnitt 4) und die vier Mapping-Dictionaries,
die `01_harmonize.py` nutzt, um jede Quelle auf das gemeinsame Schema zu bringen.
Zentrale Stelle, wenn eine neue Datenquelle oder ein neues Rating ergänzt wird.

### 6.3 `llm.py` — Schnittstelle zu Ollama

Dünner Wrapper um die Ollama-REST-API. Wird von `02`, `03`, `04` und `05`
genutzt. Funktionen:

- `ollama_available()` — prüft, ob der Ollama-Server erreichbar ist. Damit können
  Skripte in einen Fallback wechseln, statt abzustürzen.
- `generate(prompt, system, …)` — schickt einen Prompt an `llama3.1` und gibt die
  Textantwort zurück (für Übersetzung in `02` und RAG-Antworten in `05`).
- `generate_json(prompt, system)` — wie oben, erzwingt aber JSON-Ausgabe und
  parst sie robust zu einem Dict (für die strukturierte Anreicherung in `03`).
- `embed(text)` — wandelt einen Text über `nomic-embed-text` in einen
  Embedding-Vektor um (für Indexaufbau in `04` und Suche in `05`).

### 6.4 `01_harmonize.py` — Phase 0: Vereinheitlichung

**Eingang:** die drei Excel-Dateien. **Ausgang:** `reviews_unified.csv`.

Drei Ladefunktionen, eine pro Quelle:

- `load_kununu()` — liest die Kununu-Datei, filtert leere Zeilen, erzeugt IDs
  (`kununu_1` …), normalisiert den Typ über `TYP_MAP`, übernimmt Score/Datum/
  Position/Bereich/Ort und mappt die Sub-Ratings über `KUNUNU_RATING_MAP`. Die
  Freitextspalten sind in der Kununu-Rohdatei leer, werden aber für ein
  konsistentes Schema mitgeführt.
- `load_glassdoor()` — analog mit `GLASSDOOR_RATING_MAP`; übersetzt „Yes/No" der
  Weiterempfehlung, übernimmt Pros/Cons/Advice als Freitext.
- `load_indeed()` — analog mit `INDEED_RATING_MAP`; Indeed kennt keinen
  expliziten Typ (→ „Mitarbeiter"), die Texte sind englisch (`sprache = "en"`),
  und die wertvolle Spalte „Review Text" wird als `text_freitext` übernommen.

Eine Hilfsfunktion `_clip_score()` stellt sicher, dass alle Ratings numerisch im
Bereich 1–5 liegen (sonst `None`). `main()` ruft alle drei Loader auf, bringt sie
mit `reindex` auf exakt die kanonischen Spalten, hängt sie untereinander
(`concat`) und schreibt die vereinheitlichte CSV.

### 6.5 `02_clean.py` — Phase 1: Data Cleaning

**Eingang:** `reviews_unified.csv`. **Ausgang:** `reviews_clean.csv`.

- `standardize()` — trimmt Whitespace, wandelt leere Strings in „kein Wert",
  füllt fehlende Bereich/Ort mit „Unbekannt" und vereinheitlicht die
  Empfehlungs-Werte über `EMPFEHLUNG_MAP`.
- `flag_missing()` — zählt pro Zeile die fehlenden Sub-Ratings
  (`missing_ratings`) als Qualitätsmaß und markiert, ob überhaupt Freitext
  vorhanden ist (`has_freetext`). Fehlende Werte werden **nicht geraten**, nur
  gekennzeichnet — das hält die Auswertung ehrlich.
- `dedup()` — erkennt Beinahe-Duplikate: vergleicht innerhalb derselben Quelle
  Titel + Freitexte per Fuzzy-Matching (rapidfuzz, Schwelle 95 %) und setzt das
  Flag `is_duplicate`. Die Zeilen bleiben erhalten, werden aber später (in `04`
  und im Dashboard) herausgefiltert.
- `llm_fix_freetext()` — **nur mit Schalter `--llm`**: schickt jeden Freitext an
  Ollama zur Rechtschreibkorrektur und Übersetzung ins Deutsche. Wichtig für die
  englischen Indeed-Texte. Ohne laufendes Ollama wird dieser Schritt
  übersprungen.

### 6.6 `03_enrich.py` — Phase 2: KI-Anreicherung

**Eingang:** `reviews_clean.csv`. **Ausgang:** `reviews_enriched.csv` (die
Datenbasis des Dashboards).

Für jede Bewertung wird der Text (Titel + alle Freitexte) zusammengesetzt und an
`llama3.1` geschickt mit der Aufgabe, **strukturiertes JSON** zu liefern:
`sentiment` (positiv/neutral/negativ), `kategorien` (aus einer fest vorgegebenen
Liste wie Work-Life-Balance, Bezahlung, Führung …), `keywords` und eine
einsätzige `summary`.

- `enrich_row()` — baut den Prompt, ruft `llm.generate_json()` auf und greift bei
  Fehlern auf `_fallback()` zurück.
- `_fallback()` — regelbasierte Notlösung ohne LLM: leitet das Sentiment allein
  aus dem Score ab (≥ 3,5 positiv, < 2,5 negativ, sonst neutral). So bleibt die
  Pipeline auch ohne Ollama lauffähig.

Ergebnisspalten `sentiment`, `kategorien`, `keywords`, `summary` werden an die
Tabelle angehängt und gespeichert. Listen werden als JSON-Strings abgelegt.

### 6.7 `04_build_index.py` — Phase 3: Vektorindex

**Eingang:** `reviews_enriched.csv`. **Ausgang:** `data/chroma/`. Benötigt Ollama.

- Filtert zunächst die als Duplikat markierten Zeilen heraus.
- `build_document()` — setzt pro Bewertung den durchsuchbaren Text zusammen
  (Titel, Positiv, Negativ, Verbesserung, Bericht).
- `build_metadata()` — hängt Filterfelder an jedes Dokument (Quelle, Typ, Datum,
  Bereich, Ort, Score, Sentiment, Empfehlung), damit das RAG später gezielt
  filtern kann.
- In `main()` wird die ChromaDB-Sammlung frisch angelegt, jeder Text über
  `llm.embed()` in einen Vektor umgewandelt und zusammen mit Text + Metadaten
  gespeichert. Bewertungen ohne Text werden übersprungen. Als Distanzmaß dient
  Cosine-Similarity.

### 6.8 `05_rag.py` — Phase 3: RAG-Abfrage

Die eigentliche Frage-Antwort-Logik. Wird sowohl im Terminal als auch vom
Dashboard genutzt.

- `retrieve(frage, top_k, where)` — wandelt die Frage in einen Vektor um, sucht
  in ChromaDB die ähnlichsten Bewertungen (Standard: 6) und erlaubt optionale
  Metadaten-Filter (`where`), z. B. nur Quelle „kununu" oder nur Sentiment
  „negativ".
- `answer(frage, …)` — baut aus den Treffern einen nummerierten Kontextblock,
  schickt ihn zusammen mit der Frage und einer strengen Systemanweisung („nur auf
  Basis der Belege antworten, nichts erfinden, mit [1], [2] … auf Quellen
  verweisen") an `llama3.1` und gibt Antwort plus Belegliste zurück.
- Direkt im Terminal aufrufbar: `py 05_rag.py "deine Frage"`.

### 6.9 `dashboard.py` — Phase 4: Streamlit-Dashboard

**Eingang:** `reviews_enriched.csv` und der ChromaDB-Index. Startet einen lokalen
Webserver, im Browser unter `http://localhost:8501` erreichbar.

- `load_data()` — lädt die angereicherte CSV, parst Datum und Listenfelder und
  filtert Duplikate. Mit `@st.cache_data` zwischengespeichert.
- **Sidebar:** Filter nach Quelle und Typ, wirkt auf alle Auswertungen.
- **KPI-Zeile:** Anzahl Bewertungen, Ø Gesamtscore, Positiv-Anteil, Anzahl
  Quellen.
- **Tab „Auswertung":** mehrere Plotly-Diagramme — Sentiment-Verteilung,
  Themen-Ranking (aus den KI-Kategorien), Score-Trend über die Zeit, Wordcloud
  aus den Freitexten und eine Heatmap (Ø Bewertung je Bereich über die sechs
  gemeinsamen Sub-Ratings).
- **Tab „RAG-Chat":** Eingabefeld plus Filter (Quelle/Typ/Sentiment). Beim
  Absenden wird `05_rag.answer()` aufgerufen; Antwort und herangezogene Belege
  werden angezeigt. Läuft Ollama nicht, erscheint ein Hinweis statt eines
  Absturzes.

---

## 7. Erzeugte Datendateien

| Datei | Erzeugt von | Inhalt |
|-------|-------------|--------|
| `reviews_unified.csv` | 01 | Alle Quellen im gemeinsamen Schema, roh |
| `reviews_clean.csv` | 02 | Bereinigt, mit Qualitäts- und Duplikat-Flags |
| `reviews_enriched.csv` | 03 | + Sentiment, Kategorien, Keywords, Summary |
| `data/chroma/` | 04 | Vektorindex für die Ähnlichkeitssuche |

---

## 8. Ausführung

Reihenfolge (Ollama muss für `02 --llm`, `03`, `04` und den RAG-Chat laufen):

```
py 01_harmonize.py
py 02_clean.py --llm
py 03_enrich.py
py 04_build_index.py
py -m streamlit run dashboard.py
```

Schritte `01`–`04` nur erneut ausführen, wenn sich die Excel-Rohdaten ändern. Für
einen reinen Neustart des Dashboards genügt der letzte Befehl.

---

## 9. Aktueller Datenstand

- **3 Quellen:** Kununu (139), Glassdoor (30), Indeed (10) = **179 Bewertungen**.
- **Echter Freitext** liegt v. a. bei Glassdoor und Indeed vor; bei Kununu nur
  die Titelzeilen (die dedizierten Freitextspalten sind in der Rohdatei leer).
  Das RAG ist dadurch text-seitig glassdoor-/indeed-lastig.
- **Indeed-Texte sind englisch** und werden im Schritt `02 --llm` ins Deutsche
  übersetzt.

---

## 10. Erweiterungspunkte

- **Neue Datenquelle:** Mapping in `schema.py` ergänzen, Ladefunktion in
  `01_harmonize.py` hinzufügen — der Rest der Pipeline bleibt unverändert.
- **Anderes/Online-Modell:** nur `llm.py` und `config.py` betreffen; ein
  Umschalter lokal (Ollama) / API ist dort möglich, ohne die übrige Pipeline zu
  ändern.
- **Mehr Kununu-Freitext:** sobald die Spalten „Gut/Schlecht/Verbesserung"
  befüllt sind, nutzt die Pipeline sie automatisch.
