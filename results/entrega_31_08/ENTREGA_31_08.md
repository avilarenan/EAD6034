# Entrega de 31/08 - análise visual, FAC e FACP

## Recorte

- Série: retorno logarítmico percentual de 5 minutos do WIN.
- Identificação: 2024-01-02 a 2024-12-30 (249 pregões; 27639 retornos).
- Holdout: 2025, iniciado em 2025-01-02, sem uso na FAC/FACP.
- Sessão: 09:05-18:25, horário de São Paulo; primeiro bloco de 5 minutos e período final de leilão/pausa excluídos.
- Rolagem: encadeamento do contrato ativo fornecido; nenhum retorno atravessa dia ou ticker.

## Auditoria

O arquivo WIN possui 1284115 linhas, 60 contratos, 0 duplicatas de chave, 0 valores ausentes e 0 violações OHLC. No treino, 1 sessão de horário reduzido (2024-02-14) ficou abaixo de 95% e foi excluída por regra definida antes de observar retornos.

## Leitura dos resultados

Na amostra de 2024, a média do retorno é -0.000350% por barra e o desvio-padrão é 0.070680%. A proporção de retornos exatamente zero é 3.00%. A distribuição apresenta assimetria 0.59 e excesso de curtose 23.67; os extremos foram mantidos.

A FAC e a FACP da média têm magnitudes pequenas e não mostram truncamento ou decaimento simples. O maior valor absoluto da FAC entre 1 e 30 lags é 0.0112. Na separação temporal de 60 minutos (lag 12), FAC=-0.0008 e FACP=-0.0012; isso não representa um retorno acumulado de 60 minutos. Picos isolados não devem ser transformados diretamente em uma ordem ARMA, especialmente sob múltiplos testes e com amostra intradiária grande.

Em contraste, a FAC de retornos absolutos no primeiro lag é 0.218. O padrão é compatível com clustering de volatilidade, mas também contém a sazonalidade intradiária observada e não deve ser confundido com previsibilidade linear da média.

## Limites desta etapa

Esta entrega não conclui estacionariedade, não seleciona um ARMA final e não avalia previsão fora da amostra. ADF/PP/KPSS, Box-Jenkins, diagnóstico residual e comparação preditiva pertencem às entregas de 14/09 e 21/09.
