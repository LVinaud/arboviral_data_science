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
- **Referência epidemiológica:** município de **residência** para dengue, zika e chikungunya (SINAN); município de **Local Provável de Infecção (LPI)** para febre amarela (transmissão silvestre, fora do município de moradia é regra)
- **Escopo:** dengue, zika, chikungunya e febre amarela (Oropouche excluída por indisponibilidade de dados padronizados no período)
- **Alvo:** dado o conjunto de variáveis observadas até o mês `t`, prever a ocorrência de surto no mês `t+1`

### Perguntas de pesquisa

- **RQ1.** Em que medida modelos de ML treinados com dados multivariados (epidemiológicos + climáticos + indicadores municipais) melhoram a predição de surtos em comparação com baselines simples baseados apenas no histórico recente?
- **RQ2.** Quais grupos de variáveis e quais defasagens temporais (lags de casos e clima) mais contribuem para o desempenho preditivo em nível município–mês?
- **RQ3.** Quão robustas são as previsões frente a valores ausentes, heterogeneidade entre municípios e validação temporal prospectiva?
- **RQ4.** Em que medida o desempenho preditivo depende da definição operacional de surto? Comparamos quatro definições — canal endêmico (mediana + 1.96·σ histórico), Z-score relativo (Z > 2), e dois limiares brutos de incidência (≥ 100 e ≥ 300 casos por 100 mil habitantes) — para avaliar se o modelo é robusto à escolha do rótulo. Concordância entre definições é medida com Cohen's kappa.

## Estado atual

### Pipeline de dados — concluído

O pipeline de ingestão está **100% implementado** para todos os 645 municípios do estado de São Paulo. Cada fonte gera um arquivo `.parquet` em `data/interim/`:

| Arquivo interim | Fonte | Cobertura | Como foi obtido |
|---|---|---|---|
| `sinan_dengue.parquet` | SINAN/DATASUS | 2015–2025, mensal | Script FTP automático |
| `sinan_zika.parquet` | SINAN/DATASUS | 2015–2025, mensal | Script FTP automático |
| `sinan_chikungunya.parquet` | SINAN/DATASUS | 2015–2025, mensal | Script FTP automático |
| `febre_amarela.parquet` | MS Dados Abertos (SVS) | 2015–2025, mensal | Download CSV (não está no FTP SINAN) |
| `nasa_power.parquet` | NASA POWER API | 2015–2025, mensal | Script API automático |
| `saude.parquet` | CNES/LT + SIM/DATASUS | 2015–2025, mensal | Script FTP automático |
| `munic.parquet` | IBGE MUNIC 2018/2020 | estático | Download manual |
| `ibge.parquet` | IBGE SIDRA (PIB + pop) | 2002–2023, anual | Download manual |
| `socioeconomico.parquet` | IDH-M (PNUD) + CAPAG (STN) | estático + 2018–2025 | Download manual |
| `sinisa.parquet` | SINISA | 2023–2024, anual | Download manual |
| `habitacao.parquet` | IBGE Censos 2010 e 2022 | estático | Download manual (4 tabelas SIDRA) |

Uma auditoria detalhada de qualidade dos dados está em `AUDITORIA_DADOS.txt`.

### Dataset consolidado — concluído

`src/arboviral/transform/build_master.py` gera `data/processed/municipio_mes.parquet`:

- **85.140 linhas** · 645 municípios SP × 11 anos (2015–2025) × 12 meses
- **57 colunas**: chave, geolocalização (lookup INMET), 12 variáveis SINAN (3 doenças) + 2 de febre amarela, 7 variáveis climáticas (NASA POWER), saúde, PIB/pop/GINI, CAPAG/IDH-M, água/esgoto (SINISA), gestão/desastres (MUNIC), habitação

**Decisões metodológicas documentadas:**
- *População 2024–2025*: forward-fill a partir das estimativas IBGE de 2023 (IBGE só publica até 2023). Alternativa rejeitada: ajustar modelo de tendência populacional. Forward-fill foi escolhida por simplicidade e por ser conservadora — variação populacional municipal anual é tipicamente <2%, dentro da margem de erro da própria estimativa do IBGE.
- *Febre amarela*: agrega por município de Local Provável de Infecção (LPI), não residência (transmissão silvestre).

### Rótulos de surto — concluído

`src/arboviral/labels/build_labels.py` gera `data/processed/labels.parquet`:

- **85.140 linhas × 23 colunas**: chave + 4 doenças × (1 incidência auxiliar + 4 labels binários)
- Configuração centralizada em [`configs/outbreak_label.yaml`](configs/outbreak_label.yaml) (anos epidêmicos por doença, parâmetros das 4 definições, mínimo absoluto de casos)
- Entry point imprime taxa de positivos por (doença × definição) e Cohen's kappa par a par

**Taxa de positivos observada (% de surtos no dataset):**

