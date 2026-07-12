"""Inkrementelle Verarbeitung neuer Formular-Antworten.

Liest unverarbeitete Zeilen aus submissions.csv, laesst sie durch Cleaning +
Anreicherung laufen, haengt sie an reviews_enriched.csv und an den ChromaDB-Index
an (ohne Neuaufbau) und markiert sie als verarbeitet.

Aufruf:  py ingest.py            (nutzt Ollama, falls verfuegbar)
         py ingest.py --no-llm   (Sentiment regelbasiert, ohne KI)
"""
import json
import importlib
import argparse
import pandas as pd

import config
import schema
import llm
import feedback_utils as fb

clean = importlib.import_module("02_clean")
enrich = importlib.import_module("03_enrich")


def verarbeite(use_llm: bool) -> int:
    neu = fb.unverarbeitete()
    if neu.empty:
        print("Keine neuen Antworten.")
        return 0
    print(f"{len(neu)} neue Antwort(en) gefunden.")

    df = neu.reindex(columns=schema.CANONICAL_COLUMNS).copy()
    df = clean.standardize(df)
    df = clean.flag_missing(df)
    df["is_duplicate"] = False

    # Anreicherung
    out = [enrich.enrich_row(row, use_llm) for _, row in df.iterrows()]
    df["sentiment"] = [r["sentiment"] for r in out]
    df["kategorien"] = [json.dumps(r["kategorien"], ensure_ascii=False) for r in out]
    df["keywords"] = [json.dumps(r["keywords"], ensure_ascii=False) for r in out]
    df["summary"] = [r["summary"] for r in out]

    # An enriched.csv anhaengen (Spalten des Bestands uebernehmen)
    if config.ENRICHED_CSV.exists():
        bestand = pd.read_csv(config.ENRICHED_CSV, nrows=0)
        df = df.reindex(columns=bestand.columns)
        df.to_csv(config.ENRICHED_CSV, mode="a", header=False, index=False)
    else:
        df.to_csv(config.ENRICHED_CSV, index=False)
    print(f"-> {len(df)} Zeilen an {config.ENRICHED_CSV.name} angehaengt.")

    # An ChromaDB-Index anhaengen (kein Neuaufbau)
    if llm.ollama_available():
        import chromadb
        index = importlib.import_module("04_build_index")
        client = chromadb.PersistentClient(path=config.CHROMA_DIR)
        col = client.get_or_create_collection(config.COLLECTION_NAME,
                                              metadata={"hnsw:space": "cosine"})
        ids, docs, embs, metas = [], [], [], []
        for _, row in df.iterrows():
            doc = index.build_document(row)
            if not doc.strip():
                continue
            ids.append(str(row["review_id"]))
            docs.append(doc)
            embs.append(llm.embed(doc))
            metas.append(index.build_metadata(row))
        if ids:
            col.add(ids=ids, documents=docs, embeddings=embs, metadatas=metas)
        print(f"-> {len(ids)} Dokument(e) zum Index hinzugefuegt.")
    else:
        print("Ollama nicht verfuegbar -> Index nicht aktualisiert (Antworten sind aber "
              "im Dashboard sichtbar; RAG erst nach 'py 04_build_index.py').")

    # Als verarbeitet markieren
    alle = pd.read_csv(config.SUBMISSIONS_CSV)
    alle.loc[alle["review_id"].isin(df["review_id"]), "processed"] = True
    alle.to_csv(config.SUBMISSIONS_CSV, index=False)
    return len(df)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-llm", action="store_true")
    args = ap.parse_args()
    use_llm = (not args.no_llm) and llm.ollama_available()
    n = verarbeite(use_llm)
    print(f"Fertig: {n} Antwort(en) verarbeitet.")


if __name__ == "__main__":
    main()
