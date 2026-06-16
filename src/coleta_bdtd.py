"""Coleta de teses/dissertações da BDTD (Ibict).

Complementa o corpus com produção acadêmica brasileira stricto sensu
sobre licitações, compras públicas e NLP jurídico.

Uso:
    python src/coleta_bdtd.py
"""

import json
import time
import urllib.request
import urllib.parse
import ssl
from pathlib import Path

BASE_URL = "https://bdtd.ibict.br/vufind/api/v1/search"

QUERIES = [
    "licitação inteligência artificial",
    "compras públicas machine learning",
    "processamento linguagem natural documentos jurídicos",
    "mineração textos legais",
    "tribunal contas auditoria automatizada",
    "contratação pública tecnologia informação",
    "NLP direito administrativo",
    "classificação textos governo",
    "análise editais automatizada",
    "conformidade documental licitações",
]

TARGET_SIZE = 300
PER_PAGE = 100

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_PATH = OUTPUT_DIR / "bdtd_raw.jsonl"

# BDTD tem cert issues, ignorar
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def already_collected_ids(path):
    if not path.exists():
        return set()
    ids = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                ids.add(json.loads(line)["bdtd_id"])
            except Exception:
                continue
    return ids


def fetch_page(query, offset=0, limit=100):
    params = urllib.parse.urlencode({
        "lookfor": query,
        "type": "AllFields",
        "limit": limit,
        "offset": offset,
    })
    url = f"{BASE_URL}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "UFMS-FACOM-IA/1.0"})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        return json.loads(resp.read())


def normalize_record(rec):
    authors_dict = rec.get("authors", {}).get("primary", {})
    authors = list(authors_dict.keys()) if authors_dict else []

    title = (rec.get("title") or "").strip()
    summary = (rec.get("summary") or [""])[0] if isinstance(rec.get("summary"), list) else (rec.get("summary") or "")

    urls = rec.get("urls", [])
    pdf_url = urls[0].get("url") if urls else None

    subjects = rec.get("subjects", [])

    return {
        "bdtd_id": rec.get("id", ""),
        "arxiv_id": f"BDTD_{rec.get('id', '')}",
        "title": title,
        "abstract": summary.strip() if summary else title,
        "authors": authors,
        "categories": subjects,
        "primary_category": subjects[0] if subjects else "",
        "published": "",
        "doi": None,
        "pdf_url": pdf_url,
        "language": "pt",
        "source": "BDTD",
    }


def main():
    seen = already_collected_ids(RAW_PATH)
    print(f"Já coletados (BDTD): {len(seen)}")
    print(f"Meta: {TARGET_SIZE}\n")

    for i, q in enumerate(QUERIES):
        if len(seen) >= TARGET_SIZE:
            print(f"\nMeta atingida!")
            break

        print(f"[{i+1}/{len(QUERIES)}] \"{q}\"")
        try:
            data = fetch_page(q, 0, PER_PAGE)
        except Exception as e:
            print(f"  [erro] {e}")
            continue

        records = data.get("records", [])
        added = 0
        with open(RAW_PATH, "a", encoding="utf-8") as f:
            for rec in records:
                norm = normalize_record(rec)
                if norm["bdtd_id"] in seen:
                    continue
                if len(norm["abstract"]) < 20:
                    continue
                f.write(json.dumps(norm, ensure_ascii=False) + "\n")
                f.flush()
                seen.add(norm["bdtd_id"])
                added += 1

        print(f"  +{added} (global={len(seen)})")
        time.sleep(3)

    print(f"\nTotal BDTD coletado: {len(seen)}")


if __name__ == "__main__":
    main()
