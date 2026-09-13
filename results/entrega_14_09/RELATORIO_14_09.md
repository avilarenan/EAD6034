# EAD6034 - Entrega de 14/09/2026

**Renan de Luca Avila - Professor Leandro Maciel - FEA-USP**

## Pergunta e escopo

Como a dinâmica linear dos retornos do WIN varia entre 1, 5, 15, 30 e 60 minutos e o diário? Esta etapa examina estacionariedade e executa identificação, estimação e diagnóstico Box-Jenkins. A replicação adaptada de Matías e Reboredo (2012) continua centrada em 5 minutos. A dimensão executada da proposta é a escala temporal de um único futuro de índice. O arquivo não sustenta segundos, midquotes, ações ou opções.

O BIC selecionou 1 minuto ARMA(0,0), 5 minutos ARMA(0,0), 15 minutos ARMA(0,0), 30 minutos ARMA(0,0), 60 minutos ARMA(0,0), 1 dia ARMA(0,0). A escolha é uma referência para a equação da média. A avaliação dos resíduos abaixo impede confundir seleção por BIC com adequação de um modelo de ruído branco homoscedástico.

## 1. Amostra e fronteiras

Identificação de **02/01/2024 a 30/12/2024**, com **246 pregões completos comuns**, de 09:05 a 18:05 em São Paulo. O código filtra 2024 **antes** da auditoria, da seleção dos dias e de qualquer teste ou estimação. Nenhuma observação de 2025 entra nos procedimentos desta entrega. O hash do arquivo bruto é apenas uma identificação da fonte completa.

| Escala | N total | Segmentos para ARMA | Observações por segmento |
|---|---|---|---|
| 1 minuto | 132.840 | 246 | 540 |
| 5 minutos | 26.568 | 246 | 108 |
| 15 minutos | 8.856 | 246 | 36 |
| 30 minutos | 4.428 | 246 | 18 |
| 60 minutos | 2.214 | 246 | 9 |
| 1 dia | 246 | 10 | 2 a 45 |


As barras e os retornos reproduzem a entrega de 31/08. Intradiário: 100 log(C_t/C_anterior), ancorado no fechamento do candle iniciado às 09:04. Diário: 100 log(C_final/O_09:05). A soma dos retornos intradiários usa a fronteira close-to-close e difere do open-to-close pela passagem do close 09:04 ao open 09:05. Não há winsorização, interpolação ou retorno atravessando pregão ou contrato.

Cada pregão é um segmento intradiário. No diário, exclusões, lacuna da fonte de 16/04/2024 e mudanças de contrato dividem a sequência em dez segmentos de comprimentos 25, 3, 16, 25, 35, 2, 45, 45, 43 e 7. Para os testes, os três segmentos com menos de oito observações ficam explicitamente sem resultado. Os dez segmentos e as 246 observações entram na verossimilhança ARMA. A reinicialização implica que o modelo não carrega estado ou informação defasada através dessas fronteiras.

## 2. Estacionariedade: definição e execução

ADF e PP têm H0 de raiz unitária. KPSS tem H0 de estacionariedade em torno dos termos determinísticos. Rejeitar raiz unitária não prova todas as condições de estacionariedade fraca, nem elimina sazonalidade da variância, quebras ou dependência em magnitude.

Aplicam-se **testes convencionais separadamente a cada segmento**. Concatenar dias criaria defasagens artificiais. Também não se estimou uma regressão pooled com resets para então aplicar indevidamente os valores críticos de uma única série. As taxas de rejeição e medianas são descritivas, sem p-valor combinado ou conclusão universal para todos os pregões. Não há correção de multiplicidade nas decisões individuais a 5%.

Especificação principal: constante, sem tendência (`c`), pois a variável é retorno. ADF: seleção BIC entre 0 e K defasagens das diferenças, com K=min(12, max(0,floor(n/5)-1), max(0,floor(n/2)-3)). PP: estatística tau e correção não paramétrica Newey-West/Bartlett. PP e KPSS usam L=min(max(1,floor(4(n/100)^(1/4))), max(1,floor((n-1)/4))). A regra curta limita a fração da amostra consumida pela estimação da variância de longo prazo. É uma escolha explícita deste estudo, não o padrão automático das bibliotecas. Sensibilidade: ADF com AIC e bandwidth 2L limitado a floor((n-1)/3), além de constante e tendência (`ct`) quando n>=20.

