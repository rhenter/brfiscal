"""NCM - Nomenclatura Comum do Mercosul (tabela oficial da Receita Federal / Siscomex).

Exemplo::

    from brfiscal import ncm

    ncm.validar("1905.31.00")         # True
    ncm.obter("19053100").descricao_completa
    ncm.buscar("biscoito recheado chocolate")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from ._sinonimos import NCM as _SINONIMOS
from ._tabela import Metadados, Resultado, Tabela

__all__ = [
    "Ncm",
    "buscar",
    "formatar",
    "limpar",
    "metadados",
    "obter",
    "todos",
    "validar",
    "validar_formato",
]

_SO_DIGITOS = re.compile(r"\D")
#: Níveis da nomenclatura pelo número de dígitos.
NIVEIS = {2: "capitulo", 4: "posicao", 5: "subposicao1", 6: "subposicao2", 7: "item", 8: "subitem"}


@dataclass(frozen=True)
class Ncm:
    codigo: str
    """Só dígitos (2 a 8). Códigos válidos em nota fiscal têm 8 dígitos."""
    descricao: str
    """Texto do próprio nível, como publicado (ex.: ``-- Outros``)."""
    descricao_completa: str
    """Descrição montada com os níveis acima, útil quando o texto é só ``Outros``."""
    inicio: date | None = None
    fim: date | None = None
    ato: str = ""
    ancestrais: tuple[str, ...] = field(default=(), compare=False)

    @property
    def nivel(self) -> str:
        return NIVEIS.get(len(self.codigo), "?")

    @property
    def usavel_em_nota(self) -> bool:
        """Só o subitem (8 dígitos) pode ir na NF-e/NFC-e."""
        return len(self.codigo) == 8

    @property
    def codigo_formatado(self) -> str:
        return formatar(self.codigo)

    def vigente_em(self, dia: date) -> bool:
        return (self.inicio is None or self.inicio <= dia) and (self.fim is None or dia <= self.fim)

    @classmethod
    def de_dict(cls, d: dict[str, Any]) -> Ncm:
        return cls(
            codigo=d["c"],
            descricao=d["d"],
            descricao_completa=d.get("dc", d["d"]),
            inicio=date.fromisoformat(d["i"]) if d.get("i") else None,
            fim=date.fromisoformat(d["f"]) if d.get("f") else None,
            ato=d.get("a", ""),
            ancestrais=tuple(d.get("p", ())),
        )


def _texto_busca(item: Ncm) -> list[tuple[str, float]]:
    return [(item.descricao, 1.0), (item.descricao_completa, 0.6)]


_tabela: Tabela[Ncm] = Tabela(
    "ncm",
    fabrica=Ncm.de_dict,
    chave=lambda n: n.codigo,
    texto_busca=_texto_busca,
    filtro_busca=lambda n: n.usavel_em_nota,
    sinonimos=_SINONIMOS,
)


def limpar(codigo: str | int) -> str:
    """Remove pontos, espaços e tudo que não for dígito."""
    return _SO_DIGITOS.sub("", str(codigo))


def formatar(codigo: str | int) -> str:
    """``19053100`` -> ``1905.31.00`` (aceita também códigos de níveis superiores)."""
    c = limpar(codigo)
    if len(c) <= 2:
        return c
    if len(c) <= 4:
        return f"{c[:2]}.{c[2:]}"
    if len(c) <= 6:
        return f"{c[:4]}.{c[4:]}"
    return f"{c[:4]}.{c[4:6]}.{c[6:]}"


def validar_formato(codigo: str | int) -> bool:
    """Só confere se tem 8 dígitos; não consulta a tabela."""
    return len(limpar(codigo)) == 8


def obter(codigo: str | int) -> Ncm | None:
    """Devolve o NCM (de qualquer nível) ou ``None`` se não existir na tabela vigente."""
    return _tabela.obter(limpar(codigo))


def validar(codigo: str | int) -> bool:
    """``True`` se o código tem 8 dígitos e existe na tabela vigente."""
    item = obter(codigo)
    return item is not None and item.usavel_em_nota


def buscar(texto: str, limite: int = 10) -> list[Resultado[Ncm]]:
    """Sugere NCMs (8 dígitos) pela descrição do produto. Sempre confirme a sugestão."""
    return _tabela.buscar(texto, limite=limite)


def todos() -> list[Ncm]:
    return list(_tabela)


def metadados() -> Metadados:
    return _tabela.metadados


def tabela() -> Tabela[Ncm]:
    return _tabela
