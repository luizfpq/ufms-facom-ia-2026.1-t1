"""Menu interativo — Sistema de Recuperação de Informação.

Uso:
    source .venv/bin/activate
    python src/menu.py
"""

import sys
from pathlib import Path

# Check rápido de dependências
try:
    import rank_bm25, sklearn, nltk, pandas
except ImportError:
    print("Erro: dependências não encontradas.")
    print("Ative o venv primeiro:")
    print("  source .venv/bin/activate")
    print("  python src/menu.py")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
CORPUS_PATH = ROOT / "data" / "corpus.jsonl"
QUERIES_PATH = ROOT / "eval" / "queries.tsv"
QRELS_PATH = ROOT / "eval" / "qrels.tsv"
RUNS_DIR = ROOT / "notebooks" / "runs"


def load_system():
    from utils import load_corpus
    from retrievers import (build_bm25_index, build_tfidf_index)

    print("Carregando corpus...", end=" ", flush=True)
    corpus = load_corpus(str(CORPUS_PATH))
    print(f"{len(corpus)} docs")

    print("Construindo BM25...", end=" ", flush=True)
    bm25 = build_bm25_index(corpus)
    print("OK")

    print("Construindo TF-IDF...", end=" ", flush=True)
    vec, mat = build_tfidf_index(corpus)
    print("OK\n")

    return corpus, bm25, vec, mat


def do_search(corpus, bm25, vec, mat):
    from retrievers import search_bm25, search_knn, reciprocal_rank_fusion

    query = input("  Query: ").strip()
    if not query:
        return

    bm25_res = search_bm25(query, bm25, corpus, k=10)
    knn_res = search_knn(query, vec, mat, corpus, k=10)
    rrf_res = reciprocal_rank_fusion([
        search_bm25(query, bm25, corpus, k=100),
        search_knn(query, vec, mat, corpus, k=100),
    ])[:10]

    doc_map = {d["arxiv_id"]: d for d in corpus}
    for name, res in [("BM25", bm25_res), ("KNN/TF-IDF", knn_res), ("RRF", rrf_res)]:
        print(f"\n  [{name}]")
        for i, (doc_id, score) in enumerate(res[:5], 1):
            title = doc_map.get(doc_id, {}).get("title", "?")[:70]
            print(f"    {i}. [{score:.4f}] {title}")


def do_evaluate():
    import subprocess
    cmd = [sys.executable, str(ROOT / "eval" / "evaluate.py"),
           "--qrels", str(QRELS_PATH),
           "--runs", str(RUNS_DIR / "bm25.trec"),
           str(RUNS_DIR / "knn.trec"), str(RUNS_DIR / "rrf.trec"),
           "--k", "10"]
    subprocess.run(cmd)


def do_pipeline():
    import subprocess
    subprocess.run([sys.executable, str(ROOT / "src" / "run_pipeline.py")])


def do_stats():
    from utils import load_corpus
    corpus = load_corpus(str(CORPUS_PATH))
    years = {}
    for d in corpus:
        y = d.get("published", "")[:4]
        years[y] = years.get(y, 0) + 1

    print(f"\n  Corpus: {len(corpus)} documentos")
    print(f"  Distribuição por ano:")
    for y in sorted(years):
        print(f"    {y}: {years[y]}")


def main():
    print("=" * 50)
    print(" Sistema de RI — IA Aplicada a Compras Públicas")
    print(" UFMS FACOM · IA 2026.1 · Luiz Quirino")
    print("=" * 50)

    corpus, bm25, vec, mat = load_system()

    while True:
        print("\n  [1] Buscar (query → ranking dos 3 sistemas)")
        print("  [2] Rodar avaliação (P@10, MAP, nDCG)")
        print("  [3] Regenerar runs (pipeline completo)")
        print("  [4] Estatísticas do corpus")
        print("  [0] Sair")

        choice = input("\n  Opção: ").strip()

        if choice == "1":
            do_search(corpus, bm25, vec, mat)
        elif choice == "2":
            do_evaluate()
        elif choice == "3":
            do_pipeline()
        elif choice == "4":
            do_stats()
        elif choice == "0":
            print("\n  Até mais!")
            break
        else:
            print("  Opção inválida.")


if __name__ == "__main__":
    main()
