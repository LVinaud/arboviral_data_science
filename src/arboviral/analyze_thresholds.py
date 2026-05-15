"""
Análise precision × recall por threshold, com foco em INÍCIO de surto.

Pergunta científica: o relatório (§7) reporta recall em INÍCIO de surto
assumindo threshold default = 0.5. Mas e se o gestor quiser **mais
confiança** no alerta? Ou seja, só agir quando o modelo der ≥ 70% ou
≥ 90% de probabilidade?

Para cada (doença × definição × modelo × threshold), calcula sobre
`predictions.parquet`:

    n_alertas         linhas com prob_predita ≥ T
    n_alertas_corretos linhas alertadas E y_true=1   (acertos da classe alvo)
    precision         n_alertas_corretos / n_alertas
    recall            n_alertas_corretos / total positivos da classe

Refinamento focado em INÍCIO de surto (transição 0→1):

    n_inicio_alertados  linhas em transicao=INICIO E prob_predita ≥ T
    recall_inicio       n_inicio_alertados / total INÍCIO
    precision_inicio    n_inicio_alertados / n_alertas
                        (que % dos alertas são exatamente INÍCIO de surto?)

Threshold sweep: 0.5, 0.6, 0.7, 0.8, 0.9.

Saídas:
    data/processed/threshold_sweep.parquet  long-format com 1 linha por
                                            (doenca, definicao, modelo, fold,
                                             threshold) e 8 métricas
    data/processed/threshold_resumo.csv     pivot por (doenca, definicao,
                                            modelo) com média sobre folds
    Stdout: tabelas markdown prontas para colar no RELATORIO_MODELAGEM.md §13.

Uso:
    python -m arboviral.analyze_thresholds
    python -m arboviral.analyze_thresholds --thresholds 0.5 0.75 0.9
"""
from __future__ import annotations

import argparse

import pandas as pd

from arboviral.io import PROCESSED

THRESHOLDS_PADRAO = [0.5, 0.6, 0.7, 0.8, 0.9]


def _classificar_transicao(surto_atual: int, surto_t1: int) -> str:
    """0→0 = normal, 0→1 = INICIO (caso crítico), 1→1 = manutencao, 1→0 = fim."""
    if surto_atual == 0 and surto_t1 == 0:
        return "normal"
    if surto_atual == 0 and surto_t1 == 1:
        return "INICIO"
    if surto_atual == 1 and surto_t1 == 1:
        return "manutencao"
    return "fim"


