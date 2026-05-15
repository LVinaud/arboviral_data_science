"""
Hyperparameter tuning com Optuna (item 1.5 do ROADMAP).

Otimiza hiperparâmetros do Random Forest sobre fold de validação INTERNA
(target_year=2021, treinando com tudo até 2020), preservando os 3 folds
de teste reportados no relatório (2022, 2023, 2024) intocados.

Estratégia:
  - Otimizamos AUPRC no fold de validação 2021. É a métrica primária do
    projeto, robusta a class imbalance (RQ1).
  - Sampler TPE (Tree-structured Parzen Estimator) com seed fixa para
    reprodutibilidade. 100 trials por estudo, default — ajustável via CLI.
  - Cada estudo é (doença × definição × modelo). Persistimos em SQLite
    nativo do Optuna (`data/processed/optuna_studies/<estudo>.db`) — toda
    a história dos trials fica auditável; rodadas futuras podem retomar.

Cenários atacados (por escolha do orientador, top de cada doença):
  - dengue × inc100 × rf       (AUPRC default 0.795 — melhor cenário do projeto)
  - chikungunya × inc100 × rf  (AUPRC default 0.442 — top de chik)
  - zika × canal × rf          (AUPRC default 0.171 — top de zika)
  Febre amarela é ignorada: zero positivos no teste em todas as definições.

Saídas:
  data/processed/optuna_studies/{doenca}_{definicao}_{modelo}.db
                                 SQLite com todos os trials (auditável)
  data/processed/optuna_best_params.json
                                 JSON {estudo → {best_params, best_value, n_trials}}
  Stdout: relatório textual pronto para colar no RELATORIO_MODELAGEM.md §12.

Para aplicar os hiperparâmetros tuned aos 3 folds de teste reais e gerar o
arquivo de comparação default vs tuned, ver `arboviral.train_tuned` (a ser
escrito após esta busca terminar).

Uso:
    python -m arboviral.tune_optuna                          # 3 estudos × 100 trials
    python -m arboviral.tune_optuna --n-trials 50            # mais rápido
    python -m arboviral.tune_optuna --estudo dengue_inc100_rf
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import optuna
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from arboviral.evaluation.splits import adicionar_target_year
from arboviral.io import PROCESSED

# Optuna é verboso por padrão (cada trial gera várias linhas). Reduzimos para
# WARNING para o stdout focar nos resumos de estudo.
optuna.logging.set_verbosity(optuna.logging.WARNING)

RANDOM_STATE = 42

# Cenários a tunar — top de cada doença × todos os 5 modelos ML.
# Persistência e climatologia são triviais (não usam features), por isso
# ficam de fora.
DOENCAS_DEFINICOES = [
    ("dengue", "inc100"),
    ("chikungunya", "inc100"),
    ("zika", "canal"),
]
MODELOS_ML = ["rf", "xgb", "lgbm", "ebm", "logreg"]
CENARIOS = [(d, df, m) for (d, df) in DOENCAS_DEFINICOES for m in MODELOS_ML]

# Validação interna (fold dedicado, NÃO toca nos folds de teste 2022/2023/2024)
ANO_VALIDACAO = 2021

PASTA_STUDIES = PROCESSED / "optuna_studies"


def _construir_target_t1(labels: pd.DataFrame, doenca: str, definicao: str) -> pd.Series:
    """Replica a lógica de train.py — target = surto(t+1) via groupby+shift(-1)."""
    col = f"{doenca}_surto_{definicao}"
    return (
        labels.sort_values(["cod_ibge", "ano", "mes"])
              .groupby("cod_ibge")[col]
              .shift(-1)
    )


def _preparar_X_y(
    feats: pd.DataFrame, labels: pd.DataFrame, doenca: str, definicao: str,
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Junta features + target + target_year para split interno.

    Retorna (X, y, target_year). Cross-doença habilitado por padrão (configuração
    operacional vencedora segundo §11 do RELATORIO_MODELAGEM.md).
    """
    df = feats.merge(labels, on=["cod_ibge", "ano", "mes"], how="left")
    df["target_t1"] = _construir_target_t1(labels, doenca, definicao).values
    df = adicionar_target_year(df)
    df = df.dropna(subset=["target_t1"])
    df["target_t1"] = df["target_t1"].astype(int)

    cols_meta = {"cod_ibge", "ano", "mes", "target_year", "target_month"}
    cols_label = {c for c in df.columns if "_surto_" in c or "_incid_100k" in c}
    cols_label.add("target_t1")
    cols_X = [c for c in df.columns if c not in cols_meta | cols_label]
    return df[cols_X], df["target_t1"], df["target_year"]


