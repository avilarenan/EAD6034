"""Portuguese cumulative report generated exclusively from public summaries.

No price, individual return, prediction, residual or private cache is read by
this module. Statements about empirical outcomes are generated from the same
CSV tables consumed by the presentation; model winners are never hard-coded.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

import numpy as np
import pandas as pd


REPOSITORY = "https://github.com/avilarenan/EAD6034"
SCALES = ["1min", "5min", "15min", "30min", "60min", "1d"]
SCALE_NAMES = {"1min": "1 min", "5min": "5 min", "15min": "15 min",
               "30min": "30 min", "60min": "60 min", "1d": "1 dia"}
REQUIRED_TABLES = (
    "sequence_audit", "descriptive", "time_band_description", "monthly_description",
    "lag_boundary_description", "return_acf_pacf", "stationarity", "arma_grid",
    "selected_models", "mean_diagnostics", "accuracy", "diebold_mariano",
    "variance_models", "variance_diagnostics", "common_target_alignment",
    "forecast_equivalence", "observed_gap_summary", "observed_source_hours",
)


def _boolean(values: pd.Series) -> pd.Series:
    return values.astype(str).str.lower().eq("true")


def _format(value, column: str = "") -> str:
    if pd.isna(value):
        return "—"
    if isinstance(value, (bool, np.bool_)):
        return "sim" if value else "não"
    if isinstance(value, (float, np.floating, int, np.integer)):
        number = float(value)
        if not np.isfinite(number):
            return "∞" if number > 0 else "—"
        if "pvalue" in column or column == "p_value":
            if number == 0:
                return "< precisão numérica"
            return f"{number:.3e}" if number < .0001 else f"{number:.4f}"
        if column in {"n", "nobs", "nobs_test", "days", "trading_days", "h", "p", "q", "lags", "lag",
                      "df", "reference_df", "parameters", "variance_parameter_count", "targets",
                      "n_pairs", "horizon_bars", "q_requested", "h_loss", "gaps_available",
                      "eligible", "excluded", "candidates", "cross_session_lag1_count", "roll_transitions",
                      "excluded_source_days_between", "unobserved_weekdays_between"}:
            return f"{int(number):,}".replace(",", ".")
        if number == 0:
            return "0"
        if abs(number) < .0001 or abs(number) >= 1e6:
            return f"{number:.5e}"
        return f"{number:.6f}".rstrip("0").rstrip(".")
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(frame: pd.DataFrame, fields: dict[str, str]) -> str:
    if frame.empty:
        return "Não há linhas aplicáveis nesta amostra."
    missing = set(fields).difference(frame.columns)
    if missing:
        raise ValueError(f"Missing public report columns: {sorted(missing)}")
    header = "| " + " | ".join(fields.values()) + " |"
    separator = "| " + " | ".join("---" for _ in fields) + " |"
    lines = [header, separator]
    for row in frame[list(fields)].itertuples(index=False, name=None):
        values = [SCALE_NAMES.get(value, value) if name == "scale" else value
                  for name, value in zip(fields, row)]
        lines.append("| " + " | ".join(_format(value, name) for name, value in zip(fields, values)) + " |")
    return "\n".join(lines)


def _ordered(frame: pd.DataFrame, extra: list[str] | None = None) -> pd.DataFrame:
    out = frame.copy()
    if "scale" in out:
        out["_scale_order"] = out.scale.map({s: i for i, s in enumerate(SCALES)})
        out = out.sort_values(["_scale_order"] + (extra or []), kind="stable").drop(columns="_scale_order")
    return out


def _unit_root_conclusions(tests: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (scale, specification), group in tests.groupby(["scale", "specification"], sort=False):
        good = group.loc[group.status.eq("ok")].set_index("test")
        if not {"ADF", "PP", "KPSS"}.issubset(good.index):
            interpretation = "Teste indisponível; não resumir como decisão conjunta"
        else:
            reject = {name: bool(_boolean(good.loc[[name], "reject_5pct"]).iloc[0])
                      for name in ("ADF", "PP", "KPSS")}
            if reject["ADF"] and reject["PP"] and not reject["KPSS"]:
                interpretation = "Evidência concordante com I(0), sem comprovar estabilidade de toda a distribuição"
            elif not reject["ADF"] and not reject["PP"] and reject["KPSS"]:
                interpretation = "Evidência compatível com raiz unitária nesta especificação"
            else:
                interpretation = "Evidência conflitante ou inconclusiva; investigar sensibilidade, sem impor conclusão"
        rows.append(dict(scale=scale, specification=specification, interpretation=interpretation))
    return _ordered(pd.DataFrame(rows), ["specification"])


def _empirical_summary(data: dict[str, pd.DataFrame]) -> list[str]:
    selected = _ordered(data["selected_models"].loc[data["selected_models"].model.eq("ARMA_BIC")])
    orders = "; ".join(f"{SCALE_NAMES[row.scale]}: ARMA({int(row.p)},{int(row.q)})"
                       for row in selected.itertuples())
    conclusions = [f"Seleção BIC da média em 2024: {orders}."]
    diagnoses = data["mean_diagnostics"]
    principal = diagnoses.loc[diagnoses.model.eq("ARMA_BIC") & _boolean(diagnoses.principal_horizon)]
    rejected = principal.loc[principal.lb_pvalue.lt(.05), "scale"].tolist()
    conclusions.append(
        "Ljung–Box da média, no horizonte diagnóstico principal, rejeita ausência de autocorrelação em: "
        + (", ".join(SCALE_NAMES[s] for s in rejected) if rejected else "nenhuma escala")
        + ". A referência é assintótica e pode ser afetada por heterocedasticidade; não rejeitar não prova ruído independente."
    )
    accuracy = data["accuracy"]
    common = accuracy.loc[accuracy.evaluation.eq("common_60min") & accuracy.group_type.eq("all")]
    for scale in SCALES[:-1]:
        part = common.loc[common.scale.eq(scale)]
        if not part.empty:
            best = part.loc[part.mse.idxmin()]
            ratio = float(best.mse_ratio_vs_zero)
            conclusions.append(
                f"Alvo comum de 60 minutos, série-base {SCALE_NAMES[scale]}: menor MSE descritivo de {best.model}; "
                f"MSE/MSE_zero={ratio:.6f}, ganho={100 * (1 - ratio):+.4f}%. "
                "Esse ranking observado em 2025 não é uma nova seleção para reavaliar no mesmo holdout."
            )
    variance = _ordered(data["variance_models"].loc[_boolean(data["variance_models"].selected_bic)])
    descriptions = "; ".join(f"{SCALE_NAMES[row.scale]}: {row.model_label}" for row in variance.itertuples())
    conclusions.append(f"Seleção BIC condicional da variância em 2024: {descriptions}. A previsão pontual permanece a mesma.")
    constant_scales = selected.loc[selected.p.eq(0) & selected.q.eq(0) & selected.scale.ne("1d"), "scale"].tolist()
    if len(constant_scales) > 1:
        conclusions.append("As previsões ARMA(0,0) no alvo comum coincidem nas escalas "
                           + ", ".join(SCALE_NAMES[s] for s in constant_scales)
                           + ": somar as médias das barras completas produz a mesma média horária. "
                           "Isso decorre da agregação dos mesmos dados, não de confirmações independentes de previsibilidade.")
    return conclusions


def write_narrative(output, code_ref: str = "main") -> None:
    """Write the cumulative report and seven-slide speaker guide, from CSV only."""
    out = Path(output)
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", code_ref):
        raise ValueError("code_ref must be a safe Git commit, tag or branch reference")
    metadata = json.loads((out / "analysis_summary.json").read_text(encoding="utf-8"))
    data = {name: pd.read_csv(out / "tables" / f"{name}.csv") for name in REQUIRED_TABLES}
    if set(data["descriptive"].scale) != set(SCALES):
        raise ValueError("A cumulative report requires results for all six scales")
    if metadata.get("estimation_or_selection_uses_2025") is not False:
        raise ValueError("Cannot publish a report without the training-isolation assertion")
    if metadata.get("common_targets_verified") is not True:
        raise ValueError("Common-target alignment must be verified before reporting")
    base = f"{REPOSITORY}/blob/{code_ref}"
    # Code/docs are pinned to their commit. Result artifacts are committed
    # afterwards, so linking them to the earlier code commit would give 404.
    result_base = f"{REPOSITORY}/blob/main/results/{out.name}"

    def code(module: str, label: str = "Código") -> str:
        return f"[{label}]({base}/src/ead6034/{module}.py)"

    def csv(name: str, label: str | None = None) -> str:
        return f"[{label or name + '.csv'}]({result_base}/tables/{name}.csv)"

    def paragraph(section: str, module: str, body: str) -> str:
        return f"## {section}\n\n{code(module)}.\n\n{body.strip()}"

    audit = _ordered(data["sequence_audit"], ["sample"])
    tests = _ordered(data["stationarity"], ["specification", "test"])
    selected = _ordered(data["selected_models"], ["model"])
    diagnostic = data["mean_diagnostics"]
    principal_diagnostic = _ordered(diagnostic.loc[_boolean(diagnostic.principal_horizon)], ["model"])
    accuracy = data["accuracy"]
    all_accuracy = _ordered(accuracy.loc[accuracy.group_type.eq("all")], ["evaluation", "model"])
    dm = data["diebold_mariano"]
    main_dm = _ordered(dm.loc[dm.variant.eq("principal_serial_dependence")], ["evaluation", "loss"])
    variance = _ordered(data["variance_models"], ["model"])
    volatility_diag = _ordered(data["variance_diagnostics"], ["model", "test", "series", "lag"])
    empirical = _empirical_summary(data)
    audit_hour = audit.loc[audit.scale.eq("60min") & audit["sample"].eq("train")].iloc[0]
    n_hour, n_days = int(audit_hour.n), int(audit_hour.days)
    grid_counts = []
    for scale, group in data["arma_grid"].groupby("scale", sort=False):
        n_eligible = int(group.status.eq("eligible").sum())
        grid_counts.append(dict(scale=scale, candidates=len(group), eligible=n_eligible, excluded=len(group)-n_eligible))
    counts = _ordered(pd.DataFrame(grid_counts))
    equivalence = data["forecast_equivalence"]
    equal = _ordered(equivalence.loc[_boolean(equivalence.equal_within_1e_10)], ["evaluation", "model_a", "model_b"])
    cutoff = metadata.get("absolute_gap_threshold_train")
    cutoff_text = _format(cutoff) if cutoff is not None else "indisponível"

    parts = [
        "# EAD6034 — entrega cumulativa de 21/09/2026\n\n"
        "Renan de Luca Avila · Prof. Leandro Maciel · Seminário final em 28/09/2026 (até 15 minutos).\n\n"
        f"[Repositório]({REPOSITORY}) · [Código desta execução]({base}/src/ead6034/forecast_pipeline.py) · "
        f"[Protocolo pré-especificado]({base}/docs/PROTOCOL_21_09.md).\n\n"
        "Este documento incorpora e revisa as etapas de 31/08 (descrição e FAC/FACP), "
        "14/09 (estacionariedade e Box–Jenkins) e 21/09 (avaliação preditiva e modelos alternativos). "
        "Os artefatos antigos foram preservados como histórico, não corrigidos silenciosamente. "
        "A inferência atual refere-se ao desenho anual de tempo de negociação aprovado pelo autor.",
        "## Síntese calculada dos resultados\n\n" + "\n".join(f"- {item}" for item in empirical),
        paragraph("1. Pergunta, escopo e hipótese", "forecast_pipeline", """
