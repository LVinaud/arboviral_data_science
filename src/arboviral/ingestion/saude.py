"""
Ingestão: DATASUS — capacidade da rede pública municipal de saúde.

Fonte: DATASUS (CNES e indicadores derivados).
Periodicidade: mensal (capacidade) / anual ou eventual (mortalidade materna).

Arquivos esperados em data/raw/saude/:
    leitos_*.csv
    medicos_*.csv
    mortalidade_materna_*.csv

Saída: data/interim/saude.parquet
Chave: (cod_ibge, ano, mes)
Colunas:
    leitos_publicos:      leitos hospitalares na rede pública municipal
    medicos_publicos:     médicos disponíveis na rede pública municipal
    mortalidade_materna:  taxa por 100 mil nascidos vivos (anual; broadcast nos meses)
"""
from pathlib import Path

import pandas as pd

from arboviral.io import RAW, INTERIM


def build() -> pd.DataFrame:
    """TODO: implementar parser e harmonização das três fontes."""
    raise NotImplementedError("Aguardando arquivos brutos em data/raw/saude/")


if __name__ == "__main__":
    df = build()
    out = INTERIM / "saude.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Wrote {len(df):,} rows to {out}")
