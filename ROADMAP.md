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
| 1.4 | Sensitivity analysis com `--no-cross`: quantificar ganho das features cross-doença | 1 dia | ✅ feito (2026-05-14). Análise pareada PRE × POS-Onda 2 com Wilcoxon e pivot modelo×doença. Resultado: o ganho cross-doença robusto está concentrado em **RF × chikungunya** (+0.056 Δ AUPRC); os outros cenários flutuam pequeno e em geral neutro a desfavorável (efeito médio em zika é −0.005 a −0.008, p≈0.06–0.09). A interpretação anterior baseada em SHAP global ("cross é essencial pra zika") foi corrigida — SHAP mede importância dentro do modelo cross, sensitivity mede efeito real. Detalhes em [RELATORIO_MODELAGEM.md §11](RELATORIO_MODELAGEM.md). Comparativo gerado por `arboviral.analyze_no_cross --historico`. |
| 1.5 | Hyperparameter tuning com Optuna nos top 3 modelos | 2-3 dias | 📋 |
| 1.6 | Explicabilidade local para EBM e LogReg (não só árvores) | 0.5 dia | ✅ feito — `explicacao_local()` despacha por tipo de modelo (SHAP / coef×valor padronizado / `explain_local` nativo do EBM) |

**Resultado esperado**: IC final com 4 RQs respondidas + análise de antecipação (achado central) + relatório consolidado para defesa.

### Sugestões do orientador (2026-05-09) — escopo de visualização

Após avaliar a plataforma, o orientador propôs três melhorias de UX para a
demo da banca e para o paper, todas dentro do app (sem mudanças no core):

| # | Item | Status |
|---|---|---|
| 1.7 | Versão em inglês da interface (i18n PT/EN, toggle no canto da sidebar) | ✅ feito — camada `app/i18n/`, 387 chaves em paridade pt/en, smoke-test cobrindo 7 telas × 2 idiomas |
| 1.8 | Mapa com múltiplas granularidades (município → DRS → região intermediária) | ✅ feito — radio na sidebar; lookup gerado por `scripts/gerar_geo_lookup.py` a partir do scraping da SES-SP + IBGE/`geobr`; agregação em `app/lib/agregacao_geo.py` (prob ponderada por população, casos somados) |
| 1.9 | Animação temporal mensal (movimento da doença ao longo do ano) | ✅ feito — frames Plotly + slider + play; cor codifica probabilidade, tamanho da bolinha codifica casos nos níveis agregados |
| 1.10 | Modo produção: predição para o mês corrente | 🔜 pendente — hoje o app só serve os folds de backtesting (2022–2024). Para um gestor olhar "o alerta deste mês" precisaríamos de (a) features t–1 atualizadas, esbarrando na latência de notificação do SINAN (~30–60 d) — provavelmente exige nowcasting; (b) um modelo "produção" retreinado com tudo até o mês anterior, separado dos folds de validação; (c) job mensal de inferência gravando `data/processed/predicoes_atual.parquet`. É entrega de plataforma, não de IC — fica para depois da defesa. |

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

**Ainda pendentes** (2 itens): 1 (LIRAa, aguardando LAI à CCD-SP), 10 (NDVI). O item original #8 (eventos massivos) foi descartado de comum acordo: definição ambígua de "evento massivo", ausência de portal único e custo de curadoria manual desproporcional ao ganho esperado para uma IC.

**Onda 2 em andamento (2026-05-12)**:
- #6 mobilidade pendular ✅ — 2 colunas em série temporal combinando vintages Censo 2010 (microdados, matriz O-D completa) e Censo 2022 (SIDRA tabela 10329, apenas saídas). `pendulares_entram_trabalho` em 2015–2021 + NaN em 2022–2025; `pendulares_saem_trabalho` cobre toda a série 2015–2025. Detalhes em AUDITORIA_DADOS.md §15.
- #7 SIH-SUS internações ✅ — 4 colunas mensais a partir das AIH-RD do DATASUS (132 arquivos `RDSP{AAMM}.dbc`, ~2 GB), classificadas por CID-10 do diagnóstico principal: dengue (A90+A91), chikungunya (A92.0), zika (A92.5+A92.8) e febre amarela (A95*). Detalhes em AUDITORIA_DADOS.md §16.

