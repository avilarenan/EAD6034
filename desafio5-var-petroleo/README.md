# Desafio 5 - Petróleo e inflação no Brasil

**EAD6034 · Rafael Palazzi · Renan de Luca Avila**

Pergunta: **o repasse do petróleo ao IPCA mudou depois de outubro de 2016?**

A análise sugere maior resposta ao Brent na especificação-base. A magnitude e a incerteza dependem das defasagens e da identificação. Há autocorrelação residual, portanto as bandas e os testes são exploratórios. A comparação antes/depois não identifica, isoladamente, o efeito causal da política da Petrobras.

## Comece por aqui

- [Introdução em PDF: cinco slides](introducao.pdf)
- [Notebook da apresentação](apresentacao.ipynb): seis células de código, com textos, tabelas e gráficos integrados
- [Rotinas técnicas e alternativa em terminal](analise.py), importadas pelo notebook
- [Guia de estudo e perguntas para a apresentação](GUIA_ESTUDO.md)
- [Roteiro oral de dez minutos](ROTEIRO_APRESENTACAO.md)
- [Gerador dos slides em Python](gerar_pdf.py)
- [Fontes e descrição dos dados](dados/README.md)
- [Resultados de referência](resultados/)
- [Conferências e sensibilidades executadas](VALIDACAO.md)

Esta pasta é independente das atividades univariadas anteriores do repositório. Tem suas próprias dependências e dados. Não é necessário executar os outros projetos.

## Execução no Jupyter

