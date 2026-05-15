"""
Treina os modelos com hiperparâmetros tuned (Optuna) nos folds de teste.

Lê `data/processed/optuna_best_params.json` (gerado por
`arboviral.tune_optuna`), reconstroi cada modelo com os melhores
hiperparâmetros encontrados na busca de validação interna (target_year=2021),
e aplica a TODOS os 3 folds de teste oficiais (2022, 2023, 2024) — os
mesmos folds reportados no relatório.

Por que rodar isso depois do Optuna?
  - O Optuna otimiza AUPRC em UM fold (2021), barato e rápido.
  - Mas para reportar resultados de produção precisamos das mesmas 3 médias
    sobre 2022/2023/2024 que o `arboviral.train` já produz para os defaults.
  - Comparar `model_results.parquet` (defaults) × `model_results_TUNED.parquet`
    é exatamente isso — quanto cada modelo ganhou (ou perdeu) com tuning.

Saídas:
  data/processed/model_results_TUNED.parquet
                              uma linha por (doença × definição × modelo × fold)
                              com todas as métricas (mesmas colunas de model_results)
  data/processed/predictions_TUNED.parquet
                              uma linha por amostra de teste (igual a predictions)
  Stdout: tabela markdown comparando default vs tuned (AUPRC médio sobre folds).

Uso:
    python -m arboviral.train_tuned
    python -m arboviral.train_tuned --estudo dengue_inc100_xgb
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from arboviral.evaluation.metrics import computar_metricas
from arboviral.evaluation.splits import folds_expanding_window
from arboviral.io import PROCESSED
from arboviral.train import _preparar_X_y_meta, _registrar_predicoes

RANDOM_STATE = 42


def _construir_modelo(modelo: str, params: dict, y_train: pd.Series) -> Pipeline:
    """Reconstroi pipeline com hiperparâmetros tuned, mirroring tune_optuna.py.

    Para XGB e EBM, peso de classe depende de y_train (scale_pos_weight,
    sample_weight) — calculado on-the-fly aqui, igual ao Optuna.
    """
    n_pos = int(y_train.sum())
    n_neg = len(y_train) - n_pos
    spw = (n_neg / max(n_pos, 1)) if n_pos > 0 else 1.0

    if modelo == "rf":
        return Pipeline([
            ("imp", SimpleImputer(strategy="median").set_output(transform="pandas")),
            ("clf", RandomForestClassifier(
                **params, class_weight="balanced",
                n_jobs=-1, random_state=RANDOM_STATE,
            )),
        ])

    if modelo == "xgb":
        from xgboost import XGBClassifier
        return Pipeline([
            ("imp", SimpleImputer(strategy="median").set_output(transform="pandas")),
            ("clf", XGBClassifier(
                **params, scale_pos_weight=spw,
                tree_method="hist", n_jobs=-1, eval_metric="aucpr",
                random_state=RANDOM_STATE,
            )),
        ])

    if modelo == "lgbm":
        from lightgbm import LGBMClassifier
        return Pipeline([
            ("imp", SimpleImputer(strategy="median").set_output(transform="pandas")),
            ("clf", LGBMClassifier(
                **params, is_unbalance=True,
                n_jobs=-1, verbosity=-1, random_state=RANDOM_STATE,
            )),
        ])

    if modelo == "ebm":
        from interpret.glassbox import ExplainableBoostingClassifier
        return Pipeline([
            ("imp", SimpleImputer(strategy="median").set_output(transform="pandas")),
            ("clf", ExplainableBoostingClassifier(
                **params, random_state=RANDOM_STATE,
            )),
        ])

    if modelo == "logreg":
        # Reconstroi solver a partir do penalty (mesma lógica de tune_optuna).
        penalty = params.get("penalty", "l2")
        solver = "saga" if penalty in ("l1", "elasticnet") else "lbfgs"
        clf_params = {
            "C": params["C"], "penalty": penalty, "solver": solver,
            "class_weight": "balanced", "max_iter": 3000,
            "random_state": RANDOM_STATE,
        }
        if "l1_ratio" in params:
            clf_params["l1_ratio"] = params["l1_ratio"]
        return Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("sc", StandardScaler()),
            ("clf", LogisticRegression(**clf_params)),
        ])

    raise ValueError(f"Modelo desconhecido: {modelo}")


def _fit_predict(modelo: str, mdl: Pipeline,
                 X_train: pd.DataFrame, y_train: pd.Series,
                 X_test: pd.DataFrame) -> np.ndarray:
    """EBM aceita sample_weight; demais modelos não precisam (peso já no construtor)."""
    if modelo == "ebm":
        n_pos = int(y_train.sum())
        n_neg = len(y_train) - n_pos
        sw = np.where(y_train == 1, n_neg / max(n_pos, 1), 1.0)
        mdl.fit(X_train, y_train, clf__sample_weight=sw)
    else:
        mdl.fit(X_train, y_train)
    return mdl.predict_proba(X_test)[:, 1]


def _avaliar_estudo(nome_estudo: str, params: dict,
                    feats: pd.DataFrame, labels: pd.DataFrame,
                    pred_rows: list[dict]) -> list[dict]:
    """Avalia um estudo (doença_definição_modelo) em todos os 3 folds de teste."""
    # rsplit em 2 — preserva nomes com underscore (febre_amarela, p.ex.)
    doenca, definicao, modelo = nome_estudo.rsplit("_", 2)

    X, y, meta = _preparar_X_y_meta(feats, labels, doenca, definicao, incluir_cross=True)
    df_split = pd.concat([meta, X], axis=1)

    rows: list[dict] = []
    for ano_teste, idx_train, idx_test in folds_expanding_window(df_split):
        if len(idx_train) == 0 or len(idx_test) == 0:
            continue
        X_train, y_train = X.loc[idx_train], y.loc[idx_train]
        X_test, y_test = X.loc[idx_test], y.loc[idx_test]
        meta_test = meta.loc[idx_test]

        cols_validas = X_train.columns[X_train.notna().any()].tolist()
        X_train, X_test = X_train[cols_validas], X_test[cols_validas]
        n_pos_train = int(y_train.sum())
        if n_pos_train == 0:
            continue

        t0 = time.time()
        try:
            mdl = _construir_modelo(modelo, params, y_train)
            proba = _fit_predict(modelo, mdl, X_train, y_train, X_test)
            m = computar_metricas(y_test.values, proba)
            _registrar_predicoes(pred_rows, doenca, definicao, modelo,
                                 ano_teste, meta_test, y_test, proba, True)
        except Exception as e:
            print(f"    [erro] fold {ano_teste}: {e}", flush=True)
            m = {k: np.nan for k in
                 ("n", "n_pos", "prevalencia", "auprc", "auprc_lift",
                  "f1", "recall", "specificity", "precision")}
        rows.append({
            "doenca": doenca, "definicao": definicao, "modelo": modelo,
            "fold_ano_teste": ano_teste, "n_train": len(y_train),
            "n_pos_train": n_pos_train, "incluir_cross": True,
            "tempo_s": round(time.time() - t0, 2),
            **m,
        })
    return rows


def _comparar_default_vs_tuned(df_tuned: pd.DataFrame) -> pd.DataFrame:
    """Pivota AUPRC médio (sobre folds) lado a lado: default × tuned × delta."""
    base = pd.read_parquet(PROCESSED / "model_results.parquet")
    base = base[base["incluir_cross"] == True]  # noqa: E712

    chaves = ["doenca", "definicao", "modelo"]
    media_base = (base.groupby(chaves)["auprc"].mean()
                      .rename("auprc_default").reset_index())
    media_tuned = (df_tuned.groupby(chaves)["auprc"].mean()
                            .rename("auprc_tuned").reset_index())
    cmp = media_tuned.merge(media_base, on=chaves, how="left")
    cmp["delta"] = cmp["auprc_tuned"] - cmp["auprc_default"]
    cmp["delta_pct"] = (cmp["delta"] / cmp["auprc_default"] * 100).round(1)
    return cmp.sort_values(["doenca", "definicao", "delta"], ascending=[True, True, False])


def main() -> None:
    parser = argparse.ArgumentParser(description="Treina modelos tuned nos folds de teste oficiais.")
    parser.add_argument("--estudo", default=None,
                        help="Roda apenas um estudo (ex.: 'dengue_inc100_xgb'). "
                             "Default: todos do JSON.")
    args = parser.parse_args()

    print("Carregando best_params, features e labels...", flush=True)
    best = json.load(open(PROCESSED / "optuna_best_params.json", encoding="utf-8"))
    feats = pd.read_parquet(PROCESSED / "features.parquet")
    labels = pd.read_parquet(PROCESSED / "labels.parquet")

    estudos = [args.estudo] if args.estudo else list(best.keys())
    todas_rows: list[dict] = []
    pred_rows: list[dict] = []

    for i, nome in enumerate(estudos, start=1):
        if best[nome].get("skipped"):
            print(f"[{i}/{len(estudos)}] {nome}: SKIPPED no Optuna — pulando.")
            continue
        params = best[nome]["best_params"]
        print(f"\n[{i}/{len(estudos)}] {nome} (best AUPRC val: {best[nome]['best_value']:.4f})", flush=True)
        rows = _avaliar_estudo(nome, params, feats, labels, pred_rows)
        todas_rows.extend(rows)
        media = np.mean([r["auprc"] for r in rows if not np.isnan(r["auprc"])])
        print(f"  AUPRC tuned (média 3 folds): {media:.4f}", flush=True)

    df_tuned = pd.DataFrame(todas_rows)
    out = PROCESSED / "model_results_TUNED.parquet"
    df_tuned.to_parquet(out, index=False)
    print(f"\nGravado {len(df_tuned)} linhas em {out}")

    if pred_rows:
        df_preds = pd.DataFrame(pred_rows)
        out_preds = PROCESSED / "predictions_TUNED.parquet"
        df_preds.to_parquet(out_preds, index=False)
        print(f"Gravado {len(df_preds):,} predições em {out_preds}")

    print("\n" + "=" * 80)
    print("COMPARAÇÃO: AUPRC médio (3 folds) — DEFAULT × TUNED")
    print("=" * 80)
    cmp = _comparar_default_vs_tuned(df_tuned)
    print(cmp.round(4).to_string(index=False))

    out_cmp = PROCESSED / "tuning_comparison.csv"
    cmp.to_csv(out_cmp, index=False)
    print(f"\nGravado {out_cmp}")


if __name__ == "__main__":
    main()
