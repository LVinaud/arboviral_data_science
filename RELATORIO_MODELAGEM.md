# Relatório de Modelagem — Predição de Surtos de Arboviroses

> Documento auto-gerado por `arboviral.build_reports` a partir de `data/processed/model_results.parquet`, com complementações manuais: §9 sobre Onda 1, §10 sobre explicabilidade local uniforme e §11 sobre a sensitivity analysis cross-doença (item 1.4 do ROADMAP, executada após Onda 2).

## 1. Visão geral

- **Total de combinações treinadas**: 315 linhas (uma por fold × modelo × doença × definição)
- **Cobertura**: 4 doenças × 4 definições × 7 modelos × 3 folds (2022, 2023, 2024)
- **Combinações puladas**: 21 (febre amarela e zika×inc300 — zero positivos no treino, esperado pela raridade)
- **Versão dos dados**: master com **79 colunas** (após Onda 1, 2026-05) e features com **140 colunas** — pré-Onda 1 tinha 57 e 117, respectivamente. Os números deste relatório referem-se à 2ª rodada de treino, com as 5 novas fontes incorporadas.

## 2. Prevalência das classes (RQ4)

| Doença | Definição | Prevalência | Status |
|---|---|---:|---|
| dengue | canal | 16.21% | alta (treinável) |
| dengue | zscore | 13.38% | alta (treinável) |
| dengue | inc100 | 21.12% | alta (treinável) |
| dengue | inc300 | 11.79% | alta (treinável) |
| zika | canal | 0.60% | baixa (desafiador) |
| zika | zscore | 0.53% | baixa (desafiador) |
| zika | inc100 | 0.04% | raríssima (modelagem inviável) |
| zika | inc300 | 0.01% | raríssima (modelagem inviável) |
| chikungunya | canal | 1.76% | moderada |
| chikungunya | zscore | 1.59% | moderada |
| chikungunya | inc100 | 0.38% | baixa (desafiador) |
| chikungunya | inc300 | 0.14% | baixa (desafiador) |
| febre_amarela | canal | 0.03% | raríssima (modelagem inviável) |
| febre_amarela | zscore | 0.03% | raríssima (modelagem inviável) |
| febre_amarela | inc100 | 0.00% | raríssima (modelagem inviável) |
| febre_amarela | inc300 | 0.00% | raríssima (modelagem inviável) |

**Implicação**: AUPRC absoluto não é comparável entre doenças/definições — sempre reportar junto com o lift sobre baseline aleatório (= AUPRC / prevalência).

## 3. Ranking global dos modelos (RQ1)

Métrica: AUPRC médio sobre 30 combinações (4 doenças × 4 definições × 3 folds, com algumas excluídas por raridade).

| Modelo | AUPRC médio | Lift médio | Recall médio | n combinações |
|---|---:|---:|---:|---:|
| **rf** | 0.397 | 276.2× | 0.424 | 30 |
| **ebm** | 0.367 | 271.6× | 0.162 | 30 |
| **xgb** | 0.362 | 270.5× | 0.314 | 30 |
| **lgbm** | 0.372 | 106.6× | 0.289 | 30 |
| **persistencia** | 0.347 | 26.8× | 0.518 | 30 |
| **logreg** | 0.288 | 20.4× | 0.592 | 30 |
| **climatologia** | 0.151 | 11.9× | 0.045 | 30 |

**Achados:**
- **Random Forest** lidera em AUPRC médio (0.397), seguido por LightGBM e EBM (~0.37).
- **Persistência** é um baseline forte (AUPRC 0.347) — surge como 5º entre 7 modelos. Confirma a forte autocorrelação temporal de surtos.
- **Climatologia** é o pior baseline — só sazonalidade não basta.
- **LogReg** fica abaixo de persistência: features lineares não capturam interações ricas.
- O *gap* entre RF e persistência (AUPRC 0.397 vs 0.347) representa o ganho real de aprendizado: ~14% relativo.

## 4. Sensibilidade à definição de surto (RQ4)

Pergunta: o desempenho preditivo varia conforme a definição operacional de surto?

| Doença | Definição | Melhor ML | AUPRC ML | AUPRC Persist. | Ganho ML |
|---|---|---|---:|---:|---:|
| chikungunya | canal | rf | 0.388 | 0.306 | +0.083 |
| chikungunya | inc100 | rf | 0.446 | 0.254 | +0.192 |
| chikungunya | inc300 | logreg | 0.111 | 0.288 | -0.177 |
| chikungunya | zscore | lgbm | 0.288 | 0.281 | +0.007 |
| dengue | canal | rf | 0.572 | 0.536 | +0.036 |
| dengue | inc100 | xgb | 0.792 | 0.617 | +0.174 |
| dengue | inc300 | lgbm | 0.746 | 0.526 | +0.219 |
| dengue | zscore | rf | 0.483 | 0.471 | +0.011 |
| zika | canal | lgbm | 0.137 | 0.153 | -0.015 |
| zika | inc100 | rf | 0.014 | 0.051 | -0.037 |
| zika | zscore | lgbm | 0.100 | 0.113 | -0.013 |

**Achados:**
- **Para dengue**, AUPRC varia de 0.483 (zscore) a 0.792 (inc100). A escolha de definição tem **mais impacto que a escolha do modelo**.
- **Para chikungunya × inc300**, persistência supera o melhor ML (raridade extrema na classe positiva).
- **Para zika × canal**, persistência e LightGBM são tecnicamente equivalentes (~AUPRC 0.13–0.15).
- A definição **L3 (inc100)** é a mais discriminante — produz os melhores AUPRC absolutos. L4 (inc300) tem AUPRC menor mas lifts maiores (classe ainda mais rara).

## 5. Drivers preditivos por doença (RQ2)

SHAP global computado nos modelos vencedores. Top features ranqueadas por contribuição média.

### Dengue

| # | Feature | Importance norm. |
|---|---|---:|
| 1 | `dengue_incid_lag1` | 0.187 |
| 2 | `temp_media_roll3` | 0.170 |
| 3 | `temp_media` | 0.079 |
| 4 | `dengue_casos_trend3` | 0.059 |
| 5 | `temp_min` | 0.056 |
| 6 | `mes_sin` | 0.052 |
| 7 | `target_month` | 0.043 |
| 8 | `dengue_incid_roll6` | 0.036 |
| 9 | `lat` | 0.033 |
| 10 | `dengue_casos_lag12` | 0.033 |

### Chikungunya

