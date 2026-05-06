"""
Análise específica de TRANSIÇÕES — capacidade do modelo de prever INÍCIO de surto.

Pergunta científica: o modelo só "mantém" predição durante surtos em curso, ou
é capaz de antecipar a transição NÃO-surto → surto (alerta precoce, o que
realmente importa para o gestor)?

Para cada (município, mês t), classifica:
  0 → 0   "normal"        (sem surto, continua sem)
  0 → 1   "INÍCIO"        ← o caso crítico, o que define utilidade do modelo
  1 → 0   "fim"           (surto termina)
  1 → 1   "manutenção"    (surto em curso)

Métricas reportadas POR SUBCONJUNTO:
  - Recall em INÍCIO: dos meses de início de surto, quantos o modelo previu?
    (persistência por definição: 0%)
  - Precisão em alerta: dos alertas do modelo em meses NÃO-surto, quantos eram início real?

Saída: data/processed/tabela_transicoes.csv + impressão no console
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from arboviral.evaluation.splits import adicionar_target_year, folds_expanding_window
from arboviral.io import PROCESSED
from arboviral.models.classifiers import (
    make_ebm, make_lightgbm, make_logreg, make_random_forest, make_xgboost,
)
from arboviral.train import _ajustar_xgb_scale_pos_weight, _preparar_X_y_meta

DOENCAS_DEFINICOES = [
    ("dengue", "canal"),
    ("dengue", "inc100"),
    ("chikungunya", "canal"),
    ("zika", "canal"),
]

MODELOS = {
    "logreg": make_logreg,
    "rf":     make_random_forest,
    "xgb":    make_xgboost,
    "lgbm":   make_lightgbm,
    "ebm":    make_ebm,
}


def classificar_transicao(surto_atual: int, surto_t1: int) -> str:
    if surto_atual == 0 and surto_t1 == 0:
        return "normal_continua"
    if surto_atual == 0 and surto_t1 == 1:
        return "INICIO"
    if surto_atual == 1 and surto_t1 == 1:
        return "manutencao"
    return "fim"


def analisar(doenca: str, definicao: str, feats: pd.DataFrame, labels: pd.DataFrame) -> list[dict]:
    print(f"\n=== {doenca} × {definicao} ===", flush=True)
    X, y, meta = _preparar_X_y_meta(feats, labels, doenca, definicao, incluir_cross=True)
    df_split = pd.concat([meta, X], axis=1)
    folds = list(folds_expanding_window(df_split))

    rows: list[dict] = []
    for ano_teste, idx_train, idx_test in folds:
        if len(idx_train) == 0 or len(idx_test) == 0:
            continue
        cols_validas = X.loc[idx_train].columns[X.loc[idx_train].notna().any()].tolist()
        X_train = X.loc[idx_train, cols_validas]
        y_train = y.loc[idx_train]
        X_test = X.loc[idx_test, cols_validas]
        y_test = y.loc[idx_test]
        surto_atual = meta.loc[idx_test, "surto_atual"].values

        if int(y_train.sum()) == 0:
            continue

        # Classificar transições no teste
        tipos = np.array([classificar_transicao(s, t) for s, t in zip(surto_atual, y_test.values)])

        # Treinar cada modelo e avaliar nas transições
        for nome, factory in MODELOS.items():
            mdl = factory()
            try:
                if nome == "xgb":
                    _ajustar_xgb_scale_pos_weight(mdl, y_train)
                mdl.fit(X_train, y_train)
                proba = mdl.predict_proba(X_test)[:, 1]
                pred = (proba >= 0.5).astype(int)
            except Exception as e:
                print(f"  [erro] {nome} fold {ano_teste}: {e}", flush=True)
                continue

            # Recall por subconjunto
            for tipo in ("INICIO", "manutencao", "fim", "normal_continua"):
                mask = tipos == tipo
                n_no_subset = int(mask.sum())
                if n_no_subset == 0:
                    continue
                pred_pos = int(pred[mask].sum())
                # "Recall positivo" = fração de exemplos do subset que recebeu alerta
                #   Para INICIO e manutencao, esse é o recall verdadeiro (target=1)
                #   Para normal_continua e fim, é a TAXA DE ALARMES FALSOS no subset
                taxa = pred_pos / n_no_subset if n_no_subset > 0 else 0
                rows.append({
                    "doenca": doenca, "definicao": definicao, "modelo": nome,
                    "fold": ano_teste, "tipo_transicao": tipo,
                    "n_amostras": n_no_subset,
                    "n_predito_positivo": pred_pos,
                    "taxa": round(taxa, 3),
                })

        # Persistência como baseline (probabilidade = surto_atual, threshold 0.5 → predição = surto_atual)
        pred_persist = surto_atual
        for tipo in ("INICIO", "manutencao", "fim", "normal_continua"):
            mask = tipos == tipo
            n_no_subset = int(mask.sum())
            if n_no_subset == 0:
                continue
            taxa = int(pred_persist[mask].sum()) / n_no_subset
            rows.append({
                "doenca": doenca, "definicao": definicao, "modelo": "persistencia",
                "fold": ano_teste, "tipo_transicao": tipo,
                "n_amostras": n_no_subset,
                "n_predito_positivo": int(pred_persist[mask].sum()),
                "taxa": round(taxa, 3),
            })

    return rows


def main() -> None:
    print("Carregando features e labels...", flush=True)
    feats = pd.read_parquet(PROCESSED / "features.parquet")
    labels = pd.read_parquet(PROCESSED / "labels.parquet")

    todas: list[dict] = []
    for d, defn in DOENCAS_DEFINICOES:
        rows = analisar(d, defn, feats, labels)
        todas.extend(rows)

    df = pd.DataFrame(todas)
    out = PROCESSED / "tabela_transicoes.csv"
    df.to_csv(out, index=False)

    # Resumo: agregar por (doenca, definicao, modelo, tipo) — média sobre folds
    print("\n" + "=" * 100)
    print("CAPACIDADE DE PREVER INÍCIO DE SURTO (recall em transição 0→1)")
    print("Persistência por definição = 0% (nunca prevê início)")
    print("=" * 100)
    pivot = (df.groupby(["doenca", "definicao", "modelo", "tipo_transicao"])
               ["taxa"].mean().unstack().round(3))
    if "INICIO" in pivot.columns:
        pivot = pivot[["INICIO", "manutencao", "fim", "normal_continua"]]
    print(pivot.to_string())
    print(f"\nSalvo: {out}")


if __name__ == "__main__":
    main()
