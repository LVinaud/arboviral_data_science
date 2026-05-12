"""
Script pontual — gera os assets geográficos consumidos pelo app Streamlit.

Saídas em data/lookup/geo/:
    municipios_sp.geojson           — 645 polígonos (IBGE 2020, simplificados)
    drs_sp.geojson                  — 17 polígonos (SES-SP, dissolve de municípios)
    regioes_intermediarias_sp.geojson — 11 polígonos (IBGE 2019)
    municipios_sp_lookup.csv        — cod_ibge → nome, drs, rgi, lat, lon (centroides)

Rodar UMA vez (após `pip install geopandas geobr` no venv local) — os artefatos
ficam versionados; o app só lê os arquivos resultantes, não depende de geobr/
geopandas em runtime.

    cd <raiz-do-repo>
    source .venv/bin/activate
    pip install geopandas geobr     # só pra este script
    python scripts/gerar_geo_lookup.py
    pip uninstall geopandas geobr   # opcional, mantém o venv enxuto

Fonte dos polígonos:
- Municípios e RGI: pacote `geobr` (IBGE oficial).
- DRS: SES-SP — listas de municípios coletadas por scraping da página oficial
  https://saude.sp.gov.br/ses/institucional/departamentos-regionais-de-saude/
  (cada DRS tem uma subpágina lista todos seus municípios). Os polígonos das
  DRS são gerados por dissolve dos polígonos municipais agrupados pelo DRS
  correspondente.

Macrorregiões "operacionais" (que agrupariam DRS em ~6 grupos) foram
deliberadamente NÃO incluídas — não existem oficialmente na SES-SP, e usar
RGI (11) atende ao requisito de "menos granular que DRS" sem inventar divisão.

Convenção de cod_ibge: 7 dígitos (não 6 do DATASUS). O lookup IBGE/INMET
em `municipios_sp_estacoes_inmet.xlsx` segue a mesma convenção.
"""
from __future__ import annotations

import unicodedata
from pathlib import Path

import geobr
import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SAIDA = ROOT / "data" / "lookup" / "geo"
SAIDA.mkdir(parents=True, exist_ok=True)


# ============================================================
# Lookup município → DRS (scraping da SES-SP, 2026-05-09)
# ============================================================
# Nomes em UPPERCASE como aparecem nas páginas da SES-SP.
# Normalização (remover acentos + uppercase) é aplicada antes do match com
# o nome do geobr (que vem em Title Case com acentos).

