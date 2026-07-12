"""Schritt 5: RAG-Abfrage (Konzept-Phase 3).

Frage -> relevante Bewertungen aus ChromaDB -> lokales LLM "erdet" die Antwort
auf diese Belege und liefert eine faktenbasierte Antwort mit Quellenangabe.
Optionale Metadaten-Filter (Quelle, Typ, Sentiment).
"""
import chromadb
import config
import llm

SYSTEM = (
    "Du bist ein HR-Analyse-Assistent fuer die Nordzucker AG. "
    "Beantworte die Frage AUSSCHLIESSLICH auf Basis der bereitgestellten Bewertungen. "
    "Erfinde nichts. Wenn die Belege nicht ausreichen, sage das offen. "
    "Verweise auf Belege mit ihrer Nummer [1], [2], ... und antworte auf Deutsch."
)


def _client():
    return chromadb.PersistentClient(path=config.CHROMA_DIR)


def retrieve(frage: str, top_k: int = None, where: dict | None = None):
    col = _client().get_collection(config.COLLECTION_NAME)
    q_emb = llm.embed(frage)
    res = col.query(query_embeddings=[q_emb], n_results=top_k or config.RAG_TOP_K,
                    where=where or None)
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    return list(zip(docs, metas))


def answer(frage: str, top_k: int = None, where: dict | None = None) -> dict:
    treffer = retrieve(frage, top_k, where)
    if not treffer:
        return {"answer": "Keine passenden Bewertungen gefunden.", "belege": []}

    kontext = "\n\n".join(
        f"[{i+1}] (Quelle: {m['source']}, Typ: {m['typ']}, Score: {m['gesamt_score']}, "
        f"Sentiment: {m['sentiment']})\n{doc}"
        for i, (doc, m) in enumerate(treffer)
    )
    prompt = f"Bewertungen:\n{kontext}\n\nFrage: {frage}\n\nAntwort:"
    antwort = llm.generate(prompt, system=SYSTEM, temperature=0.2)
    return {"answer": antwort, "belege": treffer}


def main():
    import sys
    frage = " ".join(sys.argv[1:]) or \
        "Welche Probleme treten in der Produktion besonders haeufig auf?"
    if not llm.ollama_available():
        raise SystemExit("Ollama laeuft nicht.")
    res = answer(frage)
    print("FRAGE:", frage, "\n")
    print("ANTWORT:\n", res["answer"], "\n")
    print("--- herangezogene Belege ---")
    for i, (doc, m) in enumerate(res["belege"], 1):
        print(f"[{i}] {m['source']}/{m['typ']} | {doc[:90].replace(chr(10), ' ')}...")


if __name__ == "__main__":
    main()
