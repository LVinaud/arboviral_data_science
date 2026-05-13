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
(MUNIC, habitação, IDH, GINI, PIB, CAPAG, SINISA, lat, lon, dist_estação_inmet,
área/densidade IBGE, MapBiomas uso do solo, cobertura vacinal FA).

ESF (cobertura APS, mensal):
  esf_cobertura_pct_lag1, esf_qt_equipes_lag1 (lag1 — cobertura é o que o
  gestor observa no mês anterior); esf_metodologia one-hot (AB vs APS,
  flag categórica para o modelo distinguir os dois regimes).

Latência SINAN (proxy de qualidade da vigilância, mensal por doença):
  {doenca}_latencia_mediana_lag1, latencia_p90_lag1, n_casos_com_latencia_lag1
  Usado em lag1 porque a latência do mês corrente carrega informação que
  só está disponível DEPOIS dos casos serem notificados — usar t direto é
  leakage operacional (em produção o gestor não tem essa info ainda).

SIH-SUS (internações por arbovirose, mensal por doença — Onda 2):
  sih_internacoes_{dengue,zika,chikungunya,febre_amarela}_lag1
  Lag1 pelo mesmo motivo da latência: AIH-RD do DATASUS tem ~60 dias de
  defasagem de processamento; em produção o gestor só observa internações
  consolidadas do mês passado.

Mobilidade pendular intermunicipal (estrutural, anual — Onda 2):
  pendulares_entram_trabalho, pendulares_saem_trabalho
  Passados direto sem transformação (snapshots Censo 2010 + 2022). NaN
  em entram para 2022+ é tratado nativamente pelos modelos de árvore;
  para LogReg, o train descarta colunas all-NaN do fold automaticamente.

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

        # Latência SINAN (proxy de qualidade da vigilância) — em lag1 (info só
        # observável depois das notificações; usar t é leakage operacional)
        for col in (f"{d}_latencia_mediana", f"{d}_latencia_p90", f"{d}_n_casos_com_latencia"):
            if col in df.columns:
                feats[f"{col}_lag1"] = grupo[col].apply(lambda s: _lag(s, 1)).reset_index(level=0, drop=True)

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
        # Densidade IBGE (estáticas)
        "area_km2", "densidade_2023",
        # MapBiomas — uso do solo (anuais, varia <1%/ano)
        "pct_floresta", "pct_agricultura", "pct_nao_vegetado", "pct_agua", "pct_natural_nao_florestal",
        # Vacinação FA (anual)
        "cob_vac_fa_pct",
        # ESF — qt_capacidade e pop_referencia passados direto (denominadores estruturais);
        # cobertura_pct e qt_equipes vão como lag1 abaixo
        "esf_qt_capacidade", "esf_pop_referencia",
    ]
    for c in estaticas_anuais:
        if c in df.columns:
            feats[c] = df[c].values

    # CAPAG: categórica → one-hot
    if "capag" in df.columns:
        capag_dummies = pd.get_dummies(df["capag"], prefix="capag", dummy_na=False)
        for c in capag_dummies.columns:
            feats[c] = capag_dummies[c].values.astype(int)

    # ESF metodologia: categórica (AB vs APS) → one-hot (quebra metodológica em 2021)
    if "esf_metodologia" in df.columns:
        esf_dummies = pd.get_dummies(df["esf_metodologia"], prefix="esf_metodologia", dummy_na=False)
        for c in esf_dummies.columns:
            feats[c] = esf_dummies[c].values.astype(int)

    # ESF cobertura mensal: lag1 (em produção, gestor observa o mês passado)
    for c in ("esf_cobertura_pct", "esf_qt_equipes"):
        if c in df.columns:
            feats[f"{c}_lag1"] = grupo[c].apply(lambda s: _lag(s, 1)).reset_index(level=0, drop=True)

    # SIH-SUS: internações por arbovirose (Onda 2). São indicadores mensais
    # retrospectivos — o gestor só observa internação consolidada do mês passado,
    # então entra como lag1. Por construção do master, NaN já foi preenchido com 0
    # (ausência de internação ≠ ausência de informação), o lag preserva esse zero.
    for d in DOENCAS:
        col = f"sih_internacoes_{d}"
        if col in df.columns:
            feats[f"{col}_lag1"] = grupo[col].apply(lambda s: _lag(s, 1)).reset_index(level=0, drop=True)

    # Mobilidade pendular (Onda 2): variáveis estruturais anuais (Censo 2010+2022).
    # `pendulares_entram_trabalho` fica NaN em 2022+ — limitação documentada em
    # AUDITORIA_DADOS.md §15; o modelo trata NaN nativamente nas árvores e
    # via descarte de coluna no train para LogReg.
    for c in ("pendulares_entram_trabalho", "pendulares_saem_trabalho"):
        if c in df.columns:
            feats[c] = df[c].values

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
