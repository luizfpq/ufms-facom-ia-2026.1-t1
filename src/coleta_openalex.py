"""Coleta de artigos — OpenAlex API.

OpenAlex é gratuita, aberta e sem rate limit agressivo.
Retorna papers com abstract (via abstract_inverted_index).

Uso:
    python src/coleta_openalex.py
"""

import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

BASE_URL = "https://api.openalex.org/works"
MAILTO = "luiz.quirino@ufms.br"  # polite pool (faster)

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

QUERIES = [
    "public procurement NLP",
    "government procurement machine learning",
    "e-procurement artificial intelligence",
    "tender document analysis",
    "legal document classification",
    "legal text mining NLP",
    "regulatory compliance automation",
    "legal information retrieval",
    "contract analysis natural language processing",
    "bid evaluation machine learning",
    "procurement fraud detection",
    "legal NLP transformer BERT",
    "document conformity checking",
    "administrative text processing",
    "public sector AI automation",
]

YEAR_FROM = 2018
TARGET_SIZE = 2000
PER_PAGE = 100  # max allowed by OpenAlex

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RAW_PATH = OUTPUT_DIR / "openalex_raw.jsonl"
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
                ids.add(json.loads(line)["openalex_id"])
            except Exception:
                continue
    return ids


def reconstruct_abstract(inv_index):
    """Reconstrói abstract a partir do inverted index do OpenAlex."""
    if not inv_index:
        return ""
    word_positions = []
    for word, positions in inv_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort()
    return " ".join(w for _, w in word_positions)


def fetch_page(query, page=1, per_page=100):
    """Busca uma página de resultados no OpenAlex."""
    params = urllib.parse.urlencode({
        "search": query,
        "filter": f"from_publication_date:{YEAR_FROM}-01-01,type:article",
        "per_page": per_page,
        "page": page,
        "select": "id,title,publication_date,authorships,topics,primary_topic,"
                  "abstract_inverted_index,doi,open_access,ids",
        "mailto": MAILTO,
    })
    url = f"{BASE_URL}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "UFMS-FACOM-IA/1.0"})

    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def normalize_work(work):
    """Converte work OpenAlex para formato do corpus."""
    ids = work.get("ids") or {}
    arxiv_id = ""
    if ids.get("openalex"):
        pass
    # Tentar extrair arxiv_id dos IDs externos
    for key, val in ids.items():
        if "arxiv" in key.lower() and val:
            arxiv_id = val.split("/")[-1]
            break

    authors = [a["author"]["display_name"]
               for a in (work.get("authorships") or [])
               if a.get("author", {}).get("display_name")]

    abstract = reconstruct_abstract(work.get("abstract_inverted_index"))

    # Categorias via topics
    topics = work.get("topics") or []
    categories = [t.get("display_name", "") for t in topics[:5]]
    primary = ""
    if work.get("primary_topic"):
        primary = work["primary_topic"].get("display_name", "")

    openalex_id = (work.get("id") or "").replace("https://openalex.org/", "")

    return {
        "openalex_id": openalex_id,
        "arxiv_id": arxiv_id or openalex_id,
        "title": (work.get("title") or "").strip(),
        "abstract": abstract,
        "authors": authors,
        "categories": categories,
        "primary_category": primary,
        "published": work.get("publication_date", ""),
        "doi": work.get("doi"),
        "pdf_url": (work.get("open_access") or {}).get("oa_url"),
    }


def collect_query(query, seen, out_path, max_pages=3):
    """Coleta artigos para uma query (max_pages páginas)."""
    added = 0
    for page in range(1, max_pages + 1):
        try:
            data = fetch_page(query, page, PER_PAGE)
        except Exception as e:
            print(f"    [erro] {e}")
            break

        results = data.get("results", [])
        if not results:
            break

        with open(out_path, "a", encoding="utf-8") as f:
            for work in results:
                rec = normalize_work(work)
                if len(rec["abstract"]) < 50:
                    continue
                if rec["openalex_id"] in seen:
                    continue

                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                seen.add(rec["openalex_id"])
                added += 1

        print(f"    p{page}: +{len(results)} results (novos acum={added}, global={len(seen)})")
        time.sleep(1)

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
    df["title_norm"] = df["title"].str.lower().str.strip()
    df = df.drop_duplicates("title_norm", keep="last")
    df = df[df["title"].str.len() > 0]
    df = df[df["abstract"].str.len() > 50]
    df = df.drop(columns=["title_norm"])

    cols = ["arxiv_id", "title", "abstract", "authors", "categories",
            "primary_category", "published", "doi", "pdf_url"]
    cols = [c for c in cols if c in df.columns]

    with open(corpus_path, "w", encoding="utf-8") as f:
        for _, row in df[cols].iterrows():
            f.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")

    print(f"Corpus limpo: {len(df)} documentos → {corpus_path}")

    # Estatísticas
    if "published" in df.columns:
        df["year"] = df["published"].str[:4]
        print("\nDistribuição por ano:")
        print(df["year"].value_counts().sort_index().to_string())
    print("\nTop categorias primárias:")
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

    for i, q in enumerate(QUERIES):
        if len(seen) >= TARGET_SIZE:
            print(f"\nMeta de {TARGET_SIZE} atingida!")
            break

        print(f"[{i+1}/{len(QUERIES)}] \"{q}\"")
        collect_query(q, seen, RAW_PATH, max_pages=3)

        if i < len(QUERIES) - 1 and len(seen) < TARGET_SIZE:
            time.sleep(2)

    if RAW_PATH.exists() and len(seen) > 0:
        print(f"\n--- Deduplicação e limpeza ---")
        deduplicate(RAW_PATH, CORPUS_PATH)
    else:
        print("\nNenhum artigo coletado.")
