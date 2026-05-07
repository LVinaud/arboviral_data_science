"""
Página: Detalhe por município — predição + justificativa SHAP + histórico.

Permite o gestor entender por que aquele município recebeu (ou não) alerta.
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib.carregar import (
    carregar_features,
    carregar_labels,
    carregar_master,
    carregar_modelo,
    carregar_municipios,
    carregar_predicoes,
)
from lib.predicao import categorizar_risco, justificar_alerta

st.set_page_config(page_title="Município", page_icon="🔍", layout="wide")

st.title("🔍 Detalhe por Município")
st.caption(
    "Selecione um município e uma combinação (doença × definição × modelo) "
    "para ver a predição mais recente, justificativa SHAP e histórico de casos."
)

# --- Sidebar: seleção ---
municipios = carregar_municipios()
preds = carregar_predicoes()
master = carregar_master()
labels = carregar_labels()

with st.sidebar:
    st.header("Seleção")
    nome_sel = st.selectbox(
        "Município",
        sorted(municipios["nome_municipio"]),
        index=sorted(municipios["nome_municipio"].tolist()).index("São Paulo"),
    )
    cod = int(municipios[municipios["nome_municipio"] == nome_sel]["cod_ibge"].iloc[0])

    doenca = st.selectbox("Doença", sorted(preds["doenca"].unique()), index=0)
    definicao = st.selectbox(
        "Definição de surto",
        sorted(preds[preds["doenca"] == doenca]["definicao"].unique()),
        index=0,
    )
    modelos_disponiveis = sorted(preds[
        (preds["doenca"] == doenca) & (preds["definicao"] == definicao)
    ]["modelo"].unique())
    modelos_ml = [m for m in modelos_disponiveis if m not in ("persistencia", "climatologia")]
    modelo_default = "rf" if "rf" in modelos_ml else (modelos_ml[0] if modelos_ml else modelos_disponiveis[0])
    modelo = st.selectbox(
        "Modelo",
        modelos_disponiveis,
        index=modelos_disponiveis.index(modelo_default),
    )
    fold = st.selectbox(
        "Ano de teste",
        sorted(preds["fold_ano_teste"].unique()),
        index=len(preds["fold_ano_teste"].unique()) - 1,
    )

# --- Resumo do município ---
st.subheader(f"📍 {nome_sel}")
mun_info = municipios[municipios["cod_ibge"] == cod].iloc[0]
ultimo_master = master[master["cod_ibge"] == cod].sort_values(["ano", "mes"]).iloc[-1]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Código IBGE", str(cod))
col2.metric("População (mais recente)", f"{int(ultimo_master['populacao_estimada']):,}")
col3.metric("Estação INMET", mun_info["estacao_inmet"])
col4.metric("Distância à estação", f"{mun_info['dist_estacao_km']:.1f} km")

# --- Predição mais recente para este município no fold escolhido ---
st.divider()
st.subheader(f"🔮 Predições — {doenca.replace('_', ' ').title()} ({definicao}) · Modelo: {modelo} · Fold {fold}")

preds_mun = preds[
    (preds["cod_ibge"] == cod) &
    (preds["doenca"] == doenca) &
    (preds["definicao"] == definicao) &
    (preds["modelo"] == modelo) &
    (preds["fold_ano_teste"] == fold)
].sort_values(["ano", "mes"]).copy()

if preds_mun.empty:
    st.warning("Nenhuma predição encontrada para essa combinação.")
else:
    preds_mun["data"] = pd.to_datetime(
        preds_mun["ano"].astype(str) + "-" + preds_mun["mes"].astype(str).str.zfill(2)
    )
    preds_mun["categoria"], preds_mun["emoji"] = zip(
        *preds_mun["prob_predita"].apply(categorizar_risco)
    )

    # Gráfico de probabilidades ao longo do ano
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=preds_mun["data"],
        y=preds_mun["prob_predita"],
        marker_color=[
            "#dc2626" if p >= 0.8 else
            "#ea580c" if p >= 0.5 else
            "#facc15" if p >= 0.2 else
            "#16a34a"
            for p in preds_mun["prob_predita"]
        ],
        name="Probabilidade prevista",
        text=[f"{p:.0%}" for p in preds_mun["prob_predita"]],
        textposition="outside",
    ))
    # Marca onde de fato houve surto
    surto_real = preds_mun[preds_mun["y_true"] == 1]
    if not surto_real.empty:
        fig.add_trace(go.Scatter(
            x=surto_real["data"],
            y=[1.05] * len(surto_real),
            mode="markers",
            marker=dict(size=14, color="black", symbol="star"),
            name="Surto real ⭐",
        ))
    fig.update_layout(
        yaxis=dict(range=[0, 1.15], title="Probabilidade", tickformat=".0%"),
        xaxis_title="Mês predito",
        height=350,
        showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabela detalhada
    with st.expander("Ver detalhamento mensal"):
        cols = ["data", "emoji", "categoria", "prob_predita", "y_true", "surto_atual"]
        df_show = preds_mun[cols].copy()
        df_show["data"] = df_show["data"].dt.strftime("%Y-%m")
        st.dataframe(df_show, use_container_width=True, hide_index=True)

# --- Histórico de casos ---
st.divider()
st.subheader("📈 Histórico de casos")
casos_col = f"{doenca}_casos"
if casos_col in master.columns:
    hist = master[master["cod_ibge"] == cod][["ano", "mes", casos_col]].copy()
    hist["data"] = pd.to_datetime(hist["ano"].astype(str) + "-" + hist["mes"].astype(str).str.zfill(2))
    hist[casos_col] = hist[casos_col].fillna(0)

    fig_h = px.line(
        hist, x="data", y=casos_col,
        title=f"Casos mensais de {doenca.replace('_', ' ')} em {nome_sel}",
        labels={"data": "Mês", casos_col: "Casos notificados"},
    )
    fig_h.update_layout(height=300)
    st.plotly_chart(fig_h, use_container_width=True)

# --- Justificativa SHAP do alerta mais alto ---
st.divider()
st.subheader("🧠 Por que esse modelo deu alerta?")
st.caption(
    "Para uma predição de alta probabilidade, mostramos as 5 features que "
    "mais contribuíram positivamente (impulsionaram o alerta) ou negativamente."
)

if modelo not in ("rf", "xgb", "lgbm"):
    st.info(
        f"Justificativa SHAP por predição disponível apenas para modelos baseados em árvore "
        f"(rf, xgb, lgbm). Modelo selecionado: **{modelo}**."
    )
elif preds_mun.empty:
    st.info("Sem predição para gerar SHAP.")
else:
    with st.spinner("Carregando modelo e computando SHAP..."):
        mdl = carregar_modelo(doenca, definicao, modelo, fold)
        if mdl is None:
            st.error(
                f"Modelo `{doenca}_{definicao}_{modelo}_{fold}.joblib` não encontrado. "
                "Rode `python -m arboviral.train` para gerá-lo."
            )
        else:
            features = carregar_features()
            # Pega a linha de maior probabilidade nesse município/fold
            mes_pico = preds_mun.loc[preds_mun["prob_predita"].idxmax()]
            cod_alvo = int(mes_pico["cod_ibge"])
            ano_alvo = int(mes_pico["ano"])
            mes_alvo = int(mes_pico["mes"])

            X_amostra = features[
                (features["cod_ibge"] == cod_alvo) &
                (features["ano"] == ano_alvo) &
                (features["mes"] == mes_alvo)
            ].copy()

            # Reproduzir colunas auxiliares que o pipeline de treino adiciona
            # (vide arboviral.evaluation.splits.adicionar_target_year):
            #   target_year = ano + (mes == 12) ; target_month = (mes % 12) + 1
            X_amostra["target_year"] = X_amostra["ano"] + (X_amostra["mes"] == 12).astype(int)
            X_amostra["target_month"] = (X_amostra["mes"] % 12) + 1
            X_amostra = X_amostra.drop(columns=["cod_ibge", "ano", "mes"])

            # Alinhar com colunas esperadas pelo modelo. Se o modelo for um Pipeline,
            # consultar o passo final ("clf") cujo feature_names_in_ é o que importa.
            cols_esperadas = None
            if hasattr(mdl, "named_steps") and "clf" in mdl.named_steps:
                step = mdl.named_steps["clf"]
                if hasattr(step, "feature_names_in_"):
                    cols_esperadas = list(step.feature_names_in_)
            if cols_esperadas is None and hasattr(mdl, "feature_names_in_"):
                cols_esperadas = list(mdl.feature_names_in_)
            if cols_esperadas is None:
                cols_esperadas = X_amostra.columns.tolist()

            # Adiciona colunas faltantes como NaN (imputer no pipeline cuida disso)
            for c in cols_esperadas:
                if c not in X_amostra.columns:
                    X_amostra[c] = float("nan")
            X_amostra = X_amostra[cols_esperadas]

            try:
                top = justificar_alerta(mdl, X_amostra, top=8)
                st.markdown(
                    f"**Predição em foco**: {nome_sel}, "
                    f"{ano_alvo}-{mes_alvo:02d} → "
                    f"probabilidade de surto = **{mes_pico['prob_predita']:.1%}**"
                )
                # Render SHAP como barras
                fig_shap = go.Figure(go.Bar(
                    x=top["shap"],
                    y=top["feature"],
                    orientation="h",
                    marker_color=["#dc2626" if v > 0 else "#16a34a" for v in top["shap"]],
                    text=[f"{v:+.3f}" for v in top["shap"]],
                    textposition="outside",
                ))
                fig_shap.update_layout(
                    xaxis_title="Contribuição SHAP (impacto na probabilidade)",
                    yaxis=dict(autorange="reversed"),
                    height=400,
                )
                st.plotly_chart(fig_shap, use_container_width=True)

                with st.expander("Ver tabela completa com valores observados"):
                    st.dataframe(top, hide_index=True, use_container_width=True)

                st.caption(
                    "🔴 Vermelho = feature **aumentou** a probabilidade de surto · "
                    "🟢 Verde = feature **diminuiu**"
                )
            except Exception as e:
                st.error(f"Erro ao computar SHAP: {e}")
