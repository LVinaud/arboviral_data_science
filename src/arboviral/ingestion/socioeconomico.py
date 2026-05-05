"""
Ingestão: indicadores socioeconômicos municipais.

Fontes (uma por variável):
    pib_per_capita: IBGE
    idhm:           Atlas do Desenvolvimento Humano no Brasil
    capag:          Sistema do Tesouro Nacional (CAPAG)
    gini:           DATASUS

Periodicidade: anual.

Arquivos esperados em data/raw/socioeconomico/:
    pib_per_capita_*.xlsx
    idhm.xlsx
    CAPAG_*.xlsx
    gini_datasus_*.csv

Saída: data/interim/socioeconomico.parquet
Chave: (cod_ibge, ano)
Colunas:
    pib_per_capita: float
    idhm:           float
    capag:          categoria {A, B, C, "n.d."}
    gini:           float
"""
from pathlib import Path

import pandas as pd

from arboviral.io import RAW, INTERIM


def build() -> pd.DataFrame:
    """TODO: ler as quatro fontes e juntar por (cod_ibge, ano)."""
    raise NotImplementedError("Aguardando arquivos brutos em data/raw/socioeconomico/")


if __name__ == "__main__":
    df = build()
    out = INTERIM / "socioeconomico.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Wrote {len(df):,} rows to {out}")
