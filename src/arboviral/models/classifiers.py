"""
Classificadores ML. Todos com class_weight='balanced' (ou equivalente) para
lidar com class imbalance — ver nota didática em AUDITORIA_DADOS.

Modelos intrinsecamente interpretáveis:
  - LogReg: coeficientes lineares
  - EBM (Explainable Boosting Machine): contribuição por feature como curva

Modelos black-box (com explicação post-hoc via SHAP em explain.py):
  - Random Forest, XGBoost, LightGBM

Imputação: NaN → mediana (necessária para LogReg/RF/EBM; XGB e LGBM lidam
com NaN nativamente, mas mantemos pipeline uniforme por simplicidade).
"""
from __future__ import annotations

from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Hyperparâmetros: defaults razoáveis. Tuning fica como trabalho futuro
# (Optuna sobre fold de validação interna; para a IC, defaults são OK).
RANDOM_STATE = 42


def make_logreg() -> Pipeline:
    return Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("sc", StandardScaler()),
        ("clf", LogisticRegression(
            class_weight="balanced",
            max_iter=2000,
            solver="lbfgs",
            random_state=RANDOM_STATE,
        )),
    ])


def make_random_forest() -> Pipeline:
    return Pipeline([
        ("imp", SimpleImputer(strategy="median").set_output(transform="pandas")),
        ("clf", RandomForestClassifier(
            n_estimators=200,
            max_depth=None,
            min_samples_leaf=20,
            class_weight="balanced",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        )),
    ])


def make_xgboost() -> Pipeline:
    from xgboost import XGBClassifier
    # XGBoost: scale_pos_weight ≈ n_neg/n_pos para balancear (calculado on-the-fly em train.py)
    return Pipeline([
        ("imp", SimpleImputer(strategy="median").set_output(transform="pandas")),
        ("clf", XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            tree_method="hist",
            n_jobs=-1,
            eval_metric="aucpr",
            random_state=RANDOM_STATE,
        )),
    ])


def make_lightgbm() -> Pipeline:
    from lightgbm import LGBMClassifier
    return Pipeline([
        ("imp", SimpleImputer(strategy="median").set_output(transform="pandas")),
        ("clf", LGBMClassifier(
            n_estimators=300,
            num_leaves=63,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            class_weight="balanced",
            n_jobs=-1,
            verbose=-1,
            random_state=RANDOM_STATE,
        )),
    ])


def make_ebm() -> Pipeline:
    from interpret.glassbox import ExplainableBoostingClassifier
    return Pipeline([
        ("imp", SimpleImputer(strategy="median").set_output(transform="pandas")),
        ("clf", ExplainableBoostingClassifier(
            interactions=3,        # menos interações = ~3-5x mais rápido
            max_rounds=2000,        # ao invés de 5000
            random_state=RANDOM_STATE,
        )),
    ])


def todos_modelos() -> dict[str, Pipeline]:
    """Retorna dict {nome: factory()} com todos os modelos ML do portfolio."""
    return {
        "logreg":   make_logreg(),
        "ebm":      make_ebm(),
        "rf":       make_random_forest(),
        "xgb":      make_xgboost(),
        "lgbm":     make_lightgbm(),
    }