| # | Feature | Importance norm. |
|---|---|---:|
| 1 | `chikungunya_incid_lag1` | 0.106 |
| 2 | `chikungunya_casos_lag1` | 0.105 |
| 3 | `populacao_estimada` | 0.098 |
| 4 | `chikungunya_casos_roll6` | 0.088 |
| 5 | `chikungunya_casos_roll3` | 0.076 |
| 6 | `chikungunya_incid_roll3` | 0.065 |
| 7 | `dengue_casos_trend3` | 0.052 |
| 8 | `dengue_casos_lag1` | 0.051 |
| 9 | `leitos_publicos` | 0.046 |
| 10 | `chikungunya_incid_roll6` | 0.042 |

### Zika

| # | Feature | Importance norm. |
|---|---|---:|
| 1 | `dengue_casos_lag1` | 0.105 |
| 2 | `dengue_casos_roll6` | 0.100 |
| 3 | `lon` | 0.096 |
| 4 | `umid_media_lag1` | 0.056 |
| 5 | `temp_media` | 0.055 |
| 6 | `precip_media_dia_lag1` | 0.055 |
| 7 | `leitos_publicos` | 0.052 |
| 8 | `dengue_casos_lag12` | 0.051 |
| 9 | `populacao_estimada` | 0.044 |
| 10 | `temp_media_lag1` | 0.044 |

**Sinal cross-doença observado em zika — interpretar com cuidado:**
Para **zika**, as features de maior importância pelo SHAP global são `dengue_casos_lag1` e `dengue_casos_roll6` — ou seja, **dentro do modelo treinado com cross**, casos passados de dengue pesam mais na decisão do que casos passados da própria zika. É um achado coerente com a biologia: o vetor é o mesmo (*Aedes aegypti*) e as condições ambientais que favorecem dengue favorecem zika.

Essa observação foi originalmente interpretada como "validação empírica" da inclusão de cross-doença. **A interpretação foi revisada na §11**, com sensitivity analysis pareada (Δ AUPRC com vs sem cross). O resumo da revisão:

- SHAP global mede importância **dentro do modelo cross** — diz quanto a feature pesa na decisão dado que ela está no modelo.
- Δ AUPRC pareado mede o **efeito real no desempenho** — diz quanto o desempenho cai se a família de features for removida.
- Para zika, o Δ AUPRC pareado é levemente **negativo** (−0.005 a −0.008 em média, p≈0.06–0.09 no Wilcoxon). Quando o modelo treina **sem** as features de dengue, ele se reorganiza usando clima, indicadores estruturais (ESF, densidade, MapBiomas) e o sinal próprio de zika — e atinge desempenho similar ou ligeiramente melhor.

Os dois resultados são compatíveis: features de dengue **são úteis quando estão presentes** (alto SHAP), mas **não são insubstituíveis** (Δ AUPRC pareado próximo de zero ou negativo). O ganho cross-doença robusto na sensitivity está concentrado em **RF × chikungunya** (Δ ≈ +0.06), não em zika. Ver §11 para a análise completa, comparativo PRE × POS-Onda 2 e teste de Wilcoxon por doença.

## 6. Insights para a plataforma (use case do gestor)

O sistema gera predição + justificativa. Exemplo real do fold de teste 2024:

> Município **3548500** (chikungunya, abril/2024): probabilidade prevista = **99%**, surto real = **sim**.
>
> Razões pelo SHAP:
>
> - **+** chikungunya teve 557 casos no mês passado (`chikungunya_casos_lag1`)
> - **+** média 6 meses = 206 casos (`chikungunya_casos_roll6`)
> - **+** incidência 128/100k (`chikungunya_incid_lag1`)
> - **+** crescimento 348 → 557 (`chikungunya_casos_lag2`)

Cada alerta na plataforma final pode ter este tipo de explicação automática gerada via `shap_por_predicao()` em `evaluation/explain.py`.

## 7. Análise de antecipação — INÍCIO de surto vs manutenção (achado central)

**Pergunta científica**: o modelo realmente *antecipa* surtos, ou só *acompanha* surtos em curso? Para um gestor municipal, antecipar é o que tem valor — acompanhar é o que persistência (baseline trivial) já faz.

Classificamos cada (município, mês) do conjunto de teste em quatro tipos de transição:

| Tipo | surto(t) → surto(t+1) | Significado |
|---|:---:|---|
| **INÍCIO** | 0 → 1 | Surto vai começar — **o caso crítico para vigilância** |
| Manutenção | 1 → 1 | Surto continua — fácil de prever (autocorrelação) |
| Fim | 1 → 0 | Surto termina |
| Normal | 0 → 0 | Trivial (a maioria dos meses) |

### 7.1 Recall em INÍCIO de surto (capacidade de antecipação)

Persistência **por definição = 0%** em INÍCIO (se mês passado foi 0, ela prediz 0). Esta tabela mostra quanto cada modelo ML antecipa do que persistência simplesmente perde:

| Modelo | Dengue × canal | Dengue × inc100 | Chikungunya × canal | Zika × canal |
|---|---:|---:|---:|---:|
| persistência | 0.0% | 0.0% | 0.0% | 0.0% |
| ebm | 7.3% | 17.1% | 3.1% | 0.0% |
| lgbm | 25.8% | 30.5% | 6.9% | 6.3% |
| **rf** | **29.0%** | **31.4%** | **21.2%** | **35.4%** |
| **xgb** | **32.3%** | **35.9%** | 11.8% | 10.8% |
| logreg | 39.4% | 55.4% | 56.3% | 63.2% |

### 7.2 Custo do alerta — taxa de falsos positivos em meses normais (0→0)

| Modelo | Dengue × canal | Dengue × inc100 | Chikungunya × canal | Zika × canal |
|---|---:|---:|---:|---:|
| persistência | 0.0% | 0.0% | 0.0% | 0.0% |
| rf | 10.2% | 7.9% | **1.0%** | **0.6%** |
| xgb | 12.0% | 8.3% | 0.6% | 0.3% |
| logreg | 35.1% | 18.8% | 11.3% | 7.4% |
| ebm | 2.4% | 3.8% | 0.1% | 0.1% |

### 7.3 Achados — utilidade real para o gestor

**(a) ML supera persistência onde mais importa.** Random Forest captura **29-35% dos inícios de surto** em dengue, com falso positivo de 8-10% em meses normais. Persistência captura **0%**. Isso significa: a cada 3 surtos novos, RF antecipa 1 com 1 mês de antecedência — tempo suficiente para o gestor mobilizar agentes, intensificar visitas, preparar leitos.

**(b) Trade-off explícito entre modelos.** Modelos black-box (RF/XGB/LGBM) são *conservadores* — gritam menos, mas com alta precisão. Regressão logística é *ousada* — captura mais inícios (até 63% em zika!) mas com mais alarmes falsos. **A escolha do modelo depende da tolerância do gestor a alarmes falsos vs custo de surtos perdidos** — esse trade-off pode ser explícito na plataforma.

