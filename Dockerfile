# Sistema de Recuperacao de Informacao Hibrido (BM25 + KNN + RRF)
# Trabalho 1 — IA — UFMS/FACOM 2026.1
#
# Imagem para o docente executar/testar o sistema compilado e funcional.
# Build:  docker build -t ia-t1 .
# Run:    docker run --rm -it ia-t1            # demo interativa
#         docker run --rm ia-t1 make eval      # roda avaliacao completa

FROM python:3.13-slim

# Sem buffer no stdout (logs imediatos) e sem .pyc
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NLTK_DATA=/opt/nltk_data

WORKDIR /app

# make para os atalhos; ttyd para o terminal web.
# Sem texlive (o relatorio.pdf ja vai pronto).
RUN apt-get update && apt-get install -y --no-install-recommends make curl ca-certificates \
    && curl -fsSL -o /usr/local/bin/ttyd "https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.$(uname -m)" \
    && chmod +x /usr/local/bin/ttyd \
    && apt-get purge -y curl && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python (camada cacheavel)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Dados do NLTK embutidos na imagem (stopwords + RSLP), evita download em runtime
RUN python -c "import nltk; nltk.download('stopwords', download_dir='/opt/nltk_data'); nltk.download('rslp', download_dir='/opt/nltk_data')"

# Modelo de embeddings embutido (evita download na primeira consulta)
ENV HF_HOME=/opt/hf
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')" \
    && chmod -R a+rX /opt/hf

# Codigo, dados e artefatos de entrega
COPY src/ ./src/
COPY eval/ ./eval/
COPY data/ ./data/
COPY notebooks/runs/ ./notebooks/runs/
COPY Makefile ./
COPY relatorio.pdf ./
COPY README.md ./

# Usuario nao-root dono do app (e o usuario do terminal web)
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

# Entrypoint (modos: demo/eval/shell/ttyd)
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh

# Default: execucao local (demo). No deploy, sobe-se com o comando "ttyd".
USER app
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["demo"]
