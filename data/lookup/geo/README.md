# Assets geográficos para o app

Estes arquivos são consumidos pelo app Streamlit (`app/screens/mapa.py` +
`app/lib/agregacao_geo.py`) para renderizar o mapa hierárquico de SP em
três granularidades. O core (`src/arboviral/`) NÃO depende deles.

## Conteúdo

| Arquivo | Tamanho | Conteúdo |
|---|---:|---|
| `municipios_sp.geojson` | ~3.5 MB | 645 polígonos municipais de SP (IBGE 2020, simplificados). Não usado pelo app hoje (mantemos scatter no nível municipal), versionado pra uso futuro (ex.: choropleth de município). |
| `drs_sp.geojson` | ~1.8 MB | 17 polígonos dos Departamentos Regionais de Saúde (SES-SP). Gerado por *dissolve* dos polígonos municipais agrupados por DRS. Propriedade `id` é o numeral romano (I, II, …, XVII). |
| `regioes_intermediarias_sp.geojson` | ~650 KB | 11 polígonos das Regiões Geográficas Intermediárias (IBGE 2017). Direto do IBGE via `geobr.read_intermediate_region`. Propriedade `codigo` é o código IBGE de 4 dígitos. |
| `municipios_sp_lookup.csv` | ~61 KB | 645 linhas. Mapa município → drs, rgi, lat, lon (centroide). |

## Fontes

- **Municípios e RGI**: pacote Python `geobr` (IPEA), que distribui shapes
  oficiais do IBGE. Versão usada: municípios IBGE 2020 simplificados; RGI
  IBGE 2017 (criadas para substituir as antigas mesorregiões).
- **DRS**: scraping da página oficial da SES-SP em
  https://saude.sp.gov.br/ses/institucional/departamentos-regionais-de-saude/
  feito em 2026-05-09. Cada DRS tem uma subpágina com a lista de seus
  municípios. As listas foram coladas em `scripts/gerar_geo_lookup.py` e
  casadas com o nome do IBGE via normalização (uppercase + sem acentos);
  4 renomeações conhecidas foram tratadas (Embu → Embu das Artes,
  Florínia → Florínea, Ilha Bela → Ilhabela, Santo Antônio Da → De Posse).

## Como regenerar

```bash
source .venv/bin/activate
pip install geopandas geobr     # deps temporárias
python scripts/gerar_geo_lookup.py
pip uninstall geopandas geobr   # opcional
```

**Não estão no `pyproject.toml`** — só são necessárias pra rodar o script
de regeneração. O app em runtime lê os arquivos resultantes (json/csv) e
não precisa de geopandas.

## Quando regenerar

- Mudança na lista de municípios por DRS (rara — exigiria decreto estadual)
- Atualização da divisão IBGE (RGI poderia mudar; última mudança foi 2017)
- Mudança de método de simplificação dos polígonos (ex.: trocar `simplified=True`
  do `geobr` por um threshold customizado)

Os arquivos atuais foram gerados em **2026-05-09** com `geobr` ≥ 0.2.
