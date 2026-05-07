"""
Ingestão: Cobertura da Atenção Primária à Saúde (ex-ESF) — e-Gestor MS.

Fonte raw: 132 arquivos JSON em data/raw/esf/cobertura_<ab|aps>_<YYYYMM>.json
  (baixados por src/arboviral/scraping/esf_coverage.py)

Há duas metodologias diferentes:

  AB  (2015-2020): pc_cobertura_ab/sf, valores em STRING formato BR ("12,106,920")
                   chave nuComp = "201801"
  APS (2021-presente): qtCobertura, valores em INT/FLOAT direto
                       chave nuComp = "01/2024"

Harmonizamos em 4 colunas + 1 flag de metodologia:

    esf_cobertura_pct    cobertura % da APS/AB (pcCoberturaAb em AB ou qtCobertura em APS)
    esf_qt_equipes        número de equipes ESF (qtEsf — campo consistente entre AB e APS)
    esf_qt_capacidade     capacidade total de atendimento (apenas APS; NaN para AB)
    esf_pop_referencia    população usada como referência pelo MS (qtPopulacao)
    esf_metodologia       'AB' ou 'APS' — flag categórica para o modelo saber

Saída: data/interim/esf.parquet
Chave: (cod_ibge, ano, mes)  — mensal

Filtra SP (sgUf == 'SP') durante a leitura.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from arboviral.io import INTERIM, RAW


def _parse_pct_br(s) -> float:
    """Converte string '59.44' ou número 59.44 em float. Retorna NaN se inválido."""
    if s is None or s == "" or s == "-":
        return float("nan")
    try:
        return float(str(s).replace(",", ""))
    except (ValueError, TypeError):
        return float("nan")


def _parse_int_br(s) -> float:
    """Converte string '12,106,920' (formato BR) ou número em float."""
    if s is None or s == "" or s == "-":
        return float("nan")
    try:
        return float(str(s).replace(",", ""))
    except (ValueError, TypeError):
        return float("nan")


def _parse_nu_comp(nu_comp: str) -> tuple[int, int]:
    """Retorna (ano, mes) a partir de '201801' (AB) ou '01/2024' (APS)."""
    s = str(nu_comp).strip()
    if "/" in s:
        # APS: "01/2024"
        mm, yyyy = s.split("/")
        return int(yyyy), int(mm)
    # AB: "201801"
    return int(s[:4]), int(s[4:6])


def _processar_arquivo(arquivo: Path, metodologia: str) -> list[dict]:
    """Lê 1 arquivo JSON e retorna lista de dicts SP com campos harmonizados."""
    with open(arquivo) as f:
        registros = json.load(f)

    rows = []
    for r in registros:
        if r.get("sgUf") != "SP":
            continue
        ano, mes = _parse_nu_comp(r["nuComp"])
        cod_mun_6 = str(r["coMunicipioIbge"])  # 6 dígitos
        # cod_ibge 7 dígitos: usar lookup ou completar com dígito verificador conhecido
        # MS publica com 6 dígitos. Para compatibilidade com nosso master, faremos via merge
        # com lookup IBGE depois. Por ora, mantemos coMunicipioIbge como string.

        if metodologia == "AB":
            cobertura = _parse_pct_br(r.get("pcCoberturaAb"))
            qt_capacidade = float("nan")
        else:  # APS
            cobertura = _parse_pct_br(r.get("qtCobertura"))
            qt_capacidade = _parse_int_br(r.get("qtCapacidadeEquipe"))

        rows.append({
            "cod_ibge_6d": cod_mun_6,
            "ano": ano,
            "mes": mes,
            "esf_cobertura_pct": cobertura,
            "esf_qt_equipes": _parse_int_br(r.get("qtEsf")),
            "esf_qt_capacidade": qt_capacidade,
            "esf_pop_referencia": _parse_int_br(r.get("qtPopulacao")),
            "esf_metodologia": metodologia,
        })
    return rows


def _carregar_lookup_6_para_7d() -> dict[str, int]:
    """Mapeia código IBGE 6 dígitos (DATASUS) → 7 dígitos (oficial)."""
    from arboviral.io import LOOKUP
    df = pd.read_excel(LOOKUP / "municipios_sp_estacoes_inmet.xlsx", engine="calamine")
    return {
        str(int(v))[:-1]: int(v)
        for v in df["Código Município Completo"].dropna().astype(int)
    }


def build() -> pd.DataFrame:
    pasta = RAW / "esf"
    arquivos = sorted(pasta.glob("cobertura_*.json"))
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum cobertura_*.json em {pasta}. Rode primeiro:\n"
            "  python -m arboviral.scraping.esf_coverage"
        )

    print(f"  Processando {len(arquivos)} arquivos JSON...", flush=True)
    rows: list[dict] = []
    for arq in arquivos:
        metodologia = "AB" if arq.stem.startswith("cobertura_ab_") else "APS"
        rows.extend(_processar_arquivo(arq, metodologia))

    df = pd.DataFrame(rows)
    print(f"  {len(df):,} linhas SP totais", flush=True)

    # Resolver código 6 → 7 dígitos
    lookup = _carregar_lookup_6_para_7d()
    df["cod_ibge"] = df["cod_ibge_6d"].map(lookup)
    n_sem_match = df["cod_ibge"].isna().sum()
    if n_sem_match:
        print(f"  ⚠ {n_sem_match} linhas sem match no lookup IBGE", flush=True)
    df = df.dropna(subset=["cod_ibge"]).copy()
    df["cod_ibge"] = df["cod_ibge"].astype(int)
    df = df.drop(columns=["cod_ibge_6d"])

    cols = ["cod_ibge", "ano", "mes", "esf_metodologia", "esf_cobertura_pct",
            "esf_qt_equipes", "esf_qt_capacidade", "esf_pop_referencia"]
    return df[cols].sort_values(["cod_ibge", "ano", "mes"]).reset_index(drop=True)


if __name__ == "__main__":
    df = build()
    out = INTERIM / "esf.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"\nGravado {len(df):,} linhas em {out}")
    print(f"Municípios cobertos: {df['cod_ibge'].nunique()}")
    print(f"Metodologias: {df['esf_metodologia'].value_counts().to_dict()}")
    print(f"\nAmostra (SP capital, jan/2018 e jan/2024):")
    sp = df[df["cod_ibge"] == 3550308]
    print(sp[(sp['ano'].isin([2018, 2024])) & (sp['mes'] == 1)].to_string(index=False))
    print(f"\nEstatísticas SP (mediana estadual):")
    print(df.groupby("esf_metodologia")[["esf_cobertura_pct", "esf_qt_equipes"]]
            .median().round(2).to_string())
    print(f"\nCompletude:")
    print(df[["esf_cobertura_pct", "esf_qt_equipes", "esf_qt_capacidade"]].notna().sum().to_string())
