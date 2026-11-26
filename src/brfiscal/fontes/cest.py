"""Importação da tabela CEST (Anexos II a XXVI do Convênio ICMS 142/2018).

O Confaz publica os anexos só como uma página HTML (sem CSV/JSON oficial).

- ``converter_html``: extrai os CESTs direto da página do convênio. Regras da página:
  o Anexo I lista os segmentos; os Anexos II a XXVI listam os CESTs; redações antigas
  aparecem logo depois da vigente com estilo "verde" (classe ``...verde``) e são
  ignoradas; itens "REVOGADO" também. A partir do Anexo XXVII a página trata de outro
  assunto e a leitura para.
- ``converter_csv``: alternativa para quem já tem a tabela em CSV
  (``cest;ncm;descricao;segmento;item``, NCMs separados por espaço).
"""

from __future__ import annotations

import csv
import io
import re
import urllib.request
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from .._tabela import gravar_espelho

URL = "https://www.confaz.fazenda.gov.br/legislacao/convenios/2018/CV142_18"
_DIGITOS = re.compile(r"\D")


def _ncms(campo: str) -> list[str]:
    saida = []
    for parte in re.split(r"[\s,;]+", campo.strip()):
        codigo = _DIGITOS.sub("", parte)
        if codigo and codigo not in saida:
            saida.append(codigo)
    return saida


def converter_csv(
    texto: str, vigencia: str | None = None, ato: str = "Convênio ICMS 142/2018"
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    leitor = csv.DictReader(io.StringIO(texto), delimiter=";")
    por_codigo: dict[str, dict[str, Any]] = {}
    for linha in leitor:
        codigo = _DIGITOS.sub("", linha["cest"])
        if len(codigo) != 7:
            continue
        item = por_codigo.setdefault(
            codigo,
            {
                "c": codigo,
                "d": linha["descricao"].strip(),
                "s": linha.get("segmento", "").strip(),
                "n": [],
                "it": linha.get("item", "").strip(),
            },
        )
        for n in _ncms(linha.get("ncm", "")):
            if n not in item["n"]:
                item["n"].append(n)
    meta = {
        "tabela": "cest",
        "fonte": URL,
        "vigencia": vigencia or date.today().isoformat(),
        "ato": ato,
        "gerado_em": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    return meta, [por_codigo[c] for c in sorted(por_codigo)]


def atualizar_de_csv(destino: Path, origem: Path, vigencia: str | None = None) -> Path:
    meta, itens = converter_csv(origem.read_text(encoding="utf-8"), vigencia=vigencia)
    return gravar_espelho(Path(destino) / "cest.json.gz", meta, itens)


def baixar(url: str = URL, timeout: float = 120) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "brfiscal"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (URL fixa, https)
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


class _Tabelas(HTMLParser):
    """Lê a página do convênio como uma lista de linhas de tabela, com o anexo corrente."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.linhas: list[tuple[str, list[str], bool]] = []
        """(anexo, células, é_redação_antiga)"""
        self.anexo = ""
        self._p_fora: list[str] | None = None
        self._linha: list[str] | None = None
        self._celula: list[str] | None = None
        self._antiga = False
        self._tabela = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._tabela += 1
        elif tag == "tr" and self._tabela:
            self._linha, self._antiga = [], False
        elif tag == "td" and self._linha is not None:
            self._celula = []
        elif tag == "p":
            if self._celula is not None:
                classe = (dict(attrs).get("class") or "").lower()
                self._antiga = self._antiga or "verde" in classe
                self._celula.append(" ")
            elif not self._tabela:
                self._p_fora = []
        elif tag == "br" and self._celula is not None:
            self._celula.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag == "table":
            self._tabela = max(0, self._tabela - 1)
        elif tag == "td" and self._celula is not None and self._linha is not None:
            self._linha.append(" ".join("".join(self._celula).split()))
            self._celula = None
        elif tag == "tr" and self._linha is not None:
            self.linhas.append((self.anexo, self._linha, self._antiga))
            self._linha = None
        elif tag == "p" and self._p_fora is not None:
            texto = " ".join("".join(self._p_fora).split())
            if re.fullmatch(r"ANEXO [IVXL]+", texto):
                self.anexo = texto.split()[1]
            self._p_fora = None

    def handle_data(self, data: str) -> None:
        if self._celula is not None:
            self._celula.append(data)
        elif self._p_fora is not None:
            self._p_fora.append(data)


def _romano(r: str) -> int:
    valores = {"I": 1, "V": 5, "X": 10, "L": 50}
    total = 0
    for atual, prox in zip(r, r[1:] + " ", strict=True):
        v = valores[atual]
        total += -v if prox in valores and valores[prox] > v else v
    return total


def converter_html(
    html: str, vigencia: str | None = None, ato: str = "Convênio ICMS 142/2018"
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    leitor = _Tabelas()
    leitor.feed(html)
    segmentos: dict[str, str] = {}
    itens: dict[str, dict[str, Any]] = {}
    for anexo, celulas, antiga in leitor.linhas:
        if anexo == "I" and len(celulas) >= 3 and re.fullmatch(r"\d{2}", celulas[2]):
            segmentos[celulas[2]] = celulas[1]
            continue
        if not anexo or not 2 <= _romano(anexo) <= 26 or antiga or len(celulas) < 4:
            continue
        codigo = _DIGITOS.sub("", celulas[1])
        descricao = celulas[3]
        if len(codigo) != 7 or codigo in itens or descricao.upper().startswith("REVOGAD"):
            continue
        itens[codigo] = {
            "c": codigo,
            "d": descricao,
            "s": segmentos.get(codigo[:2], ""),
            "n": _ncms(celulas[2]),
            "it": celulas[0],
        }
    meta = {
        "tabela": "cest",
        "fonte": URL,
        "vigencia": vigencia or date.today().isoformat(),
        "ato": ato,
        "gerado_em": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    return meta, [itens[c] for c in sorted(itens)]


def atualizar(destino: Path, origem: Path | None = None, vigencia: str | None = None) -> Path:
    """Baixa a página do Confaz (ou lê ``origem``) e grava ``destino/cest.json.gz``."""
    html = origem.read_text(encoding="utf-8") if origem else baixar()
    meta, itens = converter_html(html, vigencia=vigencia)
    return gravar_espelho(Path(destino) / "cest.json.gz", meta, itens)


def assinatura(itens: list[dict[str, Any]]) -> str:
    """SHA-256 de ``codigo|ncms`` ordenado: confere se dois importadores leram o mesmo."""
    import hashlib

    linhas = sorted(f"{i['c']}|{' '.join(i['n'])}" for i in itens)
    return hashlib.sha256("\n".join(linhas).encode()).hexdigest()
