"""
Wrappers de predição + explicação SHAP para o app.

Reutiliza diretamente as funções do pacote `arboviral` (princípio: app
DEPENDE do data science, nunca o contrário).
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from arboviral.evaluation.explain import shap_por_predicao


def predicao_atual(modelo, features_municipio: pd.DataFrame) -> float:
    """Probabilidade de surto no próximo mês para um município (1 linha)."""
    return float(modelo.predict_proba(features_municipio)[0, 1])


def justificar_alerta(modelo, features_municipio: pd.DataFrame, top: int = 5) -> pd.DataFrame:
    """Top features que mais contribuíram para a predição.

    Retorna DataFrame com: feature, valor_observado, shap, abs_shap, sign.
    Apenas modelos baseados em árvore (RF, XGB, LGBM) têm SHAP por predição.
    """
    return shap_por_predicao(modelo, features_municipio, top=top)


def categorizar_risco(prob: float) -> tuple[str, str]:
    """Categoriza probabilidade em (categoria_label, cor_emoji)."""
    if prob >= 0.8:
        return "Crítico", "🔴"
    elif prob >= 0.5:
        return "Alto", "🟠"
    elif prob >= 0.2:
        return "Moderado", "🟡"
    else:
        return "Baixo", "🟢"


def cor_risco(prob: float) -> str:
    """Cor hex correspondente ao nível de risco (para gráficos)."""
    if prob >= 0.8:
        return "#dc2626"  # vermelho
    elif prob >= 0.5:
        return "#ea580c"  # laranja
    elif prob >= 0.2:
        return "#facc15"  # amarelo
    else:
        return "#16a34a"  # verde
