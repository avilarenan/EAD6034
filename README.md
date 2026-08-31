# EAD6034 - Seminário de Econometria de Séries Temporais

Repositório do seminário **Previsibilidade linear em múltiplas escalas e classes de ativos**, desenvolvido para a disciplina EAD6034 da FEA-USP.

## Entrega de 31/08/2026

A versão principal da primeira entrega implementa a dimensão multiescala da proposta:

- série principal: retorno logarítmico percentual de 5 minutos do WIN;
- extensões: 1, 15, 30 e 60 minutos e retorno diário open-to-close;
- preço: último negócio (`close`) em barras regulares;
- identificação: ano-calendário de 2024;
- holdout: 2025, preservado para a etapa de avaliação preditiva;
- comparação: mesmos pregões e janela comum de 09:05 a 18:05 em todas as escalas;
- FAC/FACP: somente dentro da amostra e sem criar defasagens entre pregões, lacunas ou contratos;
- tratamento: sem retorno overnight, sem retorno de rolagem, sem winsorização e sem interpolação entre dias.

O relatório recomendado para entrega está em [`results/entrega_31_08_multiescala/ENTREGA_31_08_MULTIESCALA.pdf`](results/entrega_31_08_multiescala/ENTREGA_31_08_MULTIESCALA.pdf). O [piloto original de 5 minutos](results/entrega_31_08/ENTREGA_31_08.pdf) foi preservado para que a mudança de protocolo permaneça explícita e auditável.

## Reprodução

Requer Python 3.11 ou superior. Os artefatos publicados foram gerados com Python 3.12.13; as versões efetivamente usadas também ficam registradas em `analysis_summary_multiscale.json`.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python scripts/run_entrega_31_08_multiescala.py \
  --input data/raw/BTG-ATS-A26.zip \
  --output results/entrega_31_08_multiescala
PYTHONPATH=src python -m unittest discover -s tests -v
```

Para usar as mesmas versões das dependências diretas empregadas na geração dos artefatos, substitua `pip install -e .` por `pip install -r requirements-lock.txt` e `pip install -e . --no-deps`. O argumento `--input` também aceita o `WIN.parquet` ou o diretório extraído que o contém.

O comando legado `python scripts/run_entrega_31_08.py ...` continua reproduzindo o piloto original de 5 minutos.

## Dados

O ZIP fornecido contém candles de **1 minuto**, apesar de a proposta inicial contemplar também segundos. A cobertura disponível sustenta 1, 5, 15, 30 e 60 minutos e a agregação diária, mas não permite executar a escala de 1 segundo, comparar negócio com midquote ou testar ações/opções.

Os dados brutos não são publicados neste repositório. Consulte [`data/README.md`](data/README.md) para a estrutura esperada.

## Decisões metodológicas desta etapa

1. O WIN é o análogo mais direto ao índice usado no benchmark de Matías e Reboredo (2012).
2. O arquivo já fornece um encadeamento com um único contrato ativo por pregão. O código valida essa propriedade e nunca calcula retorno entre dias ou tickers.
3. Timestamps sem timezone são tratados como UTC e convertidos para `America/Sao_Paulo`, convenção consistente com a abertura observada às 09:00.
4. A comparação usa a janela `[09:05, 18:05)`, com 540 minutos, divisível por todas as frequências intradiárias. As barras são ancoradas em 09:05, rotuladas à direita e nunca possuem uma cauda parcial.
5. Nas escalas intradiárias, o preço de fronteira em 09:05 é o fechamento do candle iniciado às 09:04. Assim, o primeiro retorno de cada escala cobre integralmente o primeiro bloco do pregão.
6. A amostra principal multiescala exige cobertura minuto a minuto completa e usa os mesmos pregões em todas as frequências. O piloto anterior com cobertura de 95% permanece separado como sensibilidade.
7. O retorno diário principal usa o `open` da barra 09:05 e o último `close` da janela comum, conforme a definição open-to-close da proposta. A soma close-to-close intradiária é preservada para reconciliação; o close-to-close diário aparece apenas como robustez porque inclui overnight.
8. A FAC é a correlação pooled dos pares válidos no mesmo pregão. A FACP de ordem `k` é o último coeficiente de uma regressão AR(k) pooled, também sem defasagens que atravessem sessões. No diário, lacunas e mudanças de ticker criam novos segmentos.
9. Barras não sobrepostas dependem da origem 09:05; deslocamentos da grade ficam registrados como robustez futura.
10. Cruzar isoladamente uma banda de 95% não define a ordem ARMA. A leitura considera magnitude, formato, tamanhos amostrais diferentes e múltiplos testes.

## Estrutura

```text
src/ead6034/                             pipeline, dados, análise, gráficos e relatórios
scripts/run_entrega_31_08_multiescala.py ponto de entrada multiescala
scripts/run_entrega_31_08.py             ponto de entrada do piloto original
tests/                       testes das invariantes metodológicas
results/entrega_31_08_multiescala/       entrega recomendada, tabelas e figuras
results/entrega_31_08/                   piloto original de 5 minutos
data/raw/                    dados locais ignorados pelo Git
```

A tabela diária com níveis exatos de fechamento e volume é gerada localmente para construir as figuras, mas não é versionada no repositório público.

## Cronograma do trabalho

- **31/08:** análise visual, FAC e FACP;
- **14/09:** estacionariedade e metodologia Box-Jenkins;
- **21/09:** capacidade preditiva e comparação com modelo alternativo;
- **28/09:** seminário final, com duração máxima de 15 minutos.

## Referência principal

Matías, J. M.; Reboredo, J. C. (2012). Forecasting performance of nonlinear models for intraday stock returns. *Journal of Forecasting*, 31(2), 172-188. https://doi.org/10.1002/for.1218