DRS_MUNICIPIOS: dict[str, list[str]] = {
    "I - Grande São Paulo": [
        "ARUJÁ", "BARUERI", "BIRITIBA-MIRIM", "CAIEIRAS", "CAJAMAR",
        "CARAPICUÍBA", "COTIA", "DIADEMA", "EMBU", "EMBU-GUAÇU",
        "FERRAZ DE VASCONCELOS", "FRANCISCO MORATO", "FRANCO DA ROCHA",
        "GUARAREMA", "GUARULHOS", "ITAPECERICA DA SERRA", "ITAPEVI",
        "ITAQUAQUECETUBA", "JANDIRA", "JUQUITIBA", "MAIRIPORÃ", "MAUÁ",
        "MOGI DAS CRUZES", "OSASCO", "PIRAPORA DO BOM JESUS", "POÁ",
        "RIBEIRÃO PIRES", "RIO GRANDE DA SERRA", "SALESÓPOLIS", "SANTA ISABEL",
        "SANTANA DE PARNAÍBA", "SANTO ANDRÉ", "SÃO BERNARDO DO CAMPO",
        "SÃO CAETANO DO SUL", "SÃO LOURENÇO DA SERRA", "SÃO PAULO",
        "SUZANO", "TABOÃO DA SERRA", "VARGEM GRANDE PAULISTA",
    ],
    "II - Araçatuba": [
        "ALTO ALEGRE", "ANDRADINA", "ARAÇATUBA", "AURIFLAMA", "AVANHANDAVA",
        "BARBOSA", "BENTO DE ABREU", "BILAC", "BIRIGUI", "BRAÚNA",
        "BREJO ALEGRE", "BURITAMA", "CASTILHO", "CLEMENTINA", "COROADOS",
        "GABRIEL MONTEIRO", "GLICÉRIO", "GUARAÇAÍ", "GUARARAPES",
        "GUZOLÂNDIA", "ILHA SOLTEIRA", "ITAPURA", "LAVÍNIA", "LOURDES",
        "LUIZIÂNIA", "MIRANDÓPOLIS", "MURUTINGA DO SUL", "NOVA CASTILHO",
        "NOVA INDEPENDÊNCIA", "NOVA LUZITÂNIA", "PENÁPOLIS", "PEREIRA BARRETO",
        "PIACATU", "RUBIÁCEA", "SANTO ANTÔNIO DO ARACANGUÁ",
        "SANTÓPOLIS DO AGUAPEÍ", "SUD MENNUCCI", "SUZANÁPOLIS", "TURIÚBA",
        "VALPARAÍSO",
    ],
    "III - Araraquara": [
        "AMÉRICO BRASILIENSE", "ARARAQUARA", "BOA ESPERANÇA DO SUL",
        "BORBOREMA", "CÂNDIDO RODRIGUES", "DESCALVADO", "DOBRADA", "DOURADO",
        "GAVIÃO PEIXOTO", "IBATÉ", "IBITINGA", "ITÁPOLIS", "MATÃO", "MOTUCA",
        "NOVA EUROPA", "PORTO FERREIRA", "RIBEIRÃO BONITO", "RINCÃO",
        "SANTA ERNESTINA", "SANTA LÚCIA", "SÃO CARLOS", "TABATINGA",
        "TAQUARITINGA", "TRABIJU",
    ],
    "IV - Baixada Santista": [
        "BERTIOGA", "CUBATÃO", "GUARUJÁ", "ITANHAÉM", "MONGAGUÁ",
        "PERUÍBE", "PRAIA GRANDE", "SANTOS", "SÃO VICENTE",
    ],
    "V - Barretos": [
        "ALTAIR", "BARRETOS", "BEBEDOURO", "CAJOBI", "COLINA", "COLÔMBIA",
        "GUAÍRA", "GUARACI", "JABORANDI", "MONTE AZUL PAULISTA", "OLÍMPIA",
        "SEVERÍNIA", "TAIAÇU", "TAIÚVA", "TAQUARAL", "TERRA ROXA",
        "VIRADOURO", "VISTA ALEGRE DO ALTO",
    ],
    "VI - Bauru": [
        "ÁGUAS DE SANTA BÁRBARA", "AGUDOS", "ANHEMBI", "ARANDU", "AREALVA",
        "AREIÓPOLIS", "AVAÍ", "AVARÉ", "BALBINOS", "BARÃO DE ANTONINA",
        "BARIRI", "BARRA BONITA", "BAURU", "BOCAINA", "BOFETE", "BORACÉIA",
        "BOREBI", "BOTUCATU", "BROTAS", "CABRÁLIA PAULISTA", "CAFELÂNDIA",
        "CERQUEIRA CÉSAR", "CONCHAS", "CORONEL MACEDO", "DOIS CÓRREGOS",
        "DUARTINA", "FARTURA", "GETULINA", "GUAIÇARA", "IACANGA", "IARAS",
        "IGARAÇU DO TIETÊ", "ITAÍ", "ITAJU", "ITAPORANGA", "ITAPUÍ",
        "ITATINGA", "JAÚ", "LARANJAL PAULISTA", "LENÇÓIS PAULISTA", "LINS",
        "LUCIANÓPOLIS", "MACATUBA", "MANDURI", "MINEIROS DO TIETÊ",
        "PARANAPANEMA", "PARDINHO", "PAULISTÂNIA", "PEDERNEIRAS", "PEREIRAS",
        "PIRAJU", "PIRAJUÍ", "PIRATININGA", "PONGAÍ", "PORANGABA", "PRATÂNIA",
        "PRESIDENTE ALVES", "PROMISSÃO", "REGINÓPOLIS", "SABINO", "SÃO MANUEL",
        "SARUTAIÁ", "TAGUAÍ", "TAQUARITUBA", "TEJUPÁ", "TORRE DE PEDRA",
        "TORRINHA", "URU",
    ],
    "VII - Campinas": [
        "ÁGUAS DE LINDÓIA", "AMERICANA", "AMPARO", "ARTUR NOGUEIRA", "ATIBAIA",
        "BOM JESUS DOS PERDÕES", "BRAGANÇA PAULISTA", "CABREÚVA", "CAMPINAS",
        "CAMPO LIMPO PAULISTA", "COSMÓPOLIS", "HOLAMBRA", "HORTOLÂNDIA",
        "INDAIATUBA", "ITATIBA", "ITUPEVA", "JAGUARIÚNA", "JARINU",
        "JOANÓPOLIS", "JUNDIAÍ", "LINDÓIA", "LOUVEIRA", "MONTE ALEGRE DO SUL",
        "MONTE MOR", "MORUNGABA", "NAZARÉ PAULISTA", "NOVA ODESSA", "PAULÍNIA",
        "PEDRA BELA", "PEDREIRA", "PINHALZINHO", "PIRACAIA",
        "SANTA BÁRBARA D'OESTE", "SANTO ANTÔNIO DA POSSE", "SERRA NEGRA",
        "SOCORRO", "SUMARÉ", "TUIUTI", "VALINHOS", "VARGEM", "VÁRZEA PAULISTA",
        "VINHEDO",
    ],
    "VIII - Franca": [
        "ARAMINA", "BURITIZAL", "CRISTAIS PAULISTA", "FRANCA", "GUARÁ",
        "IGARAPAVA", "IPUÃ", "ITIRAPUÃ", "ITUVERAVA", "JERIQUARA",
        "MIGUELÓPOLIS", "MORRO AGUDO", "NUPORANGA", "ORLÂNDIA",
        "PATROCÍNIO PAULISTA", "PEDREGULHO", "RESTINGA", "RIBEIRÃO CORRENTE",
        "RIFAINA", "SALES OLIVEIRA", "SÃO JOAQUIM DA BARRA",
        "SÃO JOSÉ DA BELA VISTA",
    ],
    "IX - Marília": [
        "ADAMANTINA", "ÁLVARO DE CARVALHO", "ALVINLÂNDIA", "ARCO ÍRIS", "ASSIS",
        "BASTOS", "BERNARDINO DE CAMPOS", "BORÁ", "CAMPOS NOVOS PAULISTA",
        "CÂNDIDO MOTA", "CANITAR", "CHAVANTES", "CRUZÁLIA", "ECHAPORÃ",
        "ESPÍRITO SANTO DO TURVO", "FERNÃO", "FLÓRIDA PAULISTA", "FLORÍNIA",
        "GÁLIA", "GARÇA", "GUAIMBÊ", "GUARANTÃ", "HERCULÂNDIA", "IACRI",
        "IBIRAREMA", "INÚBIA PAULISTA", "IPAUSSU", "JÚLIO MESQUITA", "LUCÉLIA",
        "LUPÉRCIO", "LUTÉCIA", "MARACAÍ", "MARIÁPOLIS", "MARÍLIA", "OCAUÇU",
        "ÓLEO", "ORIENTE", "OSCAR BRESSANE", "OSVALDO CRUZ", "OURINHOS",
        "PACAEMBU", "PALMITAL", "PARAGUAÇU PAULISTA", "PARAPUÃ",
        "PEDRINHAS PAULISTA", "PLATINA", "POMPÉIA", "PRACINHA", "QUEIROZ",
        "QUINTANA", "RIBEIRÃO DO SUL", "RINÓPOLIS", "SAGRES", "SALMOURÃO",
        "SALTO GRANDE", "SANTA CRUZ DO RIO PARDO", "SÃO PEDRO DO TURVO",
        "TARUMÃ", "TIMBURI", "TUPÃ", "UBIRAJARA", "VERA CRUZ",
    ],
    "X - Piracicaba": [
        "ÁGUAS DE SÃO PEDRO", "ANALÂNDIA", "ARARAS", "CAPIVARI", "CHARQUEADA",
        "CONCHAL", "CORDEIRÓPOLIS", "CORUMBATAÍ", "ELIAS FAUSTO",
        "ENGENHEIRO COELHO", "IPEÚNA", "IRACEMÁPOLIS", "ITIRAPINA", "LEME",
        "LIMEIRA", "MOMBUCA", "PIRACICABA", "PIRASSUNUNGA", "RAFARD",
        "RIO CLARO", "RIO DAS PEDRAS", "SALTINHO", "SANTA CRUZ DA CONCEIÇÃO",
        "SANTA GERTRUDES", "SANTA MARIA DA SERRA", "SÃO PEDRO",
    ],
    "XI - Presidente Prudente": [
        "ALFREDO MARCONDES", "ÁLVARES MACHADO", "ANHUMAS", "CAIABU", "CAIUÁ",
        "DRACENA", "EMILIANÓPOLIS", "ESTRELA DO NORTE",
        "EUCLIDES DA CUNHA PAULISTA", "FLORA RICA", "IEPÊ", "INDIANA",
        "IRAPURU", "JOÃO RAMALHO", "JUNQUEIRÓPOLIS", "MARABÁ PAULISTA",
        "MARTINÓPOLIS", "MIRANTE DO PARANAPANEMA", "MONTE CASTELO", "NANTES",
        "NARANDIBA", "NOVA GUATAPORANGA", "OURO VERDE", "PANORAMA", "PAULICÉIA",
        "PIQUEROBI", "PIRAPOZINHO", "PRESIDENTE BERNARDES",
        "PRESIDENTE EPITÁCIO", "PRESIDENTE PRUDENTE", "PRESIDENTE VENCESLAU",
        "QUATÁ", "RANCHARIA", "REGENTE FEIJÓ", "RIBEIRÃO DOS ÍNDIOS", "ROSANA",
        "SANDOVALINA", "SANTA MERCEDES", "SANTO ANASTÁCIO", "SANTO EXPEDITO",
        "SÃO JOÃO DO PAU D'ALHO", "TACIBA", "TARABAI", "TEODORO SAMPAIO",
        "TUPI PAULISTA",
    ],
    "XII - Registro": [
        "BARRA DO TURVO", "CAJATI", "CANANÉIA", "ELDORADO", "IGUAPE",
        "ILHA COMPRIDA", "IPORANGA", "ITARIRI", "JACUPIRANGA", "JUQUIÁ",
        "MIRACATU", "PARIQUERA-AÇU", "PEDRO DE TOLEDO", "REGISTRO",
        "SETE BARRAS",
    ],
    "XIII - Ribeirão Preto": [
        "ALTINÓPOLIS", "BARRINHA", "BATATAIS", "BRODOWSKI", "CAJURU",
        "CÁSSIA DOS COQUEIROS", "CRAVINHOS", "DUMONT", "GUARIBA", "GUATAPARÁ",
        "JABOTICABAL", "JARDINÓPOLIS", "LUÍS ANTÔNIO", "MONTE ALTO",
        "PITANGUEIRAS", "PONTAL", "PRADÓPOLIS", "RIBEIRÃO PRETO",
        "SANTA CRUZ DA ESPERANÇA", "SANTA RITA DO PASSA QUATRO",
        "SANTA ROSA DE VITERBO", "SANTO ANTÔNIO DA ALEGRIA", "SÃO SIMÃO",
        "SERRA AZUL", "SERRANA", "SERTÃOZINHO",
    ],
    "XIV - São João da Boa Vista": [
        "AGUAÍ", "ÁGUAS DA PRATA", "CACONDE", "CASA BRANCA", "DIVINOLÂNDIA",
        "ESPÍRITO SANTO DO PINHAL", "ESTIVA GERBI", "ITAPIRA", "ITOBI",
        "MOCOCA", "MOGI GUAÇU", "MOGI MIRIM", "SANTA CRUZ DAS PALMEIRAS",
        "SANTO ANTÔNIO DO JARDIM", "SÃO JOÃO DA BOA VISTA",
        "SÃO JOSÉ DO RIO PARDO", "SÃO SEBASTIÃO DA GRAMA", "TAMBAÚ",
        "TAPIRATIBA", "VARGEM GRANDE DO SUL",
    ],
    "XV - São José do Rio Preto": [
        "ADOLFO", "ÁLVARES FLORENCE", "AMÉRICO DE CAMPOS", "APARECIDA D'OESTE",
        "ARIRANHA", "ASPÁSIA", "BADY BASSIT", "BÁLSAMO", "CARDOSO", "CATANDUVA",
        "CATIGUÁ", "CEDRAL", "COSMORAMA", "DIRCE REIS", "DOLCINÓPOLIS",
        "ELISIÁRIO", "EMBAÚBA", "ESTRELA D'OESTE", "FERNANDÓPOLIS",
        "FERNANDO PRESTES", "FLOREAL", "GASTÃO VIDIGAL", "GENERAL SALGADO",
        "GUAPIAÇU", "GUARANI D'OESTE", "IBIRÁ", "ICÉM", "INDIAPORÃ", "IPIGUÁ",
        "IRAPUÃ", "ITAJOBI", "JACI", "JALES", "JOSÉ BONIFÁCIO", "MACAUBAL",
        "MACEDÔNIA", "MAGDA", "MARAPOAMA", "MARINÓPOLIS", "MENDONÇA",
        "MERIDIANO", "MESÓPOLIS", "MIRA ESTRELA", "MIRASSOL", "MIRASSOLÂNDIA",
        "MONÇÕES", "MONTE APRAZÍVEL", "NEVES PAULISTA", "NHANDEARA", "NIPOÃ",
        "NOVA ALIANÇA", "NOVA CANAÃ PAULISTA", "NOVA GRANADA", "NOVAIS",
        "NOVO HORIZONTE", "ONDA VERDE", "ORINDIÚVA", "OUROESTE", "PALESTINA",
        "PALMARES PAULISTA", "PALMEIRA D'OESTE", "PARAÍSO", "PARANAPUÃ",
        "PARISI", "PAULO DE FARIA", "PEDRANÓPOLIS", "PINDORAMA", "PIRANGI",
        "PLANALTO", "POLONI", "PONTALINDA", "PONTES GESTAL", "POPULINA",
        "POTIRENDABA", "RIOLÂNDIA", "RUBINÉIA", "SALES", "SANTA ADÉLIA",
        "SANTA ALBERTINA", "SANTA CLARA D'OESTE", "SANTA FÉ DO SUL",
        "SANTA RITA D'OESTE", "SANTA SALETE", "SANTANA DA PONTE PENSA",
        "SÃO FRANCISCO", "SÃO JOÃO DAS DUAS PONTES", "SÃO JOÃO DE IRACEMA",
        "SÃO JOSÉ DO RIO PRETO", "SEBASTIANÓPOLIS DO SUL", "TABAPUÃ", "TANABI",
        "TRÊS FRONTEIRAS", "TURMALINA", "UBARANA", "UCHOA", "UNIÃO PAULISTA",
        "URÂNIA", "URUPÊS", "VALENTIM GENTIL", "VITÓRIA BRASIL", "VOTUPORANGA",
        "ZACARIAS",
    ],
    "XVI - Sorocaba": [
        "ALAMBARI", "ALUMÍNIO", "ANGATUBA", "APIAÍ", "ARAÇARIGUAMA",
        "ARAÇOIABA DA SERRA", "BARRA DO CHAPÉU", "BOITUVA",
        "BOM SUCESSO DE ITARARÉ", "BURI", "CAMPINA DO MONTE ALEGRE",
        "CAPÃO BONITO", "CAPELA DO ALTO", "CERQUILHO", "CESÁRIO LANGE",
        "GUAPIARA", "GUAREÍ", "IBIÚNA", "IPERÓ", "ITABERÁ", "ITAÓCA",
        "ITAPETININGA", "ITAPEVA", "ITAPIRAPUÃ PAULISTA", "ITARARÉ", "ITU",
        "JUMIRIM", "MAIRINQUE", "NOVA CAMPINA", "PIEDADE", "PILAR DO SUL",
        "PORTO FELIZ", "QUADRA", "RIBEIRA", "RIBEIRÃO BRANCO",
        "RIBEIRÃO GRANDE", "RIVERSUL", "SALTO", "SALTO DE PIRAPORA",
        "SÃO MIGUEL ARCANJO", "SÃO ROQUE", "SARAPUÍ", "SOROCABA", "TAPIRAÍ",
        "TAQUARIVAÍ", "TATUÍ", "TIETÊ", "VOTORANTIM",
    ],
    "XVII - Taubaté": [
        "APARECIDA", "ARAPEÍ", "AREIAS", "BANANAL", "CAÇAPAVA",
        "CACHOEIRA PAULISTA", "CAMPOS DO JORDÃO", "CANAS", "CARAGUATATUBA",
        "CRUZEIRO", "CUNHA", "GUARATINGUETÁ", "IGARATÁ", "ILHA BELA",
        "JACAREÍ", "JAMBEIRO", "LAGOINHA", "LAVRINHAS", "LORENA",
        "MONTEIRO LOBATO", "NATIVIDADE DA SERRA", "PARAIBUNA", "PINDAMONHANGABA",
        "PIQUETE", "POTIM", "QUELUZ", "REDENÇÃO DA SERRA", "ROSEIRA",
        "SANTA BRANCA", "SANTO ANTÔNIO DO PINHAL", "SÃO BENTO DO SAPUCAÍ",
        "SÃO JOSÉ DO BARREIRO", "SÃO JOSÉ DOS CAMPOS",
        "SÃO LUIZ DO PARAITINGA", "SÃO SEBASTIÃO", "SILVEIRAS", "TAUBATÉ",
        "TREMEMBÉ", "UBATUBA",
    ],
}


