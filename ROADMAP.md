# Roadmap — Próximos Passos do Projeto

Este documento organiza o que vem após a finalização do pipeline atual. Dividido em três blocos:

1. **Curto prazo** — refatoração e análises pendentes para fechar a IC
2. **Médio prazo** — fontes de dados a adicionar (top 10 priorizadas)
3. **Longo prazo** — o que falta para tornar o trabalho digno de artigo internacional

---

## 1. Curto prazo — finalização da IC

| # | Item | Esforço | Status |
|---|---|---|---|
| 1.1 | Refatorar pipeline para salvar predições (`predictions.parquet`) e modelos treinados (`.joblib`) | 1 dia | ✅ feito (commit `fb0a289`) |
| 1.2 | SHAP estratificado por perfil de município (clusters por IDH × população) | 1-2 dias | 📋 |
| 1.3 | Análise de robustez (RQ3): simular dados faltantes 10/30/50% e medir queda de performance | 2-3 dias | 📋 |
| 1.4 | Sensitivity analysis com `--no-cross`: quantificar ganho das features cross-doença | 1 dia | 📋 (flag presente, mascaramento ainda não implementado em `train.py`) |
| 1.5 | Hyperparameter tuning com Optuna nos top 3 modelos | 2-3 dias | 📋 |
| 1.6 | Explicabilidade local para EBM e LogReg (não só árvores) | 0.5 dia | ✅ feito — `explicacao_local()` despacha por tipo de modelo (SHAP / coef×valor padronizado / `explain_local` nativo do EBM) |

**Resultado esperado**: IC final com 4 RQs respondidas + análise de antecipação (achado central) + relatório consolidado para defesa.

---

## 2. Médio prazo — Top 10 fontes de dados a adicionar

Listadas em ordem decrescente de impacto esperado em AUPRC. Cada uma expande o poder preditivo e reduz NaN no dataset.

### Status da Onda 1 (atualizado 2026-05-07)

**5 de 10 fontes integradas** — todas via scraping/download automático e parser dedicado, com docstring documentando URL e formato:

| # | Fonte | Variáveis adicionadas | Cobertura SP |
|---|---|---|---:|
| 2 | MapBiomas Coleção 10.1 | 5 colunas (`pct_floresta`, `pct_agricultura`, `pct_nao_vegetado`, `pct_agua`, `pct_natural_nao_florestal`) | 100% |
| 3 | Cobertura ESF/APS (e-Gestor MS) | 5 colunas (`esf_metodologia`, `esf_cobertura_pct`, `esf_qt_equipes`, `esf_qt_capacidade`, `esf_pop_referencia`) | 99.9% |
| 4 | Vacinação FA (PNI/DATASUS) | 1 coluna (`cob_vac_fa_pct`) | 97.5% |
| 5 | Latência SINAN | 9 colunas (mediana, p90, n_casos × 3 doenças com volume) | ~99.9% |
| 9 | Densidade IBGE | 2 colunas (`area_km2`, `densidade_2023`) | 100% |

**Total**: dataset de 57 → **79 colunas** (+22 do master) e features de 117 → **140** (+23). Re-treino completo (315 combinações = 4 doenças × 4 definições × 7 modelos × ~3 folds) confirmou ganho relevante em zika (RF inc100: AUPRC 0.014 → 0.101 = **+640%**) e ganho moderado em dengue/chikungunya (~+0.02 a +0.03 nos top modelos). Detalhes em `RELATORIO_MODELAGEM.md` §3-4.

**Ainda pendentes** (5 itens, em ordem de prioridade revisada): 1 (LIRAa), 6 (mobilidade pendular), 7 (SIH-SUS), 8 (eventos massivos), 10 (NDVI).

### 🥇 Top 3 — Maior impacto esperado

