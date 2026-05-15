# arboviral_data_science

> Plataforma Automatizada para Prevenção e Resposta a Arboviroses Usando Inteligência Artificial

> **Estrutura do repositório (branch única `main` desde 2026-05-08):**
> - `src/arboviral/` — pipeline de dados, rotulagem e modelagem (ciência de dados pura, autossuficiente)
> - `app/` — interface Streamlit para gestores; depende do pacote `arboviral`, mas o pacote NÃO depende do app. Veja [`app/README.md`](app/README.md).

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
| `densidade.parquet` | IBGE — área dos municípios + estimativa pop | estático | Script automático (`scraping/ibge_areas.py`) |
| `mapbiomas.parquet` | MapBiomas Brasil — Coleção 10.1 | 2015–2024, anual | Script automático (`scraping/mapbiomas.py`) |
| `esf.parquet` | e-Gestor APS — cobertura ESF | 2015–2025, mensal | Script automático (`scraping/esf_coverage.py`, API REST) |
| `vacinacao_fa.parquet` | DATASUS PNI — cobertura vacinal FA | 2015–2025, anual (gap 2017) | CSV manual (TabNet, formato inteli.gente) |
| `mobilidade_pendular.parquet` | IBGE Censo 2010 (microdados PESS) + IBGE Censo 2022 (SIDRA 10329) | 2010 + 2022 (série anual no master) | Script automático (`scraping/mobilidade_pendular.py`); 2010 reconstrói matriz O-D via V0660/V6604 ponderada por V0010, 2022 traz só saídas via API REST |
| `sih_sus.parquet` | DATASUS — SIH-SUS, AIH-RD (internações hospitalares) | 2015–2025, mensal | Script automático (`scraping/sih_sus.py`); classifica internação por CID-10 (A90, A91, A92.0, A92.5, A92.8, A95) e agrega por município de residência |

Uma auditoria detalhada de qualidade dos dados está em `AUDITORIA_DADOS.txt`.

### Dataset consolidado — concluído

`src/arboviral/transform/build_master.py` gera `data/processed/municipio_mes.parquet`:

- **85.140 linhas** · 645 municípios SP × 11 anos (2015–2025) × 12 meses
- **85 colunas**: chave, geolocalização (lookup INMET), 12 variáveis SINAN (3 doenças) + 9 de latência SINAN (proxy de subnotificação) + 2 de febre amarela, 7 variáveis climáticas (NASA POWER), saúde, PIB/pop/GINI, CAPAG/IDH-M, água/esgoto (SINISA), gestão/desastres (MUNIC), habitação, área e densidade populacional, 5 categorias de uso do solo (MapBiomas), 5 da cobertura APS/ESF (e-Gestor MS), 1 de cobertura vacinal contra febre amarela (PNI/DATASUS), 2 de mobilidade pendular intermunicipal (Censo 2010 microdados em 2015–2021 + Censo 2022 SIDRA em 2022–2025) e **4 de internações hospitalares pelo SUS por arbovirose (SIH-SUS, CID A90/A91/A92.0/A92.5/A92.8/A95)**

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

**Features** ([`src/arboviral/features/build_features.py`](src/arboviral/features/build_features.py)) — gera `data/processed/features.parquet` (**140 colunas após Onda 1**):
- Lags de casos (t-1, t-2, t-3, t-6, t-12) e de incidência (t-1..t-3) por doença
- Rolling means (janelas 3 e 6 meses) e tendência linear
- Lags climáticos (precip, temp, umidade em t-1, t-2, roll3) — literatura aponta efeito 1-2 meses
- Sazonalidade cíclica: `mes_sin`, `mes_cos`
- Estáticas e anuais já no master (MUNIC, habitação, IDH, GINI, PIB, CAPAG, SINISA)
- **Onda 1 (incorporada em 2026-05)**: 5 categorias de uso do solo MapBiomas, 2 de densidade IBGE, 1 de cobertura vacinal FA, 5 de cobertura APS/ESF (com one-hot da metodologia AB/APS), 9 de latência SINAN por doença (mediana, p90, n_casos em lag1) — total +23 colunas em relação à versão anterior (117 → 140)
- **Sem leakage**: todas as features no instante t usam apenas dados ≤ t. Latência e ESF entram como lag1 (mês anterior) por serem informações operacionais que só ficam disponíveis depois das notificações

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

