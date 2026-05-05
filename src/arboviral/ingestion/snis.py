"""
Ingestão: SNIS / SINISA — saneamento e urbanização.

Fonte: Sistema Nacional de Informações sobre Saneamento (migração SNIS → SINISA).
Periodicidade: anual.
Disponibilidade: dados de 2023 liberados em 2022; 2024 e 2025 ainda não disponíveis.

Arquivos esperados em data/raw/snis/:
    SINISA_AGUASPLUVIAIS_Indicadores_AP{ANO}.xlsx
    SINISA_AGUA_*.xlsx
    SINISA_ESGOTO_*.xlsx

Saída: data/interim/snis.parquet
Chave: (cod_ibge, ano)
Colunas (todas em %):
    iag0001_atend_agua_pct:          atendimento de rede de abastecimento de água
    ies0001_atend_esgoto_pct:        atendimento de rede coletora de esgoto
    ies2004_esgoto_tratado_pct:      esgoto tratado referido ao esgoto coletado
    iap0001_vias_pavimentadas_pct:   vias públicas pavimentadas em área urbana
"""
from pathlib import Path

import pandas as pd

from arboviral.io import RAW, INTERIM


def build() -> pd.DataFrame:
    """TODO: ler as planilhas SINISA e padronizar os indicadores."""
    raise NotImplementedError("Aguardando arquivos brutos em data/raw/snis/")


if __name__ == "__main__":
    df = build()
    out = INTERIM / "snis.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Wrote {len(df):,} rows to {out}")
