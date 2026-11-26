from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from brfiscal import DadosIndisponiveis, configurar
from brfiscal._tabela import diretorio_dados
from brfiscal.contrib.django.carga import CARREGADORES


class Command(BaseCommand):
    help = "Carrega (ou atualiza) as tabelas fiscais no banco a partir do espelho da lib."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("tabelas", nargs="*", help="ncm, cest (padrão: todas)")
        parser.add_argument(
            "--baixar",
            action="store_true",
            help="Baixa as tabelas oficiais antes de carregar (em $BRFISCAL_DADOS ou --destino).",
        )
        parser.add_argument("--destino", help="Diretório para os espelhos baixados.")

    def handle(
        self, *args: Any, tabelas: list[str], baixar: bool, destino: str | None, **opts: Any
    ) -> None:
        tabelas = tabelas or list(CARREGADORES)
        if desconhecidas := set(tabelas) - set(CARREGADORES):
            raise CommandError(f"Tabelas desconhecidas: {', '.join(sorted(desconhecidas))}")
        if baixar:
            alvo = Path(destino) if destino else diretorio_dados()
            if alvo is None:
                raise CommandError("Use --destino ou defina BRFISCAL_DADOS para --baixar.")
            from brfiscal.fontes import cest as fonte_cest
            from brfiscal.fontes import ncm as fonte_ncm

            fontes = {"ncm": fonte_ncm.atualizar, "cest": fonte_cest.atualizar}
            for nome in tabelas:
                self.stdout.write(f"Baixando {nome.upper()} para {alvo}...")
                fontes[nome](alvo)
            configurar(alvo)
        for nome in tabelas:
            try:
                total = CARREGADORES[nome]()
            except DadosIndisponiveis as exc:
                self.stderr.write(self.style.WARNING(f"{nome}: {exc}"))
                continue
            self.stdout.write(self.style.SUCCESS(f"{nome}: {total} registros carregados."))
