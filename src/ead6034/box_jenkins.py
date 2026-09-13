"""Reproducible 14 September analysis; all statistical inputs stop in 2024."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import importlib.metadata
import json
from pathlib import Path
import platform
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox

from .data import load_win_minutes, audit_minutes, SampleConfig
from .multiscale import MultiscaleConfig, build_multiscale_bars, build_daily_open_to_close
from .stationarity import test_segments, summarize_tests
from .segmented_arma import fit_grid

SCALES = ["1min", "5min", "15min", "30min", "60min", "1d"]


def training_frames(source):
    raw, metadata = load_win_minutes(source)
    # Filter before coverage selection, grouping, tests or estimation.
    raw = raw.loc[raw.date.astype(str).between("2024-01-01", "2024-12-31")].copy()
    if raw.empty:
        raise ValueError("No 2024 training data")
    metadata["audit_2024"] = audit_minutes(raw, SampleConfig(end_date="2024-12-31"))
    audit = metadata["audit_2024"]
    for key in ("duplicate_symbol_timestamps", "missing_values", "nonpositive_closes", "invalid_ohlc_rows", "local_date_mismatches"):
        if audit[key]:
            raise ValueError(f"Data audit failed: {key}={audit[key]}")
    config = MultiscaleConfig(end_date="2024-12-31")
    frames, coverage = build_multiscale_bars(raw, config)
    frames["1d"] = build_daily_open_to_close(frames["1min"], coverage, config)
    for frame in frames.values():
        if not frame.date.astype(str).str.startswith("2024").all():
            raise AssertionError("Holdout contamination")
    return frames, coverage, dict(metadata, config=asdict(config))


def segments_from_frame(frame, scale):
    group = "segment_id" if scale == "1d" else "date"
    pieces = [g.sort_values("timestamp") for _,g in frame.groupby(group,sort=True,observed=True)]
    return [g.return_pct.to_numpy(dtype=float) for g in pieces], pieces, group


def residual_correlogram(segments, max_lag):
    """Global-mean ACF with within-segment numerators and exact pair counts.

    Q(h)=N(N+2) sum_k c_k^2 / N_k. For one segment N_k=N-k,
    giving ordinary Ljung-Box. Chi-square calibration is only a working
    reference with segmented, heteroskedastic data; do not call it exact.
    """
    mean = np.concatenate(segments).mean()
    z = [s-mean for s in segments]
    n = sum(map(len,z))
    denominator = sum(s@s for s in z)
    rows, qstat = [], 0.
    for k in range(1,max_lag+1):
        valid = [s for s in z if len(s)>k]
        pairs = sum(len(s)-k for s in valid)
        if not pairs:
            break
        c = sum(s[k:] @ s[:-k] for s in valid) / denominator
        qstat += n * (n+2) * c*c / pairs
        # PACF retains the pooled OLS definition used in the first delivery.
        x = np.vstack([np.column_stack([np.ones(len(s)-k)] + [s[k-j:-j] for j in range(1,k+1)]) for s in valid])
        y = np.concatenate([s[k:] for s in valid])
        beta = np.linalg.lstsq(x,y,rcond=None)[0]
        rows.append(dict(lag=k, valid_pairs=pairs, acf=c, pacf=beta[-1], q=qstat,
                         acf_band=1.96*np.sqrt(pairs)/n, pacf_band=1.96/np.sqrt(pairs)))
    return pd.DataFrame(rows)


def diagnose(model, fit, pieces, scale):
    residuals = model.residuals(fit)
    max_lag = {"1min":60,"5min":12,"15min":4,"30min":4,"60min":4,"1d":10}[scale]
    # At least p+q+3 lags for a positive working reference df.
    max_lag = min(max(max_lag, fit.p+fit.q+3), max(map(len,residuals))-1)
    corr = residual_correlogram(residuals,max_lag)
    square = residual_correlogram([s*s for s in residuals],max_lag)
    corr["scale"], square["scale"] = scale, scale
    m = int(corr.lag.max())
    q = float(corr.q.iloc[-1])
    dof = m-fit.p-fit.q
    all_r = np.concatenate(residuals)
    jb = stats.jarque_bera(all_r)
    row = dict(scale=scale,p=fit.p,q=fit.q,diagnostic_lag=m,
               horizon_minutes=m*int(scale[:-3]) if scale.endswith("min") else None,
               q_boundary=q, working_df=dof,
               p_ljungbox_working=float(stats.chi2.sf(q,dof)) if dof>0 else None,
               squared_q=float(square.q.iloc[-1]),
               squared_p_working=float(stats.chi2.sf(square.q.iloc[-1],m)),
               residual_mean=float(all_r.mean()), residual_std=float(all_r.std(ddof=1)),
               skewness=float(stats.skew(all_r)), excess_kurtosis=float(stats.kurtosis(all_r)),
               jarque_bera=float(jb.statistic), jarque_bera_p=float(jb.pvalue),
               max_abs_acf=float(corr.acf.abs().max()))
    # Ordinary Ljung-Box tests within every sufficiently long segment are also
    # exported. Fitted-parameter df correction is an approximate reference
    # because coefficients are shared across segments.
    per_segment = []
    for values, piece in zip(residuals,pieces):
        h = min(10, len(values)//5)
        if h <= fit.p+fit.q:
            continue
        lb = acorr_ljungbox(values,lags=[h],model_df=fit.p+fit.q,return_df=True).iloc[0]
        per_segment.append(dict(scale=scale,start=str(piece.date.iloc[0]),end=str(piece.date.iloc[-1]),
                                n=len(values),lag=h,statistic=float(lb.lb_stat),pvalue=float(lb.lb_pvalue)))
    return row,corr,square,pd.DataFrame(per_segment),residuals


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output",default="results/entrega_14_09")
    parser.add_argument("--max-order",type=int,choices=range(6),default=5)
    parser.add_argument("--starts",type=int,default=3)
    parser.add_argument("--skip-report",action="store_true")
    parser.add_argument("--bootstrap-reps",type=int,default=999)
    args = parser.parse_args(argv)
    if args.starts < 1 or args.bootstrap_reps < 19:
        parser.error("Use at least one optimization start and 19 bootstrap replicates")
    out=Path(args.output)
    tables=out/"tables"
    tables.mkdir(parents=True,exist_ok=True)
    frames,coverage,metadata=training_frames(args.input)
    print(f"Training: {len(frames['1d'])} days, {frames['1d'].date.min()} to {frames['1d'].date.max()}",flush=True)
    coverage.to_csv(tables/"coverage_2024.csv",index=False)
    test_parts,selected_rows,grid_parts,diagnostics,corr_parts,square_parts,lb_parts=[],[],[],[],[],[],[]
    local=out/"private"
    local.mkdir(exist_ok=True)
    for scale in SCALES:
        frame=frames[scale]
        segments,pieces,group=segments_from_frame(frame,scale)
        np.savez_compressed(local/f"returns_{scale}.npz",**{f"s{i}":v for i,v in enumerate(segments)})
        tested=test_segments(frame,scale,group)
        tested.to_csv(tables/f"stationarity_{scale}.csv",index=False)
        test_parts.append(tested)
        print(f"{scale}: stationarity complete; fitting {args.max_order+1} x {args.max_order+1} ARMA grid",flush=True)
        def progress(p,q,row):
            print(f"  {scale} ({p},{q}) {row['status']} BIC={row.get('bic',float('nan')):.3f}",flush=True)
        model,best,grid,fits=fit_grid(segments,args.max_order,args.starts,progress)
        grid["scale"]=scale
        grid.to_csv(tables/f"arma_grid_{scale}.csv",index=False)
        grid_parts.append(grid)
        eligible=grid.loc[grid.status=="eligible"].sort_values("bic")
        aic_best=eligible.loc[eligible.aic.idxmin()]
        selected_rows.append(dict(scale=scale,**best.row(),segments=len(segments),
                                  min_segment=min(map(len,segments)), max_segment=max(map(len,segments)),
                                  eligible_models=len(eligible),
                                  next_delta_bic=float(eligible.iloc[1].bic-best.bic),
                                  aic_p=int(aic_best.p),aic_q=int(aic_best.q)))
        diag,corr,square,lb,residuals=diagnose(model,best,pieces,scale)
        diagnostics.append(diag);corr_parts.append(corr);square_parts.append(square);lb_parts.append(lb)
        np.savez_compressed(local/f"residuals_{scale}.npz",**{f"s{i}":v for i,v in enumerate(residuals)})
        print(f"{scale}: BIC selected ARMA({best.p},{best.q}), gap={selected_rows[-1]['next_delta_bic']:.3f}",flush=True)
    all_tests=pd.concat(test_parts,ignore_index=True)
    summary,joint=summarize_tests(all_tests)
    exports={"stationarity_all":all_tests,"stationarity_summary":summary,"stationarity_joint":joint,
             "arma_grid_all":pd.concat(grid_parts,ignore_index=True),"selected_models":pd.DataFrame(selected_rows),
             "residual_diagnostics":pd.DataFrame(diagnostics),"residual_acf_pacf":pd.concat(corr_parts,ignore_index=True),
             "squared_residual_acf":pd.concat(square_parts,ignore_index=True),
             "ljungbox_by_segment":pd.concat(lb_parts,ignore_index=True)}
    for name,df in exports.items(): df.to_csv(tables/f"{name}.csv",index=False)
    versions={name:importlib.metadata.version(name) for name in ["numpy","pandas","scipy","statsmodels","arch","pyarrow","matplotlib","reportlab"]}
    metadata.update(dict(period_start=str(frames["1d"].date.min()),period_end=str(frames["1d"].date.max()),
                         trading_days=len(frames["1d"]),holdout_used=False,max_order=args.max_order,
                         optimizer_starts=args.starts,bootstrap_reps=args.bootstrap_reps,
                         bootstrap_seed_base=14092026,python=platform.python_version(),versions=versions,
                         stationarity_unit="continuous_segment; no pooled p-values",
                         selection="Gaussian segmented quasi-likelihood BIC",seed=6034))
    (out/"analysis_summary.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n")
    from .box_jenkins_diagnostics import supplements
    supplements(out,frames,args.bootstrap_reps)
    if not args.skip_report:
        from .box_jenkins_report import write_report
        write_report(out)
    return exports


if __name__=="__main__":
    main()
