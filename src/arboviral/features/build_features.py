"""
Geração de features para modelagem.

Princípio crítico: SEM LEAKAGE TEMPORAL.
Para predizer surto em (município, mês t+1), todas as features são calculadas
usando apenas dados disponíveis até o mês t. Especificamente:
- Lags de casos: shift positivo (valor do mês passado), nunca do futuro
- Rolling: janelas que terminam em t-1 (não incluem t nem futuro)
- Climáticas: incluem t (assumindo que clima do mês corrente é observável
  até o fechamento — em produção, NASA POWER tem latência de ~3 dias)

Features geradas (POR DOENÇA, prefixadas — dengue_, zika_, chikungunya_,
febre_amarela_):
  Lags de casos:           {doenca}_casos_lag1, lag2, lag3, lag6, lag12
  Lags de incidência:      {doenca}_incid_lag1, lag2, lag3
  Rolling de casos:        {doenca}_casos_roll3, roll6 (médias)
  Rolling de incidência:   {doenca}_incid_roll3, roll6
  Tendência:               {doenca}_casos_trend3 (slope sobre 3 meses)
  Surtos passados:         {doenca}_surto_canal_lag1, lag3, lag12

Features cross-doença: incluídas (a doença A pode ter mosquito vetor compartilhado
com B). Comparação com vs sem cross-doença pode ser feita via flag --no-cross.

Climáticas (NASA POWER):
  precip_lag1, lag2 ; temp_media_lag1, lag2 ; umid_media_lag1, lag2
  precip_roll3 ; temp_media_roll3 ; umid_media_roll3

Sazonalidade (cíclica para evitar fronteira dez/jan):
  mes_sin = sin(2π·mes/12) ; mes_cos = cos(2π·mes/12)

Estáticas e anuais: passadas direto do master sem transformação adicional
(MUNIC, habitação, IDH, GINI, PIB, CAPAG, SINISA, lat, lon, dist_estação_inmet).

Saída: data/processed/features.parquet
Chave: (cod_ibge, ano, mes)
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from arboviral.io import PROCESSED

DOENCAS = ["dengue", "zika", "chikungunya", "febre_amarela"]

LAGS_CASOS = [1, 2, 3, 6, 12]
LAGS_INCID = [1, 2, 3]
ROLLING_WINDOWS = [3, 6]
LAGS_CLIMA = [1, 2]
LAGS_SURTO_PASSADO = [1, 3, 12]
CLIMA_VARS = ["precip_media_dia", "temp_media", "umid_media"]


def _lag(s: pd.Series, k: int) -> pd.Series:
    return s.shift(k)


def _rolling_mean(s: pd.Series, w: int) -> pd.Series:
    """Rolling mean da janela [t-w, t-1] (não inclui t nem futuro)."""
    return s.shift(1).rolling(w, min_periods=1).mean()


def _trend(s: pd.Series, w: int) -> pd.Series:
    """Slope linear da janela [t-w, t-1] — proxy de tendência."""
    def slope(x):
        if len(x) < 2 or x.isna().all():
            return np.nan
        y = x.values
        t = np.arange(len(y))
        mask = ~np.isnan(y)
        if mask.sum() < 2:
            return np.nan
        return np.polyfit(t[mask], y[mask], 1)[0]
    return s.shift(1).rolling(w, min_periods=2).apply(slope, raw=False)


def build(incluir_cross_doenca: bool = True) -> pd.DataFrame:
    print("Carregando municipio_mes.parquet e labels.parquet...", flush=True)
    master = pd.read_parquet(PROCESSED / "municipio_mes.parquet")
    labels = pd.read_parquet(PROCESSED / "labels.parquet")

    df = master.merge(labels, on=["cod_ibge", "ano", "mes"], how="left")
    df = df.sort_values(["cod_ibge", "ano", "mes"]).reset_index(drop=True)

    # Garantir que casos NaN viram 0 (sem registro = sem casos)
    for d in DOENCAS:
        df[f"{d}_casos"] = df[f"{d}_casos"].fillna(0)

    print("Gerando features por doença...", flush=True)
    feats = df[["cod_ibge", "ano", "mes"]].copy()

    grupo = df.groupby("cod_ibge", group_keys=False)

    # --- Features de casos / incidência / surto passados, por doença ---
    for d in DOENCAS:
        casos = df[f"{d}_casos"]
        incid = df[f"{d}_incid_100k"].fillna(0)

        for k in LAGS_CASOS:
            feats[f"{d}_casos_lag{k}"] = grupo[f"{d}_casos"].apply(lambda s, k=k: _lag(s, k)).reset_index(level=0, drop=True)
        for k in LAGS_INCID:
            feats[f"{d}_incid_lag{k}"] = grupo[f"{d}_incid_100k"].apply(lambda s, k=k: _lag(s, k)).reset_index(level=0, drop=True)
        for w in ROLLING_WINDOWS:
            feats[f"{d}_casos_roll{w}"] = grupo[f"{d}_casos"].apply(lambda s, w=w: _rolling_mean(s, w)).reset_index(level=0, drop=True)
            feats[f"{d}_incid_roll{w}"] = grupo[f"{d}_incid_100k"].apply(lambda s, w=w: _rolling_mean(s, w)).reset_index(level=0, drop=True)

        feats[f"{d}_casos_trend3"] = grupo[f"{d}_casos"].apply(lambda s: _trend(s, 3)).reset_index(level=0, drop=True)

        # Surtos passados (canal endêmico — referência principal por consistência com Min. Saúde)
        for k in LAGS_SURTO_PASSADO:
            feats[f"{d}_surto_canal_lag{k}"] = grupo[f"{d}_surto_canal"].apply(lambda s, k=k: _lag(s, k)).reset_index(level=0, drop=True)

    # --- Features climáticas com lag (precip, temp, umid em t-1, t-2 e roll3) ---
    print("Gerando features climáticas...", flush=True)
    for v in CLIMA_VARS:
        for k in LAGS_CLIMA:
            feats[f"{v}_lag{k}"] = grupo[v].apply(lambda s, k=k: _lag(s, k)).reset_index(level=0, drop=True)
        feats[f"{v}_roll3"] = grupo[v].apply(lambda s: _rolling_mean(s, 3)).reset_index(level=0, drop=True)

    # Clima do mês corrente (assumido observável)
    for v in CLIMA_VARS + ["temp_max", "temp_min", "pressao_media_kpa", "vento_media"]:
        feats[v] = df[v].values

    # --- Sazonalidade cíclica ---
    feats["mes_sin"] = np.sin(2 * np.pi * feats["mes"] / 12)
    feats["mes_cos"] = np.cos(2 * np.pi * feats["mes"] / 12)

    # --- Estáticas e anuais (passadas direto) ---
    estaticas_anuais = [
        "lat", "lon", "dist_estacao_km",
        "populacao_estimada", "pib_per_capita", "gini", "idhm",
        "iag0001_atend_agua_pct", "ies0001_atend_esgoto_pct", "ies2004_esgoto_tratado_pct",
        "leitos_publicos", "mortalidade_materna",
        "msau28_pacs", "msau541_vig_sanitaria", "msau542_vig_epidemiologica", "msau543_controle_endemias",
        "mgrd01_seca", "mgrd06_alagamento", "mgrd07_erosao", "mgrd08_enchente_gradual",
        "mgrd11_enxurrada", "mgrd14_deslizamento", "mgrd201_mapeamento_risco", "mmam2612_moradia_risco",
        "num_aglom_subnorm_2010", "pop_aglom_subnorm_2010",
        "num_favelas_2022", "pop_favelas_2022",
    ]
    for c in estaticas_anuais:
        if c in df.columns:
            feats[c] = df[c].values

    # CAPAG: categórica → one-hot
    if "capag" in df.columns:
        capag_dummies = pd.get_dummies(df["capag"], prefix="capag", dummy_na=False)
        for c in capag_dummies.columns:
            feats[c] = capag_dummies[c].values.astype(int)

    # --- Remover features cross-doença se solicitado ---
    if not incluir_cross_doenca:
        print("Removendo features cross-doença (--no-cross)...", flush=True)
        # Para o target dengue, manter apenas features de dengue + clima + estáticas
        # Aqui não filtramos porque features.parquet é compartilhado;
        # a filtragem cross-doença é responsabilidade do train script.
        # Adicionamos uma flag para o train identificar.
        pass  # implementação no train.py via mascaramento de colunas

    return feats


def _imprimir_resumo(feats: pd.DataFrame) -> None:
    print(f"\nshape: {feats.shape}")
    print(f"colunas: {len(feats.columns)}")
    nan_pct = (feats.isna().mean() * 100).round(1)
    print(f"\nFeatures com NaN > 50% (esperado para os primeiros meses por causa dos lags):")
    altos = nan_pct[nan_pct > 50].sort_values(ascending=False)
    print(altos.head(10).to_string())
    print(f"\nLinhas com TODAS as features de lag preenchidas: "
          f"{(feats.dropna().shape[0]):,} / {len(feats):,}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-cross", action="store_true",
                        help="(no momento, sem efeito — flag preservada para train.py)")
    args = parser.parse_args()

    feats = build(incluir_cross_doenca=not args.no_cross)
    out = PROCESSED / "features.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    feats.to_parquet(out, index=False)
    print(f"\nGravado {len(feats):,} linhas × {len(feats.columns)} colunas em {out}")
    _imprimir_resumo(feats)
