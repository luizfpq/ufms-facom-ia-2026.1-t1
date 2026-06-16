"""Testes de I/O (formato TREC e queries)."""
import utils


def test_trec_roundtrip(tmp_path):
    p = tmp_path / "run.trec"
    utils.write_trec_run([("docA", 1.5), ("docB", 0.3)], "q1", "sys", str(p), mode="w")
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    f0 = lines[0].split("\t")
    assert f0[0] == "q1" and f0[1] == "Q0" and f0[2] == "docA"
    assert f0[3] == "1" and f0[5] == "sys"


def test_load_queries(tmp_path):
    p = tmp_path / "q.tsv"
    p.write_text("q1\thello world\nq2\tfoo\n", encoding="utf-8")
    assert utils.load_queries(str(p)) == {"q1": "hello world", "q2": "foo"}


def test_load_corpus(tmp_path):
    p = tmp_path / "c.jsonl"
    p.write_text('{"arxiv_id":"a","title":"t","abstract":"x"}\n\n', encoding="utf-8")
    docs = utils.load_corpus(str(p))
    assert len(docs) == 1 and docs[0]["arxiv_id"] == "a"
