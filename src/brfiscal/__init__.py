"""brfiscal - tabelas fiscais brasileiras com espelho local versionado.

Tabelas disponíveis: :mod:`brfiscal.ncm`, :mod:`brfiscal.cest`.
"""

from . import cest, ncm
from ._tabela import DadosIndisponiveis, Metadados, Resultado, configurar

__version__ = "0.1.0.dev0"

__all__ = [
    "DadosIndisponiveis",
    "Metadados",
    "Resultado",
    "__version__",
    "cest",
    "configurar",
    "ncm",
]
