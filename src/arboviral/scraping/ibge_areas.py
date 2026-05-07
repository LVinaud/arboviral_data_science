"""
Coleta: IBGE — Áreas territoriais dos municípios (km²).

Fonte oficial:
  https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/areas_territoriais/

Estrutura: pasta por ano com arquivo XLS único contendo várias planilhas
(municípios, regiões intermediárias, regiões imediatas, UFs, regiões geográficas).

Padrão de nome: AR_BR_RG_UF_RGINT_RGI_MUN_<ANO>.xls

Saída: data/raw/ibge_areas/AR_BR_RG_UF_RGINT_RGI_MUN_<ANO>.xls

Uso:
    python -m arboviral.scraping.ibge_areas              # baixa o ano mais recente disponível
    python -m arboviral.scraping.ibge_areas --ano 2023   # baixa um ano específico
"""
from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

from arboviral.io import RAW

BASE_URL = "https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/areas_territoriais"
PASTA_DESTINO = RAW / "ibge_areas"


def _url_para_ano(ano: int) -> str:
    """Constrói a URL do XLS para o ano dado."""
    return f"{BASE_URL}/{ano}/AR_BR_RG_UF_RGINT_RGI_MUN_{ano}.xls"


def baixar(ano: int = 2024) -> Path:
    """Baixa o XLS de áreas para o ano informado.

    Retorna o Path do arquivo gravado.
    """
    PASTA_DESTINO.mkdir(parents=True, exist_ok=True)
    url = _url_para_ano(ano)
    arquivo = PASTA_DESTINO / f"AR_BR_RG_UF_RGINT_RGI_MUN_{ano}.xls"

    if arquivo.exists():
        print(f"  já existe: {arquivo.name} ({arquivo.stat().st_size / 1024:.0f} KB)")
        return arquivo

    print(f"  baixando: {url}", flush=True)
    urllib.request.urlretrieve(url, arquivo)
    print(f"  ok: {arquivo.name} ({arquivo.stat().st_size / 1024:.0f} KB)")
    return arquivo


def main() -> None:
    parser = argparse.ArgumentParser(description="Baixa áreas territoriais do IBGE")
    parser.add_argument("--ano", type=int, default=2024,
                        help="Ano de referência (padrão: 2024)")
    args = parser.parse_args()
    baixar(args.ano)


if __name__ == "__main__":
    main()
