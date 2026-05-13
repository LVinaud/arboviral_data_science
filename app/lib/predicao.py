"""
Wrappers de predição + explicação local para o app.

Reutiliza diretamente as funções do pacote `arboviral` (princípio: app
DEPENDE do data science, nunca o contrário).
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from arboviral.evaluation.explain import explicacao_local
from i18n import t


def predicao_atual(modelo, features_municipio: pd.DataFrame) -> float:
    """Probabilidade de surto no próximo mês para um município (1 linha)."""
    return float(modelo.predict_proba(features_municipio)[0, 1])


def justificar_alerta(modelo, features_municipio: pd.DataFrame, top: int = 5) -> pd.DataFrame:
    """Top features que mais contribuíram para a predição.

    Retorna DataFrame com colunas: feature, valor_observado, contribuicao,
    abs_contribuicao, sign, metodo. O método de explicação varia por tipo:
      - Árvore (RF/XGB/LGBM)        → SHAP TreeExplainer
      - Regressão Logística         → coef × valor padronizado
      - EBM (Explainable Boosting)  → API nativa explain_local
    """
    return explicacao_local(modelo, features_municipio, top=top)


def categorizar_risco(prob: float) -> str:
    """Categoriza probabilidade em label de categoria de risco.

    Thresholds alinhados ao design system (lib/tema.py): 0.25 / 0.50 / 0.75.
    A cor visual fica por conta do CSS (risk_badge / risk_legend) — esta função
    devolve apenas o rótulo textual em PT/EN.
    """
    if prob >= 0.75:
        return t("categorizar_risco.critico")
    elif prob >= 0.50:
        return t("categorizar_risco.alto")
    elif prob >= 0.25:
        return t("categorizar_risco.moderado")
    else:
        return t("categorizar_risco.baixo")


# Defaults preferidos para os selectboxes do app — uso prático mostrou que
# essa combinação é a mais informativa (dengue tem volume; inc100 é a definição
# operacional mais usada por gestores; rf é o melhor modelo geral).
DEFAULT_DOENCA = "dengue"
DEFAULT_DEFINICAO = "inc100"
DEFAULT_MODELO = "rf"


def idx_default(opcoes: list, preferido: str, fallback: int = 0) -> int:
    """Retorna o índice de `preferido` em `opcoes`; `fallback` se não existe."""
    try:
        return list(opcoes).index(preferido)
    except ValueError:
        return fallback


def cor_risco(prob: float) -> str:
    """Cor hex correspondente ao nível de risco (para gráficos plotly)."""
    if prob >= 0.75:
        return "#dc2626"   # crítico
    elif prob >= 0.50:
        return "#ea580c"   # alto (laranja queimado)
    elif prob >= 0.25:
        return "#a16207"   # moderado (mostarda)
    else:
        return "#15803d"   # baixo (verde)
