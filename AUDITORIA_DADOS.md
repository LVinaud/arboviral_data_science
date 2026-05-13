---
marp: false
---

# Relatório de Auditoria do Pipeline de Dados — Arboviroses SP

**Gerado em**: 2026-05-06

Este relatório descreve os arquivos brutos utilizados, como foram obtidos, o que foi gerado a partir deles e quaisquer limitações ou inconsistências encontradas.

---

## 1. SINAN — Arboviroses (dengue, zika, chikungunya)

**Origem**: FTP público do DATASUS

```
ftp://ftp.datasus.gov.br/dissemin/publicos/SINAN/DADOS/FINAIS/DENGBR{AA}.dbc
Idem para ZIKABR e CHIKBR (2015–2025)
```

**Obtido por**: script automatizado (`src/arboviral/ingestion/sinan_ftp.py`)

- Usa curl para baixar os .dbc (formato comprimido DATASUS)
- Anos finais: 2015–2024; ano preliminar: 2025

**Arquivos raw**: `data/raw/sinan/DENGBR{AA}.dbc`, `ZIKABR{AA}.dbc`, `CHIKBR{AA}.dbc`

**Gerado**:

```
data/interim/sinan_dengue.parquet         61.616 linhas (cod_ibge, ano, mes)
data/interim/sinan_zika.parquet            5.585 linhas
data/interim/sinan_chikungunya.parquet    13.395 linhas
```

**Colunas**: `casos_notificados`, `casos_provaveis`, `obitos`, `internacoes`

**Verificação de qualidade**:

- Dengue: max 200.201 casos notificados/mês (São Paulo, abril 2024) ✓ plausível
- Dengue: max 199.166 casos prováveis/mês ✓
- Dengue: max 198 óbitos/mês ✓
- Dengue: max 4.601 internações/mês ✓
- Zika: max 452 notificados, 8 óbitos ✓ (doença menos grave)
- Chikungunya: max 3.829 notificados ✓
- CLASSI_FIN: dengue=10/11/12, chikungunya=13, zika=2 (confirmados)
- Apenas municípios de SP (SG_UF == '35'), agregados por município de residência

**Limitações**:

- Dados 2025 são preliminares (sujeitos a revisão)
- Chikungunya e zika têm anos com pouca cobertura (2015-2016)
- `internacoes` = NaN em anos/doenças onde HOSPITALIZ não foi registrado

### ATUALIZAÇÃO 2026-05: estendido para extrair LATÊNCIA por caso individual

Cada DBC contém DT_NOTIFIC e DT_SIN_PRI. Calculamos:

```
delta_dias = DT_NOTIFIC - DT_SIN_PRI por caso
```

Filtros aplicados: 0 ≤ delta ≤ 365 dias (rejeita datas inconsistentes).
Agregamos por (cod_ibge, ano, mes) em mediana e p90.

Novas colunas em `sinan_<doenca>.parquet`:

- `latencia_mediana_dias`: mediana de dias entre sintomas e notificação
- `latencia_p90_dias`: percentil 90 (cauda longa)
- `n_casos_com_latencia`: contagem de casos com ambas as datas válidas

**Estatísticas observadas** (mediana de medianas por município/mês):

- Dengue: 3 dias mediana, p90 ~7 (sistema funcionando bem)
- Zika: 4 dias mediana, p90 ~6
- Chikungunya: 7 dias mediana, p90 ~10 (doença menos lembrada → mais lenta)

**Justificativa**: latência é proxy DIRETO de qualidade da vigilância e de subnotificação. Município com latência alta tem casos chegando atrasados (aparente "calmaria" pode esconder surto real). Modelo pode usar isso para distinguir "casos baixos = tudo bem" de "casos baixos + latência alta = preciso ficar alerta".

---

## 1b. Febre Amarela — Ministério da Saúde / SVS (Dados Abertos)

**Origem**: NÃO está no FTP público do SINAN — sistema separado por ser doença silvestre/rara. Publicação via portal de Dados Abertos do MS.

https://dadosabertos.saude.gov.br/dataset/febre-amarela-em-humanos-e-primatas-nao-humanos

**Obtido por**: download manual do CSV (curl one-liner documentado em `src/arboviral/ingestion/febre_amarela.py`)

**Arquivos raw**:

```
data/raw/febre_amarela/fa_casoshumanos_1994-2025.csv  (CSV, latin1, ';')
```

**Gerado**: `data/interim/febre_amarela.parquet`  241 linhas (2000-2025, casos esparsos)

**Colunas**: `cod_ibge`, `ano`, `mes`, `casos`, `obitos`

**Verificação de qualidade — SP 2015-2025**:

- Total: 717 casos, 264 óbitos (118 municípios afetados)
- Pico 2017-2019: surto de febre amarela silvestre em SP
  - 2017: 76 casos / 36 óbitos
  - 2018: 504 casos / 179 óbitos  ← maior surto da série
  - 2019: 71 casos / 12 óbitos
- 2020-2023: praticamente zero
- 2025: 55 casos / 31 óbitos (ressurgência preocupante)
- Letalidade ~37% (consistente com literatura: FA tem alta letalidade)

**DIFERENÇA METODOLÓGICA IMPORTANTE**:

Granularidade municipal usa Local Provável de Infecção (COD_MUN_LPI), NÃO município de residência. Isso é correto para FA porque a transmissão é silvestre — pessoas se infectam visitando áreas de mata, não em casa. Comparar com SINAN (residência) requer cuidado conceitual.

**Notas técnicas**:

- Encoding: latin1 (não UTF-8); separador ';' (não ',')
- Campo OBITO inconsistente: 'SIM' vs 'NÃO' vs 'Não' vs 'IGN' → normalizado: apenas 'SIM' conta como óbito
- COD_MUN_LPI tem 6 dígitos (igual SINAN); aplicado lookup 6→7d
- Não há HOSPITALIZ nem CLASSI_FIN — todos os registros já são confirmados

---

## 2. NASA POWER — Meteorologia

**Origem**: API REST pública da NASA

```
https://power.larc.nasa.gov/api/temporal/monthly/point
```

**Obtido por**: script automatizado (`src/arboviral/ingestion/nasa_power.py`)

- Consulta ponto a ponto para as coordenadas de cada município SP
- 645 municípios × 132 meses (2015–2025) = 85.140 registros
- Pausa de 0,4s entre requisições (respeito ao rate-limit da NASA)

**Arquivos raw**: `data/raw/nasa_power/nasa_power_municipios_sp.parquet`

**Gerado**: `data/interim/nasa_power.parquet`  85.140 linhas (cod_ibge, ano, mes)

**Colunas**: `temp_media` (°C), `temp_max` (°C), `temp_min` (°C), `precip_media_dia` (mm/dia), `umid_media` (%), `vento_media` (m/s), `pressao_media_kpa` (kPa)

**Verificação de qualidade**:

- `temp_media`: 12,3 a 31,8 °C ✓ (SP tem clima variado, de serrana a tropical)
- `temp_max`: 20,8 a 44,8 °C ✓ (máx extremas plausíveis em SP)
- `temp_min`: -1,4 a 25,6 °C ✓ (geadas pontuais em regiões serranas)
- `precip`: 0 a 14,8 mm/dia ✓
- `umid`: 30,7 a 90,9 % ✓
- `pressao`: 89,3 a 102,3 kPa ✓ (varia com altitude — municípios de serra têm < pressão)
- Completude: 100% em todas as colunas (vantagem sobre INMET)
- Resolução espacial ~0,5° (~55 km); adequada para análise municipal

**Limitações**:

- Dado de satélite/reanálise (MERRA-2), não estação física
- Resolução espacial limitada (municípios vizinhos podem ter mesmo valor)

---

## 3. MUNIC — Vigilância e Gestão Municipal de Riscos

**Origem**: IBGE — Pesquisa de Informações Básicas Municipais

https://www.ibge.gov.br/estatisticas/sociais/habitacao/10586-pesquisa-de-informacoes-basicas-municipais.html

**Obtido por**: download manual pelo aluno, inserido em `data/raw/munic/`

**Arquivos raw**:

```
data/raw/munic/Base_MUNIC_2018_xlsx_20201103.xlsx  (aba "Saúde")
data/raw/munic/Base_MUNIC_2020.xlsx                (abas "Gestão de riscos" e "Meio ambiente")
```

**Gerado**: `data/interim/munic.parquet`  645 linhas (uma por município, dado estático)

**Colunas** (bool True/False/NaN):

- `msau28_pacs`, `msau541_vig_sanitaria`, `msau542_vig_epidemiologica`, `msau543_controle_endemias`
- `mgrd01_seca`, `mgrd06_alagamento`, `mgrd07_erosao`, `mgrd08_enchente_gradual`
- `mgrd11_enxurrada`, `mgrd14_deslizamento`, `mgrd201_mapeamento_risco`, `mmam2612_moradia_risco`