ADF/PP rejeitam quando a estatística fica abaixo do valor crítico de 5%; KPSS rejeita quando fica acima. O uso dos valores críticos evita tratar o p-valor aproximado como mais exato, especialmente nos trechos curtos. Os valores de ADF/PP vêm das aproximações de MacKinnon; KPSS usa a tabela simulada do pacote `arch`. P-valores reportados como <0,001 incluem os truncados numericamente em zero pela biblioteca, não probabilidades matematicamente nulas.

### Síntese dos testes por segmento

| Escala | Trechos testados | ADF rejeita H0 | PP rejeita H0 | KPSS rejeita H0 | Concordância com I(0) |
|---|---|---|---|---|---|
| 1 minuto | 246 | 100,0% | 100,0% | 6,1% | 93,9% |
| 5 minutos | 246 | 100,0% | 100,0% | 6,1% | 93,9% |
| 15 minutos | 246 | 95,9% | 100,0% | 3,7% | 93,1% |
| 30 minutos | 246 | 86,2% | 89,4% | 4,1% | 81,3% |
| 60 minutos | 246 | 44,7% | 47,6% | 0,0% | 43,9% |
| 1 dia | 7 | 85,7% | 85,7% | 0,0% | 85,7% |


Concordância com I(0) = ADF e PP rejeitam raiz unitária, e KPSS não rejeita estacionariedade, no **mesmo trecho**. Não rejeitar KPSS é ausência de evidência contra sua H0. Diferenças de taxas entre escalas também refletem comprimentos amostrais diferentes. Com 18 ou 9 observações por pregão, as aproximações dos testes são frágeis e seu poder é baixo. Uma queda da taxa de rejeição do ADF não demonstra que os retornos agregados adquiriram raiz unitária. No diário, a evidência é local a sete segmentos testáveis e não estabelece estabilidade entre regimes ao longo do ano.

### Estatística, p-valor e valor crítico de um trecho de referência

Regra anterior à inspeção dos resultados: maior comprimento disponível, desempate pela data mais antiga. Nos intradiários isso corresponde ao primeiro pregão completo. A tabela apresenta testes reais de um trecho, não estatísticas ou p-valores obtidos pela média de testes. As demais linhas estão em `tables/stationarity_all.csv`.

| Escala | Teste | Período | n | lags/L | Estatística | Crítico 5% | p | Decisão H0 |
|---|---|---|---|---|---|---|---|---|
| 1 minuto | ADF | 2024-01-02 | 540 | 0 | -20,452 | -2,867 | <0,001 | Rejeita |
| 1 minuto | PP | 2024-01-02 | 540 | 6 | -20,619 | -2,867 | <0,001 | Rejeita |
| 1 minuto | KPSS | 2024-01-02 | 540 | 6 | 0,081 | 0,461 | 0,684 | Não rejeita |
| 5 minutos | ADF | 2024-01-02 | 108 | 0 | -8,750 | -2,889 | <0,001 | Rejeita |
| 5 minutos | PP | 2024-01-02 | 108 | 4 | -8,679 | -2,889 | <0,001 | Rejeita |
| 5 minutos | KPSS | 2024-01-02 | 108 | 4 | 0,086 | 0,461 | 0,660 | Não rejeita |
| 15 minutos | ADF | 2024-01-02 | 36 | 0 | -5,976 | -2,949 | <0,001 | Rejeita |
| 15 minutos | PP | 2024-01-02 | 36 | 3 | -5,987 | -2,949 | <0,001 | Rejeita |
| 15 minutos | KPSS | 2024-01-02 | 36 | 3 | 0,094 | 0,461 | 0,615 | Não rejeita |
| 30 minutos | ADF | 2024-01-02 | 18 | 0 | -4,086 | -3,054 | 0,001 | Rejeita |
| 30 minutos | PP | 2024-01-02 | 18 | 2 | -4,086 | -3,054 | 0,001 | Rejeita |
| 30 minutos | KPSS | 2024-01-02 | 18 | 2 | 0,094 | 0,461 | 0,613 | Não rejeita |
| 60 minutos | ADF | 2024-01-02 | 9 | 0 | -2,494 | -3,367 | 0,117 | Não rejeita |
| 60 minutos | PP | 2024-01-02 | 9 | 2 | -2,388 | -3,367 | 0,145 | Não rejeita |
| 60 minutos | KPSS | 2024-01-02 | 9 | 2 | 0,155 | 0,461 | 0,375 | Não rejeita |
| 1 dia | ADF | 2024-06-12 a 2024-08-13 | 45 | 0 | -6,886 | -2,930 | <0,001 | Rejeita |
| 1 dia | PP | 2024-06-12 a 2024-08-13 | 45 | 3 | -6,879 | -2,930 | <0,001 | Rejeita |
| 1 dia | KPSS | 2024-06-12 a 2024-08-13 | 45 | 3 | 0,165 | 0,461 | 0,348 | Não rejeita |


