"""Demo interativa: dada uma query, retorna ranking dos 3 sistemas.

Uso:
    python src/demo.py
    python src/demo.py "public procurement NLP"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import load_corpus
from retrievers import (build_bm25_index, search_bm25,
                        build_tfidf_index, search_knn,
                        reciprocal_rank_fusion)

ROOT = Path(__file__).resolve().parent.parent
CORPUS_PATH = ROOT / "data" / "corpus.jsonl"


def main():
    print("Carregando corpus...", end=" ", flush=True)
    corpus = load_corpus(str(CORPUS_PATH))
    doc_map = {d["arxiv_id"]: d for d in corpus}
    print(f"{len(corpus)} docs")

    print("Construindo índices...", end=" ", flush=True)
    bm25_index = build_bm25_index(corpus)
    vectorizer, tfidf_matrix = build_tfidf_index(corpus)
    print("OK\n")

    # Query via argumento ou interativa
    if len(sys.argv) > 1:
        queries = [" ".join(sys.argv[1:])]
    else:
        queries = None

    while True:
        if queries:
            query = queries.pop(0)
        else:
            try:
                query = input("Query (ou 'q' para sair): ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not query or query.lower() == "q":
                break

        bm25_res = search_bm25(query, bm25_index, corpus, k=10)
        knn_res = search_knn(query, vectorizer, tfidf_matrix, corpus, k=10)
        rrf_res = reciprocal_rank_fusion([
            search_bm25(query, bm25_index, corpus, k=100),
            search_knn(query, vectorizer, tfidf_matrix, corpus, k=100),
        ])[:10]

        for name, results in [("BM25", bm25_res), ("KNN", knn_res), ("RRF", rrf_res)]:
            print(f"\n{'='*60}")
            print(f" {name} — Top 5")
            print(f"{'='*60}")
            for i, (doc_id, score) in enumerate(results[:5], 1):
                doc = doc_map.get(doc_id, {})
                print(f"  {i}. [{score:.4f}] {doc.get('title', '?')[:75]}")

        print()
        if queries is not None:
            break


if __name__ == "__main__":
    main()
