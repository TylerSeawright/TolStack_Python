import numpy as np, pytest
from solver import (StackRange, run_solve, solve_error_comp, solve_batch,
                    sample_errors, sensitivity_analysis, check_inputs)

def _abbe():
    s=StackRange(); s.R=np.array([[10,0,0,0,0,0]],float); s.Re=np.array([[0,0,0,0,0,0.03]],float)
    s.C=np.zeros((1,6)); s.Cv=np.zeros((1,6)); s.Ce=np.zeros((1,6))
    s.N=50000; s.Nsig=3; s.input_distribution="Normal"; s.Seed=1; s.Result=(1,1)
    return s

def test_abbe_analytic():
    e,_,_,_,_,_,_=solve_error_comp([[10,0,0,0,0,0]],[[0,0,0,0,0,0.02]],np.zeros((1,6)),np.zeros((1,6)))
    assert abs(e[1]-10*np.sin(0.02))<1e-9 and abs(e[5]-0.02)<1e-9

def test_batch_equals_scalar_with_comp_and_ce():
    rng=np.random.default_rng(2)
    R=np.array([[10,0,0,0,0,0],[0,5,0,0,0,0]],float)
    C=np.array([[0.05,0,0,0,0,0.001]],float); Cv=np.array([[2,0,0,0,0,0]],float)
    Re=rng.standard_normal((300,2,6))*0.002; Ce=rng.standard_normal((300,1,6))*0.0008
    sc=np.array([solve_error_comp(R,Re[i],C,Cv,Ce[i])[0] for i in range(300)])
    assert np.allclose(solve_batch(R,Re,C,Cv,Ce), sc, atol=1e-10)

@pytest.mark.parametrize("dist,factor",[("Normal",1/3),("Uniform",1/np.sqrt(3)),("Triangular",1/np.sqrt(6))])
def test_distribution_std(dist,factor):
    x=sample_errors(np.array([[0.06,0,0,0,0,0]]),3,dist,300000,np.random.default_rng(3))[:,0,0]
    assert abs(x.std()-0.06*factor)<0.06*factor*0.03

def test_correlation():
    corr=np.eye(6); corr[0,1]=corr[1,0]=0.7
    x=sample_errors(np.array([[.06,.06,0,0,0,0]]),3,"Normal",200000,np.random.default_rng(4),correlation=corr)
    assert abs(np.corrcoef(x[:,0,0],x[:,0,1])[0,1]-0.7)<0.02

def test_seed_reproducible():
    a=run_solve(_abbe()); b=run_solve(_abbe())
    assert np.allclose(a.uplusNsigma,b.uplusNsigma)

def test_ce_zero_regression_and_zero_mean():
    s0=_abbe(); s0.R=np.array([[1,0,0,0,0,0]],float); s0.Re=np.array([[0,0,0,0,0,0.017]],float)
    s0.C=np.array([[0,0,0,0,0,0.001]],float); s0.Cv=np.array([[1,0,0,0,0,0]],float); s0.Ce=np.zeros((1,6))
    a=run_solve(s0)
    s1=_abbe(); s1.R=s0.R.copy(); s1.Re=s0.Re.copy(); s1.C=s0.C.copy(); s1.Cv=s0.Cv.copy()
    s1.Ce=np.array([[0,0,0,0,0,0.0005]],float)
    b=run_solve(s1)
    assert np.allclose(a.mu,b.mu,atol=2e-4)          # corrector error is zero-mean
    assert b.sigma[5]>a.sigma[5]+1e-5                 # adds Tz spread

def test_guards():
    s=_abbe(); s.Re=np.array([[0,np.nan,0,0,0,0]],float); s=check_inputs(s); assert s.invalid_stack
    s=_abbe(); s.N=1; s=check_inputs(s); assert s.invalid_stack
    s=_abbe(); s.Nsig=0; s=check_inputs(s); assert s.invalid_stack

def test_sensitivity_abbe():
    r=sensitivity_analysis(_abbe())
    assert r["labels"]==["R1.TZ"] and abs(r["J"][1,0]-10)<1e-3
