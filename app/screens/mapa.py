"""
Página: Mapa de SP — visão geográfica das predições com 3 granularidades.

Granularidades selecionáveis (sidebar):
  - Município (645)        → scatter colorido por probabilidade
  - DRS (17)               → choropleth (cor = prob) + bolinhas (tamanho = casos)
  - Reg. Intermediária(11) → idem DRS, divisão IBGE 2017

Animação mensal via slider/play do Plotly. A camada de agregação espacial vive
em `lib/agregacao_geo.py` (não toca no core `src/arboviral/`).
"""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from i18n import t
from lib.agregacao_geo import (
    agregar,
    carregar_geojson_drs,
    carregar_geojson_rgi,
)
from lib.carregar import carregar_master, carregar_predicoes
from lib.labels import (
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

# Escala alinhada ao design system (verde→mostarda→laranja→vermelho a 0/0.25/0.5/1)
ESCALA_RISCO = [
    [0.00, "#15803d"],
    [0.25, "#a16207"],
    [0.50, "#ea580c"],
    [1.00, "#dc2626"],
]


# ============================================================
# Construção do mapa animado
# ============================================================

def _tamanho_bolinhas(casos: np.ndarray, max_diametro: int = 50) -> np.ndarray:
    """Escala raiz-quadrada do número de casos para o diâmetro da bolinha.

    Raiz quadrada (não linear) porque casos podem variar 1000x entre regiões —
    sem isso, regiões pequenas viram pontos invisíveis e a Grande SP vira um
    blob que cobre o estado. Reescala globalmente pelo máximo geral, não por
    frame (senão um mês quente deturpa a percepção dos outros).
    """
    if casos.max() == 0:
        return np.zeros_like(casos, dtype=float)
    return np.sqrt(casos / casos.max()) * max_diametro


def construir_mapa_animado(df, nivel: str, geojson: dict | None) -> go.Figure:
    """Cria figura Plotly com um frame por mês predito.

    df: saída de agregacao_geo.agregar() — colunas id_unidade, nome_unidade,
        target_ano, target_mes, prob_predita, casos, populacao, lat, lon.
    nivel: 'municipio', 'drs' ou 'rgi'.
    geojson: dict do GeoJSON correspondente (None para município).
    """
    meses = sorted(df["target_mes"].unique())
    casos_max_global = max(df["casos"].max(), 1)

    # Conversão para string em `locations` é necessária porque o featureidkey
    # do plotly compara strings (mesmo que o id no geojson seja int).
    feat_key = "properties.id" if nivel == "drs" else "properties.codigo"

    frames = []
    sliders_steps = []

    for mes in meses:
        dfm = df[df["target_mes"] == mes].copy().reset_index(drop=True)
        traces = []

        if nivel == "municipio":
            # Único layer: scatter com cor=prob. Tamanho fixo (sem layer de casos).
            traces.append(go.Scattermapbox(
                lat=dfm["lat"], lon=dfm["lon"],
                mode="markers",
                marker=dict(
                    size=11,
                    color=dfm["prob_predita"],
                    colorscale=ESCALA_RISCO,
                    cmin=0, cmax=1,
                    showscale=True,
                    colorbar=dict(
                        title="Prob.", tickformat=".0%", thickness=14,
                        bgcolor="rgba(0,0,0,0)", outlinewidth=0,
                    ),
                ),
                hovertext=dfm["nome_unidade"],
                customdata=np.stack(
                    [dfm["prob_predita"], dfm["casos"], dfm["populacao"]], axis=-1,
                ),
                hovertemplate=(
                    "<b>%{hovertext}</b><br>"
                    f"{t('mapa.hover.probabilidade')}: " "%{customdata[0]:.1%}<br>"
                    f"{t('mapa.hover.casos')}: " "%{customdata[1]:,}<br>"
                    f"{t('mapa.hover.populacao')}: " "%{customdata[2]:,}<extra></extra>"
                ),
                name="",
            ))
        else:
            # Choropleth — cor pela probabilidade
            traces.append(go.Choroplethmapbox(
                geojson=geojson,
                locations=dfm["id_unidade"].astype(str),
                z=dfm["prob_predita"],
                featureidkey=feat_key,
                colorscale=ESCALA_RISCO,
                zmin=0, zmax=1,
                marker_line_width=1.5,
                marker_line_color="white",
                colorbar=dict(
                    title="Prob.", tickformat=".0%", thickness=14,
                    bgcolor="rgba(0,0,0,0)", outlinewidth=0,
                ),
                hovertext=dfm["nome_unidade"],
                customdata=np.stack(
                    [dfm["prob_predita"], dfm["casos"], dfm["populacao"]], axis=-1,
                ),
                hovertemplate=(
                    "<b>%{hovertext}</b><br>"
                    f"{t('mapa.hover.probabilidade')}: " "%{customdata[0]:.1%}<br>"
                    f"{t('mapa.hover.casos')}: " "%{customdata[1]:,}<br>"
                    f"{t('mapa.hover.populacao')}: " "%{customdata[2]:,}<extra></extra>"
                ),
                name="",
                showscale=True,
            ))
            # Bolinhas — tamanho pelos casos absolutos (escala global)
            tamanhos = _tamanho_bolinhas(dfm["casos"].values)
            traces.append(go.Scattermapbox(
                lat=dfm["lat"], lon=dfm["lon"],
                mode="markers",
                marker=dict(
                    size=tamanhos,
                    color="rgba(15, 23, 42, 0.65)",
                    sizemode="diameter",
                    sizemin=2,
                ),
                hovertext=dfm["nome_unidade"],
                customdata=dfm["casos"],
                hovertemplate=(
                    "<b>%{hovertext}</b><br>"
                    f"{t('mapa.hover.casos')}: " "%{customdata:,}<extra></extra>"
                ),
                name="",
                showlegend=False,
            ))

        frames.append(go.Frame(data=traces, name=str(mes)))
        sliders_steps.append(dict(
            method="animate",
            label=nome_mes(mes),
            args=[[str(mes)], dict(
                mode="immediate",
                frame=dict(duration=400, redraw=True),
                transition=dict(duration=250),
            )],
        ))

    # Figura inicial = primeiro frame
    fig = go.Figure(data=frames[0].data, frames=frames)
    # Fundo transparente em TODOS os controles para que o app respeite o
    # background do Streamlit (não desenhamos quadrados brancos por cima).
    # Botões e slider são alinhados verticalmente no mesmo Y (yanchor="top"
    # em ambos, com offsets idênticos de padding).
    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            zoom=5.5,
            center={"lat": -22.5, "lon": -48.5},
        ),
        height=640,
        margin=dict(l=0, r=0, t=0, b=110),
        font=dict(family="Geist, system-ui, sans-serif", color="#0f172a"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        sliders=[dict(
            active=0,
            x=0.08, y=-0.02,
            xanchor="left", yanchor="top",
            len=0.90,
            pad=dict(t=40, b=10, l=0, r=0),
            bgcolor="rgba(15,23,42,0.10)",
            bordercolor="rgba(15,23,42,0.18)",
            borderwidth=1,
            activebgcolor="rgba(15,23,42,0.55)",
            tickcolor="rgba(15,23,42,0.45)",
            ticklen=4,
            minorticklen=2,
            font=dict(size=11, color="#0f172a"),
            currentvalue=dict(
                prefix="", visible=True, offset=10, xanchor="left",
                font=dict(size=13, color="#0f172a"),
            ),
            steps=sliders_steps,
            transition=dict(duration=250),
        )],
        updatemenus=[dict(
            type="buttons",
            direction="left",
            showactive=False,
            x=0.0, y=-0.02,
            xanchor="left", yanchor="top",
            pad=dict(t=40, b=10, l=0, r=0),
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(15,23,42,0.15)",
            font=dict(color="#0f172a", size=14),
            buttons=[
                dict(
                    label="▶",
                    method="animate",
                    args=[None, dict(
                        frame=dict(duration=700, redraw=True),
                        transition=dict(duration=250),
                        fromcurrent=True, mode="immediate",
                    )],
                ),
                dict(
                    label="⏸",
                    method="animate",
                    args=[[None], dict(
                        frame=dict(duration=0, redraw=False),
                        mode="immediate",
                    )],
                ),
            ],
        )],
    )
    return fig


