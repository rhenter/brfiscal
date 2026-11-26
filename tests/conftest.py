from pathlib import Path

import pytest

import brfiscal
from brfiscal.fontes import cest as fonte_cest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True, scope="session")
def dados_cest_de_teste(tmp_path_factory):
    """CEST real ainda não está embutido; os testes usam uma amostra fictícia (códigos 99...)."""
    destino = tmp_path_factory.mktemp("dados")
    fonte_cest.atualizar_de_csv(destino, FIXTURES / "cest_amostra.csv", vigencia="2026-01-01")
    brfiscal.configurar(destino)
    yield destino
    brfiscal.configurar(None)
