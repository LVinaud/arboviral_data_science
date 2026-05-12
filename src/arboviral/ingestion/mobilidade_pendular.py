"""
Ingestão: mobilidade pendular intermunicipal para trabalho (série 2010 + 2022).

Combina duas vintages oficiais do IBGE para produzir uma série temporal
sob o esquema (cod_ibge, ano) com duas colunas:

    pendulares_entram_trabalho   Σ pessoas com residência ≠ X que trabalham em X
    pendulares_saem_trabalho     Σ pessoas residentes em X que trabalham em ≠ X

Vintages e estratégia temporal:

    CENSO 2010 — microdados da amostra (formato fixed-width).
      Permite reconstruir a matriz origem-destino ponderada pelo peso
      amostral V0010. Calculamos AMBAS as colunas (entram + saem) via
      projeção nas marginais da matriz. Vigência: anos 2015–2021.

    CENSO 2022 — SIDRA tabela 10329 (JSON via API REST).
      Agrega por município de RESIDÊNCIA com classificador "Local de
      exercício do trabalho principal" categoria "Outro município".
      Dá apenas SAÍDAS — sem destino, não dá pra calcular entradas.
      Microdados 2022 ainda não publicados em maio/2026.
      Vigência: anos 2022–2025. `entram` fica NaN nesse intervalo.

Reconstrução da matriz O-D (Censo 2010):
    Para cada registro de pessoa em SP com V0660 == 3 ("trabalha em outro
    município") e V6604 dentro dos 645 municípios paulistas, somamos o
    peso amostral V0010 ao par (cod_ibge_origem, cod_ibge_destino). As
    somas por coluna dão `entram`; as somas por linha dão `saem`. Fluxos
    com destino fora de SP (outras UFs) ou flag "país estrangeiro" são
    descartados — o modelo opera só dentro do estado.

Por que apenas trabalho e não estudo:
    Pendular para estudo é dominado por estudantes universitários e
    secundaristas, faixa etária pouco relevante como vetor adulto de
    arboviroses. Trabalho pendular concentra adultos em deslocamento
    diário regular, mecanismo mais aderente à hipótese de dispersão.

Por que não preencher `entram` em 2022+ com o valor de 2010:
    Decisão metodológica explícita: a série temporal deve respeitar a
    referência de cada vintage. Em 2022 não temos medida direta de
    entradas, então registramos NaN — o modelo trata ausência como
    informação. Preencher com 2010 seria mascarar a temporalidade.

Fontes oficiais:
    Censo 2010: https://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Resultados_Gerais_da_Amostra/Microdados/
    Censo 2022: https://sidra.ibge.gov.br/tabela/10329 (API REST)
    Data de coleta: 2026-05-12.

Variáveis dos microdados (Censo 2010, layout PESS):
    V0001  pos 1-2     UF de residência (35 = SP)
    V0002  pos 3-7     Código do município de residência (5 dígitos sem UF)
    V0010  pos 29-44   Peso amostral (16 chars; 3 inteiros + 13 decimais)
    V0660  pos 328     Local do trabalho (1=domicílio, 2=apenas neste mun,
                       3=em outro município, 4=país estrangeiro, 5=mais de
                       um município ou país)
    V6604  pos 336-342 Município de trabalho (código IBGE 7 dígitos)

Saída: data/interim/mobilidade_pendular.parquet
Chave: (cod_ibge, ano) — série temporal 2015–2025
Colunas: cod_ibge, ano, pendulares_entram_trabalho, pendulares_saem_trabalho
"""
from __future__ import annotations

import argparse
import io
import json
import zipfile
from pathlib import Path

import pandas as pd

from arboviral.io import INTERIM, RAW

PASTA_RAW = RAW / "mobilidade_pendular"
ARQUIVOS_ZIP_2010 = ["SP1.zip", "SP2_RM.zip"]
ARQUIVO_SIDRA_2022 = "sidra_10329_saidas_2022.json"
PREFIXO_PESS = "Amostra_Pessoas_"
UF_SP = "35"

