"""
Mapeamento código técnico → rótulo humano para a UI.

O pipeline de modelagem usa códigos curtos (`rf`, `inc100`, `dengue`,
`febre_amarela`) por consistência com os parquets/joblib gerados em
`data/processed/`. Esses códigos NÃO devem aparecer na interface — para o
gestor, o app mostra "Random Forest", "100 casos por 100 mil hab", etc.

Convenção de uso:
    nome_doenca("febre_amarela")       → "Febre amarela"
    nome_modelo("rf")                  → "Random Forest"
    nome_definicao("inc100")           → "100 casos / 100 mil hab"
    nome_mes(7)                        → "Julho"

Para selectboxes, passar `format_func=nome_modelo` (etc.) — o valor de
sessão continua sendo o código, só o label exibido muda.
"""
from __future__ import annotations

DOENCAS_HUMANO: dict[str, str] = {
    "dengue": "Dengue",
    "zika": "Zika",
    "chikungunya": "Chikungunya",
    "febre_amarela": "Febre amarela",
}

MODELOS_HUMANO: dict[str, str] = {
    "rf": "Random Forest",
    "xgb": "XGBoost",
    "lgbm": "LightGBM",
    "ebm": "EBM (Explainable Boosting)",
    "logreg": "Regressão Logística",
    "persistencia": "Persistência",
    "climatologia": "Climatologia",
}

# Para definições de surto, mantemos a versão técnica como subtítulo entre
# parênteses para quem conhece o jargão epidemiológico (relatório, orientador).
DEFINICOES_HUMANO: dict[str, str] = {
    "canal": "Canal endêmico (Min. Saúde)",
    "zscore": "Z-score (desvio do baseline)",
    "inc100": "100 casos / 100 mil hab",
    "inc300": "300 casos / 100 mil hab",
}

MES_NOME: dict[int, str] = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


def nome_doenca(slug: str) -> str:
    return DOENCAS_HUMANO.get(slug, slug.replace("_", " ").title())


def nome_modelo(slug: str) -> str:
    return MODELOS_HUMANO.get(slug, slug.upper())


def nome_definicao(slug: str) -> str:
    return DEFINICOES_HUMANO.get(slug, slug)


def nome_mes(num: int | str) -> str:
    """Aceita int (1-12) ou string ('07'). Retorna 'Mês N' para fora do range."""
    try:
        n = int(num)
    except (TypeError, ValueError):
        return str(num)
    return MES_NOME.get(n, f"Mês {n}")


def ano_mes_humano(ano: int, mes: int) -> str:
    """Ex.: (2024, 7) → 'Julho/2024'."""
    return f"{nome_mes(mes)}/{int(ano)}"


# ============================================================
# Humanização de nomes de feature (usado pelo SHAP)
# ============================================================
import re

# Estáticas, anuais e clima atual — dicionário direto.
_FEATURE_HUMANO: dict[str, str] = {
    # Sazonalidade
    "mes_sin": "Sazonalidade (componente sen)",
    "mes_cos": "Sazonalidade (componente cos)",
    # Geolocalização
    "lat": "Latitude",
    "lon": "Longitude",
    "dist_estacao_km": "Distância à estação INMET (km)",
    # Demografia / economia
    "populacao_estimada": "População estimada",
    "pib_per_capita": "PIB per capita",
    "gini": "Índice de Gini",
    "idhm": "IDH municipal",
    # Densidade IBGE
    "area_km2": "Área (km²)",
    "densidade_2023": "Densidade populacional (hab/km²)",
    # MapBiomas — uso do solo (%)
    "pct_floresta": "Cobertura: floresta natural (%)",
    "pct_agricultura": "Cobertura: agropecuária (%)",
    "pct_nao_vegetado": "Cobertura: urbanizado / não vegetado (%)",
    "pct_agua": "Cobertura: água (%)",
    "pct_natural_nao_florestal": "Cobertura: natural não florestal (%)",
    # Vacinação
    "cob_vac_fa_pct": "Cobertura vacinal contra febre amarela (%)",
    # ESF / APS (mensal)
    "esf_qt_capacidade": "Capacidade ESF (atendimento)",
    "esf_pop_referencia": "População de referência ESF",
    "esf_metodologia_AB": "Metodologia ESF: Atenção Básica (até 2020)",
    "esf_metodologia_APS": "Metodologia ESF: APS (a partir de 2021)",
    "esf_cobertura_pct_lag1": "Cobertura ESF (mês anterior, %)",
    "esf_qt_equipes_lag1": "Equipes ESF (mês anterior)",
    # SINISA / saneamento
    "iag0001_atend_agua_pct": "Atendimento de água (%)",
    "ies0001_atend_esgoto_pct": "Atendimento de esgoto (%)",
    "ies2004_esgoto_tratado_pct": "Esgoto tratado (%)",
    # Saúde pública
    "leitos_publicos": "Leitos públicos",
    "mortalidade_materna": "Mortalidade materna",
    # MUNIC — gestão e vigilância (booleanos)
    "msau28_pacs": "Programa de Agentes Comunitários (PACS)",
    "msau541_vig_sanitaria": "Vigilância sanitária estruturada",
    "msau542_vig_epidemiologica": "Vigilância epidemiológica estruturada",
    "msau543_controle_endemias": "Controle de endemias estruturado",
    # MUNIC — desastres (booleanos)
    "mgrd01_seca": "Município atingido por seca",
    "mgrd06_alagamento": "Município atingido por alagamento",
    "mgrd07_erosao": "Município atingido por erosão",
    "mgrd08_enchente_gradual": "Município atingido por enchente gradual",
    "mgrd11_enxurrada": "Município atingido por enxurrada",
    "mgrd14_deslizamento": "Município atingido por deslizamento",
    "mgrd201_mapeamento_risco": "Possui mapeamento de áreas de risco",
    "mmam2612_moradia_risco": "Possui moradia em situação de risco",
    # Habitação — favelas / aglomerados subnormais
    "num_aglom_subnorm_2010": "Aglomerados subnormais (Censo 2010)",
    "pop_aglom_subnorm_2010": "População em aglomerados subnormais (2010)",
    "num_favelas_2022": "Favelas (Censo 2022)",
    "pop_favelas_2022": "População em favelas (2022)",
    # Clima atual (mês corrente)
    "precip_media_dia": "Precipitação média (mês atual)",
    "temp_media": "Temperatura média (mês atual)",
    "umid_media": "Umidade média (mês atual)",
    "temp_max": "Temperatura máxima (mês atual)",
    "temp_min": "Temperatura mínima (mês atual)",
    "pressao_media_kpa": "Pressão atmosférica média (kPa)",
    "vento_media": "Vento médio",
    # CAPAG (categórica → one-hot, sem rotina especial)
    "capag_A": "CAPAG: A",
    "capag_B": "CAPAG: B",
    "capag_C": "CAPAG: C",
    "capag_D": "CAPAG: D",
    "capag_n.d.": "CAPAG: não disponível",
    # Adicionadas pelo train (split)
    "target_year": "Ano-alvo da predição",
    "target_month": "Mês-alvo da predição",
}

