"""Schritt 3: Anreicherung per Prompt-Chain (Konzept-Phase 2).

Pro Bewertung erzeugt das lokale LLM Metadaten:
  - sentiment  (positiv | neutral | negativ)
  - kategorien (z.B. Leadership, Work-Life-Balance, Bezahlung ...)
  - keywords
  - summary    (1 Satz)

Diese Felder speisen spaeter Dashboard UND RAG-Filter.
Ohne Ollama wird ein regelbasierter Fallback genutzt (Sentiment aus Score),
damit die Pipeline auch ohne LLM lauffaehig bleibt.
"""
import json
import pandas as pd
import config
import llm

KATEGORIEN = [
    "Arbeitsatmosphaere", "Work-Life-Balance", "Bezahlung", "Karriere & Weiterbildung",
    "Fuehrung & Vorgesetzte", "Kommunikation", "Arbeitsbedingungen",
    "Diversitaet & Gleichberechtigung", "Bewerbungsprozess", "Sonstiges",
]

SYSTEM = (
    "Du analysierst Mitarbeiter-/Bewerberbewertungen eines Unternehmens. "
    "Antworte ausschliesslich als JSON mit den Schluesseln: "
    "sentiment (positiv|neutral|negativ), kategorien (Liste aus der vorgegebenen Auswahl), "
    "keywords (Liste, max 5), summary (ein knapper deutscher Satz)."
)


def _review_text(row) -> str:
    teile = [row.get("titel"), row.get("text_positiv"), row.get("text_negativ"),
             row.get("text_verbesserung"), row.get("text_freitext")]
    return " | ".join(str(t) for t in teile if pd.notna(t) and str(t).strip())


def _fallback(row) -> dict:
    score = row.get("gesamt_score")
    sent = "neutral"
    if pd.notna(score):
        sent = "positiv" if score >= 3.5 else "negativ" if score < 2.5 else "neutral"
    return {"sentiment": sent, "kategorien": [], "keywords": [], "summary": row.get("titel") or ""}


def enrich_row(row, use_llm: bool) -> dict:
    text = _review_text(row)
    if not use_llm or not text.strip():
        return _fallback(row)
    prompt = (f"Auswahl Kategorien: {', '.join(KATEGORIEN)}\n\n"
              f"Bewertung:\n{text}\n\nGib das JSON zurueck.")
    res = llm.generate_json(prompt, system=SYSTEM, model=config.ENRICH_MODEL)
    if not res:
        return _fallback(row)
    return {
        "sentiment": res.get("sentiment", _fallback(row)["sentiment"]),
        "kategorien": res.get("kategorien", []),
        "keywords": res.get("keywords", []),
        "summary": res.get("summary", row.get("titel") or ""),
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-llm", action="store_true",
                    help="Schnell: kein LLM, Sentiment regelbasiert aus Score")
    args = ap.parse_args()

    df = pd.read_csv(config.CLEAN_CSV)
    use_llm = (not args.no_llm) and llm.ollama_available()
    if use_llm:
        print(f"KI-Anreicherung mit Modell '{config.ENRICH_MODEL}' fuer {len(df)} Bewertungen ...")
        print("(Das laeuft eine Weile - Fortschritt erscheint alle 10 Zeilen.)")
    else:
        print("Schnellmodus ohne KI (Sentiment regelbasiert aus Score).")

    out = []
    for i, row in df.iterrows():
        r = enrich_row(row, use_llm)
        out.append(r)
        if use_llm and (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(df)} angereichert ...")

    df["sentiment"] = [r["sentiment"] for r in out]
    df["kategorien"] = [json.dumps(r["kategorien"], ensure_ascii=False) for r in out]
    df["keywords"] = [json.dumps(r["keywords"], ensure_ascii=False) for r in out]
    df["summary"] = [r["summary"] for r in out]

    df.to_csv(config.ENRICHED_CSV, index=False)
    print(f"Angereichert: {len(df)} Zeilen -> {config.ENRICHED_CSV}")
    print("Sentiment-Verteilung:\n", df["sentiment"].value_counts().to_string())


if __name__ == "__main__":
    main()
