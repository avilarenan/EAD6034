# Guia de estudo - Desafio 5

Este guia acompanha `apresentacao.ipynb`, suas rotinas em `analise.py` e os cinco slides de `introducao.pdf`. Comece pela narrativa e pelas unidades. Depois estude os testes. Por último, rode as alterações sugeridas e tente explicar o que mudou sem ler o texto.

As marcações **aula/desafio**, **implementação** e **esclarecimento** distinguem os métodos pedidos, as escolhas operacionais e as interpretações matemáticas. Toda–Yamamoto e a referência sazonal são acréscimos declarados de implementação.

## 1. A história que você precisa conseguir contar

“O petróleo chega ao Brasil com um preço em dólares. O câmbio transforma esse custo em reais. Parte do movimento chega aos preços ao produtor e, depois, ao consumidor. Ao mesmo tempo, a política monetária reage à economia. Um VAR permite acompanhar essas relações ao longo dos meses.”

“Comparo um mesmo choque antes e depois de outubro de 2016. Na especificação-base, o IPCA responde mais ao Brent no segundo período. Mas a conclusão depende do número de defasagens e das hipóteses sobre os choques. Além disso, os resíduos ainda têm autocorrelação. Por isso apresento evidência exploratória de mudança entre regimes, sem atribuir toda a diferença à política da Petrobras.”

A conclusão tem três partes distintas: **magnitude estimada**, **incerteza** e **limite de interpretação**. Não pule da primeira para uma afirmação causal.

## 2. Variáveis, unidades e transformações

**Aula/desafio.** Um preço em reais pode aumentar porque o petróleo ficou mais caro em dólares ou porque o real se depreciou. Manter Brent e câmbio separados permite investigar esses canais. A Selic ajuda a representar a condição monetária; o IPA aproxima a etapa de produção e o IPCA, o consumidor.

| Entrada | Como ler um aumento de uma unidade |
|---|---|
| `brent = 100*diff(log(preço))` | Aproximadamente 1% a mais na variação mensal do preço em dólares |
| `cambio = 100*diff(log(R$/US$))` | Aproximadamente 1% de depreciação adicional do real |
| `ipa` | Um ponto percentual na inflação mensal ao produtor |
| `ipca` | Um ponto percentual na inflação mensal ao consumidor |
| `selic` | Um ponto percentual na taxa anualizada, mantida em nível |

**Esclarecimento.** Subir de 5 para 5,50 R$/US$ é uma alta de 10%, mas a diferença de logs multiplicada por 100 é aproximadamente **9,531**. O código usa esse valor para normalizar um choque de 10% exatos.

Não confunda **1%** com **1 ponto percentual**. Se a inflação passa de 0,4% para 0,6% no mês, ela aumenta 0,2 p.p., ou 50% relativamente à taxa inicial.

IPCA e IPA já são variações mensais. Aplicar diferença do log às próprias taxas seria outra operação, poderia falhar em meses negativos e não representaria o que queremos.

A Selic não é dividida por 12: entra na unidade anualizada da fonte. Se `DIFERENCIAR_SELIC=True`, a variável passa a ser a mudança mensal dessa taxa, em p.p.

**Por que começar em dezembro/2003 nos arquivos?** Para calcular a variação de janeiro/2004. Dezembro não é uma observação adicional do VAR.

## 3. O que o VAR estima

**Aula/desafio.** A forma compacta é:

$$y_t=c+A_1y_{t-1}+\cdots+A_py_{t-p}+D_t\gamma+e_t.$$

- (y_t): vetor das cinco variáveis no mês t.
- (A_j): efeitos das cinco variáveis, j meses atrás, sobre cada variável atual.
- (D_t): calendário e pulsos para episódios específicos.
- (e_t): parte que o passado e os controles não explicaram.

Um VAR(2) usa dois meses do passado de **todas** as variáveis. Não significa apenas dois coeficientes. São 10 coeficientes defasados por equação, mais os controles. Na amostra completa há 28 parâmetros por equação: 10 defasados, constante, 11 meses e 6 pulsos.

