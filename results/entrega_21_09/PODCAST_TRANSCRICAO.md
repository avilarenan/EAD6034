# Podcast — preparação para o seminário EAD6034

**Previsibilidade linear do WIN em múltiplas escalas temporais**  
Renan de Luca Avila · Econometria de Séries Temporais · Prof. Leandro Maciel.

Roteiro de estudo em diálogo, com duas vozes sintéticas genéricas. Abrange as entregas de **31/08, 14/09 e 21/09/2026**, incorporando as revisões da apresentação cumulativa. É material de preparação; não substitui o roteiro de cinco minutos da exposição. O seminário está previsto para **28/09/2026**.

[Slides](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/ENTREGA_21_09.pdf) · [Código Python](https://github.com/avilarenan/EAD6034/tree/f63a1048db3c36d2aeece3c8806be49f1be1a63c/src/ead6034) · [Relatório](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/RELATORIO_21_09.md) · [Questões](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/questões.md) · [Dados originais no Alpha Lab](https://alphalab.btgpactual.com/datasets/publication:7a74b3ae-90e0-4393-b1e0-01e61c0bedba).

O áudio contém apenas os diálogos delimitados abaixo. Os títulos, links e notas finais são referências para consulta.

**Duração medida do MP3: 17:43.**

## Índice do áudio

| Início | Assunto |
| --- | --- |
| 00:00 | 1. A pergunta que organiza o trabalho |
| 00:59 | 2. Dados, retornos e separação temporal |
| 02:20 | 3. Emendar pregões e corrigir o problema de amostra |
| 03:40 | 4. Primeira entrega: descrição, FAC e FACP |
| 05:21 | 5. Raiz do tempo e estacionariedade |
| 06:19 | 6. Segunda entrega: testes e suas hipóteses |
| 08:08 | 7. Box–Jenkins e a escolha pelo BIC |
| 10:20 | 8. Aula seis: prever a variância |
| 12:10 | 9. Terceira entrega: uma comparação preditiva justa |
| 14:05 | 10. Diebold–Mariano e resultados que parecem repetidos |
| 14:58 | 11. Overnight, leilões e limites de microestrutura |
| 16:24 | 12. Como defender a conclusão |

## 1. A pergunta que organiza o trabalho

**[00:00] Apresentador:** Renan, vamos ensaiar o raciocínio da sua apresentação de Econometria de Séries Temporais. Percorreremos as três entregas: descrição, em trinta e um de agosto; estacionariedade e Box–Jenkins, em quatorze de setembro; previsão e variância, em vinte e um de setembro. A pergunta central é: agregar retornos de minutos em horas melhora a previsão do minicontrato futuro de Ibovespa, o WIN?

**[00:23] Interlocutor:** A ideia inicial era que minutos estariam mais próximos das turbulências da abertura e do fechamento, enquanto horas refletiriam um mercado mais estável. Por que isso é uma hipótese, e não uma conclusão óbvia?

**[00:35] Apresentador:** Porque suavidade visual, volatilidade e previsibilidade são coisas diferentes. Agregar pode reduzir oscilações muito curtas, mas também apaga informação e reduz a amostra. Só podemos falar em ganho preditivo comparando erros futuros. Usamos as famílias ensinadas nas Aulas dois a seis. A proposta inspira a pergunta; não importa modelos novos do artigo de referência.

## 2. Dados, retornos e separação temporal

**[00:59] Interlocutor:** O que, exatamente, estamos analisando?

**[01:02] Apresentador:** Candles de negócios de um minuto do WIN, da base BTG, ATS, A vinte e seis, publicada no Alpha Lab. Convertemos os horários para São Paulo e usamos a janela das nove e cinco às dezoito e cinco. As seis escalas são um, cinco, quinze, trinta e sessenta minutos, além do diário. Treinamos somente em dois mil e vinte e quatro: duzentos e quarenta e seis pregões completos. Avaliamos duzentos e vinte e um pregões de dois mil e vinte e cinco, de dois de janeiro a vinte e oito de novembro.

**[01:32] Interlocutor:** Uma barra de cinco minutos é uma média de cinco retornos?

**[01:36] Apresentador:** Não. Calculamos cem vezes o logaritmo do preço final dividido pelo inicial. Assim, expressamos o retorno em porcentagem. Log-retornos de intervalos consecutivos, com fronteiras compatíveis, se somam. Uma hora reúne sessenta minutos. O diário mede abertura e fechamento da nossa janela e tem uma âncora inicial ligeiramente diferente; não o tratamos como soma exatamente idêntica do intradiário.

**[02:00] Interlocutor:** Então dois mil e vinte e cinco não participou da escolha dos modelos?

**[02:05] Apresentador:** Não participou da estimação, das ordens nem dos pesos da combinação. Essa separação temporal vem da Aula quatro. Avaliar no próprio treino premiaria modelos que explicam o passado, sem demonstrar utilidade futura.

## 3. Emendar pregões e corrigir o problema de amostra

**[02:20] Interlocutor:** Um professor criticou o teste horário porque havia apenas nove observações. Como respondemos?

**[02:26] Apresentador:** Reconhecemos a limitação. Eram nove barras de uma hora por pregão, não nove minutos. Testar cada sessão isoladamente era muito frágil. Agora há uma série anual por escala. Na hora, são duas mil duzentas e quatorze observações em dois mil e vinte e quatro. Não fazemos uma média de testes diários.

**[02:45] Interlocutor:** Mas emendar dias não inclui o retorno noturno?

**[02:48] Apresentador:** São decisões diferentes. Cada retorno continua calculado dentro do próprio pregão e contrato. Não dividimos o preço de hoje pelo fechamento de ontem para criar um retorno noturno. Porém, permitimos que o último retorno de ontem seja uma defasagem do primeiro de hoje. Na linguagem da Aula dois, o índice conta barras observadas. Um passo significa a próxima barra, mesmo havendo uma noite ou um fim de semana entre elas.

**[03:16] Interlocutor:** Qual é o preço dessa escolha?

**[03:18] Apresentador:** Supomos que podemos modelar essa sequência sem uma equação específica para a interrupção. Retirar o retorno noturno não retira notícias e informação acumuladas durante a noite. Tampouco duas mil observações significam duas mil observações independentes. Não preenchemos noites e lacunas com zeros, não interpolamos e não cortamos retornos extremos.

## 4. Primeira entrega: descrição, FAC e FACP

**[03:40] Interlocutor:** Vamos à entrega de agosto. Como explicar FAC e FACP sem apenas decorar as siglas?

**[03:46] Apresentador:** A função de autocorrelação, FAC, compara a sequência com uma cópia defasada dela. No lag um, pareamos cada retorno com o anterior, descontamos a média e normalizamos a covariância. No lag dois, comparamos com duas barras atrás. A FACP procura a associação linear que permanece depois de descontar as defasagens intermediárias. É o conteúdo da Aula três.

**[04:08] Interlocutor:** E OLS, que apareceu nas nossas conversas?

**[04:11] Apresentador:** Significa mínimos quadrados ordinários: escolher coeficientes que minimizam a soma dos resíduos ao quadrado. Regressões ajudam a entender a correlação parcial. Contudo, a FACP publicada nesta revisão usa o estimador de Yule–Walker, não uma média de regressões diárias. O conceito e a implementação estão documentados separadamente.

**[04:32] Interlocutor:** Uma hora no eixo horizontal significa a mesma coisa em todas as escalas?

**[04:37] Apresentador:** Se o eixo mostra lags, não. Sessenta minutos correspondem a sessenta lags na série de um minuto, doze na de cinco e um na horária, dentro da sessão. Na fronteira entre dias, o relógio deixa de ser contínuo. Também precisamos separar esse gráfico descritivo da avaliação futura com alvos comuns de uma hora.

**[04:56] Interlocutor:** Qual resultado merece atenção?

**[04:59] Apresentador:** No minuto, a primeira autocorrelação é aproximadamente menos zero vírgula zero zero oito. É pequena, mas cruza a banda de referência porque a amostra supera cento e trinta mil retornos. Significância estatística não equivale a efeito grande ou previsão útil. As bandas são aproximações pontuais, e a variância variável pode afetar sua interpretação.

## 5. Raiz do tempo e estacionariedade

**[05:21] Interlocutor:** E aquele gráfico no qual a dispersão cresce aproximadamente com a raiz do tempo?

**[05:27] Apresentador:** A variância de uma soma inclui variâncias e covariâncias. Se os retornos têm a mesma variância e autocovariâncias nulas, somar quatro períodos multiplica a variância por quatro e o desvio-padrão por dois. Daí a raiz quadrada do tempo. Independência é suficiente, mas não necessária. A proximidade dessa referência não prova independência nem variância condicional constante. Maior dispersão em uma hora também não significa maior previsibilidade.

**[05:56] Interlocutor:** Isso nos leva à entrega de setembro. O que chamamos de estacionariedade?

**[06:01] Apresentador:** Na definição fraca da Aula três, a média é constante, a variância é finita e constante, e a covariância depende da distância entre observações, não da data. Não significa que todos os retornos sejam iguais. É uma propriedade do processo; olhar uma realização não a comprova.

## 6. Segunda entrega: testes e suas hipóteses

**[06:19] Interlocutor:** Como funcionam os três testes da Aula cinco?

**[06:22] Apresentador:** ADF e Phillips–Perron têm como hipótese nula a presença de raiz unitária. O ADF acrescenta diferenças defasadas para tratar a dinâmica dos erros. Phillips–Perron corrige a estatística considerando dependência e heterocedasticidade, mediante uma estimativa de variância de longo prazo. O KPSS inverte a pergunta: sua hipótese nula é estacionariedade, em nível ou em torno de uma tendência, conforme a especificação.

**[06:50] Interlocutor:** Então basta os três concordarem?

**[06:52] Apresentador:** A leitura conjunta ajuda, mas exige declarar constante, tendência, defasagens e largura de banda. Usamos constante como especificação principal e constante com tendência como sensibilidade. O ADF escolhe lags por BIC, até doze. Os outros testes usam regras automáticas de largura de banda. O relatório registra essas escolhas; a regra numérica do Phillips–Perron não reproduz literalmente a seleção citada na aula.

**[07:20] Interlocutor:** E o resultado?

**[07:22] Apresentador:** Nas seis escalas, ADF e Phillips–Perron rejeitam raiz unitária. O KPSS com constante não rejeita estacionariedade. Porém, o KPSS com tendência rejeita em todas. Essa sensibilidade precisa aparecer na defesa. Não rejeitar não prova a hipótese nula; rejeitar com tendência também não demonstra que exista uma tendência linear.

**[07:43] Interlocutor:** Por que não diferenciar novamente os retornos?

**[07:47] Apresentador:** Porque a especificação principal sustenta trabalhar sem diferenciação adicional. Não diferenciamos apenas para conseguir concordância. A sensibilidade limita nossa conclusão. A série anual corrigiu a fragmentação em nove barras, mas não resolveu automaticamente mudanças estruturais ou padrões de volatilidade ao longo do dia.

## 7. Box–Jenkins e a escolha pelo BIC

**[08:08] Interlocutor:** Qual é a sequência de Box–Jenkins?

**[08:11] Apresentador:** Identificar padrões com FAC e FACP; estimar candidatos; comparar critérios; diagnosticar resíduos; e avaliar previsões. Na parte autorregressiva, o retorno depende de retornos anteriores. Na parte de médias móveis, depende de choques anteriores. Aqui, média móvel não significa fazer uma média de candles. Estimamos ordens de zero a cinco para cada parte, com constante, por máxima verossimilhança gaussiana. Conferimos convergência, estacionariedade e invertibilidade.

**[08:42] Interlocutor:** A verossimilhança gaussiana pressupõe retornos normais?

**[08:46] Apresentador:** Usa uma densidade normal como hipótese de trabalho para estimar. Não demonstra normalidade. As caudas dos retornos e a heterocedasticidade exigem cautela. Na Aula dois, a estabilidade aparece pelas raízes da dinâmica; na Aula três, ela fundamenta modelos estacionários.

**[09:03] Interlocutor:** E o BIC?

**[09:05] Apresentador:** É o critério de informação bayesiano. Equilibra ajuste e complexidade: menos duas vezes a log-verossimilhança, mais o número de parâmetros multiplicado pelo logaritmo do tamanho amostral. Menor é preferível entre candidatos na mesma série. AIC é informação complementar. Não comparamos valores brutos de BIC entre escalas com tamanhos e alvos diferentes.

**[09:27] Interlocutor:** Por que apareceu ARMA zero-zero?

**[09:29] Apresentador:** Nas escalas de cinco minutos até o diário, o ganho de ajuste dos modelos mais complexos não compensou a penalização. Com constante, zero-zero prevê a média estimada, não necessariamente zero. No minuto, a revisão anual escolheu ARMA dois-dois. É importante atualizar a fala: zero-zero não venceu em todas as escalas nesta versão.

**[09:50] Interlocutor:** Dois-dois resolveu a dependência do minuto?

**[09:53] Apresentador:** Não. Venceu zero-zero por apenas um vírgula vinte e quatro de BIC. Seus componentes autorregressivos e de médias móveis quase se compensam. E o Ljung–Box principal ainda rejeita ausência de autocorrelação residual. Em cinco minutos, a conclusão muda com o número de lags do diagnóstico. Seleção por BIC não equivale a adequação. Mantivemos essas falhas explícitas, como exige a etapa de diagnóstico da Aula quatro.

## 8. Aula seis: prever a variância

**[10:20] Interlocutor:** Se o retorno quase não tem autocorrelação, como ainda pode existir dinâmica?

**[10:26] Apresentador:** Porque ausência de correlação linear não significa independência. Um retorno positivo pode ser seguido de um negativo, mantendo correlação pequena, enquanto grandes oscilações vêm agrupadas. Os quadrados capturam parte desse comportamento. O teste ARCH-LM rejeitou ausência de efeitos ARCH nas seis escalas.

**[10:45] Interlocutor:** O que acrescentamos com a Aula seis?

**[10:48] Apresentador:** Comparamos variância constante, ARCH de ordem um e GARCH de ordens um e um. ARCH usa o choque passado ao quadrado. GARCH acrescenta a variância condicional passada. Estimamos sequencialmente, mantendo fixa a equação ARMA da média. Não foi estimação conjunta das duas equações.

**[11:06] Interlocutor:** Variância que muda não contradiz estacionariedade?

**[11:09] Apresentador:** Não necessariamente. A variância condicionada ao passado pode mudar enquanto a variância incondicional permanece constante e finita. No GARCH um-um, condições usuais incluem parâmetros não negativos e soma dos dois coeficientes de persistência menor que um. Na série de um minuto, essa soma ficou perto de zero vírgula noventa e nove: persistência alta da volatilidade, não raiz unitária da média.

**[11:33] Interlocutor:** O que os resultados permitem afirmar?

**[11:36] Apresentador:** O BIC escolheu GARCH até trinta minutos, ARCH na hora e variância constante no diário. Fora da amostra, houve redução descritiva do erro de previsão da variância nas cinco escalas intradiárias; cerca de quatro e meio por cento no minuto. Mas o alvo é a inovação ao quadrado, uma proxy ruidosa da variância. Ainda há dependência nos quadrados dos resíduos padronizados em algumas escalas. E todas essas variantes mantêm a mesma previsão pontual do retorno. Prever a intensidade da oscilação não é prever sua direção.

## 9. Terceira entrega: uma comparação preditiva justa

**[12:10] Interlocutor:** Como comparar um modelo de minuto com um modelo de hora?

**[12:13] Apresentador:** Primeiro, avaliamos uma barra à frente em cada frequência. Mas os horizontes nativos são diferentes. Para comparar escalas, construímos mil novecentos e oitenta e nove alvos idênticos de sessenta minutos em dois mil e vinte e cinco, sem sobreposição. O diário fica separado. Exemplo: às dez e cinco, o modelo de cinco minutos emite doze previsões e as soma para prever até onze e cinco. O modelo horário emite uma previsão para o mesmo retorno.

**[12:42] Interlocutor:** Podemos usar os retornos que forem aparecendo dentro dessa hora?

**[12:46] Apresentador:** Não naquela previsão inicial. Todas as parcelas usam apenas a informação disponível às dez e cinco. Na origem seguinte, atualizamos os estados com o passado já observado. Os parâmetros continuam fixados no treino. Atualizar estados não é reestimar parâmetros, nem conhecer o futuro.

**[13:05] Interlocutor:** Quais são os comparadores?

**[13:07] Apresentador:** O ARMA selecionado; modelos das famílias AR e MA com ordem positiva; sua combinação com metade do peso para cada um; a média do treino; e retorno zero. As famílias positivas selecionaram ordem um. São alternativas lineares próximas, com pouca diversidade para a combinação. Retorno zero é uma previsão de referência, não uma afirmação de que o mercado ficará parado.

**[13:29] Interlocutor:** Qual métrica usamos?

**[13:31] Apresentador:** Erro quadrático médio, ou MSE, que dá mais peso aos erros grandes, e erro absoluto médio, ou MAE. A razão entre o erro do modelo e o do zero facilita a leitura: abaixo de um seria melhora. Nenhum modelo superou globalmente o zero nessas métricas, nem nos horizontes nativos nem no alvo comum. Neste último, o ARMA ficou aproximadamente zero vírgula dois por cento pior em MSE. Isso é uma diferença de erro, não uma perda financeira de zero vírgula dois por cento.

## 10. Diebold–Mariano e resultados que parecem repetidos

**[14:05] Interlocutor:** O teste de Diebold–Mariano confirmou que zero é superior?

**[14:08] Apresentador:** Não fizemos esse teste contra zero. O teste comparou as perdas de AR com MA, seguindo a Aula quatro. Considera a diferença média das perdas e sua variabilidade, com tratamento da dependência temporal. No alvo comum, não rejeitou igualdade a cinco por cento. Isso não prova equivalência. Em alguns horizontes nativos há significância, mas as diferenças são microscópicas e não demonstram rentabilidade.

**[14:33] Interlocutor:** E por que várias escalas dão quase o mesmo resultado?

**[14:37] Apresentador:** Nos modelos zero-zero, somar as médias das barras completas produz a mesma previsão média horária para cinco, quinze, trinta e sessenta minutos. São transformações dos mesmos dados, não quatro confirmações independentes. A combinação de AR com MA tampouco trouxe ganho global: combinar previsões muito parecidas não garante melhora.

## 11. Overnight, leilões e limites de microestrutura

**[14:58] Interlocutor:** A hipótese sobre leilões estava errada?

**[15:01] Apresentador:** Não identificamos seu efeito causal. Leilões concentram ordens e auxiliam a formação de preços, mas não garantem menor volatilidade após notícias. Nos regimes históricos confirmados, o WIN já está negociando quando as ações abrem. A primeira hora da nossa janela pode conter essa abertura das ações. Os calls próprios do WIN ficam fora da janela estudada. Também não temos uma auditoria completa de todos os regimes de horário.

**[15:29] Interlocutor:** Então não podemos chamar início e fim de pregão de leilões?

**[15:33] Apresentador:** Exato. Os candles não identificam fases de leilão nem contêm cotações de compra e venda. Alternância entre preços de negócios, liquidez e informação são mecanismos plausíveis, não demonstrados. Os recortes por horário e magnitude do gap são descritivos. O limiar do gap foi definido no treino, mas esses grupos não constituem uma estratégia antecipadamente validada.

**[15:56] Interlocutor:** Qual limitação operacional um professor pode cobrar?

**[15:59] Apresentador:** O fornecedor escolhe o contrato de maior volume do próprio dia, informação completa conhecida depois da sessão. Nosso filtro de dias completos também é retrospectivo. Prever usando somente o passado não elimina essas escolhas na construção da base. Além disso, não simulamos spread, custos, filas ou lucro líquido. Logo, não apresentamos um sistema de negociação validado em tempo real.

## 12. Como defender a conclusão

**[16:24] Interlocutor:** Se a hora não ganhou e alguns diagnósticos falharam, qual é a contribuição?

**[16:28] Apresentador:** Uma comparação verificável, com hipóteses explícitas, alvos iguais e avaliação futura separada. A maior previsibilidade horária não recebeu suporte neste desenho. A variância apresentou melhora parcial, sem melhorar automaticamente a média. Isso não prova imprevisibilidade universal do mercado nem irrelevância dos leilões. Concluímos sobre estes modelos, este ativo e esta amostra.

**[16:52] Interlocutor:** E podemos ajustar os modelos agora até vencer em dois mil e vinte e cinco?

**[16:57] Apresentador:** Podemos explorar novas ideias, mas precisaríamos de outra avaliação independente. Depois de olhar os resultados, dois mil e vinte e cinco já não seria um teste intocado para escolhas motivadas por eles.

**[17:10] Interlocutor:** Qual frase você levaria para a banca?

**[17:13] Apresentador:** Eu separaria quatro perguntas: a série é compatível com estacionariedade? O modelo deixa dependência nos resíduos? Ajusta bem o treino? Melhora a previsão futura? Nenhuma resposta substitui as outras. Nos slides, conte essa história, da hipótese aos limites. O roteiro escrito traz as páginas das aulas, os dados originais no Alpha Lab e links clicáveis para o código Python no repositório EAD seis zero três quatro, de avilarenan, no GitHub.

## Referências para conferir e aprofundar

As páginas abaixo são as páginas físicas dos PDFs fornecidos, contando a partir de 1. Não se atribuem conteúdos às Aulas 0 ou 1, que não foram consultadas.

| Trecho do podcast | Conteúdo das aulas | Código e resultados |
| --- | --- | --- |
| 1–3: pergunta, retornos e tempo de negociação | Aula 2, pp. 54–62; Aula 4, pp. 38–44; Aula 6, p. 24 | [Construção temporal](https://github.com/avilarenan/EAD6034/blob/f63a1048db3c36d2aeece3c8806be49f1be1a63c/src/ead6034/trading_time_data.py); [agregação](https://github.com/avilarenan/EAD6034/blob/f63a1048db3c36d2aeece3c8806be49f1be1a63c/src/ead6034/multiscale.py); [auditoria](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/sequence_audit.csv) |
| 4–5: FAC, FACP, dispersão e estacionariedade | Aula 3, pp. 8–16, 43–50; Aula 6, pp. 25–27 | [Rotinas anuais](https://github.com/avilarenan/EAD6034/blob/f63a1048db3c36d2aeece3c8806be49f1be1a63c/src/ead6034/annual_models.py); [FAC/FACP](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/return_acf_pacf.csv) |
| 6: ADF, PP e KPSS | Aula 5, pp. 23–24, 28, 35, 39–45 | [Especificações e resultados](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/stationarity.csv) |
| 7: ARMA, BIC e diagnóstico | Aula 2, pp. 66–67; Aula 3, pp. 47–50; Aula 4, pp. 11–27 | [Estimação](https://github.com/avilarenan/EAD6034/blob/f63a1048db3c36d2aeece3c8806be49f1be1a63c/src/ead6034/annual_models.py); [grade ARMA](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/arma_grid.csv); [diagnósticos](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/mean_diagnostics.csv) |
| 8: variância condicional | Aula 6, pp. 5, 9–20, 28 | [ARCH/GARCH](https://github.com/avilarenan/EAD6034/blob/f63a1048db3c36d2aeece3c8806be49f1be1a63c/src/ead6034/conditional_volatility.py); [resultados](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/variance_models.csv) |
| 9–10: previsão, combinação e DM | Aula 4, pp. 32–34, 40, 43–50 | [Código da avaliação](https://github.com/avilarenan/EAD6034/blob/f63a1048db3c36d2aeece3c8806be49f1be1a63c/src/ead6034/forecast_evaluation.py); [acurácia](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/accuracy.csv); [DM](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/diebold_mariano.csv) |
| 11–12: microestrutura e conclusão | Documentação histórica da B3, distinta do conteúdo das aulas | [Horários B3 e fontes](https://github.com/avilarenan/EAD6034/blob/f63a1048db3c36d2aeece3c8806be49f1be1a63c/docs/market_hours_2024_2025.md); [proveniência](https://github.com/avilarenan/EAD6034/blob/f63a1048db3c36d2aeece3c8806be49f1be1a63c/docs/DATA_SOURCE.md); [conclusão crítica](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/CONCLUSAO_CRITICA.md) |

Notas de precisão para a arguição:

- BIC da implementação conta média e variância: \(k=p+q+2\). A diferença de contagem da variância comum aos candidatos em relação à exposição simplificada da aula não altera o ranking dentro da mesma amostra.
- ARMA usa verossimilhança gaussiana exata, com inicialização estacionária. O áudio não afirma estimação por OLS nem reprodução literal da recursão condicional da aula. Os resíduos não foram demonstrados normais; não foram publicados erros-padrão para alegar significância individual dos coeficientes.
- ADF usa seleção BIC de zero a doze lags; PP usa largura de banda automática de Schwert, com kernel Bartlett; KPSS usa largura de banda automática dependente dos dados. A Aula 5 menciona seleção de Newey–West para PP; a família do teste coincide, a regra numérica não é literal.
- Ljung–Box principal usa graus de liberdade \(h-p-q-1\), conforme Aula 4. A inferência convencional é aproximada e pode ser afetada pela heterocedasticidade. No minuto, o p-valor principal é aproximadamente 0,000169; em cinco minutos há sensibilidade ao horizonte diagnóstico.
- Persistência GARCH do minuto: \(\alpha+\beta=0{,}986811\). O ganho descritivo de aproximadamente 4,50% usa MSE contra a inovação ao quadrado; não significa melhora da previsão da média, variância verdadeira observada ou rentabilidade. Resíduos padronizados: \(z_t=\varepsilon_t/\sqrt{h_t}\).
- DM compara AR e MA, com perda quadrática principal e absoluta complementar, estimativa da variância de longo prazo, referência t e correção de pequena amostra. Não há ajuste por múltiplos testes. Não foi usado para inferir superioridade do zero sobre ARMA ou para comparar os modelos aninhados de variância.
- Os dados publicados abrangem mais anos e instrumentos, mas o recorte efetivo deste estudo é somente WIN em 2024 e no trecho disponível de 2025. A previsão fora da amostra é condicional à seleção retrospectiva do contrato e dos pregões completos.
- Inspiração: Matías e Reboredo (2012), [DOI 10.1002/for.1218](https://doi.org/10.1002/for.1218). O trabalho não replica os modelos não lineares desse artigo.

Esta produção é uma adaptação didática dos resultados existentes. Não reestima modelos nem introduz novos métodos estatísticos.

## Produção do áudio

Duas vozes sintéticas genéricas em português brasileiro: Alex e Dora. Síntese local com [Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx), montagem em Python e FFmpeg, sem trilha musical. Siglas e nomes técnicos recebem adaptações de pronúncia; a transcrição conserva a grafia acadêmica.

[Modelo Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) · [Catálogo de vozes](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md). Modelo sob licença Apache 2.0; a biblioteca kokoro-onnx usa licença MIT.

[Roteiro-fonte](https://github.com/avilarenan/EAD6034/blob/main/docs/PODCAST_PREPARACAO_21_09.md) · [Gerador Python](https://github.com/avilarenan/EAD6034/blob/main/scripts/build_podcast.py)
