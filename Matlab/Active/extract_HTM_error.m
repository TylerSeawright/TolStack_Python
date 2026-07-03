% extract_HTM_error.m
% Return the error terms from a given HTM for rotation and translation.
% HTM input in form 
% T_err = [1        -epsZ   eps_Y   dC(1);
        %  epsZ     1       -eps_X  dC(2);
        % -eps_Y    eps_X   1       dC(3);
        % 0         0       0       1];
% Error output in form rest_err = [eps_X, eps_Y, eps_Z, dC(1), dC(2), dc(3)];
% NOTE (fidelity): eps_z previously used atan2(H(2,1), H(2,2)), a small-angle
% approximation of the Z rotation that couples in the X/Y angles. It is replaced
% by the exact ZYX inverse atan2(H(2,1), H(1,1)). The two agree to < 0.005% for
% angular errors below ~0.01 rad but the old form drifts fast for larger angles.
% This matches transforms.py::extract_HTM_error in the Python port.
% For an order-independent, gimbal-lock-free small-rotation measure, see
% rotation_vector_error.m.
function err = extract_HTM_error(H)
    del_x = H(1,4);
    del_y = H(2,4);
    del_z = H(3,4);
    eps_x = atan2(H(3,2),H(3,3));
    eps_y = atan2(-H(3,1), sqrt(H(3,3)^2+H(3,2)^2));
    eps_z = atan2(H(2,1), H(1,1));   % exact ZYX (was H(2,2))

    err = [del_x, del_y, del_z, eps_x, eps_y, eps_z];
end