def _normalizar(s: str) -> str:
    """Remove acentos + uppercase + colapsa espaços. Para casar nomes do IBGE
    ('São Paulo') com o que veio do scraping da SES-SP ('SÃO PAULO').
    Tratamos também `-` e diferenças tipo 'EMBU' vs 'EMBU DAS ARTES'
    (renomeação histórica que o IBGE pode trazer com o nome novo)."""
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii")
    return s.upper().replace("-", " ").replace("'", "").replace("  ", " ").strip()


# Renomeações que conhecemos: nomes da SES-SP (esquerda) → nomes oficiais IBGE
# (direita) atualmente. Aplicado APÓS normalização.
_RENOMEACOES_NORMALIZADAS: dict[str, str] = {
    "EMBU": "EMBU DAS ARTES",   # Embu virou Embu das Artes em 2011
    "BADY BASSIT": "BADY BASSITT",  # Grafia
    "FLORINIA": "FLORINEA",     # SES-SP usa "Florínia", IBGE "Florínea"
    "ILHA BELA": "ILHABELA",    # SES-SP separa, IBGE junta
    "SANTO ANTONIO DA POSSE": "SANTO ANTONIO DE POSSE",  # da → de no IBGE
}


def construir_mapa_nome_drs() -> dict[str, str]:
    """Inverte DRS_MUNICIPIOS para {nome_normalizado: rotulo_drs}."""
    out: dict[str, str] = {}
    for drs, municipios in DRS_MUNICIPIOS.items():
        for m in municipios:
            chave = _normalizar(m)
            chave = _RENOMEACOES_NORMALIZADAS.get(chave, chave)
            out[chave] = drs
    return out


