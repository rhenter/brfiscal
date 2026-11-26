"""brfiscal - tabelas fiscais brasileiras com espelho local versionado.

Tabelas disponíveis: :mod:`brfiscal.ncm`, :mod:`brfiscal.cest`.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

from . import cest, ncm
from ._tabela import DadosIndisponiveis, Metadados, Resultado, configurar

try:
    __version__ = _version("brfiscal")
except PackageNotFoundError:  # rodando direto do código-fonte, sem instalar
    __version__ = "0.0.0"

__all__ = [
    "DadosIndisponiveis",
    "Metadados",
    "Resultado",
    "__version__",
    "cest",
    "configurar",
    "ncm",
]
