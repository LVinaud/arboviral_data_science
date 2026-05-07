"""
Consolida os parquets intermediários no dataset canônico município–mês.

Saída: data/processed/municipio_mes.parquet
Chave: (cod_ibge, ano, mes)
Grade: 645 municípios SP × 2015–2025 × 12 meses = 85.140 linhas

Fontes e estratégia de join:
  mensal  (cod_ibge, ano, mes): sinan_dengue, sinan_zika, sinan_chikungunya,
                                 febre_amarela, nasa_power, saude
  anual   (cod_ibge, ano):      ibge, socioeconomico, sinisa
  estática (cod_ibge):          munic, habitacao, densidade
  lookup  (cod_ibge):           nome, lat, lon, estação INMET

Decisões metodológicas:
  - População 2024-2025: forward-fill a partir de 2023 (IBGE só publica até 2023).
    Alternativa rejeitada: ajustar modelo de tendência populacional. Forward-fill
    foi escolhida por simplicidade e por ser conservadora — a mudança populacional
    municipal entre anos consecutivos é tipicamente <2%, dentro da margem de erro
    da própria estimativa do IBGE. Documentar essa escolha no relatório.
  - Febre amarela: usa município de Local Provável de Infecção (LPI), enquanto
    SINAN dengue/zika/chikungunya usam município de residência. Diferença
    metodológica preservada por ser intrínseca à natureza das doenças (FA é
    silvestre, transmissão fora do município de residência é regra).
  - Vacinação FA: anual com gap em 2017 dentro de 2015-2025 — forward-fill no
    grupo cod_ibge para preencher (cobertura vacinal varia <5p.p./ano em
    janelas sem campanha).
"""
import pandas as pd

from arboviral.io import INTERIM, LOOKUP, PROCESSED

_ANOS = list(range(2015, 2026))  # 2015–2025 inclusive


def _grade_base() -> pd.DataFrame:
    """Cria a grade completa (cod_ibge, ano, mes) e adiciona geolocalização."""
    lk = pd.read_excel(LOOKUP / "municipios_sp_estacoes_inmet.xlsx", engine="calamine")
    lk = lk.rename(columns={
        "Código Município Completo": "cod_ibge",
        "Nome_Município": "nome_municipio",
        "LATITUDE": "lat",
        "LONGITUDE": "lon",
        "CD_ESTACAO": "estacao_inmet",
        "NOME_ESTACAO": "nome_estacao_inmet",
        "DIST_KM": "dist_estacao_km",
    })
    lk["cod_ibge"] = lk["cod_ibge"].astype(int)

    idx = pd.MultiIndex.from_product(
        [lk["cod_ibge"], _ANOS, range(1, 13)],
        names=["cod_ibge", "ano", "mes"],
    )
    grade = pd.DataFrame(index=idx).reset_index()
    grade = grade.merge(lk, on="cod_ibge", how="left")
    return grade


def _sinan_prefixado(doenca: str) -> pd.DataFrame:
    df = pd.read_parquet(INTERIM / f"sinan_{doenca}.parquet")
    return df.rename(columns={
        "casos_notificados":      f"{doenca}_casos",
        "casos_provaveis":        f"{doenca}_casos_provaveis",
        "obitos":                 f"{doenca}_obitos",
        "internacoes":            f"{doenca}_internacoes",
        # Latência (proxy de qualidade da vigilância / subnotificação)
        "latencia_mediana_dias":  f"{doenca}_latencia_mediana",
        "latencia_p90_dias":      f"{doenca}_latencia_p90",
        "n_casos_com_latencia":   f"{doenca}_n_casos_com_latencia",
    })


