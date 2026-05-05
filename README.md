# arboviral_data_science

> Plataforma Automatizada para Prevenção e Resposta a Arboviroses Usando Inteligência Artificial

Iniciação Científica (Programa Unificado de Bolsas — PUB) desenvolvida no **Instituto de Ciências Matemáticas e de Computação da USP (ICMC-USP)** em São Carlos.

- **Aluno:** Lázaro Pereira Vinaud Neto
- **Orientador:** Prof. André Carlos Ponce de Leon Ferreira de Carvalho

## Motivação

Arboviroses como dengue, zika e chikungunya representam um desafio recorrente para a saúde pública brasileira, com impacto direto em atendimentos, internações e na organização de campanhas de prevenção em nível municipal. A dinâmica de transmissão é multifatorial — variáveis climáticas, ambientais, demográficas e de infraestrutura urbana — e, embora exista um volume crescente de indicadores públicos, esse potencial informacional permanece subaproveitado por gestores municipais devido a barreiras técnicas, fragmentação dos dados e ausência de ferramentas operacionais que produzam alertas acionáveis em tempo hábil.

Antecipar períodos de maior risco permite intensificar vigilância, planejar insumos, priorizar visitas de agentes comunitários e direcionar campanhas. Este projeto investiga a viabilidade de incorporar um módulo de **previsão de surtos de arboviroses** em nível municipal à plataforma **inteli.gente** — usada para visualização e apoio à gestão municipal — com previsões explicáveis para gestores e cidadãos.

## Formulação do problema

Tarefa de **classificação supervisionada** com granularidade **município–mês**:

- **Chave:** `(código IBGE, ano, mês)`
- **Referência epidemiológica:** município de **residência** (não de notificação)
- **Escopo:** dengue, zika e chikungunya (Oropouche foi excluída por indisponibilidade de dados padronizados no período)
- **Alvo:** dado o conjunto de variáveis observadas até o mês `t`, prever a ocorrência de surto no mês `t+1`

### Perguntas de pesquisa

- **RQ1.** Em que medida modelos de ML treinados com dados multivariados (epidemiológicos + climáticos + indicadores municipais) melhoram a predição de surtos em comparação com baselines simples baseados apenas no histórico recente?
- **RQ2.** Quais grupos de variáveis e quais defasagens temporais (lags de casos e clima) mais contribuem para o desempenho preditivo em nível município–mês?
- **RQ3.** Quão robustas são as previsões frente a valores ausentes, heterogeneidade entre municípios e validação temporal prospectiva?

## Estado atual

A primeira etapa, **já concluída**, consolidou a fundação de dados:

- Definição da unidade de análise, do esquema de dados e dos metadados mínimos por município (IBGE, UF, REGIC, Região de Saúde, mapeamento para estação meteorológica automática INMET mais próxima por coordenadas).
- Seleção iterativa de variáveis, equilibrando relevância na literatura, disponibilidade em bases públicas brasileiras e completude para uso mensal.
- Implementação do pipeline de coleta, padronização e integração dos indicadores (notebooks em `contexto/`).
- **Prova de conceito (POC)** com um subconjunto de municípios do estado de São Paulo (capitais regionais e diferentes portes populacionais) para validar o pipeline e a integração.
- Relatório parcial entregue (`contexto/Relatório Parcial - Arboviroses.pdf`).

A modelagem preditiva e a interface da plataforma **ainda não foram iniciadas** neste repositório.

## Próximas etapas

1. **Rótulo de surto.** Formalizar e validar a definição operacional (índice/limiar), incluindo alternativas baseadas em incidência ajustada por população, com análises de sensibilidade.
2. **Modelagem.** Implementar e avaliar Random Forest, XGBoost e LightGBM contra baselines de persistência, sob validação temporal (janela deslizante / *expanding window*) e métricas adequadas a desbalanceamento — **F1** e **AUPRC** como principais.
3. **Escalonamento.** Expandir o pipeline da POC para todos os municípios do estado de São Paulo, com rotinas automatizadas de atualização e checagens de qualidade (completude por variável, quebras de série, consistência das chaves).
4. **Plataforma.** Construir uma interface inicial integrada à inteli.gente para consumo das previsões, com **explicabilidade via SHAP** para indicar contribuições das variáveis em cada alerta.

## Variáveis e fontes de dados

O conjunto consolidado nesta etapa abrange:

| Dimensão | Variáveis |
|---|---|
| Epidemiológicas / assistenciais | casos prováveis e acumulados, óbitos, internações, coeficientes (incidência, prevalência, internação, letalidade) |
| Capacidade em saúde | leitos, médicos, mortalidade materna, marcadores de gestão e vigilância |
| Climáticas (mensal) | precipitação, temperatura, umidade, pressão atmosférica, vento |
| Eventos extremos | seca, alagamentos, enchentes, mapeamentos de risco |
| Socioeconômicas / infraestrutura | população estimada, PIB per capita, IDH-M, GINI, saneamento, favelas, pavimentação |

Fontes públicas utilizadas: **SINAN/DATASUS**, **INMET** (estações automáticas), **IBGE** (Censo, Aglomerados Subnormais, Munic), **Atlas do Desenvolvimento Humano**, **Sistema do Tesouro Nacional (CAPAG)**, **SNIS/SINISA**, **OpenDATASUS** (febre amarela), **NASA**, **CETESB** (balneabilidade, enterococos).

## Estrutura do repositório

```
arboviral_data_science/
├── README.md
├── LICENSE
└── contexto/                    # material legado anterior à criação deste repo
    ├── Relatório Parcial - Arboviroses.pdf
    └── IC - ARBOVIROSES-.../    # dump do Drive compartilhado
        ├── Colabs/              # 16 notebooks (pipeline de dados)
        ├── Csvs Brutos/         # dados-fonte (SINAN, INMET, MUNIC, Febre Amarela)
        ├── Csvs Filtrados/      # dengue por ano em Parquet
        ├── Dicionários de Dados/
        ├── Gráficos/            # análises exploratórias (geral + por cidade)
        └── Dados para inserção no BD/
```

A estrutura de diretórios para código de modelagem e plataforma será definida nas próximas etapas.

## Referências principais

- Bergmeir, Hyndman & Koo (2018). *A note on the validity of cross-validation for evaluating autoregressive time series prediction.* CSDA.
- Hewamalage, Ackermann & Bergmeir (2023). *Forecast evaluation for data scientists: common pitfalls and best practices.* DMKD.
- Leung et al. (2023). *A systematic review of dengue outbreak prediction models.* PLOS NTD.
- Lundberg & Lee (2017). *A unified approach to interpreting model predictions (SHAP).* NeurIPS.
- Magalhaes et al. (2020). *The endless challenges of arboviral diseases in Brazil.* TMID.
- Rahman, Amrin & Shiddik (2025). *Dengue early warning system and outbreak prediction tool in Bangladesh using interpretable tree-based machine learning model.* Health Science Reports.
- Saito & Rehmsmeier (2015). *The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets.* PLOS ONE.

A lista completa está no relatório parcial em [contexto/Relatório Parcial - Arboviroses.pdf](contexto/Relatório%20Parcial%20-%20Arboviroses.pdf).

## Licença

[MIT](LICENSE) © 2026 Lázaro Vinaud
