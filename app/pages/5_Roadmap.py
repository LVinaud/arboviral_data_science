"""
Página: Roadmap do projeto — próximos passos e plano para artigo.

Renderiza o ROADMAP.md (raiz do repositório) com navegação por horizonte
(curto/médio/longo prazo) e destaque para o caminho de publicação.
"""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Roadmap", page_icon="🗺️", layout="wide")

st.title("Roadmap do Projeto")
st.caption(
    "Plano de evolução do trabalho — desde o fechamento da IC até material "
    "publicável em artigo internacional."
)

# Localizar ROADMAP.md (na raiz do repo, dois níveis acima de app/pages/)
ROADMAP_PATH = Path(__file__).resolve().parents[2] / "ROADMAP.md"

if not ROADMAP_PATH.exists():
    st.error(
        f"`ROADMAP.md` não encontrado em `{ROADMAP_PATH}`. "
        "Esperado na raiz do repositório."
    )
    st.stop()

texto = ROADMAP_PATH.read_text(encoding="utf-8")


def _extrair_secao(md: str, marcador_inicio: str, marcador_fim: str | None) -> str:
    """Extrai uma seção do markdown entre dois marcadores (## headers)."""
    inicio = md.find(marcador_inicio)
    if inicio < 0:
        return ""
    if marcador_fim:
        fim = md.find(marcador_fim, inicio + len(marcador_inicio))
        if fim < 0:
            return md[inicio:]
        return md[inicio:fim]
    return md[inicio:]


# --- Resumo (TL;DR) ---
st.subheader("Em resumo")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("##### 🛠 Curto prazo")
    st.markdown(
        "5 itens para fechar a IC bem feita: análises post-hoc rápidas, "
        "SHAP estratificado, robustez a NaN, sensitivity analysis "
        "(`--no-cross`) e tuning."
    )
with col2:
    st.markdown("##### 📦 Médio prazo")
    st.markdown(
        "**Top 10 fontes de dados** priorizadas. Item #1 é o **LIRAa** "
        "(índice de *Aedes aegypti*) — provavelmente a feature mais "
        "preditiva possível para arboviroses urbanas."
    )
with col3:
    st.markdown("##### 📚 Longo prazo")
    st.markdown(
        "Caminho para publicação: workshop nacional → conferência IEEE → "
        "journal internacional. Validação externa em outros estados é o "
        "passo crítico."
    )

st.divider()

# --- Tabs com cada horizonte ---
tab_curto, tab_medio, tab_longo, tab_full = st.tabs([
    "🛠 Curto prazo",
    "📦 Médio prazo (10 fontes)",
    "📚 Longo prazo (artigo)",
    "📄 Documento completo",
])

with tab_curto:
    st.markdown("### Finalização da IC")
    st.markdown(
        _extrair_secao(texto, "## 1. Curto prazo", "## 2. Médio prazo")
            .replace("## 1. Curto prazo — finalização da IC", "")
            .strip()
    )

with tab_medio:
    st.markdown("### Top 10 fontes de dados a adicionar")
    st.markdown(
        _extrair_secao(texto, "## 2. Médio prazo", "## 3. Longo prazo")
            .replace("## 2. Médio prazo — Top 10 fontes de dados a adicionar", "")
            .strip()
    )

with tab_longo:
    st.markdown("### Critérios para artigo internacional")
    st.markdown(
        _extrair_secao(texto, "## 3. Longo prazo", "## Tabela-resumo")
            .replace("## 3. Longo prazo — Critérios para artigo internacional", "")
            .strip()
    )

with tab_full:
    st.markdown("### ROADMAP.md completo")
    st.caption(
        "Mesmo conteúdo das tabs anteriores, mas em formato linear "
        "(útil para imprimir ou copiar)."
    )
    st.markdown(texto)

# --- Rodapé ---
st.divider()
col1, col2 = st.columns(2)
with col1:
    st.markdown(
        "💡 **Para o orientador**: a aba *Longo prazo* tem o plano detalhado "
        "de validação externa em outros estados (esforço por etapa) e os "
        "veículos de publicação por nível."
    )
with col2:
    st.markdown(
        "📝 Este conteúdo vive em "
        "[`ROADMAP.md`](https://github.com/LVinaud/arboviral_data_science/blob/main/ROADMAP.md) "
        "no repositório. Atualizações no arquivo refletem aqui automaticamente."
    )
