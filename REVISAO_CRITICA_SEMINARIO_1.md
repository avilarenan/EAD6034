# Revisão crítica e propostas de melhoria — Seminário I

Consolidação da discussão de **27/09/2026**, para o seminário final de **28/09/2026** da disciplina EAD6034.

**Escopo:** registrar críticas, evidências e propostas. Este documento não executa alterações na análise, não aprova novos métodos e não afirma que as pendências foram resolvidas.

**Versão analisada:** [commit `ef21a78`](https://github.com/avilarenan/EAD6034/commit/ef21a78033a816cda9ab8abbb39823e8becf398c). As [anotações dos requisitos do professor](context_resources/seminario_1_requisitos_do_professor.md) foram acrescentadas posteriormente no [commit `2491f8b`](https://github.com/avilarenan/EAD6034/commit/2491f8b650c8fe808716d44b0871e244b6a4a2ed).

A avaliação abaixo se refere ao [PDF final de 28/09](https://github.com/avilarenan/EAD6034/blob/ef21a78033a816cda9ab8abbb39823e8becf398c/results/entrega_28_09/ENTREGA_28_09.pdf), ao seu [fonte Beamer](https://github.com/avilarenan/EAD6034/blob/ef21a78033a816cda9ab8abbb39823e8becf398c/results/entrega_28_09/ENTREGA_28_09.tex), ao [roteiro oral](https://github.com/avilarenan/EAD6034/blob/ef21a78033a816cda9ab8abbb39823e8becf398c/results/entrega_28_09/GUIA_APRESENTACAO.md), às tabelas publicadas e aos módulos de código citados. Não houve nova estimação para produzir esta revisão.

## 1. Avaliação geral

O estudo ficou mais completo: a divisão cronológica 80/20 atende à orientação do professor, a estatística descritiva foi ampliada e foram acrescentadas inferência sobre coeficientes e uma alternativa assimétrica para a variância.

Há pontos fortes a preservar:

- Comparação multiescala usando os mesmos alvos futuros, origens e pregões.
- Separação entre previsão da média e modelagem da variância.
- Parâmetros estimados no treino, com atualização causal dos estados no teste.
- Divulgação das limitações da seleção retrospectiva do contrato e dos dias completos.
- Referências clicáveis ao código e à origem dos dados.
- Apresentação cumulativa, com capa, dez slides de conteúdo e contracapa.

O PDF analisado foi validado e renderizado: **12 páginas, arquivo completo de 419.458 bytes**, com hash de objeto Git `220acafae28a6e56f9ac5387fa1212ffd3668cf3`. Isso atesta a integridade do arquivo examinado, não a correção de todas as conclusões.

**Conclusão da revisão:** ainda não é possível declarar todos os requisitos atendidos. Parte das pendências é de comunicação, mas o diagnóstico de autocorrelação residual é uma questão metodológica substantiva. A contribuição mais defensável é a comparação disciplinada e a documentação dos resultados, não uma prova de ruído branco, ausência de assimetria ou eficiência de mercado.

## 2. Auditoria dos requisitos do professor

A existência de uma tabela, figura ou função no repositório não substitui sua apresentação quando o requisito é mostrar e explicar o resultado no seminário.

| Requisito | Situação em 27/09 | Providência proposta |
| --- | --- | --- |
| Justificar por que prever a série | Atendido | Preservar a conexão do WIN com gestão de risco e execução. Não confundir relevância econômica com rentabilidade demonstrada. |
| Informar a fonte e a origem dos dados | Atendido | Manter B3, BTG Alpha Lab, identificação do dataset e limitações da seleção retrospectiva. |
| Justificar o horizonte preditivo | Parcial | Explicar por que 60 minutos é relevante para a pergunta de pesquisa e para uma decisão de execução/risco. A comparabilidade estatística, sozinha, não é a justificativa econômica. |
| Avaliar estacionariedade e classificar constante/tendência | Parcial | Os testes aparecem. Falta declarar explicitamente a especificação adotada: “com constante e sem tendência”, com d=0 nos retornos. |
| Mostrar a equação do ARIMA ajustado | Não atendido nos slides | Mostrar a equação com coeficientes estimados, unidades e ordem. Não basta escrever ARMA(0,0). |
| Modelo selecionado passar no Ljung–Box | Não atendido em todas as escalas | Tratar a rejeição em 1 e 5 minutos e a sensibilidade em 15 minutos. Não usar BIC como substituto do diagnóstico. |
| Mostrar medidas fora da amostra | Atendido | Manter datas, número de observações e identificação inequívoca do alvo. |
| Figura do realizado versus previsto | Existe fora do PDF | Incorporar a figura já publicada ao conjunto de slides. |
| Indicar one-step ou multi-step | Parcial | Explicitar o esquema por escala e distinguir passos futuros de sobreposição dos alvos. |
| Usar RMSE, MAE e MAPE | Parcial | RMSE e MAE estão nos CSVs, mas não nos slides. MAPE foi omitido e exige tratamento explícito da indefinição em retornos zero. |
| Comparar com o artigo de referência | Não atendido nos slides finais | Fazer uma comparação substantiva. Citação bibliográfica isolada não basta. |
| Elaborar a avaliação preditiva final | Parcial | Corrigir a interpretação de DM e integrar métricas, diagnóstico, benchmark e limitações. |

## 3. Prioridade máxima: Ljung–Box e o ciclo Box–Jenkins

### 3.1 Evidência observada

A hipótese nula do teste é ausência de autocorrelação até a defasagem avaliada. Para o modelo **ARMA_BIC**, selecionado como ARMA(0,0) em todas as escalas, os horizontes principais publicados são:

| Escala | Defasagem máxima do diagnóstico | p-valor | Decisão a 5% |
| --- | ---: | ---: | --- |
| 1 minuto | 60 | 3,54 × 10⁻²¹ | Rejeita ausência de autocorrelação |
| 5 minutos | 24 | 1,39 × 10⁻⁷ | Rejeita ausência de autocorrelação |
| 15 minutos | 24 | 0,1693 | Não rejeita nesse horizonte |
| 30 minutos | 24 | 0,4778 | Não rejeita nesse horizonte |
| 60 minutos | 24 | 0,0581 | Não rejeita nesse horizonte |
| Diário OC | 20 | 0,1125 | Não rejeita nesse horizonte |

Em **15 minutos**, há rejeição nos horizontes 10 (p=0,02196), 12 (p=0,03964) e 60 (p=0,04137). Portanto, não apresentar o resultado principal de 24 lags como adequação irrestrita.

Fontes: [diagnósticos da média](https://github.com/avilarenan/EAD6034/blob/ef21a78033a816cda9ab8abbb39823e8becf398c/results/entrega_28_09/tables/mean_diagnostics.csv) e [implementação dos modelos](https://github.com/avilarenan/EAD6034/blob/ef21a78033a816cda9ab8abbb39823e8becf398c/src/ead6034/annual_models.py).

A calibração publicada é assintótica convencional e não robusta à heteroscedasticidade arbitrária. Essa ressalva deve acompanhar os resultados, mas não transforma uma rejeição em aprovação do requisito.

### 3.2 Consequência metodológica

“BIC selecionou ARMA(0,0)” e “os resíduos são adequados” são afirmações diferentes. Coeficientes de comparadores individuais não significativos também não provam ausência de toda estrutura linear.

O requisito do professor se refere ao diagnóstico do **modelo selecionado**. Não é necessário ocupar os slides com todos os modelos candidatos, mas é necessário documentar o diagnóstico do escolhido em cada escala apresentada.

### 3.3 Proposta, ainda não implementada

1. Reexaminar FAC/FACP residual e o padrão de rejeição usando somente o treino.
2. Retomar o ciclo de identificação, estimação e diagnóstico Box–Jenkins, dentro dos métodos das aulas.
3. Registrar a regra de seleção, os horizontes diagnósticos e as tentativas. Não escolher a defasagem do teste apenas para conseguir p > 0,05.
4. Se houver mudança no modelo final, recalcular as previsões, métricas e figuras correspondentes.
5. Informar o caráter retrospectivo da revisão e a exposição prévia aos resultados de teste.
6. Se nenhum candidato defensável atender ao requisito, declarar a limitação e buscar orientação do professor. Não garantir antecipadamente que toda escala passará.

Acrescentar ARCH/GARCH à variância não corrige automaticamente autocorrelação da média. Tampouco o Ljung–Box dos resíduos ao quadrado substitui o Ljung–Box dos resíduos da equação da média.

## 4. Estacionariedade e equação ajustada

### 4.1 Classificação determinística

Os modelos atuais usam **constante e nenhuma tendência determinística**, com d=0 para os retornos. Essa especificação precisa aparecer literalmente na apresentação.

Rodar ADF sem constante, com constante e com tendência é uma análise de especificações; não constitui, por si só, um procedimento que escolhe entre essas classificações. Média estimada próxima de zero também não equivale a impor ausência de constante.

Manter a interpretação correta das hipóteses:

- ADF e PP: H0 = raiz unitária. A rejeição fornece evidência contra essa hipótese.
- KPSS: H0 = estacionariedade em nível ou em torno de tendência, conforme a especificação. Não rejeitar não significa provar estacionariedade.

A ausência de rejeição não demonstra estabilidade de toda a distribuição nem ausência de dependência na variância.

### 4.2 Equação que falta nos slides

Enquanto o selecionado permanecer ARMA(0,0) com constante, a equação da média por escala é:

```math
r_t^{(s)} = \widehat{\mu}_s + \varepsilon_t^{(s)}
```

Por exemplo, para **60 minutos**, com retorno logarítmico medido em porcentagem:

```math
r_t^{(60)} = -0{,}00351166 + \varepsilon_t^{(60)}
```

Trata-se de **ARIMA(0,0,0) com constante**, ajustado aos retornos, não ao nível de preços. O número acima vem da [tabela de modelos selecionados](https://github.com/avilarenan/EAD6034/blob/ef21a78033a816cda9ab8abbb39823e8becf398c/results/entrega_28_09/tables/selected_models.csv).

Para cobrir todas as escalas, pode-se apresentar a equação geral e uma tabela compacta dos coeficientes. Se o diagnóstico levar a outro modelo, a equação deve ser atualizada.

Caso a variância condicional faça parte da exposição, mostrar sua equação separadamente e esclarecer a estimação sequencial. Não atribuir à equação da média propriedades residuais que os diagnósticos rejeitam.

### 4.3 Mudança dos resultados de KPSS

O novo treino e as especificações de bandwidth não são iguais aos anteriores. A frase “mais dados resolveram a divergência” atribui uma causa que não foi isolada.

Formulação proposta:

> Na configuração atual de amostra e especificações, ADF/PP rejeitam raiz unitária e KPSS não rejeita estacionariedade. A diferença em relação à análise anterior evidencia sensibilidade à amostra e à especificação.

Não dizer que o novo corte “consertou” a estacionariedade.

## 5. Integridade da divisão 80/20

A nova regra usa **374 de 467 pregões no treino**, até 15/07/2025, e **93 no teste**, de 16/07/2025 a 28/11/2025. A mudança mecânica atende à orientação de usar aproximadamente 80/20.

Entretanto, o novo teste é um subconjunto do período de 2025 já examinado na entrega anterior. A regra mecânica evita escolher deliberadamente o corte pelo melhor resultado, mas **não restaura um holdout nunca observado**.

Formulação proposta:

> A divisão cronológica 80/20 foi adotada mecanicamente em atendimento à orientação do professor. O período de teste se sobrepõe ao conjunto de 2025 já examinado anteriormente; os resultados devem ser interpretados com essa limitação.

Distinguir:

- corte escolhido por regra mecânica;
- estimação sem usar o novo teste;
- estados atualizados somente com observações passadas;
- exposição prévia do pesquisador aos resultados desse período.

São propriedades diferentes. Uma não garante automaticamente as demais.

## 6. Previsão, horizonte e métricas

### 6.1 One-step e multi-step

| Avaliação | Escala do modelo | Esquema |
| --- | --- | --- |
| Próxima barra nativa | Todas as escalas | One-step-ahead da própria escala |
| Retorno futuro comum de 60 minutos | 1 minuto | Soma de uma trajetória de 60 passos futuros |
| Retorno futuro comum de 60 minutos | 5 minutos | Soma de uma trajetória de 12 passos futuros |
| Retorno futuro comum de 60 minutos | 15 minutos | Soma de uma trajetória de 4 passos futuros |
| Retorno futuro comum de 60 minutos | 30 minutos | Soma de uma trajetória de 2 passos futuros |
| Retorno futuro comum de 60 minutos | 60 minutos | One-step-ahead |

Dentro de uma trajetória multi-step, a origem é a mesma e não se inserem retornos intermediários realizados. Nas origens posteriores, os estados podem incorporar observações que já se tornaram passadas.

**Multi-step não é sinônimo de alvos sobrepostos.** A avaliação horária tem 837 alvos não sobrepostos, embora modelos de escalas menores construam trajetórias com vários passos.

O diário OC é outro alvo e deve permanecer fora do ranking intradiário comum.

Fonte: [forecast_evaluation.py](https://github.com/avilarenan/EAD6034/blob/ef21a78033a816cda9ab8abbb39823e8becf398c/src/ead6034/forecast_evaluation.py).

### 6.2 Justificativa do horizonte

Explicar duas escolhas:

1. Por que prever uma hora ajuda a examinar a hipótese original de maior previsibilidade em escalas agregadas e qual decisão de execução/risco poderia usar esse horizonte.
2. Por que os modelos precisam prever o mesmo retorno futuro para uma comparação de erros interpretável.

Não afirmar que 60 minutos é universalmente ótimo ou economicamente rentável. Não há avaliação de estratégia líquida de custos.

### 6.3 RMSE e MAE

Essas métricas já existem na [tabela de acurácia](https://github.com/avilarenan/EAD6034/blob/ef21a78033a816cda9ab8abbb39823e8becf398c/results/entrega_28_09/tables/accuracy.csv). Falta apresentá-las diretamente.

No alvo comum de 60 minutos, o ARMA_BIC atual tem, em todas as escalas intradiárias, até precisão numérica:

- n = 837;
- RMSE = 0,25918681;
- MAE = 0,18073368;
- MSE/modelo dividido por MSE/zero = 1,00136213.

RMSE e MAE estão na unidade do retorno expresso em porcentagem. A razão de MSE é adimensional e corresponde a aproximadamente **0,1362% de aumento relativo de MSE**, não a pontos percentuais de retorno.

Os valores praticamente idênticos são compatíveis com a seleção de médias constantes e com a agregação sobre os mesmos dados. A faixa “0,14%–0,16%” não deve ser atribuída ao ARMA_BIC entre escalas: separar esse modelo dos comparadores AR/MA.

### 6.4 MAPE

O requisito literal permanece pendente. O MAPE convencional é:

```math
\mathrm{MAPE} = \frac{100}{N}\sum_{t=1}^{N}
\left|\frac{r_t-\widehat r_t}{r_t}\right|
```

Retornos iguais a zero tornam o termo indefinido; retornos muito próximos de zero tornam a métrica instável. Não basta omiti-la silenciosamente.

Proposta:

- Explicitar a fórmula, as ocorrências de denominador zero no alvo avaliado e a limitação.
- Quando indefinido, registrar “não definido” com a justificativa correspondente, sem inventar um valor finito.
- Solicitar aceitação do professor para a limitação da métrica neste alvo.
- Não substituir zeros por epsilon arbitrário e não excluir silenciosamente observações.
- Não mudar de retorno para preço apenas para obter um MAPE finito sem declarar e discutir a mudança do alvo.

Esta proposta não equivale a afirmar que a exigência formal já foi dispensada.

### 6.5 Figura realizado versus previsto

A figura [09_real_vs_previsto_60min.pdf](https://github.com/avilarenan/EAD6034/blob/ef21a78033a816cda9ab8abbb39823e8becf398c/results/entrega_28_09/figures/09_real_vs_previsto_60min.pdf) já existe e apresenta o retorno realizado no teste e a previsão constante do ARMA(0,0), ao longo de 837 barras.

Ela não está no PDF final analisado. Incorporá-la, identificando:

- período de teste, horizonte e unidade;
- que a previsão vem de parâmetros estimados no treino;
- que uma linha quase horizontal é o comportamento esperado desse modelo, e não um erro de desenho;
- que previsão fora da amostra e ajuste dentro da amostra são conceitos diferentes.

## 7. Ajustes necessários nas conclusões

### 7.1 Diebold–Mariano

A comparação principal apresentada é **AR versus MA**, não **ARMA versus retorno zero**.

Consequentemente:

- Pode-se dizer que os testes apresentados não rejeitam igualdade da perda esperada entre AR e MA no horizonte comum, a 5%.
- Não se pode usar esses p-valores para concluir ausência de diferença significativa entre ARMA e zero.
- Não rejeitar uma diferença não prova equivalência.
- Evitar generalizar o resultado do alvo comum a todos os horizontes e recortes.
- Não adicionar um DM entre modelos aninhados apenas para preencher essa lacuna; respeitar a orientação da Aula 4.

Proposta de redação:

> No alvo comum, o ARMA selecionado apresenta MSE aproximadamente 0,136% superior ao retorno zero. Essa é uma comparação descritiva. Os testes DM exibidos comparam AR com MA e não rejeitam igualdade da perda esperada entre esses dois comparadores.

Fontes: [acurácia](https://github.com/avilarenan/EAD6034/blob/ef21a78033a816cda9ab8abbb39823e8becf398c/results/entrega_28_09/tables/accuracy.csv), [DM](https://github.com/avilarenan/EAD6034/blob/ef21a78033a816cda9ab8abbb39823e8becf398c/results/entrega_28_09/tables/diebold_mariano.csv) e [código](https://github.com/avilarenan/EAD6034/blob/ef21a78033a816cda9ab8abbb39823e8becf398c/src/ead6034/forecast_evaluation.py).

### 7.2 GJR e assimetria

GJR não vencer por BIC significa que o critério não favoreceu o parâmetro adicional. Não é um teste formal que rejeita a existência de assimetria.

A implementação examinada publica estimativas de gamma, mas não publica os respectivos erros-padrão e testes de significância na tabela de variâncias. Sinais diferentes entre escalas também não constituem, isoladamente, prova de inexistência do efeito.

Proposta de redação:

> Entre os candidatos avaliados no treino, o BIC não favoreceu a inclusão do termo assimétrico de GJR.

Evitar “GJR provou ausência de alavancagem”, “assimetria rejeitada” ou chamar a comparação por BIC de teste de significância de gamma. Se houver inferência adicional, ela deve ser explicitamente implementada, documentada e compatível com as aulas.

Fonte: [conditional_volatility.py](https://github.com/avilarenan/EAD6034/blob/ef21a78033a816cda9ab8abbb39823e8becf398c/src/ead6034/conditional_volatility.py).

### 7.3 Média, variância e previsão

Manter separadas:

- estacionariedade;
- ausência de autocorrelação residual;
- adequação da variância condicional;
- qualidade do ajuste no treino;
- desempenho preditivo fora da amostra;
- viabilidade econômica depois de custos.

Na estimação sequencial atual, incluir ARCH/GARCH não muda a previsão pontual da média. Melhora em uma proxy de variância não demonstra melhora de previsão do retorno.

Os diagnósticos da variância também não passam universalmente: a tabela do slide 7/10 mostra rejeição em Q(z²) para 1, 30 e 60 minutos e diário. Tornar a hipótese e a decisão explícitas. Não dizer que toda dependência foi eliminada.

### 7.4 Hipóteses de escala, overnight e leilões

Preservar a pergunta original: barras horárias poderiam ser mais previsíveis por agregarem flutuações de curtíssimo prazo. Tratá-la como hipótese confrontada com os dados, não como conclusão antecipada.

Os resultados atuais não sustentam uma vantagem geral da escala horária na previsão da média em relação ao benchmark.

- Os retornos excluem o salto overnight, mas as defasagens e os estados atravessam pregões.
- Isso não elimina efeitos da informação acumulada durante o fechamento.
- Os recortes de início/fim e de gap são descritivos.
- A base e o desenho não identificam causalmente o efeito dos leilões.
- Não inferir eficiência de mercado ou impossibilidade de previsão a partir deste único ativo, período e conjunto de modelos.

### 7.5 Zero-share

O slide descritivo chama zero-share de “barras sem negócio”. O cálculo é `mean(y == 0)`: **proporção de retornos iguais a zero**.

Negócios podem ocorrer sem alteração do preço. Substituir o rótulo e evitar inferências sobre ausência de negociação.

Fonte: [forecast_pipeline.py](https://github.com/avilarenan/EAD6034/blob/ef21a78033a816cda9ab8abbb39823e8becf398c/src/ead6034/forecast_pipeline.py).

## 8. Comparação com o artigo e disciplina de escopo

A referência é Matías e Reboredo (2012), *Forecasting performance of nonlinear models for intraday stock returns*, Journal of Forecasting, 31(2), 172–188, [DOI](https://doi.org/10.1002/for.1218).

Antes de redigir a comparação, conferir no artigo as afirmações específicas. Este documento não acrescenta resultados atribuídos ao paper que não foram verificados nesta revisão.

Proposta de uma comparação compacta:

| Dimensão | O que confrontar |
| --- | --- |
| Dados e mercado | Ativo, mercado, período, frequência e microestrutura |
| Alvo e horizonte | Retorno previsto, passos, origens e eventual sobreposição |
| Modelos | Benchmark linear, alternativas e diferenças de escopo |
| Avaliação | Partição temporal, métricas, referências triviais e testes |
| Resultados | Evidência publicada versus achados do WIN, sem comparar MSE bruto de alvos distintos |
| Alcance econômico | Custos, operabilidade e limites da interpretação |

**Métodos das aulas continuam sendo a restrição prioritária.** GJR e os demais componentes devem ter ligação verificável ao conteúdo autorizado. MLP é mencionado como classe de benchmark na Aula 4, mas essa menção não torna automaticamente qualquer arquitetura ou protocolo um método ensinado.

Chronos zero-shot é uma extensão exploratória e não deve dominar a narrativa central. Manter a extensão como opcional/apêndice, ou confirmar sua aceitação, é preferível a deixar requisitos obrigatórios sem espaço. Rotular um método como exploratório não dispensa uma restrição explícita de escopo.

Não interpretar o desempenho ruim de uma execução zero-shot como evidência contra todos os modelos de fundação.

## 9. Apresentação, roteiro e rastreabilidade

### 9.1 Alterações de comunicação

- Remover do PDF referências a “corrigida”, “antes/agora”, “lacuna pedida” e outras narrativas de revisão, conforme a preferência já expressa pelo autor.
- Isso não autoriza esconder a mudança de protocolo ou a exposição prévia ao teste. Registrar essas informações de forma factual e neutra.
- Atualizar o roteiro oral junto com os slides. Remover frases como “teste t para provar” ausência de estrutura e “mais dados resolveram” os conflitos.
- Exibir decisões dos testes e suas hipóteses. Um p-valor sem interpretação não atende ao objetivo didático.
- Aumentar a legibilidade dos rodapés e reduzir texto onde necessário, sem eliminar ressalvas importantes.
- Manter capa e contracapa, disciplina, sigla, nome do aluno e professor.
- Manter as três entregas cumulativas na narrativa: descrição/FAC/FACP, estacionariedade/Box–Jenkins e previsão/alternativas/variância.

### 9.2 Links e arquivos

- Atualizar o README: ele ainda apresenta a entrega de 21/09 como versão cumulativa atual.
- Preservar versões históricas e apontar claramente para o PDF e roteiro finais de 28/09.
- Preferir referências clicáveis ao commit específico do código e dos resultados, não apenas links móveis para `main`.
- Conferir se o “relatório completo” mencionado nos slides realmente existe para esta execução e não remete a resultados de outra partição.
- Manter a referência original [BTG Alpha Lab — BTG-ATS-A26](https://alphalab.btgpactual.com/datasets/publication:7a74b3ae-90e0-4393-b1e0-01e61c0bedba).
- Não publicar dados brutos, retornos individuais, resíduos ou previsões por barra fora dos limites já estabelecidos.

### 9.3 Tempo e integridade do PDF

O limite do seminário final é **15 minutos**, diferente do roteiro de cinco minutos usado numa entrega anterior. Reorganizar o tempo para priorizar requisitos obrigatórios e reservar margem para transições.

Na versão final a entregar:

1. Conferir correspondência entre slides e roteiro.
2. Renderizar todas as páginas e verificar tabelas, figuras, rodapés e links.
3. Validar leitura do PDF e sua contagem de páginas.
4. Após publicação, conferir tamanho e hash do arquivo baixado do GitHub, evitando a repetição do problema de PDF truncado.
5. Usar um link de versão fixa para a entrega. Verificar as regras de submissão antes de alterar material já enviado.

## 10. Ordem de execução proposta

Nenhum dos itens abaixo foi implementado por este documento.

### P0 — diagnóstico e honestidade inferencial

- [ ] Resolver ou declarar formalmente a inadequação residual nas escalas problemáticas.
- [ ] Corrigir as conclusões sobre ruído branco, DM, GJR, KPSS e integridade do holdout.
- [ ] Manter seleção/reconsideração dos modelos no treino e documentar toda mudança.

### P1 — requisitos obrigatórios do seminário

- [ ] Declarar a classificação determinística e d=0 dos retornos.
- [ ] Mostrar a equação efetivamente ajustada e seus coeficientes.
- [ ] Mostrar hipóteses, horizontes e decisões de Ljung–Box do modelo selecionado.
- [ ] Explicitar one-step/multi-step e a justificativa do horizonte.
- [ ] Exibir RMSE/MAE e tratar a exigência de MAPE de forma transparente.
- [ ] Incorporar a figura realizado versus previsto.
- [ ] Comparar substantivamente com o artigo de referência.
- [ ] Reescrever a avaliação preditiva final sem extrapolar os testes realizados.

### P2 — acabamento e entrega

- [ ] Corrigir zero-share.
- [ ] Priorizar os requisitos centrais sobre a extensão neural.
- [ ] Limpar linguagem de revisão no PDF e sincronizar o roteiro.
- [ ] Atualizar README e referências de versão.
- [ ] Ensaiar dentro de 15 minutos.
- [ ] Validar e conferir o PDF efetivamente publicado.

## 11. Mensagem final recomendada, condicionada à resolução das pendências

> A análise compara previsões de retornos do WIN em múltiplas escalas usando alvos futuros alinhados. Na configuração avaliada, a seleção parcimoniosa da média não produziu ganho global de MSE sobre o retorno zero no horizonte comum. Há dinâmica de variância, mas sua modelagem é parcial e distinta da previsão pontual da média. Os diagnósticos residuais impõem limites à adequação de alguns modelos. Os resultados dependem do ativo, período, construção da amostra e protocolo de avaliação, e não identificam causalmente efeitos de leilões nem demonstram eficiência de mercado.

Essa síntese não substitui os diagnósticos exigidos: se o modelo mudar, deve ser atualizada com os resultados correspondentes.
