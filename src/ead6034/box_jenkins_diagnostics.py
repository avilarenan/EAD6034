"""Boundary-aware diagnostics, model review and a Gaussian reference bootstrap."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.linalg import solve_discrete_lyapunov
from scipy.stats import chi2
from .segmented_arma import Fit, SegmentedARMA


def fit_from_row(row):
    return Fit(int(row.p),int(row.q),np.array(json.loads(row.ar)),np.array(json.loads(row.ma)),
               float(row.mu_pct),float(row.sigma_pct)**2,float(row.llf),int(row.nobs),True,
               "reloaded",np.array([]),int(row.starts),float(row.gradient_max))


def boundary_q(segments,h):
    n=sum(map(len,segments))
    mean=sum(float(x.sum()) for x in segments)/n
    z=[x-mean for x in segments]
    denom=sum(float(x@x) for x in z)
    q=0.
    for k in range(1,h+1):
        valid=[x for x in z if len(x)>k]
        pairs=sum(len(x)-k for x in valid)
        c=sum(float(x[k:]@x[:-k]) for x in valid)/denom
        q+=n*(n+2)*c*c/pairs
    return q


def simulate_segments(fit,lengths,rng):
    # Exact stationary initialization; no finite burn-in approximation.
    dim=max(fit.p,fit.q+1)
    transition=np.zeros((dim,dim))
    transition[:fit.p,0]=fit.ar
    if dim>1:
        transition[np.arange(dim-1),np.arange(1,dim)]=1.
    selection=np.r_[1.,fit.ma,np.zeros(dim-fit.q-1)]
    covariance=solve_discrete_lyapunov(transition,np.outer(selection,selection)*fit.sigma2)
    covariance=(covariance+covariance.T)/2
    output=[None]*len(lengths)
    for n in sorted(set(lengths)):
        indices=[i for i,length in enumerate(lengths) if length==n]
        count=len(indices)
        state=rng.multivariate_normal(np.zeros(dim),covariance,size=count,check_valid="raise")
        y=np.empty((count,n))
        for t in range(n):
            y[:,t]=fit.mu+state[:,0]
            state=state@transition.T+rng.normal(0,np.sqrt(fit.sigma2),count)[:,None]*selection
        for j,i in enumerate(indices): output[i]=y[j]
    return output


def gaussian_reference_bootstrap(segments,fit,h,reps=999,seed=14092026):
    rng=np.random.default_rng(seed)
    model=SegmentedARMA(segments)
    observed=boundary_q(model.residuals(fit),h)
    simulated=[]
    for _ in range(reps):
        sample=simulate_segments(fit,[len(x) for x in segments],rng)
        bootstrap_model=SegmentedARMA(sample)
        estimated=bootstrap_model.fit(fit.p,fit.q,starts=1,maxiter=300)
        if estimated.success:
            simulated.append(boundary_q(bootstrap_model.residuals(estimated),h))
    if len(simulated)<.95*reps:
        raise RuntimeError("Too many failed bootstrap fits")
    count=sum(q>=observed for q in simulated)
    p=(1+count)/(1+len(simulated))
    return dict(bootstrap_q=observed,bootstrap_p=p,bootstrap_reps=len(simulated),
                bootstrap_requested=reps,bootstrap_seed=seed,bootstrap_exceedances=count,
                bootstrap_mc_se=float(np.sqrt(p*(1-p)/(1+len(simulated)))),
                bootstrap_critical_95=float(np.quantile(simulated,.95)),
                bootstrap_null="Gaussian homoskedastic segmented ARMA, fixed order, refitted parameters")


def supplements(out:Path,frames=None,reps=999):
    from .box_jenkins import SCALES,segments_from_frame,diagnose
    tables=out/"tables"
    grid=pd.read_csv(tables/"arma_grid_all.csv")
    selected=pd.read_csv(tables/"selected_models.csv")
    diag=pd.read_csv(tables/"residual_diagnostics.csv")
    review=[];boots=[];grid_review=[]
    for index,scale in enumerate(SCALES):
        picked=selected.loc[selected.scale==scale].iloc[0]
        fit=fit_from_row(picked)
        if frames is not None:
            segments,pieces,_=segments_from_frame(frames[scale],scale)
        else:
            # Preserve actual returns locally, never reconstruct them from
            # standardized residuals when refitting competing models.
            with np.load(out/"private"/f"returns_{scale}.npz") as z:
                segments=[z[key] for key in z.files]
            pieces=[pd.DataFrame({"date":["local segment"]*len(s)}) for s in segments]
        model=SegmentedARMA(segments)
        candidates=grid[(grid.scale==scale)&(grid.status=="eligible")]
        review_h={"1min":60,"5min":24,"15min":12,"30min":12,"60min":8,"1d":15}[scale]
        for row in candidates.itertuples():
            if review_h-row.p-row.q<=0:
                continue
            candidate=fit_from_row(row)
            qstat=boundary_q(model.residuals(candidate),review_h)
            pvalue=float(chi2.sf(qstat,review_h-row.p-row.q))
            grid_review.append(dict(scale=scale,p=int(row.p),q=int(row.q),h=review_h,
                                    q_boundary=qstat,p_working=pvalue,bic=row.bic,
                                    delta_bic=row.delta_bic,passes_working_reference=pvalue>=.05))
        roles={"BIC":picked,"AIC":candidates.loc[candidates.aic.idxmin()],
               "best_pure_AR":candidates[candidates.q==0].sort_values("bic").iloc[0]}
        for role,row in roles.items():
            candidate=fit_from_row(row)
            result,*_=diagnose(model,candidate,pieces,scale)
            review.append(dict(result,role=role,bic=candidate.bic,aic=candidate.aic,
                               ar=row.ar,ma=row.ma,mu_pct=candidate.mu))
        h=int(diag.loc[diag.scale==scale,"diagnostic_lag"].iloc[0])
        print(f"{scale}: Gaussian reference bootstrap ({reps} replicates)",flush=True)
        boot=gaussian_reference_bootstrap(segments,fit,h,reps,14092026+index)
        boots.append(dict(scale=scale,**boot))
        pd.DataFrame(boots).to_csv(tables/"ljungbox_bootstrap.csv",index=False)
    pd.DataFrame(review).to_csv(tables/"model_review.csv",index=False)
    pd.DataFrame(grid_review).to_csv(tables/"grid_residual_review.csv",index=False)
    return pd.DataFrame(boots)