# ============================================================
# Tela
# ============================================================

preds = carregar_predicoes()
master = carregar_master()

# --- Sidebar ---
with st.sidebar:
    st.markdown(f"### {t('comum.filtros')}")

    # Granularidade vem PRIMEIRO porque é o eixo dominante da visualização
    _gran_opts = ["municipio", "drs", "rgi"]
    nivel = st.radio(
        t("mapa.granularidade.label"),
        _gran_opts,
        index=0,
        format_func=lambda k: t(f"mapa.granularidade.{k}"),
        help=t("mapa.granularidade.help"),
        key="mapa_nivel",
    )

    doencas_disp = sorted(preds["doenca"].unique())
    doenca = st.selectbox(
        t("comum.doenca"), doencas_disp,
        index=idx_default(doencas_disp, DEFAULT_DOENCA),
        format_func=nome_doenca,
    )
    definicoes_disp = sorted(preds[preds["doenca"] == doenca]["definicao"].unique())
    definicao = st.selectbox(
        t("comum.definicao_surto"), definicoes_disp,
        index=idx_default(definicoes_disp, DEFAULT_DEFINICAO),
        format_func=nome_definicao,
    )
    modelos = sorted(
        preds[(preds["doenca"] == doenca) & (preds["definicao"] == definicao)]["modelo"].unique()
    )
    modelo = st.selectbox(
        t("comum.modelo"), modelos,
        index=idx_default(modelos, DEFAULT_MODELO),
        format_func=nome_modelo,
    )
    folds_disp = sorted(preds["fold_ano_teste"].unique())
    fold = st.selectbox(
        t("comum.ano_teste"), folds_disp,
        index=len(folds_disp) - 1,
    )

