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
    % R and Re are same size matrix
    if size(s.R) ~= size(s.Re)
        fprintf("Error: R and Re Size Mixmatch\n")
        s.invalid_stack = 1;
    end
    % Length of R is same as length of C
    % if size(s.R,2) ~= any(size(s.C,2),size(s.Cv,2))
    %     fprintf("Error: R, C, and Cv Size Mixmatch\n")
    %     s.invalid_stack = 1;
    % end
    % Same number of correctors as corrector vectors
    if size(s.C,1) ~= size(s.Cv)
        fprintf("Error: Different Number of C and Cv Rows\n")
        s.invalid_stack = 1;
    end

    % Eventually upgrade this to single error message with all errors on
    % the message rather than print to console.
end