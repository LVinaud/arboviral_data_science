"""
Ingestão: IBGE MUNIC — gestão/vigilância (2018), desastres naturais e
          moradia em risco ambiental (2020).

Fonte: Pesquisa de Informações Básicas Municipais (MUNIC) — IBGE.
Periodicidade: estática (uma resposta por município por edição da pesquisa).

Arquivos em data/raw/munic/:
    Base_MUNIC_2018_xlsx_20201103.xlsx  → aba "Saúde"       → MSAU28, MSAU541-543
    Base_MUNIC_2020.xlsx                → aba "Gestão de riscos" → MGRD01,06,07,08,11,14,201
                                        → aba "Meio ambiente"    → MMAM2612

Saída: data/interim/munic.parquet
Chave: cod_ibge (7 dígitos IBGE — fornecidos diretamente nas planilhas MUNIC)
Colunas bool (True/False/NaN):
    msau28_pacs, msau541_vig_sanitaria, msau542_vig_epidemiologica, msau543_controle_endemias
    mgrd01_seca, mgrd06_alagamento, mgrd07_erosao, mgrd08_enchente_gradual,
    mgrd11_enxurrada, mgrd14_deslizamento, mgrd201_mapeamento_risco
    mmam2612_moradia_risco

Nota: "Não sabe" é mapeado para NaN (desconhecido), não False.
Leitura via calamine (engine Rust) para baixo consumo de RAM.
"""
import pandas as pd

from arboviral.io import INTERIM, RAW

_SIM_NAO = {"Sim": True, "Não": False, "Nao": False}  # "Não sabe" → NaN


def _sim_nao(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().map(_SIM_NAO)


def _ler_aba(arquivo: str, aba: str, colunas_alvo: list[str]) -> pd.DataFrame:
    """Lê aba do MUNIC via calamine, filtra para SP, retorna apenas colunas_alvo + cod_ibge.

    Linha 0 = códigos de variável, linha 1 = nomes descritivos, linhas 2+ = dados.
    O código de município nas planilhas MUNIC já vem com 7 dígitos IBGE.
    """
    caminho = str(RAW / "munic" / arquivo)
    df_raw = pd.read_excel(caminho, sheet_name=aba, header=None, engine="calamine")

    codigos = df_raw.iloc[0].tolist()
    df = df_raw.iloc[2:].copy()
    df.columns = codigos
    del df_raw

    cod_col = next(
        (c for c in codigos if isinstance(c, str) and "cod" in c.lower() and "mun" in c.lower()),
        codigos[0],
    )

    df = df[[cod_col] + colunas_alvo].copy()
    df[cod_col] = df[cod_col].astype(str).str.strip()
    df = df[df[cod_col].str.startswith("35")].reset_index(drop=True)
    df["cod_ibge"] = df[cod_col].astype(int)
    df = df.drop(columns=[cod_col])
    return df


def build() -> pd.DataFrame:
    # ── MUNIC 2018: vigilância em saúde ──────────────────────────────────────
    print("  Lendo MUNIC 2018 Saúde...", flush=True)
    df18 = _ler_aba(
        "Base_MUNIC_2018_xlsx_20201103.xlsx", "Saúde",
        ["MSAU28", "MSAU541", "MSAU542", "MSAU543"],
    )
    vigilancia = pd.DataFrame({
        "cod_ibge": df18["cod_ibge"],
        "msau28_pacs": _sim_nao(df18["MSAU28"]),
        "msau541_vig_sanitaria": _sim_nao(df18["MSAU541"]),
        "msau542_vig_epidemiologica": _sim_nao(df18["MSAU542"]),
        "msau543_controle_endemias": _sim_nao(df18["MSAU543"]),
    })
    del df18

    # ── MUNIC 2020: desastres naturais ───────────────────────────────────────
    print("  Lendo MUNIC 2020 Gestão de riscos...", flush=True)
    df20r = _ler_aba(
        "Base_MUNIC_2020.xlsx", "Gestão de riscos",
        ["Mgrd01", "Mgrd06", "Mgrd07", "Mgrd08", "Mgrd11", "Mgrd14", "Mgrd201"],
    )
    desastres = pd.DataFrame({
        "cod_ibge": df20r["cod_ibge"],
        "mgrd01_seca": _sim_nao(df20r["Mgrd01"]),
        "mgrd06_alagamento": _sim_nao(df20r["Mgrd06"]),
        "mgrd07_erosao": _sim_nao(df20r["Mgrd07"]),
        "mgrd08_enchente_gradual": _sim_nao(df20r["Mgrd08"]),
        "mgrd11_enxurrada": _sim_nao(df20r["Mgrd11"]),
        "mgrd14_deslizamento": _sim_nao(df20r["Mgrd14"]),
        "mgrd201_mapeamento_risco": _sim_nao(df20r["Mgrd201"]),
    })
    del df20r

    # ── MUNIC 2020: moradia em risco ambiental ───────────────────────────────
    print("  Lendo MUNIC 2020 Meio ambiente...", flush=True)
    df20m = _ler_aba("Base_MUNIC_2020.xlsx", "Meio ambiente", ["Mmam2612"])
    moradia = pd.DataFrame({
        "cod_ibge": df20m["cod_ibge"],
        "mmam2612_moradia_risco": _sim_nao(df20m["Mmam2612"]),
    })
    del df20m

    # ── Join ─────────────────────────────────────────────────────────────────
    resultado = (
        vigilancia
        .merge(desastres, on="cod_ibge", how="outer")
        .merge(moradia, on="cod_ibge", how="outer")
        .sort_values("cod_ibge")
        .reset_index(drop=True)
    )
    return resultado


if __name__ == "__main__":
    df = build()
    out = INTERIM / "munic.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Gravado {len(df):,} municípios em {out}")
    print(df.head())
    print("\nCompletude por coluna:")
    print(df.notna().sum().to_string())
