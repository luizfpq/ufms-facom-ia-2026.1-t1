"""Sugestao de rotulos para o pool novo, ancorada nos qrels ja anotados.

Treina um classificador (Regressao Logistica multinomial) sobre os pares
(consulta, documento) JA julgados, usando features de similaridade, e prediz
um rotulo sugerido (0/1/2) para os pares novos do pool. As sugestoes sao para
REVISAO MANUAL do autor; nao substituem o julgamento humano.
"""
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, "src")
sys.path.insert(0, "eval")

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import accuracy_score

from utils import load_corpus, load_queries
from preprocessing import preprocess, doc_text
from retrievers import (build_bm25_index, build_tfidf_index,
                        build_dense_index, _get_dense_model)
import evaluate as ev

ROOT = Path(".")
corpus = load_corpus("data/corpus.jsonl")
queries = load_queries("eval/queries.tsv")
qrels = ev.read_qrels(Path("eval/qrels.tsv"))
id2idx = {d["arxiv_id"]: i for i, d in enumerate(corpus)}
id2doc = {d["arxiv_id"]: d for d in corpus}

bm25 = build_bm25_index(corpus)
tfidf_vec, tfidf_mat = build_tfidf_index(corpus)
dense = build_dense_index(corpus, cache_path="data/dense_emb.npy")
model = _get_dense_model()

# Pre-computa por query: scores bm25, vetor tfidf da query, vetor denso da query
qcache = {}
for q, text in queries.items():
    qt = preprocess(text)
    qcache[q] = {
        "bm25": bm25.get_scores(qt),
        "tfidf": tfidf_vec.transform([" ".join(qt)]),
        "dense": np.asarray(model.encode([text], normalize_embeddings=True)[0], dtype="float32"),
        "tokens": set(qt),
    }


def feats(q, d):
    i = id2idx[d]
    c = qcache[q]
    bm = float(c["bm25"][i])
    tf = float(tfidf_mat[i].multiply(c["tfidf"]).sum())
    de = float(dense[i] @ c["dense"])
    dt = set(preprocess(doc_text(corpus[i])))
    ov = len(c["tokens"] & dt) / (len(c["tokens"]) or 1)
    return [bm, tf, de, ov]


# --- treino: pares julgados ---
Xtr, ytr = [], []
for q in qrels:
    for d, rel in qrels[q].items():
        if d in id2idx:
            Xtr.append(feats(q, d)); ytr.append(int(rel))
Xtr = np.array(Xtr); ytr = np.array(ytr)

clf = LogisticRegression(max_iter=2000, class_weight="balanced")
cvp = cross_val_predict(clf, Xtr, ytr, cv=5)
print(f"Treino: {len(ytr)} pares julgados. Acordo (5-fold) com anotacoes manuais: {accuracy_score(ytr, cvp):.1%}")
clf.fit(Xtr, ytr)

# --- pool atual e pares novos ---
systems = ["bm25", "knn", "dense", "rrf", "m1", "m3"]
pool = defaultdict(dict)
for s in systems:
    run = ev.read_run(Path(f"notebooks/runs/{s}.trec"))
    for q in run:
        for rank, score, d in run[q][:10]:
            pool[q].setdefault(d, set()).add(s)
judged = set((q, d) for q in qrels for d in qrels[q])
new = [(q, d, sys) for q in pool for d, sys in pool[q].items() if (q, d) not in judged and d in id2idx]

# --- sugere e grava arquivo de revisao ---
out = ROOT / "eval" / "pool_revisao.tsv"
rows = []
for q, d, syss in sorted(new):
    f = feats(q, d)
    sug = int(clf.predict([f])[0])
    rows.append((q, d, "+".join(sorted(syss)), id2doc[d].get("source", "?"),
                 f[2], f[3], sug, id2doc[d].get("title", "")[:80],
                 (id2doc[d].get("abstract", "") or "")[:200].replace("\t", " ").replace("\n", " ")))
with open(out, "w", encoding="utf-8") as fh:
    fh.write("qid\tdoc_id\tsistemas\tfonte\tsim_densa\toverlap\trel_sugerido\trel_revisado\ttitulo\tabstract\n")
    for r in rows:
        fh.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\t{r[4]:.3f}\t{r[5]:.2f}\t{r[6]}\t\t{r[7]}\t{r[8]}\n")

from collections import Counter
print(f"Pares novos sugeridos: {len(rows)} -> {out}")
print("Distribuicao das sugestoes:", dict(Counter(r[6] for r in rows)))