**Explicabilidade** ([`src/arboviral/evaluation/explain.py`](src/arboviral/evaluation/explain.py)) — uniforme entre todos os modelos do portfolio (atualizado 2026-05):
- `explicacao_local(modelo, X_amostra)`: top features que justificam UMA predição. Despacha automaticamente pelo tipo do estimador final do pipeline:
  - **RandomForest / XGBoost / LightGBM** → SHAP TreeExplainer (post-hoc, exato em árvores)
  - **Regressão Logística** → coeficiente × valor padronizado (a soma + intercept reproduz exatamente `decision_function`; sanity check passou)
  - **EBM (Explainable Boosting Classifier)** → API nativa `clf.explain_local()` do interpret-ml. Termos de interação 'a & b' têm a contribuição distribuída entre os pares para preservar o ranking por feature de entrada
- Output uniforme: DataFrame com `feature, valor_observado, contribuicao, abs_contribuicao, sign, metodo`. A coluna `metodo` documenta qual técnica foi usada (útil para auditoria e para a UI mostrar ao gestor).
- Funções legadas mantidas: `shap_tree()`, `importancias_logreg()`, `importancias_ebm()`, `shap_por_predicao()` (alias retrocompat).
- Use case da plataforma: o app Streamlit (`app/`) chama `explicacao_local()` para qualquer modelo selecionado pelo gestor — não está mais limitado a RF/XGB/LGBM.

**Treino e análise:**
```bash
python -m arboviral.train                # treina 4 doenças × 4 definições × 7 modelos × 3 folds (defaults)
python -m arboviral.train --no-cross     # mesma coisa, sem features cross-doença (sensitivity §11)
python -m arboviral.analyze_results       # gera tabelas-resumo (AUPRC por combinação, ranking, etc.)
python -m arboviral.analyze_no_cross --historico   # PRE × POS-Onda 2 com Wilcoxon (item 1.4)
python -m arboviral.tune_optuna           # 15 estudos × 100 trials cada (item 1.5; ~10h CPU)
python -m arboviral.train_tuned           # aplica best_params nos 3 folds oficiais
python -m arboviral.analyze_thresholds    # sweep precision×recall por threshold (§13)
python -m arboviral.build_reports         # consolida RELATORIO_MODELAGEM.md
```

Saídas principais em `data/processed/`:
- `model_results.parquet` — métricas defaults
- `model_results_TUNED.parquet` — métricas após tuning Optuna
- `predictions.parquet` — uma linha por amostra de teste (análises post-hoc)
- `optuna_studies/*.db` — histórico completo de cada trial (auditável)
- `tuning_comparison.csv` — pivot default × tuned com Δ AUPRC

### Resultados — primeira rodada completa

Pipeline rodado fim-a-fim em 4 doenças × 4 definições × 7 modelos × 3 folds = **315 combinações** (21 puladas por classe degenerada em zika×inc300 e febre amarela). Documento completo em [`RELATORIO_MODELAGEM.md`](RELATORIO_MODELAGEM.md).

**Ranking global (AUPRC médio sobre todas as combinações):**

| Modelo | AUPRC | Lift médio | Notas |
|---|---:|---:|---|
| **RF** | **0.397** | 276× | Melhor desempenho global |
| EBM | 0.367 | 272× | Intrinsecamente interpretável; quase tão bom quanto RF |
| LGBM | 0.372 | 107× | Bom AUPRC, lift menor |
| XGB | 0.362 | 271× | |
| **Persistência** | 0.347 | 27× | Baseline surpreendentemente forte (autocorrelação) |
| LogReg | 0.288 | 20× | Linear não captura interações ricas |
| Climatologia | 0.151 | 12× | Sazonalidade pura não basta |

**Achados principais (RQ1, RQ2, RQ4):**
- **RQ1**: ML supera baselines em ~14% relativo (RF 0.397 vs persistência 0.347). Ganho mais expressivo em definições raras (chikungunya×inc100: ganho de +0.19 AUPRC).
- **RQ4**: definição importa MUITO. Para dengue, AUPRC varia de 0.483 (zscore) a **0.792 (inc100)** — a escolha do rótulo tem mais impacto que a escolha do modelo.
- **RQ2**: para dengue, top features são lags próprios (`dengue_incid_lag1`, `dengue_casos_trend3`) e clima (`temp_min`, `precip_media_dia_roll3`). **Para zika, features de DENGUE são as mais preditivas** — valida empiricamente a inclusão de features cross-doença (mesmo vetor *Aedes aegypti*).
- **Casos onde ML não supera persistência**: chikungunya×inc300 (raridade extrema), zika×canal/zscore (autocorrelação domina). Documentados como achado.

**Análise de antecipação (achado central — utilidade real):**

ML supera persistência **onde mais importa**: prevendo o INÍCIO de surto (transição 0→1), não apenas mantendo predições durante surtos em curso.