# Regex para padrões parametrizados (lags, rolling, trend, latência por doença)
_DOENCA_REGEX = r"(dengue|zika|chikungunya|febre_amarela)"
_PADROES_FEATURE: list[tuple[re.Pattern, callable]] = [
    # Casos lag/roll/trend
    (re.compile(rf"^{_DOENCA_REGEX}_casos_lag(\d+)$"),
        lambda d, k: f"Casos de {nome_doenca(d).lower()} há {k} {'mês' if int(k) == 1 else 'meses'}"),
    (re.compile(rf"^{_DOENCA_REGEX}_incid_lag(\d+)$"),
        lambda d, k: f"Incidência de {nome_doenca(d).lower()} há {k} {'mês' if int(k) == 1 else 'meses'}"),
    (re.compile(rf"^{_DOENCA_REGEX}_casos_roll(\d+)$"),
        lambda d, w: f"Casos de {nome_doenca(d).lower()} (média móvel {w} meses)"),
    (re.compile(rf"^{_DOENCA_REGEX}_incid_roll(\d+)$"),
        lambda d, w: f"Incidência de {nome_doenca(d).lower()} (média móvel {w} meses)"),
    (re.compile(rf"^{_DOENCA_REGEX}_casos_trend(\d+)$"),
        lambda d, w: f"Tendência de casos de {nome_doenca(d).lower()} ({w} meses)"),
    # Surto canal endêmico em lags
    (re.compile(rf"^{_DOENCA_REGEX}_surto_canal_lag(\d+)$"),
        lambda d, k: f"Surto de {nome_doenca(d).lower()} há {k} {'mês' if int(k) == 1 else 'meses'} (canal endêmico)"),
    # Latência SINAN
    (re.compile(rf"^{_DOENCA_REGEX}_latencia_mediana_lag1$"),
        lambda d: f"Latência mediana de notificação ({nome_doenca(d).lower()}, mês anterior)"),
    (re.compile(rf"^{_DOENCA_REGEX}_latencia_p90_lag1$"),
        lambda d: f"Latência p90 de notificação ({nome_doenca(d).lower()}, mês anterior)"),
    (re.compile(rf"^{_DOENCA_REGEX}_n_casos_com_latencia_lag1$"),
        lambda d: f"Casos com latência válida ({nome_doenca(d).lower()}, mês anterior)"),
    # Clima parametrizado
    (re.compile(r"^precip_media_dia_lag(\d+)$"),
        lambda k: f"Precipitação média há {k} {'mês' if int(k) == 1 else 'meses'}"),
    (re.compile(r"^precip_media_dia_roll(\d+)$"),
        lambda w: f"Precipitação média (média móvel {w} meses)"),
    (re.compile(r"^temp_media_lag(\d+)$"),
        lambda k: f"Temperatura média há {k} {'mês' if int(k) == 1 else 'meses'}"),
    (re.compile(r"^temp_media_roll(\d+)$"),
        lambda w: f"Temperatura média (média móvel {w} meses)"),
    (re.compile(r"^umid_media_lag(\d+)$"),
        lambda k: f"Umidade média há {k} {'mês' if int(k) == 1 else 'meses'}"),
    (re.compile(r"^umid_media_roll(\d+)$"),
        lambda w: f"Umidade média (média móvel {w} meses)"),
]


def humanizar_feature(slug: str) -> str:
    """Traduz nome técnico de feature para descrição em português.

    Ordem de tentativa:
      1. Dicionário direto (estáticas, anuais, clima atual)
      2. Padrões regex (lags / rolling / trend / latência parametrizados por doença)
      3. Fallback: o próprio slug (com underscores → espaços)
    """
    if slug in _FEATURE_HUMANO:
        return _FEATURE_HUMANO[slug]
    for padrao, formatador in _PADROES_FEATURE:
        m = padrao.match(slug)
        if m:
            return formatador(*m.groups())
    return slug.replace("_", " ")
