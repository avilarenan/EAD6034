# Conferências da entrega

Verificação realizada em 26/10/2026, com Python 3.12.14 e as dependências fixadas em requirements.txt.

## Revisão de 26/10/2026: interpretação, variantes e notebook enxuto

- Reprodução independente em Linux, Python 3.12 e as versões de `requirements.txt`: todas as tabelas anteriores coincidem até 1e-10. Os hashes de dados e código conferem com `resumo.json`.
- Mudanças numéricas: nenhuma na especificação-base. Foram acrescentadas colunas (`LB_p`, `impacto_h0`, `corr_residuo_ipca`, `origem_acumulada`, posição da base no envelope) e as tabelas `05_impacto_vs_propagacao.csv` e `10_variantes.csv`, que substituem `05_propagacao_covariancia_comum.csv` e `sensibilidades.csv`.
- As 15 variantes usam 399 réplicas e as sementes da célula 3; a linha-base reproduz a banda principal, [+0,100; +0,576]. Os valores estão no README.
- Novos itens alinhados ao enunciado: `RESTRICOES` para zeros nas defasagens, com reestimação da equação restrita; teste focalizado do mesmo mês com uma restrição (`05_teste_mesmo_mes.csv`, p=0,0001); OLS-CUSUM de Ploberger–Krämer, padrão de `vars::stability()` (`06_cusum_ols.csv`), sem rejeição; variantes sem pulsos (+0,353) e com Brent exógeno (+0,333). Com `RESTRICOES` vazio, todos os números anteriores ficam iguais.
- `deterministicas()` monta a matriz de uma vez e o bootstrap a reaproveita: mesma saída, cerca de três vezes menos tempo nessa etapa.
- Notebook executado em kernel novo, sem erros: 5 células de código, 60 s no total (célula 4: 42 s; anexo: 11 s). Também sem erros com `INCLUIR_SELIC=False` (24 ordens) e com `P_FIXO=4, BOOT=99` (31 s).
- CSVs passam a ser gravados com fim de linha LF em qualquer sistema; `dados/mensal.csv` só é regravado se o conteúdo mudar.

As seções abaixo descrevem a verificação anterior. A tabela de sensibilidades com 99 réplicas foi substituída pela de variantes com 399.

## Execução e identidades

- O script completo executou sem intervenção no modo `--lote`. Tempo observado: aproximadamente 28–32 segundos, com 399 réplicas em cada um dos três bootstraps (antes, depois e amostra completa).
- A simulação recuperou melhor a resposta verdadeira com a ordem correta: RMSE das IRFs aproximadamente 0,0116, contra 0,1328 com ordem errada.
- A decomposição histórica reconstrói as cinco séries dentro da tolerância de 1e-8. O erro efetivamente observado está em `resumo.json`.
- A FEVD soma 100% em cada variável/horizonte. As 120 permutações satisfazem `P @ P.T = Sigma`.
- Os dados possuem continuidade mensal, datas únicas e nenhuma observação faltante. As séries usadas em log são positivas.
- O modo de apresentação usa o backend inline do Jupyter. O PDF tem cinco páginas, com texto extraível e revisão visual; os slides 3 e 4 descrevem um único choque de Brent, as condições do experimento e a leitura dos resultados.

## Revisão para apresentação no Jupyter

- Notebook validado com nbformat e executado por nbclient em kernel Python novo: **6 células de código, 34 linhas, 9 figuras inline e 21 tabelas HTML**, sem erros. JupyterLab 4.6.4, nbclient 0.11.0 e ipykernel 7.4.0.
- A execução-base completa levou 44 segundos, incluindo inicialização e encerramento do kernel; o tempo registrado da análise foi 30,5 segundos. As saídas estão gravadas no notebook publicado.
- Respostas aos choques, bandas da diferença, diagnósticos, métricas de previsão, reconstrução histórica e erros da simulação foram comparados com a versão anterior: **valores numéricos idênticos**. A reorganização não mudou o modelo ou os dados.
- Um segundo kernel executou as seis células após modificar somente o painel: P_FIXO=4, BOOT=99 e outra pasta de saída. Concluiu em 16,4 segundos, com as mesmas 9 figuras e 21 tabelas. A diferença do Brent permaneceu em aproximadamente +0,198 p.p., banda de 90% [−0,129; +0,444].
- O gráfico 01 foi conferido com nomes e unidades nos eixos. O gráfico 06 identifica a linha tracejada como início do regime pós-quebra em 10/2016; a legenda acompanha o parâmetro QUEBRA.
- Os slides 3, 4 e 5 foram renderizados e inspecionados depois das mudanças. O README e o roteiro oral usam o notebook como caminho principal.
- As 50 opções efetivas da execução ficam registradas em resultados/resumo.json. As rotinas técnicas permanecem em analise.py; importar esse módulo não executa a análise.

