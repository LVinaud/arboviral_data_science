---
marp: true
theme: default
paginate: true
size: 16:9
header: 'Predição de surtos de arboviroses em SP · Lázaro Vinaud · ICMC-USP'
footer: '2026-05-08'
style: |
  section {
    font-family: 'Geist', system-ui, sans-serif;
    background: #ffffff;
    color: #0f172a;
    padding: 56px 72px;
  }
  h1, h2 { color: #0f172a; letter-spacing: -0.01em; }
  h1 { font-size: 1.6em; margin-top: 0; }
  h2 { font-size: 1.2em; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }
  h3 { color: #475569; font-size: 0.95em; margin-bottom: 4px; font-weight: 600; }
  table { font-size: 0.78em; border-collapse: collapse; margin: 12px 0; }
  th, td { border: 1px solid #e2e8f0; padding: 6px 12px; }
  th { background: #f8fafc; text-align: left; }
  code { background: #f1f5f9; padding: 1px 6px; border-radius: 3px; font-size: 0.85em; }
  blockquote { border-left: 3px solid #0f172a; padding-left: 16px; color: #334155; font-style: normal; }
  .highlight { color: #dc2626; font-weight: 600; }
  .small { font-size: 0.78em; color: #64748b; }
  header { color: #94a3b8; font-size: 12px; }
  footer { color: #94a3b8; font-size: 12px; }
  section.capa { background: #0f172a; color: #ffffff; padding: 80px 96px; }
  section.capa h1 { color: #ffffff; font-size: 2em; margin-bottom: 24px; }
  section.capa .meta { color: #cbd5e1; font-size: 0.95em; line-height: 1.8; }
---

<!-- _class: capa -->
<!-- _paginate: false -->
<!-- _header: '' -->
<!-- _footer: '' -->

# Sistema de alerta precoce para arboviroses no estado de São Paulo

<div class="meta">

**Lázaro Pereira Vinaud Neto**
Iniciação Científica · ICMC-USP São Carlos

Orientador: Prof. André Carlos Ponce de Leon Ferreira de Carvalho

Maio de 2026 · Reunião com orientador

</div>

---

## Problema e perguntas de pesquisa

**Objetivo**: predizer surto de dengue, zika, chikungunya e febre amarela com **1 mês de antecedência** em cada um dos 645 municípios paulistas.

**Por que importa**: gestor municipal precisa de tempo para mobilizar agentes, intensificar visitas e preparar leitos antes do pico.

**Perguntas de pesquisa**:

- **RQ1**: qual modelo prediz melhor surtos?
- **RQ2**: quais variáveis são mais preditivas? (clima, vetorial, sanitárias, socioeconômicas)
- **RQ3**: o sistema é robusto a dados faltantes (cenário realista municipal)?
- **RQ4**: a definição operacional de surto altera o desempenho?

---

## Pipeline de dados — 3 camadas, 13 fontes

```
src/arboviral/
├── scraping/      ← baixa raw de portais externos
├── ingestion/     ← parseia raw → interim/<fonte>.parquet
└── transform/build_master.py
                   ← consolida interim → municipio_mes.parquet
```

**13 fontes integradas** (6 com scraper automatizado, 7 com download manual documentado):

| Categoria | Fontes |
|---|---|
| **Epidemiológicas** | SINAN (dengue/zika/chiku) · SVS febre amarela · latência SINAN |
| **Climáticas** | NASA POWER (T, P, umidade, vento — 645 munis × 132 meses) |
| **Vetoriais/ambientais** | MapBiomas (cobertura terra) · IBGE áreas · habitação |
| **Sistema de saúde** | CNES (leitos) · SIM (mortalidade) · ESF (cobertura APS) · PNI (vacinação FA) |
| **Socioeconômicas** | IBGE (PIB, pop, Gini) · IDH-M · CAPAG · SINISA (saneamento) · MUNIC |

**Master final**: 645 municípios × 132 meses × **79 colunas** → **140 features** (lags, rolling, sazonalidade)

---

## Modelagem

**Matriz experimental**: 4 doenças × 4 definições de surto × 7 modelos × 3 folds temporais = **315 combinações**

**Modelos** (5 ML supervisionado + 2 baselines):

| Categoria | Modelos |
|---|---|
| Baselines triviais | persistência (`y(t+1) = y(t)`) · climatologia (média do mês) |
| Linear | regressão logística |
| Árvores | random forest |
| Gradient boosting | XGBoost · LightGBM |
| Interpretável | EBM (Explainable Boosting Machine — Microsoft) |

**4 definições de surto**: canal endêmico (oficial MS) · z-score · 100 casos/100k hab · 300 casos/100k hab

**Validação**: expanding window — folds com `target_year ∈ {2022, 2023, 2024}`; 2025 reservado.
Class imbalance tratado via `class_weight=balanced` / `scale_pos_weight`. SMOTE descartado (leakage temporal).

---

## Achado central — antecipação de INÍCIO de surto

**Pergunta**: o modelo *antecipa* surto, ou só *acompanha* surto em curso?

Persistência prevê **0% dos inícios** por construção (se mês passado foi 0, ela prediz 0). Random Forest captura a fração abaixo:

| Doença × definição | Recall em INÍCIO (RF) | Falsos positivos em meses normais |
|---|---:|---:|
| Dengue × canal | <span class="highlight">29%</span> | 10% |
| Dengue × inc100 | <span class="highlight">31%</span> | 8% |
| Chikungunya × canal | <span class="highlight">21%</span> | **1%** |
| Zika × canal | <span class="highlight">35%</span> | **0,6%** |

> Para cada 3 surtos novos de dengue, o modelo antecipa 1 com 1 mês de antecedência — algo que nenhum baseline trivial consegue.

**Diferencial frente à literatura**: papers reportam AUPRC global; separar transição **0→1** (início) de **1→1** (manutenção) revela onde o ML adiciona valor real.

---

## Achado científico — features cross-doença em zika

**Top features para prever ZIKA** (SHAP global):

| # | Feature | Importance |
|---|---|---:|
| 1 | `dengue_casos_lag1` | 0.105 |
| 2 | `dengue_casos_roll6` | 0.100 |
| 3 | `lon` (longitude) | 0.096 |
| 4 | `umid_media_lag1` | 0.056 |
| 5 | `temp_media` | 0.055 |

**Casos passados de dengue são os 2 features mais preditivos para zika** — não casos passados de zika.

**Justificativa biológica**: vetor compartilhado (*Aedes aegypti*); condições ambientais que favorecem dengue favorecem zika. **Validação empírica** da decisão metodológica de incluir features cross-doença.

---

## Onda 1 de novas fontes (mai/2026) — ganho empírico

5 das 10 fontes do roadmap integradas: MapBiomas, ESF, latência SINAN, vacinação FA, áreas IBGE.
Master: 57 → 79 colunas · features: 117 → 140

| Cenário | AUPRC pré | AUPRC pós | Δ relativo |
|---|---:|---:|---:|
| **Zika × inc100 (RF)** | 0.014 | <span class="highlight">0.101</span> | **+640%** |
| Zika × canal (XGB) | 0.077 | 0.115 | +49% |
| Zika × zscore (XGB) | 0.057 | 0.094 | +65% |
| Dengue × canal (LGBM) | 0.543 | 0.569 | +5% |

**Interpretação**: cobertura vacinal de FA não imuniza contra zika — funciona como **proxy da qualidade do sistema de saúde local**. Municípios que vacinam bem também notificam bem outras arboviroses; modelo controla pelo viés de notificação.

---

## Plataforma operacional — Streamlit

**5 telas integradas, com dependência unidirecional ao núcleo de ciência de dados**:

- **Alertas**: ranking de municípios por probabilidade prevista, filtros de doença/definição/modelo
- **Município**: predição mensal + histórico de casos + justificativa SHAP por mês
  - Explicabilidade local **uniforme**: SHAP para árvores, `coef × valor padronizado` para LogReg, `explain_local` nativo do EBM
- **Mapa**: visualização geográfica de SP por município
- **Comparativo**: heatmap 4 doenças × 12 meses para um município
- **Variáveis**: catálogo das 137 features de treino, com fonte e estatísticas (auditoria)

Será integrada à plataforma **inteli.gente** (MCTI) como módulo de alerta precoce.

---

## Limitações documentadas

- **Febre amarela**: 0,03% de prevalência → modelagem clássica inviável. Considerar anomaly detection.
- **Dengue × zscore**: ML não supera persistência — autocorrelação domina o sinal.
- **Tuning**: ainda em hiperparâmetros default; Optuna pendente.
- **Cross-doença quantitativo**: hipótese confirmada por SHAP, mas comparação direta `--cross` vs `--no-cross` ainda não implementada em `train.py`.
- **Calibração de probabilidades**: não avaliada; importante para uso em produção.

**Cuidados metodológicos já tomados**:

- Sem leakage temporal (target em t+1, validação expanding window)
- Sem SMOTE (causa leakage em série temporal)
- Febre amarela contabilizada por LPI (Local Provável de Infecção), não residência
- Cobertura ESF tem quebra metodológica em 2021 (AB → APS) tratada via flag categórica

---

## Próximos passos

| Passo | Justificativa |
|---|---|
| **Onda 2** — LIRAa, mobilidade pendular, SIH-SUS, NDVI | LIRAa é o único índice oficial de densidade do *Aedes*; potencial de mover dengue/chikungunya, que ganharam pouco na Onda 1 |
| **`--cross` vs `--no-cross`** | Validação quantitativa direta da hipótese cross-doença, hoje confirmada apenas qualitativamente via SHAP |
| **Validação em outros estados** | Único teste real de generalização externa; replicar em estados com perfil diferente (Norte rural, Sul temperado) |
| **K-means + estratificação** | Modelos pan-estaduais aprendem padrões médios; cluster por perfil (capital × interior × litoral) testa heterogeneidade espacial |
| **Comparar com SARIMA** | Baseline padrão da literatura epidemiológica; sem ele, revisores cobram |
| **Disponibilizar dados (Zenodo)** | DOI permanente citável no paper; SHA256 manifest para auditoria de integridade |

---

## Anexo — sobre SARIMA

**ARIMA** (AutoRegressive Integrated Moving Average): família clássica de modelos para série temporal univariada.

- **AR**: valor de hoje depende dos N valores passados
- **I**: trabalha com diferenças (`y(t) − y(t-1)`) para remover tendência
- **MA**: valor de hoje depende dos N erros passados (suaviza ruído)

**SARIMA** = ARIMA + componente sazonal (útil em arboviroses por sazonalidade anual marcada).
**SARIMAX** = SARIMA com variáveis exógenas (clima, etc.) — comparável ao RF multivariado.

**Por que comparar**:

- Baseline padrão da literatura epidemiológica
- ARIMA é **per-município, univariada** (645 modelos separados); RF é **um modelo pan-estadual**
- ARIMA captura tendência + sazonalidade bem; **falha em mudanças bruscas** (= surtos). Espera-se que ML supere.

Implementação: `statsmodels.tsa.arima.model.ARIMA` / `SARIMAX`.

---

<!-- _class: capa -->
<!-- _paginate: false -->
<!-- _header: '' -->
<!-- _footer: '' -->

# Obrigado.

<div class="meta">

Repositório: github.com/LVinaud/arboviral_data_science
Branch principal: `main` · Branch da plataforma: `experimental/platform-app`

Documentos de referência:
`RELATORIO_MODELAGEM.md` · `AUDITORIA_DADOS.txt` · `ROADMAP.md`

</div>
