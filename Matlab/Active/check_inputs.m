function [s] = check_inputs(s)
% Function determines which inputs are empty for handling.
    if isempty(s.R)
        s.invalid_stack = 1; 
        fprintf("Required Input Missing: R\n"); 
    end
    if isempty(s.Re)
        s.invalid_stack = 1; 
        fprintf("Required Input Missing: Re\n");
    end
    if isempty(s.C)
        fprintf("Optional Input Missing: C Will Not Be Used\n");
        s.C = zeros(1,6);
    end
    if isempty(s.Cv)
        fprintf("Optional Input Missing: Cv Will Not Be Used\n");
        s.Cv = zeros(1,6);
    end
    if isempty(s.N)
        fprintf("Optional Input Missing: N = 1000 Default Will Be Used\n");
        s.N = 1000;
    end
    if isempty(s.Nsig)
        fprintf("Optional Input Missing: Nsig = 3 Default Will Be Used\n");
        s.Nsig = 3;
    end
    if isempty(s.input_distribution)
        fprintf("Optional Input Missing: Normal Distribution Default Will Be Used\n");
        s.input_distribution = 'Normal';
    end
    if isempty(s.Result)
        s.invalid_stack = 1; 
        fprintf("Required Input Missing: RESULT\n");
    end
    if isempty(s.Plot)
        fprintf("Optional Input Missing: Plots Will Not Be Generated\n");
    end
    if isempty(s.Name)
        fprintf("Optional Input Missing: Stack Name, T1T2 Will be Used\n");
        s.Name = 'T1T2';
    end

    % Other Cases
    % R and Re are same size matrix. (Was `size(R) ~= size(Re)`, which under
    % MATLAB's `if` only tripped when BOTH dimensions differed; isequal is the
    % correct test and matches the Python port.)
    if ~isequal(size(s.R), size(s.Re))
        fprintf("Error: R and Re Size Mismatch\n")
        s.invalid_stack = 1;
    end
    % Same number of correctors as corrector vectors. (Was comparing a scalar to
    % a 1x2 size vector; compare row counts explicitly.)
    if size(s.C,1) ~= size(s.Cv,1)
        fprintf("Error: Different Number of C and Cv Rows\n")
        s.invalid_stack = 1;
    end

    % ---- Robustness guards (open-source hardening; mirror solver.py) --------
    % 1) Reject blank/non-numeric cells that parsed to NaN. Without this a single
    %    bad cell silently poisons the whole Monte-Carlo with NaN.
    blocks = {'R', s.R; 'Re', s.Re; 'C', s.C; 'Cv', s.Cv};
    for k = 1:size(blocks,1)
        arr = blocks{k,2};
        if ~isempty(arr) && any(~isfinite(arr(:)))
            fprintf("Error: %s contains blank or non-numeric cells (NaN). Fill every value in the %s block.\n", blocks{k,1}, blocks{k,1});
            s.invalid_stack = 1;
        end
    end
    % 2) Sample count must allow a sample standard deviation (needs >= 2).
    if ~isempty(s.N) && s.N < 2
        fprintf("Error: N_SAMPLES must be >= 2 (need >=2 for a std dev).\n")
        s.invalid_stack = 1;
    end
    % 3) Sigma multiplier must be positive (used as a divisor).
    if ~isempty(s.Nsig) && s.Nsig <= 0
        fprintf("Error: N_SIGMA must be greater than 0.\n")
        s.invalid_stack = 1;
    end
    % 4) Distribution must be recognized (Normal / Uniform); else default Normal.
    d = upper(strtrim(char(string(s.input_distribution))));
    if ~isempty(d) && ~any(d(1) == 'NU')
        fprintf("Optional Input Note: unrecognized DISTRIBUTION '%s', using Normal.\n", d);
        s.input_distribution = 'Normal';
    end

    % Eventually upgrade this to single error message with all errors on
    % the message rather than print to console.
end