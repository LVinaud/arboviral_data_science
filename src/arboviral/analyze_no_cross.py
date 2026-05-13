"""
Sensitivity analysis: features cross-doença ON vs OFF (item 1.4 do ROADMAP).

Compara duas execuções pareadas do `train.py`:
    model_results.parquet           Treino com features cross-doença
                                     (`incluir_cross=True`, configuração padrão).
    model_results_nocross.parquet   Treino sem features cross-doença
                                     (`incluir_cross=False`, gerado por
                                      `python -m arboviral.train --no-cross`).

Calcula, para cada (doença, definição, modelo, fold):
    Δ AUPRC      = AUPRC_cross − AUPRC_nocross   (positivo = cross ajudou)
    Δ Recall     = Recall_cross − Recall_nocross
    Δ Lift       = Lift_cross   − Lift_nocross

E agrega:
  - Por doença (média sobre folds × definições × modelos)
  - Por modelo (média sobre folds × definições × doenças)
  - Top ganhos absolutos
  - Top perdas (cenários onde cross-doença atrapalhou)

Hipótese científica testada: features cross-doença adicionam sinal porque
os vetores são parcialmente compartilhados (Aedes aegypti para dengue/zika/
chikungunya em particular). Esperamos:
  - Ganho concentrado em zika (vetor compartilhado com dengue, e dengue tem
    muito mais dado disponível para o modelo aprender padrões espaço-temporais).
  - Ganho menor em chikungunya (vetor compartilhado mas dinâmica diferente).
  - Ganho marginal em dengue (a doença com mais dado próprio — pouca
    informação adicional vinda de zika/chik).
  - Ganho ~0 em febre amarela (vetor totalmente diferente — Haemagogus/
    Sabethes silvestre, não Aedes).

Saídas:
    data/processed/no_cross_comparativo.parquet   Long-format pareado (com Δ)
    data/processed/no_cross_resumo_doenca.csv      Resumo agregado por doença
    data/processed/no_cross_resumo_modelo.csv      Resumo agregado por modelo
    Stdout: relatório textual pronto para incluir em RELATORIO_MODELAGEM.md.

Uso:
    python -m arboviral.analyze_no_cross
"""
from __future__ import annotations

import pandas as pd

from arboviral.io import PROCESSED

ARQ_CROSS = PROCESSED / "model_results.parquet"
ARQ_NOCROSS = PROCESSED / "model_results_nocross.parquet"

CHAVE = ["doenca", "definicao", "modelo", "fold_ano_teste"]
METRICAS = ["auprc", "auprc_lift", "recall"]


def _carregar_pareado() -> pd.DataFrame:
    """Junta os dois parquets na mesma chave (doença × definição × modelo × fold).

    Sufixos `_cross` e `_nocross` deixam explícito de qual run vem cada métrica.
    Combinações que existem em só um lado (improvável, mas possível se algum
    fold abortar) são descartadas via inner join — comparação só faz sentido
    quando há os dois pontos.
    """
    if not ARQ_CROSS.exists() or not ARQ_NOCROSS.exists():
        raise FileNotFoundError(
            f"Faltam arquivos de treino. Verifique se rodou:\n"
            f"  python -m arboviral.train\n"
            f"  python -m arboviral.train --no-cross"
        )
    a = pd.read_parquet(ARQ_CROSS)
    b = pd.read_parquet(ARQ_NOCROSS)
    cols = CHAVE + METRICAS
    pareado = a[cols].merge(
        b[cols], on=CHAVE, how="inner", suffixes=("_cross", "_nocross"),
    )
    for m in METRICAS:
        pareado[f"delta_{m}"] = pareado[f"{m}_cross"] - pareado[f"{m}_nocross"]
    return pareado


def _resumo_por(df: pd.DataFrame, dim: str) -> pd.DataFrame:
    """Agrega Δ médio e mediano da dimensão pedida."""
    return (
        df.groupby(dim).agg(
            n=("delta_auprc", "size"),
            delta_auprc_medio=("delta_auprc", "mean"),
            delta_auprc_mediano=("delta_auprc", "median"),
            delta_recall_medio=("delta_recall", "mean"),
            delta_lift_medio=("delta_auprc_lift", "mean"),
        ).round(4).sort_values("delta_auprc_medio", ascending=False)
    )


