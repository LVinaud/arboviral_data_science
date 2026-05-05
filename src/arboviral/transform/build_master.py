"""
Consolida os parquets intermediários no dataset canônico município–mês.

Estratégia:
    1. Carrega todos os parquets de data/interim/.
2. Faz merge sequencial sobre as chaves apropriadas:
       - mensal:   (cod_ibge, ano, mes)
       - anual:    (cod_ibge, ano)            — broadcast para todos os meses
       - estática: (cod_ibge)                 — broadcast para todos os anos/meses
    3. Valida o esquema contra configs/schema.yaml.
    4. Grava data/processed/municipio_mes.parquet.

Esqueleto. Implementar à medida que as ingestões forem ficando prontas.
"""
from pathlib import Path

import pandas as pd

from arboviral.io import INTERIM, PROCESSED


def build() -> pd.DataFrame:
    """TODO: implementar joins quando houver pelo menos duas ingestões prontas."""
    raise NotImplementedError("Aguardando primeiros parquets em data/interim/")


if __name__ == "__main__":
    df = build()
    out = PROCESSED / "municipio_mes.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Wrote {len(df):,} rows to {out}")
