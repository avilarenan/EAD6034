# Exercício de cointegração — R e Python

[**Ler o notebook executado**](exercicio_cointegracao.ipynb) · [**Script R**](exercicio_cointegracao.R) · [**Abrir no Codespaces**](https://codespaces.new/avilarenan/EAD6034?quickstart=1) · [**Comparação numérica**](resultados/comparacao_r_python.csv)

## Qual é o problema?

Duas séries podem variar persistentemente e, mesmo assim, manter uma relação estável entre si. O exercício pergunta se essa relação existe e como as séries corrigem os desvios. Primeiro usamos uma simulação cuja resposta conhecemos; depois analisamos os juros americanos de **1 e 5 anos**, em **558 observações mensais de abril/1953 a setembro/1999**.

## Conclusão

Na simulação, a relação verdadeira é `y = 3x + erro`. Estimamos **3,0251** para o coeficiente de `x`, e o teste indica cointegração. A correção estimada é **−0,3780**, próxima da teórica **−0,4**: um excesso de 10 unidades gera uma contribuição de aproximadamente **−3,78 unidades** no período seguinte, mantendo os demais componentes separados.

Nos dados reais, os testes são compatíveis com taxas I(1), e Johansen seleciona **uma relação de longo prazo**:

**taxa de 5 anos ≈ 0,3571 + 1,0371 × taxa de 1 ano**

As taxas estão em % ao ano. Quando a taxa de 5 anos está acima dessa relação, o ajuste estatisticamente significativo ocorre pela **taxa de 1 ano, que tende a subir**, reduzindo o desvio. Não encontramos evidência clara de ajuste pela taxa de 5 anos. É um resultado para esta amostra e especificação, sem identificação de causalidade ou extrapolação para os juros atuais.

| Verificação | Resultado | Leitura a 5% |
|---|---:|---|
| Engle–Granger, simulação | −7,7469; crítico −3,34 | Evidência de cointegração |
| Johansen, hipótese `r = 0` | 35,0918; crítico 19,96 | Rejeita ausência de relação |
| Johansen, hipótese `r ≤ 1` | 5,4578; crítico 9,24 | Não rejeita; seleciona uma relação |
| Ajuste da taxa de 1 ano | α = 0,0633; t = 2,6708 | Significativo pelo critério da aula |
| Ajuste da taxa de 5 anos | α = 0,0037; t = 0,2131 | Sem evidência clara de ajuste |

No desafio, trocar `rho=0,6` por `rho=1` elimina a força de retorno; o teste deixa de indicar cointegração. O spread simples entre os juros rejeita raiz unitária, resultado compatível com a ligação entre as taxas. Isso não demonstra que o coeficiente de longo prazo seja exatamente 1.

## O que foi alterado?

- **Aula:** preenchidas as três lacunas do roteiro com `x`, `diff` e posto **1**, este último determinado pelo teste.
- **Implementação:** retirada a dependência não utilizada de `vars`; `urca` executa os testes. `tseries` fornece o dataset, salvo em CSV para reprodução local.
- **Implementação:** exportados os mesmos dados para R e Python. Uma semente numérica igual nas duas linguagens não produziria os mesmos sorteios.
- **Implementação:** reproduzidos a seleção AIC de 1 a 6 defasagens com amostra fixa, a constante restrita do Johansen e os erros padrão condicionais OLS do VECM. O módulo Python calcula os resultados independentemente.
- **Esclarecimento conceitual:** preservado o crítico de Engle–Granger **−3,34** do enunciado, em vez do crítico ADF comum. Não rejeitar raiz unitária em nível é evidência compatível com I(1), não uma prova.

## Validação

**52 de 52 métricas R/Python conferem**, com maior diferença absoluta de aproximadamente **4 × 10⁻¹²**. A tolerância adotada é `1e-8 + 1e-8 × |R|`. Os coeficientes também foram conferidos com `statsmodels.VECM(deterministic="ci")`.

O script foi executado em **R 4.5.3**, `urca` **1.3-4** e `tseries` **0.10-63**. Todas as células Python foram executadas em sequência, com saídas reais salvas no notebook; neste ambiente a execução usou o kernel IPython em processo local. A configuração do Codespaces foi preparada e conferida, mas uma instância remota do Codespaces não foi aberta durante esta validação.

O [manifesto](resultados/manifesto.json) registra versões, especificações e SHA256 dos dados, código e tabelas. O [console R](resultados/r_console.txt) contém as regressões completas. Os [coeficientes Python](resultados/coeficientes_python.csv) incluem erros padrão e estatísticas t. O notebook responde P1–P15 e aos dois desafios.

## Como abrir e reproduzir

**Somente leitura:** clique no notebook acima. As tabelas e os gráficos estão incorporados, sem widgets ou JavaScript.

**Codespaces:** clique em “Abrir no Codespaces”, aguarde a preparação do ambiente, selecione o kernel **Python 3 (EAD6034 — Cointegração)** e execute **Run All**. O container instala R e prepara um ambiente Python isolado. Em um Codespace já existente, atualize o repositório e use **Codespaces: Rebuild Container** para aplicar a configuração.

**Localmente**, a partir da raiz do repositório, com Python 3.12 e R instalados:

```bash
bash exercicio-cointegracao/scripts/setup_python.sh
Rscript exercicio-cointegracao/scripts/install_r.R
exercicio-cointegracao/.venv/bin/python exercicio-cointegracao/scripts/reproduzir.py
```

Para executar somente R:

```bash
Rscript exercicio-cointegracao/exercicio_cointegracao.R
```

Para recalcular Python usando a referência R já versionada:

```bash
exercicio-cointegracao/.venv/bin/python exercicio-cointegracao/scripts/reproduzir.py --so-python
```

`--rscript CAMINHO` permite indicar outro executável R. `--in-process` executa as células no kernel IPython local quando o ambiente impede a comunicação entre processos. O script falha se alguma célula ou comparação falhar.

## Fontes

- [Dados `tseries::tcm`, com origem Federal Reserve H.15](https://search.r-project.org/CRAN/refmans/tseries/html/tcm.html); [proveniência local](data/README.md).
- Código original das convenções: [`ur.df`](https://github.com/cran/urca/blob/master/R/ur-df.R), [`ca.jo`](https://github.com/cran/urca/blob/master/R/ca-jo.R) e [`cajorls`](https://github.com/cran/urca/blob/master/R/cajorls.R).
- [VECM e constante restrita no statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.tsa.vector_ar.vecm.VECM.html).
