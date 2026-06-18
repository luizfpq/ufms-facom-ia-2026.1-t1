# v2-app — Buscador de Referências com LLM

Interface web para busca de referências acadêmicas e legislação via LLM local.

## Arquitetura

```
Browser (prof:senha) → :2261
        ↓
   ┌─────────────────────────────────────────┐
   │  v2-app (FastAPI)    rede: v2net        │
   │  - extração de texto (PDF/DOCX/URL/TXT) │
   │  - LLM: keyphrases + queries            │
   │  - BM25 + KNN/TF-IDF + RRF             │
   │  - LLM: justificativas                  │
   └─────────────────┬───────────────────────┘
                     │ http://ollama:11434
   ┌─────────────────┴───────────────────────┐
   │  ollama (qwen2.5:3b)  rede: v2net      │
   │  sem porta exposta ao host              │
   └─────────────────────────────────────────┘
```

## Stack

- **LLM:** ollama + qwen2.5:3b (1.9GB, CPU ARM)
- **Backend:** FastAPI + uvicorn
- **Extração:** pymupdf (PDF), python-docx (DOCX), trafilatura (URLs)
- **Busca:** rank-bm25, scikit-learn (TF-IDF + cosseno), RRF
- **Frontend:** HTML puro, tema PQ Engine (roxo)
- **Auth:** HTTP Basic (`prof` / senha em env var)

## Deploy (ironqui-261)

```bash
# Pré-requisito: rede e volume existem
docker network create v2net
docker volume create ollama_data

# Ollama (sem porta exposta)
docker run -d --name ollama --restart unless-stopped \
  --network v2net -v ollama_data:/root/.ollama \
  ollama/ollama:latest
docker exec ollama ollama pull qwen2.5:3b

# App (expõe 2261)
docker build -t v2-app .
docker run -d --name v2-app --restart unless-stopped \
  --network v2net --cap-drop ALL --security-opt no-new-privileges \
  --pids-limit 256 --memory 2g \
  -v /path/to/corpus.jsonl:/app/data/corpus.jsonl:ro \
  -e OLLAMA_URL=http://ollama:11434 \
  -e OLLAMA_MODEL=qwen2.5:3b \
  -e AUTH_USER=prof -e AUTH_PASS=<senha> \
  -p 2261:8000 v2-app:latest
```

## Acesso

- URL: `http://204.216.149.149:2261/`
- Auth: mesmas credenciais do v1 (HTTP Basic)
- Tempo de resposta: ~30-60s (inference em CPU ARM)

## Segurança

- Ollama isolado na rede Docker interna (sem publish)
- v2-app: cap-drop ALL, no-new-privileges, 2GB RAM limit
- HTTP Basic Auth em todos os endpoints
- Regras iptables bloqueiam egress para redes internas
