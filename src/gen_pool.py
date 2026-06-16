"""Gera pool de documentos para anotação de relevância (qrels).

Pega top-10 de cada sistema (BM25, KNN, RRF) por query, remove duplicatas,
e gera um arquivo markdown para anotação manual + um qrels.tsv template.

Uso:
    python src/gen_pool.py
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import load_corpus, load_queries

ROOT = Path(__file__).resolve().parent.parent
CORPUS_PATH = ROOT / "data" / "corpus.jsonl"
QUERIES_PATH = ROOT / "eval" / "queries.tsv"
RUNS_DIR = ROOT / "notebooks" / "runs"
POOL_OUT = ROOT / "eval" / "pool_anotacao.md"
QRELS_TEMPLATE = ROOT / "eval" / "qrels.tsv"

POOL_DEPTH = 10  # top-k de cada sistema


def read_run_topk(path, k):
    """Lê top-k doc_ids por query de um .trec."""
    run = defaultdict(list)
    with open(path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                qid, docid, rank = parts[0], parts[2], int(parts[3])
                if rank <= k:
                    run[qid].append(docid)
    return run


def main():
    corpus = load_corpus(str(CORPUS_PATH))
    doc_map = {d["arxiv_id"]: d for d in corpus}
    queries = load_queries(str(QUERIES_PATH))

    # Ler top-k de cada run
    systems = ["bm25", "knn", "rrf"]
    runs = {}
    for sys_name in systems:
        path = RUNS_DIR / f"{sys_name}.trec"
        if path.exists():
            runs[sys_name] = read_run_topk(path, POOL_DEPTH)

    # Gerar pool e markdown
    md_lines = ["# Pool de Anotação — Qrels\n"]
    md_lines.append("> Anote relevância: 0=não-relevante, 1=relevante, 2=muito relevante\n")
    md_lines.append("> Edite o arquivo `eval/qrels.tsv` com suas anotações.\n\n")

    qrels_lines = ["# qid\t0\tdoc_id\trelevancia (0/1/2)\n"]

    for qid in sorted(queries.keys()):
        query_text = queries[qid]
        # Pool: união dos top-k de todos os sistemas
        pool_ids = []
        seen = set()
        for sys_name in systems:
            for doc_id in runs.get(sys_name, {}).get(qid, []):
                if doc_id not in seen:
                    pool_ids.append(doc_id)
                    seen.add(doc_id)

        md_lines.append(f"## {qid}: {query_text}\n\n")
        md_lines.append(f"Pool: {len(pool_ids)} docs únicos\n\n")

        for i, doc_id in enumerate(pool_ids, 1):
            doc = doc_map.get(doc_id, {})
            title = doc.get("title", "???")
            abstract = doc.get("abstract", "")[:300]
            # Quais sistemas retornaram este doc
            from_sys = [s for s in systems if doc_id in runs.get(s, {}).get(qid, [])]

            md_lines.append(f"### {i}. `{doc_id}` — [{', '.join(from_sys)}]\n")
            md_lines.append(f"**{title}**\n\n")
            md_lines.append(f"{abstract}...\n\n")
            md_lines.append(f"**Relevância:** ___\n\n---\n\n")

            # Template qrels (default 0, para o usuário editar)
            qrels_lines.append(f"{qid}\t0\t{doc_id}\t0\n")

    # Salvar
    with open(POOL_OUT, "w", encoding="utf-8") as f:
        f.writelines(md_lines)

    with open(QRELS_TEMPLATE, "w", encoding="utf-8") as f:
        f.writelines(qrels_lines)

    print(f"Pool de anotação: {POOL_OUT}")
    print(f"Template qrels:   {QRELS_TEMPLATE}")
    print(f"Total de julgamentos a fazer: {len(qrels_lines) - 1}")
    print()
    print("Instruções:")
    print("1. Abra eval/pool_anotacao.md para ver título+abstract de cada doc")
    print("2. Edite eval/qrels.tsv alterando o último campo (0→1 ou 0→2)")
    print("   0 = não-relevante, 1 = relevante, 2 = muito relevante")


if __name__ == "__main__":
    main()
