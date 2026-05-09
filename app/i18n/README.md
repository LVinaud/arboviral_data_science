# Camada de internacionalização (i18n) do app

> **Decisão arquitetural (2026-05-08):** apenas a UI (`app/`) é bilíngue.
> O **core** (`src/arboviral/`, parquets, configs, docstrings, comentários
> do pipeline) **permanece em PT-BR** — é o vocabulário técnico da
> epidemiologia brasileira (SINAN, LPI, canal endêmico, casos prováveis)
> e a referência para o paper. Tradução do core ficaria para a fase de
> submissão de paper internacional, e mesmo lá só docstrings principais
> + README, não nomes de variáveis.

---

## Por que apenas a UI?

| Consideração | Decisão |
|---|---|
| **Custo / churn** | Traduzir 3 camadas (scraping/ingestion/transform) + 7 docs sincronizados = semanas. UI = dicionário PT/EN. |
| **Audiência** | UI: gestores, banca de IC, demos internacionais (inteli.gente). Core: o próprio aluno + orientador + revisores de paper. |
| **Reviewers de paper** | Avaliam metodologia + resultados, não nomes de variáveis. README + abstract + docstrings principais em inglês são o que conta. |
| **Semântica** | `casos_provaveis`, `local_provavel_infeccao` (LPI), `latencia_mediana_lag1` mapeiam direto para o vocabulário SINAN — traduzir cega quem audita o pipeline com a documentação oficial. |

O i18n da UI rende imediato (demos, screenshots de paper, plataforma
inteli.gente em versão internacional). O i18n do core rende só na hora
de publicar — e nem totalmente.

---

## Arquitetura

```
app/
├── i18n/
│   ├── __init__.py     ← API pública: t, t_or_none, language_selector, set_language, get_language
│   ├── pt.py           ← dicionário PT-BR (referência canônica, 376 chaves)
│   ├── en.py           ← dicionário EN (paridade total com pt.py)
│   ├── _validar.py     ← script de paridade de chaves (CLI)
│   └── README.md       ← este arquivo
├── app.py              ← chama language_selector() ANTES de st.navigation
├── lib/
│   ├── labels.py       ← nome_doenca / humanizar_feature etc. delegam para t()
│   ├── tema.py         ← brand, footer, risk_legend usam t()
│   ├── predicao.py     ← categorizar_risco usa t()
│   └── carregar.py     ← spinners via st.spinner(t(...)) dentro da função
└── screens/*.py        ← cada string visível ao usuário vem de t("chave")
```

### Princípios

1. **PT-BR é fonte canônica.** Toda chave nasce em `pt.py`; `en.py` deve
   ter as mesmas chaves. Se EN não tiver, `t()` faz fallback para PT
   (não quebra, mas indica trabalho pendente).
2. **Idioma vive em `st.session_state["lang"]`.** Default `"pt"`.
   `set_language()` valida e marca; o app re-roda no novo idioma via
   `st.rerun()`.
3. **Slugs do core não mudam.** O parquet continua com `doenca = "dengue"`,
   `modelo = "rf"`, etc. Só o **label exibido** muda. Selectboxes usam
   `format_func=nome_doenca` — o valor de sessão é sempre o slug.
4. **Caches que dependem do idioma recebem `lang` como argumento.** Ver
   `screens/variaveis.py::_construir_catalogo(lang)` — sem isso, mudar
   idioma deixaria o catálogo travado no idioma antigo.
5. **CSS é language-agnostic.** Slugs CSS (`risk-baixo`, `risk-critico`)
   continuam em PT — `static/styles.css` não é tocado.

---

## API

```python
from i18n import t, t_or_none, get_language, set_language, language_selector
```

| Função | Uso |
|---|---|
| `t("chave.dotted")` | Resolve no idioma corrente. Aceita `**kwargs` para `.format()`. Retorna `[chave]` se não existir em nenhum idioma. |
| `t_or_none("chave")` | Variante que retorna `None` em vez de `[chave]`. Útil em `lib/labels.py` quando há fallback algorítmico (regex / `slug.title()`). |
| `get_language()` | `"pt"` ou `"en"`. |
| `set_language("en")` | Salva em session_state. Não dispara rerun — o caller decide. |
| `language_selector()` | Componente pronto: pílula PT/EN no topo da sidebar. Auto-rerun ao trocar. |

### Exemplos

```python
st.title(t("alertas.titulo"))                              # string simples
st.caption(t("home.metricas.periodo_delta",                # com placeholders
            ano_min=2014, ano_max=2024))
st.error(t("erro.modelo_nao_encontrado", arquivo="x.joblib"))
```

### Convenção de chaves

```
{tela_ou_modulo}.{secao}.{elemento}
```

Exemplos: `home.hero.titulo`, `alertas.tabela.mes_predito`,
`municipio.shap.qtd_help`, `comum.municipio` (termos repetidos),
`doenca.dengue` (slug → label), `feature.lat`, `feature_pattern.casos_lag_1`.

