# Roteiro oral — EAD6034, entrega cumulativa de 21/09/2026

Renan de Luca Avila · Prof. Leandro Maciel · Seminário em 28/09/2026.

Este roteiro acompanha os **sete slides existentes**, reunindo as entregas de 31/08, 14/09 e 21/09. A **fala principal inteira, incluindo as transições, tem aproximadamente 510 palavras** e foi planejada para **cinco minutos**, com pequenas pausas para apontar gráficos e tabelas. O tempo é uma estimativa de ensaio, não uma duração cronometrada. A redução é uma escolha de apresentação; o limite de 15 minutos previsto no enunciado permanece inalterado.

Leia apenas a seção **Roteiro principal — cinco minutos** durante a apresentação. As **notas de apoio**, reunidas depois dos sete slides, são material de preparação e consulta nas perguntas, fora dos cinco minutos. As referências às aulas usam páginas físicas dos PDFs, contadas a partir de 1. Foram consultadas as Aulas 2–6 disponíveis; não se atribuem conteúdos às Aulas 0 ou 1.

[Apresentação cumulativa](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/ENTREGA_21_09.pdf) · [Relatório completo](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/RELATORIO_21_09.md) · [Questões](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/questões.md) · [Código Python](https://github.com/avilarenan/EAD6034/tree/main/src/ead6034) · [Dataset no BTG Alpha Lab](https://alphalab.btgpactual.com/datasets/publication:7a74b3ae-90e0-4393-b1e0-01e61c0bedba).

## Distribuição dos cinco minutos

| Slide | Tempo | Relógio acumulado | Mensagem essencial |
| --- | --- | --- | --- |
| 1 — Dois anos, seis escalas, uma regra temporal | 35 s | 00:00–00:35 | Hipótese, amostra e sequência entre pregões |
| 2 — Da descrição às hipóteses de dependência | 35 s | 00:35–01:10 | Correlação pequena não garante previsão útil |
| 3 — Estacionariedade: uma série anual por escala | 45 s | 01:10–01:55 | Correção de n=9 e sensibilidade do KPSS |
| 4 — BIC seleciona; os resíduos ainda precisam passar | 45 s | 01:55–02:40 | Seleção não equivale a adequação |
| 5 — Prever a variância não é prever a direção | 40 s | 02:40–03:20 | Melhora parcial da variância, média inalterada |
| 6 — A comparação justa usa o mesmo alvo futuro | 55 s | 03:20–04:15 | Mesmo alvo de 60 minutos; ausência de ganho global |
| 7 — Conclusão: alcance dos resultados e da metodologia | 45 s | 04:15–05:00 | Hipótese não confirmada e limites de interpretação |

## Roteiro principal — cinco minutos

### Slide 1 — Dois anos, seis escalas, uma regra temporal

A hipótese era que retornos horários seriam mais previsíveis que os de minutos. Usamos WIN, seis escalas, treino em 2024 e avaliação em 2025. Emendamos barras entre pregões: excluímos o retorno noturno, mas permitimos defasagens entre dias. Isso não elimina efeitos do overnight. O contrato escolhido pelo volume do próprio dia limita a interpretação operacional. Começo pela dependência observada.

### Slide 2 — Da descrição às hipóteses de dependência

A FAC mede correlação com retornos anteriores; a FACP desconta as defasagens intermediárias. Um lag representa uma barra da respectiva escala, não a mesma quantidade de minutos em todos os gráficos. No minuto, a correlação inicial é aproximadamente menos 0,008: pequena, embora significativa na amostra grande. Significância não garante previsão útil. O aumento da dispersão em barras maiores também não demonstra maior previsibilidade: elas acumulam mais tempo. Antes da estimação, precisamos discutir estacionariedade.

### Slide 3 — Estacionariedade: uma série anual por escala

Corrigimos a análise horária anterior: eram nove barras por pregão; agora usamos uma sequência anual com 2.214 observações. Não calculamos a média de testes diários. ADF e PP rejeitam raiz unitária; KPSS, com constante, não rejeita estacionariedade nas seis escalas. Entretanto, KPSS com tendência rejeita em todas. Trabalhamos com retornos sem diferenciação adicional, sob a especificação principal, reconhecendo essa sensibilidade. A amostra maior resolve a fragmentação, mas não prova estabilidade da distribuição. Passo aos modelos da média.

### Slide 4 — BIC seleciona; os resíduos ainda precisam passar

O BIC penaliza complexidade e selecionou ARMA dois-dois no minuto e zero-zero nas demais escalas. Zero-zero com constante prevê a média estimada; não significa independência. Também comparamos famílias AR e MA de ordem positiva. No minuto, a vantagem de BIC foi apenas 1,24 e Ljung–Box ainda rejeitou ausência de autocorrelação residual. Portanto, seleção não equivale a adequação. O ARCH-LM indicou dependência nos quadrados em todas as escalas, motivando a análise separada da variância.

### Slide 5 — Prever a variância não é prever a direção

Na variância, comparamos constante, ARCH e GARCH, mantendo a média ARMA fixa. GARCH foi escolhido até trinta minutos; ARCH, na hora; constante, no diário. Os modelos intradiários melhoraram descritivamente o erro contra a inovação ao quadrado, uma proxy ruidosa da variância. Persistiram falhas de diagnóstico, inclusive no minuto. Essa melhora não altera a previsão pontual do retorno. Para compará-la entre escalas, usamos o mesmo alvo futuro.

### Slide 6 — A comparação justa usa o mesmo alvo futuro

Todas as escalas intradiárias preveem os mesmos 1.989 intervalos de sessenta minutos. O modelo de cinco minutos soma doze previsões emitidas na mesma origem, sem observar antecipadamente o restante da hora. Parâmetros e pesos ficaram fixados em 2024. Em 2025, nenhum modelo superou globalmente retorno zero nesse alvo; o ARMA ficou cerca de 0,2% pior em MSE. O Diebold–Mariano comparou AR com MA: não rejeitar igualdade não prova equivalência, nem testa a comparação com zero. Como interpretar isso diante da hipótese inicial?

### Slide 7 — Conclusão: alcance dos resultados e da metodologia

A maior previsibilidade horária não recebeu suporte neste desenho. Houve melhora parcial na previsão da variância, sem ganho global na média. Diferenças por horário ou gap são associações: os candles não identificam fases de leilão, portanto não testamos seu efeito causal. Além da seleção retrospectiva do contrato e dos dias, analisamos somente WIN e não avaliamos custos. Concluímos sobre estes modelos e esta amostra, sem afirmar imprevisibilidade geral do mercado. Código e resultados estão nos links.

## Notas de apoio — fora dos cinco minutos

As notas abaixo preservam os detalhes técnicos para preparação e respostas. Não fazem parte da fala principal. As 45 respostas ampliadas estão em [Questões](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/questões.md).

### Apoio ao slide 1 — Dois anos, seis escalas, uma regra temporal

#### Notas técnicas — fora da fala

- Retorno em porcentagem: $r_t=100\log(P_{t,\mathrm{fim}}/P_{t,\mathrm{início}})$. No intradiário, a primeira fronteira usa o fechamento do candle iniciado às 09:04; o diário usa abertura às 09:05 e fechamento da janela. Por isso, o diário não é exatamente a soma dos retornos intradiários ancorados no candle anterior.
- O critério de maior volume do próprio dia pertence à construção da fonte. Observar um único contrato por dia no ZIP não demonstra que sua identidade era conhecida antes da abertura. A previsão causal sobre a série fornecida e a seleção ex ante do instrumento são condições diferentes.
- Não se introduzem retornos de rolagem, zeros noturnos, preenchimento de lacunas ou winsorização. A passagem entre contratos permanece identificada; comparar retornos não elimina automaticamente diferenças de microestrutura entre contratos.
- A primeira previsão de 2025 pode carregar o estado final de 2024. Não se usa 2025 para escolher ordens ou estimar parâmetros.
- **Aulas:** Aula 2, pp. 54–58, dinâmica por equações de diferenças; p. 62, operador de defasagem; Aula 4, pp. 38 e 40, amostragem e separação temporal; Aula 6, p. 24, retorno logarítmico.
- **Código:** [construção e auditoria das séries](https://github.com/avilarenan/EAD6034/blob/49ece87d9558e94286c2c751808be933010f7053/src/ead6034/trading_time_data.py), [construção multiescala](https://github.com/avilarenan/EAD6034/blob/49ece87d9558e94286c2c751808be933010f7053/src/ead6034/multiscale.py). **Resultados:** [auditoria da sequência](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/sequence_audit.csv), [descrição mensal](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/monthly_description.csv).

#### Duas perguntas para ensaiar

1. **“Vocês retiraram todo o efeito do overnight?”** Não. Retiramos o retorno entre sessões do alvo principal; a informação acumulada fora da janela pode continuar influenciando os retornos seguintes. A hipótese é não modelar separadamente essa interrupção.
2. **“O contrato escolhido poderia ser operado exatamente assim em tempo real?”** A base usa volume do próprio dia, conhecido integralmente apenas depois. Isso impede apresentar o exercício como validação completa da escolha ex ante do contrato. O mesmo cuidado vale para a seleção retrospectiva de pregões completos.

Respostas ampliadas no [FAQ](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/questões.md).

### Apoio ao slide 2 — Da descrição às hipóteses de dependência

#### Notas técnicas — fora da fala

- FAC amostral utilizada:

  $$
  \widehat\rho_k=
  \frac{\sum_{t=k+1}^{N}(r_t-\bar r)(r_{t-k}-\bar r)}
       {\sum_{t=1}^{N}(r_t-\bar r)^2}.
  $$

- A FACP foi calculada por Yule–Walker com autocovariâncias de denominador $N$, `ywmle`. Não é uma média de FACPs diárias nem a regressão agrupada com reinícios usada anteriormente. A representação por regressões da Aula 3, p. 44, ajuda a explicar seu significado; diferentes estimadores convencionais podem diferir em amostra finita.
- Bandas $\pm1{,}96/\sqrt N$: referência pontual aproximada de ruído branco, sem correção de multiplicidade e sem robustez geral à heterocedasticidade. Não interpretar cada cruzamento como descoberta independente.
- FAC(1) do minuto: −0,008118; banda aproximada: ±0,005378. FAC(1) horária: −0,040841; banda: ±0,041655. Comparar esses números não isola efeito causal da agregação.
- Dependência de $r_t$, de $|r_t|$ e de $r_t^2$ corresponde a perguntas diferentes. Autocorrelação linear pequena não implica independência.
- **Aulas:** Aula 3, p. 16, autocorrelação; pp. 43–45, FACP; pp. 47–50, identificação e correlações amostrais. Aula 6, pp. 25–27, comportamento dos retornos e de seus quadrados.
- **Código:** [FAC/FACP convencionais](https://github.com/avilarenan/EAD6034/blob/49ece87d9558e94286c2c751808be933010f7053/src/ead6034/annual_models.py#L220). **Resultados:** [correlações por escala](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/return_acf_pacf.csv), [estatísticas descritivas](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/descriptive.csv).

#### Duas perguntas para ensaiar

1. **“Se a FAC é significativa, por que a previsão não ganhou?”** A relação pode ser pequena, instável ou não compensar o erro de estimação. A FAC usa 2024; o ganho preditivo foi avaliado separadamente em 2025.
2. **“FAC e FACP parecidas significam ARMA(0,0)?”** Não necessariamente. Na primeira defasagem a igualdade é esperada; nas outras, a proximidade pode refletir dependências intermediárias pequenas. A ordem foi escolhida após estimação e comparação dos candidatos.

Respostas ampliadas no [FAQ](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/questões.md).

### Apoio ao slide 3 — Estacionariedade: uma série anual por escala

#### Notas técnicas — fora da fala

- ADF com constante testa $\gamma=0$ na representação $\Delta r_t=c+\gamma r_{t-1}+\sum_j\delta_j\Delta r_{t-j}+u_t$. A alternativa relevante é $\gamma<0$; sua referência não é o teste t usual de uma regressão estacionária.
- ADF: BIC entre zero e no máximo 12 defasagens; PP: bandwidth automático de Schwert, ponderação Bartlett; KPSS: bandwidth automático dependente dos dados. Todos esses ajustes utilizam apenas 2024.
- Exemplo de sensibilidade em 5 min: KPSS com constante = 0,1909, crítico 5% = 0,4614; com tendência = 0,1774, crítico = 0,1479. A estatística diminui, mas a referência crítica também muda. Isso não demonstra a presença de uma tendência linear.
- As alternativas determinísticas utilizadas foram `c` e `ct`. Não alegar que esta execução testou integralmente todas as três formulações de Dickey–Fuller apresentadas na aula: a especificação sem determinísticos não foi incluída.
- “Não rejeitar” não equivale a “aceitar como verdadeira”. P-valores numéricos iguais a zero indicam o limite da representação do software, não uma probabilidade matematicamente nula.
- **Aulas:** Aula 3, p. 15, estacionariedade em covariância; Aula 5, pp. 23–24 e 28, especificações DF/ADF; p. 35, defasagens; p. 39, baixo poder; pp. 40–42, PP; pp. 43–45, KPSS.
- **Código:** [testes anuais](https://github.com/avilarenan/EAD6034/blob/49ece87d9558e94286c2c751808be933010f7053/src/ead6034/annual_models.py#L40). **Resultados:** [estatísticas, hipóteses e valores críticos](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/stationarity.csv).

#### Duas perguntas para ensaiar

1. **“Aumentar n resolveu o problema dos testes?”** Resolveu a fragmentação em sessões muito curtas. Não eliminou a necessidade de justificar a sequência temporal, os determinísticos, a dependência e a estabilidade da amostra.
2. **“Por que manter d=0 se KPSS com tendência rejeitou?”** Porque a especificação principal foi pré-definida e seus testes apresentam evidência concordante contra raiz unitária. A sensibilidade impede uma conclusão irrestrita; não autoriza diferenciar automaticamente uma série apenas para obter concordância entre testes.

Respostas ampliadas no [FAQ](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/questões.md).

### Apoio ao slide 4 — BIC seleciona; os resíduos ainda precisam passar

#### Notas técnicas — fora da fala

- Parametrização: $r_t-\mu=\sum_i\phi_i(r_{t-i}-\mu)+\varepsilon_t+\sum_j\theta_j\varepsilon_{t-j}$. A constante publicada por `ARIMA(trend="c")` é $\mu$, média incondicional. Na representação com intercepto, $c=\mu(1-\sum_i\phi_i)$.
- $\mathrm{BIC}=-2\ell(\widehat\theta)+k\log N$, com $k=p+q+2$, incluindo média e variância. A contagem simplificada $p+q+1$ da Aula 4, p. 19, omite a variância comum aos candidatos: incluí-la adiciona a mesma penalidade a todos na mesma amostra, preservando o ranking. Dividir o critério por $N$, como na p. 20, também preserva o ranking. Não comparar níveis de BIC entre frequências diferentes.
- A implementação usa verossimilhança gaussiana exata com inicialização estacionária. A explicação condicional da aula fixa valores iniciais; a diferença de inicialização não cria uma nova família de modelos. Sob não normalidade e heterocedasticidade, a densidade gaussiana é uma hipótese de trabalho, não uma característica empiricamente comprovada.
- Raízes: o código verifica o polinômio de lags fora do círculo unitário. Suas raízes são recíprocas das raízes características da equação de diferenças. Aulas 2, pp. 66–67, apresentam explicitamente ambas as convenções.
- Minuto: AR = (1,5253; −0,9384), MA = (−1,5310; 0,9450). BIC do ARMA(2,2) vence ARMA(0,0) por 1,2399. Coeficientes grandes quase cancelados não equivalem a grande resposta líquida aos choques.
- Ljung–Box: $Q=N(N+2)\sum_{k=1}^{h}\widehat\rho_k^2/(N-k)$, com referência principal $\chi^2_{h-p-q-1}$, conforme Aula 4, p. 27. A referência usual de software com $h-p-q$ também é exportada. O teste não comprova independência e sua calibração pode ser afetada por heterocedasticidade.
- No minuto, p-valor principal = 0,000169. Em 5 min: p = 0,0391, 0,0204 e 0,0366 para h = 10, 12 e 20; p = 0,0780 para h = 24. A escolha do horizonte principal antecedeu a avaliação.
- A Aula 4, p. 25, recomenda descartar modelos inadequados. A avaliação publicada conserva o candidato selecionado como comparação documentada; não certifica que o diagnóstico foi aprovado. `cov_type="none"` significa que esta execução não oferece erros-padrão/testes t de cada coeficiente. Não afirmar que todos são individualmente significativos.
- **Aulas:** Aula 2, pp. 58 e 66–67; Aula 3, pp. 22–26 e 47; Aula 4, pp. 4, 10–20 e 23–27.
- **Código:** [estimação e seleção](https://github.com/avilarenan/EAD6034/blob/49ece87d9558e94286c2c751808be933010f7053/src/ead6034/annual_models.py#L90), [diagnósticos](https://github.com/avilarenan/EAD6034/blob/49ece87d9558e94286c2c751808be933010f7053/src/ead6034/annual_models.py#L235). **Resultados:** [grade](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/arma_grid.csv), [modelos escolhidos](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/selected_models.csv), [diagnósticos completos](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/mean_diagnostics.csv).

#### Duas perguntas para ensaiar

1. **“Por que reportar um modelo que falha no diagnóstico?”** Para mostrar de forma transparente o resultado do protocolo e seu desempenho, sem confundir seleção por BIC com adequação. A falha faz parte da conclusão crítica, não desaparece porque o modelo foi selecionado.
2. **“ARMA(0,0) significa que a série é ruído branco independente?”** Não. É a estrutura de média escolhida dentro da grade. Dependência nos quadrados, heterocedasticidade e outras limitações continuam possíveis e foram examinadas separadamente.

Respostas ampliadas no [FAQ](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/questões.md).

### Apoio ao slide 5 — Prever a variância não é prever a direção

#### Notas técnicas — fora da fala

- $\varepsilon_t=\sqrt{h_t}\,z_t$ e $h_t=\omega+\alpha\varepsilon_{t-1}^2+\beta h_{t-1}$. ARCH(1) fixa $\beta=0$; variância constante fixa $\alpha=\beta=0$.
- Positividade e estabilidade: $\omega>0$, $\alpha,\beta\geq0$, $\alpha+\beta<1$. Persistência é medida por observação da escala; não comparar diretamente a duração física de choques apenas pelos valores de $\alpha+\beta$ de diferentes frequências.
- O BIC condicional compara as variâncias sobre a mesma média fixa e conta somente parâmetros desse bloco. Não deve ser comparado numericamente com o BIC da etapa ARMA.
- Razões MSE/constante dos modelos de variância escolhidos, em ordem 1/5/15/30/60 min: aproximadamente 0,955; 0,970; 0,908; 0,973; 0,984. São resultados descritivos contra o mesmo erro quadrado; não foram acompanhados de DM entre estruturas aninhadas.
- A escolha BIC de treino não é necessariamente o menor MSE observado no teste: no minuto, ARCH(1) apresenta MSE da proxy menor que GARCH(1,1), embora GARCH tenha sido escolhido em 2024. Não trocar retrospectivamente a seleção e apresentar a nova escolha como teste independente.
- Um p-valor arredondado para 1,000 nos diagnósticos não significa probabilidade de 100% de o modelo estar correto. Os testes têm referência aproximada depois da estimação sequencial.
- **Aulas:** Aula 6, pp. 9–16, ARCH/GARCH e restrições; pp. 17–20, identificação, ARCH-LM, padronização e sequência; pp. 24–28, retornos e integração das equações.
- **Código:** [variância condicional](https://github.com/avilarenan/EAD6034/blob/49ece87d9558e94286c2c751808be933010f7053/src/ead6034/conditional_volatility.py). **Resultados:** [modelos de variância](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/variance_models.csv), [diagnósticos da variância](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/variance_diagnostics.csv).

#### Duas perguntas para ensaiar

1. **“GARCH deixou os retornos mais previsíveis?”** Nesta implementação, não alterou sua previsão pontual. Produziu uma previsão diferente da variância condicional sobre a mesma equação da média.
2. **“Se o MSE da proxy caiu, o modelo de volatilidade está validado?”** Não automaticamente. A proxy é ruidosa, a comparação é descritiva e ainda existem rejeições nos diagnósticos de algumas escalas. Ganho de uma métrica e adequação global não são equivalentes.

Respostas ampliadas no [FAQ](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/questões.md).

### Apoio ao slide 6 — A comparação justa usa o mesmo alvo futuro

#### Notas técnicas — fora da fala

- Alvo comum: $R_{t,60}=\sum_{j=1}^{H}r_{t+j}$, com $H=60,12,4,2,1$ nas bases 1, 5, 15, 30 e 60 min. Previsão: $\widehat R_{t,60}=\sum_{j=1}^{H}\widehat r_{t+j\mid t}$, sempre com a mesma informação em $t$.
- $\mathrm{MSE}=N^{-1}\sum e_t^2$, $\mathrm{MAE}=N^{-1}\sum|e_t|$, ganho relativo $=1-\mathrm{MSE}_{modelo}/\mathrm{MSE}_{zero}$. Retornos e MAE estão em pontos percentuais; MSE, em pontos percentuais ao quadrado. Uma razão 1,002 indica aproximadamente 0,2% mais MSE, não 0,2 ponto percentual de retorno perdido.
- ZERO prevê retorno zero; TRAIN_MEAN usa a média estimada de 2024. Nos ARMA(0,0), a previsão coincide com TRAIN_MEAN. Nos alvos comuns, as médias agregadas de 5, 15, 30 e 60 min coincidem por construção dos blocos completos. Não são confirmações independentes.
- Combinação: $\widehat r^{comb}=0{,}5\widehat r^{AR}+0{,}5\widehat r^{MA}$. As previsões AR e MA são muito próximas; diversidade reduzida limita o benefício possível. Os comparadores pertencem a famílias diferentes, mas não são alternativas radicalmente distintas de modelagem.
- DM usa $d_t=g(e_t^{AR})-g(e_t^{MA})$. Valor negativo favorece AR. A soma de autocovariâncias é retangular, como na fórmula da aula, e não um estimador Bartlett. Há referência t e correção de pequena amostra. Aqui $h_{perda}=1$, porque os alvos sucessivos não se sobrepõem, embora a previsão use vários passos na frequência original. A dependência adicional recebe a truncagem de covariâncias pré-definida.
- No nativo, perda absoluta: p ≈ 0,0000061 em 1 min com diferença média AR−MA de 0,0000000394 p.p.; p ≈ 0,0000124 em 5 min com diferença de −0,0000001391 p.p. Significância estatística não demonstra ganho econômico ou vitória sobre ZERO. Não há ajuste de multiplicidade.
- A causalidade do filtro, a igualdade dos alvos e o isolamento da estimação foram testados. Isso não resolve a seleção retrospectiva do contrato e dos dias na construção da base. Após a avaliação, 2025 já foi consultado: novas escolhas motivadas por seus resultados não teriam validação independente nessa mesma amostra.
- **Aulas:** Aula 4, pp. 32–34, previsão recursiva; pp. 40 e 43–44, avaliação temporal; p. 46, métricas; pp. 48–49, DM; p. 50, combinação. Aula 2, pp. 55–58, iteração e estabilidade da dinâmica.
- **Código:** [previsão e avaliação](https://github.com/avilarenan/EAD6034/blob/49ece87d9558e94286c2c751808be933010f7053/src/ead6034/forecast_evaluation.py), [asserção de alvos comuns](https://github.com/avilarenan/EAD6034/blob/49ece87d9558e94286c2c751808be933010f7053/src/ead6034/forecast_pipeline.py#L226). **Resultados:** [acurácia](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/accuracy.csv), [DM](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/diebold_mariano.csv), [alinhamento](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/common_target_alignment.csv), [equivalências](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/forecast_equivalence.csv).

#### Duas perguntas para ensaiar

1. **“Usar observações de 2025 no filtro é vazamento?”** Não quando a previsão em cada origem usa apenas o passado, com parâmetros de 2024. Inserir uma realização futura dentro da previsão inicial multipasso seria vazamento; o código impede esse uso.
2. **“Um DM significativo provaria que temos uma estratégia rentável?”** Não. Ele compara perdas dos dois modelos especificados. Rentabilidade exigiria uma regra de decisão, execução e custos, que não foram avaliados. Aqui, as diferenças significativas entre AR e MA são muito pequenas e não implicam vitória sobre zero.

Respostas ampliadas no [FAQ](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/questões.md).

### Apoio ao slide 7 — Conclusão: alcance dos resultados e da metodologia

#### Notas técnicas — fora da fala

- Escala horária, ARMA escolhido: razões MSE/zero de aproximadamente 1,0009 no início, 1,0022 no meio, 1,0036 no fim, 1,0019 em gap alto e 1,0031 em gap baixo. Nenhum desses cinco recortes representa ganho do ARMA sobre zero.
- Há ganhos pequenos dos comparadores positivos em recortes específicos: AR/MA nativos de 1 min na primeira hora ≈ 0,0155%; em gaps baixos ≈ 0,0106%; AR(1) horário em gaps altos ≈ 0,0143%, em 873 alvos. Esses números são percentuais de redução do MSE, não retornos financeiros. No horário, o nativo e o comum são o mesmo exercício, portanto não devem ser contados duas vezes.
- O limiar do gap é definido somente com 2024; o recorte de erros de 2025 é descritivo. Não pressupõe que um gap calculado depois da abertura estivesse disponível para uma previsão emitida antes dela. Grupos por horário e por gap não são aditivos.
- Nas grades históricas confirmadas, o WIN abre às 09:00, com pré-abertura anterior, e tem call próprio a partir de 18:25. A janela 09:05–18:05 não contém esses calls. Em abril de 2024, o call das ações documentado às 16:55–17:00 fica na faixa chamada “meio”; no regime de novembro, o call às 17:55–18:00 fica na faixa “fim”. Ajuste diário, vencimento, negociação contínua e call são eventos distintos.
- A cadeia histórica de horários não está completa para 2024–2025. Não extrapolar uma regra atual nem interpolar meses não documentados. O primeiro/último preço do feed não deve ser chamado automaticamente de preço oficial de abertura/fechamento.
- A escolha do contrato por maior volume do próprio dia e a seleção de pregões completos são escolhas ex post que limitam a execução ex ante. Resultados condicionais sobre a base não demonstram disponibilidade operacional intradiária. Nenhuma afirmação de rentabilidade líquida, execução ou efeito causal de leilões decorre das métricas apresentadas.
- A hipótese não confirmada se refere a estes modelos, frequência, ativo, divisão temporal e alvo. Não foi testada uma afirmação universal de eficiência de mercado ou impossibilidade de previsão. A aplicação das aulas permanece útil mesmo quando a hipótese inicial falha.
- **Aulas:** Aula 3, pp. 8 e 15–16, distinguir ruído branco, estacionariedade e autocorrelação; Aula 4, pp. 25–27 e 45–50, diagnóstico e comparação preditiva; Aula 6, pp. 17–20 e 24–29, média, variância e usos distintos da volatilidade. A discussão de leilões vem da documentação B3, não dessas aulas.
- **Código:** [contexto temporal e gap](https://github.com/avilarenan/EAD6034/blob/49ece87d9558e94286c2c751808be933010f7053/src/ead6034/trading_time_data.py), [avaliação por recortes](https://github.com/avilarenan/EAD6034/blob/49ece87d9558e94286c2c751808be933010f7053/src/ead6034/forecast_evaluation.py). **Fontes e resultados:** [horários B3 documentados](https://github.com/avilarenan/EAD6034/blob/49ece87d9558e94286c2c751808be933010f7053/docs/market_hours_2024_2025.md), [acurácia completa](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/tables/accuracy.csv), [publicação Alpha Lab](https://alphalab.btgpactual.com/datasets/publication:7a74b3ae-90e0-4393-b1e0-01e61c0bedba).

#### Duas perguntas para ensaiar

1. **“Então a hipótese sobre os leilões foi rejeitada?”** Não fizemos um teste causal dessa hipótese. Avaliamos escalas e recortes temporais, com limitações de identificação. O que não recebeu suporte foi maior ganho preditivo global na escala horária sob este protocolo.
2. **“Se há um subgrupo com ganho, por que não operar só nele?”** O ganho é pequeno e foi observado num recorte da avaliação, sem teste de uma regra operacional após custos. Escolher agora o subgrupo favorável e usar o mesmo 2025 para comprová-lo confundiria exploração com validação independente.

Respostas ampliadas no [FAQ](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/questões.md).

## Cartão de ensaio

- Seleção por BIC, adequação dos resíduos e ganho preditivo são resultados diferentes.
- A sequência anual corrige a fragmentação; não elimina sensibilidade dos testes.
- Excluir o retorno noturno não elimina informação acumulada durante a noite.
- Melhora na previsão da variância não implica melhora da média ou da direção.
- A hipótese horária não recebeu suporte global neste desenho; efeitos causais dos leilões não foram identificados.
- Revisões motivadas pelos resultados de 2025 exigiriam outra amostra para validação independente.


## Cartão de resultados — apoio, fora dos cinco minutos

- Seleção BIC da média em 2024: 1 min: ARMA(2,2); 5 min: ARMA(0,0); 15 min: ARMA(0,0); 30 min: ARMA(0,0); 60 min: ARMA(0,0); 1 dia: ARMA(0,0).
- Ljung–Box da média, no horizonte diagnóstico principal, rejeita ausência de autocorrelação em: 1 min. A referência é assintótica e pode ser afetada por heterocedasticidade; não rejeitar não prova ruído independente.
- Alvo comum de 60 minutos, série-base 1 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Alvo comum de 60 minutos, série-base 5 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Alvo comum de 60 minutos, série-base 15 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Alvo comum de 60 minutos, série-base 30 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Alvo comum de 60 minutos, série-base 60 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Seleção BIC condicional da variância em 2024: 1 min: GARCH(1,1); 5 min: GARCH(1,1); 15 min: GARCH(1,1); 30 min: GARCH(1,1); 60 min: ARCH(1); 1 dia: Constant variance. A previsão pontual permanece a mesma.
- As previsões ARMA(0,0) no alvo comum coincidem nas escalas 5 min, 15 min, 30 min, 60 min: somar as médias das barras completas produz a mesma média horária. Isso decorre da agregação dos mesmos dados, não de confirmações independentes de previsibilidade.

Gerador: [Código](https://github.com/avilarenan/EAD6034/blob/49ece87d9558e94286c2c751808be933010f7053/src/ead6034/forecast_narrative.py).
