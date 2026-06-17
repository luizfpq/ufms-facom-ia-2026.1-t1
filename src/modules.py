"""Modulos de aprofundamento M1-M4 (o M5/RRF esta em retrievers.py).

M1 Re-ranking supervisionado     -> run m1
M3 Expansao de consulta (regras) -> run m3
M2 Agrupamento de resultados     -> analise (silhueta + facetas)
M4 Otimizacao de hiperparametros -> melhor config + tabela
"""
from collections import Counter, defaultdict

import numpy as np
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import silhouette_score
from rank_bm25 import BM25Okapi

try:
    from src.preprocessing import preprocess, doc_text
    from src.retrievers import (search_bm25, search_knn, search_dense,
                                build_bm25_index)
except ModuleNotFoundError:
    from preprocessing import preprocess, doc_text
    from retrievers import (search_bm25, search_knn, search_dense,
                            build_bm25_index)


# ===========================================================================
# M1 — Re-ranking por classificacao supervisionada (Regressao Logistica)
# ===========================================================================

def _features(qtokens, doc_idx, bm25_index, bm25_scores, tfidf_mat, dense_mat,
              qvec_tfidf, qvec_dense, corpus):
    """Vetor de features do par (consulta, documento)."""
    doc = corpus[doc_idx]
    dtokens = set(preprocess(doc_text(doc)))
    overlap = len(set(qtokens) & dtokens) / (len(set(qtokens)) or 1)
    tfidf_cos = float(tfidf_mat[doc_idx].multiply(qvec_tfidf).sum())
    dense_cos = float(dense_mat[doc_idx] @ qvec_dense)
    year = doc.get("published", "")[:4]
    try:
        year = (int(year) - 2018) / 8.0
    except ValueError:
        year = 0.0
    return [bm25_scores[doc_idx], tfidf_cos, dense_cos, overlap, year]


def m1_rerank(queries, qrels, corpus, bm25_index, tfidf_vec, tfidf_mat,
              dense_model_emb, top=100):
    """Re-ranqueia o top-100 do BM25 com Regressao Logistica.

    Validacao leave-one-query-out: para cada query, treina nas demais e
    prediz na query retida. Evita treinar e testar na mesma consulta.
    """
    from sklearn.metrics.pairwise import cosine_similarity
    qids = list(queries.keys())
    # candidatos e features por query
    cand = {}
    feats = {}
    labels = {}
    for qid in qids:
        text = queries[qid]
        qtokens = preprocess(text)
        scores = bm25_index.get_scores(qtokens)
        top_idx = np.argsort(scores)[::-1][:top]
        qv_tfidf = tfidf_vec.transform([" ".join(qtokens)])
        from retrievers import _get_dense_model  # noqa
        qv_dense = _get_dense_model().encode([text], normalize_embeddings=True)[0]
        cand[qid] = list(top_idx)
        feats[qid] = np.array([
            _features(qtokens, i, bm25_index, scores, tfidf_mat, dense_model_emb,
                      qv_tfidf, qv_dense, corpus) for i in top_idx])
        labels[qid] = np.array([
            1 if qrels.get(qid, {}).get(corpus[i]["arxiv_id"], 0) > 0 else 0
            for i in top_idx])

    run = defaultdict(list)
    for held in qids:
        X_tr = np.vstack([feats[q] for q in qids if q != held])
        y_tr = np.concatenate([labels[q] for q in qids if q != held])
        if y_tr.sum() == 0 or y_tr.sum() == len(y_tr):
            order = np.argsort(feats[held][:, 0])[::-1]  # fallback: BM25
        else:
            clf = LogisticRegression(max_iter=1000, class_weight="balanced")
            clf.fit(X_tr, y_tr)
            proba = clf.predict_proba(feats[held])[:, 1]
            order = np.argsort(proba)[::-1]
        for rank, pos in enumerate(order):
            doc_idx = cand[held][pos]
            run[held].append((corpus[doc_idx]["arxiv_id"],
                              float(len(order) - rank)))
    return run


# ===========================================================================
# M3 — Expansao de consulta por regras de associacao
# ===========================================================================

