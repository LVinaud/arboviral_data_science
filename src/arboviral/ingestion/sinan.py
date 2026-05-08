"""
Ingestão: SINAN — arboviroses (dengue, zika, chikungunya).

Fonte: FTP DATASUS — /dissemin/publicos/SINAN/DADOS/{FINAIS,PRELIM}/
Arquivos: DENGBR{AA}.dbc, ZIKABR{AA}.dbc, CHIKBR{AA}.dbc (2015–presente)

Para baixar os arquivos brutos:
    python -m arboviral.ingestion.sinan_ftp   (script de download via curl/FTP)

Dependências: pyreaddbc, dbfread

Saída:
    data/interim/sinan_dengue.parquet
    data/interim/sinan_zika.parquet
    data/interim/sinan_chikungunya.parquet

Chave: (cod_ibge, ano, mes)   — somente SP (SG_UF == '35')

Sobre os campos SINAN:
    ID_MN_RESI : código do município de RESIDÊNCIA (6 dígitos DATASUS = 7 dígitos IBGE sem o último)
    CLASSI_FIN : dengue → '10'/'11'/'12' = caso confirmado, '5' = descartado
                 chikungunya → '13' = confirmado, '5' = descartado
                 zika → '2' = confirmado, '5' = descartado
    EVOLUCAO   : '2'/'3'/'4' = óbito (por doença, outra causa, em investigação)
    HOSPITALIZ : '1' = sim (presente apenas em dengue e chikungunya)
    DT_NOTIFIC : data de notificação ao SINAN
    DT_SIN_PRI : data dos primeiros sintomas

Latência (proxy de qualidade da vigilância):
    delta_dias = DT_NOTIFIC - DT_SIN_PRI por caso individual.
    Filtramos valores absurdos (negativo ou > 365 dias).
    Agregamos por (município, mês de notificação) em mediana e p90.
    Latência alta indica subnotificação / atraso na detecção, e o modelo
    pode usar isso como sinal de risco mesmo quando casos contagem está baixa.
"""
import re
from pathlib import Path

import dbfread
import pandas as pd
from pyreaddbc import dbc2dbf

from arboviral.io import INTERIM, LOOKUP, RAW

# código IBGE 6d → 7d: o campo do DATASUS é o código IBGE 7 dígitos sem o último dígito
_LOOKUP_6_PARA_7: dict[str, int] | None = None


def _lookup_6d_para_7d() -> dict[str, int]:
    global _LOOKUP_6_PARA_7
    if _LOOKUP_6_PARA_7 is not None:
        return _LOOKUP_6_PARA_7
    xl = LOOKUP / "municipios_sp_estacoes_inmet.xlsx"
    df = pd.read_excel(xl)
    col7 = "Código Município Completo"
    _LOOKUP_6_PARA_7 = {str(int(v))[:-1]: int(v) for v in df[col7].dropna().astype(int)}
    return _LOOKUP_6_PARA_7


def _parse_data(valor) -> "datetime.date | None":
    """Aceita datetime.date ou string YYYYMMDD; devolve date ou None."""
    import datetime
    if isinstance(valor, datetime.date):
        return valor
    if isinstance(valor, str) and len(valor) >= 8:
        try:
            return datetime.date(int(valor[:4]), int(valor[4:6]), int(valor[6:8]))
        except ValueError:
            return None
    return None


