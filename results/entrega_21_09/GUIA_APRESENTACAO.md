# Guia de apresentação — EAD6034, entrega cumulativa de 21/09

Renan de Luca Avila · Seminário final 28/09/2026 · sete slides, roteiro de aproximadamente 13 minutos, até 15 minutos no total.
[Código e resultados](https://github.com/avilarenan/EAD6034) · [Relatório técnico](https://github.com/avilarenan/EAD6034/blob/main/results/entrega_21_09/RELATORIO_21_09.md).
Este guia não introduz métodos ou resultados diferentes dos CSV públicos.

## Roteiro cumulativo

| Slide | Tempo | Mensagem e orientação de fala |
| --- | --- | --- |
| 1 — Pergunta, dados e desenho | 1min30 | Estudamos WIN em seis escalas, treino 2024 e teste 2025. Horas mais previsíveis é hipótese, não conclusão. Explicar que retorno não atravessa a noite, mas o lag pode atravessar. |
| 2 — Descrição e FAC/FACP, 31/08 revisada | 1min30 | Mostrar a FAC e a FACP dos retornos, distinguindo correlação total e parcial. Ressaltar que o lag é uma observação e que comparar o mesmo lag não significa comparar o mesmo tempo físico. |
| 3 — Estacionariedade, 14/09 revisada | 2min | Corrigir explicitamente nove barras por dia versus 2214 observações anuais na escala horária. Explicar H0 opostas, c principal e ct sensibilidade. Ler as divergências da tabela, não ocultá-las. |
| 4 — Box–Jenkins, 14/09 revisada | 2min | Identificação, estimação, seleção e diagnóstico. Mostrar ordens efetivamente escolhidas e diagnóstico principal. Menor BIC não garante resíduos adequados nem previsão melhor. |
| 5 — ARCH/GARCH, Aula 6 | 1min30 | Variância condicional responde a outra pergunta: examinar a dependência dos quadrados. Estimação sequencial da mesma inovação e mesmas previsões da média. Citar persistência e diagnóstico dos resíduos padronizados. |
| 6 — Previsões e comparação, 21/09 | 2min30 | Explicar origens móveis com parâmetros fixos, alvos comuns de 60 minutos, benchmark zero, combinação 50/50 e DM AR×MA. Separar ganho econômico/descritivo de significância estatística. |
| 7 — Horários, overnight e conclusões | 1min | Distinguir faixas da janela e fases de negociação. Gap observado não é preço oficial de leilão. Ler a conclusão calculada e explicitar limites sem prometer previsibilidade. |

Referências de código para a fala: [dados](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/trading_time_data.py); [testes e ARMA](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/annual_models.py);
[ARCH/GARCH](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/conditional_volatility.py); [previsões e DM](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/forecast_evaluation.py); [execução](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/forecast_pipeline.py).
Os tempos são uma orientação de ensaio, não uma licença para ultrapassar os 15 minutos.

## Cartão de resultados da execução

- Seleção BIC da média em 2024: 1 min: ARMA(2,2); 5 min: ARMA(0,0); 15 min: ARMA(0,0); 30 min: ARMA(0,0); 60 min: ARMA(0,0); 1 dia: ARMA(0,0).
- Ljung–Box da média, no horizonte diagnóstico principal, rejeita ausência de autocorrelação em: 1 min. A referência é assintótica e pode ser afetada por heterocedasticidade; não rejeitar não prova ruído independente.
- Alvo comum de 60 minutos, série-base 1 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Alvo comum de 60 minutos, série-base 5 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Alvo comum de 60 minutos, série-base 15 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Alvo comum de 60 minutos, série-base 30 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Alvo comum de 60 minutos, série-base 60 min: menor MSE descritivo de ZERO; MSE/MSE_zero=1.000000, ganho=+0.0000%. Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout.
- Seleção BIC condicional da variância em 2024: 1 min: GARCH(1,1); 5 min: GARCH(1,1); 15 min: GARCH(1,1); 30 min: GARCH(1,1); 60 min: ARCH(1); 1 dia: Constant variance. A previsão pontual permanece a mesma.
- As previsões ARMA(0,0) no alvo comum coincidem nas escalas 5 min, 15 min, 30 min, 60 min: somar as médias das barras completas produz a mesma média horária. Isso decorre da agregação dos mesmos dados, não de confirmações independentes de previsibilidade.

Antes de falar, localizar no slide/tabela o valor exato que será mencionado. Não dizer “todas as escalas” se há exceções,
nem “ausência de efeito” apenas porque não houve rejeição. Resultados de 2025 não alteram retrospectivamente a seleção de 2024.

## Perguntas prováveis

### Por que antes n=9 e agora n=2214?

Antes cada pregão era testado separadamente; há nove barras horárias no intervalo de nove horas.
Agora numeramos todas as barras de 2024 em uma sequência cronológica. Não multiplicamos nove artificialmente nem
tiramos média dos testes: mudamos explicitamente a convenção de defasagem e refizemos todos os procedimentos.
A premissa é um modelo em tempo de negociação; isso não transforma amostras grandes em garantia de estacionariedade.
[Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/trading_time_data.py); [Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/annual_models.py).

### Como ignorar o retorno overnight e permitir um lag entre dias?

O retorno da primeira barra usa preços daquele pregão. Seu preditor pode ser o retorno da última barra de ontem.
Nenhum retorno fechamento–abertura é acrescentado ao alvo. A informação noturna pode afetar hoje e está entre as limitações;
“não modelar separadamente” não significa “demonstrar que não há efeito”. [Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/trading_time_data.py).

### BIC significa que ARMA(0,0) é ruído independente?

Não. BIC penaliza parâmetros: −2 log L + k log N. Se ARMA(0,0) vencer, apenas significa que os candidatos mais complexos
não compensaram a penalidade naquela amostra. Autocorrelação residual, dependência dos quadrados e previsão OOS são
avaliadas à parte. A constante prevê a média estimada e pode coincidir com TRAIN_MEAN. [Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/annual_models.py).

### ADF e PP rejeitam, mas KPSS pode rejeitar também?

Sim. Suas hipóteses nulas são distintas e especificações podem ser inadequadas. Rejeição simultânea não é licença para
escolher o teste preferido: reportamos conflito e sensibilidade. `c` e `ct` respondem a estacionariedade em nível e em torno
de tendência, respectivamente. Valores numéricos zero de p não são probabilidade matematicamente zero. [Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/annual_models.py).

### GARCH melhorou a previsão dos retornos?

Neste desenho GARCH não modifica a previsão da média: modela sua incerteza condicional usando as mesmas inovações.
A variância é estimada depois da média, não por MLE conjunta. Erro quadrado é uma proxy ruidosa da variância, não sua observação
direta. Portanto, uma melhora na métrica dessa proxy não pode ser vendida como melhora na previsão pontual. [Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/conditional_volatility.py).

### Por que não comparar diretamente MSE de um minuto com MSE de uma hora?

São alvos com duração e dispersão diferentes. A comparação principal entre escalas prevê os mesmos 60 minutos nas mesmas
origens. Os modelos das barras menores fazem previsão multipasso com uma única origem, sem inserir os retornos que ainda
não ocorreram. O bloco nativo responde à previsão da próxima barra da própria escala. [Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/forecast_evaluation.py).

### O DM mostra que o melhor BIC venceu todos os benchmarks?

Não. O DM foi pré-definido para AR positivo versus MA positivo, famílias não aninhadas. Estatística negativa favorece AR.
O teste tem referência aproximada; perdas degeneradas ou variância de longo prazo inválida impedem um p-valor. A comparação
não é automaticamente transferível ao ARMA geral, à combinação ou às variâncias aninhadas. [Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/forecast_evaluation.py).

### Como sabemos que os leilões causaram a diferença entre escalas?

Não sabemos com esse desenho. Candles não identificam fase de negociação e a cronologia documental é incompleta.
Os calls próprios do WIN ficam fora da janela nos regimes confirmados; eventos das ações subjacentes podem estar dentro.
Faixas e gaps são associações exploratórias, não identificação causal. Referência:
[auditoria de horários](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/docs/market_hours_2024_2025.md); [Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/trading_time_data.py).

### Todos os resultados anteriores estão contemplados?

Sim: descrição/FAC/FACP de 31/08, estacionariedade/Box–Jenkins de 14/09 e previsão/modelos alternativos de 21/09.
As etapas anteriores foram recalculadas sob o protocolo anual, sem apagar a versão histórica. Tabelas extensas ficam
no relatório/repositório, mantendo sete slides legíveis e a apresentação dentro de 15 minutos.

## Checklist do ensaio

- Confirmar que cada conclusão oral corresponde à versão entregue dos CSV e ao commit dos links.
- Explicar em 30 segundos o exemplo de retorno intradiário com lag entre pregões.
- Apresentar as duas H0 de raiz unitária e a H0 oposta de KPSS.
- Separar BIC, diagnóstico, previsão da média e previsão da variância.
- Mostrar horizonte comum, benchmark zero e magnitude do ganho antes do p-valor.
- Não chamar começo/fim da janela de “leilão do WIN”.
- Reservar aproximadamente dois minutos do limite para transições/perguntas; ensaiar sete slides em 13 minutos.

Gerador deste guia: [Código](https://github.com/avilarenan/EAD6034/blob/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034/forecast_narrative.py).