Todas as especificações, datas, avisos, tamanhos amostrais, defasagens e valores críticos de 1%, 5% e 10% estão no CSV completo. `stationarity_sensitivity.csv` permite avaliar as escolhas alternativas sem procurar retrospectivamente uma especificação que produza a conclusão desejada.

## 3. Box-Jenkins: identificação e estimação

A FAC/FACP da entrega de 31/08 mostrou correlações pequenas dos retornos e dependência mais nítida nas magnitudes. Isso motiva incluir ARMA(0,0), AR puro, MA puro e modelos mistos, sem impor uma ordem a partir de um pico isolado. Mantém-se d=0 nos retornos como especificação de trabalho, apoiada pela evidência nos trechos mais longos. Nas escalas com sessões curtas, essa escolha é provisória. Não se diferencia automaticamente o retorno quando o ADF deixa de rejeitar em amostra pequena.

Modelo: r_(s,t) = mu + soma_i phi_i (r_(s,t-i)-mu) + epsilon_(s,t) + soma_j theta_j epsilon_(s,t-j). `mu` é a média incondicional; o intercepto equivalente é c=mu(1-soma phi). Os parâmetros são comuns aos segmentos, que reiniciam com a distribuição estacionária do modelo. Não se subtrai uma média por dia.

A verossimilhança gaussiana é a soma das contribuições dos segmentos. O algoritmo de inovações calcula exatamente a inicialização estacionária dentro do modelo. Média e variância são concentradas analiticamente, mas **ambas contam como parâmetros**: k=p+q+2. Usam-se AIC=-2 log L+2k e BIC=-2 log L+k log N. AIC/BIC absolutos só são comparados na mesma escala, mesma amostra e unidade. Heteroscedasticidade e possível dependência entre dias fazem dessa verossimilhança uma quase-verossimilhança gaussiana de trabalho, sem afirmar que os retornos sejam normais ou que os segmentos sejam independentes no mercado.

Grade p,q em 0,...,5. 3 inicializações determinísticas por modelo, incluindo zero, uma solução de ordem menor quando disponível e/ou perturbação aleatória com semente fixa. Parametrização garante estacionariedade AR e invertibilidade MA. Raízes dos polinômios 1-soma(phi_i z^i) e 1+soma(theta_j z^j) precisam ter módulo >1,001 para elegibilidade numérica. Convergência é registrada, sem garantia de máximo global. Na escala de 60 minutos, (4,5), (5,4) e (5,5) são excluídos antes da estimação quando presentes na grade: nove observações por réplica fornecem apenas nove autocovariâncias distintas, insuficientes para p+q+1 parâmetros de covariância nesses casos.

| Escala | ARMA por BIC | mu (% por barra) | Distância do 2º BIC | ARMA por AIC |
|---|---|---|---|---|
| 1 minuto | (0,0) | -0,000122 | 2,93 | (5,5) |
| 5 minutos | (0,0) | -0,000611 | 10,03 | (4,3) |
| 15 minutos | (0,0) | -0,001832 | 8,66 | (4,3) |
| 30 minutos | (0,0) | -0,003664 | 8,00 | (5,0) |
| 60 minutos | (0,0) | -0,007328 | 2,70 | (2,0) |
| 1 dia | (0,0) | -0,065483 | 5,34 | (0,0) |


Para ARMA(0,0) com constante, a previsão condicional do retorno é a média estimada do treino. Ele difere do benchmark de retorno exatamente zero. A falta de ganho suficiente dos termos AR/MA pelo BIC não implica eficiência de mercado ou ausência de previsibilidade não linear. Todas as ordens, falhas, exclusões, raízes e diferenças de BIC ficam em `arma_grid_all.csv`; os coeficientes completos ficam em `selected_models.csv`.

## 4. Diagnóstico e revisão

