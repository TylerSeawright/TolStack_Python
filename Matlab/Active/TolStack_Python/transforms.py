"""
transforms.py
Homogeneous Transformation Matrix (HTM) math for TolStack.

Direct Python/NumPy port of the MATLAB functions:
    Tform.m, CoordTform.m, extract_HTM_error.m, data_transform.m, COORD.m

Author of original MATLAB: Tyler Seawright
Python port preserves the exact math (rotation conventions, 3-2-1 order).
"""

from __future__ import annotations

import numpy as np


def Tform(a, direction: int) -> np.ndarray:
    """4x4 homogeneous transform / rotation matrix.

    Mirrors MATLAB Tform(a, dir):
        dir == 0 : translation by 1x3 vector a
        dir == 1 : rotation about x by angle a (rad)
        dir == 2 : rotation about y by angle a (rad)
        dir == 3 : rotation about z by angle a (rad)
        dir == 4 : scale by 1x3 vector a
    """
    T = np.eye(4)

    if direction == 0:  # translation
        a = np.asarray(a, dtype=float).ravel()
        if a.size != 3:
            raise ValueError("Vector Transform Error in Tform: input is not a 1x3 point")
        T[0:3, 3] = a
        return T

    if direction == 1:  # rotation about x  (makehgtform('xrotate', a))
        c, s = np.cos(a), np.sin(a)
        T[1, 1], T[1, 2] = c, -s
        T[2, 1], T[2, 2] = s, c
        return T

    if direction == 2:  # rotation about y  (makehgtform('yrotate', a))
        c, s = np.cos(a), np.sin(a)
        T[0, 0], T[0, 2] = c, s
        T[2, 0], T[2, 2] = -s, c
        return T

    if direction == 3:  # rotation about z  (makehgtform('zrotate', a))
        c, s = np.cos(a), np.sin(a)
        T[0, 0], T[0, 1] = c, -s
        T[1, 0], T[1, 1] = s, c
        return T

    if direction == 4:  # scale
        a = np.asarray(a, dtype=float).ravel()
        if a.size != 3:
            raise ValueError("Scale Transform Error in Tform: input is not a 1x3 point")
        T[0, 0], T[1, 1], T[2, 2] = a[0], a[1], a[2]
        return T

    return T


def CoordTform(P, order: str = "o") -> np.ndarray:
    """Build a 6-DOF HTM from P = [x, y, z, Tx, Ty, Tz] using 3-2-1 order.

    order == "o" : orient first, then position (default; used for Abbe error)
                   T = Rz * Ry * Rx * Translate
    order == "p" : position first, then orient
                   T = Translate * Rz * Ry * Rx
    """
    P = np.asarray(P, dtype=float).ravel()
    if P.size != 6:
        raise ValueError("Input is not for 6DOF. P must contain exactly 6 values.")

    if order == "p":
        return (
            Tform(P[0:3], 0)
            @ Tform(P[5], 3)
            @ Tform(P[4], 2)
            @ Tform(P[3], 1)
        )
    # order "o" (default, also for anything that is not exactly "p")
    return (
        Tform(P[5], 3)
        @ Tform(P[4], 2)
        @ Tform(P[3], 1)
        @ Tform(P[0:3], 0)
    )


def extract_HTM_error(H: np.ndarray) -> np.ndarray:
    """Recover [dx, dy, dz, eps_x, eps_y, eps_z] from a 4x4 HTM.

    Mirrors MATLAB extract_HTM_error.m (0-indexed here).
    """
    H = np.asarray(H, dtype=float)
    del_x = H[0, 3]
    del_y = H[1, 3]
    del_z = H[2, 3]
    eps_x = np.arctan2(H[2, 1], H[2, 2])
    eps_y = np.arctan2(-H[2, 0], np.sqrt(H[2, 2] ** 2 + H[2, 1] ** 2))
    eps_z = np.arctan2(H[1, 0], H[1, 1])
    return np.array([del_x, del_y, del_z, eps_x, eps_y, eps_z])


def data_transform(data: np.ndarray, T: np.ndarray) -> np.ndarray:
    """Transform a 3xn dataset by HTM T. Mirrors MATLAB data_transform.m."""
    data = np.asarray(data, dtype=float)
    T = np.asarray(T, dtype=float)
    if T.shape[0] != T.shape[1]:
        raise ValueError("Error in data_transform: T is not a square matrix.")
    if T.shape[0] != data.shape[0] + 1:
        raise ValueError(
            "Error in data_transform: rows in data != columns in transform - 1."
        )
    n = data.shape[1]
    out = np.zeros((3, n))
    for i in range(n):
        v = T @ np.concatenate([data[0:3, i], [1.0]])
        out[:, i] = v[0:3]
    return out


def COORD() -> np.ndarray:
    """Coordinate system marker as a 3x6 array of column vectors.

    Mirrors MATLAB COORD.m:
        [origin, x_ax, origin, y_ax, origin, z_ax]
    """
    origin = np.array([0.0, 0.0, 0.0])
    x_ax = np.array([1.0, 0.0, 0.0])
    y_ax = np.array([0.0, 1.0, 0.0])
    z_ax = np.array([0.0, 0.0, 1.0])
    return np.column_stack([origin, x_ax, origin, y_ax, origin, z_ax])


def comp(E: np.ndarray, C: np.ndarray) -> np.ndarray:
    """Replace elements of E where C is nonzero with C. Mirrors comp.m."""
    E = np.asarray(E, dtype=float).copy()
    C = np.asarray(C, dtype=float)
    mask = C != 0
    E[mask] = C[mask]
    return E
