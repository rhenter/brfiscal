import pytest

pytest.importorskip("django")

from django.core.exceptions import ValidationError  # noqa: E402
from django.core.management import call_command  # noqa: E402

from brfiscal.contrib.django.models import Cest, CestNcm, Ncm, VersaoTabela  # noqa: E402
from brfiscal.contrib.django.validators import (  # noqa: E402
    ValidadorNcmCest,
    validar_cest,
    validar_ncm,
)


@pytest.mark.django_db
def test_comando_carrega_e_e_idempotente():
    call_command("brfiscal_carregar")
    total = Ncm.objects.count()
    assert total > 10_000
    assert Cest.objects.count() == 3
    assert CestNcm.objects.filter(cest_id="9999901").count() == 2
    assert VersaoTabela.objects.get(tabela="ncm").total == total

    Ncm.objects.create(codigo="99999999", descricao="saiu", descricao_completa="saiu")
    call_command("brfiscal_carregar", "ncm")
    assert Ncm.objects.count() == total + 1
    assert not Ncm.objects.get(codigo="99999999").ativo


def test_validadores():
    validar_ncm("1905.31.00")
    validar_cest("99.999.01")
    with pytest.raises(ValidationError):
        validar_ncm("1905")
    with pytest.raises(ValidationError):
        validar_ncm("00000000")
    with pytest.raises(ValidationError):
        validar_cest("1234567")


def test_validador_par_sugere_cest():
    with pytest.raises(ValidationError) as exc:
        ValidadorNcmCest()("19053100", "9999903")
    assert "99.999.01" in str(exc.value)
