classdef STACKRANGE
    % Class to define all excel inputs to Tolstack.m
    properties
    % filepath;
    % sheetname;
    Name = "";
    R;
    Re;
    C;
    Cv;
    N;
    Nsig;
    Result;
    Plot;
    invalid_stack = 0;
    input_distribution = '';
    tag = {'R', 'Re', 'C', 'Cv', 'N_SAMPLES', 'N_SIGMA', 'RESULT', 'PLOT', 'NAME', "DISTRIBUTION";...
            6, 6, 6, 6, 1, 1, 6, 1, 1, 1}
    mu;
    sigma;
    uplusNsigma;
    T_uplusNsigma;
    Error;
    Tn_list;
    Tc_list;
    end
end