# Dados locais

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
