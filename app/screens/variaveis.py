"""
Página: Catálogo de variáveis — todas as features que entram no modelo.

Lista exaustivamente as 140 colunas de features.parquet com nome técnico,
nome humano, categoria temática, fonte de origem, tipo, taxa de NaN e
estatísticas básicas. Permite busca por nome e filtro por categoria.

Útil para:
  - auditoria (revisor confere quais features o modelo viu de fato)
  - apresentação ao orientador (panorama do dataset)
  - depuração (encontrar uma feature específica e ver sua distribuição)
"""
import pandas as pd
import streamlit as st

from lib.carregar import carregar_features
from lib.labels import humanizar_feature
from lib.tema import (
    metric,
    metric_row,
    page_header,
    section_label,
)

# Categoria → (label, prefixos que casam, fonte primária)
# Ordem importa: a primeira que casa ganha. Mais específicas primeiro.
_CATEGORIAS: list[tuple[str, list[str], str]] = [
    ("Epidemiológicas — Dengue", ["dengue_"], "SINAN / DATASUS"),
    ("Epidemiológicas — Zika", ["zika_"], "SINAN / DATASUS"),
    ("Epidemiológicas — Chikungunya", ["chikungunya_"], "SINAN / DATASUS"),
    ("Epidemiológicas — Febre amarela", ["febre_amarela_", "febre_"], "SVS / Ministério da Saúde"),
    ("Climáticas", ["temp_", "precip_", "umid_", "pressao_", "vento_"], "NASA POWER (MERRA-2)"),
    ("Sazonalidade", ["mes_sin", "mes_cos"], "engenharia de features (calendário)"),
    ("Geolocalização", ["lat", "lon", "dist_estacao_km"], "lookup IBGE / INMET"),
    ("Demografia / Economia", ["populacao_estimada", "pib_", "gini", "idhm"], "IBGE SIDRA / Atlas PNUD"),
    ("Densidade territorial", ["area_km2", "densidade_"], "IBGE — áreas territoriais"),
    ("Cobertura terrestre", ["pct_"], "MapBiomas Coleção 10.1"),
    ("Saúde pública", ["leitos_", "mortalidade_"], "DATASUS — CNES + SIM"),
    ("Cobertura ESF / APS", ["esf_"], "e-Gestor / Ministério da Saúde"),
    ("Saneamento", ["iag", "ies"], "SINISA"),
    ("Vacinação", ["cob_vac_"], "PNI / DATASUS"),
    ("Vigilância municipal (MUNIC)", ["msau"], "IBGE MUNIC 2018"),
    ("Desastres / risco ambiental", ["mgrd", "mmam"], "IBGE MUNIC 2020"),
    ("Habitação / favelas", ["num_aglom_", "pop_aglom_", "num_favelas", "pop_favelas"], "IBGE — Censos 2010 / 2022"),
    ("CAPAG", ["capag_"], "Tesouro Nacional"),
    ("Metadata de predição", ["target_"], "engenharia de features (split)"),
]

_CHAVES = {"cod_ibge", "ano", "mes"}


@st.cache_data(show_spinner="Catalogando variáveis...")
def _construir_catalogo() -> pd.DataFrame:
    """Itera sobre todas as colunas de features.parquet e monta o catálogo."""
    features = carregar_features()
    cols = [c for c in features.columns if c not in _CHAVES]

    rows: list[dict] = []
    for c in cols:
        s = features[c]
        n_total = len(s)
        n_nan = int(s.isna().sum())
        nan_pct = (n_nan / n_total * 100) if n_total else 0.0

        if pd.api.types.is_bool_dtype(s):
            tipo = "booleana"
            mn, mx, media = None, None, None
            extra = f"{int(s.sum())} verdadeiros / {n_total - n_nan - int(s.sum())} falsos"
        elif pd.api.types.is_numeric_dtype(s):
            tipo = "numérica"
            valores = s.dropna()
            mn = float(valores.min()) if not valores.empty else None
            mx = float(valores.max()) if not valores.empty else None
            media = float(valores.mean()) if not valores.empty else None
            extra = ""
        else:
            tipo = "categórica"
            mn, mx, media = None, None, None
            unicos = s.dropna().astype(str).unique()
            extra = ", ".join(sorted(unicos)[:5]) + (" …" if len(unicos) > 5 else "")

        cat_nome, fonte = "Outras", "—"
        for nome, prefixos, origem in _CATEGORIAS:
            if any(c.startswith(p) or c == p for p in prefixos):
                cat_nome, fonte = nome, origem
                break

        rows.append({
            "categoria": cat_nome,
            "tecnico": c,
            "humano": humanizar_feature(c),
            "tipo": tipo,
            "fonte": fonte,
            "nan_pct": round(nan_pct, 2),
            "min": mn,
            "media": media,
            "max": mx,
            "extra": extra,
        })

    return pd.DataFrame(rows)


