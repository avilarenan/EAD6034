# Origem e limites dos dados — BTG-ATS-A26

**Fonte:** BTG Alpha Lab / BTG Solutions Data Services. *BTG-ATS-A26 — Aggregate Trade Statistics Dataset*, construído a partir de negócios da B3. Documentação consultada em **20/09/2026**.

- [Página oficial do dataset no Alpha Lab](https://alphalab.btgpactual.com/datasets/publication:7a74b3ae-90e0-4393-b1e0-01e61c0bedba).
- [README oficial do BTG-ATS-A26](https://dataservices.btgpactualsolutions.com/alphalab/v1/api/alphalab/readme/README-BTG-ATS-A26.md).
- [Portal Alpha Lab](https://alphalab.btgpactual.com).
- [Condições de acesso e uso](https://alphalab.btgpactual.com/terms-and-policies#terms-of-use).

## Base publicada e recorte efetivamente utilizado

A documentação descreve candles de negócios com duração de um minuto, campos OHLC e de atividade, com timestamp do **início do intervalo em UTC**. A cobertura geral é de 04/01/2016 a 28/11/2025, para WIN, WDO e DI1. Esses dados não fornecem cotações bid/ask ou midquotes para o presente estudo.

O seminário utiliza somente **WIN**, com treino em 2024 e avaliação no trecho disponível de 2025. Converte-se o horário para São Paulo e selecionam-se pregões completos na janela 09:05–18:05. Isso resulta em 246 pregões de treino e 221 de teste, conforme a [auditoria amostral](../results/entrega_21_09/tables/sequence_audit.csv). A referência é **BTG-ATS-A26**, não o dataset BTG-TLD-A26 de negócios individuais.

O arquivo efetivamente recebido do autor foi `BTG-ATS-A26(2).zip`, do qual o código leu `BTG-ATS-A26/WIN.parquet`. O [manifesto da execução](../results/entrega_21_09/analysis_summary.json) registra o SHA-256 do **ZIP recebido**:

```text
dc9a661df39efa85de1032d71cc2a8cca1a4a8626ac8698bb974a829337a4e23
```

Esse hash identifica a entrada local analisada. Não certifica igualdade byte a byte com um eventual novo download: a revisão consultou a documentação oficial, sem substituir ou baixar novamente a base. [Código da carga e do hash](../src/ead6034/data.py) · [construção das séries anuais](../src/ead6034/trading_time_data.py).

## Seleção retrospectiva do contrato

Segundo o README do fornecedor, o vencimento de WIN/WDO incluído é o de maior volume negociado **no próprio dia**. A informação completa só fica disponível após a sessão. Consequentemente, a série disponibilizada possui uma seleção de contrato **ex post**.

As previsões usam apenas observações anteriores à origem e parâmetros estimados em 2024. Essa propriedade do cálculo não torna a composição da base uma regra de negociação executável antecipadamente. Junto ao filtro retrospectivo de dias completos, a escolha do contrato limita a interpretação operacional: o exercício avalia previsões na série fornecida, e não uma estratégia integralmente validada em tempo real.

O tratamento evita retornos entre vencimentos: cada retorno compara preços de um mesmo contrato e pregão. Porém, os estados dos modelos continuam na sequência de barras, inclusive nas mudanças de sessão e contrato. Isso não elimina possíveis diferenças de liquidez ou efeitos de rolagem. [Código multiescala](../src/ead6034/multiscale.py) · [protocolo temporal](PROTOCOL_21_09.md).

## Acesso e reprodução

O portal disponibiliza acesso mediante cadastro e aceite de termos. Os termos consultados preveem uso acadêmico, científico e de pesquisa e restringem redistribuição, comercialização e sublicenciamento sem consentimento escrito. O repositório publica código e resumos, sem republicar o ZIP ou observações individuais. Para obter a base, deve-se utilizar o canal oficial e observar os termos aplicáveis.

Os indicadores de cobertura divulgados pelo fornecedor caracterizam a base geral e não substituem os filtros e a auditoria do recorte de 2024–2025. Lacunas, sessões reduzidas e a ausência de identificação de fases de leilão continuam relevantes. [Horários e microestrutura](market_hours_2024_2025.md) · [instruções locais dos dados](../data/README.md).