Use **Python 3.12**. Dentro de `desafio5-var-petroleo`, no Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m jupyterlab apresentacao.ipynb
```

Se o ambiente já estiver preparado, basta o último comando. No macOS/Linux, crie o ambiente com `python3.12 -m venv .venv` e use `.venv/bin/python` nos comandos seguintes.

O notebook contém **seis células de código, com 34 linhas ao todo**, além dos textos explicativos. Execute com **Shift+Enter**. Gráficos e tabelas aparecem na própria página, sem janelas externas ou abertura manual de CSVs. A cópia publicada também traz as saídas executadas para consulta.

A primeira célula concentra o dicionário `PARAMETROS`. Os controles principais têm comentários; uma tabela recolhível antes da célula documenta todos os demais parâmetros herdados. Para mudar qualquer controle avançado, acrescente-o à chamada `PARAMETROS.update(...)`.

Depois de alterar um parâmetro, use **Restart Kernel and Run All Cells**. O notebook recalcula tudo, sem cache de modelos. Na configuração-base, o cálculo leva cerca de meio minuto nesta máquina (44 segundos no teste completo, incluindo o kernel). Após instalar as bibliotecas, funciona sem internet.

As rotinas de estimação estão em `analise.py` para que a apresentação não exija percorrer centenas de linhas técnicas. Importar esse arquivo não dispara a análise. O caminho em terminal continua disponível:

```powershell
.\.venv\Scripts\python.exe analise.py --lote
.\.venv\Scripts\python.exe gerar_pdf.py
```

O gerador de PDF usa `resultados/resumo.json`. Execute a última célula do notebook antes de regenerar os slides. Os slides 3 e 4 apresentam **somente o experimento com petróleo**; o experimento cambial aparece separadamente na célula 4 do notebook.

## Dados e modelo

| Variável | Fonte | Entrada no VAR | Por que entra |
|---|---|---|---|
| Brent | FMI, distribuído pelo FRED: POILBREUSDM | 100 × diferença do log do preço em US$/barril | Custo internacional do petróleo |
| Câmbio | BCB/SGS 3698 | 100 × diferença do log de R$/US$ | Conversão do custo externo em reais |
| IPA-DI | FGV, distribuído pelo BCB/SGS 225 | Variação mensal em % | Preços ao produtor |
| IPCA | IBGE, distribuído pelo BCB/SGS 433 | Variação mensal em % | Preços ao consumidor |
| Selic | BCB/SGS 4189 | Taxa acumulada no mês, anualizada, em nível (% a.a.) | Condição monetária |

Amostra transformada: **janeiro/2004 a setembro/2026, 273 meses**. Dezembro/2003 serve apenas para construir a primeira diferença. Não há interpolação, ajuste sazonal prévio nem mistura de frequências.

VAR por MQO, constante, 11 indicadores mensais e pulsos em maio/junho de 2018 e março/junho de 2020 (quatro meses consecutivos na pandemia). A grade vai de 1 a 6 defasagens. O BIC escolhe **p=2**. A rotina procura uma ordem maior que passe o Portmanteau; nenhuma da grade passa na amostra completa, e o script mantém o BIC **com aviso explícito**. Não se trata de um modelo plenamente validado.

A mesma ordem é usada antes/depois para facilitar a comparação. Outubro/2016 é o primeiro mês do segundo período. A estimação pós-quebra perde os primeiros p meses para formar suas próprias condições iniciais.

Identificação contemporânea-base: **Brent, câmbio, IPA, IPCA, Selic**. Esta ordem é uma hipótese econômica. O código também calcula todas as **120 permutações**, uma ordem alternativa na FEVD e a diferença entre regimes em todas as ordens.

## Resultados de referência

Resposta acumulada do IPCA de **h=0 até h=12, inclusive**, após uma alta exata de 10% na variável que recebe o choque. A soma das taxas simples é uma aproximação em pontos percentuais de inflação acumulada.

| Choque | Antes | Depois | Diferença depois − antes | Banda bootstrap de 90% da diferença |
|---|---:|---:|---:|---:|
| Brent +10% | +0,074 | +0,412 | +0,338 | [+0,100; +0,576] |
| Câmbio +10% | +0,250 | −0,494 | −0,744 | [−1,333; −0,139] |

Fontes: [respostas](resultados/04_respostas_12m.csv) e [diferença](resultados/04_diferenca.csv). As bandas são pontuais, condicionais ao modelo e à ordem, com wild bootstrap recursivo. O bootstrap trata heterocedasticidade, mas não conserta a autocorrelação residual observada. A comparação das diferenças supõe independência aproximada entre os dois regimes.

O sinal negativo do câmbio após 2016 **não autoriza concluir que desvalorizar a moeda reduz estruturalmente os preços**. Ele é sensível à especificação: ao diferenciar a Selic, por exemplo, a banda da diferença inclui zero.

Em todas as 120 ordens, a diferença pontual para o Brent é positiva, mas varia de aproximadamente **0,034 a 0,338 p.p.** Esse envelope não é uma banda de confiança. Com `P_FIXO = 4`, a banda bootstrap da diferença inclui zero no ensaio de sensibilidade. Logo, a força da evidência depende da dinâmica escolhida.

Na previsão do IPCA **do mês-alvo**, o RMSE é 0,334 p.p. para VAR e 0,347 para AR em h=1. Em h=12, é 0,393 para VAR e 0,388 para AR. O ganho de curto prazo não se estende automaticamente a um ano. A avaliação é pseudo fora da amostra, com dados da versão atual e sem reconstruir datas históricas de divulgação.

## Alterações para demonstrar ao vivo

Mude **uma escolha por vez** em `PARAMETROS`, na primeira célula do notebook, e reinicie o kernel executando todas as células:

| Parâmetro | Experimento | Pergunta que responde |
|---|---|---|
| `P_FIXO` | `4` | A conclusão resiste a uma memória dinâmica maior? |
| `EXCLUIR_2020` | `True` | O ano da pandemia determina o resultado? |
| `ORDEM` | Trocar Brent e câmbio | Como distribuímos as surpresas que ocorrem no mesmo mês? |
| `FIM` | `"2023-04-01"` | O resultado depende de incluir a política posterior de 2023? |
| `DIFERENCIAR_SELIC` | `True` | A escolha de manter a taxa em nível importa? |
| `QUEBRA` | `"2018-01-01"` | A conclusão depende da data de separação? |
| `BOOT` | `99` para ensaiar, `999` para refinar | Quanto erro Monte Carlo aceitamos? |

`PASTA_SAIDA = "resultados_teste"` evita substituir a fotografia de referência. Ao trocar parâmetros, as tabelas são a nova evidência; a narrativa escrita precisa ser revista. O gerador de PDF lê a pasta definida em seu parâmetro `RESULTADOS`.

## Cobertura do desafio

| Exigência | Célula do notebook / saída |
|---|---|
| Dados, transformações, ADF e KPSS | Célula 2; arquivos `01_*` |
| Defasagens, autocorrelação, normalidade e ARCH | Célula 3; `02_*` |
| Estabilidade, meia-vida e períodos dos modos complexos | Célula 3; `02_raizes.png`, `02_ciclos.csv` |
| Granger condicional por pares e bloco, usual e robusto | Célula 3; `03_granger.csv` |
| IRFs bootstrap e comparação pré/pós | Célula 4; `04_*` |
| Envelope de 120 ordens, correlação residual, FEVD | Célula 5; `05_*` |
| Dinâmica versus covariância dos choques | Célula 5; `05_propagacao_covariancia_comum.csv` |
| Chow na data conhecida, CUSUM e repasse móvel | Célula 5; `06_*` |
| Decomposição histórica e reconstrução exata | Célula 6; `07_*` |
| Simulação com ordem verdadeira e errada | Célula 6; `08_*` |
| Previsão expansiva h=1 e h=12, AR/RW, DM e CW | Célula 6; `09_*` |
| Síntese, versões e hashes dos insumos | Célula 6; `resumo.json` |

Há uma referência ingênua sazonal adicional, que repete os últimos 12 meses e não exige estimação. Ela fornece uma comparação DM não aninhada com VAR(p<12). AR usa o mesmo p e as mesmas determinísticas do VAR, tornando o aninhamento explícito; para ele, a inferência usa **Clark–West**, não DM. RW é referência descritiva.

## Convenções e limites

- **Aula/desafio:** VAR, Cholesky, IRFs, FEVD, decomposição, Granger, estabilidade, simulação, previsão e testes pedidos.
- **Implementação:** BIC até p=6, pulsos, wild bootstrap de sinais, HAC/Bartlett, janela móvel de 96 meses e passo trimestral. Estes são parâmetros editáveis, não exigências atribuídas ao professor.
- **Implementação adicional declarada:** Granger com aumento de Toda–Yamamoto (`D_MAX=1`), para admitir variáveis I(1), e benchmark sazonal para DM. Não são apresentados como conteúdo comprovadamente ensinado nos slides.
- **Esclarecimento conceitual:** choque fixo de 10% versus choque de um desvio-padrão; razão de acumuladas versus resposta a choque normalizado; envelope de ordens versus intervalo de confiança.
- A Selic em nível tem evidência de não estacionariedade. A estabilidade estimada do VAR não resolve essa dúvida. As IRFs usuais em nível e a inferência de quebra permanecem condicionais/exploratórias; a versão com diferença é uma sensibilidade.
- O pós-2016 inclui greve, pandemia, mudanças tributárias e a estratégia comercial anunciada em maio/2023. A quebra não é um experimento controlado.
- O CUSUM auxiliar omite pulsos para manter posto completo na estimação inicial. Ele pode sinalizar episódios extremos, além de mudança persistente.
- A janela móvel estima o repasse em h=12 usando **96 meses de dados**, e não um VAR estimado com apenas 12 observações.
- Dados públicos deste desafio são versionados por solicitação do autor. As regras de dados privados do seminário anterior não são aplicadas a estas cinco séries agregadas.

O enunciado atual e a orientação de simplicidade regem esta entrega. A bateria extensa de modelos/testes e a divisão fixa do seminário univariado anterior não são transplantadas: aqui o exercício pede janela expansiva e ADF/KPSS.

## Referências

- [Enunciado: Desafio em Sala - Seis VARs para a Economia Brasileira](https://edisciplinas.usp.br/mod/resource/view.php?id=6618550).
- [Exercício VAR de Palazzi](https://edisciplinas.usp.br/mod/resource/view.php?id=6614778) e [slides da aula](https://edisciplinas.usp.br/mod/resource/view.php?id=6615251).
- [Documentação oficial do VAR no statsmodels](https://www.statsmodels.org/stable/vector_ar.html).
- [Toda e Yamamoto (1995)](https://doi.org/10.1016/0304-4076(94)01616-8).
- [Clark e West: versão dos autores no Federal Reserve de Kansas City](https://www.kansascityfed.org/documents/5368/pdf-RWP05-05.pdf).
- [Apresentação da Petrobras à Câmara: política de 2016](https://www2.camara.leg.br/atividade-legislativa/comissoes/comissoes-permanentes/cdc/apresentacoes-em-eventos/realizadas-em-2017/preco-dos-combustiveis/apresentacao-petrobras/view).
- [Petrobras: estratégia comercial anunciada em maio/2023](https://agencia.petrobras.com.br/pt/w/petrobras-aprova-estrategia-comercial-de-diesel-e-gasolina).