# Particionamento temporal por vintage de Censo.
ANOS_MASTER = list(range(2015, 2026))   # 2015..2025
ANOS_VINTAGE_2010 = list(range(2015, 2022))  # 2015..2021
ANOS_VINTAGE_2022 = list(range(2022, 2026))  # 2022..2025

# Colspecs (start, end exclusive) em índices 0-based. Layout IBGE é 1-based,
# então pos 1-2 (V0001) vira (0, 2). Lemos tudo como string e convertemos
# manualmente para preservar zeros à esquerda e isolar a aritmética do peso.
COLSPECS = {
    "V0001": (0, 2),       # UF residência
    "V0002": (2, 7),       # município residência (5 dígitos, sem UF)
    "V0010": (28, 44),     # peso amostral (16 chars)
    "V0660": (327, 328),   # local trabalho
    "V6604": (335, 342),   # município trabalho (7 dígitos)
}

# Peso amostral é inteiro de 16 dígitos com 13 decimais implícitos (3 inteiros
# + 13 decimais, conforme layout PESS — campo V0010, INT=3 DEC=13).
# Ex.: "0090376381907530" → 9.0376381907530.
# Sanity check: soma dos pesos por todos os registros bate com pop SP 2010
# (~41 milhões) — confirmado durante validação.
PESO_DECIMAIS = 13

# Tamanho do chunk na leitura fixed-width. Mantém o consumo de RAM previsível
# (~200k linhas × 600 bytes string = ~120 MB por chunk).
CHUNK_LINHAS = 200_000


def _iter_chunks_pessoas(zip_path: Path):
    """Itera sobre chunks DataFrame com as 5 colunas-chave de cada pessoa.

    Procura, dentro do ZIP, arquivos cujo nome comece com `Amostra_Pessoas_`
    (ex.: `Amostra_Pessoas_35.txt`). Lê em chunks para limitar uso de memória.
    """
    nomes_cols = list(COLSPECS.keys())
    colspecs = list(COLSPECS.values())

    with zipfile.ZipFile(zip_path) as zf:
        nomes = [n for n in zf.namelist() if Path(n).name.startswith(PREFIXO_PESS)]
        if not nomes:
            raise FileNotFoundError(
                f"Nenhum arquivo {PREFIXO_PESS}* encontrado em {zip_path.name}"
            )
        for nome in nomes:
            print(f"    lendo {Path(nome).name} ...", flush=True)
            with zf.open(nome) as f:
                # Microdados IBGE usam latin1; decodificamos via TextIOWrapper.
                buf = io.TextIOWrapper(f, encoding="latin1", newline="")
                for chunk in pd.read_fwf(
                    buf, colspecs=colspecs, names=nomes_cols, dtype=str,
                    chunksize=CHUNK_LINHAS, header=None,
                ):
                    yield chunk


def _normalizar(df: pd.DataFrame) -> pd.DataFrame:
    """Tipa as colunas e produz `cod_ibge_origem` e `peso`.

    Filtra UF=35 já aqui — o arquivo SP2_RM nominalmente só contém SP, mas
    validar por UF não tem custo e protege contra surpresas futuras.
    """
    df = df[df["V0001"] == UF_SP].copy()
    if df.empty:
        return df

    # cod_ibge residência: UF (2 dígitos) + município (5) = 7 dígitos
    df["cod_ibge_origem"] = (df["V0001"] + df["V0002"]).astype(int)

    # Peso amostral: 16 chars; os últimos 12 representam decimais.
    df["peso"] = df["V0010"].astype("int64") / (10 ** PESO_DECIMAIS)

    # Destino: 7 dígitos como int (0 quando o campo está em branco)
    df["V6604"] = pd.to_numeric(df["V6604"], errors="coerce").fillna(0).astype("int64")
    df["V0660"] = pd.to_numeric(df["V0660"], errors="coerce").fillna(0).astype("int8")
    return df


