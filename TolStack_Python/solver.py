"""solver.py — TolStack Monte-Carlo tolerance-stack core (vectorized).

Adds, vs. the original MATLAB port:
  * exact eps_z extraction, hardened input validation, fixed compensator gate
  * fully vectorized Monte-Carlo (batched 4x4 ops) — ~100-250x faster
  * Normal / Uniform / Triangular input distributions (+ optional correlation)
  * reproducible RNG seed
  * richer statistics (mu, sigma, mu+Nσ, |mu|+Nσ worst case, MC std error, 95% CI)
  * STOCHASTIC compensator: a zero-mean corrector error `Ce` (repeatability)
  * linear sensitivity / variance-contribution analysis
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import numpy as np
from transforms import (CoordTform, extract_HTM_error, coordtform_batch,
                        extract_batch)

DEFAULT_TAGS: List[Tuple[str, int]] = [
    ("R",6),("Re",6),("C",6),("Cv",6),("Ce",6),("N_SAMPLES",1),("N_SIGMA",1),
    ("RESULT",6),("MU",6),("SIGMA",6),("WORST_CASE",6),("PLOT",1),
    ("NAME",1),("DISTRIBUTION",1),("SEED",1),("SHOW",1),
]


@dataclass
class StackRange:
    Name: str = ""
    R: Optional[np.ndarray] = None
    Re: Optional[np.ndarray] = None
    C: Optional[np.ndarray] = None
    Cv: Optional[np.ndarray] = None
    Ce: Optional[np.ndarray] = None
    N: Optional[int] = None
    Nsig: Optional[float] = None
    Result: Optional[Tuple[int,int]] = None
    Plot: int = 0
    Show: int = 0
    Seed: Optional[int] = None
    invalid_stack: int = 0
    input_distribution: str = ""
    tags: List[Tuple[str,int]] = field(default_factory=lambda: list(DEFAULT_TAGS))
    mu: Optional[np.ndarray] = None
    sigma: Optional[np.ndarray] = None
    uplusNsigma: Optional[np.ndarray] = None
    worst_case: Optional[np.ndarray] = None
    se_mean: Optional[np.ndarray] = None
    ci95: Optional[np.ndarray] = None
    T_uplusNsigma: Optional[np.ndarray] = None
    Error: Optional[np.ndarray] = None
    Tn_list: Optional[List[np.ndarray]] = None
    Tc_list: Optional[List[np.ndarray]] = None
    result_cells: dict = field(default_factory=dict)


def _str2double(s):
    try: return float(s)
    except (ValueError, TypeError): return math.nan


def _scalar(v):
    """First numeric value of a parsed tag, or None if missing/blank/non-numeric."""
    if v is None: return None
    arr=np.ravel(v)
    if arr.size==0: return None
    try: x=float(arr[0])
    except (ValueError, TypeError): return None
    return None if math.isnan(x) else x


def tag_parse(data, tag, tag_length):
    numeric=[]; string_value=None; idx=[]
    for r in range(len(data)):
        cols=len(data[r])
        for c in range(cols):
            v=data[r][c]
            if not isinstance(v,str) or v!=tag: continue
            idx.append([r+1,c+1])
            raw=[data[r][c+k] if (c+k)<cols else "NaN" for k in range(1,tag_length+1)]
            parsed=[_str2double(x) for x in raw]
            if all(math.isnan(p) for p in parsed): string_value=raw[0]
            else: numeric.append(parsed)
    if string_value is not None: return string_value,idx
    if numeric: return np.array(numeric,float),idx
    return None,idx


def fetchstack(s, data=None, startcell=None):
    if data is None:
        from excel_io import read_active_excel
        data,_addr,startcell=read_active_excel()
    parsed={}; idxs={}
    for name,length in s.tags:
        parsed[name],idxs[name]=tag_parse(data,name,length)
    s.R,s.Re,s.C,s.Cv,s.Ce = parsed["R"],parsed["Re"],parsed["C"],parsed["Cv"],parsed["Ce"]
    _n=_scalar(parsed["N_SAMPLES"]);   s.N = None if _n is None else int(_n)
    s.Nsig = _scalar(parsed["N_SIGMA"])
    _sd=_scalar(parsed["SEED"]);        s.Seed = None if _sd is None else int(_sd)
    sc = startcell if startcell is not None else (1,1)
    s.result_cells={}
    for t in ("RESULT","MU","SIGMA","WORST_CASE"):
        if idxs[t]:
            ir,ic=idxs[t][0]; s.result_cells[t]=(sc[0]+ir-1, sc[1]+ic-1)
    s.Result=s.result_cells.get("RESULT")
    s.Plot = int(_scalar(parsed["PLOT"]) or 0)
    s.Show = int(_scalar(parsed["SHOW"]) or 0)
    def _txt(v):
        if v is None: return ""
        if isinstance(v,np.ndarray): return str(np.ravel(v)[0]) if v.size else ""
        return str(v)
    s.Name=_txt(parsed["NAME"]); s.input_distribution=_txt(parsed["DISTRIBUTION"])
    return s


def check_inputs(s):
    m=[]
    if s.R is None or np.size(s.R)==0: s.invalid_stack=1; m.append("Required Input Missing: R")
    if s.Re is None or np.size(s.Re)==0: s.invalid_stack=1; m.append("Required Input Missing: Re")
    if s.C is None or np.size(s.C)==0: m.append("Optional Input Missing: C Will Not Be Used"); s.C=np.zeros((1,6))
    if s.Cv is None or np.size(s.Cv)==0: m.append("Optional Input Missing: Cv Will Not Be Used"); s.Cv=np.zeros((1,6))
    if s.Ce is None or np.size(s.Ce)==0: s.Ce=np.zeros_like(np.atleast_2d(s.C))   # perfect corrector default
    if s.N is None: m.append("Optional Input Missing: N = 1000 Default"); s.N=1000
    if s.Nsig is None: m.append("Optional Input Missing: Nsig = 3 Default"); s.Nsig=3
    if not s.input_distribution: m.append("Optional Input Missing: Normal Distribution Default"); s.input_distribution="Normal"
    if s.Result is None: s.invalid_stack=1; m.append("Required Input Missing: RESULT")
    if not s.Name: m.append("Optional Input Missing: Stack Name, T1T2 Will be Used"); s.Name="T1T2"
    if s.R is not None and s.Re is not None and np.shape(s.R)!=np.shape(s.Re):
        m.append("Error: R and Re Size Mismatch"); s.invalid_stack=1
    if s.C is not None and s.Cv is not None and np.shape(s.C)[0]!=np.shape(s.Cv)[0]:
        m.append("Error: Different Number of C and Cv Rows"); s.invalid_stack=1
    if s.C is not None and s.Ce is not None and np.shape(np.atleast_2d(s.Ce))[0]!=np.shape(s.C)[0]:
        m.append("Error: Ce must have the same number of rows as C"); s.invalid_stack=1
    for nm,arr in (("R",s.R),("Re",s.Re),("C",s.C),("Cv",s.Cv),("Ce",s.Ce)):
        if arr is not None and np.size(arr)>0 and not np.all(np.isfinite(np.asarray(arr,float))):
            m.append(f"Error: {nm} contains blank or non-numeric cells (NaN)."); s.invalid_stack=1
    # Note (not error): an active corrector DOF with zero Ce is treated as perfect.
    C2=np.atleast_2d(np.asarray(s.C,float)); Ce2=np.atleast_2d(np.asarray(s.Ce,float))
    if C2.shape==Ce2.shape and np.any((C2!=0)&(Ce2==0)):
        m.append("Note: some active corrector DOFs have Ce=0 (modeled as a perfect corrector there).")
    if s.N is not None and s.N<2: m.append("Error: N_SAMPLES must be >= 2."); s.invalid_stack=1
    if s.Nsig is not None and s.Nsig<=0: m.append("Error: N_SIGMA must be > 0."); s.invalid_stack=1
    d=str(s.input_distribution).strip().upper()[:1] if s.input_distribution else "N"
    if d not in ("N","U","T"): m.append(f"Note: unrecognized DISTRIBUTION '{s.input_distribution}', using Normal."); s.input_distribution="Normal"
    s.messages=m
    return s


def nrd(mu,sigma):
    mu=np.asarray(mu,float); sigma=np.asarray(sigma,float)
    if mu.shape==sigma.shape: return np.random.randn(*sigma.shape)*sigma+mu
    if sigma.size==1: return np.random.randn(*mu.shape)*float(sigma)+mu
    return np.zeros(mu.shape)


def sample_errors(limits, nsig, distribution="Normal", n_samples=1, rng=None, correlation=None):
    """Draw (n_samples, m, 6) zero-mean error samples for limit block (m,6).
    Normal N(0,limits/nsig); Uniform U(-limits,limits); Triangular(-limits,0,limits).
    Optional Gaussian-copula correlation over the flattened m*6 elements."""
    rng=np.random.default_rng() if rng is None else rng
    limits=np.atleast_2d(np.asarray(limits,float)); m=limits.shape[0]
    d=str(distribution).strip().upper()[:1] if distribution else "N"
    shape=(n_samples,m,6); k=m*6
    if correlation is not None:
        L=np.linalg.cholesky(np.asarray(correlation,float))
        z=(rng.standard_normal((n_samples,k))@L.T)
        if d=="N": return z.reshape(shape)*(limits/nsig)
        u=0.5*(1.0+np.vectorize(math.erf)(z/np.sqrt(2.0))).reshape(shape)
        if d=="U": return (2*u-1)*limits
        return np.where(u<0.5,-1+np.sqrt(2*u),1-np.sqrt(2*(1-u)))*limits
    if d=="U": return (rng.random(shape)*2.0-1.0)*limits
    if d=="T": return rng.triangular(-1.0,0.0,1.0,shape)*limits
    return rng.standard_normal(shape)*(limits/float(nsig))


# ---- scalar reference (plotting, sensitivity, tests) ----------------------
def err_correct2(Tre,Tae,Tn,C,Cv,Ce=None):
    C=np.atleast_2d(np.asarray(C,float)); Cv=np.atleast_2d(np.asarray(Cv,float))
    Ce=None if Ce is None else np.atleast_2d(np.asarray(Ce,float))
    for j in range(C.shape[0]):
        if np.all(C[j,:]==0): continue
        Ere=extract_HTM_error(Tre); CD=np.zeros(6)
        for i in range(6):
            if C[j,i]==0: CD[i]=0.0
            else: CD[i]=C[j,i]-Ere[i]+(Ce[j,i] if Ce is not None else 0.0)
        Tvc=CoordTform(-Cv[j,:],"o"); Tcd=CoordTform(CD,"o")
        Tcae=Tae@np.linalg.solve(Tvc,(Tcd@Tvc)); Tcre=np.linalg.solve(Tn,Tcae)
        Tre=CoordTform(extract_HTM_error(Tcre),"o")
    return Tre


def solve_error_comp(Rn,Re,C,Vc,Ce=None):
    Rn=np.atleast_2d(np.asarray(Rn,float)); Re=np.atleast_2d(np.asarray(Re,float)); C=np.atleast_2d(np.asarray(C,float))
    Tn=np.eye(4); Tae=np.eye(4); n=Rn.shape[0]; Tnl=[None]*n; Tcl=[None]*n
    Ec=np.zeros(6); Tre=np.eye(4); Tc=np.eye(4)
    for i in range(n):
        Tn=Tn@CoordTform(Rn[i,:],"o"); Tnl[i]=Tn
        Tae=Tae@CoordTform(Re[i,:],"o")@CoordTform(Rn[i,:],"o")
        Tre=np.linalg.solve(Tn,Tae)
        if np.any(C!=0):
            Ec=extract_HTM_error(err_correct2(Tre,Tae,Tn,C,Vc,Ce)); Tc=CoordTform(Ec,"o")
        else:
            Ec=extract_HTM_error(Tre); Tc=Tre
        Tcl[i]=Tc
    return Ec,Tn,Tae,Tre,Tc,Tnl,Tcl


# ---- vectorized batch solver ----------------------------------------------
def _err_correct2_batch(Tre,Tae,Tn,C,Cv,Ce_samples=None):
    C=np.atleast_2d(np.asarray(C,float)); Cv=np.atleast_2d(np.asarray(Cv,float))
    Tn_inv=np.linalg.inv(Tn)
    for j in range(C.shape[0]):
        if np.all(C[j,:]==0): continue
        Ere=extract_batch(Tre)
        ec = Ce_samples[:,j,:] if Ce_samples is not None else 0.0
        CD=np.where(C[j]!=0, C[j]-Ere+ec, 0.0)
        Tvc=CoordTform(-Cv[j,:],"o"); Tvc_inv=np.linalg.inv(Tvc)
        Tcae=Tae@(Tvc_inv@coordtform_batch(CD)@Tvc)
        Tre=coordtform_batch(extract_batch(Tn_inv@Tcae))
    return Tre


def solve_batch(Rn, Re_samples, C, Cv, Ce_samples=None):
    Rn=np.atleast_2d(np.asarray(Rn,float)); C=np.atleast_2d(np.asarray(C,float))
    N=Re_samples.shape[0]; m=Rn.shape[0]
    Nseg=np.stack([CoordTform(Rn[i,:],"o") for i in range(m)])
    Tn_full=np.eye(4)
    for i in range(m): Tn_full=Tn_full@Nseg[i]
    Tae=np.tile(np.eye(4),(N,1,1))
    for i in range(m): Tae=Tae@coordtform_batch(Re_samples[:,i,:])@Nseg[i]
    Tre=np.linalg.inv(Tn_full)@Tae
    if np.any(C!=0): Tre=_err_correct2_batch(Tre,Tae,Tn_full,C,Cv,Ce_samples)
    return extract_batch(Tre)


def run_solve(s, log=None):
    """Run validation + Monte-Carlo on an already-populated StackRange
    (no Excel/file read). Returns s, or None if inputs are invalid."""
    def emit(x):
        if log: log(x)
    s=check_inputs(s)
    for x in getattr(s,"messages",[]): emit(x)
    if s.invalid_stack: emit("INVALID INPUTS"); return None
    rng=np.random.default_rng(s.Seed)
    emit(f"Solving '{s.Name}': N={s.N}, {s.input_distribution}"+(f", seed={s.Seed}" if s.Seed is not None else "")+"...")
    Re_samples=sample_errors(s.Re,s.Nsig,s.input_distribution,s.N,rng=rng)
    Ce_samples=None
    if s.Ce is not None and np.any(np.asarray(s.Ce,float)!=0):
        Ce_samples=sample_errors(s.Ce,s.Nsig,s.input_distribution,s.N,rng=rng)
    error=solve_batch(s.R,Re_samples,s.C,s.Cv,Ce_samples)
    s.Error=error
    _,_,_,_,_,s.Tn_list,s.Tc_list=solve_error_comp(s.R,np.zeros_like(np.atleast_2d(s.R)),s.C,s.Cv)
    s.mu=error.mean(0); s.sigma=error.std(0,ddof=1)
    s.uplusNsigma=s.mu+s.Nsig*s.sigma
    s.worst_case=np.abs(s.mu)+s.Nsig*s.sigma
    s.se_mean=s.sigma/np.sqrt(s.N); s.ci95=1.959964*s.se_mean
    s.T_uplusNsigma=CoordTform(s.uplusNsigma,"p")
    emit("Monte-Carlo complete.")
    return s


def tol_stack_solve(s=None, log=None, data=None, startcell=None):
    """Fetch inputs (live Excel or provided grid) then run_solve."""
    if s is None: s=StackRange()
    s=fetchstack(s, data=data, startcell=startcell)
    return run_solve(s, log=log)


def sensitivity_analysis(s, delta=1e-6):
    """Linear FD variance contribution of each random input DOF (Re and Ce)."""
    R=np.atleast_2d(np.asarray(s.R,float)); Re=np.atleast_2d(np.asarray(s.Re,float))
    C=np.atleast_2d(np.asarray(s.C,float)); Cv=s.Cv
    Ce=np.atleast_2d(np.asarray(s.Ce,float)) if s.Ce is not None else np.zeros_like(C)
    dof=["X","Y","Z","TX","TY","TZ"]; nsig=float(s.Nsig)
    base,_,_,_,_,_,_=solve_error_comp(R,np.zeros_like(Re),C,Cv,np.zeros_like(Ce))
    labels=[]; cols=[]; sig=[]
    for i in range(R.shape[0]):
        for dd in range(6):
            if Re[i,dd]==0: continue
            p=np.zeros_like(Re); p[i,dd]=delta
            out,_,_,_,_,_,_=solve_error_comp(R,p,C,Cv,np.zeros_like(Ce))
            cols.append((out-base)/delta); labels.append(f"R{i+1}.{dof[dd]}"); sig.append(Re[i,dd]/nsig)
    for j in range(C.shape[0]):
        for dd in range(6):
            if C[j,dd]==0 or Ce[j,dd]==0: continue
            p=np.zeros_like(Ce); p[j,dd]=delta
            out,_,_,_,_,_,_=solve_error_comp(R,np.zeros_like(Re),C,Cv,p)
            cols.append((out-base)/delta); labels.append(f"C{j+1}.{dof[dd]}"); sig.append(Ce[j,dd]/nsig)
    if not cols:
        return {"labels":[],"J":np.zeros((6,0)),"contributions":np.zeros((6,0)),"sigma_in":np.array([]),"dof":dof}
    J=np.array(cols).T; sig=np.array(sig)
    return {"labels":labels,"J":J,"contributions":(J*sig)**2,"sigma_in":sig,"dof":dof}