**Intuição de um coeficiente.** Ele mede uma associação parcial, mantendo os outros regressores constantes. A resposta total de vários meses não é um único coeficiente: o impulso passa por todas as equações, volta por realimentações e se acumula.

**Implementação.** O script estima por mínimos quadrados, usando `lstsq`. Como as equações têm o mesmo conjunto de regressores, MQO por equação é suficiente para o VAR reduzido. A covariância conjunta dos resíduos ainda é necessária para identificar choques e calcular a FEVD.

As tabelas `02_coeficientes_*` mostram estimativas, erros-padrão e estatísticas usuais/HAC. Não escolha a narrativa pela significância de um coeficiente isolado quando a pergunta é conjunta.

### Defasagens

Mais lags dão flexibilidade e capturam reações demoradas. Também consomem graus de liberdade: com cinco variáveis, cada lag adiciona **25 coeficientes ao sistema**.

AIC, BIC e HQ equilibram ajuste e tamanho. Menor valor é preferível **dentro da mesma comparação**. BIC tende a penalizar mais modelos grandes; não garante resíduos adequados nem identificação causal.

O código compara p=1,...,6 em uma amostra comum. BIC escolhe p=2. Nenhuma ordem da grade passa o diagnóstico multivariado de autocorrelação. Mantemos uma base parcimoniosa com essa limitação explícita. A escolha não é apresentada como solução para o problema diagnosticado.

### Sazonalidade e episódios extremos

Com constante, usamos 11 indicadores mensais. Janeiro é a referência. Incluir os 12 meses e uma constante criaria colinearidade perfeita.

Os pulsos dão a meses extraordinários um intercepto próprio. Isso evita que o VAR precise explicar todo o episódio como dinâmica usual. A contrapartida é que parte do evento aparece na componente determinística, inclusive na decomposição histórica.

Excluir 2020 é diferente de adicionar pulsos. A exclusão elimina equações cujos alvos **ou defasagens** tocam 2020. O calendário continua íntegro: dezembro/2019 não vira o mês imediatamente anterior a janeiro/2021.

## 4. Estacionariedade e estabilidade: perguntas diferentes

**Aula/desafio.** Uma série estacionária tem propriedades que não mudam com a posição no tempo, em particular média e covariâncias bem comportadas. Uma raiz unitária pode fazer os choques persistirem indefinidamente.

| Teste | Hipótese nula | Se p é pequeno |
|---|---|---|
| ADF | Raiz unitária | Rejeitamos essa hipótese na especificação do teste |
| KPSS | Estacionariedade em torno de constante, no padrão usado | Rejeitamos essa hipótese |

Rejeitar ADF e não rejeitar KPSS é uma combinação compatível com estacionariedade. A combinação contrária é compatível com raiz unitária. Outros resultados são possíveis por baixo poder, quebras ou especificação. Não rejeitar não é provar a hipótese.

**Implementação.** O padrão inclui constante, sem tendência. O ADF escolhe lags por BIC até 12 e o KPSS usa largura automática. Esses parâmetros estão no painel. KPSS frequentemente devolve 0,01 ou 0,10 como **limites da tabela**, não probabilidades exatas.

Na base, as taxas de Brent, câmbio, IPA e IPCA são compatíveis com estacionariedade pelos testes usados. Para Selic, ADF≈0,075 e KPSS≈0,030 geram dúvida relevante. Não chamamos a Selic de estacionária só porque é uma taxa de juros.

**Por que não usar VECM automaticamente?** VECM descreve relações de cointegração entre níveis integrados. Aqui o desafio determina variações de preços e câmbio, com uma taxa em nível. Investigar cointegração exigiria outra especificação e outra justificativa. A sensibilidade simples é diferenciar a Selic e comparar.

### Raízes, meia-vida e ciclos

