"""
bib_formatter.py — Gera entradas BibTeX a partir de resultados de busca.
"""
import re
import unicodedata


def slugify(text: str) -> str:
    """Gera uma chave BibTeX a partir de texto."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r'[^\w\s-]', '', text.lower())
    return re.sub(r'[\s-]+', '_', text)[:40]


def format_corpus_results(results: list[dict]) -> list[str]:
    """Formata resultados do corpus acadêmico como entradas BibTeX."""
    entries = []
    for doc in results:
        authors = doc.get("authors", doc.get("author", "Unknown"))
        if isinstance(authors, list):
            authors = " and ".join(authors[:3])
        title = doc.get("title", "Untitled")
        year = doc.get("year", doc.get("publication_year", ""))
        doi = doc.get("doi", "")
        journal = doc.get("journal", doc.get("source", ""))
        abstract = doc.get("abstract", "")

        # Gerar chave
        first_author = re.split(r'[,;&]', str(authors))[0].split()[-1] if authors else "unknown"
        key = f"{slugify(first_author)}{year}"

        entry = f"""@article{{{key},
  author = {{{authors}}},
  title = {{{title}}},
  year = {{{year}}},"""
        if journal:
            entry += f"\n  journal = {{{journal}}},"
        if doi:
            entry += f"\n  doi = {{{doi}}},"
        if abstract:
            entry += f"\n  abstract = {{{abstract[:200]}...}},"
        entry += "\n}"
        entries.append(entry)
    return entries


def format_legislation_results(results) -> list[str]:
    """Formata resultados de legislação como entradas BibTeX @misc."""
    entries = []
    for r in results:
        key = slugify(f"brasil_{r.tipo}_{r.numero}_{r.ano}")
        entry = f"""@misc{{{key},
  author = {{{{BRASIL}}}},
  title = {{{r.tipo} {r.numero}, de {r.ano}. {r.ementa}}},
  year = {{{r.ano}}},
  note = {{Disponível em: \\url{{{r.url}}}}}
}}"""
        entries.append(entry)
    return entries


def write_bib(entries: list[str], output_path: str):
    """Escreve entradas BibTeX em arquivo."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("% Referências sugeridas — gerado automaticamente por reference_finder v2\n")
        f.write(f"% Total: {len(entries)} entradas\n\n")
        f.write("\n\n".join(entries))
        f.write("\n")
