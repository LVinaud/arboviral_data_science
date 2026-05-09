"""
Script utilitário de validação — não é importado pelo app.

Compara as chaves de pt.py e en.py recursivamente. Imprime as ausências
e termina com código de saída 1 se houver divergência.

Uso:
    python -m i18n._validar      # rodar a partir de app/
"""
from __future__ import annotations

import sys
from typing import Iterator

from i18n import en, pt


def _chaves(d: dict, prefixo: str = "") -> Iterator[str]:
    for k, v in d.items():
        caminho = f"{prefixo}.{k}" if prefixo else k
        if isinstance(v, dict):
            yield from _chaves(v, caminho)
        else:
            yield caminho


def main() -> int:
    chaves_pt = set(_chaves(pt.STRINGS))
    chaves_en = set(_chaves(en.STRINGS))

    so_em_pt = sorted(chaves_pt - chaves_en)
    so_em_en = sorted(chaves_en - chaves_pt)

    if not so_em_pt and not so_em_en:
        print(f"OK — {len(chaves_pt)} chaves em paridade entre pt.py e en.py.")
        return 0

    if so_em_pt:
        print(f"\n[!] {len(so_em_pt)} chaves só em pt.py (faltam em en.py):")
        for c in so_em_pt:
            print(f"    - {c}")
    if so_em_en:
        print(f"\n[!] {len(so_em_en)} chaves só em en.py (faltam em pt.py):")
        for c in so_em_en:
            print(f"    - {c}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
