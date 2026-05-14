"""
Sensitivity analysis: features cross-doença ON vs OFF (item 1.4 do ROADMAP).

Modo padrão (default): comparação cross × no-cross no estado atual do dataset.
    model_results.parquet           cross POS-Onda 2 (padrão atual)
    model_results_nocross.parquet   no-cross POS-Onda 2 (rodado com --no-cross)

Modo histórico (--historico): comparação adicional cross × no-cross no estado
PRE-Onda 2, gerada pelo pipeline /tmp/run_full_pipeline_C.sh:
    model_results_PRE_ONDA2.parquet            cross PRE-Onda 2 (treinado em 7/mai)
    model_results_nocross_PRE_ONDA2.parquet    no-cross PRE-Onda 2 (rodado agora
                                               com `--exclude-onda2` em features)

Saídas (modo default):
    data/processed/no_cross_comparativo.parquet
    data/processed/no_cross_resumo_doenca.csv
    data/processed/no_cross_resumo_modelo.csv
    Stdout: relatório textual estado atual.

Saídas adicionais (modo --historico):
    data/processed/no_cross_comparativo_PRE_ONDA2.parquet
    data/processed/no_cross_resumo_PRE_vs_POS.csv  (Δ POS − Δ PRE por doença)
    Stdout: relatório textual incluindo PRE vs POS e tabela com a inversão
    do veredicto após Onda 2.

Hipótese científica testada: features cross-doença adicionam sinal porque
os vetores são parcialmente compartilhados (Aedes aegypti para dengue/zika/
chikungunya em particular). A pergunta agora é se a presença das fontes da
Onda 2 (SIH-SUS + mobilidade pendular) altera a magnitude do ganho cross,
porque carregam informação que antes só vinha via features prefixadas por
outras doenças.

Uso:
    python -m arboviral.analyze_no_cross
    python -m arboviral.analyze_no_cross --historico
"""
from __future__ import annotations

import argparse

import pandas as pd

from arboviral.io import PROCESSED

ARQ_CROSS_POS = PROCESSED / "model_results.parquet"
ARQ_NOCROSS_POS = PROCESSED / "model_results_nocross.parquet"

# Estado PRE-Onda 2: cross é o backup automático que fizemos em 12/mai
# (model_results.parquet daquele dia, antes de adicionarmos Onda 2 ao master),
# e o nocross é gerado pelo pipeline com `build_features --exclude-onda2`.
ARQ_CROSS_PRE = PROCESSED / "model_results_PRE_ONDA2.parquet"
ARQ_NOCROSS_PRE = PROCESSED / "model_results_nocross_PRE_ONDA2.parquet"

CHAVE = ["doenca", "definicao", "modelo", "fold_ano_teste"]
METRICAS = ["auprc", "auprc_lift", "recall"]


def _carregar_pareado(arq_cross, arq_nocross) -> pd.DataFrame:
    """Junta dois parquets na mesma chave (doença × definição × modelo × fold).

    Sufixos `_cross` e `_nocross` deixam explícito de qual run vem cada métrica.
    Combinações que existem em só um lado (improvável, mas possível se algum
    fold abortar) são descartadas via inner join — comparação só faz sentido
    quando há os dois pontos.
    """
    if not arq_cross.exists() or not arq_nocross.exists():
        raise FileNotFoundError(
            f"Faltam arquivos de treino. Verifique se rodou:\n"
            f"  {arq_cross.name}\n  {arq_nocross.name}"
        )
    a = pd.read_parquet(arq_cross)
    b = pd.read_parquet(arq_nocross)
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


def _wilcoxon_doenca(df: pd.DataFrame) -> pd.DataFrame:
    """Teste de Wilcoxon pareado de Δ AUPRC para cada doença.

    Hipótese nula: Δ AUPRC = 0 para todas as combinações daquela doença.
    Modelos baseline (persistência, climatologia) entram com Δ=0 sistemático
    e são excluídos do teste — só os 5 modelos ML contribuem informação.
    """
    try:
        from scipy.stats import wilcoxon
    except ImportError:  # pragma: no cover
        return pd.DataFrame(columns=["doenca", "n", "estatistica", "p_valor"])

    df_ml = df[~df["modelo"].isin(["persistencia", "climatologia"])]
    linhas = []
    for doenca, sub in df_ml.groupby("doenca"):
        deltas = sub["delta_auprc"].dropna()
        if len(deltas) < 6 or deltas.abs().sum() == 0:
            # Wilcoxon precisa de pelo menos uma diferença não-zero e amostra ≥6.
            linhas.append({"doenca": doenca, "n": len(deltas),
                           "estatistica": float("nan"), "p_valor": float("nan")})
            continue
        try:
            stat, p = wilcoxon(deltas, zero_method="pratt")
            linhas.append({"doenca": doenca, "n": len(deltas),
                           "estatistica": float(stat), "p_valor": float(p)})
        except ValueError:
            linhas.append({"doenca": doenca, "n": len(deltas),
                           "estatistica": float("nan"), "p_valor": float("nan")})
    return pd.DataFrame(linhas).round(4)


def _pivot_modelo_doenca(df: pd.DataFrame) -> pd.DataFrame:
    """Tabela cruzada modelo × doença com Δ AUPRC médio.

    Mostra onde o ganho cross-doença se concentra (ex.: se RF +0.017 vem
    de chikungunya ou se está distribuído).
    """
    return (
        df.groupby(["modelo", "doenca"])["delta_auprc"]
          .mean()
          .unstack(fill_value=float("nan"))
          .round(4)
    )