def _coletar_fluxos(zip_paths: list[Path]) -> pd.DataFrame:
    """Concatena todos os chunks de todos os zips em um único DataFrame.

    Esperado: ~3-4 milhões de linhas para SP (10% da população de ~41 milhões
    em 2010). Cabe em RAM com folga após a redução para 4 colunas.
    """
    frames = []
    for zp in zip_paths:
        print(f"  Processando {zp.name}...", flush=True)
        for chunk in _iter_chunks_pessoas(zp):
            chunk = _normalizar(chunk)
            if chunk.empty:
                continue
            frames.append(chunk[["cod_ibge_origem", "peso", "V0660", "V6604"]])
    return pd.concat(frames, ignore_index=True)


def _agregar_pendulares(df: pd.DataFrame, mun_sp: set[int]) -> pd.DataFrame:
    """Calcula entradas e saídas de trabalho a partir da matriz O-D ponderada.

    Filtra `V0660 == 3` (trabalha em outro município) e exige destino dentro
    dos 645 municípios SP. Soma o peso amostral por par (origem, destino)
    para reconstruir a matriz; depois projeta nas marginais.
    """
    pend = df[(df["V0660"] == 3) & df["V6604"].isin(mun_sp)].copy()
    if pend.empty:
        return pd.DataFrame(columns=[
            "cod_ibge", "pendulares_entram_trabalho", "pendulares_saem_trabalho",
        ])

    od = (
        pend.groupby(["cod_ibge_origem", "V6604"], as_index=False)["peso"]
            .sum()
            .rename(columns={"V6604": "cod_ibge_destino", "peso": "fluxo"})
    )

    saem = (
        od.groupby("cod_ibge_origem", as_index=False)["fluxo"].sum()
          .rename(columns={"cod_ibge_origem": "cod_ibge",
                           "fluxo": "pendulares_saem_trabalho"})
    )
    entram = (
        od.groupby("cod_ibge_destino", as_index=False)["fluxo"].sum()
          .rename(columns={"cod_ibge_destino": "cod_ibge",
                           "fluxo": "pendulares_entram_trabalho"})
    )
    return entram.merge(saem, on="cod_ibge", how="outer")


def build_2010() -> pd.DataFrame:
    """Reconstrói matriz O-D do Censo 2010 → entram + saem por município.

    Retorna DataFrame com colunas: cod_ibge, pendulares_entram_trabalho,
    pendulares_saem_trabalho. Uma linha por município SP.
    """
    zip_paths = [PASTA_RAW / arq for arq in ARQUIVOS_ZIP_2010]
    faltando = [p.name for p in zip_paths if not p.exists()]
    if faltando:
        raise FileNotFoundError(
            f"Microdados Censo 2010 ausentes: {faltando}. Rode:\n"
            f"  python -m arboviral.scraping.mobilidade_pendular"
        )

    print("Lendo microdados Censo 2010 (~3,65 milhões de pessoas em SP)...", flush=True)
    df = _coletar_fluxos(zip_paths)
    print(f"  Registros após filtro SP: {len(df):,}", flush=True)

    mun_sp = set(df["cod_ibge_origem"].unique())
    print(f"  Municípios SP detectados na amostra: {len(mun_sp):,}", flush=True)

    print("Reconstruindo matriz O-D ponderada e agregando...", flush=True)
    out = _agregar_pendulares(df, mun_sp)

    grade = pd.DataFrame({"cod_ibge": sorted(mun_sp)})
    out = grade.merge(out, on="cod_ibge", how="left").fillna(0)
    for col in ["pendulares_entram_trabalho", "pendulares_saem_trabalho"]:
        out[col] = out[col].round().astype("int32")
    return out.sort_values("cod_ibge").reset_index(drop=True)


