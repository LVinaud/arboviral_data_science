# Plataforma de Alerta — Arboviroses SP

App **Streamlit** que consome os modelos e dados gerados pelo pacote `arboviral`
(em `src/arboviral/`) para fornecer uma interface de visualização e alerta
para gestores municipais.

> **Dependência unidirecional**: este app DEPENDE do pacote `arboviral`,
> mas o pacote NÃO depende deste app. Nenhum arquivo em `src/arboviral/` importa
> de `app/`. Isso preserva a independência do pipeline de modelagem como
> ferramenta de pesquisa.

## Estrutura

```
app/
├── app.py                          # landing page com visão geral
├── pages/
│   ├── 1_Alertas.py                 # lista priorizada de municípios em risco
│   ├── 2_Municipio.py               # detalhe + justificativa SHAP por município
│   ├── 3_Mapa.py                    # mapa de SP por nível de risco
│   └── 4_Comparativo.py             # 4 doenças lado a lado
├── lib/
│   ├── carregar.py                  # loaders cacheados de dados/modelos
│   └── predicao.py                  # wrappers de predição + SHAP
└── README.md                        # este arquivo
```

## Como rodar

### Pré-requisitos

1. Pipeline de dados completo: `data/processed/municipio_mes.parquet`,
   `labels.parquet`, `features.parquet`, `predictions.parquet` precisam existir
2. Modelos serializados em `data/processed/models/` (gerados por `arboviral.train`)

Caso falte algum, gere com:

```bash
python -m arboviral.transform.build_master
python -m arboviral.labels.build_labels
python -m arboviral.features.build_features
python -m arboviral.train
```

### Instalação das dependências do app

A partir da raiz do repositório:

```bash
pip install -e ".[app]"
```

Esse extra `[app]` está definido em `pyproject.toml` e instala apenas as
dependências exclusivas da interface (Streamlit, Plotly). O pipeline de
modelagem continua funcionando sem essas dependências.

### Iniciar o app

```bash
streamlit run app/app.py
```

Por padrão, abre em `http://localhost:8501`. Streamlit detecta automaticamente
as páginas em `app/pages/` (ordenadas pelo prefixo numérico).

## Páginas

### 🚨 Alertas
Lista todos os alertas (predição ≥ limiar configurável) ordenada por probabilidade.
Mostra para cada município: probabilidade prevista, surto real (avaliação retroativa),
flag indicando se o município já estava em surto (distinguir antecipação de manutenção).

### 🔍 Município
Detalhe profundo de um município:
- Predições mensais ao longo do ano com gráfico de barras coloridas
- Histórico de casos notificados
- **Justificativa SHAP** das 5-8 features que mais impactaram a predição
  (vermelho = aumentou risco, verde = diminuiu)

### 🗺️ Mapa
Visualização geográfica de SP com pontos coloridos por nível de risco previsto.
Mapa interativo (zoom, pan, hover).

### 📊 Comparativo
Para um município escolhido, mostra **as 4 doenças simultaneamente** em
heatmap (linhas = doença, colunas = mês) + histórico consolidado.

## Cache e performance

Loaders usam `@st.cache_data` (dados) e `@st.cache_resource` (modelos joblib).
Primeira sessão pode demorar ~3-5s para carregar; depois fica instantâneo.

Modelos são carregados sob demanda — apenas o `.joblib` específico
(doença × definição × modelo × fold) que está sendo usado.

## Roadmap

- Choropleth com geojson dos limites municipais (em vez de scatter)
- Predição em tempo real com features atualizadas (rotina mensal)
- Exportação de PDF com lista de alertas (para envio a gestores)
- Autenticação por município (cada gestor vê apenas o seu)
- Notificação por e-mail quando alerta excede limiar
- Comparação de modelos lado a lado para o mesmo município