# --- Filtrar predições no recorte (doença × definição × modelo × fold) ---
preds_recorte = preds[
    (preds["doenca"] == doenca)
    & (preds["definicao"] == definicao)
    & (preds["modelo"] == modelo)
    & (preds["fold_ano_teste"] == fold)
].copy()

# --- Agregar conforme nível ---
df_agg = agregar(preds_recorte, master, doenca, nivel)
geojson = None
if nivel == "drs":
    geojson = carregar_geojson_drs()
elif nivel == "rgi":
    geojson = carregar_geojson_rgi()

# --- Header ---
page_header(
    titulo=t("mapa.titulo"),
    descricao=t(
        "mapa.descricao",
        fold=fold,
        doenca=nome_doenca(doenca),
        definicao=nome_definicao(definicao),
        modelo=nome_modelo(modelo),
    ),
    crumbs=t("mapa.crumbs", doenca_upper=nome_doenca(doenca).upper(), fold=fold),
)

# --- Métricas no topo (ano inteiro, não um mês específico) ---
# 'pico de unidades críticas' = quantas unidades atingiram ≥75% em ALGUM mês.
pico_criticos = (
    df_agg[df_agg["prob_predita"] >= 0.75]
    .groupby("id_unidade").size().shape[0]
)
casos_totais_ano = int(df_agg["casos"].sum())
risco_medio_anual = float(
    (df_agg["prob_predita"] * df_agg["populacao"]).sum()
    / max(df_agg["populacao"].sum(), 1)
)
n_unidades = df_agg["id_unidade"].nunique()

metric_row(
    metric(t("mapa.metricas.unidades_label"), f"{n_unidades:,}"),
    metric(t("mapa.metricas.criticos_label"), f"{pico_criticos:,}",
           delta=t("mapa.metricas.criticos_delta")),
    metric(t("mapa.metricas.casos_ano_label"),
           f"{casos_totais_ano:,}".replace(",", "."),
           delta=t("mapa.metricas.casos_ano_delta")),
    metric(t("mapa.metricas.risco_medio_label"),
           f"{risco_medio_anual:.0%}",
           delta=t("mapa.metricas.risco_medio_delta")),
)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
st.markdown(risk_legend(), unsafe_allow_html=True)
st.markdown(
    f'<div style="font-size:12px;color:var(--c-muted);margin:6px 0 12px 0">'
    f'{t("mapa.legenda.cor")}<br>'
    f'{t("mapa.legenda.bolinha") if nivel != "municipio" else ""}'
    f'</div>',
    unsafe_allow_html=True,
)

# --- Mapa ---
fig = construir_mapa_animado(df_agg, nivel, geojson)
st.plotly_chart(fig, use_container_width=True)

# --- Top 5 por risco médio anual ---
top5 = (
    df_agg.groupby(["id_unidade", "nome_unidade"], as_index=False)
    .agg(
        prob_media=("prob_predita", "mean"),
        casos=("casos", "sum"),
    )
    .nlargest(5, "prob_media")
)
if not top5.empty:
    top5["prob_pct"] = top5["prob_media"] * 100
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div class="card-section-label">{t("mapa.top5.secao")}</div>',
        unsafe_allow_html=True,
    )
    st.dataframe(
        top5[["nome_unidade", "prob_pct", "casos"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "nome_unidade": t("comum.municipio") if nivel == "municipio"
                            else t("mapa.granularidade." + nivel),
            "prob_pct": st.column_config.ProgressColumn(
                t("comum.probabilidade"),
                min_value=0, max_value=100, format="%.0f%%",
            ),
            "casos": st.column_config.NumberColumn(
                t("mapa.top5.casos"), format="%d",
            ),
        },
    )

st.markdown(
    '<hr style="border:none;border-top:1px solid var(--c-line);margin:32px 0 12px">',
    unsafe_allow_html=True,
)
st.caption(t("mapa.rodape"))
