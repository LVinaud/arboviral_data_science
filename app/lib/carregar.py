"""
Carregadores de dados e modelos para o app Streamlit.

Princípio: o app DEPENDE do pacote `arboviral` (data science), nunca o contrário.
Tudo é lido de `data/processed/` ou `data/lookup/` — outputs do pipeline.

Funções decoradas com @st.cache_data são carregadas uma única vez por sessão
do Streamlit, garantindo performance (re-carregar parquet de 12MB toda vez
seria inviável).
"""
from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

from arboviral.io import LOOKUP, PROCESSED


@st.cache_data(show_spinner="Carregando municípios...")
def carregar_municipios() -> pd.DataFrame:
    """Lookup município → nome, lat, lon, estação INMET."""
    df = pd.read_excel(LOOKUP / "municipios_sp_estacoes_inmet.xlsx", engine="calamine")
    df = df.rename(columns={
        "Código Município Completo": "cod_ibge",
        "Nome_Município": "nome_municipio",
        "LATITUDE": "lat",
        "LONGITUDE": "lon",
        "CD_ESTACAO": "estacao_inmet",
        "NOME_ESTACAO": "nome_estacao",
        "DIST_KM": "dist_estacao_km",
    })
    df["cod_ibge"] = df["cod_ibge"].astype(int)
    return df


@st.cache_data(show_spinner="Carregando dataset master...")
def carregar_master() -> pd.DataFrame:
    """municipio_mes.parquet — dataset consolidado (645 mun × 11 anos × 12 meses)."""
    return pd.read_parquet(PROCESSED / "municipio_mes.parquet")


@st.cache_data(show_spinner="Carregando rótulos de surto...")
def carregar_labels() -> pd.DataFrame:
    """labels.parquet — 4 definições binárias de surto por doença."""
    return pd.read_parquet(PROCESSED / "labels.parquet")


@st.cache_data(show_spinner="Carregando features...")
def carregar_features() -> pd.DataFrame:
    """features.parquet — input para os modelos (~140 colunas após Onda 1, sem leakage)."""
    return pd.read_parquet(PROCESSED / "features.parquet")


@st.cache_data(show_spinner="Carregando histórico de predições...")
def carregar_predicoes() -> pd.DataFrame:
    """predictions.parquet — predições de TODOS os modelos em todos os folds.

    Permite mostrar histórico de alertas que o sistema teria emitido.

    Como o alvo é surto(t+1), `(ano, mes)` no parquet referem-se ao mês das
    features (instante em que o sistema "olha"). Adicionamos `target_ano` e
    `target_mes` (mês predito = t+1) para que as telas exibam o mês ao qual
    o alerta de fato corresponde — caso contrário fold=2024 começaria em
    Dez/2023 (features que predizem Jan/2024).
    """
    df = pd.read_parquet(PROCESSED / "predictions.parquet")
    df["target_ano"] = df["ano"] + (df["mes"] == 12).astype(int)
    df["target_mes"] = (df["mes"] % 12) + 1
    return df


@st.cache_resource(show_spinner="Carregando modelos treinados...")
def carregar_modelo(doenca: str, definicao: str, nome_modelo: str, fold: int):
    """Carrega um modelo serializado específico.

    Cache de RECURSO (não de dados): modelos são objetos pesados, não devem
    ser duplicados na sessão.
    """
    arquivo = PROCESSED / "models" / f"{doenca}_{definicao}_{nome_modelo}_{fold}.joblib"
    if not arquivo.exists():
        return None
    return joblib.load(arquivo)


def listar_modelos_disponiveis() -> list[dict]:
    """Lista todos os arquivos .joblib em data/processed/models/."""
    pasta = PROCESSED / "models"
    if not pasta.exists():
        return []
    rows = []
    for f in sorted(pasta.glob("*.joblib")):
        partes = f.stem.replace("_nocross", "").split("_")
        # Convenção: {doenca}_{definicao}_{modelo}_{fold}
        # febre_amarela tem dois tokens — cuidado
        if partes[0] == "febre" and len(partes) >= 5:
            doenca, definicao, modelo, fold = "febre_amarela", partes[2], partes[3], int(partes[4])
        else:
            doenca, definicao, modelo, fold = partes[0], partes[1], partes[2], int(partes[3])
        rows.append({
            "doenca": doenca, "definicao": definicao,
            "modelo": modelo, "fold": fold, "arquivo": f.name,
        })
    return rows


def caminho_disponivel() -> bool:
    """Verifica se os arquivos essenciais existem."""
    necessarios = [
        PROCESSED / "municipio_mes.parquet",
        PROCESSED / "labels.parquet",
    ]
    return all(p.exists() for p in necessarios)
