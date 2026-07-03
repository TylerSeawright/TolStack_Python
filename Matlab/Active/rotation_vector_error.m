% rotation_vector_error.m
% Recover [dx, dy, dz, rx, ry, rz] from a 4x4 HTM, where (rx, ry, rz) is the
% rotation vector (axis * angle) of the rotation part -- the SO(3) log map.
%
% Unlike the Euler extraction in extract_HTM_error.m, this representation is
% independent of rotation order and has no gimbal-lock singularity, which makes
% it the most robust angular-error measure for small rotations. Provided as an
% optional, more-accurate alternative; the solver uses the Euler form by default
% to preserve the tool's established convention.
% Mirrors transforms.py::rotation_vector_error in the Python port.
function err = rotation_vector_error(H)
    R = H(1:3,1:3);
    cos_theta = max(-1, min(1, (trace(R) - 1)/2));
    theta = acos(cos_theta);
    if theta < 1e-12
        % Near-identity: first-order skew part (avoids 0/0).
        rx = 0.5*(R(3,2) - R(2,3));
        ry = 0.5*(R(1,3) - R(3,1));
        rz = 0.5*(R(2,1) - R(1,2));
    else
        s = 2*sin(theta);
        rx = theta*(R(3,2) - R(2,3))/s;
        ry = theta*(R(1,3) - R(3,1))/s;
        rz = theta*(R(2,1) - R(1,2))/s;
    end
    err = [H(1,4), H(2,4), H(3,4), rx, ry, rz];
end
