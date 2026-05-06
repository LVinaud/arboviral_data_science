# arboviral_data_science

> Plataforma Automatizada para Prevenção e Resposta a Arboviroses Usando Inteligência Artificial

Iniciação Científica (Programa Unificado de Bolsas — PUB) desenvolvida no **Instituto de Ciências Matemáticas e de Computação da USP (ICMC-USP)** em São Carlos.

- **Aluno:** Lázaro Pereira Vinaud Neto
- **Orientador:** Prof. André Carlos Ponce de Leon Ferreira de Carvalho

## Motivação

Arboviroses como dengue, zika e chikungunya representam um desafio recorrente para a saúde pública brasileira, com impacto direto em atendimentos, internações e na organização de campanhas de prevenção em nível municipal. A dinâmica de transmissão é multifatorial — variáveis climáticas, ambientais, demográficas e de infraestrutura urbana — e, embora exista um volume crescente de indicadores públicos, esse potencial informacional permanece subaproveitado por gestores municipais devido a barreiras técnicas, fragmentação dos dados e ausência de ferramentas operacionais que produzam alertas acionáveis em tempo hábil.

Antecipar períodos de maior risco permite intensificar vigilância, planejar insumos, priorizar visitas de agentes comunitários e direcionar campanhas. Este projeto investiga a viabilidade de incorporar um módulo de **previsão de surtos de arboviroses** em nível municipal à plataforma **inteli.gente** — usada para visualização e apoio à gestão municipal — com previsões explicáveis para gestores e cidadãos.

## Formulação do problema

Tarefa de **classificação supervisionada** com granularidade **município–mês**:

- **Chave:** `(código IBGE, ano, mês)`
- **Referência epidemiológica:** município de **residência** (não de notificação)
- **Escopo:** dengue, zika e chikungunya (Oropouche foi excluída por indisponibilidade de dados padronizados no período)
- **Alvo:** dado o conjunto de variáveis observadas até o mês `t`, prever a ocorrência de surto no mês `t+1`

### Perguntas de pesquisa

- **RQ1.** Em que medida modelos de ML treinados com dados multivariados (epidemiológicos + climáticos + indicadores municipais) melhoram a predição de surtos em comparação com baselines simples baseados apenas no histórico recente?
- **RQ2.** Quais grupos de variáveis e quais defasagens temporais (lags de casos e clima) mais contribuem para o desempenho preditivo em nível município–mês?
- **RQ3.** Quão robustas são as previsões frente a valores ausentes, heterogeneidade entre municípios e validação temporal prospectiva?

## Estado atual

### Pipeline de dados — concluído

O pipeline de ingestão está **100% implementado** para todos os 645 municípios do estado de São Paulo. Cada fonte gera um arquivo `.parquet` em `data/interim/`:

| Arquivo interim | Fonte | Cobertura | Como foi obtido |
|---|---|---|---|
| `sinan_dengue.parquet` | SINAN/DATASUS | 2015–2025, mensal | Script FTP automático |
| `sinan_zika.parquet` | SINAN/DATASUS | 2015–2025, mensal | Script FTP automático |
| `sinan_chikungunya.parquet` | SINAN/DATASUS | 2015–2025, mensal | Script FTP automático |
| `nasa_power.parquet` | NASA POWER API | 2015–2025, mensal | Script API automático |
| `saude.parquet` | CNES/LT + SIM/DATASUS | 2015–2025, mensal | Script FTP automático |
| `munic.parquet` | IBGE MUNIC 2018/2020 | estático | Download manual |
| `ibge.parquet` | IBGE SIDRA (PIB + pop) | 2002–2023, anual | Download manual |
| `socioeconomico.parquet` | IDH-M (PNUD) + CAPAG (STN) | estático + 2018–2025 | Download manual |
| `sinisa.parquet` | SINISA | 2023–2024, anual | Download manual |
| `habitacao.parquet` | IBGE Censos 2010 e 2022 | estático | Download manual (4 tabelas SIDRA) |

Uma auditoria detalhada de qualidade dos dados está em `AUDITORIA_DADOS.txt`.

### Próximas etapas

1. **Consolidação (`build_master.py`).** Juntar todos os parquets em um único `data/processed/municipio_mes.parquet` com chave `(cod_ibge, ano, mes)`.
2. **Rótulo de surto.** Formalizar a definição operacional (limiar de incidência por 100 mil habitantes) e calcular o target binário.
3. **Modelagem.** Implementar e avaliar Random Forest, XGBoost e LightGBM contra baselines de persistência, sob validação temporal (*expanding window*) com métricas F1 e AUPRC.
4. **Plataforma.** Interface integrada à inteli.gente com explicabilidade via SHAP.