#### 1. **LIRAa (Levantamento Rápido de Índices para Aedes aegypti)**
- **O que adiciona**: índice vetorial bimensal por município (Índice de Infestação Predial, % de imóveis com larvas).
- **Por que importa**: mede presença real do mosquito vetor. Provavelmente a feature mais preditiva possível para arboviroses urbanas (dengue, zika, chiku).
- **Onde obter**:
  - SES-SP (Secretaria de Estado da Saúde de SP) — publica trimestralmente
  - https://www.saude.sp.gov.br/cve-centro-de-vigilancia-epidemiologica-prof.-alexandre-vranjac/areas-de-vigilancia/doencas-de-transmissao-por-vetores-e-zoonoses/agravos/dengue
  - SVS/Ministério da Saúde também publica boletins federais
- **Formato típico**: PDF/Excel por município (chato de extrair, mas estruturado)
- **Esforço estimado**: 1 semana (web scraping + parser)

#### 2. **MapBiomas — uso e cobertura do solo** ✅ CONCLUÍDO
- **O que adiciona**: % de cobertura por classe (floresta, agricultura, não vegetado, água, natural não florestal) por município, anual 2015-2024.
- **Implementado em**:
  - Coleta: `src/arboviral/scraping/mapbiomas.py` (download Google Drive, ~75 MB)
  - Parsing: `src/arboviral/ingestion/mapbiomas.py`
- **Fonte**: MapBiomas Brasil Coleção 10.1 (DOI: 10.58053/MapBiomas/SJZOLT)
- **Cobertura**: 645/645 municípios SP × 10 anos, 100% completude
- **Estatísticas SP**: agricultura 74% mediano, floresta 9.4% mediano, urbanizado 1.3% mediano (download + integração)

#### 3. **Cobertura ESF (Estratégia Saúde da Família)** ✅ CONCLUÍDO
- **O que adiciona**: 5 colunas (cobertura %, qtde equipes ESF, capacidade, pop referência, metodologia).
- **Implementado em**:
  - Coleta: `src/arboviral/scraping/esf_coverage.py` (API REST descoberta via DevTools)
  - Parsing: `src/arboviral/ingestion/esf.py` (harmoniza AB vs APS)
- **Endpoints**: `relatorioaps-prd.saude.gov.br/cobertura/{ab,aps}` — GET retornando JSON
- **Quebra metodológica em 2021** documentada via flag `esf_metodologia` ('AB'/'APS')
- **Cobertura**: 99.9% das linhas SP (645 municípios × 132 meses)

### 🥈 Top 4-7 — Impacto moderado

#### 4. **Vacinação — cobertura vacinal de febre amarela** ✅ CONCLUÍDO
- **O que adiciona**: 1 coluna `cob_vac_fa_pct` (% da população-alvo imunizada por município/ano).
- **Implementado em**:
  - Coleta: `src/arboviral/scraping/pni_febre_amarela.py` (CSV TabNet em formato inteli.gente)
  - Parsing: `src/arboviral/ingestion/vacinacao_fa.py` (filtra SP)
- **Fonte**: DATASUS PNI — `tabnet.datasus.gov.br/cgi/tabcgi.exe?pni/cnv/cpniuf.def`
- **Cobertura**: 645/645 municípios SP, 1994-2026 (gap 2017 preenchido por ffill no master)
- **Achado preliminar**: mediana SP cai de ~94% (2002) para ~74% (2025) — declínio relevante para risco populacional

#### 5. **Tempo de notificação (latência SINAN)** ✅ CONCLUÍDO
- **O que adiciona**: 3 colunas por doença (mediana, p90, n_casos_com_latencia) — proxy de qualidade da vigilância.
- **Implementado em**: `src/arboviral/ingestion/sinan.py` (estendido para extrair DT_NOTIFIC - DT_SIN_PRI por caso, filtrar valores absurdos, agregar por município/mês).
- **Cobertura**: ~99.9% dos casos têm ambas as datas; mediana SP:
  - Dengue: 3 dias (sistema funcionando bem)
  - Zika: 4 dias
  - Chikungunya: 7 dias (doença menos lembrada, notificação mais lenta)

#### 6. **Mobilidade pendular intermunicipal**
- **O que adiciona**: matriz origem-destino de deslocamentos (estudo, trabalho).
- **Por que importa**: surtos se espalham por movimento humano. Município que recebe muitos pendulares de área endêmica tem risco maior.
- **Onde obter**:
  - IBGE Censo 2010 e 2022 (deslocamento pendular)
  - Google Mobility Reports (Covid, descontinuado mas histórico disponível)
