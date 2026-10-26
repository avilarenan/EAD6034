# Conferências da entrega

Verificação realizada em 26/10/2026, com Python 3.12.14 e as dependências fixadas em requirements.txt.

## Execução e identidades

- O script completo executou sem intervenção no modo `--lote`. Tempo observado: aproximadamente 28–32 segundos, com 399 réplicas em cada um dos três bootstraps (antes, depois e amostra completa).
- A simulação recuperou melhor a resposta verdadeira com a ordem correta: RMSE das IRFs aproximadamente 0,0116, contra 0,1328 com ordem errada.
- A decomposição histórica reconstrói as cinco séries dentro da tolerância de 1e-8. O erro efetivamente observado está em `resumo.json`.
- A FEVD soma 100% em cada variável/horizonte. As 120 permutações satisfazem `P @ P.T = Sigma`.
- Os dados possuem continuidade mensal, datas únicas e nenhuma observação faltante. As séries usadas em log são positivas.
- O modo de apresentação tem suporte TkAgg/Tk 8.6 no ambiente usado. O PDF tem cinco páginas, com texto extraível e revisão visual de todas elas.

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

Os seis cenários concluíram todas as etapas do script. Os valores completos, inclusive para câmbio, estão em [sensibilidades.csv](resultados/sensibilidades.csv). Use o painel do mesmo `analise.py` para reproduzir; não há outra implementação econométrica.

As sensibilidades usam menos réplicas que a base e não são uma busca por configuração “vencedora”. A diferença pontual do Brent mantém sinal positivo nesses ensaios, mas a banda com p=4 inclui zero. Para inferência mais refinada, aumente BOOT e continue respeitando a ressalva de especificação residual.

## Limitações verificadas, não escondidas

A amostra completa e os dois regimes rejeitam ausência de autocorrelação na base. Há evidência de não normalidade/ARCH em algumas equações. A Selic em nível apresenta dúvida de estacionariedade. O código sinaliza essas questões; nenhuma conferência numérica as elimina.

A escolha de p na previsão é refeita apenas com o prefixo de dados até cada origem. AR e VAR usam os mesmos lags e determinísticas. DM é reservado ao benchmark sazonal não aninhado para p<12; AR recebe Clark–West. As previsões são pseudo fora da amostra, sem vintages ou calendário de divulgação reconstruídos.

As tabelas e figuras de referência foram geradas novamente com a configuração-base após os ensaios. Os hashes da versão do código e dos dados que produziram essa execução estão em `resultados/resumo.json`. Os arquivos originais têm proveniência própria em `dados/fontes.json`.
