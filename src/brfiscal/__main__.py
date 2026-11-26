"""Linha de comando: ``brfiscal info``, ``brfiscal atualizar ncm``, ``brfiscal buscar ncm "x"``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import DadosIndisponiveis, cest, ncm
from ._tabela import diretorio_dados

TABELAS = {"ncm": ncm, "cest": cest}


def _info() -> int:
    for nome, mod in TABELAS.items():
        try:
            m = mod.metadados()
            print(f"{nome}: {m.total} itens, vigente em {m.vigencia} ({m.ato}) - {m.fonte}")
        except DadosIndisponiveis:
            print(f"{nome}: sem dados (rode `brfiscal atualizar {nome}`)")
    return 0


def _atualizar(args: argparse.Namespace) -> int:
    destino = Path(args.destino) if args.destino else diretorio_dados()
    if destino is None:
        print("Informe --destino ou defina BRFISCAL_DADOS.", file=sys.stderr)
        return 2
    if args.tabela == "ncm":
        from .fontes import ncm as fonte

        arquivo = fonte.atualizar(destino, Path(args.origem) if args.origem else None)
    else:
        from .fontes import cest as fonte_cest

        origem = Path(args.origem) if args.origem else None
        if origem and origem.suffix.lower() == ".csv":
            arquivo = fonte_cest.atualizar_de_csv(destino, origem)
        else:
            arquivo = fonte_cest.atualizar(destino, origem)
    print(f"Gravado {arquivo}")
    return 0


def _buscar(args: argparse.Namespace) -> int:
    for r in TABELAS[args.tabela].buscar(args.texto, limite=args.limite):
        item = r.item
        print(f"{item.codigo_formatado:<12} {r.pontuacao:>5.2f}  {item.descricao}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="brfiscal")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("info", help="mostra versão/vigência dos espelhos")
    a = sub.add_parser("atualizar", help="baixa a tabela oficial e grava o espelho")
    a.add_argument("tabela", choices=sorted(TABELAS))
    a.add_argument("--destino", help="diretório de saída (padrão: $BRFISCAL_DADOS)")
    a.add_argument("--origem", help="arquivo local em vez de baixar")
    b = sub.add_parser("buscar", help="busca por descrição")
    b.add_argument("tabela", choices=sorted(TABELAS))
    b.add_argument("texto")
    b.add_argument("--limite", type=int, default=10)
    args = p.parse_args(argv)
    if args.cmd == "info":
        return _info()
    if args.cmd == "atualizar":
        return _atualizar(args)
    return _buscar(args)


if __name__ == "__main__":
    raise SystemExit(main())
