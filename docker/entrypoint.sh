#!/usr/bin/env bash
# Entrypoint do container do Trabalho 1 de IA (UFMS/FACOM 2026.1).
# Modos:
#   demo  (padrao) -> demo interativa (query -> ranking dos 3 sistemas)
#   eval           -> pipeline + avaliacao (P@10, R@10, MAP, nDCG@10)
#   shell          -> bash interativo em /app (usado no login SSH do container)
#   sshd           -> sobe o servidor SSH do container (deploy p/ acesso do docente)
#   <outro>        -> executa como comando
set -uo pipefail
cd /app 2>/dev/null || true

banner() {
cat <<'BANNER'
============================================================
 Sistema de Recuperacao de Informacao Hibrido (BM25+KNN+RRF)
 Trabalho 1 — Inteligencia Artificial — UFMS/FACOM 2026.1
 Autor: Luiz Fernando Postingel Quirino

 Comandos uteis (dentro deste container):
   make demo QUERY="public procurement NLP"   consulta -> ranking
   make eval                                   avaliacao completa
   cat relatorio.pdf  (ou baixe via scp)       relatorio final
============================================================
BANNER
}

cmd="${1:-demo}"
case "$cmd" in
  demo)  banner; exec python src/demo.py ;;
  eval)  exec make eval ;;
  shell) banner; exec /bin/bash ;;
  sshd)
    # Gera host keys na primeira execucao e sobe o sshd em foreground
    ssh-keygen -A 2>/dev/null || true
    exec /usr/sbin/sshd -D -e
    ;;
  *)     exec "$@" ;;
esac
