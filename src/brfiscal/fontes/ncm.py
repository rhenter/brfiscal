"""Importação da tabela NCM oficial publicada pela Receita Federal no Portal Único Siscomex."""

from __future__ import annotations

import json
import re
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .._tabela import gravar_espelho
from .._texto import remover_html

URL = "https://portalunico.siscomex.gov.br/classif/api/publico/nomenclatura/download/json?perfil=PUBLICO"
_TRACOS = re.compile(r"^[\s\-–]+")
_VIGENCIA = re.compile(r"(\d{2}/\d{2}/\d{4})")


def baixar(url: str = URL, timeout: float = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "brfiscal"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (URL fixa, https)
        return resp.read()


def _data(texto: str | None) -> str | None:
    if not texto:
        return None
    d = datetime.strptime(texto, "%d/%m/%Y").date()
    return None if d.year >= 9999 else d.isoformat()


def _limpar_descricao(texto: str) -> str:
    texto = remover_html(texto).strip()
    return _TRACOS.sub("", texto).strip()


def _ancestrais(codigo: str, existentes: set[str]) -> list[str]:
    return [codigo[:n] for n in (2, 4, 5, 6, 7) if n < len(codigo) and codigo[:n] in existentes]


def converter(bruto: bytes | str | dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Converte o JSON da Receita no formato compacto do espelho."""
    dados = json.loads(bruto) if isinstance(bruto, (bytes, str)) else bruto
    registros = dados["Nomenclaturas"]
    descr: dict[str, str] = {}
    linhas: dict[str, dict[str, Any]] = {}
    for r in registros:
        codigo = re.sub(r"\D", "", r["Codigo"])
        descr[codigo] = _limpar_descricao(r["Descricao"])
        linhas[codigo] = r
    existentes = set(descr)

    itens = []
    for codigo in sorted(descr):
        r = linhas[codigo]
        pais = _ancestrais(codigo, existentes)
        # Capítulo é muito genérico; a descrição completa começa na posição (4 dígitos).
        partes = [descr[p].rstrip(":") for p in pais if len(p) >= 4] + [descr[codigo]]
        ato = " ".join(
            x for x in (r.get("Tipo_Ato_Ini"), r.get("Numero_Ato_Ini"), r.get("Ano_Ato_Ini")) if x
        )
        item: dict[str, Any] = {"c": codigo, "d": descr[codigo]}
        if len(partes) > 1:
            item["dc"] = " > ".join(partes)
        if pais:
            item["p"] = pais
        if i := _data(r.get("Data_Inicio")):
            item["i"] = i
        if f := _data(r.get("Data_Fim")):
            item["f"] = f
        if ato:
            item["a"] = ato
        itens.append(item)

    vig = _VIGENCIA.search(dados.get("Data_Ultima_Atualizacao_NCM", ""))
    vigencia = (
        datetime.strptime(vig.group(1), "%d/%m/%Y").date().isoformat()
        if vig
        else date.today().isoformat()
    )
    meta = {
        "tabela": "ncm",
        "fonte": URL,
        "vigencia": vigencia,
        "ato": dados.get("Ato", ""),
        "gerado_em": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    return meta, itens


def atualizar(destino: Path, origem: Path | None = None) -> Path:
    """Baixa (ou lê ``origem``) e grava ``destino/ncm.json.gz``."""
    bruto = origem.read_bytes() if origem else baixar()
    meta, itens = converter(bruto)
    return gravar_espelho(Path(destino) / "ncm.json.gz", meta, itens)
