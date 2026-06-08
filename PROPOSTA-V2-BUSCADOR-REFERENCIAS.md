# Proposta: v2 — Buscador de Referências Bibliográficas

> **Status:** 📋 Planejado (não implementado)
> **Contexto:** Evolução do T1 de IA (Prof. Bruno Nogueira, FACOM/UFMS 2026.1)
> **Motivação:** Usar o motor de busca existente como ferramenta de pesquisa real

---

## Conceito

Transformar o sistema de retrieval (BM25 + KNN + RRF) em um **assistente de busca de referências bibliográficas**. O usuário fornece um texto (artigo em andamento, abstract, ou ideia em linguagem natural) e o sistema retorna:

1. **Documentos relevantes do corpus** (existente)
2. **Sugestão de referências formatadas** (BibTeX) a partir dos metadados do corpus
3. **Gaps identificados** — temas mencionados no texto que NÃO encontram correspondência no corpus (indicando necessidade de busca manual)

---

## Diferença v1 → v2

| Aspecto | v1 (T1 entregue) | v2 (proposta) |
|---|---|---|
| Input | Query curta (1-2 frases) | Texto longo (abstract, seção, artigo inteiro) |
| Output | Lista rankeada de docs | Referências formatadas + gaps + justificativas |
| Corpus | Fixo (3.064 docs) | Expansível (API OpenAlex em tempo real) |
| Interface | CLI/script | CLI interativo ou web simples |
| Uso real | Avaliação acadêmica | Ferramenta de trabalho para pesquisador |

---

## Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────────┐
│  INPUT: Texto do usuário (abstract, ideia, .tex, .md)       │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. EXTRAÇÃO DE CONCEITOS                                    │
│     - Extrai keyphrases do texto (TF-IDF, YAKE, ou LLM)    │
│     - Identifica temas/eixos temáticos                      │
│     - Gera N queries derivadas automaticamente              │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. BUSCA HÍBRIDA (reutiliza core do T1)                    │
│     - BM25 sobre corpus local                               │
│     - KNN/TF-IDF (ou embeddings densos se disponível)       │
│     - RRF para fusão                                        │
│     - Opcional: consulta OpenAlex API em tempo real          │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. PÓS-PROCESSAMENTO                                        │
│     - Deduplica resultados                                   │
│     - Rankeia por relevância combinada                       │
│     - Formata como BibTeX (metadados já no corpus JSONL)     │
│     - Identifica gaps (queries sem resultado relevante)      │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  OUTPUT                                                      │
│     - Top-K referências com abstract e justificativa         │
│     - Arquivo .bib gerado                                   │
│     - Lista de gaps (temas sem cobertura no corpus)          │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementação Mínima (v2.0)

### Novos arquivos

```
src/
├── reference_finder.py    # Orquestrador principal
├── keyphrase_extractor.py # Extração de conceitos do texto input
└── bib_formatter.py       # Gera .bib a partir dos metadados do corpus
```

### Modificações no existente

- `src/retrievers.py` — parametrizar para aceitar queries longas (truncar ou chunkar)
- `data/corpus.jsonl` — garantir que metadados (DOI, autores, ano, journal) estão completos

### Uso esperado

```bash
# A partir de um abstract
python src/reference_finder.py --input "meu_abstract.txt" --top 20 --output refs.bib

# A partir de um .tex inteiro
python src/reference_finder.py --input relatorio/main.tex --top 30 --output refs.bib

# Modo interativo
python src/reference_finder.py --interactive
```

---

## Expansões Futuras (v2.1+)

- **Embeddings densos** (sentence-transformers) em vez de TF-IDF para melhor captura semântica
- **Consulta em tempo real** à OpenAlex/Semantic Scholar API para corpus expandido
- **Filtragem por recência** (priorizar papers dos últimos 3 anos)
- **Clusterização** dos resultados por tema (facilita organizar a revisão de literatura)
- **Integração com Obsidian** — gera nota de leitura para cada referência encontrada
- **Feedback loop** — usuário marca referências como "relevante/irrelevante" → ajusta ranking

---

## Caso de Uso Imediato

O artigo **"Panorama das Contratações de Nuvem no MEC"** (CCETI/IFSP) precisa de 20+ referências novas. O corpus do T1 já contém ~3.000 papers sobre IA + compras públicas. Uma v2 poderia:

1. Receber o `main.tex` do artigo como input
2. Extrair conceitos: "cloud procurement", "public sector", "Lei 14.133", "economicidade", "data quality"
3. Buscar no corpus existente + OpenAlex
4. Gerar um `references_suggestions.bib` com 30 candidatas

---

## Decisão

| Data | Decisão |
|---|---|
| 2026-06-08 | Proposta documentada. Implementação em sessão futura. |
| - | v2 NÃO altera o T1 entregue — branch separada ou diretório `v2/` |

---

*Proposta criada em 2026-06-08*