---

## Como adicionar uma nova string

1. **Escolha uma chave** seguindo o padrão dotted acima. Coloque em
   `comum.*` se for reutilizada; senão, no namespace da tela.
2. **Adicione em `pt.py` primeiro** (PT-BR é canônico).
3. **Adicione a mesma chave em `en.py`** com a tradução.
4. **No código, use `t("nova.chave")`** em vez do literal.
5. **Rode `python -m i18n._validar`** (a partir de `app/`) para garantir
   paridade. CI poderia rodar isso, mas hoje é manual.

### Placeholders

`pt.py` e `en.py` devem usar os MESMOS nomes de placeholder. Exemplo:

```python
# pt.py
"alertas.descricao": "Municípios em risco · {recorte_mes} · {doenca}"
# en.py
"alertas.descricao": "Municipalities at risk · {recorte_mes} · {doenca}"
# screen
t("alertas.descricao", recorte_mes="Mar/2024", doenca="Dengue")
```

### Singular vs plural

Para padrões como "1 mês" / "3 meses", use **duas chaves**:

```python
# feature_pattern (em pt.py e en.py)
"casos_lag_1": "Casos de {d_low} há {k} mês",      / "{d} cases {k} month ago"
"casos_lag_n": "Casos de {d_low} há {k} meses",    / "{d} cases {k} months ago"
```

E no código, escolha pela aritmética:
```python
chave = f"feature_pattern.casos_lag_{'1' if k == '1' else 'n'}"
```

### Nomes de doença em meio de frase (PT vs EN)

PT usa lowercase no meio da frase ("casos de dengue"); EN capitaliza
("Dengue cases"). Para resolver isso sem heurística, **passamos dois
kwargs**: `d` (capitalizado, para EN) e `d_low` (lowercase, para PT):

```python
d_full = nome_doenca("dengue")  # "Dengue" / "Dengue"
return t(chave, d=d_full, d_low=d_full.lower(), k=k)
```

E os templates usam o que combina com a língua:
- PT: `"Casos de {d_low} há {k} mês"`
- EN: `"{d} cases {k} month ago"`

---

## Como adicionar um novo idioma (ex.: espanhol)

1. Crie `app/i18n/es.py` espelhando `pt.py` (use `cp pt.py es.py` e
   traduza in-place).
2. Em `app/i18n/__init__.py`, acrescente:
   ```python
   from . import es
   IDIOMAS_DISPONIVEIS["es"] = es.STRINGS
   _NOMES_IDIOMA["es"] = {"pt": "Espanhol", "en": "Spanish", "es": "Español"}
   _NOMES_IDIOMA["pt"]["es"] = "Espanhol"
   _NOMES_IDIOMA["en"]["es"] = "Spanish"
   ```
3. Rode `python -m i18n._validar` (atualmente compara só PT vs EN —
   precisaria estender para incluir ES, mas é trivial).
4. O selector mostrará automaticamente PT/EN/ES.

---

## Validação

```bash
# A partir de app/:
python -m i18n._validar
# OK — 376 chaves em paridade entre pt.py e en.py.
```

O script enumera recursivamente as folhas (strings) de cada dict e
compara conjuntos. Diferença → exit code 1, com lista do que falta em cada
idioma.

### Smoke-test end-to-end

O framework `streamlit.testing.v1.AppTest` permite renderizar cada screen
sem servidor, em ambos idiomas:

```python
from streamlit.testing.v1 import AppTest

at = AppTest.from_file("screens/alertas.py", default_timeout=60)
at.session_state["lang"] = "en"   # ou "pt"
at.run()
assert not at.exception
```

Foi assim que verificamos as 7 telas × 2 idiomas (14 cenários, 0 falhas)
no commit que introduziu o i18n.

---

## O que NÃO fica em i18n

- **Nomes próprios**: "São Paulo", "ICMC", "USP", "Lázaro Vinaud", "MCTI",
  "Aedes aegypti", "Haemagogus/Sabethes" — ficam literais.
- **Slugs internos do pipeline**: `dengue`, `febre_amarela`, `inc100`, `rf`
  — esses são chaves de parquet/joblib, jamais traduzidos.
- **CSS**: `static/styles.css` não vê i18n.
- **Marcadores de seção do ROADMAP.md** (`## 1. Curto prazo`, etc.):
  o ROADMAP em si segue em PT até a fase de paper. A tela `sobre.py` lê
  o conteúdo do .md como markdown bruto — só os títulos das tabs e cards
  estão no i18n.

---

## Histórico

- **2026-05-08** — i18n introduzido. App.py + 7 telas + 4 módulos de
  `lib/` migrados. 376 chaves em pt.py / en.py com paridade total.
  Validado via `AppTest` (14/14 cenários OK).