Resíduos são inovações padronizadas pelo desvio-padrão preditivo do modelo. FAC: numerador apenas com pares do mesmo segmento, centrado pela média global, e denominador global soma(e_t-media)^2. A FAC residual usa esta normalização Box-Jenkins para ser compatível com o portmanteau; ela difere da correlação Pearson dos pares usada na primeira entrega. FACP mantém o último coeficiente de OLS AR(k) pooled, sem atravessar fronteiras.

Com N_k pares válidos, Q(h)=N(N+2) soma_(k=1)^h FAC(k)^2/N_k. Para um único segmento N_k=N-k, recupera-se Ljung-Box usual. A referência qui-quadrado com h-p-q graus de liberdade é **aproximada** nos dados segmentados e heteroscedásticos. `ljungbox_by_segment.csv` também contém testes Ljung-Box convencionais por trecho, com correção de graus de liberdade igualmente aproximada porque os parâmetros são comuns.

Uma calibração adicional simula 999 amostras do ARMA gaussiano homoscedástico selecionado, com os mesmos comprimentos de segmento e inicialização estacionária exata. Reestima-se a ordem selecionada em cada amostra e recomputa-se Q. p=(1+excedências)/(B+1). Esse bootstrap considera os resets e a estimação, condicionado à ordem escolhida; **não corrige heteroscedasticidade nem repete a seleção da grade**. É uma referência do modelo, não uma inferência robusta geral. A resolução mínima é 1/(B+1) e o erro Monte Carlo fica registrado.

| Escala | h (barras/pregões) | p Q aprox. | p bootstrap gauss. | p Q de e² aprox. | Curtose excedente |
|---|---|---|---|---|---|
| 1 minuto | 60 | <0,001 | 0,001 | <0,001 | 20,18 |
| 5 minutos | 12 | 0,012 | 0,013 | <0,001 | 21,75 |
| 15 minutos | 4 | 0,090 | 0,079 | <0,001 | 8,43 |
| 30 minutos | 4 | 0,291 | 0,283 | <0,001 | 5,07 |
| 60 minutos | 4 | 0,014 | 0,012 | <0,001 | 5,90 |
| 1 dia | 10 | 0,915 | 0,913 | 0,769 | 1,19 |


Os horizontes desta tabela servem ao diagnóstico de cada modelo; não são todos a mesma separação física. Em 1/5/15 minutos, h=60/12/4 corresponde a 60 minutos. Em 30/60 minutos, h=4 corresponde a 120/240 minutos. No diário h=10 corresponde a dez pregões dentro do segmento. Bandas dos gráficos são pontuais e aproximadas sob ruído branco; não corrigem múltiplos lags ou heteroscedasticidade.

O relatório de revisão compara o modelo de menor BIC, o de menor AIC e o melhor AR puro (`model_review.csv`). Uma falha no diagnóstico não é ocultada promovendo o vencedor por BIC a modelo plenamente adequado. Dependência em e², caudas pesadas e perfil intradiário de variância indicam que uma média linear simples pode ser útil como benchmark mesmo quando a hipótese de ruído branco gaussiano homoscedástico é inadequada. Jarque-Bera e seus p-valores constam da tabela completa, também como referência assintótica.

**Resultado concreto do diagnóstico principal:** rejeição da referência de ausência de autocorrelação residual em 1, 5 e 60 minutos, tanto pela aproximação qui-quadrado quanto pelo bootstrap gaussiano a 5%. Nas escalas de 15 e 30 minutos e no diário não há rejeição nesse corte. A FAC dos resíduos ao quadrado rejeita a referência em todas as escalas intradiárias, mas não no diário. Jarque-Bera rejeita normalidade nas seis escalas. Assim, nenhum vencedor intradiário é certificado aqui como ruído branco homoscedástico.

### Nova inspeção da grade e sensibilidade ao horizonte do diagnóstico

Reexaminamos todos os candidatos elegíveis em horizontes mais extensos, fixos dentro de cada escala, para observar correlação além do primeiro corte e acomodar ordens maiores. A tabela seguinte usa somente a referência qui-quadrado aproximada, sem bootstrap ou correção pela busca de modelos. “Não rejeita” não significa modelo validado. O critério principal BIC permanece o da proposta.