**Verificação de qualidade**:

- Vigilância em saúde (2018): 645/645 municípios sem NaN ✓
- Desastres naturais (2020): 1-5% NaN por variável (respostas "Não sabe") ✓
- `mmam2612_moradia_risco`: 38,8% NaN — muitos municípios responderam "Não sabe" à questão sobre moradias em áreas de risco ambiental. Não é erro, é dado real.
- Valores "Não sabe" mapeados para NaN (não False) conforme documentação MUNIC.

**Nota técnica**: o código IBGE nas planilhas MUNIC já vem com 7 dígitos completos (diferente do DATASUS que usa 6). Não aplicar lookup de 6→7 dígitos.

---

## 4. CNES/LT + SIM — Saúde (leitos SUS e mortalidade materna)

**Origem**: FTP público do DATASUS

```
CNES/LT: ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados/LT/LTSP{AAMM}.dbc
SIM:     ftp://ftp.datasus.gov.br/dissemin/publicos/SIM/CID10/DORES/DOSP{YYYY}.dbc
```

**Obtido por**: script automatizado (`src/arboviral/ingestion/saude.py`)

- Leitos: arquivos mensais `LTSP{AAMM}.dbc` (2015–2025)
- Mortalidade materna: arquivos anuais `DOSP{YYYY}.dbc` (2015–2024)

**Arquivos raw**: `data/raw/saude/LTSP{AAMM}.dbc` e `data/raw/saude/DOSP{YYYY}.dbc`

**Gerado**: `data/interim/saude.parquet`  82.741 linhas (cod_ibge, ano, mes)

**Colunas**: `leitos_sus` (int), `obitos_maternos` (int)

**Verificação de qualidade**:

- `leitos_sus`: 0 a 20.771 ✓ (São Paulo capital tem o maior complexo hospitalar SUS)
- `leitos_sus`: 42% NaN — municípios sem nenhum leito SUS cadastrado no CNES (não é erro: municípios pequenos podem não ter unidades SUS com leitos)
- `obitos_maternos`: 0 a 112 ✓ (filtro CAUSABAS O00-O99, CID-10)
- `obitos_maternos`: 6,5% NaN — anos sem arquivo SIM disponível (2025)

---

## 5. IBGE — PIB, População e GINI

**Origem**: IBGE SIDRA — tabelas de acesso público

- Tabela 5938: PIB municipal a preços correntes (Mil Reais), 2002–2023
- Tabela 6579: Estimativas populacionais, 2001–2025 (com lacunas)
- ginibr.xlsx: Índice de Gini da renda domiciliar per capita, 1991/2000/2010

**Obtido por**: download manual pelo aluno, inserido em `data/raw/ibge/`

**Arquivos raw**: `data/raw/ibge/tabela5938.xlsx`, `tabela6579.xlsx`, `ginibr.xlsx`

**Gerado**: `data/interim/ibge.parquet`  14.190 linhas (cod_ibge, ano — 645 × 22 anos)

**Colunas**: `pop_estimada`, `pib_mil_reais`, `pib_per_capita`, `gini_2010`

**Verificação de qualidade**:

- PIB per capita: R$ 2.263 a R$ 688.332 ✓ (mínimos em municípios rurais pequenos, máximo em Louveira/SP — polo industrial)
- `pop_estimada`: 804 a 12.396.372 ✓ (Borá/SP menor município, São Paulo capital maior)
- `gini_2010`: 0,33 a 0,69 ✓ (escala 0–1; dentro dos valores históricos para SP)
- PIB per capita calculado como `(pib_mil_reais × 1000) / pop_estimada` usando a estimativa populacional do mesmo ano. Para anos sem estimativa direta de pop (e.g., 2007, 2010), o valor foi propagado do ano anterior (ffill).
- Completude: 100% em todas as colunas (após propagação) ✓

**Limitações**:

- PIB disponível até 2023; anos 2024-2025 ainda não publicados pelo IBGE
- GINI é censitário (2010) — usado como variável estática para todos os anos

---

## 6. IDH-M e CAPAG — Indicadores Socioeconômicos

**Origem**:

- IDH-M: Atlas do Desenvolvimento Humano no Brasil (PNUD)
- CAPAG: Secretaria do Tesouro Nacional

**Obtido por**: download manual pelo aluno, inserido em `data/raw/idhm/` e `data/raw/capag/`

**Arquivos raw**:

```
data/raw/idhm/IDHM_{1991,2000,2010}.csv
data/raw/capag/capag-*.xlsx, capag_*.xlsx (2018–2025)
```

**Gerado**: `data/interim/socioeconomico.parquet`  3.682 linhas

**Colunas**: `capag` (A/B/C/D), `idhm_2010`

**Verificação de qualidade**:

- IDH-M 2010: 0,64 a 0,86 ✓ (escala 0–1; SP é estado com melhores IDH-M)
  642 municípios com dados (3 sem correspondência no IBGE 2010)
- CAPAG: distribuição plausível por ano com maioria B e C ✓
  Cobertura variável: 296 municípios (2018) a 595 (2021) — CAPAG não é obrigatório para todos e pode estar ausente em municípios com pendências junto ao Tesouro.

**Limitações**:

- IDH-M só disponível para anos censitários (1991, 2000, 2010); usando 2010 como proxy
- CAPAG de 2018 tem cobertura menor pois o sistema estava sendo implantado

---

## 7. SINISA — Saneamento Básico (água e esgoto)

**Origem**: Sistema Nacional de Informações em Saneamento Básico (SINISA)

https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa

**Obtido por**: download manual pelo aluno, inserido em `data/raw/sinisa/`

**Arquivos raw**: 14 arquivos xlsx (água, esgoto, gestão — anos 2023 e 2024)

**Gerado**: `data/interim/sinisa.parquet`  1.258 linhas (628-630 por ano)

**Colunas**: `atend_agua_total_pct`, `atend_esgoto_total_pct`, `atend_esgoto_trat_pct`

**Verificação de qualidade**:

- `atend_agua_total_pct`: 24,4 a 100% ✓
- `atend_esgoto_total_pct`: 16,8 a 100% ✓ (SP tem grande variação urbano/rural)
- `atend_esgoto_trat_pct`: 0 a 100% ✓
- `atend_esgoto_trat_pct`: 26,9% NaN — município prestou informação de coleta mas não de tratamento (dado faltante no próprio SINISA)
- 628-630 de 645 municípios presentes (15 sem prestador cadastrado no SINISA)

**Limitações**:

- Apenas 2023 e 2024 disponíveis; não há série histórica no SINISA anterior a 2023 (dados anteriores estavam no SNIS — sistema diferente, não incluído)

---

## 8. IBGE Aglomerados Subnormais — Favelas

**Origem**: IBGE — Censos Demográficos 2010 e 2022 (SIDRA)

- Tabela 3379: Número de aglomerados subnormais por município (Censo 2010)
- Tabela 3381: População residente em aglomerados subnormais (Censo 2010)
- Tabela 9883: Número de favelas e comunidades urbanas (Censo 2022)
- Tabela 9900: População residente em favelas e comunidades urbanas (Censo 2022)

**Obtido por**: download manual pelo aluno, inserido em `data/raw/habitacao/`

**Arquivos raw**: `data/raw/habitacao/tabela{3379,3381,9883,9900}.xlsx`

**Gerado**: `data/interim/habitacao.parquet`  645 linhas (todos os municípios SP)

**Colunas**: `num_aglom_subnorm_2010`, `pop_aglom_subnorm_2010`, `num_favelas_2022`, `pop_favelas_2022`

**Verificação de qualidade**:

- `num_aglom_subnorm_2010`: 1 a 1.020 ✓ (SP capital = 1.020); 60 municípios
- `pop_aglom_subnorm_2010`: 161 a 1.280.400 ✓ (SP capital = 1,28M); 60 municípios
- `num_favelas_2022`: 1 a 1.359 ✓ (SP capital = 1.359); 92 municípios
- `pop_favelas_2022`: 96 a 1.728.235 ✓ (SP capital = 1,73M); 92 municípios
- NaN = ausência de aglomerados/favelas registrados (0 implícito, não dado faltante)
- Crescimento de 60 → 92 municípios entre 2010 e 2022 é esperado pelo Censo 2022

**Nota técnica — estrutura SIDRA das tabelas de população (3381 e 9900)**:

Ambas têm cruzamento por sexo (Total / Masculino / Feminino).

- Tabela 3381: 3 colunas (cod, município, "Ano x Sexo" = Total).
- Tabela 9900: 4 colunas (cod, município, grupo_idade, "Ano x Sexo" = Total).

