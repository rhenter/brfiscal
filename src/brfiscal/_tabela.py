"""Infraestrutura comum a todas as tabelas: carga do espelho, metadados e busca."""

from __future__ import annotations

import gzip
import json
import math
import os
from collections import defaultdict
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Generic, TypeVar

from ._texto import STOPWORDS, normalizar, tokens

T = TypeVar("T")

#: Variável de ambiente com um diretório de espelhos atualizados
#: (gerados por ``brfiscal atualizar``). Se o arquivo da tabela existir lá,
#: ele tem prioridade sobre o espelho embutido no pacote.
ENV_DIRETORIO = "BRFISCAL_DADOS"

_diretorio_dados: Path | None = None


class DadosIndisponiveis(RuntimeError):
    """O espelho da tabela não está embutido nem foi baixado."""


def configurar(diretorio: str | os.PathLike[str] | None) -> None:
    """Define (ou limpa, com ``None``) o diretório de espelhos atualizados."""
    global _diretorio_dados
    _diretorio_dados = Path(diretorio) if diretorio is not None else None
    for tabela in _REGISTRO.values():
        tabela.recarregar()


def diretorio_dados() -> Path | None:
    if _diretorio_dados is not None:
        return _diretorio_dados
    env = os.environ.get(ENV_DIRETORIO)
    return Path(env) if env else None


@dataclass(frozen=True)
class Metadados:
    """De onde veio o espelho e a partir de quando vale."""

    tabela: str
    fonte: str
    vigencia: str
    ato: str = ""
    gerado_em: str = ""
    total: int = 0

    @classmethod
    def de_dict(cls, dados: dict[str, Any]) -> Metadados:
        campos = {k: dados[k] for k in cls.__dataclass_fields__ if k in dados}
        return cls(**campos)


@dataclass(frozen=True)
class Resultado(Generic[T]):
    """Um item encontrado na busca, com pontuação de 0 a 1 (relativa à consulta)."""

    item: T
    pontuacao: float


