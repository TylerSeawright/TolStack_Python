"""
plotting.py
Matplotlib versions of the TolStack figures.

Direct port of the MATLAB functions:
    plot_histogram.m -> plot_histogram()
    plot_coord2.m    -> plot_coord2()

The visuals have been polished for clarity:
    * coordinate frames are drawn as colored X/Y/Z triads (R/G/B),
    * the nominal vector path is a clean dashed poly-line with markers,
    * 3-D axes use a true equal aspect ratio so geometry isn't distorted,
    * histograms show mean and +/- N-sigma reference lines.
"""

from __future__ import annotations

from typing import List

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers 3d projection)


# Consistent axis colors (X = red, Y = green, Z = blue) reused everywhere.
_AXIS_COLORS = ("#d62728", "#2ca02c", "#1f77b4")
_PATH_COLOR = "#ff7f0e"


def _set_window_title(fig, title: str) -> None:
    """Set the window title if the backend supports it (headless-safe)."""
    try:
        fig.canvas.manager.set_window_title(title)
    except Exception:
        pass


def _set_equal_aspect_3d(ax, pts: np.ndarray) -> None:
    """Force a 1:1:1 data aspect ratio so the geometry is not distorted.

    `pts` is a (3, N) array of every point that must be visible.
    """
    pts = np.asarray(pts, dtype=float)
    if pts.size == 0:
        return
    mins = pts.min(axis=1)
    maxs = pts.max(axis=1)
    centers = (mins + maxs) / 2.0
    span = float(np.max(maxs - mins))
    if span <= 0 or not np.isfinite(span):
        span = 1.0
    r = span / 2.0 * 1.15  # 15% padding
    ax.set_xlim(centers[0] - r, centers[0] + r)
    ax.set_ylim(centers[1] - r, centers[1] + r)
    ax.set_zlim(centers[2] - r, centers[2] + r)
    try:
        ax.set_box_aspect((1, 1, 1))
    except Exception:
        pass


def plot_histogram(E, Eavg, Estd, name: str):
    """Six histograms of the 6-DOF error. Polished port of plot_histogram.m.

    Parameters mirror the MATLAB call `plot_histogram(Error, mu, N*sigma, name)`,
    so `Estd` is the N-sigma band (not 1-sigma) and is drawn as a reference band.
    """
    E = np.asarray(E, dtype=float)
    Eavg = np.asarray(Eavg, dtype=float).ravel()
    Estd = np.asarray(Estd, dtype=float).ravel()

    labels = ["X", "Y", "Z", "TX", "TY", "TZ"]
    units = ["mm", "mm", "mm", "rad", "rad", "rad"]

    with plt.style.context("seaborn-v0_8-whitegrid"):
        fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    axes = axes.ravel()
    _set_window_title(fig, f"{name} - Error Histograms")

    for i in range(6):
        ax = axes[i]
        col = E[:, i]
        color = _AXIS_COLORS[i % 3]

        # Guard against a degenerate (all-equal) column.
        if np.allclose(col, col.flat[0]):
            ax.axvline(col.flat[0], color=color, lw=2)
        else:
            ax.hist(col, bins="auto", color=color, alpha=0.75,
                    edgecolor="white", linewidth=0.4)

        mean = Eavg[i]
        band = Estd[i]
        ax.axvline(mean, color="black", lw=1.4, label=f"mean = {mean:.2e}")
        if band != 0:
            ax.axvline(mean + band, color="0.4", ls="--", lw=1.1,
                       label=f"$\\pm N\\sigma$ = {band:.2e}")
            ax.axvline(mean - band, color="0.4", ls="--", lw=1.1)

        ax.set_title(f"$E_{{{labels[i]}}}$  [{units[i]}]", fontsize=11)
        ax.set_xlabel(f"{labels[i]} error [{units[i]}]", fontsize=9)
        ax.set_ylabel("count", fontsize=9)
        ax.tick_params(labelsize=8)
        ax.ticklabel_format(axis="x", style="sci", scilimits=(-2, 3))
        ax.legend(fontsize=7, loc="upper right", framealpha=0.85)

    fig.suptitle(f"{name} — 6-DOF Error Distribution  (N = {len(E)} samples)",
                 fontsize=14, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig


def plot_coord2(C, T: List[np.ndarray], plot_title: str = ""):
    """Plot the coordinate frames along the nominal path. Polished port of
    plot_coord2.m.

    `C` is retained for signature compatibility with the MATLAB call; the axis
    directions are taken directly from each 4x4 transform so the triads are
    always orthonormal regardless of the marker passed in.
    """
    T = [np.asarray(t, dtype=float) for t in T]

    # Origins: CS0 at the world origin, then one per transform.
    origins = [np.zeros(3)] + [t[0:3, 3] for t in T]
    origins_arr = np.array(origins).T  # (3, n+1)

    # Marker length: a fraction of the overall path extent (never zero).
    span = float(np.max(origins_arr.max(axis=1) - origins_arr.min(axis=1)))
    if span <= 0 or not np.isfinite(span):
        span = 1.0
    L = span / 12.0

    frames = [np.eye(4)] + T  # include CS0

    with plt.style.context("seaborn-v0_8-whitegrid"):
        fig = plt.figure(figsize=(9, 8))
    _set_window_title(fig, plot_title or "Nominal Path")
    ax = fig.add_subplot(111, projection="3d")

    # Dashed poly-line through the frame origins (the vector path).
    ax.plot(origins_arr[0], origins_arr[1], origins_arr[2],
            color=_PATH_COLOR, ls="--", lw=1.6, marker="o", ms=4,
            markerfacecolor=_PATH_COLOR, markeredgecolor="k", zorder=2,
            label="Vector path")

    # Draw an RGB triad at every coordinate frame.
    axis_names = ("X", "Y", "Z")
    for fi, Tf in enumerate(frames):
        o = Tf[0:3, 3]
        for a in range(3):
            d = Tf[0:3, a]
            ax.quiver(o[0], o[1], o[2], d[0], d[1], d[2],
                      length=L, color=_AXIS_COLORS[a], linewidth=2,
                      arrow_length_ratio=0.25,
                      label=axis_names[a] if fi == 0 else None)
        ax.text(o[0], o[1], o[2] + L * 0.35, f"  CS{fi}",
                fontsize=9, fontweight="bold", color="k", zorder=5)

    # Collect all drawn points for a correct equal-aspect box.
    tri_pts = []
    for Tf in frames:
        o = Tf[0:3, 3]
        tri_pts.append(o)
        for a in range(3):
            tri_pts.append(o + Tf[0:3, a] * L)
    all_pts = np.column_stack([origins_arr, np.array(tri_pts).T])
    _set_equal_aspect_3d(ax, all_pts)

    ax.set_title(plot_title or "Nominal Vector Path", fontsize=13,
                 fontweight="bold")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.view_init(elev=22, azim=-60)
    fig.tight_layout()
    return fig