A dinâmica do VAR pode ser reescrita como uma matriz companheira. **No gráfico deste script, seus autovalores precisam ter módulo menor que 1.** Algumas bibliotecas mostram as raízes inversas; nesse outro formato, a condição é estar fora do círculo.

Raio≈0,913 indica estabilidade estimada do sistema completo. Isso não elimina a dúvida dos testes univariados nem a autocorrelação dos resíduos.

A meia-vida do modo dominante é `log(0.5)/log(raio)`, cerca de 7,6 meses na base. É uma medida de amortecimento do modo mais persistente, não necessariamente o mês em que toda IRF cai à metade.

Autovalores complexos combinam amortecimento e oscilação. O período matemático é `2*pi/abs(ângulo)`. Um período de centenas de meses numa amostra curta não prova um ciclo econômico observado: pode ser uma característica muito imprecisa da matriz estimada.

## 5. O que cada diagnóstico revela

| Diagnóstico | H0 | Interpretação de rejeição |
|---|---|---|
| Portmanteau multivariado | Sem autocorrelação residual até o horizonte testado | O sistema deixou dinâmica previsível nos erros |
| Jarque–Bera, por equação | Resíduos normais | Assimetria/caudas destoam da normal |
| ARCH, por equação | Ausência do padrão ARCH testado | A variância depende do passado dos erros ao quadrado |

**Esclarecimento.** “Resíduo médio próximo de zero” não significa ruído branco. Tampouco estabilidade significa boa especificação.

O Portmanteau vai até 12 meses, superando p. Com 2020 excluído, o teste usa o maior trecho contínuo dos resíduos e passa a ser um diagnóstico auxiliar desse trecho.

HAC corrige a estimativa da incerteza sob formas de dependência/heterocedasticidade. **Não muda os coeficientes estimados nem repara a dinâmica omitida.** Da mesma forma, o wild bootstrap não resolve resíduos serialmente correlacionados.

P-valores arredondados para 0,0000 não são literalmente zero. Vários testes são apresentados como diagnóstico; procurar só o menor p-valor produz uma história enganosa.

## 6. De resíduo para choque econômico

**Aula/desafio.** Os resíduos das cinco equações podem se mover juntos no mesmo mês. Uma surpresa comum de demanda global pode afetar petróleo, câmbio e inflação. Precisamos de hipóteses para repartir essa surpresa.

A identificação recursiva escreve:

$$e_t=P u_t,\qquad PP'=\Sigma_e.$$

Os choques (u_t) são ortogonais sob a identificação. Cholesky encontra P a partir da covariância e da ordem escolhida.

Na ordem **Brent, câmbio, IPA, IPCA, Selic**, uma variável anterior pode afetar uma posterior imediatamente. A resposta imediata no sentido inverso é restringida a zero. Os efeitos defasados continuam permitidos.

A ordem combina duas intuições: petróleo global é pouco afetado pelo Brasil dentro do mês, e custos podem chegar aos preços antes da reação monetária. São simplificações contestáveis; dados mensais agregam eventos que ocorrem em dias diferentes.

**Não chame automaticamente o choque do Brent de “choque puro de oferta de petróleo”.** A série também reflete demanda mundial e outros fatores. A ordenação destas cinco séries, sozinha, não separa todas essas origens.

### Por que testar 120 ordens?

Cinco variáveis têm 5!=120 permutações. O envelope mostra quanto a resposta muda ao redistribuir as surpresas contemporâneas. Se a covariância residual fosse diagonal, a ordenação teria pouca importância; correlações residuais relevantes aumentam essa preocupação.

O envelope é mínimo/máximo entre identificações. Não é intervalo de confiança, não tem cobertura de 90% e inclui ordens economicamente pouco plausíveis. É um teste de sensibilidade amplo.

## 7. IRF, acumulação e repasse

**Aula/desafio.** A IRF acompanha o efeito de uma surpresa isolada, propagada pelas equações, com as demais novas surpresas estruturais zeradas. Não é uma previsão de um episódio histórico específico.

