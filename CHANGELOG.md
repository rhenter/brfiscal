# Changelog

## 0.1.0 (em desenvolvimento)

- NCM: espelho da tabela vigente (Res. Gecex nº 926/2026, vigente em 26/11/2026), validação,
  formatação, hierarquia, descrição completa e busca por descrição com sinônimos.
- CEST: modelo, validação NCM↔CEST (um NCM pode ter vários CESTs) e importação via CSV.
- CLI `brfiscal info | atualizar | buscar`.
- Integração Django opcional: models, migration, comando `brfiscal_carregar`,
  `NcmField`, `CestField` e validadores.
