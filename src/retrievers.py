from collections import defaultdict
import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from src.preprocessing import preprocess, preprocess_str, doc_text
except ModuleNotFoundError:
    from preprocessing import preprocess, preprocess_str, doc_text


# ---------------------------------------------------------------------------
# BM25
# ---------------------------------------------------------------------------

def build_bm25_index(corpus: list[dict], k1: float = 1.5, b: float = 0.75):
    tokens = [preprocess(doc_text(doc)) for doc in corpus]
    return BM25Okapi(tokens, k1=k1, b=b)


def search_bm25(query: str, index: BM25Okapi, corpus: list[dict],
                k: int = 100) -> list[tuple[str, float]]:
    q_tokens = preprocess(query)
    scores = index.get_scores(q_tokens)
    top_k = np.argsort(scores)[::-1][:k]
    return [(corpus[i]['arxiv_id'], float(scores[i])) for i in top_k]


# ---------------------------------------------------------------------------
# KNN / TF-IDF
# ---------------------------------------------------------------------------

def build_tfidf_index(corpus: list[dict]):
    texts = [preprocess_str(doc_text(doc)) for doc in corpus]
    vectorizer = TfidfVectorizer(min_df=2, max_df=0.95)
    matrix = vectorizer.fit_transform(texts)
    return vectorizer, matrix


def search_knn(query: str, vectorizer: TfidfVectorizer, matrix,
               corpus: list[dict], k: int = 100) -> list[tuple[str, float]]:
    q_vec = vectorizer.transform([preprocess_str(query)])
    sims = cosine_similarity(q_vec, matrix).flatten()
    top_k = np.argsort(sims)[::-1][:k]
    return [(corpus[i]['arxiv_id'], float(sims[i])) for i in top_k]


# ---------------------------------------------------------------------------
# M5 — Reciprocal Rank Fusion
# ---------------------------------------------------------------------------

def reciprocal_rank_fusion(runs: list[list[tuple[str, float]]],
                           k: int = 60) -> list[tuple[str, float]]:
    """
    Combina múltiplos rankings via RRF.
    k=60 é o padrão da literatura (Cormack et al., 2009).
    """
    scores: dict[str, float] = defaultdict(float)
    for run in runs:
        for rank, (doc_id, _) in enumerate(run, start=1):
            scores[doc_id] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
