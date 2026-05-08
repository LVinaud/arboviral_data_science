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
a explicação local é o uso típico:
  explicacao_local(modelo, X_municipio) → top features que impulsionaram a
  predição naquele município/mês. Despacha para SHAP (árvore), coef×valor
  padronizado (LogReg) ou explain_local nativo (EBM) conforme o tipo do clf.
  Output uniforme: [feature, valor_observado, contribuicao, sign, metodo].

  Alias retrocompat: shap_por_predicao() — renomeia 'contribuicao' para 'shap'.
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


def _classe_clf(modelo) -> str:
    """Nome da classe do estimador final do pipeline (ex.: 'RandomForestClassifier')."""
    return type(_extrair_clf(modelo)).__name__


def _explicacao_tree(modelo, X_amostra: pd.DataFrame) -> np.ndarray:
    """SHAP TreeExplainer — funciona em RF, XGBoost, LightGBM."""
    import shap

    clf = _extrair_clf(modelo)
    X_imp = _aplicar_imputer(modelo, X_amostra)
    explainer = shap.TreeExplainer(clf)
    vals = explainer.shap_values(X_imp)
    # Binário: alguns retornam só classe pos, outros lista [neg, pos], outros 3D
    if isinstance(vals, list) and len(vals) == 2:
        vals = vals[1]
    elif hasattr(vals, "ndim") and vals.ndim == 3:
        vals = vals[..., 1]
    return np.asarray(vals).reshape(-1)


