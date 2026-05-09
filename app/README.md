# Plataforma de Alerta Precoce — Arboviroses SP

App **Streamlit** que consome modelos e dados gerados pelo pacote `arboviral`
(em `src/arboviral/`) para fornecer uma interface de visualização e alerta
para gestores municipais.

> **Dependência unidirecional**: este app DEPENDE do pacote `arboviral`,
> mas o pacote NÃO depende deste app. Nenhum arquivo em `src/arboviral/` importa
> de `app/`. Isso preserva a independência do pipeline de modelagem como
> ferramenta de pesquisa publicável.

## Estrutura

```
app/
├── app.py                          # entry point — st.navigation registra as 7 telas,
│                                   #               aplica tema e renderiza chrome (sidebar)
├── screens/
│   ├── visao_geral.py              # hero institucional + métricas + cards de navegação
│   ├── alertas.py                  # lista priorizada de municípios em risco
│   ├── municipio.py                # detalhe + explicação local por município
│   ├── mapa.py                     # mapa de SP por nível de risco (scatter_mapbox)
│   ├── comparativo.py              # 4 doenças lado a lado (heatmap + série histórica)
│   ├── variaveis.py                # catálogo das 140 features (categoria, fonte, NaN%)
│   └── sobre.py                    # roadmap do projeto e plano de publicação
├── lib/
│   ├── carregar.py                 # loaders cacheados de dados/modelos
│   ├── predicao.py                 # wrappers (categorizar_risco, justificar_alerta)
│   ├── tema.py                     # design system: aplica CSS, helpers HTML
│   └── labels.py                   # humanização de códigos técnicos (rf, inc100, dengue,
│                                   #   pct_floresta, dengue_casos_lag1) → strings PT/EN
├── i18n/                           # camada bilíngue PT-BR / EN — só UI, core fica em PT
│   ├── pt.py / en.py               # dicionários (376 chaves em paridade)
│   ├── __init__.py                 # API: t(), language_selector(), set_language()
│   ├── _validar.py                 # checa paridade de chaves entre pt.py e en.py
│   └── README.md                   # quando traduzir, como adicionar idioma, convenções
├── static/
│   └── styles.css                  # tokens + componentes do design system
└── README.md                       # este arquivo
```

A configuração de tema básica do Streamlit (paleta, fonte, accent) vive em
[`.streamlit/config.toml`](../.streamlit/config.toml) na raiz do repositório.

> **Histórico**: a estrutura inicial usava o padrão multipage do Streamlit
> com `app/pages/N_Nome.py` (auto-discovery por nome de arquivo). Em 2026-05
> migramos para `st.navigation` (Streamlit ≥ 1.36) por dois motivos:
> (1) controle total dos rótulos no menu lateral — sem isso, a primeira
> página apareceria como `app` em vez de `Visão geral`; (2) ícones por
> emoji (independem da fonte Material Symbols, que pode falhar de carregar
> atrás de proxy/adblock).

## Como rodar

### Pré-requisitos

1. Pipeline completo gerado em `data/processed/`:
   - `municipio_mes.parquet` (79 colunas após Onda 1)
   - `labels.parquet`
   - `features.parquet` (140 colunas após Onda 1)
   - `predictions.parquet`
2. Modelos serializados em `data/processed/models/` (gerados por `arboviral.train`)

Caso falte algum, gere com:

```bash
python -m arboviral.transform.build_master
python -m arboviral.labels.build_labels
python -m arboviral.features.build_features
python -m arboviral.train
```

### Instalação

```bash
pip install -e ".[app]"
```

O extra `[app]` (definido em `pyproject.toml`) instala apenas as dependências
exclusivas da interface (Streamlit, Plotly).

### Iniciar

```bash
streamlit run app/app.py
```

Abre em `http://localhost:8501`. As 6 telas são registradas declarativamente
em `app.py` (não dependem do nome do arquivo).

> **Hot-reload de módulos externos**: Streamlit não recarrega
> `arboviral.evaluation.explain` automaticamente quando você edita o pipeline.
> Se mudar `src/arboviral/`, mate o servidor (`Ctrl+C`) e reinicie. Para
> garantir, limpe o pycache: `find . -name __pycache__ -type d -exec rm -rf {} +`.

## Design system

A linguagem visual segue o mockup do Claude Design (paleta midnight + laranja
queimado, tipografia Geist, cards de baixa elevação, tabelas com chrome
sutil). Implementação:

- **Tokens em CSS**: `app/static/styles.css` define cores, raios, sombras,
  fontes via custom properties (`--c-accent`, `--c-ink`, `--r-md`, etc.).
  Único arquivo CSS — todas as cores derivam dele.
