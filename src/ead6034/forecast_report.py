"""Editable Beamer deck: cover, eight content slides and back cover."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

SCALES = ["1min", "5min", "15min", "30min", "60min", "1d"]
LABELS = dict(zip(SCALES, ["1 min", "5 min", "15 min", "30 min", "60 min", "Diário OC"]))
REPO = "https://github.com/avilarenan/EAD6034"
DATASET_URL = "https://alphalab.btgpactual.com/datasets/publication:7a74b3ae-90e0-4393-b1e0-01e61c0bedba"
STUDY_TITLE = "Previsibilidade linear do WIN em múltiplas escalas temporais"
COURSE_NAME = "Econometria de Séries Temporais"
COURSE_CODE = "EAD6034"
AUTHOR = "Renan de Luca Avila"
PROFESSOR = "Prof. Leandro Maciel"
PRESENTATION_FORMAT = "cover_eight_content_slides_back_cover_Beamer_and_PDF"


def tex(value):
    substitutions = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
                     "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}"}
    return "".join(substitutions.get(c, c) for c in str(value))


def number(value, digits=3):
    if not np.isfinite(float(value)):
        return "--"
    return f"{float(value):.{digits}f}".replace(".", ",")


def pformat(value):
    value = float(value)
    if not np.isfinite(value):
        return "--"
    return "$<0{,}001$" if value < .001 else number(value)


def hypothesis_decision(pvalue):
    """Display the decision about the stated null at the 5% level."""
    if not np.isfinite(float(pvalue)):
        return "--"
    return r"\alert{Rejeita}" if float(pvalue) < .05 else "Não rejeita"


def table(headers, rows, alignment=None):
    alignment = alignment or ("l" + "r" * (len(headers)-1))
    return (r"\begin{tabular}{" + alignment + "}\n\\toprule\n"
            + " & ".join(headers) + r" \\ \midrule" + "\n"
            + "\n".join(" & ".join(map(str, row)) + r" \\" for row in rows)
            + "\n\\bottomrule\n\\end{tabular}\\par\n")


def cover_frame(code_base):
    """Academic title page, outside the numbered content slides."""
    return (
        r"\begin{frame}[plain,noframenumbering]" + "\n"
        + r"\vspace*{0.35cm}\raggedright "
        + r"{\large\color{teal}Universidade de São Paulo\par}\medskip "
        + r"{\large " + tex(COURSE_NAME) + " (" + tex(COURSE_CODE) + r")\par}"
        + r"\vspace{0.9cm}"
        + r"{\fontsize{23}{28}\selectfont\bfseries Previsibilidade linear do WIN\par "
        + r"em múltiplas escalas temporais\par}"
        + r"\medskip{\normalsize Seminário de modelos univariados\par}\vfill "
        + r"{\large\textbf{" + tex(AUTHOR) + r"}\par}\smallskip "
        + r"{\large " + tex(PROFESSOR) + r"\par}\vspace{0.45cm}"
        + r"{\small 21 de setembro de 2026\par}\smallskip "
        + r"{\small\href{" + code_base + r"/src/ead6034/forecast_pipeline.py}{Código da análise no GitHub}\par}"
        + "\n\\end{frame}\n"
    )


def back_cover_frame(code_base):
    """Closing page with repository and data links, without extra talk content."""
    return (
        r"\begin{frame}[plain,noframenumbering]" + "\n"
        + r"\centering\vspace*{1.0cm}"
        + r"{\fontsize{30}{36}\selectfont\bfseries Obrigado\par}\medskip "
        + r"{\Large\color{teal}Perguntas e discussão\par}\vspace{0.9cm}"
        + r"{\large " + tex(AUTHOR) + r"\par}\smallskip "
        + r"{\normalsize " + tex(COURSE_NAME) + " (" + tex(COURSE_CODE) + r")\par}"
        + r"\vfill{\normalsize\href{" + code_base + r"/src/ead6034/forecast_pipeline.py}{Código da análise no GitHub}\par}\medskip "
        + r"{\small\href{" + REPO + r"/tree/main/results/entrega_21_09}{Slides, roteiro e resultados completos}\par}\smallskip "
        + r"{\small\href{" + DATASET_URL + r"}{Dados: BTG Alpha Lab, BTG-ATS-A26}\par}\vspace{0.3cm}"
        + "\n\\end{frame}\n"
    )


def build_slides(output, code_ref="main", figures=None):
    out = Path(output)
    def read(name):
        return pd.read_csv(out / "tables" / f"{name}.csv")
    metadata = json.loads((out / "analysis_summary.json").read_text())
    desc, station = read("descriptive"), read("stationarity")
    selected, diagnostics = read("selected_models"), read("mean_diagnostics")
    accuracy, dm = read("accuracy"), read("diebold_mariano")
    variances, vard = read("variance_models"), read("variance_diagnostics")
    audit, alignment = read("sequence_audit"), read("common_target_alignment")
    main_models = selected.loc[selected.model.eq("ARMA_BIC")].set_index("scale")
    principal = diagnostics.loc[diagnostics.model.eq("ARMA_BIC") & diagnostics.principal_horizon].set_index("scale")
    main_accuracy = accuracy.loc[accuracy.model.eq("ARMA_BIC") & accuracy.group_type.eq("all")]
    var_selected = variances.loc[variances.selected_bic].set_index("scale")
    code_base = f"{REPO}/blob/{code_ref}"
    preamble = r"""\documentclass[aspectratio=169,10pt]{beamer}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\hyphenpenalty=10000
