"""
Ingestão: SINAN/DATASUS — arboviroses (dengue, zika, chikungunya).

Fonte: Sistema de Informação de Agravos de Notificação (SINAN) via DATASUS.
Origem: download manual via TabNet ou pacote pysus.
Periodicidade do dado bruto: registro individual; agregar para mensal.

Arquivos esperados em data/raw/sinan/:
    DENGBR{AA}.csv        — um por ano (2015–2025)
    ZIKABR{AA}.csv        — quando disponível
    CHIKBR{AA}.csv        — quando disponível

Saída:
    data/interim/sinan_dengue.parquet
    data/interim/sinan_zika.parquet
    data/interim/sinan_chikungunya.parquet

Chave: (cod_ibge, ano, mes)

Notas importantes:
    - Filtrar por município de RESIDÊNCIA (não de notificação).
    - Coeficientes/taxas dependem da população estimada — ver ingestion.ibge.
    - "sexo_predominante" e "faixa_etaria_predominante" admitem o valor "Empate".
"""
from pathlib import Path

import pandas as pd

from arboviral.io import RAW, INTERIM


def build() -> pd.DataFrame:
    """TODO: implementar parser SINAN."""
    raise NotImplementedError("Aguardando arquivos brutos em data/raw/sinan/")


if __name__ == "__main__":
    df = build()
    out = INTERIM / "sinan_dengue.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Wrote {len(df):,} rows to {out}")