**Esclarecimento.** Comparar um desvio-padrão antes com um desvio-padrão depois confunde tamanho do choque com transmissão. O código escala os dois períodos para a mesma alta de **10% no impacto**.

“Resposta em h=12” e “resposta acumulada até h=12” são medidas distintas. O gráfico principal soma **h=0,1,...,12: treze termos**, incluindo o mês do impacto. Isso não é uma soma de apenas doze taxas.

Como IPCA entra como taxa simples em %, somar suas respostas aproxima a mudança da inflação acumulada/nível de preços. Não é uma composição exata de taxas.

### Dois números que não devem ser confundidos

1. **Resposta normalizada:** soma das respostas do IPCA após um choque cuja alta inicial no Brent/câmbio foi fixada em 10%.
2. **Razão de acumuladas:** soma da resposta do IPCA dividida pela soma da resposta do próprio Brent/câmbio ao mesmo choque.

A segunda é uma elasticidade aproximada de repasse no horizonte escolhido. O denominador mede a trajetória acumulada da variável de origem, não apenas a alta inicial. Por isso ela não é simplesmente a primeira medida dividida por 10.

A razão é recalculada dentro de cada réplica bootstrap. Não se dividem dois limites de confiança separadamente. Se o denominador puder ficar perto de zero ou trocar de sinal, a razão torna-se frágil e pode gerar bandas enormes.

### Como ler os números centrais

Brent +10%: resposta acumulada aproximada de **0,074 p.p. antes** e **0,412 p.p. depois**. Diferença de **0,338 p.p.** Na especificação-base, a banda bootstrap pontual da diferença é aproximadamente [0,100; 0,576].

Essa banda é mais relevante para “mudou?” do que comparar visualmente duas bandas separadas. Sobreposição de intervalos individuais não equivale ao teste da diferença.

O câmbio tem resposta pós-período negativa. O resultado pode refletir composição de choques, omissões, reação de outras variáveis e identificação. A sensibilidade à Selic e ao recorte da amostra reforça que não devemos transformar esse sinal numa lei econômica.

### O bootstrap

**Implementação.** A cada réplica, os resíduos recebem sinais aleatórios +1/-1. O mesmo sinal é aplicado às cinco equações em cada mês, preservando seu movimento conjunto. A série é simulada recursivamente, o VAR é reestimado e suas respostas são recalculadas.

São 399 réplicas, semente fixa e bandas pontuais de 90%. Não descartamos seletivamente réplicas instáveis; sua fração é informada. A ordem p e as determinísticas ficam fixas em cada bootstrap.

Mais réplicas reduzem o erro Monte Carlo dos quantis, mas não criam novas observações nem garantem bandas estatísticas menores. Aumentar confiança de 90% para 95% tende a alargar a banda.

Os sinais independentes por mês permitem heterocedasticidade, mas pressupõem que a dependência relevante foi absorvida pelo VAR. Como o Portmanteau rejeita, a cobertura nominal das bandas não é assegurada. A diferença pré/pós usa réplicas independentes entre períodos e supõe independência aproximada dos estimadores.

## 8. Granger: informação preditiva condicional

**Aula/desafio.** A pergunta é: “o passado de X acrescenta informação para prever Y, dado o passado das demais variáveis do sistema?” Testamos conjuntamente os coeficientes dos lags de X na equação de Y.

É um conceito de precedência/informação, não prova de causa econômica. Variáveis omitidas, simultaneidade dentro do mês e o horizonte escolhido importam.

O teste em bloco verifica se Brent e câmbio, conjuntamente, ajudam as equações de IPA e IPCA. Uma conclusão conjunta não exige que todos os coeficientes individuais sejam significativos.

**Implementação adicional.** Por causa da Selic em nível, usamos Toda–Yamamoto: estimamos p+`D_MAX` lags, mas testamos somente os p primeiros. Com p=2 e dmax=1, estimamos três e testamos dois. Isso depende de dmax cobrir a ordem máxima de integração e de especificação adequada; não é proteção universal.

