"""
Tema visual do app — porta dos tokens do mockup do Claude Design.

Aplica CSS uma vez por sessão (via st.session_state) e oferece helpers para
renderizar os componentes do design system: badges de risco, barras de
probabilidade, métricas, cards, hero, page header, SHAP rows.

Princípio: este módulo é puramente VISUAL. Conteúdo (números, textos) sempre
vem de quem chama, que por sua vez lê dos parquets do core (ciência de dados).
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from i18n import t

_STATIC = Path(__file__).resolve().parent.parent / "static"
_GEIST = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700'
    '&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet">'
    # Material Symbols Outlined — necessário para os ícones do Streamlit (botão
    # de colapsar a sidebar, ícones de navegação st.Page) renderizarem como
    # glyph em vez do nome literal.
    '<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined"'
    ' rel="stylesheet">'
)


@st.cache_data(show_spinner=False)
def _ler_css() -> str:
    return (_STATIC / "styles.css").read_text(encoding="utf-8")


def aplicar_tema() -> None:
    """Injeta CSS + Geist a cada render — IMPORTANTE: precisa rodar em toda página.

    Streamlit re-executa cada página do zero quando o usuário navega; o output
    de st.markdown é local da página, então não dá pra cachear via session_state
    (o CSS some ao mudar de página). O texto do CSS em si vem do disco apenas
    1× por processo via @st.cache_data.
    """
    st.markdown(_GEIST, unsafe_allow_html=True)
    st.markdown(f"<style>{_ler_css()}</style>", unsafe_allow_html=True)


def sidebar_brand() -> None:
    """Renderiza o brand mark + footer institucional na sidebar."""
    with st.sidebar:
        st.markdown(
            '<div class="brand">'
            '<div class="brand-mark">A</div>'
            f'<div class="brand-text">{t("tema.brand_titulo")}'
            f'<small>{t("tema.brand_sub")}</small></div>'
            '</div>',
            unsafe_allow_html=True,
        )


def sidebar_footer() -> None:
    """Footer institucional no fim da sidebar."""
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-foot">'
            f'{t("tema.footer_linha1")}<br>'
            f'{t("tema.footer_linha2")}<br>'
            f'{t("tema.footer_linha3")}'
            '</div>',
            unsafe_allow_html=True,
        )


# ---------- Helpers de cor / nível ----------

# Thresholds alinhados ao mockup (4 níveis a 0.25 / 0.50 / 0.75).
# O slug CSS continua em PT-BR (preserva contrato com static/styles.css);
# só o label exibido vem do i18n.
_NIVEIS = [
    (0.75, "critico", "CRITICO", "#dc2626"),
    (0.50, "alto", "ALTO", "#ea580c"),
    (0.25, "moderado", "MODERADO", "#a16207"),
    (0.00, "baixo", "BAIXO", "#15803d"),
]


def nivel_de(prob: float) -> tuple[str, str, str]:
    """Retorna (slug_css, label_i18n, cor_hex) para uma probabilidade [0, 1]."""
    for limiar, slug, chave_label, cor in _NIVEIS:
        if prob >= limiar:
            return slug, t(f"risco.{chave_label}"), cor
    return "baixo", t("risco.BAIXO"), "#15803d"


def cor_por_prob(prob: float) -> str:
    """Hex da cor de risco — útil para gráficos plotly."""
    return nivel_de(prob)[2]


# ---------- Componentes HTML ----------

def risk_badge(prob: float, lg: bool = False) -> str:
    """HTML do badge colorido (CRÍTICO / ALTO / MODERADO / BAIXO)."""
    slug, label, _ = nivel_de(prob)
    cls = f"risk-badge risk-{slug}{' lg' if lg else ''}"
    return f'<span class="{cls}">{label}</span>'


def prob_bar(prob: float, mostrar_valor: bool = True) -> str:
    """Barra horizontal de probabilidade + valor numérico."""
    _, _, cor = nivel_de(prob)
    pct = max(0.0, min(1.0, prob)) * 100
    valor = (
        f'<span style="min-width:38px">{pct:.0f}%</span>' if mostrar_valor else ""
    )
    return (
        '<div class="prob-row">'
        f'<div class="prob-bar"><div class="prob-bar-fill" '
        f'style="width:{pct:.1f}%;background:{cor}"></div></div>'
        f"{valor}</div>"
    )


def metric(label: str, value: str, unit: str = "", delta: str | None = None,
           delta_dir: str | None = None) -> str:
    """Card de métrica grande (substitui st.metric com a estética do design)."""
    delta_html = ""
    if delta:
        cls = f"metric-delta {delta_dir or ''}".strip()
        delta_html = f'<div class="{cls}">{delta}</div>'
    unit_html = f'<span class="metric-unit">{unit}</span>' if unit else ""
    return (
        '<div class="metric">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}{unit_html}</div>'
        f"{delta_html}"
        "</div>"
    )


def metric_row(*items: str) -> None:
    """Renderiza N cards de métrica em colunas iguais (st.columns + st.html)."""
    cols = st.columns(len(items))
    for col, html in zip(cols, items):
        with col:
            st.markdown(html, unsafe_allow_html=True)


def section_label(text: str) -> str:
    """Eyebrow tipográfico (uppercase, tracking, muted)."""
    return f'<div class="card-section-label">{text}</div>'


def page_header(titulo: str, descricao: str | None = None,
                crumbs: str | None = None) -> None:
    """Header padrão de página: crumbs + h1 + descrição + linha divisória."""
    parts = ['<div class="page-header">']
    if crumbs:
        parts.append(f'<div class="page-crumbs">{crumbs}</div>')
    parts.append(f"<h1>{titulo}</h1>")
    if descricao:
        parts.append(f"<p>{descricao}</p>")
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def hero(eyebrow: str, titulo: str, lead: str,
         meta_items: list[tuple[str, str]] | None = None) -> None:
    """Hero da landing — mantém estilo editorial sóbrio."""
    parts = ['<div class="hero">']
    parts.append(f'<div class="hero-eyebrow">{eyebrow}</div>')
    parts.append(f"<h1>{titulo}</h1>")
    parts.append(f'<p class="lead">{lead}</p>')
    if meta_items:
        parts.append('<div class="hero-meta">')
        for rotulo, valor in meta_items:
            parts.append(f"<span>{rotulo} · <strong>{valor}</strong></span>")
        parts.append("</div>")
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def nav_card(letra: str, titulo: str, descricao: str) -> str:
    """Card-link usado na grade de navegação da landing."""
    return (
        '<div class="nav-card">'
        f'<div class="nav-card-icon">{letra}</div>'
        f"<h3>{titulo}</h3>"
        f"<p>{descricao}</p>"
        "</div>"
    )


def chip(texto: str, variante: str = "") -> str:
    """Chip pequeno (variante: '', 'warn', 'good', 'mono')."""
    cls = "chip" + (f" chip-{variante}" if variante else "")
    return f'<span class="{cls}">{texto}</span>'


def risk_legend() -> str:
    """Legenda horizontal dos 4 níveis (BAIXO → CRÍTICO)."""
    items = [
        (t("risco.BAIXO"), "#15803d", "#f0fdf4"),
        (t("risco.MODERADO"), "#a16207", "#fefce8"),
        (t("risco.ALTO"), "#ea580c", "#fff7ed"),
        (t("risco.CRITICO"), "#dc2626", "#fef2f2"),
    ]
    steps = "".join(
        f'<div class="risk-legend-step" style="background:{bg};color:{cor}">{rot}</div>'
        for rot, cor, bg in items
    )
    return f'<div class="risk-legend">{steps}</div>'


def shap_row(rank: int, humano: str, tecnico: str, contrib: float,
             max_abs: float) -> str:
    """Linha de SHAP: rank + label humano + barra centrada + contribuição."""
    sentido = "pos" if contrib >= 0 else "neg"
    largura_pct = (abs(contrib) / max_abs * 50) if max_abs > 0 else 0
    sinal = "+" if contrib >= 0 else "−"
    return (
        '<div class="shap-row">'
        f'<div class="shap-rank">#{rank}</div>'
        '<div>'
        f'<div class="shap-humano">{humano}</div>'
        f'<div class="shap-tecnico">{tecnico}</div>'
        '</div>'
        '<div class="shap-bar-wrap">'
        '<div class="shap-bar-axis"></div>'
        f'<div class="shap-bar-fill {sentido}" style="width:{largura_pct:.1f}%"></div>'
        '</div>'
        f'<div class="shap-contrib {sentido}">{sinal}{abs(contrib):.3f}</div>'
        '</div>'
    )
