# Relatório final — Seminário I (Modelos Univariados), EAD6034

**Autor:** Renan de Luca Avila · **Disciplina:** Econometria de Séries Temporais (EAD6034), PPGA/FEA-USP · **Professor:** Leandro dos Santos Maciel · **Apoio:** Prof. Anderson Dias Brito · **Data do seminário:** 28/09/2026 (máximo 15 minutos)

**Propósito deste documento:** consolidar, em um único relatório em Markdown, todo o conteúdo de pesquisa necessário para o Seminário I — dados, protocolo, resultados, diagnósticos e limitações — corrigindo as pendências identificadas em [`REVISAO_CRITICA_SEMINARIO_1.md`](REVISAO_CRITICA_SEMINARIO_1.md) sobre a entrega de 28/09 anterior (commit `ef21a78`), e reorganizando a narrativa em torno do eixo escolhido pelo autor (ver §A.0.1). Este relatório **substitui** o conteúdo daquele PDF como fonte de verdade; a Parte B, ao final, contém instruções autocontidas para que outra sessão de IA construa a apresentação em Beamer **do zero**, sem reaproveitar o `.tex` anterior como modelo de conteúdo.

**O que mudou nesta rodada, em relação à entrega anterior (28/09, commit `ef21a78`):**
1. A seleção do modelo médio agora é **condicionada a passar no teste de Ljung–Box** (exigência explícita do professor, não apenas BIC) — isso de fato mudou o modelo selecionado em 15 minutos (ver §A.4).
2. Erro-padrão e teste de significância de α e β agora são publicados para os modelos de variância selecionados, não apenas o resultado da comparação de BIC (§A.6). Uma extensão assimétrica (GJR-GARCH) foi tentada nesta rodada e **removida**: verificação direta do material da Aula 6 mostrou que ela aparece apenas de forma incompleta no script R de apoio (estimada e plotada, sem diagnóstico nem previsão), nunca no conteúdo teórico dos slides — que cobre somente ARCH(1)/GARCH(1,1) (Engle 1982; Bollerslev 1986). Mantida fora da análise por disciplina de escopo (§A.6).
3. RMSE, MAE e MAPE são calculados e reportados para os retornos, com tratamento explícito da indefinição do MAPE (§A.7).
4. **Nova seção central:** modelagem e comparação da **variância condicional entre escalas**, incluindo dois modelos neurais (MLP e Chronos-2 zero-shot) aplicados à variância, com a métrica QLIKE e testes de Diebold-Mariano válidos (não aninhados) entre GARCH e os modelos neurais (§A.9 — nova).
5. A comparação com o artigo de referência agora distingue explicitamente o que foi verificado factualmente do que não foi (§A.10).
6. Conclusões sobre KPSS, Diebold-Mariano (retornos) e integridade do holdout foram reescritas para não extrapolar além do que os testes efetivamente mostram.

### A.0.1 Eixo narrativo desta entrega (decisão do autor, 27/09/2026)

> "Vamos tentar prever os preços do WIN em diferentes escalas temporais. Os resultados mostram que os retornos não são linearmente previsíveis — e provavelmente são difíceis de prever mesmo com modelos não-lineares, já que redes neurais também não resolveram facilmente o problema. Então vamos abordar a modelagem da variância, comparando-a entre escalas temporais e também com redes neurais, para ver se a variância é, ao menos, previsível."

Esse é o fio condutor de todo o relatório e da apresentação: §A.4–A.5 estabelecem que a média não tem estrutura linear robusta (com uma exceção interessante em 15 minutos); §A.7–A.8 mostram que nem o MSE do modelo linear nem os baselines neurais superam o retorno zero de forma convincente; §A.9 então pivota para variância, mostra que ela **é** substancialmente mais previsível que a média em todas as escalas, compara essa previsibilidade entre as seis escalas, e situa os modelos neurais dentro dessa mesma comparação.

---

## Parte A — Conteúdo da pesquisa

### A.0 Como este documento se relaciona com o restante do repositório

- Requisitos do professor: [`context_resources/seminario_1_requisitos_do_professor.md`](context_resources/seminario_1_requisitos_do_professor.md) e o enunciado oficial (anexo à Aula 5, reproduzido em `context_resources/`).
- Revisão crítica que motivou as correções deste relatório: [`REVISAO_CRITICA_SEMINARIO_1.md`](REVISAO_CRITICA_SEMINARIO_1.md).
- As três entregas semanais anteriores (31/08, 14/09, 21/09) permanecem publicadas em `results/entrega_31_08*/`, `results/entrega_14_09/` e `results/entrega_21_09/` como versões **históricas**, com seus próprios protocolos — não foram recalculadas e não devem ser citadas como refletindo o protocolo atual.
- Todas as tabelas citadas abaixo estão em `results/entrega_28_09/tables/`; dados privados (preços, retornos individuais, variâncias por origem) permanecem em `results/entrega_28_09/private/`, não publicados.
- `golden_rules.md` (raiz do repositório) documenta os princípios metodológicos duráveis desta disciplina.

### A.1 Motivação, dados e relevância

**Por que prever o WIN.** O WIN (mini-contrato futuro de índice Ibovespa, B3) é um dos instrumentos futuros mais líquidos do varejo brasileiro. Sua dinâmica intradiária é relevante para gestão de risco (dimensionamento de posições, VaR intradiário) e para decisões de execução. Relevância econômica de modelar a série **não implica** rentabilidade demonstrada por nenhum modelo aqui testado.

