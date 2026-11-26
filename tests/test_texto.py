from brfiscal._texto import normalizar, radical, tokens


def test_normalizar_remove_acento_html_e_pontuacao():
    assert normalizar("<i>Pão</i> de Açúcar, 1kg!") == "pao de acucar 1kg"


def test_radical_plural():
    assert radical("biscoitos") == "biscoito"
    assert radical("paes") == "pao"
    assert radical("feijoes") == "feijao"


def test_tokens_ignora_stopwords_e_medidas():
    assert tokens("Biscoito de chocolate 140G 6x1L") == ["biscoito", "chocolate"]