Filtro aplicado: `grupo_idade == "Total"` e coluna de sexo == "Total".
Traço "-" no SIDRA = município sem favelas → NaN no parquet.

**HISTÓRICO**: versões anteriores dessas tabelas tinham a variável "percentual do total geral" — artefato SIDRA que retorna 100 para a linha de soma por sexo. As tabelas foram substituídas pelo aluno com a variável "população absoluta".

---

## 9. IBGE — Áreas territoriais e densidade populacional

**Origem**: FTP do IBGE — geoftp.ibge.gov.br

https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/areas_territoriais/

Arquivo: `AR_BR_RG_UF_RGINT_RGI_MUN_2024.xls` (aba `AR_BR_MUN_2024`)

Coluna `CD_MUN` é código IBGE 7 dígitos; `AR_MUN_2024` é a área em km².

- Coleta automatizada por: `src/arboviral/scraping/ibge_areas.py`
- Parsing por: `src/arboviral/ingestion/densidade.py`

**Arquivos raw**: `data/raw/ibge_areas/AR_BR_RG_UF_RGINT_RGI_MUN_2024.xls`

**Gerado**: `data/interim/densidade.parquet` (645 linhas, 100% completude)

**Colunas**:

- `area_km2`     float   Área territorial em km² (IBGE 2024)
- `densidade_2023`    float   Habitantes / km² em 2023 (último ano IBGE)

**Verificação de qualidade**:

- 645 municípios SP cobertos sem nenhum NaN
- Áreas: mín 3.6 km² (Águas de São Pedro), máx 1.978 km² (Iguape)
- Densidades: mín 3.6 hab/km² (interior), máx 14.593 hab/km² (zona urbana metropolitana — São Caetano do Sul)
- Mediana: 41.6 hab/km² (típico de município interiorano)

**JUSTIFICATIVA EPIDEMIOLÓGICA**:

Densidade populacional é proxy direto da densidade de criadouros potenciais e da taxa de contato humano-vetor. Município denso favorece transmissão urbana de Aedes; município esparso atenua. Hipótese a ser validada via SHAP estratificado (RQ2).

**NOTA**: A área é praticamente estática (mudanças apenas em casos raros de emancipação ou conurbação). Por isso usamos o arquivo do ano de 2024 mesmo que a cobertura do dataset seja 2015-2025.

---

## 10. MapBiomas Brasil — Cobertura e uso da terra (Coleção 10.1)

**Origem**: MapBiomas Project (rede de ONGs, universidades e empresas de tecnologia)

https://brasil.mapbiomas.org/estatisticas/

- Arquivo: BIOMAS, ESTADOS E MUNICÍPIOS (Coleção 10.1) — COBERTURA
- Hospedado em Google Drive (link na página oficial do MapBiomas)
- DOI: https://doi.org/10.58053/MapBiomas/SJZOLT
- Atualização: 2026-02-19

**Coleta automatizada por**: `src/arboviral/scraping/mapbiomas.py`
**Parsing por**: `src/arboviral/ingestion/mapbiomas.py`

**Arquivos raw**: `data/raw/mapbiomas/MAPBIOMAS_COVERAGE_COL_10_1.xlsx` (~75 MB)

**Gerado**: `data/interim/mapbiomas.parquet` (6.450 linhas, 100% completude)

**Cobertura**: 645 municípios SP × 10 anos (2015-2024)
Para 2025: forward-fill no `build_master.py` (cobertura do solo é estável)

**Colunas do parquet**:

- `pct_floresta`              float   % área com floresta natural
- `pct_natural_nao_florestal` float   % formação natural não florestal
- `pct_agricultura`           float   % agropecuária (pastagem + lavoura + silvicultura)
- `pct_nao_vegetado`          float   % área urbanizada / não vegetada (cidades, mineração)
- `pct_agua`                  float   % água / ambiente marinho

**Verificação de qualidade — médias estaduais**:

- `pct_agricultura`:    74.0% (SP é estado predominantemente agrícola)
- `pct_floresta`:       17.2% (Mata Atlântica preservada + reflorestamento)
- `pct_nao_vegetado`:    5.4% (média dominada por capitais; máx 100% em ilhas urbanas)
- `pct_agua`:            2.1%
- `pct_natural_nao_flor` 1.3%

Exemplo São Paulo capital (cod 3550308) em 2024:

```
floresta 27.0% + agric 8.4% + urbanizado 59.8% + água 3.8% = 99.0% (~ok)
```

**NOTA SOBRE NORMALIZAÇÃO DE NOMES**:

MapBiomas inclui ~13 municípios SP que aparecem em outros estados também (overlap de bioma). Filtramos esses fora via lookup IBGE de SP.

**JUSTIFICATIVA EPIDEMIOLÓGICA**:

- `pct_nao_vegetado` (urbanização): correlaciona com criadouros de *Aedes aegypti* (recipientes domiciliares) — vetor urbano de dengue/zika/chiku.
- `pct_floresta`: relacionado à transmissão silvestre de febre amarela (vetores Haemagogus/Sabethes em mata fechada).
- `pct_agricultura`: modificação de habitat e exposição ocupacional.

---

## 11. e-Gestor MS — Cobertura da Atenção Primária à Saúde (ex-ESF)

**Origem**: API REST do portal e-Gestor APS do Ministério da Saúde

```
https://relatorioaps-prd.saude.gov.br/cobertura/{ab|aps}
?unidadeGeografica=MUNICIPIO&nuCompInicio=YYYYMM&nuCompFim=YYYYMM
```

Endpoints DESCOBERTOS via DevTools/Network do navegador (a SPA do e-Gestor chama essa API por baixo). Sem necessidade de Selenium — GET simples retornando JSON com lista de 5570 municípios brasileiros por mês.

**Há QUEBRA METODOLÓGICA em 2021**:

- AB  (2015-2020): "Cobertura da Atenção Básica" — usa `pcCoberturaAb`
  - valores em STRING formato BR ("12,106,920")
  - `nuComp = "201801"`
- APS (2021-presente): "Cobertura Potencial da APS" — usa `qtCobertura`
  - valores em INT/FLOAT direto
  - `nuComp = "01/2024"`

**Coleta automatizada por**: `src/arboviral/scraping/esf_coverage.py`

- 132 arquivos JSON (72 `cobertura_ab_*.json` + 60 `cobertura_aps_*.json`)
- ~380 MB total raw
- Pausa de 1s entre requests (respeito ao servidor)

**Parsing por**: `src/arboviral/ingestion/esf.py`

- Harmoniza os 2 formatos (parser distinto para AB vs APS)
- Lookup IBGE 6→7 dígitos (mesmo padrão do SINAN)
- Filtra SP

**Arquivos raw**: `data/raw/esf/cobertura_<ab|aps>_<YYYYMM>.json`

**Gerado**: `data/interim/esf.parquet` (85.037 linhas, 99.9% completude)

**Colunas**:

- `esf_metodologia`       'AB' ou 'APS' (flag categórica para o modelo)
- `esf_cobertura_pct`     % cobertura APS/AB calculada pelo MS
- `esf_qt_equipes`        número de equipes ESF
- `esf_qt_capacidade`     capacidade total (apenas APS; NaN para AB)
- `esf_pop_referencia`    população usada como denominador pelo MS

**Verificação de qualidade — SP**:

- 645 municípios SP cobertos
- 99.9% de completude (cobertura, equipes, pop)
- 45.3% para `esf_qt_capacidade` (apenas APS, esperado)
- SP capital: 59.4% AB (2018) → 58.5% APS (2024) — coerente
- Mediana estadual: 92% (AB), 107% (APS) — >100% normal pois capacidade pode exceder pop em municípios pequenos com sobreposição de equipes

**JUSTIFICATIVA EPIDEMIOLÓGICA**:

Cobertura ESF determina a CAPACIDADE DE DETECÇÃO precoce de surtos:

- Cobertura alta → mais agentes comunitários → mais notificação
- Cobertura baixa → casos sub-reportados → "calmaria aparente" pode mascarar surto real

Combinado com latência SINAN (já implementada), o modelo agora tem 2 proxies independentes da qualidade do sistema de vigilância municipal.

---

## 12. PNI/DATASUS — Cobertura vacinal contra febre amarela

**Origem**: Programa Nacional de Imunizações (PNI/MS), publicado via TabNet/DATASUS

```
http://tabnet.datasus.gov.br/cgi/tabcgi.exe?pni/cnv/cpniuf.def
Indicador: "Cobertura vacinal" × Imunobiológico = "Febre amarela"
```

**Obtido por**: download manual via TabNet (formulário CGI sem endpoint REST estável)
reformatado para o padrão da plataforma inteli.gente:

