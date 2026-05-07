"""
Ingestão: IBGE — densidade populacional (km² + cálculo derivado).

Fonte da área: arquivo XLS gerado por src/arboviral/scraping/ibge_areas.py
  data/raw/ibge_areas/AR_BR_RG_UF_RGINT_RGI_MUN_<ANO>.xls
  Aba 'AR_BR_MUN_<ANO>' tem CD_MUN (cód. IBGE 7 dígitos) e AR_MUN_<ANO> (km²).

Densidade é calculada combinando essa área com a populacao_estimada do
arquivo de população do IBGE (já presente em data/interim/ibge.parquet).

Saída: data/interim/densidade.parquet
Chave: cod_ibge (estático — área não muda mês a mês)

Colunas:
    area_km2          float   Área territorial em km² (IBGE 2024)
    densidade_2023    float   Habitantes / km² em 2023 (último ano IBGE)

Por que 2023? É o último ano oficial de estimativa populacional do IBGE.
Para os anos 2024-2025, o build_master.py propaga (forward-fill) o valor.
"""
from __future__ import annotations

import argparse

import pandas as pd

from arboviral.io import INTERIM, RAW

_SP = "35"


def _ler_areas(ano: int = 2024) -> pd.DataFrame:
    """Lê a aba AR_BR_MUN do arquivo XLS de áreas.

    Filtra municípios de SP (cod_ibge começa com '35').
    """
    arquivo = RAW / "ibge_areas" / f"AR_BR_RG_UF_RGINT_RGI_MUN_{ano}.xls"
    if not arquivo.exists():
        raise FileNotFoundError(
            f"{arquivo} não existe. Rode primeiro:\n"
            f"  python -m arboviral.scraping.ibge_areas --ano {ano}"
        )

    df = pd.read_excel(arquivo, sheet_name=f"AR_BR_MUN_{ano}", engine="calamine")
    df = df.dropna(subset=["CD_MUN"])
    df["cod_ibge"] = df["CD_MUN"].astype(int)
    df = df[df["cod_ibge"].astype(str).str.startswith(_SP)].copy()
    df = df.rename(columns={f"AR_MUN_{ano}": "area_km2"})
    return df[["cod_ibge", "area_km2"]].reset_index(drop=True)


def build(ano_area: int = 2024, ano_pop: int = 2023) -> pd.DataFrame:
    """Combina área (IBGE 2024) + população (último ano disponível) → densidade."""
    print(f"  Lendo áreas (IBGE {ano_area})...", flush=True)
    areas = _ler_areas(ano_area)

    print(f"  Lendo populações (IBGE {ano_pop})...", flush=True)
    ibge = pd.read_parquet(INTERIM / "ibge.parquet")
    pop = ibge[ibge["ano"] == ano_pop][["cod_ibge", "pop_estimada"]].copy()
    pop = pop.rename(columns={"pop_estimada": f"pop_{ano_pop}"})

    df = areas.merge(pop, on="cod_ibge", how="left")
    df[f"densidade_{ano_pop}"] = (df[f"pop_{ano_pop}"] / df["area_km2"]).round(2)
    return df[["cod_ibge", "area_km2", f"densidade_{ano_pop}"]].sort_values("cod_ibge").reset_index(drop=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ano-area", type=int, default=2024)
    parser.add_argument("--ano-pop", type=int, default=2023)
    args = parser.parse_args()

    df = build(args.ano_area, args.ano_pop)
    out = INTERIM / "densidade.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"\nGravado {len(df):,} linhas em {out}")
    print(df.head(10).to_string(index=False))
    print("\nEstatísticas:")
    print(df.describe().to_string())
    print(f"\nCompletude:")
    print(df.notna().sum().to_string())
