# Compilacao do relatorio LaTeX (sbc-template + bibtex/sbc.bst)
# O PDF final e copiado para a raiz do projeto, que e o que vai na entrega.

TEX     = relatorio.tex
PDF     = relatorio.pdf
DESTINO = ../relatorio.pdf

all: $(PDF)
	cp $(PDF) $(DESTINO)
	@echo "PDF gerado e copiado para a raiz: $(DESTINO)"

$(PDF): $(TEX) references.bib sbc-template.sty sbc.bst
	latexmk -pdf -bibtex -interaction=nonstopmode $(TEX)

clean:
	latexmk -C
	rm -f *.bbl *.blg

.PHONY: all clean