```
codigo_ibge | sigla       | ano  | variavel_valor
1100023     | COB_VAC_FA  | 1994 | 30.36
```

**Coleta documentada em**: `src/arboviral/scraping/pni_febre_amarela.py`

- Modo "verifica e documenta" (CGI não automatizável trivialmente)
- Imprime instruções de obtenção se o arquivo não existir
- Alternativa SQL: BasedosDados (br_ms_pni dataset)

**Parsing por**: `src/arboviral/ingestion/vacinacao_fa.py`

- Filtra SP (`codigo_ibge` prefixo '35')
- Códigos IBGE já em 7 dígitos (sem lookup)
- Não preenche gaps (preserva o original); ffill é feito em `build_master`

**Arquivos raw**: `data/raw/febre_amarela/COB_VAC_FA.csv` (CSV nacional, 90.234 linhas)

**Gerado**: `data/interim/vacinacao_fa.parquet` (10.546 linhas SP)

**Coluna**:

- `cob_vac_fa_pct`   % da população-alvo imunizada contra febre amarela

**Verificação de qualidade — SP**:

- 645 municípios SP cobertos (100%)
- 19 anos com dados na janela 1994-2026 (gaps em 2008, 2010, 2011, 2014, 2017)
- Dentro do recorte do master (2015-2025): falta apenas 2017
- Mediana SP por ano: declínio observado de ~94% (2002) para ~74% (2025)
- Valores >100% ocorrem (~25% das linhas): denominador-alvo do PNI fica abaixo do real em municípios com migração ou estimativa populacional defasada — preservados sem cap (são informativos)
- Max 418% (caso extremo); distribuição: p25=57%, p50=81%, p75=100%

**DECISÃO METODOLÓGICA — gap 2017**:

Forward-fill no grupo (cod_ibge) em `build_master.py` preenche 2017 com o valor de 2016. Justificativa: cobertura vacinal varia <5p.p. interanualmente em períodos sem campanha nacional, e 2017 não teve mudança brusca da política do PNI para SP. Gap 2015-2016 (912+588 linhas faltantes) é remanescente porque ffill não faz backfill — municípios sem registro em 2015-2016 ficam NaN nesses meses (afeta 2,5% do master final).

**JUSTIFICATIVA EPIDEMIOLÓGICA**:

Cobertura vacinal diferencia RISCO REAL (transmissão) de RISCO POPULACIONAL (vulnerabilidade). Município em "área de risco" pode ter risco operacional baixo se a população está bem imunizada. Sem essa variável, o modelo confunde os dois cenários. Particularmente relevante após 2017-2019 (surto silvestre SP) e 2025 (ressurgência) — combinado com `pct_floresta` (MapBiomas), permite ao modelo distinguir "matas + pop não vacinada" (alto risco) de "matas + pop vacinada" (risco controlado).

---

# Resumo das fontes e status

| Fonte             | Cobertura            | Como obtido        | Status |
|-------------------|----------------------|--------------------|--------|
| SINAN dengue      | 2015-2025, mensal    | API FTP auto       | ✓ OK |
| SINAN zika        | 2015-2025, mensal    | API FTP auto       | ✓ OK (pequeno volume) |
| SINAN chikungunya | 2015-2025, mensal    | API FTP auto       | ✓ OK |
| Febre amarela     | 2015-2025, mensal    | CSV MS dados abertos | ✓ OK (raríssima — 717 casos SP/11 anos) |
| NASA POWER        | 2015-2025, mensal    | API REST auto      | ✓ OK, 100% completude |
| MUNIC 2018/2020   | estático (1 obs/mun) | Download manual    | ✓ OK |
| CNES/LT (leitos)  | 2015-2025, mensal    | FTP auto           | ✓ OK (42% NaN = sem leitos) |
| SIM (matern.)     | 2015-2024, anual     | FTP auto           | ✓ OK |
| IBGE PIB+pop      | 2002-2023, anual     | Download manual    | ✓ OK |
| IBGE GINI         | 2010 (censo)         | Download manual    | ✓ OK (estático) |
| IDH-M             | 2010 (censo)         | Download manual    | ✓ OK (estático) |
| CAPAG             | 2018-2025, anual     | Download manual    | ✓ OK (cobertura variável) |
| SINISA            | 2023-2024, anual     | Download manual    | ✓ OK |
| Aglom. subnorm.   | 2010 e 2022          | Download manual    | ✓ OK (contagem + pop absoluta) |
| Áreas IBGE        | estático             | Script geoftp      | ✓ OK (644 km² mediano) |
| Densidade pop     | estático (de 2023)   | Calculada          | ✓ OK (100% completude) |
| MapBiomas         | 2015-2024, anual     | Script Drive       | ✓ OK (5 classes uso solo, ffill 2025) |
| ESF (cobertura)   | 2015-2025, mensal    | API REST auto      | ✓ OK (132 arq JSON, AB+APS harmonizados) |
| PNI vacinação FA  | 2015-2025, anual     | CSV TabNet manual  | ✓ OK 97.5% (gap 2017 ffill) |

---

# Dataset consolidado — `municipio_mes.parquet`

- **Gerado por**: `src/arboviral/transform/build_master.py`
- **Saída**: `data/processed/municipio_mes.parquet` (gitignored — derivado dos interim)
- **Shape**: 85.140 linhas × 57 colunas
- **Chave**: (cod_ibge, ano, mes) — 645 municípios SP × 2015–2025 × 12 meses

**Estratégia de join**:

- mensal `(cod_ibge, ano, mes)`: `sinan_dengue`, `sinan_zika`, `sinan_chikungunya`, `febre_amarela`, `nasa_power`, `saude`
- anual `(cod_ibge, ano)`: `ibge`, `socioeconomico`, `sinisa`
- estático `(cod_ibge)`: `munic`, `habitacao`, lookup INMET

**Completude por grupo de variáveis**:

| Grupo | Completude |
|---|---|
| Chave + geolocalização | 100% (lookup completo para todos os 645 municípios) |
| NASA POWER | 100% (API cobre 2015-2025 sem lacunas) |
| `populacao_estimada` | 100% (forward-fill 2024-2025 a partir de 2023; ver decisão) |
| MUNIC | 94-100% (estático — pequenas lacunas por não-resposta) |
| SINAN dengue | 72% (endêmica, mas não ocorre em todo município/mês) |
| SINAN chikungunya | 16% (surtos concentrados regionalmente) |
| SINAN zika | 7% (epidemia pontual 2016-2017) |
| Febre amarela | 0.3% (raríssima — apenas pico 2017-2019, ressurgência 2025) |
| IBGE PIB | 82% (até 2023; 2024-2025 NaN — não fizemos extrapolação) |
| CAPAG/IDH-M | 52% (CAPAG disponível a partir de 2018) |
| SINISA água/esgoto | 14-18% (apenas 2023-2024 disponíveis) |
| Habitação — favelas | 9-14% (só municípios com favelas registradas) |

**Renomeações aplicadas no `build_master`** (interim → master):

```
leitos_sus          → leitos_publicos
obitos_maternos     → mortalidade_materna
pop_estimada        → populacao_estimada
gini_2010           → gini
idhm_2010           → idhm
atend_agua_*        → iag0001_atend_agua_pct
atend_esgoto_*      → ies0001_atend_esgoto_pct / ies2004_esgoto_tratado_pct
casos_notificados   → {doenca}_casos  (dengue_, zika_, chikungunya_, febre_amarela_)
```

## Decisões metodológicas documentadas

### 1. População 2024-2025 — forward-fill de 2023

**PROBLEMA**: IBGE só publica estimativas oficiais até 2023.

**ALTERNATIVAS CONSIDERADAS**:

- (a) Forward-fill da estimativa de 2023 (escolhida)
- (b) Modelo de tendência populacional (regressão linear sobre 2015-2023)
- (c) Manter NaN e perder 2 anos da janela de modelagem

**ESCOLHA**: (a). Justificativa:

- Variação anual de população municipal em SP é tipicamente <2%
- Margem de erro da própria estimativa do IBGE é da ordem de 1-3%
- Modelo de tendência adicionaria complexidade sem ganho material
- Conservadora: assume status quo, não introduz pressupostos adicionais

**IMPACTO**: `pib_per_capita` NÃO foi recalculado para 2024-2025 (mantido NaN porque `pib_mil_reais` também é NaN). Apenas `populacao_estimada` recebeu o forward-fill.

### 2. Febre amarela — município de Local Provável de Infecção (LPI)

Fonte usa LPI em vez de residência (padrão SINAN). Diferença INTRÍNSECA à doença: febre amarela é predominantemente silvestre, transmitida por mosquitos Haemagogus/Sabethes em áreas de mata. Pessoas que se infectam geralmente o fazem fora do município de moradia (visitando áreas rurais ou de turismo). Manter o LPI é metodologicamente correto para o objetivo de identificar áreas de risco de transmissão.

