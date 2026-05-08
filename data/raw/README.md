# `data/raw/` — fontes primárias

Esta pasta contém os arquivos brutos das 13 fontes integradas ao master, exatamente
como foram baixados de cada portal/API. Todos os parsers (`src/arboviral/ingestion/`)
leem desta pasta para gerar `data/interim/*.parquet`.

`data/raw/` está **gitignored** (arquivos grandes, > 100 MB do limite GitHub).
Snapshot completo dos raws será disponibilizado no Zenodo com DOI permanente
(ver seção "Disponibilização" no fim deste documento).

## Inventário de fontes

| # | Pasta | Fonte | Como obter | Status |
|---|---|---|---|---|
| 1 | `sinan/` | DATASUS — DENGBR/ZIKABR/CHIKBR | scraper | automatizado |
| 2 | `nasa_power/` | NASA POWER API | scraper (embutido na ingestão) | automatizado |
| 3 | `esf/` | e-Gestor MS — APS/AB | scraper | automatizado |
| 4 | `mapbiomas/` | MapBiomas Coleção 10.1 | scraper | automatizado |
| 5 | `ibge_areas/` | IBGE — área territorial | scraper | automatizado |
| 6 | `febre_amarela/COB_VAC_FA.csv` | PNI/DATASUS — cobertura vacinal | scraper | automatizado |
| 7 | `febre_amarela/fa_casoshumanos_1994-2025.csv` | SVS/MS — casos humanos | curl manual | manual |
| 8 | `saude/` | DATASUS CNES/LT + SIM/DORES | FTP manual | manual |
| 9 | `ibge/` | IBGE SIDRA + Atlas PNUD | SIDRA web | manual |
| 10 | `idhm/` + `capag/` | Atlas PNUD + Tesouro Nacional | portal web | manual |
| 11 | `sinisa/` | SINISA — saneamento | portal web | manual |
| 12 | `munic/` | IBGE MUNIC | portal web | manual |
| 13 | `habitacao/` | IBGE SIDRA — favelas/aglomerados | SIDRA web | manual |

## Fontes automatizadas (rodar comando)

Os 6 comandos abaixo regeneram completamente as pastas auto-reproduzíveis. Idempotentes:
arquivos já presentes não são re-baixados (a menos que `--sobrescrever`).

```bash
# SINAN dengue/zika/chikungunya (FTP DATASUS, ~1 GB)
python -m arboviral.ingestion.sinan_ftp

# NASA POWER (API REST, ~50 MB, ~30 min)
python -m arboviral.ingestion.nasa_power

# ESF cobertura APS/AB (API e-Gestor, 132 arquivos JSON)
python -m arboviral.scraping.esf_coverage

# MapBiomas cobertura/uso da terra (1 XLSX ~30 MB)
python -m arboviral.scraping.mapbiomas

# IBGE — área territorial (1 XLS, ~5 MB)
python -m arboviral.scraping.ibge_areas

# PNI febre amarela — cobertura vacinal (1 CSV)
python -m arboviral.scraping.pni_febre_amarela
```

## Fontes manuais (baixar do portal)

### 7. Febre Amarela — casos humanos (SVS/MS)

- **URL**: https://dadosabertos.saude.gov.br/dataset/febre-amarela-em-humanos-e-primatas-nao-humanos
- **Arquivo direto** (atualizado periodicamente pela SVS):
  ```
  https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/Febre+Amarela/fa_casoshumanos_1994-2025.csv
  ```
- **Comando**:
  ```bash
  curl -sL "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/Febre+Amarela/fa_casoshumanos_1994-2025.csv" \
       -o data/raw/febre_amarela/fa_casoshumanos_1994-2025.csv
  ```
- **Encoding**: latin1 · separador `;`
- **Observação**: o nome do arquivo muda quando a SVS atualiza (incluí 2025+). Verificar no portal.

### 8. DATASUS — Saúde (CNES leitos + SIM óbitos)

- **Portal FTP**: ftp://ftp.datasus.gov.br/dissemin/publicos/
- **Arquivos esperados em `data/raw/saude/`**:
  - **Leitos hospitalares (CNES/LT)** — mensal, 2015–presente:
    ```
    /dissemin/publicos/CNES/200508_/Dados/LT/LTSP{AAMM}.dbc
    ```
    Padrão: `LTSP1501.dbc`, `LTSP1502.dbc`, ..., `LTSP2412.dbc` (~120 arquivos, ~50 MB total)
  - **Óbitos por causa (SIM/DORES)** — anual, 2015–presente:
    ```
    /dissemin/publicos/SIM/CID10/DORES/DOSP{AAAA}.dbc
    ```
    Padrão: `DOSP2015.dbc`, ..., `DOSP2024.dbc` (~10 arquivos, ~150 MB total)
- **Comando** (script auxiliar para automatizar — TODO):
  ```bash
  # Por enquanto, baixar manualmente via cliente FTP (FileZilla, lftp, curl)
  # Exemplo curl para um arquivo:
  curl -o data/raw/saude/LTSP2401.dbc \
       ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados/LT/LTSP2401.dbc
  ```
- **Formato**: `.dbc` (DBF comprimido) — descompactar via `pyreaddbc` (já em pyproject)

### 9. IBGE — PIB, população, Gini

