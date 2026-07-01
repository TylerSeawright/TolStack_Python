% extract_HTM_error.m
% Return the error terms from a given HTM for rotation and translation.
% HTM input in form 
% T_err = [1        -epsZ   eps_Y   dC(1);
        %  epsZ     1       -eps_X  dC(2);
        % -eps_Y    eps_X   1       dC(3);
        % 0         0       0       1];
% Error output in form rest_err = [eps_X, eps_Y, eps_Z, dC(1), dC(2), dc(3)];
function err = extract_HTM_error(H)
    del_x = H(1,4);
    del_y = H(2,4);
    del_z = H(3,4);
    eps_x = atan2(H(3,2),H(3,3));
    eps_y = atan2(-H(3,1), sqrt(H(3,3)^2+H(3,2)^2));
    eps_z = atan2(H(2,1), H(2,2));

    err = [del_x, del_y, del_z, eps_x, eps_y, eps_z];
end

