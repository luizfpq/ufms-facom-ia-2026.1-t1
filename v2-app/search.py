"""search.py — BM25 + KNN/TF-IDF + RRF search over corpus + legislation."""
import json, re
from pathlib import Path
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)

from nltk.corpus import stopwords

STOP_EN = set(stopwords.words("english"))
STOP_PT = set(stopwords.words("portuguese"))
STOPWORDS = STOP_EN | STOP_PT

# --- Corpus loading (cached) ---
_corpus_cache = {}


def load_corpus(path: str) -> list[dict]:
    if path in _corpus_cache:
        return _corpus_cache[path]
    docs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                docs.append(json.loads(line))
    _corpus_cache[path] = docs
    return docs


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r'\w+', text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]


def get_doc_text(doc: dict) -> str:
    return f"{doc.get('title', '')} {doc.get('abstract', '')}"


# --- BM25 ---
_bm25_cache = {}


def get_bm25(corpus_path: str):
    if corpus_path in _bm25_cache:
        return _bm25_cache[corpus_path]
    corpus = load_corpus(corpus_path)
    tokenized = [tokenize(get_doc_text(d)) for d in corpus]
    bm25 = BM25Okapi(tokenized)
    _bm25_cache[corpus_path] = bm25
    return bm25


# --- TF-IDF ---
_tfidf_cache = {}


def get_tfidf(corpus_path: str):
    if corpus_path in _tfidf_cache:
        return _tfidf_cache[corpus_path]
    corpus = load_corpus(corpus_path)
    texts = [get_doc_text(d) for d in corpus]
    vec = TfidfVectorizer(max_features=50000, stop_words=list(STOPWORDS))
    mat = vec.fit_transform(texts)
    _tfidf_cache[corpus_path] = (vec, mat)
    return vec, mat


# --- RRF ---
def reciprocal_rank_fusion(rankings: list[list[int]], k: int = 60) -> list[tuple[int, float]]:
    scores = {}
    for ranking in rankings:
        for rank, idx in enumerate(ranking):
            scores[idx] = scores.get(idx, 0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: -x[1])


# --- Main search ---
def search_corpus(queries: list[str], corpus_path: str, top_k: int = 15) -> list[dict]:
    corpus = load_corpus(corpus_path)
    bm25 = get_bm25(corpus_path)
    vec, mat = get_tfidf(corpus_path)

    aggregated = {}
    for query in queries:
        # BM25
        tokens = tokenize(query)
        if not tokens:
            continue
        bm25_scores = bm25.get_scores(tokens)
        bm25_top = sorted(range(len(bm25_scores)), key=lambda i: -bm25_scores[i])[:top_k]

        # KNN/TF-IDF
        q_vec = vec.transform([query])
        sims = cosine_similarity(q_vec, mat).flatten()
        knn_top = sorted(range(len(sims)), key=lambda i: -sims[i])[:top_k]

        # RRF
        fused = reciprocal_rank_fusion([bm25_top, knn_top])
        for idx, score in fused[:top_k]:
            s = float(score) if score == score else 0.0
            if idx in aggregated:
                aggregated[idx] = max(aggregated[idx], s)
            else:
                aggregated[idx] = s

    ranked = sorted(aggregated.items(), key=lambda x: -x[1])
    results = []
    for idx, score in ranked[:top_k]:
        doc = corpus[idx].copy()
        doc["_score"] = float(score) if score == score else 0.0
        results.append(doc)
    return results


# --- Legislation ---
LEGISLATION_DB = [
    {"tipo": "Lei", "numero": "14.133", "ano": 2021,
     "ementa": "Lei de Licitações e Contratos Administrativos",
     "url": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/L14133.htm",
     "tags": ["licitação", "contrato", "contratação", "administração pública", "pregão", "dispensa"]},
    {"tipo": "Decreto", "numero": "10.947", "ano": 2022,
     "ementa": "Regulamenta o plano de contratações anual (Lei 14.133/2021)",
     "url": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2022/decreto/D10947.htm",
     "tags": ["contratação", "planejamento", "TIC", "plano de contratações"]},
    {"tipo": "Portaria", "numero": "SGD/MGI nº 5.950", "ano": 2023,
     "ementa": "Contratação de serviços de computação em nuvem",
     "url": "https://www.gov.br/governodigital/pt-br/contratacoes/portaria-sgd-mgi-no-5950",
     "tags": ["nuvem", "cloud", "IaaS", "PaaS", "SaaS", "computação em nuvem"]},
    {"tipo": "IN", "numero": "SGD/ME nº 94", "ano": 2022,
     "ementa": "Contratação de soluções de TIC (SISP)",
     "url": "https://www.gov.br/governodigital/pt-br/contratacoes",
     "tags": ["TIC", "SISP", "contratação", "planejamento", "nuvem"]},
    {"tipo": "Lei", "numero": "13.709", "ano": 2018,
     "ementa": "Lei Geral de Proteção de Dados Pessoais (LGPD)",
     "url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm",
     "tags": ["dados", "proteção", "privacidade", "LGPD"]},
    {"tipo": "Decreto", "numero": "10.332", "ano": 2020,
     "ementa": "Estratégia de Governo Digital 2020-2022",
     "url": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/decreto/D10332.htm",
     "tags": ["governo digital", "transformação digital", "nuvem", "cloud"]},
    {"tipo": "Acórdão TCU", "numero": "1.503/2020", "ano": 2020,
     "ementa": "Diretrizes sobre contratações de computação em nuvem no setor público",
     "url": "https://portal.tcu.gov.br/",
     "tags": ["nuvem", "TCU", "contratação", "auditoria", "cloud"]},
]


def search_legislation_all(queries: list[str], top_n: int = 8) -> list[dict]:
    seen = set()
    results = []
    for q in queries:
        q_lower = q.lower()
        q_terms = set(re.findall(r'\w+', q_lower))
        for norma in LEGISLATION_DB:
            key = f"{norma['tipo']}-{norma['numero']}"
            if key in seen:
                continue
            score = 0
            for tag in norma["tags"]:
                tag_terms = set(re.findall(r'\w+', tag.lower()))
                if tag_terms & q_terms:
                    score += 2
            ementa_terms = set(re.findall(r'\w+', norma["ementa"].lower()))
            score += len(ementa_terms & q_terms)
            if score > 0:
                seen.add(key)
                results.append({**norma, "relevance_score": score})
    results.sort(key=lambda r: -r["relevance_score"])
    return results[:top_n]