- **Helpers HTML**: `app/lib/tema.py` injeta o CSS e oferece funções para
  renderizar componentes:
  - `risk_badge(prob)` — badge colorido CRÍTICO/ALTO/MODERADO/BAIXO
  - `prob_bar(prob)` — barra horizontal com cor por nível
  - `metric(label, value, ...)` / `metric_row(*items)` — substitui `st.metric`
  - `hero(eyebrow, titulo, lead, meta_items)` — usado na landing
  - `page_header(titulo, descricao, crumbs)` — header padrão das telas
  - `nav_card(letra, titulo, descricao)` — card-link com ícone
  - `chip(texto, variante)` — chip pequeno (default/warn/good/mono)
  - `risk_legend()` — legenda horizontal dos 4 níveis
  - `shap_row(rank, humano, tecnico, contrib, max_abs)` — linha do card SHAP
  - `nivel_de(prob)` / `cor_por_prob(prob)` — para uso em gráficos plotly
- **Streamlit nativo**: tema base em `.streamlit/config.toml` (`primaryColor`,
  `backgroundColor`, etc.) — esses são honrados pelos widgets nativos.

> **Padrão importante**: thresholds de risco do app (`0.25 / 0.50 / 0.75`)
> ficam centralizados em `lib/predicao.py:categorizar_risco` e em
> `lib/tema.py:nivel_de`. Mudar em um lugar exige mudar no outro — ou
> melhor, mudar só `tema.py:_NIVEIS` e fazer `predicao.py` delegar.

### Cuidados específicos com o Streamlit

- **Material Symbols**: Streamlit usa a fonte do Google Fonts para ícones do
  shell (botão de colapsar a sidebar etc.). Quando ela não carrega, o nome
  literal do ícone (`keyboard_double_arrow_left`) aparece como texto. Mitigação
  em `static/styles.css`: regra `:not(.material-symbols-outlined)` exclui
  ícones do override de fonte da sidebar, e há um fallback via CSS `::before`
  que troca o texto por uma seta unicode (`«` / `»`) caso a fonte falhe.
- **Cache do tema entre páginas**: cada navegação re-executa a página,
  então `aplicar_tema()` é chamado a cada render (o texto do CSS em si é
  cacheado em RAM via `@st.cache_data`). Sem isso, o estilo "sumia" ao
  trocar de aba.

## Internacionalização (PT / EN)

A UI é bilíngue desde 2026-05-08. Toda string visível ao usuário passa por
`t("chave.dotted")` que resolve no dicionário do idioma corrente
(`app/i18n/pt.py` ou `en.py`). O seletor PT/EN fica no topo da sidebar.

> **Apenas a UI é traduzida.** O core (`src/arboviral/`, parquets, configs,
> docstrings do pipeline) permanece em PT-BR — é vocabulário epidemiológico
> brasileiro e a referência canônica para o paper. Detalhes em
> [`app/i18n/README.md`](i18n/README.md).

```python
from i18n import t
st.title(t("alertas.titulo"))
st.caption(t("home.metricas.periodo_delta", ano_min=2014, ano_max=2024))
```

**Validar paridade de chaves**: `python -m i18n._validar` (a partir de `app/`).

## Humanização de códigos técnicos (`lib/labels.py`)

O pipeline usa códigos curtos para consistência (parquets/joblib): `rf`,
`inc100`, `dengue`, `febre_amarela`, `pct_floresta`, `dengue_casos_lag1`,
etc. Esses códigos NÃO devem aparecer na interface — para o gestor, o app
mostra:

| Código técnico | Rótulo na UI |
|---|---|
| `dengue` / `febre_amarela` | Dengue / Febre amarela |
| `rf` / `xgb` / `lgbm` / `ebm` / `logreg` | Random Forest / XGBoost / LightGBM / EBM / Regressão Logística |
| `canal` / `inc100` | Canal endêmico (Min. Saúde) / 100 casos / 100 mil hab |
| `7` (mês) | Julho |
| `dengue_casos_lag1` | Casos de dengue há 1 mês |
| `chikungunya_casos_roll6` | Casos de chikungunya (média móvel 6 meses) |
| `dengue_surto_canal_lag12` | Surto de dengue há 12 meses (canal endêmico) |
| `pct_floresta` | Cobertura: floresta natural (%) |
| `cob_vac_fa_pct` | Cobertura vacinal contra febre amarela (%) |
| `mes_sin` | Sazonalidade (componente sen) |

`lib/labels.py` tem dicionários para estáticas + regex para padrões
parametrizados. Cobertura: 137/137 features atuais. Adicionar nova feature
sem atualizar o módulo cai num fallback razoável (`slug.replace("_", " ")`).

`humanizar_feature(slug)` é a função pública usada no card SHAP do
município. Para selectboxes, passamos `format_func=` (mantém o código
como `value` real, só muda o label exibido).

### Defaults inteligentes em selectboxes

Em `lib/predicao.py`:

```python
DEFAULT_DOENCA = "dengue"
DEFAULT_DEFINICAO = "inc100"
DEFAULT_MODELO = "rf"
```

A combinação foi escolhida por uso prático: dengue tem volume,
`inc100` é a definição operacional mais usada por gestores, RF é o melhor
modelo geral. A função `idx_default(opcoes, preferido, fallback=0)`
encontra o índice de cada um na lista disponível (com fallback para 0
se a opção preferida não estiver presente).