- **Esforço**: 3-5 dias (matriz é grande; precisa agregar features tipo "% de pendulares vindo de áreas com surto")

#### 7. **Dados de internação por arboviroses (SIH-SUS)**
- **O que adiciona**: contagem de internações pelo SIH-SUS (Sistema de Informações Hospitalares), CID-10 A90/A91/A92.
- **Por que importa**: já temos `internacoes` do SINAN, mas SIH-SUS é mais completo (inclui internações de cidadãos do estado SP em outros estados).
- **Onde obter**: DATASUS FTP — `/dissemin/publicos/SIHSUS/200801_/Dados/`
- **Esforço**: 3 dias (similar ao SINAN — DBC, lookup, agregação)

### 🥉 Top 8-10 — Impacto complementar

#### 8. **Eventos massivos**
- **O que adiciona**: flag binário "houve evento massivo no município/mês" (Carnaval, festas regionais, shows).
- **Por que importa**: picos de mobilidade = picos de transmissão (especialmente dengue).
- **Onde obter**: SECTUR municipais (manual), agendas culturais (Embratur).
- **Esforço**: 1 semana (curadoria manual; pouco escalável)

#### 9. **Densidade populacional e uso urbano** ✅ CONCLUÍDO
- **O que adiciona**: `area_km2`, `densidade_2023` (hab/km²).
- **Implementado em**:
  - Coleta: `src/arboviral/scraping/ibge_areas.py`
  - Parsing: `src/arboviral/ingestion/densidade.py`
- **Fonte**: FTP IBGE — `geoftp.ibge.gov.br/.../areas_territoriais/2024/AR_BR_RG_UF_RGINT_RGI_MUN_2024.xls`
- **Cobertura**: 645/645 municípios SP, 100% completude
- **Estatísticas**: densidades de 3.6 hab/km² (interior) a 14.593 hab/km² (metropolitano)

#### 10. **Cobertura vegetal local — NDVI (índice de vegetação)**
- **O que adiciona**: NDVI mensal por município (média de pixels do MODIS/Landsat).
- **Por que importa**: complementa MapBiomas com sazonalidade — vegetação verde = mosquitos abundantes.
- **Onde obter**: NASA APPEEARS / Google Earth Engine (gratuito, mas precisa programação)
- **Esforço**: 3-5 dias (requer aprender Earth Engine)

### Notas práticas sobre as fontes

- **LIRAa permanece como o "santo graal"** — agora único item do top 3 ainda pendente. Qualquer artigo sério em arboviroses cita LIRAa como variável-chave. Próximo a atacar.
- ✅ **MapBiomas + ESF + vacinação FA** — concluídos. Confirmaram preencher lacunas estruturais: zika passou de "sem sinal" (AUPRC 0.014) para "modelo aprende" (0.101) com a entrada dessas fontes.
- **Mobilidade pendular** e **eventos massivos** continuam difíceis mas podem virar diferencial se conseguirmos extrair.
- ✅ **Latência SINAN** — concluído (era "fruta baixa"; mediana SP variou 3-7 dias por doença, com chikungunya como mais lento — coerente com o esperado).

---

## 3. Longo prazo — Critérios para artigo internacional

Análise sincera do que falta para cada nível de publicação. Ordenados por dificuldade crescente.

### 3.1 Workshop nacional (BraSNAM, ENIAC) — viável em ~1 mês

**Já temos:**
- ✅ Pipeline de dados completo e reproducível, com 5/10 fontes do top 10 integradas (Onda 1)
- ✅ Comparação de 4 definições de surto (RQ4)
- ✅ Análise de antecipação (recall em INICIO de surto) — achado central
- ✅ SHAP cross-doença (zika previsto por features de dengue) — agora **quantitativamente reforçado pela Onda 1**: zika RF×inc100 passou de AUPRC 0.014 → 0.101 (+640%), confirmando que features ambientais (MapBiomas) + cobertura sanitária (ESF) + vacinação ampliam o sinal cross-doença
- ✅ Explicabilidade local UNIFORME entre todos os modelos do portfolio: árvores via SHAP, EBM via `explain_local` nativo (interpret-ml), LogReg via `coef × valor padronizado`. Output uniforme em `explicacao_local()` permite que a interface (app Streamlit) trate qualquer modelo igual.