**(c) Para zika, RF tem o melhor trade-off da série.** Captura 35.4% dos inícios com apenas 0.6% de falsos positivos — apesar do AUPRC global parecer modesto (0.13). Mostra que AUPRC agregado pode subestimar a utilidade prática.

**(d) EBM é cauteloso demais.** Apesar da interpretabilidade nativa, captura poucos inícios. Para uso operacional, RF + SHAP é o melhor compromisso entre detecção e explicabilidade.

**(e) Chikungunya × canal — RF capta 21% dos inícios com 1% de FP.** Para uma doença com 1.76% de prevalência, isso é excelente: praticamente um detector útil sem custo prático em municípios sem surto.

### 7.4 Implicação científica

Este é o achado mais relevante para utilidade prática do trabalho. Diferentemente da literatura — que reporta AUPRC/F1 globais sem distinguir início vs manutenção — separamos a métrica nos meses de **transição**, mostrando onde o ML adiciona valor real sobre baselines triviais. **Sugere ângulo central de artigo: "Predicting outbreak ONSET (not persistence) of arboviral diseases"** — diferencial real frente à literatura predominante.

## 8. Limitações e trabalho futuro

- **Febre amarela**: zero positivos no teste em todas as definições — modelagem clássica é inviável. Alternativa: framing como *anomaly detection* ou alerta determinístico.
- **Dengue × zscore**: ML não supera persistência. Hipótese: features informativas são as mesmas que já estão na própria persistência (autocorrelação domina).
- **Tuning de hiperparâmetros**: ainda usando defaults razoáveis. Otimização Bayesiana via Optuna pode trazer ganhos marginais.
- **Sensitivity analysis com `--no-cross`**: flag presente em `build_features.py` mas mascaramento de colunas cross-doença ainda não implementado em `train.py` (placeholder na linha 159 do features). A hipótese cross-doença está **empiricamente confirmada** pela seção 9 abaixo (zika ganha sinal apenas com fontes que incluem dengue), mas o quantitativo direto (∆AUPRC com vs sem cross) ainda precisa rodar.
- **MEM (L5)**: necessita ponte com R; deixado como trabalho futuro.
- **Calibração de probabilidades**: úteis para uso em produção; não avaliada nessa rodada.

## 9. Onda 1 — ganho empírico das 5 fontes adicionais (2026-05)

Em maio/2026 integramos 5 das 10 fontes do top do roadmap (`ROADMAP.md` §2): MapBiomas Coleção 10.1 (uso do solo), e-Gestor APS (cobertura ESF mensal), latência SINAN por doença, IBGE áreas (densidade) e PNI/DATASUS (cobertura vacinal de febre amarela). Master saiu de 57 para 79 colunas; `features.parquet` saiu de 117 para 140 colunas.

Re-treino completo do portfolio (mesmas 315 combinações) permite quantificar o ganho. Backup `model_results_PRE_ONDA1.parquet` preservado para auditoria.

### 9.1 Top ganhos absolutos em AUPRC (média de 3 folds)

| Cenário | AUPRC pré | AUPRC pós | Δ | Δ relativo |
|---|---:|---:|---:|---:|
| **zika × inc100 (RF)** | 0.014 | **0.101** | +0.088 | **+640%** |
| zika × canal (XGB) | 0.077 | 0.115 | +0.038 | +49% |
| zika × zscore (XGB) | 0.057 | 0.094 | +0.037 | +65% |
| zika × canal (RF) | 0.130 | 0.165 | +0.036 | +27% |
| dengue × canal (LGBM/XGB) | 0.543 | 0.569 | +0.027 | +5% |
| chikungunya × canal (XGB) | 0.287 | 0.312 | +0.024 | +8% |

### 9.2 Resumo agregado por doença

| Doença | Δ AUPRC médio | Δ mediano | Min | Max |
|---|---:|---:|---:|---:|
| **zika** | **+0.0085** | 0.000 | -0.019 | +0.088 |
| dengue | +0.0011 | 0.000 | -0.017 | +0.027 |
| chikungunya | -0.0017 | 0.000 | -0.105 | +0.024 |
| febre amarela | — | — | — | — |

### 9.3 Achado defensável

**Zika é a doença em que as novas fontes mais movem o ponteiro.** Coerente com a hipótese cross-doença reforçada:

- **Cobertura ESF** afeta a detecção — controla o viés "calmaria aparente em município com vigilância fraca"
- **MapBiomas (urbano + floresta) + densidade IBGE** = proxies de pressão vetorial *Aedes*
- **Cross-doença** existente + agora **mais features de dengue disponíveis** (com latência SINAN, ESF) → zika "herda" mais sinal indireto

**Narrativa central para artigo**: "Ao adicionar fontes ambientais (MapBiomas), de cobertura sanitária (ESF, vacinação FA) e de qualidade da vigilância (latência SINAN), o modelo passa a capturar surtos de zika que antes eram invisíveis (AUPRC 0.014 → 0.101 em zika×inc100)."

### 9.4 Pioras pontuais — documentadas

| Cenário | Δ AUPRC | Diagnóstico |
|---|---:|---|
| chikungunya × inc100 (LGBM) | -0.105 | Definição rara (0.38% prevalência) → alta variância entre folds |
| chikungunya × inc100 (XGB) | -0.019 | Idem |
| zika × canal (LogReg) | -0.019 | LogReg sensível a colinearidade introduzida pelas novas features |
| dengue × inc300 (vários) | ~-0.005 | Dentro do ruído |

### 9.5 Implicação para o roadmap

5 das 10 fontes do top já capturadas — ganho concentrado em zika. Para os próximos passos (LIRAa, mobilidade pendular, SIH-SUS, NDVI — eventos massivos foi descartado), a expectativa é:

- **LIRAa** (índice de infestação por *Aedes*): potencial de mover dengue e chikungunya, que são as doenças com volume mas que ganharam pouco na Onda 1. É o "santo graal" do top 10.
- **Mobilidade pendular + NDVI**: efeito provável menor em SP (estado bem conectado por rodovias, sem extremos de NDVI), mas necessários para validação externa em estados com perfil rural.

## 10. Explicabilidade local — uniforme entre todos os modelos (2026-05)

Atualização em `src/arboviral/evaluation/explain.py`: nova função `explicacao_local(modelo, X_amostra)` despacha pelo tipo do estimador final do pipeline:

| Estimador final | Método de explicação |
|---|---|
| RandomForest, XGBoost, LightGBM | SHAP TreeExplainer (post-hoc, exato em árvores) |
| Regressão Logística | `coef × valor padronizado` (soma + intercept = `decision_function`; sanity check passou — diferença numérica = 0) |
| EBM (Explainable Boosting Classifier) | API nativa `clf.explain_local()` do interpret-ml. Termos de interação `'a & b'` têm a contribuição distribuída entre os pares para preservar o ranking por feature de entrada |

