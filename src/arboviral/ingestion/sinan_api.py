"""
Coletor: API de Dados Abertos do Ministério da Saúde — Arboviroses (SINAN).

Endpoint base: https://apidadosabertos.saude.gov.br/v1/arboviroses
Doenças suportadas: dengue, zika, chikungunya

Uso:
    python -m arboviral.ingestion.sinan_api               # todos os anos e doenças
    python -m arboviral.ingestion.sinan_api --doenca dengue --ano 2023

Saída (data/raw/sinan/):
    dengue_<ano>.csv
    zika_<ano>.csv
    chikungunya_<ano>.csv

Os arquivos são gravados crus (exatamente como a API retorna) para que o parser
em sinan.py possa lê-los offline sem depender de conectividade.

Referência Swagger:
    https://apidadosabertos.saude.gov.br/v1/#/Agravo%20Arboviroses
"""
import argparse
import time
from pathlib import Path

import pandas as pd
import requests

from arboviral.io import RAW

BASE_URL = "https://apidadosabertos.saude.gov.br/v1/arboviroses"
DOENCAS = ("dengue", "zika", "chikungunya")
ANOS_DEFAULT = list(range(2015, 2026))
LIMIT = 1000  # registros por página


def _buscar_pagina(doenca: str, ano: int, offset: int) -> dict:
    url = f"{BASE_URL}/{doenca}"
    params = {"ano_ini": ano, "ano_fim": ano, "limit": LIMIT, "offset": offset}
    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def coletar(doenca: str, ano: int, destino: Path | None = None) -> Path:
    """Baixa todos os registros de uma doença/ano e salva em CSV.

    Retorna o caminho do arquivo gravado.
    """
    destino = destino or RAW / "sinan"
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / f"{doenca}_{ano}.csv"

    if caminho.exists():
        print(f"  já existe: {caminho.name} — pulando")
        return caminho

    registros = []
    offset = 0
    while True:
        try:
            dados = _buscar_pagina(doenca, ano, offset)
        except requests.HTTPError as exc:
            if exc.response.status_code == 404:
                print(f"  sem dados: {doenca} {ano} (404)")
                break
            raise

        # a API pode retornar {'dados': [...]} ou uma lista direta
        lote = dados.get("dados") or dados if isinstance(dados, list) else []
        if not lote:
            break
        registros.extend(lote)
        offset += len(lote)
        if len(lote) < LIMIT:
            break
        time.sleep(0.3)  # respeitar o rate-limit do servidor

    if not registros:
        print(f"  nenhum registro: {doenca} {ano}")
        return caminho

    pd.DataFrame(registros).to_csv(caminho, index=False)
    print(f"  gravado {len(registros):,} linhas → {caminho.name}")
    return caminho


def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta dados SINAN via API pública")
    parser.add_argument("--doenca", choices=DOENCAS, default=None)
    parser.add_argument("--ano", type=int, default=None)
    args = parser.parse_args()

    doencas = [args.doenca] if args.doenca else list(DOENCAS)
    anos = [args.ano] if args.ano else ANOS_DEFAULT

    for doenca in doencas:
        for ano in anos:
            print(f"Coletando {doenca} {ano}...")
            coletar(doenca, ano)


if __name__ == "__main__":
    main()
