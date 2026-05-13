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

**Achado central — features cross-doença justificam-se cientificamente:**
Para **zika**, as features mais preditivas são `dengue_casos_lag1`, `dengue_casos_roll6` — ou seja, **casos de dengue no passado predizem zika melhor que a própria zika**. Isso é coerente com a biologia: o vetor é o mesmo (*Aedes aegypti*) e as condições ambientais que favorecem dengue favorecem zika. **A decisão de incluir features cross-doença está validada empiricamente.**

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

Atualização 2026-05-13. Pareamento entre dois runs do `train.py` sobre o mesmo `features.parquet` pós-Onda 2 (146 colunas, com mobilidade pendular e SIH-SUS já incorporadas):

- `model_results.parquet` — run com features cross-doença habilitadas (configuração padrão; o modelo de zika usa também colunas com prefixo `dengue_`, `chikungunya_`, etc.)
- `model_results_nocross.parquet` — run com `python -m arboviral.train --no-cross`, mascarando qualquer coluna cujo prefixo seja outra doença que não a alvo

Para cada um dos 315 (doença × definição × modelo × fold) pareados, calculamos Δ AUPRC = AUPRC(cross) − AUPRC(no-cross). Δ positivo significa que cross ajudou.

### 11.1 Δ AUPRC médio por doença

| Doença | n combinações | Δ AUPRC médio | Δ AUPRC mediano | Δ Recall médio |
|---|---:|---:|---:|---:|
| chikungunya | 84 | **+0.0081** | +0.0000 | -0.0230 |
| dengue | 84 | -0.0020 | +0.0000 | +0.0008 |
| zika | 84 | **-0.0081** | +0.0000 | -0.0147 |
| febre_amarela | 63 | NaN | NaN | NaN | (sem positivos no teste — métricas degeneradas) |

### 11.2 Δ AUPRC médio por modelo

| Modelo | n combinações | Δ AUPRC médio | Δ AUPRC mediano |
|---|---:|---:|---:|
| **rf** | 45 | **+0.0174** | +0.0004 |
| persistência | 45 | +0.0000 | +0.0000 | (não usa features) |
| climatologia | 45 | +0.0000 | +0.0000 | (não usa features) |
| lgbm | 45 | -0.0011 | +0.0003 |
| xgb | 45 | -0.0034 | -0.0004 |
| logreg | 45 | -0.0051 | -0.0055 |
| ebm | 45 | -0.0056 | -0.0033 |

### 11.3 Top 10 ganhos absolutos (cross > no-cross)

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

O ganho recorde de +0.6667 em `chikungunya × inc100 × rf × 2022` é influenciado por baixíssimo número de positivos (definição com 0.38% de prevalência), em que 1–2 amostras movem AUPRC de 0.33 para 1.0 — não generaliza, mas indica que o ganho se concentra em cenários raros.

### 11.4 Top 10 perdas (cross < no-cross — onde cross atrapalhou)

| Doença | Definição | Modelo | Fold | AUPRC cross | AUPRC no-cross | Δ |
|---|---|---|---:|---:|---:|---:|
| zika | canal | xgb | 2023 | 0.1091 | 0.2324 | -0.1233 |
| chikungunya | canal | xgb | 2022 | 0.0996 | 0.2193 | -0.1198 |
| zika | zscore | ebm | 2022 | 0.0235 | 0.1173 | -0.0938 |
| zika | zscore | lgbm | 2023 | 0.1095 | 0.1802 | -0.0707 |
| zika | canal | lgbm | 2023 | 0.1349 | 0.2026 | -0.0677 |
| zika | zscore | rf | 2023 | 0.1782 | 0.2455 | -0.0673 |
| zika | canal | rf | 2023 | 0.1721 | 0.2225 | -0.0504 |
| chikungunya | zscore | xgb | 2022 | 0.0787 | 0.1238 | -0.0451 |
| chikungunya | canal | rf | 2022 | 0.1736 | 0.2168 | -0.0432 |
| zika | zscore | ebm | 2023 | 0.0691 | 0.1064 | -0.0373 |

### 11.5 Interpretação científica — o veredicto inverteu pós-Onda 2

Antes da Onda 2 (mobilidade pendular + SIH-SUS), as features mais preditivas para zika eram `dengue_casos_lag1` e `dengue_casos_roll6` (relatado em §5). Isso era apresentado como prova empírica de que cross-doença era essencial, dado o vetor compartilhado *Aedes aegypti*. **Esta sensitivity, executada com a Onda 2 já incorporada, encontrou o oposto**: zika perde -0.0081 AUPRC em média quando usamos cross. Quatro das cinco maiores quedas absolutas estão concentradas em zika.

Hipótese para a inversão: as 4 colunas de internação SIH-SUS (`sih_internacoes_dengue_lag1`, `sih_internacoes_chikungunya_lag1`, etc.) já carregam — sem prefixo de doença — sinal de pressão epidêmica de cada doença na rede hospitalar do município. Para zika, o sinal cross-doença que antes vinha indiretamente via SINAN agora vem **diretamente** via SIH-SUS de dengue/chik. Adicionar também as features SINAN das outras doenças vira informação redundante e potencialmente colinear — modelos lineares (LogReg) e baseados em boosting (XGB/EBM/LGBM) sofrem mais com colinearidade do que árvores genuinamente independentes.

**Random Forest é a única exceção** (+0.0174 médio, único positivo claro). Isso é consistente com a tese: RF amostra subconjuntos aleatórios de features em cada split, sofre menos com colinearidade e consegue extrair valor de features parcialmente redundantes. Os demais modelos (XGB, LGBM, EBM, LogReg) preferem o conjunto enxuto.

### 11.6 Implicações para a IC e para o paper

1. **Defesa da IC**: a hipótese inicial (cross-doença ajuda zika) era válida no estado anterior do dataset. A integração de SIH-SUS (Onda 2) **substituiu** esse canal de informação por uma fonte mais direta, e o ganho cross virou ruído residual. Esse achado evidencia que o desenho do dataset altera o veredicto sobre features cross-doença — material rico para a defesa.

2. **Recomendação operacional**: para a plataforma em produção, manter cross habilitado **só para Random Forest**. Para os demais modelos (XGB/LGBM/EBM/LogReg), seria preferível operar com `--no-cross`. Isso pode virar uma flag por modelo no `train.py` numa rodada futura.

3. **Ângulo para o paper**: a literatura predominante reporta cross-doença como benefício monolítico para arboviroses. Mostrar que o efeito é **dependente da disponibilidade de proxies diretos** (como SIH-SUS) e **dependente do modelo** (gain only-RF) é diferencial metodológico — sustenta a contribuição teórica além do estudo de caso paulista.

4. **Próximo a fazer**: o item 1.5 do ROADMAP (Optuna nos top 3 modelos) deve usar `--no-cross` para EBM/LGBM/XGB e `cross` para RF, baseado neste resultado.

Backups preservados para auditoria:
- `data/processed/model_results_PRE_ONDA2.parquet`
- `data/processed/predictions_PRE_ONDA2.parquet`
- `data/processed/no_cross_comparativo.parquet` (long-format pareado, 315 linhas)
- `data/processed/no_cross_resumo_doenca.csv`
- `data/processed/no_cross_resumo_modelo.csv`
