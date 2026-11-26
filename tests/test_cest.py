from brfiscal import cest
from brfiscal.cest import SituacaoPar


def test_obter_e_formatar():
    item = cest.obter("99.999.01")
    assert item.descricao.startswith("Biscoitos")
    assert item.codigo_formatado == "99.999.01"


def test_para_ncm_por_prefixo_retorna_varios():
    codigos = {c.codigo for c in cest.para_ncm("1905.31.00")}
    assert codigos == {"9999901", "9999902"}


def test_validar_par_ok():
    assert cest.validar_par("19053100", "9999901").situacao is SituacaoPar.OK


def test_validar_par_ncm_nao_listado_sugere():
    r = cest.validar_par("19053100", "9999903")
    assert r.situacao is SituacaoPar.NCM_NAO_LISTADO
    assert not r.ok
    assert {c.codigo for c in r.sugestoes} == {"9999901", "9999902"}


def test_validar_par_sem_cest():
    assert cest.validar_par("48181000", None).situacao is SituacaoPar.SEM_CEST
    assert cest.validar_par("22021000", "").situacao is SituacaoPar.CEST_FALTANDO


def test_cest_inexistente():
    assert cest.validar_par("19053100", "1234567").situacao is SituacaoPar.CEST_INEXISTENTE
