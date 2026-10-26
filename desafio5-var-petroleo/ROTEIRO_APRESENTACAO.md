# Roteiro oral - cerca de dez minutos

## Preparação

Abra o PDF e o script. No terminal, use `python analise.py`. Ele ficará esperando Enter antes do primeiro bloco. Os gráficos aparecem quando o bloco roda; feche cada janela depois de comentar. `--lote` serve para regenerar arquivos sem interação.

Ensaiar com 399 réplicas já levou aproximadamente meio minuto de cálculo total, sem contar fala/pausas. `BOOT=99` permite um ensaio ainda mais curto. Na apresentação, avise se reduzir o número de réplicas.

## 0:00-2:00 - cinco slides

**Slide 1, 20 s.** “Minha pergunta é se um mesmo aumento do petróleo passa de maneira diferente aos preços brasileiros antes e depois de outubro de 2016.”

**Slide 2, 25 s.** “Separo o petróleo em dólares do câmbio. O IPA representa preços ao produtor e o IPCA, ao consumidor. A Selic representa a condição monetária. Uso séries mensais públicas, com a base salva para reprodução.”

**Slide 3, 30 s.** “Cada variável depende dos dois meses anteriores de todas as cinco. A ordem de Cholesky define quem pode reagir no mesmo mês. Comparo uma alta de 10% nos dois períodos e acumulo a resposta do IPCA até h=12, incluindo o impacto.”

**Slide 4, 30 s.** “O efeito do petróleo passa de cerca de 0,07 para 0,41 ponto percentual. A diferença é positiva na base. Mas os resíduos ainda são autocorrelacionados; a banda é exploratória. O sinal negativo do câmbio também exige cuidado.”

**Slide 5, 15 s.** “Essa comparação não isola a Petrobras. Vou mostrar os diagnósticos e as respostas, depois alterar uma hipótese para verificar a conclusão.”

## 2:00-3:15 - dados, modelo e diagnóstico

**Células 2 e 3.** Aperte Enter, mostre rapidamente as séries e os testes.

“Petróleo e câmbio entram como diferenças de log. IPCA e IPA já são taxas. A Selic fica em nível na base, mas os testes deixam uma dúvida sobre sua estacionariedade.”

“O BIC escolheu dois lags. As raízes estimadas estão dentro do círculo, indicando estabilidade dinâmica. Isso não resolve outro problema: o Portmanteau rejeita ausência de autocorrelação. Nenhum p da grade até seis passou. Por isso não vou tratar o modelo como definitivamente validado.”

Não leia cada p-valor. Localize `02_diagnostico`. Se perguntarem sobre um coeficiente, abra `02_coeficientes_completa.csv`.

## 3:15-4:45 - Granger e resultado central

**Célula 4, 20 s.** “Granger mede se o passado de uma variável ajuda a prever outra, condicionado às demais. Não é causalidade estrutural. Mostro a versão usual e uma covariância robusta.”

**Célula 5, cerca de 70 s, incluindo cálculo.** Enquanto o bootstrap roda:

“Eu reestimo o modelo em várias amostras simuladas para medir a incerteza. O choque tem a mesma magnitude inicial antes e depois, de modo que a comparação não seja apenas diferença de volatilidade.”

Mostre o gráfico `04_irf_antes_depois`.

“Esta linha é a resposta acumulada. O petróleo tem resposta maior no segundo período. Para testar a mudança, olho a banda da diferença, não apenas se duas bandas individuais se sobrepõem. No câmbio, o sinal pós-período é estranho e varia com a especificação.”

## 4:45-6:00 - identificação e quebra

**Célula 6, 40 s.** Mostre o envelope.

“Estas são todas as 120 ordens possíveis. A faixa mostra sensibilidade à identificação e não é um intervalo de confiança. A diferença pontual do petróleo é positiva em todas as ordens, mas sua magnitude varia bastante.”

“A FEVD reparte a variância do erro de previsão. Ela não mede a porcentagem da inflação observada causada pelo petróleo. A comparação com Sigma comum ajuda a distinguir dinâmica de mudança nos impactos.”

**Célula 7, 35 s.** Mostre CUSUM e janela móvel brevemente.

“Chow testa uma data conhecida; CUSUM procura deslocamentos ao longo da amostra. A curva móvel usa oito anos de observações para calcular um repasse de horizonte 12. Ela não estima um VAR com apenas doze meses.”

## 6:00-7:15 - decomposição, simulação e previsão

**Célula 8, 25 s.** “Reconstruo o IPCA com uma base determinística e as contribuições dos cinco choques. O código confere a soma. A linha aqui é o IPCA depois de retirar a base.”

**Célula 9, 20 s.** “Nestes dados artificiais, conheço a verdade. A ordem certa se aproxima mais da resposta verdadeira. Isso ilustra a importância da identificação, mas não prova a ordem do caso brasileiro.”

**Célula 10, 30 s.** “Agora a pergunta é previsão. Cada treino usa só dados até a origem. O VAR ganha do AR em um mês nesta amostra; em doze meses não. O AR é aninhado, então a comparação usa Clark–West. O DM é reservado ao ingênuo sazonal não aninhado.”

## 7:15-9:30 - alteração ao vivo

Mude no início:

```python
P_FIXO = 4
BOOT = 99
PASTA_SAIDA = "resultados_teste"
```

Salve e execute desde o começo. Para ganhar tempo, use `python analise.py --lote` e abra `resultados_teste/04_diferenca.csv` ou `04_irf_antes_depois.png` quando terminar.

“Antes de executar, espero mais flexibilidade e menos graus de liberdade. Com quatro lags, a diferença do petróleo continua positiva, mas a banda inclui zero. Isso mostra que a significância não é robusta à escolha da memória do modelo.”

O ensaio de referência com 99 réplicas produziu diferença de aproximadamente **0,198 p.p.**, banda **[−0,129; 0,444]**. Refaça a leitura a partir da nova saída; outro número de réplicas pode alterar os extremos.

Se o professor escolher outro parâmetro, use `EXCLUIR_2020`, `ORDEM`, `FIM` ou `DIFERENCIAR_SELIC` e explique previamente que hipótese foi modificada.

## 9:30-10:00 - fechamento

“Encontro uma resposta estimada maior do IPCA ao petróleo após 2016 em várias especificações. A magnitude depende da identificação e a significância depende das defasagens. Com autocorrelação residual e outros eventos entre os regimes, a conclusão é exploratória. O resultado principal é a comparação condicional e seus limites, não uma estimativa causal isolada da política da Petrobras.”

## Para os cinco minutos de perguntas

Tenha abertas estas saídas:

- `02_diagnostico.csv`: estabilidade e autocorrelação.
- `04_diferenca.csv`: comparação correta dos regimes.
- `05_mudanca_120_ordens.csv`: sensibilidade à identificação.
- `09_metricas.csv`: ganho preditivo por horizonte.
- `VALIDACAO.md`: alterações já executadas e conferências.

A versão detalhada das respostas está no [guia de estudo](GUIA_ESTUDO.md). Após o ensaio, restaure `P_FIXO=None`, `BOOT=399` e `PASTA_SAIDA="resultados"` antes de regenerar os resultados de referência.