A versão usual usa a covariância convencional. A robusta usa HAC/Bartlett até 12 meses. Divergência entre as duas sugere que a inferência depende de hipóteses sobre os resíduos.

Há vinte pares direcionais possíveis. Com muitos testes a 5%, algumas rejeições podem acontecer por acaso. O quadro é exploratório e condicional às cinco variáveis incluídas.

## 9. Houve quebra? O que mudou?

**Aula/desafio.** O Chow usa uma data conhecida: outubro/2016. Na implementação, a constante e os coeficientes defasados podem mudar; calendário e pulsos são comuns. São 11 restrições por equação no VAR(2). Mostramos F convencional e Wald com covariância HAC. O LR conjunto testa as restrições no sistema sob covariância comum.

Rejeição significa que a estabilidade desses coeficientes é questionável. Não identifica quem causou a mudança. Heterocedasticidade, dependência e a Selic em nível tornam essas referências assintóticas exploratórias.

O CUSUM acumula resíduos de estimações recursivas e procura deslocamentos persistentes. É uma verificação ao longo do tempo, diferente do teste concentrado numa data. Usa uma regressão auxiliar sem pulsos porque indicadores que só aparecem tarde tornam a amostra inicial singular.

O repasse móvel reestima o VAR em **96 meses**, avançando três meses por vez, e calcula o repasse em h=12. A janela não tem doze observações. Como as janelas se sobrepõem muito, a curva é suave e os pontos não são evidências independentes. O arquivo inclui o raio da matriz para detectar instabilidade local.

### Dinâmica versus covariância

A resposta depende tanto das matrizes A quanto de P, que vem de Sigma. A variância e a composição dos choques podem mudar mesmo se a propagação permanecer parecida.

O exercício de Sigma comum mantém a covariância da amostra completa nos dois regimes e troca apenas A. É uma comparação descritiva para enxergar o papel da propagação. Não é decomposição causal única da mudança nem avaliação isolada da Petrobras.

## 10. FEVD e decomposição histórica

**Aula/desafio.** A FEVD responde: “qual parcela da variância do erro de previsão, num horizonte, é atribuída a cada choque identificado?” As parcelas são não negativas e somam 100%.

Na base, o Brent explica cerca de **6,6% da variância do erro de previsão do IPCA em h=12**. Não significa que o petróleo explica 6,6% de toda inflação observada nem que aumentar o petróleo eleva o IPCA em 6,6%.

A FEVD de h passos soma inovações de h=0 até h−1. Isso difere da convenção do gráfico acumulado, que inclui h=12. Os rótulos explicitam essa diferença.

A decomposição histórica reconstrói:

**IPCA observado = base determinística/condições iniciais + contribuições dos cinco choques.**

No gráfico de 2021–2022, as barras mostram as contribuições dos choques. A linha compara essas barras com o IPCA depois de retirar a base. A soma completa é conferida numericamente, mês a mês.

A base inclui constante, sazonalidade, pulsos e condições iniciais. Por isso “tudo que aconteceu na pandemia” não aparece automaticamente como choque do petróleo ou do câmbio.

## 11. Simulação: aprender onde a identificação entra

**Aula/desafio.** Na simulação, conhecemos as matrizes verdadeiras de um VAR de produto, inflação e juros. Geramos dados, estimamos o modelo e comparamos a resposta verdadeira a um choque monetário com duas ordenações.

A ordem correta recupera melhor a resposta nesta realização; a errada distribui de outro modo as surpresas contemporâneas. O RMSE das IRFs é aproximadamente 0,012 contra 0,133 na configuração de referência.

Isso verifica a implementação e ilustra a hipótese de identificação. Não prova que a ordem escolhida para a economia brasileira seja verdadeira. Mais observações reduzem o erro de estimação, mas não corrigem uma hipótese estrutural errada.

## 12. Prever fora da amostra

