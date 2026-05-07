"""
Plataforma de Alerta Precoce de Arboviroses — entry point Streamlit.

Branch experimental/platform-app: interface DEPENDE do pacote `arboviral`,
mas o pacote NÃO depende deste app. Verificação: nenhum arquivo em
src/arboviral/ importa de app/.

Uso:
    streamlit run app/app.py

Páginas (autodescobertas em app/pages/):
    1_Alertas        Lista de municípios em maior risco previsto
    2_Municipio      Detalhe + justificativa SHAP por município
    3_Mapa           Mapa de SP colorido por nível de risco
    4_Comparativo    4 doenças lado a lado para um município
"""
import streamlit as st

from lib.carregar import (
    caminho_disponivel,
    carregar_master,
    carregar_municipios,
    carregar_predicoes,
    listar_modelos_disponiveis,
)

st.set_page_config(
    page_title="Alerta Arboviroses SP",
    page_icon="🦟",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🦟 Plataforma de Alerta de Arboviroses — São Paulo")
st.caption(
    "Iniciação Científica · Lázaro Vinaud · ICMC-USP · "
    "Predição mensal de surtos de dengue, zika, chikungunya e febre amarela"
)

# Verificação de pré-requisitos
if not caminho_disponivel():
    st.error(
        "Arquivos de dados não encontrados. Rode primeiro o pipeline de modelagem:\n\n"
        "```bash\n"
        "python -m arboviral.transform.build_master\n"
        "python -m arboviral.labels.build_labels\n"
        "python -m arboviral.features.build_features\n"
        "python -m arboviral.train\n"
        "```"
    )
    st.stop()

st.markdown(
    """
## Sobre a plataforma

Sistema de **alerta precoce** baseado em aprendizado de máquina explicável.
Para cada um dos **645 municípios paulistas**, o sistema prediz mensalmente
a probabilidade de surto de arbovirose no mês seguinte e justifica cada alerta
mostrando os fatores de maior contribuição.

### Como navegar

- **🚨 Alertas** — lista priorizada dos municípios em maior risco previsto
- **🗺️ Mapa** — visão geográfica com cores por nível de risco
- **🔍 Município** — detalhe individual: predição + razões + histórico
- **📊 Comparativo** — 4 doenças lado a lado para um município escolhido

### Como o modelo funciona

A cada mês, o sistema recebe **117 variáveis** sobre cada município:
casos passados das 4 arboviroses (lags 1, 2, 3, 6 e 12 meses), clima
(temperatura, precipitação, umidade), indicadores socioeconômicos
(IDH-M, GINI, PIB per capita, CAPAG), saneamento (SINISA), gestão municipal
(IBGE MUNIC) e habitação (favelas, aglomerados subnormais).

Modelos comparados: Random Forest, XGBoost, LightGBM, EBM (todos com
explicabilidade SHAP), além de baselines triviais para referência.
    """
)

# Estatísticas rápidas
master = carregar_master()
municipios = carregar_municipios()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Municípios cobertos", f"{municipios.shape[0]:,}")
col2.metric("Período", f"{int(master['ano'].min())}-{int(master['ano'].max())}")
col3.metric("Variáveis no dataset", f"{len(master.columns)}")
col4.metric("Doenças monitoradas", "4")

# Modelos disponíveis
st.divider()
st.subheader("Modelos disponíveis")
modelos = listar_modelos_disponiveis()
if modelos:
    import pandas as pd
    df_mod = pd.DataFrame(modelos)
    resumo = (
        df_mod.groupby(["doenca", "definicao", "modelo"])
        .size()
        .reset_index(name="folds")
        .sort_values(["doenca", "definicao", "modelo"])
    )
    st.dataframe(
        resumo,
        use_container_width=True,
        hide_index=True,
        column_config={
            "doenca": "Doença",
            "definicao": "Definição de surto",
            "modelo": "Modelo",
            "folds": "# Folds treinados",
        },
    )
    st.caption(
        f"{len(df_mod)} modelos serializados disponíveis em `data/processed/models/`. "
        "As páginas usam o modelo do fold mais recente (2024) como predição mais atualizada."
    )
else:
    st.warning(
        "Nenhum modelo treinado encontrado em `data/processed/models/`. "
        "Rode `python -m arboviral.train` para gerá-los."
    )

st.divider()
st.caption(
    "Repositório: [github.com/LVinaud/arboviral_data_science](https://github.com/LVinaud/arboviral_data_science) · "
    "Branch: `experimental/platform-app`"
)
