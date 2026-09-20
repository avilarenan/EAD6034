# Perguntas de professores — EAD6034, entrega de 21/09/2026

FAQ técnico cumulativo para o seminário de 28/09/2026. As páginas citadas são **páginas físicas dos PDFs, contando a capa como página 1**. Foram consultadas as Aulas 2, 3, 4, 5 e 6; não se atribui conteúdo às Aulas 0 ou 1, que não estavam disponíveis nesta revisão. Os resultados abaixo vêm das tabelas públicas da entrega de 21/09, não de novas estimações.

Referências: [código do estudo](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/forecast_pipeline.py), [roteiro dos sete slides](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/GUIA_APRESENTACAO.md) e [conclusão crítica](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/CONCLUSAO_CRITICA.md).

**Três níveis de afirmação:** “aula” indica método efetivamente desenvolvido no material; “implementação” identifica uma escolha operacional ou numérica explícita; “esclarecimento conceitual” apresenta uma interpretação matemática, sem alegar a estimação de um método adicional. Essa distinção importa, por exemplo, para bandwidth automático, tempo de negociação, estacionariedade estrita e efeitos causais de leilões.

## Fundamentos, índice temporal e amostra — slides 1 e 2

### 1. O que é um processo estocástico e o que representa a série observada?

Um processo estocástico é uma família de variáveis aleatórias indexadas, como $\{R_t\}$. A sequência observada de retornos do WIN é uma realização desse processo; o modelo aproxima aspectos de sua dinâmica, sem pretender explicar cada choque. Construímos seis sequências do mesmo ativo, uma para cada escala. Aqui $t$ é a posição da barra na sequência de negociação, e não cada minuto consecutivo do calendário.

**Aula:** Aula 2, p. 60; Aula 3, pp. 4–7. **Implementação:** [construção temporal](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/trading_time_data.py).

### 2. A aula pressupõe intervalos regulares. Emendar pregões não viola esse pressuposto?

A regularidade é assumida no **índice de observações de negociação**: uma unidade significa uma barra anterior disponível. No relógio, a distância varia nas passagens entre dias, fins de semana e lacunas. Essa é uma hipótese do nosso modelo, não uma propriedade que os dados demonstraram. O estado e os lags continuam entre pregões; não criamos observações de preço ou retornos para preencher o fechamento do mercado.

Há duas operações diferentes: o retorno da primeira barra usa preços daquele pregão; seu preditor pode ser o retorno da última barra de ontem. O movimento fechamento–abertura não é acrescentado ao alvo, embora informações noturnas possam influenciar hoje. Assim, a expressão correta é “não modelamos separadamente a interrupção”, não “o overnight não tem efeito”.

**Aula:** Aula 2, p. 4 (tempo discreto) e p. 62 (operador de defasagem). **Hipótese do estudo:** [código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/trading_time_data.py), [auditoria das sequências](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/sequence_audit.csv).

### 3. Por que antes havia n=9 e agora n=2.214? Isso resolve o problema de poder?

Antes, cada sessão horária era testada isoladamente: nove **barras de 60 minutos**, não nove minutos. Agora usamos os 246 pregões de 2024 em uma sequência com 2.214 retornos horários, antes das perdas por diferenças e defasagens. Nos testes ADF/PP horários, o número efetivo de linhas é 2.213. Não tiramos média de testes nem multiplicamos artificialmente observações: mudamos a convenção temporal e refizemos a análise.

Isso reduz a fragmentação extrema, mas não elimina problemas de especificação, dependência e quebras. “N efetivo” exportado pelo software significa linhas utilizadas, **não um número estimado de observações independentes**. No minuto há 132.840 retornos; essa amostra pode detectar desvios pequenos sem que eles tenham utilidade preditiva. A Aula 5 discute baixo poder do ADF e o custo de muitas defasagens; não promete validade automática para amostras grandes.

