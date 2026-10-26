# Desafio 5 - Petróleo e inflação no Brasil

**EAD6034 · Rafael Palazzi · Renan de Luca Avila**

Pergunta: **o repasse do petróleo ao IPCA mudou depois de outubro de 2016?**

Resposta curta: **sim, na direção.** Depois de outubro de 2016, o IPCA responde mais ao Brent.

- **Magnitude:** +0,34 p.p. na base. Em 13 variantes de especificação e amostra, a diferença fica entre +0,20 e +0,38 p.p., sempre positiva.
- **Incerteza:** a banda de 90% exclui zero em 10 dessas 13 variantes. Inclui zero com p=4 e com a amostra encerrada em 12/2025 ou 12/2021.
- **Mecanismo:** a mudança está no próprio mês do choque. A correlação entre as surpresas do Brent e do IPCA passa de −0,02 para +0,42, compatível com reajustes mais frequentes dos combustíveis. Por isso o resultado depende de ordenar o Brent antes do IPCA.
- **Resíduos:** a autocorrelação residual vem quase toda da equação da Selic. Sem a Selic, a diferença é +0,38 p.p.
- **Câmbio:** não há aumento. A resposta estimada cai de +0,25 para −0,49 p.p., mas varia de −0,06 a −0,94 entre variantes; não é efeito estrutural.
- **Limite:** a comparação antes/depois não identifica, isoladamente, o efeito causal da política da Petrobras.

## As três perguntas do enunciado

1. **O repasse aumentou?** O do Brent, sim: mais forte (+0,07 → +0,41 p.p.) e mais rápido, com um terço do efeito já no mês do choque. O do câmbio, não.
2. **Quantas restrições testa o Chow?** No sistema, 55: constante e 10 coeficientes defasados em cada uma das 5 equações, com p=2. Com p=4 seriam 105. Tantas restrições diluem o poder contra uma mudança concentrada, e o Chow da forma reduzida não olha a correlação dos resíduos. O LR rejeita (p=0,001), mas não diz onde. O teste focalizado na relação do mesmo mês, com uma restrição, rejeita com p=0,0001. O OLS-CUSUM, padrão de `vars::stability()`, não rejeita em nenhuma equação.
3. **Política ou correlação dos resíduos?** Trocando uma peça de cada vez entre os regimes: só as defasagens mudam a resposta em −0,04 a +0,08 p.p.; só a covariância dos resíduos, em +0,26 a +0,38. A mudança está no mesmo mês. Reajustes mais frequentes aparecem exatamente assim em dados mensais, mas o VAR recursivo não separa política de choques comuns. Proibindo o repasse no mês, com o IPCA antes do Brent, a diferença cai para +0,10.

## Comece por aqui

- [Guia rápido: fala, números, perguntas e mudanças no código](GUIA_RAPIDO.md)
- [Roteiro de dez minutos: 5 de slides e 5 de notebook](ROTEIRO_APRESENTACAO.md)
- [Notebook da apresentação](apresentacao.ipynb): quatro células para apresentar e uma de anexo
- [Slides da apresentação](EAD6034_Brent_cambio_IPCA.pdf), montados com o [pacote para o Claude Desktop](claude_desktop/INSTRUCOES.md)
- [Introdução em PDF anterior](introducao.pdf), substituída pelos slides acima
- [Rotinas técnicas e alternativa em terminal](analise.py), importadas pelo notebook
- [Guia de estudo detalhado](GUIA_ESTUDO.md)
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

O notebook contém **cinco células de código, com 33 linhas ao todo**: quatro para apresentar e um anexo com os demais itens do desafio. Execute com **Shift+Enter**. Gráficos e tabelas aparecem na própria página, sem janelas externas ou abertura manual de CSVs. A cópia publicada também traz as saídas executadas para consulta.

A primeira célula concentra o dicionário `PARAMETROS`. Os controles principais têm comentários; uma tabela recolhível antes da célula documenta todos os demais parâmetros herdados. Para mudar qualquer controle avançado, acrescente-o à chamada `PARAMETROS.update(...)`.

Depois de alterar um parâmetro, use **Restart Kernel and Run All Cells**. O notebook recalcula tudo, sem cache de modelos. Na configuração-base, a execução completa levou cerca de 60 segundos no teste. As células 1 a 3 rodam em segundos; a célula 4, com 15 variantes e 399 réplicas cada, em cerca de 45 segundos; o anexo, em cerca de 11. Com `BOOT=99`, tudo roda em menos de meio minuto. Após instalar as bibliotecas, funciona sem internet.

