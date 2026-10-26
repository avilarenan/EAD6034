# Guia rápido: Desafio 5

Leia em 15 minutos. Roteiro de fala em [ROTEIRO_APRESENTACAO.md](ROTEIRO_APRESENTACAO.md).

## A mensagem, em três frases

1. Depois de outubro de 2016, a mesma alta de 10% no Brent passa mais ao IPCA: **+0,07 p.p. antes, +0,41 p.p. depois, diferença +0,34 p.p.** (banda de 90%: +0,10 a +0,58).
2. A mudança está **no próprio mês do choque**: a correlação das surpresas de Brent e IPCA vai de −0,02 a +0,42, compatível com reajustes mais frequentes dos combustíveis.
3. O sinal resiste a 13 variantes (+0,20 a +0,38). A significância depende das defasagens e dos meses finais, e o antes/depois **não isola** o efeito da Petrobras.

## As três perguntas do enunciado

1. **O repasse aumentou? E o do câmbio?** O do Brent, sim: mais forte (+0,07 → +0,41) e mais rápido (+0,145 p.p. já no mês do choque, contra −0,005). O do câmbio, não: a resposta estimada cai (+0,25 → −0,49), mas é instável entre variantes.
2. **Quantas restrições no Chow? E o poder?** 55 no sistema: 5 equações × (10 defasagens + constante), com p=2; com p=4, 105. Muitas restrições diluem o poder contra uma mudança concentrada em poucos coeficientes, e o Chow da forma reduzida não testa a correlação dos resíduos. O LR rejeita (p=0,001); o teste focalizado no mesmo mês, com 1 restrição, rejeita com p=0,0001. O OLS-CUSUM do `vars::stability()` não rejeita em nenhuma equação.
3. **Política ou correlação dos resíduos?** Troque uma peça de cada vez entre os períodos: só as defasagens (A) mudam a resposta em −0,04 a +0,08; só a covariância (Σ), em +0,26 a +0,38. A mudança está na correlação do mesmo mês. Em dados mensais, reajustes mais frequentes aparecem exatamente assim, mas o VAR recursivo não separa isso de choques comuns. Com o IPCA antes do Brent, que proíbe o repasse no mês, a diferença cai para +0,10.

**Pós-2016 curto e 2020.** Há 118 meses depois da quebra. Com p=2, cada equação tem 28 parâmetros: 10 defasagens, constante, 11 meses e 6 pulsos. Cada defasagem a mais custa 5 por equação; com p=4, a banda já inclui zero. Os pulsos dão a cada mês atípico um intercepto próprio: sem eles a diferença é +0,35; excluindo 2020, +0,32.

## Conceitos em uma linha

- **VAR:** cada variável depende dos meses anteriores de todas as cinco.
- **Choque de 10%:** surpresa única no Brent no mês 0. As outras surpresas ficam em zero; as variáveis reagem pelo modelo.
- **Resposta acumulada:** soma das diferenças do IPCA, com e sem o choque, do mês 0 ao 12. Em p.p. de inflação acumulada.
- **Ordem de Cholesky** (Brent → câmbio → IPA → IPCA → Selic): quem vem antes pode afetar quem vem depois **no mesmo mês**.
- **Banda bootstrap de 90%:** reamostra os resíduos, reestima e recalcula. Olhe a banda **da diferença**, não a sobreposição das bandas separadas.
- **Portmanteau / Ljung–Box:** testam autocorrelação dos resíduos. O conjunto rejeita; por equação, só a Selic rejeita.
- **Granger:** o passado de X ajuda a prever Y. Não é causalidade.

## Perguntas prováveis

