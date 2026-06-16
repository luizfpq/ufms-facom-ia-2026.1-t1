# Trabalho Pratico 1 — Inteligencia Artificial — UFMS/FACOM 2026.1
# Sistema de Recuperacao de Informacao Hibrido (BM25 + KNN + RRF)
#
# Use o ambiente virtual antes de rodar os alvos Python:
#   python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

PYTHON ?= python3
RUNS    = notebooks/runs/bm25.trec notebooks/runs/knn.trec notebooks/runs/rrf.trec
QUERY  ?= public procurement NLP

all: help

runs:
	$(PYTHON) src/run_pipeline.py

eval: runs
	$(PYTHON) eval/evaluate.py --qrels eval/qrels.tsv --runs $(RUNS) --k 10

demo:
	$(PYTHON) src/demo.py "$(QUERY)"

relatorio:
	$(MAKE) -C relatorio-fonte

clean:
	$(MAKE) -C relatorio-fonte clean

help:
	@echo "Trabalho 1 IA — UFMS/FACOM 2026.1 (BM25 + KNN + RRF)"
	@echo ""
	@echo "Pre-requisito: source .venv/bin/activate (ou defina PYTHON=)"
	@echo ""
	@echo "Targets:"
	@echo "  make runs        Gera os 3 runs TREC (BM25, KNN, RRF) em notebooks/runs/"
	@echo "  make eval        Gera os runs e avalia (P@10, R@10, MAP, nDCG@10)"
	@echo "  make demo        Demo interativa (use QUERY=\"sua consulta\")"
	@echo "  make relatorio   Compila o relatorio LaTeX -> relatorio.pdf na raiz"
	@echo "  make clean       Limpa artefatos de build do relatorio"
	@echo "  make help        Exibe esta ajuda"

.PHONY: all runs eval demo relatorio clean help