Nas células de apresentação, itens secundários (resíduos por regime, raízes, ciclos e razões) são gravados em `resultados/` e exibidos no anexo. `EXIBIR_TUDO=True` os mostra também nas células 2 e 3.

As rotinas de estimação estão em `analise.py` para que a apresentação não exija percorrer centenas de linhas técnicas. Importar esse arquivo não dispara a análise. O caminho em terminal continua disponível:

```powershell
.\.venv\Scripts\python.exe analise.py --lote
.\.venv\Scripts\python.exe gerar_pdf.py
```

O gerador de PDF usa `resultados/resumo.json`. Execute a última célula do notebook antes de regenerar os slides. Os slides 3 e 4 apresentam **somente o experimento com petróleo**; o experimento cambial aparece separadamente na célula 3 do notebook.

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

O Ljung–Box por equação localiza a rejeição: só a equação da **Selic** falha, nas três amostras (p<0,001). Brent, câmbio, IPA e IPCA ficam acima de 0,18 ([02_residuos_completa.csv](resultados/02_residuos_completa.csv)). O padrão é compatível com o calendário do Copom, com reuniões a cada seis semanas, numa taxa média mensal; mais defasagens não o eliminam. Sem a Selic (`INCLUIR_SELIC=False`), a diferença do Brent é +0,38 [+0,19; +0,57]. O teste conjunto das outras quatro equações ainda rejeita, mais fracamente: a ressalva diminui, mas não desaparece.

A mesma ordem é usada antes/depois para facilitar a comparação. Outubro/2016 é o primeiro mês do segundo período. A estimação pós-quebra perde os primeiros p meses para formar suas próprias condições iniciais.

Identificação contemporânea-base: **Brent, câmbio, IPA, IPCA, Selic**. Esta ordem é uma hipótese econômica. O código também calcula todas as **120 permutações**, uma ordem alternativa na FEVD e a diferença entre regimes em todas as ordens.

## Resultados de referência

Resposta acumulada do IPCA de **h=0 até h=12, inclusive**, após uma alta exata de 10% na variável que recebe o choque. A soma das taxas simples é uma aproximação em pontos percentuais de inflação acumulada.

| Choque | Antes | Depois | Diferença depois − antes | Banda bootstrap de 90% da diferença |
|---|---:|---:|---:|---:|
| Brent +10% | +0,074 | +0,412 | +0,338 | [+0,100; +0,576] |
| Câmbio +10% | +0,250 | −0,494 | −0,744 | [−1,333; −0,139] |

Fontes: [respostas](resultados/04_respostas_12m.csv) e [diferença](resultados/04_diferenca.csv). As bandas são pontuais, condicionais ao modelo e à ordem, com wild bootstrap recursivo. O bootstrap trata heterocedasticidade, mas não conserta a autocorrelação residual observada. A comparação das diferenças supõe independência aproximada entre os dois regimes.

**Onde está a mudança.** No próprio mês do choque, o IPCA responde −0,005 p.p. antes e +0,145 p.p. depois: cerca de um terço da resposta posterior. A correlação entre as surpresas do Brent e do IPCA no mesmo mês passa de −0,02 para +0,42 ([04_respostas_12m.csv](resultados/04_respostas_12m.csv)). Em [05_impacto_vs_propagacao.csv](resultados/05_impacto_vs_propagacao.csv), trocar entre regimes apenas a covariância das surpresas desloca a resposta em +0,26 a +0,38 p.p.; trocar apenas as defasagens, em −0,04 a +0,08. A mudança é de repasse no mesmo mês, compatível com reajustes mais frequentes dos combustíveis após 2016. A decomposição é descritiva e não única.

**Por que isso depende da ordem.** Nas 120 ordens, a diferença do Brent é sempre positiva, de 0,034 a 0,338 p.p., e **a ordem-base fica no topo**: toda ordem com o Brent em primeiro dá 0,338. Com o IPCA antes do Brent, o petróleo não pode afetar o IPCA no mesmo mês e a diferença cai para 0,03–0,10 p.p. ([05_mudanca_120_ordens.csv](resultados/05_mudanca_120_ordens.csv)). Ordenar o Brent primeiro é a hipótese usual para uma economia pequena: o Brasil não move o preço internacional dentro do mês. Esse envelope não é uma banda de confiança.

