"""
reference_finder.py — Buscador de referências bibliográficas + legislação.
Recebe texto (artigo, abstract, .tex) e retorna referências relevantes.
Reutiliza o core do T1 (BM25, KNN/TF-IDF, RRF).
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from keyphrase_extractor import extract_keyphrases, generate_queries, clean_latex
from legislation_source import search_all as search_legislation_all
from bib_formatter import format_corpus_results, format_legislation_results, write_bib
from utils import load_corpus
from retrievers import build_bm25_index, search_bm25, build_tfidf_index, search_knn, reciprocal_rank_fusion


def search_corpus(queries: list[str], corpus: list[dict], top_k: int = 20) -> list[dict]:
    """Busca no corpus usando BM25+KNN+RRF."""
    # Build indexes (once)
    bm25_idx = build_bm25_index(corpus)
    tfidf_vec, tfidf_mat = build_tfidf_index(corpus)

    # Map arxiv_id → doc for lookup
    id_to_doc = {doc["arxiv_id"]: doc for doc in corpus}
    aggregated = {}

    for query in queries:
        bm25_results = search_bm25(query, bm25_idx, corpus, k=top_k)
        knn_results = search_knn(query, tfidf_vec, tfidf_mat, corpus, k=top_k)
        fused = reciprocal_rank_fusion([bm25_results, knn_results], k=60)

        for doc_id, score in fused[:top_k]:
            if doc_id in aggregated:
                aggregated[doc_id] = max(aggregated[doc_id], score)
            else:
                aggregated[doc_id] = score

    # Rank and return full docs
    ranked = sorted(aggregated.items(), key=lambda x: -x[1])
    results = []
    for doc_id, score in ranked[:top_k]:
        if doc_id in id_to_doc:
            doc = id_to_doc[doc_id].copy()
            doc["_score"] = score
            results.append(doc)
    return results


def find_references(input_path: str, corpus_path: str = "data/corpus.jsonl",
                    top_k: int = 20, output: str = None):
    """Pipeline: extrai keyphrases → busca corpus + legislação → formata .bib"""
    # 1. Carregar input
    text = Path(input_path).read_text(encoding="utf-8")
    text_clean = clean_latex(text) if input_path.endswith(".tex") else text
    print(f"[1/4] Input: {Path(input_path).name} ({len(text_clean)} chars)")

    # 2. Extrair keyphrases
    keyphrases = extract_keyphrases(text_clean, top_n=15)
    queries = generate_queries(keyphrases, max_queries=10)
    print(f"[2/4] Keyphrases extraídas: {len(keyphrases)}")
    for i, kp in enumerate(keyphrases[:5]):
        print(f"       {i+1}. {kp}")

    # 3. Buscar
    print(f"[3/4] Buscando...")
    corpus = load_corpus(corpus_path)
    academic = search_corpus(queries, corpus, top_k=top_k)
    legislation = search_legislation_all(queries, top_n=10)
    print(f"       Corpus acadêmico: {len(academic)} resultados")
    print(f"       Legislação: {len(legislation)} normas")

    # 4. Formatar e salvar
    bib_entries = format_corpus_results(academic) + format_legislation_results(legislation)
    output_path = output or "refs_sugeridas.bib"
    write_bib(bib_entries, output_path)
    print(f"[4/4] → {output_path} ({len(bib_entries)} entradas BibTeX)")

    # Preview top 5
    print(f"\n{'='*60}")
    print("TOP 5 REFERÊNCIAS ACADÊMICAS:")
    for doc in academic[:5]:
        print(f"  • {doc.get('title','?')[:70]}")
        print(f"    {doc.get('authors','?')[:50]} ({doc.get('published','?')[:4]})")
    print(f"\nLEGISLAÇÃO RELEVANTE:")
    for r in legislation[:5]:
        print(f"  • {r.tipo} {r.numero}/{r.ano} — {r.ementa[:60]}")


def main():
    parser = argparse.ArgumentParser(description="Buscador de referências v2")
    parser.add_argument("--input", "-i", required=True, help="Arquivo de entrada (.tex, .md, .txt)")
    parser.add_argument("--corpus", default="data/corpus.jsonl", help="Corpus JSONL")
    parser.add_argument("--top", type=int, default=20, help="Máx referências acadêmicas")
    parser.add_argument("--output", "-o", default=None, help="Arquivo .bib de saída")
    args = parser.parse_args()
    find_references(args.input, args.corpus, args.top, args.output)


if __name__ == "__main__":
    main()
