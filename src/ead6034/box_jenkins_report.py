"""Python figures, seven-page seminar PDF and a detailed audit-ready report."""
from __future__ import annotations

import json
from pathlib import Path
import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT

SCALES=["1min","5min","15min","30min","60min","1d"]
LABELS={"1min":"1 minuto","5min":"5 minutos","15min":"15 minutos","30min":"30 minutos","60min":"60 minutos","1d":"1 dia"}
NAVY="#142D48"; TEAL="#087F8C"; ORANGE="#BC642D"; GRAY="#4E5B68"


def fmt(x,d=3):
    return f"{float(x):.{d}f}".replace(".",",")


def pformat(x):
    if float(x)<.001:return "<0,001"
    return fmt(x)


def order(row):
    return f"({int(row.p)},{int(row.q)})"


def markdown_table(headers,rows):
    return "| "+" | ".join(headers)+" |\n|"+"|".join(["---"]*len(headers))+"|\n"+"\n".join("| "+" | ".join(map(str,row))+" |" for row in rows)+"\n"


def figures(out,summary,joint,grid,corr,squared):
    directory=out/"figures";directory.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    fig,axes=plt.subplots(2,3,figsize=(12.5,6.3),layout="constrained")
    for ax,scale in zip(axes.flat,SCALES):
        g=corr[corr.scale==scale]
        ax.axhline(0,color=GRAY,lw=.6)
        ax.vlines(g.lag-.12,0,g.acf,color=TEAL,lw=1.8,label="FAC")
        ax.vlines(g.lag+.12,0,g.pacf,color=ORANGE,lw=1.5,label="FACP")
        ax.plot(g.lag,g.acf_band,color=TEAL,ls="--",lw=.8)
        ax.plot(g.lag,-g.acf_band,color=TEAL,ls="--",lw=.8)
        ax.plot(g.lag,g.pacf_band,color=ORANGE,ls=":",lw=.8)
        ax.plot(g.lag,-g.pacf_band,color=ORANGE,ls=":",lw=.8)
        ax.set_title(LABELS[scale],fontweight="bold",color=NAVY)
        ax.set_xlabel("Defasagem (pregões)" if scale=="1d" else "Defasagem (barras)")
        ax.set_ylabel("Autocorrelação")
        ax.set_xlim(.3,g.lag.max()+.7)
        extent=max(g.acf.abs().max(),g.pacf.abs().max(),g.pacf_band.max())*1.25
        ax.set_ylim(-extent,extent)
        ax.xaxis.get_major_locator().set_params(integer=True)
    axes[0,0].legend(frameon=False,fontsize=9,loc="lower right")
    fig.savefig(directory/"01_residual_acf_pacf.png",dpi=175)
    plt.close(fig)
    fig,axes=plt.subplots(2,3,figsize=(12.5,6.3),layout="constrained")
    for ax,scale in zip(axes.flat,SCALES):
        g=squared[squared.scale==scale]
        ax.axhline(0,color=GRAY,lw=.6)
        ax.vlines(g.lag,0,g.acf,color=ORANGE,lw=1.6)
        ax.plot(g.lag,g.acf_band,color=GRAY,ls="--",lw=.8)
        ax.plot(g.lag,-g.acf_band,color=GRAY,ls="--",lw=.8)
        ax.set_title(LABELS[scale],fontweight="bold",color=NAVY)
        ax.set_xlabel("Defasagem (pregões)" if scale=="1d" else "Defasagem (barras)")
        ax.set_ylabel("FAC dos resíduos ao quadrado")
        ax.xaxis.get_major_locator().set_params(integer=True)
    fig.savefig(directory/"02_squared_residual_acf.png",dpi=175)
    plt.close(fig)
    fig,axes=plt.subplots(2,3,figsize=(12.5,7),layout="constrained")
    for ax,scale in zip(axes.flat,SCALES):
        g=grid[(grid.scale==scale)&(grid.status=="eligible")]
        matrix=g.pivot(index="p",columns="q",values="delta_bic").reindex(index=range(6),columns=range(6))
        image=ax.imshow(np.clip(matrix,0,60),vmin=0,vmax=60,cmap="YlGnBu",origin="lower")
        for p in range(6):
            for q in range(6):
                x=matrix.loc[p,q]
                ax.text(q,p,"-" if pd.isna(x) else f"{x:.0f}",ha="center",va="center",fontsize=9,color="white" if x>35 else NAVY)
        ax.set_title(LABELS[scale],color=NAVY,fontweight="bold")
        ax.set_xlabel("Ordem MA (q)");ax.set_ylabel("Ordem AR (p)")
    fig.colorbar(image,ax=axes.ravel().tolist(),label="Diferença para o menor BIC da própria escala (cor limitada a 60)",shrink=.8)
    fig.savefig(directory/"03_bic_grid.png",dpi=175)
    plt.close(fig)