def _top_n(df: pd.DataFrame, n: int = 10, ascending: bool = False) -> pd.DataFrame:
    """Top n cenários por Δ AUPRC (descendente = ganhos; ascendente = perdas)."""
    cols_show = CHAVE + ["auprc_cross", "auprc_nocross", "delta_auprc"]
    return (
        df[cols_show].sort_values("delta_auprc", ascending=ascending)
                     .head(n).round(4)
                     .reset_index(drop=True)
    )


def _markdown_section(df: pd.DataFrame) -> str:
    """Gera bloco markdown pronto para colar no RELATORIO_MODELAGEM.md (§11)."""
    lines: list[str] = []
    lines.append("## 11. Sensitivity analysis — features cross-doença (RQ2 / item 1.4)")
    lines.append("")
    lines.append("Comparação pareada de dois runs do pipeline de treino, com e sem "
                 "features cross-doença. A hipótese é que sinais compartilhados via "
                 "vetor (especialmente *Aedes aegypti* entre dengue/zika/chikungunya) "
                 "qualificam a predição. O run \"cross\" usa todas as features de todas "
                 "as 4 doenças disponíveis no momento `t`; o run \"no-cross\" exclui "
                 "qualquer coluna cujo prefixo seja outra doença, mantendo apenas "
                 "features da doença-alvo + clima + indicadores estruturais.")
    lines.append("")

    res_doenca = _resumo_por(df, "doenca")
    lines.append("### 11.1 Δ AUPRC médio por doença")
    lines.append("")
    lines.append("| Doença | n combinações | Δ AUPRC médio | Δ AUPRC mediano | Δ Recall médio |")
    lines.append("|---|---:|---:|---:|---:|")
    for d, row in res_doenca.iterrows():
        lines.append(f"| {d} | {int(row['n'])} | "
                     f"{row['delta_auprc_medio']:+.4f} | "
                     f"{row['delta_auprc_mediano']:+.4f} | "
                     f"{row['delta_recall_medio']:+.4f} |")
    lines.append("")

    res_modelo = _resumo_por(df, "modelo")
    lines.append("### 11.2 Δ AUPRC médio por modelo")
    lines.append("")
    lines.append("| Modelo | n combinações | Δ AUPRC médio | Δ AUPRC mediano |")
    lines.append("|---|---:|---:|---:|")
    for m, row in res_modelo.iterrows():
        lines.append(f"| {m} | {int(row['n'])} | "
                     f"{row['delta_auprc_medio']:+.4f} | "
                     f"{row['delta_auprc_mediano']:+.4f} |")
    lines.append("")

    lines.append("### 11.3 Top 10 ganhos absolutos (cross > no-cross)")
    lines.append("")
    top = _top_n(df, 10, ascending=False)
    lines.append("| Doença | Definição | Modelo | Fold | AUPRC cross | AUPRC no-cross | Δ |")
    lines.append("|---|---|---|---:|---:|---:|---:|")
    for _, row in top.iterrows():
        lines.append(f"| {row['doenca']} | {row['definicao']} | {row['modelo']} | "
                     f"{int(row['fold_ano_teste'])} | "
                     f"{row['auprc_cross']:.4f} | {row['auprc_nocross']:.4f} | "
                     f"{row['delta_auprc']:+.4f} |")
    lines.append("")

    lines.append("### 11.4 Top 10 perdas (cross < no-cross — onde cross atrapalhou)")
    lines.append("")
    bot = _top_n(df, 10, ascending=True)
    lines.append("| Doença | Definição | Modelo | Fold | AUPRC cross | AUPRC no-cross | Δ |")
    lines.append("|---|---|---|---:|---:|---:|---:|")
    for _, row in bot.iterrows():
        lines.append(f"| {row['doenca']} | {row['definicao']} | {row['modelo']} | "
                     f"{int(row['fold_ano_teste'])} | "
                     f"{row['auprc_cross']:.4f} | {row['auprc_nocross']:.4f} | "
                     f"{row['delta_auprc']:+.4f} |")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    df = _carregar_pareado()
    print(f"Pareado {len(df):,} combinações (doença × definição × modelo × fold).\n")

    # Persistência de artefatos
    df.to_parquet(PROCESSED / "no_cross_comparativo.parquet", index=False)
    _resumo_por(df, "doenca").to_csv(PROCESSED / "no_cross_resumo_doenca.csv")
    _resumo_por(df, "modelo").to_csv(PROCESSED / "no_cross_resumo_modelo.csv")

    # Relatório textual
    print(_markdown_section(df))


if __name__ == "__main__":
    main()
