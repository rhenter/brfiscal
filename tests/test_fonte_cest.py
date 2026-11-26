from pathlib import Path

from brfiscal.fontes.cest import assinatura, converter_html

TRECHO = (Path(__file__).parent / "fixtures" / "cv142_trecho.html").read_text(encoding="utf-8")


def test_converter_html_le_vigentes_e_ignora_antigas():
    meta, itens = converter_html(TRECHO, vigencia="2026-11-26")
    por_codigo = {i["c"]: i for i in itens}
    assert meta["vigencia"] == "2026-11-26"
    # REVOGADO e Anexo XXVII ficam de fora
    assert set(por_codigo) == {"0301002", "1700100", "1702400"}
    # redação "verde" (antiga) ignorada: fica só 1704.90.10
    assert por_codigo["1700100"]["n"] == ["17049010"]
    # sem classe verde, mas a primeira redação (vigente) vence
    assert por_codigo["1702400"]["d"].endswith("17.024.04 e 17.024.05")
    # NCMs em vários <p> da mesma célula
    assert por_codigo["0301002"]["n"] == ["22021000", "22029900"]
    assert por_codigo["0301002"]["s"] == "Cervejas, chopes, refrigerantes, águas e outras bebidas"
    assert por_codigo["1700100"]["it"] == "1.0"


def test_assinatura_independe_da_ordem():
    _, itens = converter_html(TRECHO)
    assert assinatura(itens) == assinatura(list(reversed(itens)))
