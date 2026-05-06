"""
Explicabilidade dos modelos.

Suporta os dois grupos do portfolio:

  Intrinsecamente interpretáveis (lemos o modelo direto):
    - LogReg:  coeficientes lineares (sinal + magnitude)
    - EBM:     contribuição por feature (curvas suaves) e interações de pares,
               via API nativa do interpret-ml

  Black-box (explicação post-hoc com SHAP):
    - RandomForest, XGBoost, LightGBM:  TreeExplainer (rápido e exato para árvores)

Funções principais:
  importancias_logreg(modelo, X)   → DataFrame [feature, coef, abs_coef]
  importancias_ebm(modelo, X)      → DataFrame [feature, importance, tipo]
  shap_tree(modelo, X, max_amostras=2000) → DataFrame [feature, shap_mean_abs]
  resumo_global(modelo, X, nome) → top features de qualquer modelo do portfolio

Para a plataforma (objetivo: "gestor, sua cidade está em risco POR ESSES MOTIVOS"),
o SHAP por predição é o uso típico:
  shap_por_predicao(modelo, X_municipio) → contribuição de cada feature
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# SHAP é importado lazy (módulo lento de carregar)


def _extrair_clf(modelo):
    """Pipeline → estimador final."""
    return modelo.named_steps["clf"] if hasattr(modelo, "named_steps") else modelo


def _aplicar_imputer(modelo, X: pd.DataFrame) -> pd.DataFrame:
    """Aplica o imputer do pipeline (se houver) e retorna DataFrame."""
    if hasattr(modelo, "named_steps") and "imp" in modelo.named_steps:
        return modelo.named_steps["imp"].transform(X)
    return X


def importancias_logreg(modelo, X: pd.DataFrame) -> pd.DataFrame:
    """Coeficientes da regressão logística — sinal indica direção."""
    clf = _extrair_clf(modelo)
    coefs = clf.coef_[0]
    df = pd.DataFrame({
        "feature": list(X.columns),
        "coef": coefs,
        "abs_coef": np.abs(coefs),
    }).sort_values("abs_coef", ascending=False).reset_index(drop=True)
    return df


def importancias_ebm(modelo, X: pd.DataFrame) -> pd.DataFrame:
    """Importância global via API nativa do EBM.

    Retorna features individuais e interações (tipo='main' ou 'interaction').
    """
    clf = _extrair_clf(modelo)
    expl_global = clf.explain_global()
    data = expl_global.data()
    df = pd.DataFrame({
        "feature": data["names"],
        "importance": data["scores"],
    })
    df["tipo"] = ["interaction" if " & " in str(n) else "main" for n in df["feature"]]
    return df.sort_values("importance", ascending=False).reset_index(drop=True)


def shap_tree(modelo, X: pd.DataFrame, max_amostras: int = 2000, random_state: int = 42) -> pd.DataFrame:
    """SHAP para modelos baseados em árvore (RF, XGB, LGBM).

    max_amostras: subamostra X para acelerar — SHAP escala com n_amostras.
    """
    import shap

    clf = _extrair_clf(modelo)
    X_imp = _aplicar_imputer(modelo, X)

    if len(X_imp) > max_amostras:
        X_imp = X_imp.sample(n=max_amostras, random_state=random_state)

    explainer = shap.TreeExplainer(clf)
    shap_vals = explainer.shap_values(X_imp)

    # Para classificadores binários, alguns retornam só a classe positiva,
    # outros uma lista [classe0, classe1]. Normalizar:
    if isinstance(shap_vals, list) and len(shap_vals) == 2:
        shap_vals = shap_vals[1]
    elif hasattr(shap_vals, "ndim") and shap_vals.ndim == 3:
        shap_vals = shap_vals[..., 1]

    abs_mean = np.abs(shap_vals).mean(axis=0)
    df = pd.DataFrame({
        "feature": list(X_imp.columns),
        "shap_mean_abs": abs_mean,
    }).sort_values("shap_mean_abs", ascending=False).reset_index(drop=True)
    return df


def resumo_global(modelo, X: pd.DataFrame, nome_modelo: str, top: int = 20) -> pd.DataFrame:
    """Wrapper genérico — devolve top features para qualquer modelo do portfolio.

    Coluna 'importance' é normalizada para somar 1 (comparável entre modelos).
    """
    if nome_modelo == "logreg":
        df = importancias_logreg(modelo, X).head(top)
        df = df.rename(columns={"abs_coef": "importance"})[["feature", "importance"]]
    elif nome_modelo == "ebm":
        df = importancias_ebm(modelo, X)
        df = df[df["tipo"] == "main"].head(top)[["feature", "importance"]]
    elif nome_modelo in ("rf", "xgb", "lgbm"):
        df = shap_tree(modelo, X).head(top)
        df = df.rename(columns={"shap_mean_abs": "importance"})
    else:
        return pd.DataFrame(columns=["feature", "importance", "modelo"])

    total = df["importance"].sum()
    df["importance_norm"] = df["importance"] / total if total > 0 else 0.0
    df["modelo"] = nome_modelo
    return df.reset_index(drop=True)


def shap_por_predicao(
    modelo, X_amostra: pd.DataFrame, top: int = 5
) -> pd.DataFrame:
    """Para UMA predição (1 linha), top features que mais contribuíram.

    Use case: gestor, seu município está em risco POR ESSES MOTIVOS (ordenados).
    Coluna 'sign' indica se a feature aumentou (+) ou diminuiu (-) o risco.
    """
    import shap

    if len(X_amostra) != 1:
        raise ValueError("Esperando exatamente uma linha em X_amostra")

    clf = _extrair_clf(modelo)
    X_imp = _aplicar_imputer(modelo, X_amostra)

    explainer = shap.TreeExplainer(clf)
    shap_vals = explainer.shap_values(X_imp)
    if isinstance(shap_vals, list) and len(shap_vals) == 2:
        shap_vals = shap_vals[1]
    elif hasattr(shap_vals, "ndim") and shap_vals.ndim == 3:
        shap_vals = shap_vals[..., 1]
    shap_vals = np.asarray(shap_vals).reshape(-1)

    df = pd.DataFrame({
        "feature": list(X_imp.columns),
        "valor_observado": X_imp.iloc[0].values,
        "shap": shap_vals,
        "abs_shap": np.abs(shap_vals),
        "sign": ["+" if v >= 0 else "-" for v in shap_vals],
    }).sort_values("abs_shap", ascending=False).reset_index(drop=True)
    return df.head(top)