Como a previsibilidade dos retornos do WIN varia entre 1, 5, 15, 30 e 60 minutos e o diário?
A hipótese de maior previsibilidade horária é confrontada com os erros fora da amostra, não usada para escolher vencedores.
Maior suavidade visual, menor ruído e maior capacidade preditiva são propriedades diferentes.
A comparação usa ganhos frente ao benchmark e, quando se comparam escalas, alvos físicos idênticos de 60 minutos.

Este é um estudo multiescala de um futuro de índice, com 5 minutos como referência da proposta.
Não se alegam resultados para outras classes de ativos, segundos, spreads, midquotes ou custos de execução.
A adaptação de Matías e Reboredo (2012) aproveita a questão de previsão intradiária; não reproduz os modelos
não lineares do artigo, pois foram utilizados apenas os métodos das aulas fornecidas.
"""),
        paragraph("2. Dados, revisão amostral e significado de overnight", "trading_time_data", f"""
Retornos são expressos em porcentagem: `100 × log(P_final/P_inicial)`. Janela fixa local de São Paulo:
09:05–18:05, com 540 minutos. O intradiário usa a fronteira inicial no fechamento do candle iniciado às 09:04.
O diário usa abertura às 09:05 e fechamento da janela, portanto não deve ser tratado como soma exatamente
idêntica dos retornos intradiários ancorados no candle anterior. Os alvos comuns intradiários, sim, são reconciliados.