| Modelo | Recall em INÍCIO de surto (dengue × inc100) | Falsos alarmes |
|---|---:|---:|
| persistência | **0.0%** | 0% |
| Random Forest | **31.4%** | 7.9% |
| XGBoost | **35.9%** | 8.3% |

Random Forest antecipa **1 a cada 3 surtos novos** com 1 mês de antecedência, com baixa taxa de falsos alarmes. Persistência (modelo trivial) **nunca antecipa**. Esse é o resultado que justifica o uso de ML em vigilância. Detalhes em [`RELATORIO_MODELAGEM.md`](RELATORIO_MODELAGEM.md) seção 7.

**Caso de uso da plataforma — exemplo real:**

> Município **3548500**, abril/2024 (chikungunya): probabilidade prevista = **99%**, surto real = **sim**.
> 
> Razões (SHAP):
> - **+** chikungunya teve 557 casos no mês passado
> - **+** média 6 meses = 206 casos (epidemia em curso)
> - **+** incidência 128/100k (alta)
> - **+** crescimento 348 → 557 (tendência ascendente)

### Resultados — segunda rodada (Onda 1 de novas fontes)

Em maio/2026, integramos 5 fontes do top 10 do roadmap (MapBiomas, ESF, latência SINAN, densidade, vacinação FA — ver [`ROADMAP.md`](ROADMAP.md) §2). O re-treino completo (~2h, mesmas 315 combinações) permite quantificar o ganho real das novas features:

**Top ganhos absolutos em AUPRC** (média dos 3 folds, comparado ao treino pré-Onda 1):

| Cenário | AUPRC pré | AUPRC pós | Δ | Δ relativo |
|---|---:|---:|---:|---:|
| **zika × inc100 (RF)** | 0.014 | **0.101** | +0.088 | **+640%** |
| zika × canal (XGB) | 0.077 | 0.115 | +0.038 | +49% |
| zika × zscore (XGB) | 0.057 | 0.094 | +0.037 | +65% |
| zika × canal (RF) | 0.130 | 0.165 | +0.036 | +27% |
| dengue × canal (LGBM/XGB) | 0.543 | 0.569 | +0.027 | +5% |
| chikungunya × canal (XGB) | 0.287 | 0.312 | +0.024 | +8% |

**Achado defensável**: zika é a doença mais beneficiada (média +0.0085 vs +0.0011 dengue, -0.0017 chikungunya). Coerente com a hipótese cross-doença + as novas fontes:
- Cobertura ESF afeta detecção (vigilância), reduzindo viés de subnotificação
- MapBiomas (uso urbano) + densidade IBGE = pressão vetorial *Aedes*
- Cross-doença (já existia) com agora **mais features de dengue disponíveis** → zika "herda" mais sinal

A narrativa para o relatório/artigo é forte: **ao adicionar fontes ambientais (MapBiomas), de cobertura sanitária (ESF, vacinação FA) e de qualidade da vigilância (latência SINAN), o modelo passa a capturar surtos de zika que antes eram invisíveis** (AUPRC 0.014 → 0.101 em zika×inc100).

**Pioras pontuais documentadas** (provavelmente ruído de fold em definições raras):
- chikungunya × inc100 (LGBM): -0.105 — a definição inc100 tem só 0.38% de prevalência; alta variância entre folds
- febre amarela: continua NaN em todas as definições (raridade impede aprendizado clássico)

### Próximas etapas