| Escala | h | Não rejeitam Q | Avaliados | Menor BIC entre não rejeitados | Delta BIC |
|---|---|---|---|---|---|
| 1 minuto | 60 | 0 | 36 | Nenhum | - |
| 5 minutos | 24 | 35 | 35 | (0,0) | 0,00 |
| 15 minutos | 12 | 32 | 32 | (0,0) | 0,00 |
| 30 minutos | 12 | 26 | 26 | (0,0) | 0,00 |
| 60 minutos | 8 | 8 | 19 | (2,0) | 2,70 |
| 1 dia | 15 | 22 | 22 | (0,0) | 0,00 |


Em 1 minuto, nenhum dos 36 candidatos supera essa referência de diagnóstico em h=60: a adequação da média linear permanece em aberto. Em 5 minutos, a decisão muda entre h=12 (rejeita) e h=24 (não rejeita), mostrando sensibilidade ao horizonte. Em 60 minutos, AR(2) é o candidato de menor BIC entre os que não rejeitam em h=8, com penalidade de aproximadamente 2,70 frente a ARMA(0,0); ele fica registrado como alternativa para a avaliação futura. Essas observações não autorizam selecionar o horizonte que “aprova” um modelo ou afirmar ganho fora da amostra.

## 5. Conclusões e etapa de 21/09

- Os testes oferecem evidência de ausência de raiz unitária nos trechos de maior resolução, com limitações fortes nas sessões de 30 e 60 minutos. A concordância local não estabelece estacionariedade global da variância ou entre regimes.
- A seleção por BIC privilegia ARMA(0,0) nas seis escalas. A rejeição residual em 1, 5 e 60 minutos impede tratar essa escolha como encerramento da adequação Box-Jenkins. Em 1 minuto, a revisão da grade tampouco elimina a rejeição da referência.
- A modelagem da média não esgota a dinâmica da volatilidade. O ajuste gaussiano serve como benchmark e não valida uma distribuição de risco homoscedástica.
- Estacionariedade, ausência de autocorrelação, ajuste dentro da amostra e ganho preditivo fora da amostra são propriedades diferentes. Esta entrega não avalia o último item.
- Para 21/09: avaliação com origem móvel em 2025, horizontes economicamente interpretáveis, retorno zero/média histórica/AR restrito, modelo alternativo e combinação, métricas de acurácia e Diebold-Mariano. Reestimações e transformações deverão usar apenas informação disponível em cada origem.

## Reprodução e referências

```bash
pip install -e .
OPENBLAS_NUM_THREADS=1 python scripts/run_entrega_14_09.py --input data/raw/BTG-ATS-A26.zip
PYTHONPATH=src python -m unittest discover -s tests -v
```

O comando gera tabelas, figuras, relatório e PDF. `private/` contém apenas caches locais de retornos/resíduos, ignorados pelo Git. Python 3.12.14. Versões efetivas: numpy 2.3.5, pandas 2.2.3, scipy 1.17.0, statsmodels 0.15.0, arch 8.0.0, pyarrow 25.0.1, matplotlib 3.10.8, reportlab 4.4.9. Os testes de código comparam a verossimilhança com filtros Kalman independentes, verificam resets, contagem de parâmetros, fronteiras dos pares e equivalência com Ljung-Box para uma única série.

- Maciel, L. Materiais fornecidos da EAD6034: Aula 4, Metodologia Box & Jenkins; Aula 5, Tendência e Raiz Unitária. Requisitos: EAD6034TrabalhoUnivariado_2026, entrega de 14/09.
- Matías, J. M.; Reboredo, J. C. (2012). Forecasting performance of nonlinear models for intraday stock returns. Journal of Forecasting 31(2), 172-188. https://doi.org/10.1002/for.1218
- [ADF: especificações, seleção de lags e aproximações de MacKinnon](https://arch.readthedocs.io/en/latest/unitroot/generated/arch.unitroot.ADF.html).
- [Phillips-Perron: tau e correção Newey-West](https://arch.readthedocs.io/en/latest/unitroot/generated/arch.unitroot.PhillipsPerron.html).
- [KPSS: hipóteses, bandwidth e valores críticos](https://arch.readthedocs.io/en/latest/unitroot/generated/arch.unitroot.KPSS.html).
- [Algoritmo de inovações ARMA em statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.tsa.innovations.arma_innovations.arma_innovations.html).
- [Ljung-Box e graus de liberdade em statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.stats.diagnostic.acorr_ljungbox.html).
- [Hyndman e Athanasopoulos: identificação, seleção e diagnóstico ARIMA](https://otexts.com/fpp3/arima-r.html).
