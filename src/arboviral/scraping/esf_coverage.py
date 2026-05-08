"""
Coleta: Cobertura da Atenção Primária à Saúde (APS) — ex-Estratégia Saúde da Família.

Fonte: API REST do portal e-Gestor (relatorioaps-prd.saude.gov.br),
descoberta via DevTools do navegador. Endpoints retornam JSON estruturado
por município, sem necessidade de Selenium/JSF.

Há DOIS endpoints, com mesma assinatura de parâmetros:

    https://relatorioaps-prd.saude.gov.br/cobertura/ab    (relatório AB 2007-2020)
    https://relatorioaps-prd.saude.gov.br/cobertura/aps   (relatório APS 2021-atual)

Parâmetros (query string):
    unidadeGeografica=MUNICIPIO   granularidade desejada
    nuCompInicio=YYYYMM           competência inicial (mês)
    nuCompFim=YYYYMM              competência final (mês)

Retorna lista JSON com 1 registro por (município, competência) — todos os 5570
municípios brasileiros. Filtramos SP só na ingestão (mantendo raw integral
para reuso futuro em outros estados).

Estratégia: baixa mês a mês para não estourar timeout em períodos longos.
Cada arquivo ~3MB; total esperado ~400 MB para 132 meses (2015-01 a 2025-12).

Saída: data/raw/esf/cobertura_<endpoint>_<YYYYMM>.json
       endpoint = 'ab' (anos ≤ 2020) ou 'aps' (anos ≥ 2021)

Uso:
    python -m arboviral.scraping.esf_coverage                # baixa 2015-01 a 2025-12 (132 meses)
    python -m arboviral.scraping.esf_coverage --ano 2024     # baixa só um ano
    python -m arboviral.scraping.esf_coverage --comp 202005  # baixa um único mês
"""
from __future__ import annotations

import argparse
import time
import urllib.error
import urllib.request
from pathlib import Path

from arboviral.io import RAW

BASE_URL = "https://relatorioaps-prd.saude.gov.br/cobertura"
PASTA_DESTINO = RAW / "esf"

ANOS_AB = list(range(2015, 2021))    # 2015-2020 → endpoint /ab
ANOS_APS = list(range(2021, 2026))   # 2021-2025 → endpoint /aps


def _endpoint_para_ano(ano: int) -> str:
    """Anos ≤ 2020 → 'ab' (relatório antigo); ≥ 2021 → 'aps' (cobertura potencial)."""
    return "ab" if ano <= 2020 else "aps"


def baixar_competencia(ano: int, mes: int, sobrescrever: bool = False) -> Path | None:
    """Baixa o JSON de cobertura para uma competência específica (YYYYMM).

    Retorna o Path do arquivo gravado ou None se já existia (e não foi sobrescrito).
    """
    PASTA_DESTINO.mkdir(parents=True, exist_ok=True)
    endpoint = _endpoint_para_ano(ano)
    competencia = f"{ano}{mes:02d}"
    arquivo = PASTA_DESTINO / f"cobertura_{endpoint}_{competencia}.json"

    if arquivo.exists() and not sobrescrever:
        size_kb = arquivo.stat().st_size / 1024
        print(f"  já existe: {arquivo.name} ({size_kb:.0f} KB)", flush=True)
        return None

    url = (
        f"{BASE_URL}/{endpoint}"
        f"?unidadeGeografica=MUNICIPIO"
        f"&nuCompInicio={competencia}"
        f"&nuCompFim={competencia}"
    )
    try:
        urllib.request.urlretrieve(url, arquivo)
        size_kb = arquivo.stat().st_size / 1024
        print(f"  ok: {arquivo.name} ({size_kb:.0f} KB)", flush=True)
        return arquivo
    except urllib.error.URLError as e:
        print(f"  ERRO: {arquivo.name}: {e}", flush=True)
        if arquivo.exists() and arquivo.stat().st_size < 1000:
            arquivo.unlink()
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Baixa cobertura da APS/AB do e-Gestor MS")
    parser.add_argument("--ano", type=int, default=None,
                        help="Baixar só um ano específico (ex.: 2024)")
    parser.add_argument("--comp", type=str, default=None,
                        help="Baixar uma única competência (formato YYYYMM, ex.: 202405)")
    parser.add_argument("--sobrescrever", action="store_true",
                        help="Re-baixa arquivos que já existem")
    parser.add_argument("--pausa", type=float, default=1.0,
                        help="Pausa entre requests em segundos (padrão: 1.0)")
    args = parser.parse_args()

    if args.comp:
        ano = int(args.comp[:4])
        mes = int(args.comp[4:6])
        baixar_competencia(ano, mes, sobrescrever=args.sobrescrever)
        return

    anos = [args.ano] if args.ano else (ANOS_AB + ANOS_APS)
    total = len(anos) * 12
    contador = 0

    for ano in anos:
        endpoint = _endpoint_para_ano(ano)
        print(f"\n[{ano}] endpoint /{endpoint}", flush=True)
        for mes in range(1, 13):
            contador += 1
            print(f"  ({contador}/{total}) competência {ano}-{mes:02d}", flush=True)
            baixar_competencia(ano, mes, sobrescrever=args.sobrescrever)
            time.sleep(args.pausa)


if __name__ == "__main__":
    main()
