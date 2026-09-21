# EAD6034 - Seminário de Econometria de Séries Temporais

Repositório do seminário **Previsibilidade linear em múltiplas escalas e classes de ativos**, desenvolvido para a disciplina EAD6034 da FEA-USP.

## Entrega de 21/09/2026 — versão cumulativa atual

Estudo empírico do **WIN nas seis escalas disponíveis**, com treino exclusivamente em 2024 e avaliação em 2025. A pergunta sobre maior previsibilidade horária é confrontada com os resultados, não imposta aos modelos. Esta versão incorpora e recalcula as etapas de 31/08 e 14/09 e acrescenta previsão, modelos alternativos, combinação, Diebold–Mariano e ARCH/GARCH, usando somente métodos das aulas.

**Mudança aprovada no índice temporal:** retornos continuam sem atravessar pregões ou contratos, mas suas defasagens e os estados dos modelos atravessam as fronteiras entre sessões. Uma série anual por escala substitui os testes separados por pregão. Em 60 minutos, são **2.214 observações de treino**, não apenas nove por sessão. Isso não demonstra ausência de efeitos overnight; eles não são modelados separadamente.

- [Slides — capa, oito slides de conteúdo e contracapa](results/entrega_21_09/ENTREGA_21_09.pdf), dez páginas, e [fonte editável Beamer](results/entrega_21_09/ENTREGA_21_09.tex).
- [Relatório técnico completo](results/entrega_21_09/RELATORIO_21_09.md) e [guia de apresentação — cinco minutos de fala](results/entrega_21_09/GUIA_APRESENTACAO.md).
- [Conclusão crítica](results/entrega_21_09/CONCLUSAO_CRITICA.md) e [questões, com respostas e referências às aulas](results/entrega_21_09/questões.md).
- [Podcast de preparação — transcrição com tempos](results/entrega_21_09/PODCAST_TRANSCRICAO.md), [roteiro do diálogo](docs/PODCAST_PREPARACAO_21_09.md) e [gerador Python do áudio](scripts/build_podcast.py).
- [Protocolo pré-especificado](docs/PROTOCOL_21_09.md) e [auditoria histórica dos horários/leilões](docs/market_hours_2024_2025.md).
- [Código principal](src/ead6034/forecast_pipeline.py), [dados](src/ead6034/trading_time_data.py), [testes e ARMA](src/ead6034/annual_models.py), [previsões e DM](src/ead6034/forecast_evaluation.py) e [ARCH/GARCH](src/ead6034/conditional_volatility.py).
- [Modelos selecionados](results/entrega_21_09/tables/selected_models.csv), [acurácia](results/entrega_21_09/tables/accuracy.csv), [DM](results/entrega_21_09/tables/diebold_mariano.csv) e [manifesto reproduzível](results/entrega_21_09/analysis_summary.json).

**Amostras:** 246 pregões comuns de 02/01 a 30/12/2024; 221 pregões comuns de 02/01 a 28/11/2025. Janela 09:05–18:05 de São Paulo. As ordens e parâmetros são fixados no treino; durante o teste só os estados são atualizados com informação passada. O filtro de dias completos é retrospectivo e condiciona a amostra avaliada.

