"""
Página: Catálogo de variáveis — todas as features que entram no modelo.

Lista exaustivamente as 140 colunas de features.parquet com nome técnico,
nome humano, categoria temática, fonte de origem, tipo, taxa de NaN e
estatísticas básicas. Permite busca por nome e filtro por categoria.

Útil para:
  - auditoria (revisor confere quais features o modelo viu de fato)
  - apresentação ao orientador (panorama do dataset)
  - depuração (encontrar uma feature específica e ver sua distribuição)

i18n: o cache de `_construir_catalogo` recebe `lang` como argumento — quando
o usuário troca de idioma, o catálogo inteiro é re-humanizado (categorias,
fontes, tipos, descrição de cada feature). Sem o argumento `lang`, o cache
preservaria os labels do idioma antigo.
"""
import pandas as pd
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
            tipo = t("variaveis.tipos.booleana")
            mn, mx, media = None, None, None
            n_true = int(s.eq(True).sum())
            n_false = (n_total - n_nan) - n_true
            extra = (
                f"{n_true:,} {t('comum.verdadeiros')} / "
                f"{n_false:,} {t('comum.falsos')}"
            ).replace(",", ".")
        elif pd.api.types.is_numeric_dtype(s):
            tipo = t("variaveis.tipos.numerica")
            valores = s.dropna()
            mn = float(valores.min()) if not valores.empty else None
            mx = float(valores.max()) if not valores.empty else None
            media = float(valores.mean()) if not valores.empty else None
            extra = ""
        else:
            tipo = t("variaveis.tipos.categorica")
            mn, mx, media = None, None, None
            unicos = s.dropna().astype(str).unique()
            extra = ", ".join(sorted(unicos)[:5]) + (" …" if len(unicos) > 5 else "")

        cat_chave, fonte_chave = "outras", "indef"
        for chave_cat, prefixos, chave_fonte in _CATEGORIAS:
            if any(c.startswith(p) or c == p for p in prefixos):
                cat_chave, fonte_chave = chave_cat, chave_fonte
                break

        rows.append({
            "categoria": t(f"variaveis.categorias.{cat_chave}"),
            "tecnico": c,
            "humano": humanizar_feature(c),
            "tipo": tipo,
            "fonte": t(f"variaveis.fontes.{fonte_chave}"),
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
    titulo=t("variaveis.titulo"),
    descricao=t("variaveis.descricao", n_features=len(catalogo)),
    crumbs=t("variaveis.crumbs"),
)

# --- Métricas no topo ---
n_categorias = catalogo["categoria"].nunique()
nan_medio = catalogo["nan_pct"].mean()
n_quase_completas = int((catalogo["nan_pct"] < 1).sum())
n_com_buraco = int((catalogo["nan_pct"] >= 10).sum())

metric_row(
    metric(t("variaveis.metricas.total_label"), f"{len(catalogo)}",
           delta=t("variaveis.metricas.total_delta", n_categorias=n_categorias)),
    metric(t("variaveis.metricas.completas_label"), f"{n_quase_completas}",
           delta=t("variaveis.metricas.completas_delta")),
    metric(t("variaveis.metricas.lacunas_label"), f"{n_com_buraco}",
           delta=t("variaveis.metricas.lacunas_delta")),
    metric(t("variaveis.metricas.nan_medio_label"), f"{nan_medio:.1f}%",
           delta=t("variaveis.metricas.nan_medio_delta")),
)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# --- Filtros ---
st.markdown(section_label(t("variaveis.filtros.secao")), unsafe_allow_html=True)
col_busca, col_cat, col_tipo = st.columns([2, 2, 1])

with col_busca:
    busca = st.text_input(
        t("variaveis.filtros.busca_label"),
        placeholder=t("variaveis.filtros.busca_placeholder"),
        help=t("variaveis.filtros.busca_help"),
    )

with col_cat:
    categorias_disp = sorted(catalogo["categoria"].unique())
    cat_sel = st.multiselect(
        t("variaveis.filtros.categorias_label"), categorias_disp, default=[],
        help=t("variaveis.filtros.categorias_help"),
    )

with col_tipo:
    tipos_disp = sorted(catalogo["tipo"].unique())
    tipo_sel = st.multiselect(
        t("variaveis.filtros.tipo_label"), tipos_disp, default=[],
        help=t("variaveis.filtros.tipo_help"),
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
st.caption(t(
    "variaveis.tabela.info_filtro",
    n_filtrado=len(df), n_total=len(catalogo),
    n_categorias=df["categoria"].nunique(),
))

# --- Tabela ---
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
    height=620,
)

# --- Distribuição por categoria ---
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
st.markdown(section_label(t("variaveis.tabela.secao_distribuicao")), unsafe_allow_html=True)
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

st.markdown(
    '<hr style="border:none;border-top:1px solid var(--c-line);margin:24px 0 12px">',
    unsafe_allow_html=True,
)
st.caption(t("variaveis.tabela.rodape"))
