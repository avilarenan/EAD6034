# Guia de apresentação - EAD6034, 14/09/2026

Use a apresentação de sete páginas como síntese e o relatório técnico para consultar estatísticas, p-valores, valores críticos e decisões individuais. A sequência abaixo cabe em cerca de 10 a 12 minutos.

## 1. Pergunta e resultado central

“Continuamos a comparação de retornos do WIN em seis escalas. Esta entrega examina estacionariedade e aplica Box-Jenkins usando apenas 2024. A escala de 5 minutos é a replicação adaptada do benchmark. As demais estendem a dimensão temporal mantendo os mesmos pregões.”

Explique que BIC escolhe uma estrutura da equação da média. A escolha não demonstra que os retornos sejam independentes, normais ou que a volatilidade seja constante.

## 2. Amostra e fronteiras

“São 246 pregões completos, de 2 de janeiro a 30 de dezembro de 2024, na janela de nove horas. Em 1 minuto cada dia fornece 540 observações. Em 60 minutos fornece apenas nove. Quando um dia termina, o próximo começa um novo segmento.”

No diário, cada observação é o retorno open-to-close. Os dez segmentos refletem rolagens e lacunas, conforme a primeira entrega. Sete são longos o suficiente para executar os testes definidos. A estimação ARMA usa os dez.

## 3. Testes de estacionariedade

“ADF e PP perguntam se há raiz unitária. KPSS parte da hipótese de estacionariedade. Consideramos concordância com I(0) quando ADF e PP rejeitam e KPSS não rejeita no mesmo segmento.”

Leia a tabela como frequência de decisões entre pregões. A tabela não contém um teste global do ano. Nas escalas mais lentas, poucos pontos por dia reduzem o poder dos testes. Não rejeitar raiz unitária em nove observações não demonstra que ela exista.

ADF acrescenta defasagens das diferenças para lidar com correlação dos erros. PP corrige a estatística utilizando uma estimativa HAC da variância de longo prazo. KPSS usa somas parciais dos resíduos em relação à mesma ideia de variância de longo prazo. A especificação principal contém constante, com tendência como sensibilidade nos trechos suficientemente longos.

## 4. Seleção por BIC

“Estimamos a grade da proposta, com parâmetros comuns entre os segmentos e reinicialização estacionária em cada um. A média e a variância fazem parte da contagem de parâmetros. Comparamos BIC dentro da mesma escala, e mantemos AIC para avaliar sensibilidade à penalização.”

ARMA(0,0) com constante significa retorno igual a uma média mais uma inovação. Sua previsão pontual é a média histórica estimada no treino. O benchmark de retorno zero é distinto, ainda que as médias estimadas sejam pequenas.

Na escala de 60 minutos, três ordens grandes não são identificáveis pela estrutura de covariância de réplicas de nove pontos. Outras soluções podem ser excluídas por convergência ou proximidade de raízes unitárias. Isso consta da grade completa.

## 5. FAC e FACP residual

“Os resíduos são os erros de previsão de um passo padronizados pelo modelo. As defasagens continuam restritas ao mesmo segmento. Observamos magnitude, padrões e testes conjuntos, em vez de escolher um modelo por um pico isolado.”

O eixo horizontal mede lags na escala de cada painel. Uma defasagem representa um minuto no painel de 1 minuto e um pregão no diário. Estes painéis não comparam todos os pontos na mesma separação física.

## 6. Diagnóstico

“O Q reúne autocorrelações dos resíduos usando apenas pares válidos. A aproximação qui-quadrado é uma referência. Também simulamos o modelo gaussiano com a mesma segmentação e reestimamos seus parâmetros para calibrar Q.”

O bootstrap tem 999 réplicas, resolução mínima de 0,001 e mantém a ordem selecionada. Não é um bootstrap robusto à heteroscedasticidade. A referência residual é rejeitada em 1, 5 e 60 minutos. Isso limita o modelo completo e não prova automaticamente previsibilidade linear rentável.

Na revisão, nenhum dos 36 candidatos de 1 minuto elimina a rejeição em h=60. Em 5 minutos, a conclusão é sensível ao horizonte h=12 ou h=24. Em 60 minutos, AR(2) fica documentado como alternativa: não rejeita a referência em h=8 e custa aproximadamente 2,70 pontos de BIC frente a ARMA(0,0). O relatório não escolhe retrospectivamente o horizonte que aprova um modelo.

A coluna de resíduos ao quadrado trata da dependência na magnitude. A curtose excedente descreve caudas mais pesadas que a normal quando positiva. Nenhuma dessas medidas substitui a avaliação fora da amostra.

## 7. Continuidade

“A evidência de estacionariedade é local, a seleção da média é parcimoniosa e a volatilidade continua relevante. O ganho preditivo será medido em 2025, na entrega de 21/09, com benchmarks, modelo alternativo, combinação e Diebold-Mariano.”

## Perguntas prováveis

**Por que não concatenar os pregões para os testes?**

Porque isso faria o primeiro retorno do dia seguinte ser a defasagem de uma barra do último retorno do dia anterior. Isso conflita com o protocolo intradiário. Testes convencionais não têm automaticamente a mesma distribuição quando suas regressões são alteradas para reiniciar as defasagens.

**Por que não tirar a média dos p-valores?**

A média não é um p-valor válido de um teste conjunto. O relatório usa frequências e medianas como descrições e publica cada teste individual. Combinar testes exigiria definir outra hipótese e tratar a dependência entre eles.

**Usamos ADF no preço ou no retorno?**

Nos retornos, que são a variável de interesse e o alvo de previsão da proposta. Concluir sobre raiz unitária dos retornos não é o mesmo que concluir sobre o nível de preços.

**Por que d=0?**

Já trabalhamos com diferenças logarítmicas de preços. Os testes nos trechos mais longos oferecem evidência a favor de I(0) dos retornos. A escolha continua provisória nos trechos curtos; não usamos a baixa potência de um teste para justificar diferenciação adicional automática.

**Se BIC escolheu ARMA(0,0), o seminário não encontrou nada?**

Encontrou que, nessa amostra e nesse protocolo, a complexidade AR/MA não foi compensada pelo critério principal. Esse é um resultado empírico relevante. A dinâmica da volatilidade e os resultados fora da amostra são questões distintas e continuam abertas.

**O modelo passa em todos os diagnósticos?**

Consulte a tabela. A seleção por BIC não garante isso. Caudas pesadas, heteroscedasticidade e dependência residual podem tornar inadequado o modelo completo, ainda que sua equação da média seja uma referência útil. A revisão inclui o melhor AIC e o melhor AR puro, sem esconder falhas.

**Podemos dizer que uma escala é mais previsível que outra?**

Ainda não. Esta etapa usa apenas ajuste e diagnóstico dentro da amostra. Escalas também têm tamanhos amostrais e precisões diferentes. A comparação preditiva deve usar horizontes compatíveis, métricas e dados de 2025 sem acesso antecipado ao futuro.
