"""
Página: Roadmap do projeto — próximos passos e plano para artigo.

Renderiza ROADMAP.md (raiz) com navegação por horizonte (curto/médio/longo).
"""
from pathlib import Path

import streamlit as st

from i18n import t
from lib.tema import (
    nav_card,
    page_header,
    section_label,
)

page_header(
    titulo=t("sobre.titulo"),
    descricao=t("sobre.descricao"),
    crumbs=t("sobre.crumbs"),
)

ROADMAP_PATH = Path(__file__).resolve().parents[2] / "ROADMAP.md"

if not ROADMAP_PATH.exists():
    st.error(t("erro.roadmap_ausente", caminho=ROADMAP_PATH))
    st.stop()

texto = ROADMAP_PATH.read_text(encoding="utf-8")


def _extrair_secao(md: str, marcador_inicio: str, marcador_fim: str | None) -> str:
    inicio = md.find(marcador_inicio)
    if inicio < 0:
        return ""
    if marcador_fim:
        fim = md.find(marcador_fim, inicio + len(marcador_inicio))
        if fim < 0:
            return md[inicio:]
        return md[inicio:fim]
    return md[inicio:]


# --- 3 cards-resumo dos horizontes ---
st.markdown(section_label(t("sobre.secao_resumo")), unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(nav_card(
        "C", t("sobre.card_curto_titulo"), t("sobre.card_curto_desc"),
    ), unsafe_allow_html=True)
with c2:
    st.markdown(nav_card(
        "M", t("sobre.card_medio_titulo"), t("sobre.card_medio_desc"),
    ), unsafe_allow_html=True)
with c3:
    st.markdown(nav_card(
        "L", t("sobre.card_longo_titulo"), t("sobre.card_longo_desc"),
    ), unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# --- Tabs com cada horizonte ---
# Os marcadores ## 1./## 2./## 3. são marcadores estáveis no ROADMAP.md
# (o conteúdo das tabs sai do .md em PT-BR — tradução do roadmap em si fica
# para uma fase futura, junto com a do paper).
tab_curto, tab_medio, tab_longo, tab_full = st.tabs([
    t("sobre.tab_curto"),
    t("sobre.tab_medio"),
    t("sobre.tab_longo"),
    t("sobre.tab_full"),
])

with tab_curto:
    st.markdown(
        _extrair_secao(texto, "## 1. Curto prazo", "## 2. Médio prazo")
        .replace("## 1. Curto prazo — finalização da IC", "")
        .strip()
    )

with tab_medio:
    st.markdown(
        _extrair_secao(texto, "## 2. Médio prazo", "## 3. Longo prazo")
        .replace("## 2. Médio prazo — Top 10 fontes de dados a adicionar", "")
        .strip()
    )

with tab_longo:
    st.markdown(
        _extrair_secao(texto, "## 3. Longo prazo", "## Tabela-resumo")
        .replace("## 3. Longo prazo — Critérios para artigo internacional", "")
        .strip()
    )

with tab_full:
    st.caption(t("sobre.tab_full_caption"))
    st.markdown(texto)

st.markdown(
    '<hr style="border:none;border-top:1px solid var(--c-line);margin:32px 0 12px">',
    unsafe_allow_html=True,
)
st.markdown(
    '<div style="display:flex;justify-content:space-between;font-size:12px;color:var(--c-muted)">'
    f'<span>{t("sobre.rodape")}</span>'
    '<a href="https://github.com/LVinaud/arboviral_data_science" '
    'style="color:var(--c-accent)">github.com/LVinaud/arboviral_data_science</a>'
    '</div>',
    unsafe_allow_html=True,
)