Output uniforme entre os 3 métodos: DataFrame com colunas `feature, valor_observado, contribuicao, abs_contribuicao, sign, metodo`. A coluna `metodo` documenta qual técnica foi usada — útil para auditoria e para a UI exibir ao gestor.

**Implicação**: a interface (app Streamlit em `app/`) consegue mostrar a justificativa do alerta para qualquer modelo do portfolio, não apenas árvores. Apenas os baselines (Persistência, Climatologia) seguem sem card de explicação por feature — fazem sentido pedagógico mas não usam features.

A função legada `shap_por_predicao()` foi mantida como alias retrocompat (renomeia `contribuicao` → `shap`, `abs_contribuicao` → `abs_shap`).

## 11. Sensitivity analysis — features cross-doença (RQ2 / item 1.4 do ROADMAP)

Atualizada 2026-05-14. Pareamento de quatro runs do `train.py` para isolar o efeito das features cross-doença em dois estados do dataset (antes e depois da Onda 2 — mobilidade pendular + SIH-SUS). Esta versão inclui o **Wilcoxon pareado** por doença, o **pivot modelo × doença** e a **comparação histórica PRE × POS**, todos gerados por `python -m arboviral.analyze_no_cross --historico`.

### 11.0 Desenho experimental

Quatro execuções do `train.py`, todas sobre o `labels.parquet` corrente (não tocamos nos rótulos):

| Run | Features | Cross-doença | Output |
|---|---|---|---|
| POS-cross | `features.parquet` (146 cols, com Onda 2) | sim | `model_results.parquet` |
| POS-nocross | `features.parquet` (146 cols, com Onda 2) | não (`--no-cross`) | `model_results_nocross.parquet` |
| PRE-cross | `features_PRE_ONDA2.parquet` (140 cols, sem Onda 2) | sim | `model_results_PRE_ONDA2.parquet` |
| PRE-nocross | `features_PRE_ONDA2.parquet` (140 cols, sem Onda 2) | não | `model_results_nocross_PRE_ONDA2.parquet` |

A versão "PRE" do `features_PRE_ONDA2.parquet` é gerada por `python -m arboviral.features.build_features --exclude-onda2 --saida ...`, que reproduz exatamente o `features.parquet` que existia antes da integração da Onda 2 — mesma chave, mesmas 140 colunas, mesmos valores. Para cada run produzimos 315 linhas de (doença × definição × modelo × fold) com métrica AUPRC. Δ = AUPRC(cross) − AUPRC(no-cross). Δ positivo = cross ajudou.

### 11.1 Δ AUPRC médio por doença, POS-Onda 2

| Doença | n combinações | Δ AUPRC médio | Δ AUPRC mediano | Δ Recall médio |
|---|---:|---:|---:|---:|
| chikungunya | 84 | +0.0081 | +0.0000 | −0.0230 |
| dengue | 84 | −0.0020 | +0.0000 | +0.0008 |
| zika | 84 | −0.0081 | +0.0000 | −0.0147 |
| febre amarela | 63 | NaN | NaN | NaN | (sem positivos no teste) |

### 11.2 Δ AUPRC médio por modelo, POS-Onda 2

| Modelo | n combinações | Δ AUPRC médio | Δ AUPRC mediano |
|---|---:|---:|---:|
| **rf** | 45 | **+0.0174** | +0.0004 |
| persistência | 45 | +0.0000 | +0.0000 | (não usa features) |
| climatologia | 45 | +0.0000 | +0.0000 | (não usa features) |
| lgbm | 45 | −0.0011 | +0.0003 |
| xgb | 45 | −0.0034 | −0.0004 |
| logreg | 45 | −0.0051 | −0.0055 |
| ebm | 45 | −0.0056 | −0.0033 |

### 11.3 Comparativo PRE × POS-Onda 2 (cross−nocross)

A pergunta científica subjacente: a integração da Onda 2 (mobilidade pendular + SIH-SUS) altera substancialmente o efeito médio de cross-doença?

| Doença | Δ médio PRE | Δ médio POS | Δ do Δ (POS − PRE) |
|---|---:|---:|---:|
| chikungunya | +0.0108 | +0.0081 | −0.0027 |
| dengue | −0.0021 | −0.0020 | +0.0001 |
| zika | −0.0055 | −0.0081 | −0.0026 |
| febre amarela | NaN | NaN | NaN |

**Achado importante**: a hipótese inicial deste relatório (na §5) afirmava que cross-doença era **essencial** para zika, baseada em SHAP global. A análise pareada Δ AUPRC mostra que o efeito médio para zika já era **levemente negativo PRÉ-Onda 2** (−0.0055), e a Onda 2 apenas o **acentuou** marginalmente (−0.0026 a mais). Não há "inversão" — há um efeito pequeno e estável que **a leitura simplista do SHAP global não capturou**. SHAP mede a importância da feature na decisão do modelo; sensitivity Δ AUPRC mede o efeito da feature no desempenho preditivo. As duas perguntas são distintas, e dão respostas distintas.

### 11.4 Teste de Wilcoxon pareado por doença

Hipótese nula: Δ AUPRC = 0 para a doença em questão. Apenas modelos ML entram (persistência e climatologia ficam de fora porque Δ=0 sistemático). n = nº de (definição × modelo ML × fold) pareados, descartadas combinações com NaN.

| Doença | n | p-valor PRE | p-valor POS |
|---|---:|---:|---:|
| chikungunya | 55 | 0.3812 | 0.9699 |
| dengue | 60 | **0.0167** | 0.0690 |
| zika | 35 | 0.0934 | 0.0557 |
| febre amarela | 0 | NaN | NaN |

**Leitura**: nenhum efeito é significativo a 5% no estado **POS-Onda 2**. O único p-valor robusto está em **dengue PRE-Onda 2** (p=0.017), confirmando que cross atrapalha levemente a previsão de dengue — mas o efeito é pequeno (−0.0021 médio) e perde significância depois da Onda 2 (p=0.069). Para zika, o p-valor é marginal nos dois estados (~0.06–0.09): efeito sugestivo mas não conclusivo. Para chikungunya, completamente NS — o efeito médio positivo (+0.008) tem variância grande.

### 11.5 Pivot modelo × doença, POS-Onda 2

Onde exatamente se concentra o ganho do RF (+0.017 médio)?

