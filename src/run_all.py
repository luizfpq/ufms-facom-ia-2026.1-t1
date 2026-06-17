"""Orquestra todos os recuperadores e modulos sobre o corpus atual.

Gera as runs TREC em notebooks/runs/ (bm25, knn, dense, rrf, m1, m3) e
salva analises de M2 (clustering) e M4 (otimizacao) em resultados/.

Uso: python src/run_all.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))

import numpy as np
from utils import load_corpus, load_queries, write_trec_run
from retrievers import (build_bm25_index, search_bm25, build_tfidf_index,
                        search_knn, build_dense_index, search_dense,
                        reciprocal_rank_fusion)
import modules
import evaluate as ev

CORPUS = ROOT / "data" / "corpus.jsonl"
QUERIES = ROOT / "eval" / "queries.tsv"
QRELS = ROOT / "eval" / "qrels.tsv"
RUNS = ROOT / "notebooks" / "runs"
RES = ROOT / "resultados"
RUNS.mkdir(parents=True, exist_ok=True)
RES.mkdir(parents=True, exist_ok=True)
EMB_CACHE = str(ROOT / "data" / "dense_emb.npy")


def write_run(run, name):
    path = RUNS / f"{name}.trec"
    path.unlink(missing_ok=True)
    for qid, results in run.items():
        write_trec_run(results, qid, name, str(path))
    return path


def main():
    corpus = load_corpus(str(CORPUS))
    queries = load_queries(str(QUERIES))
    qrels = ev.read_qrels(QRELS)
    print(f"corpus={len(corpus)} queries={len(queries)}")

    print("indices: bm25...", end=" ", flush=True)
    bm25 = build_bm25_index(corpus)
    print("tfidf...", end=" ", flush=True)
    tfidf_vec, tfidf_mat = build_tfidf_index(corpus)
    print("dense...", flush=True)
    dense = build_dense_index(corpus, cache_path=EMB_CACHE)

    # --- baselines ---
    runs = {}
    runs["bm25"] = {q: search_bm25(t, bm25, corpus, 100) for q, t in queries.items()}
    runs["knn"] = {q: search_knn(t, tfidf_vec, tfidf_mat, corpus, 100) for q, t in queries.items()}
    runs["dense"] = {q: search_dense(t, dense, corpus, 100) for q, t in queries.items()}
    # M5: RRF sparse + dense neural
    runs["rrf"] = {}
    for q, t in queries.items():
        runs["rrf"][q] = reciprocal_rank_fusion(
            [search_bm25(t, bm25, corpus, 100), search_dense(t, dense, corpus, 100)])[:100]

    # --- M1 re-ranking ---
    print("M1 re-ranking...", flush=True)
    runs["m1"] = modules.m1_rerank(queries, qrels, corpus, bm25, tfidf_vec, tfidf_mat, dense)

    # --- M3 expansao de consulta ---
    print("M3 expansao...", flush=True)
    runs["m3"], m3_terms = modules.m3_expand(queries, corpus, bm25)

    for name, run in runs.items():
        write_run(run, name)
    print("runs gravadas:", list(runs.keys()))

    # --- M2 clustering (consulta exemplo) ---
    print("M2 clustering...", flush=True)
    sample_q = queries["q14"]
    k, sil, facets = modules.m2_cluster(sample_q, corpus, dense, bm25, top=30)
    with open(RES / "m2_clustering.txt", "w", encoding="utf-8") as f:
        f.write(f"Consulta: {sample_q}\nMelhor k={k} (silhueta={sil:.3f})\n\nFacetas:\n")
        for c, terms in facets.items():
            f.write(f"  cluster {c}: {', '.join(terms)}\n")

    # --- M4 otimizacao ---
    print("M4 grid search...", flush=True)
    def map_of(run):
        df = ev.evaluate(qrels, {q: [(r, s, d) for r, (d, s) in enumerate(v, 1)]
                                  for q, v in run.items()}, 10)
        return float(df["AP"].mean()) if not df.empty else 0.0
    grid, best = modules.m4_grid_search(queries, qrels, corpus, map_of,
                                        k1_grid=[1.2, 1.5, 2.0], b_grid=[0.5, 0.75, 1.0])
    with open(RES / "m4_otimizacao.txt", "w", encoding="utf-8") as f:
        f.write("k1\tb\tMAP\n")
        for k1, b, m in grid:
            f.write(f"{k1}\t{b}\t{m:.4f}\n")
        f.write(f"\nMelhor: k1={best[0]}, b={best[1]}, MAP={best[2]:.4f}\n")
    print(f"M4 melhor: k1={best[0]} b={best[1]} MAP={best[2]:.4f}")
    print("M3 termos de expansao (amostra):",
          {q: m3_terms[q] for q in list(m3_terms)[:3]})


if __name__ == "__main__":
    main()