**Origem dos dados:** [BTG Alpha Lab — BTG-ATS-A26](https://alphalab.btgpactual.com/datasets/publication:7a74b3ae-90e0-4393-b1e0-01e61c0bedba), candles de negócios da B3. [Documentação e proveniência](docs/DATA_SOURCE.md). O fornecedor seleciona o vencimento de maior volume **do próprio dia**; essa escolha ex post também limita a interpretação operacional. A causalidade temporal das previsões não transforma a composição retrospectiva da base em uma regra executável antecipadamente.

**Conclusão principal:** os modelos não superaram globalmente o retorno zero em 2025. No horizonte comum de 60 minutos, o ARMA por BIC tem aproximadamente 0,194% a 0,203% mais MSE que zero. A evidência de dinâmica na variância é mais forte, mas a modelagem é parcial e não altera a previsão pontual. Os resultados não identificam causalmente efeitos de leilões. O roteiro detalha essas ressalvas e as perguntas técnicas das Aulas 2–6 disponíveis.

**Comparação justa:** além da próxima barra de cada escala, as cinco escalas intradiárias preveem os mesmos 1.989 alvos não sobrepostos de 60 minutos. MSE bruto de horizontes distintos não ranqueia previsibilidade. O diário open-to-close é avaliado separadamente. DM compara AR puro com MA puro, não modelos de variância aninhados. ARCH/GARCH é estimado sequencialmente sobre a mesma média fixa; sua inclusão não muda a previsão pontual do retorno.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock-21-09.txt
python -m pip install -e . --no-deps
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python scripts/run_entrega_21_09.py \
  --input data/raw/BTG-ATS-A26.zip --output results/entrega_21_09 --workers 3
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v
```

Os slides requerem `pdflatex`, Beamer e Latin Modern. `--skip-report` executa toda a análise sem LaTeX. Para regenerar figuras/relatos/slides a partir dos CSV públicos e da figura das séries completas já publicada: `PYTHONPATH=src python -m ead6034.forecast_report --output results/entrega_21_09 --code-ref COMMIT_DO_CODIGO`. Use o hash registrado no manifesto para links fixados. Os arquivos individuais de preços, retornos, previsões, resíduos, ZIP e caches permanecem locais em diretórios ignorados pelo Git.

O slide 2/8 apresenta todas as observações nas seis escalas, com cores para treino (2024) e teste (2025). O gráfico usa eixos verticais próprios por escala, sem suavização ou subamostragem. Para reconstruí-lo a partir dos frames locais produzidos pelo pipeline: `PYTHONPATH=src python -m ead6034.series_overview --output results/entrega_21_09`. O código verifica os hashes das séries contra o manifesto antes de desenhar e publica apenas a figura, com os traços rasterizados.

No manifesto, `presentation.code_ref` identifica o código da apresentação e `analysis_code_ref` preserva a referência da estimação. O roteiro de cinco minutos aborda os sete slides analíticos. O slide de inspeção visual aparece entre o primeiro e o segundo desses slides.

### Podcast de preparação

Diálogo em português com duas vozes sintéticas, cobrindo as três entregas, as premissas, os resultados e perguntas críticas ligadas às Aulas 2–6. O áudio de estudo tem limite de 20 minutos, distinto do roteiro de cinco minutos da apresentação. Sua duração medida, capítulos e hashes estão no [manifesto do podcast](results/entrega_21_09/podcast_manifest.json). O MP3 foi entregue diretamente ao autor; o repositório contém o roteiro, a transcrição e o gerador.

A síntese usa [Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx), inteiramente local, com as vozes brasileiras Alex e Dora. É necessário instalar FFmpeg e FFprobe, além das dependências opcionais abaixo. Baixe o [modelo ONNX](https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx) e o [arquivo de vozes](https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin) para `../ead6034-vozes/`, preservando os nomes. O texto não é enviado a um serviço de síntese. O [modelo Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) usa licença Apache 2.0; a biblioteca kokoro-onnx usa MIT. A geração de áudio não executa nem altera a estimação econométrica.

```bash
python -m venv .venv-podcast
source .venv-podcast/bin/activate
python -m pip install -r requirements-podcast.txt
python scripts/build_podcast.py \
  --models ../ead6034-vozes \
  --cache ../ead6034-audio-cache \
  --audio ../EAD6034_Podcast_Preparacao.mp3
```

O script sintetiza apenas os diálogos delimitados no roteiro, adapta a pronúncia de siglas, intercala as vozes, acrescenta pausas e capítulos, normaliza o volume e verifica a decodificação completa e a duração final. Não utiliza música. Os pesos de voz e os intermediários ficam fora do repositório. A forma de onda pode variar entre versões do sintetizador; os hashes dos modelos efetivamente usados e do áudio entregue constam do manifesto.

As versões abaixo são **históricas**, com convenções metodológicas anteriores documentadas, e não foram sobrescritas.

## Entrega de 14/09/2026

Continuação em Python da comparação multiescala do WIN, usando exclusivamente os 246 pregões de 2024. A entrega contém ADF, Phillips-Perron e KPSS, busca ARMA por BIC, comparação com AIC e diagnóstico dos resíduos.

O BIC escolheu ARMA(0,0) com constante nas seis escalas. A referência de ausência de autocorrelação residual é rejeitada em 1, 5 e 60 minutos, e há dependência nos resíduos ao quadrado intradiários. A conclusão distingue essa escolha parcimoniosa de um modelo plenamente adequado. A revisão de toda a grade, a sensibilidade ao horizonte e as alternativas por AIC estão documentadas.

- [Apresentação em PDF, 7 páginas](results/entrega_14_09/ENTREGA_14_09.pdf)
- [Relatório técnico com hipóteses, decisões e resultados completos](results/entrega_14_09/RELATORIO_14_09.md)
- [Guia para apresentação e perguntas](results/entrega_14_09/GUIA_APRESENTACAO.md)
- [Testes por trecho e especificação](results/entrega_14_09/tables/stationarity_all.csv)
- [Grade de modelos ARMA](results/entrega_14_09/tables/arma_grid_all.csv)
- [Modelos selecionados](results/entrega_14_09/tables/selected_models.csv)
- [Diagnósticos](results/entrega_14_09/tables/residual_diagnostics.csv)

**Fronteiras entre pregões:** testes convencionais são aplicados separadamente aos trechos contínuos. Não se atribui um p-valor convencional a uma regressão pooled com resets. As taxas de rejeição por escala são descritivas. Sessões de 30/60 minutos contêm apenas 18/9 observações, o que limita a evidência. No diário, sete segmentos são testáveis e os dez segmentos entram na estimação ARMA.

**Box-Jenkins:** parâmetros comuns, verossimilhança gaussiana com inicialização estacionária em cada segmento e grade `p,q=0,...,5`. BIC conta média e variância entre os parâmetros. O relatório registra falhas, restrições de identificação e convergência. O Q dos resíduos respeita as fronteiras e acompanha uma calibração bootstrap gaussiana com reestimação, condicionada à ordem escolhida. Essa referência não corrige heteroscedasticidade.

```bash
pip install -r requirements-lock-14-09.txt
pip install -e . --no-deps
OPENBLAS_NUM_THREADS=1 python scripts/run_entrega_14_09.py \
  --input data/raw/BTG-ATS-A26.zip \
  --output results/entrega_14_09
PYTHONPATH=src python -m unittest discover -s tests -v
```

O comando calcula a grade completa com três inicializações e executa 999 réplicas bootstrap por escala. `--skip-report` omite apenas a geração de figuras, Markdown e PDF. O parâmetro `--bootstrap-reps` controla as réplicas. Os caches locais de retornos/resíduos em `private/` não são publicados. As decisões da entrega de 31/08 e seus artefatos continuam disponíveis abaixo.

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

## Decisões metodológicas de 31/08 (histórico)

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