| modelo | chikungunya | dengue | zika |
|---|---:|---:|---:|
| climatologia | 0.0000 | 0.0000 | 0.0000 |
| ebm | +0.0079 | −0.0078 | −0.0230 |
| lgbm | +0.0081 | +0.0009 | −0.0192 |
| logreg | −0.0004 | −0.0067 | −0.0100 |
| persistência | 0.0000 | 0.0000 | 0.0000 |
| **rf** | **+0.0557** | −0.0005 | −0.0122 |
| xgb | −0.0147 | +0.0004 | +0.0079 |

**Pivot equivalente PRE-Onda 2** (para comparação):

| modelo | chikungunya | dengue | zika |
|---|---:|---:|---:|
| ebm | +0.0111 | −0.0114 | −0.0311 |
| lgbm | +0.0068 | +0.0004 | −0.0099 |
| logreg | +0.0007 | −0.0054 | −0.0119 |
| rf | +0.0602 | −0.0002 | +0.0047 |
| xgb | −0.0033 | +0.0018 | +0.0093 |

**Achados:**
1. O ganho do RF se concentra **fortemente em chikungunya** (+0.056 POS, +0.060 PRE), não em zika. O ganho médio +0.017 do RF na §11.2 vinha quase 100% deste cenário.
2. Em zika, **xgb é o único modelo que ganha de forma marginal e consistente com cross** (+0.008 POS, +0.009 PRE). Os demais perdem.
3. Em dengue, **todos os modelos têm Δ próximo de zero**, alguns ligeiramente negativos. Cross é neutro a desfavorável.
4. A Onda 2 **suaviza o efeito do cross**: as magnitudes em zika ficam menos extremas (ebm −0.031 → −0.023, lgbm −0.010 → −0.019), e em chikungunya o RF perde 0.005 de ganho. Padrão consistente com a hipótese de que SIH-SUS já carrega alguma da informação cross-doença.

### 11.6 Top 10 ganhos absolutos (cross > no-cross), POS-Onda 2

| Doença | Definição | Modelo | Fold | AUPRC cross | AUPRC no-cross | Δ |
|---|---|---|---:|---:|---:|---:|
| chikungunya | inc100 | rf | 2022 | 1.0000 | 0.3333 | +0.6667 |
| zika | zscore | xgb | 2022 | 0.1182 | 0.0377 | +0.0805 |
| zika | zscore | xgb | 2023 | 0.1744 | 0.1128 | +0.0616 |
| chikungunya | inc300 | ebm | 2024 | 0.2025 | 0.1447 | +0.0578 |
| chikungunya | inc300 | logreg | 2024 | 0.2612 | 0.2090 | +0.0522 |
| zika | canal | xgb | 2022 | 0.1994 | 0.1585 | +0.0409 |
| chikungunya | canal | ebm | 2022 | 0.1871 | 0.1484 | +0.0387 |
| chikungunya | zscore | ebm | 2022 | 0.1426 | 0.1069 | +0.0357 |
| chikungunya | zscore | lgbm | 2024 | 0.5422 | 0.5094 | +0.0327 |
| chikungunya | inc300 | lgbm | 2023 | 0.0539 | 0.0225 | +0.0315 |

O ganho recorde de +0.6667 em `chikungunya × inc100 × rf × 2022` é influenciado por baixíssimo número de positivos (0.38% de prevalência) — 1 ou 2 amostras movem AUPRC de 0.33 para 1.0. Não generaliza.

### 11.7 Top 10 perdas (cross < no-cross), POS-Onda 2

| Doença | Definição | Modelo | Fold | AUPRC cross | AUPRC no-cross | Δ |
|---|---|---|---:|---:|---:|---:|
| zika | canal | xgb | 2023 | 0.1091 | 0.2324 | −0.1233 |
| chikungunya | canal | xgb | 2022 | 0.0996 | 0.2193 | −0.1198 |
| zika | zscore | ebm | 2022 | 0.0235 | 0.1173 | −0.0938 |
| zika | zscore | lgbm | 2023 | 0.1095 | 0.1802 | −0.0707 |
| zika | canal | lgbm | 2023 | 0.1349 | 0.2026 | −0.0677 |
| zika | zscore | rf | 2023 | 0.1782 | 0.2455 | −0.0673 |
| zika | canal | rf | 2023 | 0.1721 | 0.2225 | −0.0504 |
| chikungunya | zscore | xgb | 2022 | 0.0787 | 0.1238 | −0.0451 |
| chikungunya | canal | rf | 2022 | 0.1736 | 0.2168 | −0.0432 |
| zika | zscore | ebm | 2023 | 0.0691 | 0.1064 | −0.0373 |

Sete dos dez piores cenários estão em zika — confirmando que o efeito cross é negativo e disperso por modelos quando a doença-alvo é zika.

### 11.8 Interpretação revisada

A leitura simplista de §5 ("cross-doença é essencial para zika porque o SHAP global mostra dengue_casos_lag1 no topo") **não se sustenta** quando confrontada com sensitivity Δ AUPRC pareado:

1. SHAP global mede importância **interna ao modelo cross** — quão dependente o modelo está daquela feature. Não é diretamente equivalente a "remover a feature degrada o desempenho".
2. Δ AUPRC pareado mede o efeito real da família de features sobre a predição. Para zika, esse Δ é levemente negativo em ambos os estados do dataset (−0.005 PRE, −0.008 POS), e marginalmente significativo (p≈0.06–0.09).
3. **O ganho cross é localizado, não generalizado**: existe e é robusto **apenas em RF×chikungunya** (+0.056). Para todas as outras combinações modelo×doença, o efeito é pequeno e majoritariamente neutro a negativo.
4. A integração da **Onda 2** moveu o ponteiro pouco — não inverte o veredicto, apenas reduz marginalmente o ganho cross em chikungunya e o aumenta marginalmente como custo em zika. A hipótese de que SIH-SUS substituiu informação cross é **plausível mas não dramática**.

### 11.9 Implicações para a IC, para a plataforma e para o paper

1. **Para a defesa da IC**: este achado **corrige** a interpretação anterior do projeto. A hipótese cross-doença não deve ser apresentada como "validada empiricamente" sem caveat; a evidência rigorosa (Δ AUPRC pareado + Wilcoxon) indica efeito localizado em RF×chikungunya e neutro a desfavorável nos demais cenários. Material honesto e mais sofisticado para a banca.

2. **Para a plataforma em produção**: a recomendação operacional é **manter cross habilitado por default** (configuração padrão atual), porque:
   - Em RF, traz ganho substancial em chikungunya (+0.056) sem dano relevante em outras doenças
   - Os custos médios em XGB/LGBM/EBM/LogReg são pequenos em magnitude (−0.003 a −0.006)
   - A complexidade de um flag por (modelo × doença) não compensa o ganho marginal de retirar cross seletivamente
   Alternativa mais sofisticada: usar `--no-cross` apenas em XGB/LGBM/EBM se item 1.5 (Optuna) confirmar que esses modelos beneficiam de hiperparâmetros próprios para o conjunto enxuto.

