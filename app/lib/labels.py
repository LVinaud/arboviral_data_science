"""
Mapeamento código técnico → rótulo humano para a UI.

Os parquets/joblib usam slugs curtos (`rf`, `inc100`, `dengue`,
`febre_amarela`) — esta camada traduz para texto humano no idioma corrente
(PT-BR ou EN), consultando os dicionários em `app/i18n/`.

Convenção de uso:
    nome_doenca("febre_amarela")       → "Febre amarela" / "Yellow fever"
    nome_modelo("rf")                  → "Random Forest"
    nome_definicao("inc100")           → "100 casos / 100 mil hab" / "100 cases / 100k inhab."
    nome_mes(7)                        → "Julho" / "July"

Para selectboxes, passar `format_func=nome_modelo` (etc.) — o valor de
sessão continua sendo o slug, só o label exibido muda. **IMPORTANTE**: caches
do Streamlit que usam essas funções devem incluir `lang=get_language()` na
chave do cache (ver `screens/variaveis.py::_construir_catalogo`).
"""
from __future__ import annotations

import re

from i18n import get_language, t, t_or_none


def nome_doenca(slug: str) -> str:
    return t_or_none(f"doenca.{slug}") or slug.replace("_", " ").title()


def nome_modelo(slug: str) -> str:
    return t_or_none(f"modelo.{slug}") or slug.upper()


def nome_definicao(slug: str) -> str:
    return t_or_none(f"definicao.{slug}") or slug


def nome_mes(num: int | str) -> str:
    """Aceita int (1-12) ou string ('07'). Retorna 'Mês N' / 'Month N' fora do range."""
    try:
        n = int(num)
    except (TypeError, ValueError):
        return str(num)
    direto = t_or_none(f"mes.{n}")
    if direto:
        return direto
    return t("mes.fora_range", n=n)


def ano_mes_humano(ano: int, mes: int) -> str:
    """Ex.: (2024, 7) → 'Julho/2024' / 'July/2024'."""
    return f"{nome_mes(mes)}/{int(ano)}"


# ============================================================
# Humanização de nomes de feature (usado pelo SHAP)
# ============================================================
# Estratégia em três camadas:
#   1. Lookup direto em i18n[feature.<slug>]  (estáticas, anuais, clima atual)
#   2. Padrões regex parametrizados (lags, rolling, trend, latência por doença)
#      → resolvem com templates em i18n[feature_pattern.<chave>]
#   3. Fallback: slug com underscores → espaços
#
# Os templates recebem dois kwargs para o nome da doença:
#   - {d}     forma capitalizada (ex.: "Dengue", "Yellow fever") — usada em EN
#   - {d_low} forma lowercase    (ex.: "dengue", "febre amarela")  — usada em PT
# Isso preserva o caso correto em cada idioma sem precisar de heurística.

_DOENCA_REGEX = r"(dengue|zika|chikungunya|febre_amarela)"


def _tpl_lag_doenca(slug: str, marcador: str, base_chave: str) -> str | None:
    m = re.match(rf"^{_DOENCA_REGEX}_{marcador}_lag(\d+)$", slug)
    if not m:
        return None
    d, k = m.group(1), m.group(2)
    chave = f"feature_pattern.{base_chave}_{'1' if k == '1' else 'n'}"
    d_full = nome_doenca(d)
    return t(chave, d=d_full, d_low=d_full.lower(), k=k)


def _tpl_roll_doenca(slug: str, marcador: str, base_chave: str) -> str | None:
    m = re.match(rf"^{_DOENCA_REGEX}_{marcador}_roll(\d+)$", slug)
    if not m:
        return None
    d, w = m.group(1), m.group(2)
    d_full = nome_doenca(d)
    return t(f"feature_pattern.{base_chave}", d=d_full, d_low=d_full.lower(), w=w)


def _tpl_lag_clima(slug: str, var: str, base_chave: str) -> str | None:
    m = re.match(rf"^{var}_lag(\d+)$", slug)
    if not m:
        return None
    k = m.group(1)
    chave = f"feature_pattern.{base_chave}_lag_{'1' if k == '1' else 'n'}"
    return t(chave, k=k)


def _tpl_roll_clima(slug: str, var: str, base_chave: str) -> str | None:
    m = re.match(rf"^{var}_roll(\d+)$", slug)
    if not m:
        return None
    return t(f"feature_pattern.{base_chave}_roll", w=m.group(1))


def humanizar_feature(slug: str) -> str:
    """Traduz nome técnico de feature para descrição legível no idioma corrente."""
    direto = t_or_none(f"feature.{slug}")
    if direto:
        return direto

    # Casos / incidência por doença (lag e rolling)
    for marcador, base in [("casos", "casos_lag"), ("incid", "incid_lag")]:
        r = _tpl_lag_doenca(slug, marcador, base)
        if r:
            return r
    for marcador, base in [("casos", "casos_roll"), ("incid", "incid_roll")]:
        r = _tpl_roll_doenca(slug, marcador, base)
        if r:
            return r

    # Tendência (sempre janela em meses, sem singular)
    m = re.match(rf"^{_DOENCA_REGEX}_casos_trend(\d+)$", slug)
    if m:
        d, w = m.group(1), m.group(2)
        d_full = nome_doenca(d)
        return t("feature_pattern.casos_trend", d=d_full, d_low=d_full.lower(), w=w)

    # Surto (canal endêmico) em lags
    m = re.match(rf"^{_DOENCA_REGEX}_surto_canal_lag(\d+)$", slug)
    if m:
        d, k = m.group(1), m.group(2)
        chave = f"feature_pattern.surto_canal_{'1' if k == '1' else 'n'}"
        d_full = nome_doenca(d)
        return t(chave, d=d_full, d_low=d_full.lower(), k=k)

    # Latência SINAN
    for sufixo, chave in [
        ("latencia_mediana_lag1", "latencia_mediana"),
        ("latencia_p90_lag1", "latencia_p90"),
        ("n_casos_com_latencia_lag1", "casos_com_latencia"),
    ]:
        m = re.match(rf"^{_DOENCA_REGEX}_{sufixo}$", slug)
        if m:
            d_full = nome_doenca(m.group(1))
            return t(f"feature_pattern.{chave}", d=d_full, d_low=d_full.lower())

    # Clima parametrizado
    for var, base in [
        ("precip_media_dia", "precip"),
        ("temp_media", "temp"),
        ("umid_media", "umid"),
    ]:
        r = _tpl_lag_clima(slug, var, base)
        if r:
            return r
        r = _tpl_roll_clima(slug, var, base)
        if r:
            return r

    return slug.replace("_", " ")


# Re-exporta `get_language` para callers que precisam usar como cache key.
__all__ = [
    "nome_doenca", "nome_modelo", "nome_definicao", "nome_mes",
    "ano_mes_humano", "humanizar_feature", "get_language",
]