def _explicacao_logreg(modelo, X_amostra: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """LogReg: contribuição de cada feature na predição = coef × valor_padronizado.

    Como o pipeline tem StandardScaler antes do clf, o modelo "vê" os valores
    padronizados — a contribuição honesta é coef * X_scaled, não coef * X cru.
    A soma dessas contribuições + intercept_ produz exatamente o logit da
    predição (sanity check).

    Retorna (contribuicoes, colunas_alinhadas) — a lista de colunas pode ser
    um SUBCONJUNTO de X_amostra.columns se o pipeline foi treinado com filtro.
    """
    clf = _extrair_clf(modelo)
    # Restringe X às colunas que o pipeline conhece (algumas features podem ter
    # sido filtradas no train — ver feature_names_in_ do primeiro transformador).
    cols_modelo = None
    if hasattr(modelo, "named_steps"):
        primeira = next(iter(modelo.named_steps.values()))
        if hasattr(primeira, "feature_names_in_"):
            cols_modelo = list(primeira.feature_names_in_)
    if cols_modelo:
        # Adiciona colunas faltantes como NaN; remove colunas extras
        X_align = X_amostra.copy()
        for c in cols_modelo:
            if c not in X_align.columns:
                X_align[c] = float("nan")
        X_align = X_align[cols_modelo]
    else:
        X_align = X_amostra

    X_pre = X_align
    if hasattr(modelo, "named_steps"):
        for nome, etapa in modelo.named_steps.items():
            if nome == "clf":
                break
            X_pre = etapa.transform(X_pre)
    X_arr = np.asarray(X_pre).reshape(-1)
    return clf.coef_[0] * X_arr, list(cols_modelo or X_amostra.columns)


def _explicacao_ebm(modelo, X_amostra: pd.DataFrame) -> np.ndarray:
    """EBM: API nativa do interpret-ml — `explain_local` retorna a contribuição
    aditiva de cada feature/par de features para a predição em logit.

    Mais fiel ao modelo do que SHAP em GAM, porque o EBM literalmente soma
    essas funções para gerar a predição. Inclui termos de interação (pares),
    que aqui são listados pelo nome 'feat_a & feat_b' e desempatados pelo
    valor absoluto da contribuição.

    Para alinhar com o output das outras funções (uma linha por feature de
    entrada), distribuímos a contribuição de interações ao primeiro membro
    do par — opção pragmática para ranking.
    """
    clf = _extrair_clf(modelo)
    X_imp = _aplicar_imputer(modelo, X_amostra)

    expl = clf.explain_local(X_imp)
    data = expl.data(0)
    nomes = data["names"]                    # nomes na ordem do EBM (incluindo pares 'a & b')
    scores = np.asarray(data["scores"])      # contribuição em logit por termo
    cols_originais = list(X_imp.columns)

    # Agrega: para termos main, soma direto na coluna; para pares 'a & b',
    # soma metade em 'a' e metade em 'b' (preserva total e mantém o ranking
    # consistente com o efeito real).
    contrib = np.zeros(len(cols_originais))
    for nome, score in zip(nomes, scores):
        if " & " in str(nome):
            partes = [p.strip() for p in str(nome).split(" & ")]
            for p in partes:
                if p in cols_originais:
                    contrib[cols_originais.index(p)] += score / len(partes)
        else:
            if nome in cols_originais:
                contrib[cols_originais.index(nome)] += score
    return contrib


def explicacao_local(
    modelo, X_amostra: pd.DataFrame, top: int = 5
) -> pd.DataFrame:
    """Para UMA predição (1 linha), top features que mais contribuíram.

    Despacha pelo tipo do estimador final do pipeline:
      - RandomForest, XGBoost, LightGBM   → SHAP TreeExplainer
      - LogisticRegression                → coef × valor_padronizado
      - ExplainableBoostingClassifier     → API nativa do EBM (explain_local)

    Use case: gestor, seu município está em risco POR ESSES MOTIVOS (ordenados).
    Output uniforme:
      feature  valor_observado  contribuicao  abs_contribuicao  sign  metodo
    """
    if len(X_amostra) != 1:
        raise ValueError("Esperando exatamente uma linha em X_amostra")

    classe = _classe_clf(modelo)
    cols = list(X_amostra.columns)
    if classe in ("RandomForestClassifier", "XGBClassifier", "LGBMClassifier"):
        contrib = _explicacao_tree(modelo, X_amostra)
        metodo = "SHAP (TreeExplainer)"
    elif classe == "LogisticRegression":
        contrib, cols = _explicacao_logreg(modelo, X_amostra)
        metodo = "Coeficiente × valor padronizado"
    elif classe == "ExplainableBoostingClassifier":
        contrib = _explicacao_ebm(modelo, X_amostra)
        metodo = "EBM explain_local (nativo)"
    else:
        raise NotImplementedError(
            f"Explicação local não implementada para {classe}. "
            "Modelos suportados: árvore (RF/XGB/LGBM), LogReg, EBM."
        )

    # Valor observado: lê do X_amostra alinhado às colunas usadas pelo modelo.
    valores = []
    for c in cols:
        v = X_amostra[c].iloc[0] if c in X_amostra.columns else float("nan")
        valores.append(v)
    df = pd.DataFrame({
        "feature": cols,
        "valor_observado": np.asarray(valores, dtype=float),
        "contribuicao": contrib,
        "abs_contribuicao": np.abs(contrib),
        "sign": ["+" if v >= 0 else "-" for v in contrib],
        "metodo": metodo,
    }).sort_values("abs_contribuicao", ascending=False).reset_index(drop=True)
    return df.head(top)


def shap_por_predicao(modelo, X_amostra: pd.DataFrame, top: int = 5) -> pd.DataFrame:
    """Alias retrocompat: chama `explicacao_local` e renomeia coluna p/ 'shap'.

    Mantido pela base de código antiga (app/lib/predicao.py:justificar_alerta).
    Quando o modelo é EBM/LogReg, 'shap' guarda a contribuição nativa daquele
    modelo, não SHAP propriamente dito — ver coluna `metodo`.
    """
    df = explicacao_local(modelo, X_amostra, top=top)
    return df.rename(columns={"contribuicao": "shap", "abs_contribuicao": "abs_shap"})