A etapa anterior testava cada sessão isoladamente: **nove barras de uma hora, não nove minutos**.
Agora a sequência horária de treino possui **{n_hour:,} observações em {n_days} pregões**, antes das perdas por defasagens.
O índice continua entre dias, sem acrescentar um retorno que compare fechamento de ontem e abertura de hoje.
A última barra de ontem pode explicar a primeira barra de hoje, embora cada retorno seja calculado inteiramente
dentro do próprio pregão e contrato. Um lag significa a observação anterior, não uma distância constante de relógio.

Essa mudança reduz o problema dos testes com nove observações, mas não prova por si só estacionariedade.
Informação acumulada durante a noite pode afetar a primeira barra; a hipótese é não modelar separadamente a interrupção.
Trocas de contrato e dias ausentes permanecem identificados. A contagem de dias úteis não observados não é um
calendário B3 validado: pode incluir feriados. Não se preenchem lacunas com zeros ou interpolação e não se winsorizam retornos.

{_table(audit, {'scale':'Escala','sample':'Amostra','n':'N','days':'Pregões','start':'Início','end':'Fim','cross_session_lag1_count':'Lags entre sessões','roll_transitions':'Trocas de contrato'})}

2024 é treino; 2025 é teste. A primeira observação de teste pode usar o estado final de 2024, por isso a contagem
de lags entre sessões no teste pode incluir a transição treino–teste. O filtro de pregões completos é uma seleção
retrospectiva de qualidade: as métricas são condicionais à amostra, não uma garantia de disponibilidade operacional.
Auditoria completa: {csv('sequence_audit')}; cobertura: {csv('coverage')}.
"""),
        paragraph("3. Entrega de 31/08 revisada: descrição, FAC e FACP", "annual_models", f"""
As estatísticas e correlações foram recalculadas em 2024 sob a mesma sequência anual utilizada nos testes e modelos.
A FAC usa pares na sequência de observações, inclusive os que atravessam sessões. A FACP usa Yule–Walker com
denominador de máxima verossimilhança (`ywmle`), sem regressões agrupadas por pregão. As bandas pontuais
`±1,96/√N` são referências aproximadas de ruído branco, não bandas simultâneas robustas à heterocedasticidade.

{_table(_ordered(data['descriptive']), {'scale':'Escala','n':'N','mean_pct':'Média (%)','std_pct':'Desvio (%)','skewness':'Assimetria','excess_kurtosis':'Excesso de curtose','zero_share':'Fração zero'})}

FAC/FACP lag 1 (todas as demais defasagens permanecem nas tabelas e figuras):

{_table(_ordered(data['return_acf_pacf'].loc[data['return_acf_pacf'].lag.eq(1)]), {'scale':'Escala','lag':'Lag','acf':'FAC','pacf':'FACP','valid_pairs':'Pares','white_noise_pointwise_band':'Banda pontual'})}

Pares que atravessam sessões são também descritos separadamente; essas correlações não são novos testes nem
constituem evidência causal de overnight:

{_table(_ordered(data['lag_boundary_description'], ['pair_type']), {'scale':'Escala','pair_type':'Pares','n_pairs':'N pares','pair_correlation':'Correlação descritiva'})}

Tabelas completas: {csv('return_acf_pacf')}, {csv('time_band_description')}, {csv('monthly_description')}.
Uma dispersão maior na escala diária não demonstra maior ou menor previsibilidade; o horizonte e a unidade do alvo mudaram.
"""),
        paragraph("4. Entrega de 14/09 revisada: estacionariedade", "annual_models", f"""
ADF e PP: H0 = raiz unitária. KPSS: H0 = estacionariedade em nível (`c`) ou em torno de tendência (`ct`).
`c` é a especificação principal; `ct` é sensibilidade pré-definida, não escolhida retrospectivamente para obter concordância.
ADF seleciona lags por BIC entre 0 e 12, sujeito ao limite amostral; PP usa bandwidth automático Schwert com Bartlett;
KPSS usa seleção automática dependente dos dados, também com Bartlett. Decisões usam o valor crítico de 5%.

