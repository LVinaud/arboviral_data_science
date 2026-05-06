"""
Ingestão: Febre Amarela — Ministério da Saúde / SVS.

Fonte: Portal de Dados Abertos do MS (não está no FTP público do SINAN — febre
amarela é tratada em sistema separado por ser doença silvestre/rara).

URL: https://dadosabertos.saude.gov.br/dataset/febre-amarela-em-humanos-e-primatas-nao-humanos
Arquivo: fa_casoshumanos_1994-2025.csv

Para baixar (rodar manualmente — atualizado pela SVS de tempos em tempos):
    curl -sL "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/Febre+Amarela/fa_casoshumanos_1994-2025.csv" \\
         -o data/raw/febre_amarela/fa_casoshumanos_1994-2025.csv

Saída: data/interim/febre_amarela.parquet
Chave: (cod_ibge, ano, mes) — somente SP (UF_LPI == 'SP')

Diferenças em relação ao SINAN dengue/zika/chikungunya:
  - Município = Local Provável de Infecção (LPI), NÃO residência. Para febre
    amarela faz mais sentido porque a transmissão é predominantemente silvestre
    (mosquitos Haemagogus/Sabethes em ambiente de mata). Documentar essa
    diferença ao comparar com as outras doenças.
  - Granularidade do dado é por caso individual (CSV, não DBC), com encoding
    latin1 e separador ';'.
  - Campos disponíveis: SEXO, IDADE, DT_IS, ANO_IS, MES_IS, OBITO. Não há
    HOSPITALIZ nem CLASSI_FIN — todos os registros são casos confirmados.
  - Campo OBITO tem valores inconsistentes ('SIM', 'NÃO', 'Não', 'IGN').
    Normalizado: 'SIM' → óbito; demais → não-óbito.

Colunas geradas:
    casos    int   contagem de casos confirmados no município/mês
    obitos   int   contagem de óbitos confirmados (campo OBITO == 'SIM')
"""
import pandas as pd

from arboviral.io import INTERIM, LOOKUP, RAW

_SP = "SP"
_ARQUIVO = "fa_casoshumanos_1994-2025.csv"


def _lookup_6d_para_7d() -> dict[str, int]:
    """Mapeia código IBGE 6 dígitos (DATASUS) → 7 dígitos (oficial)."""
    df = pd.read_excel(LOOKUP / "municipios_sp_estacoes_inmet.xlsx", engine="calamine")
    return {str(int(v))[:-1]: int(v) for v in df["Código Município Completo"].dropna().astype(int)}


def build() -> pd.DataFrame:
    print(f"  Lendo {_ARQUIVO}...", flush=True)
    df = pd.read_csv(RAW / "febre_amarela" / _ARQUIVO, encoding="latin1", sep=";")

    df = df[df["UF_LPI"] == _SP].copy()
    df["ano"] = pd.to_numeric(df["ANO_IS"], errors="coerce").astype("Int64")
    df["mes"] = pd.to_numeric(df["MES_IS"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["ano", "mes", "COD_MUN_LPI"])

    lookup = _lookup_6d_para_7d()
    df["cod_ibge"] = df["COD_MUN_LPI"].astype(int).astype(str).str.zfill(6).map(lookup)
    df = df.dropna(subset=["cod_ibge"])
    df["cod_ibge"] = df["cod_ibge"].astype(int)

    df["obito_flag"] = df["OBITO"].astype(str).str.strip().str.upper().eq("SIM").astype(int)

    agg = (df.groupby(["cod_ibge", "ano", "mes"])
             .agg(casos=("ID", "count"), obitos=("obito_flag", "sum"))
             .reset_index())
    agg["ano"] = agg["ano"].astype(int)
    agg["mes"] = agg["mes"].astype(int)
    return agg.sort_values(["cod_ibge", "ano", "mes"]).reset_index(drop=True)


if __name__ == "__main__":
    df = build()
    out = INTERIM / "febre_amarela.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Gravado {len(df):,} linhas em {out}")
    print(f"\nAnos cobertos: {sorted(df['ano'].unique())}")
    print(f"Municípios SP com casos: {df['cod_ibge'].nunique()}")
    print(f"Total casos: {df['casos'].sum():,}")
    print(f"Total óbitos: {df['obitos'].sum():,}")
    print("\nCasos por ano:")
    print(df.groupby("ano")[["casos", "obitos"]].sum().to_string())
