% SC_Sensitivities
clear, clc, close all

R_AB = [-25,25,50]';
R_AC = [-50,-20,0]';

Force = [0,1,0];
Mx = R_AB(2)*Force(3)-R_AB(3)*Force(2);
My = -(R_AB(1)*Force(3)-R_AB(3)*Force(1));
Mz = R_AB(1)*Force(2)-R_AB(2)*Force(1);
Moment = [Mx,My,Mz];

P = [Force, Moment];
k = [5.6,8e6,1e4,4e1,7.5e4,8.15e1];

pos_err_A = P./k;

R_BC = R_AC - R_AB;

T_pos_err_BC = inv(Tform(R_BC',0))*CoordTform(pos_err_A,"p")*Tform(R_BC',0);

pos_err_BC = extract_HTM_error(T_pos_err_BC)