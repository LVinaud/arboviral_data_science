"""
Agregação espacial de predições e casos para o mapa hierárquico.

Esta camada vive DENTRO do app — o core (`src/arboviral/`) não conhece DRS,
regiões intermediárias ou qualquer divisão geográfica adicional. Aqui
combinamos:

    predictions.parquet   ← core (cod_ibge × target_ano × target_mes × prob_predita)
    municipio_mes.parquet ← core (cod_ibge × ano × mes × casos × população)
    data/lookup/geo/      ← assets pré-computados (gerados por scripts/gerar_geo_lookup.py)

… e devolvemos um DataFrame uniforme por nível geográfico, pronto pra plotar.

Convenção do nível:
    "municipio" → 645 unidades, sem agregação
    "drs"       → 17 unidades, dissolve por Direção Regional de Saúde (SES-SP)
    "rgi"       → 11 unidades, dissolve por Região Intermediária IBGE 2017

Regras de agregação ao subir de nível:
    prob_predita → média PONDERADA POR POPULAÇÃO (não pode somar; média simples
                   sobrestima municípios pequenos com prob alta).
    casos        → soma simples (preserva totais regionais).
    populacao    → soma simples (informativa; também base do peso da prob).
    lat/lon      → média dos centroides municipais ponderada por população
                   (alinha o ponto com o centro populacional da região).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from arboviral.io import LOOKUP


NIVEIS_VALIDOS = ("municipio", "drs", "rgi")
GEO_DIR = LOOKUP / "geo"


@st.cache_data(show_spinner=False)
def carregar_lookup_geo() -> pd.DataFrame:
    """Lookup município → drs, rgi, lat/lon de centroide, ordenado por cod_ibge."""
    df = pd.read_csv(GEO_DIR / "municipios_sp_lookup.csv")
    df["cod_ibge"] = df["cod_ibge"].astype(int)
    df["rgi_codigo"] = df["rgi_codigo"].astype(int)
    return df


@st.cache_data(show_spinner=False)
def carregar_geojson_drs() -> dict:
    """GeoJSON com 17 polígonos de DRS (chave: 'id' = numeral romano)."""
    import json
    return json.loads((GEO_DIR / "drs_sp.geojson").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def carregar_geojson_rgi() -> dict:
    """GeoJSON com 11 polígonos de Regiões Intermediárias (chave: 'codigo')."""
    import json
    return json.loads((GEO_DIR / "regioes_intermediarias_sp.geojson").read_text(encoding="utf-8"))


def _coluna_id_nivel(nivel: str) -> tuple[str, str]:
    """Retorna (col_id, col_nome) do nível no lookup. col_id é o que vira
    `locations=` no choropleth e o que `featureidkey` mapeia no geojson."""
    if nivel == "municipio":
        return "cod_ibge", "nome_municipio"
    if nivel == "drs":
        # Usamos o id romano (parte antes do hífen) como chave estável; o nome
        # completo "I - Grande São Paulo" entra como rótulo humano.
        return "drs_id", "drs"
    if nivel == "rgi":
        return "rgi_codigo", "rgi_nome"
    raise ValueError(f"Nível inválido: {nivel!r}. Esperado: {NIVEIS_VALIDOS}")


def _populacao_recente(master: pd.DataFrame) -> pd.DataFrame:
    """População por município no último ano disponível.

    O master tem `populacao_estimada` mensal (forward-fill após 2023), então
    para ponderação usamos o ano mais recente — equivalente à fotografia
    populacional vigente.
    """
    ano_max = int(master["ano"].max())
    pop = (
        master[master["ano"] == ano_max]
        .groupby("cod_ibge", as_index=False)["populacao_estimada"]
        .first()
        .rename(columns={"populacao_estimada": "populacao"})
    )
    pop["cod_ibge"] = pop["cod_ibge"].astype(int)
    return pop


def agregar(
    predicoes: pd.DataFrame,
    master: pd.DataFrame,
    doenca: str,
    nivel: str,
) -> pd.DataFrame:
    """Agrega predições + casos para o nível geográfico solicitado.

    Args:
        predicoes: já filtrado por (doença, definição, modelo, fold). Deve ter
            colunas cod_ibge, target_ano, target_mes, prob_predita, y_true.
        master: dataset completo (precisa de populacao_estimada e {doenca}_casos).
        doenca: slug da doença (entra na seleção do `{doenca}_casos`).
        nivel: 'municipio' | 'drs' | 'rgi'.

    Returns:
        DataFrame com colunas:
            id_unidade        — chave estável (cod_ibge / drs_id / rgi_codigo)
            nome_unidade      — rótulo humano
            target_ano, target_mes
            prob_predita      — escala [0, 1]
            casos             — inteiro (soma no nível, casos do município)
            populacao         — informativa
            lat, lon          — centroide ponderado por população
            y_true            — soma ou taxa de surtos confirmados na região
    """
    if nivel not in NIVEIS_VALIDOS:
        raise ValueError(f"Nível inválido: {nivel!r}. Esperado: {NIVEIS_VALIDOS}")

    lookup = carregar_lookup_geo()
    pop = _populacao_recente(master)

    # Casos por (município, target_ano, target_mes) — extraídos do master.
    # target_mes é o mês PREDITO, que é (mes + 1) com wrap em dezembro.
    casos_col = f"{doenca}_casos"
    if casos_col not in master.columns:
        raise KeyError(f"Coluna {casos_col!r} não existe no master.")
    casos = master[["cod_ibge", "ano", "mes", casos_col]].copy()
    casos = casos.rename(columns={"ano": "target_ano", "mes": "target_mes",
                                  casos_col: "casos"})
    casos["cod_ibge"] = casos["cod_ibge"].astype(int)

    # Predições normalizadas
    p = predicoes[["cod_ibge", "target_ano", "target_mes",
                   "prob_predita", "y_true"]].copy()
    p["cod_ibge"] = p["cod_ibge"].astype(int)

    # Combinar tudo (predições já cobrem (cod, ano, mes); casos pode faltar
    # → vira 0; pop e geometria vêm do lookup)
    df = p.merge(casos, on=["cod_ibge", "target_ano", "target_mes"], how="left")
    df["casos"] = df["casos"].fillna(0).astype(int)
    df = df.merge(pop, on="cod_ibge", how="left")
    df["populacao"] = df["populacao"].fillna(0).astype(int)
    df = df.merge(
        lookup[["cod_ibge", "nome_municipio", "drs", "rgi_codigo",
                "rgi_nome", "lat", "lon"]],
        on="cod_ibge", how="left",
    )
    # drs_id = "I", "II", ..., "XVII" — chave estável (o nome muda com tradução)
    df["drs_id"] = df["drs"].str.split(" - ").str[0]

    if nivel == "municipio":
        return df.rename(columns={"cod_ibge": "id_unidade",
                                  "nome_municipio": "nome_unidade"})[[
            "id_unidade", "nome_unidade", "target_ano", "target_mes",
            "prob_predita", "casos", "populacao", "lat", "lon", "y_true",
        ]]

    col_id, col_nome = _coluna_id_nivel(nivel)
    grupos = ["target_ano", "target_mes", col_id, col_nome]

    # Agregação: prob via média ponderada (Σ p×pop / Σ pop); soma de casos;
    # centroide via média ponderada de lat/lon por população.
    df["_prob_x_pop"] = df["prob_predita"] * df["populacao"]
    df["_lat_x_pop"] = df["lat"] * df["populacao"]
    df["_lon_x_pop"] = df["lon"] * df["populacao"]

    agreg = df.groupby(grupos, as_index=False).agg(
        soma_prob_pop=("_prob_x_pop", "sum"),
        soma_lat_pop=("_lat_x_pop", "sum"),
        soma_lon_pop=("_lon_x_pop", "sum"),
        populacao=("populacao", "sum"),
        casos=("casos", "sum"),
        y_true=("y_true", "sum"),
    )
    agreg["prob_predita"] = agreg["soma_prob_pop"] / agreg["populacao"].replace(0, 1)
    agreg["lat"] = agreg["soma_lat_pop"] / agreg["populacao"].replace(0, 1)
    agreg["lon"] = agreg["soma_lon_pop"] / agreg["populacao"].replace(0, 1)
    agreg = agreg.drop(columns=["soma_prob_pop", "soma_lat_pop", "soma_lon_pop"])
    return agreg.rename(columns={col_id: "id_unidade", col_nome: "nome_unidade"})[[
        "id_unidade", "nome_unidade", "target_ano", "target_mes",
        "prob_predita", "casos", "populacao", "lat", "lon", "y_true",
    ]]
