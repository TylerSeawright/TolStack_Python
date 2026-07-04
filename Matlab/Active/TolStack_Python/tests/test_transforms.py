import numpy as np
from transforms import (CoordTform, extract_HTM_error, rotation_vector_error,
                        coordtform_batch, extract_batch)

def test_epsz_exact_roundtrip():
    rng=np.random.default_rng(0)
    for _ in range(2000):
        ang=rng.uniform(-1.4,1.4,3)
        back=extract_HTM_error(CoordTform([0,0,0,*ang],"o"))
        assert np.allclose(back[3:], ang, atol=1e-9)

def test_batch_equals_scalar_transforms():
    rng=np.random.default_rng(1); P=rng.uniform(-2,2,(50,6))
    Hb=coordtform_batch(P)
    for i in range(50):
        assert np.allclose(Hb[i], CoordTform(P[i],"o"), atol=1e-12)
    Eb=extract_batch(Hb)
    for i in range(50):
        assert np.allclose(Eb[i], extract_HTM_error(Hb[i]), atol=1e-12)

def test_rotation_vector_pure_axis_exact():
    # Pure single-axis rotation: log map equals the angle exactly.
    for axis,idx in [(3,3),(4,4),(5,5)]:
        P=[0,0,0,0,0,0]; P[idx]=0.5
        v=rotation_vector_error(CoordTform(P,"o"))
        assert abs(v[idx]-0.5)<1e-12 and np.allclose(np.delete(v[3:],idx-3),0,atol=1e-12)

def test_rotation_vector_small_angle_first_order():
    # For small combined rotations it matches Euler to first order (~1e-5).
    v=rotation_vector_error(CoordTform([0,0,0,0.001,-0.002,0.0015],"o"))
    assert np.allclose(v[3:], [0.001,-0.002,0.0015], atol=1e-5)
