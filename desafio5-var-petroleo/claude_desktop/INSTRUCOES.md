# Instruções: apresentação de 5 slides em 5 minutos

## Tarefa

Crie um arquivo **.pptx 16:9 com exatamente 5 slides**, em português do Brasil. Ele abre uma apresentação de aula de **10 minutos**: 5 minutos de slides e, depois, 5 minutos de notebook ao vivo.

- Disciplina: EAD6034, Econometria de Séries Temporais, FEA-USP. Professor: Rafael Palazzi.
- Autor: Renan de Luca Avila.
- Público: professor e colegas de pós-graduação. Conhecem VAR, mas não este trabalho.

O enunciado pede respostas a três perguntas. O slide 5 responde às três, uma por linha:

1. O repasse do Brent ao IPCA aumentou depois de 2016? E o do câmbio?
2. O teste de Chow num VAR com 5 variáveis testa quantas restrições? Isso afeta o poder?
3. A mudança nas respostas vem da política de preços ou de uma mudança na correlação dos resíduos?

Arquivos deste pacote:

- `figuras/irf_brent.png`: figura do slide 3.
- `figuras/variantes.png`: figura do slide 4.

## Regras

1. **Simples e direto.** O título de cada slide é uma frase-conclusão. No máximo três blocos curtos de texto por slide, exceto as três respostas do slide 5. Sem parágrafos.
2. **Use só os números deste arquivo**, com vírgula decimal e os sinais indicados. Não recalcule nem arredonde de outro jeito.
3. Use as duas figuras sem recortar, distorcer ou redesenhar.
4. Escreva **notas do orador** em cada slide, com o texto de fala abaixo, cerca de um minuto por slide.
5. Visual: fundo branco, fonte sem serifa, títulos em `#12384a`, "antes" em `#166a8f`, "depois" em `#d78222`, texto de apoio em `#56616b`. Sem ícones decorativos, gradientes ou imagens de banco.
6. Rodapé discreto em todos os slides, exceto o primeiro: "EAD6034 · Renan de Luca Avila · n/5".
7. Confira antes de entregar: 5 slides, números iguais aos da tabela final, nenhum texto cortado ou sobreposto.

## O que não escrever

- Que a política da Petrobras **causou** a mudança. O desenho compara regimes; não isola a causa.
- "Choque de oferta de petróleo". O choque do Brent mistura oferta e demanda mundial.
- Que desvalorizar o real reduz a inflação. O sinal negativo do câmbio é instável e não é estrutural.
- "%" no lugar de "p.p." para mudanças de inflação.
- "Intervalo de confiança de 95%". As bandas são **bootstrap de 90%**.

## Slides

### Slide 1 · Pergunta

- **Título:** Choques no Brent e no câmbio chegam mais rápido e mais forte ao IPCA depois de 2016?
- **Subtítulo:** VAR com Brent, câmbio, IPA, IPCA e Selic · dados mensais de 01/2004 a 09/2026
- **Linha de contexto:** Em outubro de 2016, a Petrobras passou a seguir a paridade de importação nos combustíveis.
- Nome, disciplina e professor.
- **Fala:** "Em outubro de 2016, a Petrobras passou a seguir a paridade de importação. Minha pergunta é se, depois disso, choques no petróleo e no câmbio passaram a chegar mais rápido e mais forte ao IPCA."

### Slide 2 · Experimento

- **Título:** O experimento: a mesma surpresa de +10%, em dois períodos
- **Coluna esquerda, cinco variáveis:** Brent (US$, variação do log) · câmbio R$/US$ (variação do log) · IPA (% ao mês) · IPCA (% ao mês) · Selic (% ao ano), com sazonais.
- **Coluna direita, três passos curtos:**
  1. Dois VARs(2): 01/2004–09/2016 e 10/2016–09/2026.
  2. No mês 0, o Brent sobe 10% de surpresa. Em outro experimento, o câmbio. As demais surpresas ficam em zero.
  3. Comparo o IPCA com e sem a surpresa e somo do mês 0 ao mês 12.
- **Nota no rodapé do slide:** Ordem no mesmo mês: Brent → câmbio → IPA → IPCA → Selic. Com o câmbio antes do Brent, a diferença é +0,28.
- **Fala:** "Estimo um VAR antes e outro depois. Nos dois, aplico a mesma alta de 10% e meço quanto o IPCA acumulado sobe em doze meses, contra o caminho sem a surpresa. O Brent vem primeiro porque o Brasil não move o preço internacional no mês. O real reage ao petróleo, por isso o câmbio vem depois; se eu inverter, o resultado se mantém."

### Slide 3 · Resultado

- **Título:** O Brent passa muito mais ao IPCA depois de 2016; o câmbio, não
- **Três números grandes, lado a lado, para o Brent:**
  - Antes: **+0,07 p.p.**
  - Depois: **+0,41 p.p.**
  - Diferença: **+0,34 p.p.**, com a legenda "banda de 90%: +0,10 a +0,58"