def build_2022_saidas() -> pd.DataFrame:
    """Lê SIDRA tabela 10329 → apenas saídas (Censo 2022).

    Retorna DataFrame: cod_ibge, pendulares_saem_trabalho. Uma linha por
    município SP. Sem entradas (a SIDRA não desagrega por destino).
    """
    arquivo = PASTA_RAW / ARQUIVO_SIDRA_2022
    if not arquivo.exists():
        raise FileNotFoundError(
            f"SIDRA 10329 ausente: {arquivo}. Rode:\n"
            f"  python -m arboviral.scraping.mobilidade_pendular"
        )

    print("Lendo SIDRA tabela 10329 (Censo 2022 — saídas pendulares)...", flush=True)
    with open(arquivo, encoding="utf-8") as f:
        data = json.load(f)

    series = data[0]["resultados"][0]["series"]
    linhas = []
    suprimidos = 0
    for s in series:
        cod = int(s["localidade"]["id"])
        valor_str = s["serie"].get("2022", "-")
        if valor_str in ("-", "...", "X"):
            suprimidos += 1
            continue
        # SIDRA usa "-" para suprimido por sigilo; "..." para não aplicável;
        # "X" para zero exato. Tratamos os três como ausência ou zero.
        linhas.append((cod, int(valor_str)))

    df = pd.DataFrame(linhas, columns=["cod_ibge", "pendulares_saem_trabalho"])
    df["pendulares_saem_trabalho"] = df["pendulares_saem_trabalho"].astype("int32")
    print(f"  Municípios com valor: {len(df):,} | suprimidos: {suprimidos:,}", flush=True)
    return df.sort_values("cod_ibge").reset_index(drop=True)


def build() -> pd.DataFrame:
    """Combina as duas vintages em série temporal (cod_ibge, ano).

    Esquema de saída:
      anos 2015–2021 → snapshot Censo 2010 (ambas as colunas preenchidas)
      anos 2022–2025 → snapshot Censo 2022 (entram=NaN, saem=SIDRA)

    Retorna DataFrame longo com 645 × 11 = 7.095 linhas.
    """
    v2010 = build_2010()
    v2022 = build_2022_saidas()

    # Grade temporal: produto cartesiano (cod_ibge × ano)
    grade = pd.MultiIndex.from_product(
        [v2010["cod_ibge"].tolist(), ANOS_MASTER],
        names=["cod_ibge", "ano"],
    ).to_frame(index=False)

    # Vintage 2010 (anos 2015–2021): merge com v2010
    parte_2010 = grade[grade["ano"].isin(ANOS_VINTAGE_2010)].merge(
        v2010, on="cod_ibge", how="left",
    )

    # Vintage 2022 (anos 2022–2025): merge com v2022; entram fica NaN
    parte_2022 = grade[grade["ano"].isin(ANOS_VINTAGE_2022)].merge(
        v2022, on="cod_ibge", how="left",
    )
    parte_2022["pendulares_entram_trabalho"] = pd.NA

    out = pd.concat([parte_2010, parte_2022], ignore_index=True)
    out = out.sort_values(["cod_ibge", "ano"]).reset_index(drop=True)
    # `pendulares_entram_trabalho` precisa ser nullable int para conviver com NA
    out["pendulares_entram_trabalho"] = out["pendulares_entram_trabalho"].astype("Int32")
    out["pendulares_saem_trabalho"] = out["pendulares_saem_trabalho"].astype("Int32")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    df = build()
    destino = INTERIM / "mobilidade_pendular.parquet"
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(destino, index=False)

    print(f"\nGravado {len(df):,} linhas em {destino}")
    print(f"Anos cobertos: {sorted(df['ano'].unique())}")
    print(f"Municípios: {df['cod_ibge'].nunique():,}")

    print("\nAmostra (São Paulo capital, 3550308):")
    print(df[df["cod_ibge"] == 3550308].to_string(index=False))

    print("\nCompletude por ano:")
    completude = df.groupby("ano").agg(
        entram_nao_nulos=("pendulares_entram_trabalho", lambda s: s.notna().sum()),
        saem_nao_nulos=("pendulares_saem_trabalho", lambda s: s.notna().sum()),
    )
    print(completude.to_string())

    print("\nComparativo 2010 vs 2022 — top 5 emissores (cidades-dormitório):")
    pivot = df.pivot_table(
        index="cod_ibge", columns="ano", values="pendulares_saem_trabalho",
    )[[2015, 2022]].rename(columns={2015: "saem_2010_vint", 2022: "saem_2022_vint"})
    pivot["delta"] = pivot["saem_2022_vint"] - pivot["saem_2010_vint"]
    print(pivot.sort_values("saem_2010_vint", ascending=False).head(10).to_string())
