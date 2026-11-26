"""Validadores para usar em models e forms do seu projeto.

Consultam o espelho embutido na lib (não precisam do banco).
"""

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

from brfiscal import cest, ncm


def validar_ncm(valor: str) -> None:
    if not valor:
        return
    if not ncm.validar_formato(valor):
        raise ValidationError("NCM deve ter 8 dígitos.", code="ncm_formato")
    if not ncm.validar(valor):
        raise ValidationError(
            "NCM %(valor)s não existe na tabela vigente.",
            code="ncm_inexistente",
            params={"valor": ncm.formatar(valor)},
        )


def validar_cest(valor: str) -> None:
    if not valor:
        return
    if len(cest.limpar(valor)) != 7:
        raise ValidationError("CEST deve ter 7 dígitos.", code="cest_formato")
    if not cest.validar(valor):
        raise ValidationError(
            "CEST %(valor)s não existe na tabela vigente.",
            code="cest_inexistente",
            params={"valor": cest.formatar(valor)},
        )


@deconstructible
class ValidadorNcmCest:
    """Para ``Model.clean``: ``ValidadorNcmCest()(self.ncm, self.cest)``."""

    def __call__(self, valor_ncm: str, valor_cest: str | None) -> None:
        resultado = cest.validar_par(valor_ncm, valor_cest)
        if resultado.ok:
            return
        sugestoes = ", ".join(c.codigo_formatado for c in resultado.sugestoes[:5])
        dica = f" CESTs possíveis para este NCM: {sugestoes}." if sugestoes else ""
        mensagens = {
            "cest_inexistente": "CEST não existe na tabela vigente.",
            "ncm_nao_listado": "Este CEST não lista o NCM informado.",
            "cest_faltando": "Este NCM tem CEST; confira se o produto se enquadra.",
        }
        raise ValidationError(
            {"cest": mensagens[resultado.situacao.value] + dica}, code=resultado.situacao.value
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ValidadorNcmCest)
