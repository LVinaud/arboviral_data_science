"""
Treina e avalia todos os modelos para todas as combinações (doença × definição × fold).

Loop:
  para cada doença em [dengue, zika, chikungunya, febre_amarela]:
    para cada definição em [canal, zscore, inc100, inc300]:
      construir target_t1 = surto(t+1) por groupby+shift
      para cada fold (target_year=2022, 2023, 2024):
        para cada modelo em [persistência, climatologia, logreg, ebm, rf, xgb, lgbm]:
          treinar, predizer, computar métricas
          salvar linha em results

Saída: data/processed/model_results.parquet (uma linha por combinação)

Uso:
  python -m arboviral.train                    # todas as combinações
  python -m arboviral.train --doencas dengue   # apenas dengue
  python -m arboviral.train --no-cross         # sem features cross-doença
"""
from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from arboviral.evaluation.metrics import computar_metricas
from arboviral.evaluation.splits import (
    ANOS_TESTE,
    adicionar_target_year,
    folds_expanding_window,
)
from arboviral.io import PROCESSED
from arboviral.models.baselines import BaselineClimatologia, BaselinePersistencia
from arboviral.models.classifiers import todos_modelos

DOENCAS = ["dengue", "zika", "chikungunya", "febre_amarela"]
DEFINICOES = ["canal", "zscore", "inc100", "inc300"]


def _construir_target_t1(labels: pd.DataFrame, doenca: str, definicao: str) -> pd.Series:
    """Calcula target = surto(t+1) via groupby(cod_ibge) + shift(-1).

    Linhas onde t+1 não existe (último mês de cada município) ficam NaN —
    serão removidas via dropna no train.
    """
    col = f"{doenca}_surto_{definicao}"
    return (
        labels.sort_values(["cod_ibge", "ano", "mes"])
              .groupby("cod_ibge")[col]
              .shift(-1)
    )