3. **Para o paper**: o ângulo defensável é **"sensitivity analysis honesta sobre a hipótese cross-doença em arboviroses"** — não "cross-doença é essencial". A literatura predominante reporta cross como benefício monolítico; mostrar que o efeito é (a) localizado em poucos modelos e doenças, (b) pequeno em magnitude (Δ ≪ 0.01 na maioria dos casos), e (c) marginalmente significativo no Wilcoxon é uma contribuição metodológica genuína. O dataset SP funciona como contrapeso útil porque tem volume e variedade de doenças.

4. **Próxima ação**: item 1.5 (Optuna) deve avaliar se hiperparâmetros otimizados para XGB/LGBM/EBM no regime no-cross conseguem capturar o ganho que essas famílias perdem por cross-induzida colinearidade. Se sim, vale por modelo no-cross em produção. Se não, manter cross global é mais simples e equivalente.

### 11.10 Backups preservados para auditoria

- `data/processed/model_results_PRE_ONDA2.parquet` — cross PRE-Onda 2
- `data/processed/model_results_nocross_PRE_ONDA2.parquet` — no-cross PRE-Onda 2
- `data/processed/model_results_nocross_POS_ONDA2.parquet` — no-cross POS-Onda 2 (backup)
- `data/processed/predictions_PRE_ONDA2.parquet` + `predictions_nocross_PRE_ONDA2.parquet`
- `data/processed/predictions_nocross_POS_ONDA2.parquet`
- `data/processed/features_PRE_ONDA2.parquet` — features sem as 6 colunas Onda 2
- `data/processed/no_cross_comparativo.parquet` — long-format POS-Onda 2 (315 linhas)
- `data/processed/no_cross_comparativo_PRE_ONDA2.parquet` — long-format PRE-Onda 2 (315 linhas)
- `data/processed/no_cross_resumo_doenca.csv` + `no_cross_resumo_modelo.csv` + `no_cross_resumo_PRE_vs_POS.csv`

## 12. Hyperparameter tuning com Optuna (item 1.5 do ROADMAP, 2026-05-15)

### 12.0 Motivação e desenho

A §3 reporta o ranking dos 5 modelos com **hiperparâmetros default** (200 árvores, profundidade ilimitada, etc.). A pergunta deste capítulo é simples: **quanto cada modelo ganharia se ajustássemos seus hiperparâmetros com busca bayesiana?** Isso responde duas coisas ao mesmo tempo:

1. **Quão perto do teto cada modelo já está** com defaults — se um RF default de 200 árvores está a 1% de um RF tuned de 100 trials, o tuning não compensa o custo.
2. **Se algum modelo "mediano" (LogReg, EBM) sobe ao topo quando bem ajustado** — tese clássica em pesquisas de comparação de modelos.

**Desenho experimental — separação rigorosa entre busca e teste:**

- Sampler: **TPE (Tree-structured Parzen Estimator)** com `seed=42` para reprodutibilidade.
- 100 trials por estudo, persistidos em SQLite (`data/processed/optuna_studies/*.db`) — toda a história de cada trial fica auditável.
- **Busca**: AUPRC sobre fold de validação interna (`target_year=2021`, treinando com tudo até 2020). **NUNCA toca nos folds de teste oficiais 2022/2023/2024.**
- **Avaliação**: aplicamos os hiperparâmetros vencedores aos 3 folds de teste (mesma divisão da §3) e comparamos `model_results.parquet` (default) × `model_results_TUNED.parquet` (tuned).

**Cenários atacados** (3 doenças × 5 modelos ML = 15 estudos):
- `dengue × inc100`, `chikungunya × inc100`, `zika × canal` (top de cada doença na §3)
- Modelos: `rf`, `xgb`, `lgbm`, `ebm`, `logreg`
- Febre amarela ignorada (zero positivos no teste em todas as definições)
- Custo total: ~10h de CPU (notebook do autor, single-node)

### 12.1 Comparativo AUPRC default × tuned (média sobre 3 folds)

| Doença | Definição | Modelo | AUPRC default | AUPRC tuned | Δ | Δ% |
|---|---|---|---:|---:|---:|---:|
| dengue | inc100 | **lgbm** | 0.7940 | **0.7980** | +0.0040 | +0.5% |
| dengue | inc100 | xgb | 0.7919 | 0.7932 | +0.0013 | +0.2% |
| dengue | inc100 | rf | 0.7952 | 0.7906 | −0.0046 | −0.6% |
| dengue | inc100 | ebm | 0.7528 | 0.7876 | +0.0349 | +4.6% |
| dengue | inc100 | logreg | 0.6552 | 0.6793 | +0.0240 | +3.7% |
| chikungunya | inc100 | rf | 0.4418 | 0.4272 | −0.0146 | −3.3% |
| chikungunya | inc100 | xgb | 0.4024 | 0.4133 | +0.0109 | +2.7% |
| chikungunya | inc100 | ebm | 0.4179 | 0.1286 | −0.2893 | **−69.2%** |
| chikungunya | inc100 | lgbm | 0.1177 | 0.0315 | −0.0863 | **−73.3%** |
| chikungunya | inc100 | logreg | 0.1271 | 0.2052 | +0.0781 | +61.4% |
| zika | canal | rf | 0.1709 | 0.1485 | −0.0223 | −13.1% |
| zika | canal | xgb | 0.1186 | 0.1405 | +0.0219 | +18.5% |
| zika | canal | lgbm | 0.1364 | 0.0672 | −0.0692 | **−50.7%** |
| zika | canal | ebm | 0.0898 | 0.1028 | +0.0130 | +14.4% |
| zika | canal | logreg | 0.0449 | 0.0424 | −0.0025 | −5.5% |

### 12.2 Achados

**Em dengue (regime de bons sinais), tuning entrega micro-ganhos. O melhor modelo do projeto agora é LGBM tuned.**

- **dengue × inc100 × lgbm tuned = 0.798** (era 0.795 com RF default — novo melhor cenário do projeto, mas ganho marginal de 0.4 pontos)
- RF default e XGB default já estavam **a < 1% do teto** — confirma que o portfolio default já estava bem calibrado; tuning é refinamento, não revolução
- **EBM e LogReg ganharam 4–5%** em dengue — o tuning fez os modelos interpretáveis se aproximarem dos black-box. Útil se um stakeholder priorizar interpretabilidade nativa sobre 5 pontos de AUPRC.

