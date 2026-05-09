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
        "variaveis": "Variables",
        "sobre": "About",
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
            "hover_prob": "<b>%{{customdata}}</b><br>Prob: %{{y:.1%}}<extra></extra>",
            "hover_surto": "<b>%{{customdata}}</b><br>Outbreak confirmed<extra></extra>",
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
            "Predicted outbreak probability in {mes_humano} for "
            "{doenca} · {definicao} · {modelo}. "
            "Each point = 1 municipality. Color indicates risk level."
        ),
        "crumbs": "PLATFORM / MAP / {doenca_upper} / {mes_upper}",
        "mes_help": "Month for which the map shows the predicted probability (alert target).",
        "metricas": {
            "mapeados_label": "Mapped municipalities",
            "criticos_delta": "≥ 75% prob.",
            "altos_delta": "50% to 75%",
            "risco_medio_label": "Average risk",
            "risco_medio_delta": "state-wide mean",
        },
        "top5": {
            "secao": "Top 5 highest-risk municipalities",
            "surto_real": "Actual outbreak?",
        },
        "rodape": (
            "Interactive map: click and drag to pan, scroll to zoom, "
            "hover over a point for details. "
            "Future version: choropleth with municipal boundary geojson."
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
    # screens/variaveis.py
    # ============================================================
    "variaveis": {
        "titulo": "Variable catalog",
        "descricao": (
            "All **{n_features} features** that feed the models, with technical name, "
            "human description, source, type, and statistics. "
            "Useful for auditing what the model actually sees and for checking gaps (% NaN)."
        ),
        "crumbs": "PLATFORM / VARIABLES",
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
                "Showing **{n_filtrado} of {n_total}** features "
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
    # screens/sobre.py
    # ============================================================
    "sobre": {
        "titulo": "About the project",
        "descricao": (
            "Research roadmap — from the closing of the undergraduate research "
            "to publishable material for an international paper. The content reflects "
            "the ROADMAP.md at the repository root."
        ),
        "crumbs": "PLATFORM / ABOUT",
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