- **Figura:** `figuras/irf_brent.png`, abaixo dos números.
- **Linha abaixo da figura:** Câmbio +10%: +0,25 antes e −0,49 depois. Não há aumento; o sinal negativo é instável entre variantes.
- **Rodapé do slide:** IPCA acumulado do mês 0 ao 12; bandas bootstrap de 90%.
- **Fala:** "Antes de 2016, a alta de 10% no Brent quase não aparece no IPCA: sete centésimos de ponto. Depois, são quatro décimos. A diferença é de 0,34 ponto, e a banda da diferença não inclui zero. Para o câmbio, não há aumento: a resposta estimada cai e muda muito entre especificações, então não a trato como efeito estrutural."

### Slide 4 · Mecanismo e robustez

- **Título:** A mudança está no próprio mês, e o sinal resiste a 13 variantes
- **Coluna esquerda, três fatos:**
  - Trocar só as defasagens entre períodos muda a resposta em **−0,04 a +0,08 p.p.**
  - Trocar só a correlação dos resíduos muda em **+0,26 a +0,38 p.p.**
  - No próprio mês, o efeito vai de **−0,005 a +0,145 p.p.** Teste com uma restrição: p = 0,0001.
- **Coluna direita:** `figuras/variantes.png`.
- **Legenda da figura:** Positiva nas 13 variantes de especificação e amostra (+0,20 a +0,38). A banda exclui zero em 10 e inclui zero com p=4 e sem os meses finais (fim em 12/2025 ou 12/2021).
- **Fala:** "Para separar política e correlação dos resíduos, troco uma peça de cada vez entre os períodos. Trocar as defasagens quase não muda nada; trocar a correlação dos resíduos muda quase tudo. Ou seja, a mudança está no próprio mês. Testei treze variantes: sem pulsos, sem 2020, sem a Selic, com o Brent exógeno, com mais defasagens e amostras menores. O sinal é sempre positivo; a significância depende das defasagens e dos meses finais."

### Slide 5 · Respostas

- **Título:** Respostas às três perguntas
- **Três linhas numeradas:**
  1. **Repasse:** o do Brent aumentou, mais rápido e mais forte (+0,34 p.p.); o do câmbio, não.
  2. **Chow:** 55 restrições no sistema, 11 por equação. O poder se dilui e o teste não olha a correlação dos resíduos. O teste focalizado, com uma restrição, rejeita com p = 0,0001.
  3. **Política ou correlação:** a mudança vem da correlação no próprio mês, não das defasagens. Reajustes mais frequentes aparecem assim em dados mensais, mas o VAR recursivo não separa política de choques comuns. Proibindo o repasse no mês, a diferença cai para +0,10.
- **Linha final, em destaque:** Agora, o notebook ao vivo.
- **Fala:** "Respondendo às três perguntas: o repasse do Brent aumentou, o do câmbio não. O Chow do sistema testa 55 restrições ao mesmo tempo, o que dilui o poder; um teste focalizado no mesmo mês é muito mais claro. E a mudança está na correlação dos resíduos no próprio mês: é compatível com a política, mas o VAR não a separa de choques comuns. Agora mostro isso no código, e posso mudar qualquer hipótese."

## Números de referência

| Medida | Valor |
|---|---|
| Amostra | 01/2004 a 09/2026, 273 meses; quebra em 10/2016 |
| Defasagens escolhidas pelo BIC | p = 2 |
| Brent +10%, IPCA acumulado meses 0–12: antes | +0,07 p.p. (banda de 90%: −0,08 a +0,21) |
| Brent +10%: depois | +0,41 p.p. (banda de 90%: +0,22 a +0,59) |
| Brent: diferença depois − antes | +0,34 p.p. (banda de 90%: +0,10 a +0,58) |
| Câmbio +10%: antes e depois | +0,25 e −0,49 p.p.; diferença −0,74, que varia de −0,06 a −0,94 entre variantes |
| Brent, efeito no próprio mês | antes −0,005 p.p.; depois +0,145 p.p.; teste com 1 restrição: p = 0,0001 |
| Correlação das surpresas Brent–IPCA no mesmo mês | antes −0,02; depois +0,42 |
| Trocar só as defasagens / só a correlação dos resíduos | −0,04 a +0,08 / +0,26 a +0,38 p.p. |
| Chow do sistema | 55 restrições (11 por equação); LR = 91,8; p = 0,001 |
| Variantes de especificação e amostra | 13; diferença positiva em todas, de +0,20 a +0,38 p.p.; banda exclui zero em 10 |
| Variantes com banda incluindo zero | p = 4 (+0,20); fim em 12/2025 (+0,29); fim em 12/2021 (+0,22) |
| Câmbio antes do Brent | +0,28 p.p. (banda +0,06 a +0,51) |
| IPCA antes do Brent (sem repasse no mês) | +0,10 p.p. (banda −0,12 a +0,33) |
