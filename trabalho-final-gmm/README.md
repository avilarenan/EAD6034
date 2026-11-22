# Replicação de Hansen (1982): checkpoint de 19 de novembro

**Renan de Luca Avila · EAD6034 – Econometria de Séries Temporais · FEA-USP.**

[PDF do checkpoint](resultados/checkpoint_19_11.pdf) · [Tabela lado a lado](resultados/tabela_I.csv) · [Dados e fontes](dados/README.md) · [Estimador em Python](estimate.py) · [Especificações alternativas](resultados/sensibilidade.csv)

O que se consegue reproduzir da aplicação clássica do GMM sem acesso ao CRSP? Com o arquivo histórico disponibilizado por A. Ronald Gallant, as quatro estatísticas J do bloco de consumo de não duráveis mais serviços e retorno da NYSE coincidem com os valores publicados, às três casas decimais. Com dados públicos reconstruídos para não duráveis, as estatísticas são maiores nas quatro especificações. Nesse segundo bloco também não há rejeição a 5%, mas há uma diferença de decisão a 10% com duas defasagens: p = 0,068 na reconstrução contra 0,121 no artigo.

## O que foi entregue

[Hansen (1982)](https://doi.org/10.2307/1912775) é o artigo designado: estabelece propriedades do estimador GMM e do teste das restrições sobreidentificadoras. Como não contém tabela empírica, seguimos a proposta enviada em outubro: reproduzir a aplicação de [Hansen e Singleton (1982)](https://doi.org/10.2307/1911873). Os números de referência vêm da [errata de 1984, p. 268, Tabela I](https://doi.org/10.2307/1911486); os autores corrigiram as séries de consumo. A aceitação deste desenho como **replicação estrita** continua sujeita à confirmação do professor.

O checkpoint contém os dados mensais e **oito linhas da Tabela I**: os dois blocos de retorno ponderado pelo valor de mercado (VWR), com 1, 2, 4 e 6 defasagens. O primeiro bloco usa um arquivo histórico publicado; o outro usa uma aproximação pública. A Tabela I completa inclui também retornos igualmente ponderados. A Tabela III usa múltiplos retornos simultâneos: não faz parte dos resultados entregues aqui. Não foi necessário usar WRDS, Capital IQ nem Economática.

## Leitura da tabela

A condição de Euler é que o erro de apreçamento, `β × (crescimento bruto do consumo real per capita)^α × (retorno bruto real) − 1`, seja ortogonal aos instrumentos conhecidos antes do retorno. β é o fator de desconto **mensal** e −α mede aversão relativa ao risco no modelo CRRA. Para cada ativo e medida de consumo, a constante e L defasagens de cada uma das duas variáveis produzem 1+2L momentos para dois parâmetros. Há 239 observações transformadas de fevereiro/1959 a dezembro/1978; sobram 238, 237, 235 e 233 observações após formar os instrumentos.

O CSV traz coeficientes, erros-padrão, J, graus de liberdade, p-valores, datas e diferenças. A coluna *Prob* da publicação é a probabilidade **acumulada**. Para julgar rejeição usamos a **cauda superior**. Todos os p-valores da reconstrução principal excedem 5%. Isso não prova que o modelo é verdadeiro: no painel histórico a estimativa de α muda de sinal ao passar de uma para duas defasagens e os erros-padrão são grandes. A precisão da replicação numérica e a precisão com que se identifica a aversão ao risco são questões diferentes.

O estimador foi escrito para este trabalho. A configuração principal usa GMM iterado com covariância dos momentos centrada; a conferência do bloco histórico orientou essa escolha. Também reportamos GMM em duas etapas, matrizes não centradas e amostra comum. O texto dos autores descreve duas etapas e admite centrar os momentos; a coincidência numérica não demonstra qual rotina histórica foi executada. Consulte [Método e sensibilidade](metodo_gmm.md).

## Reproduzir com um comando

Ambiente de referência: Python 3.12. Após instalar as dependências, a execução não precisa de rede, senha nem arquivos externos. Os dois CSVs já contêm as séries transformadas. A partir desta pasta:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python executar.py
```

O script verifica a integridade dos dados, as datas, o posto das matrizes e a proximidade dos resultados com a errata; regenera o PDF, as tabelas comparativas, a análise de sensibilidade e o [manifesto](resultados/manifesto.json) com hashes e versões. A estimação é determinística e não usa sorteios.

**Para a entrega final:** completar os painéis factíveis da Tabela I/III, realizar a simulação de Monte Carlo prevista na proposta e aplicar o modelo a dados brasileiros. A extensão brasileira requer compatibilizar a frequência do consumo do IBGE com a dos retornos; seus resultados ainda não foram estimados.