{_table(tests, {'scale':'Escala','specification':'Especificação','test':'Teste','trend':'Determinístico','n':'N bruto','nobs':'N efetivo','lags':'Lags/bandwidth','statistic':'Estatística','critical_5':'Crítico 5%','pvalue':'p-valor','reject_5pct':'Rejeita H0 a 5%'})}

Leitura conjunta, sem teste de painel ou combinação de p-valores:

{_table(_unit_root_conclusions(tests), {'scale':'Escala','specification':'Especificação','interpretation':'Leitura'})}

Não rejeitar H0 não demonstra sua verdade. Amostras grandes podem detectar desvios pequenos e não eliminam
quebras, sazonalidade intradiária ou fragilidade de especificação. Resultados conflitantes entre `c` e `ct` são preservados.
P-valores que o software retorna como zero por limite numérico são mostrados como **< precisão numérica**, nunca como probabilidade exatamente nula.
Valores críticos de 1%, 5% e 10%, regras de lag e avisos: {csv('stationarity')}.
"""),
        paragraph("5. Box–Jenkins: identificação, estimação, seleção e diagnóstico", "annual_models", f"""
Grade ARMA(p,q), p,q entre 0 e {int(metadata.get('max_order', 5))}, com constante, usando somente 2024.
A constante da parametrização de `statsmodels.ARIMA` é a média incondicional μ; não é o intercepto da equação AR.
ARMA(0,0) usa a solução gaussiana fechada: média amostral e variância dos resíduos com denominador N.
Para as demais ordens, estimamos numericamente a verossimilhança gaussiana exata com inicialização estacionária
e GLS iterativo para a média. Se a primeira tentativa não converge, a rotina registra uma nova tentativa de
máxima verossimilhança em espaço de estados.
Escalonamento numérico é desfeito nos parâmetros, variância, log-verossimilhança e critérios; raízes e convergência são auditadas.

`BIC = −2 log L + k log N`, com `k = p + q + 2` (média e variância incluídas). Menor BIC vence entre candidatos elegíveis
da mesma escala e amostra. Não se comparam níveis de BIC entre frequências distintas. AIC é complementar.
AR puro positivo e MA puro positivo são selecionados dentro de suas próprias famílias; não substituem o vencedor geral.

{_table(counts, {'scale':'Escala','candidates':'Candidatos','eligible':'Elegíveis','excluded':'Excluídos/falhos'})}

{_table(selected, {'scale':'Escala','model':'Papel','p':'p','q':'q','parameters':'k','mu_pct':'μ (%)','sigma_pct':'σ (%)','llf':'log L','aic':'AIC','bic':'BIC','delta_bic':'ΔBIC geral'})}

Uma seleção ARMA(0,0) significa que, na grade examinada, o ganho de ajuste não compensou a penalidade por parâmetros;
não é uma prova de independência, inexistência de padrões ou impossibilidade de previsão por qualquer método.
Toda a grade, inclusive falhas, está em {csv('arma_grid')}; parâmetros e raízes em {csv('selected_models')}.

Diagnósticos nos horizontes principais pré-definidos (60 lags no minuto; 24 nas demais escalas intradiárias; 20 no diário):

{_table(principal_diagnostic, {'scale':'Escala','model':'Modelo','h':'h','df':'gl da aula','lb_stat':'Q resíduos','lb_pvalue':'p Q','lb_squared_pvalue':'p Q quadrados','arch_lags':'Lags ARCH','arch_lm_pvalue':'p ARCH-LM','jb_pvalue':'p normalidade'})}

Ljung–Box da média segue `gl = h − p − q − 1`, contando a constante, conforme a Aula 4. A referência usual do software
com `h − p − q` também é exportada. Em quadrados usa-se `gl=h`, como diagnóstico de dependência de segundo momento.
O cálculo por FAC-FFT e `q_stat` é numericamente equivalente ao Q convencional; não há correção por fronteiras ou bootstrap.
Referências assintóticas podem ser afetadas por heterocedasticidade; critérios de informação e diagnóstico respondem
a perguntas diferentes. Não promovemos modelos pela ausência de rejeição num horizonte escolhido depois de ver os resultados.
Todos os horizontes: {csv('mean_diagnostics')}; {csv('residual_acf_pacf')}; {csv('squared_residual_acf')}.
"""),
        paragraph("6. Aula 6: ARCH/GARCH e previsão da variância", "conditional_volatility", f"""
Sequência da Aula 6, pp. 17–20: estimar a média ARMA, examinar quadrados dos resíduos, aplicar ARCH-LM, estimar variância
e diagnosticar resíduos padronizados. Comparamos variância constante, ARCH(1) e GARCH(1,1) normais sobre as mesmas inovações.

`h_t = ω + α ε²_(t−1) + β h_(t−1)`; ARCH(1) tem β=0. Exigimos convergência, ω>0, α≥0, β≥0 e
`α+β < 1−10⁻⁸`. Persistência ≥0,98 gera aviso. Não se confundem convergência numérica, positividade e adequação dos resíduos.

A estimação é **sequencial, não máxima verossimilhança conjunta ARMA–GARCH**. A média ARMA não é reestimada.
AIC/BIC contam somente os parâmetros de variância (1, 2 ou 3) e comparam candidatos condicionais à mesma média;
não são diretamente comparáveis com a log-verossimilhança ou BIC do ARMA original.