## Variáveis e fontes de dados

Cada linha do dataset é identificada por **(município, ano, mês)**. A tabela abaixo lista todas as variáveis acordadas, organizadas por grupo temático.

### Geolocalização e período

| Campo | Descrição |
|---|---|
| ID município / Nome | Código IBGE e nome do município |
| ID Região de Saúde / Nome | Região de Saúde a que o município pertence |
| Ano / Mês | Referência temporal da observação |
| Porte (população total estimada) | Estimativa populacional do município no período |

### Arboviroses — Base: SINAN/DATASUS

Abrange dengue, zika e chikungunya (município de **residência**).

| Variável | Descrição |
|---|---|
| Casos acumulados | Total de casos acumulados no período |
| Casos prováveis | Casos com classificação provável |
| Total de óbitos | Óbitos confirmados |
| Total de internações | Internações registradas |
| Sexo (Masc/Fem) e quantidade de casos | Distribuição por sexo |
| Faixa etária (descrição) e quantidade de casos | Distribuição por faixa etária |
| Coeficiente de incidência | Casos por 100 mil habitantes |
| Coeficiente de prevalência | Prevalência calculada |
| Taxa de internação (%) | Internações sobre casos |
| Taxa de letalidade (%) | Óbitos sobre casos confirmados |

### Saúde — Base: DATASUS

| Variável | Descrição |
|---|---|
| Leitos hospitalares na rede pública municipal | Disponibilidade de leitos públicos |
| Médicos disponíveis na rede pública municipal | Disponibilidade de médicos públicos |
| Mortalidade materna | Indicador de qualidade da atenção à saúde |

### Gestão e Serviços de Vigilância — Base: IBGE MUNIC 2018

| Código | Descrição |
|---|---|
| Msau28 | Existência do Programa de Agentes Comunitários de Saúde |
| Msau541 | Vigilância sanitária realizada pela gestão municipal |
| Msau542 | Vigilância epidemiológica |
| Msau543 | Controle de endemias |

### Desastres Naturais — Base: IBGE MUNIC (2020 e 2017)

| Código | Descrição |
|---|---|
| Mgrd01 | Município atingido por seca nos últimos 4 anos |
| Mgrd06 | Município atingido por alagamentos nos últimos 4 anos |
| Mgrd07 | Município atingido por processo erosivo acelerado nos últimos 4 anos |
| Mgrd08 | Município atingido por enchentes ou inundações graduais nos últimos 4 anos |
| Mgrd11 | Município atingido por enxurradas ou inundações bruscas nos últimos 4 anos |
| Mgrd14 | Município atingido por escorregamentos ou deslizamentos de encostas nos últimos 4 anos |
| Mgrd201 | Existência de mapeamentos de áreas de risco de enchentes ou inundações |

### Meteorológicos — Base: INMET (lag de 30 dias)

Variáveis climáticas agregadas mensalmente (mínimo, média e máximo quando aplicável), associando cada município à estação meteorológica automática do INMET mais próxima por coordenadas geográficas.

| Variável |
|---|
| Precipitação mínima / média / máxima |
| Temperatura mínima / média / máxima |
| Umidade relativa mínima / média / máxima |
| Pressão atmosférica média |
| Velocidade média do vento |

### Socioeconômico — Bases: IBGE, Atlas IDH-M, CAPAG (STN), DATASUS

| Variável | Fonte |
|---|---|
| PIB per capita do município | IBGE |
| Índice de Desenvolvimento Humano Municipal (IDH-M) | Atlas do Desenvolvimento Humano no Brasil |
| Capacidade de pagamento dos municípios (CAPAG) | Sistema do Tesouro Nacional |
| Índice de GINI da renda domiciliar per capita | DATASUS |

### Água e Esgoto — Base: SNIS / SINISA

> Dados de 2023 liberados; 2024 e 2025 ainda não disponibilizados pelo SINISA.

| Código | Descrição |
|---|---|
| IAG0001 | Atendimento da população total com rede de abastecimento de água (%) |
| IES0001 | Atendimento da população total com rede coletora de esgoto (%) |
| IES2004 | Esgoto tratado referido ao esgoto coletado (%) |