def write_report(out):
    out=Path(out);tables=out/"tables"
    read=lambda name:pd.read_csv(tables/f"{name}.csv")
    metadata=json.loads((out/"analysis_summary.json").read_text())
    selected=read("selected_models").set_index("scale").loc[SCALES].reset_index()
    tests=read("stationarity_all");summary=read("stationarity_summary");joint=read("stationarity_joint").set_index("scale").loc[SCALES].reset_index()
    grid=read("arma_grid_all");corr=read("residual_acf_pacf");squared=read("squared_residual_acf")
    diagnostics=read("residual_diagnostics").merge(read("ljungbox_bootstrap"),on="scale").set_index("scale").loc[SCALES].reset_index()
    review=read("model_review")
    figures(out,summary,joint,grid,corr,squared)
    rejection=summary.pivot(index="scale",columns="test",values="rejection_share")
    station_rows=[];model_rows=[];diagnostic_rows=[];sample_rows=[]
    for row in selected.itertuples():
        s=row.scale;j=joint[joint.scale==s].iloc[0];r=rejection.loc[s];d=diagnostics[diagnostics.scale==s].iloc[0]
        sample_rows.append([LABELS[s],f"{int(row.nobs):,}".replace(",","."),str(int(row.segments)),str(int(row.min_segment)) if row.min_segment==row.max_segment else f"{int(row.min_segment)} a {int(row.max_segment)}"])
        station_rows.append([LABELS[s],f"{int(j.tested_segments)}",fmt(100*r.ADF,1)+"%",fmt(100*r.PP,1)+"%",fmt(100*r.KPSS,1)+"%",fmt(100*j.supports_i0_share,1)+"%"])
        model_rows.append([LABELS[s],order(row),fmt(row.mu_pct,6),fmt(row.next_delta_bic,2),f"({int(row.aic_p)},{int(row.aic_q)})"])
        diagnostic_rows.append([LABELS[s],str(int(d.diagnostic_lag)),pformat(d.p_ljungbox_working),pformat(d.bootstrap_p),pformat(d.squared_p_working),fmt(d.excess_kurtosis,2)])
    representative=[]
    # Ex ante rule: longest segment, ties resolved by earliest date. This is
    # an illustration with actual test p-values, never a selected best result.
    main=tests[(tests.specification=="main")&(tests.status=="ok")]
    for scale in SCALES:
        g=main[main.scale==scale].sort_values(["n","start"],ascending=[False,True])
        sid=g.iloc[0].segment
        representative.append(g[g.segment==sid])
    rep=pd.concat(representative,ignore_index=True)
    rep.to_csv(tables/"stationarity_reference_segments.csv",index=False)
    detail_rows=[[LABELS[r.scale],r.test,r.start if r.start==r.end else r.start+" a "+r.end,int(r.n),int(r.lags),fmt(r.statistic),fmt(r.critical_5),pformat(r.pvalue),"Rejeita" if r.reject_5pct else "Não rejeita"] for r in rep.itertuples()]
    sensitivity=tests[tests.status=="ok"].groupby(["scale","specification","test"],sort=False).agg(segments=("segment","count"),rejection_share=("reject_5pct","mean")).reset_index()
    sensitivity.to_csv(tables/"stationarity_sensitivity.csv",index=False)
    grid_status=grid.groupby(["scale","status"]).size().unstack(fill_value=0)
    grid_review=read("grid_residual_review")
    review_rows=[]
    for scale in SCALES:
        g=grid_review[grid_review.scale==scale]
        passing=g[g.passes_working_reference].sort_values("bic")
        review_rows.append([LABELS[scale],int(g.h.iloc[0]),len(passing),len(g),
                           "Nenhum" if passing.empty else order(passing.iloc[0]),
                           "-" if passing.empty else fmt(passing.iloc[0].delta_bic,2)])

    md=f"""# EAD6034 - Entrega de 14/09/2026

**Renan de Luca Avila - Professor Leandro Maciel - FEA-USP**

## Pergunta e escopo

Como a dinâmica linear dos retornos do WIN varia entre 1, 5, 15, 30 e 60 minutos e o diário? Esta etapa examina estacionariedade e executa identificação, estimação e diagnóstico Box-Jenkins. A replicação adaptada de Matías e Reboredo (2012) continua centrada em 5 minutos. A dimensão executada da proposta é a escala temporal de um único futuro de índice. O arquivo não sustenta segundos, midquotes, ações ou opções.

O BIC selecionou {', '.join(LABELS[r.scale]+' ARMA'+order(r) for r in selected.itertuples())}. A escolha é uma referência para a equação da média. A avaliação dos resíduos abaixo impede confundir seleção por BIC com adequação de um modelo de ruído branco homoscedástico.

## 1. Amostra e fronteiras

Identificação de **02/01/2024 a 30/12/2024**, com **246 pregões completos comuns**, de 09:05 a 18:05 em São Paulo. O código filtra 2024 **antes** da auditoria, da seleção dos dias e de qualquer teste ou estimação. Nenhuma observação de 2025 entra nos procedimentos desta entrega. O hash do arquivo bruto é apenas uma identificação da fonte completa.

{markdown_table(['Escala','N total','Segmentos para ARMA','Observações por segmento'],sample_rows)}

As barras e os retornos reproduzem a entrega de 31/08. Intradiário: 100 log(C_t/C_anterior), ancorado no fechamento do candle iniciado às 09:04. Diário: 100 log(C_final/O_09:05). A soma dos retornos intradiários usa a fronteira close-to-close e difere do open-to-close pela passagem do close 09:04 ao open 09:05. Não há winsorização, interpolação ou retorno atravessando pregão ou contrato.

Cada pregão é um segmento intradiário. No diário, exclusões, lacuna da fonte de 16/04/2024 e mudanças de contrato dividem a sequência em dez segmentos de comprimentos 25, 3, 16, 25, 35, 2, 45, 45, 43 e 7. Para os testes, os três segmentos com menos de oito observações ficam explicitamente sem resultado. Os dez segmentos e as 246 observações entram na verossimilhança ARMA. A reinicialização implica que o modelo não carrega estado ou informação defasada através dessas fronteiras.

## 2. Estacionariedade: definição e execução

ADF e PP têm H0 de raiz unitária. KPSS tem H0 de estacionariedade em torno dos termos determinísticos. Rejeitar raiz unitária não prova todas as condições de estacionariedade fraca, nem elimina sazonalidade da variância, quebras ou dependência em magnitude.

Aplicam-se **testes convencionais separadamente a cada segmento**. Concatenar dias criaria defasagens artificiais. Também não se estimou uma regressão pooled com resets para então aplicar indevidamente os valores críticos de uma única série. As taxas de rejeição e medianas são descritivas, sem p-valor combinado ou conclusão universal para todos os pregões. Não há correção de multiplicidade nas decisões individuais a 5%.

Especificação principal: constante, sem tendência (`c`), pois a variável é retorno. ADF: seleção BIC entre 0 e K defasagens das diferenças, com K=min(12, max(0,floor(n/5)-1), max(0,floor(n/2)-3)). PP: estatística tau e correção não paramétrica Newey-West/Bartlett. PP e KPSS usam L=min(max(1,floor(4(n/100)^(1/4))), max(1,floor((n-1)/4))). A regra curta limita a fração da amostra consumida pela estimação da variância de longo prazo. É uma escolha explícita deste estudo, não o padrão automático das bibliotecas. Sensibilidade: ADF com AIC e bandwidth 2L limitado a floor((n-1)/3), além de constante e tendência (`ct`) quando n>=20.

ADF/PP rejeitam quando a estatística fica abaixo do valor crítico de 5%; KPSS rejeita quando fica acima. O uso dos valores críticos evita tratar o p-valor aproximado como mais exato, especialmente nos trechos curtos. Os valores de ADF/PP vêm das aproximações de MacKinnon; KPSS usa a tabela simulada do pacote `arch`. P-valores reportados como <0,001 incluem os truncados numericamente em zero pela biblioteca, não probabilidades matematicamente nulas.

### Síntese dos testes por segmento

{markdown_table(['Escala','Trechos testados','ADF rejeita H0','PP rejeita H0','KPSS rejeita H0','Concordância com I(0)'],station_rows)}

Concordância com I(0) = ADF e PP rejeitam raiz unitária, e KPSS não rejeita estacionariedade, no **mesmo trecho**. Não rejeitar KPSS é ausência de evidência contra sua H0. Diferenças de taxas entre escalas também refletem comprimentos amostrais diferentes. Com 18 ou 9 observações por pregão, as aproximações dos testes são frágeis e seu poder é baixo. Uma queda da taxa de rejeição do ADF não demonstra que os retornos agregados adquiriram raiz unitária. No diário, a evidência é local a sete segmentos testáveis e não estabelece estabilidade entre regimes ao longo do ano.

### Estatística, p-valor e valor crítico de um trecho de referência

Regra anterior à inspeção dos resultados: maior comprimento disponível, desempate pela data mais antiga. Nos intradiários isso corresponde ao primeiro pregão completo. A tabela apresenta testes reais de um trecho, não estatísticas ou p-valores obtidos pela média de testes. As demais linhas estão em `tables/stationarity_all.csv`.

{markdown_table(['Escala','Teste','Período','n','lags/L','Estatística','Crítico 5%','p','Decisão H0'],detail_rows)}

Todas as especificações, datas, avisos, tamanhos amostrais, defasagens e valores críticos de 1%, 5% e 10% estão no CSV completo. `stationarity_sensitivity.csv` permite avaliar as escolhas alternativas sem procurar retrospectivamente uma especificação que produza a conclusão desejada.

## 3. Box-Jenkins: identificação e estimação

A FAC/FACP da entrega de 31/08 mostrou correlações pequenas dos retornos e dependência mais nítida nas magnitudes. Isso motiva incluir ARMA(0,0), AR puro, MA puro e modelos mistos, sem impor uma ordem a partir de um pico isolado. Mantém-se d=0 nos retornos como especificação de trabalho, apoiada pela evidência nos trechos mais longos. Nas escalas com sessões curtas, essa escolha é provisória. Não se diferencia automaticamente o retorno quando o ADF deixa de rejeitar em amostra pequena.

Modelo: r_(s,t) = mu + soma_i phi_i (r_(s,t-i)-mu) + epsilon_(s,t) + soma_j theta_j epsilon_(s,t-j). `mu` é a média incondicional; o intercepto equivalente é c=mu(1-soma phi). Os parâmetros são comuns aos segmentos, que reiniciam com a distribuição estacionária do modelo. Não se subtrai uma média por dia.

A verossimilhança gaussiana é a soma das contribuições dos segmentos. O algoritmo de inovações calcula exatamente a inicialização estacionária dentro do modelo. Média e variância são concentradas analiticamente, mas **ambas contam como parâmetros**: k=p+q+2. Usam-se AIC=-2 log L+2k e BIC=-2 log L+k log N. AIC/BIC absolutos só são comparados na mesma escala, mesma amostra e unidade. Heteroscedasticidade e possível dependência entre dias fazem dessa verossimilhança uma quase-verossimilhança gaussiana de trabalho, sem afirmar que os retornos sejam normais ou que os segmentos sejam independentes no mercado.

Grade p,q em 0,...,{metadata['max_order']}. {metadata['optimizer_starts']} inicializações determinísticas por modelo, incluindo zero, uma solução de ordem menor quando disponível e/ou perturbação aleatória com semente fixa. Parametrização garante estacionariedade AR e invertibilidade MA. Raízes dos polinômios 1-soma(phi_i z^i) e 1+soma(theta_j z^j) precisam ter módulo >1,001 para elegibilidade numérica. Convergência é registrada, sem garantia de máximo global. Na escala de 60 minutos, (4,5), (5,4) e (5,5) são excluídos antes da estimação quando presentes na grade: nove observações por réplica fornecem apenas nove autocovariâncias distintas, insuficientes para p+q+1 parâmetros de covariância nesses casos.

{markdown_table(['Escala','ARMA por BIC','mu (% por barra)','Distância do 2º BIC','ARMA por AIC'],model_rows)}

Para ARMA(0,0) com constante, a previsão condicional do retorno é a média estimada do treino. Ele difere do benchmark de retorno exatamente zero. A falta de ganho suficiente dos termos AR/MA pelo BIC não implica eficiência de mercado ou ausência de previsibilidade não linear. Todas as ordens, falhas, exclusões, raízes e diferenças de BIC ficam em `arma_grid_all.csv`; os coeficientes completos ficam em `selected_models.csv`.

## 4. Diagnóstico e revisão

Resíduos são inovações padronizadas pelo desvio-padrão preditivo do modelo. FAC: numerador apenas com pares do mesmo segmento, centrado pela média global, e denominador global soma(e_t-media)^2. A FAC residual usa esta normalização Box-Jenkins para ser compatível com o portmanteau; ela difere da correlação Pearson dos pares usada na primeira entrega. FACP mantém o último coeficiente de OLS AR(k) pooled, sem atravessar fronteiras.

Com N_k pares válidos, Q(h)=N(N+2) soma_(k=1)^h FAC(k)^2/N_k. Para um único segmento N_k=N-k, recupera-se Ljung-Box usual. A referência qui-quadrado com h-p-q graus de liberdade é **aproximada** nos dados segmentados e heteroscedásticos. `ljungbox_by_segment.csv` também contém testes Ljung-Box convencionais por trecho, com correção de graus de liberdade igualmente aproximada porque os parâmetros são comuns.

Uma calibração adicional simula {int(diagnostics.bootstrap_reps.iloc[0])} amostras do ARMA gaussiano homoscedástico selecionado, com os mesmos comprimentos de segmento e inicialização estacionária exata. Reestima-se a ordem selecionada em cada amostra e recomputa-se Q. p=(1+excedências)/(B+1). Esse bootstrap considera os resets e a estimação, condicionado à ordem escolhida; **não corrige heteroscedasticidade nem repete a seleção da grade**. É uma referência do modelo, não uma inferência robusta geral. A resolução mínima é 1/(B+1) e o erro Monte Carlo fica registrado.

{markdown_table(['Escala','h (barras/pregões)','p Q aprox.','p bootstrap gauss.','p Q de e² aprox.','Curtose excedente'],diagnostic_rows)}

Os horizontes desta tabela servem ao diagnóstico de cada modelo; não são todos a mesma separação física. Em 1/5/15 minutos, h=60/12/4 corresponde a 60 minutos. Em 30/60 minutos, h=4 corresponde a 120/240 minutos. No diário h=10 corresponde a dez pregões dentro do segmento. Bandas dos gráficos são pontuais e aproximadas sob ruído branco; não corrigem múltiplos lags ou heteroscedasticidade.

O relatório de revisão compara o modelo de menor BIC, o de menor AIC e o melhor AR puro (`model_review.csv`). Uma falha no diagnóstico não é ocultada promovendo o vencedor por BIC a modelo plenamente adequado. Dependência em e², caudas pesadas e perfil intradiário de variância indicam que uma média linear simples pode ser útil como benchmark mesmo quando a hipótese de ruído branco gaussiano homoscedástico é inadequada. Jarque-Bera e seus p-valores constam da tabela completa, também como referência assintótica.

**Resultado concreto do diagnóstico principal:** rejeição da referência de ausência de autocorrelação residual em 1, 5 e 60 minutos, tanto pela aproximação qui-quadrado quanto pelo bootstrap gaussiano a 5%. Nas escalas de 15 e 30 minutos e no diário não há rejeição nesse corte. A FAC dos resíduos ao quadrado rejeita a referência em todas as escalas intradiárias, mas não no diário. Jarque-Bera rejeita normalidade nas seis escalas. Assim, nenhum vencedor intradiário é certificado aqui como ruído branco homoscedástico.

### Nova inspeção da grade e sensibilidade ao horizonte do diagnóstico

Reexaminamos todos os candidatos elegíveis em horizontes mais extensos, fixos dentro de cada escala, para observar correlação além do primeiro corte e acomodar ordens maiores. A tabela seguinte usa somente a referência qui-quadrado aproximada, sem bootstrap ou correção pela busca de modelos. “Não rejeita” não significa modelo validado. O critério principal BIC permanece o da proposta.

{markdown_table(['Escala','h','Não rejeitam Q','Avaliados','Menor BIC entre não rejeitados','Delta BIC'],review_rows)}

Em 1 minuto, nenhum dos 36 candidatos supera essa referência de diagnóstico em h=60: a adequação da média linear permanece em aberto. Em 5 minutos, a decisão muda entre h=12 (rejeita) e h=24 (não rejeita), mostrando sensibilidade ao horizonte. Em 60 minutos, AR(2) é o candidato de menor BIC entre os que não rejeitam em h=8, com penalidade de aproximadamente 2,70 frente a ARMA(0,0); ele fica registrado como alternativa para a avaliação futura. Essas observações não autorizam selecionar o horizonte que “aprova” um modelo ou afirmar ganho fora da amostra.

## 5. Conclusões e etapa de 21/09

- Os testes oferecem evidência de ausência de raiz unitária nos trechos de maior resolução, com limitações fortes nas sessões de 30 e 60 minutos. A concordância local não estabelece estacionariedade global da variância ou entre regimes.
- A seleção por BIC privilegia ARMA(0,0) nas seis escalas. A rejeição residual em 1, 5 e 60 minutos impede tratar essa escolha como encerramento da adequação Box-Jenkins. Em 1 minuto, a revisão da grade tampouco elimina a rejeição da referência.
- A modelagem da média não esgota a dinâmica da volatilidade. O ajuste gaussiano serve como benchmark e não valida uma distribuição de risco homoscedástica.
- Estacionariedade, ausência de autocorrelação, ajuste dentro da amostra e ganho preditivo fora da amostra são propriedades diferentes. Esta entrega não avalia o último item.
- Para 21/09: avaliação com origem móvel em 2025, horizontes economicamente interpretáveis, retorno zero/média histórica/AR restrito, modelo alternativo e combinação, métricas de acurácia e Diebold-Mariano. Reestimações e transformações deverão usar apenas informação disponível em cada origem.

## Reprodução e referências

```bash
pip install -e .
OPENBLAS_NUM_THREADS=1 python scripts/run_entrega_14_09.py --input data/raw/BTG-ATS-A26.zip
PYTHONPATH=src python -m unittest discover -s tests -v
```

O comando gera tabelas, figuras, relatório e PDF. `private/` contém apenas caches locais de retornos/resíduos, ignorados pelo Git. Python {metadata['python']}. Versões efetivas: {', '.join(k+' '+v for k,v in metadata['versions'].items())}. Os testes de código comparam a verossimilhança com filtros Kalman independentes, verificam resets, contagem de parâmetros, fronteiras dos pares e equivalência com Ljung-Box para uma única série.

- Maciel, L. Materiais fornecidos da EAD6034: Aula 4, Metodologia Box & Jenkins; Aula 5, Tendência e Raiz Unitária. Requisitos: EAD6034TrabalhoUnivariado_2026, entrega de 14/09.
- Matías, J. M.; Reboredo, J. C. (2012). Forecasting performance of nonlinear models for intraday stock returns. Journal of Forecasting 31(2), 172-188. https://doi.org/10.1002/for.1218
- [ADF: especificações, seleção de lags e aproximações de MacKinnon](https://arch.readthedocs.io/en/latest/unitroot/generated/arch.unitroot.ADF.html).
- [Phillips-Perron: tau e correção Newey-West](https://arch.readthedocs.io/en/latest/unitroot/generated/arch.unitroot.PhillipsPerron.html).
- [KPSS: hipóteses, bandwidth e valores críticos](https://arch.readthedocs.io/en/latest/unitroot/generated/arch.unitroot.KPSS.html).
- [Algoritmo de inovações ARMA em statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.tsa.innovations.arma_innovations.arma_innovations.html).
- [Ljung-Box e graus de liberdade em statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.stats.diagnostic.acorr_ljungbox.html).
- [Hyndman e Athanasopoulos: identificação, seleção e diagnóstico ARIMA](https://otexts.com/fpp3/arima-r.html).
"""
    (out/"RELATORIO_14_09.md").write_text(md,encoding="utf-8")
    write_pdf(out,metadata,selected,joint,diagnostics,sample_rows,station_rows,model_rows,diagnostic_rows)
    return out/"ENTREGA_14_09.pdf"


