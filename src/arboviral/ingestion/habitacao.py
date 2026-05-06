"""
Ingestão: IBGE — aglomerados subnormais / favelas (Censos 2010 e 2022).

Arquivos em data/raw/habitacao/:
    tabela3379.xlsx  Número de aglomerados subnormais (Censo 2010)
    tabela3381.xlsx  População em aglomerados subnormais (Censo 2010)
    tabela9883.xlsx  Número de favelas e comunidades urbanas (Censo 2022)
    tabela9900.xlsx  % população em favelas e comunidades urbanas (Censo 2022)

Saída: data/interim/habitacao.parquet
Chave: cod_ibge (dado estático/censitário — sem dimensão de ano)
Colunas:
    num_aglom_subnorm_2010  int    Número de aglomerados subnormais (Censo 2010)
    num_favelas_2022        int    Número de favelas e comunidades urbanas (Censo 2022)

Municípios não listados nas tabelas = ausência de aglomerados/favelas (0 implícito).

Nota: tabela3381 e tabela9900 (variável "percentual do total geral") retornam
sempre 100 para a categoria "Total" — artefato do SIDRA em tabelas cross-tabuladas
por sexo. Não são utilizáveis como % da população municipal e foram excluídas.
Para obter a população absoluta em aglomerados/favelas, seria necessária outra
tabela SIDRA (ex.: Tabela 3382 ou consulta direta ao IBGE).
"""
import pandas as pd

from arboviral.io import INTERIM, RAW

_SP = "35"


def _ler_sidra_simples(arquivo: str, coluna: str, skiprows_extra: int = 0) -> pd.DataFrame:
    """Lê tabela SIDRA com uma única variável e um único ano.

    Estrutura: row 0-1 = título/variável, row 2 = Cód./Município/Ano,
               row 3 = NaN/ano, row 3+extra = Total (em algumas tabelas),
               row 4+extra = dados.
    """
    df_raw = pd.read_excel(RAW / "habitacao" / arquivo, header=None, engine="calamine")
    inicio = 4 + skiprows_extra
    df = df_raw.iloc[inicio:].copy().reset_index(drop=True)
    df = df.iloc[:, :3]
    df.columns = ["cod_ibge", "municipio", coluna]
    df = df.dropna(subset=["cod_ibge"])
    df = df[pd.to_numeric(df["cod_ibge"], errors="coerce").notna()]
    df["cod_ibge"] = df["cod_ibge"].astype(float).astype(int)
    df = df[df["cod_ibge"].astype(str).str.startswith(_SP)]
    df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
    return df[["cod_ibge", coluna]].reset_index(drop=True)


def _ler_pct_pop_2022() -> pd.DataFrame:
    """Lê tabela9900: % pop em favelas (Censo 2022), filtra 'Total' de grupo de idade."""
    df_raw = pd.read_excel(RAW / "habitacao" / "tabela9900.xlsx", header=None, engine="calamine")
    # row 0-1: título, row 2: Cód./Município/Grupo de idade/Ano x Sexo
    # row 3: NaN/2022, row 4: NaN/Total, row 5+: dados (colunas: cod, mun, grupo_idade, valor)
    df = df_raw.iloc[5:].copy().reset_index(drop=True)
    df = df.iloc[:, :4]
    df.columns = ["cod_ibge", "municipio", "grupo_idade", "pct_pop_favelas_2022"]
    df = df[df["grupo_idade"].astype(str).str.strip() == "Total"]
    df = df.dropna(subset=["cod_ibge"])
    df = df[pd.to_numeric(df["cod_ibge"], errors="coerce").notna()]
    df["cod_ibge"] = df["cod_ibge"].astype(float).astype(int)
    df = df[df["cod_ibge"].astype(str).str.startswith(_SP)]
    df["pct_pop_favelas_2022"] = pd.to_numeric(df["pct_pop_favelas_2022"], errors="coerce")
    return df[["cod_ibge", "pct_pop_favelas_2022"]].reset_index(drop=True)


def build() -> pd.DataFrame:
    print("  Lendo tabela3379 (num aglomerados 2010)...", flush=True)
    t3379 = _ler_sidra_simples("tabela3379.xlsx", "num_aglom_subnorm_2010")

    print("  Lendo tabela9883 (num favelas 2022)...", flush=True)
    t9883 = _ler_sidra_simples("tabela9883.xlsx", "num_favelas_2022")

    # tabela3381 (pop 2010) e tabela9900 (% pop 2022) excluídas — artefato SIDRA:
    # a variável "percentual do total geral" retorna 100 para todos na linha "Total".

    df = t3379.merge(t9883, on="cod_ibge", how="outer")
    df["cod_ibge"] = df["cod_ibge"].astype(int)
    return df.sort_values("cod_ibge").reset_index(drop=True)


if __name__ == "__main__":
    df = build()
    out = INTERIM / "habitacao.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Gravado {len(df):,} municípios em {out}")
    print(df.head())
    print("\nCompletude:")
    print(df.notna().sum().to_string())
