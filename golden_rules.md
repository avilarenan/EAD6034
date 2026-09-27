# Golden Rules — EAD6034 (Econometria de Séries Temporais)

Durable principles for every delivery in this course (Seminar I univariate, Seminar II
multivariate, and the weekly checkpoints in between). These are distilled from the
professors' emails, `docs/PROTOCOL_21_09.md`, `CONCLUSAO_CRITICA.md`, `VALIDACAO_21_09.md`,
the TA's feedback on 14/09 and 21/09, the TA's written checklist
(`context_resources/Check-list - séries temporais_7662.pdf`), and the reference paper
(Matías & Reboredo, 2012, *Journal of Forecasting* 31(2), 172–188).

## 1. Scope discipline
Only use methods actually taught in class, or clearly label any deviation as such. Tag
every non-obvious methodological choice as **aula** (taught method), **implementação**
(a defensible operational/numeric choice not spelled out in class), or **esclarecimento
conceitual** (a math clarification, not a new method) — the convention already used in
`questões.md`. Check what's *actually* in the lecture slides/scripts before assuming
something is out of scope: Aula 4's own forecasting checklist names **"ARMA, ETS, MLP,
SVM, Deep Learning"** as example benchmark classes, so a lightweight MLP baseline is a
named Aula-4 benchmark, not a scope violation — `docs/PROTOCOL_21_09.md`'s exclusion of
"redes neurais" was this student's own deliberate narrowing for one weekly checkpoint,
not a professor-mandated ban on the topic. Anything genuinely beyond what any lecture
covers (e.g. a pretrained Transformer foundation model run zero-shot) should still be
labeled as a time-budget-driven engineering choice within the "Deep Learning" bucket,
not folded silently into the core taught-methodology narrative.

## 1a. Diebold-Mariano and nested models
Aula 4 explicitly teaches that DM is **not appropriate for nested models** (its own
example: ARMA(1,1) vs ARMA(2,1)). Check nesting before adding any DM comparison — e.g.
volatility candidates built as constant ⊂ ARCH(1) ⊂ GARCH(1,1) ⊂ GJR-GARCH are all
nested in each other, so no pairwise DM test between them is valid; say so explicitly
rather than silently omitting it. Prefer DM between genuinely non-nested families (e.g.
a pure-AR vs. a pure-MA restriction of the same general model — neither is a special
case of the other).

## 2. Holdout integrity — mechanical changes only
Once a test period's results have been reported/examined, never reuse that data to pick
or confirm an "improved" model or split. If the split itself must change (e.g., per TA
feedback), change it **mechanically by a pre-registered rule** (e.g., a fixed day-count
ratio) — never because a particular cut "looked better" once you saw test performance.
Say so explicitly in the writeup: state the rule that produced the new cutoff, not just
the cutoff. See [[project_ead6034_final_seminar]] for the concrete 80/20 application.

## 3. Causal-only recursion
Parameters and orders are estimated once on the training window. Anything touching the
test window may only update filter/recursion *state* (Kalman state, GARCH variance
recursion, a neural net's hidden state at inference) using strictly past-realized test
observations — never re-estimate or re-select using test-period data. Any new model
class added to the pipeline needs its own causality test (mirror
`tests/test_forecast_pipeline.py`'s pattern: verify no future observation ever changes
an earlier forecast).

## 4. Fair comparison across model classes
Classical models here (ARMA, GARCH) select order via in-sample BIC on the training set —
there is no validation slice. A new model class that *does* need a validation split
(e.g., a neural net needing early stopping) must carve that slice **out of the training
window only**, never touch the test window with it. Otherwise it gets an unearned
advantage over the classical models. Reuse the existing model-agnostic contract
(`evaluate_scale`'s `(n_obs, horizon)` forecast-matrix input) rather than building a
parallel evaluation path.

## 5. Stationarity: run everything, report conflicts honestly
Run ADF, Phillips–Perron, and KPSS — and run each of them in every specification the
checklist/course names (ADF: none/drift/trend; PP: constant+trend, short+long lags;
KPSS: mu+tau, short+long) rather than a convenient subset. If tests disagree (e.g.
KPSS-trend rejecting while ADF/PP don't), report the disagreement as the finding, don't
pick the convenient one. Watch for small-sample pitfalls at coarse aggregation (e.g.
n≈9 observations/session at 60-min bars) — flag it explicitly rather than letting a
test's nominal p-value stand unqualified.

## 6. Metrics discipline
- Never use MAPE on returns near zero — it's numerically degenerate (a few near-zero
  actuals blow it up arbitrarily). Aula 4 teaches the exact formula
  (`MAPE = (1/H)Σ|e_ti/y_ti|`) alongside MSE/MAE, so it's a taught metric being
  deliberately excluded, not an unfamiliar one being skipped — cite the formula, then
  show concretely why it's degenerate here, rather than silently omitting it.
- Always benchmark against trivial baselines (zero-return, historical mean) before
  claiming a model "wins."
- State units unambiguously: a 0.2% *relative* MSE increase is not a 0.2 percentage-point
  return swing — say which one you mean, every time.
- For volatility models, report ω>0, α≥0, β≥0, persistence α+β<1, and prefer QLIKE
  alongside MSE-on-squared-innovation proxies.
- Publish coefficient standard errors / t-statistics for every estimated model. A
  BIC-preferred model with insignificant coefficients is a valid, reportable finding —
  don't suppress it by fitting with `cov_type="none"`.

## 7. Diebold-Mariano: pre-register, then report honestly
Decide which pair(s) of models get DM-tested and on what loss (squared/absolute) and
lag-truncation `q` *before* looking at results. Report p-values honestly even when null.
Statistical significance on a tiny average loss difference is not economic significance —
say both numbers, every time.

## 8. Reproducibility
Hash raw inputs (sha256) and code per module in every run's summary JSON. Cache fitted
results keyed by a hash of (code, data, config). Bind narrative claims to specific table
hashes (as in `docs/discussion_results_manifest.json`) so prose can't silently drift from
a re-run's numbers.

## 9. Public/private data separation
Never commit raw prices, per-bar forecasts, or residuals — only aggregated tables,
figures, and summaries go in `results/`. Follow `data/README.md`'s gitignore boundary.
Licensed market data (BTG Alpha Lab) stays out of version control entirely.

## 10. Presentation discipline
- Every claim in the talk must trace to a specific table/figure in the repo.
- Keep a rehearsal FAQ (aula / implementação / esclarecimento conceitual tags)
  anticipating "why didn't you do X taught in class."
- Time-box the script per slide and rehearse against a real clock.
- Before presenting, diff the oral script against the actual slide deck — a slide with
  no narration budget is a real bug that happened once already (21/09's slide 2).
- Treat the submitted PDF as immutable once sent — check submission logistics
  (deadline, format, "no changes after submission") every time; they've varied.

## 11. Honest null results
"The simple baseline wins" or "no gain over zero" is a valid, reportable scientific
result. State it plainly, explain why, and don't dress it up as failure. Don't claim
more generality than the sample supports (one asset, specific years, no transaction-cost
or tradability claim) — see the paper's own dual statistical+economic framing
(Matías & Reboredo, 2012) as the standard to match: statistical accuracy alone isn't
enough, but don't claim economic significance you haven't tested either.

## 12. Expect a written checklist from the TA — ask for it early
Both graded submissions so far generated a specific, detailed TA checklist
(`Check-list - séries temporais_7662.pdf` for Seminar I). For Seminar II
(multivariate, 07/12), ask Prof. Anderson for the equivalent checklist well before the
final push, instead of reconstructing requirements from feedback after the fact.
