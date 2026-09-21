# Protocolo definido antes da avaliação de 2025

Entrega cumulativa de 21/09/2026. Seminário em 28/09/2026, máximo de 15 minutos.
Aluno: Renan de Luca Avila. EAD6034, Prof. Leandro Maciel.

## Pergunta e hipóteses

Investigar a previsibilidade dos retornos do WIN nas escalas de 1, 5, 15, 30 e
60 minutos e no diário. A hipótese de maior previsibilidade na escala horária
será confrontada com as previsões, sem impor uma ordenação aos resultados.
Ruído de microestrutura, informações acumuladas entre sessões e leilões são
motivações. Este desenho não identifica seus efeitos causais separadamente.

## Amostra e convenção aprovada

- Treino: 02/01/2024 a 30/12/2024, 246 pregões completos comuns.
- Avaliação: 02/01/2025 a 28/11/2025, 221 pregões completos comuns.
- Janela principal: [09:05,18:05), horário de São Paulo, 540 minutos.
- Intradiário: 100 log(C_final/C_fronteira), com fronteira inicial igual ao
  fechamento do candle iniciado às 09:04. Diário: 100 log(C_18:05/O_09:05).
- Retornos nunca atravessam pregões ou contratos. Nenhum zero, interpolação,
  winsorização ou retorno de rolagem é introduzido.
- O índice de cada escala é a sequência cronológica de observações. Defasagens
  e estados dos modelos continuam entre pregões, inclusive no diário.
- Um lag significa uma observação anterior, não necessariamente uma distância
  constante de relógio. Lacunas, rolagens e interrupções permanecem identificadas.
- A seleção de pregões completos é um filtro retrospectivo de qualidade. As
  métricas são condicionais à amostra incluída, não uma promessa de
  disponibilidade operacional intradiária.

A mudança substitui os testes por pregão da entrega de 14/09. Toda identificação,
inferência e estimação da nova entrega deve usar a mesma sequência anual. Os
artefatos antigos permanecem históricos, sem alteração silenciosa.

## Métodos restritos às aulas

- Aulas 3 e 4: FAC/FACP, ARMA, máxima verossimilhança gaussiana, AIC/BIC,
  diagnóstico Ljung–Box, previsões recursivas, MSE/MAE, combinação e DM.
- Aula 5: ADF, PP e KPSS, com hipóteses, especificação determinística, defasagens,
  estatísticas e valores críticos explícitos. Não rejeição não prova H0.
- Aula 6: ARCH-LM, ARCH(1), GARCH(1,1), estimação sequencial da variância dos
  resíduos, positividade/estabilidade e diagnóstico padronizado.
- Sem testes de painel, bootstrap, Ljung–Box modificado, redes neurais,
  modelos de mudança de regime, EGARCH ou novos testes de comparação.

## Seleção e modelos

1. Grade ARMA(p,q), p,q=0,...,5, constante, seleção por BIC apenas no treino.
   AIC complementar. Registrar não convergência, raízes e candidatos inelegíveis.
   A constante é a média incondicional na parametrização ARIMA de statsmodels.
2. AR puro com p=1,...,5 e MA puro com q=1,...,5: comparadores pré-especificados,
   selecionados por BIC em suas famílias. Não substituem silenciosamente o
   vencedor geral, que pode ser ARMA(0,0).
3. Referências: retorno zero e média do treino. Previsões idênticas são
   identificadas, não contadas como evidências independentes.
4. Combinação pré-fixada: 0,5 previsão AR + 0,5 previsão MA, sem otimizar pesos
   em 2025.
5. Variância constante, ARCH(1), GARCH(1,1) normal sobre as mesmas inovações
   da média ARMA fixa. BIC condicional compara apenas essas variâncias.
   Estimação sequencial, não MLE conjunta ARMA–GARCH. A previsão da média
   permanece igual. Variância prevista é avaliada contra a mesma inovação
   quadrada, uma proxy ruidosa, não uma variância observada.

