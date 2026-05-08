"""
Página: Roadmap do projeto — próximos passos e plano para artigo.

Renderiza ROADMAP.md (raiz) com navegação por horizonte (curto/médio/longo).
"""
from pathlib import Path

import streamlit as st

from lib.tema import (
    nav_card,
    page_header,
    section_label,
)

page_header(
    titulo="Sobre o projeto",
    descricao=(
        "Plano de evolução da pesquisa — desde o fechamento da IC até material "
        "publicável em artigo internacional. Conteúdo reflete o ROADMAP.md do repositório."
    ),
    crumbs="PLATAFORMA / SOBRE",
)

ROADMAP_PATH = Path(__file__).resolve().parents[2] / "ROADMAP.md"

if not ROADMAP_PATH.exists():
    st.error(f"`ROADMAP.md` não encontrado em `{ROADMAP_PATH}`.")
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
st.markdown(section_label("Em resumo"), unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(nav_card(
        "C", "Curto prazo",
        "5 itens para fechar a IC bem feita: análises post-hoc, SHAP "
        "estratificado, robustez a NaN, sensitivity analysis (--no-cross), tuning.",
    ), unsafe_allow_html=True)
with c2:
    st.markdown(nav_card(
        "M", "Médio prazo",
        "Top 10 fontes de dados priorizadas por impacto. 5/10 já integradas "
        "(MapBiomas, ESF, latência SINAN, densidade, vacinação FA).",
    ), unsafe_allow_html=True)
with c3:
    st.markdown(nav_card(
        "L", "Longo prazo",
        "Caminho para publicação: workshop nacional → conferência IEEE → "
        "journal internacional. Validação externa em outros estados é o passo crítico.",
    ), unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# --- Tabs com cada horizonte ---
tab_curto, tab_medio, tab_longo, tab_full = st.tabs([
    "Curto prazo",
    "Médio prazo (top 10 fontes)",
    "Longo prazo (artigo)",
    "Documento completo",
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
    st.caption(
        "Mesmo conteúdo das tabs anteriores, em formato linear "
        "(útil para imprimir ou copiar)."
    )
    st.markdown(texto)

st.markdown(
    '<hr style="border:none;border-top:1px solid var(--c-line);margin:32px 0 12px">',
    unsafe_allow_html=True,
)
st.markdown(
    '<div style="display:flex;justify-content:space-between;font-size:12px;color:var(--c-muted)">'
    '<span>Conteúdo vive em <code>ROADMAP.md</code> no repositório · '
    'atualizações refletem aqui automaticamente.</span>'
    '<a href="https://github.com/LVinaud/arboviral_data_science" '
    'style="color:var(--c-accent)">github.com/LVinaud/arboviral_data_science</a>'
    '</div>',
    unsafe_allow_html=True,
)

