# Roteiro oral - notebook e cinco slides, cerca de dez minutos

## Antes da apresentação

Abra `introducao.pdf` e `apresentacao.ipynb`. No notebook, use Shift+Enter para executar cada uma das seis células de código. As tabelas e figuras aparecem abaixo delas. Não é necessário abrir PNGs, CSVs ou o arquivo técnico enquanto apresenta.

A primeira célula concentra `PARAMETROS`; os cálculos reutilizáveis ficam em `analise.py`. Use a configuração-base antes da abertura. Para uma mudança de cenário, reinicie o kernel e execute todas as células.

## 0:00-2:15 - introdução em PDF

**Slide 1, 15 s.** “Minha pergunta é se o mesmo aumento inesperado do petróleo passa de maneira diferente ao IPCA antes e depois de outubro de 2016.”

**Slide 2, 20 s.** “O petróleo tem preço em dólares. O câmbio converte esse custo em reais. O IPA representa preços ao produtor, o IPCA ao consumidor e a Selic a condição monetária.”

**Slide 3, 45 s.** “O experimento é uma alta inesperada e única de 10% no Brent em dólares. Dentro de cada regime, comparo duas trajetórias com o mesmo ponto de partida: uma recebe essa surpresa; a outra não. As outras surpresas ficam zeradas, mas as variáveis podem reagir ao petróleo. Uso um modelo estimado até setembro de 2016 e outro a partir de outubro de 2016. Somo a diferença no IPCA desde o impacto até o mês 12.”

**Slide 4, 40 s.** “No modelo anterior, o choque acrescenta cerca de 0,07 ponto percentual de inflação acumulada. No posterior, acrescenta 0,41. A diferença entre essas respostas é 0,34. Estamos falando de efeitos estimados em relação ao caminho sem o choque, não da inflação total observada. A banda é condicional ao modelo, e há limitações nos resíduos e nas defasagens.”

**Slide 5, 15 s.** “Essa comparação entre períodos não isola o efeito da Petrobras. Agora vou construir o resultado no notebook e verificar sua sensibilidade.”

## 2:15-3:00 - células 1 e 2: condições e dados

Execute o painel de parâmetros e a leitura dos dados.

“Todos os controles que vou alterar estão neste dicionário. Os dados são locais. Brent e câmbio entram como variações do log; IPA e IPCA já são taxas mensais. A Selic está em nível na base.”

Mostre nomes e unidades dos eixos. Na tabela ADF/KPSS, aponte a dúvida de estacionariedade da Selic. Não leia cada número.

## 3:00-3:45 - célula 3: dinâmica e diagnósticos

“O BIC escolheu dois meses de memória. As raízes estão dentro do círculo, indicando estabilidade estimada. Porém, o Portmanteau ainda rejeita ausência de autocorrelação. São perguntas diferentes, e o diagnóstico limita a interpretação das bandas.”

“Granger mede informação preditiva adicional, condicionada às demais variáveis. Não estabelece causalidade estrutural.”

A tabela `02_diagnostico` e o gráfico das raízes bastam para a fala principal. Os outros resultados permanecem na mesma célula para perguntas.

## 3:45-5:10 - célula 4: o experimento principal

Enquanto o bootstrap roda:

“Aplico o mesmo aumento de 10% nos dois modelos para que a comparação não seja apenas uma diferença de volatilidade dos choques.”

No painel do Brent:

“A linha é o efeito acumulado no IPCA em relação ao caminho sem o choque. O modelo posterior responde mais na base. Para verificar a mudança, olho a banda da diferença, não apenas a sobreposição das bandas individuais.”

No painel do câmbio:

“Este é um segundo experimento, separado: agora a surpresa é uma depreciação de 10% do real. Não injetei os dois choques ao mesmo tempo. O sinal negativo no pós-período é sensível à especificação e não deve virar uma afirmação estrutural de que depreciar a moeda reduz preços.”

## 5:10-6:25 - célula 5: identificação e quebra

“O envelope cobre as 120 ordenações. Ele mede sensibilidade à identificação, e não incerteza estatística. A diferença pontual do Brent é positiva em todas as ordens, mas sua magnitude varia.”

“A FEVD divide a variância do erro de previsão entre os choques. O Chow avalia uma data conhecida; o CUSUM acompanha desvios ao longo da amostra.”

No gráfico móvel:

“Cada ponto usa 96 meses de dados para estimar um repasse até h=12. A linha tracejada, identificada na legenda, marca outubro de 2016. Ela indica o início do segundo regime, não o início de cada janela.”

## 6:25-7:30 - célula 6: história, simulação e previsão

“Na decomposição histórica, a base e os choques reconstroem a série. As barras somam o IPCA depois de retirar a base.”

“Nos dados artificiais, conheço a verdade: a ordenação correta recupera melhor a resposta. Isso verifica o método, mas não prova a ordenação brasileira.”

“Na previsão, cada treino usa somente dados disponíveis até a origem. O VAR ganha do AR em um mês na base, mas não em doze. O alvo de doze meses é a inflação daquele mês futuro, não a inflação acumulada durante o ano.”

## 7:30-9:30 - mudança ao vivo no próprio notebook

Na primeira célula, mude:

```python
P_FIXO=4,
BOOT=99,
PASTA_SAIDA="resultados_teste",
```

Use **Restart Kernel and Run All Cells** e volte à saída da célula 4, na mesma página. O índice de títulos do JupyterLab ajuda a navegar.

“Mais defasagens dão flexibilidade, mas gastam graus de liberdade. Com p=4, a diferença do petróleo continua positiva e a banda passa a incluir zero. A significância, portanto, depende dessa escolha.”

O ensaio de referência com 99 réplicas deu diferença aproximada de **0,198 p.p.**, banda **[−0,129; 0,444]**. Leia os resultados atuais se alterar outros parâmetros.

Para outra pergunta do professor, mude `EXCLUIR_2020`, `ORDEM`, `FIM` ou `DIFERENCIAR_SELIC`, sempre antecipando que hipótese está sendo alterada.

## 9:30-10:00 - fechamento

“Encontro uma resposta estimada maior ao petróleo após 2016 na base e em vários ensaios. A magnitude varia com a identificação, a significância varia com as defasagens e os resíduos deixam ressalvas. A conclusão é uma comparação condicional entre regimes, sem isolar o efeito causal da Petrobras.”

## Perguntas

Mantenha o notebook aberto. Os diagnósticos estão na célula 3, a diferença entre regimes na 4, a sensibilidade à ordem e a quebra na 5, e a previsão na 6. O [guia de estudo](GUIA_ESTUDO.md) detalha conceitos e respostas.

Depois do ensaio, restaure `P_FIXO=None`, `BOOT=399` e `PASTA_SAIDA="resultados"`. Reinicie e execute tudo antes de gerar novamente o PDF.