def _agregar_dbc_streaming(
    caminho_dbc: Path,
    doenca: str,
    lookup: dict[str, int],
    filtrar_uf: str = "35",
) -> pd.DataFrame:
    """Converte DBC → agregado município-mês sem acumular registros individuais em RAM.

    Itera o DBF registro a registro, filtrando para a UF indicada, e acumula
    apenas contagens (dicts), evitando OOM em arquivos grandes (ex.: DENGBR24, 287 MB).

    Também agrega LATÊNCIAS (DT_NOTIFIC - DT_SIN_PRI) em listas por chave para
    cálculo de mediana/p90 ao final — proxy de qualidade da vigilância.
    """
    from collections import defaultdict

    caminho_dbf = caminho_dbc.with_suffix(".dbf")
    try:
        dbc2dbf(str(caminho_dbc), str(caminho_dbf))
        table = dbfread.DBF(str(caminho_dbf), load=False, encoding="latin1")

        # acumuladores: chave = (cod_ibge, ano, mes)
        notificados: defaultdict = defaultdict(int)
        provaveis: defaultdict = defaultdict(int)
        obitos: defaultdict = defaultdict(int)
        internacoes: defaultdict = defaultdict(int)
        # latências em dias por (cod_ibge, ano_notif, mes_notif)
        latencias: defaultdict = defaultdict(list)
        tem_hospitaliz = False

        for rec in table:
            if str(rec.get("SG_UF", "")).strip() != filtrar_uf:
                continue

            cod6 = str(rec.get("ID_MN_RESI", "")).strip().zfill(6)
            cod7 = lookup.get(cod6)
            if cod7 is None:
                continue

            dt_notif = _parse_data(rec.get("DT_NOTIFIC"))
            if dt_notif is None:
                continue
            ano, mes = dt_notif.year, dt_notif.month
            chave = (cod7, ano, mes)

            notificados[chave] += 1

            # Latência = DT_NOTIFIC - DT_SIN_PRI (em dias)
            # Filtrar valores absurdos: < 0 (data inconsistente) e > 365 (provavelmente erro)
            dt_sin = _parse_data(rec.get("DT_SIN_PRI"))
            if dt_sin is not None:
                delta = (dt_notif - dt_sin).days
                if 0 <= delta <= 365:
                    latencias[chave].append(delta)

            cf = str(rec.get("CLASSI_FIN", "")).strip()
            if _casos_confirmados_mask_rec(cf, doenca):
                provaveis[chave] += 1

            ev = str(rec.get("EVOLUCAO", "")).strip()
            if ev in ("2", "3", "4"):
                obitos[chave] += 1

            hosp = str(rec.get("HOSPITALIZ", "")).strip()
            if hosp:
                tem_hospitaliz = True
                if hosp == "1":
                    internacoes[chave] += 1

        if not notificados:
            return pd.DataFrame()

        chaves = sorted(notificados)
        # Estatísticas de latência: mediana + p90; NaN quando sem latências válidas
        import numpy as np
        med_lat = []
        p90_lat = []
        n_validas = []
        for k in chaves:
            lats = latencias.get(k, [])
            if lats:
                med_lat.append(float(np.median(lats)))
                p90_lat.append(float(np.percentile(lats, 90)))
                n_validas.append(len(lats))
            else:
                med_lat.append(float("nan"))
                p90_lat.append(float("nan"))
                n_validas.append(0)

        rows = {
            "cod_ibge": [k[0] for k in chaves],
            "ano": [k[1] for k in chaves],
            "mes": [k[2] for k in chaves],
            "casos_notificados": [notificados[k] for k in chaves],
            "casos_provaveis": [provaveis[k] for k in chaves],
            "obitos": [obitos[k] for k in chaves],
            "internacoes": [internacoes.get(k, float("nan")) if tem_hospitaliz else float("nan") for k in chaves],
            "latencia_mediana_dias": med_lat,
            "latencia_p90_dias": p90_lat,
            "n_casos_com_latencia": n_validas,
        }
        return pd.DataFrame(rows)
    finally:
        caminho_dbf.unlink(missing_ok=True)


def _casos_confirmados_mask_rec(classi_fin: str, doenca: str) -> bool:
    if doenca == "dengue":
        return classi_fin in ("10", "11", "12")
    if doenca == "chikungunya":
        return classi_fin == "13"
    if doenca == "zika":
        return classi_fin == "2"
    return False



def build(doenca: str = "dengue") -> pd.DataFrame:
    """Lê todos os DBC disponíveis para a doença e retorna o agregado SP município–mês.

    doenca: 'dengue', 'zika' ou 'chikungunya'

    Usa leitura streaming registro a registro para evitar OOM em arquivos grandes
    (ex.: DENGBR24 tem 287 MB comprimido → ~2 M registros SP em 2024).
    """
    prefixo = {"dengue": "DENGBR", "zika": "ZIKABR", "chikungunya": "CHIKBR"}[doenca]
    pasta_raw = RAW / "sinan"
    lookup = _lookup_6d_para_7d()

    arquivos = sorted(pasta_raw.glob(f"{prefixo}*.dbc"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo {prefixo}*.dbc em {pasta_raw}")

    partes = []
    for arq in arquivos:
        print(f"  Processando {arq.name}...")
        df_agg = _agregar_dbc_streaming(arq, doenca, lookup)
        if not df_agg.empty:
            partes.append(df_agg)

    if not partes:
        raise RuntimeError(f"Nenhum dado SP encontrado para {doenca}")

    # Agregação: cada chave (cod_ibge, ano, mes) aparece em apenas 1 arquivo DBC
    # (arquivos do FTP DATASUS são separados por ano de notificação), então
    # 'first' e 'sum' são equivalentes para chaves únicas — mas usar 'first'
    # nas estatísticas de latência é mais correto conceitualmente.
    return (
        pd.concat(partes, ignore_index=True)
        .groupby(["cod_ibge", "ano", "mes"], as_index=False)
        .agg({
            "casos_notificados":     "sum",
            "casos_provaveis":       "sum",
            "obitos":                "sum",
            "internacoes":           "sum",
            "latencia_mediana_dias": "first",
            "latencia_p90_dias":     "first",
            "n_casos_com_latencia":  "sum",
        })
        .sort_values(["cod_ibge", "ano", "mes"])
        .reset_index(drop=True)
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--doenca", default="dengue", choices=["dengue", "zika", "chikungunya"])
    args = parser.parse_args()

    df = build(args.doenca)
    out = INTERIM / f"sinan_{args.doenca}.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Gravado {len(df):,} linhas em {out}")
    print(df.head())