def mine_rules_for_query(qtokens, corpus, inverted, df, n_docs,
                         min_support=0.01, min_conf=0.3, max_terms=3,
                         max_df_ratio=0.25, min_lift=1.5):
    """Para cada termo da consulta, encontra consequentes {A}=>{B} com
    suporte, confianca e lift acima do limiar. Exclui termos muito
    frequentes (genericos) via max_df_ratio. Retorna termos de expansao."""
    expansions = Counter()
    qset = set(qtokens)
    for a in qset:
        docs_a = inverted.get(a)
        if not docs_a or len(docs_a) < 3:
            continue
        co = Counter()
        for d in docs_a:
            for b in corpus_terms_cache[d]:
                if b != a and b not in qset:
                    co[b] += 1
        for b, cab in co.items():
            pb = df.get(b, 0) / n_docs
            if pb == 0 or pb > max_df_ratio:
                continue  # termo generico/raro demais
            support = cab / n_docs
            conf = cab / len(docs_a)
            lift = conf / pb
            if support >= min_support and conf >= min_conf and lift >= min_lift:
                expansions[b] += lift
    return [t for t, _ in expansions.most_common(max_terms)]


corpus_terms_cache = {}


def m3_expand(queries, corpus, bm25_index, top=100,
              min_support=0.01, min_conf=0.3, max_terms=3):
    """Expande cada consulta com termos minerados e re-roda BM25."""
    n_docs = len(corpus)
    inverted = defaultdict(set)
    global corpus_terms_cache
    corpus_terms_cache = {}
    for i, doc in enumerate(corpus):
        terms = set(preprocess(doc_text(doc)))
        corpus_terms_cache[i] = terms
        for t in terms:
            inverted[t].add(i)
    df = {t: len(ds) for t, ds in inverted.items()}

    run = defaultdict(list)
    chosen = {}
    for qid, text in queries.items():
        qtokens = preprocess(text)
        exp = mine_rules_for_query(qtokens, corpus, inverted, df, n_docs,
                                   min_support, min_conf, max_terms)
        chosen[qid] = exp
        new_q = " ".join(qtokens + exp)
        for did, sc in search_bm25(new_q, bm25_index, corpus, k=top):
            run[qid].append((did, sc))
    return run, chosen


# ===========================================================================
# M2 — Agrupamento dos resultados (K-means + silhueta + facetas)
# ===========================================================================

def m2_cluster(query, corpus, dense_emb, bm25_index, top=30, k_range=(2, 6)):
    """Agrupa o top-k de uma consulta e descreve facetas por termos."""
    res = search_bm25(query, bm25_index, corpus, k=top)
    id2idx = {d["arxiv_id"]: i for i, d in enumerate(corpus)}
    idxs = [id2idx[d] for d, _ in res if d in id2idx]
    X = dense_emb[idxs]
    best = None
    for k in range(k_range[0], k_range[1] + 1):
        if k >= len(idxs):
            break
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        sil = silhouette_score(X, km.labels_)
        if best is None or sil > best["sil"]:
            best = {"k": k, "sil": sil, "labels": km.labels_, "idxs": idxs}
    # facetas: termos mais frequentes por cluster
    facets = {}
    for c in set(best["labels"]):
        terms = Counter()
        for j, lab in zip(best["idxs"], best["labels"]):
            if lab == c:
                terms.update(preprocess(doc_text(corpus[j])))
        facets[int(c)] = [t for t, _ in terms.most_common(6)]
    return best["k"], best["sil"], facets


# ===========================================================================
# M4 — Otimizacao de hiperparametros do BM25 (grid search)
# ===========================================================================

def m4_grid_search(queries, qrels, corpus, eval_fn, k1_grid, b_grid, top=100):
    """Grid search de (k1, b) do BM25 maximizando MAP no conjunto de avaliacao."""
    tokens = [preprocess(doc_text(d)) for d in corpus]
    results = []
    best = None
    for k1 in k1_grid:
        for b in b_grid:
            index = BM25Okapi(tokens, k1=k1, b=b)
            run = defaultdict(list)
            for qid, text in queries.items():
                qt = preprocess(text)
                sc = index.get_scores(qt)
                top_idx = np.argsort(sc)[::-1][:top]
                for i in top_idx:
                    run[qid].append((corpus[i]["arxiv_id"], float(sc[i])))
            mapv = eval_fn(run)
            results.append((k1, b, mapv))
            if best is None or mapv > best[2]:
                best = (k1, b, mapv)
    return results, best
