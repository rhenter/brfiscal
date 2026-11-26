"""Carrega o espelho da lib nas tabelas do banco (upsert + desativa o que saiu)."""

from __future__ import annotations

from datetime import date

from django.db import transaction

from brfiscal import cest as cest_mod
from brfiscal import ncm as ncm_mod
from brfiscal._tabela import Metadados

from .models import Cest, CestNcm, Ncm, VersaoTabela

LOTE = 2000


def _versao(nome: str, meta: Metadados) -> None:
    VersaoTabela.objects.update_or_create(
        tabela=nome,
        defaults={
            "vigencia": date.fromisoformat(meta.vigencia),
            "ato": meta.ato,
            "fonte": meta.fonte,
            "total": meta.total,
        },
    )


@transaction.atomic
def carregar_ncm() -> int:
    itens = ncm_mod.todos()
    # Tudo que não vier no espelho atual fica inativo; o upsert reativa o que veio.
    Ncm.objects.update(ativo=False)
    objs = [
        Ncm(
            codigo=n.codigo,
            descricao=n.descricao,
            descricao_completa=n.descricao_completa,
            inicio=n.inicio,
            fim=n.fim,
            ato=n.ato,
            ativo=True,
        )
        for n in itens
    ]
    Ncm.objects.bulk_create(
        objs,
        batch_size=LOTE,
        update_conflicts=True,
        unique_fields=["codigo"],
        update_fields=["descricao", "descricao_completa", "inicio", "fim", "ato", "ativo"],
    )
    _versao("ncm", ncm_mod.metadados())
    return len(objs)


@transaction.atomic
def carregar_cest() -> int:
    itens = list(cest_mod.tabela())
    Cest.objects.bulk_create(
        [
            Cest(codigo=c.codigo, descricao=c.descricao, segmento=c.segmento, item=c.item)
            for c in itens
        ],
        batch_size=LOTE,
        update_conflicts=True,
        unique_fields=["codigo"],
        update_fields=["descricao", "segmento", "item", "ativo"],
    )
    # CestNcm é espelho puro da tabela: recria inteiro.
    CestNcm.objects.all().delete()
    CestNcm.objects.bulk_create(
        [CestNcm(cest_id=c.codigo, ncm_prefixo=n) for c in itens for n in c.ncms],
        batch_size=LOTE,
    )
    _versao("cest", cest_mod.metadados())
    return len(itens)


CARREGADORES = {"ncm": carregar_ncm, "cest": carregar_cest}
