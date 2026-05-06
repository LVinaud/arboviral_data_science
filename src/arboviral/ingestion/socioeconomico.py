"""
Ingestão: indicadores socioeconômicos municipais — IDH-M e CAPAG.

Fontes:
    IDH-M:  Atlas do Desenvolvimento Humano no Brasil (PNUD)
            data/raw/idhm/IDHM_{1991,2000,2010}.csv
            Dado censitário; valor de 2010 usado como variável estática.

    CAPAG:  Sistema do Tesouro Nacional — Capacidade de Pagamento dos municípios
            data/raw/capag/capag-*.xlsx / capag_*.xlsx (2018–2025)
            Periodicidade: anual. Classificação {A, B, C, D}.

Saída: data/interim/socioeconomico.parquet
Chave: (cod_ibge, ano) para CAPAG; idhm_2010 é estático (mesmo valor todos os anos)
Colunas:
    idhm_2010   float   IDH-M do Censo 2010
    capag       str     Nota CAPAG do ano (A/B/C/D, ou NaN se não disponível)
"""
import re

import pandas as pd

from arboviral.io import INTERIM, RAW

_SP = "35"


def _ler_idhm() -> pd.DataFrame:
    """IDH-M 2010 por município SP (cod_ibge 7 dígitos direto nos CSVs)."""
    df = pd.read_csv(RAW / "idhm" / "IDHM_2010.csv")
    df = df[df["codigo_ibge"].astype(str).str.startswith(_SP)]
    df = df[df["sigla"] == "IDHM"][["codigo_ibge", "variavel_valor"]]
    df.columns = ["cod_ibge", "idhm_2010"]
    df["cod_ibge"] = df["cod_ibge"].astype(int)
    return df.reset_index(drop=True)


def _ano_do_arquivo(nome: str) -> int:
    """Extrai o ano do nome do arquivo CAPAG."""
    anos = re.findall(r"20\d{2}", nome)
    return max(int(a) for a in anos)


def _ler_capag_arquivo(caminho, ano: int) -> pd.DataFrame:
    """Lê um arquivo CAPAG e retorna (cod_ibge, ano, capag) para municípios SP."""
    df_raw = pd.read_excel(caminho, header=None, engine="calamine")

    # Encontrar a linha de cabeçalho (contém alguma variação de 'ibge' ou 'municip')
    header_row = None
    for i in range(min(10, len(df_raw))):
        row = df_raw.iloc[i].astype(str).str.lower().tolist()
        if any("ibge" in v or "município" in v or "municipio" in v for v in row):
            header_row = i
            break
    if header_row is None:
        return pd.DataFrame()

    df = pd.read_excel(caminho, header=header_row, engine="calamine")

    # Coluna de código IBGE
    cod_col = next(
        (c for c in df.columns if "ibge" in str(c).lower() or "cód" in str(c).lower() or "cod" in str(c).lower()),
        None,
    )
    # Coluna de nota CAPAG (varia por arquivo)
    capag_col = next(
        (c for c in df.columns if "capag" in str(c).lower() or "classif" in str(c).lower()),
        None,
    )
    if cod_col is None or capag_col is None:
        return pd.DataFrame()

    df = df[[cod_col, capag_col]].copy()
    df.columns = ["cod_ibge", "capag"]
    df = df.dropna(subset=["cod_ibge"])
    df["cod_ibge"] = df["cod_ibge"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    df = df[df["cod_ibge"].str.startswith(_SP)]
    df["cod_ibge"] = df["cod_ibge"].astype(int)
    df["capag"] = df["capag"].astype(str).str.strip().str.upper()
    df = df[df["capag"].isin(["A", "B", "C", "D"])]
    df["ano"] = ano
    return df[["cod_ibge", "ano", "capag"]].reset_index(drop=True)


def _ler_capag() -> pd.DataFrame:
    arquivos = sorted((RAW / "capag").glob("*.xlsx"))
    partes = []
    for arq in arquivos:
        ano = _ano_do_arquivo(arq.name)
        parte = _ler_capag_arquivo(arq, ano)
        if not parte.empty:
            partes.append(parte)
            print(f"    {arq.name} → {len(parte)} municípios SP, ano {ano}", flush=True)
    if not partes:
        return pd.DataFrame(columns=["cod_ibge", "ano", "capag"])
    return pd.concat(partes, ignore_index=True)


def build() -> pd.DataFrame:
    print("  Lendo IDH-M 2010...", flush=True)
    idhm = _ler_idhm()
    print(f"    {len(idhm)} municípios SP com IDH-M", flush=True)

    print("  Lendo CAPAG (todos os anos)...", flush=True)
    capag = _ler_capag()

    # Juntar: CAPAG já é (cod_ibge, ano); IDH-M é estático → join por cod_ibge
    df = capag.merge(idhm, on="cod_ibge", how="outer")
    return df.sort_values(["cod_ibge", "ano"]).reset_index(drop=True)


if __name__ == "__main__":
    df = build()
    out = INTERIM / "socioeconomico.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Gravado {len(df):,} linhas em {out}")
    print(df.head())
    print("\nCompletude:")
    print(df.notna().sum().to_string())
    print("\nCAPAG por ano:")
    print(df.groupby("ano")["capag"].value_counts().to_string())