def _objetivo_rf(trial: optuna.Trial,
                 X_train: pd.DataFrame, y_train: pd.Series,
                 X_val: pd.DataFrame, y_val: pd.Series) -> float:
    """Função objetivo para Random Forest — devolve AUPRC no fold de validação.

    Espaço de busca cobre os hiperparâmetros mais influentes em RF para
    classificação binária desbalanceada:
      - n_estimators: tamanho da floresta
      - max_depth: profundidade máxima por árvore (None = sem limite)
      - min_samples_split / min_samples_leaf: regularização por amostra
      - max_features: aleatoriedade por split
      - max_samples: bootstrap sampling (regularização global)
    Mantemos `class_weight='balanced'` fixo — a §3 do relatório mostra que é
    crítico para nosso desbalanceamento; deixar ele variar adicionaria muito
    ruído sem ganho esperado.
    """
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 100, 1000, step=50),
        "max_depth": trial.suggest_categorical("max_depth", [None, 5, 10, 15, 20, 30]),
        "min_samples_split": trial.suggest_int("min_samples_split", 2, 50),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 30),
        "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2", 0.3, 0.5, 0.7]),
        "max_samples": trial.suggest_float("max_samples", 0.5, 1.0, step=0.1),
        "class_weight": "balanced",
        "n_jobs": -1,
        "random_state": RANDOM_STATE,
    }

    pipeline = Pipeline([
        ("imp", SimpleImputer(strategy="median").set_output(transform="pandas")),
        ("clf", RandomForestClassifier(**params)),
    ])
    pipeline.fit(X_train, y_train)
    proba = pipeline.predict_proba(X_val)[:, 1]
    return float(average_precision_score(y_val, proba))


def _objetivo_xgb(trial: optuna.Trial,
                  X_train: pd.DataFrame, y_train: pd.Series,
                  X_val: pd.DataFrame, y_val: pd.Series) -> float:
    """XGBoost — gradient boosted trees. scale_pos_weight = n_neg/n_pos para
    compensar desbalanceamento (substitui class_weight='balanced')."""
    from xgboost import XGBClassifier
    n_pos = int(y_train.sum())
    n_neg = len(y_train) - n_pos
    spw = n_neg / max(n_pos, 1)

    params = {
        "n_estimators": trial.suggest_int("n_estimators", 100, 800, step=50),
        "max_depth": trial.suggest_int("max_depth", 3, 12),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0, step=0.1),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0, step=0.1),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        "reg_lambda": trial.suggest_float("reg_lambda", 0.01, 10.0, log=True),
        "scale_pos_weight": spw,
        "tree_method": "hist",
        "n_jobs": -1,
        "eval_metric": "aucpr",
        "random_state": RANDOM_STATE,
    }
    pipeline = Pipeline([
        ("imp", SimpleImputer(strategy="median").set_output(transform="pandas")),
        ("clf", XGBClassifier(**params)),
    ])
    pipeline.fit(X_train, y_train)
    proba = pipeline.predict_proba(X_val)[:, 1]
    return float(average_precision_score(y_val, proba))


def _objetivo_lgbm(trial: optuna.Trial,
                   X_train: pd.DataFrame, y_train: pd.Series,
                   X_val: pd.DataFrame, y_val: pd.Series) -> float:
    """LightGBM — leaf-wise tree boosting. is_unbalance=True replica o efeito
    de class_weight='balanced' (atribui peso inverso à frequência da classe)."""
    from lightgbm import LGBMClassifier
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 100, 800, step=50),
        "num_leaves": trial.suggest_int("num_leaves", 15, 255),
        "max_depth": trial.suggest_int("max_depth", -1, 15),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 50),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0, step=0.1),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0, step=0.1),
        "reg_lambda": trial.suggest_float("reg_lambda", 0.01, 10.0, log=True),
        "is_unbalance": True,
        "n_jobs": -1,
        "verbosity": -1,
        "random_state": RANDOM_STATE,
    }
    pipeline = Pipeline([
        ("imp", SimpleImputer(strategy="median").set_output(transform="pandas")),
        ("clf", LGBMClassifier(**params)),
    ])
    pipeline.fit(X_train, y_train)
    proba = pipeline.predict_proba(X_val)[:, 1]
    return float(average_precision_score(y_val, proba))


