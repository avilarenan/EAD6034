# Dados locais

Fonte oficial: **[BTG Alpha Lab — BTG-ATS-A26](https://alphalab.btgpactual.com/datasets/publication:7a74b3ae-90e0-4393-b1e0-01e61c0bedba)**, candles de negócios da B3. Consulte o [README do fornecedor](https://dataservices.btgpactualsolutions.com/alphalab/v1/api/alphalab/readme/README-BTG-ATS-A26.md) e a [documentação de proveniência e limitações](../docs/DATA_SOURCE.md), incluindo a escolha retrospectiva do contrato de maior volume diário. O acesso deve ser realizado pelo canal oficial, sujeito aos termos do Alpha Lab.

Coloque aqui uma das estruturas abaixo:

```text
data/raw/BTG-ATS-A26.zip
```

ou

```text
data/raw/BTG-ATS-A26/WIN.parquet
data/raw/BTG-ATS-A26/WDO.parquet
data/raw/BTG-ATS-A26/DI1.parquet
```

O pipeline desta entrega lê apenas `WIN.parquet`. Arquivos `.zip` e `.parquet` estão ignorados pelo Git para que o repositório público contenha código e resultados, não a base bruta.