{_table(variance, {'scale':'Escala','model_label':'Variância','omega':'ω','alpha':'α','beta':'β','persistence':'α+β','bic':'BIC condicional','eligible':'Elegível','selected_bic':'Escolhido','near_boundary':'Próximo da fronteira'})}

Na avaliação de 2025, o estado é carregado do treino e continua entre pregões. `h_t` utiliza somente a inovação
efetivamente observada em t−1, nunca o erro de t. A normalização numérica usa o RMS de treino e inclui o Jacobiano
na transformação da log-verossimilhança. O teste não escolhe modelos nem seus parâmetros.

Avaliação contra **a mesma inovação quadrada da média ARMA fixa**, proxy ruidosa e não variância condicional observada:

{_table(variance, {'scale':'Escala','model_label':'Modelo','nobs_test':'N teste','oos_variance_proxy_mse':'MSE proxy (p.p.)⁴','oos_variance_proxy_mae':'MAE proxy (p.p.)²','status':'Estado'})}

Melhorar essa proxy não equivale a melhorar o retorno previsto: **todas as especificações de variância compartilham
exatamente as mesmas previsões pontuais**. Não se aplica DM às especificações aninhadas de variância.
Ljung–Box de `z=ε/√h` e `z²` usa referência assintótica χ²(h), sem subtração ad hoc de parâmetros GARCH; a calibração
é aproximada após estimação sequencial. A tabela completa de ARCH-LM e Q está no apêndice e em {csv('variance_diagnostics')}.
"""),
        paragraph("7. Entrega de 21/09: protocolo de previsão fora da amostra", "forecast_evaluation", f"""
Ordens e parâmetros são fixados em 2024; 2025 entra somente na avaliação e na atualização causal dos estados,
defasagens e variâncias já definidos. Filtro não é suavizador: uma observação futura não pode alterar uma previsão anterior.
Na previsão multipasso, todos os passos partem da mesma origem sem inserir realizações intermediárias futuras.

Modelos: `ARMA_BIC`, `AR_BIC`, `MA_BIC`, combinação pré-fixada `AR_MA_50_50`, retorno zero `ZERO` e média de treino `TRAIN_MEAN`.
O diário prevê o retorno da próxima janela diária; não seu preço ou overnight.

- **Nativo:** uma barra à frente em cada escala. O horizonte físico muda entre frequências: os MSE brutos não servem para ranquear escalas.
- **Comum de 60 minutos:** nove origens não sobrepostas por pregão, 09:05, 10:05, …, 17:05. Alvos não atravessam a noite.
  Cada escala prevê o mesmo retorno horário, somando apenas previsões emitidas na mesma origem.
- MSE, MAE, RMSE e razão MSE/MSE_zero são calculados sobre origens e máscaras comuns. Razão <1 é melhora; >1 é piora.
  MAPE não é usado em retornos próximos de zero. Não há otimização de pesos com o teste.

Verificação automática dos alvos realizados e das origens após a máscara de previsões finitas:

{_table(_ordered(data['common_target_alignment']), {'scale':'Escala-base','targets':'Alvos','identical_origins':'Origens iguais','max_target_reconciliation_error_pct':'Erro máximo (%)','tolerance_pct':'Tolerância (%)'})}

Previsões que coincidem numericamente (tolerância absoluta 10⁻¹⁰) não representam evidências independentes:

{_table(equal, {'scale':'Escala','evaluation':'Exercício','model_a':'Modelo A','model_b':'Modelo B','max_abs_difference':'Diferença máxima'})}

Sem otimização ex post: o menor MSE observado em 2025 é um ranking descritivo, não um modelo novamente selecionado e testado na mesma amostra.
"""),
        paragraph("8. Acurácia: todas as escalas e comparadores", "forecast_evaluation", f"""
Erros de retorno estão em pontos percentuais; MSE em (p.p.)²; MAE/RMSE em p.p.; a razão com o modelo zero é adimensional.
O sinal do ganho é `1 − MSE/MSE_zero`. Comparar previsibilidade entre escalas requer o bloco de alvos comuns,
e não apenas que uma escala tenha retornos numericamente menores.

{_table(all_accuracy, {'scale':'Escala','evaluation':'Exercício','model':'Modelo','n':'N','mse':'MSE','mae':'MAE','rmse':'RMSE','mse_ratio_vs_zero':'MSE/MSE zero','mse_gain_vs_zero':'Ganho fracionário'})}

Tabela completa, inclusive faixas e grupos de gaps: {csv('accuracy')}.
"""),
        paragraph("9. Comparação Diebold–Mariano", "forecast_evaluation", f"""
Comparação pré-especificada: AR puro positivo × MA puro positivo, selecionados em 2024. São famílias não aninhadas,
mas podem degenerar em previsões ou perdas idênticas. O teste não é aplicado ao ARMA geral contra sua extensão GARCH
e não demonstra superioridade dos comparadores frente ao vencedor geral da grade.

`d_t = perda_AR − perda_MA`: estatística negativa favorece AR. Perda quadrática é principal; absoluta, complementar.
A variância de longo prazo segue a soma retangular de autocovariâncias da Aula 4; há correção de pequena amostra
e referência t com N−1 graus de liberdade. No nativo, q cobre uma hora em barras; no comum60 e diário, q=1.
q=0 é sensibilidade exportada. Os alvos da sequência de perdas não se sobrepõem, portanto `h_perda=1`, distinto
do número de barras necessário para prever 60 minutos em cada escala.

{_table(main_dm, {'scale':'Escala','evaluation':'Exercício','loss':'Perda','n':'N','q':'q covariâncias','horizon_bars':'Horizonte em barras','h_loss':'h perdas','mean_loss_difference':'Diferença média AR−MA','statistic':'DM corrigido','p_value':'p-valor','status':'Estado'})}

