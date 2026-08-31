# EAD6034 - Seminário de Econometria de Séries Temporais

Repositório do seminário **Previsibilidade linear em múltiplas escalas e classes de ativos**, desenvolvido para a disciplina EAD6034 da FEA-USP.

## Entrega de 31/08/2026

A primeira entrega implementa um piloto rigoroso da replicação linear proposta:

- série principal: retorno logarítmico percentual de 5 minutos do WIN;
- preço: último negócio (`close`) em barras regulares;
- identificação: ano-calendário de 2024;
- holdout: 2025, preservado para a etapa de avaliação preditiva;
- FAC/FACP: somente dentro da amostra e sem criar defasagens entre pregões;
- tratamento: sem retorno overnight, sem retorno de rolagem, sem winsorização e sem interpolação entre dias.

O relatório pronto para entrega está em [`results/entrega_31_08/ENTREGA_31_08.pdf`](results/entrega_31_08/ENTREGA_31_08.pdf). A versão textual, tabelas e figuras permanecem no mesmo diretório.

## Reprodução

Requer Python 3.11 ou superior. Os artefatos publicados foram gerados com Python 3.12.13; as versões efetivamente usadas também ficam registradas em `analysis_summary.json`.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python scripts/run_entrega_31_08.py \
  --input data/raw/BTG-ATS-A26.zip \
  --output results/entrega_31_08
PYTHONPATH=src python -m unittest discover -s tests -v
```

Para usar as mesmas versões das dependências diretas empregadas na geração dos artefatos, substitua `pip install -e .` por `pip install -r requirements-lock.txt` e `pip install -e . --no-deps`. O argumento `--input` também aceita o `WIN.parquet` ou o diretório extraído que o contém.

## Dados

O ZIP fornecido contém candles de **1 minuto**, apesar de a proposta inicial contemplar também segundos. A cobertura disponível sustenta 1 minuto e agregações (5, 15 e 30 minutos), mas não permite executar a escala de 1 segundo, comparar negócio com midquote ou testar ações/opções.

Os dados brutos não são publicados neste repositório. Consulte [`data/README.md`](data/README.md) para a estrutura esperada.

## Decisões metodológicas desta etapa

1. O WIN é o análogo mais direto ao índice usado no benchmark de Matías e Reboredo (2012).
2. O arquivo já fornece um encadeamento com um único contrato ativo por pregão. O código valida essa propriedade e nunca calcula retorno entre dias ou tickers.
3. Timestamps sem timezone são tratados como UTC e convertidos para `America/Sao_Paulo`, convenção consistente com a abertura observada às 09:00.
4. A janela `[09:05, 18:25)` exclui os cinco minutos iniciais e a pausa/leilão final. Cada barra representa `[t-5min, t)`, é rotulada à direita e usa o último negócio do intervalo.
5. Pregões com menos de 95% das 112 barras esperadas são excluídos por uma regra definida sem observar os retornos. No treino, isso elimina apenas 14/02/2024, uma sessão de horário reduzido no Carnaval.
6. A FAC usa apenas pares no mesmo pregão. A FACP de ordem `k` é o último coeficiente de uma regressão AR(k) pooled, também sem defasagens que atravessem sessões.
7. Cruzar isoladamente uma banda de 95% não define a ordem ARMA. A leitura considera magnitude, formato, múltiplos testes e, nas próximas etapas, BIC e diagnóstico residual.

## Estrutura

```text
src/ead6034/                 pipeline, dados, análise, gráficos e relatório
scripts/run_entrega_31_08.py ponto de entrada reproduzível
tests/                       testes das invariantes metodológicas
results/entrega_31_08/       PDF, figuras, tabelas públicas e metadados gerados
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
