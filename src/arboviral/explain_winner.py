"""
Treina o modelo vencedor para cada doença (rótulo escolhido) e gera SHAP global +
exemplo de SHAP por predição.

Use case principal:
  - RQ2: quais features mais contribuem para a predição? (SHAP global)
  - Plataforma: justificar alerta para gestor (SHAP por predição)

Saída:
  - data/processed/shap_top_features.csv (top features por doença/modelo)
  - Imprime exemplo de SHAP por predição para um município em situação de risco

Uso:
  python -m arboviral.explain_winner
"""
from __future__ import annotations

import pandas as pd

from arboviral.evaluation.explain import resumo_global, shap_por_predicao
from arboviral.evaluation.splits import adicionar_target_year, folds_expanding_window
from arboviral.io import PROCESSED
from arboviral.models.classifiers import make_random_forest, make_lightgbm, make_ebm
from arboviral.train import _preparar_X_y_meta

# Combinações vencedoras (de model_results) — rodamos SHAP nos melhores
COMBINACOES = [
    ("dengue", "inc100", "lgbm"),         # melhor AUPRC absoluta (0.791)
    ("dengue", "canal", "rf"),            # melhor para canal endêmico
    ("chikungunya", "canal", "rf"),       # melhor para chikungunya
    ("zika", "canal", "lgbm"),            # melhor para zika
]

FACTORIES = {"rf": make_random_forest, "lgbm": make_lightgbm, "ebm": make_ebm}


def treinar_e_explicar(doenca: str, definicao: str, nome_modelo: str,
                       feats: pd.DataFrame, labels: pd.DataFrame) -> dict:
    print(f"\n=== {doenca} × {definicao} × {nome_modelo} ===", flush=True)
    X, y, meta = _preparar_X_y_meta(feats, labels, doenca, definicao, incluir_cross=True)
    df_split = pd.concat([meta, X], axis=1)

    # Treinar no fold mais "completo" (todos os anos baseline ≤ 2023, prediz 2024)
    folds = list(folds_expanding_window(df_split))
    ano_teste, idx_train, idx_test = folds[-1]
    cols_validas = X.loc[idx_train].columns[X.loc[idx_train].notna().any()].tolist()

    X_train = X.loc[idx_train, cols_validas]
    y_train = y.loc[idx_train]
    X_test = X.loc[idx_test, cols_validas]
    y_test = y.loc[idx_test]
    meta_test = meta.loc[idx_test]

    print(f"  fold teste = {ano_teste}, n_train={len(y_train):,}, "
          f"n_pos_train={int(y_train.sum())}, n_pos_test={int(y_test.sum())}", flush=True)

    modelo = FACTORIES[nome_modelo]()
    if nome_modelo == "xgb":
        from arboviral.train import _ajustar_xgb_scale_pos_weight
        _ajustar_xgb_scale_pos_weight(modelo, y_train)
    modelo.fit(X_train, y_train)

    # SHAP global — top 20 features
    print(f"  Computando SHAP global (top 20)...", flush=True)
    top = resumo_global(modelo, X_train, nome_modelo, top=20)
    print(top.to_string(index=False))

    # SHAP por predição: pegar uma linha com alta probabilidade prevista (alerta acionável)
    proba = modelo.predict_proba(X_test)[:, 1]
    top_risco = proba.argsort()[-3:][::-1]
    print(f"\n  Top 3 municípios em risco previsto (fold {ano_teste}):", flush=True)
    for rank, i in enumerate(top_risco, start=1):
        cod = meta_test.iloc[i]["cod_ibge"]
        ano = meta_test.iloc[i]["ano"]
        mes = meta_test.iloc[i]["mes"]
        target_real = y_test.iloc[i]
        prob = proba[i]
        print(f"    #{rank} cod_ibge={cod} {ano}-{mes:02d}: "
              f"prob_predita={prob:.3f}, surto_real={target_real}", flush=True)
        if nome_modelo in ("rf", "xgb", "lgbm"):
            X_amostra = X_test.iloc[[i]]
            top_feats = shap_por_predicao(modelo, X_amostra, top=5)
            for _, row in top_feats.iterrows():
                print(f"        {row['sign']} {row['feature']:<40} valor={row['valor_observado']:>10.2f}  shap={row['shap']:+.3f}", flush=True)

    top["doenca"] = doenca
    top["definicao"] = definicao
    top["modelo"] = nome_modelo
    return top.to_dict("records")


def main() -> None:
    print("Carregando features e labels...", flush=True)
    feats = pd.read_parquet(PROCESSED / "features.parquet")
    labels = pd.read_parquet(PROCESSED / "labels.parquet")

    todos_tops: list[dict] = []
    for doenca, definicao, modelo in COMBINACOES:
        try:
            rows = treinar_e_explicar(doenca, definicao, modelo, feats, labels)
            todos_tops.extend(rows)
        except Exception as e:
            print(f"  [erro] {doenca}×{definicao}×{modelo}: {e}", flush=True)

    df = pd.DataFrame(todos_tops)
    out = PROCESSED / "shap_top_features.csv"
    df.to_csv(out, index=False)
    print(f"\nSalvo {out}")


if __name__ == "__main__":
    main()