1. ✅ **Sensitivity analysis com `--no-cross`** (2026-05-14): ganho cross-doença concentrado em RF×chikungunya (+0.056 Δ AUPRC); demais cenários flutuam pequeno. Detalhes em [`RELATORIO_MODELAGEM.md` §11](RELATORIO_MODELAGEM.md).
2. ✅ **Hyperparameter tuning Optuna** (2026-05-15): 15 estudos × 100 trials. Defaults já estão ~no teto: melhor cenário do projeto subiu de 0.795 (RF default) → 0.798 (LGBM tuned, dengue×inc100). Em chik/zika, tuning piorou por overfit ao fold 2021. Detalhes em [`RELATORIO_MODELAGEM.md` §12](RELATORIO_MODELAGEM.md).
3. **Calibração de probabilidades** (importante para uso em produção) — pendente, listado em ROADMAP §3.2 (rumo a conferência)
4. **Plataforma**: interface integrada à inteli.gente, exibindo top features para cada alerta. App Streamlit funcional em `app/` — design system completo, 7 telas (Visão geral, Alertas, Município, Mapa, Comparativo, Variáveis, Sobre), interface bilíngue PT/EN (toggle no topo da sidebar; ver [`app/i18n/README.md`](app/i18n/README.md)), explicabilidade local para todos os modelos do portfolio (não apenas árvores).
5. **Fontes restantes do top 10** (após Onda 2): LIRAa (#1 — pausado, aguardando LAI à CCD-SP) e NDVI (#10 — sazonalidade vegetal via Earth Engine). O item original #8 (eventos massivos) foi descartado por inviabilidade prática (curadoria manual desproporcional ao ganho).
6. Trabalho futuro: MEM (L5) via ponte R, framing alternativo para FA (anomaly detection).

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

### Onda 1 — Fontes integradas em maio/2026

#### Densidade populacional — Base: IBGE Áreas Territoriais (FTP)

| Variável | Descrição |
|---|---|
| `area_km2` | Área territorial do município em km² (IBGE 2024) |
| `densidade_2023` | Habitantes por km² calculado como `populacao_2023 / area_km2` |

> Fonte: `geoftp.ibge.gov.br/.../areas_territoriais/2024/AR_BR_RG_UF_RGINT_RGI_MUN_2024.xls`. Cobertura 645/645 municípios SP, 100% completude. Densidade varia de 3.6 hab/km² (interior) a 14.593 hab/km² (metropolitano).
>
> Coleta: [`scraping/ibge_areas.py`](src/arboviral/scraping/ibge_areas.py) · Parsing: [`ingestion/densidade.py`](src/arboviral/ingestion/densidade.py).

#### Uso e cobertura do solo — Base: MapBiomas Brasil Coleção 10.1

| Variável | Descrição |
|---|---|
| `pct_floresta` | % de área com floresta natural |
| `pct_agricultura` | % com agropecuária (pastagem + lavoura + silvicultura) |
| `pct_nao_vegetado` | % urbanizado / não vegetado (cidades, infraestrutura, mineração) |
| `pct_agua` | % de água / ambiente marinho |
| `pct_natural_nao_florestal` | % de formação natural não florestal (cerrado aberto, campos, etc.) |

> Fonte: MapBiomas Brasil Coleção 10.1, DOI [10.58053/MapBiomas/SJZOLT](https://doi.org/10.58053/MapBiomas/SJZOLT). Cobertura 645/645 municípios SP × anos 2015-2024 (2025 por ffill — variação <1%/ano). Mediana SP: agricultura 74%, floresta 9.4%, urbanizado 1.3%.
>
> Coleta: [`scraping/mapbiomas.py`](src/arboviral/scraping/mapbiomas.py) (Google Drive, ~75 MB) · Parsing: [`ingestion/mapbiomas.py`](src/arboviral/ingestion/mapbiomas.py).

#### Cobertura da Atenção Primária à Saúde — Base: e-Gestor APS / Ministério da Saúde

| Variável | Descrição |
|---|---|
| `esf_metodologia` | Categórica `'AB'` (2015–2020) ou `'APS'` (2021–presente) |
| `esf_cobertura_pct` | % cobertura calculada pelo MS |
| `esf_qt_equipes` | Número de equipes ESF do município |
| `esf_qt_capacidade` | Capacidade total de atendimento (apenas APS, NaN para AB) |
| `esf_pop_referencia` | População usada como denominador pelo MS |

> Fonte: API REST descoberta via DevTools no portal e-Gestor APS — `relatorioaps-prd.saude.gov.br/cobertura/{ab|aps}`. **Quebra metodológica em 2021**: parâmetros, formato dos números (string BR `"12,106,920"` em AB vs int em APS) e nome do campo (`pcCoberturaAb` → `qtCobertura`). A flag `esf_metodologia` permite ao modelo distinguir os dois regimes.
>
> Cobertura: 99.9% das linhas SP (645 municípios × 132 meses, 2015-01 a 2025-12). Coleta automatizada (132 arquivos JSON, ~380 MB raw): [`scraping/esf_coverage.py`](src/arboviral/scraping/esf_coverage.py) · Parsing: [`ingestion/esf.py`](src/arboviral/ingestion/esf.py).

#### Cobertura vacinal contra febre amarela — Base: PNI / DATASUS

| Variável | Descrição |
|---|---|
| `cob_vac_fa_pct` | % da população-alvo imunizada contra febre amarela (anual) |

> Fonte: Programa Nacional de Imunizações (PNI/MS) via TabNet — `tabnet.datasus.gov.br/cgi/tabcgi.exe?pni/cnv/cpniuf.def`. Coleta manual reformatada para o padrão da plataforma inteli.gente (`codigo_ibge, sigla, ano, variavel_valor`). Consulta SQL alternativa via BasedosDados (`br_ms_pni`).
>
> Cobertura SP: 645/645 municípios × 1994-2026 com gaps (2008, 2010, 2011, 2014, 2017). Dentro da janela do master (2015-2025) falta apenas 2017, preenchido por forward-fill no `build_master.py` (cobertura vacinal varia <5p.p./ano em períodos sem campanha; e 2017 não teve mudança brusca da política nacional para SP).
>
> **Achado preliminar relevante**: mediana SP cai de ~94% (2002) para ~74% (2025) — declínio progressivo com implicações para risco populacional, especialmente combinado com `pct_floresta` (MapBiomas) para identificar municípios com matas + população não imunizada.
>
> Valores >100% ocorrem (~25% das linhas) e são preservados sem cap: ocorrem quando o denominador-alvo do PNI fica abaixo do real (migração, estimativa populacional defasada).
>
> Coleta documentada (CGI sem REST estável): [`scraping/pni_febre_amarela.py`](src/arboviral/scraping/pni_febre_amarela.py) · Parsing: [`ingestion/vacinacao_fa.py`](src/arboviral/ingestion/vacinacao_fa.py).

#### Latência de notificação SINAN — Bases: SINAN/DATASUS (extensão da ingestão existente)

| Variável | Descrição |
|---|---|
| `{doenca}_latencia_mediana` | Mediana de `DT_NOTIFIC - DT_SIN_PRI` em dias (proxy de qualidade da vigilância) |
| `{doenca}_latencia_p90` | Percentil 90 da latência (cauda longa, indica casos atrasados) |
| `{doenca}_n_casos_com_latencia` | Contagem de casos com ambas as datas válidas |

> Cada caso individual no SINAN tem dois carimbos de tempo: `DT_NOTIFIC` (quando o caso foi notificado ao sistema) e `DT_SIN_PRI` (data dos primeiros sintomas). A diferença mede o quão rápido o município detecta e reporta. Ingestão estendida em [`ingestion/sinan.py`](src/arboviral/ingestion/sinan.py) calcula a latência por caso, filtra valores absurdos (0 ≤ delta ≤ 365 dias) e agrega por (município, mês).
>
> **Cobertura**: ~99.9% dos casos têm ambas as datas válidas. Mediana SP por doença:
> - Dengue: 3 dias (sistema funcionando bem para a doença mais comum)
> - Zika: 4 dias
> - Chikungunya: 7 dias (doença menos lembrada → notificação mais lenta)
>
> **Justificativa epidemiológica**: latência alta em um município = casos chegando atrasados ao sistema. Uma "calmaria aparente" pode mascarar surto real em curso. Combinada com cobertura ESF, dá ao modelo dois proxies independentes de qualidade do sistema de vigilância municipal.

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
│   ├── scraping/                # NOVO — coleta de dados externos para data/raw/
│   │   ├── README.md            # tabela de fontes, status, datas de coleta
│   │   ├── ibge_areas.py        # IBGE — áreas territoriais por município
│   │   ├── mapbiomas.py         # MapBiomas — uso e cobertura do solo (Coleção 10.1)
│   │   ├── esf_coverage.py      # e-Gestor MS — cobertura ESF/APS (REST mensal)
│   │   └── pni_febre_amarela.py # DATASUS PNI — cobertura vacinal FA (manual via TabNet)
│   ├── ingestion/               # 1 módulo por fonte (raw → interim)
│   │   ├── sinan.py + sinan_ftp.py + sinan_api.py     # dengue, zika, chikungunya
│   │   ├── febre_amarela.py     # FA (dados abertos MS — não está no FTP SINAN)
│   │   ├── nasa_power.py        # clima
│   │   ├── saude.py             # CNES + SIM (leitos, mortalidade)
│   │   ├── munic.py             # IBGE MUNIC (gestão e desastres)
│   │   ├── ibge.py              # PIB, população, GINI
│   │   ├── socioeconomico.py    # IDH-M + CAPAG
│   │   ├── snis.py              # água e esgoto (SINISA)
│   │   ├── habitacao.py         # aglomerados subnormais e favelas (Censos 2010, 2022)
│   │   ├── densidade.py         # área (IBGE) + densidade populacional
│   │   ├── mapbiomas.py         # uso/cobertura do solo (5 classes %, anual)
│   │   ├── esf.py               # cobertura ESF/APS (mensal, AB+APS harmonizados)
│   │   └── vacinacao_fa.py      # cobertura vacinal contra febre amarela (PNI, anual)
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