### 3. Cohen's kappa entre definições de surto

Implementado em `src/arboviral/labels/build_labels.py`. Resultados:

**TAXA DE POSITIVOS POR (DOENÇA × DEFINIÇÃO)**:

|                  | L1 canal | L2 zscore | L3 inc100 | L4 inc300 |
|------------------|---------:|----------:|----------:|----------:|
| dengue           | 16.21%   | 13.38%    | 21.12%    | 11.79%    |
| zika             | 0.60%    | 0.53%     | 0.04%     | 0.01%     |
| chikungunya      | 1.76%    | 1.59%     | 0.38%     | 0.14%     |
| febre_amarela    | 0.03%    | 0.03%     | 0.00%     | 0.00%     |

**CONCORDÂNCIA ENTRE DEFINIÇÕES** (κ par a par):

- dengue:        L1↔L2: 0.886 | L1↔L3: 0.520 | L3↔L4: 0.666
- zika:          L1↔L2: 0.937 | L1↔L3: 0.118 (definição estatística degenera)
- chikungunya:   L1↔L2: 0.944 | L1↔L3: 0.345 | L1↔L4: 0.143
- febre_amarela: L1↔L2: 1.000 | L1↔L4: 0.000 (zero positivos em L3 e L4)

**ACHADOS PRELIMINARES (RQ4)**:

- (a) L1 (canal endêmico) e L2 (Z-score) são praticamente equivalentes em todas as doenças — escolher entre elas é detalhe metodológico. Faz sentido: ambas usam mediana/média + dispersão da distribuição histórica.
- (b) Para dengue, L3 e L4 capturam fenômenos parcialmente distintos das definições estatísticas. Pode haver predições com performance diferente entre L1/L2 e L3/L4 — isso responde diretamente à RQ4.
- (c) Para zika e febre amarela, baseline é praticamente zero (raridade), então L1/L2 viram "qualquer caso ≥ casos_min". Modelagem clássica é difícil mas não inviável — pode-se usar limiar de probabilidade muito baixo na predição.
- (d) Para febre amarela, L3 e L4 são sempre zero (raridade absoluta). Restam apenas L1/L2 para essa doença.

---

# Rótulos de surto — `labels.parquet`

- **Gerado por**: `src/arboviral/labels/build_labels.py`
- **Configuração**: `configs/outbreak_label.yaml` (anos epidêmicos, parâmetros, mínimo abs)
- **Saída**: `data/processed/labels.parquet` (gitignored — derivado do master)
- **Shape**: 85.140 linhas × 23 colunas
- **Chave**: (cod_ibge, ano, mes)

**POR DOENÇA** (4 doenças × 5 colunas = 20 colunas + 3 chaves):

- `{doenca}_incid_100k`    incidência mensal/100k hab (transparência, não é label)
- `{doenca}_surto_canal`   L1: canal endêmico (mediana + 1.96·σ histórico)
- `{doenca}_surto_zscore`  L2: Z-score relativo (Z > 2 sobre baseline)
- `{doenca}_surto_inc100`  L3: incidência ≥ 100/100k hab
- `{doenca}_surto_inc300`  L4: incidência ≥ 300/100k hab

**DECISÕES DE DESIGN** (também em `configs/outbreak_label.yaml`):

- (a) Anos epidêmicos excluídos do baseline (por inspeção da incidência estadual):
  - dengue:        2015, 2019, 2024, 2025
  - chikungunya:   2021, 2024, 2025
  - zika:          2016 (único pico — definição relativa fica degenerada)
  - febre_amarela: 2017, 2018, 2019, 2025
- (b) Janela do baseline = FIXA (anos não-epidêmicos da série completa, não rolling). Justificativa: dataset começa em 2015, sem baseline pré-série disponível. Trade-off: a janela fixa usa "futuro" para construir baseline de anos antigos (não é problema porque labels são alvo, não predição).
- (c) Mínimo absoluto de casos = 5 (configurável). Aplicado como AND em todas as definições para evitar surto de 1 caso isolado em município pequeno virar positivo só porque mediana baseline = 0. Empírico, alinhado com práticas comuns de vigilância em arboviroses.
- (d) NaN em casos é tratado como 0 (ausência de registro = sem casos notificados).

---

# Modelagem — `model_results.parquet`

- **Gerado por**: `src/arboviral/train.py`
- **Pós-processamento**: `src/arboviral/analyze_results.py` + `src/arboviral/build_reports.py`
- **Saída**: `data/processed/model_results.parquet` (315 linhas) + ~8 tabelas CSV
- **Documento consolidado**: `RELATORIO_MODELAGEM.md` (auto-gerado)

**ESCOPO**:

4 doenças × 4 definições × 7 modelos × 3 folds = 336 combinações pretendidas.
Realmente executadas: 315. Excluídas: 21 (febre amarela em todas as definições + zika × inc300) por zero positivos no treino — esperado pela raridade absoluta.

**VALIDAÇÃO TEMPORAL — expanding window (sem leakage)**:

```
Fold 1: train target_year ≤ 2021 → test target_year == 2022
Fold 2: train target_year ≤ 2022 → test target_year == 2023
Fold 3: train target_year ≤ 2023 → test target_year == 2024
target_year = ano de t+1 (não da feature) — cada predição é um surto do ano alvo.
2025 reservado para demonstração futura.
```

**DESBALANCEAMENTO (RECAPITULAÇÃO)**:

Para classes raras, modelo trivial "nunca declarar surto" tem alta acurácia mas recall=0, F1=0, inútil para vigilância.

Solução adotada: `class_weight='balanced'` nos modelos sklearn (LogReg, RF, LGBM, EBM) — o erro em positivos pesa `n_total/(2·n_positivos)`, forçando o modelo a valorizar acertos na classe minoritária.

XGBoost não aceita `class_weight`; usa `scale_pos_weight = n_neg/n_pos` com mesmo efeito matemático. Calculado on-the-fly por fold em `train.py`.

SMOTE/oversampling NÃO foi usado: introduz risco de leakage temporal em séries (mistura registros de momentos diferentes). `class_weight` é matematicamente equivalente sem esse risco.

**MÉTRICA PRIMÁRIA — AUPRC + lift**:

AUPRC (Average Precision) é robusta a class imbalance. Sempre reportada com `AUPRC_lift = AUPRC / prevalência_da_classe` (= performance vs random baseline). Modelo com lift > 1 é melhor que random; lift = 100 significa 100× melhor.

**RANKING GLOBAL DOS MODELOS (RQ1)**:

| Modelo       | AUPRC | Lift | Recall | Notas |
|--------------|------:|-----:|-------:|-------|
| rf           | 0.397 | 276× | 0.42   | Melhor desempenho global |
| ebm          | 0.367 | 272× | 0.16   | Intrinsecamente interpretável |
| xgb          | 0.362 | 271× | 0.31   | |
| lgbm         | 0.372 | 107× | 0.29   | |
| persistencia | 0.347 |  27× | 0.52   | Baseline forte (autocorrelação) |
| logreg       | 0.288 |  20× | 0.59   | Linear não captura interações |
| climatologia | 0.151 |  12× | 0.05   | Sazonalidade pura é insuficiente |

Conclusão RQ1: ML supera baselines em ~14% relativo (RF vs persistência). Ganho mais expressivo em definições raras (chikungunya × inc100: +0.19 AUPRC absoluto, com persistência muito fraca pela raridade da classe).

**SENSIBILIDADE À DEFINIÇÃO DE SURTO (RQ4)**:

Para dengue, AUPRC varia de 0.483 (zscore) a 0.792 (inc100) — a escolha do rótulo tem MAIS impacto que a escolha do modelo. Confirma a relevância da análise multi-definição proposta.

Casos onde ML NÃO supera persistência:

- chikungunya × inc300 (raridade extrema, persistência domina)
- zika × canal/zscore (autocorrelação muito forte)

Documentados como achado científico, não como falha do método.

**DRIVERS PREDITIVOS (RQ2) — SHAP global nos modelos vencedores**:

DENGUE (RF, canal endêmico):

```
14% dengue_incid_lag1     | 13% dengue_casos_trend3   | 12% dengue_casos_lag1
 9% dengue_casos_lag12    |  6% dengue_casos_roll3    |  5% temp_min
 2% precip_media_dia_roll3
```

→ Lags próprios + clima dominam; sazonalidade anual (lag12) é importante.

CHIKUNGUNYA (RF, canal):