def build() -> pd.DataFrame:
    print("Criando grade base (645 municípios × 2015–2025 × 12 meses)...", flush=True)
    df = _grade_base()
    print(f"  {len(df):,} linhas", flush=True)

    # --- Mensal ---
    for doenca in ("dengue", "zika", "chikungunya"):
        print(f"  Juntando SINAN {doenca}...", flush=True)
        sinan = _sinan_prefixado(doenca)
        df = df.merge(sinan, on=["cod_ibge", "ano", "mes"], how="left")

    print("  Juntando febre amarela (MS dados abertos)...", flush=True)
    fa = pd.read_parquet(INTERIM / "febre_amarela.parquet").rename(columns={
        "casos":  "febre_amarela_casos",
        "obitos": "febre_amarela_obitos",
    })
    df = df.merge(fa, on=["cod_ibge", "ano", "mes"], how="left")

    print("  Juntando NASA POWER...", flush=True)
    df = df.merge(
        pd.read_parquet(INTERIM / "nasa_power.parquet"),
        on=["cod_ibge", "ano", "mes"], how="left",
    )

    print("  Juntando saúde (CNES/SIM)...", flush=True)
    saude = pd.read_parquet(INTERIM / "saude.parquet").rename(columns={
        "leitos_sus":      "leitos_publicos",
        "obitos_maternos": "mortalidade_materna",
    })
    df = df.merge(saude, on=["cod_ibge", "ano", "mes"], how="left")

    # --- Anual ---
    print("  Juntando IBGE (PIB, pop, GINI)...", flush=True)
    ibge = pd.read_parquet(INTERIM / "ibge.parquet").rename(columns={
        "pop_estimada":  "populacao_estimada",
        "gini_2010":     "gini",
    })
    df = df.merge(ibge, on=["cod_ibge", "ano"], how="left")

    print("  Juntando socioeconômico (CAPAG, IDH-M)...", flush=True)
    socio = pd.read_parquet(INTERIM / "socioeconomico.parquet")
    socio = socio.dropna(subset=["ano"]).copy()
    socio["ano"] = socio["ano"].astype(int)
    socio = socio.rename(columns={"idhm_2010": "idhm"})
    df = df.merge(socio, on=["cod_ibge", "ano"], how="left")

    print("  Juntando SINISA (água e esgoto)...", flush=True)
    sinisa = pd.read_parquet(INTERIM / "sinisa.parquet").rename(columns={
        "atend_agua_total_pct":   "iag0001_atend_agua_pct",
        "atend_esgoto_total_pct": "ies0001_atend_esgoto_pct",
        "atend_esgoto_trat_pct":  "ies2004_esgoto_tratado_pct",
    })
    df = df.merge(sinisa, on=["cod_ibge", "ano"], how="left")

    # --- Estático ---
    print("  Juntando MUNIC (gestão e desastres)...", flush=True)
    df = df.merge(
        pd.read_parquet(INTERIM / "munic.parquet"),
        on="cod_ibge", how="left",
    )

    print("  Juntando habitação (favelas/aglomerados)...", flush=True)
    df = df.merge(
        pd.read_parquet(INTERIM / "habitacao.parquet"),
        on="cod_ibge", how="left",
    )

    print("  Juntando densidade populacional (área IBGE)...", flush=True)
    df = df.merge(
        pd.read_parquet(INTERIM / "densidade.parquet"),
        on="cod_ibge", how="left",
    )

    print("  Juntando MapBiomas (uso do solo)...", flush=True)
    df = df.merge(
        pd.read_parquet(INTERIM / "mapbiomas.parquet"),
        on=["cod_ibge", "ano"], how="left",
    )

    print("  Juntando ESF (cobertura APS, e-Gestor MS)...", flush=True)
    df = df.merge(
        pd.read_parquet(INTERIM / "esf.parquet"),
        on=["cod_ibge", "ano", "mes"], how="left",
    )

    print("  Juntando vacinação febre amarela (PNI/DATASUS)...", flush=True)
    df = df.merge(
        pd.read_parquet(INTERIM / "vacinacao_fa.parquet"),
        on=["cod_ibge", "ano"], how="left",
    )

    # Ordenação canônica antes do forward-fill (importante para o ffill respeitar a ordem)
    df = df.sort_values(["cod_ibge", "ano", "mes"]).reset_index(drop=True)

    # População 2024-2025: IBGE só publica até 2023. Ver decisão metodológica no docstring.
    print("  Forward-fill populacao_estimada para 2024-2025...", flush=True)
    df["populacao_estimada"] = df.groupby("cod_ibge")["populacao_estimada"].ffill()

    # Vacinação FA: PNI tem gap em 2017 dentro da janela 2015-2025 (CSV não cobre o ano).
    # Forward-fill é seguro: cobertura vacinal varia <5p.p. interanualmente em períodos sem
    # campanha, e 2017 não teve mudança brusca da política nacional para SP.
    print("  Forward-fill cob_vac_fa_pct para preencher gap de 2017...", flush=True)
    df["cob_vac_fa_pct"] = df.groupby("cod_ibge")["cob_vac_fa_pct"].ffill()

    # MapBiomas só publica até 2024. Para 2025, ffill (cobertura do solo é estável ano a ano).
    print("  Forward-fill MapBiomas para 2025...", flush=True)
    cols_mb = [c for c in df.columns if c.startswith("pct_")
               and c not in ("pct_pop_favelas_2022", "pop_aglom_subnorm_2010")]
    cols_mb = [c for c in cols_mb if c in df.columns and not c.startswith("pop_")]
    for c in cols_mb:
        df[c] = df.groupby("cod_ibge")[c].ffill()
    # pib_per_capita também recalculado depois do ffill quando pib_mil_reais existir
    # (mas pib_mil_reais permanece NaN para 2024-2025; OK — variável separada)

    return df


def _relatorio(df: pd.DataFrame) -> None:
    print(f"\nShape final: {df.shape}")
    print(f"Municípios: {df['cod_ibge'].nunique()}")
    print(f"Anos: {sorted(df['ano'].unique())}")
    print(f"Colunas ({len(df.columns)}): {list(df.columns)}")
    print("\nCompletude (% não-nulo):")
    pct = (df.notna().mean() * 100).round(1)
    for col, v in pct.items():
        bar = "█" * int(v / 5)
        print(f"  {col:<40} {v:5.1f}%  {bar}")


if __name__ == "__main__":
    df = build()
    out = PROCESSED / "municipio_mes.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"\nGravado {len(df):,} linhas em {out}")
    _relatorio(df)