**Falta:**
- 📋 Hyperparameter tuning (Optuna) para fortalecer resultados
- 📋 Sensitivity `--no-cross` finalizar (mascaramento no `train.py` ainda placeholder)
- 📋 Texto do artigo (~8-12 páginas)

**Veículos típicos**:
- BraSNAM (Brazilian Workshop on Social Network Analysis and Mining)
- ENIAC (Encontro Nacional de Inteligência Artificial e Computacional)
- KDMiLe (Symposium on Knowledge Discovery, Mining and Learning)

### 3.2 Conferência internacional (BRACIS, IJCAI, IEEE) — viável em ~3-6 meses

**Falta adicionar (em ordem):**
- 📋 **Validação externa em outros estados** (MG, RJ ou PR) — diferencial técnico crítico
- 📋 SHAP estratificado por perfil de município
- 📋 Análise de robustez a dados faltantes (RQ3)
- 📋 Comparação com baseline da literatura: ARIMA, Prophet, simple LSTM
- 📋 Calibração de probabilidades (importante para uso prático)
- 📋 LIRAa — única fonte do top 3 ainda pendente (5 das outras já entraram na Onda 1)

**Esforço estimado**: 3-4 meses de trabalho focado pós-IC.

**Veículos típicos**:
- BRACIS (Brazilian Conference on Intelligent Systems)
- IJCAI (workshops do AI for Social Good)
- IEEE BigData (track de healthcare)
- IEEE BHI (Biomedical and Health Informatics)

### 3.3 Journal internacional (Lancet Reg Health, PLOS NTD, IJID) — viável em ~6-12 meses

**Falta tudo do nível anterior +:**
- 📋 **Validação em pelo menos 2 estados externos** (não só 1)
- 📋 **Comparação com modelo de referência publicado** (ex.: replicar paper recente e mostrar superação)
- 📋 **Discussão de impacto operacional** (custo evitado, vidas salvas — quantificado)
- 📋 **Análise de equidade**: o modelo funciona igualmente bem em municípios pobres vs ricos? Pequenos vs grandes?
- 📋 **Multitask learning** (modelo único para 4 doenças) — diferencial metodológico
- 📋 **Análise de calibração temporal**: a performance se mantém em 2025, 2026?
- 📋 **Discussão de generalização**: por que funciona/não funciona em SP? Hipóteses para outros climas?
- 📋 **Submissão para revisão por pares com saúde pública** (idealmente coautoria com epidemiologista)

**Esforço estimado**: 6-12 meses pós-IC, com possível necessidade de bolsa de mestrado.

**Veículos típicos**:
- The Lancet Regional Health — Americas
- PLOS Neglected Tropical Diseases
- International Journal of Infectious Diseases (IJID)
- BMC Infectious Diseases

### 3.4 Validação externa — o passo crítico para artigo sério

**Como executar a validação externa SP → outro estado:**

A pipeline atual é parametrizada apenas para SP (UF=35). Para validar em outro estado:

| Etapa | O que muda | Esforço |
|---|---|---|
| Filtro UF nos scripts SINAN | trocar `'35'` por código alvo (MG=`'31'`, RJ=`'33'`, PR=`'41'`) | 1 hora |
| Lookup município → estação INMET | gerar novo lookup com municípios do estado alvo | 1 dia (script existente reutilizável) |
| NASA POWER | re-rodar API para todos os municípios do novo estado | 1-2 dias (rate limit) |
| IBGE PIB/pop, IDH-M, GINI | já são nacionais, só refiltrar | 1 hora |
| MUNIC, SINISA, habitação | nacionais, só refiltrar | 1 dia |
| Treinar modelos no estado alvo | rodar `train.py` com novo dataset | 1-2 dias |
| Avaliar modelo SP em estado alvo | trocar fold de teste para outro estado | 1 hora (mudança trivial em `splits.py`) |

