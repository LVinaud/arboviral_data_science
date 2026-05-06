"""
Pós-processa model_results.parquet em tabelas e rankings prontos para o relatório.

Saídas (impressão e arquivos em data/processed/):
  - tabela_auprc_doenca_definicao.csv: AUPRC médio por (doença × definição × modelo)
  - tabela_modelo_ranking.csv: ranking dos modelos por AUPRC médio (responde RQ1)
  - tabela_concordancia_definicoes.csv: AUPRC do melhor modelo para cada definição (RQ4)
  - tabela_baseline_lift.csv: ganho sobre baseline aleatório (lift)

Uso:
  python -m arboviral.analyze_results
  python -m arboviral.analyze_results --doencas dengue
"""
from __future__ import annotations

import argparse

import pandas as pd

from arboviral.io import PROCESSED


def _carregar() -> pd.DataFrame:
    df = pd.read_parquet(PROCESSED / "model_results.parquet")
    return df


def tabela_auprc(df: pd.DataFrame) -> pd.DataFrame:
    """AUPRC médio sobre folds, por (doença, definição, modelo)."""
    return (
        df.groupby(["doenca", "definicao", "modelo"])
          .agg(auprc=("auprc", "mean"),
               auprc_lift=("auprc_lift", "mean"),
               auprc_std=("auprc", "std"),
               recall=("recall", "mean"),
               precision=("precision", "mean"),
               f1=("f1", "mean"),
               specificity=("specificity", "mean"),
               n_pos_test=("n_pos", "mean"))
          .round(3)
    )


def ranking_modelos(df: pd.DataFrame) -> pd.DataFrame:
    """Ranking global por AUPRC médio (RQ1)."""
    return (
        df.groupby("modelo")
          .agg(auprc_media=("auprc", "mean"),
               auprc_lift_media=("auprc_lift", "mean"),
               recall_media=("recall", "mean"),
               n_combinacoes=("auprc", "count"))
          .sort_values("auprc_lift_media", ascending=False)
          .round(3)
    )


def tabela_melhor_por_definicao(df: pd.DataFrame) -> pd.DataFrame:
    """Para cada (doença, definição), qual modelo ganha (responde RQ4)."""
    agg = (df.groupby(["doenca", "definicao", "modelo"])
             .agg(auprc=("auprc", "mean"),
                  auprc_lift=("auprc_lift", "mean"))
             .reset_index())
    # Excluir baselines do "melhor modelo" (queremos saber se ML > baseline)
    agg_ml = agg[~agg["modelo"].isin(["persistencia", "climatologia"])]
    melhor = (agg_ml.sort_values("auprc_lift", ascending=False)
              .groupby(["doenca", "definicao"])
              .first()
              .reset_index())

    # Adicionar baseline para comparação
    base_persist = (agg[agg["modelo"] == "persistencia"]
                    .groupby(["doenca", "definicao"])["auprc_lift"]
                    .first().reset_index()
                    .rename(columns={"auprc_lift": "lift_persistencia"}))
    base_clim = (agg[agg["modelo"] == "climatologia"]
                 .groupby(["doenca", "definicao"])["auprc_lift"]
                 .first().reset_index()
                 .rename(columns={"auprc_lift": "lift_climatologia"}))
    melhor = melhor.merge(base_persist, on=["doenca", "definicao"], how="left")
    melhor = melhor.merge(base_clim, on=["doenca", "definicao"], how="left")
    melhor["ganho_vs_persistencia"] = (melhor["auprc_lift"] - melhor["lift_persistencia"]).round(2)
    return melhor.round(3)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doencas", nargs="+", default=None)
    args = parser.parse_args()

    df = _carregar()
    if args.doencas:
        df = df[df["doenca"].isin(args.doencas)]

    print("=" * 100)
    print("RANKING GLOBAL DOS MODELOS (RQ1: ML melhora sobre baselines?)")
    print("=" * 100)
    rk = ranking_modelos(df)
    print(rk.to_string())

    print("\n" + "=" * 100)
    print("MELHOR MODELO POR (DOENÇA × DEFINIÇÃO) — RQ4: sensibilidade à definição de surto")
    print("Coluna ganho_vs_persistencia = quanto ML supera baseline trivial (lift relativo)")
    print("=" * 100)
    melhor = tabela_melhor_por_definicao(df)
    print(melhor[["doenca", "definicao", "modelo", "auprc", "auprc_lift",
                  "lift_persistencia", "ganho_vs_persistencia"]].to_string(index=False))

    print("\n" + "=" * 100)
    print("AUPRC POR DOENÇA × DEFINIÇÃO × MODELO (todas as combinações)")
    print("=" * 100)
    tab = tabela_auprc(df)
    print(tab[["auprc", "auprc_lift", "recall", "n_pos_test"]].to_string())

    out_dir = PROCESSED
    rk.to_csv(out_dir / "tabela_modelo_ranking.csv")
    melhor.to_csv(out_dir / "tabela_melhor_por_definicao.csv", index=False)
    tab.to_csv(out_dir / "tabela_auprc_doenca_definicao.csv")
    print(f"\nSalvas tabelas em {out_dir}")


if __name__ == "__main__":
    main()
