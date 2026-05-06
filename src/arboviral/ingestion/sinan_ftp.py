"""
Download: SINAN — arboviroses via FTP DATASUS.

Baixa os arquivos .dbc de dengue, zika e chikungunya diretamente do FTP do DATASUS,
que é a forma prática de obter os dados completos.

A API REST (apidadosabertos.saude.gov.br) retorna no máximo 20 registros por chamada
e não tem filtro por UF, tornando-a inviável para extração em massa.

Uso:
    python -m arboviral.ingestion.sinan_ftp                         # tudo (2015-2025)
    python -m arboviral.ingestion.sinan_ftp --doenca dengue         # só dengue
    python -m arboviral.ingestion.sinan_ftp --doenca zika --ano 2023

Arquivos gravados em data/raw/sinan/:
    DENGBR{AA}.dbc, ZIKABR{AA}.dbc, CHIKBR{AA}.dbc
"""
import argparse
import subprocess
from pathlib import Path

from arboviral.io import RAW

FTP_FINAIS = "ftp://ftp.datasus.gov.br/dissemin/publicos/SINAN/DADOS/FINAIS"
FTP_PRELIM = "ftp://ftp.datasus.gov.br/dissemin/publicos/SINAN/DADOS/PRELIM"

PREFIXOS = {"dengue": "DENGBR", "zika": "ZIKABR", "chikungunya": "CHIKBR"}

# Anos com dados finais (publicados) vs. preliminares
ANO_FINAL_ATE = 2024  # a partir de 2025 os dados são preliminares


def _yy(ano: int) -> str:
    return str(ano)[-2:]


def _baixar(url: str, destino: Path) -> bool:
    if destino.exists():
        print(f"  já existe: {destino.name}")
        return True
    result = subprocess.run(
        ["curl", "-s", "--max-time", "600", url, "-o", str(destino)],
        capture_output=True,
    )
    if result.returncode != 0 or destino.stat().st_size < 1000:
        destino.unlink(missing_ok=True)
        print(f"  falhou: {destino.name}")
        return False
    size_mb = destino.stat().st_size / 1_048_576
    print(f"  ok: {destino.name} ({size_mb:.1f} MB)")
    return True


def baixar(doenca: str, ano: int) -> bool:
    prefixo = PREFIXOS[doenca]
    arquivo = f"{prefixo}{_yy(ano)}.dbc"
    destino = RAW / "sinan" / arquivo
    destino.parent.mkdir(parents=True, exist_ok=True)

    ftp_base = FTP_FINAIS if ano <= ANO_FINAL_ATE else FTP_PRELIM
    url = f"{ftp_base}/{arquivo}"
    return _baixar(url, destino)


def main() -> None:
    parser = argparse.ArgumentParser(description="Baixa arquivos SINAN do FTP DATASUS")
    parser.add_argument("--doenca", choices=list(PREFIXOS), default=None)
    parser.add_argument("--ano", type=int, default=None)
    args = parser.parse_args()

    doencas = [args.doenca] if args.doenca else list(PREFIXOS)
    anos = [args.ano] if args.ano else list(range(2015, 2026))

    for doenca in doencas:
        for ano in anos:
            print(f"{doenca} {ano}...")
            baixar(doenca, ano)


if __name__ == "__main__":
    main()