def _objetivo_ebm(trial: optuna.Trial,
                  X_train: pd.DataFrame, y_train: pd.Series,
                  X_val: pd.DataFrame, y_val: pd.Series) -> float:
    """EBM (Explainable Boosting Machine) — modelo aditivo generalizado com
    bagging interno. O EBM não tem class_weight nativo, então passamos
    sample_weight inversamente proporcional à frequência da classe."""
    from interpret.glassbox import ExplainableBoostingClassifier
    params = {
        "max_bins": trial.suggest_int("max_bins", 128, 512, step=64),
        "max_interaction_bins": trial.suggest_int("max_interaction_bins", 16, 64, step=8),
        "interactions": trial.suggest_int("interactions", 0, 20),
        "learning_rate": trial.suggest_float("learning_rate", 0.005, 0.1, log=True),
        "max_leaves": trial.suggest_int("max_leaves", 2, 10),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 2, 30),
        "outer_bags": trial.suggest_int("outer_bags", 4, 16),
        "inner_bags": trial.suggest_int("inner_bags", 0, 8),
        "random_state": RANDOM_STATE,
    }
    n_pos = int(y_train.sum())
    n_neg = len(y_train) - n_pos
    sw = np.where(y_train == 1, n_neg / max(n_pos, 1), 1.0)

    pipeline = Pipeline([
        ("imp", SimpleImputer(strategy="median").set_output(transform="pandas")),
        ("clf", ExplainableBoostingClassifier(**params)),
    ])
    # sample_weight precisa ser passado por nome do step no Pipeline
    pipeline.fit(X_train, y_train, clf__sample_weight=sw)
    proba = pipeline.predict_proba(X_val)[:, 1]
    return float(average_precision_score(y_val, proba))


def _objetivo_logreg(trial: optuna.Trial,
                     X_train: pd.DataFrame, y_train: pd.Series,
                     X_val: pd.DataFrame, y_val: pd.Series) -> float:
    """Regressão Logística — pequeno espaço de busca (4 hiperparâmetros).
    Mantemos class_weight='balanced' fixo. l1 e l2 com solver compatível."""
    penalty = trial.suggest_categorical("penalty", ["l1", "l2", "elasticnet"])
    if penalty == "elasticnet":
        l1_ratio = trial.suggest_float("l1_ratio", 0.0, 1.0, step=0.1)
        solver = "saga"
    elif penalty == "l1":
        l1_ratio = None
        solver = "saga"
    else:
        l1_ratio = None
        solver = "lbfgs"

    params = {
        "C": trial.suggest_float("C", 0.001, 10.0, log=True),
        "penalty": penalty,
        "solver": solver,
        "class_weight": "balanced",
        "max_iter": 3000,
        "random_state": RANDOM_STATE,
    }
    if l1_ratio is not None:
        params["l1_ratio"] = l1_ratio

    pipeline = Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("sc", StandardScaler()),
        ("clf", LogisticRegression(**params)),
    ])
    pipeline.fit(X_train, y_train)
    proba = pipeline.predict_proba(X_val)[:, 1]
    return float(average_precision_score(y_val, proba))


# Tabela de despacho modelo → função objetivo
_OBJETIVOS = {
    "rf": _objetivo_rf,
    "xgb": _objetivo_xgb,
    "lgbm": _objetivo_lgbm,
    "ebm": _objetivo_ebm,
    "logreg": _objetivo_logreg,
}