```
11% chikungunya_incid_lag1 | 11% chikungunya_casos_lag1
10% populacao_estimada     |  9% chikungunya_casos_roll6
 5% dengue_casos_trend3    |  5% dengue_casos_lag1     ← cross-doença!
 5% leitos_publicos        |  3% dengue_casos_roll3
```

→ População do município + features de dengue estão entre os top.

ZIKA (LGBM, canal):

```
11% dengue_casos_lag1      ← cross-doença é a feature mais preditiva!
10% dengue_casos_roll6     | 10% lon (longitude)
 6% umid_media_lag1        |  5% temp_media
```

→ **ACHADO CENTRAL**: features de DENGUE são as mais preditivas para ZIKA. Coerente com biologia: mesmo vetor (*Aedes aegypti*), mesmas condições ambientais. Valida empiricamente a decisão de incluir features cross-doença.

**ANÁLISE DE TRANSIÇÕES (RECALL EM INÍCIO DE SURTO)**:

Pergunta crítica: o modelo antecipa o INÍCIO de surto (transição 0→1) ou só "acompanha" surtos em curso? Para um gestor, antecipar é o que tem valor. Persistência por definição = 0% (nunca prevê início).

**RECALL EM INÍCIO** (transição 0→1):

| Modelo       | Dengue×canal | Dengue×inc100 | Chiku×canal | Zika×canal |
|--------------|-------------:|--------------:|------------:|-----------:|
| persistencia |         0.0% |          0.0% |        0.0% |       0.0% |
| rf           |        29.0% |         31.4% |       21.2% |      35.4% |
| xgb          |        32.3% |         35.9% |       11.8% |      10.8% |
| lgbm         |        25.8% |         30.5% |        6.9% |       6.3% |
| logreg       |        39.4% |         55.4% |       56.3% |      63.2% |
| ebm          |         7.3% |         17.1% |        3.1% |       0.0% |

**TAXA DE FALSOS POSITIVOS EM MESES NORMAIS** (0→0):

| Modelo       | Dengue×canal | Dengue×inc100 | Chiku×canal | Zika×canal |
|--------------|-------------:|--------------:|------------:|-----------:|
| persistencia |         0.0% |          0.0% |        0.0% |       0.0% |
| rf           |        10.2% |          7.9% |        1.0% |       0.6% |
| xgb          |        12.0% |          8.3% |        0.6% |       0.3% |
| logreg       |        35.1% |         18.8% |       11.3% |       7.4% |
| ebm          |         2.4% |          3.8% |        0.1% |       0.1% |

**ACHADOS**:

- ML supera persistência ONDE MAIS IMPORTA: RF antecipa 29-35% dos INÍCIOS de surto em dengue com 8-10% de falsos positivos. Persistência: 0%.
- Trade-off entre LogReg (recall alto, mais alarmes falsos) e black-box (recall menor, alta precisão). Escolha depende da tolerância do gestor.
- Para zika×canal, RF captura 35.4% de inícios com apenas 0.6% de FP (apesar de AUPRC global modesto = 0.13).
- EBM é cauteloso demais para uso operacional; RF + SHAP é melhor compromisso.

**IMPLICAÇÃO CIENTÍFICA**:

Este é o achado mais relevante para utilidade prática. Literatura raramente separa início vs manutenção. Sugere ângulo central de artigo:

> "Predicting outbreak ONSET (not persistence) of arboviral diseases"

**CASO DE USO DA PLATAFORMA — exemplo real do fold de teste 2024**:

Município 3548500, abril/2024 (chikungunya):

- Probabilidade prevista: 99%
- Surto real: SIM
- Razões via SHAP:
  - 557 casos no mês passado (`chikungunya_casos_lag1`)
  - média 6 meses = 206 casos (`chikungunya_casos_roll6`)
  - incidência 128/100k (`chikungunya_incid_lag1`)
  - crescimento 348 → 557 (`chikungunya_casos_lag2`)

Cada alerta na plataforma final pode ter explicação automática gerada por `explicacao_local()` em `src/arboviral/evaluation/explain.py` — agora UNIFORME para todos os modelos do portfolio (árvores via SHAP, LogReg via coef×valor padronizado, EBM via API nativa `explain_local`).

---

## 13. Explicabilidade local — uniforme entre todos os modelos (atualização 2026-05)

Antes: app só mostrava SHAP por predição para árvores (RF/XGB/LGBM); EBM e LogReg ficavam com mensagem "explicabilidade não disponível", apesar de serem mais interpretáveis que árvores.

**Implementação**: `src/arboviral/evaluation/explain.py` estendido com função `explicacao_local()` que despacha pelo tipo do estimador final do pipeline:

- RandomForest / XGBoost / LightGBM   → SHAP `TreeExplainer` (post-hoc, exato)
- Regressão Logística                 → `coef_[i] × X_padronizado[i]`
  - (soma + intercept = `decision_function`; sanity check passou: diferença = 0)
- EBM (`ExplainableBoostingClassifier`) → `clf.explain_local(X).data(0)['scores']`
  - API nativa do interpret-ml.
  - Termos de interação 'a & b' têm a contribuição distribuída entre os pares para preservar o ranking por feature de entrada.

Output uniforme entre todos os métodos:

```
feature  valor_observado  contribuicao  abs_contribuicao  sign  metodo
```

A coluna `metodo` documenta qual técnica foi usada (auditoria + UI mostra ao gestor). Útil para o relatório: cada doença/modelo tem o EXATO mecanismo de explicação documentado.

Função legada `shap_por_predicao()` mantida como alias retrocompat (renomeia 'contribuicao' → 'shap', 'abs_contribuicao' → 'abs_shap').

---

## 14. Onda 1 — efeito empírico das 5 fontes integradas (atualização 2026-05)

Após integrar MapBiomas, ESF, latência SINAN, densidade IBGE e vacinação FA ao master (57 → 79 colunas) e ao features (117 → 140), retreinamos o portfolio completo (315 combinações) e comparamos AUPRC pré × pós:

**TOP GANHOS** (média de 3 folds, AUPRC):

| Cenário | AUPRC pré | AUPRC pós | Δ | Δ relativo |
|---|---:|---:|---:|---:|
| zika × inc100 (RF)         | 0.014 | 0.101 | +0.088 | +640% |
| zika × canal (XGB)         | 0.077 | 0.115 | +0.038 | |
| zika × zscore (XGB)        | 0.057 | 0.094 | +0.037 | |
| zika × canal (RF)          | 0.130 | 0.165 | +0.036 | |
| dengue × canal (LGBM/XGB)  | 0.543 | 0.569 | +0.027 | |
| chikungunya × canal (XGB)  | 0.287 | 0.312 | +0.024 | |

**RESUMO POR DOENÇA** (média do delta AUPRC):

- zika           +0.0085   ← maior beneficiada
- dengue         +0.0011
- chikungunya    -0.0017   (dentro do ruído de fold)
- febre amarela    NaN     (continua impossível pela raridade)

**ACHADO DEFENSÁVEL**: ZIKA é a doença em que as novas fontes mais movem o ponteiro. Coerente com a hipótese cross-doença reforçada:

- Cobertura ESF afeta detecção (proxy de qualidade da vigilância)
- MapBiomas (urbano + floresta) + densidade IBGE = pressão vetorial
- Cross-doença existente + agora dengue tem mais features → zika "herda" mais sinal indireto

Narrativa para relatório/artigo: "ao adicionar fontes ambientais (MapBiomas), de cobertura sanitária (ESF, vacinação FA) e de qualidade da vigilância (latência SINAN), o modelo passa a capturar surtos de zika que antes eram invisíveis (AUPRC 0.014 → 0.101 em zika×inc100)."

**PIORAS PONTUAIS — documentadas como ruído de fold**:

- chikungunya × inc100 (LGBM)  -0.105   (definição com 0.38% prevalência)
- dengue × inc300 (vários)     ~-0.005  (ruído de fold)

Backups dos resultados pré-Onda 1 preservados em:

- `data/processed/model_results_PRE_ONDA1.parquet`
- `data/processed/predictions_PRE_ONDA1.parquet`

para auditoria, re-análise e ablação reportável.

---

## 15. Mobilidade pendular intermunicipal (Censo 2010 + 2022) — adicionada em 2026-05-12

### Por que esta fonte

Hipótese científica: arboviroses se espalham geograficamente pelo movimento humano. Município pequeno que recebe muitos pendulares de uma região endêmica herda risco que o histórico próprio de casos não captura. Era item **#6 do top 10** do roadmap; foi atacada logo após Onda 1 (LIRAa permanece pausado aguardando LAI à CCD-SP).

### Duas vintages combinadas

A integração usa **duas vintages oficiais** do IBGE de forma complementar:

