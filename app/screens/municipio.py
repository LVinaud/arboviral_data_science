"""
Página: Detalhe por município — predição + justificativa SHAP + histórico.
Permite ao gestor entender por que aquele município recebeu (ou não) alerta.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from i18n import t
from lib.carregar import (
    carregar_features,
    carregar_master,
    carregar_modelo,
    carregar_municipios,
    carregar_predicoes,
)
from lib.labels import (
    ano_mes_humano,
    humanizar_feature,
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
    justificar_alerta,
)
from lib.tema import (
    chip,
    cor_por_prob,
    metric,
    metric_row,
    nivel_de,
    page_header,
    risk_badge,
    section_label,
    shap_row,
)

municipios = carregar_municipios()
preds = carregar_predicoes()
master = carregar_master()

# --- Sidebar: seleção ---
with st.sidebar:
    st.markdown(f"### {t('comum.selecao')}")
    nomes = sorted(municipios["nome_municipio"].tolist())
    nome_sel = st.selectbox(
        t("comum.municipio"), nomes,
        index=nomes.index("São Paulo") if "São Paulo" in nomes else 0,
    )
    cod = int(municipios[municipios["nome_municipio"] == nome_sel]["cod_ibge"].iloc[0])

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
    modelos_disp = sorted(
        preds[(preds["doenca"] == doenca) & (preds["definicao"] == definicao)]["modelo"].unique()
    )
    modelo = st.selectbox(
        t("comum.modelo"), modelos_disp,
        index=idx_default(modelos_disp, DEFAULT_MODELO),
        format_func=nome_modelo,
    )
    folds_disp = sorted(preds["fold_ano_teste"].unique())
    fold = st.selectbox(
        t("comum.ano_teste"), folds_disp, index=len(folds_disp) - 1,
    )

    # Mês foca o SHAP — o gráfico de 12 meses continua mostrando o ano todo,
    # mas a justificativa SHAP analisa esse mês específico (em vez do pico).
    # Selecionamos pelo mês PREDITO (target_mes), não pelo mês das features.
    meses_disp_mun = sorted(preds[
        (preds["cod_ibge"] == cod) & (preds["doenca"] == doenca)
        & (preds["definicao"] == definicao) & (preds["modelo"] == modelo)
        & (preds["fold_ano_teste"] == fold)
    ]["target_mes"].unique())
    _opcoes_mes = ["__pico__"] + list(meses_disp_mun)
    mes_foco_sel = st.selectbox(
        t("comum.mes_analise_shap"), _opcoes_mes, index=0,
        format_func=lambda x: t("comum.pico_ano") if x == "__pico__" else nome_mes(x),
        help=t("municipio.shap_help"),
    )
    mes_foco = None if mes_foco_sel == "__pico__" else int(mes_foco_sel)

# --- Dados do município ---
mun_info = municipios[municipios["cod_ibge"] == cod].iloc[0]
ultimo_master = master[master["cod_ibge"] == cod].sort_values(["ano", "mes"]).iloc[-1]
pop = int(ultimo_master["populacao_estimada"])

# --- Header ---
page_header(
    titulo=nome_sel,
    descricao=t(
        "municipio.descricao",
        doenca=nome_doenca(doenca),
        definicao=nome_definicao(definicao),
        modelo=nome_modelo(modelo),
        fold=fold,
    ),
    crumbs=t(
        "municipio.crumbs",
        nome_upper=nome_sel.upper(),
        doenca_upper=nome_doenca(doenca).upper(),
    ),
)

# Chips com metadata do município
chips_html = " ".join([
    chip(t("municipio.chips.ibge", cod=cod), "mono"),
    chip(t("municipio.chips.populacao", pop=f"{pop:,}".replace(",", "."))),
    chip(t("municipio.chips.estacao", est=mun_info["estacao_inmet"])),
    chip(t("municipio.chips.distancia", dist=f"{mun_info['dist_estacao_km']:.1f}")),
])
st.markdown(chips_html, unsafe_allow_html=True)
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# --- Predições ---
preds_mun = preds[
    (preds["cod_ibge"] == cod)
    & (preds["doenca"] == doenca)
    & (preds["definicao"] == definicao)
    & (preds["modelo"] == modelo)
    & (preds["fold_ano_teste"] == fold)
].sort_values(["target_ano", "target_mes"]).copy()

if preds_mun.empty:
    st.warning(t("erro.sem_predicao"))
    st.stop()

# Eixo temporal = mês PREDITO (t+1). Assim fold=2024 mostra Jan→Dez/2024,
# em vez de Dez/2023 → Nov/2024 (que é o mês das features).
preds_mun["data"] = pd.to_datetime(
    preds_mun["target_ano"].astype(str) + "-"
    + preds_mun["target_mes"].astype(str).str.zfill(2)
)

# --- Mês de foco do SHAP ---
# Filtro pelo mês predito (target_mes); se não houver match, cai no pico do ano.
if mes_foco is not None and (preds_mun["target_mes"] == mes_foco).any():
    mes_pico = preds_mun[preds_mun["target_mes"] == mes_foco].iloc[0]
    label_foco = nome_mes(mes_foco)
else:
    mes_pico = preds_mun.loc[preds_mun["prob_predita"].idxmax()]
    label_foco = t("comum.pico_ano")
prob_pico = float(mes_pico["prob_predita"])
slug_pico, label_pico, _ = nivel_de(prob_pico)

n_alertas = int((preds_mun["prob_predita"] >= 0.5).sum())
n_surtos_reais = int(preds_mun["y_true"].sum())

metric_row(
    metric(label_foco,
           value=f"{prob_pico:.0%}",
           delta=(
               f"{ano_mes_humano(int(mes_pico['target_ano']), int(mes_pico['target_mes']))}"
               f" · {label_pico}"
           ),
           delta_dir="up" if slug_pico in ("alto", "critico") else None),
    metric(t("municipio.metricas.meses_alerta_label"), f"{n_alertas}",
           delta=t("municipio.metricas.meses_alerta_delta", n=len(preds_mun))),
    metric(t("municipio.metricas.surtos_reais_label"), f"{n_surtos_reais}",
           delta=t("municipio.metricas.surtos_reais_delta")),
    metric(t("municipio.metricas.definicao_label"),
           nome_definicao(definicao).split(" (")[0],
           delta=nome_definicao(definicao)),
)

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

# --- Gráfico de probabilidades ao longo do ano ---
st.markdown(section_label(t("municipio.graficos.secao_probabilidade")), unsafe_allow_html=True)

fig = go.Figure()
fig.add_trace(go.Bar(
    x=preds_mun["data"],
    y=preds_mun["prob_predita"],
    marker_color=[cor_por_prob(p) for p in preds_mun["prob_predita"]],
    name=t("municipio.graficos.trace_probabilidade"),
    text=[f"{p:.0%}" for p in preds_mun["prob_predita"]],
    textposition="outside",
    customdata=[nome_mes(m) for m in preds_mun["target_mes"]],
    hovertemplate=t("municipio.graficos.hover_prob"),
))
surto_real = preds_mun[preds_mun["y_true"] == 1]
if not surto_real.empty:
    fig.add_trace(go.Scatter(
        x=surto_real["data"],
        y=[1.05] * len(surto_real),
        mode="markers",
        marker=dict(size=14, color="#0f172a", symbol="star"),
        name=t("municipio.graficos.trace_surto"),
        customdata=[nome_mes(m) for m in surto_real["target_mes"]],
        hovertemplate=t("municipio.graficos.hover_surto"),
    ))
fig.update_layout(
    yaxis=dict(range=[0, 1.18], title=t("municipio.graficos.y_axis"),
               tickformat=".0%", gridcolor="#e2e8f0"),
    xaxis=dict(title=t("municipio.graficos.x_axis_mes_predito"), gridcolor="#e2e8f0"),
    height=340,
    showlegend=True,
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    font=dict(family="Geist, system-ui, sans-serif", color="#0f172a"),
    margin=dict(l=20, r=20, t=20, b=20),
)
st.plotly_chart(fig, use_container_width=True)

# --- Histórico de casos ---
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
st.markdown(
    section_label(t("municipio.graficos.secao_historico", doenca=nome_doenca(doenca))),
    unsafe_allow_html=True,
)

casos_col = f"{doenca}_casos"
if casos_col in master.columns:
    hist = master[master["cod_ibge"] == cod][["ano", "mes", casos_col]].copy()
    hist["data"] = pd.to_datetime(
        hist["ano"].astype(str) + "-" + hist["mes"].astype(str).str.zfill(2)
    )
    hist[casos_col] = hist[casos_col].fillna(0)

    fig_h = px.line(
        hist, x="data", y=casos_col,
        labels={
            "data": t("comum.mes"),
            casos_col: t("municipio.graficos.y_axis_casos",
                         doenca=nome_doenca(doenca),
                         doenca_lower=nome_doenca(doenca).lower()),
        },
    )
    fig_h.update_traces(line_color="#ea580c", line_width=2)
    fig_h.update_layout(
        height=280,
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Geist, system-ui, sans-serif", color="#0f172a"),
        xaxis=dict(gridcolor="#e2e8f0"),
        yaxis=dict(gridcolor="#e2e8f0"),
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig_h, use_container_width=True)

# --- SHAP ---
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

titulo_shap = (
    t("municipio.shap.titulo_alerta") if prob_pico >= 0.5
    else t("municipio.shap.titulo_baixo")
)
st.markdown(section_label(titulo_shap), unsafe_allow_html=True)
mes_humano_shap = ano_mes_humano(int(mes_pico["target_ano"]), int(mes_pico["target_mes"]))
caption_chave = "municipio.shap.caption_pico" if mes_foco is None else "municipio.shap.caption_mes"
st.caption(t(
    caption_chave,
    municipio=nome_sel,
    mes_humano=mes_humano_shap,
    prob=f"{prob_pico:.1%}",
))

if modelo in ("persistencia", "climatologia"):
    st.info(t("municipio.shap.info_baseline", modelo=nome_modelo(modelo)))
else:
    # Quantos fatores mostrar — default 8 (panorama rápido); "Todos" abre os 137.
    _opcoes_top = ["5", "8", "15", "30", "50", "__todos__"]
    qtd_sel = st.radio(
        t("municipio.shap.qtd_label"), _opcoes_top, index=1, horizontal=True,
        format_func=lambda x: t("municipio.shap.qtd_todos") if x == "__todos__" else x,
        help=t("municipio.shap.qtd_help"),
    )
    qtd_top = 9999 if qtd_sel == "__todos__" else int(qtd_sel)

    with st.spinner(t("municipio.shap.spinner")):
        mdl = carregar_modelo(doenca, definicao, modelo, fold)
        if mdl is None:
            st.error(t(
                "erro.modelo_nao_encontrado",
                arquivo=f"{doenca}_{definicao}_{modelo}_{fold}.joblib",
            ))
        else:
            features = carregar_features()
            cod_alvo = int(mes_pico["cod_ibge"])
            # Filtramos features pelo mês t (entrada do modelo); o badge mostra
            # o mês predito t+1 (target_ano/target_mes) — são instantes distintos.
            ano_features = int(mes_pico["ano"])
            mes_features = int(mes_pico["mes"])
            ano_predito = int(mes_pico["target_ano"])
            mes_predito = int(mes_pico["target_mes"])

            X_amostra = features[
                (features["cod_ibge"] == cod_alvo)
                & (features["ano"] == ano_features)
                & (features["mes"] == mes_features)
            ].copy()

            X_amostra["target_year"] = X_amostra["ano"] + (X_amostra["mes"] == 12).astype(int)
            X_amostra["target_month"] = (X_amostra["mes"] % 12) + 1
            X_amostra = X_amostra.drop(columns=["cod_ibge", "ano", "mes"])

            cols_esperadas = None
            if hasattr(mdl, "named_steps") and "clf" in mdl.named_steps:
                step = mdl.named_steps["clf"]
                if hasattr(step, "feature_names_in_"):
                    cols_esperadas = list(step.feature_names_in_)
            if cols_esperadas is None and hasattr(mdl, "feature_names_in_"):
                cols_esperadas = list(mdl.feature_names_in_)
            if cols_esperadas is None:
                cols_esperadas = X_amostra.columns.tolist()

            for c in cols_esperadas:
                if c not in X_amostra.columns:
                    X_amostra[c] = float("nan")
            X_amostra = X_amostra[cols_esperadas]

            try:
                top = justificar_alerta(mdl, X_amostra, top=qtd_top)
                max_abs = float(top["contribuicao"].abs().max())
                metodo_usado = top["metodo"].iloc[0]
                # Resumo no topo: chip de risco + mês predito + método
                st.markdown(
                    f'<div style="margin:12px 0">{risk_badge(prob_pico, lg=True)}'
                    f' <span style="margin-left:8px;color:var(--c-muted);font-size:13px">'
                    f"{ano_mes_humano(ano_predito, mes_predito)} · {prob_pico:.1%}</span>"
                    f' <span style="margin-left:8px;color:var(--c-muted-2);'
                    f'font-size:11px;font-family:var(--font-mono)">'
                    f'{t("municipio.shap.metodo", metodo=metodo_usado)}</span>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
                rows_html = "".join(
                    shap_row(
                        rank=i + 1,
                        humano=humanizar_feature(str(row["feature"])),
                        tecnico=(
                            t("municipio.shap.valor_observado",
                              tecnico=row["feature"], valor=f"{row['valor_observado']:.3g}")
                            if pd.notna(row["valor_observado"])
                            else t("municipio.shap.valor_observado_nan", tecnico=row["feature"])
                        ),
                        contrib=float(row["contribuicao"]),
                        max_abs=max_abs,
                    )
                    for i, row in top.iterrows()
                )
                st.markdown(
                    f'<div class="card">{rows_html}</div>',
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.error(t("erro.explicacao_falhou", erro=e))
