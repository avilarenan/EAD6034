# Roteiro oral — EAD6034, seminário final de 28/09/2026

Limite: 15 minutos. Alvo do roteiro abaixo: ~12–13 minutos falados, com folga para
o início/transição entre slides. 10 slides de conteúdo + capa + agradecimentos.

| Slide | Tempo alvo | Mensagem central |
|---|---|---|
| 1 (capa) | — | (sem fala; título já diz o que é) |
| 2. Dados, relevância, divisão 80/20 | 90s | Por que o WIN importa; por que o corte mudou e como foi decidido |
| 3. Estatística descritiva | 60s | O que faltava (Prof. Anderson, 21/09) agora está completo |
| 4. Séries completas | 45s | Inspeção visual; onde fica o novo corte |
| 5. FAC/FACP | 45s | Correlação pequena não é o mesmo que previsão útil |
| 6. Estacionariedade | 90s | Três famílias de teste, agora concordam |
| 7. BIC + significância | 100s | Ruído branco vence em tudo; e agora com teste $t$ para provar |
| 8. GARCH + GJR | 90s | Volatilidade prevê melhor que média; assimetria testada e não encontrada |
| 9. Comparação justa | 80s | Mesmo alvo, mesmo protocolo; nenhuma diferença é significativa |
| 10. Baselines exploratórios | 70s | MLP e Chronos, claramente fora da metodologia central |
| 11. Conclusão | 60s | O que o corte 80/20 trouxe: resultado mais limpo, não só conformidade |

Total falado: ~12 min 30s. Deixa ~2min30 de folga para respiração/perguntas rápidas.

## Texto de apoio por slide

### Slide 2 — Dados, relevância, divisão 80/20 (90s)
"O WIN é o futuro de índice mais líquido do varejo na B3; entender sua dinâmica
intradiária importa para quem gerencia risco ou executa ordens nessa escala. A
pergunta central continua sendo se agregar minutos em horas melhora a previsão
dos retornos, e se a variância é mais previsível que a média.

O Prof. Anderson pediu, em 21/09, para eu usar a regra 80/20 em vez da divisão
quase 50/50 que eu tinha. Apliquei isso de forma mecânica: contei os 467 pregões
completos entre janeiro de 2024 e novembro de 2025, e cortei exatamente no dia
374 — 80,1% para treino, sem olhar antes para o que aconteceria no novo trecho de
teste. Isso importa porque meu próprio relatório de 21/09 já alertava contra
reusar 2025 para 'melhorar' um resultado depois de olhar para ele; a diferença
aqui é que o corte mudou por uma regra pré-registrada de proporção, não porque um
recorte parecia melhor."

### Slide 3 — Estatística descritiva (60s)
"Essa tabela também respondia a um pedido direto do Prof. Anderson: estatística
descritiva completa, com mínimo, máximo, quartis e desvio-padrão, que não
apareceu na entrega anterior. Não há nada estruturalmente novo aqui além do que
já se via nos violinos anteriores, mas agora está no formato que foi pedido: os
retornos ficam mais dispersos e menos concentrados em zero conforme a escala
cresce, e a curtose excedente cai — o que é esperado por agregação, mesmo sem
qualquer modelo."

### Slide 4 — Séries completas (45s)
"Aqui está a inspeção visual completa, sem suavização, com a linha tracejada
marcando onde fica o novo corte. Dá para ver visualmente que o treino agora cobre
uma fatia bem maior da amostra."

### Slide 5 — FAC/FACP (45s)
"A função de autocorrelação mostra picos ocasionais, mas dentro do que se espera
de ruído sob a banda de referência pontual. Correlação pequena não é o mesmo que
previsão útil — isso só aparece quando testamos fora da amostra, mais adiante."

