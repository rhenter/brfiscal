# Contribuindo

Obrigado por ajudar! Algumas regras para manter a lib confiável:

1. **Dados só de fonte oficial.** Todo espelho em `src/brfiscal/dados/` deve ser gerado
   pelo importador em `src/brfiscal/fontes/`, nunca editado à mão. Informe a fonte e a
   vigência no PR.
2. **Nova tabela** = um módulo em `src/brfiscal/<tabela>.py` (modelo + funções) e um
   importador em `src/brfiscal/fontes/<tabela>.py`, com testes usando uma amostra pequena.
3. **Sinônimos** (`src/brfiscal/_sinonimos.py`): bem-vindos, desde que levem a palavras
   que existem no texto oficial. Inclua um teste de busca.
4. Nada de regra tributária de empresa específica (alíquotas, regimes, exceções).

```bash
uv sync
uv run pytest && uv run ruff check src tests && uv run ruff format --check src tests
```
