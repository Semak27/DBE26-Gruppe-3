"""Schritt 4: Embeddings erzeugen und in ChromaDB ablegen (RAG-Aufbau).

Jede Bewertung wird zu einem Dokument (Titel + Freitexte) und mit Metadaten
(Quelle, Typ, Sentiment, Score, Bereich ...) in der lokalen Vektor-DB gespeichert.
Embeddings kommen vom lokalen Ollama-Modell.
"""
import json
import pandas as pd
import chromadb
import config
import llm


def build_document(row) -> str:
    teile = []
    if pd.notna(row.get("titel")):
        teile.append(f"Titel: {row['titel']}")
    if pd.notna(row.get("text_positiv")):
        teile.append(f"Positiv: {row['text_positiv']}")
    if pd.notna(row.get("text_negativ")):
        teile.append(f"Negativ: {row['text_negativ']}")
    if pd.notna(row.get("text_verbesserung")):
        teile.append(f"Verbesserung: {row['text_verbesserung']}")
    if pd.notna(row.get("text_freitext")):
        teile.append(f"Bericht: {row['text_freitext']}")
    return "\n".join(teile)


def build_metadata(row) -> dict:
    def s(v):
        return "" if pd.isna(v) else (round(float(v), 2) if isinstance(v, float) else str(v))
    return {
        "review_id": str(row["review_id"]),
        "unternehmen": s(row.get("unternehmen")),
        "source": s(row.get("source")),
        "typ": s(row.get("typ")),
        "datum": s(row.get("datum"))[:10],
        "bereich": s(row.get("bereich")),
        "ort": s(row.get("ort")),
        "gesamt_score": s(row.get("gesamt_score")),
        "sentiment": s(row.get("sentiment")),
        "empfehlung": s(row.get("empfehlung")),
    }


def main():
    if not llm.ollama_available():
        raise SystemExit("Ollama laeuft nicht. Bitte 'ollama serve' starten und "
                         f"'ollama pull {config.EMBED_MODEL}' ausfuehren.")

    df = pd.read_csv(config.ENRICHED_CSV)
    df = df[~df.get("is_duplicate", False).fillna(False)]  # Duplikate raus

    client = chromadb.PersistentClient(path=config.CHROMA_DIR)
    # Frisch aufbauen
    try:
        client.delete_collection(config.COLLECTION_NAME)
    except Exception:
        pass
    col = client.create_collection(config.COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    ids, docs, embs, metas = [], [], [], []
    for _, row in df.iterrows():
        doc = build_document(row)
        if not doc.strip():
            continue  # ohne Text kein sinnvolles Embedding
        ids.append(str(row["review_id"]))
        docs.append(doc)
        embs.append(llm.embed(doc))
        metas.append(build_metadata(row))

    if ids:
        col.add(ids=ids, documents=docs, embeddings=embs, metadatas=metas)
    print(f"Index aufgebaut: {len(ids)} Dokumente in '{config.COLLECTION_NAME}'")
    print(f"-> {config.CHROMA_DIR}")


if __name__ == "__main__":
    main()
