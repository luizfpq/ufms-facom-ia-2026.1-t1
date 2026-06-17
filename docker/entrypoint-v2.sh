#!/usr/bin/env bash
# Entrypoint do container v2 (buscador de referencias) — UFMS/FACOM 2026.1
set -uo pipefail
cd /app 2>/dev/null || true

banner() {
cat <<'BANNER'
============================================================
 v2 — Buscador de Referencias (prototipo) — Trabalho 1 IA
 Extensao conceitual do sistema de recuperacao.

 Recebe um texto (abstract/artigo), extrai palavras-chave,
 busca no corpus e sugere referencias em BibTeX + lacunas.

 Exemplo:
   python src/v2/reference_finder.py -i exemplo.txt -o refs.bib
   cat refs.bib

 Docs do prototipo: PROPOSTA-V2-BUSCADOR-REFERENCIAS.md
============================================================
BANNER
}

cmd="${1:-shell}"
case "$cmd" in
  shell) banner; exec /bin/bash ;;
  ttyd)  exec ttyd -W -p 7681 -b "/${TTYD_SLUG:-terminal}" /usr/local/bin/entrypoint.sh shell ;;
  *)     exec "$@" ;;
esac
