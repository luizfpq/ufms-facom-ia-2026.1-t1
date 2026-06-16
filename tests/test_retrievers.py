"""Testes do modulo de fusao (Reciprocal Rank Fusion)."""
from retrievers import reciprocal_rank_fusion


def test_rrf_score_formula():
    # Documento em 1a posicao de um unico run: score = 1/(k+1)
    fused = dict(reciprocal_rank_fusion([[("x", 5.0)]], k=60))
    assert abs(fused["x"] - 1 / 61) < 1e-9


def test_rrf_combina_todos_os_docs():
    run1 = [("a", 9.0), ("b", 8.0), ("c", 1.0)]
    run2 = [("b", 0.9), ("a", 0.5), ("d", 0.1)]
    fused = reciprocal_rank_fusion([run1, run2], k=60)
    assert {d for d, _ in fused} == {"a", "b", "c", "d"}


def test_rrf_ordenado_desc():
    run1 = [("a", 9.0), ("b", 8.0)]
    run2 = [("a", 0.9), ("b", 0.5)]
    fused = reciprocal_rank_fusion([run1, run2], k=60)
    # 'a' aparece em 1o nos dois runs -> deve liderar
    assert fused[0][0] == "a"
    scores = [s for _, s in fused]
    assert scores == sorted(scores, reverse=True)


def test_rrf_k_menor_aumenta_score():
    s10 = dict(reciprocal_rank_fusion([[("x", 1.0)]], k=10))["x"]
    s60 = dict(reciprocal_rank_fusion([[("x", 1.0)]], k=60))["x"]
    assert s10 > s60
