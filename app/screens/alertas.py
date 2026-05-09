"""
Página: Lista de alertas — municípios em maior risco previsto.

Usa as predições calculadas (predictions.parquet) para mostrar onde o sistema
teria emitido alerta. Em produção, seria substituído por uma rotina mensal
que carrega os modelos e prediz com features atualizadas.
"""
import streamlit as st

from i18n import t
from lib.carregar import carregar_municipios, carregar_predicoes
from lib.labels import (
    ano_mes_humano,
    nome_definicao,
    nome_doenca,
    nome_mes,
    nome_modelo,
)
from lib.predicao import (
    DEFAULT_DEFINICAO,
    DEFAULT_DOENCA,
    DEFAULT_MODELO,
    categorizar_risco,
    idx_default,
)
from lib.tema import (
    metric,
    metric_row,
    page_header,
    risk_legend,
)

preds = carregar_predicoes()
municipios = carregar_municipios()

# --- Sidebar: filtros ---
with st.sidebar:
    st.markdown(f"### {t('comum.filtros')}")

    doencas_disponiveis = sorted(preds["doenca"].unique())
    doenca = st.selectbox(
        t("comum.doenca"), doencas_disponiveis,
        index=idx_default(doencas_disponiveis, DEFAULT_DOENCA),
        format_func=nome_doenca,
    )

    definicoes_disponiveis = sorted(
        preds[preds["doenca"] == doenca]["definicao"].unique()
    )
    definicao = st.selectbox(
        t("comum.definicao_surto"), definicoes_disponiveis,
        index=idx_default(definicoes_disponiveis, DEFAULT_DEFINICAO),
        format_func=nome_definicao,
        help=t("alertas.definicao_help"),
    )

    modelos_disponiveis = sorted(
        preds[(preds["doenca"] == doenca) & (preds["definicao"] == definicao)]["modelo"].unique()
    )
    modelo = st.selectbox(
        t("comum.modelo"), modelos_disponiveis,
        index=idx_default(modelos_disponiveis, DEFAULT_MODELO),
        format_func=nome_modelo,
    )

    folds = sorted(preds["fold_ano_teste"].unique())
    fold = st.selectbox(
        t("comum.ano_teste"), folds, index=len(folds) - 1,
        help=t("alertas.ano_teste_help"),
    )

    meses_disp = sorted(
        preds[(preds["doenca"] == doenca) & (preds["definicao"] == definicao)
              & (preds["modelo"] == modelo) & (preds["fold_ano_teste"] == fold)]["target_mes"].unique()
    )
    mes_sel = st.selectbox(
        t("comum.mes_predito"), ["Todos"] + list(meses_disp), index=0,
        format_func=lambda x: t("comum.todos_meses") if x == "Todos" else nome_mes(x),
        help=t("alertas.mes_help"),
    )
    mes = None if mes_sel == "Todos" else int(mes_sel)

    risco_min = st.slider(t("alertas.risco_min_label"), 0.0, 1.0, 0.5, 0.05)

# fold_ano_teste já é o ano do mês predito (target_year), então casa com `mes`
# (que agora é target_mes) — não há mais defasagem entre o rótulo e a predição.
_recorte_mes = (
    ano_mes_humano(fold, mes) if mes
    else t("alertas.fold_todos", ano=fold)
)

# --- Header ---
page_header(
    titulo=t("alertas.titulo"),
    descricao=t(
        "alertas.descricao",
        recorte_mes=_recorte_mes,
        doenca=nome_doenca(doenca),
        definicao=nome_definicao(definicao),
        modelo=nome_modelo(modelo),
    ),
    crumbs=t(
        "alertas.crumbs",
        doenca_upper=nome_doenca(doenca).upper(),
        recorte_upper=_recorte_mes.upper(),
    ),
)

# --- Filtrar predições ---
df = preds[
    (preds["doenca"] == doenca)
    & (preds["definicao"] == definicao)
    & (preds["modelo"] == modelo)
    & (preds["fold_ano_teste"] == fold)
    & (preds["prob_predita"] >= risco_min)
].copy()
if mes is not None:
    df = df[df["target_mes"] == mes]

df = df.merge(municipios[["cod_ibge", "nome_municipio"]], on="cod_ibge", how="left")
# zip(*serie_vazia) retorna [], que não pode ser unpacked em 2 — proteger o caso
if df.empty:
    df["categoria"] = []
    df["emoji"] = []