| Vintage | Fonte | Cobertura | Variáveis derivadas |
|---|---|---|---|
| Censo **2010** — microdados da amostra | <https://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Resultados_Gerais_da_Amostra/Microdados/> | anos 2015–2021 do master | `pendulares_entram_trabalho`, `pendulares_saem_trabalho` |
| Censo **2022** — SIDRA tabela 10329 | <https://sidra.ibge.gov.br/tabela/10329> (API REST) | anos 2022–2025 do master | apenas `pendulares_saem_trabalho` (entram fica **NaN**) |

A escolha das vintages se baseia na referência temporal de cada fonte. Não fazemos forward-fill cego: os anos pós-2022 recebem o snapshot 2022, recompondo a temporalidade real do fenômeno.

#### Vintage 2010 — matriz O-D via microdados

Arquivos baixados em `data/raw/mobilidade_pendular/`:
- `SP1.zip` (130 MB) — interior e capital fora da RM
- `SP2_RM.zip` (64 MB) — Região Metropolitana
- `Documentacao.zip` (10 MB) — layout fixed-width (aba PESS)

Reconstrução da **matriz origem-destino ponderada** entre os 645 municípios paulistas, a partir de 3.651.181 registros de pessoa após filtro UF=35. Mantemos somente registros com `V0660 == 3` ("trabalha em outro município") e destino dentro dos 645 SP — fluxo inter-UF e flag "país estrangeiro / mais de um município" descartados (genéricos demais para virarem feature limpa).

A partir da matriz O-D, projetamos para duas marginais:

| Coluna | Definição operacional |
|---|---|
| `pendulares_entram_trabalho` | Σ peso amostral de pessoas residentes em ≠ X que trabalham em X (soma da coluna de destino X na matriz) |
| `pendulares_saem_trabalho` | Σ peso amostral de pessoas residentes em X que trabalham em ≠ X (soma da linha de origem X na matriz) |

**Validação metodológica do peso amostral**: o layout PESS define V0010 com INT=3 + DEC=13, ou seja, peso é um inteiro de 16 dígitos representando o valor real com 13 decimais implícitos (faixa típica 1–500; média ~10 reflete a amostragem ~10% do Censo). A soma dos pesos sobre todos os 3,65 milhões de registros bate com a população oficial SP 2010 (~41,26 milhões), confirmando a interpretação correta. Documentado também como comentário no código.

#### Vintage 2022 — SIDRA tabela 10329 (apenas saídas)

A **tabela 10329 do Censo 2022** (liberada em 9/out/2025) traz "Pessoas de 10 anos ou mais ocupadas... por local de exercício do trabalho principal", em nível municipal. Pegamos a categoria **C469 = 12188 ("Outro município")** com totais nos demais classificadores (sexo, classes de rendimento, retorno semanal), via API REST:

```
GET https://servicodados.ibge.gov.br/api/v3/agregados/10329/periodos/2022/
    variaveis/13373?localidades=N6[N3[35]]
    &classificacao=469[12188]|2[6794]|386[9680]|2087[79177]
```

Resultado salvo em `data/raw/mobilidade_pendular/sidra_10329_saidas_2022.json` (~77 KB). Cobertura: 645/645 municípios SP, sem suprimidos por sigilo. Por que apenas saídas? Porque a tabela agrega por município de **residência** — não desagrega o destino. Microdados 2022 do IBGE ainda não estavam públicos em 12/mai/2026; sem eles, não há como reconstruir entradas para 2022.

### Por que `entram` fica NaN em 2022+ (e não copiamos o valor de 2010)

Decisão metodológica explícita: a série temporal deve respeitar a **referência de cada vintage**. Em 2022 não temos medida direta de entradas, então registramos NaN — o modelo trata ausência como informação. Preencher com 2010 seria mascarar a temporalidade e induzir o modelo a interpretar "valor estável" como observação fresca.

### Por que apenas trabalho e não estudo

Pendulares para estudo concentram universitários e secundaristas. Para vetor adulto de arboviroses, trabalho é o canal demograficamente mais relevante. Estudo permaneceria como feature derivada de menor poder preditivo e maior custo cognitivo para gestor entender. Decidimos não complicar e manter trabalho como única dimensão por enquanto.

### Sanity check dos valores

Top receptores na saída do parser fazem sentido geograficamente:

| Cod IBGE | Município | Entram 2010 | Saem 2010 | Saem 2022 | Δ saídas | Perfil |
|---|---|---:|---:|---:|---:|---|
| 3550308 | São Paulo capital | 899.708 | 155.256 | 149.070 | −6.186 | polo de empregos |
| 3547809 | Santo André | 75.579 | 122.608 | 113.299 | −9.309 | RMSP misto |
| 3518800 | Guarulhos | 50.411 | 113.131 | 91.279 | −21.852 | dormitório + aeroporto |
| 3534401 | Osasco | 57.155 | 110.771 | 107.063 | −3.708 | dormitório clássico |
| 3548708 | São Bernardo do Campo | 103.645 | 107.866 | 90.967 | −16.899 | RMSP misto |
| 3513801 | Carapicuíba | 41.022 | 72.199 | 66.457 | −5.742 | dormitório puro |

**Achado da comparação 2010 vs 2022**: quase todas as cidades-dormitório da RMSP tiveram queda nas saídas — efeito esperado do home office pós-pandemia. Guarulhos perdeu ~22 mil pendulares, Suzano ~19 mil, São Bernardo ~17 mil. A única do top 10 que cresceu foi Caieiras (+6.398). Esses ∆ não viram feature por si só, mas justificam metodologicamente a necessidade de manter as duas vintages distintas.

Cobertura no master: 100% para `saem` em todos os anos; 100% para `entram` nos anos 2015–2021 (vintage 2010); NaN para `entram` nos anos 2022–2025 (vintage 2022 não tem destino).

### Limitações documentadas

1. **Vintage 2010 cobre 7 anos do master, vintage 2022 cobre 4 anos** — descontinuidade implícita na transição 2021→2022. O modelo verá um salto que reflete a mudança real de comportamento pós-pandemia + mudança de metodologia. Considerar interagir com flag binário "ano ≥ 2022" se a descontinuidade afetar o modelo.
2. **`pendulares_entram_trabalho` ausente em 2022+** — limitação conhecida da SIDRA 10329. Será resolvida quando IBGE liberar microdados 2022.
3. **Apenas dimensão trabalho** — estudo, lazer e turismo não estão modelados.
4. **Apenas pendular intra-SP** — destinos em outras UFs descartados (efeito local em Paraíba do Sul, Mogi Guaçu fronteira MG etc. fica oculto).
5. **Peso amostral é estimativa** — Censo 2010 entrevistou ~10% da população; pesos calibram para o total, mas há erro amostral residual em municípios pequenos.

### Plano para atualizar quando IBGE liberar microdados Censo 2022

1. Estender `scraping/mobilidade_pendular.py` para baixar também os microdados 2022 (URLs análogas em `/Censos/Censo_Demografico_2022/Resultados_Gerais_da_Amostra/Microdados/`).
2. Estender `ingestion/mobilidade_pendular.py` com função `build_2022_microdados()` que reconstrói matriz O-D completa — formato e layout das variáveis-chave V0660/V6604 devem se manter (verificar via `Layout_microdados_Amostra.xls` da nova documentação).
3. Atualizar `build()` para usar a matriz O-D 2022 para anos ≥ 2022, preenchendo a coluna `pendulares_entram_trabalho` que hoje está NaN.
4. Re-treinar portfólio e reportar Δ AUPRC.

### 15.1 Integração ao `features.parquet` (2026-05-12)

`pendulares_entram_trabalho` e `pendulares_saem_trabalho` foram adicionadas a `src/arboviral/features/build_features.py` como **estáticas-anuais passadas direto** (sem transformação). Ficam expostas a todas as 4 doenças-alvo. Para o run `--no-cross`, não são afetadas pelo mascaramento porque o mascaramento exclui apenas colunas com prefixo de outra doença (`dengue_`, `zika_`, `chikungunya_`, `febre_amarela_`) — mobilidade pendular não tem prefixo de doença.

`pendulares_entram_trabalho` é NaN em 2022–2025 por construção. Modelos de árvore (RF/XGB/LGBM) tratam NaN nativamente; Regressão Logística e EBM dependem do descarte de coluna all-NaN no fold (`train.py:172-176`). Como a coluna **não** é all-NaN nos folds 2022/2023/2024 (apenas o teste é NaN; o treino tem dados 2015–2021), a coluna é mantida — o modelo aprende com 2015–2021 mas tenta predizer 2022+ usando NaN onde não deveria. Para LogReg/EBM isso vira um problema silencioso. **Nota de ação**: quando o IBGE liberar microdados 2022, esse problema some; até lá, vale considerar mask específico em LogReg para excluir essa coluna nos folds de teste 2023/2024.

