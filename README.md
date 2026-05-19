# Trabalho Prático — Inteligência Artificial (FACOM/UFMS, 2026/1)

**Aluno:** Luiz Quirino  
**Nível:** Mestrado  
**Tema da coleção:** IA aplicada a compras públicas e licitações — recuperação de artigos científicos sobre NLP para documentos governamentais, análise de editais e automação de procurement.

## Estrutura do repositório

```
.
├── README.md
├── requirements.txt
├── data/
│   ├── arxiv_raw.jsonl       <- artigos brutos da API (não versionar se > 50MB)
│   └── corpus.jsonl          <- coleção final pré-processada
├── notebooks/
│   ├── 01_coleta_arxiv.ipynb
│   ├── 02_baseline_bm25.ipynb
│   ├── 03_retrieval_knn.ipynb
│   ├── 04_modulo_aprofundamento.ipynb  <- M5: RRF híbrido
│   └── runs/
│       ├── bm25.trec
│       ├── knn.trec
│       └── hybrid_rrf.trec
├── src/
│   ├── __init__.py
│   ├── preprocessing.py
│   ├── retrievers.py
│   └── utils.py
├── eval/
│   ├── queries.tsv
│   ├── qrels.tsv
│   └── evaluate.py
└── relatorio/
    ├── relatorio.tex
    └── relatorio.pdf
```

## Reprodução

```bash
# 1. Criar ambiente e instalar dependências
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Coletar dados (ajuste palavras-chave em notebooks/01_coleta_arxiv.ipynb)
jupyter notebook notebooks/01_coleta_arxiv.ipynb

# 3. Baseline BM25
jupyter notebook notebooks/02_baseline_bm25.ipynb

# 4. KNN / TF-IDF
jupyter notebook notebooks/03_retrieval_knn.ipynb

# 5. Módulo M5 — Ranking Híbrido RRF
jupyter notebook notebooks/04_modulo_aprofundamento.ipynb

# 6. Avaliação
python eval/evaluate.py \
    --qrels eval/qrels.tsv \
    --runs notebooks/runs/bm25.trec notebooks/runs/knn.trec notebooks/runs/hybrid_rrf.trec \
    --k 10
```

## Demo rápido

```bash
python -c "
from src.retrievers import search_bm25, load_index
idx = load_index('data/corpus.jsonl')
results = search_bm25('public procurement NLP document classification', idx, k=10)
for rank, (doc_id, score) in enumerate(results, 1):
    print(f'{rank}. [{score:.4f}] {doc_id}')
"
```

## Decisões de projeto

- **Tema/escopo:** IA aplicada a compras públicas e licitações (cs.CL + cs.IR + cs.AI, 2018–2026)
- **Fonte:** API pública do ArXiv
- **Tamanho final da coleção:** _(preencher após coleta)_
- **Pré-processamento:** lower-casing, remoção de pontuação, stopwords NLTK en, Porter stemmer
- **BM25:** rank_bm25, k1=1.5, b=0.75
- **KNN/denso:** TF-IDF (scikit-learn) + cosine similarity, K=100
- **Módulo M5:** Reciprocal Rank Fusion (k=60) combinando BM25 + KNN

## Uso de assistentes de IA generativa

Claude (Anthropic) foi utilizado para: estruturação do plano de trabalho, sugestão de arquitetura de código, apoio à escrita de seções do relatório e revisão de código. Todo código foi revisado, adaptado e testado pelo autor. Decisões de projeto, anotação de qrels e análise dos resultados são inteiramente do autor.

## Vídeo de apresentação

URL: _(preencher antes da entrega)_