def ler_espelho(arquivo: Path) -> dict[str, Any]:
    with gzip.open(arquivo, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def gravar_espelho(arquivo: Path, meta: dict[str, Any], itens: list[dict[str, Any]]) -> Path:
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    meta = {**meta, "total": len(itens)}
    with gzip.open(arquivo, "wt", encoding="utf-8", compresslevel=9) as fh:
        json.dump({"meta": meta, "itens": itens}, fh, ensure_ascii=False, separators=(",", ":"))
    return arquivo


_REGISTRO: dict[str, Tabela[Any]] = {}


class Tabela(Generic[T]):
    """Tabela carregada sob demanda a partir de um espelho ``<nome>.json.gz``."""

    def __init__(
        self,
        nome: str,
        fabrica: Callable[[dict[str, Any]], T],
        chave: Callable[[T], str],
        texto_busca: Callable[[T], list[tuple[str, float]]],
        filtro_busca: Callable[[T], bool] | None = None,
        sinonimos: dict[str, str] | None = None,
    ) -> None:
        self.nome = nome
        self._fabrica = fabrica
        self._chave = chave
        self._texto_busca = texto_busca
        self._filtro_busca = filtro_busca
        self._sinonimos = {normalizar(k): v for k, v in (sinonimos or {}).items()}
        self._itens: dict[str, T] | None = None
        self._meta: Metadados | None = None
        self._indice: dict[str, dict[str, float]] | None = None
        self._vocab: list[str] = []
        _REGISTRO[nome] = self

    # carga ---------------------------------------------------------------
    @property
    def arquivo(self) -> Path:
        externo = diretorio_dados()
        if externo is not None and (externo / f"{self.nome}.json.gz").exists():
            return externo / f"{self.nome}.json.gz"
        return Path(str(resources.files("brfiscal") / "dados" / f"{self.nome}.json.gz"))

    def recarregar(self) -> None:
        self._itens = None
        self._meta = None
        self._indice = None

    def _carregar(self) -> dict[str, T]:
        if self._itens is None:
            arquivo = self.arquivo
            if not arquivo.exists():
                raise DadosIndisponiveis(
                    f"Espelho da tabela {self.nome!r} não encontrado. "
                    f"Rode `brfiscal atualizar {self.nome}`."
                )
            bruto = ler_espelho(arquivo)
            self._meta = Metadados.de_dict(bruto["meta"])
            itens = (self._fabrica(d) for d in bruto["itens"])
            self._itens = {self._chave(i): i for i in itens}
        return self._itens

    @property
    def metadados(self) -> Metadados:
        self._carregar()
        assert self._meta is not None
        return self._meta

    def __iter__(self) -> Iterator[T]:
        return iter(self._carregar().values())

    def __len__(self) -> int:
        return len(self._carregar())

    def obter(self, chave: str) -> T | None:
        return self._carregar().get(chave)

    # busca ---------------------------------------------------------------
    def _montar_indice(self) -> dict[str, dict[str, float]]:
        if self._indice is None:
            indice: dict[str, dict[str, float]] = defaultdict(dict)
            for item in self._carregar().values():
                if self._filtro_busca and not self._filtro_busca(item):
                    continue
                chave = self._chave(item)
                for texto, peso in self._texto_busca(item):
                    for tok in tokens(texto):
                        atual = indice[tok].get(chave, 0.0)
                        indice[tok][chave] = max(atual, peso)
            self._indice = dict(indice)
            self._vocab = sorted(self._indice)
        return self._indice

    def _expandir(self, tok: str) -> list[tuple[str, float]]:
        """Termo exato, ou termos que começam com ele (abreviações: 'bisc' -> 'biscoito')."""
        indice = self._montar_indice()
        if tok in indice:
            return [(tok, 1.0)]
        if len(tok) < 3:
            return []
        from bisect import bisect_left

        i = bisect_left(self._vocab, tok)
        saida = []
        while i < len(self._vocab) and self._vocab[i].startswith(tok):
            saida.append((self._vocab[i], 0.8))
            i += 1
        return saida

    def _consulta(self, texto: str) -> list[list[tuple[list[str], float]]]:
        """Cada palavra da consulta vira um grupo de alternativas.

        Uma alternativa é uma lista de termos que precisam aparecer *todos* no item
        (a própria palavra, ou a expressão sinônima, com peso menor). Sinônimos de
        duas palavras ("creme dental") substituem as duas.
        """
        palavras = [p for p in normalizar(texto).split() if p not in STOPWORDS]
        grupos: list[list[tuple[list[str], float]]] = []
        i = 0
        while i < len(palavras):
            par = " ".join(palavras[i : i + 2])
            if i + 1 < len(palavras) and par in self._sinonimos:
                grupos.append([(tokens(self._sinonimos[par]), 0.9)])
                i += 2
                continue
            proprios = tokens(palavras[i])
            if proprios:
                grupo = [(proprios, 1.0)]
                if extra := self._sinonimos.get(palavras[i]):
                    grupo.append((tokens(extra), 0.9))
                grupos.append(grupo)
            i += 1
        unicos: list[list[tuple[list[str], float]]] = []
        for g in grupos:
            if g not in unicos:
                unicos.append(g)
        return unicos

    def _casar(self, termos: list[str]) -> dict[str, float]:
        """Itens que contêm todos os termos (com expansão por prefixo) e seu peso."""
        indice = self._montar_indice()
        resultado: dict[str, float] | None = None
        for termo in termos:
            atual: dict[str, float] = {}
            for t, fator in self._expandir(termo):
                for chave, peso in indice[t].items():
                    atual[chave] = max(atual.get(chave, 0.0), peso * fator)
            if resultado is None:
                resultado = atual
            else:
                resultado = {c: min(v, atual[c]) for c, v in resultado.items() if c in atual}
            if not resultado:
                return {}
        return resultado or {}

    def buscar(self, texto: str, limite: int = 10) -> list[Resultado[T]]:
        """Busca por descrição (ex.: nome do produto). Retorna sugestões, não verdade absoluta."""
        consulta = self._consulta(texto)
        if not consulta:
            return []
        total = max(len(self._carregar()), 1)
        pontos: dict[str, float] = defaultdict(float)
        maximo = 0.0
        for grupo in consulta:
            melhor: dict[str, float] = {}
            for termos, fator in grupo:
                for chave, peso in self._casar(termos).items():
                    melhor[chave] = max(melhor.get(chave, 0.0), peso * fator)
            if not melhor:
                continue  # palavra desconhecida (marca, gramatura): não penaliza
            idf = math.log(1 + total / len(melhor))
            maximo += idf
            for chave, valor in melhor.items():
                pontos[chave] += valor * idf
        if not pontos or maximo == 0:
            return []
        itens = self._carregar()
        ordenados = sorted(pontos.items(), key=lambda kv: (-kv[1], kv[0]))[:limite]
        return [Resultado(itens[c], round(p / maximo, 4)) for c, p in ordenados]