def _metricas_por_threshold(grupo: pd.DataFrame, threshold: float) -> dict:
    """Calcula métricas para um único (doença, definição, modelo, fold, T).

    Convenção: linha alertada = prob_predita ≥ T.

    Métricas globais (sobre todas as transições):
      n_alertas, n_alertas_corretos, precision, recall

    Métricas focadas em INÍCIO (transição 0→1, classe crítica):
      n_inicio_total, n_inicio_alertados, recall_inicio, precision_inicio

    Precisão do alerta de início (foco do gestor — alerta novo,
    município ainda calmo, vai mesmo virar surto?):
      n_alertas_em_calmo            : alertas a T em meses surto_atual=0
      n_inicio_acertados_em_calmo   : alertas em calmo que viraram surto
      precision_alerta_inicio       : taxa de acerto do alerta de início
                                      (= 1 - taxa de falso alarme em mês calmo)
    """
    alertado = grupo["prob_predita"] >= threshold
    pos = grupo["y_true"] == 1
    inicio = grupo["transicao"] == "INICIO"
    em_calmo = grupo["surto_atual"] == 0   # município sem surto agora

    n_alertas = int(alertado.sum())
    n_alertas_corretos = int((alertado & pos).sum())
    n_total_positivos = int(pos.sum())
    n_inicio_total = int(inicio.sum())
    n_inicio_alertados = int((alertado & inicio).sum())
    n_alertas_em_calmo = int((alertado & em_calmo).sum())
    # Alertas em mês calmo cujo mês seguinte virou surto = INÍCIO acertado
    n_inicio_acertados_em_calmo = int((alertado & em_calmo & pos).sum())

    precision = (n_alertas_corretos / n_alertas) if n_alertas else float("nan")
    recall = (n_alertas_corretos / n_total_positivos) if n_total_positivos else float("nan")
    recall_inicio = (n_inicio_alertados / n_inicio_total) if n_inicio_total else float("nan")
    # "Dos alertas, quantos % são INÍCIO?" — útil para gestor entender se o
    # alerta tende a apontar surtos novos ou apenas reforça surtos em curso.
    precision_inicio = (n_inicio_alertados / n_alertas) if n_alertas else float("nan")
    # "Quando o modelo grita ≥T num município ainda calmo, qual % das vezes
    # ele acerta que vai começar surto?" Esta é a métrica operacional do
    # alerta preventivo: ignora alertas em surto em curso (manutenção/fim)
    # e foca no que importa para o gestor — confiança da previsão de surto novo.
    precision_alerta_inicio = (
        n_inicio_acertados_em_calmo / n_alertas_em_calmo
        if n_alertas_em_calmo else float("nan")
    )

    return {
        "threshold": threshold,
        "n_amostras": len(grupo),
        "n_alertas": n_alertas,
        "n_alertas_corretos": n_alertas_corretos,
        "precision": round(precision, 4) if pd.notna(precision) else None,
        "recall": round(recall, 4) if pd.notna(recall) else None,
        "n_inicio_total": n_inicio_total,
        "n_inicio_alertados": n_inicio_alertados,
        "recall_inicio": round(recall_inicio, 4) if pd.notna(recall_inicio) else None,
        "precision_inicio": round(precision_inicio, 4) if pd.notna(precision_inicio) else None,
        "n_alertas_em_calmo": n_alertas_em_calmo,
        "n_inicio_acertados_em_calmo": n_inicio_acertados_em_calmo,
        "precision_alerta_inicio": round(precision_alerta_inicio, 4)
                                    if pd.notna(precision_alerta_inicio) else None,
    }


def _carregar_predicoes() -> pd.DataFrame:
    pred_path = PROCESSED / "predictions.parquet"
    if not pred_path.exists():
        raise FileNotFoundError(
            f"{pred_path} ausente. Rode antes:\n  python -m arboviral.train"
        )
    df = pd.read_parquet(pred_path)
    df["transicao"] = [
        _classificar_transicao(s, y) for s, y in zip(df["surto_atual"], df["y_true"])
    ]
    return df


def _sweep(df: pd.DataFrame, thresholds: list[float]) -> pd.DataFrame:
    """Retorna long-format: 1 linha por (doença, definição, modelo, fold, T)."""
    chaves = ["doenca", "definicao", "modelo", "fold_ano_teste"]
    linhas: list[dict] = []
    for chave_vals, grupo in df.groupby(chaves):
        for t in thresholds:
            row = dict(zip(chaves, chave_vals))
            row.update(_metricas_por_threshold(grupo, t))
            linhas.append(row)
    return pd.DataFrame(linhas)


