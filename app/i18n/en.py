"""
English (en) strings for the app — mirror of pt.py.

Every key in pt.py must be present here. If a key goes missing, t() falls
back to PT-BR rather than crashing — but we aim for full parity.

Translation conventions:
    - Brazilian institutional / academic terms keep their original form
      (ICMC · USP São Carlos, "MCTI") — they are proper nouns.
    - "Iniciação Científica" → "Undergraduate Research" (Lattes / NSF style).
    - "Surto" → "outbreak" (epidemiology standard).
    - "Canal endêmico" → "endemic channel" (Brazilian Min. of Health method).
    - "Município" → "municipality" (the IBGE administrative unit; "city" is wrong
      because it includes rural areas and very small populations).
    - "Antecipação" / "manutenção" of an outbreak → "early warning" / "maintenance".
"""
from __future__ import annotations

STRINGS: dict = {
    # ============================================================
    # app.py
    # ============================================================
    "app": {
        "page_title": "Early Warning — Arboviruses SP",
    },

    "nav": {
        "visao_geral": "Overview",
        "alertas": "Alerts",
        "municipio": "Municipality",
        "mapa": "SP map",
        "comparativo": "Comparison",
        "sobre": "About",
        "proximos_passos": "Next steps",
    },

    # ============================================================
    # Common terms
    # ============================================================
    "comum": {
        "municipio": "Municipality",
        "doenca": "Disease",
        "modelo": "Model",
        "definicao_surto": "Outbreak definition",
        "ano_teste": "Test year",
        "mes_predito": "Predicted month",
        "mes_analise_shap": "Analysis month (SHAP)",
        "filtros": "Filters",
        "selecao": "Selection",
        "probabilidade": "Probability",
        "criticos": "Critical",
        "altos": "High",
        "moderados": "Moderate",
        "surto_real": "Actual outbreak",
        "sim": "Yes",
        "nao": "No",
        "todos_meses": "All months",
        "pico_ano": "Yearly peak",
        "codigo_ibge": "IBGE code",
        "categoria": "Category",
        "tipo": "Type",
        "fonte": "Source",
        "descricao": "Description",
        "minimo": "Min.",
        "media": "Mean",
        "maximo": "Max.",
        "observacao": "Notes",
        "nome_tecnico": "Technical name",
        "fonte_primaria": "Primary source",
        "n_features": "# features",
        "pct_nan": "% NaN",
        "pct_nan_medio": "Mean % NaN",
        "verdadeiros": "true",
        "falsos": "false",
        "mes": "Month",
    },

    # ============================================================
    # Slug → human label dictionaries
    # ============================================================
    "doenca": {
        "dengue": "Dengue",
        "zika": "Zika",
        "chikungunya": "Chikungunya",
        "febre_amarela": "Yellow fever",
    },

    "modelo": {
        "rf": "Random Forest",
        "xgb": "XGBoost",
        "lgbm": "LightGBM",
        "ebm": "EBM (Explainable Boosting)",
        "logreg": "Logistic Regression",
        "persistencia": "Persistence",
        "climatologia": "Climatology",
    },

    "definicao": {
        "canal": "Endemic channel (Min. of Health)",
        "zscore": "Z-score (baseline deviation)",
        "inc100": "100 cases / 100k inhab.",
        "inc300": "300 cases / 100k inhab.",
    },

    "mes": {
        "1": "January", "2": "February", "3": "March", "4": "April",
        "5": "May", "6": "June", "7": "July", "8": "August",
        "9": "September", "10": "October", "11": "November", "12": "December",
        "fora_range": "Month {n}",
    },

    "risco": {
        "BAIXO": "LOW",
        "MODERADO": "MODERATE",
        "ALTO": "HIGH",
        "CRITICO": "CRITICAL",
        "label_baixo": "Low",
        "label_moderado": "Moderate",
        "label_alto": "High",
        "label_critico": "Critical",
    },

    # ============================================================
    # lib/tema.py
    # ============================================================
    "tema": {
        "brand_titulo": "Early Warning",
        "brand_sub": "Arboviruses · SP",
        "footer_linha1": "ICMC · USP São Carlos",
        "footer_linha2": "Undergraduate Research",
        "footer_linha3": "Lázaro Vinaud — 2025/26",
    },

    # ============================================================
    # lib/carregar.py — spinner messages
    # ============================================================
    "carregar": {
        "municipios": "Loading municipalities...",
        "master": "Loading master dataset...",
        "labels": "Loading outbreak labels...",
        "features": "Loading features...",
        "predicoes": "Loading prediction history...",
        "modelos": "Loading trained models...",
        "catalogando": "Cataloging variables...",
    },

    # ============================================================
    # Common error messages
    # ============================================================
    "erro": {
        "dados_nao_encontrados": (
            "Data files not found. Run the pipeline first:\n\n"
            "```bash\n"
            "python -m arboviral.transform.build_master\n"
            "python -m arboviral.labels.build_labels\n"
            "python -m arboviral.features.build_features\n"
            "python -m arboviral.train\n"
            "```"
        ),
        "modelo_nao_encontrado": (
            "Model `{arquivo}` not found. "
            "Run `python -m arboviral.train` to generate it."
        ),
        "explicacao_falhou": "Failed to compute explanation: {erro}",
        "sem_predicao": "No prediction found for this combination.",
        "sem_dados_combinacao": "No data for this combination.",
        "sem_modelos": "No trained model found. Run `python -m arboviral.train`.",
        "sem_alertas_limiar": "No prediction above the selected threshold.",
        "roadmap_ausente": "`ROADMAP.md` not found at `{caminho}`.",
    },

    # ============================================================
    # screens/visao_geral.py — landing
    # ============================================================
    "home": {
        "hero": {
            "eyebrow": "ICMC · USP São Carlos · Undergraduate Research",
            "titulo": "Operational early-warning system for arboviruses in São Paulo state",
            "lead": (
                "Each month, explainable machine-learning models estimate the "
                "outbreak probability of dengue, zika, chikungunya, and yellow fever "
                "in each of São Paulo's 645 municipalities — and justify every alert "
                "with the factors that contributed the most."
            ),
            "meta_aluno": "Student",
            "meta_aluno_valor": "Lázaro Vinaud",
            "meta_orientador": "Advisor",
            "meta_orientador_valor": "Prof. André C. P. L. F. de Carvalho",
            "meta_periodo": "Data period",
        },
        "metricas": {
            "municipios_label": "Monitored municipalities",
            "municipios_unidade": " / SP",
            "periodo_label": "Historical period",
            "periodo_unidade": " years",
            "periodo_delta": "January/{ano_min} — December/{ano_max}",
            "variaveis_label": "Variables in master",
            "variaveis_delta": "Climate · epidemiological · environmental · health system",
            "doencas_label": "Diseases covered",
            "doencas_delta": "Dengue · Zika · Chikungunya · Yellow fever",
        },
        "modelos": {
            "secao": "Available models",
            "caption": (
                "Models serialized in `data/processed/models/` per (disease × definition × fold). "
                "Pages use the most recent fold (target year 2024) as the up-to-date prediction."
            ),
            "col_doenca": "Disease",
            "col_definicao": "Outbreak definition",
            "col_modelo": "Model",
            "col_folds": "Test years trained",
            "rodape_total": (
                "{n_modelos} models in total · 7 algorithms (persistence, climatology, "
                "logreg, EBM, RF, XGBoost, LightGBM) × 4 outbreak definitions × 3 temporal folds "
                "(2022, 2023, 2024)."
            ),
        },
        "navegacao": {
            "secao": "How to navigate the platform",
            "alertas_titulo": "Monthly alerts",
            "alertas_desc": (
                "Ranked table of municipalities at risk for the current month, "
                "with filters by disease, outbreak definition, and model."
            ),
            "municipio_titulo": "Municipality detail",
            "municipio_desc": (
                "Monthly prediction + history + SHAP justification "
                "(which variables pushed risk up or down)."
            ),
            "comparativo_titulo": "Comparison across diseases",
            "comparativo_desc": (
                "Heatmap of 4 diseases × 12 months + historical series to understand "
                "seasonality and cross-transmission."
            ),
        },
        "rodape_esq": "Early Warning Platform · ICMC USP · 2026",
        "rodape_dir": "Planned integration · inteli.gente platform / MCTI",
    },

    # ============================================================
    # screens/alertas.py
    # ============================================================
    "alertas": {
        "titulo": "Monthly alerts",
        "descricao": (
            "Municipalities at predicted risk · {recorte_mes} · "
            "{doenca} · {definicao} · {modelo}. "
            "Each row is a monthly prediction: outbreak probability for the indicated month."
        ),
        "crumbs": "PLATFORM / ALERTS / {doenca_upper} / {recorte_upper}",
        "fold_todos": "{ano} (all months)",
        "definicao_help": (
            "Endemic channel = Brazilian Ministry of Health official method · "
            "Z-score = deviation from historical baseline · "
            "100 or 300 cases / 100k inhab. = raw incidence threshold"
        ),
        "ano_teste_help": "Each year is one round of temporal validation (expanding window).",
        "mes_help": (
            "Month for which the alert is issued (prediction target). "
            "In production, this corresponds to the next month."
        ),
        "risco_min_label": "Minimum probability shown",
        "metricas": {
            "total_label": "Total alerts",
            "total_delta": "≥ {limiar} probability",
            "criticos_delta": "Probability ≥ 75%",
            "altos_delta": "50% to 75%",
            "moderados_delta": "25% to 50%",
        },
        "tabela": {
            "risco": "Risk",
            "municipio": "Municipality",
            "codigo_ibge": "IBGE code",
            "mes_predito": "Predicted month",
            "probabilidade": "Probability",
            "surto_real": "Actual outbreak?",
            "surto_real_help": "Did the outbreak actually happen that month? (retrospective evaluation)",
            "em_surto_agora": "Currently in outbreak?",
            "em_surto_agora_help": (
                "Yes = municipality was already in an outbreak in the reference month "
                "(alert = maintenance). No = true early warning (model predicts ONSET)."
            ),
        },
        "avaliacao": {
            "precisao_label": "Precision in this slice",
            "precisao_delta": "{n_corretos} of {n_total} alerts matched a real outbreak",
            "antecipacao_label": "True early warnings",
            "antecipacao_delta": "alerts predicting outbreak ONSET (not maintenance)",
        },
        "rodape": (
            "Use the **Municipality** page to see the detailed SHAP justification of each alert. "
            "The *Currently in outbreak?* column distinguishes early warning (=0) from maintenance (=1) — "
            "true early warnings are the central finding of this research."
        ),
    },

    # ============================================================
    # screens/municipio.py
    # ============================================================
    "municipio": {
        "descricao": "{doenca} · {definicao} · {modelo} · test year {fold}",
        "crumbs": "PLATFORM / MUNICIPALITY / {nome_upper} / {doenca_upper}",
        "shap_help": (
            "Predicted month (alert target) used by the SHAP justification. "
            "'Yearly peak' = month with the highest predicted probability. "
            "In production this corresponds to the current month."
        ),
        "chips": {
            "ibge": "IBGE {cod}",
            "populacao": "Pop. {pop}",
            "estacao": "Station {est}",
            "distancia": "{dist} km from station",
        },
        "metricas": {
            "meses_alerta_label": "Months with alert",
            "meses_alerta_delta": "out of {n} predicted months (≥ 50%)",
            "surtos_reais_label": "Actual outbreaks in the year",
            "surtos_reais_delta": "confirmed by the chosen definition",
            "definicao_label": "Definition in use",
        },
        "graficos": {
            "secao_probabilidade": "Predicted probability month by month",
            "trace_probabilidade": "Predicted probability",
            "trace_surto": "Actual outbreak",
            "hover_prob": "<b>%{customdata}</b><br>Prob: %{y:.1%}<extra></extra>",
            "hover_surto": "<b>%{customdata}</b><br>Outbreak confirmed<extra></extra>",
            "y_axis": "Probability",
            "x_axis_mes_predito": "Predicted month",
            "secao_historico": "Reported case history — {doenca}",
            "y_axis_casos": "{doenca} cases",
        },
        "shap": {
            "titulo_alerta": "Why this alert?",
            "titulo_baixo": "What is keeping the risk low?",
            "caption_pico": (
                "Analysis for {municipio} in {mes_humano} (highest-probability month of the year). "
                "Predicted probability: {prob}. "
                "🔴 red = pushed risk UP · 🟢 green = pushed risk DOWN."
            ),
            "caption_mes": (
                "Analysis for {municipio} in {mes_humano}. "
                "Predicted probability: {prob}. "
                "🔴 red = pushed risk UP · 🟢 green = pushed risk DOWN."
            ),
            "info_baseline": (
                "Baseline models ({modelo}) have no features — "
                "they predict only from the recent history of the municipality itself. "
                "Pick a machine-learning model (Random Forest, XGBoost, "
                "LightGBM, Logistic Regression, or EBM) to see the justification."
            ),
            "qtd_label": "How many factors to display?",
            "qtd_help": (
                "Default is top 8 — enough to identify the main drivers. "
                "'All' lists the ~137 features in absolute-contribution order "
                "(useful for model auditing)."
            ),
            "qtd_todos": "All",
            "spinner": "Loading model and computing explanation...",
            "metodo": "method: {metodo}",
            "valor_observado": "{tecnico} · observed value: {valor}",
            "valor_observado_nan": "{tecnico} · observed value: NaN",
        },
    },

    # ============================================================
    # screens/mapa.py
    # ============================================================
    "mapa": {
        "titulo": "Risk map — São Paulo",
        "descricao": (
            "Predicted outbreak probability across {fold} for "
            "{doenca} · {definicao} · {modelo}. "
            "Use the slider to scrub through months or switch granularity in the sidebar."
        ),
        "crumbs": "PLATFORM / MAP / {doenca_upper} / {fold}",
        "granularidade": {
            "label": "Granularity",
            "help": (
                "Municipality (645): individual bubbles. "
                "DRS (17): São Paulo State Health Regional Departments. "
                "Intermediate region (11): IBGE official geographic division (2017)."
            ),
            "municipio": "Municipality (645)",
            "drs": "DRS (17)",
            "rgi": "Intermediate region (11)",
        },
        "legenda": {
            "cor": "Color: predicted probability (population-weighted mean when aggregated)",
            "bolinha": "Bubble size: reported cases in the unit (sum when aggregated)",
        },
        "hover": {
            "probabilidade": "Probability",
            "casos": "Cases",
            "populacao": "Population",
        },
        "metricas": {
            "unidades_label": "Mapped units",
            "criticos_label": "Peak of critical units",
            "criticos_delta": "≥ 75% prob. in any month",
            "casos_ano_label": "Total cases in year",
            "casos_ano_delta": "state-wide notification sum",
            "risco_medio_label": "Yearly average risk",
            "risco_medio_delta": "state-wide pop.-weighted mean",
        },
        "top5": {
            "secao": "Top 5 units by yearly average risk",
            "casos": "Cases in year",
        },
        "rodape": (
            "Interactive map: use the slider/play to animate, click and drag to pan, "
            "scroll to zoom. DRS polygons obtained by dissolving municipalities (source: SES-SP, scraped 2026-05-09); "
            "intermediate-region polygons from IBGE 2017."
        ),
    },

    # ============================================================
    # screens/comparativo.py
    # ============================================================
    "comparativo": {
        "titulo": "{municipio} · 4 diseases side by side",
        "descricao": (
            "Probability heatmap + case history for all arboviruses "
            "in {fold} · {definicao} · {modelo}."
        ),
        "crumbs": "PLATFORM / COMPARISON / {nome_upper}",
        "chips": {
            "ano_teste": "Test year {fold}",
        },
        "secao_heatmap": "Predicted probability by month × disease",
        "secao_historico": "Case history — 11 years, all diseases",
        "x_axis_mes_predito": "Predicted month",
        "y_axis_doenca": "Disease",
        "y_axis_casos": "Reported cases",
        "rodape": (
            "All four diseases share the *Aedes aegypti* vector (dengue, zika, chikungunya) "
            "or are sylvatic (yellow fever, transmitted by Haemagogus/Sabethes). "
            "Outbreaks may overlap or distribute according to environmental conditions."
        ),
    },

    # ============================================================
    # screens/sobre.py — overview, data collection, variables, training
    # ============================================================
    "sobre": {
        "titulo": "About the project",
        "descricao": (
            "How this platform forecasts dengue, zika, chikungunya and yellow-fever "
            "outbreaks across the 645 São Paulo state municipalities, explained in plain language."
        ),
        "crumbs": "PLATFORM / ABOUT",
        # ----- Why -----
        "intro": {
            "secao": "Why does this platform exist?",
            "motivacao": (
                "Every epidemic starts before it makes the news. By the time the "
                "health system realizes a town is in outbreak, the worst has usually "
                "already happened. Beds fill up, community workers are overstretched, "
                "campaigns arrive late. Traditional surveillance is reactive, with a "
                "lag that can reach 30 or 60 days between a case occurring and the "
                "consolidated notification."
            ),
            "objetivo": (
                "The proposal is to shift to a predictive regime. We combine "
                "epidemiological, climatic, demographic, environmental and "
                "health-coverage data to estimate, with one month of lead time, the "
                "probability of an outbreak in each of the 645 SP municipalities. "
                "Each alert is paired with its rationale, that is, the variables that "
                "weighed most in the decision, so it can support concrete prevention "
                "actions."
            ),
            "para_quem_titulo": "Who is it for?",
            "para_quem": (
                "Municipal and state health managers, to support decisions on "
                "where to focus prevention effort. Epidemiological surveillance, "
                "as a predictive complement to traditional indicators. Citizens and "
                "researchers, with transparency about how each alert was generated "
                "and end-to-end auditability. The data is public, the code is open "
                "and the methodology is documented."
            ),
            "ic_titulo": "Who built it",
            "ic": (
                "Undergraduate research project conducted by Lázaro Pereira "
                "Vinaud Neto at the Institute of Mathematical and Computer "
                "Sciences, University of São Paulo, São Carlos campus, advised by "
                "Prof. André Carlos Ponce de Leon Ferreira de Carvalho and with "
                "support from PhD candidate Márcia Regina Martins Martinez "
                "Corso. Funded by USP's Unified Scholarship Programme (PUB)."
            ),
        },
        # ----- How it works -----
        "funcionamento": {
            "secao": "How it works, in 4 steps",
            "intro": (
                "We combine public data from multiple sources and train "
                "machine-learning models to recognize patterns that precede "
                "outbreaks. Every step is deterministic and reproducible, and "
                "anyone can run the pipeline from the open code."
            ),
            "passo1_badge": "01",
            "passo1_titulo": "We collect public data",
            "passo1_texto": (
                "Fifteen official, open sources: SINAN/DATASUS for dengue, zika and "
                "chikungunya cases, MS/SVS for yellow fever, NASA POWER for climate, "
                "IBGE for demography, economy and areas, MapBiomas for land cover, "
                "e-Gestor APS for primary care, PNI for vaccination, plus CNES, "
                "SINISA, IDH-M, CAPAG and IBGE MUNIC."
            ),
            "passo2_badge": "02",
            "passo2_titulo": "We build a single municipality × month table",
            "passo2_texto": (
                "Each combination of municipality, year and month becomes one row. "
                "That gives 85,140 rows in total: 645 municipalities × 11 years × "
                "12 months. On top of that base we derive 140 features, "
                "including lags of cases from the previous month and from the last "
                "3 and 6 months, rolling means, trends, cyclical seasonality and "
                "structural indicators."
            ),
            "passo3_badge": "03",
            "passo3_titulo": "We train multiple models and compare",
            "passo3_texto": (
                "Seven algorithms compete: two trivial baselines, persistence and "
                "climatology, plus logistic regression, EBM as an interpretable "
                "additive model and three tree-based models: Random Forest, "
                "XGBoost and LightGBM. Each disease and each outbreak definition "
                "has its own best model. We do not assume one algorithm fits "
                "everything."
            ),
            "passo4_badge": "04",
            "passo4_titulo": "We generate probabilities and rationales",
            "passo4_texto": (
                "For each municipality the model estimates the probability of an "
                "outbreak next month and classifies it into four levels: low, "
                "moderate, high and critical. The rationale behind the alert is "
                "computed via SHAP for tree models or by the coefficients for "
                "logistic regression. The manager sees exactly which variables "
                "pushed the probability up."
            ),
        },
        # ----- Where data comes from -----
        "coleta": {
            "secao": "Where does the data come from?",
            "intro": (
                "Everything that feeds the model is public and official. No "
                "private sources, no proprietary collection. Every variable can be "
                "traced back to its origin portal, ensuring scientific and "
                "administrative auditability."
            ),
            "grupo_saude_titulo": "Health",
            "grupo_saude_texto": (
                "SINAN/DATASUS provides probable dengue, zika and chikungunya "
                "cases by municipality of residence, monthly since 2015, with "
                "notification latency extracted per individual case. MS/SVS Open "
                "Data delivers yellow fever by Likely Place of Infection, the "
                "appropriate criterion for sylvatic transmission. CNES records "
                "public hospital beds, e-Gestor APS tracks monthly coverage of "
                "Family Health Strategy and primary care, and PNI maintains "
                "yellow-fever vaccination coverage."
            ),
            "grupo_clima_titulo": "Climate",
            "grupo_clima_texto": (
                "NASA POWER, based on the MERRA-2 product, supplies mean, "
                "minimum and maximum temperature, precipitation, relative humidity, "
                "atmospheric pressure and wind. Resolution is monthly for each of "
                "the 645 SP municipalities since 2015. We generate lags of 1, 2 "
                "and 3 months, since the literature points to climate-on-vector "
                "effects with a lag of 1 to 2 months."
            ),
            "grupo_demo_titulo": "Demographics and economy",
            "grupo_demo_texto": (
                "IBGE SIDRA publishes estimated population, municipal GDP and "
                "Gini index. UNDP maintains the Municipal HDI and its "
                "components. National Treasury, via CAPAG, classifies the "
                "payment capacity of municipalities. The IBGE Censuses of 2010 "
                "and 2022 provide the number and population of subnormal "
                "clusters."
            ),
            "grupo_ambiente_titulo": "Environment and territory",
            "grupo_ambiente_texto": (
                "MapBiomas Collection 10.1 reports the share of urban, rural, "
                "forest, pasture and water surface. The IBGE territorial areas "
                "feed municipal population density. SINISA covers basic "
                "sanitation, with access to treated water and sewage. This set is "
                "important because it is the closest available proxy for *Aedes "
                "aegypti* vector pressure."
            ),
            "grupo_gestao_titulo": "Municipal management",
            "grupo_gestao_texto": (
                "IBGE MUNIC 2018 and 2020 describe the institutional "
                "structure of the municipality, including epidemiological "
                "surveillance, risk management and disaster response. It acts as "
                "a response-capacity variable. Better-prepared municipalities "
                "tend to have improved detection and containment."
            ),
            "fechamento": (
                "The consolidated result is 85,140 rows, that is, 645 "
                "municipalities × 11 years × 12 months, and 140 features "
                "after feature engineering. That is the matrix the model consumes "
                "to learn, and it is open for auditing in the technical-detail "
                "expander below."
            ),
        },
        # ----- How the computer learns -----
        "aprende": {
            "secao": "How does the computer learn to forecast?",
            "intro": (
                "The critical question is: how do we know the model truly "
                "forecasts, rather than memorizing the past? The answer comes "
                "from the design of the prospective validation. We always "
                "test on periods the model has never seen during training."
            ),
            "metodo_titulo": "Train on the past, test on the future",
            "metodo_texto": (
                "Shuffling data at random would leak future information into "
                "training, so we respect temporal order. The model learns from "
                "everything up to year X and is evaluated on year X+1, month by "
                "month. We repeat this for three windows. This design "
                "simulates the platform's real operation. If it were "
                "running in production, this is how it would make decisions."
            ),
            "diagrama_titulo": "The three validation windows",
            "diagrama": (
                "| Round | Learns from | Is tested on |\n"
                "|---|---|---|\n"
                "| 1st | data 2015 to 2021 | year 2022 |\n"
                "| 2nd | data 2015 to 2022 | year 2023 |\n"
                "| 3rd | data 2015 to 2023 | year 2024 |\n\n"
                "*Year 2025 is reserved for demonstration and has never been seen by the model.*"
            ),
            "comparacao_titulo": "Hitting the target is not enough, we have to beat the baselines",
            "comparacao_texto": (
                "We always compare with two trivial models. The first is "
                "persistence, which predicts that next month will be like "
                "the last. The second is climatology, which predicts that "
                "next month will be like the historical average for that "
                "month. Persistence is a strong baseline because of the "
                "temporal autocorrelation of outbreaks. Our model is only "
                "considered useful if it beats this reference by a clear "
                "margin, especially in outbreak onset months, where "
                "there is a transition from calm period to outbreak and "
                "persistence fails by construction."
            ),
            "metricas_titulo": "How we measure performance",
            "metricas_texto": (
                "Outbreaks are rare events, so plain accuracy hides the "
                "problem. A model that always predicts \"no outbreak\" hits "
                "84% of months but is useless. That is why the primary "
                "metric is AUPRC, the area under the precision and "
                "recall curve, robust to imbalance. We also report the "
                "lift over random baseline, recall in outbreak onset "
                "months, which measures the real anticipation ability, "
                "and the false-alarm rate in normal months, which "
                "represents the operational cost for the manager."
            ),
            "grafico1_titulo": "Model ranking by mean AUPRC",
            "grafico1_eixo": "Mean AUPRC (higher is better)",
            "grafico1_legenda": (
                "Average over 30 combinations of disease, outbreak definition and "
                "validation window. Random Forest leads the ranking. Persistence "
                "comes fifth, confirming it is a competitive baseline thanks to the "
                "temporal autocorrelation of outbreaks."
            ),
            "grafico2_titulo": "Recall on outbreak-onset months: Random Forest vs Persistence",
            "grafico2_eixo": "Recall on onset months",
            "grafico2_legenda_persist": "Persistence",
            "grafico2_legenda_rf": "Random Forest",
            "grafico2_legenda": (
                "On outbreak-onset months, the transition from calm month to outbreak "
                "month, persistence has 0% recall by construction. Random Forest "
                "captures between 21% and 35% of those onsets, depending on the "
                "disease and outbreak definition. These are precisely the months "
                "where the model delivers real value to the manager: it detects new "
                "outbreaks with 1 month of lead time."
            ),
        },
        # ----- Technical catalog (hidden in expander) -----
        "catalogo": {
            "secao": "Technical detail for the curious",
            "intro": (
                "For auditing or deeper inspection: the table below lists the "
                "{n_features} variables actually used by the models, grouped into "
                "{n_categorias} thematic categories. Includes technical name, "
                "Portuguese description, primary source, type (numeric, boolean, or "
                "categorical), missing-data rate, and descriptive statistics."
            ),
            "expander_label": "Show all variables used by the model",
        },
        "tipos": {
            "booleana": "boolean",
            "numerica": "numeric",
            "categorica": "categorical",
        },
        "categorias": {
            "epi_dengue": "Epidemiological — Dengue",
            "epi_zika": "Epidemiological — Zika",
            "epi_chik": "Epidemiological — Chikungunya",
            "epi_fa": "Epidemiological — Yellow fever",
            "climaticas": "Climate",
            "sazonalidade": "Seasonality",
            "geo": "Geolocation",
            "demo_econ": "Demography / Economy",
            "densidade": "Territorial density",
            "cobertura": "Land cover",
            "saude_publica": "Public health",
            "esf_aps": "ESF / APS coverage",
            "saneamento": "Sanitation",
            "vacinacao": "Vaccination",
            "munic": "Municipal surveillance (MUNIC)",
            "desastres": "Disasters / environmental risk",
            "habitacao": "Housing / favelas",
            "capag": "CAPAG",
            "predicao_meta": "Prediction metadata",
            "outras": "Other",
        },
        "fontes": {
            "sinan": "SINAN / DATASUS",
            "svs": "SVS / Brazilian Ministry of Health",
            "nasa_power": "NASA POWER (MERRA-2)",
            "calendario": "feature engineering (calendar)",
            "ibge_inmet": "IBGE / INMET lookup",
            "ibge_atlas": "IBGE SIDRA / Atlas PNUD",
            "ibge_areas": "IBGE — territorial areas",
            "mapbiomas": "MapBiomas Collection 10.1",
            "datasus_cnes": "DATASUS — CNES + SIM",
            "egestor": "e-Gestor / Brazilian Ministry of Health",
            "sinisa": "SINISA",
            "pni": "PNI / DATASUS",
            "ibge_munic_2018": "IBGE MUNIC 2018",
            "ibge_munic_2020": "IBGE MUNIC 2020",
            "ibge_censos": "IBGE — Censuses 2010 / 2022",
            "tesouro": "Brazilian National Treasury",
            "split_features": "feature engineering (split)",
            "indef": "—",
        },
        "metricas": {
            "total_label": "Total features",
            "total_delta": "in {n_categorias} thematic categories",
            "completas_label": "Nearly complete",
            "completas_delta": "< 1% NaN",
            "lacunas_label": "With sizable gaps",
            "lacunas_delta": "≥ 10% NaN — pay attention",
            "nan_medio_label": "Mean NaN",
            "nan_medio_delta": "average across all features",
        },
        "filtros": {
            "secao": "Filters",
            "busca_label": "Search (technical name or description)",
            "busca_placeholder": "e.g. temp, dengue_lag, esf, surveillance…",
            "busca_help": "Case-insensitive substring search on both names.",
            "categorias_label": "Categories",
            "categorias_help": "Empty = all. Pick one or more to filter.",
            "tipo_label": "Type",
            "tipo_help": "Empty = all.",
        },
        "tabela": {
            "info_filtro": (
                "Showing {n_filtrado} of {n_total} features "
                "(in {n_categorias} categories)."
            ),
            "secao_distribuicao": "Distribution by category",
            "rodape": (
                "Columns `cod_ibge`, `ano`, and `mes` are not listed here — they are "
                "identification keys, not model input features. Columns `target_year` "
                "and `target_month` are derived in `train.py` for the temporal split and "
                "are also used as features (seasonality of the predicted month)."
            ),
        },
    },

    # ============================================================
    # screens/proximos_passos.py
    # ============================================================
    "proximos": {
        "titulo": "Next steps",
        "descricao": (
            "Research roadmap — from the closing of the undergraduate research "
            "to publishable material for an international paper. The content reflects "
            "the ROADMAP.md at the repository root."
        ),
        "crumbs": "PLATFORM / NEXT STEPS",
        "secao_resumo": "Summary",
        "card_curto_titulo": "Short term",
        "card_curto_desc": (
            "5 items to wrap up the undergraduate research properly: post-hoc analyses, "
            "stratified SHAP, NaN robustness, sensitivity analysis (--no-cross), tuning."
        ),
        "card_medio_titulo": "Medium term",
        "card_medio_desc": (
            "Top 10 data sources prioritized by impact. 5/10 already integrated "
            "(MapBiomas, ESF, SINAN latency, density, YF vaccination)."
        ),
        "card_longo_titulo": "Long term",
        "card_longo_desc": (
            "Path to publication: national workshop → IEEE conference → "
            "international journal. External validation in other states is the critical step."
        ),
        "tab_curto": "Short term",
        "tab_medio": "Medium term (top 10 sources)",
        "tab_longo": "Long term (paper)",
        "tab_full": "Full document",
        "tab_full_caption": (
            "Same content as the previous tabs, in linear format "
            "(useful for printing or copying)."
        ),
        "rodape": (
            "Content lives in <code>ROADMAP.md</code> at the repository root · "
            "updates show up here automatically."
        ),
    },

    # ============================================================
    # lib/predicao.py — categorizar_risco
    # ============================================================
    "categorizar_risco": {
        "critico": "Critical",
        "alto": "High",
        "moderado": "Moderate",
        "baixo": "Low",
    },

    # ============================================================
    # Feature humanization (lib/labels.py)
    # ============================================================
    "feature": {
        # Seasonality
        "mes_sin": "Seasonality (sin component)",
        "mes_cos": "Seasonality (cos component)",
        # Geolocation
        "lat": "Latitude",
        "lon": "Longitude",
        "dist_estacao_km": "Distance to INMET station (km)",
        # Demography / economy
        "populacao_estimada": "Estimated population",
        "pib_per_capita": "GDP per capita",
        "gini": "Gini index",
        "idhm": "Municipal HDI",
        # IBGE density
        "area_km2": "Area (km²)",
        "densidade_2023": "Population density (inhab/km²)",
        # MapBiomas
        "pct_floresta": "Cover: natural forest (%)",
        "pct_agricultura": "Cover: farmland (%)",
        "pct_nao_vegetado": "Cover: urban / unvegetated (%)",
        "pct_agua": "Cover: water (%)",
        "pct_natural_nao_florestal": "Cover: natural non-forest (%)",
        # Vaccination
        "cob_vac_fa_pct": "Yellow-fever vaccination coverage (%)",
        # ESF / APS
        "esf_qt_capacidade": "ESF capacity (service)",
        "esf_pop_referencia": "ESF reference population",
        "esf_metodologia_AB": "ESF methodology: AB (until 2020)",
        "esf_metodologia_APS": "ESF methodology: APS (from 2021)",
        "esf_cobertura_pct_lag1": "ESF coverage (previous month, %)",
        "esf_qt_equipes_lag1": "ESF teams (previous month)",
        # Sanitation
        "iag0001_atend_agua_pct": "Water service (%)",
        "ies0001_atend_esgoto_pct": "Sewage service (%)",
        "ies2004_esgoto_tratado_pct": "Treated sewage (%)",
        # Public health
        "leitos_publicos": "Public hospital beds",
        "mortalidade_materna": "Maternal mortality",
        # MUNIC — surveillance
        "msau28_pacs": "Community Health Agents Program (PACS)",
        "msau541_vig_sanitaria": "Structured sanitary surveillance",
        "msau542_vig_epidemiologica": "Structured epidemiological surveillance",
        "msau543_controle_endemias": "Structured endemic disease control",
        # MUNIC — disasters
        "mgrd01_seca": "Municipality affected by drought",
        "mgrd06_alagamento": "Municipality affected by flooding",
        "mgrd07_erosao": "Municipality affected by erosion",
        "mgrd08_enchente_gradual": "Municipality affected by gradual flood",
        "mgrd11_enxurrada": "Municipality affected by flash flood",
        "mgrd14_deslizamento": "Municipality affected by landslide",
        "mgrd201_mapeamento_risco": "Has risk-area mapping",
        "mmam2612_moradia_risco": "Has at-risk housing",
        # Housing
        "num_aglom_subnorm_2010": "Subnormal agglomerations (2010 Census)",
        "pop_aglom_subnorm_2010": "Subnormal-agglomeration population (2010)",
        "num_favelas_2022": "Favelas (2022 Census)",
        "pop_favelas_2022": "Favela population (2022)",
        # Current climate
        "precip_media_dia": "Mean precipitation (current month)",
        "temp_media": "Mean temperature (current month)",
        "umid_media": "Mean humidity (current month)",
        "temp_max": "Max. temperature (current month)",
        "temp_min": "Min. temperature (current month)",
        "pressao_media_kpa": "Mean atmospheric pressure (kPa)",
        "vento_media": "Mean wind",
        # CAPAG
        "capag_A": "CAPAG: A",
        "capag_B": "CAPAG: B",
        "capag_C": "CAPAG: C",
        "capag_D": "CAPAG: D",
        "capag_n.d.": "CAPAG: not available",
        # Split
        "target_year": "Target year of prediction",
        "target_month": "Target month of prediction",
    },

    # Parametrized templates for feature patterns
    "feature_pattern": {
        "casos_lag_1": "{d} cases {k} month ago",
        "casos_lag_n": "{d} cases {k} months ago",
        "incid_lag_1": "{d} incidence {k} month ago",
        "incid_lag_n": "{d} incidence {k} months ago",
        "casos_roll": "{d} cases (rolling mean {w} months)",
        "incid_roll": "{d} incidence (rolling mean {w} months)",
        "casos_trend": "{d} case trend ({w} months)",
        "surto_canal_1": "{d} outbreak {k} month ago (endemic channel)",
        "surto_canal_n": "{d} outbreak {k} months ago (endemic channel)",
        "latencia_mediana": "Median notification latency ({d}, previous month)",
        "latencia_p90": "p90 notification latency ({d}, previous month)",
        "casos_com_latencia": "Cases with valid latency ({d}, previous month)",
        "precip_lag_1": "Mean precipitation {k} month ago",
        "precip_lag_n": "Mean precipitation {k} months ago",
        "precip_roll": "Mean precipitation (rolling mean {w} months)",
        "temp_lag_1": "Mean temperature {k} month ago",
        "temp_lag_n": "Mean temperature {k} months ago",
        "temp_roll": "Mean temperature (rolling mean {w} months)",
        "umid_lag_1": "Mean humidity {k} month ago",
        "umid_lag_n": "Mean humidity {k} months ago",
        "umid_roll": "Mean humidity (rolling mean {w} months)",
    },
}
