"""
Página: Comparativo entre as 4 doenças para um município escolhido.

Permite ao gestor ver de uma vez se o município está em risco de qualquer
arbovirose simultaneamente.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib.carregar import carregar_master, carregar_municipios, carregar_predicoes

st.set_page_config(page_title="Comparativo", page_icon="📊", layout="wide")

st.title("📊 Comparativo entre Arboviroses")
st.caption("Visão consolidada das 4 doenças (dengue, zika, chikungunya, febre amarela) para um município.")

municipios = carregar_municipios()
preds = carregar_predicoes()
master = carregar_master()

with st.sidebar:
    st.header("Seleção")
    nome_sel = st.selectbox(
        "Município",
        sorted(municipios["nome_municipio"]),
        index=sorted(municipios["nome_municipio"].tolist()).index("São Paulo"),
    )
    cod = int(municipios[municipios["nome_municipio"] == nome_sel]["cod_ibge"].iloc[0])

    definicao = st.selectbox(
        "Definição de surto", sorted(preds["definicao"].unique()), index=0
    )
    modelos_disp = sorted(preds[preds["definicao"] == definicao]["modelo"].unique())
    modelo_default = "rf" if "rf" in modelos_disp else modelos_disp[0]
    modelo = st.selectbox("Modelo", modelos_disp, index=modelos_disp.index(modelo_default))
    fold = st.selectbox(
        "Ano de teste",
        sorted(preds["fold_ano_teste"].unique()),
        index=len(preds["fold_ano_teste"].unique()) - 1,
    )

st.subheader(f"📍 {nome_sel} — Predições por doença ({modelo}, ano {fold})")

# --- Heatmap-like: linhas = doença, colunas = mês ---
df = preds[
    (preds["cod_ibge"] == cod) &
    (preds["definicao"] == definicao) &
    (preds["modelo"] == modelo) &
    (preds["fold_ano_teste"] == fold)
].copy()

if df.empty:
    st.warning("Sem dados para essa combinação.")
else:
    pivot = (
        df.pivot_table(index="doenca", columns="mes", values="prob_predita", aggfunc="mean")
        .reindex(index=["dengue", "chikungunya", "zika", "febre_amarela"])
    )
    pivot.columns = [f"{int(c):02d}" for c in pivot.columns]

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=[d.replace("_", " ").title() for d in pivot.index],
        colorscale=[
            [0.0, "#16a34a"], [0.2, "#facc15"], [0.5, "#ea580c"], [1.0, "#dc2626"],
        ],
        zmin=0, zmax=1,
        text=[[f"{v:.0%}" if pd.notna(v) else "" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont={"size": 12},
        hoverongaps=False,
    ))
    fig.update_layout(
        xaxis_title="Mês",
        yaxis_title="Doença",
        height=400,
        coloraxis_colorbar=dict(title="Probabilidade"),
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Histórico de casos das 4 doenças no mesmo gráfico ---
st.divider()
st.subheader("📈 Histórico de casos — todas as doenças")

hist = master[master["cod_ibge"] == cod].copy()
hist["data"] = pd.to_datetime(hist["ano"].astype(str) + "-" + hist["mes"].astype(str).str.zfill(2))

doencas = ["dengue", "chikungunya", "zika", "febre_amarela"]
colors = {"dengue": "#dc2626", "chikungunya": "#ea580c", "zika": "#facc15", "febre_amarela": "#7c3aed"}

fig_h = go.Figure()
for d in doencas:
    col = f"{d}_casos"
    if col in hist.columns:
        fig_h.add_trace(go.Scatter(
            x=hist["data"],
            y=hist[col].fillna(0),
            mode="lines",
            name=d.replace("_", " ").title(),
            line=dict(color=colors[d]),
        ))
fig_h.update_layout(
    xaxis_title="Mês",
    yaxis_title="Casos notificados",
    height=400,
    legend=dict(orientation="h", y=-0.2),
)
st.plotly_chart(fig_h, use_container_width=True)

st.caption(
    "🦟 As 4 doenças compartilham o vetor *Aedes aegypti* (dengue, zika, chikungunya) "
    "ou são silvestres (febre amarela). Surtos podem ocorrer simultaneamente "
    "ou em épocas distintas dependendo das condições ambientais e de cada doença."
)
