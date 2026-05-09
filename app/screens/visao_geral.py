"""Tela: Visão geral (landing) — hero + métricas + tabela de modelos + nav cards."""
import pandas as pd
import streamlit as st

from i18n import t
from lib.carregar import (
    caminho_disponivel,
    carregar_master,
    carregar_municipios,
    listar_modelos_disponiveis,
)
from lib.labels import nome_definicao, nome_doenca, nome_modelo
from lib.tema import hero, metric, metric_row, nav_card, section_label

if not caminho_disponivel():
    st.error(t("erro.dados_nao_encontrados"))
    st.stop()

master = carregar_master()
municipios = carregar_municipios()
modelos = listar_modelos_disponiveis()
ano_min, ano_max = int(master["ano"].min()), int(master["ano"].max())

hero(
    eyebrow=t("home.hero.eyebrow"),
    titulo=t("home.hero.titulo"),
    lead=t("home.hero.lead"),
    meta_items=[
        (t("home.hero.meta_aluno"), t("home.hero.meta_aluno_valor")),
        (t("home.hero.meta_orientador"), t("home.hero.meta_orientador_valor")),
        (t("home.hero.meta_periodo"), f"{ano_min} — {ano_max}"),
    ],
)

metric_row(
    metric(t("home.metricas.municipios_label"),
           f"{municipios.shape[0]:,}",
           t("home.metricas.municipios_unidade")),
    metric(t("home.metricas.periodo_label"),
           value=f"{ano_max - ano_min + 1}",
           unit=t("home.metricas.periodo_unidade"),
           delta=t("home.metricas.periodo_delta", ano_min=ano_min, ano_max=ano_max)),
    metric(t("home.metricas.variaveis_label"),
           value=f"{len(master.columns)}",
           delta=t("home.metricas.variaveis_delta")),
    metric(t("home.metricas.doencas_label"), value="4",
           delta=t("home.metricas.doencas_delta")),
)

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

st.markdown(section_label(t("home.modelos.secao")), unsafe_allow_html=True)
st.caption(t("home.modelos.caption"))

if modelos:
    df_mod = pd.DataFrame(modelos)
    resumo = (
        df_mod.groupby(["doenca", "definicao", "modelo"])
        .size()
        .reset_index(name="folds")
        .sort_values(["doenca", "definicao", "modelo"])
    )
    # Rotular colunas com nomes humanos para a tabela
    resumo["doenca"] = resumo["doenca"].map(nome_doenca)
    resumo["definicao"] = resumo["definicao"].map(nome_definicao)
    resumo["modelo"] = resumo["modelo"].map(nome_modelo)
    st.dataframe(
        resumo,
        use_container_width=True,
        hide_index=True,
        column_config={
            "doenca": t("home.modelos.col_doenca"),
            "definicao": t("home.modelos.col_definicao"),
            "modelo": t("home.modelos.col_modelo"),
            "folds": t("home.modelos.col_folds"),
        },
    )
    st.caption(t("home.modelos.rodape_total", n_modelos=len(df_mod)))
else:
    st.warning(t("erro.sem_modelos"))

st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

st.markdown(section_label(t("home.navegacao.secao")), unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(nav_card(
        "A", t("home.navegacao.alertas_titulo"),
        t("home.navegacao.alertas_desc"),
    ), unsafe_allow_html=True)
with c2:
    st.markdown(nav_card(
        "M", t("home.navegacao.municipio_titulo"),
        t("home.navegacao.municipio_desc"),
    ), unsafe_allow_html=True)
with c3:
    st.markdown(nav_card(
        "C", t("home.navegacao.comparativo_titulo"),
        t("home.navegacao.comparativo_desc"),
    ), unsafe_allow_html=True)

st.markdown(
    '<hr style="border:none;border-top:1px solid var(--c-line);margin:32px 0 16px">',
    unsafe_allow_html=True,
)
st.markdown(
    '<div style="display:flex;justify-content:space-between;font-size:12px;color:var(--c-muted)">'
    f'<span>{t("home.rodape_esq")}</span>'
    f'<span>{t("home.rodape_dir")}</span>'
    '</div>',
    unsafe_allow_html=True,
)