else:
    df["categoria"], df["emoji"] = zip(*df["prob_predita"].apply(categorizar_risco))
df = df.sort_values("prob_predita", ascending=False)

# --- 4 métricas no topo ---
n_total = len(df)
n_critico = int((df["prob_predita"] >= 0.75).sum())
n_alto = int(((df["prob_predita"] >= 0.50) & (df["prob_predita"] < 0.75)).sum())
n_moderado = int(((df["prob_predita"] >= 0.25) & (df["prob_predita"] < 0.50)).sum())

metric_row(
    metric(t("alertas.metricas.total_label"), f"{n_total:,}",
           delta=t("alertas.metricas.total_delta", limiar=f"{risco_min:.0%}")),
    metric(t("comum.criticos"), f"{n_critico:,}",
           delta=t("alertas.metricas.criticos_delta")),
    metric(t("comum.altos"), f"{n_alto:,}",
           delta=t("alertas.metricas.altos_delta")),
    metric(t("comum.moderados"), f"{n_moderado:,}",
           delta=t("alertas.metricas.moderados_delta")),
)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
st.markdown(risk_legend(), unsafe_allow_html=True)
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# --- Tabela ---
if df.empty:
    st.info(t("erro.sem_alertas_limiar"))
else:
    df_display = df[[
        "categoria", "nome_municipio", "cod_ibge", "target_ano", "target_mes",
        "prob_predita", "y_true", "surto_atual",
    ]].copy()
    df_display["mes_predito"] = df_display.apply(
        lambda r: ano_mes_humano(int(r["target_ano"]), int(r["target_mes"])),
        axis=1,
    )
    df_display["surto_real"] = df_display["y_true"].map(
        {1: t("comum.sim"), 0: t("comum.nao")}
    )
    df_display["em_surto_agora"] = df_display["surto_atual"].map(
        {1: t("comum.sim"), 0: t("comum.nao")}
    )
    # ProgressColumn com format "%" não multiplica internamente — passamos
    # o valor já em escala 0-100 para que "%.0f%%" produza ex.: "85%".
    df_display["prob_pct"] = df_display["prob_predita"] * 100
    df_display = df_display[[
        "categoria", "nome_municipio", "cod_ibge",
        "mes_predito", "prob_pct", "surto_real", "em_surto_agora",
    ]]
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "categoria": st.column_config.TextColumn(t("alertas.tabela.risco"), width="small"),
            "nome_municipio": t("alertas.tabela.municipio"),
            "cod_ibge": st.column_config.TextColumn(t("alertas.tabela.codigo_ibge"), width="small"),
            "mes_predito": st.column_config.TextColumn(t("alertas.tabela.mes_predito")),
            "prob_pct": st.column_config.ProgressColumn(
                t("alertas.tabela.probabilidade"),
                min_value=0, max_value=100, format="%.0f%%",
            ),
            "surto_real": st.column_config.TextColumn(
                t("alertas.tabela.surto_real"),
                help=t("alertas.tabela.surto_real_help"),
                width="small",
            ),
            "em_surto_agora": st.column_config.TextColumn(
                t("alertas.tabela.em_surto_agora"),
                help=t("alertas.tabela.em_surto_agora_help"),
                width="small",
            ),
        },
        height=520,
    )

    # --- Avaliação retroativa do recorte ---
    n_corretos = int(df["y_true"].sum())
    precisao = n_corretos / n_total * 100 if n_total else 0
    n_antecipacao = int(((df["y_true"] == 1) & (df["surto_atual"] == 0)).sum())

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    metric_row(
        metric(t("alertas.avaliacao.precisao_label"),
               f"{precisao:.1f}", "%",
               delta=t("alertas.avaliacao.precisao_delta",
                       n_corretos=f"{n_corretos:,}", n_total=f"{n_total:,}")),
        metric(t("alertas.avaliacao.antecipacao_label"),
               f"{n_antecipacao:,}",
               delta=t("alertas.avaliacao.antecipacao_delta")),
    )

st.markdown(
    '<hr style="border:none;border-top:1px solid var(--c-line);margin:32px 0 16px">',
    unsafe_allow_html=True,
)
st.caption(t("alertas.rodape"))
