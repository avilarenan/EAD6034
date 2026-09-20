# EAD6034 — entrega cumulativa de 21/09/2026

Renan de Luca Avila · Prof. Leandro Maciel · Seminário final em 28/09/2026 (até 15 minutos).

[Repositório](https://github.com/avilarenan/EAD6034) · [Código desta execução](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/forecast_pipeline.py) · [Protocolo pré-especificado](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/docs/PROTOCOL_21_09.md).

Este documento incorpora e revisa as etapas de 31/08 (descrição e FAC/FACP), 14/09 (estacionariedade e Box–Jenkins) e 21/09 (avaliação preditiva e modelos alternativos). Os artefatos antigos foram preservados como histórico, não corrigidos silenciosamente. A inferência atual refere-se ao desenho anual de tempo de negociação aprovado pelo autor.

## Síntese calculada dos resultados

- Seleção BIC da média em 2024: 1 min: ARMA(2,2); 5 min: ARMA(0,0); 15 min: ARMA(0,0); 30 min: ARMA(0,0); 60 min: ARMA(0,0); 1 dia: ARMA(0,0).
- Ljung–Box da média, no horizonte diagnóstico principal, rejeita ausência de autocorrelação em: 1 min. A referência é assintótica e pode ser afetada por heterocedasticidade; não rejeitar não prova ruído independente.
- Alvo comum de 60 minutos, série-base 1 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Alvo comum de 60 minutos, série-base 5 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Alvo comum de 60 minutos, série-base 15 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Alvo comum de 60 minutos, série-base 30 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Alvo comum de 60 minutos, série-base 60 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Seleção BIC condicional da variância em 2024: 1 min: GARCH(1,1); 5 min: GARCH(1,1); 15 min: GARCH(1,1); 30 min: GARCH(1,1); 60 min: ARCH(1); 1 dia: Constant variance. A previsão pontual permanece a mesma.
- As previsões ARMA(0,0) no alvo comum coincidem nas escalas 5 min, 15 min, 30 min, 60 min: somar as médias das barras completas produz a mesma média horária. Isso decorre da agregação dos mesmos dados, não de confirmações independentes de previsibilidade.

## 1. Pergunta, escopo e hipótese

[Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/forecast_pipeline.py).

Como a previsibilidade dos retornos do WIN varia entre 1, 5, 15, 30 e 60 minutos e o diário?
A hipótese de maior previsibilidade horária é confrontada com os erros fora da amostra, não usada para escolher vencedores.
Maior suavidade visual, menor ruído e maior capacidade preditiva são propriedades diferentes.
A comparação usa ganhos frente ao benchmark e, quando se comparam escalas, alvos físicos idênticos de 60 minutos.

Este é um estudo multiescala de um futuro de índice, com 5 minutos como referência da proposta.
Não se alegam resultados para outras classes de ativos, segundos, spreads, midquotes ou custos de execução.
A adaptação de Matías e Reboredo (2012) aproveita a questão de previsão intradiária; não reproduz os modelos
não lineares do artigo, pois foram utilizados apenas os métodos das aulas fornecidas.

## 2. Dados, revisão amostral e significado de overnight

[Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/trading_time_data.py).

Retornos são expressos em porcentagem: `100 × log(P_final/P_inicial)`. Janela fixa local de São Paulo:
09:05–18:05, com 540 minutos. O intradiário usa a fronteira inicial no fechamento do candle iniciado às 09:04.
O diário usa abertura às 09:05 e fechamento da janela, portanto não deve ser tratado como soma exatamente
idêntica dos retornos intradiários ancorados no candle anterior. Os alvos comuns intradiários, sim, são reconciliados.

A etapa anterior testava cada sessão isoladamente: **nove barras de uma hora, não nove minutos**.
Agora a sequência horária de treino possui **2,214 observações em 246 pregões**, antes das perdas por defasagens.
O índice continua entre dias, sem acrescentar um retorno que compare fechamento de ontem e abertura de hoje.
A última barra de ontem pode explicar a primeira barra de hoje, embora cada retorno seja calculado inteiramente
dentro do próprio pregão e contrato. Um lag significa a observação anterior, não uma distância constante de relógio.

Essa mudança reduz o problema dos testes com nove observações, mas não prova por si só estacionariedade.
Informação acumulada durante a noite pode afetar a primeira barra; a hipótese é não modelar separadamente a interrupção.
Trocas de contrato e dias ausentes permanecem identificados. A contagem de dias úteis não observados não é um
calendário B3 validado: pode incluir feriados. Não se preenchem lacunas com zeros ou interpolação e não se winsorizam retornos.

| Escala | Amostra | N | Pregões | Início | Fim | Lags entre sessões | Trocas de contrato |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 min | test | 119.340 | 221 | 2025-01-02 | 2025-11-28 | 221 | 5 |
| 1 min | train | 132.840 | 246 | 2024-01-02 | 2024-12-30 | 245 | 6 |
| 5 min | test | 23.868 | 221 | 2025-01-02 | 2025-11-28 | 221 | 5 |
| 5 min | train | 26.568 | 246 | 2024-01-02 | 2024-12-30 | 245 | 6 |
| 15 min | test | 7.956 | 221 | 2025-01-02 | 2025-11-28 | 221 | 5 |
| 15 min | train | 8.856 | 246 | 2024-01-02 | 2024-12-30 | 245 | 6 |
| 30 min | test | 3.978 | 221 | 2025-01-02 | 2025-11-28 | 221 | 5 |
| 30 min | train | 4.428 | 246 | 2024-01-02 | 2024-12-30 | 245 | 6 |
| 60 min | test | 1.989 | 221 | 2025-01-02 | 2025-11-28 | 221 | 5 |
| 60 min | train | 2.214 | 246 | 2024-01-02 | 2024-12-30 | 245 | 6 |
| 1 dia | test | 221 | 221 | 2025-01-02 | 2025-11-28 | 221 | 5 |
| 1 dia | train | 246 | 246 | 2024-01-02 | 2024-12-30 | 245 | 6 |

2024 é treino; 2025 é teste. A primeira observação de teste pode usar o estado final de 2024, por isso a contagem
de lags entre sessões no teste pode incluir a transição treino–teste. O filtro de pregões completos é uma seleção
retrospectiva de qualidade: as métricas são condicionais à amostra, não uma garantia de disponibilidade operacional.
Auditoria completa: [sequence_audit.csv](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/sequence_audit.csv); cobertura: [coverage.csv](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/coverage.csv).

## 3. Entrega de 31/08 revisada: descrição, FAC e FACP

[Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/annual_models.py).

As estatísticas e correlações foram recalculadas em 2024 sob a mesma sequência anual utilizada nos testes e modelos.
A FAC usa pares na sequência de observações, inclusive os que atravessam sessões. A FACP usa Yule–Walker com
denominador de máxima verossimilhança (`ywmle`), sem regressões agrupadas por pregão. As bandas pontuais
`±1,96/√N` são referências aproximadas de ruído branco, não bandas simultâneas robustas à heterocedasticidade.

| Escala | N | Média (%) | Desvio (%) | Assimetria | Excesso de curtose | Fração zero |
| --- | --- | --- | --- | --- | --- | --- |
| 1 min | 132.840 | -0.000122 | 0.032106 | 0.228852 | 20.184339 | 0.067329 |
| 5 min | 26.568 | -0.000611 | 0.071369 | 0.678404 | 21.754198 | 0.029321 |
| 15 min | 8.856 | -0.001832 | 0.121649 | 0.488107 | 8.432952 | 0.015921 |
| 30 min | 4.428 | -0.003664 | 0.171137 | 0.18418 | 5.065635 | 0.012421 |
| 60 min | 2.214 | -0.007328 | 0.244616 | 0.015826 | 5.899066 | 0.008582 |
| 1 dia | 246 | -0.065483 | 0.78495 | -0.527006 | 1.194597 | 0 |

FAC/FACP lag 1 (todas as demais defasagens permanecem nas tabelas e figuras):

| Escala | Lag | FAC | FACP | Pares | Banda pontual |
| --- | --- | --- | --- | --- | --- |
| 1 min | 1 | -0.008118 | -0.008118 | 132839 | 0.005378 |
| 5 min | 1 | 0.002417 | 0.002417 | 26567 | 0.012025 |
| 15 min | 1 | 0.007447 | 0.007447 | 8855 | 0.020828 |
| 30 min | 1 | 0.006421 | 0.006421 | 4427 | 0.029455 |
| 60 min | 1 | -0.040841 | -0.040841 | 2213 | 0.041655 |
| 1 dia | 1 | -0.044539 | -0.044539 | 245 | 0.124965 |

Pares que atravessam sessões são também descritos separadamente; essas correlações não são novos testes nem
constituem evidência causal de overnight:

| Escala | Pares | N pares | Correlação descritiva |
| --- | --- | --- | --- |
| 1 min | across_sessions | 245 | 0.00241 |
| 1 min | all_pairs | 132.839 | -0.008118 |
| 1 min | within_session | 132.594 | -0.008154 |
| 5 min | across_sessions | 245 | -0.009033 |
| 5 min | all_pairs | 26.567 | 0.002417 |
| 5 min | within_session | 26.322 | 0.00244 |
| 15 min | across_sessions | 245 | 0.029029 |
| 15 min | all_pairs | 8.855 | 0.007448 |
| 15 min | within_session | 8.610 | 0.007062 |
| 30 min | across_sessions | 245 | -0.05098 |
| 30 min | all_pairs | 4.427 | 0.006421 |
| 30 min | within_session | 4.182 | 0.009533 |
| 60 min | across_sessions | 245 | -0.003858 |
| 60 min | all_pairs | 2.213 | -0.040844 |
| 60 min | within_session | 1.968 | -0.045344 |
| 1 dia | across_sessions | 245 | -0.04457 |
| 1 dia | all_pairs | 245 | -0.04457 |
| 1 dia | within_session | 0 | — |

Tabelas completas: [return_acf_pacf.csv](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/return_acf_pacf.csv), [time_band_description.csv](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/time_band_description.csv), [monthly_description.csv](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/monthly_description.csv).
Uma dispersão maior na escala diária não demonstra maior ou menor previsibilidade; o horizonte e a unidade do alvo mudaram.

## 4. Entrega de 14/09 revisada: estacionariedade

[Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/annual_models.py).

ADF e PP: H0 = raiz unitária. KPSS: H0 = estacionariedade em nível (`c`) ou em torno de tendência (`ct`).
`c` é a especificação principal; `ct` é sensibilidade pré-definida, não escolhida retrospectivamente para obter concordância.
ADF seleciona lags por BIC entre 0 e 12, sujeito ao limite amostral; PP usa bandwidth automático Schwert com Bartlett;
KPSS usa seleção automática dependente dos dados, também com Bartlett. Decisões usam o valor crítico de 5%.

| Escala | Especificação | Teste | Determinístico | N bruto | N efetivo | Lags/bandwidth | Estatística | Crítico 5% | p-valor | Rejeita H0 a 5% |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 min | main | ADF | c | 132.840 | 132.839 | 0 | -367.446275 | -2.861562 | < precisão numérica | sim |
| 1 min | main | KPSS | c | 132.840 | 132.840 | 15 | 0.189171 | 0.4614 | 0.2901 | não |
| 1 min | main | PP | c | 132.840 | 132.839 | 73 | -367.505353 | -2.861562 | < precisão numérica | sim |
| 1 min | trend_sensitivity | ADF | ct | 132.840 | 132.839 | 0 | -367.445531 | -3.410523 | < precisão numérica | sim |
| 1 min | trend_sensitivity | KPSS | ct | 132.840 | 132.840 | 15 | 0.175753 | 0.1479 | 0.0261 | sim |
| 1 min | trend_sensitivity | PP | ct | 132.840 | 132.839 | 73 | -367.505036 | -3.410523 | < precisão numérica | sim |
| 5 min | main | ADF | c | 26.568 | 26.567 | 0 | -162.601231 | -2.861649 | < precisão numérica | sim |
| 5 min | main | KPSS | c | 26.568 | 26.568 | 7 | 0.190902 | 0.4614 | 0.2864 | não |
| 5 min | main | PP | c | 26.568 | 26.567 | 49 | -162.632378 | -2.861649 | < precisão numérica | sim |
| 5 min | trend_sensitivity | ADF | ct | 26.568 | 26.567 | 0 | -162.599621 | -3.410655 | < precisão numérica | sim |
| 5 min | trend_sensitivity | KPSS | ct | 26.568 | 26.568 | 6 | 0.177413 | 0.1479 | 0.0250 | sim |
| 5 min | trend_sensitivity | PP | ct | 26.568 | 26.567 | 49 | -162.631399 | -3.410655 | < precisão numérica | sim |
| 15 min | main | ADF | c | 8.856 | 8.855 | 0 | -93.389736 | -2.861866 | < precisão numérica | sim |
| 15 min | main | KPSS | c | 8.856 | 8.856 | 11 | 0.197543 | 0.4614 | 0.2729 | não |
| 15 min | main | PP | c | 8.856 | 8.855 | 37 | -93.387392 | -2.861866 | < precisão numérica | sim |
| 15 min | trend_sensitivity | ADF | ct | 8.856 | 8.855 | 0 | -93.386991 | -3.410986 | < precisão numérica | sim |
| 15 min | trend_sensitivity | KPSS | ct | 8.856 | 8.856 | 11 | 0.183591 | 0.1479 | 0.0218 | sim |
| 15 min | trend_sensitivity | PP | ct | 8.856 | 8.855 | 37 | -93.384519 | -3.410986 | < precisão numérica | sim |
| 30 min | main | ADF | c | 4.428 | 4.427 | 0 | -66.095734 | -2.862193 | < precisão numérica | sim |
| 30 min | main | KPSS | c | 4.428 | 4.428 | 6 | 0.196811 | 0.4614 | 0.2743 | não |
| 30 min | main | PP | c | 4.428 | 4.427 | 31 | -66.104106 | -2.862193 | < precisão numérica | sim |
| 30 min | trend_sensitivity | ADF | ct | 4.428 | 4.427 | 0 | -66.091446 | -3.411482 | < precisão numérica | sim |
| 30 min | trend_sensitivity | KPSS | ct | 4.428 | 4.428 | 6 | 0.182942 | 0.1479 | 0.0221 | sim |
| 30 min | trend_sensitivity | PP | ct | 4.428 | 4.427 | 31 | -66.099051 | -3.411482 | < precisão numérica | sim |
| 60 min | main | ADF | c | 2.214 | 2.213 | 0 | -48.983115 | -2.862847 | < precisão numérica | sim |
| 60 min | main | KPSS | c | 2.214 | 2.214 | 2 | 0.199137 | 0.4614 | 0.2697 | não |
| 60 min | main | PP | c | 2.214 | 2.213 | 27 | -48.945115 | -2.862847 | < precisão numérica | sim |
| 60 min | trend_sensitivity | ADF | ct | 2.214 | 2.213 | 0 | -48.97691 | -3.412476 | < precisão numérica | sim |
| 60 min | trend_sensitivity | KPSS | ct | 2.214 | 2.214 | 2 | 0.185068 | 0.1479 | 0.0210 | sim |
| 60 min | trend_sensitivity | PP | ct | 2.214 | 2.213 | 27 | -48.938693 | -3.412476 | < precisão numérica | sim |
| 1 dia | main | ADF | c | 246 | 245 | 0 | -16.310103 | -2.87341 | 3.202e-29 | sim |
| 1 dia | main | KPSS | c | 246 | 246 | 0 | 0.170297 | 0.4614 | 0.3339 | não |
| 1 dia | main | PP | c | 246 | 245 | 16 | -16.426299 | -2.87341 | 2.503e-29 | sim |
| 1 dia | trend_sensitivity | ADF | ct | 246 | 245 | 0 | -16.294977 | -3.428564 | < precisão numérica | sim |
| 1 dia | trend_sensitivity | KPSS | ct | 246 | 246 | 0 | 0.158082 | 0.1479 | 0.0393 | sim |
| 1 dia | trend_sensitivity | PP | ct | 246 | 245 | 16 | -16.409811 | -3.428564 | < precisão numérica | sim |

Leitura conjunta, sem teste de painel ou combinação de p-valores:

| Escala | Especificação | Leitura |
| --- | --- | --- |
| 1 min | main | Evidência concordante com I(0), sem comprovar estabilidade de toda a distribuição |
| 1 min | trend_sensitivity | Evidência conflitante ou inconclusiva; investigar sensibilidade, sem impor conclusão |
| 5 min | main | Evidência concordante com I(0), sem comprovar estabilidade de toda a distribuição |
| 5 min | trend_sensitivity | Evidência conflitante ou inconclusiva; investigar sensibilidade, sem impor conclusão |
| 15 min | main | Evidência concordante com I(0), sem comprovar estabilidade de toda a distribuição |
| 15 min | trend_sensitivity | Evidência conflitante ou inconclusiva; investigar sensibilidade, sem impor conclusão |
| 30 min | main | Evidência concordante com I(0), sem comprovar estabilidade de toda a distribuição |
| 30 min | trend_sensitivity | Evidência conflitante ou inconclusiva; investigar sensibilidade, sem impor conclusão |
| 60 min | main | Evidência concordante com I(0), sem comprovar estabilidade de toda a distribuição |
| 60 min | trend_sensitivity | Evidência conflitante ou inconclusiva; investigar sensibilidade, sem impor conclusão |
| 1 dia | main | Evidência concordante com I(0), sem comprovar estabilidade de toda a distribuição |
| 1 dia | trend_sensitivity | Evidência conflitante ou inconclusiva; investigar sensibilidade, sem impor conclusão |

Não rejeitar H0 não demonstra sua verdade. Amostras grandes podem detectar desvios pequenos e não eliminam
quebras, sazonalidade intradiária ou fragilidade de especificação. Resultados conflitantes entre `c` e `ct` são preservados.
P-valores que o software retorna como zero por limite numérico são mostrados como **< precisão numérica**, nunca como probabilidade exatamente nula.
Valores críticos de 1%, 5% e 10%, regras de lag e avisos: [stationarity.csv](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/stationarity.csv).

## 5. Box–Jenkins: identificação, estimação, seleção e diagnóstico

[Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/annual_models.py).

Grade ARMA(p,q), p,q entre 0 e 5, com constante, usando somente 2024.
A constante da parametrização de `statsmodels.ARIMA` é a média incondicional μ; não é o intercepto da equação AR.
ARMA(0,0) usa a solução gaussiana fechada: média amostral e variância dos resíduos com denominador N.
Para as demais ordens, estimamos numericamente a verossimilhança gaussiana exata com inicialização estacionária
e GLS iterativo para a média. Se a primeira tentativa não converge, a rotina registra uma nova tentativa de
máxima verossimilhança em espaço de estados.
Escalonamento numérico é desfeito nos parâmetros, variância, log-verossimilhança e critérios; raízes e convergência são auditadas.

`BIC = −2 log L + k log N`, com `k = p + q + 2` (média e variância incluídas). Menor BIC vence entre candidatos elegíveis
da mesma escala e amostra. Não se comparam níveis de BIC entre frequências distintas. AIC é complementar.
AR puro positivo e MA puro positivo são selecionados dentro de suas próprias famílias; não substituem o vencedor geral.

| Escala | Candidatos | Elegíveis | Excluídos/falhos |
| --- | --- | --- | --- |
| 1 min | 36 | 36 | 0 |
| 5 min | 36 | 36 | 0 |
| 15 min | 36 | 36 | 0 |
| 30 min | 36 | 36 | 0 |
| 60 min | 36 | 36 | 0 |
| 1 dia | 36 | 36 | 0 |

| Escala | Papel | p | q | k | μ (%) | σ (%) | log L | AIC | BIC | ΔBIC geral |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 min | ARMA_BIC | 2 | 2 | 6 | -0.000122 | 0.0321 | 268330.923551 | -536649.847103 | -536591.065699 | 0 |
| 1 min | AR_BIC | 1 | 0 | 3 | -0.000122 | 0.032105 | 268311.087317 | -536616.174634 | -536586.783932 | 4.281766 |
| 1 min | MA_BIC | 0 | 1 | 3 | -0.000122 | 0.032105 | 268311.110507 | -536616.221014 | -536586.830312 | 4.235386 |
| 5 min | ARMA_BIC | 0 | 0 | 2 | -0.000611 | 0.071368 | 32438.815976 | -64873.631952 | -64857.257027 | 0 |
| 5 min | AR_BIC | 1 | 0 | 3 | -0.000611 | 0.071367 | 32438.893575 | -64871.78715 | -64847.224762 | 10.032265 |
| 5 min | MA_BIC | 0 | 1 | 3 | -0.000611 | 0.071367 | 32438.895488 | -64871.790977 | -64847.228589 | 10.028438 |
| 15 min | ARMA_BIC | 0 | 0 | 2 | -0.001832 | 0.121642 | 6090.573179 | -12177.146359 | -12162.968658 | 0 |
| 15 min | AR_BIC | 1 | 0 | 3 | -0.001832 | 0.121639 | 6090.818793 | -12175.637587 | -12154.371035 | 8.597623 |
| 15 min | MA_BIC | 0 | 1 | 3 | -0.001832 | 0.121639 | 6090.816002 | -12175.632004 | -12154.365452 | 8.603206 |
| 30 min | ARMA_BIC | 0 | 0 | 2 | -0.003664 | 0.171118 | 1534.138114 | -3064.276228 | -3051.484821 | 0 |
| 30 min | AR_BIC | 1 | 0 | 3 | -0.003664 | 0.171115 | 1534.229386 | -3062.458772 | -3043.271662 | 8.213159 |
| 30 min | MA_BIC | 0 | 1 | 3 | -0.003664 | 0.171114 | 1534.233531 | -3062.467062 | -3043.279953 | 8.204869 |
| 60 min | ARMA_BIC | 0 | 0 | 2 | -0.007328 | 0.244561 | -23.572861 | 51.145722 | 62.550834 | 0 |
| 60 min | AR_BIC | 1 | 0 | 3 | -0.007328 | 0.244457 | -21.725782 | 49.451563 | 66.559232 | 4.008397 |
| 60 min | MA_BIC | 0 | 1 | 3 | -0.007328 | 0.244369 | -21.833769 | 49.667538 | 66.775207 | 4.224372 |
| 1 dia | ARMA_BIC | 0 | 0 | 2 | -0.065483 | 0.783353 | -288.992717 | 581.985434 | 588.996097 | 0 |
| 1 dia | AR_BIC | 1 | 0 | 3 | -0.065398 | 0.782575 | -288.749129 | 583.498258 | 594.014253 | 5.018156 |
| 1 dia | MA_BIC | 0 | 1 | 3 | -0.065394 | 0.782583 | -288.751585 | 583.503169 | 594.019164 | 5.023067 |

Uma seleção ARMA(0,0) significa que, na grade examinada, o ganho de ajuste não compensou a penalidade por parâmetros;
não é uma prova de independência, inexistência de padrões ou impossibilidade de previsão por qualquer método.
Toda a grade, inclusive falhas, está em [arma_grid.csv](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/arma_grid.csv); parâmetros e raízes em [selected_models.csv](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/selected_models.csv).

Diagnósticos nos horizontes principais pré-definidos (60 lags no minuto; 24 nas demais escalas intradiárias; 20 no diário):

| Escala | Modelo | h | gl da aula | Q resíduos | p Q | p Q quadrados | Lags ARCH | p ARCH-LM | p normalidade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 min | ARMA_BIC | 60 | 55 | 100.658649 | 0.0002 | < precisão numérica | 12 | < precisão numérica | < precisão numérica |
| 1 min | AR_BIC | 60 | 58 | 133.630529 | 6.658e-08 | < precisão numérica | 12 | < precisão numérica | < precisão numérica |
| 1 min | MA_BIC | 60 | 58 | 133.589413 | 6.740e-08 | < precisão numérica | 12 | < precisão numérica | < precisão numérica |
| 5 min | ARMA_BIC | 24 | 23 | 33.181021 | 0.0780 | 3.161e-202 | 12 | 2.945e-164 | < precisão numérica |
| 5 min | AR_BIC | 24 | 22 | 33.094993 | 0.0606 | 8.353e-201 | 12 | 8.518e-163 | < precisão numérica |
| 5 min | MA_BIC | 24 | 22 | 33.092896 | 0.0606 | 9.067e-201 | 12 | 9.255e-163 | < precisão numérica |
| 15 min | ARMA_BIC | 24 | 23 | 23.895298 | 0.4096 | 7.933e-55 | 12 | 1.504e-48 | < precisão numérica |
| 15 min | AR_BIC | 24 | 22 | 23.392286 | 0.3799 | 8.601e-54 | 12 | 1.371e-47 | < precisão numérica |
| 15 min | MA_BIC | 24 | 22 | 23.398854 | 0.3795 | 8.414e-54 | 12 | 1.343e-47 | < precisão numérica |
| 30 min | ARMA_BIC | 24 | 23 | 22.363419 | 0.4984 | 2.533e-18 | 12 | 6.947e-12 | < precisão numérica |
| 30 min | AR_BIC | 24 | 22 | 22.236255 | 0.4459 | 3.597e-18 | 12 | 9.066e-12 | < precisão numérica |
| 30 min | MA_BIC | 24 | 22 | 22.229153 | 0.4463 | 3.667e-18 | 12 | 9.196e-12 | < precisão numérica |
| 60 min | ARMA_BIC | 24 | 23 | 24.701674 | 0.3658 | 7.195e-07 | 12 | 5.333e-05 | < precisão numérica |
| 60 min | AR_BIC | 24 | 22 | 19.981802 | 0.5842 | 1.054e-06 | 12 | 7.317e-05 | < precisão numérica |
| 60 min | MA_BIC | 24 | 22 | 20.258798 | 0.5669 | 1.065e-06 | 12 | 7.445e-05 | < precisão numérica |
| 1 dia | ARMA_BIC | 20 | 19 | 19.929005 | 0.3989 | 0.0034 | 12 | 0.0004 | 2.244e-06 |
| 1 dia | AR_BIC | 20 | 18 | 18.668676 | 0.4125 | 0.0049 | 12 | 0.0008 | 7.104e-06 |
| 1 dia | MA_BIC | 20 | 18 | 18.702563 | 0.4104 | 0.0049 | 12 | 0.0008 | 6.942e-06 |

Ljung–Box da média segue `gl = h − p − q − 1`, contando a constante, conforme a Aula 4. A referência usual do software
com `h − p − q` também é exportada. Em quadrados usa-se `gl=h`, como diagnóstico de dependência de segundo momento.
O cálculo por FAC-FFT e `q_stat` é numericamente equivalente ao Q convencional; não há correção por fronteiras ou bootstrap.
Referências assintóticas podem ser afetadas por heterocedasticidade; critérios de informação e diagnóstico respondem
a perguntas diferentes. Não promovemos modelos pela ausência de rejeição num horizonte escolhido depois de ver os resultados.
Todos os horizontes: [mean_diagnostics.csv](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/mean_diagnostics.csv); [residual_acf_pacf.csv](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/residual_acf_pacf.csv); [squared_residual_acf.csv](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/squared_residual_acf.csv).

## 6. Aula 6: ARCH/GARCH e previsão da variância

[Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/conditional_volatility.py).

Sequência da Aula 6, pp. 17–20: estimar a média ARMA, examinar quadrados dos resíduos, aplicar ARCH-LM, estimar variância
e diagnosticar resíduos padronizados. Comparamos variância constante, ARCH(1) e GARCH(1,1) normais sobre as mesmas inovações.

`h_t = ω + α ε²_(t−1) + β h_(t−1)`; ARCH(1) tem β=0. Exigimos convergência, ω>0, α≥0, β≥0 e
`α+β < 1−10⁻⁸`. Persistência ≥0,98 gera aviso. Não se confundem convergência numérica, positividade e adequação dos resíduos.

A estimação é **sequencial, não máxima verossimilhança conjunta ARMA–GARCH**. A média ARMA não é reestimada.
AIC/BIC contam somente os parâmetros de variância (1, 2 ou 3) e comparam candidatos condicionais à mesma média;
não são diretamente comparáveis com a log-verossimilhança ou BIC do ARMA original.

| Escala | Variância | ω | α | β | α+β | BIC condicional | Elegível | Escolhido | Próximo da fronteira |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 min | ARCH(1) | 0.000739 | 0.290224 | 0 | 0.290224 | -548728.889322 | sim | não | não |
| 1 min | Constant variance | 0.00103 | 0 | 0 | 0 | -536650.052943 | sim | não | não |
| 1 min | GARCH(1,1) | 1.58843e-05 | 0.084163 | 0.902648 | 0.986811 | -569004.707538 | sim | sim | sim |
| 5 min | ARCH(1) | 0.003839 | 0.27475 | 0 | 0.27475 | -66462.712926 | sim | não | não |
| 5 min | Constant variance | 0.005093 | 0 | 0 | 0 | -64867.44449 | sim | não | não |
| 5 min | GARCH(1,1) | 0.000576 | 0.165542 | 0.733703 | 0.899245 | -68096.122488 | sim | sim | não |
| 15 min | ARCH(1) | 0.011991 | 0.199146 | 0 | 0.199146 | -12549.215355 | sim | não | não |
| 15 min | Constant variance | 0.014797 | 0 | 0 | 0 | -12172.057509 | sim | não | não |
| 15 min | GARCH(1,1) | 0.004566 | 0.157947 | 0.538202 | 0.696149 | -12710.834504 | sim | sim | não |
| 30 min | ARCH(1) | 0.024932 | 0.154463 | 0 | 0.154463 | -3177.04374 | sim | não | não |
| 30 min | Constant variance | 0.029281 | 0 | 0 | 0 | -3059.880524 | sim | não | não |
| 30 min | GARCH(1,1) | 0.016199 | 0.150001 | 0.300339 | 0.45034 | -3202.467329 | sim | sim | não |
| 60 min | ARCH(1) | 0.051265 | 0.144086 | 0 | 0.144086 | -3.575941 | sim | sim | não |
| 60 min | Constant variance | 0.05981 | 0 | 0 | 0 | 54.848278 | sim | não | não |
| 60 min | GARCH(1,1) | 0.046806 | 0.138574 | 0.078047 | 0.216621 | 1.597081 | sim | não | não |
| 1 dia | ARCH(1) | 0.531178 | 0.142999 | 0 | 0.142999 | 586.322896 | sim | não | não |
| 1 dia | Constant variance | 0.613642 | 0 | 0 | 0 | 583.490765 | sim | sim | não |
| 1 dia | GARCH(1,1) | 0.055179 | 0.069124 | 0.843679 | 0.912802 | 587.987477 | sim | não | não |

Na avaliação de 2025, o estado é carregado do treino e continua entre pregões. `h_t` utiliza somente a inovação
efetivamente observada em t−1, nunca o erro de t. A normalização numérica usa o RMS de treino e inclui o Jacobiano
na transformação da log-verossimilhança. O teste não escolhe modelos nem seus parâmetros.

Avaliação contra **a mesma inovação quadrada da média ARMA fixa**, proxy ruidosa e não variância condicional observada:

| Escala | Modelo | N teste | MSE proxy (p.p.)⁴ | MAE proxy (p.p.)² | Estado |
| --- | --- | --- | --- | --- | --- |
| 1 min | ARCH(1) | 119.340 | 5.57959e-05 | 0.001456 | eligible |
| 1 min | Constant variance | 119.340 | 5.94509e-05 | 0.001452 | eligible |
| 1 min | GARCH(1,1) | 119.340 | 5.67779e-05 | 0.001449 | eligible |
| 5 min | ARCH(1) | 23.868 | 0.001295 | 0.007208 | eligible |
| 5 min | Constant variance | 23.868 | 0.001251 | 0.007138 | eligible |
| 5 min | GARCH(1,1) | 23.868 | 0.001214 | 0.007131 | eligible |
| 15 min | ARCH(1) | 7.956 | 0.003106 | 0.020333 | eligible |
| 15 min | Constant variance | 7.956 | 0.003375 | 0.020584 | eligible |
| 15 min | GARCH(1,1) | 7.956 | 0.003065 | 0.020178 | eligible |
| 30 min | ARCH(1) | 3.978 | 0.009224 | 0.040231 | eligible |
| 30 min | Constant variance | 3.978 | 0.009402 | 0.040301 | eligible |
| 30 min | GARCH(1,1) | 3.978 | 0.009144 | 0.040194 | eligible |
| 60 min | ARCH(1) | 1.989 | 0.033825 | 0.083621 | eligible |
| 60 min | Constant variance | 1.989 | 0.034385 | 0.08369 | eligible |
| 60 min | GARCH(1,1) | 1.989 | 0.03384 | 0.083594 | eligible |
| 1 dia | ARCH(1) | 221 | 1.609774 | 0.780669 | eligible |
| 1 dia | Constant variance | 221 | 1.540572 | 0.74333 | eligible |
| 1 dia | GARCH(1,1) | 221 | 1.552235 | 0.788274 | eligible |

Melhorar essa proxy não equivale a melhorar o retorno previsto: **todas as especificações de variância compartilham
exatamente as mesmas previsões pontuais**. Não se aplica DM às especificações aninhadas de variância.
Ljung–Box de `z=ε/√h` e `z²` usa referência assintótica χ²(h), sem subtração ad hoc de parâmetros GARCH; a calibração
é aproximada após estimação sequencial. A tabela completa de ARCH-LM e Q está no apêndice e em [variance_diagnostics.csv](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/variance_diagnostics.csv).

## 7. Entrega de 21/09: protocolo de previsão fora da amostra

[Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/forecast_evaluation.py).

Ordens e parâmetros são fixados em 2024; 2025 entra somente na avaliação e na atualização causal dos estados,
defasagens e variâncias já definidos. Filtro não é suavizador: uma observação futura não pode alterar uma previsão anterior.
Na previsão multipasso, todos os passos partem da mesma origem sem inserir realizações intermediárias futuras.

Modelos: `ARMA_BIC`, `AR_BIC`, `MA_BIC`, combinação pré-fixada `AR_MA_50_50`, retorno zero `ZERO` e média de treino `TRAIN_MEAN`.
O diário prevê o retorno da próxima janela diária; não seu preço ou overnight.

- **Nativo:** uma barra à frente em cada escala. O horizonte físico muda entre frequências: os MSE brutos não servem para ranquear escalas.
- **Comum de 60 minutos:** nove origens não sobrepostas por pregão, 09:05, 10:05, …, 17:05. Alvos não atravessam a noite.
  Cada escala prevê o mesmo retorno horário, somando apenas previsões emitidas na mesma origem.
- MSE, MAE, RMSE e razão MSE/MSE_zero são calculados sobre origens e máscaras comuns. Razão <1 é melhora; >1 é piora.
  MAPE não é usado em retornos próximos de zero. Não há otimização de pesos com o teste.

Verificação automática dos alvos realizados e das origens após a máscara de previsões finitas:

| Escala-base | Alvos | Origens iguais | Erro máximo (%) | Tolerância (%) |
| --- | --- | --- | --- | --- |
| 1 min | 1.989 | sim | 0 | 1.00000e-10 |
| 5 min | 1.989 | sim | 1.41429e-13 | 1.00000e-10 |
| 15 min | 1.989 | sim | 1.54876e-13 | 1.00000e-10 |
| 30 min | 1.989 | sim | 1.56430e-13 | 1.00000e-10 |
| 60 min | 1.989 | sim | 1.70419e-13 | 1.00000e-10 |

Previsões que coincidem numericamente (tolerância absoluta 10⁻¹⁰) não representam evidências independentes:

| Escala | Exercício | Modelo A | Modelo B | Diferença máxima |
| --- | --- | --- | --- | --- |
| 5 min | common_60min | ARMA_BIC | TRAIN_MEAN | 1.73472e-18 |
| 5 min | native | ARMA_BIC | TRAIN_MEAN | 2.16840e-19 |
| 15 min | common_60min | ARMA_BIC | TRAIN_MEAN | 0 |
| 15 min | native | ARMA_BIC | TRAIN_MEAN | 0 |
| 30 min | common_60min | ARMA_BIC | TRAIN_MEAN | 8.67362e-19 |
| 30 min | native | ARMA_BIC | TRAIN_MEAN | 4.33681e-19 |
| 60 min | common_60min | ARMA_BIC | TRAIN_MEAN | 1.73472e-18 |
| 60 min | native | ARMA_BIC | TRAIN_MEAN | 1.73472e-18 |
| 1 dia | native | ARMA_BIC | TRAIN_MEAN | 1.38778e-17 |

Sem otimização ex post: o menor MSE observado em 2025 é um ranking descritivo, não um modelo novamente selecionado e testado na mesma amostra.

## 8. Acurácia: todas as escalas e comparadores

[Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/forecast_evaluation.py).

Erros de retorno estão em pontos percentuais; MSE em (p.p.)²; MAE/RMSE em p.p.; a razão com o modelo zero é adimensional.
O sinal do ganho é `1 − MSE/MSE_zero`. Comparar previsibilidade entre escalas requer o bloco de alvos comuns,
e não apenas que uma escala tenha retornos numericamente menores.

| Escala | Exercício | Modelo | N | MSE | MAE | RMSE | MSE/MSE zero | Ganho fracionário |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 min | common_60min | ARMA_BIC | 1.989 | 0.076756 | 0.193667 | 0.277048 | 1.00194 | -0.00194 |
| 1 min | common_60min | AR_BIC | 1.989 | 0.076768 | 0.193666 | 0.277071 | 1.002102 | -0.002102 |
| 1 min | common_60min | AR_MA_50_50 | 1.989 | 0.076768 | 0.193666 | 0.277071 | 1.002103 | -0.002103 |
| 1 min | common_60min | MA_BIC | 1.989 | 0.076768 | 0.193666 | 0.277071 | 1.002103 | -0.002103 |
| 1 min | common_60min | TRAIN_MEAN | 1.989 | 0.076763 | 0.193661 | 0.277061 | 1.002031 | -0.002031 |
| 1 min | common_60min | ZERO | 1.989 | 0.076607 | 0.193495 | 0.27678 | 1 | 0 |
| 1 min | native | ARMA_BIC | 119.340 | 0.001309 | 0.024502 | 0.036184 | 1.000524 | -0.000524 |
| 1 min | native | AR_BIC | 119.340 | 0.001309 | 0.024482 | 0.036175 | 1.000019 | -1.90268e-05 |
| 1 min | native | AR_MA_50_50 | 119.340 | 0.001309 | 0.024482 | 0.036175 | 1.000019 | -1.87767e-05 |
| 1 min | native | MA_BIC | 119.340 | 0.001309 | 0.024482 | 0.036175 | 1.000019 | -1.85296e-05 |
| 1 min | native | TRAIN_MEAN | 119.340 | 0.001309 | 0.024487 | 0.036176 | 1.000033 | -3.30186e-05 |
| 1 min | native | ZERO | 119.340 | 0.001309 | 0.024479 | 0.036175 | 1 | 0 |
| 5 min | common_60min | ARMA_BIC | 1.989 | 0.076763 | 0.193661 | 0.277061 | 1.002031 | -0.002031 |
| 5 min | common_60min | AR_BIC | 1.989 | 0.076763 | 0.193662 | 0.277062 | 1.002037 | -0.002037 |
| 5 min | common_60min | AR_MA_50_50 | 1.989 | 0.076763 | 0.193662 | 0.277062 | 1.002037 | -0.002037 |
| 5 min | common_60min | MA_BIC | 1.989 | 0.076763 | 0.193662 | 0.277062 | 1.002037 | -0.002037 |
| 5 min | common_60min | TRAIN_MEAN | 1.989 | 0.076763 | 0.193661 | 0.277061 | 1.002031 | -0.002031 |
| 5 min | common_60min | ZERO | 1.989 | 0.076607 | 0.193495 | 0.27678 | 1 | 0 |
| 5 min | native | ARMA_BIC | 23.868 | 0.006558 | 0.055458 | 0.080979 | 1.000165 | -0.000165 |
| 5 min | native | AR_BIC | 23.868 | 0.006558 | 0.055464 | 0.080983 | 1.000251 | -0.000251 |
| 5 min | native | AR_MA_50_50 | 23.868 | 0.006558 | 0.055464 | 0.080983 | 1.000252 | -0.000252 |
| 5 min | native | MA_BIC | 23.868 | 0.006558 | 0.055464 | 0.080983 | 1.000253 | -0.000253 |
| 5 min | native | TRAIN_MEAN | 23.868 | 0.006558 | 0.055458 | 0.080979 | 1.000165 | -0.000165 |
| 5 min | native | ZERO | 23.868 | 0.006557 | 0.055435 | 0.080973 | 1 | 0 |
| 15 min | common_60min | ARMA_BIC | 1.989 | 0.076763 | 0.193661 | 0.277061 | 1.002031 | -0.002031 |
| 15 min | common_60min | AR_BIC | 1.989 | 0.076774 | 0.19368 | 0.277081 | 1.002174 | -0.002174 |
| 15 min | common_60min | AR_MA_50_50 | 1.989 | 0.076774 | 0.19368 | 0.27708 | 1.002172 | -0.002172 |
| 15 min | common_60min | MA_BIC | 1.989 | 0.076773 | 0.19368 | 0.27708 | 1.002171 | -0.002171 |
| 15 min | common_60min | TRAIN_MEAN | 1.989 | 0.076763 | 0.193661 | 0.277061 | 1.002031 | -0.002031 |
| 15 min | common_60min | ZERO | 1.989 | 0.076607 | 0.193495 | 0.27678 | 1 | 0 |
| 15 min | native | ARMA_BIC | 7.956 | 0.018622 | 0.09381 | 0.136461 | 1.000522 | -0.000522 |
| 15 min | native | AR_BIC | 7.956 | 0.018622 | 0.093828 | 0.136463 | 1.000545 | -0.000545 |
| 15 min | native | AR_MA_50_50 | 7.956 | 0.018622 | 0.093828 | 0.136462 | 1.000544 | -0.000544 |
| 15 min | native | MA_BIC | 7.956 | 0.018622 | 0.093827 | 0.136462 | 1.000543 | -0.000543 |
| 15 min | native | TRAIN_MEAN | 7.956 | 0.018622 | 0.09381 | 0.136461 | 1.000522 | -0.000522 |
| 15 min | native | ZERO | 7.956 | 0.018612 | 0.093753 | 0.136425 | 1 | 0 |
| 30 min | common_60min | ARMA_BIC | 1.989 | 0.076763 | 0.193661 | 0.277061 | 1.002031 | -0.002031 |
| 30 min | common_60min | AR_BIC | 1.989 | 0.076777 | 0.193667 | 0.277087 | 1.002222 | -0.002222 |
| 30 min | common_60min | AR_MA_50_50 | 1.989 | 0.076778 | 0.193668 | 0.277088 | 1.002226 | -0.002226 |
| 30 min | common_60min | MA_BIC | 1.989 | 0.076778 | 0.193668 | 0.277088 | 1.00223 | -0.00223 |
| 30 min | common_60min | TRAIN_MEAN | 1.989 | 0.076763 | 0.193661 | 0.277061 | 1.002031 | -0.002031 |
| 30 min | common_60min | ZERO | 1.989 | 0.076607 | 0.193495 | 0.27678 | 1 | 0 |
| 30 min | native | ARMA_BIC | 3.978 | 0.036911 | 0.133923 | 0.192123 | 1.001055 | -0.001055 |
| 30 min | native | AR_BIC | 3.978 | 0.036909 | 0.133947 | 0.192117 | 1.000995 | -0.000995 |
| 30 min | native | AR_MA_50_50 | 3.978 | 0.036909 | 0.133948 | 0.192117 | 1.000994 | -0.000994 |
| 30 min | native | MA_BIC | 3.978 | 0.036909 | 0.133948 | 0.192117 | 1.000993 | -0.000993 |
| 30 min | native | TRAIN_MEAN | 3.978 | 0.036911 | 0.133923 | 0.192123 | 1.001055 | -0.001055 |
| 30 min | native | ZERO | 3.978 | 0.036872 | 0.133881 | 0.192021 | 1 | 0 |
| 60 min | common_60min | ARMA_BIC | 1.989 | 0.076763 | 0.193661 | 0.277061 | 1.002031 | -0.002031 |
| 60 min | common_60min | AR_BIC | 1.989 | 0.076832 | 0.193923 | 0.277187 | 1.00294 | -0.00294 |
| 60 min | common_60min | AR_MA_50_50 | 1.989 | 0.076828 | 0.193916 | 0.277179 | 1.002886 | -0.002886 |
| 60 min | common_60min | MA_BIC | 1.989 | 0.076824 | 0.193908 | 0.277172 | 1.002835 | -0.002835 |
| 60 min | common_60min | TRAIN_MEAN | 1.989 | 0.076763 | 0.193661 | 0.277061 | 1.002031 | -0.002031 |
| 60 min | common_60min | ZERO | 1.989 | 0.076607 | 0.193495 | 0.27678 | 1 | 0 |
| 60 min | native | ARMA_BIC | 1.989 | 0.076763 | 0.193661 | 0.277061 | 1.002031 | -0.002031 |
| 60 min | native | AR_BIC | 1.989 | 0.076832 | 0.193923 | 0.277187 | 1.00294 | -0.00294 |
| 60 min | native | AR_MA_50_50 | 1.989 | 0.076828 | 0.193916 | 0.277179 | 1.002886 | -0.002886 |
| 60 min | native | MA_BIC | 1.989 | 0.076824 | 0.193908 | 0.277172 | 1.002835 | -0.002835 |
| 60 min | native | TRAIN_MEAN | 1.989 | 0.076763 | 0.193661 | 0.277061 | 1.002031 | -0.002031 |
| 60 min | native | ZERO | 1.989 | 0.076607 | 0.193495 | 0.27678 | 1 | 0 |
| 1 dia | native | ARMA_BIC | 221 | 0.747564 | 0.653092 | 0.864618 | 1.017005 | -0.017005 |
| 1 dia | native | AR_BIC | 221 | 0.749286 | 0.650592 | 0.865613 | 1.019348 | -0.019348 |
| 1 dia | native | AR_MA_50_50 | 221 | 0.749353 | 0.650681 | 0.865652 | 1.019439 | -0.019439 |
| 1 dia | native | MA_BIC | 221 | 0.749421 | 0.650771 | 0.865691 | 1.019533 | -0.019533 |
| 1 dia | native | TRAIN_MEAN | 221 | 0.747564 | 0.653092 | 0.864618 | 1.017005 | -0.017005 |
| 1 dia | native | ZERO | 221 | 0.735064 | 0.649552 | 0.857359 | 1 | 0 |

Tabela completa, inclusive faixas e grupos de gaps: [accuracy.csv](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/accuracy.csv).

## 9. Comparação Diebold–Mariano

[Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/forecast_evaluation.py).

Comparação pré-especificada: AR puro positivo × MA puro positivo, selecionados em 2024. São famílias não aninhadas,
mas podem degenerar em previsões ou perdas idênticas. O teste não é aplicado ao ARMA geral contra sua extensão GARCH
e não demonstra superioridade dos comparadores frente ao vencedor geral da grade.

`d_t = perda_AR − perda_MA`: estatística negativa favorece AR. Perda quadrática é principal; absoluta, complementar.
A variância de longo prazo segue a soma retangular de autocovariâncias da Aula 4; há correção de pequena amostra
e referência t com N−1 graus de liberdade. No nativo, q cobre uma hora em barras; no comum60 e diário, q=1.
q=0 é sensibilidade exportada. Os alvos da sequência de perdas não se sobrepõem, portanto `h_perda=1`, distinto
do número de barras necessário para prever 60 minutos em cada escala.

| Escala | Exercício | Perda | N | q covariâncias | Horizonte em barras | h perdas | Diferença média AR−MA | DM corrigido | p-valor | Estado |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 min | common_60min | absolute | 1.989 | 1 | 60 | 1 | -4.55293e-08 | -0.476481 | 0.6338 | computed_approximate |
| 1 min | common_60min | squared | 1.989 | 1 | 60 | 1 | -9.72424e-08 | -1.581505 | 0.1139 | computed_approximate |
| 1 min | native | absolute | 119.340 | 60 | 1 | 1 | 3.93600e-08 | 4.522884 | 6.106e-06 | computed_approximate |
| 1 min | native | squared | 119.340 | 60 | 1 | 1 | 6.50584e-10 | 0.348406 | 0.7275 | computed_approximate |
| 5 min | common_60min | absolute | 1.989 | 1 | 12 | 1 | -1.56119e-08 | -0.150159 | 0.8807 | computed_approximate |
| 5 min | common_60min | squared | 1.989 | 1 | 12 | 1 | -2.39829e-09 | -0.033633 | 0.9732 | computed_approximate |
| 5 min | native | absolute | 23.868 | 12 | 1 | 1 | -1.39107e-07 | -4.370671 | 1.244e-05 | computed_approximate |
| 5 min | native | squared | 23.868 | 12 | 1 | 1 | -1.41667e-08 | -1.924797 | 0.0543 | computed_approximate |
| 15 min | common_60min | absolute | 1.989 | 1 | 4 | 1 | 2.95608e-07 | 0.657737 | 0.5108 | computed_approximate |
| 15 min | common_60min | squared | 1.989 | 1 | 4 | 1 | 2.64341e-07 | 0.831369 | 0.4059 | computed_approximate |
| 15 min | native | absolute | 7.956 | 4 | 1 | 1 | 2.60440e-07 | 1.692103 | 0.0907 | computed_approximate |
| 15 min | native | squared | 7.956 | 4 | 1 | 1 | 4.46922e-08 | 0.537698 | 0.5908 | computed_approximate |
| 30 min | common_60min | absolute | 1.989 | 1 | 2 | 1 | -3.87166e-07 | -0.359532 | 0.7192 | computed_approximate |
| 30 min | common_60min | squared | 1.989 | 1 | 2 | 1 | -6.50495e-07 | -0.776972 | 0.4373 | computed_approximate |
| 30 min | native | absolute | 3.978 | 2 | 1 | 1 | -1.11880e-06 | -1.292088 | 0.1964 | computed_approximate |
| 30 min | native | squared | 3.978 | 2 | 1 | 1 | 5.16869e-08 | 0.11807 | 0.9060 | computed_approximate |
| 60 min | common_60min | absolute | 1.989 | 1 | 1 | 1 | 1.49657e-05 | 0.890721 | 0.3732 | computed_approximate |
| 60 min | common_60min | squared | 1.989 | 1 | 1 | 1 | 8.04645e-06 | 0.72308 | 0.4697 | computed_approximate |
| 60 min | native | absolute | 1.989 | 1 | 1 | 1 | 1.49657e-05 | 0.890721 | 0.3732 | computed_approximate |
| 60 min | native | squared | 1.989 | 1 | 1 | 1 | 8.04645e-06 | 0.72308 | 0.4697 | computed_approximate |
| 1 dia | native | absolute | 221 | 1 | 1 | 1 | -0.000179 | -1.467435 | 0.1437 | computed_approximate |
| 1 dia | native | squared | 221 | 1 | 1 | 1 | -0.000136 | -0.592352 | 0.5542 | computed_approximate |

Perdas iguais, variância de longo prazo não positiva ou degenerada impedem p-valor, em vez de produzir significância artificial.
A inferência é aproximada, pressupõe comportamento adequado da sequência de perdas e não é robusta a toda forma
de não estacionariedade. Os vários testes não têm correção de multiplicidade e devem ser lidos conjuntamente com
magnitudes de erro, horizonte e diagnóstico. Não criamos testes adicionais fora do material da disciplina.
Todas as sensibilidades: [diebold_mariano.csv](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/diebold_mariano.csv).

## 10. Faixas do pregão, gaps e limites sobre leilões

[Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/trading_time_data.py).

As faixas são físicas e iguais entre escalas: início 09:05–10:05; meio 10:05–17:05; fim 17:05–18:05.
Uma hora de minuto é comparada com uma hora de barras maiores, não a primeira barra de qualquer duração.
O diário não tem uma decomposição intradiária artificial. Descrição de 2024:

| Escala | Faixa | N | Média (%) | Desvio (%) | Excesso curtose |
| --- | --- | --- | --- | --- | --- |
| 1 min | fim | 14.760 | -5.14536e-05 | 0.021961 | 13.653434 |
| 1 min | inicio | 14.760 | -0.000348 | 0.039217 | 34.836001 |
| 1 min | meio | 103.320 | -0.0001 | 0.032198 | 14.066401 |
| 5 min | fim | 2.952 | -0.000257 | 0.046376 | 6.641493 |
| 5 min | inicio | 2.952 | -0.001738 | 0.091066 | 35.711835 |
| 5 min | meio | 20.664 | -0.0005 | 0.071114 | 14.201673 |
| 15 min | fim | 984 | -0.000772 | 0.075754 | 4.727508 |
| 15 min | inicio | 984 | -0.005215 | 0.155841 | 8.920476 |
| 15 min | meio | 6.888 | -0.0015 | 0.121407 | 7.057865 |
| 30 min | fim | 492 | -0.001544 | 0.104766 | 4.910711 |
| 30 min | inicio | 492 | -0.010431 | 0.215685 | 3.199077 |
| 30 min | meio | 3.444 | -0.003 | 0.171614 | 4.911572 |
| 60 min | fim | 246 | -0.003087 | 0.148563 | 3.634899 |
| 60 min | inicio | 246 | -0.020862 | 0.305426 | 2.46861 |
| 60 min | meio | 1.722 | -0.006 | 0.245949 | 6.237631 |
| 1 dia | diario | 246 | -0.065483 | 0.78495 | 1.194597 |

Gap auxiliar: primeiro open observado do dia / último close observado da sessão anterior, somente no mesmo contrato
e sem lacuna de dias úteis suspeita. É chamado **gap entre sessões observadas**, não retorno overnight oficial nem preço certificado de leilão.
O limiar entre menor/maior magnitude é a mediana de |gap| nos pregões incluídos de 2024: **0.200222%**;
o mesmo limiar é aplicado a 2025. Ausência de calendário completo pode excluir conservadoramente feriados.

| Amostra | Grupo | Dias | Gaps disponíveis | Gap médio (%) | Desvio gap (%) |
| --- | --- | --- | --- | --- | --- |
| test | high | 97 | 97 | -0.033212 | 0.484693 |
| test | low | 114 | 114 | -0.006659 | 0.109807 |
| test | unavailable | 10 | 0 | — | — |
| train | high | 117 | 117 | 0.004156 | 0.475773 |
| train | low | 117 | 117 | 0.009344 | 0.118528 |
| train | unavailable | 12 | 0 | — | — |

Comparações por grupo são decomposições **ex post** de erros já produzidos, não preditores retroativamente disponíveis.
Um gap observado somente depois da abertura não entra numa previsão emitida antes dela.
As tabelas do apêndice apresentam ARMA selecionado e benchmark zero; os demais modelos permanecem em [accuracy.csv](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/accuracy.csv).

Os candles não trazem fase de negociação. Nos horários históricos efetivamente documentados, a janela principal
não cobre os calls próprios de abertura/fechamento do WIN. Pode cobrir o entorno de eventos das ações subjacentes,
em horários que mudam por regime. O período intermediário não é necessariamente afastado de todos os eventos de mercado.
A cronologia de ofícios e exceções de 2024–2025 é incompleta; não se extrapola a grade atual para toda a amostra.

Fontes B3, datas de vigência, diferenças entre ajuste e call, e lacunas:
[auditoria histórica de horários](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/docs/market_hours_2024_2025.md).
Primeiros e últimos horários efetivamente observados no feed: [observed_source_hours.csv](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/observed_source_hours.csv).
Essas evidências não identificam efeito causal de leilões, não demonstram que os efeitos overnight desapareceram
e não permitem atribuir toda diferença entre frequências à microestrutura.

## 11. Conclusão e limites do que foi demonstrado

[Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/forecast_pipeline.py).

Seleção BIC da média em 2024: 1 min: ARMA(2,2); 5 min: ARMA(0,0); 15 min: ARMA(0,0); 30 min: ARMA(0,0); 60 min: ARMA(0,0); 1 dia: ARMA(0,0).

Ljung–Box da média, no horizonte diagnóstico principal, rejeita ausência de autocorrelação em: 1 min. A referência é assintótica e pode ser afetada por heterocedasticidade; não rejeitar não prova ruído independente.

Alvo comum de 60 minutos, série-base 1 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.

Alvo comum de 60 minutos, série-base 5 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.

Alvo comum de 60 minutos, série-base 15 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.

Alvo comum de 60 minutos, série-base 30 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.

Alvo comum de 60 minutos, série-base 60 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.

Seleção BIC condicional da variância em 2024: 1 min: GARCH(1,1); 5 min: GARCH(1,1); 15 min: GARCH(1,1); 30 min: GARCH(1,1); 60 min: ARCH(1); 1 dia: Constant variance. A previsão pontual permanece a mesma.

As previsões ARMA(0,0) no alvo comum coincidem nas escalas 5 min, 15 min, 30 min, 60 min: somar as médias das barras completas produz a mesma média horária. Isso decorre da agregação dos mesmos dados, não de confirmações independentes de previsibilidade.

Estacionariedade, ausência de autocorrelação linear residual, ajuste dentro da amostra e capacidade preditiva fora da amostra são propriedades distintas.

A comparação multiescala precisa separar horizonte e frequência de observação. Maior previsibilidade horária não foi incorporada como premissa nem garantida pela agregação.

A validade externa está limitada a um ativo, uma janela, um ano de estimação e ao trecho disponível de 2025, condicionados ao filtro de qualidade. Não há simulação de P&L, custos, impacto de mercado ou recomendação de operação.

Os modelos são convencionais e as referências inferenciais são aproximadas. Heterocedasticidade, sazonalidade intradiária, quebras e calendários incompletos restringem as conclusões. Os métodos das aulas foram mantidos sem bootstrap, testes de painel, redes neurais ou modelos adicionais de regime.

## 12. Reprodutibilidade, versões e publicação

[Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/forecast_pipeline.py).

O comando abaixo pressupõe acesso autorizado ao ZIP original. Dados brutos, preços, retornos, previsões individuais,
resíduos e caches de ajuste ficam em `private/` e não são publicados. Este relatório usa somente CSV agregados públicos.
O código não baixa nem substitui os dados por uma série simulada. Parâmetros não são reestimados no holdout.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock-21-09.txt
OPENBLAS_NUM_THREADS=1 python scripts/run_entrega_21_09.py \
  --input /caminho/autorizado/BTG-ATS-A26.zip \
  --output results/entrega_21_09 --workers 3 --code-ref a6c7de81989e586ea117e994f366a1bb6933a66b
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v
```

No Windows, a ativação e definição de variáveis de ambiente devem usar a sintaxe equivalente do shell.
O arquivo de dependências travadas descreve a execução entregue; `requirements.txt`/`pyproject.toml` descrevem os requisitos gerais.
Para compilar a apresentação PDF, é necessário instalar separadamente uma distribuição LaTeX com `pdflatex`,
classe Beamer e fontes Latin Modern (`lmodern`). Esses componentes não são instalados pelo pip.
A opção `--skip-report` permite executar a análise numérica e exportar suas tabelas sem depender de LaTeX;
nessa modalidade a apresentação e os relatórios não são gerados automaticamente.
Python registrado: **3.12.14**. Versões numéricas:

| Pacote | Versão |
| --- | --- |
| numpy | 2.3.5 |
| pandas | 2.2.3 |
| scipy | 1.17.0 |
| statsmodels | 0.15.0 |
| arch | 8.0.0 |
| pyarrow | 25.0.1 |
| matplotlib | 3.10.8 |
| reportlab | 4.4.9 |

Manifesto com hashes do código, fonte, parâmetros do protocolo e asserções de isolamento:
[analysis_summary.json](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/analysis_summary.json). Referência de código dos links: `a6c7de81989e586ea117e994f366a1bb6933a66b`.
Fonte deste relatório: [Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/forecast_narrative.py). Alterações de lógica invalidam os checkpoints pertinentes.
Testes automatizados exercitam isolamento de 2024, contaminação artificial do futuro, igualdade de alvos horários,
recursão de variância, Jacobiano, identidade de Q e cálculo de DM; verificar o registro de execução para a contagem efetiva.

## Referências e vinculação às aulas

- Maciel, Leandro. EAD6034, Aulas 3 e 4: identificação, máxima verossimilhança, AIC/BIC, Box–Jenkins, diagnóstico e avaliação de previsões; materiais fornecidos pelo aluno.
- Maciel, Leandro. Aula 5: ADF, Phillips–Perron e KPSS, hipóteses e especificações determinísticas.
- Maciel, Leandro. Aula 6: ARCH/GARCH e estabilidade (pp. 9–16), FAC dos quadrados e ARCH-LM (pp. 17–18), diagnóstico e sequência metodológica (pp. 19–20), integração ARMA–GARCH (p. 28).
- Matías, J. M.; Reboredo, J. C. (2012). Forecasting performance of nonlinear models for intraday stock returns. *Journal of Forecasting*, 31(2), 172–188. [DOI](https://doi.org/10.1002/for.1218). Referência de motivação, não reprodução dos modelos não lineares.
- B3. Ofícios e grades históricas discriminados na [auditoria de horários](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/docs/market_hours_2024_2025.md).
- [Enunciado/protocolo operacional consolidado](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/docs/PROTOCOL_21_09.md): entregas de 31/08, 14/09 e 21/09; seminário de 28/09.

## Apêndice A — diagnóstico completo da variância

[Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/conditional_volatility.py).

| Escala | Modelo | Série | Teste | Lag | Estatística | gl | p-valor | Rejeita 5% |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 min | arch1 | squared_standardized_residuals | Ljung-Box | 10 | 3716.604872 | 10 | < precisão numérica | sim |
| 1 min | arch1 | squared_standardized_residuals | Ljung-Box | 20 | 6404.729674 | 20 | < precisão numérica | sim |
| 1 min | arch1 | squared_standardized_residuals | Ljung-Box | 60 | 12134.96816 | 60 | < precisão numérica | sim |
| 1 min | arch1 | standardized_residuals | Ljung-Box | 10 | 26.580036 | 10 | 0.0030 | sim |
| 1 min | arch1 | standardized_residuals | Ljung-Box | 20 | 47.831536 | 20 | 0.0004 | sim |
| 1 min | arch1 | standardized_residuals | Ljung-Box | 60 | 89.209535 | 60 | 0.0085 | sim |
| 1 min | constant | squared_standardized_residuals | Ljung-Box | 10 | 15840.628777 | 10 | < precisão numérica | sim |
| 1 min | constant | squared_standardized_residuals | Ljung-Box | 20 | 17744.101109 | 20 | < precisão numérica | sim |
| 1 min | constant | squared_standardized_residuals | Ljung-Box | 60 | 21088.451986 | 60 | < precisão numérica | sim |
| 1 min | constant | standardized_residuals | Ljung-Box | 10 | 24.834806 | 10 | 0.0057 | sim |
| 1 min | constant | standardized_residuals | Ljung-Box | 20 | 42.039475 | 20 | 0.0027 | sim |
| 1 min | constant | standardized_residuals | Ljung-Box | 60 | 100.658648 | 60 | 0.0008 | sim |
| 1 min | fixed_arma_mean | innovations | ARCH-LM | 10 | 11464.678171 | 10 | < precisão numérica | sim |
| 1 min | fixed_arma_mean | innovations | ARCH-LM | 20 | 11768.891747 | 20 | < precisão numérica | sim |
| 1 min | fixed_arma_mean | innovations | ARCH-LM | 60 | 12068.792876 | 60 | < precisão numérica | sim |
| 1 min | garch11 | squared_standardized_residuals | Ljung-Box | 10 | 146.12264 | 10 | 2.336e-26 | sim |
| 1 min | garch11 | squared_standardized_residuals | Ljung-Box | 20 | 168.01172 | 20 | 2.110e-25 | sim |
| 1 min | garch11 | squared_standardized_residuals | Ljung-Box | 60 | 249.754902 | 60 | 5.387e-25 | sim |
| 1 min | garch11 | standardized_residuals | Ljung-Box | 10 | 16.79746 | 10 | 0.0790 | não |
| 1 min | garch11 | standardized_residuals | Ljung-Box | 20 | 27.067062 | 20 | 0.1334 | não |
| 1 min | garch11 | standardized_residuals | Ljung-Box | 60 | 61.761546 | 60 | 0.4129 | não |
| 5 min | arch1 | squared_standardized_residuals | Ljung-Box | 10 | 50.860252 | 10 | 1.853e-07 | sim |
| 5 min | arch1 | squared_standardized_residuals | Ljung-Box | 20 | 115.436119 | 20 | 1.984e-15 | sim |
| 5 min | arch1 | squared_standardized_residuals | Ljung-Box | 24 | 121.376104 | 24 | 5.514e-15 | sim |
| 5 min | arch1 | standardized_residuals | Ljung-Box | 10 | 19.694863 | 10 | 0.0323 | sim |
| 5 min | arch1 | standardized_residuals | Ljung-Box | 20 | 32.178606 | 20 | 0.0414 | sim |
| 5 min | arch1 | standardized_residuals | Ljung-Box | 24 | 34.109421 | 24 | 0.0827 | não |
| 5 min | constant | squared_standardized_residuals | Ljung-Box | 10 | 959.549689 | 10 | 9.638e-200 | sim |
| 5 min | constant | squared_standardized_residuals | Ljung-Box | 20 | 1025.725975 | 20 | 1.272e-204 | sim |
| 5 min | constant | squared_standardized_residuals | Ljung-Box | 24 | 1030.36016 | 24 | 3.161e-202 | sim |
| 5 min | constant | standardized_residuals | Ljung-Box | 10 | 17.679917 | 10 | 0.0606 | não |
| 5 min | constant | standardized_residuals | Ljung-Box | 20 | 31.38924 | 20 | 0.0503 | não |
| 5 min | constant | standardized_residuals | Ljung-Box | 24 | 33.181021 | 24 | 0.1003 | não |
| 5 min | fixed_arma_mean | innovations | ARCH-LM | 10 | 794.047654 | 10 | 3.928e-164 | sim |
| 5 min | fixed_arma_mean | innovations | ARCH-LM | 20 | 819.967668 | 20 | 8.148e-161 | sim |
| 5 min | fixed_arma_mean | innovations | ARCH-LM | 24 | 822.628946 | 24 | 3.427e-158 | sim |
| 5 min | garch11 | squared_standardized_residuals | Ljung-Box | 10 | 0.763845 | 10 | 1.0000 | não |
| 5 min | garch11 | squared_standardized_residuals | Ljung-Box | 20 | 2.25535 | 20 | 1.0000 | não |
| 5 min | garch11 | squared_standardized_residuals | Ljung-Box | 24 | 2.496777 | 24 | 1.0000 | não |
| 5 min | garch11 | standardized_residuals | Ljung-Box | 10 | 12.952618 | 10 | 0.2263 | não |
| 5 min | garch11 | standardized_residuals | Ljung-Box | 20 | 18.235609 | 20 | 0.5719 | não |
| 5 min | garch11 | standardized_residuals | Ljung-Box | 24 | 19.386102 | 24 | 0.7311 | não |
| 15 min | arch1 | squared_standardized_residuals | Ljung-Box | 10 | 42.078811 | 10 | 7.260e-06 | sim |
| 15 min | arch1 | squared_standardized_residuals | Ljung-Box | 20 | 49.819685 | 20 | 0.0002 | sim |
| 15 min | arch1 | squared_standardized_residuals | Ljung-Box | 24 | 50.729786 | 24 | 0.0011 | sim |
| 15 min | arch1 | standardized_residuals | Ljung-Box | 10 | 15.284215 | 10 | 0.1220 | não |
| 15 min | arch1 | standardized_residuals | Ljung-Box | 20 | 24.541584 | 20 | 0.2195 | não |
| 15 min | arch1 | standardized_residuals | Ljung-Box | 24 | 25.53719 | 24 | 0.3771 | não |
| 15 min | constant | squared_standardized_residuals | Ljung-Box | 10 | 319.559908 | 10 | 1.130e-62 | sim |
| 15 min | constant | squared_standardized_residuals | Ljung-Box | 20 | 325.294334 | 20 | 5.361e-57 | sim |
| 15 min | constant | squared_standardized_residuals | Ljung-Box | 24 | 326.363233 | 24 | 7.933e-55 | sim |
| 15 min | constant | standardized_residuals | Ljung-Box | 10 | 14.416203 | 10 | 0.1548 | não |
| 15 min | constant | standardized_residuals | Ljung-Box | 20 | 23.069339 | 20 | 0.2854 | não |
| 15 min | constant | standardized_residuals | Ljung-Box | 24 | 23.895298 | 24 | 0.4676 | não |
| 15 min | fixed_arma_mean | innovations | ARCH-LM | 10 | 258.922413 | 10 | 7.204e-50 | sim |
| 15 min | fixed_arma_mean | innovations | ARCH-LM | 20 | 263.451369 | 20 | 2.188e-44 | sim |
| 15 min | fixed_arma_mean | innovations | ARCH-LM | 24 | 265.054667 | 24 | 1.681e-42 | sim |
| 15 min | garch11 | squared_standardized_residuals | Ljung-Box | 10 | 2.299995 | 10 | 0.9935 | não |
| 15 min | garch11 | squared_standardized_residuals | Ljung-Box | 20 | 5.45955 | 20 | 0.9995 | não |
| 15 min | garch11 | squared_standardized_residuals | Ljung-Box | 24 | 6.195034 | 24 | 0.9999 | não |
| 15 min | garch11 | standardized_residuals | Ljung-Box | 10 | 13.858946 | 10 | 0.1795 | não |
| 15 min | garch11 | standardized_residuals | Ljung-Box | 20 | 23.116381 | 20 | 0.2831 | não |
| 15 min | garch11 | standardized_residuals | Ljung-Box | 24 | 24.191628 | 24 | 0.4507 | não |
| 30 min | arch1 | squared_standardized_residuals | Ljung-Box | 10 | 20.683985 | 10 | 0.0234 | sim |
| 30 min | arch1 | squared_standardized_residuals | Ljung-Box | 20 | 47.168497 | 20 | 0.0006 | sim |
| 30 min | arch1 | squared_standardized_residuals | Ljung-Box | 24 | 48.836249 | 24 | 0.0020 | sim |
| 30 min | arch1 | standardized_residuals | Ljung-Box | 10 | 12.773214 | 10 | 0.2366 | não |
| 30 min | arch1 | standardized_residuals | Ljung-Box | 20 | 23.938575 | 20 | 0.2451 | não |
| 30 min | arch1 | standardized_residuals | Ljung-Box | 24 | 24.222048 | 24 | 0.4490 | não |
| 30 min | constant | squared_standardized_residuals | Ljung-Box | 10 | 89.755466 | 10 | 5.988e-15 | sim |
| 30 min | constant | squared_standardized_residuals | Ljung-Box | 20 | 135.020431 | 20 | 4.429e-19 | sim |
| 30 min | constant | squared_standardized_residuals | Ljung-Box | 24 | 139.801262 | 24 | 2.533e-18 | sim |
| 30 min | constant | standardized_residuals | Ljung-Box | 10 | 9.989009 | 10 | 0.4415 | não |
| 30 min | constant | standardized_residuals | Ljung-Box | 20 | 21.807441 | 20 | 0.3511 | não |
| 30 min | constant | standardized_residuals | Ljung-Box | 24 | 22.363419 | 24 | 0.5576 | não |
| 30 min | fixed_arma_mean | innovations | ARCH-LM | 10 | 76.402684 | 10 | 2.536e-12 | sim |
| 30 min | fixed_arma_mean | innovations | ARCH-LM | 20 | 104.940197 | 20 | 1.628e-13 | sim |
| 30 min | fixed_arma_mean | innovations | ARCH-LM | 24 | 108.883577 | 24 | 8.830e-13 | sim |
| 30 min | garch11 | squared_standardized_residuals | Ljung-Box | 10 | 2.454095 | 10 | 0.9915 | não |
| 30 min | garch11 | squared_standardized_residuals | Ljung-Box | 20 | 25.619782 | 20 | 0.1787 | não |
| 30 min | garch11 | squared_standardized_residuals | Ljung-Box | 24 | 27.093926 | 24 | 0.3001 | não |
| 30 min | garch11 | standardized_residuals | Ljung-Box | 10 | 12.57547 | 10 | 0.2484 | não |
| 30 min | garch11 | standardized_residuals | Ljung-Box | 20 | 23.813172 | 20 | 0.2506 | não |
| 30 min | garch11 | standardized_residuals | Ljung-Box | 24 | 24.076513 | 24 | 0.4572 | não |
| 60 min | arch1 | squared_standardized_residuals | Ljung-Box | 10 | 20.643233 | 10 | 0.0237 | sim |
| 60 min | arch1 | squared_standardized_residuals | Ljung-Box | 20 | 37.032553 | 20 | 0.0116 | sim |
| 60 min | arch1 | squared_standardized_residuals | Ljung-Box | 24 | 41.881157 | 24 | 0.0133 | sim |
| 60 min | arch1 | standardized_residuals | Ljung-Box | 10 | 8.383394 | 10 | 0.5914 | não |
| 60 min | arch1 | standardized_residuals | Ljung-Box | 20 | 17.022814 | 20 | 0.6515 | não |
| 60 min | arch1 | standardized_residuals | Ljung-Box | 24 | 23.79842 | 24 | 0.4732 | não |
| 60 min | constant | squared_standardized_residuals | Ljung-Box | 10 | 42.753245 | 10 | 5.504e-06 | sim |
| 60 min | constant | squared_standardized_residuals | Ljung-Box | 20 | 67.924206 | 20 | 3.960e-07 | sim |
| 60 min | constant | squared_standardized_residuals | Ljung-Box | 24 | 73.158516 | 24 | 7.195e-07 | sim |
| 60 min | constant | standardized_residuals | Ljung-Box | 10 | 9.284369 | 10 | 0.5053 | não |
| 60 min | constant | standardized_residuals | Ljung-Box | 20 | 18.202116 | 20 | 0.5741 | não |
| 60 min | constant | standardized_residuals | Ljung-Box | 24 | 24.701674 | 24 | 0.4221 | não |
| 60 min | fixed_arma_mean | innovations | ARCH-LM | 10 | 39.087275 | 10 | 2.451e-05 | sim |
| 60 min | fixed_arma_mean | innovations | ARCH-LM | 20 | 59.257424 | 20 | 9.273e-06 | sim |
| 60 min | fixed_arma_mean | innovations | ARCH-LM | 24 | 62.98695 | 24 | 2.391e-05 | sim |
| 60 min | garch11 | squared_standardized_residuals | Ljung-Box | 10 | 16.286894 | 10 | 0.0917 | não |
| 60 min | garch11 | squared_standardized_residuals | Ljung-Box | 20 | 33.388286 | 20 | 0.0306 | sim |
| 60 min | garch11 | squared_standardized_residuals | Ljung-Box | 24 | 38.101769 | 24 | 0.0338 | sim |
| 60 min | garch11 | standardized_residuals | Ljung-Box | 10 | 8.762483 | 10 | 0.5548 | não |
| 60 min | garch11 | standardized_residuals | Ljung-Box | 20 | 17.338112 | 20 | 0.6309 | não |
| 60 min | garch11 | standardized_residuals | Ljung-Box | 24 | 24.014976 | 24 | 0.4607 | não |
| 1 dia | arch1 | squared_standardized_residuals | Ljung-Box | 10 | 18.545451 | 10 | 0.0464 | sim |
| 1 dia | arch1 | squared_standardized_residuals | Ljung-Box | 20 | 28.688496 | 20 | 0.0941 | não |
| 1 dia | arch1 | standardized_residuals | Ljung-Box | 10 | 10.509554 | 10 | 0.3970 | não |
| 1 dia | arch1 | standardized_residuals | Ljung-Box | 20 | 21.084908 | 20 | 0.3922 | não |
| 1 dia | constant | squared_standardized_residuals | Ljung-Box | 10 | 26.621088 | 10 | 0.0030 | sim |
| 1 dia | constant | squared_standardized_residuals | Ljung-Box | 20 | 41.259979 | 20 | 0.0034 | sim |
| 1 dia | constant | standardized_residuals | Ljung-Box | 10 | 9.983947 | 10 | 0.4419 | não |
| 1 dia | constant | standardized_residuals | Ljung-Box | 20 | 19.929005 | 20 | 0.4624 | não |
| 1 dia | fixed_arma_mean | innovations | ARCH-LM | 10 | 33.139639 | 10 | 0.0003 | sim |
| 1 dia | fixed_arma_mean | innovations | ARCH-LM | 20 | 54.427561 | 20 | 4.998e-05 | sim |
| 1 dia | garch11 | squared_standardized_residuals | Ljung-Box | 10 | 16.563835 | 10 | 0.0846 | não |
| 1 dia | garch11 | squared_standardized_residuals | Ljung-Box | 20 | 29.553695 | 20 | 0.0774 | não |
| 1 dia | garch11 | standardized_residuals | Ljung-Box | 10 | 9.882622 | 10 | 0.4509 | não |
| 1 dia | garch11 | standardized_residuals | Ljung-Box | 20 | 20.376664 | 20 | 0.4346 | não |

## Apêndice B — acurácia por faixa e grupo de gap

[Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/forecast_evaluation.py).

ARMA selecionado e benchmark zero são exibidos abaixo; a tabela pública de acurácia contém todos os comparadores. As decomposições são exploratórias, sem testes adicionais nem alteração de especificações.

| Escala | Exercício | Tipo | Grupo | Modelo | N | MSE | MAE | MSE/MSE zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 min | common_60min | gap_group | high | ARMA_BIC | 873 | 0.079154 | 0.197496 | 1.002113 |
| 1 min | common_60min | gap_group | high | ZERO | 873 | 0.078987 | 0.197411 | 1 |
| 1 min | common_60min | gap_group | low | ARMA_BIC | 1.026 | 0.070831 | 0.1854 | 1.002748 |
| 1 min | common_60min | gap_group | low | ZERO | 1.026 | 0.070637 | 0.185063 | 1 |
| 1 min | common_60min | time_band | fim | ARMA_BIC | 221 | 0.027277 | 0.111719 | 1.004357 |
| 1 min | common_60min | time_band | fim | ZERO | 221 | 0.027159 | 0.110301 | 1 |
| 1 min | common_60min | time_band | inicio | ARMA_BIC | 221 | 0.121734 | 0.258079 | 1.000993 |
| 1 min | common_60min | time_band | inicio | ZERO | 221 | 0.121613 | 0.257652 | 1 |
| 1 min | common_60min | time_band | meio | ARMA_BIC | 1.547 | 0.077399 | 0.196173 | 1.002032 |
| 1 min | common_60min | time_band | meio | ZERO | 1.547 | 0.077242 | 0.196215 | 1 |
| 1 min | native | gap_group | high | ARMA_BIC | 52.380 | 0.001456 | 0.025639 | 1.000339 |
| 1 min | native | gap_group | high | ZERO | 52.380 | 0.001456 | 0.025622 | 1 |
| 1 min | native | gap_group | low | ARMA_BIC | 61.560 | 0.001174 | 0.023348 | 1.000765 |
| 1 min | native | gap_group | low | ZERO | 61.560 | 0.001173 | 0.02332 | 1 |
| 1 min | native | time_band | fim | ARMA_BIC | 13.260 | 0.000573 | 0.014403 | 1.001556 |
| 1 min | native | time_band | fim | ZERO | 13.260 | 0.000572 | 0.014375 | 1 |
| 1 min | native | time_band | inicio | ARMA_BIC | 13.260 | 0.002068 | 0.033098 | 1.000345 |
| 1 min | native | time_band | inicio | ZERO | 13.260 | 0.002067 | 0.033078 | 1 |
| 1 min | native | time_band | meio | ARMA_BIC | 92.820 | 0.001306 | 0.024716 | 1.0005 |
| 1 min | native | time_band | meio | ZERO | 92.820 | 0.001306 | 0.024695 | 1 |
| 5 min | common_60min | gap_group | high | ARMA_BIC | 873 | 0.079136 | 0.197441 | 1.001895 |
| 5 min | common_60min | gap_group | high | ZERO | 873 | 0.078987 | 0.197411 | 1 |
| 5 min | common_60min | gap_group | low | ARMA_BIC | 1.026 | 0.07086 | 0.18543 | 1.003148 |
| 5 min | common_60min | gap_group | low | ZERO | 1.026 | 0.070637 | 0.185063 | 1 |
| 5 min | common_60min | time_band | fim | ARMA_BIC | 221 | 0.027255 | 0.111632 | 1.003555 |
| 5 min | common_60min | time_band | fim | ZERO | 221 | 0.027159 | 0.110301 | 1 |
| 5 min | common_60min | time_band | inicio | ARMA_BIC | 221 | 0.121718 | 0.258056 | 1.000858 |
| 5 min | common_60min | time_band | inicio | ZERO | 221 | 0.121613 | 0.257652 | 1 |
| 5 min | common_60min | time_band | meio | ARMA_BIC | 1.547 | 0.077413 | 0.196181 | 1.002218 |
| 5 min | common_60min | time_band | meio | ZERO | 1.547 | 0.077242 | 0.196215 | 1 |
| 5 min | native | gap_group | high | ARMA_BIC | 10.476 | 0.007321 | 0.057807 | 1.000142 |
| 5 min | native | gap_group | high | ZERO | 10.476 | 0.00732 | 0.057781 | 1 |
| 5 min | native | gap_group | low | ARMA_BIC | 12.312 | 0.00583 | 0.052744 | 1.000265 |
| 5 min | native | gap_group | low | ZERO | 12.312 | 0.005828 | 0.05272 | 1 |
| 5 min | native | time_band | fim | ARMA_BIC | 2.652 | 0.002951 | 0.033139 | 1.000227 |
| 5 min | native | time_band | fim | ZERO | 2.652 | 0.00295 | 0.033078 | 1 |
| 5 min | native | time_band | inicio | ARMA_BIC | 2.652 | 0.010737 | 0.077266 | 1.000068 |
| 5 min | native | time_band | inicio | ZERO | 2.652 | 0.010737 | 0.077239 | 1 |
| 5 min | native | time_band | meio | ARMA_BIC | 18.564 | 0.006476 | 0.055531 | 1.000184 |
| 5 min | native | time_band | meio | ZERO | 18.564 | 0.006475 | 0.055513 | 1 |
| 15 min | common_60min | gap_group | high | ARMA_BIC | 873 | 0.079136 | 0.197441 | 1.001895 |
| 15 min | common_60min | gap_group | high | ZERO | 873 | 0.078987 | 0.197411 | 1 |
| 15 min | common_60min | gap_group | low | ARMA_BIC | 1.026 | 0.07086 | 0.18543 | 1.003148 |
| 15 min | common_60min | gap_group | low | ZERO | 1.026 | 0.070637 | 0.185063 | 1 |
| 15 min | common_60min | time_band | fim | ARMA_BIC | 221 | 0.027255 | 0.111632 | 1.003555 |
| 15 min | common_60min | time_band | fim | ZERO | 221 | 0.027159 | 0.110301 | 1 |
| 15 min | common_60min | time_band | inicio | ARMA_BIC | 221 | 0.121718 | 0.258056 | 1.000858 |
| 15 min | common_60min | time_band | inicio | ZERO | 221 | 0.121613 | 0.257652 | 1 |
| 15 min | common_60min | time_band | meio | ARMA_BIC | 1.547 | 0.077413 | 0.196181 | 1.002218 |
| 15 min | common_60min | time_band | meio | ZERO | 1.547 | 0.077242 | 0.196215 | 1 |
| 15 min | native | gap_group | high | ARMA_BIC | 3.492 | 0.020321 | 0.096729 | 1.000461 |
| 15 min | native | gap_group | high | ZERO | 3.492 | 0.020311 | 0.096656 | 1 |
| 15 min | native | gap_group | low | ARMA_BIC | 4.104 | 0.016764 | 0.089955 | 1.00083 |
| 15 min | native | gap_group | low | ZERO | 4.104 | 0.01675 | 0.089907 | 1 |
| 15 min | native | time_band | fim | ARMA_BIC | 884 | 0.006763 | 0.054553 | 1.000893 |
| 15 min | native | time_band | fim | ZERO | 884 | 0.006757 | 0.054363 | 1 |
| 15 min | native | time_band | inicio | ARMA_BIC | 884 | 0.031902 | 0.13268 | 1.000204 |
| 15 min | native | time_band | inicio | ZERO | 884 | 0.031896 | 0.132605 | 1 |
| 15 min | native | time_band | meio | ARMA_BIC | 6.188 | 0.018418 | 0.093866 | 1.000582 |
| 15 min | native | time_band | meio | ZERO | 6.188 | 0.018408 | 0.09383 | 1 |
| 30 min | common_60min | gap_group | high | ARMA_BIC | 873 | 0.079136 | 0.197441 | 1.001895 |
| 30 min | common_60min | gap_group | high | ZERO | 873 | 0.078987 | 0.197411 | 1 |
| 30 min | common_60min | gap_group | low | ARMA_BIC | 1.026 | 0.07086 | 0.18543 | 1.003148 |
| 30 min | common_60min | gap_group | low | ZERO | 1.026 | 0.070637 | 0.185063 | 1 |
| 30 min | common_60min | time_band | fim | ARMA_BIC | 221 | 0.027255 | 0.111632 | 1.003555 |
| 30 min | common_60min | time_band | fim | ZERO | 221 | 0.027159 | 0.110301 | 1 |
| 30 min | common_60min | time_band | inicio | ARMA_BIC | 221 | 0.121718 | 0.258056 | 1.000858 |
| 30 min | common_60min | time_band | inicio | ZERO | 221 | 0.121613 | 0.257652 | 1 |
| 30 min | common_60min | time_band | meio | ARMA_BIC | 1.547 | 0.077413 | 0.196181 | 1.002218 |
| 30 min | common_60min | time_band | meio | ZERO | 1.547 | 0.077242 | 0.196215 | 1 |
| 30 min | native | gap_group | high | ARMA_BIC | 1.746 | 0.038929 | 0.137161 | 1.000962 |
| 30 min | native | gap_group | high | ZERO | 1.746 | 0.038892 | 0.137105 | 1 |
| 30 min | native | gap_group | low | ARMA_BIC | 2.052 | 0.03426 | 0.12897 | 1.001625 |
| 30 min | native | gap_group | low | ZERO | 2.052 | 0.034204 | 0.128907 | 1 |
| 30 min | native | time_band | fim | ARMA_BIC | 442 | 0.012181 | 0.075063 | 1.001985 |
| 30 min | native | time_band | fim | ZERO | 442 | 0.012157 | 0.074611 | 1 |
| 30 min | native | time_band | inicio | ARMA_BIC | 442 | 0.063129 | 0.183604 | 1.000413 |
| 30 min | native | time_band | inicio | ZERO | 442 | 0.063103 | 0.183451 | 1 |
| 30 min | native | time_band | meio | ARMA_BIC | 3.094 | 0.036699 | 0.135235 | 1.001168 |
| 30 min | native | time_band | meio | ZERO | 3.094 | 0.036656 | 0.135266 | 1 |
| 60 min | common_60min | gap_group | high | ARMA_BIC | 873 | 0.079136 | 0.197441 | 1.001895 |
| 60 min | common_60min | gap_group | high | ZERO | 873 | 0.078987 | 0.197411 | 1 |
| 60 min | common_60min | gap_group | low | ARMA_BIC | 1.026 | 0.07086 | 0.18543 | 1.003148 |
| 60 min | common_60min | gap_group | low | ZERO | 1.026 | 0.070637 | 0.185063 | 1 |
| 60 min | common_60min | time_band | fim | ARMA_BIC | 221 | 0.027255 | 0.111632 | 1.003555 |
| 60 min | common_60min | time_band | fim | ZERO | 221 | 0.027159 | 0.110301 | 1 |
| 60 min | common_60min | time_band | inicio | ARMA_BIC | 221 | 0.121718 | 0.258056 | 1.000858 |
| 60 min | common_60min | time_band | inicio | ZERO | 221 | 0.121613 | 0.257652 | 1 |
| 60 min | common_60min | time_band | meio | ARMA_BIC | 1.547 | 0.077413 | 0.196181 | 1.002218 |
| 60 min | common_60min | time_band | meio | ZERO | 1.547 | 0.077242 | 0.196215 | 1 |
| 60 min | native | gap_group | high | ARMA_BIC | 873 | 0.079136 | 0.197441 | 1.001895 |
| 60 min | native | gap_group | high | ZERO | 873 | 0.078987 | 0.197411 | 1 |
| 60 min | native | gap_group | low | ARMA_BIC | 1.026 | 0.07086 | 0.18543 | 1.003148 |
| 60 min | native | gap_group | low | ZERO | 1.026 | 0.070637 | 0.185063 | 1 |
| 60 min | native | time_band | fim | ARMA_BIC | 221 | 0.027255 | 0.111632 | 1.003555 |
| 60 min | native | time_band | fim | ZERO | 221 | 0.027159 | 0.110301 | 1 |
| 60 min | native | time_band | inicio | ARMA_BIC | 221 | 0.121718 | 0.258056 | 1.000858 |
| 60 min | native | time_band | inicio | ZERO | 221 | 0.121613 | 0.257652 | 1 |
| 60 min | native | time_band | meio | ARMA_BIC | 1.547 | 0.077413 | 0.196181 | 1.002218 |
| 60 min | native | time_band | meio | ZERO | 1.547 | 0.077242 | 0.196215 | 1 |
| 1 dia | native | gap_group | high | ARMA_BIC | 97 | 0.669926 | 0.605283 | 1.018289 |
| 1 dia | native | gap_group | high | ZERO | 97 | 0.657894 | 0.601763 | 1 |
| 1 dia | native | gap_group | low | ARMA_BIC | 114 | 0.817356 | 0.68989 | 1.022334 |
| 1 dia | native | gap_group | low | ZERO | 114 | 0.7995 | 0.684874 | 1 |
