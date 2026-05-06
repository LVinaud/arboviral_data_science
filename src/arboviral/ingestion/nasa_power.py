"""
Ingestão: NASA POWER — dados meteorológicos mensais por município SP.

Fonte: NASA POWER (Prediction Of Worldwide Energy Resources)
API:   https://power.larc.nasa.gov/api/temporal/monthly/point
Resolução: ~0,5° (~55 km); dado observado via satélite e reanálise (MERRA-2)

Vantagens sobre INMET:
    - Cobertura completa (sem estações inativas nem valores ausentes)
    - Série histórica desde 1981
    - Não requer download manual

Variáveis coletadas:
    T2M          Temperatura média mensal a 2m (°C)
    T2M_MAX      Temperatura máxima mensal a 2m (°C)
    T2M_MIN      Temperatura mínima mensal a 2m (°C)
    PRECTOTCORR  Precipitação total mensal corrigida (mm/dia → multiplicar por dias do mês)
    RH2M         Umidade relativa média a 2m (%)
    WS10M        Velocidade média do vento a 10m (m/s)
    PS           Pressão superficial média (kPa)

Uso:
    python -m arboviral.ingestion.nasa_power   # baixa 2015–2025 para todos os 645 municípios SP

Saída (data/raw/nasa_power/):
    nasa_power_municipios_sp.parquet   — (~645 municípios × 132 meses × 7 vars)

O arquivo é salvo diretamente em raw/ por ser dado primário (não processado localmente);
a ingestão final (data/interim/nasa_power.parquet) é gerada por build().
"""
import time
from pathlib import Path

import pandas as pd
import requests

from arboviral.io import INTERIM, LOOKUP, RAW

NASA_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
VARIAVEIS = "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS10M,PS"
FILL_VALUE = -999.0
ANO_INICIO = 2015
ANO_FIM = 2025
PAUSA_S = 0.4  # respeitar rate-limit (~150 req/min segundo docs NASA POWER)


def _municipios_sp() -> pd.DataFrame:
    xl = LOOKUP / "municipios_sp_estacoes_inmet.xlsx"
    df = pd.read_excel(xl)[["Código Município Completo", "Nome_Município", "LATITUDE", "LONGITUDE"]]
    df.columns = ["cod_ibge", "nome_municipio", "lat", "lon"]
    return df


def _buscar_municipio(cod_ibge: int, lat: float, lon: float) -> list[dict]:
    params = {
        "start": str(ANO_INICIO),
        "end": str(ANO_FIM),
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "parameters": VARIAVEIS,
        "community": "AG",
        "format": "JSON",
        "user": "arboviralicusp",
    }
    resp = requests.get(NASA_URL, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    parameter = data["properties"]["parameter"]
    # Chaves: YYYYMM (dados mensais) + YYYYMM onde MM=13 (média anual — descartar)
    meses_chaves = {k for k in next(iter(parameter.values())) if not k.endswith("13")}

    registros = []
    for chave in sorted(meses_chaves):
        ano = int(chave[:4])
        mes = int(chave[4:])
        row = {"cod_ibge": cod_ibge, "ano": ano, "mes": mes}
        for var, vals in parameter.items():
            v = vals.get(chave, FILL_VALUE)
            row[var.lower()] = None if v == FILL_VALUE else v
        registros.append(row)
    return registros


def coletar(destino: Path | None = None) -> pd.DataFrame:
    """Baixa dados NASA POWER para todos os municípios SP e retorna DataFrame."""
    destino = destino or RAW / "nasa_power" / "nasa_power_municipios_sp.parquet"
    destino.parent.mkdir(parents=True, exist_ok=True)

    if destino.exists():
        print(f"Já existe: {destino} — carregando cache.")
        return pd.read_parquet(destino)

    munis = _municipios_sp()
    total = len(munis)
    todos = []

    for i, row in munis.iterrows():
        cod = int(row["cod_ibge"])
        nome = row["nome_municipio"]
        lat, lon = row["lat"], row["lon"]

        if (i + 1) % 50 == 0 or i == 0:
            print(f"  [{i+1}/{total}] {nome} ({cod})...")

        try:
            registros = _buscar_municipio(cod, lat, lon)
            todos.extend(registros)
        except Exception as exc:
            print(f"  ERRO {nome}: {exc}")

        time.sleep(PAUSA_S)

    df = pd.DataFrame(todos).sort_values(["cod_ibge", "ano", "mes"]).reset_index(drop=True)
    df.to_parquet(destino, index=False)
    print(f"\nGravado {len(df):,} linhas em {destino}")
    return df


def build() -> pd.DataFrame:
    """Retorna o dataset NASA POWER (lê cache ou baixa se ausente)."""
    raw_parquet = RAW / "nasa_power" / "nasa_power_municipios_sp.parquet"
    df = coletar(raw_parquet)

    # Renomear para nomes canônicos do schema
    rename = {
        "t2m": "temp_media",
        "t2m_max": "temp_max",
        "t2m_min": "temp_min",
        "prectotcorr": "precip_media_dia",
        "rh2m": "umid_media",
        "ws10m": "vento_media",
        "ps": "pressao_media_kpa",
    }
    df = df.rename(columns=rename)
    return df


if __name__ == "__main__":
    df = build()
    out = INTERIM / "nasa_power.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Gravado {len(df):,} linhas em {out}")
    print(df.head())
