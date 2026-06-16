"""Coleta de artigos — Semantic Scholar API (backup ao ArXiv).

O ArXiv está com rate limit no IP. Semantic Scholar tem API gratuita
com 100 req/5min sem chave, e retorna papers com abstract.

Uso:
    python src/coleta_s2.py
"""

import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

S2_API = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "paperId,externalIds,title,abstract,authors,year,fieldsOfStudy,publicationDate"

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

QUERIES = [
    "public procurement NLP",
    "government procurement machine learning",
    "e-procurement automation",
    "tender document analysis",
    "legal document classification NLP",
    "legal text mining",
    "regulatory compliance automation",
    "legal information retrieval",
    "contract analysis NLP",
    "bid evaluation machine learning",
    "administrative document processing",
    "procurement fraud detection",
    "legal NLP transformer",
    "document conformity checking",
    "public sector artificial intelligence",
]

YEAR_FROM = 2018
TARGET_SIZE = 2000
PER_QUERY_LIMIT = 200  # S2 retorna max 100 por página, paginamos até 200

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RAW_PATH = OUTPUT_DIR / "s2_raw.jsonl"
CORPUS_PATH = OUTPUT_DIR / "corpus.jsonl"


# ---------------------------------------------------------------------------
# Funções
# ---------------------------------------------------------------------------

def already_collected_ids(path: Path) -> set:
    if not path.exists():
        return set()
    ids = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                ids.add(obj.get("paperId") or obj.get("arxiv_id", ""))
            except Exception:
                continue
    return ids


def search_s2(query, offset=0, limit=100, year_from=2018):
    """Busca na Semantic Scholar API. Retorna (papers, total, next_offset)."""
    params = urllib.parse.urlencode({
        "query": query,
        "offset": offset,
        "limit": limit,
        "fields": FIELDS,
        "year": f"{year_from}-",
    })
    url = f"{S2_API}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "UFMS-FACOM-IA/1.0"})

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    papers = data.get("data", [])
    total = data.get("total", 0)
    next_offset = data.get("next", None)
    return papers, total, next_offset


def normalize_paper(paper):
    """Converte paper S2 para formato compatível com o resto do pipeline."""
    ext_ids = paper.get("externalIds") or {}
    arxiv_id = ext_ids.get("ArXiv", "")
    doi = ext_ids.get("DOI")

    authors = [a.get("name", "") for a in (paper.get("authors") or [])]

    return {
        "arxiv_id": arxiv_id or paper.get("paperId", ""),
        "paper_id_s2": paper.get("paperId", ""),
        "title": (paper.get("title") or "").strip(),
        "abstract": (paper.get("abstract") or "").strip(),
        "authors": authors,
        "categories": paper.get("fieldsOfStudy") or [],
        "primary_category": (paper.get("fieldsOfStudy") or [""])[0] if paper.get("fieldsOfStudy") else "",
        "published": paper.get("publicationDate") or str(paper.get("year", "")),
        "doi": doi,
        "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else None,
    }


def collect_query(query, seen, out_path, year_from, per_query_limit):
    """Coleta artigos para uma query."""
    offset = 0
    added = 0

    with open(out_path, "a", encoding="utf-8") as f:
        while added < per_query_limit:
            try:
                papers, total, next_off = search_s2(query, offset, 100, year_from)
            except Exception as e:
                print(f"    [erro] {e}")
                time.sleep(30)
                break

            if not papers:
                break

            for p in papers:
                rec = normalize_paper(p)
                if not rec["abstract"] or len(rec["abstract"]) < 50:
                    continue
                uid = rec["paper_id_s2"]
                if uid in seen:
                    continue

                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                seen.add(uid)
                added += 1

            print(f"    +{len(papers)} papers (novos={added}, global={len(seen)})")

            if next_off is None or offset + 100 >= per_query_limit:
                break
            offset = next_off
            time.sleep(3)  # rate limit: ~100 req/5min

    return added


def deduplicate(raw_path, corpus_path):
    import pandas as pd

    raw = []
    with open(raw_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                raw.append(json.loads(line))
            except Exception:
                continue

    print(f"Registros brutos: {len(raw)}")
    df = pd.DataFrame(raw)
    # Dedup por title normalizado (papers podem ter IDs diferentes em fontes distintas)
    df["title_norm"] = df["title"].str.lower().str.strip()
    df = df.drop_duplicates("title_norm", keep="last")
    df = df[df["title"].str.len() > 0]
    df = df[df["abstract"].str.len() > 50]
    df = df.drop(columns=["title_norm"])

    cols = ["arxiv_id", "title", "abstract", "authors", "categories",
            "primary_category", "published", "doi", "pdf_url"]
    # Manter apenas colunas que existem
    cols = [c for c in cols if c in df.columns]

    with open(corpus_path, "w", encoding="utf-8") as f:
        for _, row in df[cols].iterrows():
            f.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")

    print(f"Corpus limpo: {len(df)} documentos → {corpus_path}")
    return len(df)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    seen = already_collected_ids(RAW_PATH)
    print(f"Artigos já coletados: {len(seen)}")
    print(f"Meta: {TARGET_SIZE}")
    print()

    for i, q in enumerate(QUERIES):
        if len(seen) >= TARGET_SIZE:
            print(f"\nMeta de {TARGET_SIZE} atingida!")
            break

        print(f"[{i+1}/{len(QUERIES)}] Query: \"{q}\"")
        collect_query(q, seen, RAW_PATH, YEAR_FROM, PER_QUERY_LIMIT)

        # Pausa entre queries
        if i < len(QUERIES) - 1 and len(seen) < TARGET_SIZE:
            time.sleep(5)

    if RAW_PATH.exists() and len(seen) > 0:
        print(f"\n--- Deduplicação e limpeza ---")
        deduplicate(RAW_PATH, CORPUS_PATH)
    else:
        print("\nNenhum artigo coletado.")