def _modo_estado_atual() -> None:
    """Comparação POS-Onda 2: cross × no-cross com features.parquet atual."""
    df = _carregar_pareado(ARQ_CROSS_POS, ARQ_NOCROSS_POS)
    print(f"Pareado {len(df):,} combinações POS-Onda 2 "
          f"(doença × definição × modelo × fold).\n")

    df.to_parquet(PROCESSED / "no_cross_comparativo.parquet", index=False)
    _resumo_por(df, "doenca").to_csv(PROCESSED / "no_cross_resumo_doenca.csv")
    _resumo_por(df, "modelo").to_csv(PROCESSED / "no_cross_resumo_modelo.csv")

    print(_markdown_section(df))


def _modo_historico() -> None:
    """Comparação PRE-Onda 2 + PRE vs POS — testa a inversão do veredicto.

    Roda no contexto onde o pipeline `/tmp/run_full_pipeline_C.sh` foi
    completo, gerando `model_results_nocross_PRE_ONDA2.parquet`.
    """
    df_pos = _carregar_pareado(ARQ_CROSS_POS, ARQ_NOCROSS_POS)
    df_pre = _carregar_pareado(ARQ_CROSS_PRE, ARQ_NOCROSS_PRE)
    print(f"POS-Onda 2: {len(df_pos):,} combinações pareadas")
    print(f"PRE-Onda 2: {len(df_pre):,} combinações pareadas")

    df_pre.to_parquet(PROCESSED / "no_cross_comparativo_PRE_ONDA2.parquet",
                       index=False)

    # Comparação cruzada PRE × POS por doença
    resumo_pre = _resumo_por(df_pre, "doenca").rename(
        columns={c: f"{c}_PRE" for c in ("n", "delta_auprc_medio",
                 "delta_auprc_mediano", "delta_recall_medio", "delta_lift_medio")}
    )
    resumo_pos = _resumo_por(df_pos, "doenca").rename(
        columns={c: f"{c}_POS" for c in ("n", "delta_auprc_medio",
                 "delta_auprc_mediano", "delta_recall_medio", "delta_lift_medio")}
    )
    comparado = resumo_pre.join(resumo_pos, how="outer")
    comparado["delta_do_delta_auprc"] = (
        comparado["delta_auprc_medio_POS"] - comparado["delta_auprc_medio_PRE"]
    )
    comparado.to_csv(PROCESSED / "no_cross_resumo_PRE_vs_POS.csv")

    wil_pos = _wilcoxon_doenca(df_pos)
    wil_pre = _wilcoxon_doenca(df_pre)

    print("\n## Comparativo PRE-Onda 2 × POS-Onda 2 (Δ AUPRC médio cross−nocross)\n")
    print("| Doença | Δ médio PRE | Δ médio POS | Δ do Δ (POS−PRE) |")
    print("|---|---:|---:|---:|")
    for doenca in sorted(comparado.index):
        row = comparado.loc[doenca]
        pre = row.get("delta_auprc_medio_PRE", float("nan"))
        pos = row.get("delta_auprc_medio_POS", float("nan"))
        dd = row.get("delta_do_delta_auprc", float("nan"))
        print(f"| {doenca} | {pre:+.4f} | {pos:+.4f} | {dd:+.4f} |")

    print("\n## Teste de Wilcoxon pareado por doença (apenas modelos ML)\n")
    print("Hipótese nula: Δ AUPRC = 0. Rejeita-se se p < 0.05. n = nº de "
          "(definição × modelo ML × fold) pareados naquela doença.\n")
    print("| Doença | n | p-valor PRE | p-valor POS |")
    print("|---|---:|---:|---:|")
    for d in sorted(set(wil_pos["doenca"]) | set(wil_pre["doenca"])):
        p_pre_row = wil_pre[wil_pre["doenca"] == d]
        p_pos_row = wil_pos[wil_pos["doenca"] == d]
        # `n` real do Wilcoxon vem da coluna `n` retornada por _wilcoxon_doenca
        # (não confundir com len(p_pos_row), que sempre é 1 — uma linha por doença).
        n = int(p_pos_row["n"].iloc[0]) if len(p_pos_row) else 0
        p_pre = (p_pre_row["p_valor"].iloc[0]
                 if len(p_pre_row) else float("nan"))
        p_pos = (p_pos_row["p_valor"].iloc[0]
                 if len(p_pos_row) else float("nan"))
        print(f"| {d} | {n} | {p_pre:.4f} | {p_pos:.4f} |")

    print("\n## Pivot modelo × doença (Δ AUPRC médio POS-Onda 2)\n")
    pivot = _pivot_modelo_doenca(df_pos)
    print(pivot.to_markdown())

    print("\n## Pivot modelo × doença (Δ AUPRC médio PRE-Onda 2)\n")
    pivot_pre = _pivot_modelo_doenca(df_pre)
    print(pivot_pre.to_markdown())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sensitivity analysis cross-doença (item 1.4)"
    )
    parser.add_argument("--historico", action="store_true",
                        help="Inclui análise PRE-Onda 2 e tabelas comparativas + "
                             "teste Wilcoxon. Requer model_results_nocross_PRE_ONDA2 "
                             "(gerado pelo pipeline /tmp/run_full_pipeline_C.sh).")
    args = parser.parse_args()

    if args.historico:
        _modo_historico()
    else:
        _modo_estado_atual()


if __name__ == "__main__":
    main()
