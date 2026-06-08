"""
keyphrase_extractor.py — Extrai conceitos-chave de um texto para gerar queries de busca.
Usa YAKE (unsupervised keyword extraction) + heurísticas para textos acadêmicos.
"""
import re
import yake


def clean_latex(text: str) -> str:
    """Remove comandos LaTeX, mantendo o texto."""
    text = re.sub(r'\\(begin|end)\{[^}]*\}', '', text)
    text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    text = re.sub(r'[{}\\%$~^_]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_keyphrases(text: str, language: str = "pt", top_n: int = 15, max_ngram: int = 3) -> list[str]:
    """Extrai keyphrases usando YAKE."""
    text = clean_latex(text)
    kw_extractor = yake.KeywordExtractor(
        lan=language, n=max_ngram, top=top_n,
        dedupLim=0.7, dedupFunc='seqm', windowsSize=1
    )
    keywords = kw_extractor.extract_keywords(text)
    return [kw for kw, score in keywords]


def generate_queries(keyphrases: list[str], max_queries: int = 10) -> list[str]:
    """Gera queries de busca a partir de keyphrases (combina singles e pares)."""
    queries = []
    # Keyphrases individuais (as mais relevantes)
    for kp in keyphrases[:max_queries]:
        queries.append(kp)
    # Combinações de pares para queries mais específicas
    for i in range(min(3, len(keyphrases))):
        for j in range(i + 1, min(5, len(keyphrases))):
            if len(queries) >= max_queries:
                break
            queries.append(f"{keyphrases[i]} {keyphrases[j]}")
    return queries[:max_queries]


if __name__ == "__main__":
    sample = """
    Este artigo apresenta uma análise exploratória das práticas de contratação de 
    serviços de computação em nuvem pelas autarquias federais vinculadas ao 
    Ministério da Educação. Utilizando dados da API do Portal Nacional de 
    Contratações Públicas (PNCP), identificamos padrões de contratação, distribuição 
    por modalidade e aderência à Lei nº 14.133/2021.
    """
    kps = extract_keyphrases(sample)
    print("Keyphrases:", kps)
    print("Queries:", generate_queries(kps))
