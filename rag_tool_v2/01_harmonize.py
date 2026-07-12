"""Schritt 1: Alle Rohquellen auf das gemeinsame Schema bringen.

Liest alle in config.DATA_SOURCES registrierten Excel-Dateien (mehrere
Unternehmen x mehrere Quellen) und schreibt EINE vereinheitlichte CSV.
Jede Zeile traegt ein Tag fuer 'unternehmen' UND 'source'.
"""
import re
import warnings
import pandas as pd
import config
import schema


def _clip_score(v):
    try:
        v = float(v)
        return v if 1 <= v <= 5 else None
    except (TypeError, ValueError):
        return None


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def load_kununu(path, unternehmen) -> pd.DataFrame:
    df = pd.read_excel(path)
    df = df[df["Nr"].notna()].copy()
    out = pd.DataFrame()
    out["review_id"] = f"{_slug(unternehmen)}_kununu_" + df["Nr"].astype(int).astype(str)
    out["unternehmen"] = unternehmen
    out["source"] = "kununu"
    out["typ"] = df["Typ"].map(lambda t: schema.TYP_MAP.get(t, t))
    out["datum"] = pd.to_datetime(df["Datum"], errors="coerce")
    out["titel"] = df["Titel"]
    out["gesamt_score"] = df["Score"].map(_clip_score)
    out["empfehlung"] = df["Empfehlung"]
    out["position"] = df["Position"]
    out["bereich"] = df["Bereich"]
    out["ort"] = df["Ort"]
    out["sprache"] = "de"
    for canon, orig in schema.KUNUNU_RATING_MAP.items():
        out[canon] = df[orig].map(_clip_score) if orig in df.columns else None
    out["text_positiv"] = df.get("Gut am Arbeitergeber")
    out["text_negativ"] = df.get("Schlecht am Arbeitgeber ")
    out["text_verbesserung"] = df.get("Verbesserungsvorschläge")
    return out


def load_glassdoor(path, unternehmen) -> pd.DataFrame:
    df = pd.read_excel(path)
    df = df[df["Review Title"].notna()].copy()
    out = pd.DataFrame()
    out["review_id"] = f"{_slug(unternehmen)}_glassdoor_" + (df.reset_index().index + 1).astype(str)
    out["unternehmen"] = unternehmen
    out["source"] = "glassdoor"
    out["typ"] = df["Employment Status"].map(lambda t: schema.TYP_MAP.get(t, "Mitarbeiter"))
    out["datum"] = pd.to_datetime(df["Review Date"], errors="coerce")
    out["titel"] = df["Review Title"]
    out["gesamt_score"] = df["Overall Rating"].map(_clip_score)
    out["empfehlung"] = df["Recommend to Friend"].map(
        {"Yes": "Empfohlen", "No": "Nicht empfohlen"})
    out["position"] = df["Job Title"]
    out["bereich"] = df["Job Function"]
    out["ort"] = df["Location"]
    out["sprache"] = df.get("Language", "de")
    for canon in schema.ALL_RATINGS:
        orig = schema.GLASSDOOR_RATING_MAP.get(canon)
        out[canon] = df[orig].map(_clip_score) if orig and orig in df.columns else None
    out["text_positiv"] = df["Pros"]
    out["text_negativ"] = df["Cons"]
    out["text_verbesserung"] = df["Advice to Management"]
    return out


def load_indeed(path, unternehmen) -> pd.DataFrame:
    df = pd.read_excel(path)
    df = df[df["Review Title"].notna()].copy()
    out = pd.DataFrame()
    out["review_id"] = f"{_slug(unternehmen)}_indeed_" + (df.reset_index().index + 1).astype(str)
    out["unternehmen"] = unternehmen
    out["source"] = "indeed"
    out["typ"] = "Mitarbeiter"
    out["datum"] = pd.to_datetime(df["Review Date"], errors="coerce")
    out["titel"] = df["Review Title"]
    out["gesamt_score"] = df["Overall Rating"].map(_clip_score)
    out["empfehlung"] = "Keine Angabe"
    out["position"] = df["Job Title"]
    out["bereich"] = None
    out["ort"] = df["Location"].map(lambda x: str(x).replace(", Germany", "").strip()
                                    if pd.notna(x) else x)
    out["sprache"] = "en"
    for canon in schema.ALL_RATINGS:
        orig = schema.INDEED_RATING_MAP.get(canon)
        out[canon] = df[orig].map(_clip_score) if orig and orig in df.columns else None
    out["text_positiv"] = df["Pros"]
    out["text_negativ"] = df["Cons"]
    out["text_verbesserung"] = None
    out["text_freitext"] = df["Review Text"]
    return out


LOADERS = {"kununu": load_kununu, "glassdoor": load_glassdoor, "indeed": load_indeed}


def main():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    teile = []
    zusammenfassung = []
    for unternehmen, quelle, pfad in config.DATA_SOURCES:
        if not pfad.exists():
            print(f"  WARNUNG: Datei fehlt, uebersprungen: {pfad}")
            continue
        d = LOADERS[quelle](pfad, unternehmen).reindex(columns=schema.CANONICAL_COLUMNS)
        teile.append(d)
        zusammenfassung.append(f"{unternehmen}/{quelle}: {len(d)}")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        unified = pd.concat(teile, ignore_index=True)
    unified.to_csv(config.UNIFIED_CSV, index=False)
    print("Harmonisiert:")
    for z in zusammenfassung:
        print("  -", z)
    print(f"= {len(unified)} Zeilen | Unternehmen: "
          f"{unified['unternehmen'].value_counts().to_dict()}")
    print(f"-> {config.UNIFIED_CSV}")


if __name__ == "__main__":
    main()
