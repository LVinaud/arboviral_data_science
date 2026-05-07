"""
Página: Mapa de SP — visão geográfica das predições.

Implementação simples com scatter_mapbox (lat/lon dos centróides) — leve e
não requer geojson. Versão futura pode usar choropleth com geojson dos limites
municipais (https://github.com/tbrugz/geodata-br).
"""
import plotly.express as px
import streamlit as st

from lib.carregar import carregar_municipios, carregar_predicoes

st.set_page_config(page_title="Mapa", page_icon="🗺️", layout="wide")

st.title("🗺️ Mapa de Risco — Estado de São Paulo")
st.caption(
    "Cada ponto representa um município. Cor indica probabilidade prevista de "
    "surto no mês selecionado; tamanho do ponto é proporcional à população."
)

municipios = carregar_municipios()
preds = carregar_predicoes()

# --- Sidebar ---
with st.sidebar:
    st.header("Filtros")
    doenca = st.selectbox("Doença", sorted(preds["doenca"].unique()), index=0)
    definicao = st.selectbox(
        "Definição de surto",
        sorted(preds[preds["doenca"] == doenca]["definicao"].unique()),
    )
    modelos = sorted(preds[
        (preds["doenca"] == doenca) & (preds["definicao"] == definicao)
    ]["modelo"].unique())
    modelo = st.selectbox("Modelo", modelos,
                          index=modelos.index("rf") if "rf" in modelos else 0)
    fold = st.selectbox(
        "Ano de teste",
        sorted(preds["fold_ano_teste"].unique()),
        index=len(preds["fold_ano_teste"].unique()) - 1,
    )

    # Mês específico dentro do fold
    meses_disponiveis = sorted(preds[
        (preds["doenca"] == doenca) & (preds["definicao"] == definicao) &
        (preds["modelo"] == modelo) & (preds["fold_ano_teste"] == fold)
    ]["mes"].unique())
    mes = st.selectbox("Mês de referência", meses_disponiveis,
                       index=len(meses_disponiveis) // 2)

# --- Filtrar predições do mês ---
df = preds[
    (preds["doenca"] == doenca) &
    (preds["definicao"] == definicao) &
    (preds["modelo"] == modelo) &
    (preds["fold_ano_teste"] == fold) &
    (preds["mes"] == mes)
].copy()

df = df.merge(municipios[["cod_ibge", "nome_municipio", "lat", "lon"]],
              on="cod_ibge", how="left")

# Adicionar população do master mais recente (via labels que tem cod_ibge)
# Para simplicidade, usar tamanho fixo se não tiver pop
df["tamanho"] = 8  # tamanho default; melhoria futura: usar populacao_estimada do master

# Categorizar
def cat(p):
    if p >= 0.8: return "🔴 Crítico"
    if p >= 0.5: return "🟠 Alto"
    if p >= 0.2: return "🟡 Moderado"
    return "🟢 Baixo"
df["categoria"] = df["prob_predita"].apply(cat)

# Métricas
col1, col2, col3, col4 = st.columns(4)
col1.metric("Municípios mapeados", len(df))
col2.metric("🔴 Críticos", int((df["prob_predita"] >= 0.8).sum()))
col3.metric("🟠 Altos", int(((df["prob_predita"] >= 0.5) & (df["prob_predita"] < 0.8)).sum()))
col4.metric("Risco médio", f"{df['prob_predita'].mean():.1%}")

st.subheader(
    f"{doenca.replace('_', ' ').title()} — {definicao} — Predição para o mês {mes:02d}/{fold}"
)

# Mapa Plotly scatter_mapbox
fig = px.scatter_mapbox(
    df,
    lat="lat",
    lon="lon",
    color="prob_predita",
    color_continuous_scale=[
        (0.0, "#16a34a"), (0.2, "#facc15"), (0.5, "#ea580c"), (1.0, "#dc2626"),
    ],
    range_color=(0, 1),
    size_max=15,
    hover_name="nome_municipio",
    hover_data={
        "categoria": True,
        "prob_predita": ":.2%",
        "y_true": True,
        "lat": False,
        "lon": False,
    },
    zoom=5.5,
    center={"lat": -22.5, "lon": -48.5},
    height=650,
)
fig.update_layout(
    mapbox_style="carto-positron",
    margin=dict(l=0, r=0, t=0, b=0),
    coloraxis_colorbar=dict(title="Prob. surto", tickformat=".0%"),
)
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "💡 Mapa interativo: clique e arraste para mover, scroll para zoom, "
    "passe o mouse sobre um ponto para ver detalhes do município. "
    "Cor verde → vermelho indica probabilidade crescente de surto."
)