**Aula/desafio.** A janela expansiva começa com uma origem em janeiro/2017. A cada origem, o modelo usa apenas dados até aquele mês e prevê o IPCA do mês t+1 e do mês t+12. Conforme o tempo avança, novas observações passadas entram no treino.

O horizonte 12 é a inflação **daquele mês futuro**, não a inflação acumulada nos próximos doze meses.

| Referência | Previsão |
|---|---|
| VAR | Cinco séries interagem |
| AR | Só o passado do IPCA, com o mesmo p e controles |
| RW | Repete a última inflação mensal |
| Ingênuo sazonal | Repete o último ciclo de doze meses |

**Implementação.** BIC é reavaliado em cada janela, sem olhar dados posteriores à origem. Não se usa o p escolhido com a amostra completa para contaminar a seleção retrospectiva, salvo quando o usuário fixa deliberadamente `P_FIXO`. Os pulsos futuros são sempre zero.

Esta é uma avaliação pseudo fora da amostra. Os valores são da versão atual dos dados; não reconstruímos revisões, defasagens de publicação e a informação efetivamente disponível em cada dia histórico. As datas dos controles também são uma escolha retrospectiva do exercício.

RMSE penaliza erros grandes mais fortemente; MAE resume o tamanho médio dos erros absolutos. Ambos ficam em p.p. de inflação mensal. Não usamos MAPE, que se torna problemático perto de inflação zero.

### Comparação estatística

DM testa a igualdade da perda média; usamos erros quadráticos, covariância HAC e correção de pequena amostra de Harvey–Leybourne–Newbold. A comparação reportada é **VAR versus ingênuo sazonal**, não aninhados para p<12.

O AR é uma restrição do VAR com mesmo p e controles. Nesse caso, a distribuição usual do DM não é a referência apropriada. Clark–West ajusta a diferença de perdas pelo custo de estimar o modelo maior e usa teste unilateral em favor do VAR. O procedimento tem interpretação aproximada em amostras finitas e com seleção de ordem.

RW é mostrado como referência descritiva. O código não reporta DM para comparações aninhadas só para preencher a tabela. Em h=12, as previsões pontuais de RW e do ingênuo sazonal coincidem por construção, embora as regras completas difiram em outros horizontes.

A base encontra ganho do VAR sobre AR em h=1 (CW≈0,0003), mas não em h=12 (CW≈0,660). “Explica uma resposta a choques” e “prevê melhor” são perguntas diferentes.

## 13. Experimentos para estudar

Faça os ensaios com `BOOT=99` e `PASTA_SAIDA="resultados_teste"`. Para resultados finais, restaure 399 ou aumente para 999. Depois de editar a primeira célula, use Restart Kernel and Run All Cells.

1. **p=4:** antes de rodar, antecipe maior flexibilidade e menos graus de liberdade. Observe que a banda da diferença do petróleo passa a incluir zero.
2. **Excluir 2020:** veja se a magnitude muda e quantas observações se perdem, inclusive nas defasagens.
3. **Trocar Brent e câmbio na ordem:** explique que os dados e o ajuste reduzido são iguais, mas a distribuição dos choques muda.
4. **Diferenciar a Selic:** compare escolha de p, diagnóstico e resposta cambial. Não compare coeficientes de Selic como se a unidade fosse a mesma.
5. **Encerrar em abril/2023:** explique a redução do pós-período e a maior incerteza.
6. **Mudar a quebra para janeiro/2018:** trate como sensibilidade de data, sem escolher a data pelo menor p-valor.

A tabela numérica dos seis ensaios está em [VALIDACAO.md](VALIDACAO.md). A evidência pontual para o Brent se mantém positiva nesses ensaios, mas a significância é sensível a p. Não selecione só os ensaios favoráveis.

## 14. Perguntas que o professor pode fazer

**Por que cinco variáveis?** [aula/desafio] São as variáveis do desafio: custo internacional, câmbio, produção, consumidor e condição monetária.

