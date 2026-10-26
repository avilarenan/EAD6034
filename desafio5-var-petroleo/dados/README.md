# Dados mensais congelados

Extração: **26/10/2026 (UTC)**. Período dos arquivos brutos: dezembro/2003 a setembro/2026. Cada série tem 274 observações. A análise começa em janeiro/2004, após as diferenças.

| Arquivo | Série | Unidade original | Produtor / distribuição |
|---|---|---|---|
| brent.csv | POILBREUSDM | US$/barril, média mensal, sem ajuste sazonal | FMI / FRED |
| cambio.json | SGS 3698 | R$/US$, dólar venda, média mensal | BCB |
| ipa.json | SGS 225 | IPA-DI, variação mensal (%) | FGV / BCB |
| ipca.json | SGS 433 | IPCA, variação mensal (%) | IBGE / BCB |
| selic.json | SGS 4189 | Selic acumulada no mês anualizada (% a.a.), base 252 | BCB |
| mensal.csv | Consolidação das cinco séries | Unidades originais acima | Gerado por analise.py |

O Brent é o preço global mensal do FMI distribuído pelo FRED, não uma série diária agregada no script. O câmbio já é média mensal na fonte. IPA-DI e IPCA já são taxas mensais: não se aplica diferença do log a essas taxas.

## URLs de obtenção

- Brent: https://fred.stlouisfed.org/graph/fredgraph.csv?id=POILBREUSDM&cosd=2003-12-01&coed=2026-09-30
- Metadados do Brent: https://fred.stlouisfed.org/series/POILBREUSDM
- Câmbio: https://api.bcb.gov.br/dados/serie/bcdata.sgs.3698/dados?formato=json&dataInicial=01/12/2003&dataFinal=30/09/2026
- IPA-DI: https://api.bcb.gov.br/dados/serie/bcdata.sgs.225/dados?formato=json&dataInicial=01/12/2003&dataFinal=30/09/2026
- IPCA: https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json&dataInicial=01/12/2003&dataFinal=30/09/2026
- Selic: https://api.bcb.gov.br/dados/serie/bcdata.sgs.4189/dados?formato=json&dataInicial=01/12/2003&dataFinal=30/09/2026
- Consulta de metadados SGS: https://www3.bcb.gov.br/sgspub/

Os JSONs mantêm o formato original da API (data dia/mês/ano e valor). O CSV consolidado usa datas ISO, ponto decimal e vírgula como separador. A execução verifica continuidade mensal, ausência de duplicatas/faltantes e positividade dos níveis usados em log.

A fotografia pode conter revisões históricas das fontes. Uma nova consulta futura pode alterar valores. Por isso o script não baixa novamente a base durante a apresentação. Os hashes dos arquivos originais e do código constam de `resultados/resumo.json` e `fontes.json`.

A execução publica estes dados agregados para reprodução acadêmica, com atribuição aos produtores. Não inclui dados de mercado licenciados usados nas tarefas anteriores, mensagens privadas nem cópias dos slides do professor.
