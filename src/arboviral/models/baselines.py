"""
Baselines triviais (sem ML). Servem como piso de comparação.

  Persistência:  P(surto t+1) = surto(t)
  Climatologia:  P(surto t+1) = média histórica de surtos no (município, mês)

Cada baseline é um wrapper com a interface mínima fit/predict_proba esperada
pelo train.py — sem dependência de scikit-learn.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class BaselinePersistencia:
    """Predição = label do mês corrente (assume continuidade do estado atual).

    Espera que X tenha uma coluna `surto_atual` com o label de t (não t+1).
    Não 'fita' nada — apenas devolve a coluna como probabilidade {0, 1}.
    """
    nome = "persistencia"

    def fit(self, X, y):
        return self

    def predict_proba(self, X):
        p = np.asarray(X["surto_atual"].fillna(0).values, dtype=float)
        return np.column_stack([1 - p, p])


class BaselineClimatologia:
    """Predição = frequência histórica de surtos para (município, mês), aprendida no fit."""
    nome = "climatologia"

    def __init__(self):
        self.mapa: dict[tuple[int, int], float] = {}
        self.media_global: float = 0.0

    def fit(self, X, y):
        df = pd.DataFrame({
            "cod_ibge": X["cod_ibge"].values,
            "mes": X["mes"].values,
            "y": np.asarray(y, dtype=float),
        })
        agg = df.groupby(["cod_ibge", "mes"])["y"].mean()
        self.mapa = agg.to_dict()
        self.media_global = float(df["y"].mean())
        return self

    def predict_proba(self, X):
        chaves = list(zip(X["cod_ibge"].values, X["mes"].values))
        p = np.array([self.mapa.get(k, self.media_global) for k in chaves], dtype=float)
        return np.column_stack([1 - p, p])
