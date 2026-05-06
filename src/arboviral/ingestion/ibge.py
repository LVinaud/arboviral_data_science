"""
Ingestão: IBGE — PIB municipal, população estimada e GINI.

Arquivos em data/raw/ibge/:
    tabela5938.xlsx  PIB municipal a preços correntes (Mil Reais), 2002-2023
    tabela6579.xlsx  Estimativas populacionais, 2001-2025 (com lacunas)
    ginibr.xlsx      Índice de Gini da renda domiciliar per capita, 1991/2000/2010

PIB per capita = (pib_mil_reais × 1000) / pop_estimada
    Calculado para cada (cod_ibge, ano) com população propagada para anos sem estimativa.

GINI: dado censitário (1991, 2000, 2010). Valor de 2010 usado como variável estática.

Saída: data/interim/ibge.parquet
Chave: (cod_ibge, ano)
Colunas:
    pop_estimada    int     Estimativa populacional do município no ano
    pib_mil_reais   float   PIB a preços correntes (Mil R$)
    pib_per_capita  float   PIB per capita (R$)
    gini_2010       float   Índice de Gini (Censo 2010)
"""
import pandas as pd

from arboviral.io import INTERIM, LOOKUP, RAW

_SP = "35"


def _ler_tabela_sidra(arquivo: str, coluna: str) -> pd.DataFrame:
    """Lê tabela SIDRA no formato wide exportado pelo IBGE.

    Estrutura:
        row 0-1: metadados
        row 2:   'Cód.', 'Município', 'Ano'
        row 3:   NaN, NaN, ano1, ano2, ...
        row 4+:  dados (cod_ibge_7d, nome, val_ano1, val_ano2, ...)
    """
    df_raw = pd.read_excel(RAW / "ibge" / arquivo, header=None, engine="calamine")
    anos = [int(float(v)) for v in df_raw.iloc[3, 2:].dropna()]
    df = df_raw.iloc[4:, : 2 + len(anos)].copy().reset_index(drop=True)
    df.columns = ["cod_ibge", "municipio"] + anos
    df = df.dropna(subset=["cod_ibge"])
    df = df[pd.to_numeric(df["cod_ibge"], errors="coerce").notna()]
    df["cod_ibge"] = df["cod_ibge"].astype(float).astype(int)
    df = df[df["cod_ibge"].astype(str).str.startswith(_SP)]
    df = df.melt(id_vars=["cod_ibge"], value_vars=anos, var_name="ano", value_name=coluna)
    df["ano"] = df["ano"].astype(int)
    return df.dropna(subset=[coluna]).reset_index(drop=True)


def _ler_gini() -> pd.DataFrame:
    """Retorna GINI 2010 para municípios SP (cod_ibge 7 dígitos via lookup 6→7)."""
    lookup_df = pd.read_excel(str(LOOKUP / "municipios_sp_estacoes_inmet.xlsx"), engine="calamine")
    lookup = {
        str(int(v))[:-1]: int(v)
        for v in lookup_df["Código Município Completo"].dropna().astype(int)
    }

    df_raw = pd.read_excel(RAW / "ibge" / "ginibr.xlsx", header=None, engine="calamine")
    # row 2 = header: 'Município', 1991, 2000, 2010
    df = df_raw.iloc[3:].copy()
    df.columns = df_raw.iloc[2].tolist()
    df = df.dropna(subset=["Município"])
    df["cod6"] = df["Município"].astype(str).str[:6].str.strip()
    df["cod_ibge"] = df["cod6"].map(lookup)
    df = df.dropna(subset=["cod_ibge"])
    df["cod_ibge"] = df["cod_ibge"].astype(int)
    col2010 = [c for c in df.columns if str(c).startswith("2010")][0]
    return df[["cod_ibge", col2010]].rename(columns={col2010: "gini_2010"}).reset_index(drop=True)


def build() -> pd.DataFrame:
    print("  Lendo PIB (tabela5938)...", flush=True)
    pib = _ler_tabela_sidra("tabela5938.xlsx", "pib_mil_reais")

    print("  Lendo população (tabela6579)...", flush=True)
    pop = _ler_tabela_sidra("tabela6579.xlsx", "pop_estimada")
    pop["pop_estimada"] = pop["pop_estimada"].astype(int)

    print("  Lendo GINI...", flush=True)
    gini = _ler_gini()

    # Grade municípios × anos do PIB
    anos_pib = sorted(pib["ano"].unique())
    municipios = sorted(pib["cod_ibge"].unique())
    grade = pd.MultiIndex.from_product([municipios, anos_pib], names=["cod_ibge", "ano"])
    df = pd.DataFrame(index=grade).reset_index()
    df = df.merge(pib, on=["cod_ibge", "ano"], how="left")
    df = df.merge(pop, on=["cod_ibge", "ano"], how="left")

    # Para anos sem estimativa pop, propagar o mais próximo disponível
    df = df.sort_values(["cod_ibge", "ano"])
    df["pop_estimada"] = df.groupby("cod_ibge")["pop_estimada"].ffill().bfill()

    df["pib_mil_reais"] = pd.to_numeric(df["pib_mil_reais"], errors="coerce")
    df["pop_estimada"] = pd.to_numeric(df["pop_estimada"], errors="coerce")
    df["pib_per_capita"] = (df["pib_mil_reais"] * 1000 / df["pop_estimada"]).round(2)
    df = df.merge(gini, on="cod_ibge", how="left")
    return df.sort_values(["cod_ibge", "ano"]).reset_index(drop=True)


if __name__ == "__main__":
    df = build()
    out = INTERIM / "ibge.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Gravado {len(df):,} linhas em {out}")
    print(df.head())
    print("\nCompletude:")
    print(df.notna().sum().to_string())