**Por que BIC e só seis lags?** [implementação] Para controlar o número de parâmetros, sobretudo no pós-período. A alternativa p=4 está testada. O teto não é uma verdade econômica.

**Se os resíduos têm autocorrelação, por que apresentar?** [esclarecimento] Para mostrar o resultado e a inadequação juntos. A análise é exploratória; as bandas não recebem uma interpretação definitiva. Nenhum p da grade resolveu o problema.

**Por que não acrescentar cada variável que parece faltar?** [implementação] Mais variáveis mudam a pergunta e aumentam muito os parâmetros. Atividade econômica e diferentes choques globais são omissões plausíveis a discutir, não algo que esta especificação resolveu.

**Qual é a hipótese mais forte?** [aula/desafio] A identificação contemporânea por Cholesky, junto da suficiência do sistema e da estabilidade dentro dos regimes. As 120 ordens mostram uma parte dessa fragilidade.

**Granger prova causalidade?** [esclarecimento] Não. Mede informação preditiva adicional, condicional ao conjunto de variáveis.

**Por que 90% e não 95%?** [implementação] É a convenção adotada para a apresentação e próxima ao exercício da aula. A confiança é editável; maior confiança tende a alargar bandas.

**Mais bootstrap resolve o tamanho pequeno da amostra?** [esclarecimento] Não. Diminui o erro numérico dos quantis, não acrescenta informação histórica.

**O pós-período inclui outra política da Petrobras?** [esclarecimento] Sim. Por isso há o ensaio que termina em abril/2023, antes da nova estratégia anunciada em maio.

**O câmbio negativo prova um efeito deflacionário?** [esclarecimento] Não. O sinal é condicional ao modelo e se mostra sensível. Precisa de melhor identificação antes de virar explicação estrutural.

**Por que a FEVD muda com a ordem?** [aula/desafio] Porque cada ordem atribui de modo diferente a covariância contemporânea aos choques.

**O que significa meia-vida?** [esclarecimento] O amortecimento do modo dominante da matriz estimada. Não é automaticamente o tempo de retorno do IPCA à trajetória inicial.

**O que o Chow testa exatamente?** [implementação] Estabilidade da constante e dos coeficientes defasados na data definida, mantendo calendário e pulsos comuns.

**Os 96 meses são o horizonte do repasse?** [esclarecimento] Não. São a janela de estimação. O repasse é acumulado até h=12.

**Como você impede o futuro de entrar na previsão?** [implementação] Cada ajuste recebe apenas o prefixo da amostra até a origem. Lags, escolha de p e pulsos estimados vêm desse prefixo; pulsos futuros ficam zerados.

**Por que Clark–West?** [implementação] Porque o AR comparável é aninhado no VAR. DM convencional não deve ser usado como se os modelos fossem não aninhados.

**A mudança de 2016 causou a diferença?** [esclarecimento] O desenho não identifica isso isoladamente. Ele detecta associações entre regimes que também diferem em pandemia, tributos, composição dos choques e política posterior.

## 15. Revisão em uma hora

- **15 min:** explicar, sem fórmulas, a pergunta e a unidade de cada variável.
- **15 min:** ler os diagnósticos e diferenciar estabilidade, estacionariedade, Granger e identificação.
- **15 min:** apresentar as IRFs, a diferença pré/pós, a FEVD e a decomposição histórica.
- **15 min:** rodar p=4 e responder às perguntas acima em voz alta.

Antes da aula, ensaie com o relógio e com a mesma máquina. Saiba encontrar `P_FIXO`, `ORDEM`, `EXCLUIR_2020`, `FIM` e `BOOT` sem pesquisar. A fala curta está em [ROTEIRO_APRESENTACAO.md](ROTEIRO_APRESENTACAO.md).

Referências técnicas e links da aula estão no [README](README.md). Os números deste guia descrevem a configuração de referência; uma nova execução com outros parâmetros exige rever a narrativa.
