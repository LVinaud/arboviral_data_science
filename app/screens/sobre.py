"""
Página: Sobre o projeto — explicação didática para gestores e público geral.

Página rolável em 5 seções (linguagem didática para gestor + público geral):
  1. Por que esta plataforma existe — motivação
  2. Como funciona em 4 passos — cards numerados (01..04)
  3. De onde vêm os dados — 5 grupos temáticos (saúde/clima/demo/ambiente/gestão)
  4. Como o computador aprende — validação prospectiva, baselines, AUPRC
  5. Detalhe técnico para curiosos — catálogo de 140 features escondido em
     expander (busca + filtros + distribuição por categoria, mantém auditoria)

Conteúdo textual vem de `app/i18n/{pt,en}.py` (chave `sobre.*`).

i18n: o cache de `_construir_catalogo` recebe `lang` como argumento — quando
o usuário troca de idioma, o catálogo inteiro é re-humanizado (categorias,
fontes, tipos, descrição de cada feature). Sem o argumento `lang`, o cache
preservaria os labels do idioma antigo.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from i18n import get_language, t
from lib.carregar import carregar_features
from lib.labels import humanizar_feature
from lib.tema import (
    metric,
    metric_row,
    page_header,
    section_label,
)

# Cada categoria conhecida → (chave de label i18n, prefixos, chave de fonte i18n).
# Ordem importa: a primeira que casa ganha. Mais específicas primeiro.
_CATEGORIAS: list[tuple[str, list[str], str]] = [
    ("epi_dengue", ["dengue_"], "sinan"),
    ("epi_zika", ["zika_"], "sinan"),
    ("epi_chik", ["chikungunya_"], "sinan"),
    ("epi_fa", ["febre_amarela_", "febre_"], "svs"),
    ("climaticas", ["temp_", "precip_", "umid_", "pressao_", "vento_"], "nasa_power"),
    ("sazonalidade", ["mes_sin", "mes_cos"], "calendario"),
    ("geo", ["lat", "lon", "dist_estacao_km"], "ibge_inmet"),
    ("demo_econ", ["populacao_estimada", "pib_", "gini", "idhm"], "ibge_atlas"),
    ("densidade", ["area_km2", "densidade_"], "ibge_areas"),
    ("cobertura", ["pct_"], "mapbiomas"),
    ("saude_publica", ["leitos_", "mortalidade_"], "datasus_cnes"),
    ("esf_aps", ["esf_"], "egestor"),
    ("saneamento", ["iag", "ies"], "sinisa"),
    ("vacinacao", ["cob_vac_"], "pni"),
    ("munic", ["msau"], "ibge_munic_2018"),
    ("desastres", ["mgrd", "mmam"], "ibge_munic_2020"),
    ("habitacao", ["num_aglom_", "pop_aglom_", "num_favelas", "pop_favelas"], "ibge_censos"),
    ("capag", ["capag_"], "tesouro"),
    ("predicao_meta", ["target_"], "split_features"),
]

_CHAVES = {"cod_ibge", "ano", "mes"}


@st.cache_data(show_spinner=False)
def _construir_catalogo(lang: str) -> pd.DataFrame:
    """Itera sobre todas as colunas de features.parquet e monta o catálogo.

    O argumento `lang` (idioma corrente) entra na chave de cache para que
    a troca PT↔EN invalide o catálogo e re-humanize todas as descrições.
    """
    with st.spinner(t("carregar.catalogando")):
        features = carregar_features()
    cols = [c for c in features.columns if c not in _CHAVES]

    rows: list[dict] = []
    for c in cols:
        s = features[c]
        n_total = len(s)
        n_nan = int(s.isna().sum())
        nan_pct = (n_nan / n_total * 100) if n_total else 0.0

        # Booleano "verdadeiro" (dtype bool) OU booleano disfarcado em object
        # (acontece quando ha NaN: pandas promove bool para object).
        unicos_nao_nan = set(s.dropna().unique())
        eh_bool_disfarcado = unicos_nao_nan and unicos_nao_nan.issubset({True, False, 0, 1})
        if pd.api.types.is_bool_dtype(s) or eh_bool_disfarcado:
            tipo = t("sobre.tipos.booleana")
            mn, mx, media = None, None, None
            n_true = int(s.eq(True).sum())
            n_false = (n_total - n_nan) - n_true
            extra = (
                f"{n_true:,} {t('comum.verdadeiros')} / "
                f"{n_false:,} {t('comum.falsos')}"
            ).replace(",", ".")
        elif pd.api.types.is_numeric_dtype(s):
            tipo = t("sobre.tipos.numerica")
            valores = s.dropna()
            mn = float(valores.min()) if not valores.empty else None
            mx = float(valores.max()) if not valores.empty else None
            media = float(valores.mean()) if not valores.empty else None
            extra = ""
        else:
            tipo = t("sobre.tipos.categorica")
            mn, mx, media = None, None, None
            unicos = s.dropna().astype(str).unique()
            extra = ", ".join(sorted(unicos)[:5]) + (" …" if len(unicos) > 5 else "")

        cat_chave, fonte_chave = "outras", "indef"
        for chave_cat, prefixos, chave_fonte in _CATEGORIAS:
            if any(c.startswith(p) or c == p for p in prefixos):
                cat_chave, fonte_chave = chave_cat, chave_fonte
                break

        rows.append({
            "categoria": t(f"sobre.categorias.{cat_chave}"),
            "tecnico": c,
            "humano": humanizar_feature(c),
            "tipo": tipo,
            "fonte": t(f"sobre.fontes.{fonte_chave}"),
            "nan_pct": round(nan_pct, 2),
            "min": mn,
            "media": media,
            "max": mx,
            "extra": extra,
        })

    return pd.DataFrame(rows)


catalogo = _construir_catalogo(get_language())

# --- Header ---
page_header(
    titulo=t("sobre.titulo"),
    descricao=t("sobre.descricao", n_features=len(catalogo)),
    crumbs=t("sobre.crumbs"),
)

_ESPACO = "<div style='height:32px'></div>"


def _numbered_card(badge: str, titulo: str, texto: str) -> str:
    """Card visual com badge numerado (ex.: '01') no topo. Sem emojis."""
    return (
        '<div style="background:var(--c-surface);border:1px solid var(--c-line);'
        'border-radius:12px;padding:20px;height:100%">'
        f'<div style="font-family:ui-monospace,Menlo,Consolas,monospace;'
        f'font-size:13px;font-weight:600;color:var(--c-muted);'
        f'letter-spacing:0.08em;margin-bottom:12px">{badge}</div>'
        f'<div style="font-weight:600;font-size:15px;margin-bottom:8px">{titulo}</div>'
        f'<div style="font-size:13px;color:var(--c-muted);line-height:1.5">{texto}</div>'
        "</div>"
    )


# Cores do design system (mantém consistência com o resto do app).
_COR_DESTAQUE = "#15803d"   # verde escuro — RF, modelo vencedor
_COR_NEUTRA = "#94a3b8"     # cinza ardósia — demais modelos / persistência
_COR_TEXTO = "#0f172a"

# Resultados oficiais da segunda rodada (pós-Onda 1), extraídos do
# RELATORIO_MODELAGEM.md §3 e §7.1. Hard-coded aqui porque a página Sobre
# não deve depender de model_results.parquet ter sido gerado.
_AUPRC_RANKING = [
    ("Random Forest", 0.397),
    ("LightGBM", 0.372),
    ("EBM", 0.367),
    ("XGBoost", 0.362),
    ("Persistência", 0.347),
    ("Reg. Logística", 0.288),
    ("Climatologia", 0.151),
]
_RECALL_INICIO = [
    ("Dengue (canal)", 0.0, 0.290),
    ("Dengue (inc100)", 0.0, 0.314),
    ("Chikungunya (canal)", 0.0, 0.212),
    ("Zika (canal)", 0.0, 0.354),
]


def _grafico_auprc(titulo_eixo: str) -> go.Figure:
    """Bar horizontal: AUPRC médio por modelo, RF destacado em verde."""
    nomes = [n for n, _ in _AUPRC_RANKING][::-1]   # invertido para RF aparecer no topo
    valores = [v for _, v in _AUPRC_RANKING][::-1]
    cores = [_COR_DESTAQUE if n == "Random Forest" else _COR_NEUTRA for n in nomes]
    fig = go.Figure(go.Bar(
        y=nomes, x=valores, orientation="h",
        marker_color=cores,
        text=[f"{v:.3f}" for v in valores],
        textposition="outside",
        hovertemplate="%{y}: %{x:.3f}<extra></extra>",
    ))
    fig.update_layout(
        height=280,
        margin=dict(l=0, r=40, t=10, b=30),
        xaxis=dict(title=titulo_eixo, range=[0, 0.46], showgrid=True,
                   gridcolor="rgba(15,23,42,0.08)"),
        yaxis=dict(title=""),
        font=dict(family="Geist, system-ui, sans-serif", color=_COR_TEXTO, size=12),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


def _grafico_recall_inicio(label_persist: str, label_rf: str,
                           titulo_eixo: str) -> go.Figure:
    """Barras agrupadas: Persistência (sempre 0%) vs RF, em 4 cenários."""
    cenarios = [c for c, _, _ in _RECALL_INICIO]
    persistencia = [p * 100 for _, p, _ in _RECALL_INICIO]
    rf = [r * 100 for _, _, r in _RECALL_INICIO]
    fig = go.Figure([
        go.Bar(name=label_persist, x=cenarios, y=persistencia,
               marker_color=_COR_NEUTRA,
               text=[f"{v:.0f}%" for v in persistencia], textposition="outside",
               hovertemplate=f"{label_persist}: " "%{y:.1f}%<extra></extra>"),
        go.Bar(name=label_rf, x=cenarios, y=rf,
               marker_color=_COR_DESTAQUE,
               text=[f"{v:.1f}%" for v in rf], textposition="outside",
               hovertemplate=f"{label_rf}: " "%{y:.1f}%<extra></extra>"),
    ])
    fig.update_layout(
        height=320,
        margin=dict(l=0, r=0, t=10, b=30),
        barmode="group",
        yaxis=dict(title=titulo_eixo, range=[0, 45], ticksuffix="%",
                   showgrid=True, gridcolor="rgba(15,23,42,0.08)"),
        xaxis=dict(title=""),
        font=dict(family="Geist, system-ui, sans-serif", color=_COR_TEXTO, size=12),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def _titled_card(titulo: str, texto: str) -> str:
    """Card visual sem badge, só título e corpo. Para grupos temáticos e razões."""
    return (
        '<div style="background:var(--c-surface);border:1px solid var(--c-line);'
        'border-radius:12px;padding:20px;height:100%">'
        f'<div style="font-weight:600;font-size:15px;margin-bottom:10px">{titulo}</div>'
        f'<div style="font-size:13px;color:var(--c-muted);line-height:1.55">{texto}</div>'
        "</div>"
    )


# ============================================================
# 1. Por que esta plataforma existe?
# ============================================================
st.markdown(f"## {t('sobre.intro.secao')}")
st.markdown(t("sobre.intro.motivacao"))
st.markdown(t("sobre.intro.objetivo"))
st.markdown(f"**{t('sobre.intro.para_quem_titulo')}**")
st.markdown(t("sobre.intro.para_quem"))
st.markdown(f"**{t('sobre.intro.ic_titulo')}**")
st.markdown(t("sobre.intro.ic"))
st.markdown(_ESPACO, unsafe_allow_html=True)

# ============================================================
# 2. Como funciona, em 4 passos
# ============================================================
st.markdown(f"## {t('sobre.funcionamento.secao')}")
st.markdown(t("sobre.funcionamento.intro"))
c1, c2, c3, c4 = st.columns(4)
for col, n in zip([c1, c2, c3, c4], ["passo1", "passo2", "passo3", "passo4"]):
    with col:
        st.markdown(
            _numbered_card(
                t(f"sobre.funcionamento.{n}_badge"),
                t(f"sobre.funcionamento.{n}_titulo"),
                t(f"sobre.funcionamento.{n}_texto"),
            ),
            unsafe_allow_html=True,
        )
st.markdown(_ESPACO, unsafe_allow_html=True)

# ============================================================
# 3. De onde vêm os dados
# ============================================================
st.markdown(f"## {t('sobre.coleta.secao')}")
st.markdown(t("sobre.coleta.intro"))

# 5 grupos em duas linhas: 3 + 2
linha1 = st.columns(3)
linha2 = st.columns(3)  # terceira coluna fica vazia para alinhamento
grupos_linha1 = ["grupo_saude", "grupo_clima", "grupo_demo"]
grupos_linha2 = ["grupo_ambiente", "grupo_gestao"]

for col, g in zip(linha1, grupos_linha1):
    with col:
        st.markdown(
            _titled_card(
                t(f"sobre.coleta.{g}_titulo"),
                t(f"sobre.coleta.{g}_texto"),
            ),
            unsafe_allow_html=True,
        )
for col, g in zip(linha2[:2], grupos_linha2):
    with col:
        st.markdown(
            _titled_card(
                t(f"sobre.coleta.{g}_titulo"),
                t(f"sobre.coleta.{g}_texto"),
            ),
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
st.info(t("sobre.coleta.fechamento"))
st.markdown(_ESPACO, unsafe_allow_html=True)

# ============================================================
# 4. Como o computador aprende
# ============================================================
st.markdown(f"## {t('sobre.aprende.secao')}")
st.markdown(t("sobre.aprende.intro"))
st.markdown(f"**{t('sobre.aprende.metodo_titulo')}**")
st.markdown(t("sobre.aprende.metodo_texto"))
st.markdown(f"**{t('sobre.aprende.diagrama_titulo')}**")
st.markdown(t("sobre.aprende.diagrama"))
st.markdown(f"**{t('sobre.aprende.comparacao_titulo')}**")
st.markdown(t("sobre.aprende.comparacao_texto"))
st.markdown(f"**{t('sobre.aprende.metricas_titulo')}**")
st.markdown(t("sobre.aprende.metricas_texto"))

# Gráfico 1: ranking de AUPRC por modelo
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.markdown(f"*{t('sobre.aprende.grafico1_titulo')}*")
st.plotly_chart(
    _grafico_auprc(t("sobre.aprende.grafico1_eixo")),
    use_container_width=True,
    config={"displayModeBar": False},
)
st.caption(t("sobre.aprende.grafico1_legenda"))

# Gráfico 2: recall em INÍCIO de surto (RF vs persistência)
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
st.markdown(f"*{t('sobre.aprende.grafico2_titulo')}*")
st.plotly_chart(
    _grafico_recall_inicio(
        label_persist=t("sobre.aprende.grafico2_legenda_persist"),
        label_rf=t("sobre.aprende.grafico2_legenda_rf"),
        titulo_eixo=t("sobre.aprende.grafico2_eixo"),
    ),
    use_container_width=True,
    config={"displayModeBar": False},
)
st.caption(t("sobre.aprende.grafico2_legenda"))

st.markdown(_ESPACO, unsafe_allow_html=True)

# ============================================================
# 5. Catálogo técnico (escondido em expander)
# ============================================================
st.markdown(f"## {t('sobre.catalogo.secao')}")
n_categorias = catalogo["categoria"].nunique()
st.markdown(t("sobre.catalogo.intro",
              n_features=len(catalogo), n_categorias=n_categorias))

with st.expander(t("sobre.catalogo.expander_label"), expanded=False):
    nan_medio = catalogo["nan_pct"].mean()
    n_quase_completas = int((catalogo["nan_pct"] < 1).sum())
    n_com_buraco = int((catalogo["nan_pct"] >= 10).sum())

    metric_row(
        metric(t("sobre.metricas.total_label"), f"{len(catalogo)}",
               delta=t("sobre.metricas.total_delta", n_categorias=n_categorias)),
        metric(t("sobre.metricas.completas_label"), f"{n_quase_completas}",
               delta=t("sobre.metricas.completas_delta")),
        metric(t("sobre.metricas.lacunas_label"), f"{n_com_buraco}",
               delta=t("sobre.metricas.lacunas_delta")),
        metric(t("sobre.metricas.nan_medio_label"), f"{nan_medio:.1f}%",
               delta=t("sobre.metricas.nan_medio_delta")),
    )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown(section_label(t("sobre.filtros.secao")), unsafe_allow_html=True)
    col_busca, col_cat, col_tipo = st.columns([2, 2, 1])
    with col_busca:
        busca = st.text_input(
            t("sobre.filtros.busca_label"),
            placeholder=t("sobre.filtros.busca_placeholder"),
            help=t("sobre.filtros.busca_help"),
        )
    with col_cat:
        categorias_disp = sorted(catalogo["categoria"].unique())
        cat_sel = st.multiselect(
            t("sobre.filtros.categorias_label"), categorias_disp, default=[],
            help=t("sobre.filtros.categorias_help"),
        )
    with col_tipo:
        tipos_disp = sorted(catalogo["tipo"].unique())
        tipo_sel = st.multiselect(
            t("sobre.filtros.tipo_label"), tipos_disp, default=[],
            help=t("sobre.filtros.tipo_help"),
        )

    df = catalogo.copy()
    if busca:
        mask = (
            df["tecnico"].str.contains(busca, case=False, regex=False)
            | df["humano"].str.contains(busca, case=False, regex=False)
        )
        df = df[mask]
    if cat_sel:
        df = df[df["categoria"].isin(cat_sel)]
    if tipo_sel:
        df = df[df["tipo"].isin(tipo_sel)]

    st.caption(t(
        "sobre.tabela.info_filtro",
        n_filtrado=len(df), n_total=len(catalogo),
        n_categorias=df["categoria"].nunique(),
    ))
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "categoria": st.column_config.TextColumn(t("comum.categoria"), width="medium"),
            "tecnico": st.column_config.TextColumn(t("comum.nome_tecnico"), width="medium"),
            "humano": st.column_config.TextColumn(t("comum.descricao")),
            "tipo": st.column_config.TextColumn(t("comum.tipo"), width="small"),
            "fonte": st.column_config.TextColumn(t("comum.fonte"), width="medium"),
            "nan_pct": st.column_config.NumberColumn(
                t("comum.pct_nan"), format="%.1f%%", width="small",
            ),
            "min": st.column_config.NumberColumn(t("comum.minimo"), format="%.3g", width="small"),
            "media": st.column_config.NumberColumn(t("comum.media"), format="%.3g", width="small"),
            "max": st.column_config.NumberColumn(t("comum.maximo"), format="%.3g", width="small"),
            "extra": st.column_config.TextColumn(t("comum.observacao"), width="medium"),
        },
        height=520,
    )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown(section_label(t("sobre.tabela.secao_distribuicao")), unsafe_allow_html=True)
    resumo = (
        catalogo.groupby("categoria")
        .agg(
            n_features=("tecnico", "count"),
            nan_medio_pct=("nan_pct", "mean"),
            fonte=("fonte", "first"),
        )
        .reset_index()
        .sort_values("n_features", ascending=False)
    )
    resumo["nan_medio_pct"] = resumo["nan_medio_pct"].round(2)
    st.dataframe(
        resumo,
        use_container_width=True,
        hide_index=True,
        column_config={
            "categoria": t("comum.categoria"),
            "n_features": st.column_config.NumberColumn(t("comum.n_features")),
            "nan_medio_pct": st.column_config.NumberColumn(t("comum.pct_nan_medio"), format="%.1f%%"),
            "fonte": t("comum.fonte_primaria"),
        },
    )
    st.caption(t("sobre.tabela.rodape"))

st.markdown(
    '<hr style="border:none;border-top:1px solid var(--c-line);margin:32px 0 12px">',
    unsafe_allow_html=True,
)
