"""
Ingestão: INMET — variáveis meteorológicas mensais por município.

Fonte: Instituto Nacional de Meteorologia (INMET) — estações automáticas.
Periodicidade do dado bruto: horária; agregar para mensal (min, média, máx).

Arquivos esperados em data/raw/inmet/:
    dados_{COD_ESTACAO}_M_{INICIO}_{FIM}.csv  — um por estação automática

Lookup necessário (data/lookup/):
    municipio_para_estacao.csv — mapeamento município → estação INMET mais próxima
    (gerado uma única vez a partir das coordenadas geográficas).

Saída: data/interim/inmet_mensal.parquet
Chave: (cod_ibge, ano, mes)
Colunas: precip_min, precip_media, precip_max,
         temp_min, temp_media, temp_max,
         umid_min, umid_media, umid_max,
         pressao_media, vento_media

Observação: a modelagem aplicará lag de 30 dias sobre estas variáveis.
"""
from pathlib import Path

import pandas as pd

from arboviral.io import RAW, INTERIM, LOOKUP


def build() -> pd.DataFrame:
    """TODO: implementar agregação horária→mensal e join com lookup município↔estação."""
    raise NotImplementedError("Aguardando arquivos brutos em data/raw/inmet/")


if __name__ == "__main__":
    df = build()
    out = INTERIM / "inmet_mensal.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Wrote {len(df):,} rows to {out}")
