"""
Página: Lista de alertas — municípios em maior risco previsto.

Usa as predições calculadas (predictions.parquet) para mostrar onde o sistema
teria emitido alerta. Em produção, seria substituído por uma rotina mensal
que carrega os modelos e prediz com features atualizadas.
"""
import streamlit as st

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
    st.markdown("### Filtros")

    doencas_disponiveis = sorted(preds["doenca"].unique())
    doenca = st.selectbox(
        "Doença", doencas_disponiveis,
        index=idx_default(doencas_disponiveis, DEFAULT_DOENCA),
        format_func=nome_doenca,
    )

    definicoes_disponiveis = sorted(
        preds[preds["doenca"] == doenca]["definicao"].unique()
    )
    definicao = st.selectbox(
        "Definição de surto", definicoes_disponiveis,
        index=idx_default(definicoes_disponiveis, DEFAULT_DEFINICAO),
        format_func=nome_definicao,
        help=(
            "Canal endêmico = método oficial Ministério da Saúde · "
            "Z-score = desvio do baseline histórico · "
            "100 ou 300 casos / 100 mil hab = limiar bruto de incidência"
        ),
    )

    modelos_disponiveis = sorted(
        preds[(preds["doenca"] == doenca) & (preds["definicao"] == definicao)]["modelo"].unique()
    )
    modelo = st.selectbox(
        "Modelo", modelos_disponiveis,
        index=idx_default(modelos_disponiveis, DEFAULT_MODELO),
        format_func=nome_modelo,
    )

    folds = sorted(preds["fold_ano_teste"].unique())
    fold = st.selectbox(
        "Ano de teste", folds, index=len(folds) - 1,
        help="Cada ano é uma rodada de validação temporal (expanding window).",
    )

    meses_disp = sorted(
        preds[(preds["doenca"] == doenca) & (preds["definicao"] == definicao)
              & (preds["modelo"] == modelo) & (preds["fold_ano_teste"] == fold)]["mes"].unique()
    )
    mes_sel = st.selectbox(
        "Mês de referência", ["Todos"] + list(meses_disp), index=0,
        format_func=lambda x: "Todos os meses" if x == "Todos" else nome_mes(x),
        help=("Mês em que a predição foi feita; o alerta vale para o mês seguinte. "
              "Em produção, este filtro selecionaria o mês corrente."),
    )
    mes = None if mes_sel == "Todos" else int(mes_sel)

    risco_min = st.slider("Probabilidade mínima exibida", 0.0, 1.0, 0.5, 0.05)

_recorte_mes = ano_mes_humano(fold, mes) if mes else f"{fold} (todos os meses)"

# --- Header ---
page_header(
    titulo="Alertas do mês",
    descricao=(
        f"Municípios em risco previsto · {_recorte_mes} · "
        f"{nome_doenca(doenca)} · {nome_definicao(definicao)} · {nome_modelo(modelo)}. "
        "Cada linha é uma predição mensal: probabilidade de surto no mês seguinte ao mês exibido."
    ),
    crumbs=f"PLATAFORMA / ALERTAS / {nome_doenca(doenca).upper()} / "
           f"{_recorte_mes.upper()}",
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
    df = df[df["mes"] == mes]

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
    metric("Total de alertas", f"{n_total:,}",
           delta=f"≥ {risco_min:.0%} de probabilidade"),
    metric("Críticos", f"{n_critico:,}", delta="Probabilidade ≥ 75%"),
    metric("Altos", f"{n_alto:,}", delta="50% a 75%"),
    metric("Moderados", f"{n_moderado:,}", delta="25% a 50%"),
)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
st.markdown(risk_legend(), unsafe_allow_html=True)
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# --- Tabela ---
if df.empty:
    st.info("Nenhuma predição acima do limiar selecionado.")
else:
    df_display = df[[
        "categoria", "nome_municipio", "cod_ibge", "ano", "mes",
        "prob_predita", "y_true", "surto_atual",
    ]].copy()
    # Mês predito = mês seguinte ao mês exibido (em dezembro vira janeiro do próximo ano)
    df_display["mes_predito"] = df_display.apply(
        lambda r: ano_mes_humano(
            int(r["ano"]) + (1 if int(r["mes"]) == 12 else 0),
            (int(r["mes"]) % 12) + 1,
        ),
        axis=1,
    )
    df_display["surto_real"] = df_display["y_true"].map({1: "Sim", 0: "Não"})
    df_display["em_surto_agora"] = df_display["surto_atual"].map({1: "Sim", 0: "Não"})
    df_display = df_display[[
        "categoria", "nome_municipio", "cod_ibge",
        "mes_predito", "prob_predita", "surto_real", "em_surto_agora",
    ]]
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "categoria": st.column_config.TextColumn("Risco", width="small"),
            "nome_municipio": "Município",
            "cod_ibge": st.column_config.TextColumn("Código IBGE", width="small"),
            "mes_predito": st.column_config.TextColumn("Mês predito"),
            "prob_predita": st.column_config.ProgressColumn(
                "Probabilidade", min_value=0, max_value=1, format="%.0f%%",
            ),
            "surto_real": st.column_config.TextColumn(
                "Surto real?",
                help="O surto realmente ocorreu naquele mês? (avaliação retroativa)",
                width="small",
            ),
            "em_surto_agora": st.column_config.TextColumn(
                "Em surto agora?",
                help=(
                    "Sim = município já estava em surto no mês de referência "
                    "(alerta = manutenção). Não = antecipação verdadeira (modelo prevê INÍCIO)."
                ),
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
        metric("Precisão neste recorte", f"{precisao:.1f}", "%",
               delta=f"{n_corretos:,} de {n_total:,} alertas correspondiam a surto real"),
        metric("Antecipações verdadeiras", f"{n_antecipacao:,}",
               delta="alertas que previram INÍCIO de surto (não manutenção)"),
    )

st.markdown(
    '<hr style="border:none;border-top:1px solid var(--c-line);margin:32px 0 16px">',
    unsafe_allow_html=True,
)
st.caption(
    "Use a página **Município** para ver a justificativa SHAP detalhada de cada alerta. "
    "A coluna *Em surto agora?* distingue antecipação (=0) de manutenção (=1) — "
    "antecipações verdadeiras são o achado central da pesquisa."
)

