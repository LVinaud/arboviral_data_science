"""
Coleta: mobilidade pendular intermunicipal SP — duas vintages.

Duas fontes complementares, ambas oficiais do IBGE:

  CENSO 2010 — Microdados da Amostra (para reconstruir matriz origem-destino)
    URL: https://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Resultados_Gerais_da_Amostra/Microdados/
    Arquivos baixados:
      SP1.zip            ~136 MB  Interior + Capital (fora da RM)
      SP2_RM.zip          ~67 MB  Região Metropolitana de São Paulo
      Documentacao.zip    ~10 MB  Layout fixed-width
    Permite calcular AMBAS as features (entram + saem) via matriz O-D.

  CENSO 2022 — Tabela SIDRA 10329 (apenas agregado de saídas)
    URL: https://sidra.ibge.gov.br/tabela/10329
    API: https://servicodados.ibge.gov.br/api/v3/agregados/10329/...
    Variável 13373, classificador C469 categoria 12188 ("Outro município").
    Permite calcular APENAS pendulares_saem_trabalho. Não há tabela do
    Censo 2022 com município de destino (microdados ainda não públicos
    em maio/2026), então pendulares_entram_trabalho fica NaN para 2022+.

Data de coleta documentada: 2026-05-12.

Estratégia temporal no master (ver ingestion/mobilidade_pendular.py):
  anos 2015-2021 → snapshot Censo 2010 para AMBAS as colunas
  anos 2022-2025 → snapshot Censo 2022 para `pendulares_saem_trabalho`;
                   `pendulares_entram_trabalho` fica NaN.

Saídas em data/raw/mobilidade_pendular/:
  SP1.zip, SP2_RM.zip, Documentacao.zip            (Censo 2010 microdados)
  sidra_10329_saidas_2022.json                      (Censo 2022 SIDRA)

Uso:
    python -m arboviral.scraping.mobilidade_pendular
    python -m arboviral.scraping.mobilidade_pendular --sobrescrever
"""
from __future__ import annotations

import argparse
import time
import urllib.request
from pathlib import Path

from arboviral.io import RAW

# --- Censo 2010 microdados ---
URL_BASE_2010 = (
    "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/"
    "Resultados_Gerais_da_Amostra/Microdados"
)
ARQUIVOS_2010 = ["SP1.zip", "SP2_RM.zip", "Documentacao.zip"]

# --- Censo 2022 SIDRA tabela 10329 ---
# Tabela 10329: "Pessoas... ocupadas... por local de exercício do trabalho
# principal" — agrega por município de residência. Pegamos a categoria
# "Outro município" (id 12188) com totais nos demais classificadores
# (sexo, classe de renda, retorno semanal).
URL_SIDRA_10329 = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/10329/"
    "periodos/2022/variaveis/13373"
    "?localidades=N6[N3[35]]"
    "&classificacao=469[12188]|2[6794]|386[9680]|2087[79177]"
)
ARQUIVO_SIDRA = "sidra_10329_saidas_2022.json"

PASTA_DESTINO = RAW / "mobilidade_pendular"
PAUSA_S = 1.0  # cortesia entre requests


def _baixar_url(url: str, destino: Path, sobrescrever: bool, timeout: int = 600) -> Path:
    """Baixa uma URL para destino, com idempotência."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists() and not sobrescrever:
        tam_kb = destino.stat().st_size / 1024
        print(f"  já existe: {destino.name} ({tam_kb:.0f} KB)")
        return destino

    print(f"  baixando: {url}", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp, open(destino, "wb") as f:
        f.write(resp.read())
    tam_kb = destino.stat().st_size / 1024
    print(f"  ok: {destino.name} ({tam_kb:.0f} KB)")
    return destino


def baixar(sobrescrever: bool = False) -> list[Path]:
    """Baixa os 3 ZIPs do Censo 2010 + o JSON SIDRA do Censo 2022."""
    arquivos = []

    print("Censo 2010 — microdados da amostra...")
    for i, arq in enumerate(ARQUIVOS_2010):
        if i > 0:
            time.sleep(PAUSA_S)
        arquivos.append(_baixar_url(
            url=f"{URL_BASE_2010}/{arq}",
            destino=PASTA_DESTINO / arq,
            sobrescrever=sobrescrever,
        ))

    time.sleep(PAUSA_S)
    print("Censo 2022 — SIDRA tabela 10329 (saídas pendulares de trabalho)...")
    arquivos.append(_baixar_url(
        url=URL_SIDRA_10329,
        destino=PASTA_DESTINO / ARQUIVO_SIDRA,
        sobrescrever=sobrescrever,
        timeout=60,
    ))

    return arquivos


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Baixa microdados da amostra do Censo 2010 (matriz O-D) "
                    "e agregados de saída do Censo 2022 via SIDRA (tabela 10329)."
    )
    parser.add_argument(
        "--sobrescrever", action="store_true",
        help="Re-baixa mesmo se o arquivo local já existir.",
    )
    args = parser.parse_args()
    baixar(args.sobrescrever)


if __name__ == "__main__":
    main()