catalogo = _construir_catalogo()

# --- Header ---
page_header(
    titulo="Catálogo de variáveis",
    descricao=(
        f"Todas as **{len(catalogo)} features** que entram nos modelos, com nome técnico, "
        "descrição em português, fonte de origem, tipo e estatísticas. "
        "Útil para auditoria do que o modelo realmente vê e para checar lacunas (NaN%)."
    ),
    crumbs="PLATAFORMA / VARIÁVEIS",
)

# --- Métricas no topo ---
n_categorias = catalogo["categoria"].nunique()
nan_medio = catalogo["nan_pct"].mean()
n_quase_completas = int((catalogo["nan_pct"] < 1).sum())
n_com_buraco = int((catalogo["nan_pct"] >= 10).sum())

metric_row(
    metric("Features totais", f"{len(catalogo)}",
           delta=f"em {n_categorias} categorias temáticas"),
    metric("Quase completas", f"{n_quase_completas}",
           delta="< 1% de NaN"),
    metric("Com lacunas relevantes", f"{n_com_buraco}",
           delta="≥ 10% de NaN — atenção"),
    metric("NaN médio", f"{nan_medio:.1f}%",
           delta="média sobre todas as features"),
)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# --- Filtros ---
st.markdown(section_label("Filtros"), unsafe_allow_html=True)
col_busca, col_cat, col_tipo = st.columns([2, 2, 1])

with col_busca:
    busca = st.text_input(
        "Buscar (nome técnico ou descrição)",
        placeholder="ex.: temp, dengue_lag, esf, vigilância…",
        help="Busca substring case-insensitive em ambos os nomes.",
    )

with col_cat:
    categorias_disp = sorted(catalogo["categoria"].unique())
    cat_sel = st.multiselect(
        "Categorias", categorias_disp, default=[],
        help="Vazio = todas. Selecione uma ou mais para filtrar.",
    )

with col_tipo:
    tipos_disp = sorted(catalogo["tipo"].unique())
    tipo_sel = st.multiselect(
        "Tipo", tipos_disp, default=[],
        help="Vazio = todos.",
    )

# --- Aplicar filtros ---
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

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.caption(
    f"Mostrando **{len(df)} de {len(catalogo)}** features "
    f"(em {df['categoria'].nunique()} categorias)."
)

# --- Tabela ---
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "categoria": st.column_config.TextColumn("Categoria", width="medium"),
        "tecnico": st.column_config.TextColumn("Nome técnico", width="medium"),
        "humano": st.column_config.TextColumn("Descrição"),
        "tipo": st.column_config.TextColumn("Tipo", width="small"),
        "fonte": st.column_config.TextColumn("Fonte", width="medium"),
        "nan_pct": st.column_config.NumberColumn(
            "% NaN", format="%.1f%%", width="small",
        ),
        "min": st.column_config.NumberColumn("Mínimo", format="%.3g", width="small"),
        "media": st.column_config.NumberColumn("Média", format="%.3g", width="small"),
        "max": st.column_config.NumberColumn("Máximo", format="%.3g", width="small"),
        "extra": st.column_config.TextColumn("Observação", width="medium"),
    },
    height=620,
)

# --- Distribuição por categoria ---
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
st.markdown(section_label("Distribuição por categoria"), unsafe_allow_html=True)
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
        "categoria": "Categoria",
        "n_features": st.column_config.NumberColumn("Nº de features"),
        "nan_medio_pct": st.column_config.NumberColumn("% NaN médio", format="%.1f%%"),
        "fonte": "Fonte primária",
    },
)

st.markdown(
    '<hr style="border:none;border-top:1px solid var(--c-line);margin:24px 0 12px">',
    unsafe_allow_html=True,
)
st.caption(
    "As colunas `cod_ibge`, `ano` e `mes` não aparecem aqui — são chaves de "
    "identificação, não features de entrada do modelo. As colunas `target_year` "
    "e `target_month` são derivadas no `train.py` para o split temporal e "
    "também entram como features (sazonalidade do mês predito)."
)