## Avaliação preditiva

- Parâmetros e ordens fixados com 2024. Somente filtros/defasagens e variâncias
  condicionais são atualizados com observações já disponíveis em cada origem.
- Nativa: próxima barra, em todas as escalas, incluindo a primeira do pregão.
  Diário: retorno da próxima janela diária, conhecido somente após o seu fim.
- Horizonte físico comum: retorno acumulado dos próximos 60 minutos,
  origens 09:05,10:05,...,17:05. São nove alvos não sobrepostos por dia,
  iguais nas cinco escalas intradiárias. Nunca somar previsões de um passo
  atualizadas com realizações futuras dentro do alvo.
- Origem, alvo e máscara de avaliação devem coincidir entre os modelos e,
  no horizonte comum, entre as escalas. Verificação automática obrigatória.
- MSE, MAE, RMSE e razão MSE/modelo zero. Não comparar diretamente MSE
  de horizontes diferentes como se os alvos fossem os mesmos. MAPE excluído.
- DM principal: AR puro versus MA puro, perda quadrática. Perda absoluta é
  complementar. Famílias positivas não aninhadas, mas previsões degeneradas
  tornam o teste não aplicável. A fórmula da Aula 4 inclui correção de pequena
  amostra e referência t. Nesta avaliação os alvos não se sobrepõem: h_perda=1.
- Variância de longo prazo de DM: soma retangular de autocovariâncias da
  Aula 4. q principal corresponde a uma hora de barras no nativo, q=1 no
  comum60 e diário. q=0 como sensibilidade. Variância não positiva impede o
  cálculo do p-valor. Referência aproximada, sem correção de multiplicidade.
  Horizonte do modelo em barras é registrado separadamente de h_perda.
- Não aplicar DM às comparações aninhadas de variância nem alegar que o
  teste AR versus MA demonstra superioridade frente ao ARMA geral selecionado.

## Horários, interrupções e interpretação

- Faixas físicas fixas: início 09:05–10:05, meio 10:05–17:05 e fim 17:05–18:05.
  Apresentar descrição de treino e métricas fora da amostra por faixa.
- Gap auxiliar: primeiro open do dia fonte / último close do dia fonte anterior,
  apenas no mesmo contrato e sem dias úteis ausentes entre observações.
  Chamar "gap entre sessões observadas", nunca overnight oficial ou preço
  de leilão. Ausência de calendário validado exclui conservadoramente feriados.
- Grupos de magnitude do gap usam a mediana do |gap| nos pregões incluídos
  de 2024. Aplicar esse limiar fixo a 2025. Comparação por gap é exploratória.
- A base não contém fase de negociação. Documentos históricos oficiais
  comprovam apenas os intervalos descritos em market_hours_2024_2025.md.
  A janela principal não cobre os calls próprios de abertura/fechamento do WIN
  nos horários documentados. O call das ações subjacentes pode estar no meio
  ou no fim, conforme o regime. Não chamar todo o meio de período estável.

## Reprodutibilidade e publicação

- Python para toda a análise, dependências e sementes registradas.
- Tabelas agregadas, figuras, relatório, apresentação cumulativa de sete slides
  e fontes editáveis no repositório. Código clicável em cada slide.
  Atualização editorial de 21/09/2026, a pedido do autor: capa e contracapa
  acrescentadas aos sete slides de conteúdo, totalizando nove páginas no PDF.
  A inclusão não altera a análise nem o roteiro de cinco minutos.
- Dados brutos, preços, retornos individuais, previsões individuais, resíduos,
  objetos ajustados e caches ficam em private/, ignorados pelo Git.
- Testes de código: invariância do treino ao modificar 2025, ausência de dados
  futuros nas previsões, igualdade dos alvos de 60 minutos, estabilidade das
  variâncias, identidade do cálculo DM e correspondência das tabelas/slides.
- Relatar limitações, resultados negativos e falhas numéricas sem selecionar
  retrospectivamente especificações para favorecer a hipótese.
