# Entrega de 31/08 - análise visual multiescala, FAC e FACP

## Pergunta desta etapa

Como a dependência linear amostral do retorno do WIN muda quando o mesmo processo é observado em diferentes escalas?

O retorno de 5 minutos permanece como série principal e replicação adaptada do benchmark de Matías e Reboredo (2012). As escalas de 1, 15, 30 e 60 minutos e o diário são extensões descritivas que começam a executar o eixo escala da proposta.

## Protocolo comum

- Identificação: 2024-01-02 a 2024-12-30; 2025 permanece reservado para avaliação fora da amostra.
- Janela intradiária: `[09:05,18:05)`, com 540 minutos, ancorada exatamente em 09:05.
- Escalas: 1, 5, 15, 30 e 60 minutos; retorno diário open-to-close da mesma janela.
- Amostra comum: 246 pregões completos; excluídos 2024-02-06, 2024-02-14, 2024-03-08, 2024-06-07.
- Preço inicial intradiário: fechamento do candle iniciado às 09:04, imediatamente anterior à fronteira de 09:05.
- Preço inicial diário: `open` da primeira barra às 09:05, conforme a definição open-to-close da proposta.
- Retornos: logarítmicos percentuais, sem overnight, sem rolagem, sem winsorização e sem barras parciais.
- FAC intradiária: correlação pooled dos pares válidos no mesmo pregão; FACP: último coeficiente da AR(k) pooled. No diário, a lacuna integral de 2024-04-16, dias excluídos e trocas de contrato quebram a sequência.

## Comparação

| Escala | N | Desvio-padrão | Zeros | FAC lag 1 | FAC a 60 min | FAC do retorno absoluto lag 1 |
|---|---:|---:|---:|---:|---:|---:|
| 1 minuto | 132.840 | 0.0321% | 6.73% | -0.0082 | 0.0037 | 0.242 |
| 5 minutos | 26.568 | 0.0714% | 2.93% | 0.0024 | -0.0020 | 0.216 |
| 15 minutos | 8.856 | 0.1216% | 1.59% | 0.0071 | -0.0264 | 0.199 |
| 30 minutos | 4.428 | 0.1711% | 1.24% | 0.0095 | -0.0244 | 0.176 |
| 60 minutos | 2.214 | 0.2446% | 0.86% | -0.0453 | -0.0453 | 0.164 |
| 1 dia | 246 | 0.7850% | 0.00% | -0.0256 | - | 0.032 |

Na origem fixa de 09:05 e na separação física comum de 60 minutos, a FAC da média varia entre -0.0453 e 0.0037, com mudança de sinal entre escalas. Não aparece uma redução monotônica nem um padrão simples de truncamento ou decaimento. Em contraste, a FAC de retornos absolutos nessa mesma separação permanece positiva, entre 0.109 e 0.164.

Os zeros diminuem monotonicamente; o excesso de curtose se atenua nas escalas mais grossas, embora não de forma perfeitamente monotônica. A dispersão cresce aproximadamente com a raiz do tempo. Essas regularidades descrevem a distribuição; não demonstram capacidade preditiva.

## Limites

- Escala da barra, lag e horizonte futuro de previsão são conceitos distintos.
- Bandas pontuais de 95% não corrigem múltiplos testes, heteroscedasticidade ou dependência comum dentro do pregão.
- A escala de 1 minuto pode refletir bid-ask bounce, discretização e último negócio; o arquivo não possui midquotes para separar esses mecanismos.
- A FAC de |r| mistura clustering de volatilidade e sazonalidade intradiária.
- Barras não sobrepostas dependem da origem 09:05; deslocamentos da grade são uma robustez futura.
- O diário possui amostra pequena e usa lags em pregões, não em minutos.
- Esta etapa não conclui estacionariedade, não escolhe ordem ARMA e não avalia previsão OOS.

O relatório original de 5 minutos em `results/entrega_31_08/` foi preservado como piloto. A versão multiescala usa um protocolo comum mais estrito e não mistura silenciosamente os dois recortes.
