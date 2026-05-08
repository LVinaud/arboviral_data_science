"""
Ingestão: MapBiomas Brasil — cobertura/uso da terra por município (Coleção 10.1).

Fonte raw: data/raw/mapbiomas/MAPBIOMAS_COVERAGE_COL_10_1.xlsx
  (baixado por src/arboviral/scraping/mapbiomas.py)

Estrutura do raw:
  Aba COVERAGE_10.1 — colunas:
    - state_acronym, municipality, class_level_1, ...
    - colunas anuais 1985..2024 com área em hectares

Processamento:
  1. Filtrar SP (state_acronym == 'SP')
  2. Agregar por (município, classe_nível_1, ano) — soma sobre subclasses
  3. Calcular % de cobertura por classe (área_classe / área_total_município)
  4. Match município nome → cod_ibge via lookup
  5. Wide format: 1 linha por (cod_ibge, ano), 5 colunas de % cobertura

Saída: data/interim/mapbiomas.parquet
Chave: (cod_ibge, ano)  — anual

Colunas de saída:
    pct_floresta             % de área com floresta natural
    pct_agricultura          % de área com agropecuária (pastagem + lavoura + silvicultura)
    pct_nao_vegetado         % de área urbanizada / não vegetada (cidades, infraestrutura, mineração)
    pct_agua                 % de água / ambiente marinho
    pct_natural_nao_florestal % de formação natural não florestal (cerrado aberto, campos, etc.)

Justificativa epidemiológica:
  - Áreas urbanas favorecem Aedes aegypti (vetor urbano de dengue/zika/chikungunya)
  - Áreas de mata fechada favorecem Haemagogus/Sabethes (vetores silvestres de febre amarela)
  - Pastagem e agricultura modificam o habitat e a interface humano-vetor
"""
from __future__ import annotations

import pandas as pd

from arboviral.io import INTERIM, LOOKUP, RAW

_NOME_ARQUIVO = "MAPBIOMAS_COVERAGE_COL_10_1.xlsx"
_CLASSES = {
    "1. Forest":                          "pct_floresta",
    "2. Non Forest Natural Formation":    "pct_natural_nao_florestal",
    "3. Farming":                         "pct_agricultura",
    "4. Non vegetated area":              "pct_nao_vegetado",
    "5. Water and Marine Environment":    "pct_agua",
}
_ANOS_ALVO = list(range(2015, 2025))  # MapBiomas vai até 2024


def _carregar_lookup_municipios() -> dict[str, int]:
    """Mapeia nome do município (lowercase, sem acento, sem espaços extras) → cod_ibge."""
    import unicodedata
    df = pd.read_excel(LOOKUP / "municipios_sp_estacoes_inmet.xlsx", engine="calamine")
    df = df.rename(columns={
        "Código Município Completo": "cod_ibge",
        "Nome_Município": "nome",
    })

    def normalizar(s: str) -> str:
        s = str(s).strip().lower()
        s = unicodedata.normalize("NFD", s)
        s = "".join(c for c in s if unicodedata.category(c) != "Mn")
        return s

    return {normalizar(n): int(c) for n, c in zip(df["nome"], df["cod_ibge"])}


def build() -> pd.DataFrame:
    print(f"  Lendo {_NOME_ARQUIVO}...", flush=True)
    df = pd.read_excel(RAW / "mapbiomas" / _NOME_ARQUIVO,
                       sheet_name="COVERAGE_10.1", engine="calamine")

    # Filtrar SP e classes principais (level_1)
    df = df[df["state_acronym"] == "SP"].copy()
    df = df[df["class_level_1"].isin(_CLASSES.keys())].copy()

    print(f"  SP: {df['municipality'].nunique()} municípios, {len(df)} linhas", flush=True)

    # Agregar por (município, class_level_1) somando todas as subclasses
    cols_anos = [c for c in df.columns if isinstance(c, int) and c in _ANOS_ALVO]
    df_agg = df.groupby(["municipality", "class_level_1"], as_index=False)[cols_anos].sum()

    # Wide → long: 1 linha por (município, classe, ano)
    df_long = df_agg.melt(
        id_vars=["municipality", "class_level_1"],
        value_vars=cols_anos,
        var_name="ano",
        value_name="hectares",
    )
    df_long["classe"] = df_long["class_level_1"].map(_CLASSES)

    # Pivot para classes virarem colunas
    df_wide = df_long.pivot_table(
        index=["municipality", "ano"],
        columns="classe",
        values="hectares",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    # Garantir todas as 5 colunas de classe (alguns municípios podem não ter alguma)
    for col in _CLASSES.values():
        if col not in df_wide.columns:
            df_wide[col] = 0.0

    # Calcular percentuais (cada classe / total)
    cols_pct = list(_CLASSES.values())
    df_wide["area_total_ha"] = df_wide[cols_pct].sum(axis=1)
    for col in cols_pct:
        df_wide[col] = (df_wide[col] / df_wide["area_total_ha"] * 100).round(2)
    df_wide = df_wide.drop(columns=["area_total_ha"])

    # Match município → cod_ibge via lookup
    import unicodedata
    def normalizar(s: str) -> str:
        s = str(s).strip().lower()
        s = unicodedata.normalize("NFD", s)
        s = "".join(c for c in s if unicodedata.category(c) != "Mn")
        return s

    lookup = _carregar_lookup_municipios()
    df_wide["cod_ibge"] = df_wide["municipality"].apply(
        lambda n: lookup.get(normalizar(n))
    )

    n_sem_match = df_wide["cod_ibge"].isna().sum()
    if n_sem_match:
        municipios_sem = df_wide[df_wide["cod_ibge"].isna()]["municipality"].unique()
        print(f"  ⚠ {n_sem_match} linhas sem match no lookup IBGE "
              f"({len(municipios_sem)} municípios distintos)", flush=True)
        print(f"     Primeiros sem match: {list(municipios_sem)[:5]}", flush=True)
    df_wide = df_wide.dropna(subset=["cod_ibge"]).copy()
    df_wide["cod_ibge"] = df_wide["cod_ibge"].astype(int)
    df_wide["ano"] = df_wide["ano"].astype(int)

    cols_finais = ["cod_ibge", "ano"] + cols_pct
    return df_wide[cols_finais].sort_values(["cod_ibge", "ano"]).reset_index(drop=True)


if __name__ == "__main__":
    df = build()
    out = INTERIM / "mapbiomas.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"\nGravado {len(df):,} linhas em {out}")
    print(f"Municípios cobertos: {df['cod_ibge'].nunique()}")
    print(f"Anos: {sorted(df['ano'].unique())}")
    print(f"\nAmostra (São Paulo capital, código 3550308):")
    print(df[df["cod_ibge"] == 3550308].to_string(index=False))
    print(f"\nEstatísticas (média estadual):")
    cols_pct = [c for c in df.columns if c.startswith("pct_")]
    print(df[cols_pct].describe().round(2).to_string())
