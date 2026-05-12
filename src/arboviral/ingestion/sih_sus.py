"""
Ingestão: SIH-SUS — internações por arboviroses (AIH-RD).

Lê arquivos `data/raw/sih_sus/RDSP{AAMM}.dbc` baixados por
`src/arboviral/scraping/sih_sus.py` e agrega para cada
(município de residência, ano, mês de internação) o total de internações
hospitalares pelo SUS classificadas como arbovirose pelo CID-10 do
diagnóstico principal:

    sih_internacoes_dengue          CID A90 (clássico) + A91 (grave/hemorrágico)
    sih_internacoes_chikungunya     CID A92.0
    sih_internacoes_zika            CID A92.5 (próprio desde 2017) + A92.8
                                    (genérico, usado nos primeiros surtos 2015-2016)
    sih_internacoes_febre_amarela   CID A95* (qualquer subcategoria)

Por que essas variáveis adicionam valor sobre o SINAN:
    O SINAN registra o caso reconhecido pela vigilância (caso confirmado
    ou provável). O SIH-SUS registra a internação efetiva no sistema SUS,
    proxy de severidade da arbovirose. Internações reagem após o início
    de uma onda — utilidade preditiva pode vir como variável defasada
    (lag 1-3 meses), capturando a "memória" do município sobre surtos
    recentes que se traduziram em pressão hospitalar.

Particularidades do SIH-SUS:
    - Cobertura: apenas internações pagas pelo SUS (não inclui plano de
      saúde privado nem internações domiciliares).
    - Agrega pelo município de RESIDÊNCIA do paciente (campo MUNIC_RES),
      mesmo quando a internação ocorre em outro município — captura
      busca por tratamento em centros de referência.
    - Apenas casos graves: arbovirose leve normalmente não interna.

Fonte oficial:
    ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/
    Acessível também via HTTPS pelo mesmo path.
    Data de coleta: 2026-05-12.

Campos relevantes da AIH-RD:
    MUNIC_RES    Município de residência (código DATASUS 6 dígitos)
    DT_INTER     Data de internação (YYYYMMDD string) — define ano/mês
                 da agregação
    DIAG_PRINC   CID-10 do diagnóstico principal (4 chars, ex.: "A90 ")
    MORTE        '1' se o paciente faleceu durante a internação
                 (mantido como observação adicional, não usado por enquanto)
    DIAS_PERM    Dias de permanência (não usado por enquanto)

Saída: data/interim/sih_sus.parquet
Chave: (cod_ibge, ano, mes)
Colunas: cod_ibge, ano, mes, sih_internacoes_dengue, sih_internacoes_chikungunya,
         sih_internacoes_zika, sih_internacoes_febre_amarela
"""
from __future__ import annotations

import argparse
import datetime
import re
from collections import defaultdict
from pathlib import Path

import dbfread
import pandas as pd
from pyreaddbc import dbc2dbf

from arboviral.io import INTERIM, LOOKUP, RAW

PASTA_RAW = RAW / "sih_sus"
PADRAO_ARQUIVO = re.compile(r"^RDSP(\d{2})(\d{2})\.dbc$", re.IGNORECASE)

# Mapeamento CID-10 → categoria de doença. A chave usa as 3 primeiras letras/dígitos
# para A90, A91, A95; usa 4 chars para A92.0, A92.5, A92.8 (necessário distinguir
# chikungunya de zika).
def _classificar_cid(diag: str) -> str | None:
    """Mapeia CID-10 do diagnóstico principal para a doença, ou None.

    O campo DIAG_PRINC vem com padding de espaço (ex.: 'A90 '). Removemos
    espaços e o ponto antes de comparar.
    """
    s = diag.strip().replace(".", "").upper()
    if not s:
        return None
    if s.startswith("A90") or s.startswith("A91"):
        return "dengue"
    if s.startswith("A920"):
        return "chikungunya"
    if s.startswith("A925") or s.startswith("A928"):
        return "zika"
    if s.startswith("A95"):
        return "febre_amarela"
    return None


_LOOKUP_6_PARA_7: dict[str, int] | None = None


def _lookup_6d_para_7d() -> dict[str, int]:
    """Lookup oficial DATASUS 6 dígitos → IBGE 7 dígitos (645 munic. SP).

    DATASUS usa o cod_ibge sem o último dígito verificador. Reutilizamos
    o mesmo lookup do SINAN (`data/lookup/municipios_sp_estacoes_inmet.xlsx`).
    """
    global _LOOKUP_6_PARA_7
    if _LOOKUP_6_PARA_7 is not None:
        return _LOOKUP_6_PARA_7
    df = pd.read_excel(LOOKUP / "municipios_sp_estacoes_inmet.xlsx")
    col7 = "Código Município Completo"
    _LOOKUP_6_PARA_7 = {str(int(v))[:-1]: int(v) for v in df[col7].dropna().astype(int)}
    return _LOOKUP_6_PARA_7


