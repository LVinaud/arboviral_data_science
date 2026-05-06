"""
Gera os 4 rótulos de surto para as 4 doenças (16 colunas binárias + 4 incidências).

Saída: data/processed/labels.parquet
Chave: (cod_ibge, ano, mes)

Para cada doença ∈ {dengue, zika, chikungunya, febre_amarela}, gera:
    {doenca}_incid_100k    incidência mensal por 100k hab (auxiliar, transparência)
    {doenca}_surto_canal   L1: canal endêmico
    {doenca}_surto_zscore  L2: Z-score
    {doenca}_surto_inc100  L3: incidência ≥ 100/100k hab
    {doenca}_surto_inc300  L4: incidência ≥ 300/100k hab

Imprime ao final:
    - Taxa de positivos (% de surtos) por (doença, definição)
    - Cohen's kappa par a par entre as 4 definições, por doença (responde RQ4)
"""
from __future__ import annotations

import itertools

import pandas as pd
import yaml
from sklearn.metrics import cohen_kappa_score

from arboviral.io import CONFIGS, PROCESSED
from arboviral.labels.outbreak import (
    calcular_incidencia,
    label_canal_endemico,
    label_limiar_bruto,
    label_zscore,
)


def _carregar_config() -> dict:
    with open(CONFIGS / "outbreak_label.yaml") as f:
        return yaml.safe_load(f)


def build() -> pd.DataFrame:
    cfg = _carregar_config()
    doencas: list[str] = cfg["doencas"]
    casos_min: int = cfg["casos_minimos_absolutos"]
    z_thr: float = cfg["z_score"]["threshold"]
    inc_baixo: float = cfg["limiares_brutos_por_100k"]["baixo"]
    inc_alto: float = cfg["limiares_brutos_por_100k"]["alto"]

    print(f"Carregando municipio_mes.parquet...", flush=True)
    df = pd.read_parquet(PROCESSED / "municipio_mes.parquet")

    out = df[["cod_ibge", "ano", "mes"]].copy()

    for doenca in doencas:
        anos_ep = cfg["anos_epidemicos"].get(doenca, [])
        print(f"  {doenca}: anos epidêmicos excluídos do baseline = {anos_ep}", flush=True)

        out[f"{doenca}_incid_100k"] = calcular_incidencia(df, doenca)
        out[f"{doenca}_surto_canal"]  = label_canal_endemico(df, doenca, anos_ep, casos_min)
        out[f"{doenca}_surto_zscore"] = label_zscore(df, doenca, anos_ep, casos_min, z_thr)
        out[f"{doenca}_surto_inc100"] = label_limiar_bruto(df, doenca, inc_baixo, casos_min)
        out[f"{doenca}_surto_inc300"] = label_limiar_bruto(df, doenca, inc_alto, casos_min)

    return out


def relatorio(out: pd.DataFrame, doencas: list[str]) -> None:
    print("\n" + "=" * 78)
    print("TAXA DE POSITIVOS POR (DOENÇA × DEFINIÇÃO)")
    print("=" * 78)
    print(f"{'doença':<16} {'L1 canal':>10} {'L2 zscore':>11} {'L3 inc100':>11} {'L4 inc300':>11}")
    for d in doencas:
        cols = [f"{d}_surto_{s}" for s in ("canal", "zscore", "inc100", "inc300")]
        pcts = [f"{out[c].mean()*100:>9.2f}%" for c in cols]
        print(f"{d:<16} {pcts[0]:>10} {pcts[1]:>11} {pcts[2]:>11} {pcts[3]:>11}")

    print("\n" + "=" * 78)
    print("COHEN'S KAPPA PAR A PAR ENTRE DEFINIÇÕES (RQ4)")
    print("κ < 0.20 pobre · 0.21-0.40 razoável · 0.41-0.60 moderada · 0.61-0.80 substancial · 0.81+ quase perfeita")
    print("=" * 78)
    defs = [("canal", "L1"), ("zscore", "L2"), ("inc100", "L3"), ("inc300", "L4")]
    for d in doencas:
        print(f"\n  {d.upper()}")
        for (a, la), (b, lb) in itertools.combinations(defs, 2):
            ya, yb = out[f"{d}_surto_{a}"], out[f"{d}_surto_{b}"]
            if ya.sum() == 0 and yb.sum() == 0:
                kappa_str = "N/A (ambas zero)"
            else:
                k = cohen_kappa_score(ya, yb)
                kappa_str = f"κ = {k:>+5.3f}"
            print(f"    {la} vs {lb}: {kappa_str}")


if __name__ == "__main__":
    cfg = _carregar_config()
    df = build()
    out = PROCESSED / "labels.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"\nGravado {len(df):,} linhas × {len(df.columns)} colunas em {out}")
    relatorio(df, cfg["doencas"])
