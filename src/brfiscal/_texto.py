"""Normalização de texto para busca (sem dependências externas)."""

from __future__ import annotations

import re
import unicodedata

_HTML = re.compile(r"<[^>]+>")
_NAO_ALFANUM = re.compile(r"[^a-z0-9]+")
# Pesos/medidas típicos de nome de produto: 140G, 1,5L, 2KG, 500ML, 12UN, 6X1L
_MEDIDA = re.compile(r"^\d+([.,]\d+)?(x\d+)?(g|gr|kg|mg|ml|l|lt|un|und|cx|pct|m|cm|mm)?$")

STOPWORDS = frozenset(
    "a as o os de da das do dos e em no na nos nas com sem para por ou um uma "
    "ao aos que se seu sua the of and".split()
)


def remover_html(texto: str) -> str:
    return _HTML.sub("", texto)


def sem_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento, sem HTML e só com letras/números separados por espaço."""
    texto = sem_acentos(remover_html(texto)).lower()
    return _NAO_ALFANUM.sub(" ", texto).strip()


def radical(palavra: str) -> str:
    """Stemming bem simples de plural em português (biscoitos -> biscoito, paes -> pao)."""
    if len(palavra) <= 3:
        return palavra
    for sufixo, troca in (
        ("oes", "ao"),
        ("aes", "ao"),
        ("ais", "al"),
        ("eis", "el"),
        ("res", "r"),
        ("zes", "z"),
        ("ns", "m"),
    ):
        if palavra.endswith(sufixo) and len(palavra) > len(sufixo):
            return palavra[: -len(sufixo)] + troca
    if palavra.endswith("s") and not palavra.endswith("ss"):
        return palavra[:-1]
    return palavra


def tokens(texto: str) -> list[str]:
    """Quebra o texto em radicais úteis para busca, ignorando stopwords e medidas."""
    saida = []
    for palavra in normalizar(texto).split():
        if palavra in STOPWORDS or _MEDIDA.match(palavra) or len(palavra) < 2:
            continue
        saida.append(radical(palavra))
    return saida
