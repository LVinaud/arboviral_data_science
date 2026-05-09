"""
Strings em português brasileiro — referência canônica do app.

Cada idioma adicional (en.py, es.py futuro) deve replicar EXATAMENTE estas
chaves. Se uma chave estiver faltando no outro idioma, o `t()` faz fallback
para PT, então o app não quebra — mas o objetivo é manter paridade.

Convenção de nomes:
    {tela}.{secao}.{elemento}
    Ex.: home.hero.titulo, alertas.tabela.mes_predito

Placeholders usam {nome_kwarg}, resolvidos por str.format(**kwargs):
    "Análise para {municipio} em {mes_humano}"
"""
from __future__ import annotations

STRINGS: dict = {
    # ============================================================
    # app.py — entry point
    # ============================================================
    "app": {
        "page_title": "Alerta Precoce — Arboviroses SP",
    },

    # Navegação (títulos de st.Page no menu lateral)
    "nav": {
        "visao_geral": "Visão geral",
        "alertas": "Alertas",
        "municipio": "Município",
        "mapa": "Mapa de SP",
        "comparativo": "Comparativo",
        "variaveis": "Variáveis",
        "sobre": "Sobre o projeto",
    },

    # ============================================================
    # Termos comuns reutilizados em várias telas
    # ============================================================
    "comum": {
        "municipio": "Município",
        "doenca": "Doença",
        "modelo": "Modelo",
        "definicao_surto": "Definição de surto",
        "ano_teste": "Ano de teste",
        "mes_predito": "Mês predito",
        "mes_analise_shap": "Mês de análise (SHAP)",
        "filtros": "Filtros",
        "selecao": "Seleção",
        "probabilidade": "Probabilidade",
        "criticos": "Críticos",
        "altos": "Altos",
        "moderados": "Moderados",
        "surto_real": "Surto real",
        "sim": "Sim",
        "nao": "Não",
        "todos_meses": "Todos os meses",
        "pico_ano": "Pico do ano",
        "codigo_ibge": "Código IBGE",
        "categoria": "Categoria",
        "tipo": "Tipo",
        "fonte": "Fonte",
        "descricao": "Descrição",
        "minimo": "Mínimo",
        "media": "Média",
        "maximo": "Máximo",
        "observacao": "Observação",
        "nome_tecnico": "Nome técnico",
        "fonte_primaria": "Fonte primária",
        "n_features": "Nº de features",
        "pct_nan": "% NaN",
        "pct_nan_medio": "% NaN médio",
        "verdadeiros": "verdadeiros",
        "falsos": "falsos",
        "mes": "Mês",
    },

    # ============================================================
    # Dicionários de slugs → labels humanos
    # ============================================================
    "doenca": {
        "dengue": "Dengue",
        "zika": "Zika",
        "chikungunya": "Chikungunya",
        "febre_amarela": "Febre amarela",
    },

    "modelo": {
        "rf": "Random Forest",
        "xgb": "XGBoost",
        "lgbm": "LightGBM",
        "ebm": "EBM (Explainable Boosting)",
        "logreg": "Regressão Logística",
        "persistencia": "Persistência",
        "climatologia": "Climatologia",
    },

    "definicao": {
        "canal": "Canal endêmico (Min. Saúde)",
        "zscore": "Z-score (desvio do baseline)",
        "inc100": "100 casos / 100 mil hab",
        "inc300": "300 casos / 100 mil hab",
    },

    "mes": {
        "1": "Janeiro", "2": "Fevereiro", "3": "Março", "4": "Abril",
        "5": "Maio", "6": "Junho", "7": "Julho", "8": "Agosto",
        "9": "Setembro", "10": "Outubro", "11": "Novembro", "12": "Dezembro",
        "fora_range": "Mês {n}",
    },

    # Categorias de risco (badges + tabela)
    "risco": {
        "BAIXO": "BAIXO",
        "MODERADO": "MODERADO",
        "ALTO": "ALTO",
        "CRITICO": "CRÍTICO",
        "label_baixo": "Baixo",
        "label_moderado": "Moderado",
        "label_alto": "Alto",
        "label_critico": "Crítico",
    },

    # ============================================================
    # lib/tema.py — brand e footer da sidebar
    # ============================================================
    "tema": {
        "brand_titulo": "Alerta Precoce",
        "brand_sub": "Arboviroses · SP",
        "footer_linha1": "ICMC · USP São Carlos",
        "footer_linha2": "Iniciação Científica",
        "footer_linha3": "Lázaro Vinaud — 2025/26",
    },

    # ============================================================
    # lib/carregar.py — spinners do @st.cache_data
    # ============================================================
    "carregar": {
        "municipios": "Carregando municípios...",
        "master": "Carregando dataset master...",
        "labels": "Carregando rótulos de surto...",
        "features": "Carregando features...",
        "predicoes": "Carregando histórico de predições...",
        "modelos": "Carregando modelos treinados...",
        "catalogando": "Catalogando variáveis...",
    },

    # ============================================================
    # Mensagens de erro comuns
    # ============================================================
    "erro": {
        "dados_nao_encontrados": (
            "Arquivos de dados não encontrados. Rode primeiro o pipeline:\n\n"
            "```bash\n"
            "python -m arboviral.transform.build_master\n"
            "python -m arboviral.labels.build_labels\n"
            "python -m arboviral.features.build_features\n"
            "python -m arboviral.train\n"
            "```"
        ),
        "modelo_nao_encontrado": (
            "Modelo `{arquivo}` não encontrado. "
            "Rode `python -m arboviral.train` para gerá-lo."
        ),
        "explicacao_falhou": "Erro ao computar a explicação: {erro}",
        "sem_predicao": "Nenhuma predição encontrada para essa combinação.",
        "sem_dados_combinacao": "Sem dados para essa combinação.",
        "sem_modelos": "Nenhum modelo treinado encontrado. Rode `python -m arboviral.train`.",
        "sem_alertas_limiar": "Nenhuma predição acima do limiar selecionado.",
        "roadmap_ausente": "`ROADMAP.md` não encontrado em `{caminho}`.",
    },

    # ============================================================
    # screens/visao_geral.py — landing
    # ============================================================
    "home": {
        "hero": {
            "eyebrow": "ICMC · USP São Carlos · Iniciação Científica",
            "titulo": "Sistema operacional de alerta precoce para arboviroses no estado de São Paulo",
            "lead": (
                "A cada mês, modelos de aprendizado de máquina explicáveis estimam a "
                "probabilidade de surto de dengue, zika, chikungunya e febre amarela "
                "em cada um dos 645 municípios paulistas — e justificam cada alerta "
                "com os fatores que mais contribuíram."
            ),
            "meta_aluno": "Aluno",
            "meta_aluno_valor": "Lázaro Vinaud",
            "meta_orientador": "Orientador",
            "meta_orientador_valor": "Prof. André C. P. L. F. de Carvalho",
            "meta_periodo": "Período de dados",
        },
        "metricas": {
            "municipios_label": "Municípios monitorados",
            "municipios_unidade": " / SP",
            "periodo_label": "Período histórico",
            "periodo_unidade": " anos",
            "periodo_delta": "Janeiro/{ano_min} — Dezembro/{ano_max}",
            "variaveis_label": "Variáveis no master",
            "variaveis_delta": "Climáticas · epidemiológicas · ambientais · sanitárias",
            "doencas_label": "Doenças cobertas",
            "doencas_delta": "Dengue · Zika · Chikungunya · Febre amarela",
        },
        "modelos": {
            "secao": "Modelos disponíveis",
            "caption": (
                "Modelos serializados em `data/processed/models/` por (doença × definição × fold). "
                "As páginas usam o modelo do fold mais recente (alvo 2024) como predição mais atualizada."
            ),
            "col_doenca": "Doença",
            "col_definicao": "Definição de surto",
            "col_modelo": "Modelo",
            "col_folds": "Anos de teste treinados",
            "rodape_total": (
                "{n_modelos} modelos no total · 7 algoritmos (persistência, climatologia, "
                "logreg, EBM, RF, XGBoost, LightGBM) × 4 definições de surto × 3 folds temporais "
                "(2022, 2023, 2024)."
            ),
        },
        "navegacao": {
            "secao": "Como navegar pela plataforma",
            "alertas_titulo": "Alertas mensais",
            "alertas_desc": (
                "Tabela ranqueada de municípios em risco para o mês corrente, "
                "com filtros por doença, definição de surto e modelo."
            ),
            "municipio_titulo": "Detalhe do município",
            "municipio_desc": (
                "Predição mensal + histórico + justificativa SHAP "
                "(quais variáveis empurraram o risco para cima ou para baixo)."
            ),
            "comparativo_titulo": "Comparativo entre doenças",
            "comparativo_desc": (
                "Heatmap 4 doenças × 12 meses + série histórica para entender "
                "sazonalidade e cruzamento de transmissão."
            ),
        },
        "rodape_esq": "Plataforma de Alerta Precoce · ICMC USP · 2026",
        "rodape_dir": "Integração planejada · plataforma inteli.gente / MCTI",
    },

    # ============================================================
    # screens/alertas.py
    # ============================================================
    "alertas": {
        "titulo": "Alertas do mês",
        "descricao": (
            "Municípios em risco previsto · {recorte_mes} · "
            "{doenca} · {definicao} · {modelo}. "
            "Cada linha é uma predição mensal: probabilidade de surto para o mês indicado."
        ),
        "crumbs": "PLATAFORMA / ALERTAS / {doenca_upper} / {recorte_upper}",
        "fold_todos": "{ano} (todos os meses)",
        "definicao_help": (
            "Canal endêmico = método oficial Ministério da Saúde · "
            "Z-score = desvio do baseline histórico · "
            "100 ou 300 casos / 100 mil hab = limiar bruto de incidência"
        ),
        "ano_teste_help": "Cada ano é uma rodada de validação temporal (expanding window).",
        "mes_help": (
            "Mês para o qual o alerta é emitido (alvo da predição). "
            "Em produção, corresponderia ao próximo mês."
        ),
        "risco_min_label": "Probabilidade mínima exibida",
        "metricas": {
            "total_label": "Total de alertas",
            "total_delta": "≥ {limiar} de probabilidade",
            "criticos_delta": "Probabilidade ≥ 75%",
            "altos_delta": "50% a 75%",
            "moderados_delta": "25% a 50%",
        },
        "tabela": {
            "risco": "Risco",
            "municipio": "Município",
            "codigo_ibge": "Código IBGE",
            "mes_predito": "Mês predito",
            "probabilidade": "Probabilidade",
            "surto_real": "Surto real?",
            "surto_real_help": "O surto realmente ocorreu naquele mês? (avaliação retroativa)",
            "em_surto_agora": "Em surto agora?",
            "em_surto_agora_help": (
                "Sim = município já estava em surto no mês de referência "
                "(alerta = manutenção). Não = antecipação verdadeira (modelo prevê INÍCIO)."
            ),
        },
        "avaliacao": {
            "precisao_label": "Precisão neste recorte",
            "precisao_delta": "{n_corretos} de {n_total} alertas correspondiam a surto real",
            "antecipacao_label": "Antecipações verdadeiras",
            "antecipacao_delta": "alertas que previram INÍCIO de surto (não manutenção)",
        },
        "rodape": (
            "Use a página **Município** para ver a justificativa SHAP detalhada de cada alerta. "
            "A coluna *Em surto agora?* distingue antecipação (=0) de manutenção (=1) — "
            "antecipações verdadeiras são o achado central da pesquisa."
        ),
    },

    # ============================================================
    # screens/municipio.py
    # ============================================================
    "municipio": {
        "descricao": "{doenca} · {definicao} · {modelo} · ano de teste {fold}",
        "crumbs": "PLATAFORMA / MUNICÍPIO / {nome_upper} / {doenca_upper}",
        "shap_help": (
            "Mês predito (alvo do alerta) usado pela justificativa SHAP. "
            "'Pico do ano' = mês com a maior probabilidade prevista. "
            "Em produção corresponde ao mês corrente."
        ),
        "chips": {
            "ibge": "IBGE {cod}",
            "populacao": "Pop. {pop}",
            "estacao": "Estação {est}",
            "distancia": "{dist} km da estação",
        },
        "metricas": {
            "meses_alerta_label": "Meses com alerta",
            "meses_alerta_delta": "de {n} meses preditos (≥ 50%)",
            "surtos_reais_label": "Surtos reais no ano",
            "surtos_reais_delta": "confirmados pela definição escolhida",
            "definicao_label": "Definição em uso",
        },
        "graficos": {
            "secao_probabilidade": "Probabilidade prevista mês a mês",
            "trace_probabilidade": "Probabilidade prevista",
            "trace_surto": "Surto real",
            "hover_prob": "<b>%{{customdata}}</b><br>Prob: %{{y:.1%}}<extra></extra>",
            "hover_surto": "<b>%{{customdata}}</b><br>Surto confirmado<extra></extra>",
            "y_axis": "Probabilidade",
            "x_axis_mes_predito": "Mês predito",
            "secao_historico": "Histórico de casos notificados — {doenca}",
            "y_axis_casos": "Casos de {doenca_lower}",
        },
        "shap": {
            "titulo_alerta": "Por que esse alerta?",
            "titulo_baixo": "O que está mantendo o risco baixo?",
            "caption_pico": (
                "Análise para {municipio} em {mes_humano} (mês de maior probabilidade no ano). "
                "Probabilidade prevista: {prob}. "
                "🔴 vermelho = empurrou para CIMA · 🟢 verde = empurrou para BAIXO."
            ),
            "caption_mes": (
                "Análise para {municipio} em {mes_humano}. "
                "Probabilidade prevista: {prob}. "
                "🔴 vermelho = empurrou para CIMA · 🟢 verde = empurrou para BAIXO."
            ),
            "info_baseline": (
                "Modelos de baseline ({modelo}) não têm features — "
                "predizem só a partir do histórico recente do próprio município. "
                "Selecione um modelo de aprendizado de máquina (Random Forest, XGBoost, "
                "LightGBM, Regressão Logística ou EBM) para ver a justificativa."
            ),
            "qtd_label": "Quantos fatores exibir?",
            "qtd_help": (
                "Padrão é top 8 — suficiente para identificar os principais drivers. "
                "'Todos' lista as ~137 features na ordem de contribuição absoluta "
                "(útil para auditoria do modelo)."
            ),
            "qtd_todos": "Todos",
            "spinner": "Carregando modelo e computando explicação...",
            "metodo": "método: {metodo}",
            "valor_observado": "{tecnico} · valor observado: {valor}",
            "valor_observado_nan": "{tecnico} · valor observado: NaN",
        },
    },

    # ============================================================
    # screens/mapa.py
    # ============================================================
    "mapa": {
        "titulo": "Mapa de risco — São Paulo",
        "descricao": (
            "Probabilidade prevista de surto em {mes_humano} para "
            "{doenca} · {definicao} · {modelo}. "
            "Cada ponto = 1 município. Cor indica nível de risco."
        ),
        "crumbs": "PLATAFORMA / MAPA / {doenca_upper} / {mes_upper}",
        "mes_help": "Mês para o qual o mapa mostra a probabilidade prevista (alvo do alerta).",
        "metricas": {
            "mapeados_label": "Municípios mapeados",
            "criticos_delta": "≥ 75% prob.",
            "altos_delta": "50% a 75%",
            "risco_medio_label": "Risco médio",
            "risco_medio_delta": "média estadual",
        },
        "top5": {
            "secao": "Top 5 municípios em maior risco",
            "surto_real": "Surto real?",
        },
        "rodape": (
            "Mapa interativo: clique e arraste para mover, scroll para zoom, "
            "passe o mouse sobre um ponto para ver detalhes. "
            "Versão futura: choropleth com geojson dos limites municipais."
        ),
    },

    # ============================================================
    # screens/comparativo.py
    # ============================================================
    "comparativo": {
        "titulo": "{municipio} · 4 doenças lado a lado",
        "descricao": (
            "Heatmap de probabilidades + histórico de casos para todas as arboviroses "
            "em {fold} · {definicao} · {modelo}."
        ),
        "crumbs": "PLATAFORMA / COMPARATIVO / {nome_upper}",
        "chips": {
            "ano_teste": "Ano de teste {fold}",
        },
        "secao_heatmap": "Probabilidade prevista por mês × doença",
        "secao_historico": "Histórico de casos — 11 anos, todas as doenças",
        "x_axis_mes_predito": "Mês predito",
        "y_axis_doenca": "Doença",
        "y_axis_casos": "Casos notificados",
        "rodape": (
            "As 4 doenças compartilham o vetor *Aedes aegypti* (dengue, zika, chikungunya) "
            "ou são silvestres (febre amarela, transmitida por Haemagogus/Sabethes). "
            "Surtos podem coincidir ou se distribuir conforme condições ambientais."
        ),
    },

    # ============================================================
    # screens/variaveis.py
    # ============================================================
    "variaveis": {
        "titulo": "Catálogo de variáveis",
        "descricao": (
            "Todas as **{n_features} features** que entram nos modelos, com nome técnico, "
            "descrição em português, fonte de origem, tipo e estatísticas. "
            "Útil para auditoria do que o modelo realmente vê e para checar lacunas (NaN%)."
        ),
        "crumbs": "PLATAFORMA / VARIÁVEIS",
        "tipos": {
            "booleana": "booleana",
            "numerica": "numérica",
            "categorica": "categórica",
        },
        "categorias": {
            "epi_dengue": "Epidemiológicas — Dengue",
            "epi_zika": "Epidemiológicas — Zika",
            "epi_chik": "Epidemiológicas — Chikungunya",
            "epi_fa": "Epidemiológicas — Febre amarela",
            "climaticas": "Climáticas",
            "sazonalidade": "Sazonalidade",
            "geo": "Geolocalização",
            "demo_econ": "Demografia / Economia",
            "densidade": "Densidade territorial",
            "cobertura": "Cobertura terrestre",
            "saude_publica": "Saúde pública",
            "esf_aps": "Cobertura ESF / APS",
            "saneamento": "Saneamento",
            "vacinacao": "Vacinação",
            "munic": "Vigilância municipal (MUNIC)",
            "desastres": "Desastres / risco ambiental",
            "habitacao": "Habitação / favelas",
            "capag": "CAPAG",
            "predicao_meta": "Metadata de predição",
            "outras": "Outras",
        },
        "fontes": {
            "sinan": "SINAN / DATASUS",
            "svs": "SVS / Ministério da Saúde",
            "nasa_power": "NASA POWER (MERRA-2)",
            "calendario": "engenharia de features (calendário)",
            "ibge_inmet": "lookup IBGE / INMET",
            "ibge_atlas": "IBGE SIDRA / Atlas PNUD",
            "ibge_areas": "IBGE — áreas territoriais",
            "mapbiomas": "MapBiomas Coleção 10.1",
            "datasus_cnes": "DATASUS — CNES + SIM",
            "egestor": "e-Gestor / Ministério da Saúde",
            "sinisa": "SINISA",
            "pni": "PNI / DATASUS",
            "ibge_munic_2018": "IBGE MUNIC 2018",
            "ibge_munic_2020": "IBGE MUNIC 2020",
            "ibge_censos": "IBGE — Censos 2010 / 2022",
            "tesouro": "Tesouro Nacional",
            "split_features": "engenharia de features (split)",
            "indef": "—",
        },
        "metricas": {
            "total_label": "Features totais",
            "total_delta": "em {n_categorias} categorias temáticas",
            "completas_label": "Quase completas",
            "completas_delta": "< 1% de NaN",
            "lacunas_label": "Com lacunas relevantes",
            "lacunas_delta": "≥ 10% de NaN — atenção",
            "nan_medio_label": "NaN médio",
            "nan_medio_delta": "média sobre todas as features",
        },
        "filtros": {
            "secao": "Filtros",
            "busca_label": "Buscar (nome técnico ou descrição)",
            "busca_placeholder": "ex.: temp, dengue_lag, esf, vigilância…",
            "busca_help": "Busca substring case-insensitive em ambos os nomes.",
            "categorias_label": "Categorias",
            "categorias_help": "Vazio = todas. Selecione uma ou mais para filtrar.",
            "tipo_label": "Tipo",
            "tipo_help": "Vazio = todos.",
        },
        "tabela": {
            "info_filtro": (
                "Mostrando **{n_filtrado} de {n_total}** features "
                "(em {n_categorias} categorias)."
            ),
            "secao_distribuicao": "Distribuição por categoria",
            "rodape": (
                "As colunas `cod_ibge`, `ano` e `mes` não aparecem aqui — são chaves de "
                "identificação, não features de entrada do modelo. As colunas `target_year` "
                "e `target_month` são derivadas no `train.py` para o split temporal e "
                "também entram como features (sazonalidade do mês predito)."
            ),
        },
    },

    # ============================================================
    # screens/sobre.py
    # ============================================================
    "sobre": {
        "titulo": "Sobre o projeto",
        "descricao": (
            "Plano de evolução da pesquisa — desde o fechamento da IC até material "
            "publicável em artigo internacional. Conteúdo reflete o ROADMAP.md do repositório."
        ),
        "crumbs": "PLATAFORMA / SOBRE",
        "secao_resumo": "Em resumo",
        "card_curto_titulo": "Curto prazo",
        "card_curto_desc": (
            "5 itens para fechar a IC bem feita: análises post-hoc, SHAP "
            "estratificado, robustez a NaN, sensitivity analysis (--no-cross), tuning."
        ),
        "card_medio_titulo": "Médio prazo",
        "card_medio_desc": (
            "Top 10 fontes de dados priorizadas por impacto. 5/10 já integradas "
            "(MapBiomas, ESF, latência SINAN, densidade, vacinação FA)."
        ),
        "card_longo_titulo": "Longo prazo",
        "card_longo_desc": (
            "Caminho para publicação: workshop nacional → conferência IEEE → "
            "journal internacional. Validação externa em outros estados é o passo crítico."
        ),
        "tab_curto": "Curto prazo",
        "tab_medio": "Médio prazo (top 10 fontes)",
        "tab_longo": "Longo prazo (artigo)",
        "tab_full": "Documento completo",
        "tab_full_caption": (
            "Mesmo conteúdo das tabs anteriores, em formato linear "
            "(útil para imprimir ou copiar)."
        ),
        "rodape": (
            "Conteúdo vive em <code>ROADMAP.md</code> no repositório · "
            "atualizações refletem aqui automaticamente."
        ),
    },

    # ============================================================
    # Categorização de risco (lib/predicao.py)
    # ============================================================
    "categorizar_risco": {
        "critico": "Crítico",
        "alto": "Alto",
        "moderado": "Moderado",
        "baixo": "Baixo",
    },

    # ============================================================
    # Humanização de features (lib/labels.py / humanizar_feature)
    # ============================================================
    "feature": {
        # Sazonalidade
        "mes_sin": "Sazonalidade (componente sen)",
        "mes_cos": "Sazonalidade (componente cos)",
        # Geolocalização
        "lat": "Latitude",
        "lon": "Longitude",
        "dist_estacao_km": "Distância à estação INMET (km)",
        # Demografia / economia
        "populacao_estimada": "População estimada",
        "pib_per_capita": "PIB per capita",
        "gini": "Índice de Gini",
        "idhm": "IDH municipal",
        # Densidade IBGE
        "area_km2": "Área (km²)",
        "densidade_2023": "Densidade populacional (hab/km²)",
        # MapBiomas
        "pct_floresta": "Cobertura: floresta natural (%)",
        "pct_agricultura": "Cobertura: agropecuária (%)",
        "pct_nao_vegetado": "Cobertura: urbanizado / não vegetado (%)",
        "pct_agua": "Cobertura: água (%)",
        "pct_natural_nao_florestal": "Cobertura: natural não florestal (%)",
        # Vacinação
        "cob_vac_fa_pct": "Cobertura vacinal contra febre amarela (%)",
        # ESF / APS
        "esf_qt_capacidade": "Capacidade ESF (atendimento)",
        "esf_pop_referencia": "População de referência ESF",
        "esf_metodologia_AB": "Metodologia ESF: Atenção Básica (até 2020)",
        "esf_metodologia_APS": "Metodologia ESF: APS (a partir de 2021)",
        "esf_cobertura_pct_lag1": "Cobertura ESF (mês anterior, %)",
        "esf_qt_equipes_lag1": "Equipes ESF (mês anterior)",
        # SINISA / saneamento
        "iag0001_atend_agua_pct": "Atendimento de água (%)",
        "ies0001_atend_esgoto_pct": "Atendimento de esgoto (%)",
        "ies2004_esgoto_tratado_pct": "Esgoto tratado (%)",
        # Saúde pública
        "leitos_publicos": "Leitos públicos",
        "mortalidade_materna": "Mortalidade materna",
        # MUNIC — vigilância
        "msau28_pacs": "Programa de Agentes Comunitários (PACS)",
        "msau541_vig_sanitaria": "Vigilância sanitária estruturada",
        "msau542_vig_epidemiologica": "Vigilância epidemiológica estruturada",
        "msau543_controle_endemias": "Controle de endemias estruturado",
        # MUNIC — desastres
        "mgrd01_seca": "Município atingido por seca",
        "mgrd06_alagamento": "Município atingido por alagamento",
        "mgrd07_erosao": "Município atingido por erosão",
        "mgrd08_enchente_gradual": "Município atingido por enchente gradual",
        "mgrd11_enxurrada": "Município atingido por enxurrada",
        "mgrd14_deslizamento": "Município atingido por deslizamento",
        "mgrd201_mapeamento_risco": "Possui mapeamento de áreas de risco",
        "mmam2612_moradia_risco": "Possui moradia em situação de risco",
        # Habitação
        "num_aglom_subnorm_2010": "Aglomerados subnormais (Censo 2010)",
        "pop_aglom_subnorm_2010": "População em aglomerados subnormais (2010)",
        "num_favelas_2022": "Favelas (Censo 2022)",
        "pop_favelas_2022": "População em favelas (2022)",
        # Clima atual
        "precip_media_dia": "Precipitação média (mês atual)",
        "temp_media": "Temperatura média (mês atual)",
        "umid_media": "Umidade média (mês atual)",
        "temp_max": "Temperatura máxima (mês atual)",
        "temp_min": "Temperatura mínima (mês atual)",
        "pressao_media_kpa": "Pressão atmosférica média (kPa)",
        "vento_media": "Vento médio",
        # CAPAG
        "capag_A": "CAPAG: A",
        "capag_B": "CAPAG: B",
        "capag_C": "CAPAG: C",
        "capag_D": "CAPAG: D",
        "capag_n.d.": "CAPAG: não disponível",
        # Split
        "target_year": "Ano-alvo da predição",
        "target_month": "Mês-alvo da predição",
    },

    # Templates parametrizados para padrões de feature (lags, rolling, etc.)
    # `{d_low}` = nome humano da doença (já traduzido), `{k}` = lag/janela
    "feature_pattern": {
        "casos_lag_1": "Casos de {d_low} há {k} mês",
        "casos_lag_n": "Casos de {d_low} há {k} meses",
        "incid_lag_1": "Incidência de {d_low} há {k} mês",
        "incid_lag_n": "Incidência de {d_low} há {k} meses",
        "casos_roll": "Casos de {d_low} (média móvel {w} meses)",
        "incid_roll": "Incidência de {d_low} (média móvel {w} meses)",
        "casos_trend": "Tendência de casos de {d_low} ({w} meses)",
        "surto_canal_1": "Surto de {d_low} há {k} mês (canal endêmico)",
        "surto_canal_n": "Surto de {d_low} há {k} meses (canal endêmico)",
        "latencia_mediana": "Latência mediana de notificação ({d_low}, mês anterior)",
        "latencia_p90": "Latência p90 de notificação ({d_low}, mês anterior)",
        "casos_com_latencia": "Casos com latência válida ({d_low}, mês anterior)",
        "precip_lag_1": "Precipitação média há {k} mês",
        "precip_lag_n": "Precipitação média há {k} meses",
        "precip_roll": "Precipitação média (média móvel {w} meses)",
        "temp_lag_1": "Temperatura média há {k} mês",
        "temp_lag_n": "Temperatura média há {k} meses",
        "temp_roll": "Temperatura média (média móvel {w} meses)",
        "umid_lag_1": "Umidade média há {k} mês",
        "umid_lag_n": "Umidade média há {k} meses",
        "umid_roll": "Umidade média (média móvel {w} meses)",
    },
}
