"""
Ingestão: IBGE — aglomerados subnormais / favelas (Censos 2010 e 2022).

Arquivos em data/raw/habitacao/:
    tabela3379.xlsx  Número de aglomerados subnormais (Censo 2010)
    tabela3381.xlsx  População em aglomerados subnormais (Censo 2010)
    tabela9883.xlsx  Número de favelas e comunidades urbanas (Censo 2022)
    tabela9900.xlsx  População em favelas e comunidades urbanas (Censo 2022)

Saída: data/interim/habitacao.parquet
Chave: cod_ibge (dado estático/censitário — sem dimensão de ano)
Colunas:
    num_aglom_subnorm_2010  int    Número de aglomerados subnormais (Censo 2010)
    pop_aglom_subnorm_2010  int    População em aglomerados subnormais (Censo 2010)
    num_favelas_2022        int    Número de favelas e comunidades urbanas (Censo 2022)
    pop_favelas_2022        int    População em favelas e comunidades urbanas (Censo 2022)

Municípios não listados nas tabelas = ausência de aglomerados/favelas (0 implícito).

Nota: tabela3381 e tabela9900 têm estrutura SIDRA com cruzamento por sexo
(Total / Masculino / Feminino). Filtramos apenas a linha "Total" da coluna
"Ano x Sexo" (row 4) para obter o total geral. Traço "-" = município sem
aglomerados/favelas, tratado como NaN (0 implícito no merge).
"""
import pandas as pd

from arboviral.io import INTERIM, RAW

_SP = "35"


def _ler_sidra_simples(arquivo: str, coluna: str) -> pd.DataFrame:
    """Lê tabela SIDRA com uma variável, um ano e sem cruzamento por faixa etária.

    Estrutura: row 0-1 = título/variável, row 2 = Cód./Município/Ano x Sexo,
               row 3 = ano, row 4 = "Total" (cabeçalho da coluna de sexo),
               row 5+ = dados.
    """
    df_raw = pd.read_excel(RAW / "habitacao" / arquivo, header=None, engine="calamine")
    df = df_raw.iloc[5:].copy().reset_index(drop=True)
    df = df.iloc[:, :3]
    df.columns = ["cod_ibge", "municipio", coluna]
    df = df.dropna(subset=["cod_ibge"])
    df = df[pd.to_numeric(df["cod_ibge"], errors="coerce").notna()]
    df["cod_ibge"] = df["cod_ibge"].astype(float).astype(int)
    df = df[df["cod_ibge"].astype(str).str.startswith(_SP)]
    df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
    return df[["cod_ibge", coluna]].reset_index(drop=True)


def _ler_sidra_com_grupo_idade(arquivo: str, coluna: str) -> pd.DataFrame:
    """Lê tabela SIDRA com cruzamento por grupo de idade e sexo.

    Estrutura: row 0-1 = título/variável, row 2 = Cód./Município/Grupo de idade/Ano x Sexo,
               row 3 = ano, row 4 = "Total" (cabeçalho de sexo),
               row 5+ = dados (4 colunas: cod, mun, grupo_idade, valor).
    Filtra grupo_idade == "Total" para obter o total geral.
    Traço "-" = município sem aglomerados → NaN.
    """
    df_raw = pd.read_excel(RAW / "habitacao" / arquivo, header=None, engine="calamine")
    df = df_raw.iloc[5:].copy().reset_index(drop=True)
    df = df.iloc[:, :4]
    df.columns = ["cod_ibge", "municipio", "grupo_idade", coluna]
    df = df[df["grupo_idade"].astype(str).str.strip() == "Total"]
    df = df.dropna(subset=["cod_ibge"])
    df = df[pd.to_numeric(df["cod_ibge"], errors="coerce").notna()]
    df["cod_ibge"] = df["cod_ibge"].astype(float).astype(int)
    df = df[df["cod_ibge"].astype(str).str.startswith(_SP)]
    df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
    return df[["cod_ibge", coluna]].reset_index(drop=True)


def build() -> pd.DataFrame:
    print("  Lendo tabela3379 (num aglomerados 2010)...", flush=True)
    t3379 = _ler_sidra_simples("tabela3379.xlsx", "num_aglom_subnorm_2010")

    print("  Lendo tabela3381 (pop aglomerados 2010)...", flush=True)
    t3381 = _ler_sidra_simples("tabela3381.xlsx", "pop_aglom_subnorm_2010")

    print("  Lendo tabela9883 (num favelas 2022)...", flush=True)
    t9883 = _ler_sidra_simples("tabela9883.xlsx", "num_favelas_2022")

    print("  Lendo tabela9900 (pop favelas 2022)...", flush=True)
    t9900 = _ler_sidra_com_grupo_idade("tabela9900.xlsx", "pop_favelas_2022")

    df = t3379.merge(t3381, on="cod_ibge", how="outer")
    df = df.merge(t9883, on="cod_ibge", how="outer")
    df = df.merge(t9900, on="cod_ibge", how="outer")
    df["cod_ibge"] = df["cod_ibge"].astype(int)
    return df.sort_values("cod_ibge").reset_index(drop=True)


if __name__ == "__main__":
    df = build()
    out = INTERIM / "habitacao.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Gravado {len(df):,} municípios em {out}")
    print(df.head(10).to_string())
    print("\nCompletude:")
    print(df.notna().sum().to_string())
    print("\nEstatísticas:")
    print(df.describe().to_string())
