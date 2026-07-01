function T = Tform(a, dir)
%% Script Description
% This function returns the 4x4 rotation matrix describing either a
% transformation or rotation by 'a' about 'dir'. 

% Set dir = 0 to transform. For rotation axes, set dir to 1, 2, or 3 for x, y,
% and z respectively.
%% Script Contents
T = eye(4);

if (dir == 0) % Vector Transformation
    if (size(a,2) == 3)
        T = makehgtform('translate', a);
    else
        errordlg("Vector Transform Error in Tform(a, dir): Transformation input is not a 1x3 point")
        return
    end
elseif (dir == 1) % Rotation about x
    T = makehgtform('xrotate',a);
elseif (dir == 2)% Rotation about y
    T = makehgtform('yrotate',a);
elseif (dir == 3) % Rotation about z
    T = makehgtform('zrotate',a);
elseif (dir == 4) % Scale transformation by sx, sy, sz
    if (size(a,2) == 3)
        T = eye(4);
        T(1,1) = a(1);
        T(2,2) = a(2);
        T(3,3) = a(3);
    else
        errordlg("Scale Transform Error in Tform(a, dir): Transformation input is not a 1x3 point")
        return
    end
end
end