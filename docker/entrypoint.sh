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
 Recuperacao de artigos — Trabalho 1 IA — UFMS/FACOM 2026.1
 Autor: Luiz Fernando Postingel Quirino

 Sistema completo: BM25 + KNN/TF-IDF + denso (embeddings)
 + RRF + modulos M1-M5.

 Comandos:
   make demo QUERY="public procurement NLP"   consulta -> ranking
   make eval                                   avaliacao dos 6 sistemas
   cat README.md                               instrucoes e resultados
 (o relatorio em PDF esta na submissao e no repositorio)
============================================================
BANNER
}

cmd="${1:-demo}"
case "$cmd" in
  demo)  banner; exec python src/demo.py ;;
  eval)  exec make eval ;;
  shell) banner; exec /bin/bash ;;
  sshd)
    echo "Modo SSH removido. Use o modo 'ttyd' (terminal web)." >&2; exit 1
    ;;
  ttyd)
    # Terminal web (WebSocket). Cada conexao abre um shell proprio no container.
    # Base-path = slug nao-adivinhavel: http://host:porta/SLUG
    # Auth via env TTYD_CREDENTIAL (formato user:pass); sem ela, roda sem auth.
    CRED_FLAG=""
    [ -n "${TTYD_CREDENTIAL:-}" ] && CRED_FLAG="-c ${TTYD_CREDENTIAL}"
    exec ttyd -W -p 7681 -b "/${TTYD_SLUG:-terminal}" $CRED_FLAG /usr/local/bin/entrypoint.sh shell
    ;;
  *)     exec "$@" ;;
esac
