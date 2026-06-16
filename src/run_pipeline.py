"""Pipeline completo: BM25 + KNN + RRF → runs/*.trec

Uso:
    python src/run_pipeline.py
"""

import sys
from pathlib import Path

# Garantir imports do src/
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import load_corpus, load_queries, write_trec_run
from retrievers import (build_bm25_index, search_bm25,
                        build_tfidf_index, search_knn,
                        reciprocal_rank_fusion)

ROOT = Path(__file__).resolve().parent.parent
CORPUS_PATH = ROOT / "data" / "corpus.jsonl"
QUERIES_PATH = ROOT / "eval" / "queries.tsv"
RUNS_DIR = ROOT / "notebooks" / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("Carregando corpus...")
    corpus = load_corpus(str(CORPUS_PATH))
    print(f"  {len(corpus)} documentos")

    print("Carregando queries...")
    queries = load_queries(str(QUERIES_PATH))
    print(f"  {len(queries)} queries")

    # --- BM25 ---
    print("\nConstruindo índice BM25 (k1=1.5, b=0.75)...")
    bm25_index = build_bm25_index(corpus)

    bm25_path = RUNS_DIR / "bm25.trec"
    bm25_path.unlink(missing_ok=True)
    for qid, text in queries.items():
        results = search_bm25(text, bm25_index, corpus, k=100)
        write_trec_run(results, qid, "bm25", str(bm25_path))
    print(f"  → {bm25_path}")

    # --- KNN/TF-IDF ---
    print("\nConstruindo índice TF-IDF...")
    vectorizer, tfidf_matrix = build_tfidf_index(corpus)

    knn_path = RUNS_DIR / "knn.trec"
    knn_path.unlink(missing_ok=True)
    for qid, text in queries.items():
        results = search_knn(text, vectorizer, tfidf_matrix, corpus, k=100)
        write_trec_run(results, qid, "knn", str(knn_path))
    print(f"  → {knn_path}")

    # --- RRF Híbrido ---
    print("\nGerando ranking híbrido (RRF k=60)...")
    rrf_path = RUNS_DIR / "rrf.trec"
    rrf_path.unlink(missing_ok=True)
    for qid, text in queries.items():
        bm25_results = search_bm25(text, bm25_index, corpus, k=100)
        knn_results = search_knn(text, vectorizer, tfidf_matrix, corpus, k=100)
        rrf_results = reciprocal_rank_fusion([bm25_results, knn_results], k=60)[:100]
        write_trec_run(rrf_results, qid, "rrf", str(rrf_path))
    print(f"  → {rrf_path}")

    print("\nPipeline concluído. Runs gerados em:", RUNS_DIR)


if __name__ == "__main__":
    main()
