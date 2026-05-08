"""
Coleta: MapBiomas Brasil — Cobertura e uso da terra (Coleção 10.1).

Fonte: https://brasil.mapbiomas.org/estatisticas/
Arquivo: BIOMAS, ESTADOS E MUNICÍPIOS (Coleção 10.1) — COBERTURA
DOI: https://doi.org/10.58053/MapBiomas/SJZOLT

Dados de área (hectares) por classe de cobertura/uso da terra para o
cruzamento bioma × estado × município, 1985-2024.

Saída: data/raw/mapbiomas/MAPBIOMAS_COVERAGE_COL_10_1.xlsx (~80 MB)

URL de download: Google Drive (~80 MB)
  ID do arquivo: 1p0dLrhvKymPhrSithsRBMRgHlFHq0FUf
  URL direta: https://drive.google.com/uc?export=download&id=<ID>

Aviso: o link do MapBiomas pode mudar entre coleções. Caso o download
falhe, conferir o ID na página oficial https://brasil.mapbiomas.org/estatisticas/
e atualizar a constante DRIVE_FILE_ID.

Uso:
    python -m arboviral.scraping.mapbiomas
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

from arboviral.io import RAW

DRIVE_FILE_ID = "1p0dLrhvKymPhrSithsRBMRgHlFHq0FUf"  # Coleção 10.1, atualização 2026-02-19
URL = f"https://drive.google.com/uc?export=download&id={DRIVE_FILE_ID}"
PASTA_DESTINO = RAW / "mapbiomas"
NOME_ARQUIVO = "MAPBIOMAS_COVERAGE_COL_10_1.xlsx"


def baixar() -> Path:
    """Baixa o XLSX de cobertura municipal do MapBiomas Coleção 10.1."""
    PASTA_DESTINO.mkdir(parents=True, exist_ok=True)
    arquivo = PASTA_DESTINO / NOME_ARQUIVO

    if arquivo.exists():
        print(f"  já existe: {arquivo.name} ({arquivo.stat().st_size / 1_048_576:.1f} MB)")
        return arquivo

    print(f"  baixando: {URL}", flush=True)
    print("  ⚠ arquivo grande (~80 MB), pode levar 1-3 minutos...", flush=True)
    urllib.request.urlretrieve(URL, arquivo)
    size_mb = arquivo.stat().st_size / 1_048_576
    print(f"  ok: {arquivo.name} ({size_mb:.1f} MB)")
    return arquivo


if __name__ == "__main__":
    baixar()
