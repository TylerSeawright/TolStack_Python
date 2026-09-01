"""plotting.py — TolStack figures (histograms, coordinate path, tornado)."""
from __future__ import annotations
from typing import List
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa
from transforms import data_transform

_AXIS_COLORS = ("#d62728", "#2ca02c", "#1f77b4")
_PATH_COLOR = "#ff7f0e"


def _wt(fig, t):
    try: fig.canvas.manager.set_window_title(t)
    except Exception: pass


def _equal3d(ax, pts):
    pts = np.asarray(pts, float)
    if pts.size == 0: return
    mn, mx = pts.min(1), pts.max(1); c = (mn+mx)/2; s = float(np.max(mx-mn))
    if s <= 0 or not np.isfinite(s): s = 1.0
    r = s/2*1.15
    ax.set_xlim(c[0]-r,c[0]+r); ax.set_ylim(c[1]-r,c[1]+r); ax.set_zlim(c[2]-r,c[2]+r)
    try: ax.set_box_aspect((1,1,1))
    except Exception: pass


def plot_histogram(E, Eavg, Estd, name, nsig=None):
    E=np.asarray(E,float); Eavg=np.asarray(Eavg,float).ravel(); Estd=np.asarray(Estd,float).ravel()
    lab=["X","Y","Z","TX","TY","TZ"]; un=["mm","mm","mm","rad","rad","rad"]
    with plt.style.context("seaborn-v0_8-whitegrid"): fig,axes=plt.subplots(2,3,figsize=(13,7))
    axes=axes.ravel(); _wt(fig,f"{name} - Error Histograms")
    for i in range(6):
        ax=axes[i]; col=E[:,i]; color=_AXIS_COLORS[i%3]
        if np.allclose(col,col.flat[0]): ax.axvline(col.flat[0],color=color,lw=2)
        else: ax.hist(col,bins="auto",color=color,alpha=0.75,edgecolor="white",linewidth=0.4)
        m=Eavg[i]; b=Estd[i]
        ns=f"{nsig:g}" if nsig is not None else "N"
        ax.axvline(m,color="black",lw=1.4,label=f"mean = {m:.2e}")
        if b!=0:
            ax.axvline(m+b,color="0.4",ls="--",lw=1.1,label=f"$\\pm{ns}\\sigma$ = {b:.2e}"); ax.axvline(m-b,color="0.4",ls="--",lw=1.1)
        ax.set_title(f"$E_{{{lab[i]}}}$  [{un[i]}]",fontsize=11)
        ax.set_xlabel(f"{lab[i]} error [{un[i]}]",fontsize=9); ax.set_ylabel("count",fontsize=9)
        ax.tick_params(labelsize=8); ax.ticklabel_format(axis="x",style="sci",scilimits=(-2,3))
        ax.legend(fontsize=7,loc="upper right",framealpha=0.85)
    fig.suptitle(f"{name} — 6-DOF Error Distribution  (N = {len(E)} samples)",fontsize=14,fontweight="bold")
    fig.tight_layout(rect=(0,0,1,0.96)); return fig


def plot_coord2(C, T, plot_title=""):
    T=[np.asarray(t,float) for t in T]
    org=[np.zeros(3)]+[t[0:3,3] for t in T]; oa=np.array(org).T
    s=float(np.max(oa.max(1)-oa.min(1)))
    if s<=0 or not np.isfinite(s): s=1.0
    L=s/12.0; fr=[np.eye(4)]+T
    with plt.style.context("seaborn-v0_8-whitegrid"): fig=plt.figure(figsize=(9,8))
    _wt(fig,plot_title or "Nominal Path"); ax=fig.add_subplot(111,projection="3d")
    ax.plot(oa[0],oa[1],oa[2],color=_PATH_COLOR,ls="--",lw=1.6,marker="o",ms=4,markerfacecolor=_PATH_COLOR,markeredgecolor="k",zorder=2,label="Vector path")
    an=("X","Y","Z")
    for fi,Tf in enumerate(fr):
        o=Tf[0:3,3]
        for a in range(3):
            d=Tf[0:3,a]; ax.quiver(o[0],o[1],o[2],d[0],d[1],d[2],length=L,color=_AXIS_COLORS[a],linewidth=2,arrow_length_ratio=0.25,label=an[a] if fi==0 else None)
        ax.text(o[0],o[1],o[2]+L*0.35,f"  CS{fi}",fontsize=9,fontweight="bold",color="k",zorder=5)
    tp=[]
    for Tf in fr:
        o=Tf[0:3,3]; tp.append(o)
        for a in range(3): tp.append(o+Tf[0:3,a]*L)
    _equal3d(ax,np.column_stack([oa,np.array(tp).T]))
    ax.set_title(plot_title or "Nominal Vector Path",fontsize=13,fontweight="bold")
    ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
    ax.legend(loc="upper left",fontsize=9,framealpha=0.9); ax.view_init(elev=22,azim=-60); fig.tight_layout(); return fig


def plot_tornado(sens, name="", output="magnitude"):
    """Tornado chart of variance contributions.

    `sens` is the dict from solver.sensitivity_analysis. `output` selects which
    result to rank contributions for: one of X,Y,Z,TX,TY,TZ, 'magnitude'
    (positional, sqrt of X+Y+Z variance contribution), or 'angular'.
    """
    labels=sens["labels"]; contrib=sens["contributions"]  # (6,k)
    if not labels:
        fig=plt.figure(figsize=(6,2)); plt.text(0.5,0.5,"No random error sources",ha="center"); return fig
    dof=sens.get("dof",["X","Y","Z","TX","TY","TZ"])
    if output=="magnitude": vals=np.sqrt(contrib[0:3,:].sum(axis=0))
    elif output=="angular": vals=np.sqrt(contrib[3:6,:].sum(axis=0))
    else: vals=np.sqrt(contrib[dof.index(output),:])
    order=np.argsort(vals)
    labels=[labels[i] for i in order]; vals=vals[order]
    with plt.style.context("seaborn-v0_8-whitegrid"): fig,ax=plt.subplots(figsize=(8,max(2.5,0.4*len(labels)+1)))
    _wt(fig,f"{name} - Sensitivity")
    ax.barh(range(len(vals)),vals,color="#4c72b0",edgecolor="white")
    ax.set_yticks(range(len(vals))); ax.set_yticklabels(labels,fontsize=9)
    ax.set_xlabel(f"1-sigma contribution to {output} error")
    ax.set_title(f"{name} — Sensitivity (tornado): {output}",fontsize=12,fontweight="bold")
    fig.tight_layout(); return fig
