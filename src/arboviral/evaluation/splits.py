"""
Validação temporal — expanding window.

Regra crítica: como o alvo é o surto em t+1, definimos target_year = ano de t+1.
Cada linha de features (município, ano, mes) é classificada pelo ano em que cai
o target predito (= ano da feature, ou ano+1 quando mes=12).

  Fold 1: train target_year ∈ {2016..2021}, test target_year == 2022
  Fold 2: train target_year ∈ {2016..2022}, test target_year == 2023
  Fold 3: train target_year ∈ {2016..2023}, test target_year == 2024

Linhas com target_year == 2025 ficam de fora (ano "atual", reservado para
demonstração futura). Linhas com target_year == 2015 não existem porque a série
começa em 2015 (a linha jan/2015 prediz fev/2015 → target_year=2015, mas
features de jan/2015 não têm lags suficientes — descartadas via dropna).

Não há vazamento: cada predição do conjunto de teste é um surto do ano alvo,
e nenhum dado posterior ao último mês de treino é usado.
"""
from __future__ import annotations

from typing import Iterator

import numpy as np
import pandas as pd

ANOS_TESTE = [2022, 2023, 2024]


def adicionar_target_year(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona coluna target_year = ano do mês t+1."""
    df = df.copy()
    df["target_year"] = df["ano"] + (df["mes"] == 12).astype(int)
    df["target_month"] = (df["mes"] % 12) + 1
    return df


def folds_expanding_window(
    df: pd.DataFrame, anos_teste: list[int] = ANOS_TESTE
) -> Iterator[tuple[int, pd.Index, pd.Index]]:
    """Itera (target_year_teste, idx_train, idx_test).

    Pré-requisito: df tem coluna 'target_year' (chamar adicionar_target_year antes).
    """
    if "target_year" not in df.columns:
        raise ValueError("DataFrame precisa de 'target_year'. Chame adicionar_target_year().")
    for ano_teste in anos_teste:
        idx_train = df.index[df["target_year"] < ano_teste]
        idx_test = df.index[df["target_year"] == ano_teste]
        yield ano_teste, idx_train, idx_test