def _preparar_X_y_meta(
    feats: pd.DataFrame, labels: pd.DataFrame, doenca: str, definicao: str,
    incluir_cross: bool = True,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Junta features + target + colunas auxiliares para baselines.

    Retorna (X, y, meta) onde:
      X: features para os modelos ML (pode excluir cross-doença)
      y: target_t1 binário
      meta: DataFrame com cod_ibge, ano, mes, target_year, surto_atual (para baselines)
    """
    df = feats.copy()
    df = df.merge(labels, on=["cod_ibge", "ano", "mes"], how="left")

    # Target = surto(t+1) e label do mês atual (para baseline persistência)
    df["target_t1"] = _construir_target_t1(labels, doenca, definicao).values
    df["surto_atual"] = df[f"{doenca}_surto_{definicao}"].fillna(0).astype(int)
    df = adicionar_target_year(df)

    # Remover linhas sem target (último mês de cada município) e fora do range válido
    df = df.dropna(subset=["target_t1"])
    df["target_t1"] = df["target_t1"].astype(int)

    cols_meta = ["cod_ibge", "ano", "mes", "target_year", "surto_atual"]
    cols_label = [c for c in df.columns if "_surto_" in c or "_incid_100k" in c]
    cols_label += ["target_t1"]
    cols_X = [c for c in df.columns if c not in cols_meta + cols_label]

    if not incluir_cross:
        outras = [d for d in DOENCAS if d != doenca]
        cols_X = [c for c in cols_X if not any(c.startswith(o + "_") for o in outras)]

    X = df[cols_X]
    y = df["target_t1"]
    meta = df[cols_meta]
    return X.reset_index(drop=True), y.reset_index(drop=True), meta.reset_index(drop=True)


def _ajustar_xgb_scale_pos_weight(modelo, y_train: pd.Series):
    """XGBoost não aceita class_weight; em vez disso usa scale_pos_weight = n_neg/n_pos."""
    n_pos = int(y_train.sum())
    n_neg = len(y_train) - n_pos
    spw = (n_neg / max(n_pos, 1)) if n_pos > 0 else 1.0
    if hasattr(modelo, "named_steps") and "clf" in modelo.named_steps:
        if modelo.named_steps["clf"].__class__.__name__ == "XGBClassifier":
            modelo.named_steps["clf"].set_params(scale_pos_weight=spw)


def avaliar_combinacao(
    feats: pd.DataFrame, labels: pd.DataFrame,
    doenca: str, definicao: str, incluir_cross: bool = True,
) -> list[dict]:
    """Avalia todos os modelos para uma combinação (doença × definição) em todos os folds."""
    rows: list[dict] = []
    X, y, meta = _preparar_X_y_meta(feats, labels, doenca, definicao, incluir_cross)
    df_split = pd.concat([meta, X], axis=1)

    for fold_idx, (ano_teste, idx_train, idx_test) in enumerate(
        folds_expanding_window(df_split), start=1
    ):
        if len(idx_train) == 0 or len(idx_test) == 0:
            continue
        X_train, y_train = X.loc[idx_train], y.loc[idx_train]
        X_test, y_test = X.loc[idx_test], y.loc[idx_test]
        meta_train = meta.loc[idx_train]
        meta_test = meta.loc[idx_test]

        # Descartar colunas all-NaN no treino (ex.: SINISA pré-2023). Para o teste
        # essas colunas também devem ser descartadas para manter alinhamento.
        cols_validas = X_train.columns[X_train.notna().any()].tolist()
        X_train = X_train[cols_validas]
        X_test = X_test[cols_validas]

        n_pos_train = int(y_train.sum())
        n_pos_test = int(y_test.sum())
        if n_pos_train == 0:
            print(f"    [skip] fold {ano_teste}: zero positivos no treino", flush=True)
            continue

        # --- Baselines (precisam de meta + surto_atual, não de X completo) ---
        for baseline_cls in (BaselinePersistencia, BaselineClimatologia):
            t0 = time.time()
            base = baseline_cls()
            X_base_train = pd.concat([meta_train[["cod_ibge", "mes", "surto_atual"]]], axis=1)
            X_base_test = pd.concat([meta_test[["cod_ibge", "mes", "surto_atual"]]], axis=1)
            base.fit(X_base_train, y_train)
            proba = base.predict_proba(X_base_test)[:, 1]
            m = computar_metricas(y_test.values, proba)
            rows.append({
                "doenca": doenca, "definicao": definicao, "modelo": base.nome,
                "fold_ano_teste": ano_teste, "n_train": len(y_train), "n_pos_train": n_pos_train,
                "incluir_cross": incluir_cross, "tempo_s": round(time.time() - t0, 2),
                **m,
            })

        # --- Modelos ML ---
        modelos = todos_modelos()
        for nome, mdl in modelos.items():
            t0 = time.time()
            try:
                if nome == "xgb":
                    _ajustar_xgb_scale_pos_weight(mdl, y_train)
                mdl.fit(X_train, y_train)
                proba = mdl.predict_proba(X_test)[:, 1]
                m = computar_metricas(y_test.values, proba)
            except Exception as e:
                print(f"    [erro] {nome} fold {ano_teste}: {e}", flush=True)
                m = {k: np.nan for k in
                     ("n", "n_pos", "prevalencia", "auprc", "auprc_lift",
                      "f1", "recall", "specificity", "precision")}
            rows.append({
                "doenca": doenca, "definicao": definicao, "modelo": nome,
                "fold_ano_teste": ano_teste, "n_train": len(y_train), "n_pos_train": n_pos_train,
                "incluir_cross": incluir_cross, "tempo_s": round(time.time() - t0, 2),
                **m,
            })

    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doencas", nargs="+", default=DOENCAS, choices=DOENCAS)
    parser.add_argument("--definicoes", nargs="+", default=DEFINICOES, choices=DEFINICOES)
    parser.add_argument("--no-cross", action="store_true",
                        help="Excluir features cross-doença para sensitivity analysis (RQ2)")
    args = parser.parse_args()

    print("Carregando features e labels...", flush=True)
    feats = pd.read_parquet(PROCESSED / "features.parquet")
    labels = pd.read_parquet(PROCESSED / "labels.parquet")

    incluir_cross = not args.no_cross
    suffix = "" if incluir_cross else "_nocross"

    todas_rows: list[dict] = []
    total = len(args.doencas) * len(args.definicoes)
    contador = 0

    for doenca in args.doencas:
        for definicao in args.definicoes:
            contador += 1
            print(f"\n[{contador}/{total}] {doenca} × {definicao} (cross={incluir_cross})", flush=True)
            t0 = time.time()
            rows = avaliar_combinacao(feats, labels, doenca, definicao, incluir_cross)
            todas_rows.extend(rows)
            print(f"  ({time.time() - t0:.1f}s) {len(rows)} resultados", flush=True)

    df_results = pd.DataFrame(todas_rows)
    out = PROCESSED / f"model_results{suffix}.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df_results.to_parquet(out, index=False)
    print(f"\nGravado {len(df_results):,} linhas em {out}")

    # Resumo: AUPRC médio por (doença, definição, modelo) — média sobre folds
    print("\n" + "=" * 90)
    print("AUPRC MÉDIO (sobre 3 folds) — modelo × doença × definição")
    print("=" * 90)
    pivot = (df_results.groupby(["doenca", "definicao", "modelo"])
             .agg(auprc_media=("auprc", "mean"),
                  auprc_lift_media=("auprc_lift", "mean"),
                  recall_media=("recall", "mean"))
             .round(3))
    print(pivot.to_string())


if __name__ == "__main__":
    main()
