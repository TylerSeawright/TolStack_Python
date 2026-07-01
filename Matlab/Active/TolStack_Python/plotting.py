"""
plotting.py
Matplotlib versions of the TolStack figures.

Direct port of the MATLAB functions:
    plot_histogram.m -> plot_histogram()
    plot_coord2.m    -> plot_coord2()
"""

from __future__ import annotations

from typing import List

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers 3d projection)

from transforms import data_transform


def plot_histogram(E, Eavg, Estd, name: str):
    """Six histograms of the 6-DOF error. Port of plot_histogram.m."""
    E = np.asarray(E, dtype=float)
    Eavg = np.asarray(Eavg, dtype=float).ravel()
    Estd = np.asarray(Estd, dtype=float).ravel()
    pax = ["X", "Y", "Z", "TX [rad]", "TY [rad]", "TZ [rad]"]

    fig, axes = plt.subplots(1, 6, figsize=(18, 4))
    fig.canvas.manager.set_window_title(f"{name} - Error Histograms")
    for i in range(6):
        ax = axes[i]
        ax.hist(E[:, i], bins="auto")
        ax.set_box_aspect(1)
        ax.set_title(
            f"{name}\n$E_{{{pax[i]}}}$\nMean {Eavg[i]:.2e}\nSigma {Estd[i]:.2e}",
            fontsize=8,
        )
        ax.set_xlabel(pax[i])
    fig.tight_layout()
    return fig


def plot_coord2(C, T: List[np.ndarray], plot_title: str = ""):
    """Plot the coordinate frames along the nominal path. Port of plot_coord2.m."""
    C = np.asarray(C, dtype=float)
    T = [np.asarray(t, dtype=float) for t in T]

    # Autoscale the coordinate marker relative to the path length.
    normvec = [np.linalg.norm(t[0:3, 3]) for t in T]
    scale = (max(normvec) / 10.0) if normvec and max(normvec) > 0 else 1.0
    C = C * scale
    offset = 1.05

    fig = plt.figure()
    fig.canvas.manager.set_window_title(plot_title or "Nominal Path")
    ax = fig.add_subplot(111, projection="3d")

    # Plot origin frame (CS0).
    ax.plot(C[0, :], C[1, :], C[2, :])
    ax.text(C[0, 0] * offset, C[1, 0] * offset, C[2, 0], "CS0")
    C0 = C

    for i, Ti in enumerate(T, start=1):
        C2 = data_transform(C, Ti)
        ax.plot(C2[0, :], C2[1, :], C2[2, :])
        ax.text(C2[0, 0] * offset, C2[1, 0] * offset, C2[2, 0], f"CS{i}")
        ax.plot(
            [C0[0, 0], C2[0, 0]],
            [C0[1, 0], C2[1, 0]],
            [C0[2, 0], C2[2, 0]],
            "r--",
        )
        C0 = C2

    ax.set_title(plot_title)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    try:
        ax.set_box_aspect((1, 1, 1))  # axis equal-ish
    except Exception:
        pass
    ax.view_init(elev=30, azim=45)
    return fig