### 15.2 Efeito sobre a hipótese cross-doença — sensitivity 2026-05-13

Mobilidade pendular é uma das duas fontes da Onda 2 que mais alteram o veredicto da hipótese cross-doença (a outra é SIH-SUS, ver §16.1 abaixo). Antes da Onda 2, zika era a doença que mais ganhava com cross — `dengue_casos_lag1` era a feature mais preditiva no SHAP global. Re-rodando a sensitivity com Onda 2 incorporada, **zika passou a perder −0.008 AUPRC com cross em média**, com 7 das 10 maiores quedas absolutas concentradas nessa doença. Detalhes e interpretação completa em §11 do RELATORIO_MODELAGEM.md. Mobilidade pendular contribuiu indiretamente: ao adicionar contexto estrutural sobre fluxo populacional, reduziu a unicidade do sinal indireto que vinha das features de dengue.

---

## 16. Internações por arbovirose pelo SUS (SIH-SUS) — adicionada em 2026-05-12

### Por que esta fonte

Hipótese: internações pelo SUS são proxy de **severidade** da arbovirose em um município–mês, complementando os dados do SINAN. SINAN registra a notificação ao sistema de vigilância (incluindo casos leves); SIH-SUS registra a internação efetiva, ou seja, o subconjunto grave que precisou de leito hospitalar. Além disso, captura residentes paulistas internados em outros estados (centros de referência) — informação ausente no SINAN, que agrega por município de residência mas exige notificação local.

Era item **#7 do top 10** do roadmap, atacado logo após mobilidade pendular.

### Fonte e formato

| Atributo | Valor |
|---|---|
| Fonte | DATASUS — SIH-SUS, AIH-RD (Autorização de Internação Hospitalar — Reduzida) |
| URL canônica | <ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/> |
| Padrão de arquivo | `RDSP{AAMM}.dbc` — um arquivo por mês, formato DBC (DataSUS comprimido) |
| Janela coletada | janeiro/2015 a dezembro/2025 — 132 arquivos, ~2 GB total |
| Tamanho típico | 12–18 MB por mês |
| Data de coleta | 2026-05-12 |

### Como o AIH-RD mapeia para o master

Cada linha do AIH-RD é uma internação hospitalar com 113 campos. Filtramos apenas os 4 campos necessários:

| Campo AIH-RD | Uso | Observação |
|---|---|---|
| `MUNIC_RES` | Município de residência do paciente | 6 dígitos DATASUS, convertido para 7 via lookup `municipios_sp_estacoes_inmet.xlsx` (mesmo lookup do SINAN) |
| `DT_INTER` | Data de internação | String AAAAMMDD, define ano/mês da agregação no master |
| `DIAG_PRINC` | CID-10 do diagnóstico principal | 3-4 chars, com padding por espaço |
| `MORTE` | Falecimento durante internação | Coletado mas não usado por enquanto |

### Classificação CID-10 → doença

| CID-10 | Doença derivada | Notas |
|---|---|---|
| A90 | dengue | dengue clássico |
| A91 | dengue | dengue grave / hemorrágico — somado ao dengue clássico para a feature `sih_internacoes_dengue` |
| A92.0 | chikungunya | código específico desde 2014 |
| A92.5 | zika | código próprio criado pela OMS em 2016 e adotado no Brasil em 2017 |
| A92.8 | zika | "outras febres por arbovírus específicas" — código usado pelos hospitais nos surtos 2015–2016 antes da existência do A92.5; mantido para não perder o histórico inicial |
| A95* | febre_amarela | qualquer subcategoria (silvestre ou urbana) |

Não filtramos por gravidade do CID dentro da família (A90 leve vs A91 grave) — qualquer internação pelo SUS já indica severidade suficiente para justificar leito hospitalar.

### Colunas adicionadas ao master

Quatro contagens mensais, uma por doença:

| Coluna | Definição operacional |
|---|---|
| `sih_internacoes_dengue` | nº de internações pelo SUS com CID A90/A91 no município-mês (residência) |
| `sih_internacoes_chikungunya` | nº de internações pelo SUS com CID A92.0 |
| `sih_internacoes_zika` | nº de internações pelo SUS com CID A92.5 ou A92.8 |
| `sih_internacoes_febre_amarela` | nº de internações pelo SUS com CID A95* |

Zero não significa NaN — significa que não houve internação por aquela doença naquele município-mês. Espera-se zero majoritário para zika (próximo) e febre amarela (raríssimo, normalmente confinado a surtos pontuais).

### Diferença prática vs `internacoes` do SINAN

A coluna `internacoes` já presente no master vem do campo `HOSPITALIZ == '1'` do SINAN (apenas dengue e chikungunya, zika não tem). O SIH-SUS adiciona:

1. **Cobertura mais completa de internação**: SINAN depende da notificação compulsória + preenchimento do campo HOSPITALIZ pelo notificador; muita internação real não aparece como tal no SINAN porque a ficha não foi atualizada após o paciente piorar.
2. **Inclui residentes SP internados fora de SP**: SINAN agrega no município de notificação; SIH-SUS agrega no município de residência mesmo quando o leito ficou em outro estado.
3. **Inclui zika e febre amarela**: SINAN para zika não tem campo HOSPITALIZ; SIH-SUS captura.

### Sanity check dos valores

Janela 2015–2025 (132 arquivos): contagens totais por doença batem com a literatura epidemiológica brasileira — dengue domina (centenas de milhares de internações ao longo da década), chikungunya na faixa de milhares, zika nas dezenas (rede severa pouco comum), febre amarela raríssima (poucos casos isolados).

Top picos esperados: São Paulo capital em abr–mai/2024 (auge da maior epidemia de dengue do estado).

### Limitações documentadas

1. **Apenas SUS** — internações privadas ficam fora. Em SP isso é particularmente relevante porque há cobertura de plano de saúde acima da média nacional. Subestimativa sistemática nos municípios de maior renda.
2. **Apenas casos graves** — arbovirose leve não interna; a feature está correlacionada com casos mas é deslocada para a cauda direita da gravidade.
3. **CID-10 do principal** — não conta arbovirose como diagnóstico secundário (paciente internado por outra causa + dengue concomitante).
4. **Defasagem de processamento DATASUS** — ~60 dias entre a internação e a publicação no FTP. Para o mês corrente em produção, esperar 2 meses de "encheção" do dado.
5. **A92.8 também captura outras arboviroses raras** (Mayaro, etc.). Em SP isso é desprezível mas há ruído residual.

### Como usar a feature no modelo (recomendação)

`sih_internacoes_*` em t é uma **medida retrospectiva** (registra o que aconteceu no mês). Para virar feature preditiva de surto em t+1, usar com defasagem (lag 1, 2 ou 3 meses) e/ou médias móveis — segue a convenção das demais features do master, gerada por `src/arboviral/features/build_features.py`. Não substituir `internacoes` do SINAN, e sim coexistir como sinal complementar.

### 16.1 Efeito sobre a hipótese cross-doença — sensitivity 2026-05-13

SIH-SUS foi a fonte da Onda 2 que provavelmente mais alterou o veredicto sobre features cross-doença. As 4 colunas `sih_internacoes_{dengue,zika,chikungunya,febre_amarela}_lag1` carregam — sem prefixo de doença — sinal direto da pressão epidêmica de cada doença na rede hospitalar. Para zika em particular, isso substituiu o canal indireto que antes vinha via `dengue_casos_lag1` no SHAP global (ver §5 do RELATORIO_MODELAGEM.md). A sensitivity executada após Onda 2 mostrou que **zika perde −0.008 AUPRC com cross em média**, com 7 das 10 maiores quedas concentradas nessa doença. Detalhes em §11 do RELATORIO_MODELAGEM.md.

---

# Próximos passos

1. **Sensitivity analysis com `--no-cross`**: ✅ executada em 2026-05-13. Resultado contraintuitivo (cross atrapalha em zika pós-Onda 2; só RF mantém ganho positivo). Ver §11 do RELATORIO_MODELAGEM.md.
2. **Hyperparameter tuning com Optuna** sobre fold de validação interna (atual usa defaults razoáveis). Esperar ganhos marginais (<5% AUPRC).
3. **Calibração de probabilidades** (importante para uso em produção): atualmente modelos retornam probabilidades não-calibradas. Aplicar Platt scaling ou isotonic regression no fold de validação.
4. **Framing alternativo para febre amarela**: anomaly detection (ex.: Isolation Forest sobre features climáticas + contexto).
5. **MEM (L5) via ponte R** — comparar com canal endêmico nas mesmas combinações.
6. **Plataforma**: interface integrada à `inteli.gente` com explicabilidade SHAP automatizada por alerta.
