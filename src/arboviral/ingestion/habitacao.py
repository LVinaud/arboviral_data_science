"""
Ingestão: habitação — favelas e moradias em situação de risco.

Fontes:
    - IBGE Aglomerados Subnormais (Censo 2022, com complementos do Censo 2020)
    - IBGE MUNIC (variável MMAM2612 — moradia em situação de risco ambiental)

Periodicidade: anual / estática (varia por variável).

Arquivos esperados em data/raw/habitacao/:
    aglomerados_subnormais_*.xlsx
    munic_mmam2612_*.xlsx  (ou usar a base MUNIC já em data/raw/munic/)

Saída: data/interim/habitacao.parquet
Chave: (cod_ibge, ano)  — para variáveis estáticas, replicar em todos os anos
Colunas:
    pop_favelas:               int
    num_favelas:               int
    mmam2612_moradia_risco:    bool
"""
from pathlib import Path

import pandas as pd

from arboviral.io import RAW, INTERIM


def build() -> pd.DataFrame:
    """TODO: implementar parsers e padronização Sim/Não → bool."""
    raise NotImplementedError("Aguardando arquivos brutos em data/raw/habitacao/")


if __name__ == "__main__":
    df = build()
    out = INTERIM / "habitacao.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Wrote {len(df):,} rows to {out}")
