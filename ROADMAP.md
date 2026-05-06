# Roadmap — Próximos Passos do Projeto

Este documento organiza o que vem após a finalização do pipeline atual. Dividido em três blocos:

1. **Curto prazo** — refatoração e análises pendentes para fechar a IC
2. **Médio prazo** — fontes de dados a adicionar (top 10 priorizadas)
3. **Longo prazo** — o que falta para tornar o trabalho digno de artigo internacional

---

## 1. Curto prazo — finalização da IC

| # | Item | Esforço | Status |
|---|---|---|---|
| 1.1 | Refatorar pipeline para salvar predições (`predictions.parquet`) e modelos treinados (`.joblib`) | 1 dia | ⏳ próximo |
| 1.2 | SHAP estratificado por perfil de município (clusters por IDH × população) | 1-2 dias | 📋 |
| 1.3 | Análise de robustez (RQ3): simular dados faltantes 10/30/50% e medir queda de performance | 2-3 dias | 📋 |
| 1.4 | Sensitivity analysis com `--no-cross`: quantificar ganho das features cross-doença | 1 dia | 📋 |
| 1.5 | Hyperparameter tuning com Optuna nos top 3 modelos | 2-3 dias | 📋 |

**Resultado esperado**: IC final com 4 RQs respondidas + análise de antecipação (achado central) + relatório consolidado para defesa.

---

## 2. Médio prazo — Top 10 fontes de dados a adicionar

Listadas em ordem decrescente de impacto esperado em AUPRC. Cada uma expande o poder preditivo e reduz NaN no dataset.

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

#### 2. **MapBiomas — uso e cobertura do solo**
- **O que adiciona**: % de cobertura por classe (mata, agropastoril, urbano, água) por município, anual.
- **Por que importa**: áreas de mata = transmissão silvestre (FA, Mayaro). Urbanização rápida = vetor urbano. Agricultura = uso de pesticidas e modificação de habitat.
- **Onde obter**:
  - https://mapbiomas.org/ (gratuito, abertos)
  - Estatísticas municipais já agregadas em CSV
- **Formato**: CSV download direto
- **Esforço**: 2 dias (download + integração)

#### 3. **Cobertura ESF (Estratégia Saúde da Família)**
- **O que adiciona**: % de cobertura ESF por município (mensal/anual).
- **Por que importa**: determina capacidade de detecção precoce e resposta a surtos. Município com cobertura alta detecta cedo, captura mais casos no SINAN — mas também responde mais rápido.
- **Onde obter**: DATASUS/e-Gestor AB
  - https://egestorab.saude.gov.br/paginas/acessoPublico/relatorios/relHistoricoCoberturaAB.xhtml
- **Formato**: Excel/CSV mensal
- **Esforço**: 2-3 dias

### 🥈 Top 4-7 — Impacto moderado

#### 4. **Vacinação — cobertura vacinal de febre amarela**
- **O que adiciona**: % população vacinada contra FA por município, anual.
- **Por que importa**: diferencia risco real (transmissão) de risco populacional (vulnerabilidade). Sem isso, modelo confunde "área de risco baixo" com "área bem protegida".
- **Onde obter**: DATASUS PNI (Programa Nacional de Imunizações)
  - http://pni.datasus.gov.br/
- **Esforço**: 2 dias

#### 5. **Tempo de notificação (latência SINAN)**
- **O que adiciona**: feature derivada — média do delta `DT_NOTIFIC - DT_SIN_PRI` por município/mês.
- **Por que importa**: proxy direto de subnotificação. Município com latência alta tem casos sub-reportados, então casos baixos podem mascarar surtos reais.
- **Onde obter**: já temos! Calculável a partir dos arquivos DBC do SINAN que já baixamos.
- **Esforço**: 1 dia (modificar `sinan.py` para preservar essa info na agregação)

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

#### 9. **Densidade populacional e uso urbano**
- **O que adiciona**: `pop / area_km2`, % urbanização.
- **Por que importa**: hoje só temos `populacao_estimada`. Densidade é mais explicativa para vetor urbano (densidade alta favorece *Aedes aegypti*).
- **Onde obter**: IBGE — área já está em outras tabelas SIDRA.
- **Esforço**: 1 dia

#### 10. **Cobertura vegetal local — NDVI (índice de vegetação)**
- **O que adiciona**: NDVI mensal por município (média de pixels do MODIS/Landsat).
- **Por que importa**: complementa MapBiomas com sazonalidade — vegetação verde = mosquitos abundantes.
- **Onde obter**: NASA APPEEARS / Google Earth Engine (gratuito, mas precisa programação)
- **Esforço**: 3-5 dias (requer aprender Earth Engine)

### Notas práticas sobre as fontes

- **LIRAa é o "santo graal"** — qualquer artigo sério em arboviroses cita LIRAa como variável-chave. Vale priorizar.
- **MapBiomas + ESF + vacinação** preenchem lacunas estruturais que nosso modelo ainda não vê.
- **Mobilidade pendular** e **eventos massivos** são difíceis mas podem virar diferencial se conseguirmos extrair.
- **Latência SINAN** é "fruta baixa" — já temos os dados, só não calculamos.

---

## 3. Longo prazo — Critérios para artigo internacional

Análise sincera do que falta para cada nível de publicação. Ordenados por dificuldade crescente.

### 3.1 Workshop nacional (BraSNAM, ENIAC) — viável em ~1 mês

**Já temos:**
- ✅ Pipeline de dados completo e reproducível
- ✅ Comparação de 4 definições de surto (RQ4)
- ✅ Análise de antecipação (recall em INICIO de surto) — achado central
- ✅ SHAP cross-doença (zika previsto por features de dengue)

**Falta:**
- 📋 Hyperparameter tuning (Optuna) para fortalecer resultados
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
- 📋 Pelo menos 1-2 fontes novas do top 10 acima (LIRAa de preferência)

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

| Prazo | Item | Impacto |
|---|---|---|
| **Curto** | 1.1 Salvar predições e modelos | Análises post-hoc 100× mais rápidas |
| **Curto** | 1.2 SHAP estratificado | Achado novo + interpretação rica |
| **Curto** | 1.3 Robustez a NaN (RQ3) | Responde RQ pendente, publicável |
| **Curto** | 1.4 Sensitivity --no-cross | Quantifica ganho cross-doença |
| **Curto** | 1.5 Hyperparameter tuning | +5% AUPRC esperado |
| **Médio** | 2.1 LIRAa | +20% AUPRC esperado, diferencial |
| **Médio** | 2.2 MapBiomas | Drivers ambientais, interpretação |
| **Médio** | 2.3 Cobertura ESF | Controla viés de detecção |
| **Médio** | 2.5 Latência SINAN | "Fruta baixa", proxy de subnotificação |
| **Longo** | 3.4 Validação externa MG | Crítico para artigo sério |
| **Longo** | 3.4 Validação externa 2º estado | Generalização real |
| **Longo** | Multitask multidoença | Diferencial metodológico para journal |