- **Portal**: https://sidra.ibge.gov.br
- **Arquivos esperados em `data/raw/ibge/`**:
  - `tabela5938.xlsx` — PIB municipal a preços correntes (Mil R$), 2002–2023
    - SIDRA tabela 5938: https://sidra.ibge.gov.br/tabela/5938
    - Filtrar: Brasil (todos os municípios) · Anos: 2015–2023 · Variáveis: Produto Interno Bruto a preços correntes (Mil Reais)
  - `tabela6579.xlsx` — Estimativas populacionais, 2001–2025
    - SIDRA tabela 6579: https://sidra.ibge.gov.br/tabela/6579
    - Filtrar: Brasil (todos os municípios) · Anos: 2015–2025
  - `ginibr.xlsx` — Índice de Gini da renda domiciliar per capita, 1991/2000/2010
    - https://www.ibge.gov.br/estatisticas/sociais/trabalho/9221-sintese-de-indicadores-sociais.html
    - Ou via Atlas Brasil: http://www.atlasbrasil.org.br/

### 10. Socioeconômico — IDH-M + CAPAG

- **`data/raw/idhm/`**:
  - `IDHM_1991.csv`, `IDHM_2000.csv`, `IDHM_2010.csv`
  - **Fonte**: Atlas do Desenvolvimento Humano no Brasil (PNUD)
  - **Portal**: http://www.atlasbrasil.org.br/consulta
  - Exportar como CSV no formato inteli.gente: colunas `codigo_ibge, sigla, ano, variavel_valor`

- **`data/raw/capag/`**:
  - `capag-2018.xlsx` ... `capag_2025.xlsx` (nome varia por ano)
  - **Fonte**: Tesouro Nacional Transparente — Capacidade de Pagamento dos Municípios
  - **Portal**: https://www.tesourotransparente.gov.br/temas/estados-e-municipios/capacidade-de-pagamento-capag

### 11. SINISA — saneamento

- **Portal**: https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa
- **Arquivos esperados em `data/raw/sinisa/`** (anos 2023, 2024):
  - `SINISA_AGUA_Indicadores_Base Municipal_2023_V2.xlsx` (cobertura de água)
  - `SINISA_ESGOTO_Indicadores_Base Municipal_2023_V2.xlsx` (cobertura de esgoto)
  - `SINISA_AGUA_Indicadores_Base Municipal_2024.xlsx`
  - `SINISA_ESGOTO_Indicadores_Base Municipal_2024.xlsx`

### 12. IBGE MUNIC — vigilância e desastres

- **Portal**: https://www.ibge.gov.br/estatisticas/sociais/saude/10586-pesquisa-de-informacoes-basicas-municipais.html
- **Arquivos esperados em `data/raw/munic/`**:
  - `Base_MUNIC_2018_xlsx_20201103.xlsx` — abas "Saúde" (MSAU28, MSAU541-543)
  - `Base_MUNIC_2020.xlsx` — abas "Gestão de riscos" e "Meio ambiente"
- **Documentação dos questionários** (importante para auditar respostas):
  - https://www.ibge.gov.br/estatisticas/sociais/saude/10586-pesquisa-de-informacoes-basicas-municipais.html?=&t=downloads
  - Pasta `Documentação` → questionário PDF

### 13. IBGE — habitação (favelas/aglomerados subnormais)

- **Portal**: https://sidra.ibge.gov.br
- **Arquivos esperados em `data/raw/habitacao/`** (formato XLSX SIDRA):
  - `tabela3379.xlsx` — Aglomerados subnormais por município (Censo 2010)
    - https://sidra.ibge.gov.br/tabela/3379
  - `tabela3381.xlsx` — População em aglomerados subnormais (Censo 2010)
    - https://sidra.ibge.gov.br/tabela/3381
  - `tabela9883.xlsx` — Favelas e comunidades urbanas (Censo 2022)
    - https://sidra.ibge.gov.br/tabela/9883
  - `tabela9900.xlsx` — População em favelas e comunidades urbanas (Censo 2022)
    - https://sidra.ibge.gov.br/tabela/9900

## Disponibilização (Zenodo — TODO)

Para garantir reprodutibilidade científica do trabalho de IC, todo o conteúdo
de `data/raw/` será depositado no Zenodo, gerando um DOI permanente.

Plano:

1. **Após download completo de todas as fontes**, gerar `MANIFEST.sha256` com hash de cada arquivo:
   ```bash
   cd data/raw && find . -type f -not -name 'README.md' -not -name 'MANIFEST.sha256' \
       -exec sha256sum {} \; | sort > MANIFEST.sha256
   ```
2. **Empacotar** (sem incluir o próprio MANIFEST no tar):
   ```bash
   tar -czf arboviral_data_raw_v1.tar.gz -C data raw/
   ```
3. **Upload no Zenodo** (https://zenodo.org), preencher:
   - Título: "Raw data for arboviral outbreak prediction in São Paulo (2015–2025)"
   - Autores: Lázaro P. Vinaud Neto, André C. P. L. F. de Carvalho
   - Tipo: Dataset
   - Licença: CC BY 4.0 (ou compatível com licenças das fontes originais)
4. **Citar o DOI** retornado no `README.md` raiz do repositório e na seção
   "Disponibilidade dos dados" do paper.

Arquivo `MANIFEST.sha256` deve ser **versionado no git** — assim qualquer pessoa
que baixar o tarball do Zenodo pode verificar a integridade.
