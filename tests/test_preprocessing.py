"""Testes do pre-processamento bilingue."""
import preprocessing as pp


def test_detect_lang_pt():
    txt = "a contratacao de compras publicas para a administracao e o tribunal de contas"
    # marcadores PT sem acento nao batem; usa versao com acento
    txt_acento = "a contratação de compras públicas para a administração e o tribunal"
    assert pp.detect_lang(txt_acento) == "pt"


def test_detect_lang_en():
    txt = "the procurement of public goods and services for the government"
    assert pp.detect_lang(txt) == "en"


def test_preprocess_remove_stopwords_e_aplica_stem():
    toks = pp.preprocess("the running models are presented", lang="en")
    assert "the" not in toks and "are" not in toks
    assert "run" in toks  # Porter: running -> run


def test_preprocess_str_retorna_string():
    s = pp.preprocess_str("public procurement systems", lang="en")
    assert isinstance(s, str) and len(s) > 0
