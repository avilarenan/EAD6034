# Roteiro oral — EAD6034, entrega cumulativa de 21/09/2026

Renan de Luca Avila · Prof. Leandro Maciel · Seminário em 28/09/2026.

Este roteiro acompanha os **sete slides existentes**, reunindo as entregas de 31/08, 14/09 e 21/09. Os trechos de **fala principal** e as transições foram preparados para um ensaio de aproximadamente **13 minutos**, com pausas para apontar gráficos e tabelas. As notas técnicas, fórmulas e perguntas são material de preparação e não devem ser lidas integralmente durante a apresentação. Os dois minutos restantes até o limite de 15 minutos são margem para transições e esclarecimentos breves.

As referências às aulas usam **páginas físicas dos PDFs, contadas a partir de 1**. Foram consultadas as Aulas 2, 3, 4, 5 e 6. Não se atribuem conteúdos às Aulas 0 ou 1, que não estavam disponíveis nesta preparação. As afirmações empíricas correspondem aos resultados entregues; este roteiro não executa testes adicionais nem introduz modelos novos.

[Apresentação cumulativa](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/ENTREGA_21_09.pdf) · [Relatório completo](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/RELATORIO_21_09.md) · [Perguntas dos professores](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/PERGUNTAS_PROFESSORES.md) · [Publicação do dataset no BTG Alpha Lab](https://alphalab.btgpactual.com/datasets/publication:7a74b3ae-90e0-4393-b1e0-01e61c0bedba).

## Distribuição dos 13 minutos

| Slide | Tempo | Relógio acumulado | Resultado que precisa ficar claro |
| --- | --- | --- | --- |
| 1 — Dois anos, seis escalas, uma regra temporal | 1min30 | 00:00–01:30 | Objeto, treino/teste e hipótese de tempo de negociação |
| 2 — Da descrição às hipóteses de dependência | 1min30 | 01:30–03:00 | Correlação pequena não equivale a previsão útil |
| 3 — Estacionariedade: uma série anual por escala | 1min45 | 03:00–04:45 | Correção de n=9 e sensibilidade das hipóteses dos testes |
| 4 — BIC seleciona; os resíduos ainda precisam passar | 2min | 04:45–06:45 | Seleção, adequação e desempenho são decisões diferentes |
| 5 — Prever a variância não é prever a direção | 1min45 | 06:45–08:30 | A variância muda; a previsão pontual permanece igual |
| 6 — A comparação justa usa o mesmo alvo futuro | 2min15 | 08:30–10:45 | Nenhum ganho global sobre zero; DM tem objeto específico |
| 7 — Conclusão: alcance dos resultados e da metodologia | 2min15 | 10:45–13:00 | Hipótese não confirmada e alcance real da evidência |

## Slide 1 — Dois anos, seis escalas, uma regra temporal

### Fala principal

A pergunta deste trabalho é se agregar retornos de minutos em horas melhora a previsão do WIN. A motivação é que diferentes escalas podem refletir de formas diferentes a informação e a negociação ao longo do pregão. Essa é uma hipótese a investigar, não uma conclusão estabelecida.

Uso retornos logarítmicos em seis escalas, de um minuto ao diário. A estimação utiliza 2024, com 246 pregões completos comuns, e a avaliação utiliza 221 pregões de 2025. A janela é a mesma em todas as escalas intradiárias: das nove e cinco às dezoito e cinco. As seis séries são agregações dos mesmos dados, não seis amostras independentes.

A principal revisão metodológica é continuar a sequência entre pregões. Não calculamos um retorno que atravesse a noite, mas o retorno da última barra de ontem pode ser a defasagem da primeira barra de hoje. Assim, um lag significa uma observação anterior de negociação.

Há duas limitações de construção: a fonte escolhe o contrato de maior volume no próprio dia, informação retrospectiva, e nós exigimos dias completos. Portanto, este é um exercício empírico condicionado a essa base, não uma operação em tempo real plenamente validada. O pequeno gráfico mostra a média dos retornos de cinco minutos em cada mês, não o retorno mensal acumulado.

**Transição:** “Com essa definição de observação, começo pela descrição e pela dependência dos retornos.”

### Notas técnicas — fora da fala

- Retorno em porcentagem: $r_t=100\log(P_{t,\mathrm{fim}}/P_{t,\mathrm{início}})$. No intradiário, a primeira fronteira usa o fechamento do candle iniciado às 09:04; o diário usa abertura às 09:05 e fechamento da janela. Por isso, o diário não é exatamente a soma dos retornos intradiários ancorados no candle anterior.
- O critério de maior volume do próprio dia pertence à construção da fonte. Observar um único contrato por dia no ZIP não demonstra que sua identidade era conhecida antes da abertura. A previsão causal sobre a série fornecida e a seleção ex ante do instrumento são condições diferentes.
- Não se introduzem retornos de rolagem, zeros noturnos, preenchimento de lacunas ou winsorização. A passagem entre contratos permanece identificada; comparar retornos não elimina automaticamente diferenças de microestrutura entre contratos.
- A primeira previsão de 2025 pode carregar o estado final de 2024. Não se usa 2025 para escolher ordens ou estimar parâmetros.
- **Aulas:** Aula 2, pp. 54–58, dinâmica por equações de diferenças; p. 62, operador de defasagem; Aula 4, pp. 38 e 40, amostragem e separação temporal; Aula 6, p. 24, retorno logarítmico.
- **Código:** [construção e auditoria das séries](https://github.com/avilarenan/EAD6034/blob/6e24660054ee39c6037fc1e68aed22d4b78ea6ed/src/ead6034/trading_time_data.py), [construção multiescala](https://github.com/avilarenan/EAD6034/blob/6e24660054ee39c6037fc1e68aed22d4b78ea6ed/src/ead6034/multiscale.py). **Resultados:** [auditoria da sequência](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/sequence_audit.csv), [descrição mensal](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/monthly_description.csv).

### Duas perguntas para ensaiar

1. **“Vocês retiraram todo o efeito do overnight?”** Não. Retiramos o retorno entre sessões do alvo principal; a informação acumulada fora da janela pode continuar influenciando os retornos seguintes. A hipótese é não modelar separadamente essa interrupção.
2. **“O contrato escolhido poderia ser operado exatamente assim em tempo real?”** A base usa volume do próprio dia, conhecido integralmente apenas depois. Isso impede apresentar o exercício como validação completa da escolha ex ante do contrato. O mesmo cuidado vale para a seleção retrospectiva de pregões completos.

Respostas ampliadas no [FAQ](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/PERGUNTAS_PROFESSORES.md).

## Slide 2 — Da descrição às hipóteses de dependência

### Fala principal

Aqui recupero a análise descritiva da primeira entrega, recalculada com a sequência anual. A FAC mostra a correlação do retorno com suas defasagens. A FACP procura retirar a influência das defasagens intermediárias para identificar a associação que permanece.

Na primeira defasagem, FAC e FACP coincidem. Em outras, elas também podem ficar próximas quando as relações intermediárias são fracas. Os desenhos teóricos de AR e MA ajudam na identificação, mas não espero cortes perfeitos em uma amostra real de retornos financeiros.

No minuto, a autocorrelação de primeira ordem é aproximadamente menos zero vírgula zero zero oito. Ela ultrapassa a banda porque temos uma amostra grande, mas sua magnitude é pequena. Significância amostral não informa, sozinha, se conseguiremos reduzir o erro de previsão em outro ano.

Também é importante ler corretamente os eixos: um lag no minuto é diferente de um lag na escala horária. E o aumento do desvio-padrão com a duração da barra não demonstra aumento de previsibilidade; estamos medindo variações acumuladas por mais tempo.

Portanto, estes gráficos orientam os modelos candidatos e mostram limites da identificação visual. A escolha e a validação precisam das próximas etapas.

**Transição:** “Antes de estimar esses modelos, verifico se a hipótese de estacionariedade encontra apoio nos dados.”

### Notas técnicas — fora da fala

- FAC amostral utilizada:

  $
  \widehat\rho_k=
  \frac{\sum_{t=k+1}^{N}(r_t-\bar r)(r_{t-k}-\bar r)}
       {\sum_{t=1}^{N}(r_t-\bar r)^2}.
  $

- A FACP foi calculada por Yule–Walker com autocovariâncias de denominador $N$, `ywmle`. Não é uma média de FACPs diárias nem a regressão agrupada com reinícios usada anteriormente. A representação por regressões da Aula 3, p. 44, ajuda a explicar seu significado; diferentes estimadores convencionais podem diferir em amostra finita.
- Bandas $\pm1{,}96/\sqrt N$: referência pontual aproximada de ruído branco, sem correção de multiplicidade e sem robustez geral à heterocedasticidade. Não interpretar cada cruzamento como descoberta independente.
- FAC(1) do minuto: −0,008118; banda aproximada: ±0,005378. FAC(1) horária: −0,040841; banda: ±0,041655. Comparar esses números não isola efeito causal da agregação.
- Dependência de $r_t$, de $|r_t|$ e de $r_t^2$ corresponde a perguntas diferentes. Autocorrelação linear pequena não implica independência.
- **Aulas:** Aula 3, p. 16, autocorrelação; pp. 43–45, FACP; pp. 47–50, identificação e correlações amostrais. Aula 6, pp. 25–27, comportamento dos retornos e de seus quadrados.
- **Código:** [FAC/FACP convencionais](https://github.com/avilarenan/EAD6034/blob/6e24660054ee39c6037fc1e68aed22d4b78ea6ed/src/ead6034/annual_models.py#L220). **Resultados:** [correlações por escala](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/return_acf_pacf.csv), [estatísticas descritivas](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/descriptive.csv).

### Duas perguntas para ensaiar

1. **“Se a FAC é significativa, por que a previsão não ganhou?”** A relação pode ser pequena, instável ou não compensar o erro de estimação. A FAC usa 2024; o ganho preditivo foi avaliado separadamente em 2025.
2. **“FAC e FACP parecidas significam ARMA(0,0)?”** Não necessariamente. Na primeira defasagem a igualdade é esperada; nas outras, a proximidade pode refletir dependências intermediárias pequenas. A ordem foi escolhida após estimação e comparação dos candidatos.

Respostas ampliadas no [FAQ](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/PERGUNTAS_PROFESSORES.md).

## Slide 3 — Estacionariedade: uma série anual por escala

### Fala principal

Este slide corrige o ponto mais importante levantado sobre a entrega anterior. Antes, cada pregão horário gerava uma série com nove observações. Eram nove barras de uma hora, e não nove minutos. Era muito pouco para uma conclusão confiável sobre raiz unitária.

Agora aplicamos cada teste à sequência anual. Na escala horária temos 2.214 observações, antes das perdas por defasagens. Não tiramos uma média dos testes anteriores: mudamos a hipótese temporal e refizemos a análise. Isso aumenta a informação disponível, mas não torna as observações independentes nem garante a validade de toda aproximação estatística.

ADF e Phillips–Perron têm como hipótese nula a presença de raiz unitária. KPSS parte da estacionariedade. Na especificação principal, com constante, ADF e PP rejeitam raiz unitária e KPSS não rejeita estacionariedade em todas as escalas. Essa leitura sustenta trabalhar com os retornos sem uma diferenciação adicional.

A ressalva está destacada: quando acrescentamos tendência como sensibilidade, KPSS rejeita nas seis escalas. Não escolhemos silenciosamente o resultado mais conveniente. As decisões dependem da especificação determinística e dos valores críticos correspondentes.

Minha conclusão é evidência favorável ao uso de uma equação da média sem raiz unitária na especificação principal, com sensibilidade documentada. Não é uma prova de distribuição estável, variância constante ou ausência de mudanças durante o ano.

**Transição:** “Com essa ressalva explícita, passo à identificação, estimação e diagnóstico dos modelos da média.”

### Notas técnicas — fora da fala

- ADF com constante testa $\gamma=0$ na representação $\Delta r_t=c+\gamma r_{t-1}+\sum_j\delta_j\Delta r_{t-j}+u_t$. A alternativa relevante é $\gamma<0$; sua referência não é o teste t usual de uma regressão estacionária.
- ADF: BIC entre zero e no máximo 12 defasagens; PP: bandwidth automático de Schwert, ponderação Bartlett; KPSS: bandwidth automático dependente dos dados. Todos esses ajustes utilizam apenas 2024.
- Exemplo de sensibilidade em 5 min: KPSS com constante = 0,1909, crítico 5% = 0,4614; com tendência = 0,1774, crítico = 0,1479. A estatística diminui, mas a referência crítica também muda. Isso não demonstra a presença de uma tendência linear.
- As alternativas determinísticas utilizadas foram `c` e `ct`. Não alegar que esta execução testou integralmente todas as três formulações de Dickey–Fuller apresentadas na aula: a especificação sem determinísticos não foi incluída.
- “Não rejeitar” não equivale a “aceitar como verdadeira”. P-valores numéricos iguais a zero indicam o limite da representação do software, não uma probabilidade matematicamente nula.
- **Aulas:** Aula 3, p. 15, estacionariedade em covariância; Aula 5, pp. 23–24 e 28, especificações DF/ADF; p. 35, defasagens; p. 39, baixo poder; pp. 40–42, PP; pp. 43–45, KPSS.
- **Código:** [testes anuais](https://github.com/avilarenan/EAD6034/blob/6e24660054ee39c6037fc1e68aed22d4b78ea6ed/src/ead6034/annual_models.py#L40). **Resultados:** [estatísticas, hipóteses e valores críticos](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/stationarity.csv).

### Duas perguntas para ensaiar

1. **“Aumentar n resolveu o problema dos testes?”** Resolveu a fragmentação em sessões muito curtas. Não eliminou a necessidade de justificar a sequência temporal, os determinísticos, a dependência e a estabilidade da amostra.
2. **“Por que manter d=0 se KPSS com tendência rejeitou?”** Porque a especificação principal foi pré-definida e seus testes apresentam evidência concordante contra raiz unitária. A sensibilidade impede uma conclusão irrestrita; não autoriza diferenciar automaticamente uma série apenas para obter concordância entre testes.

Respostas ampliadas no [FAQ](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/PERGUNTAS_PROFESSORES.md).

## Slide 4 — BIC seleciona; os resíduos ainda precisam passar

### Fala principal

Seguindo Box–Jenkins, estimamos por máxima verossimilhança os modelos ARMA com ordens de zero a cinco, sempre usando 2024. O BIC equilibra ajuste e número de parâmetros; o AIC aparece como informação complementar. Também selecionamos AR e MA de ordem positiva dentro de suas famílias para a comparação preditiva.

O BIC escolheu ARMA dois-dois no minuto e ARMA zero-zero nas outras escalas. Com constante, zero-zero significa prever a média estimada. Não significa que o retorno seja independente ou que nenhuma forma de previsão seja possível.

No minuto, a vantagem de BIC sobre o zero-zero foi somente 1,24. Além disso, os componentes AR e MA quase se cancelam. Eu não interpreto essa escolha como uma dinâmica forte ou uma superioridade inequívoca.

O diagnóstico é uma etapa separada: Ljung–Box rejeita ausência de autocorrelação no minuto. Portanto, esse modelo é um candidato escolhido pelo critério, com inadequação residual documentada. Não o apresento como plenamente validado. Em cinco minutos, não há rejeição no horizonte principal de 24 lags, mas há em outros horizontes exportados; também existe sensibilidade.

Finalmente, o ARCH-LM indica dependência nos quadrados dos resíduos em todas as escalas. Assim, mesmo quando a autocorrelação da média parece limitada, a hipótese de variância condicional constante merece tratamento próprio.

**Transição:** “É essa diferença entre média e variância que motiva a aplicação da Aula 6.”

### Notas técnicas — fora da fala

- Parametrização: $r_t-\mu=\sum_i\phi_i(r_{t-i}-\mu)+\varepsilon_t+\sum_j\theta_j\varepsilon_{t-j}$. A constante publicada por `ARIMA(trend="c")` é $\mu$, média incondicional. Na representação com intercepto, $c=\mu(1-\sum_i\phi_i)$.
- $\mathrm{BIC}=-2\ell(\widehat\theta)+k\log N$, com $k=p+q+2$, incluindo média e variância. A contagem simplificada $p+q+1$ da Aula 4, p. 19, omite a variância comum aos candidatos: incluí-la adiciona a mesma penalidade a todos na mesma amostra, preservando o ranking. Dividir o critério por $N$, como na p. 20, também preserva o ranking. Não comparar níveis de BIC entre frequências diferentes.
- A implementação usa verossimilhança gaussiana exata com inicialização estacionária. A explicação condicional da aula fixa valores iniciais; a diferença de inicialização não cria uma nova família de modelos. Sob não normalidade e heterocedasticidade, a densidade gaussiana é uma hipótese de trabalho, não uma característica empiricamente comprovada.
- Raízes: o código verifica o polinômio de lags fora do círculo unitário. Suas raízes são recíprocas das raízes características da equação de diferenças. Aulas 2, pp. 66–67, apresentam explicitamente ambas as convenções.
- Minuto: AR = (1,5253; −0,9384), MA = (−1,5310; 0,9450). BIC do ARMA(2,2) vence ARMA(0,0) por 1,2399. Coeficientes grandes quase cancelados não equivalem a grande resposta líquida aos choques.
- Ljung–Box: $Q=N(N+2)\sum_{k=1}^{h}\widehat\rho_k^2/(N-k)$, com referência principal $\chi^2_{h-p-q-1}$, conforme Aula 4, p. 27. A referência usual de software com $h-p-q$ também é exportada. O teste não comprova independência e sua calibração pode ser afetada por heterocedasticidade.
- No minuto, p-valor principal = 0,000169. Em 5 min: p = 0,0391, 0,0204 e 0,0366 para h = 10, 12 e 20; p = 0,0780 para h = 24. A escolha do horizonte principal antecedeu a avaliação.
- A Aula 4, p. 25, recomenda descartar modelos inadequados. A avaliação publicada conserva o candidato selecionado como comparação documentada; não certifica que o diagnóstico foi aprovado. `cov_type="none"` significa que esta execução não oferece erros-padrão/testes t de cada coeficiente. Não afirmar que todos são individualmente significativos.
- **Aulas:** Aula 2, pp. 58 e 66–67; Aula 3, pp. 22–26 e 47; Aula 4, pp. 4, 10–20 e 23–27.
- **Código:** [estimação e seleção](https://github.com/avilarenan/EAD6034/blob/6e24660054ee39c6037fc1e68aed22d4b78ea6ed/src/ead6034/annual_models.py#L90), [diagnósticos](https://github.com/avilarenan/EAD6034/blob/6e24660054ee39c6037fc1e68aed22d4b78ea6ed/src/ead6034/annual_models.py#L235). **Resultados:** [grade](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/arma_grid.csv), [modelos escolhidos](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/selected_models.csv), [diagnósticos completos](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/mean_diagnostics.csv).

### Duas perguntas para ensaiar

1. **“Por que reportar um modelo que falha no diagnóstico?”** Para mostrar de forma transparente o resultado do protocolo e seu desempenho, sem confundir seleção por BIC com adequação. A falha faz parte da conclusão crítica, não desaparece porque o modelo foi selecionado.
2. **“ARMA(0,0) significa que a série é ruído branco independente?”** Não. É a estrutura de média escolhida dentro da grade. Dependência nos quadrados, heterocedasticidade e outras limitações continuam possíveis e foram examinadas separadamente.

Respostas ampliadas no [FAQ](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/PERGUNTAS_PROFESSORES.md).

## Slide 5 — Prever a variância não é prever a direção

### Fala principal

A Aula 6 mostra por que uma série pode ter pouca dependência linear nos retornos e, ao mesmo tempo, apresentar períodos de maior ou menor volatilidade. Um choque grande pode indicar maior incerteza no período seguinte sem indicar se o retorno será positivo ou negativo.

Comparo variância constante, ARCH um e GARCH um-um. A estimação é sequencial: primeiro fixo a média ARMA e depois estimo a variância sobre suas inovações. Portanto, não fiz máxima verossimilhança conjunta e as três especificações compartilham exatamente a mesma previsão pontual do retorno.

O BIC escolheu GARCH até trinta minutos, ARCH na hora e variância constante no diário. Nos modelos intradiários escolhidos, a avaliação em 2025 apresentou MSE menor que o da variância constante contra a inovação ao quadrado. Essa inovação é uma proxy ruidosa; a verdadeira variância condicional não é diretamente observada.

Novamente, seleção não encerra o diagnóstico. No minuto, a persistência é alta, cerca de zero vírgula noventa e nove, e permanece dependência nos quadrados dos resíduos padronizados. Também há rejeição no horário e no diário. Não declaro que todos os modelos explicaram adequadamente a volatilidade.

A evidência mais favorável, portanto, está no tamanho condicional dos erros, e mesmo ali exige qualificação. Ela não representa ganho na previsão da direção.

**Transição:** “Voltando à média dos retornos, a comparação preditiva precisa colocar todos os modelos diante do mesmo futuro.”

### Notas técnicas — fora da fala

- $\varepsilon_t=\sqrt{h_t}\,z_t$ e $h_t=\omega+\alpha\varepsilon_{t-1}^2+\beta h_{t-1}$. ARCH(1) fixa $\beta=0$; variância constante fixa $\alpha=\beta=0$.
- Positividade e estabilidade: $\omega>0$, $\alpha,\beta\geq0$, $\alpha+\beta<1$. Persistência é medida por observação da escala; não comparar diretamente a duração física de choques apenas pelos valores de $\alpha+\beta$ de diferentes frequências.
- O BIC condicional compara as variâncias sobre a mesma média fixa e conta somente parâmetros desse bloco. Não deve ser comparado numericamente com o BIC da etapa ARMA.
- Razões MSE/constante dos modelos de variância escolhidos, em ordem 1/5/15/30/60 min: aproximadamente 0,955; 0,970; 0,908; 0,973; 0,984. São resultados descritivos contra o mesmo erro quadrado; não foram acompanhados de DM entre estruturas aninhadas.
- A escolha BIC de treino não é necessariamente o menor MSE observado no teste: no minuto, ARCH(1) apresenta MSE da proxy menor que GARCH(1,1), embora GARCH tenha sido escolhido em 2024. Não trocar retrospectivamente a seleção e apresentar a nova escolha como teste independente.
- Um p-valor arredondado para 1,000 nos diagnósticos não significa probabilidade de 100% de o modelo estar correto. Os testes têm referência aproximada depois da estimação sequencial.
- **Aulas:** Aula 6, pp. 9–16, ARCH/GARCH e restrições; pp. 17–20, identificação, ARCH-LM, padronização e sequência; pp. 24–28, retornos e integração das equações.
- **Código:** [variância condicional](https://github.com/avilarenan/EAD6034/blob/6e24660054ee39c6037fc1e68aed22d4b78ea6ed/src/ead6034/conditional_volatility.py). **Resultados:** [modelos de variância](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/variance_models.csv), [diagnósticos da variância](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/variance_diagnostics.csv).

### Duas perguntas para ensaiar

1. **“GARCH deixou os retornos mais previsíveis?”** Nesta implementação, não alterou sua previsão pontual. Produziu uma previsão diferente da variância condicional sobre a mesma equação da média.
2. **“Se o MSE da proxy caiu, o modelo de volatilidade está validado?”** Não automaticamente. A proxy é ruidosa, a comparação é descritiva e ainda existem rejeições nos diagnósticos de algumas escalas. Ganho de uma métrica e adequação global não são equivalentes.

Respostas ampliadas no [FAQ](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/PERGUNTAS_PROFESSORES.md).

## Slide 6 — A comparação justa usa o mesmo alvo futuro

### Fala principal

Para comparar escalas, não basta colocar lado a lado o erro de um retorno de um minuto e o de uma hora: os alvos têm dispersões diferentes. Por isso, esta tabela intradiária usa exatamente os mesmos 1.989 retornos de sessenta minutos, nas mesmas origens, sem sobreposição.

Por exemplo, às dez e cinco, o modelo de cinco minutos faz doze previsões usando somente a informação disponível naquele instante. Somamos essas previsões para o retorno até onze e cinco. O modelo horário prevê o mesmo intervalo em um passo. Não atualizamos aquela previsão inicial com os retornos que acontecem durante a hora.

Ordens e parâmetros ficaram fixados em 2024. Em 2025, atualizamos apenas os estados com observações já conhecidas. Além do ARMA escolhido, comparo AR, MA, a combinação meio a meio, retorno zero e média de treino. Os pesos da combinação não foram escolhidos olhando o teste.

A leitura da tabela é direta: razão menor que um seria melhora de MSE sobre zero. Todas as razões mostradas são maiores que um. As diferenças são pequenas, mas não favorecem a hipótese inicial. No diário, o alvo é outro e a piora do ARMA é de aproximadamente um vírgula sete por cento.

O Diebold–Mariano compara apenas AR com MA. No horizonte comum, não rejeita igualdade de perda quadrática. Isso não prova equivalência, nem testa o ARMA contra zero. No horizonte nativo existem diferenças significativas em perda absoluta, mas microscópicas; globalmente, nenhum modelo venceu zero também naquele exercício.

**Transição:** “Resta verificar se os recortes de horário e gap mudam essa leitura e delimitar o que podemos concluir sobre o mercado.”

### Notas técnicas — fora da fala

- Alvo comum: $R_{t,60}=\sum_{j=1}^{H}r_{t+j}$, com $H=60,12,4,2,1$ nas bases 1, 5, 15, 30 e 60 min. Previsão: $\widehat R_{t,60}=\sum_{j=1}^{H}\widehat r_{t+j\mid t}$, sempre com a mesma informação em $t$.
- $\mathrm{MSE}=N^{-1}\sum e_t^2$, $\mathrm{MAE}=N^{-1}\sum|e_t|$, ganho relativo $=1-\mathrm{MSE}_{modelo}/\mathrm{MSE}_{zero}$. Retornos e MAE estão em pontos percentuais; MSE, em pontos percentuais ao quadrado. Uma razão 1,002 indica aproximadamente 0,2% mais MSE, não 0,2 ponto percentual de retorno perdido.
- ZERO prevê retorno zero; TRAIN_MEAN usa a média estimada de 2024. Nos ARMA(0,0), a previsão coincide com TRAIN_MEAN. Nos alvos comuns, as médias agregadas de 5, 15, 30 e 60 min coincidem por construção dos blocos completos. Não são confirmações independentes.
- Combinação: $\widehat r^{comb}=0{,}5\widehat r^{AR}+0{,}5\widehat r^{MA}$. As previsões AR e MA são muito próximas; diversidade reduzida limita o benefício possível. Os comparadores pertencem a famílias diferentes, mas não são alternativas radicalmente distintas de modelagem.
- DM usa $d_t=g(e_t^{AR})-g(e_t^{MA})$. Valor negativo favorece AR. A soma de autocovariâncias é retangular, como na fórmula da aula, e não um estimador Bartlett. Há referência t e correção de pequena amostra. Aqui $h_{perda}=1$, porque os alvos sucessivos não se sobrepõem, embora a previsão use vários passos na frequência original. A dependência adicional recebe a truncagem de covariâncias pré-definida.
- No nativo, perda absoluta: p ≈ 0,0000061 em 1 min com diferença média AR−MA de 0,0000000394 p.p.; p ≈ 0,0000124 em 5 min com diferença de −0,0000001391 p.p. Significância estatística não demonstra ganho econômico ou vitória sobre ZERO. Não há ajuste de multiplicidade.
- A causalidade do filtro, a igualdade dos alvos e o isolamento da estimação foram testados. Isso não resolve a seleção retrospectiva do contrato e dos dias na construção da base. Após a avaliação, 2025 já foi consultado: novas escolhas motivadas por seus resultados não teriam validação independente nessa mesma amostra.
- **Aulas:** Aula 4, pp. 32–34, previsão recursiva; pp. 40 e 43–44, avaliação temporal; p. 46, métricas; pp. 48–49, DM; p. 50, combinação. Aula 2, pp. 55–58, iteração e estabilidade da dinâmica.
- **Código:** [previsão e avaliação](https://github.com/avilarenan/EAD6034/blob/6e24660054ee39c6037fc1e68aed22d4b78ea6ed/src/ead6034/forecast_evaluation.py), [asserção de alvos comuns](https://github.com/avilarenan/EAD6034/blob/6e24660054ee39c6037fc1e68aed22d4b78ea6ed/src/ead6034/forecast_pipeline.py#L226). **Resultados:** [acurácia](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/accuracy.csv), [DM](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/diebold_mariano.csv), [alinhamento](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/common_target_alignment.csv), [equivalências](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/forecast_equivalence.csv).

### Duas perguntas para ensaiar

1. **“Usar observações de 2025 no filtro é vazamento?”** Não quando a previsão em cada origem usa apenas o passado, com parâmetros de 2024. Inserir uma realização futura dentro da previsão inicial multipasso seria vazamento; o código impede esse uso.
2. **“Um DM significativo provaria que temos uma estratégia rentável?”** Não. Ele compara perdas dos dois modelos especificados. Rentabilidade exigiria uma regra de decisão, execução e custos, que não foram avaliados. Aqui, as diferenças significativas entre AR e MA são muito pequenas e não implicam vitória sobre zero.

Respostas ampliadas no [FAQ](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/PERGUNTAS_PROFESSORES.md).

## Slide 7 — Conclusão: alcance dos resultados e da metodologia

### Fala principal e conclusão crítica

Na tabela final, o ARMA horário fica ligeiramente pior que zero no início, no meio e no fim da janela, e também nos dois grupos de gap. Isso não quer dizer que os horários sejam iguais. Quer dizer que, nesses recortes, o modelo escolhido não transformou diferenças de comportamento em redução do erro de previsão.

Há pequenos ganhos de outros comparadores em alguns subgrupos. Por exemplo, AR e MA de um minuto melhoram cerca de zero vírgula zero quinze por cento na primeira hora. São recortes descritivos, sem validação como estratégia, e não revertem a ausência de ganho global. Não escolhemos apenas a faixa favorável para declarar sucesso.

Também não identificamos um efeito causal de leilões. A fonte não marca a fase de negociação. Nos regimes históricos confirmados, a nossa janela exclui os calls próprios do WIN, mas pode incluir eventos de abertura ou fechamento das ações. O gap observado também não é um preço oficial de leilão.

Minha conclusão tem três partes. Primeiro, a hipótese de que agregar minutos em horas necessariamente melhora a previsão não recebeu suporte neste desenho: todos os modelos ficaram atrás de zero no alvo comum. Segundo, a evidência mais favorável está na dinâmica da variância, sem melhora automática da direção prevista e com limitações de diagnóstico. Terceiro, o alcance é condicional à amostra: usamos contratos e dias selecionados retrospectivamente, apenas um ativo, parâmetros fixos e nenhuma avaliação após custos.

O resultado não demonstra que o mercado seja imprevisível. Mostra que as dependências identificadas por estes métodos das aulas não se converteram em ganho preditivo global em 2025. A contribuição é separar o que conseguimos ajustar, o que os diagnósticos sustentam e o que efetivamente funcionou fora da amostra.

**Encerramento:** “O código de cada etapa e as tabelas completas estão nos links dos slides. Obrigado.”

### Notas técnicas — fora da fala

- Escala horária, ARMA escolhido: razões MSE/zero de aproximadamente 1,0009 no início, 1,0022 no meio, 1,0036 no fim, 1,0019 em gap alto e 1,0031 em gap baixo. Nenhum desses cinco recortes representa ganho do ARMA sobre zero.
- Há ganhos pequenos dos comparadores positivos em recortes específicos: AR/MA nativos de 1 min na primeira hora ≈ 0,0155%; em gaps baixos ≈ 0,0106%; AR(1) horário em gaps altos ≈ 0,0143%, em 873 alvos. Esses números são percentuais de redução do MSE, não retornos financeiros. No horário, o nativo e o comum são o mesmo exercício, portanto não devem ser contados duas vezes.
- O limiar do gap é definido somente com 2024; o recorte de erros de 2025 é descritivo. Não pressupõe que um gap calculado depois da abertura estivesse disponível para uma previsão emitida antes dela. Grupos por horário e por gap não são aditivos.
- Nas grades históricas confirmadas, o WIN abre às 09:00, com pré-abertura anterior, e tem call próprio a partir de 18:25. A janela 09:05–18:05 não contém esses calls. Em abril de 2024, o call das ações documentado às 16:55–17:00 fica na faixa chamada “meio”; no regime de novembro, o call às 17:55–18:00 fica na faixa “fim”. Ajuste diário, vencimento, negociação contínua e call são eventos distintos.
- A cadeia histórica de horários não está completa para 2024–2025. Não extrapolar uma regra atual nem interpolar meses não documentados. O primeiro/último preço do feed não deve ser chamado automaticamente de preço oficial de abertura/fechamento.
- A escolha do contrato por maior volume do próprio dia e a seleção de pregões completos são escolhas ex post que limitam a execução ex ante. Resultados condicionais sobre a base não demonstram disponibilidade operacional intradiária. Nenhuma afirmação de rentabilidade líquida, execução ou efeito causal de leilões decorre das métricas apresentadas.
- A hipótese não confirmada se refere a estes modelos, frequência, ativo, divisão temporal e alvo. Não foi testada uma afirmação universal de eficiência de mercado ou impossibilidade de previsão. A aplicação das aulas permanece útil mesmo quando a hipótese inicial falha.
- **Aulas:** Aula 3, pp. 8 e 15–16, distinguir ruído branco, estacionariedade e autocorrelação; Aula 4, pp. 25–27 e 45–50, diagnóstico e comparação preditiva; Aula 6, pp. 17–20 e 24–29, média, variância e usos distintos da volatilidade. A discussão de leilões vem da documentação B3, não dessas aulas.
- **Código:** [contexto temporal e gap](https://github.com/avilarenan/EAD6034/blob/6e24660054ee39c6037fc1e68aed22d4b78ea6ed/src/ead6034/trading_time_data.py), [avaliação por recortes](https://github.com/avilarenan/EAD6034/blob/6e24660054ee39c6037fc1e68aed22d4b78ea6ed/src/ead6034/forecast_evaluation.py). **Fontes e resultados:** [horários B3 documentados](https://github.com/avilarenan/EAD6034/blob/6e24660054ee39c6037fc1e68aed22d4b78ea6ed/docs/market_hours_2024_2025.md), [acurácia completa](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/accuracy.csv), [publicação Alpha Lab](https://alphalab.btgpactual.com/datasets/publication:7a74b3ae-90e0-4393-b1e0-01e61c0bedba).

### Duas perguntas para ensaiar

1. **“Então a hipótese sobre os leilões foi rejeitada?”** Não fizemos um teste causal dessa hipótese. Avaliamos escalas e recortes temporais, com limitações de identificação. O que não recebeu suporte foi maior ganho preditivo global na escala horária sob este protocolo.
2. **“Se há um subgrupo com ganho, por que não operar só nele?”** O ganho é pequeno e foi observado num recorte da avaliação, sem teste de uma regra operacional após custos. Escolher agora o subgrupo favorável e usar o mesmo 2025 para comprová-lo confundiria exploração com validação independente.

Respostas ampliadas no [FAQ](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/PERGUNTAS_PROFESSORES.md).

## Cartão de ensaio: cinco frases que não podem perder a qualificação

- “Escolhido por BIC” não significa “diagnosticado como adequado”.
- “Não rejeitou com constante” não significa “a estacionariedade foi provada”; KPSS com tendência rejeitou nas seis escalas.
- “Nenhum ganho global sobre zero” permite pequenos ganhos descritivos em subgrupos, que não foram validados como estratégia.
- “Previsão de variância melhor na proxy” não significa “direção do retorno mais previsível”.
- “Filtro causal e treino separado” não significam “base inteiramente selecionável ex ante”: contrato por volume do próprio dia e pregões completos são escolhas retrospectivas.

As notas aprofundam o material existente. Qualquer revisão de modelos ou regras motivada pelos resultados de 2025 deve ser identificada como exploração posterior, sem apresentar a mesma amostra como uma nova validação independente.


## Cartão de resultados gerado dos CSV

- Seleção BIC da média em 2024: 1 min: ARMA(2,2); 5 min: ARMA(0,0); 15 min: ARMA(0,0); 30 min: ARMA(0,0); 60 min: ARMA(0,0); 1 dia: ARMA(0,0).
- Ljung–Box da média, no horizonte diagnóstico principal, rejeita ausência de autocorrelação em: 1 min. A referência é assintótica e pode ser afetada por heterocedasticidade; não rejeitar não prova ruído independente.
- Alvo comum de 60 minutos, série-base 1 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Alvo comum de 60 minutos, série-base 5 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Alvo comum de 60 minutos, série-base 15 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Alvo comum de 60 minutos, série-base 30 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Alvo comum de 60 minutos, série-base 60 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Seleção BIC condicional da variância em 2024: 1 min: GARCH(1,1); 5 min: GARCH(1,1); 15 min: GARCH(1,1); 30 min: GARCH(1,1); 60 min: ARCH(1); 1 dia: Constant variance. A previsão pontual permanece a mesma.
- As previsões ARMA(0,0) no alvo comum coincidem nas escalas 5 min, 15 min, 30 min, 60 min: somar as médias das barras completas produz a mesma média horária. Isso decorre da agregação dos mesmos dados, não de confirmações independentes de previsibilidade.

Gerador: [Código](https://github.com/avilarenan/EAD6034/blob/6e24660054ee39c6037fc1e68aed22d4b78ea6ed/src/ead6034/forecast_narrative.py).