Master: 79 → 85 colunas (+2 mobilidade, +4 SIH-SUS).

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

#### 6. **Mobilidade pendular intermunicipal** ✅ CONCLUÍDO (2026-05-12)
- **O que adiciona**: 2 colunas em série temporal — `pendulares_entram_trabalho` e `pendulares_saem_trabalho`.
- **Implementado em**:
  - Coleta: `src/arboviral/scraping/mobilidade_pendular.py` — microdados Censo 2010 (SP1.zip + SP2_RM.zip, ~200 MB) + SIDRA tabela 10329 do Censo 2022 (API REST, JSON ~77 KB)
  - Parsing: `src/arboviral/ingestion/mobilidade_pendular.py` — reconstrói matriz O-D do 2010 (fixed-width PESS, ~3,65 milhões de registros) e lê o JSON SIDRA 2022; combina em série anual
- **Fontes**:
  - IBGE Censo Demográfico 2010 — Microdados da Amostra <https://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Resultados_Gerais_da_Amostra/Microdados/>
  - IBGE Censo Demográfico 2022 — SIDRA tabela 10329 <https://sidra.ibge.gov.br/tabela/10329> (variável 13373, C469=12188 "Outro município")
- **Estratégia temporal**:
  - Anos 2015–2021 → vintage 2010 (ambas as colunas preenchidas via matriz O-D)
  - Anos 2022–2025 → vintage 2022 (apenas `pendulares_saem_trabalho`; `entram` fica NaN porque SIDRA não desagrega destino)
- **Cobertura**: 100% para `saem` em todos os anos; 100% para `entram` em 2015–2021. NaN em `entram` para 2022–2025 — decisão metodológica explícita, preferimos honestidade temporal a forward-fill enganoso.
- **Validação**: soma dos pesos amostrais 2010 bate com pop SP (~41,26 milhões). Comparação 2010 vs 2022 mostra queda das saídas em quase todas as cidades-dormitório (Guarulhos −22k, Suzano −19k, SBC −17k) — efeito coerente com o home office pós-pandemia. Detalhes em [AUDITORIA_DADOS.md §15](AUDITORIA_DADOS.md).
- **Upgrade futuro**: quando IBGE liberar microdados do Censo 2022, reconstruir matriz O-D 2022 e preencher `pendulares_entram_trabalho` no intervalo 2022–2025.

#### 7. **Dados de internação por arboviroses (SIH-SUS)** ✅ CONCLUÍDO (2026-05-12)
- **O que adiciona**: 4 colunas mensais — `sih_internacoes_{dengue,chikungunya,zika,febre_amarela}` —, contagens de internação hospitalar pelo SUS classificadas pelo CID-10 do diagnóstico principal (A90+A91, A92.0, A92.5+A92.8, A95*).
- **Implementado em**:
  - Coleta: `src/arboviral/scraping/sih_sus.py` (132 arquivos `RDSP{AAMM}.dbc` do FTP DATASUS, ~2 GB)
  - Parsing: `src/arboviral/ingestion/sih_sus.py` (DBC → DBF via `pyreaddbc`, streaming registro a registro filtrando CIDs e UF de residência, lookup IBGE 6→7 dígitos reaproveitado do SINAN)
