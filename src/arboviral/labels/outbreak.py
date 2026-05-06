"""
Definições operacionais de surto (RQ4 — sensitivity analysis).

4 rótulos binários calculados em paralelo para cada doença:
    L1  surto_canal      Canal endêmico (mediana + 1.96·σ histórico, por mun/mês)
    L2  surto_zscore     Z-score relativo (Z > 2)
    L3  surto_inc100     Incidência ≥ 100 casos / 100 mil hab
    L4  surto_inc300     Incidência ≥ 300 casos / 100 mil hab

Em todas as definições, exige-se mínimo absoluto de casos (default 5) para
evitar que município pequeno com 1 caso isolado seja classificado como surto.

Decisões metodológicas (ver configs/outbreak_label.yaml):
- Baseline: anos não-epidêmicos da série completa (janela fixa, não expansiva).
  Justificativa: dataset começa em 2015 — não há baseline pré-série disponível
  para janela rolling. A janela fixa usa "futuro" para definir labels do passado,
  o que é aceitável (labels não são predições — são alvo do treino).
- Anos epidêmicos por doença identificados via inspeção da incidência estadual:
    dengue:        2015, 2019, 2024, 2025
    chikungunya:   2021, 2024, 2025
    zika:          2016 (único pico — definição relativa fica degenerada)
    febre amarela: 2017, 2018, 2019, 2025 (epidemia silvestre + ressurgência)
- Para zika e febre amarela, a raridade da doença leva a baseline=0 na maioria
  dos (município, mês). Canal endêmico e Z-score ficam essencialmente equivalentes
  a "qualquer caso ≥ casos_min". Isso é documentado e esperado.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _stats_baseline(
    df: pd.DataFrame,
    casos_col: str,
    anos_epidemicos: list[int],
) -> pd.DataFrame:
    """Mediana, média e std por (cod_ibge, mes) usando apenas anos não-epidêmicos."""
    baseline = df[~df["ano"].isin(anos_epidemicos)].copy()
    baseline[casos_col] = baseline[casos_col].fillna(0)
    stats = (
        baseline.groupby(["cod_ibge", "mes"])[casos_col]
        .agg(mediana="median", media="mean", desvio="std")
        .reset_index()
    )
    # std=NaN quando há apenas 1 observação no baseline; tratamos como 0
    stats["desvio"] = stats["desvio"].fillna(0)
    return stats


def label_canal_endemico(
    df: pd.DataFrame, doenca: str, anos_epidemicos: list[int], casos_min: int
) -> pd.Series:
    """L1: surto se casos > mediana_baseline + 1.96·σ_baseline E casos ≥ casos_min."""
    casos_col = f"{doenca}_casos"
    stats = _stats_baseline(df, casos_col, anos_epidemicos)
    stats["limiar"] = stats["mediana"] + 1.96 * stats["desvio"]
    merged = df[["cod_ibge", "ano", "mes", casos_col]].merge(
        stats[["cod_ibge", "mes", "limiar"]], on=["cod_ibge", "mes"], how="left"
    )
    casos = merged[casos_col].fillna(0)
    return ((casos > merged["limiar"]) & (casos >= casos_min)).astype(int)


def label_zscore(
    df: pd.DataFrame, doenca: str, anos_epidemicos: list[int], casos_min: int, threshold: float
) -> pd.Series:
    """L2: surto se Z > threshold E casos ≥ casos_min.

    Quando std=0, declara surto se casos > média (qualquer aumento sobre baseline
    constante é considerado anômalo, desde que respeitando casos_min).
    """
    casos_col = f"{doenca}_casos"
    stats = _stats_baseline(df, casos_col, anos_epidemicos)
    merged = df[["cod_ibge", "ano", "mes", casos_col]].merge(
        stats[["cod_ibge", "mes", "media", "desvio"]], on=["cod_ibge", "mes"], how="left"
    )
    casos = merged[casos_col].fillna(0)
    desvio = merged["desvio"].fillna(0)
    media = merged["media"].fillna(0)

    excede_threshold = np.where(
        desvio > 0,
        (casos - media) / desvio.replace(0, np.nan) > threshold,
        casos > media,  # fallback quando std=0
    )
    return (excede_threshold & (casos >= casos_min)).astype(int)


def label_limiar_bruto(df: pd.DataFrame, doenca: str, limiar_100k: float, casos_min: int) -> pd.Series:
    """L3/L4: surto se incidência ≥ limiar_100k E casos ≥ casos_min.

    incidência = casos / populacao_estimada * 100_000
    """
    casos_col = f"{doenca}_casos"
    casos = df[casos_col].fillna(0)
    incid = casos / df["populacao_estimada"] * 100_000
    return ((incid >= limiar_100k) & (casos >= casos_min)).astype(int)


def calcular_incidencia(df: pd.DataFrame, doenca: str) -> pd.Series:
    """Coluna auxiliar — incidência por 100k hab (transparência, não é label)."""
    casos_col = f"{doenca}_casos"
    return (df[casos_col].fillna(0) / df["populacao_estimada"] * 100_000).round(2)