def _imprimir_destaques(sweep: pd.DataFrame, thresholds: list[float]) -> None:
    """Imprime tabelas markdown prontas para o relatório.

    Foca nos cenários mais informativos: top de cada doença (RF × {dengue
    inc100, chik inc100, zika canal}), comparando como recall_inicio e
    precision_inicio caem (ou sobem) ao endurecer o threshold.
    """
    cenarios = [
        ("dengue", "inc100", "rf"),
        ("chikungunya", "inc100", "rf"),
        ("zika", "canal", "rf"),
        ("dengue", "canal", "rf"),
    ]

    print("\n## Recall e precision em INÍCIO de surto, por threshold (média sobre 3 folds)\n")
    print("Definição operacional do alerta: linha com `prob_predita ≥ T` é considerada "
          "**alerta de surto**. INÍCIO de surto = transição mês calmo → mês de surto (0→1).\n")
    print("- **precision** (geral): dos meses alertados, quantos tinham surto no mês "
          "seguinte (qualquer transição).\n"
          "- **recall** (geral): dos meses com surto no t+1, quantos % o modelo alertou.\n"
          "- **recall_inicio**: dos meses que de fato foram INÍCIO de surto, quantos % o "
          "modelo alertou.\n"
          "- **prec_alerta_inicio**: filtra apenas os alertas em meses calmos "
          "(município sem surto agora). Dentre eles, qual % realmente virou surto no "
          "mês seguinte (acertou um INÍCIO real)? = 1 − taxa de falso alarme em "
          "mês calmo. **Métrica operacional do alerta preventivo.**\n")

    for doenca, definicao, modelo in cenarios:
        sub = sweep[
            (sweep["doenca"] == doenca)
            & (sweep["definicao"] == definicao)
            & (sweep["modelo"] == modelo)
        ]
        if sub.empty:
            continue
        # Média sobre folds para cada threshold
        agg = (sub.groupby("threshold")
                  .agg(recall=("recall", "mean"),
                       precision=("precision", "mean"),
                       recall_inicio=("recall_inicio", "mean"),
                       precision_inicio=("precision_inicio", "mean"),
                       precision_alerta_inicio=("precision_alerta_inicio", "mean"),
                       n_alertas=("n_alertas", "mean"),
                       n_alertas_em_calmo=("n_alertas_em_calmo", "mean"),
                       n_inicio_total=("n_inicio_total", "mean"))
                  .reset_index())

        print(f"### {doenca} × {definicao} × {modelo}\n")
        print("| Threshold | Recall geral | Precision geral | Recall INÍCIO | "
              "**Prec alerta INÍCIO** | n alertas / fold | n alertas em calmo / fold | "
              "n INÍCIO / fold |")
        print("|---:|---:|---:|---:|---:|---:|---:|---:|")
        for _, row in agg.iterrows():
            pai = (f"{row['precision_alerta_inicio']:.3f}"
                   if pd.notna(row['precision_alerta_inicio']) else "—")
            print(f"| {row['threshold']:.2f} | "
                  f"{row['recall']:.3f} | {row['precision']:.3f} | "
                  f"{row['recall_inicio']:.3f} | **{pai}** | "
                  f"{row['n_alertas']:.0f} | {row['n_alertas_em_calmo']:.0f} | "
                  f"{row['n_inicio_total']:.0f} |")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Análise precision × recall por threshold com foco em INÍCIO."
    )
    parser.add_argument("--thresholds", nargs="+", type=float, default=THRESHOLDS_PADRAO,
                        help=f"Thresholds a varrer (padrão: {THRESHOLDS_PADRAO}).")
    args = parser.parse_args()

    print("Carregando predictions.parquet...", flush=True)
    df = _carregar_predicoes()
    print(f"  {len(df):,} predições, {df.groupby(['doenca','definicao','modelo']).ngroups} combinações")

    print(f"Varrendo {len(args.thresholds)} thresholds: {args.thresholds}...", flush=True)
    sweep = _sweep(df, args.thresholds)

    out = PROCESSED / "threshold_sweep.parquet"
    sweep.to_parquet(out, index=False)
    print(f"Gravado long-format: {out} ({len(sweep):,} linhas)")

    # Resumo agregado por (doença, definição, modelo) — média sobre folds
    resumo = (sweep.groupby(["doenca", "definicao", "modelo", "threshold"])
                   .agg({"precision": "mean", "recall": "mean",
                         "precision_inicio": "mean", "recall_inicio": "mean"})
                   .round(4)
                   .reset_index())
    out_csv = PROCESSED / "threshold_resumo.csv"
    resumo.to_csv(out_csv, index=False)
    print(f"Gravado resumo agregado: {out_csv}")

    _imprimir_destaques(sweep, args.thresholds)


if __name__ == "__main__":
    main()