Perdas iguais, variância de longo prazo não positiva ou degenerada impedem p-valor, em vez de produzir significância artificial.
A inferência é aproximada, pressupõe comportamento adequado da sequência de perdas e não é robusta a toda forma
de não estacionariedade. Os vários testes não têm correção de multiplicidade e devem ser lidos conjuntamente com
magnitudes de erro, horizonte e diagnóstico. Não criamos testes adicionais fora do material da disciplina.
Todas as sensibilidades: {csv('diebold_mariano')}.
"""),
        paragraph("10. Faixas do pregão, gaps e limites sobre leilões", "trading_time_data", f"""
As faixas são físicas e iguais entre escalas: início 09:05–10:05; meio 10:05–17:05; fim 17:05–18:05.
Uma hora de minuto é comparada com uma hora de barras maiores, não a primeira barra de qualquer duração.
O diário não tem uma decomposição intradiária artificial. Descrição de 2024:

{_table(_ordered(data['time_band_description'], ['time_band']), {'scale':'Escala','time_band':'Faixa','n':'N','mean_pct':'Média (%)','std_pct':'Desvio (%)','excess_kurtosis':'Excesso curtose'})}

Gap auxiliar: primeiro open observado do dia / último close observado da sessão anterior, somente no mesmo contrato
e sem lacuna de dias úteis suspeita. É chamado **gap entre sessões observadas**, não retorno overnight oficial nem preço certificado de leilão.
O limiar entre menor/maior magnitude é a mediana de |gap| nos pregões incluídos de 2024: **{cutoff_text}%**;
o mesmo limiar é aplicado a 2025. Ausência de calendário completo pode excluir conservadoramente feriados.

{_table(data['observed_gap_summary'], {'sample':'Amostra','gap_group':'Grupo','days':'Dias','gaps_available':'Gaps disponíveis','gap_mean_pct':'Gap médio (%)','gap_std_pct':'Desvio gap (%)'})}

Comparações por grupo são decomposições **ex post** de erros já produzidos, não preditores retroativamente disponíveis.
Um gap observado somente depois da abertura não entra numa previsão emitida antes dela.
As tabelas do apêndice apresentam ARMA selecionado e benchmark zero; os demais modelos permanecem em {csv('accuracy')}.

Os candles não trazem fase de negociação. Nos horários históricos efetivamente documentados, a janela principal
não cobre os calls próprios de abertura/fechamento do WIN. Pode cobrir o entorno de eventos das ações subjacentes,
em horários que mudam por regime. O período intermediário não é necessariamente afastado de todos os eventos de mercado.
A cronologia de ofícios e exceções de 2024–2025 é incompleta; não se extrapola a grade atual para toda a amostra.

Fontes B3, datas de vigência, diferenças entre ajuste e call, e lacunas:
[auditoria histórica de horários]({base}/docs/market_hours_2024_2025.md).
Primeiros e últimos horários efetivamente observados no feed: {csv('observed_source_hours')}.
Essas evidências não identificam efeito causal de leilões, não demonstram que os efeitos overnight desapareceram
e não permitem atribuir toda diferença entre frequências à microestrutura.
"""),
        paragraph("11. Conclusão e limites do que foi demonstrado", "forecast_pipeline", "\n\n".join(
            empirical + [
                "Estacionariedade, ausência de autocorrelação linear residual, ajuste dentro da amostra e capacidade preditiva fora da amostra são propriedades distintas.",
                "A comparação multiescala precisa separar horizonte e frequência de observação. Maior previsibilidade horária não foi incorporada como premissa nem garantida pela agregação.",
                "A validade externa está limitada a um ativo, uma janela, um ano de estimação e ao trecho disponível de 2025, condicionados ao filtro de qualidade. Não há simulação de P&L, custos, impacto de mercado ou recomendação de operação.",
                "Os modelos são convencionais e as referências inferenciais são aproximadas. Heterocedasticidade, sazonalidade intradiária, quebras e calendários incompletos restringem as conclusões. Os métodos das aulas foram mantidos sem bootstrap, testes de painel, redes neurais ou modelos adicionais de regime.",
            ])),
        paragraph("12. Reprodutibilidade, versões e publicação", "forecast_pipeline", f"""
