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
    Ce;            % Compensator error (N-sigma, zero-mean corrector repeatability)
    N;
    Nsig;
    Result;
    Plot;
    Seed;          % Optional RNG seed for reproducible runs
    invalid_stack = 0;
    input_distribution = '';
    % 'Ce' and 'SEED' are appended at the END so existing tag indices are unchanged.
    tag = {'R', 'Re', 'C', 'Cv', 'N_SAMPLES', 'N_SIGMA', 'RESULT', 'PLOT', 'NAME', "DISTRIBUTION", 'Ce', 'SEED';...
            6, 6, 6, 6, 1, 1, 6, 1, 1, 1, 6, 1}
    mu;
    sigma;
    uplusNsigma;
    T_uplusNsigma;
    Error;
    Tn_list;
    Tc_list;
    end
end