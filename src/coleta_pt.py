"""Coleta complementar em português — OpenAlex API.

Adiciona artigos em PT ao corpus existente (bilíngue).

Uso:
    python src/coleta_pt.py
"""

import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

BASE_URL = "https://api.openalex.org/works"
MAILTO = "luiz.quirino@ufms.br"

QUERIES_PT = [
    "processamento linguagem natural documentos juridicos",
    "tribunal contas inteligência artificial",
    "administração pública dados mineração",
    "lei licitações tecnologia informação",
    "direito administrativo machine learning",
    "contratos públicos análise automatizada",
    "compras públicas governo digital",
    "compliance governamental auditoria",
    "NLP textos legais português",
    "classificação documentos administrativos",
]

YEAR_FROM = 2018
TARGET_SIZE = 500
PER_PAGE = 100

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_PATH = OUTPUT_DIR / "openalex_pt_raw.jsonl"


def reconstruct_abstract(inv_index):
    if not inv_index:
        return ""
    word_positions = []
    for word, positions in inv_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort()
    return " ".join(w for _, w in word_positions)


def already_collected_ids(path):
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


def fetch_page(query, page=1):
    params = urllib.parse.urlencode({
        "search": query,
        "filter": f"from_publication_date:{YEAR_FROM}-01-01,language:pt",
        "per_page": PER_PAGE,
        "page": page,
        "select": "id,title,publication_date,authorships,topics,primary_topic,"
                  "abstract_inverted_index,doi,open_access,ids,language",
        "mailto": MAILTO,
    })
    url = f"{BASE_URL}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "UFMS-FACOM-IA/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def normalize_work(work):
    ids = work.get("ids") or {}
    authors = [a["author"]["display_name"]
               for a in (work.get("authorships") or [])
               if a.get("author", {}).get("display_name")]
    abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
    topics = work.get("topics") or []
    categories = [t.get("display_name", "") for t in topics[:5]]
    primary = work.get("primary_topic", {}).get("display_name", "") if work.get("primary_topic") else ""
    openalex_id = (work.get("id") or "").replace("https://openalex.org/", "")

    return {
        "openalex_id": openalex_id,
        "arxiv_id": openalex_id,
        "title": (work.get("title") or "").strip(),
        "abstract": abstract,
        "authors": authors,
        "categories": categories,
        "primary_category": primary,
        "published": work.get("publication_date", ""),
        "doi": work.get("doi"),
        "pdf_url": (work.get("open_access") or {}).get("oa_url"),
        "language": "pt",
    }


def main():
    seen = already_collected_ids(RAW_PATH)
    print(f"Já coletados (PT): {len(seen)}")
    print(f"Meta: {TARGET_SIZE}\n")

    for i, q in enumerate(QUERIES_PT):
        if len(seen) >= TARGET_SIZE:
            print(f"\nMeta atingida!")
            break

        print(f"[{i+1}/{len(QUERIES_PT)}] \"{q}\"")
        for page in range(1, 3):  # max 2 páginas por query
            try:
                data = fetch_page(q, page)
            except Exception as e:
                print(f"  [erro] {e}")
                break

            results = data.get("results", [])
            if not results:
                break

            added = 0
            with open(RAW_PATH, "a", encoding="utf-8") as f:
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

            print(f"  p{page}: +{added} (global={len(seen)})")
            time.sleep(1)

        if i < len(QUERIES_PT) - 1:
            time.sleep(2)

    print(f"\nTotal PT coletado: {len(seen)}")


if __name__ == "__main__":
    main()
