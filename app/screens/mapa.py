"""
Página: Mapa de SP — visão geográfica das predições.

scatter_mapbox por município (lat/lon dos centróides). Versão futura pode
trocar por choropleth com geojson dos limites municipais.
"""
import plotly.express as px
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
    idx_default,
)
from lib.tema import (
    metric,
    metric_row,
    page_header,
    risk_legend,
)

municipios = carregar_municipios()
preds = carregar_predicoes()

# --- Sidebar ---
with st.sidebar:
    st.markdown("### Filtros")
    doencas_disp = sorted(preds["doenca"].unique())
    doenca = st.selectbox(
        "Doença", doencas_disp,
        index=idx_default(doencas_disp, DEFAULT_DOENCA),
        format_func=nome_doenca,
    )
    definicoes_disp = sorted(preds[preds["doenca"] == doenca]["definicao"].unique())
    definicao = st.selectbox(
        "Definição de surto", definicoes_disp,
        index=idx_default(definicoes_disp, DEFAULT_DEFINICAO),
        format_func=nome_definicao,
    )
    modelos = sorted(
        preds[(preds["doenca"] == doenca) & (preds["definicao"] == definicao)]["modelo"].unique()
    )
    modelo = st.selectbox(
        "Modelo", modelos,
        index=idx_default(modelos, DEFAULT_MODELO),
        format_func=nome_modelo,
    )
    folds_disp = sorted(preds["fold_ano_teste"].unique())
    fold = st.selectbox(
        "Ano de teste", folds_disp,
        index=len(folds_disp) - 1,
    )

    meses_disp = sorted(
        preds[(preds["doenca"] == doenca) & (preds["definicao"] == definicao)
              & (preds["modelo"] == modelo) & (preds["fold_ano_teste"] == fold)]["mes"].unique()
    )
    mes = st.selectbox(
        "Mês de referência", meses_disp,
        index=len(meses_disp) // 2,
        format_func=nome_mes,
    )

# --- Filtrar predições ---
df = preds[
    (preds["doenca"] == doenca)
    & (preds["definicao"] == definicao)
    & (preds["modelo"] == modelo)
    & (preds["fold_ano_teste"] == fold)
    & (preds["mes"] == mes)
].copy()
df = df.merge(
    municipios[["cod_ibge", "nome_municipio", "lat", "lon"]],
    on="cod_ibge", how="left",
)

# --- Header ---
page_header(
    titulo="Mapa de risco — São Paulo",
    descricao=(
        f"Probabilidade prevista de surto em {ano_mes_humano(fold, mes)} para "
        f"{nome_doenca(doenca)} · {nome_definicao(definicao)} · {nome_modelo(modelo)}. "
        "Cada ponto = 1 município. Cor indica nível de risco."
    ),
    crumbs=f"PLATAFORMA / MAPA / {nome_doenca(doenca).upper()} / "
           f"{ano_mes_humano(fold, mes).upper()}",
)

# --- Métricas ---
metric_row(
    metric("Municípios mapeados", f"{len(df):,}"),
    metric("Críticos",
           f"{int((df['prob_predita'] >= 0.75).sum()):,}",
           delta="≥ 75% prob."),
    metric("Altos",
           f"{int(((df['prob_predita'] >= 0.50) & (df['prob_predita'] < 0.75)).sum()):,}",
           delta="50% a 75%"),
    metric("Risco médio", f"{df['prob_predita'].mean():.0%}",
           delta="média estadual"),
)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
st.markdown(risk_legend(), unsafe_allow_html=True)
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# --- Mapa ---
fig = px.scatter_mapbox(
    df,
    lat="lat",
    lon="lon",
    color="prob_predita",
    color_continuous_scale=[
        (0.00, "#15803d"),
        (0.25, "#a16207"),
        (0.50, "#ea580c"),
        (1.00, "#dc2626"),
    ],
    range_color=(0, 1),
    size_max=15,
    hover_name="nome_municipio",
    hover_data={
        "prob_predita": ":.2%",
        "y_true": True,
        "lat": False,
        "lon": False,
    },
    zoom=5.5,
    center={"lat": -22.5, "lon": -48.5},
    height=620,
)
fig.update_layout(
    mapbox_style="carto-positron",
    margin=dict(l=0, r=0, t=0, b=0),
    coloraxis_colorbar=dict(title="Prob.", tickformat=".0%"),
    font=dict(family="Geist, system-ui, sans-serif", color="#0f172a"),
    paper_bgcolor="#ffffff",
)
st.plotly_chart(fig, use_container_width=True)

# --- Top 5 críticos ---
top5 = df.nlargest(5, "prob_predita")[["nome_municipio", "cod_ibge", "prob_predita", "y_true"]].copy()
if not top5.empty:
    top5["prob_pct"] = top5["prob_predita"] * 100
    top5["surto_real"] = top5["y_true"].map({1: "Sim", 0: "Não"})
    top5 = top5[["nome_municipio", "cod_ibge", "prob_pct", "surto_real"]]
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div class="card-section-label">Top 5 municípios em maior risco</div>',
        unsafe_allow_html=True,
    )
    st.dataframe(
        top5,
        use_container_width=True,
        hide_index=True,
        column_config={
            "nome_municipio": "Município",
            "cod_ibge": st.column_config.TextColumn("Código IBGE", width="small"),
            "prob_pct": st.column_config.ProgressColumn(
                "Probabilidade", min_value=0, max_value=100, format="%.0f%%",
            ),
            "surto_real": st.column_config.TextColumn("Surto real?", width="small"),
        },
    )

st.markdown(
    '<hr style="border:none;border-top:1px solid var(--c-line);margin:32px 0 12px">',
    unsafe_allow_html=True,
)
st.caption(
    "Mapa interativo: clique e arraste para mover, scroll para zoom, "
    "passe o mouse sobre um ponto para ver detalhes. "
    "Versão futura: choropleth com geojson dos limites municipais."
)

