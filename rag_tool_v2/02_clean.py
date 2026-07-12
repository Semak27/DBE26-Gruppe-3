"""Schritt 2: Data Cleaning (Konzept-Phase 1).

- Whitespace/Leerstrings vereinheitlichen
- Standardisierung von Bereich/Ort/Empfehlung
- Duplikaterkennung ueber aehnliche Titel+Texte (Fuzzy)
- Missing Values explizit kennzeichnen (NICHT raten -> sauberer fuers Dashboard)
- optionale LLM-Rechtschreibkorrektur/Uebersetzung der Freitexte (--llm)
"""
import argparse
import pandas as pd
from rapidfuzz import fuzz
import config
import schema

EMPFEHLUNG_MAP = {
    "empfohlen": "Empfohlen", "nicht empfohlen": "Nicht empfohlen",
    "zusage": "Zusage", "absage": "Absage",
}


def _norm_text(s):
    if pd.isna(s):
        return None
    s = str(s).strip()
    return s if s else None


def standardize(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["titel", "position", "bereich", "ort",
                "text_positiv", "text_negativ", "text_verbesserung", "text_freitext"]:
        df[col] = df[col].map(_norm_text)
    df["bereich"] = df["bereich"].fillna("Unbekannt")
    df["ort"] = df["ort"].fillna("Unbekannt")
    df["empfehlung"] = df["empfehlung"].map(
        lambda e: EMPFEHLUNG_MAP.get(str(e).strip().lower(), e) if pd.notna(e) else "Keine Angabe")
    return df


def flag_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Anteil fehlender Sub-Ratings je Zeile als Qualitaetsmass."""
    df["missing_ratings"] = df[schema.ALL_RATINGS].isna().sum(axis=1)
    df["has_freetext"] = df[["text_positiv", "text_negativ",
                             "text_verbesserung", "text_freitext"]].notna().any(axis=1)
    return df


def dedup(df: pd.DataFrame, threshold: int = 95) -> pd.DataFrame:
    """Markiert Beinahe-Duplikate (gleiche Quelle, sehr aehnlicher Text)."""
    df = df.reset_index(drop=True)
    df["is_duplicate"] = False
    keys = (df["titel"].fillna("") + " " + df["text_positiv"].fillna("") + " " +
            df["text_negativ"].fillna("")).tolist()
    seen = []
    for i, k in enumerate(keys):
        if len(k.strip()) < 10:
            seen.append((i, k))
            continue
        for j, prev in seen:
            same_group = (df.at[i, "source"] == df.at[j, "source"]
                          and df.at[i, "unternehmen"] == df.at[j, "unternehmen"])
            if same_group and fuzz.ratio(k, prev) >= threshold:
                df.at[i, "is_duplicate"] = True
                break
        seen.append((i, k))
    return df


def llm_fix_freetext(df: pd.DataFrame) -> pd.DataFrame:
    """Optional: uebersetzt NUR fremdsprachige Freitexte (z.B. Indeed=en) ins
    Deutsche. Deutsche Texte werden nicht angefasst -> deutlich weniger LLM-Aufrufe.
    """
    import llm
    if not llm.ollama_available():
        print("  Ollama nicht erreichbar -> ueberspringe LLM-Uebersetzung")
        return df
    sysmsg = ("Uebersetze den folgenden Text ins Deutsche und korrigiere die "
              "Rechtschreibung. Gib NUR den deutschen Text zurueck, ohne Kommentar.")
    cols = ["text_positiv", "text_negativ", "text_verbesserung", "text_freitext"]
    # nur nicht-deutsche Zeilen
    zu_uebersetzen = df[df["sprache"].astype(str).str.lower() != "de"]
    gesamt = zu_uebersetzen[cols].notna().sum().sum()
    print(f"  Uebersetze {int(gesamt)} fremdsprachige Textfelder ...")
    done = 0
    for idx in zu_uebersetzen.index:
        for col in cols:
            if pd.notna(df.at[idx, col]):
                df.at[idx, col] = llm.generate(df.at[idx, col], system=sysmsg)
                done += 1
                print(f"    {done}/{int(gesamt)}", end="\r")
    print()
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", action="store_true",
                    help="Freitexte zusaetzlich per Ollama korrigieren/uebersetzen")
    args = ap.parse_args()

    df = pd.read_csv(config.UNIFIED_CSV)
    df = standardize(df)
    df = flag_missing(df)
    df = dedup(df)
    if args.llm:
        df = llm_fix_freetext(df)

    df.to_csv(config.CLEAN_CSV, index=False)
    print(f"Bereinigt: {len(df)} Zeilen, davon {int(df['is_duplicate'].sum())} Duplikate markiert")
    print(f"Mit Freitext: {int(df['has_freetext'].sum())} | -> {config.CLEAN_CSV}")


if __name__ == "__main__":
    main()