def _parse_data(valor) -> datetime.date | None:
    """Aceita datetime.date ou string YYYYMMDD; devolve date ou None."""
    if isinstance(valor, datetime.date):
        return valor
    if isinstance(valor, str) and len(valor) >= 8:
        try:
            return datetime.date(int(valor[:4]), int(valor[4:6]), int(valor[6:8]))
        except ValueError:
            return None
    return None


def _agregar_dbc(caminho_dbc: Path, lookup: dict[str, int]) -> dict:
    """Streaming sobre um RDSP{AAMM}.dbc → contagens por (cod_ibge, ano, mes, doenca).

    Retorna dict[(cod_ibge, ano, mes, doenca)] = n_internacoes.
    Conversão DBC→DBF feita inline; arquivo DBF temporário é apagado ao final.
    """
    caminho_dbf = caminho_dbc.with_suffix(".dbf")
    contagens: defaultdict[tuple[int, int, int, str], int] = defaultdict(int)
    try:
        dbc2dbf(str(caminho_dbc), str(caminho_dbf))
        table = dbfread.DBF(str(caminho_dbf), load=False, encoding="latin1")
        for rec in table:
            doenca = _classificar_cid(str(rec.get("DIAG_PRINC", "")))
            if doenca is None:
                continue

            cod6 = str(rec.get("MUNIC_RES", "")).strip().zfill(6)
            cod7 = lookup.get(cod6)
            if cod7 is None:
                continue

            dt = _parse_data(rec.get("DT_INTER"))
            if dt is None:
                continue

            contagens[(cod7, dt.year, dt.month, doenca)] += 1
        return contagens
    finally:
        caminho_dbf.unlink(missing_ok=True)


def build() -> pd.DataFrame:
    """Lê todos os RDSP{AAMM}.dbc → DataFrame agregado em (cod_ibge, ano, mes).

    Pivota a contagem por doença em 4 colunas; zeros quando não houve
    internação daquela doença naquele município-mês.
    """
    arquivos = sorted(PASTA_RAW.glob("RDSP*.dbc"))
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum RDSP*.dbc em {PASTA_RAW}. Rode antes:\n"
            f"  python -m arboviral.scraping.sih_sus"
        )

    lookup = _lookup_6d_para_7d()
    print(f"Processando {len(arquivos)} arquivos AIH-RD...", flush=True)
    contagens_total: defaultdict[tuple[int, int, int, str], int] = defaultdict(int)
    for i, dbc in enumerate(arquivos, start=1):
        print(f"  [{i:>3}/{len(arquivos)}] {dbc.name} ...", flush=True)
        cont = _agregar_dbc(dbc, lookup)
        for k, v in cont.items():
            contagens_total[k] += v

    if not contagens_total:
        print("Nenhuma internação por arbovirose encontrada nos arquivos.")
        return pd.DataFrame()

    # Long → pivot wide
    long = pd.DataFrame(
        [(*k, v) for k, v in contagens_total.items()],
        columns=["cod_ibge", "ano", "mes", "doenca", "internacoes"],
    )
    wide = long.pivot_table(
        index=["cod_ibge", "ano", "mes"],
        columns="doenca",
        values="internacoes",
        fill_value=0,
    ).reset_index()
    wide.columns.name = None
    # Garantir as 4 colunas mesmo se alguma doença não apareceu em nenhum mês
    for doenca in ("dengue", "chikungunya", "zika", "febre_amarela"):
        col = f"sih_internacoes_{doenca}"
        if doenca in wide.columns:
            wide = wide.rename(columns={doenca: col})
        else:
            wide[col] = 0

    cols = ["cod_ibge", "ano", "mes",
            "sih_internacoes_dengue", "sih_internacoes_chikungunya",
            "sih_internacoes_zika", "sih_internacoes_febre_amarela"]
    return wide[cols].astype({c: "int32" for c in cols[3:]}).sort_values(
        ["cod_ibge", "ano", "mes"]
    ).reset_index(drop=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    df = build()
    destino = INTERIM / "sih_sus.parquet"
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(destino, index=False)

    print(f"\nGravado {len(df):,} linhas em {destino}")
    print()
    print("Internações totais por doença na janela 2015-2025:")
    for c in df.columns:
        if c.startswith("sih_internacoes_"):
            print(f"  {c:<40} {df[c].sum():>10,}")
    print()
    print("Top 10 (município, mês) com mais internações por dengue:")
    print(df.nlargest(10, "sih_internacoes_dengue").to_string(index=False))
