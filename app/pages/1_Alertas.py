"""
Página: Lista de alertas — municípios em maior risco previsto.

Usa as predições já calculadas (predictions.parquet) para mostrar onde o
sistema teria emitido alerta. Para o "agora real" da plataforma em produção,
seria substituído por uma rotina mensal que carrega os modelos e prediz
com features atualizadas — mas a infraestrutura é a mesma.
"""
import pandas as pd
import streamlit as st

from app.lib.carregar import carregar_municipios, carregar_predicoes
from app.lib.predicao import categorizar_risco

st.set_page_config(page_title="Alertas", page_icon="🚨", layout="wide")

st.title("🚨 Alertas Ativos")
st.caption(
    "Lista priorizada de municípios em maior risco previsto. "
    "Cada linha representa uma predição feita pelo modelo: "
    "*município X teve probabilidade Y de surto no mês seguinte ao mês exibido*."
)

preds = carregar_predicoes()
municipios = carregar_municipios()

# --- Sidebar: filtros ---
with st.sidebar:
    st.header("Filtros")

    doencas_disponiveis = sorted(preds["doenca"].unique())
    doenca = st.selectbox("Doença", doencas_disponiveis, index=0)

    definicoes_disponiveis = sorted(preds[preds["doenca"] == doenca]["definicao"].unique())
    definicao = st.selectbox("Definição de surto", definicoes_disponiveis, index=0,
                             help="Canal endêmico = método oficial Min. Saúde · "
                                  "z-score = desvio do baseline · "
                                  "inc100/inc300 = limiar bruto de incidência por 100k hab")

    modelos_disponiveis = sorted(preds[
        (preds["doenca"] == doenca) & (preds["definicao"] == definicao)
    ]["modelo"].unique())
    modelos_ml = [m for m in modelos_disponiveis if m not in ("persistencia", "climatologia")]
    modelo_default = modelos_ml[0] if modelos_ml else modelos_disponiveis[0]
    modelo = st.selectbox("Modelo", modelos_disponiveis,
                          index=modelos_disponiveis.index(modelo_default))

    folds = sorted(preds["fold_ano_teste"].unique())
    fold = st.selectbox("Ano de teste (fold)", folds, index=len(folds) - 1,
                        help="Cada fold é uma rodada de validação temporal")

    risco_min = st.slider("Probabilidade mínima exibida", 0.0, 1.0, 0.5, 0.05)

# --- Filtrar predições ---
df = preds[
    (preds["doenca"] == doenca) &
    (preds["definicao"] == definicao) &
    (preds["modelo"] == modelo) &
    (preds["fold_ano_teste"] == fold) &
    (preds["prob_predita"] >= risco_min)
].copy()

# Adicionar nome do município
df = df.merge(municipios[["cod_ibge", "nome_municipio"]], on="cod_ibge", how="left")

# Categorizar risco e ordenar por probabilidade
df["categoria"], df["emoji"] = zip(*df["prob_predita"].apply(categorizar_risco))
df = df.sort_values("prob_predita", ascending=False)

# Métricas no topo
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de alertas", len(df))
col2.metric("🔴 Críticos (≥80%)", int((df["prob_predita"] >= 0.8).sum()))
col3.metric("🟠 Altos (50-80%)", int(((df["prob_predita"] >= 0.5) & (df["prob_predita"] < 0.8)).sum()))
col4.metric("🟡 Moderados (20-50%)", int(((df["prob_predita"] >= 0.2) & (df["prob_predita"] < 0.5)).sum()))

# Tabela formatada
st.subheader(f"Predições para ano {fold} — {doenca.replace('_', ' ').title()} ({definicao})")
if df.empty:
    st.info("Nenhuma predição acima do limiar selecionado.")
else:
    df_display = df[[
        "emoji", "categoria", "nome_municipio", "cod_ibge", "ano", "mes",
        "prob_predita", "y_true", "surto_atual",
    ]].copy()
    df_display["mês_predito"] = df_display.apply(
        lambda r: f"{int(r['ano'])}-{int(r['mes'] % 12 + 1):02d}", axis=1
    )
    df_display = df_display[[
        "emoji", "categoria", "nome_municipio", "cod_ibge",
        "mês_predito", "prob_predita", "y_true", "surto_atual",
    ]]
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "emoji": "",
            "categoria": "Risco",
            "nome_municipio": "Município",
            "cod_ibge": "Código IBGE",
            "mês_predito": "Mês predito",
            "prob_predita": st.column_config.ProgressColumn(
                "Probabilidade", min_value=0, max_value=1, format="%.2f"
            ),
            "y_true": st.column_config.NumberColumn(
                "Surto real?", help="1 = surto realmente ocorreu, 0 = não", format="%d"
            ),
            "surto_atual": st.column_config.NumberColumn(
                "Em surto agora?", help="1 = município já estava em surto no mês corrente", format="%d"
            ),
        },
    )

    # Análise rápida de acertos no fold
    st.divider()
    st.subheader("Avaliação retroativa")
    n_alertas = len(df)
    n_corretos = int(df["y_true"].sum())
    st.markdown(
        f"Dos **{n_alertas} alertas** acima do limiar selecionado neste fold, "
        f"**{n_corretos} correspondiam a surtos reais** "
        f"({n_corretos / n_alertas * 100:.1f}% de precisão neste recorte). "
        "Variar o limiar (slider lateral) muda o trade-off precisão × cobertura."
    )

st.divider()
st.caption(
    "ℹ️ Use a página **🔍 Município** para ver justificativa SHAP detalhada de cada alerta. "
    "A coluna *surto_atual* indica se o município já estava em surto no mês corrente — "
    "alertas onde *surto_atual=0* representam **antecipação verdadeira** (modelo prevê INÍCIO)."
)
