# Roteiro do Vídeo — T1 Inteligência Artificial (~8 minutos)

> Checklist do professor: "Cobre motivação, decisões de projeto, modelos, metodologia, resultados."
> Alinhado com: `apresentacao/apresentacao.tex` e `_interno/FALAS_APRESENTACAO.md`

---

## [0:00 – 0:30] Abertura — Título

**O que mostrar:** Slide 1 (título)

**O que falar:**

"Meu nome é Luiz Quirino, mestrando no PPGCC da FACOM. Este é o Trabalho 1 de Inteligência Artificial — um sistema de recuperação de artigos científicos sobre IA aplicada a compras públicas e licitações. O 'R' do RAG."

---

## [0:30 – 1:30] O que é este trabalho? (Slide 2)

**O que mostrar:** Slide 2 + diagrama de arquitetura

**O que falar:**

"O que eu construí é um sistema de recuperação de artigos científicos. A ideia é buscar artigos relevantes dentro de um corpus bilíngue sobre um tema específico: IA aplicada a compras públicas."

"Esse tema não é aleatório — é o embrião técnico da minha proposta de mestrado. O T1 me deu a oportunidade de testar a viabilidade técnica desse módulo de busca."

---

## [1:30 – 2:30] Corpus: 3.106 artigos de 3 fontes (Slide 3)

**O que mostrar:** Slide 3

**O que falar:**

"Construí o corpus do zero, com 3.106 artigos de três fontes. OpenAlex foi a principal — 2.758 artigos, gratuita, sem rate limit. BDTD trouxe 306 teses em português — porque a Lei 14.133 produz literatura majoritariamente em PT. O arXiv rendeu só 42 artigos on-topic — e isso por si só é um achado: o tema é nichado. Existe muita pesquisa sobre IA e muita sobre licitação, mas pouco no cruzamento."

"No total: 2.135 em inglês, 971 em português. Janela de 2018 a 2026."

---

## [2:30 – 3:15] Pipeline de pré-processamento (Slide 4)

**O que mostrar:** Slide 4, opcional terminal mostrando tokenização

**O que falar:**

"Pré-processamento direto: tokenização, lowercase, stopwords bilíngues — NLTK inglês e português mais custom. Stemming por idioma detectado automaticamente: Porter para inglês, RSLP para português. Cada documento é título + abstract concatenados."

---

## [3:15 – 4:00] Três recuperadores (Slide 5)

**O que mostrar:** Slide 5

**O que falar:**

"Três recuperadores base. BM25, esparso clássico — casa termos exatos. Tem conexão conceitual com Naïve Bayes: o IDF funciona como log-odds de termos raros."

"KNN com TF-IDF — vetoriza e busca por cosseno."

"E embeddings multilíngues com o paraphrase-multilingual-MiniLM — casa significado entre PT e EN mesmo sem palavras em comum."

---

## [4:00 – 4:45] Cinco módulos (Slide 6)

**O que mostrar:** Slide 6

**O que falar:**

"Cinco módulos implementados. M1 é re-ranking com Regressão Logística. M2, agrupamento com K-means. M3, expansão de consulta com regras de associação. M4, otimização — grid search que encontrou k1=2.0, b=0.5 com MAP 0.851. M5, fusão híbrida via Reciprocal Rank Fusion."

---

## [4:45 – 5:00] Transição (Chapter slide)

**O que mostrar:** Slide 7 — "O achado honesto"

*[pausa breve, deixar respirar]*

---

## [5:00 – 6:00] Avaliação e viés de pooling (Slides 8–10)

**O que mostrar:** Slides 8, 9, 10

**O que falar:**

"15 consultas do domínio, 443 julgamentos de relevância. Aqui está o ponto central: quando adicionei o denso e os módulos, o pool cresceu. O denso retorna documentos claramente relevantes que o gabarito original — construído a partir de resultados do BM25 — não reconhecia. As métricas do denso parecem baixas, mas é viés de pooling, não falha do modelo."

"Dois exemplos concretos: query sobre 'regulatory compliance verification' — o denso achou um artigo sobre verificação de conformidade GDPR. Overlap lexical de 60%, relevância máxima. O BM25 não retornou porque os termos não batem diretamente."

"Eu poderia esconder isso. Preferi mostrar e explicar. E isso conecta diretamente com o mestrado: anotar relevância à mão não escala."

---

## [6:00 – 6:45] Resultados (Slide 11)

**O que mostrar:** Slide 11 — tabela de resultados

**O que falar:**

"O melhor sistema é o M1, re-ranking supervisionado: MAP 0.864. BM25 puro é baseline forte com MAP 0.830. O denso e o RRF ficam abaixo nas métricas pelo viés que expliquei — encontram relevantes que o gabarito não cobre."

---

## [6:45 – 7:15] Acesso ao vivo (Slide 12)

**O que mostrar:** Slide 12, opcionalmente abrir o terminal/v2 no browser

**O que falar:**

"O sistema está rodando em container na Oracle Cloud. Duas formas de acesso: um terminal web com o pipeline completo, e uma interface gráfica com LLM local que aceita upload de PDF ou texto e busca referências automaticamente com justificativas. Links e credenciais no LINKS.txt do repositório."

---

## [7:15 – 8:00] Três lições aprendidas (Slide 13)

**O que mostrar:** Slide 13

**O que falar:**

"Três lições. Primeira: esparso e denso são complementares — um casa termo, o outro casa significado."

"Segunda: domínio nichado e bilíngue exige múltiplas fontes e embeddings multilíngues."

"Terceira, a mais importante: a qualidade da avaliação depende da completude do gabarito. Avaliar recuperadores semânticos com gabarito lexical subestima o que eles têm de melhor. Esse é o gargalo que levo para o mestrado."

"Obrigado."

---

## [8:00] Encerramento (Slide 14)

*[não falar, slide de créditos]*

---

## Dados de referência (para conferência)

| Sistema | P@10 | R@10 | MAP | nDCG@10 |
|---------|------|------|-----|---------|
| BM25 | 0.727 | 0.644 | 0.830 | 0.791 |
| KNN/TF-IDF | 0.720 | 0.639 | 0.740 | 0.697 |
| Denso (embeddings) | 0.240 | 0.172 | 0.180 | 0.306 |
| RRF (BM25+denso) | 0.580 | 0.456 | 0.552 | 0.642 |
| **M1 (re-ranking)** | **0.740** | **0.651** | **0.864** | **0.794** |
| M3 (expansão) | 0.567 | 0.515 | 0.608 | 0.643 |

- Corpus: 3.106 documentos (2.758 OpenAlex + 306 BDTD + 42 arXiv)
- Idiomas: 2.135 EN + 971 PT
- Queries: 15 (443 julgamentos de relevância)
- Modelo denso: paraphrase-multilingual-MiniLM-L12-v2

---

## Dicas para gravação

- **Não leia.** Internalize os pontos e fale naturalmente.
- **Mostre o terminal.** Demo ao vivo impressiona mais que slides.
- **Sequência de telas:** Slides → Terminal (demo) → Slides (resultados)
- **Se passar de 8 min:** Corte o bloco de pré-processamento (slide 4).
- **O que NÃO precisa mostrar:** Coleta inteira, setup do venv, código auxiliar.
