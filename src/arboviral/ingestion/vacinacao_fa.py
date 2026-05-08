"""
Ingestão: cobertura vacinal de febre amarela (PNI/DATASUS).

Fonte: data/raw/febre_amarela/COB_VAC_FA.csv (formato inteli.gente:
codigo_ibge, sigla, ano, variavel_valor). Detalhes da coleta em
src/arboviral/scraping/pni_febre_amarela.py.

Saída: data/interim/vacinacao_fa.parquet
Chave: (cod_ibge, ano) — anual, propagado a 12 meses no build_master.

Tratamentos aplicados:
  - Filtra SP (codigo_ibge com prefixo '35'); CSV é nacional.
  - Mantém valores >100% sem cap (denominador-alvo do PNI fica abaixo do
    real em cenários de migração / estimativa defasada — informativo).
  - Não preenche gaps aqui; ffill é feito em build_master para preservar a
    natureza dos dados originais no parquet intermediário.

Coluna gerada:
    cob_vac_fa_pct  float  cobertura vacinal contra febre amarela (%)
"""
import pandas as pd

from arboviral.io import INTERIM, RAW

_UF_SP = "35"
_ARQUIVO = "COB_VAC_FA.csv"


def build() -> pd.DataFrame:
    print(f"  Lendo {_ARQUIVO}...", flush=True)
    df = pd.read_csv(RAW / "febre_amarela" / _ARQUIVO)

    df["cod_ibge"] = df["codigo_ibge"].astype(int)
    df = df[df["cod_ibge"].astype(str).str.startswith(_UF_SP)].copy()
    df["ano"] = df["ano"].astype(int)
    df = df.rename(columns={"variavel_valor": "cob_vac_fa_pct"})

    out = (df[["cod_ibge", "ano", "cob_vac_fa_pct"]]
           .drop_duplicates(subset=["cod_ibge", "ano"], keep="last")
           .sort_values(["cod_ibge", "ano"])
           .reset_index(drop=True))
    return out


if __name__ == "__main__":
    df = build()
    out = INTERIM / "vacinacao_fa.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Gravado {len(df):,} linhas em {out}")
    print(f"\nMunicípios SP: {df['cod_ibge'].nunique()}")
    print(f"Anos cobertos: {sorted(df['ano'].unique())}")
    print("\nDistribuição da cobertura (% da pop-alvo):")
    print(df["cob_vac_fa_pct"].describe().round(2).to_string())
    print("\nMediana SP por ano:")
    print(df.groupby("ano")["cob_vac_fa_pct"].median().round(2).to_string())
