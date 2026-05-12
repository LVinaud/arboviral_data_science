# Scripts pontuais

Scripts que **não** fazem parte do pipeline reproducível do projeto — são
usados uma vez (ou eventualmente) para gerar assets que ficam versionados.
Por isso suas dependências **não** estão no `pyproject.toml`: instale só
quando precisar rodar e desinstale depois para manter o venv enxuto.

## `gerar_geo_lookup.py`

Gera os arquivos em `data/lookup/geo/` consumidos pelo mapa do app:
geojsons de municípios / DRS / regiões intermediárias + CSV de lookup
município → DRS → RGI.

```bash
source .venv/bin/activate
pip install geopandas geobr
python scripts/gerar_geo_lookup.py
pip uninstall geopandas geobr
```

Detalhes em [`data/lookup/geo/README.md`](../data/lookup/geo/README.md).

## Diretrizes para adicionar scripts aqui

- Documentar a finalidade no docstring do módulo.
- Listar dependências extras explicitamente no docstring (já que não vão
  pro `pyproject.toml`).
- Salvar os artefatos resultantes em `data/lookup/`, `data/processed/` ou
  similar — nunca dentro de `scripts/` (scripts são código, não dados).
- Idempotente quando possível: rodar duas vezes não deve quebrar.