**Mesmo choque, trajetórias diferentes do petróleo.** Depois do impacto, o próprio Brent segue a dinâmica de cada regime. No mês 12, ele está 14,1 acima da trajetória sem choque no modelo anterior e 10,1 no posterior, em 100×log. A razão entre as acumuladas corrige essa diferença e também sobe: 0,005 antes e 0,041 depois ([04_razao_antes.csv](resultados/04_razao_antes.csv), [04_razao_depois.csv](resultados/04_razao_depois.csv)).

**Variantes.** A célula 4 repete o experimento mudando uma escolha por vez ([tabela](resultados/10_variantes.csv), [gráfico](resultados/10_variantes.png)). Todas usam 399 réplicas e as sementes da célula 3.

| Grupo | Variante | p | Diferença do Brent | Banda de 90% |
|---|---|---:|---:|---:|
| Referência | Base | 2 | +0,338 | [+0,100; +0,576] |
| Defasagens | p = 1 | 1 | +0,302 | [+0,111; +0,434] |
| Defasagens | p = 4 | 4 | +0,198 | [−0,081; +0,489] |
| Selic | Selic em diferença | 1 | +0,346 | [+0,119; +0,554] |
| Selic | Sem a Selic (4 variáveis) | 1 | +0,381 | [+0,194; +0,574] |
| Episódios | Sem pulsos de 2018 e 2020 | 2 | +0,353 | [+0,120; +0,558] |
| Episódios | Excluir 2020 | 2 | +0,321 | [+0,028; +0,524] |
| Episódios | Pulsos no corte do ICMS, 07–08/2022 | 2 | +0,382 | [+0,134; +0,636] |
| Episódios | Pulsos no tarifaço, 01–03/2015 | 2 | +0,273 | [+0,045; +0,491] |
| Amostra | Fim em 04/2023, antes da nova estratégia | 2 | +0,342 | [+0,021; +0,622] |
| Amostra | Fim em 12/2025, sem a alta de 2026 | 2 | +0,294 | [−0,003; +0,524] |
| Amostra | Fim em 12/2021, sem 2022 em diante | 2 | +0,220 | [−0,057; +0,493] |
| Identificação | Câmbio antes do Brent | 2 | +0,281 | [+0,055; +0,505] |
| Identificação | IPCA primeiro, sem repasse no mês | 2 | +0,100 | [−0,123; +0,333] |
| Restrição | Brent exógeno ao Brasil | 2 | +0,333 | [+0,061; +0,552] |

Nas 13 variantes de especificação e amostra, a diferença é positiva em todas e a banda exclui zero em 10. Os pulsos quase não mudam o resultado: +0,35 sem eles. A significância depende das defasagens e dos meses finais: sem 2026, ano de alta do petróleo, o limite inferior vai a −0,003. As duas linhas de identificação mudam a pergunta, não a amostra: com o IPCA primeiro, o repasse no mesmo mês é proibido por hipótese.

O sinal negativo do câmbio após 2016 **não autoriza concluir que desvalorizar a moeda reduz estruturalmente os preços**. A diferença cambial é negativa em todas as variantes, mas vai de −0,06 a −0,94 p.p. e a banda inclui zero em 7 das 13 especificações. A correlação entre as surpresas do câmbio e do IPCA no mesmo mês passa de +0,09 para −0,28, e as defasagens também mudam. Isso sugere composição de choques ou identificação insuficiente, não o efeito isolado de uma depreciação.

Na previsão do IPCA **do mês-alvo**, o RMSE é 0,334 p.p. para VAR e 0,347 para AR em h=1. Em h=12, é 0,393 para VAR e 0,388 para AR. O ganho de curto prazo não se estende automaticamente a um ano. A avaliação é pseudo fora da amostra, com dados da versão atual e sem reconstruir datas históricas de divulgação.

## Alterações para demonstrar ao vivo

A célula 4 já mostra 15 variantes sem reiniciar o kernel. Para uma pergunta nova, mude **uma escolha por vez** em `PARAMETROS`, na primeira célula do notebook, e reinicie o kernel executando todas as células. A célula 4 então parte do novo painel. O [guia rápido](GUIA_RAPIDO.md) lista também mudanças que exigem editar `analise.py`.