**Total**: ~1 semana para o primeiro estado externo, ~3 dias para cada estado adicional.

**Recomendação**: começar com **Minas Gerais** (UF 31), por ter perfil epidemiológico similar a SP (clima tropical, alta incidência de dengue) — facilita comparação justa.

### 3.5 Estrutura sugerida do artigo (preparação)

Seções alinhadas com o que já temos:

1. **Introduction**: motivação (dengue Brasil), state of the art (citar Leung 2023, Rahman 2025), gap identificado (definição operacional + antecipação)
2. **Methods**:
   - Data sources (10 fontes integradas, tabela)
   - Outbreak labels (4 definições, justificativa, Cohen's kappa)
   - Features (lags, rolling, climate, sociodemographic)
   - Models (portfolio com explicabilidade)
   - Validation (expanding window)
3. **Results**:
   - Ranking global (RQ1)
   - Sensibilidade à definição (RQ4)
   - SHAP / drivers (RQ2)
   - **Análise de antecipação** (RQ central)
   - Validação externa (em outro estado)
   - Análise estratificada por perfil
4. **Discussion**:
   - Diferencial frente à literatura (antecipação + multi-definição)
   - Implicações para vigilância (SES-SP, gestor)
   - Limitações e trabalho futuro
5. **Conclusion**

A IC final pode já ser estruturada nesse formato — assim o artigo fica 60% pronto ao terminar a IC.

---

## Tabela-resumo: roadmap completo

| Prazo | Item | Status | Impacto |
|---|---|---|---|
| **Curto** | 1.1 Salvar predições e modelos | ✅ feito | Análises post-hoc 100× mais rápidas |
| **Curto** | 1.6 Explicabilidade EBM/LogReg uniforme | ✅ feito | Interface trata qualquer modelo igual |
| **Curto** | 1.2 SHAP estratificado | 📋 | Achado novo + interpretação rica |
| **Curto** | 1.3 Robustez a NaN (RQ3) | 📋 | Responde RQ pendente, publicável |
| **Curto** | 1.4 Sensitivity --no-cross | 📋 | Quantifica ganho cross-doença |
| **Curto** | 1.5 Hyperparameter tuning | 📋 | +5% AUPRC esperado |
| **Médio** | 2.1 LIRAa | 📋 | +20% AUPRC esperado, diferencial |
| **Médio** | 2.2 MapBiomas — uso do solo | ✅ feito | Distingue urbano/floresta/agric (drivers vetoriais distintos) |
| **Médio** | 2.3 Cobertura ESF/APS | ✅ feito | API REST direta (sem Selenium); 132 meses harmonizados |
| **Médio** | 2.4 Vacinação FA (PNI) | ✅ feito | Cobertura vacinal anual 1994-2026 — declínio observado de 94% (2002) → 74% (2025) |
| **Médio** | 2.5 Latência SINAN | ✅ feito | Proxy direto de subnotificação (mediana 3-7d por doença) |
| **Médio** | 2.6 Mobilidade pendular | 📋 | Espalhamento via deslocamento (IBGE Censo 2010/2022) |
| **Médio** | 2.7 SIH-SUS internações | 📋 | Complementa SINAN; CID-10 A90/A91/A92 |
| **Médio** | 2.8 Eventos massivos | 📋 | Picos de mobilidade (Carnaval, festas) — curadoria manual |
| **Médio** | 2.9 Densidade populacional | ✅ feito | Driver direto de transmissão urbana |
| **Médio** | 2.10 NDVI mensal | 📋 | Sazonalidade vegetal (NASA APPEEARS / Earth Engine) |
| **Longo** | 3.4 Validação externa MG | 📋 | Crítico para artigo sério |
| **Longo** | 3.4 Validação externa 2º estado | 📋 | Generalização real |
| **Longo** | Multitask multidoença | 📋 | Diferencial metodológico para journal |

**Marcador de progresso geral**: 5/10 fontes do top 10 integradas + 1.1 (predições/modelos) e 1.6 (explicabilidade uniforme) feitos. Restam 5 fontes + 4 itens curtos para fechar a IC.
