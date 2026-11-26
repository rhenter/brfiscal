"""CEST - Código Especificador da Substituição Tributária (Convênio ICMS 142/2018).

O CEST tem 7 dígitos: ``SS.III.DD`` (segmento, item, especificação). Cada CEST lista
NCMs (às vezes só o início do código, como ``1905`` ou ``1905.31``). Por isso a
relação NCM -> CEST é de **um para muitos**: um mesmo NCM pode ter vários CESTs, e
quem escolhe é a descrição do produto. A lib sugere; o usuário confirma.

Exemplo::

    from brfiscal import cest

    cest.para_ncm("19053100")            # CESTs possíveis para o NCM
    cest.validar_par("19053100", "1705700")
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ._tabela import Metadados, Resultado, Tabela

__all__ = [
    "Cest",
    "SituacaoPar",
    "ValidacaoPar",
    "buscar",
    "formatar",
    "limpar",
    "metadados",
    "obter",
    "para_ncm",
    "validar",
    "validar_par",
]

_SO_DIGITOS = re.compile(r"\D")


@dataclass(frozen=True)
class Cest:
    codigo: str
    """7 dígitos."""
    descricao: str
    segmento: str
    """Nome do segmento (anexo), ex.: ``Produtos alimentícios``."""
    ncms: tuple[str, ...]
    """NCMs/prefixos de NCM listados para o CEST (só dígitos)."""
    item: str = ""
    """Número do item no anexo (ex.: ``17.0``)."""

    @property
    def codigo_formatado(self) -> str:
        return formatar(self.codigo)

    @property
    def codigo_segmento(self) -> str:
        return self.codigo[:2]

    def aceita_ncm(self, ncm: str) -> bool:
        ncm = limpar(ncm)
        return any(ncm.startswith(p) for p in self.ncms)

    @classmethod
    def de_dict(cls, d: dict[str, Any]) -> Cest:
        return cls(
            codigo=d["c"],
            descricao=d["d"],
            segmento=d.get("s", ""),
            ncms=tuple(d.get("n", ())),
            item=d.get("it", ""),
        )


class SituacaoPar(str, Enum):
    OK = "ok"
    """O CEST lista esse NCM."""
    CEST_INEXISTENTE = "cest_inexistente"
    NCM_NAO_LISTADO = "ncm_nao_listado"
    """O CEST existe, mas não lista esse NCM."""
    SEM_CEST = "sem_cest"
    """Nenhum CEST foi informado e o NCM não aparece em nenhum CEST (esperado)."""
    CEST_FALTANDO = "cest_faltando"
    """Nenhum CEST informado, mas o NCM aparece em algum CEST: confirmar com o produto."""


@dataclass(frozen=True)
class ValidacaoPar:
    situacao: SituacaoPar
    sugestoes: tuple[Cest, ...] = ()
    """CESTs que listam o NCM (para o usuário escolher pela descrição)."""

    @property
    def ok(self) -> bool:
        return self.situacao in (SituacaoPar.OK, SituacaoPar.SEM_CEST)


_tabela: Tabela[Cest] = Tabela(
    "cest",
    fabrica=Cest.de_dict,
    chave=lambda c: c.codigo,
    texto_busca=lambda c: [(c.descricao, 1.0), (c.segmento, 0.3)],
)


def limpar(codigo: str | int) -> str:
    return _SO_DIGITOS.sub("", str(codigo))


def formatar(codigo: str | int) -> str:
    """``1705700`` -> ``17.057.00``."""
    c = limpar(codigo)
    return f"{c[:2]}.{c[2:5]}.{c[5:]}" if len(c) == 7 else c


def obter(codigo: str | int) -> Cest | None:
    return _tabela.obter(limpar(codigo))


def validar(codigo: str | int) -> bool:
    return obter(codigo) is not None


def para_ncm(ncm: str | int) -> list[Cest]:
    """CESTs cujo anexo lista o NCM (pelo código completo ou por prefixo)."""
    n = limpar(ncm)
    return [c for c in _tabela if c.aceita_ncm(n)]


def validar_par(ncm: str | int, cest: str | int | None) -> ValidacaoPar:
    """Confere se o CEST informado é compatível com o NCM."""
    possiveis = tuple(para_ncm(ncm))
    if not cest or not limpar(cest):
        situacao = SituacaoPar.CEST_FALTANDO if possiveis else SituacaoPar.SEM_CEST
        return ValidacaoPar(situacao, possiveis)
    item = obter(cest)
    if item is None:
        return ValidacaoPar(SituacaoPar.CEST_INEXISTENTE, possiveis)
    if item.aceita_ncm(limpar(ncm)):
        return ValidacaoPar(SituacaoPar.OK, possiveis)
    return ValidacaoPar(SituacaoPar.NCM_NAO_LISTADO, possiveis)


def buscar(texto: str, limite: int = 10) -> list[Resultado[Cest]]:
    return _tabela.buscar(texto, limite=limite)


def metadados() -> Metadados:
    return _tabela.metadados


def tabela() -> Tabela[Cest]:
    return _tabela