## Telas

### Visão geral (`screens/visao_geral.py`)
Hero institucional, 4 métricas-resumo (municípios, período, variáveis no
master, doenças), tabela de modelos disponíveis (com nomes humanos:
"Random Forest" em vez de `rf`) e 3 cards de navegação.

### Alertas (`screens/alertas.py`)
Filtros laterais (doença, definição, modelo, ano de teste, mês de
referência, limiar de probabilidade), 4 métricas no topo (total/críticos/
altos/moderados), legenda de risco e tabela ranqueada com:
- Coluna **Risco** (categórica: CRÍTICO/ALTO/MODERADO/BAIXO)
- Coluna **Mês predito** humanizado (ex.: "Maio/2024")
- Coluna **Probabilidade** com barra de progresso
- Colunas **Surto real?** e **Em surto agora?** com Sim/Não
  (em vez de 1/0 brutos)

Métricas de avaliação retroativa: precisão neste recorte + antecipações
verdadeiras (alertas que previram INÍCIO de surto, não manutenção).

### Município (`screens/municipio.py`)
Header com chips de metadata (IBGE, população, estação INMET), 4 métricas
(pico do ano ou mês selecionado, meses com alerta, surtos reais no ano,
definição em uso), gráfico de probabilidades mês a mês (com marcadores ★
de surto real, hover mostra "Outubro" em vez de `2024-10`), histórico de
casos, e **card de explicação local** com 8 features ranqueadas.

A explicação é **uniforme entre todos os modelos do portfolio**:
- Árvores (RF/XGB/LGBM) → SHAP TreeExplainer
- LogReg → coef × valor padronizado
- EBM → API nativa `explain_local` do interpret-ml

Cada linha do card mostra: rank, label humano (`Casos de dengue há 1 mês`),
detalhe técnico em mono (`dengue_casos_lag1 · valor observado: 1.5e+05`),
barra centrada (vermelha = empurra para cima, verde = empurra para baixo)
e contribuição numérica. O método de explicação usado aparece em monoespaçado
no topo (`método: SHAP (TreeExplainer)`, `EBM explain_local (nativo)`, etc.).

Selectbox **Mês de análise (SHAP)** permite focar a explicação num mês
específico em vez do pico do ano.

### Mapa (`screens/mapa.py`)
scatter_mapbox com paleta verde→mostarda→laranja→vermelho (alinhada aos
níveis 0.25/0.50/0.75 do design), 4 métricas no topo, legenda de risco
e tabela "Top 5 municípios em maior risco" abaixo do mapa.

### Comparativo (`screens/comparativo.py`)
Heatmap 4 doenças × 12 meses (linhas com nome humano, colunas com
abreviação do mês: "Jan", "Fev"...) + série histórica das 4 doenças
sobrepostas (cores fixas por doença, atualizadas para a paleta do design).

### Sobre o projeto (`screens/sobre.py`)
3 cards-resumo dos horizontes (curto/médio/longo) + tabs com cada seção
extraída do `ROADMAP.md` da raiz — atualização do arquivo reflete aqui
automaticamente.

## Cache e performance

- Loaders usam `@st.cache_data` (parquets) e `@st.cache_resource` (modelos
  joblib). Primeira sessão demora ~3-5 s; depois fica instantâneo.
- Modelos são carregados sob demanda — apenas o `.joblib` específico
  (doença × definição × modelo × fold) que está sendo usado.
- O CSS do design system é cacheado em RAM (`@st.cache_data` na função que
  lê do disco) e re-injetado a cada render — necessário porque o output
  de `st.markdown` é local da página.

## Convenções e padrões para extensão

- **Adicionar nova tela**: criar `screens/minha_tela.py` (sem
  `set_page_config`, sem chamadas de chrome — `app.py` central faz tudo)
  e registrar com `st.Page(...)` em `app.py`.
- **Adicionar nova fonte de dados ao master**: a humanização das features
  novas precisa entrar em `lib/labels.py` (dicionário direto OU regex se
  parametrizado por doença/lag). Sem isso o nome técnico vaza no card
  SHAP do município.
- **Mudar threshold de risco**: editar `_NIVEIS` em `lib/tema.py` e
  `categorizar_risco` em `lib/predicao.py` (atualmente duplicado por
  histórico — refatoração futura: única fonte de verdade).

## Roadmap visual / funcional

- Choropleth com geojson dos limites municipais (em vez de scatter)
- Predição em tempo real com features atualizadas (rotina mensal)
- Exportação de PDF com lista de alertas (para envio a gestores)
- Autenticação por município (cada gestor vê apenas o seu)
- Notificação por e-mail quando alerta excede limiar
- Comparação de modelos lado a lado para o mesmo município
- Página dedicada "Comparar pré × pós Onda 1" (usar
  `model_results_PRE_ONDA1.parquet` que está preservado em
  `data/processed/`) — útil para defesa da IC e relatório