O comando abaixo pressupõe acesso autorizado ao ZIP original. Dados brutos, preços, retornos, previsões individuais,
resíduos e caches de ajuste ficam em `private/` e não são publicados. Este relatório usa somente CSV agregados públicos.
O código não baixa nem substitui os dados por uma série simulada. Parâmetros não são reestimados no holdout.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock-21-09.txt
OPENBLAS_NUM_THREADS=1 python scripts/run_entrega_21_09.py \\
  --input /caminho/autorizado/BTG-ATS-A26.zip \\
  --output results/entrega_21_09 --workers 3 --code-ref {code_ref}
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v
```

No Windows, a ativação e definição de variáveis de ambiente devem usar a sintaxe equivalente do shell.
O arquivo de dependências travadas descreve a execução entregue; `requirements.txt`/`pyproject.toml` descrevem os requisitos gerais.
Para compilar a apresentação PDF, é necessário instalar separadamente uma distribuição LaTeX com `pdflatex`,
classe Beamer e fontes Latin Modern (`lmodern`). Esses componentes não são instalados pelo pip.
A opção `--skip-report` permite executar a análise numérica e exportar suas tabelas sem depender de LaTeX;
nessa modalidade a apresentação e os relatórios não são gerados automaticamente.
Python registrado: **{metadata.get('python', 'não informado')}**. Versões numéricas:

{_table(pd.DataFrame([{'package': key, 'version': value} for key, value in metadata.get('versions', {}).items()]), {'package':'Pacote','version':'Versão'})}

Manifesto com hashes do código, fonte, parâmetros do protocolo e asserções de isolamento:
[analysis_summary.json]({result_base}/analysis_summary.json). Referência de código dos links: `{code_ref}`.
Fonte deste relatório: {code('forecast_narrative')}. Alterações de lógica invalidam os checkpoints pertinentes.
Testes automatizados exercitam isolamento de 2024, contaminação artificial do futuro, igualdade de alvos horários,
recursão de variância, Jacobiano, identidade de Q e cálculo de DM; verificar o registro de execução para a contagem efetiva.
"""),
        "## Referências e vinculação às aulas\n\n"
        "- Maciel, Leandro. EAD6034, Aulas 3 e 4: identificação, máxima verossimilhança, AIC/BIC, Box–Jenkins, diagnóstico e avaliação de previsões; materiais fornecidos pelo aluno.\n"
        "- Maciel, Leandro. Aula 5: ADF, Phillips–Perron e KPSS, hipóteses e especificações determinísticas.\n"
        "- Maciel, Leandro. Aula 6: ARCH/GARCH e estabilidade (pp. 9–16), FAC dos quadrados e ARCH-LM (pp. 17–18), diagnóstico e sequência metodológica (pp. 19–20), integração ARMA–GARCH (p. 28).\n"
        "- Matías, J. M.; Reboredo, J. C. (2012). Forecasting performance of nonlinear models for intraday stock returns. "
        "*Journal of Forecasting*, 31(2), 172–188. [DOI](https://doi.org/10.1002/for.1218). Referência de motivação, não reprodução dos modelos não lineares.\n"
        f"- B3. Ofícios e grades históricas discriminados na [auditoria de horários]({base}/docs/market_hours_2024_2025.md).\n"
        f"- [Enunciado/protocolo operacional consolidado]({base}/docs/PROTOCOL_21_09.md): entregas de 31/08, 14/09 e 21/09; seminário de 28/09.",
        "## Apêndice A — diagnóstico completo da variância\n\n"
        + code("conditional_volatility") + ".\n\n"
        + _table(volatility_diag, {'scale':'Escala','model':'Modelo','series':'Série','test':'Teste','lag':'Lag','statistic':'Estatística','reference_df':'gl','pvalue':'p-valor','reject_5pct':'Rejeita 5%'}),
        "## Apêndice B — acurácia por faixa e grupo de gap\n\n"
        + code("forecast_evaluation") + ".\n\n"
        + "ARMA selecionado e benchmark zero são exibidos abaixo; a tabela pública de acurácia contém todos os comparadores. "
        "As decomposições são exploratórias, sem testes adicionais nem alteração de especificações.\n\n"
        + _table(_ordered(accuracy.loc[accuracy.group_type.ne("all") & accuracy.model.isin(["ARMA_BIC", "ZERO"])],
                          ["evaluation", "group_type", "group", "model"]),
                 {'scale':'Escala','evaluation':'Exercício','group_type':'Tipo','group':'Grupo','model':'Modelo','n':'N','mse':'MSE','mae':'MAE','mse_ratio_vs_zero':'MSE/MSE zero'}),
    ]
    report = "\n\n".join(parts) + "\n"

    guide = f"""# Guia de apresentação — EAD6034, entrega cumulativa de 21/09

Renan de Luca Avila · Seminário final 28/09/2026 · sete slides, roteiro de aproximadamente 13 minutos, até 15 minutos no total.
[Código e resultados]({REPOSITORY}) · [Relatório técnico]({result_base}/RELATORIO_21_09.md).
Este guia não introduz métodos ou resultados diferentes dos CSV públicos.

## Roteiro cumulativo

| Slide | Tempo | Mensagem e orientação de fala |
| --- | --- | --- |
| 1 — Pergunta, dados e desenho | 1min30 | Estudamos WIN em seis escalas, treino 2024 e teste 2025. Horas mais previsíveis é hipótese, não conclusão. Explicar que retorno não atravessa a noite, mas o lag pode atravessar. |
| 2 — Descrição e FAC/FACP, 31/08 revisada | 1min30 | Mostrar a FAC e a FACP dos retornos, distinguindo correlação total e parcial. Ressaltar que o lag é uma observação e que comparar o mesmo lag não significa comparar o mesmo tempo físico. |
| 3 — Estacionariedade, 14/09 revisada | 2min | Corrigir explicitamente nove barras por dia versus {n_hour} observações anuais na escala horária. Explicar H0 opostas, c principal e ct sensibilidade. Ler as divergências da tabela, não ocultá-las. |
| 4 — Box–Jenkins, 14/09 revisada | 2min | Identificação, estimação, seleção e diagnóstico. Mostrar ordens efetivamente escolhidas e diagnóstico principal. Menor BIC não garante resíduos adequados nem previsão melhor. |
| 5 — ARCH/GARCH, Aula 6 | 1min30 | Variância condicional responde a outra pergunta: examinar a dependência dos quadrados. Estimação sequencial da mesma inovação e mesmas previsões da média. Citar persistência e diagnóstico dos resíduos padronizados. |
| 6 — Previsões e comparação, 21/09 | 2min30 | Explicar origens móveis com parâmetros fixos, alvos comuns de 60 minutos, benchmark zero, combinação 50/50 e DM AR×MA. Separar ganho econômico/descritivo de significância estatística. |
| 7 — Horários, overnight e conclusões | 1min | Distinguir faixas da janela e fases de negociação. Gap observado não é preço oficial de leilão. Ler a conclusão calculada e explicitar limites sem prometer previsibilidade. |

Referências de código para a fala: {code('trading_time_data', 'dados')}; {code('annual_models', 'testes e ARMA')};
{code('conditional_volatility', 'ARCH/GARCH')}; {code('forecast_evaluation', 'previsões e DM')}; {code('forecast_pipeline', 'execução')}.
Os tempos são uma orientação de ensaio, não uma licença para ultrapassar os 15 minutos.

## Cartão de resultados da execução

""" + "\n".join(f"- {item}" for item in empirical) + f"""

Antes de falar, localizar no slide/tabela o valor exato que será mencionado. Não dizer “todas as escalas” se há exceções,
nem “ausência de efeito” apenas porque não houve rejeição. Resultados de 2025 não alteram retrospectivamente a seleção de 2024.

## Perguntas prováveis

### Por que antes n=9 e agora n={n_hour}?

Antes cada pregão era testado separadamente; há nove barras horárias no intervalo de nove horas.
Agora numeramos todas as barras de 2024 em uma sequência cronológica. Não multiplicamos nove artificialmente nem
tiramos média dos testes: mudamos explicitamente a convenção de defasagem e refizemos todos os procedimentos.
A premissa é um modelo em tempo de negociação; isso não transforma amostras grandes em garantia de estacionariedade.
{code('trading_time_data')}; {code('annual_models')}.

### Como ignorar o retorno overnight e permitir um lag entre dias?

O retorno da primeira barra usa preços daquele pregão. Seu preditor pode ser o retorno da última barra de ontem.
Nenhum retorno fechamento–abertura é acrescentado ao alvo. A informação noturna pode afetar hoje e está entre as limitações;
“não modelar separadamente” não significa “demonstrar que não há efeito”. {code('trading_time_data')}.

### BIC significa que ARMA(0,0) é ruído independente?

Não. BIC penaliza parâmetros: −2 log L + k log N. Se ARMA(0,0) vencer, apenas significa que os candidatos mais complexos
não compensaram a penalidade naquela amostra. Autocorrelação residual, dependência dos quadrados e previsão OOS são
avaliadas à parte. A constante prevê a média estimada e pode coincidir com TRAIN_MEAN. {code('annual_models')}.

### ADF e PP rejeitam, mas KPSS pode rejeitar também?

Sim. Suas hipóteses nulas são distintas e especificações podem ser inadequadas. Rejeição simultânea não é licença para
escolher o teste preferido: reportamos conflito e sensibilidade. `c` e `ct` respondem a estacionariedade em nível e em torno
de tendência, respectivamente. Valores numéricos zero de p não são probabilidade matematicamente zero. {code('annual_models')}.

### GARCH melhorou a previsão dos retornos?

Neste desenho GARCH não modifica a previsão da média: modela sua incerteza condicional usando as mesmas inovações.
A variância é estimada depois da média, não por MLE conjunta. Erro quadrado é uma proxy ruidosa da variância, não sua observação
direta. Portanto, uma melhora na métrica dessa proxy não pode ser vendida como melhora na previsão pontual. {code('conditional_volatility')}.

### Por que não comparar diretamente MSE de um minuto com MSE de uma hora?

São alvos com duração e dispersão diferentes. A comparação principal entre escalas prevê os mesmos 60 minutos nas mesmas
origens. Os modelos das barras menores fazem previsão multipasso com uma única origem, sem inserir os retornos que ainda
não ocorreram. O bloco nativo responde à previsão da próxima barra da própria escala. {code('forecast_evaluation')}.

### O DM mostra que o melhor BIC venceu todos os benchmarks?

Não. O DM foi pré-definido para AR positivo versus MA positivo, famílias não aninhadas. Estatística negativa favorece AR.
O teste tem referência aproximada; perdas degeneradas ou variância de longo prazo inválida impedem um p-valor. A comparação
não é automaticamente transferível ao ARMA geral, à combinação ou às variâncias aninhadas. {code('forecast_evaluation')}.

### Como sabemos que os leilões causaram a diferença entre escalas?

Não sabemos com esse desenho. Candles não identificam fase de negociação e a cronologia documental é incompleta.
Os calls próprios do WIN ficam fora da janela nos regimes confirmados; eventos das ações subjacentes podem estar dentro.
Faixas e gaps são associações exploratórias, não identificação causal. Referência:
[auditoria de horários]({base}/docs/market_hours_2024_2025.md); {code('trading_time_data')}.

### Todos os resultados anteriores estão contemplados?

Sim: descrição/FAC/FACP de 31/08, estacionariedade/Box–Jenkins de 14/09 e previsão/modelos alternativos de 21/09.
As etapas anteriores foram recalculadas sob o protocolo anual, sem apagar a versão histórica. Tabelas extensas ficam
no relatório/repositório, mantendo sete slides legíveis e a apresentação dentro de 15 minutos.

## Checklist do ensaio

- Confirmar que cada conclusão oral corresponde à versão entregue dos CSV e ao commit dos links.
- Explicar em 30 segundos o exemplo de retorno intradiário com lag entre pregões.
- Apresentar as duas H0 de raiz unitária e a H0 oposta de KPSS.
- Separar BIC, diagnóstico, previsão da média e previsão da variância.
- Mostrar horizonte comum, benchmark zero e magnitude do ganho antes do p-valor.
- Não chamar começo/fim da janela de “leilão do WIN”.
- Reservar aproximadamente dois minutos do limite para transições/perguntas; ensaiar sete slides em 13 minutos.

Gerador deste guia: {code('forecast_narrative')}.
"""
    (out / "RELATORIO_21_09.md").write_text(report, encoding="utf-8")
    (out / "GUIA_APRESENTACAO.md").write_text(guide, encoding="utf-8")