def write_pdf(out,meta,selected,joint,diag,sample_rows,station_rows,model_rows,diagnostic_rows):
    fontdir=Path(matplotlib.get_data_path())/"fonts/ttf"
    pdfmetrics.registerFont(TTFont("DV",str(fontdir/"DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DV-Bold",str(fontdir/"DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFontFamily("DV",normal="DV",bold="DV-Bold")
    width,height=841.89,595.28
    c=canvas.Canvas(str(out/"ENTREGA_14_09.pdf"),pagesize=(width,height),pageCompression=1,invariant=1)
    c.setTitle("EAD6034 - Estacionariedade e Box-Jenkins multiescala - 14/09/2026")
    c.setAuthor("Renan de Luca Avila")
    def text(txt,x,y,w=745,size=15,color=NAVY,bold=False):
        style=ParagraphStyle("body",fontName="DV-Bold" if bold else "DV",fontSize=size,leading=size*1.35,textColor=HexColor(color),alignment=TA_LEFT)
        para=Paragraph(txt,style);_,h=para.wrap(w,height)
        if y-h<38: raise ValueError(f"Text overflow: {txt[:50]}")
        para.drawOn(c,x,y-h)
        return y-h
    def page(num,title):
        c.setFillColor(white);c.rect(0,0,width,height,fill=1,stroke=0)
        text("EAD6034  /  ENTREGA DE 14.09.2026",42,567,size=10,color=TEAL,bold=True)
        text(title,42,535,size=25,bold=True)
        c.setStrokeColor(HexColor("#DCE3E8"));c.line(42,44,800,44)
        c.setFillColor(HexColor(GRAY));c.setFont("DV",8.5)
        c.drawString(42,27,"Renan de Luca Avila  |  Professor Leandro Maciel  |  FEA-USP")
        c.drawRightString(800,27,f"{num}/7")
    def table(headers,rows,widths,top=465,size=13,rowheight=42):
        x0=42; total=sum(widths)
        c.setFillColor(HexColor(NAVY));c.rect(x0,top-rowheight,total,rowheight,fill=1,stroke=0)
        for i,head in enumerate(headers):
            text(head,x0+sum(widths[:i])+9,top-5,w=widths[i]-14,size=size-1,color="#FFFFFF",bold=True)
        y=top-rowheight
        for ri,row in enumerate(rows):
            if ri%2==0:
                c.setFillColor(HexColor("#F0F5F7"));c.rect(x0,y-rowheight,total,rowheight,fill=1,stroke=0)
            for i,value in enumerate(row):
                text(str(value),x0+sum(widths[:i])+9,y-10,w=widths[i]-14,size=size)
            y-=rowheight
        return y
    page(1,"WIN: estacionariedade e modelos ARMA")
    text("Comparação entre 1, 5, 15, 30 e 60 minutos e o diário",42,471,size=19,color=GRAY)
    all_zero=all((r.p==0 and r.q==0) for r in selected.itertuples())
    headline="O BIC escolhe uma média constante nas seis escalas" if all_zero else "A seleção por BIC e os resíduos definem o alcance do modelo"
    text(headline,42,404,w=710,size=29,bold=True)
    text("ARMA(0,0) com constante é um benchmark para o retorno. A dinâmica da variância e a avaliação preditiva exigem análise própria.",42,300,w=720,size=19)
    text("02/01 a 30/12/2024<br/>246 pregões comuns, janela 09:05-18:05<br/>5 minutos: replicação adaptada de Matías e Reboredo (2012)",42,201,size=16,color=GRAY)
    c.showPage()
    page(2,"Amostra e unidades de análise")
    table(["Escala","N total","Segmentos ARMA","n por segmento"],sample_rows,[150,170,215,222],top=474,rowheight=40,size=15)
    text("Testes em cada trecho contínuo. Intradiário: um pregão por trecho. Diário: resets nas lacunas e trocas de contrato.",42,171,size=15)
    text("Os testes usam 7 dos 10 segmentos diários. Os trechos com n&lt;8 ficam sem teste. O ARMA usa todas as 246 observações diárias. 2025 permanece reservado.",42,112,size=13,color=GRAY)
    c.showPage()
    page(3,"Evidência de estacionariedade por escala")
    text("Frequência de rejeição individual a 5% nos trechos testados",42,483,size=14,color=GRAY)
    table(["Escala","Trechos","ADF<br/>H0: RU","PP<br/>H0: RU","KPSS<br/>H0: I(0)","Concorda<br/>com I(0)"],station_rows,[142,84,129,129,136,137],top=449,rowheight=39,size=13)
    text("Concordância: ADF e PP rejeitam raiz unitária e KPSS não rejeita estacionariedade no mesmo trecho. São frequências descritivas, sem p-valor combinado.",42,159,size=13)
    text("30 e 60 minutos: apenas 18 e 9 observações por pregão. Baixo poder e aproximações frágeis limitam a conclusão. Ausência de rejeição não comprova raiz unitária.",42,100,size=12.5,color=ORANGE)
    c.showPage()
    page(4,"Seleção dos modelos por BIC")
    table(["Escala","ARMA<br/>BIC","Média (%)","Distância<br/>2º BIC","ARMA<br/>AIC"],model_rows,[151,113,188,159,146],top=469,rowheight=42,size=14)
    text("Grade p,q=0,...,5. Parâmetros comuns e inicialização estacionária em cada segmento. Média e variância contam na penalização.",42,157,size=14)
    text("Na escala de 60 minutos, três ordens excedem a informação de covariância disponível e são excluídas. BICs absolutos só se comparam dentro de cada escala.",42,98,size=12.5,color=GRAY)
    c.showPage()
    page(5,"FAC e FACP dos resíduos")
    c.drawImage(str(out/"figures/01_residual_acf_pacf.png"),42,97,width=757,height=382,preserveAspectRatio=True,anchor="c",mask="auto")
    text("Inovações padronizadas. Lags respeitam cada segmento. Bandas pontuais sob ruído branco são aproximadas e não corrigem heteroscedasticidade ou múltiplos testes.",42,83,size=11,color=GRAY)
    c.showPage()
    page(6,"Diagnóstico da média e da variância")
    table(["Escala","h","p Q<br/>aprox.","p bootstrap<br/>gaussiano","p Q de e²<br/>aprox.","Curtose<br/>excedente"],diagnostic_rows,[142,55,124,157,146,133],top=469,rowheight=40,size=13)
    text("Q usa apenas pares válidos. h está em barras ou pregões. O bootstrap refaz a estimação com a ordem fixa e a mesma segmentação.",42,170,size=13)
    text(f"Q rejeita a referência em 1, 5 e 60 minutos. Bootstrap gaussiano homoscedástico: {int(diag.bootstrap_reps.iloc[0])} réplicas. O Q de e² rejeita nas cinco escalas intradiárias.",42,111,size=13,color=ORANGE)
    c.showPage()
    page(7,"Conclusões e continuidade")
    statements=[
      ("Estacionariedade", "A evidência é local aos segmentos. Os testes mais curtos não sustentam uma conclusão forte sobre raiz unitária ou estabilidade global."),
      ("Equação da média", "ARMA(0,0) vence o BIC, mas falha na referência residual em 1, 5 e 60 minutos. A grade não elimina a rejeição em 1 minuto."),
      ("Volatilidade", "A dependência nas magnitudes exige atenção própria. Uma média constante pode coexistir com variância condicional persistente."),
      ("Entrega de 21/09", "Avaliar previsões em 2025, comparar benchmarks e modelo alternativo, combinar previsões e aplicar métricas de acurácia e Diebold-Mariano.")]
    y=475
    for title,body in statements:
        text(title,42,y,w=170,size=16,bold=True,color=TEAL)
        end=text(body,225,y,w=570,size=15)
        y=min(y-90,end-24)
    text("Fontes: Aulas 4 e 5 da EAD6034. Métodos, tabelas completas e referências no relatório técnico e no repositório avilarenan/EAD6034.",42,84,size=10.5,color=GRAY)
    c.showPage();c.save()


if __name__=="__main__":
    import sys
    write_report(Path(sys.argv[1] if len(sys.argv)>1 else "results/entrega_14_09"))
