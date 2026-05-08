"""
Coleta: Vacinação contra febre amarela — DATASUS PNI / inteli.gente.

Fonte primária: Programa Nacional de Imunizações (PNI/MS), publicado via
TabNet/DATASUS:
  http://tabnet.datasus.gov.br/cgi/tabcgi.exe?pni/cnv/cpniuf.def

A indicador-alvo é "Cobertura vacinal" (COB_VAC_FA) — % da população-alvo
imunizada contra febre amarela em cada município/ano. Denominador é a
população-alvo (faixas etárias indicadas) estimada pelo PNI; numerador é o
número de doses aplicadas. Valores >100% ocorrem ocasionalmente quando o
denominador estimado fica abaixo do número real de vacinados (migrações,
estimativas defasadas) — são preservados sem cap, com flag implícita pelo
próprio valor.

CSV utilizado: COB_VAC_FA.csv (formato adotado pela plataforma inteli.gente
do MCTI, com a qual o projeto se integrará). Estrutura:
  codigo_ibge | sigla       | ano  | variavel_valor
  1100023     | COB_VAC_FA  | 1994 | 30.36
  ...

Cobertura da série:
  - Brasil inteiro (27 UFs); filtraremos UF=35 (SP) na ingestão.
  - Anos disponíveis: 1994, 1997, 2002, 2004-2007, 2009, 2012-2013,
    2015-2016, 2018-2026 (gaps em 2008, 2010, 2011, 2014, 2017).
  - Para 2017, aplicamos forward-fill no build_master (estabilidade da
    cobertura inter-anual + ausência de surto silvestre que justificasse
    queda abrupta).

Como o CSV foi obtido originalmente do DATASUS PNI por consulta TabNet
(operação manual, formulário CGI sem endpoint REST estável), este módulo
opera em modo "verifica e documenta": confirma que o arquivo existe em
data/raw/febre_amarela/COB_VAC_FA.csv. Se não existir, imprime as
instruções de obtenção.

Saída: data/raw/febre_amarela/COB_VAC_FA.csv (já presente; preservado).
"""
from __future__ import annotations

from arboviral.io import RAW

ARQUIVO = RAW / "febre_amarela" / "COB_VAC_FA.csv"

INSTRUCOES = """
Para regerar COB_VAC_FA.csv (coleta manual via TabNet/DATASUS PNI):

  1. Acessar http://tabnet.datasus.gov.br/cgi/tabcgi.exe?pni/cnv/cpniuf.def
  2. Linha = Município; Coluna = Ano; Conteúdo = "Cobertura vacinal"
  3. Imunobiológico = "Febre amarela" (todas as faixas etárias somadas)
  4. Período = todos os anos disponíveis
  5. Exportar como CSV; reformatar para colunas
     codigo_ibge,sigla,ano,variavel_valor com sigla='COB_VAC_FA'

Alternativa: consulta SQL via BasedosDados (br_ms_pni dataset).
"""


def main() -> None:
    if ARQUIVO.exists():
        kb = ARQUIVO.stat().st_size / 1024
        print(f"  ok: {ARQUIVO.name} ({kb:.0f} KB) já presente")
        return
    print(f"  faltando: {ARQUIVO}")
    print(INSTRUCOES)


if __name__ == "__main__":
    main()
