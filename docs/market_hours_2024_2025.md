# Horários, leilões e limites da análise de overnight

Verificação documental: 20/09/2026. Objeto: WIN em 2024 e no período de teste de 02/01/2025 a 28/11/2025. Horários locais de São Paulo. Este documento é uma auditoria parcial das fontes históricas, **não um calendário completo de sessões**.

## Decisão para a entrega de 21/09

A análise principal usa a janela fixa **09:05-18:05**, com retornos calculados dentro de cada pregão e defasagens que podem atravessar a passagem de um pregão ao seguinte. As faixas `inicio`, `meio` e `fim` significam posição nessa janela, não fase de leilão.

Código: [construção e contexto das séries](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/trading_time_data.py) e [construção multiescala original](https://github.com/avilarenan/EAD6034/blob/main/src/ead6034/multiscale.py).

Os candles OHLCV fornecidos não identificam explicitamente a fase da negociação. Por isso, a análise não identifica observações individuais como negócio de leilão, não estima efeito causal de leilões e não presume que o primeiro/último preço observado é o preço oficial de abertura/fechamento.

## Evidência histórica confirmada

As datas abaixo são as informadas nos documentos. A ausência de uma data final verificada **não autoriza prolongar a grade até 2025**. As páginas são as posições físicas no PDF, contadas a partir de 1.

| Fonte B3 | Publicação e vigência informada | WIN não vincendo | Ajuste IND/WIN e contrato vincendo | Ações à vista |
|---|---|---|---|---|
| [059/2024-PRE, português](https://www.b3.com.br/data/files/CE/04/53/7F/6D8EE810C54843E8DC0D8AA8/OC%20059-2024%20PRE%20Novos%20horarios%20de%20negociacao_Estrategias%20-%20Fut%20Bitcoin%20%28PT%29.pdf), pp. 1, 3, 5 e 9 | Publicado em 16/04; grade de índices a partir de 17/04/2024 | Negociação 09:00-18:25; pré-abertura cinco minutos antes; call eletrônico a partir de 18:25 | Ajuste 17:00-17:15; vincendo encerra às 17:00 | Pré-abertura 09:45-10:00; negociação 10:00-16:55; call 16:55-17:00 |
| [004/2024-VNC, português](https://www.b3.com.br/data/files/B7/B1/AC/F5/3021F8100E866AE8AC094EA8/OC%20004-2024-VNC%20Novos%20hor%C3%A1rios%20de%20negocia%C3%A7%C3%A3o_Estrat%C3%A9gias%20%2B%20Fut%20Bitcoin%20-%20Revoga%C3%A7%C3%A3o_PT.pdf), pp. 1-2, 4 e 8 | Publicado em 24/04; substitui 059/2024 **a partir de 26/04/2024**; mantém grade de índices de 17/04 | Mesmos horários do WIN na linha anterior | Mesmos horários de ajuste e vencimento | Mesmos horários da linha anterior |
| [132/2024-PRE, inglês](https://www.b3.com.br/data/files/A4/74/E4/7B/A3D629106EEC8429AC094EA8/OC%20132-2024%20PRE%20%20Novos%20Horarios%20de%20negociacao%20%28EN%29.pdf), pp. 1 e 5 | Publicado em 08/10; alterações de índices e ações a partir de **04/11/2024**; substituído pelo 153/2024 | Negociação 09:00-18:25; pré-abertura cinco minutos antes; call a partir de 18:25 | Ajuste 18:00-18:15; vincendo encerra às 18:00 | A grade de ações também muda em 04/11, detalhada e confirmada no documento seguinte |
| [153/2024-PRE, português](https://www.b3.com.br/data/files/55/56/E6/49/EB0239106EEC8429AC094EA8/OC%20153-2024%20PRE%20%20Novos%20Horarios%20de%20Negociacao%20%28PT%29.pdf), pp. 1-3, 6 e 8 | Publicado em 12/11; confirma grades em vigor desde **04/11/2024** | Negociação 09:00-18:25; pré-abertura cinco minutos antes; call a partir de 18:25 | Ajuste 18:00-18:15; vincendo encerra às 18:00 | Pré-abertura 09:45-10:00; negociação 10:00-17:55; call 17:55-18:00 |

O documento 132/2024 vincula a alteração de novembro ao encerramento do horário de verão nos EUA. Não se deve confundir isso com uma mudança de fuso em São Paulo. O horário de ajuste também não é sinônimo de call de fechamento: são eventos distintos nas próprias tabelas da B3.

### Cuidados com as datas dos ofícios

- A indicação no 059/2024 de revogação pelo documento **datado** de 24/04 não antecipa para esse dia a substituição expressamente prevista para 26/04 pelo sucessor.
- O [001/2024-VNC, de 11/01/2024](https://www.b3.com.br/data/files/1F/C6/71/B8/AFE0D8103152D4C8AC094EA8/CL%20001-2024-VNC%20Novos%20Hor%C3%A1rios%20Exerc%C3%ADcio%20Op%C3%A7%C3%B5es%20Jan-24_EN.pdf), p. 1, anunciava alterações para 05/02 e indica revogação pelo 013/2024-PRE, de 23/01. Isoladamente, não comprova uma grade operacional de 11/01 a 22/01; não foi usado para classificar a amostra.
- O 004/2024-VNC aponta o 066/2024-PRE, de 07/05, como sucessor; o 132/2024 confirma que o substitui. Não foi recuperado o texto integral do 066 nesta auditoria, logo sua data efetiva não foi presumida a partir da publicação.

## Lacunas documentais preservadas

Não foi concluída a cadeia de grades, revogações, exceções e calendários para **todo 2024 e 2025**. Em particular, não foram confirmadas aqui as grades efetivas em todos os regimes de 2025. A [página atual de horários de índices](https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-participantes-e-traders/horario-de-negociacao/derivativos/indices/) e o [arquivo oficial de ofícios](https://www.b3.com.br/pt_br/regulacao/oficios-e-comunicados/) foram consultados, mas a página atual não foi aplicada retrospectivamente.

Consequências:

1. Não existe nesta entrega um classificador universal de leilões históricos.
2. As evidências de abril e novembro não são interpoladas para meses não verificados.
3. A falta de um calendário completo não impede a comparação pelas três faixas fixas da janela; limita as afirmações sobre fases de negociação e suas causas.
4. Seriam necessários os ofícios faltantes, as exceções de sessão e mensagens/flags de fase ou documentação equivalente do fornecedor para identificar com segurança os negócios de leilão em todos os dias.

## Relação da janela estudada com os eventos de mercado

Nos horários históricos confirmados para o WIN não vincendo, a janela principal inicia cinco minutos depois das 09:00 e termina vinte minutos antes do call das 18:25. Portanto, **não contém os leilões próprios de abertura/fechamento do WIN**, mesmo que retornos posteriores à abertura possam refletir informação acumulada durante a noite. Isso não impede que a janela contenha eventos de outro mercado.

| Faixa da análise | Interpretação permitida | O que não concluir |
|---|---|---|
| 09:05-10:05 (`inicio`) | Primeira hora da janela, que inclui o entorno das 10:00 nos regimes de ações documentados | Que todos os negócios sejam da abertura do WIN ou que o seu leilão ocorreu às 10:00 |
| 10:05-17:05 (`meio`) | Parte intermediária da janela; no regime de abril inclui o entorno do call das ações às 17:00 | Que seja uniformemente afastada de eventos de fechamento de todos os mercados |
| 17:05-18:05 (`fim`) | Última hora da janela; no regime de novembro inclui o call das ações às 18:00 | Que corresponda ao call próprio do WIN às 18:25 |

As linhas dessa tabela são interpretações da interseção entre as janelas do estudo e os horários documentados acima, não novas regras da B3. Sua diferença entre regimes reforça a necessidade de não atribuir causalmente um padrão de variância à simples etiqueta `inicio` ou `fim`.

## Gap auxiliar: definição e uso defensivo

O contexto diário pode medir `100 * log(primeiro_open_observado_d / ultimo_close_observado_d_anterior)` quando os dois preços pertencem ao mesmo contrato e não há uma lacuna de dias úteis suspeita. Esses preços são do feed, não preços oficiais certificados de leilão. Rolagens não devem gerar gaps artificiais.

O nome interpretativo é **gap entre sessões observadas**, não retorno overnight puro. Pode incluir movimentos de trechos não cobertos pelo feed, abertura, encerramento e interrupções mais longas. Os campos de auditoria guardam o primeiro/último horário observado, a duração da interrupção e a cobertura fora da janela principal. `auction_phase_observed=False` explicita a ausência de identificação de fase.

Os valores individuais de preços e retornos auxiliares permanecem privados; o repositório publica apenas resumos e regras reproduzíveis. Cortes para grupos de magnitude do gap são definidos em 2024. A avaliação por grupo em 2025 é uma decomposição **ex post** de erros já produzidos, não uma variável preditora retroativamente disponível na origem. Um gap calculado após a abertura não pode ser utilizado para uma previsão emitida antes dela.

## Formulação adequada para slides e conclusões

“Comparamos a previsão nas seis escalas e, no intradiário, em faixas fixas da janela 09:05-18:05. O retorno entre sessões foi excluído do alvo principal, embora as defasagens atravessem pregões. A sensibilidade ao gap observado e ao horário é exploratória. Os candles não identificam a fase de leilão, e a cronologia documental de horários é incompleta; por isso, os resultados não identificam causalmente efeitos de leilões nem demonstram ausência de efeitos overnight.”

## Mecanismos de leilão e hipóteses de microestrutura

O [Manual de Procedimentos Operacionais de Negociação da B3, edição de 17/02/2025](https://www.b3.com.br/data/files/55/65/B5/7D/AC31591029BEEC39AC094EA8/MPO%20de%20Negociacao%20da%20B3.pdf), pp. 36 e 55, descreve a formação de preço nas fases de abertura/fechamento e a maximização da quantidade negociada como primeiro critério do fixing. Isso não garante menor volatilidade: a incorporação de uma surpresa pode produzir uma variação expressiva. O mecanismo documentado não identifica seu efeito causal nesta amostra.

O mesmo manual, p. 45, relaciona spread, profundidade e volume à liquidez. A alternância de negócios nas ofertas de compra e venda pode gerar reversões nos preços negociados sem igual oscilação no ponto médio das ofertas (*bid–ask bounce*). Essa é uma hipótese interpretativa: os candles de negócios não contêm cotações nem permitem verificar o mecanismo. Agregar minutos em horas pode atenuar tal oscilação, mas também acumular choques ou ocultar sinais; maior previsibilidade horária exige evidência da comparação preditiva, não decorre do mecanismo por definição.

A edição do manual está identificada no [portal normativo da B3](https://www.b3.com.br/pt_br/regulacao/estrutura-normativa/operacoes/). Ela fundamenta essas descrições operacionais, sem completar a cronologia histórica dos horários de 2024–2025.