- **Fonte**: DATASUS — SIH-SUS, AIH-RD (Autorização de Internação Hospitalar reduzida) <ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/>
- **Cobertura**: 132 arquivos × 11 anos × 12 meses. Inclui residentes paulistas internados em outros estados (busca por tratamento em centros de referência), o que o SINAN não captura.
- **Diferença sobre SINAN**: SINAN registra notificação (vigilância); SIH-SUS registra internação efetiva (severidade). Coexistem como sinais complementares, não substituem.
- **Validação prévia**: piloto com 24 arquivos (apenas 2024) registrou 45.427 internações por dengue, pico de 2.034 em SP capital em mai/2024 — coerente com a maior epidemia do estado. Detalhes em [AUDITORIA_DADOS.md §16](AUDITORIA_DADOS.md).
- **Limitação documentada**: cobertura apenas SUS (sem plano privado), o que subestima em municípios de maior renda.

### 🥉 Top 8-10 — Impacto complementar

#### 8. ~~Eventos massivos~~ — DESCARTADO (2026-05-12)
- Originalmente proposto como flag binário "houve evento massivo no município/mês" (Carnaval, festas, shows).
- Removido do escopo: não há portal único nem padrão de curadoria; cada município publica em formato livre. Custo de curadoria manual desproporcional ao ganho esperado para uma IC.
- Se eventualmente quisermos reaproveitar a hipótese, o caminho automatizável seria um flag de "mês de Carnaval/Semana Santa", derivado direto do calendário, sem precisar de curadoria municipal.

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
- ✅ **Mobilidade pendular** — concluída na Onda 2 com vintages 2010 + 2022 (ver §15 do AUDITORIA_DADOS).
- ✅ **Latência SINAN** — concluído (era "fruta baixa"; mediana SP variou 3-7 dias por doença, com chikungunya como mais lento — coerente com o esperado).

---

## 3. Longo prazo — Critérios para artigo internacional

Análise sincera do que falta para cada nível de publicação. Ordenados por dificuldade crescente.

### 3.1 Workshop nacional (BraSNAM, ENIAC) — viável em ~1 mês

**Já temos:**
- ✅ Pipeline de dados completo e reproducível, com 5/10 fontes do top 10 integradas (Onda 1)
- ✅ Comparação de 4 definições de surto (RQ4)
- ✅ Análise de antecipação (recall em INICIO de surto) — achado central
- ✅ SHAP global em zika mostra `dengue_casos_lag1` e `dengue_casos_roll6` no topo. Onda 1 ainda elevou zika RF×inc100 de AUPRC 0.014 → 0.101 (+640%) — o ganho veio das fontes ambientais (MapBiomas) + cobertura sanitária (ESF) + vacinação. **A leitura anterior** ("cross-doença essencial") foi revisada pela sensitivity do item 1.4: SHAP global mede importância dentro do modelo cross, não substituibilidade. O ganho cross robusto está localizado em RF × chikungunya. Para zika, cross é levemente desfavorável em média (Δ AUPRC ≈ −0.005, p≈0.09). Ver §5 e §11 do RELATORIO_MODELAGEM.md.
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
| **Médio** | 2.6 Mobilidade pendular | ✅ feito | Espalhamento via deslocamento (Censo 2010 microdados + Censo 2022 SIDRA) |
| **Médio** | 2.7 SIH-SUS internações | ✅ feito | Complementa SINAN; CID-10 A90/A91/A92.0/A92.5/A92.8/A95 |
| **Médio** | 2.9 Densidade populacional | ✅ feito | Driver direto de transmissão urbana |
| **Médio** | 2.10 NDVI mensal | 📋 | Sazonalidade vegetal (NASA APPEEARS / Earth Engine) |
| **Longo** | 3.4 Validação externa MG | 📋 | Crítico para artigo sério |
| **Longo** | 3.4 Validação externa 2º estado | 📋 | Generalização real |
| **Longo** | Multitask multidoença | 📋 | Diferencial metodológico para journal |

**Marcador de progresso geral**: 5/10 fontes do top 10 integradas + 1.1 (predições/modelos) e 1.6 (explicabilidade uniforme) feitos. Restam 5 fontes + 4 itens curtos para fechar a IC.
