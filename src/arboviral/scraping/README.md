# `scraping/` — Coleta de dados externos

Scripts que **baixam dados brutos** de fontes públicas para `data/raw/<fonte>/`.
Não fazem parsing nem agregação — essa é responsabilidade de
[`src/arboviral/ingestion/`](../ingestion/).

> Apesar do nome "scraping", a maioria desses scripts é simplesmente um
> **download documentado** (URLs estáveis, formato CSV/XLSX). True
> webscraping (parsing de HTML/PDF) só é necessário para fontes como o
> LIRAa, que publicam em boletins PDF da SES-SP.

## Por que existe esse módulo?

1. **Reprodutibilidade científica**: o "como" da obtenção dos dados é parte
   da metodologia. Sem scripts versionados, "como foi obtido" vira folclore.
2. **Auditoria**: qualquer pessoa (você daqui 6 meses, orientador, revisor
   de artigo) consegue refazer o download e validar.
3. **Separação de responsabilidades**: download é uma operação distinta de
   parsing — esse módulo só faz a primeira.

## Convenções

- Cada fonte tem **um arquivo Python** com nome curto e descritivo
  (ex.: `ibge_areas.py`, `mapbiomas.py`, `liraa.py`).
- Cada script é executável: `python -m arboviral.scraping.<fonte>`.
- Saída sempre em `data/raw/<fonte>/<arquivo>.<ext>` — caminho documentado
  no docstring do módulo.
- Output é gitignored (`data/raw/` está no `.gitignore`); apenas os
  scripts vão para o git.
- Dependências externas: usar bibliotecas leves (`requests`, `urllib`).
  Selenium / browser automation só se for inevitável.

## Status das fontes

| Fonte | Script | Última coleta | Output bruto | Parser | Status |
|---|---|---|---|---|---|
| IBGE — Áreas dos municípios | `ibge_areas.py` | 2026-05 | `data/raw/ibge_areas/AR_BR_RG_UF_RGINT_RGI_MUN_2024.xls` | `ingestion/densidade.py` | ✅ |
| MapBiomas — uso do solo | `mapbiomas.py` | — | — | — | ⏳ |
| Cobertura ESF (e-Gestor AB) | `esf_coverage.py` | — | — | — | ⏳ |
| Vacinação FA (DATASUS PNI) | `pni_febre_amarela.py` | — | — | — | ⏳ |
| LIRAa (SES-SP) | `liraa_sp.py` | — | — | — | ⏳ |
| SIH-SUS (internações) | `sih_arboviroses.py` | — | — | — | ⏳ |
| Latência SINAN (subnotificação) | (recálculo) | — | reusa DBC do SINAN | atualização em `ingestion/sinan.py` | ⏳ |

## Como rodar

```bash
python -m arboviral.scraping.ibge_areas       # baixa a última versão
python -m arboviral.scraping.mapbiomas        # baixa as tabelas municipais
# ...
```

Após o download, os scripts em `src/arboviral/ingestion/` parseiam e
geram os parquets em `data/interim/`.
