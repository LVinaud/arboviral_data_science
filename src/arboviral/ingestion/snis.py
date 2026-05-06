"""
Ingestão: SINISA — saneamento básico municipal (água e esgoto).

Fonte: Sistema Nacional de Informações em Saneamento Básico (SINISA).
Arquivos em data/raw/sinisa/:
    SINISA_AGUA_Indicadores_Base Municipal_{ANO}*.xlsx   → cobertura de água
    SINISA_ESGOTO_Indicadores_Base Municipal_{ANO}*.xlsx → cobertura de esgoto

Anos disponíveis: 2023, 2024.

Saída: data/interim/sinisa.parquet
Chave: (cod_ibge, ano)
Colunas (valores em %):
    atend_agua_total_pct    Atendimento da população total com rede de água
    atend_esgoto_total_pct  Atendimento da população total com rede coletora de esgoto
    atend_esgoto_trat_pct   Atendimento dos domicílios totais com coleta e tratamento de esgoto
"""
import pandas as pd

from arboviral.io import INTERIM, RAW

_SP = "35"
_SKIP = 7  # linhas de cabeçalho institucionais nos xlsx SINISA 2023
_SKIP_2024 = 8  # 2024 tem uma linha extra


def _ler_sinisa_indicadores(caminho, col_interesse: str, nome_saida: str, ano: int) -> pd.DataFrame:
    """Lê um arquivo de indicadores SINISA e extrai uma coluna de cobertura."""
    # Determina quantas linhas pular (2023 = 7, 2024 = 8)
    skip = _SKIP_2024 if "2024" in str(caminho) else _SKIP

    df_raw = pd.read_excel(caminho, engine="calamine", skiprows=skip, header=0)
    # Pula a linha de NaN e a linha de códigos de variável logo abaixo do cabeçalho
    df = df_raw.iloc[2:].copy().reset_index(drop=True)

    cod_col = next((c for c in df.columns if "ibge" in str(c).lower()), None)
    dado_col = next((c for c in df.columns if col_interesse.lower() in str(c).lower()), None)
    if cod_col is None or dado_col is None:
        return pd.DataFrame()

    out = df[[cod_col, dado_col]].copy()
    out.columns = ["cod_ibge", nome_saida]
    out = out.dropna(subset=["cod_ibge"])
    out["cod_ibge"] = out["cod_ibge"].astype(str).str.strip()
    out = out[out["cod_ibge"].str.startswith(_SP)]
    out["cod_ibge"] = out["cod_ibge"].astype(int)
    out[nome_saida] = pd.to_numeric(out[nome_saida], errors="coerce")
    out["ano"] = ano
    return out[["cod_ibge", "ano", nome_saida]].reset_index(drop=True)


def _ler_ano(ano: int) -> pd.DataFrame:
    pasta = RAW / "sinisa"
    sufixo = f"_{ano}" if ano == 2024 else f"_{ano}_V2"

    agua_glob = list(pasta.glob(f"SINISA_AGUA_Indicadores*{ano}*.xlsx"))
    esgoto_glob = list(pasta.glob(f"SINISA_ESGOTO_Indicadores*{ano}*.xlsx"))

    if not agua_glob or not esgoto_glob:
        print(f"    Arquivos SINISA {ano} não encontrados", flush=True)
        return pd.DataFrame()

    agua = _ler_sinisa_indicadores(
        agua_glob[0],
        "população total com rede de abastecimento de água",
        "atend_agua_total_pct",
        ano,
    )
    esgoto = _ler_sinisa_indicadores(
        esgoto_glob[0],
        "população total com rede coletora de esgoto",
        "atend_esgoto_total_pct",
        ano,
    )
    esgoto_trat = _ler_sinisa_indicadores(
        esgoto_glob[0],
        "domicílios totais com coleta e tratamento de esgoto",
        "atend_esgoto_trat_pct",
        ano,
    )

    df = agua.merge(esgoto, on=["cod_ibge", "ano"], how="outer")
    df = df.merge(esgoto_trat, on=["cod_ibge", "ano"], how="outer")
    return df


def build() -> pd.DataFrame:
    partes = []
    for ano in [2023, 2024]:
        print(f"  Lendo SINISA {ano}...", flush=True)
        parte = _ler_ano(ano)
        if not parte.empty:
            partes.append(parte)
            print(f"    {len(parte)} municípios SP", flush=True)

    if not partes:
        raise FileNotFoundError("Nenhum arquivo SINISA encontrado em data/raw/sinisa/")

    df = pd.concat(partes, ignore_index=True)
    return df.sort_values(["cod_ibge", "ano"]).reset_index(drop=True)


if __name__ == "__main__":
    df = build()
    out = INTERIM / "sinisa.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Gravado {len(df):,} linhas em {out}")
    print(df.head())
    print("\nCompletude por coluna:")
    print(df.notna().sum().to_string())
