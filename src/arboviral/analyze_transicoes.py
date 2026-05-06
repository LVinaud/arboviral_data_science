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
  - Taxa de FP em normal_continua: dos meses sem surto e sem início, quantos
    receberam alarme falso?

ESTRATÉGIA: lê predictions.parquet (gerado por train.py com --save-predictions
implícito). Análise vira instantânea (era ~30 min com retreinamento).

Uso:
  python -m arboviral.analyze_transicoes
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from arboviral.io import PROCESSED


def classificar_transicao(surto_atual: int, surto_t1: int) -> str:
    if surto_atual == 0 and surto_t1 == 0:
        return "normal_continua"
    if surto_atual == 0 and surto_t1 == 1:
        return "INICIO"
    if surto_atual == 1 and surto_t1 == 1:
        return "manutencao"
    return "fim"


def main() -> None:
    pred_path = PROCESSED / "predictions.parquet"
    if not pred_path.exists():
        raise FileNotFoundError(
            f"{pred_path} não existe. Rode primeiro:\n  python -m arboviral.train"
        )

    print(f"Carregando {pred_path.name}...", flush=True)
    df = pd.read_parquet(pred_path)
    df["pred"] = (df["prob_predita"] >= 0.5).astype(int)
    df["transicao"] = [
        classificar_transicao(s, y) for s, y in zip(df["surto_atual"], df["y_true"])
    ]

    print(f"  {len(df):,} predições carregadas")
    print(f"  combinações: {df.groupby(['doenca', 'definicao', 'modelo']).ngroups}")

    # Para cada (doenca, definicao, modelo, fold, transicao): taxa = pred_pos / n
    agg = (df.groupby(["doenca", "definicao", "modelo", "fold_ano_teste", "transicao"])
             .agg(n_amostras=("pred", "size"),
                  n_predito_positivo=("pred", "sum"))
             .reset_index())
    agg["taxa"] = (agg["n_predito_positivo"] / agg["n_amostras"]).round(3)

    out = PROCESSED / "tabela_transicoes.csv"
    agg.to_csv(out, index=False)

    # Pivot para impressão amigável (média sobre folds)
    pivot = (agg.groupby(["doenca", "definicao", "modelo", "transicao"])
                ["taxa"].mean().unstack().round(3))
    if "INICIO" in pivot.columns:
        cols_ord = [c for c in ["INICIO", "manutencao", "fim", "normal_continua"]
                    if c in pivot.columns]
        pivot = pivot[cols_ord]

    print("\n" + "=" * 100)
    print("CAPACIDADE DE PREVER INÍCIO DE SURTO (recall em transição 0→1)")
    print("Persistência por definição = 0% (nunca prevê início)")
    print("=" * 100)
    print(pivot.to_string())
    print(f"\nSalvo: {out}")


if __name__ == "__main__":
    main()
