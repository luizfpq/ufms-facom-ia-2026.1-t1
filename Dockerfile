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

# make para os atalhos; openssh-server para acesso SSH direto ao container.
# Sem texlive (o relatorio.pdf ja vai pronto).
RUN apt-get update && apt-get install -y --no-install-recommends make openssh-server \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python (camada cacheavel)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Dados do NLTK embutidos na imagem (stopwords + RSLP), evita download em runtime
RUN python -c "import nltk; nltk.download('stopwords', download_dir='/opt/nltk_data'); nltk.download('rslp', download_dir='/opt/nltk_data')"

# Codigo, dados e artefatos de entrega
COPY src/ ./src/
COPY eval/ ./eval/
COPY data/ ./data/
COPY notebooks/runs/ ./notebooks/runs/
COPY Makefile ./
COPY relatorio.pdf ./
COPY README.md ./

# Usuario nao-root dono do app (e tambem o usuario de login SSH do container)
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app \
    && install -d -m 700 -o app -g app /home/app/.ssh

# Entrypoint (modos: demo/eval/shell/sshd)
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh

# Configuracao do sshd DO CONTAINER (acesso direto do docente, isolado do host)
# - apenas chave, sem senha; sem root; somente o usuario app
# - ao logar, cai no banner + bash em /app (pode rodar make eval / demo)
RUN mkdir -p /run/sshd \
    && { \
       echo "PermitRootLogin no"; \
       echo "PasswordAuthentication no"; \
       echo "ChallengeResponseAuthentication no"; \
       echo "KbdInteractiveAuthentication no"; \
       echo "AllowUsers app"; \
       echo "X11Forwarding no"; \
       echo "AllowTcpForwarding no"; \
       echo "PermitTunnel no"; \
       echo "PrintMotd no"; \
       echo "Match User app"; \
       echo "    ForceCommand /usr/local/bin/entrypoint.sh shell"; \
    } > /etc/ssh/sshd_config.d/ia-t1.conf

# Default: execucao local (demo). No deploy, sobe-se com o comando "sshd".
USER app
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["demo"]
