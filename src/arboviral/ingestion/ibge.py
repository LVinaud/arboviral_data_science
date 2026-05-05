"""
Ingestão: IBGE — população estimada anual por município.

Fonte: Estimativas populacionais IBGE.
Periodicidade: anual.

Arquivos esperados em data/raw/ibge/:
    populacao_estimada_{ANO}.xlsx  (ou consolidado em um único arquivo)

Saída: data/interim/populacao.parquet
Chave: (cod_ibge, ano)
Colunas:
    populacao_estimada: int
    nome_municipio:     str
    cod_regiao_saude:   int
    nome_regiao_saude:  str
"""
from pathlib import Path

import pandas as pd

from arboviral.io import RAW, INTERIM


def build() -> pd.DataFrame:
    """TODO: implementar leitura das estimativas populacionais."""
    raise NotImplementedError("Aguardando arquivos brutos em data/raw/ibge/")


if __name__ == "__main__":
    df = build()
    out = INTERIM / "populacao.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Wrote {len(df):,} rows to {out}")