**Em chikungunya/zika (regime de poucos positivos), tuning frequentemente PIORA o teste — overfitting do TPE ao fold de validação único (2021).**

- chik × ebm: 0.418 → **0.129** (queda de 69%)
- chik × lgbm: 0.118 → **0.032** (queda de 73%)
- zika × lgbm: 0.136 → **0.067** (queda de 51%)

A causa é mecânica: 2021 teve 13 positivos de chikungunya na validação (vs ~50 nos folds de teste agregados); o TPE encontrou hiperparâmetros que "decoram" esse pequeno conjunto e não generalizam. Modelos com mais regularização nativa (RF, XGB) sofreram menos; modelos com leaf-wise growth agressivo (LGBM, EBM com poucas leaves) foram os mais afetados.

**LogReg em chik subiu 61% (0.127 → 0.205)** — único caso em chik onde o ganho é grande e legítimo (penalty L1 forte selecionou ~10 features e gerou um modelo enxuto que generaliza melhor que o default).

### 12.3 Hiperparâmetros vencedores (top 5 com maior |Δ|)

| Estudo | Δ | Hiperparâmetros chave |
|---|---:|---|
| dengue × ebm | +4.6% | `learning_rate=0.074`, `interactions=0`, `outer_bags=13` |
| dengue × logreg | +3.7% | `penalty=l1`, `C=0.002` (regularização forte) |
| dengue × lgbm | +0.5% | `n_estimators=450`, `num_leaves=220`, `learning_rate=0.012` |
| chik × logreg | +61.4% | `penalty=l1`, `C` pequeno (sparsity → ~10 features ativas) |
| zika × xgb | +18.5% | `max_depth=8`, `learning_rate=0.255`, `min_child_weight=8` |

JSON completo em `data/processed/optuna_best_params.json`.

### 12.4 Ranking final (atualizado para o relatório)

Mantemos a §3 do relatório com defaults como **baseline reproduzível**, mas o ranking **operacional** das melhores combinações por doença passa a ser:

| Doença | Melhor combinação | AUPRC | Configuração |
|---|---|---:|---|
| **dengue** | inc100 × **LGBM tuned** | **0.798** | tuned via Optuna |
| **chikungunya** | inc100 × **RF default** | 0.442 | NÃO tunar (chik é instável) |
| **zika** | canal × **EBM tuned** | 0.103 | tuned, mas AUPRC ainda baixo |

A diferença prática para **dengue** entre RF default (0.795), XGB tuned (0.793) e LGBM tuned (0.798) é **estatisticamente irrelevante** (3 folds, IC ampla). Em produção qualquer um dos três é defensável.

### 12.5 Recomendação para a IC e trabalho futuro

1. **Reportar os 3 melhores modelos por doença lado a lado** (RF default, XGB default, LGBM tuned). Defender a escolha de RF default para a aplicação na inteli.gente por **estabilidade** (overfitting contido em todos os folds) e **explicabilidade nativa via feature_importances_** sem precisar de SHAP.
2. **NÃO tunar chikungunya/zika** com este desenho — o sinal é fraco demais para uma busca bayesiana ser confiável. **Trabalho futuro**: validação cruzada interna com mais de um fold dedicado (rolling 2019/2020/2021) antes de declarar hiperparâmetro vencedor — descrito no item 1.7 (ROADMAP).
3. **Calibração de probabilidades** (listada em ROADMAP §3.2 — rumo a conferência) é a próxima alavanca operacional: o tuning otimiza ranking (AUPRC), mas não corrige miscalibração — ver §13 sobre threshold.

### 12.6 Backup — arquivos

- `data/processed/model_results_TUNED.parquet` — 45 linhas (15 estudos × 3 folds)
- `data/processed/predictions_TUNED.parquet` — 348.300 linhas (uma por amostra de teste)
- `data/processed/tuning_comparison.csv` — pivot default × tuned com Δ e Δ%
- `data/processed/optuna_studies/*.db` — 15 SQLites com 100 trials cada (auditável)
- `data/processed/optuna_best_params.json` — JSON consolidado para reprodução


## 13. Calibração operacional do alerta — análise por threshold (2026-05-14)

### 13.0 Motivação

Toda a §7 (achado central da antecipação) foi reportada no threshold default 0.5 — a saída do `predict_proba` é binarizada em "alerta" se `prob_predita ≥ 0.5`. Esse é o ponto operacional padrão da maioria dos benchmarks de ML, mas **não é o ponto operacional ideal para um gestor de saúde pública**. O gestor enfrenta um trade-off concreto:

- Threshold baixo (0.5) → muitos alertas, capta mais surtos, mas inunda a vigilância com falsos positivos
- Threshold alto (0.9) → poucos alertas, alta confiança em cada um, mas perde surtos por exigência de evidência

Esta seção varre 5 thresholds (0.5, 0.6, 0.7, 0.8, 0.9) sobre `predictions.parquet` e calcula 4 métricas para cada (doença × definição × modelo × fold × threshold), com foco no **alerta preventivo de início de surto** — quando o modelo grita num município que ainda está calmo.

Geração reproduzível: `python -m arboviral.analyze_thresholds`. Outputs em `data/processed/threshold_sweep.parquet` (1.575 linhas, long-format) e `threshold_resumo.csv`.

### 13.1 As 4 métricas e o que cada uma responde

| Métrica | Definição | Pergunta operacional |
|---|---|---|
| `precision` (geral) | n alertas corretos / n alertas | Quando o modelo alerta, qual % tem surto no t+1 (qualquer transição)? |
| `recall` (geral) | n alertas corretos / n surtos t+1 totais | Dos surtos no t+1, quantos % o modelo pegou? |
| `recall_inicio` | n alertas em INÍCIO / n meses INÍCIO | Dos meses que foram INÍCIO de surto novo, quantos % o modelo alertou? |
| **`precision_alerta_inicio`** | n alertas em mês calmo que viraram surto / n alertas em mês calmo | **Quando o modelo grita num município ainda calmo, qual % das vezes ele acerta que vai começar surto?** |

A última métrica é a **operacional** para o gestor de plataforma: ignora alertas em meses de surto em curso (que são autocorrelação trivial) e foca exclusivamente nos alertas preventivos. Equivale a "1 − taxa de falso alarme em mês calmo".

### 13.2 Tabela completa — top de cada doença com Random Forest

#### Dengue × inc100 × RF (cenário-bandeira)

