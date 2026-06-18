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
│   └── corpus.jsonl         ← coleção limpa (3.106 docs: OpenAlex+BDTD+arXiv)
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
    ├── qrels.tsv            ← 443 julgamentos de relevância (15 queries)
    ├── evaluate.py          ← script de avaliação (P@k, MAP, nDCG)
    └── pool_anotacao.md     ← docs do pool com título+abstract
```

## Reprodução

> **Ambiente testado:** Intel Core i7-12650H (16 threads), Debian 13, Python 3.13, execução em CPU (sem GPU). A codificação dos embeddings dos 3.106 documentos leva ~3,6 min; o restante roda em segundos.


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

> A demo mostra, abaixo de cada resultado, o link de acesso do documento (DOI
> quando existe; senão PDF, arXiv ou OpenAlex). Antes o resultado trazia só o
> texto indexado (título + resumo), o que dificultava conferir cada item. Com o
> link e os dados reais de acesso, dá para abrir a fonte e verificar na hora.

### Execução isolada (Docker)

```bash
docker build -t ia-t1 .
docker run --rm -it ia-t1          # demo interativa
docker run --rm ia-t1 make eval    # avaliação completa
```

## Decisões de projeto

- **Tema:** IA aplicada a compras públicas, licitações e textos jurídico-administrativos
- **Fontes:** OpenAlex (EN+PT) + BDTD (teses/dissertações PT) + arXiv (42 artigos on-topic; tema nichado)
- **Idiomas:** Inglês (2.135 docs) + Português (971 docs) — corpus bilíngue
- **Janela temporal:** 2018–2026
- **Tamanho final:** 3.106 documentos (2.758 OpenAlex + 306 BDTD + 42 arXiv)
- **Pré-processamento:** lowercase, regex tokenization, stopwords bilíngues (NLTK EN+PT + custom), Porter stemmer (EN) / RSLP stemmer (PT), detecção automática de idioma
- **Recuperadores:** BM25 (k1=1.5, b=0.75); KNN/TF-IDF + cosseno; denso (embeddings multilíngues, `paraphrase-multilingual-MiniLM-L12-v2`)
- **Módulos:** M1 re-ranking (Reg. Logística), M2 clustering (K-means), M3 expansão por regras de associação, M4 otimização (grid search), M5 RRF (BM25 + denso)

## Resultados

Corpus bilíngue: 3.106 documentos (2.135 EN + 971 PT; OpenAlex + BDTD + arXiv). 15 consultas, 443 julgamentos de relevância.

| Sistema | P@10 | R@10 | MAP | nDCG@10 |
|---------|------|------|-----|---------|
| BM25 | 0.727 | 0.644 | 0.830 | 0.791 |
| KNN/TF-IDF | 0.720 | 0.639 | 0.740 | 0.697 |
| Denso (embeddings) | 0.240 | 0.172 | 0.180 | 0.306 |
| RRF (BM25+denso) | 0.580 | 0.456 | 0.552 | 0.642 |
| **M1 (re-ranking)** | **0.740** | **0.651** | **0.864** | **0.794** |
| M3 (expansão) | 0.567 | 0.515 | 0.608 | 0.643 |

> O re-ranking supervisionado (M1) é o melhor sistema. O denso e o RRF aparecem subavaliados por viés de pooling: encontram relevantes que o gabarito (de origem lexical) não reconhece. O relatório discute isso em "O desafio da anotação de relevância" e o liga à motivação do mestrado (anotação manual não escala). M4 (otimização) achou o melhor BM25 em k1=2.0, b=0.5 (MAP 0.851).

## Uso de assistentes de IA generativa

Conforme Resolução nº 455-COUN/UFMS (BO-UFMS ID 581705; Art. 6º, V; Art. 12, Parágrafo único):

- **Gemini (Google, Deep Research):** pesquisa exploratória de fontes acadêmicas em português. O domínio específico (compras públicas brasileiras, Lei 14.133/2021) exigiu busca por bases complementares ao ArXiv. Resultados avaliados criticamente e verificados manualmente.
- **Claude/Kiro (Anthropic):** apoio na implementação de scripts de coleta e pipeline, sugestões de hiperparâmetros e estruturação do relatório.

As decisões de projeto, anotação de qrels, análise dos resultados e redação argumentativa são integralmente do autor. Todo código gerado com auxílio de IA foi revisado, testado e adaptado.

## Vídeo de apresentação

Ver `LINKS.txt`.
