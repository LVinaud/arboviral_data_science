"""
Ingestão: DATASUS — capacidade da rede pública de saúde por município SP.

Fontes via FTP DATASUS:
    CNES/LT — Leitos hospitalares (mensal)
        ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados/LT/LTSP{YYMM}.dbc
    SIM/DORES — Sistema de Informações sobre Mortalidade (anual)
        ftp://ftp.datasus.gov.br/dissemin/publicos/SIM/CID10/DORES/DOSP{YYYY}.dbc

Arquivos esperados em data/raw/saude/:
    LTSP{YYMM}.dbc   — um por mês, 2015–presente
    DOSP{YYYY}.dbc   — um por ano, 2015–presente

Saída: data/interim/saude.parquet
Chave: (cod_ibge, ano, mes)
Colunas:
    leitos_sus:          total de leitos SUS (QT_SUS) por município-mês
    mortalidade_materna: óbitos maternos (CID O00-O99) por 100 mil nascidos vivos,
                         calculado anualmente e repetido nos 12 meses

Sobre mortalidade materna:
    Calculada como (óbitos O00-O99 / nascidos vivos estimados) * 100.000.
    Os nascidos vivos são obtidos do SINASC — placeholder por ora (retornamos
    a contagem bruta de óbitos maternos até integrá-los).

Nota: médicos por município não estão disponíveis de forma agregada nos arquivos LT.
    A fonte correta seria CNES/PF (Profissionais), mas os arquivos são muito grandes
    (>70 MB/mês). Implementar sob demanda quando necessário.
"""
import re
from pathlib import Path

import dbfread
import pandas as pd
from pyreaddbc import dbc2dbf

from arboviral.io import INTERIM, RAW

# CIDs de mortalidade materna (capítulo XV do CID-10: O00–O99)
_CID_MATERNO = re.compile(r"^O\d{2}")


def _dbc_para_df(caminho_dbc: Path, filtrar_uf_col: str | None = None,
                 filtrar_uf_val: str = "35") -> pd.DataFrame:
    caminho_dbf = caminho_dbc.with_suffix(".dbf")
    try:
        dbc2dbf(str(caminho_dbc), str(caminho_dbf))
        table = dbfread.DBF(str(caminho_dbf), load=False, encoding="latin1")
        if filtrar_uf_col:
            registros = [r for r in table if str(r.get(filtrar_uf_col, "")).strip()[:2] == filtrar_uf_val]
        else:
            registros = list(table)
        return pd.DataFrame(registros) if registros else pd.DataFrame()
    finally:
        caminho_dbf.unlink(missing_ok=True)


def _lookup_6d_para_7d() -> dict[str, int]:
    from arboviral.io import LOOKUP
    xl = LOOKUP / "municipios_sp_estacoes_inmet.xlsx"
    df = pd.read_excel(xl)
    return {str(int(v))[:-1]: int(v) for v in df["Código Município Completo"].dropna().astype(int)}


def _construir_leitos(pasta: Path) -> pd.DataFrame:
    """Agrega leitos SUS por município-mês a partir dos arquivos LTSP{YYMM}.dbc."""
    lookup = _lookup_6d_para_7d()
    partes = []

    for arq in sorted(pasta.glob("LTSP*.dbc")):
        m = re.match(r"LTSP(\d{2})(\d{2})\.dbc", arq.name, re.I)
        if not m:
            continue
        yy, mm = int(m.group(1)), int(m.group(2))
        ano = yy + (2000 if yy < 50 else 1900)
        if not 2015 <= ano <= 2026:
            continue

        print(f"  {arq.name}...", end=" ", flush=True)
        df = _dbc_para_df(arq)
        if df.empty:
            print("vazio")
            continue

        df["cod_ibge_6d"] = df["CODUFMUN"].astype(str).str.strip().str.zfill(6)
        df["cod_ibge"] = df["cod_ibge_6d"].map(lookup)
        df = df.dropna(subset=["cod_ibge"])
        df["cod_ibge"] = df["cod_ibge"].astype(int)
        df["ano"] = ano
        df["mes"] = mm
        df["qt_sus"] = pd.to_numeric(df["QT_SUS"], errors="coerce").fillna(0).astype(int)

        agg = df.groupby(["cod_ibge", "ano", "mes"])["qt_sus"].sum().reset_index()
        agg.columns = ["cod_ibge", "ano", "mes", "leitos_sus"]
        partes.append(agg)
        print(f"{len(agg)} municípios")

    if not partes:
        raise FileNotFoundError("Nenhum arquivo LTSP*.dbc em data/raw/saude/")
    return pd.concat(partes, ignore_index=True).sort_values(["cod_ibge", "ano", "mes"]).reset_index(drop=True)


def _construir_mortalidade_materna(pasta: Path) -> pd.DataFrame:
    """Conta óbitos maternos (O00-O99) por município-ano a partir dos arquivos DOSP{YYYY}.dbc."""
    lookup = _lookup_6d_para_7d()
    partes = []

    for arq in sorted(pasta.glob("DOSP*.dbc")):
        m = re.match(r"DOSP(\d{4})\.dbc", arq.name, re.I)
        if not m:
            continue
        ano = int(m.group(1))
        if not 2015 <= ano <= 2026:
            continue

        print(f"  {arq.name}...", end=" ", flush=True)
        # Filtrar por município de residência em SP (cod começa com 35)
        df = _dbc_para_df(arq, filtrar_uf_col="CODMUNRES", filtrar_uf_val="35")
        if df.empty:
            print("vazio")
            continue

        # Selecionar apenas óbitos maternos
        df["mat"] = df["CAUSABAS"].astype(str).str.strip().str.upper().map(
            lambda c: bool(_CID_MATERNO.match(c))
        ).astype(int)

        df["cod_ibge_6d"] = df["CODMUNRES"].astype(str).str.strip().str.zfill(6)
        df["cod_ibge"] = df["cod_ibge_6d"].map(lookup)
        df = df.dropna(subset=["cod_ibge"])
        df["cod_ibge"] = df["cod_ibge"].astype(int)
        df["ano"] = ano

        agg = df.groupby(["cod_ibge", "ano"])["mat"].sum().reset_index()
        agg.columns = ["cod_ibge", "ano", "obitos_maternos"]
        partes.append(agg)
        print(f"{agg['obitos_maternos'].sum()} óbitos maternos")

    if not partes:
        raise FileNotFoundError("Nenhum arquivo DOSP*.dbc em data/raw/saude/")

    anual = pd.concat(partes, ignore_index=True)
    # Replicar para todos os 12 meses (variável anual)
    meses = pd.DataFrame({"mes": range(1, 13)})
    return (
        anual.merge(meses, how="cross")
        .sort_values(["cod_ibge", "ano", "mes"])
        .reset_index(drop=True)
    )


def build() -> pd.DataFrame:
    """Constrói saude.parquet: leitos SUS + mortalidade materna."""
    pasta = RAW / "saude"

    print("Processando leitos (CNES/LT)...")
    df_leitos = _construir_leitos(pasta)

    print("\nProcessando mortalidade materna (SIM)...")
    df_mortalidade = _construir_mortalidade_materna(pasta)

    resultado = df_leitos.merge(df_mortalidade, on=["cod_ibge", "ano", "mes"], how="outer")
    return resultado.sort_values(["cod_ibge", "ano", "mes"]).reset_index(drop=True)


if __name__ == "__main__":
    df = build()
    out = INTERIM / "saude.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"\nGravado {len(df):,} linhas em {out}")
    print(df.head())
