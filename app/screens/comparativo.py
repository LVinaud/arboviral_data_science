"""
Página: Comparativo entre as 4 doenças para um município escolhido.
Mostra de uma vez se o município está em risco de qualquer arbovirose.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from i18n import t
from lib.carregar import carregar_master, carregar_municipios, carregar_predicoes
from lib.labels import nome_definicao, nome_doenca, nome_mes, nome_modelo
from lib.predicao import DEFAULT_DEFINICAO, DEFAULT_MODELO, idx_default
from lib.tema import (
    chip,
    page_header,
    risk_legend,
    section_label,
)

municipios = carregar_municipios()
preds = carregar_predicoes()
master = carregar_master()

with st.sidebar:
    st.markdown(f"### {t('comum.selecao')}")
    nomes = sorted(municipios["nome_municipio"].tolist())
    nome_sel = st.selectbox(
        t("comum.municipio"), nomes,
        index=nomes.index("São Paulo") if "São Paulo" in nomes else 0,
    )
    cod = int(municipios[municipios["nome_municipio"] == nome_sel]["cod_ibge"].iloc[0])

    definicoes_disp = sorted(preds["definicao"].unique())
    definicao = st.selectbox(
        t("comum.definicao_surto"), definicoes_disp,
        index=idx_default(definicoes_disp, DEFAULT_DEFINICAO),
        format_func=nome_definicao,
    )
    modelos_disp = sorted(preds[preds["definicao"] == definicao]["modelo"].unique())
    modelo = st.selectbox(
        t("comum.modelo"), modelos_disp,
        index=idx_default(modelos_disp, DEFAULT_MODELO),
        format_func=nome_modelo,
    )
    fold = st.selectbox(
        t("comum.ano_teste"), sorted(preds["fold_ano_teste"].unique()),
        index=len(preds["fold_ano_teste"].unique()) - 1,
    )

# --- Header ---
page_header(
    titulo=t("comparativo.titulo", municipio=nome_sel),
    descricao=t(
        "comparativo.descricao",
        fold=fold,
        definicao=nome_definicao(definicao),
        modelo=nome_modelo(modelo),
    ),
    crumbs=t("comparativo.crumbs", nome_upper=nome_sel.upper()),
)
st.markdown(
    " ".join([
        chip(f"IBGE {cod}", "mono"),
        chip(t("comparativo.chips.ano_teste", fold=fold)),
        chip(nome_definicao(definicao)),
    ]),
    unsafe_allow_html=True,
)
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# --- Heatmap ---
df = preds[
    (preds["cod_ibge"] == cod)
    & (preds["definicao"] == definicao)
    & (preds["modelo"] == modelo)
    & (preds["fold_ano_teste"] == fold)
].copy()

st.markdown(section_label(t("comparativo.secao_heatmap")), unsafe_allow_html=True)
st.markdown(risk_legend(), unsafe_allow_html=True)
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

if df.empty:
    st.warning(t("erro.sem_dados_combinacao"))
else:
    # Pivota pelo mês PREDITO — para fold=2024 isso dá Jan→Dez/2024 alinhado
    # com o ano de teste, em vez de Dez/2023→Nov/2024 (mês das features).
    pivot = (
        df.pivot_table(index="doenca", columns="target_mes",
                       values="prob_predita", aggfunc="mean")
        .reindex(index=["dengue", "chikungunya", "zika", "febre_amarela"])
    )
    pivot.columns = [nome_mes(c)[:3] for c in pivot.columns]

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=[nome_doenca(d) for d in pivot.index],
        colorscale=[
            [0.00, "#15803d"],
            [0.25, "#a16207"],
            [0.50, "#ea580c"],
            [1.00, "#dc2626"],
        ],
        zmin=0, zmax=1,
        text=[[f"{v:.0%}" if pd.notna(v) else "" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont={"size": 11, "color": "rgba(15,23,42,0.85)"},
        hoverongaps=False,
        colorbar=dict(title="Prob.", tickformat=".0%"),
    ))
    fig.update_layout(
        xaxis=dict(title=t("comparativo.x_axis_mes_predito")),
        yaxis=dict(title=t("comparativo.y_axis_doenca")),
        height=380,
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Geist, system-ui, sans-serif", color="#0f172a"),
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Histórico das 4 doenças ---
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
st.markdown(section_label(t("comparativo.secao_historico")),
            unsafe_allow_html=True)

hist = master[master["cod_ibge"] == cod].copy()
hist["data"] = pd.to_datetime(
    hist["ano"].astype(str) + "-" + hist["mes"].astype(str).str.zfill(2)
)

doencas = ["dengue", "chikungunya", "zika", "febre_amarela"]
cores = {
    "dengue": "#dc2626",
    "chikungunya": "#ea580c",
    "zika": "#a16207",
    "febre_amarela": "#7c3aed",
}

fig_h = go.Figure()
for d in doencas:
    col = f"{d}_casos"
    if col in hist.columns:
        fig_h.add_trace(go.Scatter(
            x=hist["data"],
            y=hist[col].fillna(0),
            mode="lines",
            name=nome_doenca(d),
            line=dict(color=cores[d], width=1.6),
        ))
fig_h.update_layout(
    xaxis=dict(title=t("comum.mes"), gridcolor="#e2e8f0"),
    yaxis=dict(title=t("comparativo.y_axis_casos"), gridcolor="#e2e8f0"),
    height=360,
    legend=dict(orientation="h", y=-0.18),
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    font=dict(family="Geist, system-ui, sans-serif", color="#0f172a"),
    margin=dict(l=20, r=20, t=20, b=20),
)
st.plotly_chart(fig_h, use_container_width=True)

st.markdown(
    '<hr style="border:none;border-top:1px solid var(--c-line);margin:24px 0 12px">',
    unsafe_allow_html=True,
)
st.caption(t("comparativo.rodape"))
