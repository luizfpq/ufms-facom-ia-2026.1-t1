# Fontes de Dados & APIs — Legislação e Referências

> Documentação de APIs testadas e ideias para expansão do buscador de referências (v2).

---

## APIs Testadas (2026-06-08)

### ✅ API do Senado Federal (Legislação)
- **URL:** `https://legis.senado.leg.br/dadosabertos/legislacao/lista`
- **Formato:** XML
- **Autenticação:** Nenhuma
- **Parâmetros úteis:**
  - `tipo` — lei, decreto, in, portaria, resolucao, etc.
  - `ano` — ano da norma
  - `numero` — número da norma
  - `palavraChave` — busca textual (limitada, retorna muito ruído)
- **Exemplo:**
  ```
  GET https://legis.senado.leg.br/dadosabertos/legislacao/lista?tipo=lei&ano=2021&numero=14133
  ```
- **Resultado:** Retorna metadados (tipo, número, ementa, data, apelido)
- **Limitação:** Busca por `palavraChave` não filtra pela ementa — retorna todas as normas do tipo, não funciona bem para busca semântica

### ⚠️ LexML (Senado/Rede de Informação Legislativa)
- **URL web:** `https://www.lexml.gov.br/busca/search?keyword=X&tipoDocumento=Legislacao`
- **API SRU:** `https://www.lexml.gov.br/busca/SRU` — **FORA DO AR** (404 em jun/2026)
- **Status:** Interface web funciona, API REST morta
- **Abordagem:** Scraping leve da página de resultados (extrai títulos + URNs)
- **Dados:** Toda legislação federal, estadual e municipal + jurisprudência

### ❌ normas.leg.br/api
- **Status:** 404 — API não existe nesse endpoint (testado jun/2026)

### ❌ Planalto (legislacao.planalto.gov.br)
- **Status:** Sem API REST. Apenas HTML estático. Scraping possível mas frágil.

---

## Abordagem Implementada na v2

Dado que as APIs de busca textual são limitadas, a v2 usa **abordagem híbrida:**

1. **Base curada local** (`LEGISLATION_DB` em `legislation_source.py`)
   - 12 normas federais sobre TIC/nuvem/contratações com tags manuais
   - Busca por match de termos no query vs tags + ementa
   - Vantagem: preciso, relevante, controlado
   - Desvantagem: escopo limitado ao que foi cadastrado

2. **Scraping LexML** (fallback)
   - Busca web no portal LexML
   - Extrai títulos e URNs do HTML
   - Complementa a base local quando query não encontra match

---

## Ideias para Expansão (v2.1+)

### Fontes Acadêmicas

| Fonte | API | Status | Notas |
|---|---|---|---|
| OpenAlex | REST, gratuita | ✅ Já usado no T1 | 250M+ works, filtros por conceito/instituição |
| Semantic Scholar | REST, gratuita | 🟡 Testar | Embeddings SPECTER, grafo de citações |
| CrossRef | REST, gratuita | 🟡 Testar | DOIs, metadados de journals |
| BDTD | OAI-PMH | ✅ Já usado (coleta_bdtd.py) | Teses/dissertações brasileiras |
| Google Scholar | Scraping | ⚠️ Rate limit | Mais abrangente, mas frágil |
| Scopus/WoS | REST, paga | ❌ Sem acesso | Precisaria de institucional via CAPES |

### Fontes de Legislação

| Fonte | Tipo | Cobertura | Viabilidade |
|---|---|---|---|
| Base curada (local) | JSON/dict | TIC/nuvem/licitações | ✅ Implementado |
| LexML web scraping | HTML parsing | Federal + estadual | ⚠️ Frágil |
| API Senado | XML REST | Leis federais | ✅ Para busca por nº/tipo |
| Portal e-Cidadania | - | Projetos de lei | 🟡 Futuro |
| TCU Jurisprudência | HTML | Acórdãos | 🟡 Scraping possível |
| CONAMA/normas ambientais | - | INs ambientais | 🟡 Se necessário |

### Features Futuras

1. **Embeddings densos** — substituir TF-IDF por sentence-transformers (e5-base ou multilingual-e5) para melhor captura semântica entre português e inglês

2. **Busca em tempo real na OpenAlex** — para cada query, consultar OpenAlex API e trazer papers frescos que não estão no corpus local

3. **Grafo de citações** — dado um paper relevante, puxar "quem cita este paper" e "quem este paper cita" (via Semantic Scholar ou OpenAlex)

4. **Classificação de relevância por seção** — identificar QUAL seção do artigo cada referência sugerida melhor atende (Intro, Fundamentação, Metodologia, Discussão)

5. **Legislação viva** — monitorar alterações em normas (revogações, alterações) via API do Senado

6. **Geração de justificativa** — para cada referência sugerida, gerar 1-2 frases explicando POR QUE ela é relevante para o texto input

7. **Integração Obsidian** — gerar notas de leitura automáticas (template com abstract, relevância, seção-alvo)

8. **Índice de cobertura** — avaliar quais temas do input NÃO encontraram correspondência (gaps) → indicar necessidade de busca manual

---

## Como Expandir a Base de Legislação

Editar `src/v2/legislation_source.py`, dicionário `LEGISLATION_DB`:

```python
{"tipo": "Resolução CNJ", "numero": "182", "ano": 2013,
 "ementa": "Diretrizes para implantação de TI no Judiciário",
 "url": "https://...",
 "tags": ["TI", "judiciário", "governança", "contratação"]},
```

Cada entrada precisa de: tipo, número, ano, ementa, url e lista de tags para matching.

---

*Documentado em 2026-06-08*