def rodar_estudo(doenca: str, definicao: str, modelo: str,
                 feats: pd.DataFrame, labels: pd.DataFrame,
                 n_trials: int = 100) -> dict:
    """Roda um estudo Optuna completo para um cenário (doença × definição × modelo).

    Retorna dict com best_params, best_value, n_trials e tempo decorrido.
    Os trials individuais ficam persistidos no SQLite — basta carregar o
    study por nome para retomar ou reanalisar.
    """
    X, y, target_year = _preparar_X_y(feats, labels, doenca, definicao)
    idx_train = target_year < ANO_VALIDACAO
    idx_val = target_year == ANO_VALIDACAO

    n_pos_train = int(y[idx_train].sum())
    n_pos_val = int(y[idx_val].sum())
    print(f"\n  treino ≤ {ANO_VALIDACAO - 1}: {idx_train.sum():,} linhas, {n_pos_train} positivos")
    print(f"  validação == {ANO_VALIDACAO}: {idx_val.sum():,} linhas, {n_pos_val} positivos")

    if n_pos_train == 0 or n_pos_val == 0:
        print(f"  [SKIP] sem positivos no treino ou validação")
        return {"skipped": True, "reason": "sem positivos"}

    # Persistência SQLite para auditoria + retomada
    PASTA_STUDIES.mkdir(parents=True, exist_ok=True)
    nome_estudo = f"{doenca}_{definicao}_{modelo}"
    storage = f"sqlite:///{PASTA_STUDIES / (nome_estudo + '.db')}"
    study = optuna.create_study(
        study_name=nome_estudo,
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE),
        storage=storage,
        load_if_exists=True,
    )

    n_existentes = len(study.trials)
    n_a_rodar = max(0, n_trials - n_existentes)
    if n_a_rodar > 0:
        print(f"  rodando {n_a_rodar} novos trials ({n_existentes} já no banco)...", flush=True)
        t0 = time.time()
        funcao = _OBJETIVOS.get(modelo)
        if funcao is None:
            raise NotImplementedError(
                f"Modelo {modelo} sem objetivo. Disponíveis: {list(_OBJETIVOS)}"
            )
        obj = lambda tr: funcao(
            tr, X[idx_train], y[idx_train], X[idx_val], y[idx_val]
        )
        study.optimize(obj, n_trials=n_a_rodar, show_progress_bar=False)
        tempo = time.time() - t0
    else:
        print(f"  estudo já tem {n_existentes} trials ≥ {n_trials} pedidos — pulando.")
        tempo = 0.0

    return {
        "best_params": study.best_params,
        "best_value": float(study.best_value),
        "n_trials_total": len(study.trials),
        "tempo_s": round(tempo, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Tuning Optuna nos top modelos por doença.")
    parser.add_argument("--n-trials", type=int, default=100,
                        help="Número de trials por estudo (padrão: 100).")
    parser.add_argument("--estudo", default=None,
                        help="Roda apenas um estudo específico no formato "
                             "'doenca_definicao_modelo' (ex.: 'dengue_inc100_rf').")
    args = parser.parse_args()

    print("Carregando features e labels...", flush=True)
    feats = pd.read_parquet(PROCESSED / "features.parquet")
    labels = pd.read_parquet(PROCESSED / "labels.parquet")

    cenarios = CENARIOS
    if args.estudo is not None:
        # rsplit suporta nomes de doença com '_' (ex.: febre_amarela_canal_rf).
        partes = args.estudo.rsplit("_", 2)
        cenarios = [(partes[0], partes[1], partes[2])]

    resultados: dict = {}
    for doenca, definicao, modelo in cenarios:
        nome = f"{doenca}_{definicao}_{modelo}"
        print(f"\n=== Estudo: {nome} ===")
        resultados[nome] = rodar_estudo(
            doenca, definicao, modelo, feats, labels, n_trials=args.n_trials,
        )

    # Persistência consolidada — JSON com best_params para a próxima rodada de treino
    out_json = PROCESSED / "optuna_best_params.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"\nGravado {out_json}")

    # Stdout: tabela resumo pronta para o relatório
    print("\n## Resumo dos estudos\n")
    print("| Estudo | Best AUPRC validação | Trials | Tempo (s) |")
    print("|---|---:|---:|---:|")
    for nome, r in resultados.items():
        if r.get("skipped"):
            print(f"| {nome} | — | (skipped: {r.get('reason')}) | — |")
            continue
        print(f"| {nome} | {r['best_value']:.4f} | {r['n_trials_total']} | {r['tempo_s']:.0f} |")

    print("\n## Best hyperparameters\n")
    for nome, r in resultados.items():
        if r.get("skipped"):
            continue
        print(f"### {nome}")
        for k, v in r["best_params"].items():
            print(f"  - `{k}`: {v}")


if __name__ == "__main__":
    main()
