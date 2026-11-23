# Dados do exercício

Os dois arquivos são compartilhados entre R e Python. São dados sintéticos e dados públicos históricos; não contêm o feed privado de mercado usado em outros trabalhos deste repositório.

## `simulacao.csv`

300 observações geradas pelo script R com `set.seed(10)`, RNG padrão do R (`Mersenne-Twister`, normais por `Inversion`). Primeiro são sorteados os 300 incrementos de `x`; depois, os 299 choques do erro `z`, iniciado em zero. A ordem de sorteio é a do roteiro fornecido.

| Coluna | Definição |
|---|---|
| `t` | Índice de 1 a 300 |
| `x` | Passeio aleatório gaussiano |
| `z` | Erro AR(1), `rho=0,6`, iniciado em zero |
| `y` | `3*x + z` |
| `z_rho1` | Mesmos choques de `z`, com `rho=1` |
| `y_rho1` | `3*x + z_rho1`, usado no desafio D1 |

O script R regenera esse arquivo a cada execução. Python usa as observações exportadas, pois uma semente igual em NumPy e R não produz os mesmos sorteios. O CSV preserva 17 algarismos significativos para permitir a recuperação dos mesmos números de ponto flutuante.

## `juros.csv`

Snapshot de **`tseries::tcm`**, exportado de `tcm5y` e `tcm1y` em `tseries 0.10-63`. A igualdade numérica de ambas as colunas foi conferida diretamente contra os objetos nativos em R.

- **Período:** abril/1953 a setembro/1999, 558 observações mensais.
- **Fonte original informada pelo pacote:** Federal Reserve, Statistical Release H.15.
- **Unidade:** porcentagem ao ano; diferenças entre taxas são pontos percentuais.
- **`date`:** primeiro dia do mês como rótulo do período mensal; não é uma observação diária.
- **`media`:** taxa com maturidade de 5 anos (`tcm5y`).
- **`curta`:** taxa com maturidade de 1 ano (`tcm1y`).

[Documentação original do dataset](https://search.r-project.org/CRAN/refmans/tseries/html/tcm.html) · [Distribuição CRAN do pacote](https://CRAN.R-project.org/package=tseries).

O script usa o CSV versionado, sem consultar taxas recentes. Se o arquivo estiver ausente, `data("tcm", package="tseries")` reconstrói o snapshot; nesse caso é necessário instalar `tseries`. A execução confere nomes de colunas, número de observações e datas inicial/final.

Os hashes SHA256 dos dois arquivos estão em [`../resultados/manifesto.json`](../resultados/manifesto.json).