def main() -> None:
    print("=" * 64)
    print("Gerando assets geográficos para o app")
    print("=" * 64)

    # ---------- 1. Municípios IBGE (645 polígonos) ----------
    print("\n[1/5] Baixando municípios SP (geobr, IBGE 2020)...")
    mun = geobr.read_municipality(code_muni="SP", year=2020, simplified=True)
    mun["code_muni"] = mun["code_muni"].astype("int64")
    print(f"      → {len(mun)} municípios")

    # ---------- 2. Regiões Intermediárias IBGE (11 polígonos) ----------
    print("\n[2/5] Baixando regiões intermediárias SP (IBGE 2019)...")
    rgi = geobr.read_intermediate_region(code_intermadiate="SP", year=2019)
    rgi["code_intermediate"] = rgi["code_intermediate"].astype("int64")
    print(f"      → {len(rgi)} regiões intermediárias")

    # ---------- 3. Atribuir cada município à sua RGI via spatial join ----------
    # IBGE oficialmente lista a hierarquia município→RGI mas o geobr não traz
    # a coluna direto; spatial join (centroide do município dentro do polígono
    # da RGI) é deterministico e robusto.
    print("\n[3/5] Spatial join município → RGI (via centroide)...")
    mun_centroide = mun.copy()
    mun_centroide["geometry"] = mun.geometry.centroid
    juntado = gpd.sjoin(
        mun_centroide, rgi[["code_intermediate", "name_intermediate", "geometry"]],
        how="left", predicate="within",
    )
    if juntado["code_intermediate"].isna().any():
        # Fallback raro (centroide em água/fronteira): usa nearest
        sem_rgi = juntado["code_intermediate"].isna().sum()
        print(f"      ! {sem_rgi} municípios sem match por within — usando nearest")
        falta = mun_centroide[juntado["code_intermediate"].isna()]
        nearest = gpd.sjoin_nearest(
            falta, rgi[["code_intermediate", "name_intermediate", "geometry"]],
            how="left",
        )
        juntado.loc[nearest.index, "code_intermediate"] = nearest["code_intermediate"]
        juntado.loc[nearest.index, "name_intermediate"] = nearest["name_intermediate"]
    juntado["code_intermediate"] = juntado["code_intermediate"].astype("int64")
    print(f"      → todos os {len(juntado)} municípios mapeados")

    # ---------- 4. Atribuir cada município ao seu DRS via nome ----------
    print("\n[4/5] Casando nomes município → DRS (scraping SES-SP)...")
    mapa_drs = construir_mapa_nome_drs()
    juntado["_nome_norm"] = juntado["name_muni"].apply(_normalizar)
    juntado["drs"] = juntado["_nome_norm"].map(mapa_drs)

    sem_drs = juntado[juntado["drs"].isna()]
    if len(sem_drs):
        print(f"      ! {len(sem_drs)} municípios sem DRS: revisar renomeações")
        for _, r in sem_drs.iterrows():
            print(f"        - {r['name_muni']} (cod {r['code_muni']})")
        raise SystemExit(1)
    print(f"      → 645/645 municípios com DRS atribuída")

    # ---------- 5. Salvar artefatos ----------
    print("\n[5/5] Gerando artefatos em data/lookup/geo/")

    # 5.1 Lookup CSV (sem geometria)
    lookup = juntado[[
        "code_muni", "name_muni", "drs",
        "code_intermediate", "name_intermediate",
    ]].copy()
    lookup = lookup.rename(columns={
        "code_muni": "cod_ibge",
        "name_muni": "nome_municipio",
        "code_intermediate": "rgi_codigo",
        "name_intermediate": "rgi_nome",
    })
    # Centroide pra reuso (lat, lon)
    lookup["lat"] = mun_centroide.geometry.y.values
    lookup["lon"] = mun_centroide.geometry.x.values
    lookup = lookup.sort_values("cod_ibge").reset_index(drop=True)
    arquivo_csv = SAIDA / "municipios_sp_lookup.csv"
    lookup.to_csv(arquivo_csv, index=False, encoding="utf-8")
    print(f"      ✓ {arquivo_csv.relative_to(ROOT)}  ({len(lookup)} linhas)")

    # 5.2 Municípios — geojson (versão simplificada já vem do geobr)
    mun_out = mun[["code_muni", "name_muni", "geometry"]].copy()
    mun_out = mun_out.rename(columns={"code_muni": "cod_ibge", "name_muni": "nome"})
    arquivo_mun = SAIDA / "municipios_sp.geojson"
    mun_out.to_file(arquivo_mun, driver="GeoJSON")
    print(f"      ✓ {arquivo_mun.relative_to(ROOT)}  ({len(mun_out)} polígonos)")

    # 5.3 DRS — dissolve de municípios agrupados por DRS
    juntado_full = mun.merge(
        lookup[["cod_ibge", "drs"]], left_on="code_muni", right_on="cod_ibge"
    )
    drs_geo = juntado_full.dissolve(by="drs", as_index=False)[["drs", "geometry"]]
    drs_geo = drs_geo.rename(columns={"drs": "nome"})
    drs_geo["id"] = drs_geo["nome"].str.split(" - ").str[0]
    drs_geo = drs_geo[["id", "nome", "geometry"]].sort_values("id")
    arquivo_drs = SAIDA / "drs_sp.geojson"
    drs_geo.to_file(arquivo_drs, driver="GeoJSON")
    print(f"      ✓ {arquivo_drs.relative_to(ROOT)}  ({len(drs_geo)} polígonos)")

    # 5.4 Regiões Intermediárias — geojson direto do IBGE
    rgi_out = rgi[["code_intermediate", "name_intermediate", "geometry"]].copy()
    rgi_out = rgi_out.rename(columns={
        "code_intermediate": "codigo", "name_intermediate": "nome",
    })
    arquivo_rgi = SAIDA / "regioes_intermediarias_sp.geojson"
    rgi_out.to_file(arquivo_rgi, driver="GeoJSON")
    print(f"      ✓ {arquivo_rgi.relative_to(ROOT)}  ({len(rgi_out)} polígonos)")

    # ---------- Resumo final ----------
    print("\n" + "=" * 64)
    print("RESUMO")
    print("=" * 64)
    print(f"  Municípios SP        : {len(mun)}")
    print(f"  DRS (SES-SP)         : {drs_geo['id'].nunique()}")
    print(f"  Reg. Intermed. IBGE  : {len(rgi)}")
    print(f"\nDistribuição de municípios por DRS:")
    print(lookup["drs"].value_counts().sort_index().to_string())
    print(f"\nDistribuição de municípios por RGI:")
    print(lookup["rgi_nome"].value_counts().to_string())


if __name__ == "__main__":
    main()
