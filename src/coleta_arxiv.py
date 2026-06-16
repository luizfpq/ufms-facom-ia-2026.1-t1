"""Coleta de artigos ArXiv — IA aplicada a compras públicas/licitações.

Usa urllib direto na API Atom do ArXiv (sem lib `arxiv`) para controle total
de timing e retry. Coleta por keyword individual para evitar 429.

Uso:
    python src/coleta_arxiv.py
"""

import json
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

ATOM = "http://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

QUERIES = [
    "public procurement",
    "government procurement",
    "e-procurement",
    "tender document",
    "bid analysis",
    "contract analysis NLP",
    "legal document classification",
    "legal text NLP",
    "regulatory compliance NLP",
    "legal information retrieval",
    "document conformity checking",
    "administrative text mining",
]

CATEGORIES = ["cs.CL", "cs.IR", "cs.AI", "cs.LG"]
YEAR_FROM = 2018
YEAR_TO = 2026
TARGET_SIZE = 2000
PAGE_SIZE = 20

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RAW_PATH = OUTPUT_DIR / "arxiv_raw.jsonl"
CORPUS_PATH = OUTPUT_DIR / "corpus.jsonl"


# ---------------------------------------------------------------------------
# Funções
# ---------------------------------------------------------------------------

def build_query(keyword, categories):
    cat_part = " OR ".join([f"cat:{c}" for c in categories])
    return f'all:"{keyword}" AND ({cat_part})'


def already_collected_ids(path: Path) -> set:
    if not path.exists():
        return set()
    ids = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                ids.add(json.loads(line)["arxiv_id"])
            except Exception:
                continue
    return ids


def fetch_page(query, start, page_size, max_retries=4):
    """Faz uma request à API e retorna o XML parseado."""
    params = urllib.parse.urlencode({
        "search_query": query,
        "start": start,
        "max_results": page_size,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    url = f"{ATOM}?{params}"

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "UFMS-FACOM-IA/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                if resp.status == 200:
                    return ET.fromstring(resp.read())
        except Exception as e:
            wait = 60 * (2 ** attempt)
            print(f"    [retry {attempt+1}/{max_retries}] {e} — aguardando {wait}s")
            time.sleep(wait)
    return None


def parse_entries(root):
    """Extrai artigos de um XML Atom do ArXiv."""
    entries = []
    for entry in root.findall("atom:entry", NS):
        title = entry.findtext("atom:title", "", NS).strip().replace("\n", " ")
        abstract = entry.findtext("atom:summary", "", NS).strip().replace("\n", " ")
        entry_id = entry.findtext("atom:id", "", NS)

        if not entry_id or "arxiv.org/abs/" not in entry_id:
            continue

        arxiv_id = entry_id.split("/abs/")[-1].split("v")[0]
        published = entry.findtext("atom:published", "", NS)[:10]
        updated = entry.findtext("atom:updated", "", NS)[:10]

        authors = [a.findtext("atom:name", "", NS)
                   for a in entry.findall("atom:author", NS)]

        categories = [c.get("term", "") for c in entry.findall("atom:category", NS)]
        primary = categories[0] if categories else ""

        doi_el = entry.find("arxiv:doi", NS)
        doi = doi_el.text if doi_el is not None else None

        pdf_url = None
        for link in entry.findall("atom:link", NS):
            if link.get("title") == "pdf":
                pdf_url = link.get("href")

        entries.append({
            "arxiv_id": arxiv_id,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "categories": categories,
            "primary_category": primary,
            "published": published,
            "updated": updated,
            "doi": doi,
            "pdf_url": pdf_url,
        })
    return entries


def collect_keyword(keyword, categories, seen, out_path,
                    year_from, year_to, page_size, max_per_kw=300):
    """Coleta artigos para uma keyword individual."""
    query = build_query(keyword, categories)
    start = 0
    added = 0

    with open(out_path, "a", encoding="utf-8") as f:
        while added < max_per_kw:
            print(f"    página start={start}...", end=" ", flush=True)
            root = fetch_page(query, start, page_size)
            if root is None:
                print("FALHOU, pulando keyword")
                break

            entries = parse_entries(root)
            if not entries:
                print(f"0 resultados, fim desta keyword")
                break

            page_added = 0
            for rec in entries:
                year_str = rec.get("published", "")[:4]
                try:
                    year = int(year_str)
                except ValueError:
                    continue
                if year < year_from or year > year_to:
                    continue
                if rec["arxiv_id"] in seen:
                    continue
                if len(rec["abstract"]) < 50:
                    continue

                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                seen.add(rec["arxiv_id"])
                added += 1
                page_added += 1

            print(f"+{page_added} (total kw={added}, global={len(seen)})")
            start += page_size

            # Pausa entre páginas
            time.sleep(15)

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
    df = df.drop_duplicates("arxiv_id", keep="last")
    df = df[df["title"].str.len() > 0]
    df = df[df["abstract"].str.len() > 50]

    cols = ["arxiv_id", "title", "abstract", "authors", "categories",
            "primary_category", "published", "doi", "pdf_url"]
    with open(corpus_path, "w", encoding="utf-8") as f:
        for _, row in df[cols].iterrows():
            f.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")

    print(f"Corpus limpo: {len(df)} documentos → {corpus_path}")

    # Estatísticas
    df["year"] = df["published"].str[:4].astype(int, errors="ignore")
    print("\nDistribuição por ano:")
    print(df["year"].value_counts().sort_index().to_string())
    print("\nTop categorias:")
    print(df["primary_category"].value_counts().head(10).to_string())
    return len(df)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    seen = already_collected_ids(RAW_PATH)
    print(f"Artigos já coletados: {len(seen)}")
    print(f"Meta: {TARGET_SIZE}")
    print()

    for i, kw in enumerate(QUERIES):
        if len(seen) >= TARGET_SIZE:
            print(f"\nMeta de {TARGET_SIZE} atingida!")
            break

        print(f"[{i+1}/{len(QUERIES)}] Keyword: \"{kw}\"")
        collect_keyword(kw, CATEGORIES, seen, RAW_PATH,
                        YEAR_FROM, YEAR_TO, PAGE_SIZE)

        # Pausa entre keywords
        if i < len(QUERIES) - 1 and len(seen) < TARGET_SIZE:
            print("  Pausa 45s entre keywords...")
            time.sleep(45)

    if RAW_PATH.exists() and len(seen) > 0:
        print("\n--- Deduplicação e limpeza ---")
        deduplicate(RAW_PATH, CORPUS_PATH)
    else:
        print("\nNenhum artigo coletado. Tente novamente em 15-30 min.")
