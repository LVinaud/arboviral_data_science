"""
Camada de internacionalização (i18n) do app Streamlit.

Princípio: o **core** (`src/arboviral/`) permanece em PT-BR — variáveis,
docstrings, parquets, tudo segue a convenção do projeto. Esta camada cobre
apenas a UI (`app/`), porque o público pode ser bilíngue (banca, demo
internacional, plataforma inteli.gente em versão EN).

Arquitetura:
    app/i18n/
    ├── __init__.py     ← API pública (t, set_language, language_selector)
    ├── pt.py           ← dicionário PT-BR (referência canônica)
    ├── en.py           ← dicionário EN (mesmas chaves)
    └── README.md       ← documentação do processo

Uso:
    from i18n import t
    st.title(t("home.hero.titulo"))
    st.caption(t("home.hero.lead", ano_min=2014, ano_max=2024))

O idioma é guardado em `st.session_state["lang"]` (default: "pt"). Trocar
o idioma força um rerun da página, redesenhando tudo no novo idioma.

Para adicionar um novo idioma (ex.: espanhol):
    1. Crie `app/i18n/es.py` espelhando as chaves de `pt.py`
    2. Acrescente a entrada em `IDIOMAS_DISPONIVEIS` abaixo
    3. (opcional) Acrescente um label EN para o idioma em `_NOMES_IDIOMA`
"""
from __future__ import annotations

import streamlit as st

from . import en, pt

IDIOMAS_DISPONIVEIS: dict[str, dict] = {
    "pt": pt.STRINGS,
    "en": en.STRINGS,
}

DEFAULT_LANG = "pt"


def get_language() -> str:
    """Idioma corrente (lê de st.session_state, fallback no default)."""
    return st.session_state.get("lang", DEFAULT_LANG)


def set_language(lang: str) -> None:
    """Define o idioma corrente. Aceita apenas códigos em IDIOMAS_DISPONIVEIS."""
    if lang not in IDIOMAS_DISPONIVEIS:
        raise ValueError(f"Idioma '{lang}' não suportado. Disponíveis: {list(IDIOMAS_DISPONIVEIS)}")
    st.session_state["lang"] = lang


def t(chave: str, **kwargs) -> str:
    """Traduz uma chave dotted-path para o idioma corrente.

    Resolve a chave no dicionário do idioma. Se a chave não existir no idioma
    selecionado, faz fallback para PT-BR (a referência canônica). Se mesmo no
    PT-BR a chave estiver ausente, retorna a própria chave entre colchetes
    (`[home.foo]`) — torna fácil identificar strings esquecidas durante a
    migração ou quando se adiciona uma tela nova.

    Args:
        chave: caminho dotted (ex.: "home.hero.titulo").
        **kwargs: variáveis para .format() na string traduzida.

    Exemplos:
        t("alertas.titulo")
        t("home.hero.lead", ano_min=2014, ano_max=2024)
    """
    valor = t_or_none(chave, **kwargs)
    if valor is None:
        return f"[{chave}]"
    return valor


def t_or_none(chave: str, **kwargs) -> str | None:
    """Variante de t() que retorna None se a chave não existe.

    Útil em lib/labels.py — quando não há tradução para um slug específico,
    o chamador prefere recorrer a um fallback algorítmico (regex, slug.title())
    em vez de exibir `[chave]`.
    """
    lang = get_language()
    valor = _resolver(IDIOMAS_DISPONIVEIS[lang], chave)
    if valor is None and lang != DEFAULT_LANG:
        valor = _resolver(IDIOMAS_DISPONIVEIS[DEFAULT_LANG], chave)
    if valor is None:
        return None
    if kwargs:
        try:
            return valor.format(**kwargs)
        except (KeyError, IndexError):
            return valor
    return valor


def _resolver(dicionario: dict, chave: str):
    """Caminha por um dict aninhado seguindo um caminho 'a.b.c'."""
    no = dicionario
    for parte in chave.split("."):
        if not isinstance(no, dict) or parte not in no:
            return None
        no = no[parte]
    return no if isinstance(no, str) else None


def language_selector(localizacao: str = "sidebar") -> None:
    """Seletor de idioma. Chamado uma vez por render no topo da sidebar.

    Pílulas mostram o código ISO em uppercase (PT / EN) — universal, não
    depende do idioma corrente, e evita ambiguidade (uma versão antiga
    usava o nome completo cortado em 2 letras, mas "Português"/"Portuguese"
    colapsavam ambos em "PO"). O label "Idioma / Language" deixa claro
    que o controle é bilíngue.
    """
    container = st.sidebar if localizacao == "sidebar" else st
    lang_atual = get_language()
    opcoes = list(IDIOMAS_DISPONIVEIS.keys())
    idx = opcoes.index(lang_atual) if lang_atual in opcoes else 0

    with container:
        nova = st.radio(
            "Idioma / Language",
            opcoes,
            index=idx,
            horizontal=True,
            format_func=str.upper,
            key="_lang_radio",
            label_visibility="visible",
        )
    if nova != lang_atual:
        set_language(nova)
        st.rerun()


__all__ = ["t", "t_or_none", "get_language", "set_language", "language_selector",
           "IDIOMAS_DISPONIVEIS", "DEFAULT_LANG"]
