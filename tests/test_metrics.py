"""Testes das metricas de avaliacao (valores conferidos a mao)."""
import evaluate as ev

# Relevantes: d1 (rel=1) e d3 (rel=2). Total relevantes = 2.
QRELS = {"d1": 1, "d2": 0, "d3": 2, "d4": 0}


def test_precision_at_k():
    ranked = ["d1", "d2", "d3", "d5"]
    assert ev.precision_at_k(ranked, QRELS, 4) == 2 / 4


def test_recall_at_k():
    ranked = ["d1", "d2"]
    assert ev.recall_at_k(ranked, QRELS, 2) == 1 / 2


def test_recall_sem_relevantes():
    assert ev.recall_at_k(["a"], {"a": 0}, 1) == 0.0


def test_average_precision():
    ranked = ["d1", "d2", "d3"]
    esperado = (1 / 1 + 2 / 3) / 2  # acertos em pos 1 e 3, /total_rel
    assert abs(ev.average_precision(ranked, QRELS) - esperado) < 1e-9


def test_ndcg_perfeito():
    qrels = {"a": 1, "b": 1}
    assert abs(ev.ndcg_at_k(["a", "b"], qrels, 2) - 1.0) < 1e-9


def test_ndcg_sem_relevantes():
    assert ev.ndcg_at_k(["x"], {}, 10) == 0.0
