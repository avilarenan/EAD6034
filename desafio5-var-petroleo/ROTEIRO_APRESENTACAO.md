# Roteiro: 10 minutos, 5 de slides e 5 de notebook

## Antes de começar

- Abra os slides e `apresentacao.ipynb`. No notebook, rode **Restart Kernel and Run All Cells** uma vez antes da aula (cerca de um minuto).
- Na fala, rode só as células 1 a 4 com **Shift+Enter**. A célula 5 é o anexo: mostre só se pedirem.
- Deixe [GUIA_RAPIDO.md](GUIA_RAPIDO.md) aberto para perguntas e mudanças no código.

## 0:00–5:00 · Slides

| Tempo | Slide | Fala |
|---|---|---|
| 0:00–0:45 | 1. Pergunta | "Em outubro de 2016, a Petrobras passou a seguir a paridade de importação. A pergunta é se choques no petróleo e no câmbio passaram a chegar mais rápido e mais forte ao IPCA." |
| 0:45–1:45 | 2. Experimento | "Estimo um VAR antes e outro depois. Nos dois, aplico a mesma alta de 10% no Brent e meço quanto o IPCA acumulado sobe em doze meses, contra o caminho sem a surpresa. O Brent vem primeiro na ordem: o Brasil não move o preço internacional dentro do mês." |
| 1:45–2:45 | 3. Resultado | "Antes de 2016, a alta quase não aparece no IPCA: 0,07 ponto. Depois, 0,41. A diferença é 0,34, e a banda de 90% da diferença não inclui zero. O câmbio não passa mais; a resposta cai e é instável." |
| 2:45–4:00 | 4. Mecanismo e robustez | "Troco uma peça de cada vez: as defasagens quase não mudam nada; a correlação dos resíduos no mesmo mês muda quase tudo. Em treze variantes, o sinal é sempre positivo, de 0,20 a 0,38; a significância depende das defasagens e dos meses finais." |
| 4:00–5:00 | 5. Respostas | "Um: o repasse do Brent aumentou; o do câmbio, não. Dois: o Chow do sistema testa 55 restrições, o que dilui o poder; o teste de uma restrição no mesmo mês dá p de 0,0001. Três: a mudança está na correlação do mesmo mês, compatível com a política, mas o VAR não a separa de choques comuns. Agora, o código." |

## 5:00–10:00 · Notebook

| Tempo | Célula | O que mostrar e dizer |
|---|---|---|
| 5:00–5:30 | 1. Painel | "Todas as escolhas estão aqui: defasagens, quebra, amostra, ordem, tamanho do choque. Qualquer mudança é uma linha." |
| 5:30–6:30 | 2. Dados e modelo | Aponte o BIC com p=2 e o raio menor que 1. "O Portmanteau rejeita, mas a coluna LB_p mostra que só a equação da Selic tem autocorrelação: é o calendário do Copom numa média mensal." |
| 6:30–7:45 | 3. Experimento | Painel esquerdo do gráfico e tabela `04_diferenca`. "Mesmo choque, dois regimes: 0,07 antes, 0,41 depois, diferença 0,34 com banda de +0,10 a +0,58. O painel do câmbio é outro experimento e não é estrutural." |
| 7:45–9:30 | 4. Identificação e variantes | As tabelas de identificação e o teste de uma restrição aparecem na hora; comente enquanto as variantes rodam, cerca de 45 s. "Trocar só a covariância do mesmo mês muda a resposta em 0,26 a 0,38; trocar só as defasagens, quase nada." No gráfico: "positiva em todas; banda inclui zero com p=4 e sem os meses finais." |
| 9:30–10:00 | Conclusão | "Resultado: maior repasse após 2016, concentrado no mesmo mês, sem atribuir a causa à Petrobras. O anexo tem os demais itens do desafio. Posso mudar qualquer parâmetro agora." |

## Se o tempo apertar

Corte a fala da célula 2 para uma frase. Não rode a célula 4: role até a saída já salva da execução feita antes da aula. Rodar de novo apaga essa saída até terminar.

## Depois: mudanças pedidas pelo professor

Use a tabela "Mudanças que o professor pode pedir" do [guia rápido](GUIA_RAPIDO.md). Para respostas rápidas, ponha `BOOT=99` junto com a mudança e use **Restart Kernel and Run All Cells**. Leia os números novos na tela, não os do texto.
