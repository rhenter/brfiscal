from datetime import date

import pytest

from brfiscal import ncm


def test_metadados_do_espelho_embutido():
    m = ncm.metadados()
    assert m.tabela == "ncm"
    assert m.total > 10_000
    assert m.vigencia >= "2026-01-01"


@pytest.mark.parametrize("codigo", ["19053100", "1905.31.00", " 1905 31 00 ", 19053100])
def test_validar_aceita_formatos(codigo):
    assert ncm.validar(codigo)


@pytest.mark.parametrize("codigo", ["1905", "19053", "00000000", "", "abc"])
def test_validar_rejeita(codigo):
    assert not ncm.validar(codigo)


def test_obter_nivel_superior_mas_nao_usavel_em_nota():
    item = ncm.obter("1905")
    assert item is not None
    assert item.nivel == "posicao"
    assert not item.usavel_em_nota


def test_descricao_completa_resolve_outros():
    item = ncm.obter("19059090")
    assert item.descricao == "Outros"
    assert "Produtos de padaria" in item.descricao_completa
    assert item.ancestrais[:2] == ("19", "1905")


def test_formatar():
    assert ncm.formatar("19053100") == "1905.31.00"
    assert ncm.formatar("1905") == "19.05"
    assert ncm.formatar("190531") == "1905.31"


def test_vigencia():
    item = ncm.obter("19053100")
    assert item.vigente_em(date(2026, 11, 26))
    assert not item.vigente_em(date(2000, 1, 1))


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("creme dental colgate 90g", "33061000"),
        ("papel higienico folha dupla", "48181000"),
        ("queijo mussarela fatiado", "04061010"),
        ("biscoito recheado chocolate", "19053100"),
    ],
)
def test_buscar_sugere_ncm(texto, esperado):
    codigos = [r.item.codigo for r in ncm.buscar(texto, limite=3)]
    assert esperado in codigos


def test_buscar_so_retorna_codigos_de_8_digitos():
    assert all(len(r.item.codigo) == 8 for r in ncm.buscar("leite", limite=50))


def test_buscar_vazio():
    assert ncm.buscar("") == []
    assert ncm.buscar("xyzxyz") == []