| Parâmetro | Experimento | Pergunta que responde |
|---|---|---|
| `P_FIXO` | `4` | A conclusão resiste a uma memória dinâmica maior? |
| `INCLUIR_SELIC` | `False` | A equação com autocorrelação residual muda o resultado? |
| `MESES_ATIPICOS` | Acrescentar `"2022-07", "2022-08"` | O corte do ICMS de 2022 explica a resposta posterior? |
| `RESTRICOES` | `{"brent": ["cambio", "ipa", "ipca", "selic"]}` | Impor que o Brent não reage ao Brasil muda o resultado? |
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
| Defasagens, autocorrelação conjunta e por equação, normalidade e ARCH | Célula 2; resíduos por regime no anexo; `02_*` |
| Estabilidade, meia-vida e períodos dos modos complexos | Célula 2 (raio e meia-vida); anexo (`02_raizes.png`, `02_ciclos.csv`) |
| IRFs bootstrap e comparação pré/pós | Célula 3; `04_*` |
| Diferença entre regimes nas 120 ordens; mesmo mês versus defasagens | Célula 4; `05_mudanca_120_ordens.csv`, `05_impacto_vs_propagacao.csv` |
| Variantes de defasagens, Selic, episódios, amostra e identificação | Célula 4; `10_*` |
| Granger condicional por pares e bloco, usual e robusto | Anexo; `03_granger.csv` |
| Envelope de 120 ordens, correlação residual, FEVD | Anexo; `05_envelope.png`, `05_correlacao_residuos.csv`, `05_fevd_ipca.csv` |
| Chow na data conhecida, CUSUM recursivo, OLS-CUSUM como em `vars::stability()` e repasse móvel | Anexo; `06_*` |
| Teste focalizado da mudança no mesmo mês, com uma restrição | Célula 4; `05_teste_mesmo_mes.csv` |
| Decomposição histórica e reconstrução exata | Anexo; `07_*` |
| Simulação com ordem verdadeira e errada | Anexo; `08_*` |
| Previsão expansiva h=1 e h=12, AR/RW, DM e CW | Anexo; `09_*` |
| Síntese, versões e hashes dos insumos | Anexo; `resumo.json` |

Há uma referência ingênua sazonal adicional, que repete os últimos 12 meses e não exige estimação. Ela fornece uma comparação DM não aninhada com VAR(p<12). AR usa o mesmo p e as mesmas determinísticas do VAR, tornando o aninhamento explícito; para ele, a inferência usa **Clark–West**, não DM. RW é referência descritiva.

## Convenções e limites

- **Aula/desafio:** VAR, Cholesky, IRFs, FEVD, decomposição, Granger, estabilidade, simulação, previsão e testes pedidos.
- **Implementação:** BIC até p=6, pulsos, wild bootstrap de sinais, HAC/Bartlett, janela móvel de 96 meses e passo trimestral. Estes são parâmetros editáveis, não exigências atribuídas ao professor.
- **Implementação adicional declarada:** Granger com aumento de Toda–Yamamoto (`D_MAX=1`), para admitir variáveis I(1), e benchmark sazonal para DM. Não são apresentados como conteúdo comprovadamente ensinado nos slides.
- **Esclarecimento conceitual:** choque fixo de 10% versus choque de um desvio-padrão; razão de acumuladas versus resposta a choque normalizado; envelope de ordens versus intervalo de confiança.
- A Selic em nível tem evidência de não estacionariedade, e sua equação concentra a autocorrelação residual. A estabilidade estimada do VAR não resolve essas dúvidas. As IRFs usuais em nível e a inferência de quebra permanecem condicionais/exploratórias; as versões com diferença e sem Selic são sensibilidades.
- O pós-2016 inclui greve, pandemia, mudanças tributárias e a estratégia comercial anunciada em maio/2023. A quebra não é um experimento controlado.
- Os pulsos-base cobrem a greve de 2018 e o início da pandemia. Episódios comparáveis, como o tarifaço de 2015 e o corte do ICMS em 2022, entram como variantes. A escolha dos meses é retrospectiva.
- A janela móvel não mostra uma quebra nítida em 2016: a razão do Brent fica negativa nas janelas que terminam entre o fim de 2016 e meados de 2020, que ainda contêm 2015–2016, e só passa de 0,03 quando a janela termina no fim de 2022.
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
