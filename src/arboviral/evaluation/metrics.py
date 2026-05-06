"""
Métricas de avaliação para classificação binária com classes desbalanceadas.

Métrica primária: AUPRC (Average Precision) — robusta a class imbalance.
Reportada junto com o lift sobre baseline aleatório (= prevalência da classe positiva).

Métricas secundárias (a um threshold fixo de 0.5):
  F1, sensibilidade (recall), especificidade, precisão.

Para problemas raros (zika, FA), também reportamos AUPRC para sanity check —
quando há zero positivos no teste, AUPRC fica indefinido e retornamos NaN.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def computar_metricas(y_true: np.ndarray, y_proba: np.ndarray, threshold: float = 0.5) -> dict:
    """Retorna dict com todas as métricas. y_true/y_proba são arrays 1D."""
    y_true = np.asarray(y_true)
    y_proba = np.asarray(y_proba)
    y_pred = (y_proba >= threshold).astype(int)

    n = len(y_true)
    n_pos = int(y_true.sum())
    n_neg = n - n_pos
    prevalencia = n_pos / n if n > 0 else np.nan

    if n_pos == 0:
        # Sem positivos no teste: AUPRC, F1, recall indefinidos
        return {
            "n": n, "n_pos": 0, "prevalencia": prevalencia,
            "auprc": np.nan, "auprc_lift": np.nan,
            "f1": np.nan, "recall": np.nan, "specificity": np.nan, "precision": np.nan,
        }

    auprc = average_precision_score(y_true, y_proba)
    auprc_lift = auprc / prevalencia if prevalencia > 0 else np.nan

    if n_neg == 0:
        specificity = np.nan
    else:
        tn, fp, _, _ = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        specificity = tn / (tn + fp)

    return {
        "n": n,
        "n_pos": n_pos,
        "prevalencia": prevalencia,
        "auprc": auprc,
        "auprc_lift": auprc_lift,
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "specificity": specificity,
        "precision": precision_score(y_true, y_pred, zero_division=0),
    }
