"""Zentrale Konfiguration fuer das Nordzucker RAG-Tool."""
from pathlib import Path

# --- Pfade -------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent            # Ordner mit den Excel-Rohdaten
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"               # optionaler Ablageort fuer Rohdaten
CHROMA_DIR = str(DATA_DIR / "chroma")    # Vektor-DB

UNIFIED_CSV = DATA_DIR / "reviews_unified.csv"     # nach Harmonisierung
CLEAN_CSV   = DATA_DIR / "reviews_clean.csv"       # nach Cleaning
ENRICHED_CSV = DATA_DIR / "reviews_enriched.csv"   # nach Anreicherung (Dashboard-Basis)

# Ordner mit den VW-FS-Wettbewerbsdaten
VWFS_DIR = DATA_DIR / "VW FS"

# Datenquellen-Registry: (unternehmen, quelle, dateipfad)
# Neue Unternehmen/Quellen einfach hier ergaenzen.
DATA_SOURCES = [
    ("Nordzucker", "kununu",    PROJECT_DIR / "Nordzucker_Kununu_Bewertungen_raw.xlsx"),
    ("Nordzucker", "glassdoor", PROJECT_DIR / "Glassdoor_Bewertungen_synthetisch_30_Datensaetze.xlsx"),
    ("Nordzucker", "indeed",    PROJECT_DIR / "Indeed_Bewertungen_synthetisch_10_Datensaetze.xlsx"),
    ("VW FS",      "kununu",    VWFS_DIR / "VWFS_Braunschweig_Kununu_Bewertungen_synthetisch_50.xlsx"),
    ("VW FS",      "glassdoor", VWFS_DIR / "VWFS_Braunschweig_Glassdoor_Bewertungen_synthetisch_20.xlsx"),
    ("VW FS",      "indeed",    VWFS_DIR / "VWFS_Braunschweig_Indeed_Bewertungen_synthetisch_10.xlsx"),
]

# Eigenes Unternehmen (Referenz im Wettbewerbsvergleich)
HAUPTUNTERNEHMEN = "Nordzucker"

# --- Feedback-Formular / Versand ---------------------------------------
SUBMISSIONS_CSV = DATA_DIR / "submissions.csv"   # Formular-Eingaenge
TOKENS_CSV      = DATA_DIR / "tokens.csv"        # Einmal-Token je Empfaenger
EMPFAENGER_CSV  = DATA_DIR / "empfaenger.csv"    # Mailadressen
FORM_QUELLE = "intern"                            # Quelle interner Befragungen
FORM_PORT = 8502                                  # Port der Formular-App
NGROK_API = "http://localhost:4040/api/tunnels"   # lokale ngrok-Schnittstelle

# --- Ollama ------------------------------------------------------------
OLLAMA_HOST = "http://localhost:11434"
LLM_MODEL = "llama3.1"            # RAG-Antworten (Qualitaet)
ENRICH_MODEL = "llama3.2"        # Massen-Anreicherung (klein & schnell). Alternativ "llama3.1".
EMBED_MODEL = "nomic-embed-text" # Embeddings

COLLECTION_NAME = "nordzucker_reviews"

# Anzahl der Belege, die das RAG pro Frage heranzieht
RAG_TOP_K = 6