**Aula:** Aula 5, pp. 24–27, 35 e 39. **Código e resultados:** [testes](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [estacionariedade](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/stationarity.csv).

### 4. Como são construídas as barras e por que excluir pregões incompletos?

Usamos a janela comum de 09:05–18:05, no horário de São Paulo, com 540 minutos. As barras recebem o rótulo da fronteira final: a barra de cinco minutos 09:05–09:10 é rotulada 09:10. A fronteira inicial dos retornos intradiários é o fechamento do candle iniciado às 09:04. Já o diário usa a abertura da janela às 09:05: não se presume igualdade exata com a soma intradiária ancorada no fechamento anterior.

Foram incluídos 246 de 250 dias com dados em 2024 e 221 de 230 em 2025, para que as escalas compartilhem sessões completas e alvos comparáveis. Um dia excluído pode ser sessão reduzida, não necessariamente erro da fonte. Esse filtro é retrospectivo: não estaria integralmente conhecido no começo da sessão. Portanto, os resultados são condicionais à amostra selecionada, não uma promessa de funcionamento em todos os pregões. A seleção ex post do contrato também é discutida adiante.

**Implementação, não regra prescrita pela aula:** [barras](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/multiscale.py), [protocolo anual](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/trading_time_data.py), [cobertura](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/coverage.csv).

### 5. Ruído branco significa independência? A covariância do choque consigo mesmo é zero?

Na definição usada na disciplina, ruído branco tem média zero, variância constante e covariância zero **entre tempos diferentes**. Para o mesmo instante, $\operatorname{Cov}(\varepsilon_t,\varepsilon_t)=\operatorname{Var}(\varepsilon_t)=\sigma^2$, não zero. Independência é mais forte que ausência de correlação. Uma FAC pequena não prova que nenhum aspecto da distribuição possa ser previsto.

Em 5 minutos, o Ljung–Box dos resíduos em 24 lags tem p≈0,07796, enquanto o dos quadrados tem p≈3,16×10⁻²⁰². Isso distingue dependência linear e dependência de segundo momento. Não rejeitar um teste também não comprova sua hipótese nula.

**Aula:** Aula 3, pp. 8, 10 e 16; Aula 6, pp. 17–19. **Código e resultados:** [diagnóstico](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [tabela](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/mean_diagnostics.csv).

### 6. Como calcular FAC e FACP a partir das barras? Estamos fazendo médias entre dias?

Cada barra fornece um retorno. A FAC de lag $h$ relaciona a série de retornos com a mesma série deslocada em $h$ observações; a FACP mede a associação que permanece após controlar as defasagens intermediárias. Não calculamos uma média das FAC/FACP de nove observações de cada dia: a nova análise usa a sequência anual, incluindo pares que atravessam pregões.

A implementação atual usa FAC convencional com denominador amostral comum e FACP por Yule–Walker (`ywmle`). A Aula 3, p. 44, apresenta a interpretação via regressões; OLS significa *Ordinary Least Squares*, ou Mínimos Quadrados Ordinários: escolhe coeficientes minimizando a soma dos quadrados dos resíduos. Yule–Walker é uma escolha computacional para estimar os mesmos coeficientes parciais populacionais, com diferenças possíveis em amostras finitas. Não afirmar que rodamos literalmente aquelas regressões OLS nesta versão. As bandas ±1,96/√N são referências pontuais aproximadas, não bandas simultâneas robustas à heterocedasticidade.

**Aula:** Aula 3, pp. 16 e 43–47. **Detalhe de implementação:** [correlogramas](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [FAC/FACP](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/return_acf_pacf.csv).

### 7. O que é estacionariedade fraca? Os testes comprovam estacionariedade estrita?

Estacionariedade fraca requer média constante, variância finita constante e autocovariância dependente somente da defasagem: $E(R_t)=\mu$, $\operatorname{Var}(R_t)=\gamma_0$, $\operatorname{Cov}(R_t,R_{t-h})=\gamma_h$. Estacionariedade estrita exige invariância de todas as distribuições conjuntas a deslocamentos do índice. Com segundos momentos finitos, a estrita implica a fraca; a recíproca não é geral. Nossos testes não demonstram estacionariedade estrita.

Um padrão sistemático por horário permanece relevante: em 5 minutos, o desvio-padrão de 2024 foi aproximadamente 0,0911% no início, 0,0711% no meio e 0,0464% no final da janela. A ausência de raiz unitária não comprova que todas as características sejam constantes. Variância condicional variável pode coexistir com variância incondicional constante sob condições ARCH/GARCH; não se deve confundir isso com qualquer mudança arbitrária de variância por calendário.

**Aula:** estacionariedade fraca na Aula 3, p. 15; condicional/incondicional na Aula 6, pp. 5 e 10–15. **Esclarecimento conceitual:** definição estrita, não um novo teste estimado. [Código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [faixas](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/time_band_description.csv).

### 8. De onde vem a regra da raiz do tempo? Ela demonstra ausência de dependência?

Pelas propriedades de variância e covariância, sob estacionariedade fraca:

$$
\operatorname{Var}\left(\sum_{j=1}^{k}R_j\right)
=k\gamma_0+2\sum_{h=1}^{k-1}(k-h)\gamma_h.
$$

Se as covariâncias cruzadas forem zero, resulta $\sigma_k=\sqrt{k}\sigma_1$. Independência é suficiente, mas não necessária. Para 60 minutos, a referência calculada é aproximadamente 0,24869%, contra desvio-padrão observado de 0,24462%. Proximidade não demonstra independência, normalidade ou ausência de volatilidade condicional. A figura não ajusta um novo expoente aos dados.

**Dedução conceitual:** propriedades desenvolvidas na Aula 3, pp. 9–10 e 24–25; a regra não é atribuída a uma página inexistente da Aula 2. [Código da figura](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/forecast_figures.py), [descrição](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/descriptive.csv).

## Raiz unitária e especificação — slide 3

### 9. Por que ADF, PP e KPSS têm hipóteses nulas diferentes?

ADF e PP usam H0 de raiz unitária; KPSS usa H0 de estacionariedade, em nível ou em torno de tendência conforme a especificação. Assim, “rejeitar” não significa a mesma coisa nos três testes. Em `c`, ADF e PP rejeitam nas seis escalas, enquanto KPSS não rejeita. No diário: ADF p≈3,20×10⁻²⁹, PP p≈2,50×10⁻²⁹ e KPSS p≈0,3339. A leitura é evidência concordante com I(0) nessa especificação, sem comprovar estabilidade de toda a distribuição.

**Aula:** Aula 5, pp. 23, 42–45. [Código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [resultados](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/stationarity.csv).

### 10. Por que usar constante como principal e constante mais tendência como sensibilidade?

São duas especificações pré-definidas: `c` permite média não nula sem impor tendência determinística aos retornos; `ct` permite constante e tendência linear. A escolha principal não foi feita depois de olhar qual produzia o p-valor desejado. A terceira formulação sem constante nem tendência aparece na Aula 5, p. 23, mas não foi executada nesta entrega; tampouco executamos os testes conjuntos φ apresentados nas pp. 29–34.

Isso deve ser apresentado como recorte do protocolo, não como reprodução integral de toda a árvore de especificação da aula. A sensibilidade `ct` tem resultados importantes e permanece visível. Incluir uma tendência na regressão de teste não é demonstrar que a série realmente possui tendência determinística.

**Aula:** Aula 5, pp. 23–24 e 29–34. **Protocolo executado:** [código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [testes](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/stationarity.csv).

### 11. Como KPSS pode não rejeitar com constante e rejeitar ao incluir tendência?

As duas versões usam resíduos e distribuições de referência diferentes. Na escala horária, `c` produz estatística 0,199137, crítico de 5% 0,4614 e p=0,269730; `ct` produz estatística 0,185068, crítico 0,1479 e p=0,021047. A estatística caiu, mas o crítico caiu ainda mais. Aumentar o conjunto de termos determinísticos não garante monotonicidade do p-valor desses testes amostrais.

O padrão ocorre nas seis escalas: p de KPSS-`c` entre 0,2697 e 0,3339; p de KPSS-`ct` entre 0,0210 e 0,0393. Não ocultamos essa sensibilidade. Rejeição em `ct` não prova tendência determinística nem determina sozinha que devemos diferenciar os retornos; evidencia uma limitação da conclusão quando alteramos a especificação.

**Aula:** Aula 5, pp. 43–45; importância dos termos determinísticos nas pp. 23–24. [Código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [tabela](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/stationarity.csv).

### 12. Por que o ADF escolheu zero lags? Isso significa que os retornos são independentes?

O BIC escolheu zero **diferenças defasadas adicionais** entre os candidatos de 0 a 12 na regressão auxiliar. Isso não é a ordem do ARMA de previsão, nem prova independência. A aula descreve o compromisso: poucos lags podem deixar autocorrelação; muitos reduzem poder e graus de liberdade. Seleção por BIC é uma regra explícita, não garantia automática de resíduos adequados em todos os aspectos.

No horário, ADF-`c` tem estatística −48,9831 e crítico −2,86285. Um p-valor retornado numericamente como zero é apresentado como abaixo da precisão numérica, não como probabilidade matematicamente nula. O grande afastamento da região de raiz unitária não elimina a sensibilidade de KPSS à especificação.

**Aula:** Aula 5, pp. 28 e 35. [Código e regra de seleção](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [estatísticas](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/stationarity.csv).

### 13. Como PP trata autocorrelação? Seu bandwidth reproduz literalmente a aula?

ADF acrescenta diferenças defasadas; PP corrige a estatística de Dickey–Fuller com uma estimativa da variância de longo prazo dos resíduos. A implementação usa ponderação Bartlett. O PP recebe o bandwidth automático padrão da biblioteca, com regra Schwert: 73, 49, 37, 31, 27 e 16 nas seis escalas. KPSS usa a seleção automática dependente dos dados da biblioteca.

A Aula 5, p. 41, menciona a seleção de Newey–West (1994). Portanto, **não afirmar que a regra automática específica Schwert reproduz literalmente essa indicação**. PP e a correção de longo prazo são métodos da aula; a regra de bandwidth é detalhe de implementação que foi registrado e limita a alegação de reprodução exata. Também não chamar bandwidth de ordem AR estimada.

**Aula:** Aula 5, pp. 40–42 e 45. **Implementação explícita:** [código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [colunas lag_rule e lags](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/stationarity.csv).

### 14. Diante da rejeição de KPSS-ct, não deveríamos diferenciar os retornos?

Não automaticamente. A especificação principal fornece evidência contra raiz unitária, e a sensibilidade com tendência revela conflito que precisa ser relatado. Diferenciar uma série já I(0) não é uma correção neutra: altera a variável de interesse e pode introduzir dinâmica artificial. A Aula 5, p. 39, alerta para diferenciar séries estacionárias por limitações dos testes.

Mantivemos o ARMA dos retornos com d=0 como protocolo previamente fixado e divulgamos a sensibilidade, sem declarar estacionariedade absoluta. Isso não encerra a discussão sobre sazonalidade, quebras ou estabilidade da distribuição; esses aspectos não foram transformados em novos métodos nesta entrega.

**Aula:** Aula 5, pp. 15, 36 e 39. [Código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [resultados completos](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/stationarity.csv).

## ARMA, verossimilhança e diagnóstico — slide 4

### 15. O que significa ARMA(p,q), e quais modelos venceram nesta versão?

O componente AR usa retornos anteriores; o MA usa choques anteriores, não uma média móvel aritmética dos preços. A versão atual escolheu ARMA(2,2) no minuto e ARMA(0,0) em 5, 15, 30 e 60 minutos e no diário. ARMA(0,0) com constante prevê uma média fixa; não significa “retorno necessariamente zero” nem demonstra ausência de qualquer padrão.

Esses resultados pertencem ao desenho anual. A entrega anterior, segmentada por pregão, selecionara (0,0) em todas as escalas; não devemos misturar os vencedores dos dois protocolos. A constante de `statsmodels.ARIMA` é μ, a média incondicional; no AR(1), o intercepto da equação dinâmica é μ(1−φ), não necessariamente μ.

**Aula:** Aula 3, modelos ARMA e exemplo na p. 41; Aula 4, identificação e estimação. [Código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [modelos selecionados](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/selected_models.csv).

### 16. Como foi feita a máxima verossimilhança? É igual a minimizar erros quadrados?

Sob uma variância gaussiana constante e uma definição fixa dos resíduos, o critério contém $-\tfrac12\sum_t[\log(2\pi\sigma^2)+\varepsilon_t^2/\sigma^2]$. ARMA(0,0) usa a solução fechada: média amostral e variância dos resíduos com denominador N. Nas demais ordens, o código maximiza numericamente a verossimilhança exata das inovações, com inicialização estacionária e estimação iterativa da média; tentativas e falhas são registradas.

A inicialização exata não é literalmente o exemplo didático condicionado em erro inicial zero. É uma escolha de implementação dentro da mesma família ARMA. Sob variância variável, cada erro pode receber peso distinto, além do termo logarítmico da variância; não se pode reduzir todo problema ARMA–GARCH a minimizar uma única soma não ponderada de quadrados.

**Aula:** Aula 4, pp. 11–17; Aula 6, p. 16. [Estimação](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [grade e tentativas](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/arma_grid.csv).

### 17. Por que BIC usa p+q+2 se a aula menciona p+q+1? Podemos comparar escalas?

Usamos $BIC=-2\log L+k\log N$, contando p coeficientes AR, q MA, média e variância: k=p+q+2. A contagem da equação apresentada na aula trata p+q+1. Acrescentar o parâmetro de variância comum a todos os candidatos aumenta o critério em log N, mas preserva o ranking **na mesma escala e amostra**. A forma dividida por N da aula também preserva esse ranking.

Não se comparam diretamente BIC de frequências com diferentes amostras e unidades. No minuto, ARMA(2,2) vence ARMA(0,0) por somente **ΔBIC=1,2399**; não é evidência de grande ganho econômico. Nas demais escalas, o ganho de ajuste dos candidatos mais complexos não compensou a penalidade. Menor BIC não garante diagnóstico satisfatório nem menor erro em 2025.

**Aula:** Aula 4, pp. 19–20 e 23. [Código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [grade](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/arma_grid.csv).

### 18. A aula exige raízes dentro do círculo unitário; por que o código exige módulo maior que um?

São raízes de polinômios diferentes, reciprocamente relacionadas. No AR(1), a dinâmica estável exige |φ|<1. O polinômio de defasagem 1−φz=0 tem raiz z=1/φ, portanto |z|>1. Não há contradição entre a raiz característica da equação de diferenças e a raiz do polinômio em lags.

O código verifica raízes AR e MA para estacionariedade/invertibilidade e utiliza inicialização estacionária. Essas condições tornam um candidato admissível, mas não comprovam diagnóstico adequado ou capacidade preditiva. Uma condição inicial arbitrária também pode introduzir transientes, tema explicitado nas aulas.

**Aula:** Aula 2, pp. 30 e 66–67; Aula 3, pp. 18–21. [Verificação numérica](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [raízes dos selecionados](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/selected_models.csv).

### 19. Coeficientes grandes no ARMA(2,2) do minuto indicam forte previsibilidade?

Não necessariamente. Os coeficientes AR são aproximadamente [1,5253; −0,9384], e os MA [−1,5310; 0,9450]. Os polinômios apresentam **quase cancelamento**: efeitos grandes em cada componente podem resultar em dinâmica líquida pequena. Os menores módulos das raízes são aproximadamente 1,0323 e 1,0287, admissíveis, mas próximos entre si.

Não afirmamos cancelamento exato nem reduzimos o modelo após olhar o teste. A pequena vantagem BIC frente a (0,0), Δ=1,2399, e os erros de previsão devem acompanhar a leitura dos coeficientes. Olhar apenas |coeficiente|, isolado da combinação AR/MA, produziria uma conclusão enganosa.

**Esclarecimento algébrico dentro do ARMA:** Aula 2, pp. 66–67, e Aula 3, p. 41, dão a base de polinômios/dinâmica. [Código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [coeficientes e raízes](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/selected_models.csv).

### 20. Os coeficientes são estatisticamente significativos? Onde estão os erros-padrão?

A execução utiliza `cov_type='none'` e **não apresenta erros-padrão, testes t ou intervalos dos coeficientes**. Portanto, não podemos dizer que um coeficiente é significativo a partir do valor estimado ou de o BIC ter escolhido o modelo. Seleção por critério de informação e inferência sobre parâmetros individuais não são equivalentes.

A Aula 4, p. 23, discute significância de parâmetros, mas essa etapa não foi executada em sua totalidade. É uma limitação a reconhecer na defesa, juntamente com heterocedasticidade e quase cancelamento. A ausência de uma matriz de covariância não foi compensada por alegações de inferência robusta ou por testes novos.

**Aula:** Aula 4, p. 23. **Implementação e limitação:** [código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [estimativas sem erros-padrão](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/selected_models.csv).

### 21. Se o modelo escolhido ainda rejeita Ljung–Box, ele completou Box–Jenkins com sucesso?

Não. Identificação, estimação, seleção e diagnóstico são etapas distintas. No minuto, o candidato BIC rejeita o diagnóstico principal em 60 lags, p≈0,000169. Assim, não deve ser chamado de modelo plenamente adequado; mantê-lo como referência documentada permite avaliar sua previsão, sem apagar a falha. Em 5 minutos, p≈0,078 no horizonte principal de 24 lags, mas há rejeições em 10, 12 e 20 lags, com p≈0,0391, 0,0204 e 0,0366. Evitar a frase irrestrita “passou no diagnóstico”.

O Q é convencional. A referência principal usa gl=h−p−q−1, contando a constante conforme a Aula 4, p. 27; a convenção usual de software h−p−q também é exportada. FAC por FFT é uma aceleração do cálculo, não o antigo Q modificado por fronteiras. Heterocedasticidade pode afetar a calibração assintótica. Não escolher h retrospectivamente para produzir não rejeição.

**Aula:** Aula 4, pp. 25 e 27. [Código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [todos os horizontes](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/mean_diagnostics.csv).

## Variância condicional — slide 5

### 22. O que o ARCH-LM testa? Ele escolhe automaticamente GARCH(1,1)?

Regredimos o resíduo quadrado nos seus atrasos e testamos conjuntamente se os coeficientes desses atrasos são zero. A estatística é T_efetivo R², com referência assintótica χ². Rejeição indica efeitos ARCH no conjunto de atrasos examinado; não determina automaticamente uma ordem ou a preferência por GARCH.

No bloco de variância, com 20 defasagens, a escala horária tem LM=59,2574 e p≈9,27×10⁻⁶; o diário, LM=54,4276 e p≈5,00×10⁻⁵. O BIC diário ainda escolhe a constante entre os três candidatos simples. Isso não é contradição: um teste com vinte atrasos pode detectar estrutura que ARCH(1)/GARCH(1,1) não capturam suficientemente para compensar a penalidade.

**Aula:** Aula 6, pp. 18–20. [Código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/conditional_volatility.py), [ARCH-LM](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/variance_diagnostics.csv).

### 23. Qual a diferença entre ARCH(1), GARCH(1,1) e variância constante?

Na equação $h_t=\omega+\alpha\varepsilon_{t-1}^2+\beta h_{t-1}$, a constante tem α=β=0; ARCH(1) tem β=0; GARCH(1,1) usa o choque quadrado e a variância anteriores. Exigimos ω>0, α≥0, β≥0 e persistência menor que 1−10⁻⁸, além de convergência numérica. O pequeno afastamento da unidade é uma tolerância operacional, não um novo teorema da aula.

GARCH(1,1) foi escolhido por BIC condicional em 1, 5, 15 e 30 minutos; ARCH(1), em 60 minutos; constante, no diário. A grade de variância contém somente essas três estruturas previamente definidas, não todos os modelos possíveis. “Melhor” significa melhor nesse conjunto e critério.

**Aula:** Aula 6, pp. 9–16 e 21. [Código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/conditional_volatility.py), [candidatos](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/variance_models.csv).

### 24. O GARCH do minuto tem persistência 0,987. Isso não contradiz estacionariedade?

No minuto, α≈0,084163, β≈0,902648 e α+β≈0,986811. A soma indica dissipação lenta dos desvios na dinâmica esperada da variância; não é uma probabilidade, nem o coeficiente de raiz unitária da média. Está abaixo da unidade e satisfaz o critério adotado, mas recebeu aviso por estar próxima da fronteira.

Sob as condições do modelo, $\operatorname{Var}(\varepsilon_t)=\omega/(1-\alpha-\beta)$, aproximadamente 0,00120436 (p.p.)² no minuto. A variância condicional muda com o passado, enquanto a incondicional pode ser constante e finita. A interpretação é em passos de negociação, não diretamente em horas de relógio ou duração do overnight. Estabilidade paramétrica não comprova que o modelo descreva adequadamente todos os dados.

**Aula:** Aula 6, pp. 5, 11 e 15. [Código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/conditional_volatility.py), [parâmetros](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/variance_models.csv).

### 25. Por que usar uma densidade normal diante das caudas pesadas? Podemos alegar QMLE robusta?

A normal é uma densidade de trabalho. A amostra tem excesso de curtose de aproximadamente 20,18 no minuto e 21,75 em 5 minutos, mas normalidade incondicional dos retornos e normalidade condicional das inovações padronizadas são perguntas distintas: uma variância condicional variável pode produzir caudas incondicionais pesadas. Não foi demonstrada normalidade após cada ajuste GARCH.

Se a densidade for incorreta, o critério pode ser descrito cautelosamente como quase-verossimilhança gaussiana. Isso **não autoriza prometer automaticamente consistência, eficiência ou inferência robusta**: essas propriedades dependem de condições que a execução não comprovou. Não foi estimada uma teoria ou correção adicional de QMLE nesta entrega. A Aula 6 admite distribuições para a inovação; escolhemos somente a normal no protocolo.

**Aula:** Aula 4, pp. 11–17; Aula 6, pp. 16 e 25. **Limite interpretativo:** [código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/conditional_volatility.py), [curtose observada](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/descriptive.csv).

### 26. Estimamos ARMA–GARCH conjuntamente? Seus BIC são comparáveis com os do ARMA?

Não. Primeiro estimamos a média ARMA, depois fixamos seus coeficientes e estimamos a variância das mesmas inovações. É **estimação sequencial**, coerente com a sequência didática da Aula 6, p. 20, e não máxima verossimilhança conjunta. A previsão pontual da média permanece exatamente compartilhada entre as três variâncias.

Os BIC condicionais contam 1, 2 ou 3 parâmetros de variância e só comparam candidatos sobre a mesma média fixa. Não são diretamente comparáveis com o BIC do ARMA original. No horário: constante BIC=54,8483; ARCH(1)=−3,57594; GARCH(1,1)=1,59708. O vencedor dessa comparação é ARCH(1), não uma escolha conjunta de nova equação da média.

**Aula:** Aula 6, pp. 16, 20 e 28. [Implementação sequencial](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/conditional_volatility.py), [critérios](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/variance_models.csv).

### 27. O BIC escolheu GARCH, mas Ljung–Box de z² ainda rejeita. Como apresentar isso?

Como captura parcial da dinâmica, não validação completa. A Aula 6 pede verificar $z_t=\varepsilon_t/\sqrt{h_t}$ e $z_t^2$. No GARCH do minuto, a 60 lags, Q(z) tem p=0,41293; Q(z²), p≈5,39×10⁻²⁵. Não houve rejeição de correlação linear em z nesse diagnóstico, mas permanece evidência muito forte nos quadrados. Menor BIC não garante que toda dependência foi eliminada.

O ARCH horário ainda rejeita em z² a 24 lags, p≈0,01331; a constante diária rejeita a 20 lags, p≈0,003449. GARCH em 5, 15 e 30 minutos não rejeita nos horizontes examinados, sem comprovar independência. A referência χ²(h), sem subtração ad hoc dos parâmetros GARCH, é aproximada após estimação sequencial; não alegamos calibração exata em amostra finita.

**Aula:** Aula 6, p. 19. [Código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/conditional_volatility.py), [diagnósticos padronizados](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/variance_diagnostics.csv).

### 28. Como avaliar uma variância não observada? Melhorar sua previsão melhora o retorno previsto?

Usamos o **mesmo erro quadrado da média ARMA fixa** como proxy para todos os modelos. Ele é uma realização ruidosa, não a própria variância condicional. No minuto, os MSE dessa proxy em 2025 foram 5,94509×10⁻⁵ para a constante, 5,57959×10⁻⁵ para ARCH(1) e 5,67779×10⁻⁵ para GARCH(1,1). GARCH melhora cerca de 4,50% contra a constante, mas ARCH tem a melhora descritiva maior, 6,15%, apesar de não vencer no BIC de treino.

Isso não autoriza trocar retrospectivamente o selecionado e reutilizar o mesmo teste como validação independente. As três variâncias mantêm exatamente as mesmas previsões pontuais da média: melhorar a proxy não significa melhorar o retorno previsto. O MSE da proxy é medido em (p.p.)⁴, e o MAE em (p.p.)². Não aplicamos DM às especificações aninhadas de variância.

Se a equação da média estiver incorreta, o erro quadrado também contém o desvio sistemático da média prevista: erro quadrático condicional é variância condicional mais o quadrado desse desvio. Portanto, a proxy não separa perfeitamente falha de média e variância. Esse esclarecimento reforça a importância do diagnóstico da média, sem introduzir uma nova estimação.

**Aula:** Aula 6, pp. 8, 13, 17 e 19. [Código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/conditional_volatility.py), [avaliação da proxy](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/variance_models.csv).

## Previsão, comparadores e validação — slide 6

### 29. Se os parâmetros são fixos, como a previsão muda ao longo de 2025?

Ordens e parâmetros foram estimados em 2024. Em 2025, atualizamos somente os estados e defasagens com observações que já ficaram disponíveis, e a variância com o choque anterior observado. Isso permite mudar a previsão sem reestimar os coeficientes. No ARMA(0,0), a previsão da média é constante; no GARCH, sua variância pode mudar.

O código usa filtro causal, não suavização com observações futuras. Uma previsão multipasso parte de uma única origem e não insere realizações intermediárias ainda desconhecidas. Testes de código modificam artificialmente o futuro para confirmar que previsões anteriores não mudam. Esse controle evita vazamento no filtro, mas não apaga as limitações de seleção ex post do universo/qualidade da fonte.

**Aula:** Aula 4, seção de previsão; Aula 6, p. 19. **Verificação de implementação:** [previsões](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/forecast_evaluation.py), [variância](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/conditional_volatility.py).

### 30. Por que o horizonte comum de 60 minutos é necessário?

Um retorno de um minuto e um de uma hora têm duração e dispersão distintas. Comparar seus MSE brutos confundiria alvo com capacidade preditiva. No exercício comum, sessenta retornos de um minuto, doze de cinco minutos, quatro de quinze minutos, dois de trinta minutos e um horário referem-se aos mesmos preços de fronteira. A soma telescópica dos log-retornos permite verificar a igualdade do alvo.

São nove alvos horários não sobrepostos por dia, totalizando **1.989 alvos em 221 pregões de 2025**, com origens e máscaras comuns. O exercício nativo de um passo continua apresentado separadamente. No comum60, o ARMA escolhido tem MSE/MSE_zero≈1,001940 no minuto e ≈1,002031 nas demais escalas intradiárias: os resultados não confirmam superioridade horária frente ao benchmark zero nessa comparação.

**Aula:** Aula 4, previsão e comparação de erros. **Protocolo e identidade algébrica dos log-retornos:** [código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/forecast_evaluation.py), [alvos reconciliados](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/common_target_alignment.csv), [acurácia](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/accuracy.csv).

### 31. Uma razão MSE menor é prova de rentabilidade? E significância estatística é ganho relevante?

MSE mede o erro quadrático, MAE o absoluto e RMSE a raiz do MSE. Os retornos estão em pontos percentuais; MSE em (p.p.)² e MAE/RMSE em p.p. Razão MSE/MSE_zero<1 indica melhora frente à previsão zero naquele alvo. Não usamos MAPE porque retornos podem ser zero ou muito próximos de zero.

Não foi calculado P&L, nem incluídos spread, custos, impacto, risco ou regras de execução. Portanto, nenhuma diferença de erro comprova rentabilidade. No DM de perda absoluta nativa, o minuto tem p≈6,11×10⁻⁶, mas a diferença média AR−MA é apenas **3,936×10⁻⁸ p.p.**; em 5 minutos, p≈1,24×10⁻⁵ acompanha diferença **−1,391×10⁻⁷ p.p.**. Significância, magnitude e utilidade econômica precisam ser apresentadas separadamente.

**Aula:** Aula 4, comparação de previsões, pp. 48–49. [Código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/forecast_evaluation.py), [métricas](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/accuracy.csv), [DM](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/diebold_mariano.csv).

### 32. O DM compara quais modelos e como trata dependência das perdas?

A comparação pré-especificada é AR puro positivo versus MA puro positivo, escolhidos por BIC em 2024, com $d_t=\operatorname{perda}_{AR}-\operatorname{perda}_{MA}$. Estatística negativa favorece AR. A fórmula segue a soma retangular de autocovariâncias da Aula 4, correção de pequena amostra e referência t. O q principal cobre uma hora de barras no nativo; no comum60 e diário, q=1. q=0 é sensibilidade. Não se confunde q da variância de longo prazo com ordem ARMA.

Como os alvos de perdas não se sobrepõem, h_perda=1, mesmo quando um modelo precisa prever sessenta barras para atingir uma hora. Perdas idênticas ou variância de longo prazo não positiva impedem o p-valor. A inferência é aproximada, sem correção de multiplicidade, e não prova superioridade frente ao ZERO ou ao vencedor ARMA geral. Não aplicamos esse DM às comparações aninhadas de variância.

**Aula:** Aula 4, pp. 48–49. **Escolhas operacionais explícitas:** [código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/forecast_evaluation.py), [todos os testes](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/diebold_mariano.csv).

### 33. Por que combinar AR e MA com pesos de 50%? Não seria melhor estimar os pesos?

A combinação é a média simples das duas previsões, com pesos fixados antes de examinar 2025. A Aula 4 motiva combinações porque modelos podem capturar informações distintas; não promete melhora em toda amostra. Aqui, AR e MA frequentemente geram previsões muito próximas, portanto oferecem pouca diversidade para a combinação.

Não estimamos pesos usando o teste nem escolhemos retrospectivamente uma combinação vencedora. Otimizar pesos depois de olhar 2025 mudaria a pergunta e consumiria a mesma informação que deveria avaliar a regra. A comparação inclui explicitamente o ZERO e a média de treino, e previsões numericamente idênticas são identificadas.

**Aula:** Aula 4, p. 50. [Código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/forecast_evaluation.py), [acurácia](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/accuracy.csv), [equivalência de previsões](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/forecast_equivalence.csv).

### 34. AR e MA são um modelo alternativo suficientemente diferente? GARCH resolve essa questão?

AR e MA positivos são estruturas não aninhadas entre si e estão nas aulas, mas pertencem à mesma família linear ARMA. Essa é uma alternativa **pouco diversa**, sobretudo quando os coeficientes são próximos de zero. No minuto, AR(1)≈−0,00812 e MA(1)≈−0,00816; as previsões quase coincidem. Não devemos vender essa comparação como confronto entre paradigmas amplamente diferentes.

ARCH/GARCH acrescenta uma equação da variância, mas nesta estimação sequencial não gera uma segunda previsão pontual independente do retorno. Portanto, a inclusão de GARCH não transforma automaticamente a comparação da média em algo mais diverso. O trabalho atende ao recorte dos métodos fornecidos, mas o alcance científico e a interpretação do requisito de modelo alternativo devem ser reconhecidos na defesa.

**Aula:** Aula 3, p. 41; Aula 4, pp. 49–50; Aula 6, p. 28. [Modelos](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [variância](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/conditional_volatility.py), [seleções](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/selected_models.csv).

### 35. Podemos melhorar os modelos agora que vimos 2025 e continuar chamando-o de holdout?

2025 já foi utilizado para avaliação e **agora está consumido como teste para este protocolo**. Mudar modelos, pesos, horários ou regras depois de observar seus erros torna as novas comparações exploratórias nesse mesmo período. Não seriam uma nova validação independente apenas por manter os coeficientes nominalmente estimados em 2024.

Resultados negativos são preservados. Não houve ganho global nativo de MSE/MAE frente a ZERO; pequenos ganhos de alguns comparadores em recortes não autorizam selecionar a melhor faixa e anunciar uma estratégia validada. Uma etapa posterior precisaria distinguir desenvolvimento exploratório e nova avaliação independente, sem alegar que executamos métodos ou amostras adicionais nesta entrega.

**Princípio de separação treino/teste aplicado ao estudo:** [execução](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/forecast_pipeline.py), [avaliação](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/forecast_evaluation.py), [resultados completos](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/accuracy.csv).

## Fonte, contratos, microestrutura e leilões — slides 1 e 7

### 36. De onde vêm os preços? São cotações médias? O dataset é aberto para redistribuição?

O conjunto exato é **BTG-ATS-A26: Aggregate Trade Statistics Dataset**, não BTG-TLD-A26. A documentação oficial informa candles de um minuto construídos de mensagens de negócios da B3, com cobertura declarada de 04/01/2016 a 28/11/2025; nosso estudo utiliza apenas o recorte indicado. Abertura e fechamento são primeiro e último **negócio** da janela, não midpoint das melhores ofertas. O timestamp `candle` representa o início do intervalo em UTC, convertido no código para São Paulo.

Acesso gratuito mediante cadastro e finalidade acadêmica/científica não equivalem a uma autorização geral de redistribuição. Publicamos código, figuras e agregados, mantendo preços, retornos individuais, previsões, resíduos e caches fora do Git. Não se publica a íntegra do README como se fosse conteúdo autoral do estudo.

**Fonte documental:** [publicação exata AlphaLab](https://alphalab.btgpactual.com/datasets/publication:7a74b3ae-90e0-4393-b1e0-01e61c0bedba), [README BTG-ATS-A26](https://dataservices.btgpactualsolutions.com/alphalab/v1/api/alphalab/readme/README-BTG-ATS-A26.md), [termos AlphaLab](https://alphalab.btgpactual.com/terms-and-policies#terms-of-use). **Implementação:** [leitura e construção](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/trading_time_data.py).

### 37. O contrato WIN escolhido era conhecido antes de começar o pregão?

**Não é garantido.** O README define, para WIN/WDO, o contrato de maior volume negociado **no próprio dia**. A seleção da série é, portanto, ex post. No começo da sessão ainda não se conhece, em geral, qual contrato terá o maior volume ao final. Não basta dizer “usamos somente retornos passados” para transformar a composição desse universo numa regra online comprovada.

A estimativa dos coeficientes usa 2024 e os filtros de previsão em 2025 são causais condicionais à série fornecida. Essa verificação permanece válida, mas não elimina a antecipação na escolha original do contrato nem o filtro retrospectivo de pregões completos. A formulação correta é **avaliação estatística em uma série de contratos selecionada retrospectivamente**; não um backtest integral de seleção do contrato e execução disponível em tempo real. Não quantificamos quanto essa escolha altera as métricas, porque não reconstruímos uma seleção alternativa usando informação anterior ao dia.

**Fonte documental:** regra da seção 2.3 do [README BTG-ATS-A26](https://dataservices.btgpactualsolutions.com/alphalab/v1/api/alphalab/readme/README-BTG-ATS-A26.md). **Limite da execução:** [dados](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/trading_time_data.py), [filtro causal da previsão](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/forecast_evaluation.py).

### 38. Uma FAC negativa em minutos prova bid–ask bounce?

Não. Alternância de negócios executados no bid e no ask pode produzir reversões dos preços de negócio sem uma mudança correspondente no midpoint das ofertas. Isso é uma **explicação possível de microestrutura**, não um mecanismo identificado na entrega. Os candles contêm negócios agregados, sem ofertas ou livro suficientes para reconstruir midquotes e separar esse componente.

A B3 trata spread, profundidade e volume como dimensões de liquidez. Isso fundamenta sua relevância, mas não demonstra que a FAC observada foi causada por bid–ask bounce. Não estimamos modelo de microestrutura, não substituímos negócio por midquote e não atribuímos causalidade a um coeficiente negativo.

**Documentação e esclarecimento conceitual:** [README](https://dataservices.btgpactualsolutions.com/alphalab/v1/api/alphalab/readme/README-BTG-ATS-A26.md); [Manual de Procedimentos Operacionais B3, edição de 17/02/2025, p. 45](https://www.b3.com.br/data/files/55/65/B5/7D/AC31591029BEEC39AC094EA8/MPO%20de%20Negociacao%20da%20B3.pdf). **Análise efetivamente feita:** [FAC/FACP](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/annual_models.py), [correlações](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/return_acf_pacf.csv).

### 39. O leilão necessariamente reduz volatilidade e assimetria de informação?

Não podemos presumir esse resultado em todos os eventos. A B3 descreve a formação transparente de preços de abertura/fechamento e estabelece, como primeiro critério de fixing, a maximização da quantidade negociada. Esses mecanismos organizam o encontro das ordens, mas não prometem menor variância: o preço pode incorporar uma surpresa relevante justamente nesse momento.

Amortecimento da assimetria de informação é uma motivação econômica da hipótese, não uma variável diretamente medida nem uma conclusão causal do nosso estudo. Sem identificação de fase e estratégia de comparação causal, uma diferença entre faixas horárias não permite atribuir o resultado ao leilão. Esse esclarecimento não adiciona um método novo ao trabalho.

**Fonte documental:** [Manual B3, edição de 17/02/2025, pp. 36 e 55](https://www.b3.com.br/data/files/55/65/B5/7D/AC31591029BEEC39AC094EA8/MPO%20de%20Negociacao%20da%20B3.pdf), com edição identificada no [portal normativo de operações](https://www.b3.com.br/pt_br/regulacao/estrutura-normativa/operacoes/). **Limites do estudo:** [auditoria histórica](https://github.com/avilarenan/EAD6034/blob/main/docs/market_hours_2024_2025.md), [código do contexto](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/trading_time_data.py).

### 40. Excluir o retorno overnight elimina a influência da informação overnight?

Não. A operação exclui do alvo a mudança entre fechamento e abertura; os primeiros retornos intradiários ainda podem refletir notícias acumuladas, ajustes de expectativas e outras decisões. Emendar os lags também permite carregar informações do pregão anterior. Nenhuma dessas escolhas prova que a distribuição antes e depois da interrupção seja igual.

O gap auxiliar é entre primeiro open e último close **observados no feed**, com restrições de contrato e cobertura. Não é necessariamente o retorno entre preços oficiais de leilão. A divisão entre gaps maiores e menores usa a mediana de magnitude de 2024, aplicada a 2025, mas é uma decomposição ex post dos erros. Um gap conhecido somente depois da abertura não foi introduzido retroativamente numa previsão emitida antes dela.

**Definição metodológica do estudo:** [código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/trading_time_data.py), [resumo dos gaps](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/observed_gap_summary.csv), [métricas por grupo](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/accuracy.csv). **Limites documentais:** [auditoria](https://github.com/avilarenan/EAD6034/blob/main/docs/market_hours_2024_2025.md).

### 41. A abertura do WIN e a das ações ocorrem no mesmo horário?

Não nos regimes históricos confirmados: WIN começa às 09:00 e ações às 10:00. Logo, a faixa 09:05–10:05 do estudo atravessa o entorno da abertura das ações, embora comece depois da abertura do próprio WIN. Essa diferença é uma motivação plausível para explorar perfis intradiários, sem identificar automaticamente um mecanismo responsável pelos erros.

O Ofício 059/2024 foi publicado em 16/04/2024 e apresenta a grade aplicável a partir de 17/04; o 153/2024, publicado em 12/11, confirma horários desde 04/11. Não recuperamos um calendário integral de todos os regimes e exceções de 2024–2025. A tabela atual não foi aplicada retrospectivamente e a ausência de uma data final recuperada não autoriza prolongar uma grade indefinidamente.

**Fontes oficiais:** [B3 059/2024-PRE, WIN p. 5 e ações p. 9](https://www.b3.com.br/data/files/CE/04/53/7F/6D8EE810C54843E8DC0D8AA8/OC%20059-2024%20PRE%20Novos%20horarios%20de%20negociacao_Estrategias%20-%20Fut%20Bitcoin%20%28PT%29.pdf); [B3 153/2024-PRE, WIN p. 6 e ações p. 8](https://www.b3.com.br/data/files/55/56/E6/49/EB0239106EEC8429AC094EA8/OC%20153-2024%20PRE%20%20Novos%20Horarios%20de%20Negociacao%20%28PT%29.pdf). **Código:** [faixas físicas](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/trading_time_data.py).

### 42. Como evitamos um retorno artificial na troca de vencimento do WIN?

Não dividimos o preço de um contrato pelo preço de outro para gerar retorno. Cada retorno principal é construído dentro do mesmo pregão e contrato. Para o gap auxiliar, as transições de contrato são excluídas; não se interpreta diferença de preços entre vencimentos como retorno overnight. Isso evita um salto de rolagem aritmético fabricado.

Os lags, porém, podem relacionar retornos de contratos diferentes em sessões consecutivas, e mudanças de composição/liquidez continuam presentes. A escolha do contrato por volume do próprio dia é ex post, como explicado na pergunta 37. Não foi construída uma nova série de preços ajustada nem estimado um mecanismo de rolagem online.

**Fontes:** [README da amostra](https://dataservices.btgpactualsolutions.com/alphalab/v1/api/alphalab/readme/README-BTG-ATS-A26.md), [especificação do futuro mini de Ibovespa na B3](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/futuro-mini-de-ibovespa.htm). **Código e auditoria:** [dados](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/trading_time_data.py), [transições](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/sequence_audit.csv).

### 43. Um lag corresponde sempre ao mesmo tempo decorrido, inclusive quando a bolsa está fechada?

Não. Lag 1 é a observação anterior da sequência de negociação. Dentro de um pregão completo, barras da mesma escala são consecutivas e igualmente espaçadas; entre pregões, o relógio pode avançar uma noite, fim de semana ou outro intervalo. Estados contínuos no modelo não significam que houve negociação contínua no mercado fechado.

Essa hipótese deve acompanhar a leitura de persistência, FAC e previsões. O Manual B3 distingue fases da negociação, mas sua descrição de fases não valida automaticamente nossa hipótese estatística de emenda. Não estimamos um efeito separado para cada duração de interrupção; elas permanecem sinalizadas na auditoria, sem criar preços noturnos ou preencher retornos zero.

**Aula:** Aula 2, pp. 4 e 62. **Fonte de fases:** [Manual B3, edição de 17/02/2025, p. 36](https://www.b3.com.br/data/files/55/65/B5/7D/AC31591029BEEC39AC094EA8/MPO%20de%20Negociacao%20da%20B3.pdf). **Hipótese implementada:** [código](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/trading_time_data.py).

### 44. Agregar em horas deveria eliminar o ruído de execução e produzir uma estratégia lucrativa?

É uma hipótese, não uma consequência necessária. Agregação pode atenuar oscilações de execução, mas também esconder sinais, acumular choques e reduzir o número de observações. A comparação exige alvos comuns e ganho frente a uma referência, como o exercício de 60 minutos. As razões MSE/MSE_zero observadas não confirmam vantagem do ARMA horário frente ao ZERO.

Mesmo eventual ganho estatístico não incorpora spread, slippage, filas, profundidade, custos ou disponibilidade operacional do contrato. Candles de negócios não permitem reproduzir fielmente essas condições de execução. Não foi realizada uma simulação de trading, nem uma estimativa causal da parcela de erro atribuível à microestrutura.

**Esclarecimento econômico, sem novo método estimado:** [Manual B3, edição de 17/02/2025, p. 45, dimensões de liquidez](https://www.b3.com.br/data/files/55/65/B5/7D/AC31591029BEEC39AC094EA8/MPO%20de%20Negociacao%20da%20B3.pdf). **Análise efetiva:** [código de previsão](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/forecast_evaluation.py), [acurácia](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/accuracy.csv).

### 45. A última hora da janela coincide com o leilão de fechamento do WIN? O meio é sempre um período estável?

Não. Nos horários históricos documentados para o WIN não vincendo, nosso fim às 18:05 antecede o início do call às 18:25. A faixa final 17:05–18:05 pode conter o call das ações de 17:55–18:00 na grade de novembro. Já no regime documentado de abril, o call das ações 16:55–17:00 pertence à nossa faixa intermediária. O horário de ajuste do futuro também não é automaticamente o horário do seu call.

Assim, `inicio`, `meio` e `fim` são posições na janela, **não fases de mercado observadas** nem uma classificação universal de estabilidade. A documentação histórica é parcial e não identifica cada negócio como negócio de leilão. A conclusão da entrega é sobre o alcance dos resultados e da metodologia: associação por faixa/gap, em um futuro e período específicos, sem demonstração causal de efeitos de leilões ou de ausência de influência overnight.

**Fontes oficiais:** [B3 059/2024-PRE, pp. 5 e 9](https://www.b3.com.br/data/files/CE/04/53/7F/6D8EE810C54843E8DC0D8AA8/OC%20059-2024%20PRE%20Novos%20horarios%20de%20negociacao_Estrategias%20-%20Fut%20Bitcoin%20%28PT%29.pdf); [B3 153/2024-PRE, pp. 6 e 8](https://www.b3.com.br/data/files/55/56/E6/49/EB0239106EEC8429AC094EA8/OC%20153-2024%20PRE%20%20Novos%20Horarios%20de%20Negociacao%20%28PT%29.pdf). **Código e limites:** [contexto](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/trading_time_data.py), [auditoria consolidada](https://github.com/avilarenan/EAD6034/blob/main/docs/market_hours_2024_2025.md).

## Referências de consulta rápida

- **Aula 2:** tempo discreto (p. 4), processo estocástico (p. 60), defasagem (p. 62), raízes características e recíprocas (pp. 66–67).
- **Aula 3:** ruído branco (p. 8), covariância (p. 10), estacionariedade fraca (p. 15), autocorrelação (p. 16), FACP e identificação (pp. 43–47).
- **Aula 4:** máxima verossimilhança (pp. 11–17), AIC/BIC (pp. 19–20), significância dos coeficientes (p. 23), diagnóstico (pp. 25–27), Diebold–Mariano (pp. 48–49) e combinação (p. 50).
- **Aula 5:** especificações determinísticas (pp. 23–24), ADF (p. 28), seleção de lags (p. 35), poder (p. 39), PP (pp. 40–42), KPSS (pp. 43–45).
- **Aula 6:** ARCH/GARCH e estabilidade (pp. 9–16), quadrados e ARCH-LM (pp. 17–18), diagnóstico e sequência (pp. 19–20), integração ARMA–GARCH (p. 28).
- **Dados:** [AlphaLab — publicação BTG-ATS-A26](https://alphalab.btgpactual.com/datasets/publication:7a74b3ae-90e0-4393-b1e0-01e61c0bedba). Identificação do README consultado: SHA-256 `7d30399abc95e2db9b6c8be864e6047a141b86e8eb6d939234a0d7ecf765741b`; o hash identifica a leitura, não concede licença de redistribuição.
- **Horários/microestrutura:** [auditoria com fontes oficiais, vigências e lacunas](https://github.com/avilarenan/EAD6034/blob/main/docs/market_hours_2024_2025.md). O manual de 2025 fundamenta mecanismos documentados; não preenche retrospectivamente todas as grades de 2024.
- **Motivação acadêmica:** Matías, J. M.; Reboredo, J. C. (2012), *Forecasting performance of nonlinear models for intraday stock returns*, Journal of Forecasting 31(2), 172–188, [DOI](https://doi.org/10.1002/for.1218). O estudo é uma adaptação linear da pergunta de previsão, não reprodução dos modelos não lineares do artigo.
