# Trabalho Prático — Inteligência Artificial (FACOM/UFMS, 2026/1)

**Aluno:** Luiz Fernando Postingel Quirino  
**Matrícula:** 2026...  
**Nível:** Mestrado  
**Tema da coleção:** IA aplicada a compras públicas e licitações  

## Estrutura do repositório

```
.
├── README.md                ← este arquivo
├── Makefile                 ← atalhos: make runs / eval / demo / relatorio / help
├── requirements.txt         ← dependências Python
├── LINKS.txt                ← URLs do vídeo e repositório
├── Dockerfile               ← imagem para execução isolada
├── docker/                  ← entrypoint + plano de deploy (acesso do docente)
├── relatorio.pdf            ← relatório final compilado (ENTREGA)
├── relatorio-fonte/         ← fontes LaTeX (.tex, .bib, sbc-template.sty, sbc.bst, Makefile)
├── data/
│   ├── openalex_raw.jsonl   ← coleta bruta OpenAlex (2.099 registros)
│   ├── bdtd_raw.jsonl       ← coleta bruta BDTD (PT)
│   └── corpus.jsonl         ← coleção limpa (3.064 documentos, EN+PT)
├── notebooks/
│   ├── 01_coleta_arxiv.ipynb
│   ├── 02_baseline_bm25.ipynb
│   ├── 03_retrieval_knn.ipynb
│   ├── 04_modulo_aprofundamento.ipynb
│   └── runs/                ← arquivos .trec gerados
│       ├── bm25.trec
│       ├── knn.trec
│       └── rrf.trec
├── src/
│   ├── preprocessing.py     ← tokenização, stopwords, stemming
│   ├── retrievers.py        ← BM25, KNN/TF-IDF, RRF
│   ├── utils.py             ← I/O de corpus, queries, runs
│   ├── run_pipeline.py      ← gera todas as runs de uma vez
│   ├── demo.py              ← demo interativa (query → ranking)
│   ├── gen_pool.py          ← gera pool para anotação de qrels
│   ├── coleta_openalex.py   ← coleta via OpenAlex API
│   ├── coleta_bdtd.py       ← coleta via BDTD (teses/dissertações PT)
│   └── coleta_arxiv.py      ← coleta via ArXiv API (backup)
└── eval/
    ├── queries.tsv          ← 15 queries do domínio
    ├── qrels.tsv            ← 232 julgamentos de relevância
    ├── evaluate.py          ← script de avaliação (P@k, MAP, nDCG)
    └── pool_anotacao.md     ← docs do pool com título+abstract
```

## Reprodução

```bash
# 1. Criar ambiente virtual e instalar dependências
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Coleta (já executada — corpus.jsonl incluso no repositório)
# Para re-executar:
python src/coleta_openalex.py

# 3. Gerar runs (BM25 + KNN + RRF)
python src/run_pipeline.py

# 4. Avaliação
python eval/evaluate.py --qrels eval/qrels.tsv \
    --runs notebooks/runs/bm25.trec notebooks/runs/knn.trec notebooks/runs/rrf.trec \
    --k 10
```

### Atalhos (Makefile)

```bash
make help        # lista os alvos
make runs        # gera os 3 runs TREC
make eval        # gera os runs e avalia (P@10, R@10, MAP, nDCG@10)
make demo QUERY="public procurement NLP"
make relatorio   # compila relatorio-fonte/ → relatorio.pdf na raiz
```

### Execução isolada (Docker)

```bash
docker build -t ia-t1 .
docker run --rm -it ia-t1          # demo interativa
docker run --rm ia-t1 make eval    # avaliação completa
```

## Decisões de projeto

- **Tema:** IA aplicada a compras públicas, licitações e textos jurídico-administrativos
- **Fonte da coleção:** OpenAlex API (EN+PT) + BDTD (teses/dissertações PT); ArXiv como backup (estava com rate limit)
- **Idiomas:** Inglês (2.093 docs) + Português (971 docs) — corpus bilíngue
- **Janela temporal:** 2018–2026
- **Tamanho final:** 3.064 documentos
- **Pré-processamento:** lowercase, regex tokenization, stopwords bilíngues (NLTK EN+PT + custom), Porter stemmer (EN) / RSLP stemmer (PT), detecção automática de idioma
- **BM25:** rank_bm25 (Okapi), k1=1.5, b=0.75
- **KNN/denso:** TF-IDF (scikit-learn) + cosine similarity
- **Módulo M5:** Reciprocal Rank Fusion (k=60) combinando BM25 + KNN

## Resultados

Corpus bilíngue: 3.064 documentos (2.093 EN + 971 PT, fontes: OpenAlex + BDTD)

| Sistema | P@10 | R@10 | MAP | nDCG@10 |
|---------|------|------|-----|---------|
| BM25 | 0.707 | 0.738 | 0.823 | 0.853 |
| KNN/TF-IDF | 0.700 | 0.724 | 0.774 | 0.745 |
| RRF Híbrido | **0.727** | **0.762** | **0.867** | 0.845 |

## Uso de assistentes de IA generativa

Conforme Resolução nº 455-COUN/UFMS (BO-UFMS ID 581705; Art. 6º, V; Art. 12, Parágrafo único):

- **Gemini (Google, Deep Research):** pesquisa exploratória de fontes acadêmicas em português. O domínio específico (compras públicas brasileiras, Lei 14.133/2021) exigiu busca por bases complementares ao ArXiv. Resultados avaliados criticamente e verificados manualmente.
- **Claude/Kiro (Anthropic):** apoio na implementação de scripts de coleta e pipeline, sugestões de hiperparâmetros e estruturação do relatório.

As decisões de projeto, anotação de qrels, análise dos resultados e redação argumentativa são integralmente do autor. Todo código gerado com auxílio de IA foi revisado, testado e adaptado.

## Vídeo de apresentação

Ver `LINKS.txt`.
