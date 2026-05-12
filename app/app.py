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
import streamlit as st

from i18n import language_selector, t
from lib.tema import aplicar_tema, sidebar_footer

st.set_page_config(
    page_title=t("app.page_title"),
    page_icon="🦟",
    layout="wide",
    initial_sidebar_state="expanded",
)

aplicar_tema()
language_selector()

# Emojis em vez de :material/...: porque a fonte Material Symbols pode não
# carregar (proxy/adblock/cache) e os ícones viram texto literal ("home",
# "notifications") sobrepostos ao label. Emojis são glyphs Unicode garantidos
# em qualquer sistema operacional.
paginas = [
    st.Page("screens/visao_geral.py", title=t("nav.visao_geral"),
            icon="🏠", default=True),
    st.Page("screens/alertas.py", title=t("nav.alertas"), icon="🔔"),
    st.Page("screens/municipio.py", title=t("nav.municipio"), icon="🔎"),
    st.Page("screens/mapa.py", title=t("nav.mapa"), icon="🗺️"),
    st.Page("screens/comparativo.py", title=t("nav.comparativo"), icon="📊"),
    st.Page("screens/sobre.py", title=t("nav.sobre"), icon="ℹ️"),
    st.Page("screens/proximos_passos.py", title=t("nav.proximos_passos"), icon="🧭"),
]

nav = st.navigation(paginas)
nav.run()
# Footer DEPOIS de nav.run para ficar no fim da sidebar (após os filtros que
# cada screen adiciona). Se chamado antes, aparece entre brand e filtros.
sidebar_footer()
