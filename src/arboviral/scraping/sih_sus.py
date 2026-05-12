"""
Coleta: SIH-SUS — internações por arboviroses (CID A90/A91/A92/A95).

Fonte oficial:
  ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/
  Acessível também via HTTPS pelo mesmo path (FTP-over-HTTP wrapper).

Arquivos: RDSP{AAMM}.dbc — um por mês, contendo as AIH-RD (Autorização de
Internação Hospitalar — Reduzido) processadas no município de residência
do paciente. RD = registro "reduzido", versão consolidada das AIH.

Tamanho típico: ~15 MB por mês para SP → ~2 GB para a janela 2015–2025
(132 meses). Idempotente: arquivos já baixados não são re-baixados a
menos que `--sobrescrever`.

Por que SIH-SUS adicional ao SINAN:
  - SINAN registra notificação por doença (cobertura: caso reconhecido
    pelo sistema de vigilância).
  - SIH-SUS registra internação hospitalar (cobertura: caso grave que
    precisou de leito SUS). É proxy de severidade.
  - SIH-SUS inclui residentes de SP internados em qualquer município
    do Brasil — captura também migração para tratamento.

Data de coleta documentada: 2026-05-12.

Saída: data/raw/sih_sus/RDSP{AAMM}.dbc

Uso:
    python -m arboviral.scraping.sih_sus
    python -m arboviral.scraping.sih_sus --ano 2024
    python -m arboviral.scraping.sih_sus --sobrescrever
"""
from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path

from arboviral.io import RAW

FTP_BASE = "ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados"
UF = "SP"
PASTA_DESTINO = RAW / "sih_sus"
PAUSA_S = 1.0  # cortesia entre requests


def _arquivo_mes(ano: int, mes: int) -> str:
    return f"RD{UF}{str(ano)[-2:]}{mes:02d}.dbc"


def _baixar_um(ano: int, mes: int, sobrescrever: bool = False) -> bool:
    """Baixa um arquivo mensal RDSP{AAMM}.dbc.

    Retorna True se baixou (ou já existia) com sucesso, False se falhou.
    """
    arquivo = _arquivo_mes(ano, mes)
    destino = PASTA_DESTINO / arquivo
    destino.parent.mkdir(parents=True, exist_ok=True)

    if destino.exists() and not sobrescrever:
        size_mb = destino.stat().st_size / 1_048_576
        print(f"  já existe: {arquivo} ({size_mb:.1f} MB)")
        return True

    url = f"{FTP_BASE}/{arquivo}"
    result = subprocess.run(
        ["curl", "-s", "--max-time", "600", url, "-o", str(destino)],
        capture_output=True,
    )
    # FTP do DATASUS retorna 0 mesmo quando o arquivo não existe, gerando
    # arquivos vazios ou de poucos bytes. Validar o tamanho mínimo.
    if result.returncode != 0 or destino.stat().st_size < 1000:
        destino.unlink(missing_ok=True)
        print(f"  falhou: {arquivo}")
        return False
    size_mb = destino.stat().st_size / 1_048_576
    print(f"  ok: {arquivo} ({size_mb:.1f} MB)")
    return True


def baixar(ano_inicio: int = 2015, ano_fim: int = 2025,
           sobrescrever: bool = False) -> tuple[int, int]:
    """Baixa todos os arquivos mensais da janela.

    Retorna (n_baixados_ok, n_falharam).
    """
    ok = falhou = 0
    primeiro = True
    for ano in range(ano_inicio, ano_fim + 1):
        for mes in range(1, 13):
            if not primeiro:
                time.sleep(PAUSA_S)
            primeiro = False
            if _baixar_um(ano, mes, sobrescrever):
                ok += 1
            else:
                falhou += 1
    return ok, falhou


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Baixa SIH-SUS (AIH-RD) mensal para SP do FTP DATASUS."
    )
    parser.add_argument(
        "--ano", type=int, default=None,
        help="Apenas um ano específico (padrão: 2015-2025).",
    )
    parser.add_argument(
        "--sobrescrever", action="store_true",
        help="Re-baixa mesmo se o arquivo local já existir.",
    )
    args = parser.parse_args()

    if args.ano is not None:
        ok, falhou = baixar(args.ano, args.ano, args.sobrescrever)
    else:
        ok, falhou = baixar(sobrescrever=args.sobrescrever)
    print(f"\nResumo: {ok} arquivos OK, {falhou} falharam.")


if __name__ == "__main__":
    main()