| Doença | L1 canal | L2 zscore | L3 inc100 | L4 inc300 |
|---|---:|---:|---:|---:|
| Dengue | 16.21% | 13.38% | 21.12% | 11.79% |
| Chikungunya | 1.76% | 1.59% | 0.38% | 0.14% |
| Zika | 0.60% | 0.53% | 0.04% | 0.01% |
| Febre amarela | 0.03% | 0.03% | 0.00% | 0.00% |

**Concordância entre definições (Cohen's kappa) — primeiros achados (RQ4):**
- L1 (canal) vs L2 (z-score): κ > 0.88 em todas as doenças → são definições praticamente equivalentes
- Dengue: L3 vs L4 (κ=0.67) e L1 vs L3 (κ=0.52) capturam fenômenos parcialmente distintos
- Zika e FA: definições estatísticas degeneram (baseline ≈ 0) e ficam essencialmente equivalentes a "qualquer caso ≥ 5"
- Implicação: para dengue, comparar todas as definições é informativo; para FA, modelagem clássica é inviável e isso por si só é um achado

### Pipeline de modelagem — implementado

Pipeline completo de features → treino → análise, com foco em **explicabilidade** (a plataforma final precisa justificar o alerta para o gestor):

**Features** ([`src/arboviral/features/build_features.py`](src/arboviral/features/build_features.py)) — gera `data/processed/features.parquet` (117 colunas):
- Lags de casos (t-1, t-2, t-3, t-6, t-12) e de incidência (t-1..t-3) por doença
- Rolling means (janelas 3 e 6 meses) e tendência linear
- Lags climáticos (precip, temp, umidade em t-1, t-2, roll3) — literatura aponta efeito 1-2 meses
- Sazonalidade cíclica: `mes_sin`, `mes_cos`
- Estáticas e anuais já no master (MUNIC, habitação, IDH, GINI, PIB, CAPAG, SINISA)
- **Sem leakage**: todas as features no instante t usam apenas dados ≤ t

**Validação** ([`src/arboviral/evaluation/splits.py`](src/arboviral/evaluation/splits.py)) — *expanding window* com 3 dobras:
- Fold 1: treina ≤ 2021, testa target_year=2022
- Fold 2: treina ≤ 2022, testa target_year=2023
- Fold 3: treina ≤ 2023, testa target_year=2024
- 2025 reservado para demonstração futura

**Portfolio de modelos** ([`src/arboviral/models/`](src/arboviral/models/)):

| Modelo | Tipo | Explicabilidade |
|---|---|---|
| Persistência | Baseline trivial (P(t+1) = surto(t)) | N/A |
| Climatologia | Baseline trivial (frequência histórica por mun/mês) | N/A |
| LogReg | Intrinsecamente interpretável | Coeficientes |
| **EBM** (interpret-ml) | Intrinsecamente interpretável | Curvas de contribuição por feature |
| Random Forest | Black-box | SHAP |
| XGBoost | Black-box | SHAP |
| LightGBM | Black-box | SHAP |

Todos os modelos ML usam `class_weight='balanced'` (XGBoost via `scale_pos_weight`) — para detalhes pedagógicos sobre desbalanceamento de classes ver [`AUDITORIA_DADOS.txt`](AUDITORIA_DADOS.txt).

**Métricas** ([`src/arboviral/evaluation/metrics.py`](src/arboviral/evaluation/metrics.py)):
- Primária: **AUPRC** (Average Precision) — robusta a class imbalance, padrão em vigilância
- Lift sobre baseline aleatório: AUPRC / prevalência
- Secundárias: F1, recall (sensibilidade), specificity, precision

**Explicabilidade** ([`src/arboviral/evaluation/explain.py`](src/arboviral/evaluation/explain.py)):
- `shap_tree()`: TreeExplainer para RF/XGB/LGBM
- `importancias_logreg()` / `importancias_ebm()`: extração nativa
- `shap_por_predicao()`: top features que justificam UMA predição (use case da plataforma)

**Treino e análise:**
```bash
python -m arboviral.train                # treina 4 doenças × 4 definições × 7 modelos × 3 folds
python -m arboviral.analyze_results       # gera tabelas-resumo (AUPRC por combinação, ranking, etc.)
```

Saída: `data/processed/model_results.parquet` (uma linha por combinação) + tabelas CSV.

### Próximas etapas

1. **Análise dos resultados** após o treino completo (RQ1: ML melhora sobre baselines? RQ4: definição importa?)
2. **Sensitivity analysis com `--no-cross`**: comparar performance com vs sem features cross-doença
3. **Hyperparameter tuning** com Optuna (atual usa defaults razoáveis)
4. **Plataforma**: interface integrada à inteli.gente, exibindo top features SHAP para cada alerta
5. Trabalho futuro: MEM (L5) via ponte R, redes neurais (LSTM/Transformer)

## Variáveis e fontes de dados

Cada linha do dataset é identificada por **(município, ano, mês)**. A tabela abaixo lista todas as variáveis acordadas, organizadas por grupo temático.

### Geolocalização e período

| Campo | Descrição |
|---|---|
| ID município / Nome | Código IBGE e nome do município |
| ID Região de Saúde / Nome | Região de Saúde a que o município pertence |
| Ano / Mês | Referência temporal da observação |
| Porte (população total estimada) | Estimativa populacional do município no período |

### Arboviroses — Bases: SINAN/DATASUS + MS Dados Abertos (febre amarela)

**Dengue, Zika e Chikungunya** (município de **residência**, fonte SINAN FTP):

| Variável | Descrição |
|---|---|
| `{doenca}_casos` | Total de casos notificados no município/mês |
| `{doenca}_casos_provaveis` | Casos com classificação provável (CLASSI_FIN específico por doença) |
| `{doenca}_obitos` | Óbitos confirmados (EVOLUCAO ∈ {2,3,4}) |
| `{doenca}_internacoes` | Internações registradas (HOSPITALIZ == 1) |

**Febre Amarela** (município de **Local Provável de Infecção (LPI)**, fonte MS dados abertos):

| Variável | Descrição |
|---|---|
| `febre_amarela_casos` | Total de casos confirmados no município/mês |
| `febre_amarela_obitos` | Óbitos confirmados (campo OBITO == 'SIM') |

> Febre amarela não está no FTP público do SINAN (sistema separado por ser doença silvestre). Dados obtidos do CSV publicado no portal `dadosabertos.saude.gov.br` (atualização periódica pela SVS).
> Variáveis derivadas (sexo predominante, faixa etária predominante, coeficiente de incidência, taxa de letalidade etc.) serão calculadas no módulo `features/` a partir das variáveis brutas acima e da `populacao_estimada`.

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
├── data/                        # local; data/raw e data/processed são gitignored
│   ├── raw/                     # arquivos brutos (gitignored — Zenodo no futuro)
│   ├── interim/                 # 1 parquet por fonte (saída de ingestion/) — versionado
│   ├── processed/               # municipio_mes, labels, features, model_results — gitignored
│   └── lookup/                  # tabelas pequenas versionadas (município↔estação INMET)
├── src/arboviral/
│   ├── io.py                    # caminhos canônicos
│   ├── ingestion/               # 1 módulo por fonte
│   │   ├── sinan.py + sinan_ftp.py + sinan_api.py     # dengue, zika, chikungunya
│   │   ├── febre_amarela.py     # FA (dados abertos MS — não está no FTP SINAN)
│   │   ├── nasa_power.py        # clima
│   │   ├── saude.py             # CNES + SIM (leitos, mortalidade)
│   │   ├── munic.py             # IBGE MUNIC (gestão e desastres)
│   │   ├── ibge.py              # PIB, população, GINI
│   │   ├── socioeconomico.py    # IDH-M + CAPAG
│   │   ├── snis.py              # água e esgoto (SINISA)
│   │   └── habitacao.py         # aglomerados subnormais e favelas (Censos 2010, 2022)
│   ├── transform/build_master.py    # consolida 10 interim → municipio_mes.parquet
│   ├── labels/                  # rótulos de surto (4 definições, RQ4)
│   │   ├── outbreak.py          # funções por definição (canal, zscore, inc100, inc300)
│   │   └── build_labels.py      # entry point — gera labels.parquet + Cohen's kappa
│   ├── features/build_features.py   # lags, rolling, sazonalidade — gera features.parquet
│   ├── models/                  # portfolio: baselines + classificadores
│   │   ├── baselines.py         # persistência, climatologia
│   │   └── classifiers.py       # logreg, ebm, rf, xgb, lgbm
│   ├── evaluation/
│   │   ├── splits.py            # expanding window (3 folds)
│   │   ├── metrics.py           # AUPRC + lift, F1, recall, specificity
│   │   └── explain.py           # SHAP (tree models) + interpretação nativa (LogReg, EBM)
│   ├── train.py                 # treina (4 doenças × 4 def × 7 modelos × 3 folds)
│   └── analyze_results.py       # agrega resultados em tabelas para o relatório
├── configs/                     # contratos do projeto (YAML)
│   ├── schema.yaml              # esquema canônico do dataset município–mês
│   ├── outbreak_label.yaml      # parâmetros das 4 definições de surto
│   └── municipios_poc.yaml      # 32 municípios da POC inicial
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

### Dados brutos (`data/raw/`)

`data/raw/` não está versionada no git (arquivos DBC do DATASUS chegam a 275MB).
Os dados brutos serão disponibilizados via **Zenodo** (DOI citável) em versão futura.
Por enquanto, cada módulo de ingestão em `src/arboviral/ingestion/` tem um docstring
descrevendo quais arquivos espera em `data/raw/<fonte>/` e de onde obtê-los.

Depois de obter os dados brutos, rode a ingestão:

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