### Slide 6 — Estacionariedade (90s)
"Aqui expandi a bateria de testes para bater com o que o checklist pedia: ADF nas
três especificações — sem constante, com deriva, com tendência — e Phillips-
Perron e KPSS em duas larguras de banda cada, curta e longa, seguindo Schwert
1989. O resultado interessante: sob a divisão anterior, quase 50/50, o KPSS com
tendência rejeitava estacionariedade em todas as escalas, o que exigia uma
explicação cuidadosa da divergência com ADF e PP. Com a divisão 80/20 e mais
dados de treino, essa divergência desaparece — as três famílias de teste agora
concordam em todas as escalas. Isso não foi um ajuste feito para 'consertar' o
resultado; é uma consequência de ter mais observações no treino."

### Slide 7 — BIC + significância dos coeficientes (100s)
"Aqui está a mudança mais marcante desta entrega. Antes, no minuto, o BIC
selecionava um ARMA(2,2) com vantagem de só 1,24 de BIC sobre o ruído branco, e
eu não tinha erro-padrão publicado para dizer se os coeficientes eram
significativos. Agora, com o treino maior, o BIC seleciona ARMA(0,0) — ruído
branco — em todas as seis escalas, com folgas de BIC bem maiores.

E agora eu também respondo à pergunta que ficou em aberto: mesmo quando forço um
AR(1) ou MA(1) como comparador, que o próprio enunciado do trabalho pede, o único
coeficiente extra nunca é estatisticamente significativo a 5% em nenhuma escala
— o maior valor absoluto de estatística $t$ é 0,85. Isso reforça com um teste
formal o que o BIC já sugeria: não há estrutura linear explorável nesses
retornos, nesta amostra."

### Slide 8 — GARCH e GJR (90s)
"Na variância, GARCH(1,1) ainda vence por BIC em quatro das seis escalas, ARCH(1)
no de 60 minutos, e variância constante no diário — igual à entrega anterior.
O que há de novo é o teste de assimetria: adicionei GJR-GARCH, que permite que
choques negativos afetem a variância de forma diferente de choques positivos —
o efeito alavancagem clássico. Em nenhuma escala o GJR vence por BIC, e o
parâmetro de assimetria é pequeno e muda de sinal entre escalas — não há evidência
de alavancagem aqui.

Uma decisão metodológica importante: eu não fiz teste de Diebold-Mariano entre
essas quatro especificações de variância, porque elas são aninhadas — constante
é ARCH(1) com alfa zero, que é GARCH com beta zero, que é GJR sem o termo de
assimetria — e a Aula 4 ensina explicitamente que Diebold-Mariano não é
apropriado para comparar modelos aninhados."

### Slide 9 — Comparação justa (80s)
"Esta é a comparação com o mesmo protocolo de sempre: parâmetros fixos do treino,
alvo comum de 60 minutos reconciliado entre todas as escalas intradiárias, 837
origens sem sobreposição no novo período de teste. As razões de MSE contra o
retorno zero ficam todas muito perto de 1, entre 0,14% e 0,16% piores na maioria
das escalas — pequeno, não um salto de 1 ou 2 pontos percentuais de retorno — e
nenhuma diferença entre AR e MA é estatisticamente significativa."

### Slide 10 — Baselines exploratórios (70s)
"Como extensão exploratória, fora da metodologia central que segui até aqui, testei
duas alternativas. Um MLP simples, com 30 defasagens, escolhido por validação
cronológica dentro do próprio treino e depois reajustado em treino mais validação
antes do teste — a mesma disciplina que os modelos lineares recebem com o BIC.
Não bateu o retorno zero de forma significativa. E um modelo de fundação
pré-treinado, Chronos-2, rodado zero-shot, sem qualquer ajuste — e esse ficou
significativamente pior que o retorno zero. Isso ilustra que pré-treino genérico
não garante desempenho num ativo e frequência específicos sem adaptação."

### Slide 11 — Conclusão (60s)
"O resultado central não mudou de direção desde a entrega anterior — a agregação,
por si só, não trouxe ganho de previsão sobre o retorno zero — mas ficou mais
limpo: a divisão 80/20 corrigida eliminou tanto a estrutura frágil do minuto
quanto a divergência do KPSS, e agora tenho testes formais de significância dos
coeficientes e de assimetria na variância para sustentar essa conclusão. A
contribuição deste trabalho é tornar essa comparação verificável, não afirmar que
o mercado é imprevisível de forma geral."

