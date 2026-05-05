"""
Ingestão: IBGE MUNIC — gestão/vigilância (2018) e desastres naturais (2020/2017).

Fonte: Pesquisa de Informações Básicas Municipais (MUNIC) — IBGE.
Periodicidade: estática (uma resposta por município por edição da pesquisa).

Arquivos esperados em data/raw/munic/:
    Base_MUNIC_2018_xlsx_20201103.xlsx
    Base_MUNIC_2020.xlsx
    Base_MUNIC_2017.xlsx  (opcional, complementa desastres não cobertos em 2020)

Saída: data/interim/munic.parquet
Chave: cod_ibge
Colunas:
    Gestão e vigilância (MUNIC 2018):
        msau28_pacs, msau541_vig_sanitaria,
        msau542_vig_epidemiologica, msau543_controle_endemias
    Desastres naturais (MUNIC 2020 / 2017):
        mgrd01_seca, mgrd06_alagamento, mgrd07_erosao,
        mgrd08_enchente_gradual, mgrd11_enxurrada,
        mgrd14_deslizamento, mgrd201_mapeamento_risco

Notas:
    - As respostas originais são "Sim/Não/Não sabe/-"; converter para bool/NaN.
    - Considerar manter a coluna original como categórica quando "Não sabe" for informativo.
"""
from pathlib import Path

import pandas as pd

from arboviral.io import RAW, INTERIM


def build() -> pd.DataFrame:
    """TODO: implementar leitura das duas edições MUNIC e padronização Sim/Não → bool."""
    raise NotImplementedError("Aguardando arquivos brutos em data/raw/munic/")


if __name__ == "__main__":
    df = build()
    out = INTERIM / "munic.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Wrote {len(df):,} rows to {out}")
