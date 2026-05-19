import json
from pathlib import Path


def load_corpus(path: str) -> list[dict]:
    docs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                docs.append(json.loads(line))
    return docs


def write_trec_run(results: list[tuple[str, float]], query_id: str,
                   system_name: str, path: str, mode: str = 'a') -> None:
    """Escreve resultados no formato TREC: qid Q0 doc_id rank score system."""
    with open(path, mode) as f:
        for rank, (doc_id, score) in enumerate(results, start=1):
            f.write(f"{query_id}\tQ0\t{doc_id}\t{rank}\t{score:.6f}\t{system_name}\n")


def load_queries(path: str) -> dict[str, str]:
    """Lê queries.tsv: qid TAB texto"""
    queries = {}
    with open(path) as f:
        for line in f:
            parts = line.strip().split('\t', 1)
            if len(parts) == 2:
                queries[parts[0]] = parts[1]
    return queries