## Comparação independente com statsmodels

A estimação transparente por MQO foi comparada com `statsmodels.tsa.api.VAR`, usando p=2 e exatamente as mesmas determinísticas. Não é apenas uma comparação com os próprios resultados do script.

| Cálculo | Maior diferença absoluta |
|---|---:|
| Coeficientes | 0 |
| Covariância residual | 0 |
| Coeficientes da representação MA | 6,3 × 10⁻¹⁵ |
| IRFs de Cholesky | 1,4 × 10⁻¹⁵ |
| P-valor do Portmanteau ajustado | 0 |
| Previsões recursivas de 12 passos | 8,9 × 10⁻¹⁵ |

Essas conferências verificam a implementação numérica. Não validam as hipóteses econômicas, a ausência de omissões ou a cobertura das bandas sob a autocorrelação diagnosticada.

## Sensibilidades executadas

Cada linha muda uma escolha em relação à base, com `BOOT=99` para ensaio. O alvo é a diferença pós menos pré da resposta acumulada do IPCA ao mesmo choque de +10% no Brent, de h=0 a h=12.

| Mudança | p selecionado/fixado | Diferença, p.p. | Banda pontual de 90% |
|---|---:|---:|---|
| Fixar p=1 | 1 | +0,302 | [+0,135; +0,445] |
| Fixar p=4 | 4 | +0,198 | [−0,129; +0,444] |
| Excluir 2020 e equações que o usam nos lags | 2 | +0,321 | [+0,013; +0,477] |
| Encerrar a amostra em abril/2023 | 2 | +0,342 | [+0,040; +0,685] |
| Diferenciar a Selic | 1 | +0,346 | [+0,116; +0,589] |
| Mover a quebra para janeiro/2018 | 2 | +0,390 | [+0,110; +0,725] |

Os seis cenários concluíram todas as etapas do script. Os valores atuais, com 399 réplicas e também para o câmbio, estão em [10_variantes.csv](resultados/10_variantes.csv). Use o painel da primeira célula do notebook para reproduzir; ele chama as mesmas rotinas de `analise.py`, sem outra implementação econométrica.

As sensibilidades usam menos réplicas que a base e não são uma busca por configuração “vencedora”. A diferença pontual do Brent mantém sinal positivo nesses ensaios, mas a banda com p=4 inclui zero. Para inferência mais refinada, aumente BOOT e continue respeitando a ressalva de especificação residual.

## Limitações verificadas, não escondidas

A amostra completa e os dois regimes rejeitam ausência de autocorrelação na base. Há evidência de não normalidade/ARCH em algumas equações. A Selic em nível apresenta dúvida de estacionariedade. O código sinaliza essas questões; nenhuma conferência numérica as elimina.

A escolha de p na previsão é refeita apenas com o prefixo de dados até cada origem. AR e VAR usam os mesmos lags e determinísticas. DM é reservado ao benchmark sazonal não aninhado para p<12; AR recebe Clark–West. As previsões são pseudo fora da amostra, sem vintages ou calendário de divulgação reconstruídos.

As tabelas e figuras de referência foram geradas novamente com a configuração-base após os ensaios. Os hashes da versão do código e dos dados que produziram essa execução estão em `resultados/resumo.json`. Os arquivos originais têm proveniência própria em `dados/fontes.json`.