| Pergunta | Resposta curta |
|---|---|
| Por que o Brent primeiro na ordem? | O Brasil não move o preço internacional dentro do mês. É a hipótese usual para economia pequena. |
| E se mudar a ordem? | A diferença é positiva nas 120 ordens, de 0,03 a 0,34. A base fica no topo; com o IPCA antes do Brent, o repasse no mês é proibido e cai para 0,03–0,10. |
| Os resíduos têm autocorrelação. O modelo vale? | A rejeição vem da equação da Selic: reuniões do Copom a cada seis semanas numa média mensal. Sem a Selic, +0,38. Por isso as bandas são tratadas como exploratórias. |
| Por que p=2? E com mais? | O BIC escolhe 2. Com p=4, a diferença cai para 0,20 e a banda inclui zero: a significância depende de p. |
| Isso prova o efeito da Petrobras? | Não. É comparação entre períodos que também diferem em pandemia, corte do ICMS de 2022 e estratégia de 2023. |
| Por que 10% e não um desvio-padrão? | O desvio-padrão muda entre períodos. Fixar 10% compara a transmissão, não o tamanho típico dos choques. |
| O Brent sobe só 10%? | Sobe 10% no mês 0 e depois segue a dinâmica: no mês 12, 14,1 acima antes e 10,1 depois (100×log). A razão de repasse também sobe: 0,005 → 0,041. |
| Por que o câmbio dá negativo depois? | Não é efeito estrutural: varia de −0,06 a −0,94 entre variantes e a banda inclui zero em 7 das 13. |
| O câmbio não deveria vir antes do Brent? | O real reage ao petróleo no mês e o Brasil não move o Brent; por isso o Brent vem antes. Invertendo, a diferença é +0,28, com banda que exclui zero. |
| Cadê o `vars::stability()`? | O código é em Python. O anexo traz o OLS-CUSUM de Ploberger–Krämer, o mesmo padrão do `vars`, e o CUSUM de resíduos recursivos. Nenhum rejeita: a mudança está no mesmo mês, não nas defasagens. |
| A pandemia, o ICMS ou 2026 explicam? | Sem 2020: +0,32. Com pulsos no corte do ICMS: +0,38. Sem 2026, +0,29, mas a banda toca zero. |
| Por que a janela móvel não mostra o salto em 2016? | Janelas que terminam até 2020 ainda contêm 2015–16, quando o Brent caiu e o IPCA subiu. A curva só passa de 0,03 quando a janela termina no fim de 2022. |
| O VAR prevê melhor que o AR? | Em 1 mês, sim (RMSE 0,334 contra 0,347; Clark–West p=0,0003). Em 12 meses, não. |

## Mudanças que o professor pode pedir

Mude **uma linha** no painel (célula 1), use **Restart Kernel and Run All Cells** e leia os novos números. Para ser rápido, ponha `BOOT=99`: tudo roda em menos de meio minuto.

| Pedido | O que mudar no painel | O que esperar |
|---|---|---|
| Mais defasagens | `P_FIXO=4` | Diferença +0,20; banda inclui zero |
| Outro critério | `CRITERIO="aic"` | O AIC escolhe p=3 |
| Outra data de quebra | `QUEBRA="2018-01-01"` | +0,39 |
| Amostra até antes de 2023 | `FIM="2023-04-01"` | +0,34 |
| Outra ordem | `ORDEM=["cambio", "brent", "ipa", "ipca", "selic"]` | +0,28. Use os cinco nomes, sem erro de grafia |
| Choque maior | `CHOQUE_PCT=20.0` | Respostas ×1,91: o modelo é linear e o choque é em log |
| Outro horizonte | `H_REPASSE=6` | Até 24; acima disso, aumente também `H` |
| Banda de 95% | `CONFIANCA=0.95` | Bandas mais largas |
| Sem 2020 | `EXCLUIR_2020=True` | +0,32 |
| Selic em diferença ou fora | `DIFERENCIAR_SELIC=True` ou `INCLUIR_SELIC=False` | +0,35 ou +0,38 |
| Impor uma restrição | `RESTRICOES={"brent": ["cambio", "ipa", "ipca", "selic"]}` | Brent exógeno ao Brasil: +0,33 |
| Mais um pulso | Acrescente ao `PARAMETROS.update(...)`: `MESES_ATIPICOS=PARAMETROS["MESES_ATIPICOS"] + ["2022-07", "2022-08"]` | +0,38 |
| Sem sazonais ou sem pulsos | `SAZONAIS=False` ou `DUMMIES=False` | Resíduos piores; compare a diferença |
| Ver tabelas escondidas | `EXIBIR_TUDO=True` | Resíduos por regime, raízes e razões nas células 2 e 3 |

Pedidos que exigem editar `analise.py`:

- **Resposta do IPA em vez do IPCA:** na função `resposta()`, troque `t[:, 3, :2]` por `t[:, 2, :2]`. Índices: Brent 0, câmbio 1, IPA 2, IPCA 3, Selic 4. Os rótulos continuam dizendo IPCA.
- **Choque de um desvio-padrão:** em `resposta()`, apague `* impacto / np.diag(t[0])[:2]`.
- **Nova variante na célula 4:** troque a chamada por `var.variantes(var.VARIANTES + [("Amostra", "Início em 2008", {"INICIO": "2008-01-01"})])`.

Se uma mudança der erro, desfaça a linha e rode tudo de novo: o painel volta à referência.

## Antes da aula

1. Abra o notebook e rode **Restart Kernel and Run All Cells** uma vez. Leva cerca de um minuto.
2. Na fala, rode só as células 1 a 4. A célula 4 leva uns 40 segundos: comente as tabelas de identificação enquanto ela roda.
3. Deixe este guia aberto em outra aba.