**Fonte dos dados.** BTG Alpha Lab, dataset BTG-ATS-A26, candles de 1 minuto agregados de negócios da B3. [Landing page](https://alphalab.btgpactual.com/datasets/publication:7a74b3ae-90e0-4393-b1e0-01e61c0bedba); proveniência em `docs/DATA_SOURCE.md`. Cobertura: 04/01/2016 a 28/11/2025, WIN/WDO/DI1 — usa-se somente WIN. **Limitação estrutural:** o fornecedor seleciona, por dia, o contrato de maior volume no próprio dia — seleção retrospectiva que a recursão causal dos modelos não desfaz.

**Horizonte preditivo e sua justificativa.** Seis escalas (1, 5, 15, 30, 60 minutos, diário open-to-close); alvo comum de comparação entre as cinco escalas intradiárias: retorno futuro (ou, na Parte 2 da análise, variância realizada futura) de **60 minutos**. Duas justificativas distintas:

1. **Comparabilidade estatística:** para comparar erro de previsão entre modelos ajustados em escalas diferentes, é necessário que todos prevejam exatamente o mesmo alvo futuro realizado.
2. **Relevância prática:** uma hora é uma janela operacionalmente significativa para decisões de execução/risco intradiário — mas o estudo não simula nenhuma estratégia de negociação nem estima custo de transação; a relevância aqui é qualitativa.

### A.2 Protocolo metodológico

**Amostra e janela.** Sessão 09:05–18:05 (São Paulo), 540 minutos. Retornos logarítmicos em %, sem overnight. Um dia só entra se todos os minutos da janela estiverem observados.

**Divisão amostral — 80/20 mecânico.** 467 pregões completos (02/01/2024–28/11/2025). Regra de contagem, fixada **antes** de examinar qualquer resultado no novo trecho de teste: primeiros 374 pregões (80,1%) = treino (até **15/07/2025**); 93 restantes = teste (**16/07/2025** a 28/11/2025). Atende à orientação do Prof. Anderson Brito (22/09/2026) e à referência da Aula 4 ("~80% in / 20% out").

**Honestidade sobre o holdout.** O novo teste (16/07–28/11/2025) é um **subconjunto** do 2025 já examinado em 21/09. A regra de corte é mecânica (não escolhida por parecer melhor), o que evita garimpagem de especificação, mas **não restaura um holdout nunca observado**. Propriedades distintas, não mutuamente implicadas: corte mecânico (satisfeita) · estimação sem o novo teste (satisfeita) · estados atualizados causalmente (satisfeita) · ausência de exposição prévia do pesquisador ao período (**não satisfeita**).

**Classificação determinística.** Retornos, não níveis — constante, **sem tendência determinística**, **d=0**. Sustentado por ADF/PP rejeitando raiz unitária em todas as especificações (§A.3), não imposto a priori.

### A.3 Estacionariedade

**Interpretação das hipóteses:** ADF/PP — H0 = raiz unitária; rejeitar é evidência **contra** raiz unitária, não prova de estacionariedade. KPSS — H0 = estacionariedade; não rejeitar **não prova** estacionariedade.

**Resultados** (treino, n conforme escala; `tables/stationarity.csv`): ADF (3 especificações: sem constante/deriva/tendência; até 12 defasagens, BIC) e Phillips-Perron (Z-tau; bandas curta/longa de Schwert 1989) **rejeitam raiz unitária nas seis escalas e em todas as especificações** (p < 0,001). KPSS (mu e tau; bandas curta/longa) **não rejeita estacionariedade em nenhum caso** (todos p > 0,05; ex. 1 min: KPSS-mu p=0,675–0,686, KPSS-tau p=0,472–0,487).

**Sobre a divergência da entrega anterior:** sob a divisão anterior (~50/50), KPSS-tau rejeitava em todas as escalas. Sob a atual (80/20, mais treino, outra convenção de bandwidth para PP/KPSS), essa rejeição não se repete. Formulação correta: a configuração atual produz concordância entre os três testes; a anterior, com outra amostra/especificação, não produzia. Evidencia **sensibilidade da conclusão à amostra e à especificação** — não que "mais dados resolveram" ou "consertaram" algo.

**Estatística descritiva** (treino; `tables/descriptive.csv`, todos os valores em %):

| Escala | n | Média | DP | Mín | Q1 | Mediana | Q3 | Máx | Zero-share* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 min | 201.960 | −0,0001 | 0,0344 | −0,825 | −0,0162 | 0,0000 | 0,0160 | 1,294 | 6,55% |
| 5 min | 40.392 | −0,0003 | 0,0770 | −1,015 | −0,0388 | 0,0000 | 0,0384 | 2,132 | 2,78% |
| 15 min | 13.464 | −0,0009 | 0,1301 | −1,121 | −0,0664 | 0,0000 | 0,0636 | 1,761 | 1,69% |
| 30 min | 6.732 | −0,0018 | 0,1826 | −1,543 | −0,0942 | 0,0000 | 0,0895 | 1,560 | 1,26% |
| 60 min | 3.366 | −0,0035 | 0,2607 | −2,034 | −0,1362 | −0,0036 | 0,1263 | 1,937 | 0,80% |
| Diário OC | 374 | −0,0313 | 0,8451 | −3,462 | −0,5396 | −0,0331 | 0,4944 | 2,679 | 0,00% |

\* *`zero_share` = proporção de retornos **exatamente iguais a zero** (`mean(y==0)`), não "barras sem negócio" — negócios podem ocorrer sem alteração de preço.*

### A.4 Identificação, estimação e diagnóstico da média (Box–Jenkins)

**Grade de candidatos.** Todos os ARMA(p,q), p,q ∈ {0,...,5}, máxima verossimilhança gaussiana exata, seleção primária por BIC (k=p+q+2).

**Exigência adicional do professor: o modelo apresentado deve passar no teste de Ljung–Box**, não apenas vencer por BIC. Implementado como um segundo critério, **aplicado além do BIC**: entre os candidatos elegíveis (mesmo espaço p,q≤5), seleciona-se o de menor BIC cujos resíduos não rejeitem ausência de autocorrelação em **nenhum** dos horizontes pré-registrados (10, 12, 20, 24, 60, conforme o tamanho amostral permita) — critério não seletivo por defasagem (exige p>0,05 em **todos** os horizontes testados, não em um escolhido a posteriori).

**Resultado do filtro** (`tables/ljungbox_gate.csv`):

| Escala | BIC irrestrito | Satisfeito por algum candidato? | Candidatos verificados | Modelo final | Custo de BIC | p mínimo entre horizontes |
|---|---|---|---:|---|---:|---:|
| 1 min | ARMA(0,0) | **Não** | 36/36 | ARMA(0,0) (BIC puro, sem alternativa) | — | 3,54×10⁻²¹ |
| 5 min | ARMA(0,0) | **Não** | 36/36 | ARMA(0,0) (BIC puro, sem alternativa) | — | 5,71×10⁻⁸ |
| 15 min | ARMA(0,0) | **Sim** | 14/36 | **ARMA(3,3)** | +34,56 | 0,0528 |
| 30 min | ARMA(0,0) | Sim (imediato) | 1/36 | ARMA(0,0) | 0,00 | 0,268 |
| 60 min | ARMA(0,0) | Sim (imediato) | 1/36 | ARMA(0,0) | 0,00 | 0,058 |
| Diário OC | ARMA(0,0) | Sim (imediato) | 1/36 | ARMA(0,0) | 0,00 | 0,099 |

**1 e 5 minutos: nenhum candidato ARMA(p≤5,q≤5) passa em todos os horizontes** — nem mesmo o maior modelo da grade, ARMA(5,5): o melhor p-valor mínimo alcançável em toda a grade é 4,27×10⁻¹³ (1 min) e 4,12×10⁻³ (5 min). Ver interpretação em §A.5.1 — isto é tratado como um resultado substantivo, não uma falha de busca.

**15 minutos — equação ajustada** (ARMA(3,3) com constante, retornos em %):

```math
r_t = -0{,}000886 - 0{,}064837\,r_{t-1} + 0{,}085674\,r_{t-2} + 0{,}952075\,r_{t-3} + \varepsilon_t + 0{,}071864\,\varepsilon_{t-1} - 0{,}094538\,\varepsilon_{t-2} - 0{,}945738\,\varepsilon_{t-3}
```

**Significância dos coeficientes** (`tables/coefficient_significance.csv`, `cov_type="robust"`; |t|>1,96 = significativo a 5%, Aula 4):

| Parâmetro | Estimativa | Erro-padrão | t | p | Significativo? |
|---|---:|---:|---:|---:|---|
| const | −0,000886 | 0,001307 | −0,68 | 0,498 | Não |
| ar.L1 | −0,064837 | 0,027622 | −2,35 | 0,019 | **Sim** |
| ar.L2 | 0,085674 | 0,026956 | 3,18 | 0,001 | **Sim** |
| ar.L3 | 0,952075 | 0,026782 | 35,55 | ≈0 | **Sim** |
| ma.L1 | 0,071864 | 0,029571 | 2,43 | 0,015 | **Sim** |
| ma.L2 | −0,094538 | 0,028771 | −3,29 | 0,001 | **Sim** |
| ma.L3 | −0,945738 | 0,028340 | −33,37 | ≈0 | **Sim** |

Ao contrário do padrão em todas as outras escalas (abaixo), aqui os **seis** coeficientes AR/MA são individualmente significativos — 15 minutos é a única escala com estrutura linear ao mesmo tempo detectável por BIC (com o filtro de diagnóstico), estatisticamente significativa e com resíduos que não rejeitam ausência de autocorrelação. Isso não deve ser lido como "15 minutos é a escala previsível": o ganho preditivo fora da amostra continua próximo de zero (§A.7) — o que este resultado mostra é presença de dependência linear residual **removível e estatisticamente real**, não necessariamente **útil para previsão**, distinção discutida em §A.7.

Nas demais escalas (0,0 selecionado, sem alternativa aprovada em 1/5 min; 0,0 aprovado diretamente em 30/60 min/diário), a equação da média é simplesmente `r_t = μ̂ + ε_t`, com μ̂ = −0,000059 (1 min), −0,000293 (5 min), −0,001756 (30 min), −0,003512 (60 min), −0,031269 (diário) — e, para os comparadores restritos obrigatórios (AR(1)/MA(1)), o único coeficiente extra **nunca é individualmente significativo em nenhuma dessas cinco escalas** (|t| entre 0,03 e 0,85, p entre 0,40 e 0,98 — ver `coefficient_significance.csv`).

### A.5 Diagnóstico residual completo

`tables/mean_diagnostics.csv`, modelo final (pós-filtro) por escala, todos os horizontes testados:

| Escala | h=10 | h=12 | h=20 | h=24 | h=60 |
|---|---:|---:|---:|---:|---:|
| 1 min | 4,2×10⁻⁹ | 2,2×10⁻¹⁰ | 3,6×10⁻¹⁷ | 9,7×10⁻¹⁸ | 3,5×10⁻²¹ |
| 5 min | 1,9×10⁻⁷ | 1,7×10⁻⁷ | 5,7×10⁻⁸ | 1,4×10⁻⁷ | 8,7×10⁻⁶ |
| 15 min | 0,0528 | 0,0965 | 0,317 | 0,445 | 0,336 |
| 30 min | 0,681 | 0,831 | 0,611 | 0,478 | 0,268 |
| 60 min | 0,663 | 0,366 | 0,366 | 0,058 | 0,494 |
| Diário OC | 0,339 | 0,350 | 0,113 | 0,099 | 0,251 |

(células = p-valor de Ljung–Box; **negrito conceitual**: 1 e 5 min rejeitam em todos os cinco horizontes, sem exceção; as demais escalas não rejeitam em nenhum.)

#### A.5.1 Interpretação — 1 e 5 minutos

Nenhum ARMA(p≤5,q≤5) remove a dependência residual nessas duas escalas. A interpretação correta **não é** que a análise falhou, mas que **a dependência residual nessas frequências não é removível por um modelo linear de baixa ordem** — consistente com ruído de microestrutura (bid-ask bounce, discretização, agrupamento de negócios) — hipótese interpretativa, não demonstrada causalmente (sem dados de bid/ask ou agressor). Ampliar a ordem além de 5 apenas para forçar uma passagem seria o mesmo problema que o professor advertiu contra (escolher a defasagem do teste para conseguir p>0,05), aplicado agora ao espaço de busca do modelo.

### A.6 Modelagem da variância condicional — primeira parte (por escala)

Estimação **sequencial**: a média é fixada (pós-filtro de Ljung–Box, §A.4); os modelos de variância (constante, ARCH(1), GARCH(1,1)) são ajustados aos resíduos dessa média fixa, selecionados por BIC (só parâmetros de variância). **Nenhuma especificação de variância altera a previsão pontual do retorno.**

**Por que não uma extensão assimétrica (GJR-GARCH/EGARCH).** Uma variante GJR-GARCH (Glosten-Jagannathan-Runkle 1993, efeito alavancagem) foi implementada e testada nesta rodada, e depois **removida por disciplina de escopo**: a leitura direta das 32 páginas do slide `Aula6.pdf` mostra que o conteúdo teórico ensinado cobre **somente** ARCH(1) (Engle 1982) e GARCH(1,1) (Bollerslev 1986) — condição de persistência, teste ARCH-LM, diagnóstico de Ljung-Box nos resíduos padronizados e ao quadrado, um exemplo numérico completo. GJR-GARCH não aparece em nenhum slide, com fórmula ou sem ela. A bibliografia da própria aula cita Nelson (1991) — o artigo do EGARCH — mas sem qualquer discussão de EGARCH no conteúdo. O script R de apoio da mesma aula (`ScriptAula6.R`) chega a especificar e estimar um modelo `gjrGARCH` (via `rugarch`) para duas séries reais, mas **sem** aplicar diagnóstico ou gerar previsão sobre ele — ao contrário do GARCH(1,1) simples, tratado por completo no mesmo script. Ou seja: GJR-GARCH está presente de forma incompleta no código de apoio da aula, mas não no conteúdo teórico dos slides. Diante da exigência do trabalho de usar "modelos das aulas", a especificação assimétrica foi descartada da análise, mantendo-se apenas constante/ARCH(1)/GARCH(1,1) — o conteúdo efetivamente ensinado.

**Seleção e persistência** (`tables/variance_models.csv`):

| Escala | Variância BIC | α | β | α+β | α (p) | β (p) |
|---|---|---:|---:|---:|---:|---:|
| 1 min | GARCH(1,1) | 0,0775 | 0,9108 | 0,988 | ≈0 | ≈0 |
| 5 min | GARCH(1,1) | 0,1594 | 0,7654 | 0,925 | 1,6×10⁻²⁴ | ≈0 |
| 15 min | GARCH(1,1) | 0,1767 | 0,5741 | 0,751 | 1,2×10⁻¹⁸ | 2,3×10⁻⁴⁹ |
| 30 min | GARCH(1,1) | 0,1658 | 0,3915 | 0,557 | 6,5×10⁻¹² | 1,4×10⁻¹³ |
| 60 min | ARCH(1) | 0,1457 | — | 0,146 | 5,2×10⁻⁴ | — |
| Diário OC | Constante | — | — | 0,000 | — | — |

α e β (onde aplicável) são altamente significativos em todas as escalas (`alpha_pvalue`/`beta_pvalue` em `variance_models.csv`) — a estrutura GARCH em si é robusta.

**Por que não há Diebold-Mariano entre constante/ARCH/GARCH.** Hierarquia aninhada — constante ⊂ ARCH(1) ⊂ GARCH(1,1), cada uma a próxima com um parâmetro em zero — e a Aula 4 ensina explicitamente que DM não é apropriado para modelos aninhados. Isso muda em §A.9: MLP e Chronos **não são aninhados** em relação ao GARCH, então DM entre eles é válido e foi computado.

### A.7 Previsão fora da amostra dos retornos: horizonte, métricas e resultados

**One-step vs. multi-step, explicitamente:**

| Avaliação | Escala do modelo | Esquema |
|---|---|---|
| Próxima barra nativa | Todas | *One-step-ahead* da própria escala |
| Retorno comum de 60 min | 1 / 5 / 15 / 30 min | Soma de uma trajetória de 60 / 12 / 4 / 2 passos futuros, mesma origem |
| Retorno comum de 60 min | 60 min | *One-step-ahead* (nativo = comum) |

Origem sempre a mesma dentro de uma trajetória; nunca se inserem retornos intermediários realizados ("previsão encavalada com previsão" não ocorre). Os 837 alvos horários comuns **não se sobrepõem**. Diário (open-to-close) é outro alvo, fora do ranking intradiário comum.

**RMSE, MAE, MAPE — alvo comum de 60 min** (`tables/accuracy.csv`, modelo final por escala):

| Escala | n | RMSE | MAE | MAPE | MSE/zero |
|---|---:|---:|---:|---|---:|
| 1 min | 837 | 0,2592 | 0,1807 | indefinido (ver abaixo) | 1,00136 |
| 5 min | 837 | 0,2592 | 0,1807 | indefinido | 1,00136 |
| 15 min | 837 | 0,2592 | 0,1810 | indefinido | 1,00168 |
| 30 min | 837 | 0,2592 | 0,1807 | indefinido | 1,00136 |
| 60 min | 837 | 0,2592 | 0,1807 | 99,6% (n=829, 8 excluídos) | 1,00136 |

**MAPE, tratamento explícito.** Fórmula: `MAPE = 100/N · Σ|（r_t − r̂_t)/r_t|`, indefinida quando `r_t=0`. No alvo comum de 60 minutos, o denominador é a **soma de retornos de 60 minutos** (não retornos individuais); em 60 min nativo=comum, 8 das 837 observações têm soma realizada exatamente zero (excluídas, não substituídas por epsilon). Nas quatro escalas mais finas, o efeito é mais severo: como o alvo comum de 60 min é uma **soma** de vários passos, alguns pontos ficam muito próximos de zero por cancelamento parcial, e o MAPE explode numericamente — por exemplo, em 5 minutos o MAPE calculado sobre esse alvo chega a **2×10¹²%**. Esse número **não é um erro de cálculo**: é a demonstração concreta de por que o MAPE convencional é inadequado para um alvo de soma de retornos financeiros perto de zero, e por isso reportado apenas qualitativamente (indefinido/instável) nessas quatro escalas, com o valor de 60 minutos nativo como a única leitura numericamente estável.
No horizonte **nativo** (1 passo, todas as escalas, sem soma), o MAPE fica em torno de 99,6%–101,3% em todas as seis escalas — um valor que se aproxima de 100% quase independentemente da qualidade do modelo, porque a previsão está sempre perto de zero: também pouco informativo, mas ao menos numericamente estável, ao contrário do caso do alvo somado.

**Figura realizado vs. previsto.** `results/entrega_28_09/figures/09_real_vs_previsto_60min.pdf`: retorno realizado no teste e previsão do modelo (constante, para as escalas com ARMA(0,0)) ao longo das 837 barras de 60 minutos. Linha quase horizontal é o comportamento **esperado**, não um erro de geração.

**Diebold-Mariano — o que o teste publicado mostra** (`tables/diebold_mariano.csv`, alvo comum): comparação pré-registrada é **AR(1) puro vs. MA(1) puro**, não ARMA selecionado vs. zero. Nenhum p rejeita a 5% (1 min: p=0,664/0,697; 5 min: p=0,249/0,315; 15 min: p=0,413/0,478; 30 min: p=0,189/0,217; 60 min: p=0,398/0,455 — perdas quadrática/absoluta respectivamente). "Não se rejeita igualdade da perda esperada entre AR e MA" **não permite concluir** ausência de diferença entre o modelo selecionado e o retorno zero — essa comparação não foi testada formalmente, é apenas descritiva via razão de MSE (≈1,0014–1,0017, ou seja, 0,14%–0,17% mais MSE que zero, não pontos percentuais de retorno).

### A.8 Extensões exploratórias de retorno (MLP, Chronos) — fechando o capítulo "retornos são difíceis de prever"

Fora do escopo central (ARIMA + modelo alternativo, já satisfeito por AR/MA/combinação), mantidas como apêndice claramente rotulado:

- **MLP** (nomeado como classe de benchmark na Aula 4): 30 defasagens → 1 retorno futuro, hiperparâmetros por validação cronológica na cauda do treino, reajustado em treino+validação antes do teste. Nativo, 1 min: **MSE/zero = 1,0051**; DM vs. zero: p=0,102 (não significativo).
- **Chronos-2 zero-shot** ("Deep Learning", sem ajuste): 837 origens comuns de 60 min, contexto de 512 retornos passados. **MSE/zero = 1,126**; DM vs. zero: **p=0,0028** (significativamente **pior** que zero).

**Conclusão do capítulo de retornos:** nem o BIC/Ljung-Box (linear), nem o MLP (não-linear leve), nem um modelo de fundação pré-treinado (não-linear, zero-shot) batem de forma convincente o retorno zero nesta série, nesta janela. Isso motiva a pergunta central da próxima seção.

### A.9 Modelagem e comparação da variância entre escalas — incluindo redes neurais (seção central)

**Motivação.** Dado que a média não mostra estrutura linear robusta em quatro das seis escalas, e que abordagens não-lineares leves (MLP) e um modelo de fundação (Chronos, zero-shot) não resolvem isso facilmente (§A.8), a pergunta desloca-se: **a variância condicional é mais previsível que a média, e essa previsibilidade muda entre escalas e entre classes de modelo?**

**Desenho experimental — alvo comum de variância realizada.** Espelhando exatamente o desenho de retornos (§A.7), define-se, nas mesmas 837 origens horárias não sobrepostas de cada escala intradiária, a **variância realizada** no próximo intervalo de 60 minutos como a soma dos quadrados dos retornos realizados nesse intervalo (proxy padrão, estilo Andersen-Bollerslev) — e compara-se contra ela a soma, no mesmo intervalo, da trajetória de variância condicional **de um passo** de cada modelo (h_t do GARCH/ARCH já estimado em §A.6; ou a previsão do modelo neural correspondente). Métrica primária: **QLIKE** (`realizado/previsto − log(realizado/previsto) − 1`, Patton 2011) — o critério padrão da literatura para previsão de variância, robusto a heterocedasticidade e mais apropriado que o MSE para um alvo estritamente positivo e caududo pesado; MSE reportado como métrica secundária.

**Resultado central — a variância é substancialmente mais previsível que a média, em todas as escalas** (`tables/variance_common_horizon_accuracy.csv`; razões em relação ao modelo de variância constante):

| Escala | Modelo BIC | MSE/constante | QLIKE/constante |
|---|---|---:|---:|
| 1 min | GARCH(1,1) | **0,350** | **0,131** |
| 5 min | GARCH(1,1) | 0,386 | 0,402 |
| 15 min | GARCH(1,1) | 0,647 | 0,687 |
| 30 min | GARCH(1,1) | 0,868 | 0,857 |
| 60 min | ARCH(1) | 0,981 | 0,987 |

Ganho de GARCH/ARCH sobre a variância constante é grande em 1 minuto (queda de 87% no QLIKE!) e **diminui monotonicamente com a escala**, ficando marginal em 60 minutos (~1,3%). Isto é o oposto do padrão encontrado para a média (§A.4–A.5, onde 1/5 min eram as escalas problemáticas) — a variância condicional é mais previsível justamente nas escalas mais finas, onde a média não tinha estrutura linear utilizável.

**Redes neurais na variância (1 minuto, mesmo alvo de 60 min comum):**

| Modelo | MSE/constante | QLIKE/constante | Observação |
|---|---:|---:|---|
| GARCH(1,1) | 0,350 | 0,131 | referência |
| **MLP** (lags de retorno² → retorno² futuro) | **0,274** | 0,407 | menor MSE, maior QLIKE |
| **Chronos-2 zero-shot** (série de retorno², sem ajuste) | 1,308 | 21,89 | pior que a variância constante |

O MLP (mesma disciplina de validação/reajuste do §A.8, aplicada à série de retornos ao quadrado) tem **MSE menor** que o GARCH(1,1), mas **QLIKE muito maior** — uma divergência real e interessante entre métricas, não um erro: o MLP provavelmente comete alguns erros grandes em valores de variância realizada muito pequenos (onde QLIKE penaliza desproporcionalmente), enquanto acerta melhor em média quadrática simples. O Chronos zero-shot, aplicado à série de quadrados dos retornos sem qualquer ajuste, é **pior que a variância constante** em ambas as métricas — consistente com seu desempenho fraco também nos retornos (§A.8).

**Teste de Diebold-Mariano — agora válido, pois os pares não são aninhados** (GARCH vs. MLP e vs. Chronos são classes de modelo genuinamente diferentes; ao contrário de §A.6, aqui DM se aplica; usa-se QLIKE como a perda pré-especificada, comparada diretamente pela extensão `loss="precomputed"` de `diebold_mariano()`):

| Comparação | Diferença média de QLIKE | Estatística | p-valor | Conclusão a 5% |
|---|---:|---:|---:|---|
| GARCH(1,1) vs. MLP | −0,119 | −23,84 | 3,2×10⁻⁹⁶ | GARCH significativamente melhor |
| GARCH(1,1) vs. Chronos zero-shot | −9,38 | −2,16 | 0,031 | GARCH significativamente melhor |
| MLP vs. Chronos zero-shot | −9,26 | −2,14 | 0,033 | MLP significativamente melhor |

**Síntese da seção:** pela métrica apropriada para variância (QLIKE), **o GARCH(1,1) clássico supera significativamente ambas as alternativas neurais** nesta série — um resultado que, ao contrário do capítulo de retornos, favorece o modelo econométrico tradicional sobre as extensões de aprendizado de máquina, mesmo quando o MLP parece competitivo pelo MSE bruto. A variância é previsível — muito mais que a média —, mas essa previsibilidade decresce com a escala e não é mais bem capturada por modelos neurais leves ou por um modelo de fundação zero-shot do que pelo GARCH.

**Limitações desta seção:** avaliação em uma única escala-fonte para os modelos neurais (1 minuto, por orçamento computacional); QLIKE herda a mesma calibração assintótica aproximada do restante do estudo (sem correção robusta a heterocedasticidade arbitrária); nenhuma simulação de estratégia usando a variância prevista (ex. dimensionamento de posição) foi realizada.

### A.10 Comparação com o artigo de referência

**Referência:** Matías, J. M.; Reboredo, J. C. (2012). "Forecasting performance of nonlinear models for intraday stock returns." *Journal of Forecasting*, 31(2), 172–188. DOI: [10.1002/for.1218](https://doi.org/10.1002/for.1218).

**Aviso de verificação.** As afirmações abaixo foram checadas contra buscas na web em 27/09/2026 (resumos indexados/abstract, não o texto completo, que está atrás de paywall); cada linha traz seu nível de confiança. **Cuidado:** existe um artigo-irmão de fácil confusão — Reboredo, Matías & García-Rubio (2012), "Nonlinearity in Forecasting of High-Frequency Stock Returns," *Computational Economics* 40(3), 245–264 — mesmos autores principais, mesmo ano, mesmo ativo (S&P 500), mas revista, lista de modelos, horizontes e critério econômico diferentes. As linhas marcadas "não verificado" abaixo frequentemente aparecem atribuídas ao artigo errado em buscas superficiais.

| Dimensão | Matías & Reboredo (2012), J. of Forecasting | Confiança | Este estudo (WIN) |
|---|---|---|---|
| Ativo/mercado | S&P 500, série única | **Alta** (abstract, múltiplas fontes) | Mini-índice Ibovespa (WIN), B3 |
| Frequência/período/tamanho da amostra | Não encontrado | — | 1 min agregado; treino 2024–jul/2025 (374 pregões), teste jul–nov/2025 (93 pregões) |
| Modelos | Lineares: AR, random walk. Não-lineares: STAR, Markov-switching, ANN, regressão kernel não paramétrica, SVM | **Alta** | Lineares: ARIMA/AR/MA + combinação. Variância: ARCH/GARCH. Exploratório: MLP, Chronos-2 (zero-shot) |
| Horizontes | 5, 10, 20, 30, 60 minutos | **Alta** | 1 min a 1 dia (nativo); alvo comum de 60 min |
| Critério estatístico | Inferido: medidas de erro convencionais + Diebold-Mariano | **Média** (não é uma citação direta do método, é inferência da lista de referências) | MSE/MAE/RMSE/MAPE vs. zero; QLIKE para variância; Diebold-Mariano (retornos: AR vs MA; variância: GARCH vs. redes neurais) |
| Critério econômico | Inferido como próximo a Leitch-Tanner (lucro/direção); **não confirmado** se há simulação de estratégia com custos de transação ou Sharpe | **Baixa-média** | Nenhum — nenhuma estratégia, custo ou Sharpe nesta análise |
| Resultado central | Modelos não-lineares superam os lineares em critérios estatísticos **e** econômicos; previsibilidade (segundo os modelos não-lineares) persiste até 60 min mesmo com a correlação serial simples desaparecendo perto de 10 min; lucratividade cai com o horizonte; **SVM e ANN não superam claramente os demais não-lineares** | **Alta** (frase do abstract, reproduzida identicamente em múltiplas buscas) | Nenhum modelo (linear, MLP ou Chronos) supera o retorno zero de forma convincente/significativa; a variância, ao contrário, é substancialmente previsível em todas as escalas, com GARCH superando os modelos neurais |
| Alcance econômico | Critério econômico mencionado, mecanismo exato não confirmado para este artigo específico | — | Nenhuma simulação de estratégia/custos |

**Leitura comparativa.** O achado central de Matías & Reboredo — que modelos não-lineares (mesmo sem ser os mais flexíveis, como SVM/ANN) melhoram a previsão da **média** dos retornos intradiários do S&P 500 — **não se repete** neste estudo para o WIN: nem o MLP nem o Chronos batem o retorno zero de forma significativa (§A.8). Isso pode refletir diferenças de ativo/mercado, período, protocolo de avaliação (o estudo de referência usa métricas diferentes e não usa um alvo comum entre escalas da mesma forma), ou genuína diferença na estrutura de dependência. **Não se deve concluir**, a partir de uma única série e uma janela específica, que o resultado do artigo esteja "errado" ou que o mercado brasileiro seja mais eficiente — apenas que os resultados não se replicam automaticamente entre ativos/mercados/protocolos.

**Disciplina de escopo.** Métodos das aulas continuam sendo a restrição prioritária: ARCH/GARCH ligam-se diretamente à Aula 6 (Engle 1982; Bollerslev 1986); uma extensão assimétrica (GJR-GARCH) foi considerada e descartada por não estar no conteúdo teórico da aula (§A.6); MLP é citado como classe de benchmark na Aula 4 (mas isso não valida automaticamente qualquer arquitetura/protocolo específico); Chronos zero-shot é extensão exploratória sem ligação às aulas.

### A.11 Limitações gerais

- Seleção retrospectiva do contrato ativo pelo fornecedor — não identificável causalmente nem replicável em tempo real.
- Filtro de dias completos é retrospectivo e condiciona a amostra avaliada.
- Holdout de teste se sobrepõe a dados já examinados na entrega de 21/09 (§A.2).
- Nenhuma simulação de estratégia de negociação, custo de transação ou execução, inclusive para a variância (§A.9) — resultados não implicam viabilidade econômica.
- Recortes por faixa horária e por magnitude de gap (relatório completo) são descritivos, não testes formais.
- Resultado restrito a um ativo, uma janela amostral e um conjunto específico de modelos.
- QLIKE e Ljung-Box usam calibração assintótica convencional, não robusta a heterocedasticidade arbitrária.
- Avaliação neural da variância limitada a uma escala-fonte (1 minuto) por orçamento computacional.

### A.12 Síntese preditiva final

Ao comparar a previsão de preços/retornos do WIN em seis escalas temporais, a média condicional mostrou-se, no melhor caso, marginalmente diferente do retorno zero (razões de MSE entre 1,0014 e 1,0017 no alvo comum de 60 minutos), sem diferença estatisticamente significativa entre os comparadores lineares testados (AR vs. MA, p>0,18 em todas as escalas) — e nem um MLP nem um modelo de fundação zero-shot (Chronos-2) mudaram esse quadro, com o segundo tendo desempenho **significativamente pior** que o retorno zero (p=0,0028). Em duas das seis escalas (1 e 5 minutos), nenhum modelo ARMA(p≤5,q≤5) sequer passou no diagnóstico de Ljung-Box exigido — um resultado honesto sobre os limites de modelos lineares de baixa ordem nessas frequências, não uma falha de busca. Em 15 minutos, um ARMA(3,3) com todos os coeficientes individualmente significativos passou no diagnóstico, mas com custo relevante de BIC e sem tradução em ganho preditivo fora da amostra.

Diante disso, a análise pivotou para a variância condicional, seguindo a sugestão de que ela seria mais previsível que a média. **Essa hipótese foi confirmada de forma robusta**: GARCH(1,1)/ARCH(1) reduzem o MSE e o QLIKE da variância entre 1,3% (60 min) e 87% (1 min, por QLIKE) em relação à variância constante, em todas as seis escalas — com a previsibilidade concentrada justamente nas escalas mais finas, onde a média não mostrava estrutura útil. Quando comparados diretamente contra o GARCH(1,1) na mesma tarefa (1 minuto, alvo comum de 60 min), nem o MLP nem o Chronos zero-shot superaram o modelo clássico pela métrica apropriada (QLIKE; diferenças estatisticamente significativas via Diebold-Mariano, p<0,04 em ambos os casos) — embora o MLP tenha exibido menor MSE bruto, uma divergência de métricas discutida explicitamente, não ocultada.

Os resultados não identificam causalmente efeitos de leilões, não demonstram eficiência ou ineficiência geral de mercado, e não avaliam viabilidade econômica líquida de custos — são restritos a um ativo, uma janela amostral e o conjunto de modelos aqui especificado.
## Parte B — Instruções para outra sessão de IA construir a apresentação (Beamer, do zero)

**Leia isto por completo antes de escrever qualquer `.tex`.** Você está construindo uma apresentação nova, não editando `results/entrega_28_09/ENTREGA_28_09.tex` — esse arquivo é uma versão anterior já identificada como tendo problemas de rigor (ver `REVISAO_CRITICA_SEMINARIO_1.md`) e não deve ser reaproveitada como fonte de conteúdo. Você pode olhá-lo apenas como referência de **estilo visual** (cores, macros do Beamer — navy/teal/orange, `\tagline`, `\source`), nunca como fonte de números ou de texto. Todo o conteúdo vem de [`RELATORIO_FINAL_SEMINARIO_1.md`](RELATORIO_FINAL_SEMINARIO_1.md) (Parte A).

### B.1 Eixo narrativo (não é opcional — é a estrutura pedida pelo autor)

"Vamos tentar prever os preços do WIN em diferentes escalas → os retornos não são linearmente previsíveis, e nem redes neurais resolvem isso facilmente → então modelamos a variância, comparando-a entre escalas e com redes neurais, para ver se ao menos ela é previsível." A apresentação deve seguir esse arco em duas partes claras (retornos → variância), com os requisitos obrigatórios do professor (§B.3) tecidos ao longo do caminho, não relegados a um apêndice — ver a estrutura sugerida em §B.4.

### B.2 Restrições inegociáveis

1. **Limite de 15 minutos.** Confirme com o usuário o horário exato de envio antes de finalizar; depois de enviado, o PDF é a única entrega e não pode ser alterado.
2. **Todo número apresentado vem das tabelas em `results/entrega_28_09/tables/`** (ou do relatório final, Parte A, que já as transcreve) — nunca do PDF antigo (`ENTREGA_28_09.tex`/`.pdf` anteriores).
3. **Não usar linguagem de "revisão"**: evite "corrigida", "antes/agora", "lacuna pedida por", "consertou" (preferência já expressa pelo autor). Isso não autoriza omitir a mudança de protocolo ou a exposição prévia ao teste — declare-as de forma factual e neutra.
4. **Nunca afirmar mais do que o teste mostra** — guarda-corpos explícitos (violar qualquer um é o tipo de erro que motivou a revisão crítica anterior):
   - DM sobre retornos (AR vs MA) não implica nada sobre ARMA vs. zero.
   - DM sobre variância (GARCH vs. MLP/Chronos) **é válido** — não são modelos aninhados — mas não generalize além da escala/alvo testados (1 min, comum de 60 min).
   - Não apresente GJR-GARCH nem qualquer variante assimétrica como parte da análise — foi tentada e removida por não estar no conteúdo teórico da Aula 6 (só no script R de apoio, de forma incompleta); mencionar isso só se perguntado, como nota de disciplina de escopo (§A.6).
   - KPSS não rejeitar ≠ "provamos estacionariedade". ADF/PP rejeitar ≠ "provamos estacionariedade" — é evidência contra raiz unitária.
   - Não dizer que a mudança de amostra "resolveu"/"consertou" a divergência de KPSS; dizer que a conclusão é sensível à amostra/especificação.
   - `zero_share` é proporção de retornos iguais a zero, não "barras sem negócio".
   - 1 e 5 minutos: nenhum ARMA(p≤5,q≤5) passa no Ljung-Box — declare isso como resultado substantivo (§A.5.1), não omita as escalas nem force uma alegação de adequação.
   - MLP tem MSE menor que GARCH na variância, mas QLIKE pior, e perde no teste DM — **não escolha uma métrica para esconder a outra**; apresente as duas e a divergência é o ponto interessante.
   - O novo período de teste se sobrepõe a dados já examinados antes (§A.2) — mencionar ao descrever a integridade do holdout.
5. **A comparação de variância com redes neurais foi feita em 1 minuto apenas** (orçamento computacional) — não generalize para as outras cinco escalas.

### B.3 Conteúdo obrigatório (enunciado oficial + anotações de aula, `context_resources/seminario_1_requisitos_do_professor.md`)

1. Por que prever esta série é relevante; importância de modelá-la.
2. Fonte e origem dos dados.
3. Justificativa do horizonte preditivo (relevância prática, não apenas comparabilidade estatística).
4. Classificação determinística explícita (constante/tendência) e d.
5. Equação do ARIMA efetivamente ajustado, com coeficientes — não apenas "ARMA(p,q)" (ver a equação de 15 min, §A.4, e os μ̂ das demais escalas).
6. Ljung–Box do modelo **selecionado**, com hipótese, horizontes e decisão — não substituir por BIC; inclua a declaração honesta de 1/5 minutos.
7. Medidas fora da amostra, com datas/n/identificação do alvo.
8. Figura realizado vs. previsto (`figures/09_real_vs_previsto_60min.pdf`).
9. Indicação explícita de one-step vs. multi-step (tabela de §A.7).
10. RMSE, MAE e MAPE, com o tratamento do MAPE indefinido/instável (o número astronômico de 5 min é um bom recurso didático, não apenas uma ressalva).
11. Comparação substantiva com o artigo de referência (§A.10), com os níveis de confiança respeitados — não apresentar itens "não verificados" como fato.
12. Avaliação preditiva final, sem extrapolar os testes realizados (§A.12).
13. Breve descrição do modelo alternativo selecionado (comparadores AR/MA + combinação) e de todas as decisões metodológicas.

### B.4 Critério de avaliação do professor

"Será avaliada a adequação das decisões metodológicas, a compreensão adequada da metodologia e a discussão apropriada dos resultados." Não é uma competição de quantidade de modelos. A seção de variância (§A.9) é o ponto alto da narrativa, mas não deve consumir tempo às custas dos itens obrigatórios de B.3 — several desses itens (equação ajustada, Ljung-Box, MAPE, figura) são sobre a **média**, não a variância, e são exigências explícitas e "obrigatórias" do professor.

### B.5 Estrutura sugerida (adapte o número de slides ao tempo)

Capa → dados/relevância/horizonte (§A.1–A.2) → divisão amostral e classificação determinística (§A.2) → estacionariedade + estatística descritiva (§A.3) → **"Parte 1: a média é previsível?"** — identificação/BIC/filtro de Ljung–Box/equação/significância (§A.4) → diagnóstico residual completo, incl. a declaração honesta de 1/5 min (§A.5) → previsão fora da amostra: one-step/multi-step, RMSE/MAE/MAPE (com o exemplo astronômico), figura realizado-vs-previsto, DM (§A.7) → MLP/Chronos nos retornos, fechando a Parte 1 (§A.8) → **"Parte 2: e a variância?"** — ARCH/GARCH por escala com significância (§A.6) → comparação de variância entre escalas + redes neurais + QLIKE + DM (§A.9, o clímax) → comparação com o artigo (§A.10) → conclusão/síntese (§A.12) → contracapa. Isso é ~13-14 slides de conteúdo; ajuste densidade por slide (siga o estilo compacto do `.tex` anterior: tabela + 2-3 takeaways + rodapé em fonte pequena com ressalvas) para caber em 15 minutos.

### B.6 Antes de finalizar — checklist

- [ ] O eixo narrativo (§B.1) está claro do início ao fim, não só mencionado uma vez.
- [ ] Nenhum dos guarda-corpos do §B.2.4 foi violado — releia cada slide contra essa lista.
- [ ] Todos os 13 itens de §B.3 aparecem em algum slide.
- [ ] O roteiro oral foi escrito e cronometrado; soma ≤ 15 minutos com folga.
- [ ] Todo slide tem parágrafo correspondente no roteiro oral (evite slides "órfãos").
- [ ] O PDF foi renderizado, páginas conferidas visualmente (tabelas não estouram a margem, figuras aparecem corretamente).
- [ ] O README do repositório foi atualizado, apontando este relatório/a nova apresentação como versão atual; 21/09 e a versão anterior de 28/09 movidas para "histórico".
- [ ] Conferir com o usuário antes de qualquer commit/push.
