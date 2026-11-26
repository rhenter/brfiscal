"""Importação da tabela CEST (Anexos II a XXVI do Convênio ICMS 142/2018).

O Confaz publica os anexos só como páginas HTML (sem CSV/JSON oficial). O fluxo é:

1. ``converter_csv``: lê um CSV intermediário com as colunas
   ``cest;ncm;descricao;segmento;item`` (uma linha por CEST, NCMs separados por espaço);
2. ``converter_html``: (em construção) extrai o mesmo conteúdo direto da página do Confaz.
"""

from __future__ import annotations

import csv
import io
import re
from datetime import date, datetime, timezone
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