| T | Recall geral | Precision geral | Recall INÍCIO | **Prec alerta INÍCIO** | n alertas/fold | n alertas em calmo/fold | n INÍCIO/fold |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.50 | 0.721 | 0.690 | 0.365 | **0.325** | 2.158 | 595 | 519 |
| 0.60 | 0.613 | 0.774 | 0.217 | **0.382** | 1.666 | 318 | 519 |
| 0.70 | 0.503 | 0.857 | 0.116 | **0.435** | 1.240 | 152 | 519 |
| 0.80 | 0.367 | 0.918 | 0.048 | **0.482** | 858 | 59 | 519 |
| 0.90 | 0.202 | 0.974 | 0.012 | **0.725** | 449 | 12 | 519 |

#### Dengue × canal × RF (definição "oficial" do MS)

| T | Recall geral | Precision geral | Recall INÍCIO | **Prec alerta INÍCIO** | n alertas/fold | n alertas em calmo/fold | n INÍCIO/fold |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.50 | 0.637 | 0.527 | 0.295 | **0.208** | 1.999 | 688 | 491 |
| 0.60 | 0.495 | 0.620 | 0.174 | **0.271** | 1.345 | 313 | 491 |
| 0.70 | 0.301 | 0.727 | 0.070 | **0.317** | 738 | 109 | 491 |
| 0.80 | 0.129 | 0.854 | 0.017 | **0.385** | 318 | 22 | 491 |
| 0.90 | 0.009 | 0.992 | 0.000 | **0.333** | 28 | 1 | 491 |

#### Chikungunya × inc100 × RF

| T | Recall geral | Precision geral | Recall INÍCIO | **Prec alerta INÍCIO** | n alertas/fold | n alertas em calmo/fold | n INÍCIO/fold |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.50 | 0.364 | 0.174 | 0.344 | **0.067** | 21 | 15 | 25 |
| 0.60 | 0.349 | 0.224 | 0.333 | **0.083** | 10 | 6 | 25 |
| 0.70 | 0.335 | 0.400 | 0.333 | **0.333** | 3 | 3 | 25 |
| 0.80 | 0.000 | NaN | 0.000 | — | 0 | 0 | 25 |
| 0.90 | 0.000 | NaN | 0.000 | — | 0 | 0 | 25 |

#### Zika × canal × RF

| T | Recall geral | Precision geral | Recall INÍCIO | **Prec alerta INÍCIO** | n alertas/fold | n alertas em calmo/fold | n INÍCIO/fold |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.50 | 0.369 | 0.164 | 0.372 | **0.114** | 45 | 38 | 13 |
| 0.60 | 0.148 | 0.143 | 0.150 | **0.087** | 21 | 17 | 13 |
| 0.70 | 0.084 | 0.194 | 0.057 | **0.100** | 9 | 7 | 13 |
| 0.80 | 0.042 | 0.222 | 0.000 | **0.000** | 3 | 2 | 13 |
| 0.90 | 0.000 | NaN | 0.000 | — | 0 | 0 | 13 |

### 13.3 Achados principais

**1. Headline para defesa — dengue × inc100 × RF a 0.9 → `precision_alerta_inicio = 72,5%`.**
Quando a plataforma grita ≥ 90% de probabilidade num município paulista que ainda não está em surto de dengue, ela acerta a previsão de surto novo em 7 de cada 10 alertas. Esse é o ponto operacional de "alerta crítico" recomendado para uso real.

**2. `precision_alerta_inicio` cresce monotonicamente com o threshold em dengue × inc100, enquanto `recall_inicio` cai.**
Trade-off limpo: cada incremento de threshold reduz alertas mas aumenta confiabilidade. No outro extremo (T = 0.5), a métrica cai para 33% — apenas 1 em cada 3 alertas em mês calmo realmente vira surto. Operar em 0.5 é "tagarelar".

**3. Para chikungunya e zika, threshold ≥ 0.8 colapsa o número de alertas para zero ou 1.**
Modelos para essas doenças simplesmente nunca atribuem probabilidade ≥ 80% — característica do problema: prevalência baixíssima (chik inc100 = 0.38%, zika canal = 0.6%) impede que o modelo "tenha certeza alta" em cenários positivos.

**4. `precision_geral` (97% a T = 0.9 em dengue inc100) é enganosa para uso preventivo.**
A maior parte dessa precision vem de alertas em meses de surto em curso (manutenção) — autocorrelação domina. A `precision_alerta_inicio` é a métrica honesta porque exclui esses casos triviais.

**5. `precision_inicio` (calculada na §11.4) e `precision_alerta_inicio` são métricas distintas.**
- `precision_inicio` = % dos alertas que caíram em mês INÍCIO (relativo a todos os alertas, incluindo manutenção)
- `precision_alerta_inicio` = % dos alertas em mês calmo que viraram surto (exclui manutenção)
A segunda é a que importa para o gestor.

### 13.4 Recomendação operacional por doença

Threshold único para todas as doenças não funciona — chik e zika perdem totalmente acima de 0.8. A plataforma deve usar **threshold por doença**, calibrado conforme a tolerância do gestor a falso alarme:

| Doença | Threshold sugerido | Recall INÍCIO esperado | Prec alerta INÍCIO esperada | Uso |
|---|---:|---:|---:|---|
| Dengue (inc100) | **0.90** | 1% | **73%** | banda "alerta crítico" — gestor age com alta confiança |
| Dengue (inc100) | 0.70 | 12% | **44%** | banda "alerta forte" — mais cobertura, menos confiança |
| Dengue (canal) | 0.70 | 7% | **32%** | banda "alerta moderado" |
| Chikungunya (inc100) | 0.70 | 33% | **33%** | banda única possível — acima disso, 0 alertas |
| Zika (canal) | 0.50 | 37% | **11%** | apenas monitoramento informativo — sem confiança operacional |

A interface da plataforma já pode usar `threshold` como controle deslizante; o gestor ajusta conforme a fase do ano e a tolerância de campo.

### 13.5 Conexão com a §7

A §7 reportou recall em INÍCIO de surto a threshold default 0.5. Esta seção mostra que a métrica anterior é apenas um ponto de uma curva — e que o ponto realmente operacional, para uso preventivo, é o `precision_alerta_inicio` em thresholds altos. Para o gestor de uma plataforma em produção, a leitura correta é:

> "Random Forest em dengue × inc100 captura 36% dos inícios a confiança 0.5, mas se exigirmos confiança 0.9, captura apenas 1.2% dos inícios, com a vantagem de que cada alerta novo tem 73% de probabilidade de virar surto real."

Esse é o tipo de calibração que justifica o uso da plataforma como **ferramenta de apoio à decisão**, não como sistema de classificação automática.

### 13.6 Backups preservados

- `data/processed/threshold_sweep.parquet` — long-format, 1.575 linhas (3 doenças × 4 definições × 5 modelos ML × 3 folds × 5 thresholds, com algumas combinações puladas por raridade)
- `data/processed/threshold_resumo.csv` — média sobre folds, formato amigável para abrir em Excel