\exhyphenpenalty=10000
\usepackage{booktabs,graphicx,amsmath}
\definecolor{navy}{HTML}{142B43}
\definecolor{teal}{HTML}{007F83}
\definecolor{orange}{HTML}{B55A21}
\definecolor{muted}{HTML}{526273}
\setbeamercolor{normal text}{fg=navy,bg=white}
\setbeamercolor{frametitle}{fg=navy}
\setbeamercolor{structure}{fg=teal}
\setbeamercolor{alerted text}{fg=orange}
\setbeamercolor{block title}{fg=teal,bg=white}
\setbeamercolor{block body}{fg=navy,bg=white}
\setbeamertemplate{navigation symbols}{}
\setbeamertemplate{frametitle}{\vspace{0.15cm}\insertframetitle\par\vspace{0.03cm}{\color{teal}\rule{\textwidth}{0.6pt}}}
\setbeamersize{text margin left=0.6cm,text margin right=0.6cm}
\setbeamerfont{frametitle}{size=\Large,series=\bfseries}
\setbeamerfont{footline}{size=\tiny}
\setbeamertemplate{footline}{\hspace{0.6cm}\color{muted}EAD6034 | Renan de Luca Avila | 21/09/2026\hfill\insertframenumber/\inserttotalframenumber\hspace{0.6cm}\vspace{0.15cm}}
\hypersetup{colorlinks=true,urlcolor=teal,linkcolor=teal,pdftitle={EAD6034 | Previsibilidade linear do WIN},pdfauthor={Renan de Luca Avila}}
\newcommand{\source}[2]{\par\vfill{\raggedright\tiny\color{muted}#1\quad\href{#2}{Código reproduzível no GitHub}\par}}
\newcommand{\tagline}[1]{{\small\color{teal}#1}\par\medskip}
\begin{document}
"""
    slides = []
    def source(module, lesson):
        return r"\source{" + tex(lesson) + "}{" + code_base + "/src/ead6034/" + module + "}"
    def frame(title, body, module, lesson):
        slides.append(r"\begin{frame}[t]{" + title + "}\n" + body + "\n" + source(module, lesson) + "\n\\end{frame}\n")
    counts = []
    for scale in SCALES:
        a = audit.loc[audit.scale.eq(scale)].set_index("sample")
        counts.append([LABELS[scale], f"{int(a.loc['train','n']):,}".replace(",", "."),
                       f"{int(a.loc['test','n']):,}".replace(",", ".")])
    body = r"\tagline{Previsibilidade linear do WIN em seis escalas temporais}" + "\n"
    body += r"\begin{columns}[T]\begin{column}{0.48\textwidth}" + "\n"
    body += r"\textbf{Pergunta:} agregar minutos em horas melhora a previsão dos retornos?\medskip\par" + "\n"
    body += r"Treino: \textbf{2024}, 246 pregões.\par Teste: \textbf{2025}, 221 pregões.\medskip\par" + "\n"
    body += r"Janela comum: 09:05--18:05.\par Retornos logarítmicos em \%.\medskip\par" + "\n"
    body += r"\alert{Não criamos retorno overnight.}\par Os lags e estados \textbf{continuam} entre pregões, em tempo de negociação." + "\n"
    body += r"\par\medskip\scriptsize\href{" + DATASET_URL + r"}{Fonte: BTG Alpha Lab | BTG-ATS-A26}\par "
    body += r"Candles de negócios B3. Contrato de maior volume do próprio dia: seleção retrospectiva."
    body += r"\end{column}\begin{column}{0.47\textwidth}\centering\scriptsize" + "\n"
    body += table(["Escala", "$n$ treino", "$n$ teste"], counts)
    body += r"\smallskip\scriptsize 02/01--30/12/2024; 02/01--28/11/2025.\par Diário: abertura--fechamento da janela.\par "
    body += r"\includegraphics[width=\textwidth,height=2.05cm,keepaspectratio]{figures/08_monthly_mean_5min.pdf}\par "
    body += r"\tiny Média dos retornos de 5 min, não retorno mensal acumulado.\end{column}\end{columns}"
    frame("Dois anos, seis escalas, uma regra temporal", body, "trading_time_data.py", "Dados e protocolo de análise")

    from .series_overview import FIGURE_NAME, make_series_overview
    series_figure = out / "figures" / FIGURE_NAME
    if not series_figure.is_file():
        make_series_overview(out)
    body = r"\tagline{02/01/2024 a 28/11/2025. Retornos logarítmicos sem overnight}" + "\n"
    body += r"\centering\includegraphics[width=0.98\textwidth,height=5.3cm,keepaspectratio]{figures/" + FIGURE_NAME + r"}\par\smallskip "
    body += r"\scriptsize Eixo horizontal: calendário. Eixos verticais próprios por escala. Todos os retornos, sem suavização."
    frame("Séries completas de retornos", body, "series_overview.py", "Inspeção visual | Mesmas séries usadas na análise")

    # Plot names are a stable interface of forecast_figures.make_figures.
    figure_dir = out / "figures"
    acf_candidates = sorted(figure_dir.glob("01b_return_acf_pacf_slide.pdf")) + sorted(figure_dir.glob("01_return_acf_pacf.pdf"))
    if not acf_candidates:
        acf_candidates = sorted(figure_dir.glob("01*.pdf"))
    if acf_candidates:
        relative = acf_candidates[0].relative_to(out).as_posix()
        body = r"\tagline{Identificação por FAC/FACP na sequência anual de 2024}" + "\n"
        body += r"\centering\includegraphics[width=0.98\textwidth,height=5.0cm,keepaspectratio]{" + relative + r"}\par\smallskip " + "\n"
        body += r"\scriptsize Um lag = uma barra da própria escala, inclusive entre pregões. Bandas pontuais sem ajuste para múltiplas comparações.\par Dispersão e dependência na média são propriedades distintas."
        body += r"\par Desvios-padrão (\%; 1/5/15/30/60 min/diário): " + "; ".join(
            number(desc.loc[desc.scale.eq(scale), "std_pct"].iloc[0]) for scale in SCALES) + "."
    else:
        raise FileNotFoundError("Annual return ACF/PACF figure is required")
    frame("Da descrição às hipóteses de dependência", body, "annual_models.py", "Aulas 2--4 | FAC/FACP convencionais")

    station_rows = []
    for scale in SCALES:
        test = station.loc[station.scale.eq(scale) & station.specification.eq("main")].set_index("test")
        station_rows.append([LABELS[scale], f"{int(test.loc['ADF', 'n']):,}".replace(",", "."),
                             pformat(test.loc["ADF", "pvalue"]), pformat(test.loc["PP", "pvalue"]),
                             pformat(test.loc["KPSS", "pvalue"]),
                             "/".join(str(int(test.loc[t, "lags"])) for t in ["ADF", "PP", "KPSS"])])
    body = r"\tagline{ADF, PP e KPSS em 2024. Decisões a 5\% de significância}" + "\n"
    body += r"\centering\small" + table(["Escala", "$n$", "$p$ ADF", "$p$ PP", "$p$ KPSS", "Lags/bw*"], station_rows)
    main_station = station.loc[station.specification.eq("main")]
    unit_root_reject = main_station.loc[main_station.test.isin(["ADF", "PP"]), "reject_5pct"].mean()
    level_not_reject = 1 - main_station.loc[main_station.test.eq("KPSS"), "reject_5pct"].mean()
    body += r"\raggedright\medskip\small\textbf{ADF e PP:} $H_0$ = raiz unitária.\par "
    body += r"\textbf{Rejeitam raiz unitária em " + number(100 * unit_root_reject, 0) + r"\% das escalas.}\par\smallskip "
    body += r"\textbf{KPSS com constante:} $H_0$ = estacionariedade em nível.\par "
    body += r"\textbf{Não rejeita estacionariedade em " + number(100 * level_not_reject, 0) + r"\% das escalas.}\par\smallskip "
    trend_kpss = station.loc[station.test.eq("KPSS") & station.specification.eq("trend_sensitivity")]
    trend_reject_pct = number(100 * trend_kpss.reject_5pct.mean(), 0)
    body += r"\scriptsize\alert{KPSS com tendência: rejeita estacionariedade em torno de tendência em " + trend_reject_pct + r"\% das escalas.}\par "
    body += r"Não rejeitar $H_0$ não a confirma. A variância condicional pode oscilar.\par\smallskip "
    body += r"*Tabela: constante. Ordem ADF/PP/KPSS. bw = defasagens na variância de longo prazo.\par "
    body += r"Amostra horária: 2.214 observações em 246 pregões, numa sequência anual."
    frame("Estacionariedade: uma série anual por escala", body, "annual_models.py", "Aula 5 | Estatísticas e valores críticos nas tabelas completas")

    model_rows = []
    for scale in SCALES:
        s, d = main_models.loc[scale], principal.loc[scale]
        ar = selected.loc[selected.scale.eq(scale) & selected.model.eq("AR_BIC")].iloc[0]
        ma = selected.loc[selected.scale.eq(scale) & selected.model.eq("MA_BIC")].iloc[0]
        model_rows.append([LABELS[scale], f"({int(s.p)},{int(s.q)})", f"AR({int(ar.p)}) / MA({int(ma.q)})",
                           pformat(d.lb_pvalue), hypothesis_decision(d.lb_pvalue),
                           pformat(d.arch_lm_pvalue), hypothesis_decision(d.arch_lm_pvalue)])
    body = r"\tagline{Resíduos do ARMA escolhido em 2024. Decisões sobre $H_0$ a 5\%}" + "\n"
    body += r"\centering\small\setlength{\tabcolsep}{3.5pt}" + table(
        ["Escala", "ARMA BIC", "Alternativos", "$p$ LB", "Decisão $H_0$", "$p$ ARCH--LM", "Decisão $H_0$"],
        model_rows, alignment="lccrcrc")
    body += r"\raggedright\medskip\small\textbf{Ljung--Box (LB):} $H_0$ = ausência de autocorrelação residual até $h$.\par "
    body += r"\textbf{ARCH--LM:} $H_0$ = ausência de efeitos ARCH até 12 defasagens.\par\smallskip "
    body += r"\scriptsize Rejeitar $H_0$ indica autocorrelação (LB) ou efeitos ARCH (ARCH--LM).\par "
    grid = read("arma_grid")
    minute_grid = grid.loc[grid.scale.eq("1min") & grid.status.eq("eligible")]
    zero_bic = float(minute_grid.loc[minute_grid.p.eq(0) & minute_grid.q.eq(0), "bic"].iloc[0])
    delta_bic = zero_bic - float(main_models.loc["1min", "bic"])
    body += r"\smallskip\scriptsize Minuto: vantagem de apenas $\Delta BIC=" + number(delta_bic, 2) + r"$ sobre (0,0), com autocorrelação residual.\par "
    body += r"5 min: LB não rejeita em 24 lags, mas rejeita em 10, 12 e 20.\par\smallskip "
    body += r"Grade $p,q=0,\ldots,5$, média e variância contadas no BIC. Diagnósticos assintóticos aproximados sob heteroscedasticidade.\par LB usa $h-p-q-1$ (Aula 4). $h=60$ em 1 min, 24 nas demais intradiárias, 20 no diário."
    frame("Seleção por BIC e diagnóstico dos resíduos", body, "annual_models.py", "Aulas 3--4 | Box--Jenkins e alternativas lineares")

    var_rows = []
    for scale in SCALES:
        v = var_selected.loc[scale]
        constant = variances.loc[variances.scale.eq(scale) & variances.model.eq("constant")].iloc[0]
        variance_diag = vard.loc[vard.scale.eq(scale) & vard.model.eq(v.model)
                                 & vard.test.eq("Ljung-Box") & vard.series.eq("squared_standardized_residuals")]
        pv = variance_diag.sort_values("lag").iloc[-1].pvalue if len(variance_diag) else np.nan
        ratio = v.oos_variance_proxy_mse / constant.oos_variance_proxy_mse
        label = "Constante" if v.model == "constant" else v.model_label
        var_rows.append([LABELS[scale], tex(label), number(v.persistence), pformat(pv),
                         hypothesis_decision(pv), number(ratio)])
    body = r"\tagline{Aula 6: constante, ARCH(1) e GARCH(1,1), escolhidos apenas em 2024}" + "\n"
    body += r"\centering\small" + table(["Escala", "Variância BIC", "$\\alpha+\\beta$", "$p$ Q($z^2$)*", "Decisão $H_0$", "MSE/const.*"], var_rows, alignment="lcrrcr")
    body += r"\raggedright\medskip\small\textbf{Ljung--Box em $z^2$:} $H_0$ = ausência de autocorrelação nos resíduos\par padronizados ao quadrado até $h$. Decisões a 5\%.\par\smallskip "
    body += r"Estimação \textbf{sequencial}. A previsão pontual do retorno \textbf{não muda}.\par\smallskip "
    body += r"\scriptsize *Q($z^2$): $h=60$ em 1 min, 24 nas demais intradiárias, 20 no diário. Referência assintótica aproximada após estimação, sem ajuste de graus de liberdade.\par "
    body += r"MSE em 2025 contra inovação ao quadrado: proxy ruidosa, não variância observada.\par Rejeitar $H_0$ indica dependência remanescente em $z^2$. BIC é condicional à média fixa."
    frame("Previsão e diagnóstico da variância", body, "conditional_volatility.py", "Aula 6 | Estabilidade, persistência e diagnóstico")

    accuracy_rows = []
    for scale in SCALES:
        evaluation = "native" if scale == "1d" else "common_60min"
        a = accuracy.loc[accuracy.scale.eq(scale) & accuracy.evaluation.eq(evaluation) & accuracy.group_type.eq("all")].set_index("model")
        d = dm.loc[dm.scale.eq(scale) & dm.evaluation.eq(evaluation) & dm.loss.eq("squared")
                   & dm.variant.eq("principal_serial_dependence")].iloc[0]
        accuracy_rows.append([LABELS[scale] + ("*" if scale == "1d" else ""),
                              number(a.loc["ARMA_BIC", "mse_ratio_vs_zero"], 4),
                              number(a.loc["AR_BIC", "mse_ratio_vs_zero"], 4),
                              number(a.loc["MA_BIC", "mse_ratio_vs_zero"], 4),
                              number(a.loc["AR_MA_50_50", "mse_ratio_vs_zero"], 4),
                              pformat(d.p_value)])
    body = r"\tagline{Parâmetros fixos de 2024, somente informação passada em cada origem}" + "\n"
    body += r"\centering\small" + table(["Escala", "ARMA", "AR", "MA", "50/50", "$p$ DM"], accuracy_rows)
    body += r"\raggedright\medskip\small \textbf{MSE do modelo / MSE do retorno zero: menor que 1 é melhor.}\par "
    target_count = f"{int(alignment.targets.iloc[0]):,}".replace(",", ".")
    body += tex(f"Intradiário: {target_count} alvos idênticos de 60 minutos, sem sobreposição.") + r"\par"
    body += r"\scriptsize *Diário prevê sua janela open-to-close: alvo diferente, não entra no ranking intradiário.\par DM compara apenas AR versus MA, não ARMA versus zero. Referência aproximada; p-valores sem ajuste de multiplicidade. Perdas absolutas e horizonte nativo estão no relatório."
    frame("A comparação justa usa o mesmo alvo futuro", body, "forecast_evaluation.py", "Aula 4 | MSE, MAE, combinação e Diebold--Mariano")

    common = main_accuracy.loc[main_accuracy.evaluation.eq("common_60min")].set_index("scale")
    hour = float(common.loc["60min", "mse_ratio_vs_zero"])
    minute = float(common.loc["1min", "mse_ratio_vs_zero"])
    body = r"\tagline{A hipótese de maior previsibilidade horária não recebeu suporte neste desenho}" + "\n"
    body += r"\small\textbf{Evidência:} ARMA no alvo comum tem " + number(100*(minute-1), 3) + r"\% (1 min) e " + number(100*(hour-1), 3) + r"\% (60 min) mais MSE que zero. Diferença descritiva; DM compara AR com MA.\par\medskip"
    body += r"\begin{columns}[T]\begin{column}{0.50\textwidth}\small"
    subgroup = accuracy.loc[accuracy.scale.eq("60min") & accuracy.evaluation.eq("common_60min")
                            & accuracy.model.eq("ARMA_BIC")]
    group_rows = []
    for group_type, group, label in [("time_band", "inicio", "Início"), ("time_band", "meio", "Meio"),
                                      ("time_band", "fim", "Fim"), ("gap_group", "high", "Gap alto"),
                                      ("gap_group", "low", "Gap baixo")]:
        row = subgroup.loc[subgroup.group_type.eq(group_type) & subgroup.group.eq(group)].iloc[0]
        group_rows.append([label, str(int(row.n)), number(row.mse_ratio_vs_zero, 4)])
    body += r"\textbf{ARMA de 60 min em 2025}\par\smallskip" + table(["Recorte", "$n$", "MSE/zero"], group_rows)
    body += r"\scriptsize Início: 09:05--10:05; meio: até 17:05; fim: até 18:05. Todas as escalas no relatório.\par Grupos não são aditivos; gaps indisponíveis excluídos desse recorte."
    body += r"\end{column}\begin{column}{0.46\textwidth}\small"
    body += r"\textbf{Força:} mesmos alvos e parâmetros fixados antes do teste.\par\smallskip "
    body += r"\textbf{Limites:} contrato escolhido por volume diário e dias completos são seleções retrospectivas.\par\smallskip "
    body += r"\alert{Leilões: mecanismos plausíveis, sem identificação causal.}\par\smallskip "
    body += r"\scriptsize Overnight fora do alvo, mas lags continuam. Sem flags de fase; horários históricos incompletos.\par\smallskip "
    body += r"Dependência da variância não garante direção previsível. Resultado restrito a este ativo, janela e modelos; não prova eficiência de mercado ou lucro após custos."
    body += r"\end{column}\end{columns}\medskip\scriptsize"
    body += r"\href{" + REPO + r"/blob/main/results/entrega_21_09/RELATORIO_21_09.md}{Relatório, análises por faixa/gap e resultados completos}" + "\n"
    frame("Conclusão: alcance dos resultados e da metodologia", body, "forecast_pipeline.py", "Síntese dos resultados | Evidência, adequação e utilidade econômica são distintas")
    path = out / "ENTREGA_21_09.tex"
    path.write_text(preamble + cover_frame(code_base) + "\n".join(slides)
                    + back_cover_frame(code_base) + "\n\\end{document}\n", encoding="utf-8")
    for _ in range(2):
        result = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", path.name],
                                cwd=out, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError("LaTeX compilation failed:\n" + result.stdout[-6000:])
    metadata["presentation_format"] = PRESENTATION_FORMAT
    metadata["presentation"] = {
        "title": STUDY_TITLE, "course_name": COURSE_NAME, "course_code": COURSE_CODE,
        "author": AUTHOR, "professor": PROFESSOR,
        "pdf_pages": len(slides) + 2, "numbered_content_slides": len(slides), "unnumbered_covers": 2,
        "talk_minutes": 5, "code_ref": code_ref,
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "series_generator_sha256": hashlib.sha256(Path(__file__).with_name("series_overview.py").read_bytes()).hexdigest(),
        "series_figure_sha256": hashlib.sha256(series_figure.read_bytes()).hexdigest(),
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out / "analysis_summary.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return out / "ENTREGA_21_09.pdf"


def write_report(output, code_ref="main"):
    from .forecast_figures import make_figures
    from .forecast_narrative import write_narrative
    out = Path(output)
    manifest = out / "analysis_summary.json"
    metadata = json.loads(manifest.read_text(encoding="utf-8"))
    module_dir = Path(__file__).resolve().parent
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
              for path in module_dir.glob("*.py")}
    scientific_modules = ["data.py", "multiscale.py", "trading_time_data.py", "annual_models.py",
                          "forecast_evaluation.py", "conditional_volatility.py", "forecast_pipeline.py"]
    for name in scientific_modules:
        if metadata["code_sha256"].get(name) != hashes[name]:
            raise ValueError(f"Scientific source {name} changed after analysis; rerun before reporting")
    metadata.setdefault("analysis_code_ref", metadata.get("code_ref"))
    metadata.update(code_ref=code_ref, code_sha256=hashes,
                    report_created_utc=datetime.now(timezone.utc).isoformat(),
                    presentation_format=PRESENTATION_FORMAT)
    metadata["source_documentation"] = {
        "provider": "BTG Alpha Lab / BTG Solutions Data Services",
        "dataset": "BTG-ATS-A26",
        "landing_page": DATASET_URL,
        "readme": "https://dataservices.btgpactualsolutions.com/alphalab/v1/api/alphalab/readme/README-BTG-ATS-A26.md",
        "consulted_on": "2026-09-20",
        "timestamp": "start of one-minute interval, UTC",
        "supplier_contract_selection": "highest traded volume in the same day; ex post",
        "fresh_download_hash_compared": False,
        "operational_caveat": "Causal forecast recursion does not undo ex-post contract and full-day selection",
    }
    metadata["estimation_or_selection_scope"] = "Model orders and fitted parameters; excludes supplier contract selection and complete-session filtering"
    manifest.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    figures = make_figures(out, code_ref=code_ref)
    if (out / "private" / "frames_1min.parquet").is_file():
        from .series_overview import make_series_overview
        make_series_overview(out)
    write_narrative(out, code_ref=code_ref)
    return build_slides(out, code_ref=code_ref, figures=figures)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results/entrega_21_09")
    parser.add_argument("--code-ref", default="main")
    args = parser.parse_args()
    print(write_report(args.output, code_ref=args.code_ref))


if __name__ == "__main__":
    main()
