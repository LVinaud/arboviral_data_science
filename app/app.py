"""
Plataforma de Alerta Precoce de Arboviroses — entry point Streamlit.

Regra arquitetural: a interface DEPENDE do pacote `arboviral`, mas o
pacote NÃO depende deste app. Verificação: nenhum arquivo em
src/arboviral/ importa de app/ (validar com grep antes de cada release).

Roteamento via st.navigation (Streamlit ≥ 1.36): rótulos e ícones de cada
tela são definidos aqui, não inferidos do nome do arquivo. Isso evita o
default feio "app" no menu lateral. Cada arquivo em screens/ é um script
puro — set_page_config e chrome (tema/sidebar) são responsabilidade só
deste app.py.

i18n: o seletor de idioma é renderizado AQUI (antes de nav.run) para ficar
no topo da sidebar. Cada screen pode adicionar seus filtros embaixo. O
sidebar_footer fica DEPOIS de nav.run para garantir que aparece no fim.

Uso:
    streamlit run app/app.py
"""
from pathlib import Path

import streamlit as st

from i18n import language_selector, t
from lib.tema import aplicar_tema, sidebar_footer

# Favicon PNG monogram em verde do design system (sem emoji).
# Gerado por scripts/gerar_favicon.py — basta re-executar para mudar a cor/letra.
_FAVICON = Path(__file__).parent / "static" / "favicon.png"

st.set_page_config(
    page_title=t("app.page_title"),
    page_icon=str(_FAVICON) if _FAVICON.exists() else None,
    layout="wide",
    initial_sidebar_state="expanded",
)

aplicar_tema()
language_selector()

# Sidebar sem ícones — Material Symbols (`:material/...:`) foi tentado mas
# a fonte do Google Fonts não carrega de forma confiável neste setup,
# resultando no nome literal sobreposto ao label ("home", "info", etc).
# Texto puro é mais limpo do que ícone quebrado.
paginas = [
    st.Page("screens/visao_geral.py", title=t("nav.visao_geral"), default=True),
    st.Page("screens/alertas.py", title=t("nav.alertas")),
    st.Page("screens/municipio.py", title=t("nav.municipio")),
    st.Page("screens/mapa.py", title=t("nav.mapa")),
    st.Page("screens/comparativo.py", title=t("nav.comparativo")),
    st.Page("screens/sobre.py", title=t("nav.sobre")),
    st.Page("screens/proximos_passos.py", title=t("nav.proximos_passos")),
]

nav = st.navigation(paginas)
nav.run()
# Footer DEPOIS de nav.run para ficar no fim da sidebar (após os filtros que
# cada screen adiciona). Se chamado antes, aparece entre brand e filtros.
sidebar_footer()
