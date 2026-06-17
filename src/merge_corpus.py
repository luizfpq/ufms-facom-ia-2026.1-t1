"""Integra o arXiv ao corpus existente, sem alterar os ids dos documentos
ja anotados nos qrels.

O que faz:
 1. Le data/corpus.jsonl (OpenAlex + BDTD ja validados) e infere o campo
    `source` pelo prefixo do id (W -> openalex, B -> bdtd).
 2. Le data/arxiv_raw.jsonl (coleta arXiv on-topic).
 3. Deduplica o arXiv contra o corpus por titulo normalizado e por DOI.
 4. Anexa os documentos novos do arXiv com source='arxiv'.
 5. Reescreve data/corpus.jsonl com o campo `source` em todos os registros.

O campo `arxiv_id` e mantido como id canonico do documento (heranca do
material de apoio do professor); para OpenAlex/BDTD ele guarda o id daquela
base, e para o arXiv guarda o id real do arXiv.

Uso: python src/merge_corpus.py
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus.jsonl"
ARXIV = ROOT / "data" / "arxiv_raw.jsonl"
BACKUP = ROOT / "data" / "corpus_pre_arxiv.jsonl"

COLS = ["arxiv_id", "title", "abstract", "authors", "categories",
        "primary_category", "published", "doi", "pdf_url", "language", "source"]


def norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def norm_doi(d) -> str:
    if not d:
        return ""
    return str(d).lower().replace("https://doi.org/", "").strip()


def infer_source(rec: dict) -> str:
    if rec.get("source"):
        return rec["source"]
    aid = str(rec.get("arxiv_id", ""))
    if aid.startswith("W"):
        return "openalex"
    if aid.startswith("B"):
        return "bdtd"
    return "desconhecida"


def load_jsonl(path: Path) -> list:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def main():
    corpus = load_jsonl(CORPUS)
    print(f"Corpus atual: {len(corpus)} documentos")

    # Backup antes de reescrever
    shutil.copy(CORPUS, BACKUP)

    titles = {norm_title(d.get("title")) for d in corpus}
    dois = {norm_doi(d.get("doi")) for d in corpus if d.get("doi")}

    for d in corpus:
        d["source"] = infer_source(d)
        d.setdefault("language", "en")

    arxiv = load_jsonl(ARXIV)
    added = 0
    dup = 0
    for r in arxiv:
        nt = norm_title(r.get("title"))
        nd = norm_doi(r.get("doi"))
        if nt in titles or (nd and nd in dois):
            dup += 1
            continue
        r["source"] = "arxiv"
        r.setdefault("language", "en")
        corpus.append(r)
        titles.add(nt)
        if nd:
            dois.add(nd)
        added += 1

    with open(CORPUS, "w", encoding="utf-8") as f:
        for d in corpus:
            row = {c: d.get(c) for c in COLS}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"arXiv: {len(arxiv)} lidos, {added} novos, {dup} duplicados")
    print(f"Corpus final: {len(corpus)} documentos")
    by_src = {}
    for d in corpus:
        by_src[d["source"]] = by_src.get(d["source"], 0) + 1
    print("Por fonte:", by_src)


if __name__ == "__main__":
    main()
