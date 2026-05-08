"""Tela: Visão geral (landing) — hero + métricas + tabela de modelos + nav cards."""
import pandas as pd
import streamlit as st

from lib.carregar import (
    caminho_disponivel,
    carregar_master,
    carregar_municipios,
    listar_modelos_disponiveis,
)
from lib.labels import nome_definicao, nome_doenca, nome_modelo
from lib.tema import hero, metric, metric_row, nav_card, section_label

if not caminho_disponivel():
    st.error(
        "Arquivos de dados não encontrados. Rode primeiro o pipeline:\n\n"
        "```bash\n"
        "python -m arboviral.transform.build_master\n"
        "python -m arboviral.labels.build_labels\n"
        "python -m arboviral.features.build_features\n"
        "python -m arboviral.train\n"
        "```"
    )
    st.stop()

master = carregar_master()
municipios = carregar_municipios()
modelos = listar_modelos_disponiveis()
ano_min, ano_max = int(master["ano"].min()), int(master["ano"].max())

hero(
    eyebrow="ICMC · USP São Carlos · Iniciação Científica",
    titulo="Sistema operacional de alerta precoce para arboviroses no estado de São Paulo",
    lead=(
        "A cada mês, modelos de aprendizado de máquina explicáveis estimam a "
        "probabilidade de surto de dengue, zika, chikungunya e febre amarela "
        "em cada um dos 645 municípios paulistas — e justificam cada alerta "
        "com os fatores que mais contribuíram."
    ),
    meta_items=[
        ("Aluno", "Lázaro Vinaud"),
        ("Orientador", "Prof. André C. P. L. F. de Carvalho"),
        ("Período de dados", f"{ano_min} — {ano_max}"),
    ],
)

metric_row(
    metric("Municípios monitorados", f"{municipios.shape[0]:,}", " / SP"),
    metric("Período histórico",
           value=f"{ano_max - ano_min + 1}",
           unit=" anos",
           delta=f"Janeiro/{ano_min} — Dezembro/{ano_max}"),
    metric("Variáveis no master",
           value=f"{len(master.columns)}",
           delta="Climáticas · epidemiológicas · ambientais · sanitárias"),
    metric("Doenças cobertas", value="4",
           delta="Dengue · Zika · Chikungunya · Febre amarela"),
)

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

st.markdown(section_label("Modelos disponíveis"), unsafe_allow_html=True)
st.caption(
    "Modelos serializados em `data/processed/models/` por (doença × definição × fold). "
    "As páginas usam o modelo do fold mais recente (alvo 2024) como predição mais atualizada."
)

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
            "doenca": "Doença",
            "definicao": "Definição de surto",
            "modelo": "Modelo",
            "folds": "Anos de teste treinados",
        },
    )
    st.caption(
        f"{len(df_mod)} modelos no total · 7 algoritmos (persistência, climatologia, "
        "logreg, EBM, RF, XGBoost, LightGBM) × 4 definições de surto × 3 folds temporais "
        "(2022, 2023, 2024)."
    )
else:
    st.warning("Nenhum modelo treinado encontrado. Rode `python -m arboviral.train`.")

st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

st.markdown(section_label("Como navegar pela plataforma"), unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(nav_card(
        "A", "Alertas mensais",
        "Tabela ranqueada de municípios em risco para o mês corrente, "
        "com filtros por doença, definição de surto e modelo.",
    ), unsafe_allow_html=True)
with c2:
    st.markdown(nav_card(
        "M", "Detalhe do município",
        "Predição mensal + histórico + justificativa SHAP "
        "(quais variáveis empurraram o risco para cima ou para baixo).",
    ), unsafe_allow_html=True)
with c3:
    st.markdown(nav_card(
        "C", "Comparativo entre doenças",
        "Heatmap 4 doenças × 12 meses + série histórica para entender "
        "sazonalidade e cruzamento de transmissão.",
    ), unsafe_allow_html=True)

st.markdown(
    '<hr style="border:none;border-top:1px solid var(--c-line);margin:32px 0 16px">',
    unsafe_allow_html=True,
)
st.markdown(
    '<div style="display:flex;justify-content:space-between;font-size:12px;color:var(--c-muted)">'
    '<span>Plataforma de Alerta Precoce · ICMC USP · 2026</span>'
    '<span>Integração planejada · plataforma inteli.gente / MCTI</span>'
    '</div>',
    unsafe_allow_html=True,
)