## Perguntas prováveis (FAQ rápida)

Tags: **aula** = método ensinado; **implementação** = escolha operacional defensável;
**esclarecimento** = clarificação conceitual, não um método novo.

1. **[implementação]** Por que 15/07/2025 e não outra data? — Contagem mecânica:
   dia 374 de 467 pregões completos, fixado antes de ver qualquer resultado no
   novo teste.
2. **[esclarecimento]** Isso não reusa dados de teste já examinados? — Só no
   sentido de que parte do que era teste em 21/09 virou treino agora; a regra em
   si (proporção 80/20) foi aplicada de forma cega ao resultado, não escolhida
   por parecer melhor depois de olhar.
3. **[aula]** Por que ADF em três especificações? — Aula 5: none/drift/trend
   mapeiam para `ur.df(type=...)`; o checklist pede as três.
4. **[implementação]** Por que "short"/"long" do pacote `arch` e não `urca`
   (R)? — Mesmas fórmulas de Schwert (1989), $4(n/100)^{0{,}25}$ e
   $12(n/100)^{0{,}25}$; `arch` usa teto (`ceil`), `urca` usa truncamento — mesma
   ideia, arredondamento diferente.
5. **[esclarecimento]** BIC selecionou (0,0) em tudo — então o trabalho não achou
   nada? — Achou: nem BIC nem o teste $t$ do único coeficiente extra encontram
   estrutura linear robusta. Isso é um resultado, não uma ausência de resultado.
6. **[implementação]** Por que refit só nos modelos selecionados para pegar
   erro-padrão, e não na grade toda? — A grade tem 216 candidatos por rodada;
   recalcular covariância robusta em todos seria caro e alguns candidatos perto
   da fronteira de estacionariedade podem falhar a inversão. Só os ~18
   selecionados precisam de significância reportada.
7. **[aula]** Por que GJR e não EGARCH? — Checklist aceita "e/ou"; GJR já testa
   assimetria e reaproveita a mesma estrutura de elegibilidade/BIC já validada.
8. **[aula]** Por que não Diebold-Mariano entre as variâncias? — Aula 4: DM não é
   apropriado para modelos aninhados, e constante⊂ARCH(1)⊂GARCH(1,1)⊂GJR são
   todos aninhados entre si.
9. **[esclarecimento]** MAPE não aparece — por quê, se a Aula 4 ensina a
   fórmula? — MAPE diverge quando o retorno realizado fica perto de zero (que é a
   maioria das barras aqui); preferimos MSE/MAE e a razão contra o retorno zero.
10. **[esclarecimento]** Por que só MLP e Chronos, e não os 4 modelos de rede
    neural originalmente cogitados? — Compromisso de tempo (~20h até a entrega) e
    escopo: o enunciado pede só um modelo adicional, que já está coberto por
    AR/MA/combinação; MLP e Chronos são um adendo exploratório rotulado, não uma
    substituição da metodologia central.
11. **[implementação]** O MLP teve vantagem injusta por causa da validação? —
    Não: a validação usa só a cauda do próprio treino, nunca o teste; o modelo
    final é reajustado em treino+validação antes de gerar previsões de teste,
    igualando a quantidade de dados de treino que os modelos lineares recebem.
12. **[esclarecimento]** Por que Chronos só nas 837 origens comuns, não em cada
    minuto? — Orçamento de CPU (rodando localmente, sem GPU); escolha declarada
    explicitamente, não uma restrição escondida da avaliação.
13. **[esclarecimento]** O resultado ruim do Chronos invalida modelos de
    fundação em geral? — Não; mostra que pré-treino genérico, sem ajuste
    (zero-shot), não é garantia de desempenho numa série específica de alta
    frequência e baixa relação sinal-ruído.
