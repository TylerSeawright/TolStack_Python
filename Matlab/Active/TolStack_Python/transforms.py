"""transforms.py — HTM math for TolStack (scalar + vectorized/batched)."""
from __future__ import annotations
import numpy as np


def Tform(a, direction: int) -> np.ndarray:
    T = np.eye(4)
    if direction == 0:
        a = np.asarray(a, float).ravel()
        if a.size != 3:
            raise ValueError("Tform translate needs a 1x3 point")
        T[0:3, 3] = a; return T
    if direction == 1:
        c, s = np.cos(a), np.sin(a); T[1,1],T[1,2],T[2,1],T[2,2]=c,-s,s,c; return T
    if direction == 2:
        c, s = np.cos(a), np.sin(a); T[0,0],T[0,2],T[2,0],T[2,2]=c,s,-s,c; return T
    if direction == 3:
        c, s = np.cos(a), np.sin(a); T[0,0],T[0,1],T[1,0],T[1,1]=c,-s,s,c; return T
    if direction == 4:
        a = np.asarray(a, float).ravel(); T[0,0],T[1,1],T[2,2]=a[0],a[1],a[2]; return T
    return T


def CoordTform(P, order: str = "o") -> np.ndarray:
    P = np.asarray(P, float).ravel()
    if P.size != 6:
        raise ValueError("P must contain exactly 6 values")
    if order == "p":
        return Tform(P[0:3],0) @ Tform(P[5],3) @ Tform(P[4],2) @ Tform(P[3],1)
    return Tform(P[5],3) @ Tform(P[4],2) @ Tform(P[3],1) @ Tform(P[0:3],0)


def extract_HTM_error(H: np.ndarray) -> np.ndarray:
    """Exact ZYX inverse (eps_z uses H[0,0], not the old small-angle H[1,1])."""
    H = np.asarray(H, float)
    return np.array([H[0,3], H[1,3], H[2,3],
        np.arctan2(H[2,1], H[2,2]),
        np.arctan2(-H[2,0], np.sqrt(H[2,2]**2 + H[2,1]**2)),
        np.arctan2(H[1,0], H[0,0])])


def rotation_vector_error(H: np.ndarray) -> np.ndarray:
    """SO(3) log map: order-independent, no gimbal lock. Optional robust measure."""
    H = np.asarray(H, float); R = H[0:3,0:3]
    ct = np.clip((np.trace(R)-1.0)/2.0, -1.0, 1.0); th = np.arccos(ct)
    if th < 1e-12:
        rx,ry,rz = 0.5*(R[2,1]-R[1,2]), 0.5*(R[0,2]-R[2,0]), 0.5*(R[1,0]-R[0,1])
    else:
        s = 2.0*np.sin(th)
        rx,ry,rz = th*(R[2,1]-R[1,2])/s, th*(R[0,2]-R[2,0])/s, th*(R[1,0]-R[0,1])/s
    return np.array([H[0,3],H[1,3],H[2,3],rx,ry,rz])


# ---- Batched (vectorized over N samples) ----------------------------------
def _rot_batch(angle, axis):
    """(N,) angles -> (N,4,4) rotation about axis 1=x,2=y,3=z."""
    angle = np.asarray(angle, float); N = angle.shape[0]
    T = np.tile(np.eye(4), (N,1,1)); c,s = np.cos(angle), np.sin(angle)
    if axis == 1: T[:,1,1],T[:,1,2],T[:,2,1],T[:,2,2]=c,-s,s,c
    elif axis == 2: T[:,0,0],T[:,0,2],T[:,2,0],T[:,2,2]=c,s,-s,c
    else: T[:,0,0],T[:,0,1],T[:,1,0],T[:,1,1]=c,-s,s,c
    return T


def coordtform_batch(P, order: str = "o") -> np.ndarray:
    """P (N,6) -> (N,4,4), same convention as CoordTform."""
    P = np.atleast_2d(np.asarray(P, float)); N = P.shape[0]
    Tr = np.tile(np.eye(4), (N,1,1)); Tr[:,0:3,3] = P[:,0:3]
    Rx,Ry,Rz = _rot_batch(P[:,3],1), _rot_batch(P[:,4],2), _rot_batch(P[:,5],3)
    if order == "p":
        return Tr @ Rz @ Ry @ Rx
    return Rz @ Ry @ Rx @ Tr


def extract_batch(H: np.ndarray) -> np.ndarray:
    """H (N,4,4) -> (N,6) exact ZYX error vectors."""
    H = np.asarray(H, float)
    d = H[:,0:3,3]
    ex = np.arctan2(H[:,2,1], H[:,2,2])
    ey = np.arctan2(-H[:,2,0], np.sqrt(H[:,2,2]**2 + H[:,2,1]**2))
    ez = np.arctan2(H[:,1,0], H[:,0,0])
    return np.column_stack([d[:,0], d[:,1], d[:,2], ex, ey, ez])


def data_transform(data, T):
    data = np.asarray(data, float); T = np.asarray(T, float)
    n = data.shape[1]; out = np.zeros((3,n))
    for i in range(n):
        out[:,i] = (T @ np.concatenate([data[0:3,i],[1.0]]))[0:3]
    return out


def COORD():
    o=np.zeros(3); return np.column_stack([o,[1,0,0],o,[0,1,0],o,[0,0,1]]).astype(float)


def comp(E, C):
    E=np.asarray(E,float).copy(); C=np.asarray(C,float); m=C!=0; E[m]=C[m]; return E