### Habitação — Bases: IBGE Aglomerados Subnormais (Censo 2010), IBGE Favelas (Censo 2022)

Dados estáticos censitários. Municípios sem aglomerados/favelas têm NaN (0 implícito).

| Campo | Fonte SIDRA | Descrição |
|---|---|---|
| `num_aglom_subnorm_2010` | Tabela 3379 | Número de aglomerados subnormais (Censo 2010) |
| `pop_aglom_subnorm_2010` | Tabela 3381 | População residente em aglomerados subnormais (Censo 2010) |
| `num_favelas_2022` | Tabela 9883 | Número de favelas e comunidades urbanas (Censo 2022) |
| `pop_favelas_2022` | Tabela 9900 | População residente em favelas e comunidades urbanas (Censo 2022) |
| MMAM2612 | IBGE MUNIC | Existência de moradia em situação de risco ambiental |

### Urbanização — Base: SINISA 2024

| Código | Descrição |
|---|---|
| IAP0001 | Parcela de vias públicas pavimentadas na área urbana (%) |

## Estrutura do repositório

```
arboviral_data_science/
├── README.md
├── LICENSE
├── pyproject.toml               # dependências e metadados do pacote
├── configs/                     # contratos do projeto
│   ├── schema.yaml              # esquema canônico do dataset município–mês
│   ├── municipios_poc.yaml      # 32 municípios da POC
│   └── outbreak_label.yaml      # definição operacional do rótulo de surto
├── data/                        # local, fora do git (exceto lookup/)
│   ├── raw/                     # arquivos baixados manualmente, por fonte
│   ├── interim/                 # 1 parquet por fonte (saída de src/arboviral/ingestion)
│   ├── processed/               # municipio_mes.parquet (saída do build_master)
│   ├── manual/                  # planilhas editadas à mão
│   └── lookup/                  # tabelas pequenas versionadas (município↔estação INMET, etc.)
├── src/arboviral/
│   ├── io.py                    # caminhos canônicos
│   ├── ingestion/               # 1 módulo por fonte: sinan, inmet, munic, saude, ibge,
│   │                            # socioeconomico, snis, habitacao
│   ├── transform/               # build_master.py — junta os parquets intermediários
│   ├── features/                # lags, médias móveis, normalizações
│   ├── labels/                  # rótulo de surto
│   ├── models/                  # baselines, RF, XGBoost, LightGBM
│   └── evaluation/              # split temporal, métricas, SHAP
├── notebooks/                   # exploração e prototipagem
├── tests/                       # smoke tests e validação de schema
└── contexto/                    # material legado (Drive, relatório PDF) — gitignored
```

> A plataforma web vive em repositório separado (`arboviral_platform`, ainda não criado).

## Como começar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Depois, baixe os arquivos brutos para `data/raw/<fonte>/` e rode a ingestão correspondente:

```bash
python -m arboviral.ingestion.sinan          # ou inmet, munic, saude, ibge, ...
python -m arboviral.transform.build_master   # consolida tudo
```

O dataset final é gravado em `data/processed/municipio_mes.parquet`.

Cada módulo em `src/arboviral/ingestion/` tem um docstring no topo descrevendo
quais arquivos espera em `data/raw/<fonte>/` e quais colunas produz.

## Referências principais

- Bergmeir, Hyndman & Koo (2018). *A note on the validity of cross-validation for evaluating autoregressive time series prediction.* CSDA.
- Hewamalage, Ackermann & Bergmeir (2023). *Forecast evaluation for data scientists: common pitfalls and best practices.* DMKD.
- Leung et al. (2023). *A systematic review of dengue outbreak prediction models.* PLOS NTD.
- Lundberg & Lee (2017). *A unified approach to interpreting model predictions (SHAP).* NeurIPS.
- Magalhaes et al. (2020). *The endless challenges of arboviral diseases in Brazil.* TMID.
- Rahman, Amrin & Shiddik (2025). *Dengue early warning system and outbreak prediction tool in Bangladesh using interpretable tree-based machine learning model.* Health Science Reports.
- Saito & Rehmsmeier (2015). *The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets.* PLOS ONE.

A lista completa está no relatório parcial em [contexto/Relatório Parcial - Arboviroses.pdf](contexto/Relatório%20Parcial%20-%20Arboviroses.pdf).

## Licença

[MIT](LICENSE) © 2026 Lázaro Vinaud
