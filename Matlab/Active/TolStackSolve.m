%% HEADER
%{
    TolStackSolve.m
    Author: Tyler Seawright
    Date Created: 06/12/2025
    Last Updated: 10/24/2025 by Tyler Seawright
    License: MIT License
%}
%% DESCRIPTION
%{
    * The TolStackSolve() function takes input of an empty STACKRANGE data structure containing all
    information to model HTM error propagation via Montecarlo simulation.
    * The TolStackSolve() function returns S, the STACKRANGE data structure
    containing simulation results and imported data.
    * Data is imported only through Excel by highlighting the cell range
    the data lies within.
    * Data is parsed by tag and tag length listed in STACKRANGE data structure.
%}
%% FUNCTION DEFINITION
function S = TolStackSolve(STACK)
%% CLEANUP

clc, close all
%% FETCH DATA INPUTS

% Retrieve inputs from cells highlighted in Excel and parse.
S = fetchstack(STACK);
%% INPUT VERIFICATION

% Verify the inputs are valid or reconfigure solution process for
% simplicity. Apply defaults where not listed.
S = check_inputs(S);

% If inputs are not valid for solution, notify user with an error and quit
% code.
if S.invalid_stack
    % fprintf("INVALID INPUTS\n");fprintf("______________________\n");
    errordlg("INVALID INPUTS\n");
    return
else
% fprintf("Data Import Successful\n");fprintf("______________________\n");
end
%% PREPARE DATA

% N-sigma error limits (as entered in the sheet). Sampling per-iteration is
% handled by draw_error() using the selected DISTRIBUTION (Normal or Uniform).
Re_limits = S.Re;

% Optional reproducible RNG seed. A blank cell parses to the string "NaN";
% only seed when a real number was supplied (else the run is random each time).
if ~isempty(S.Seed) && isnumeric(S.Seed) && all(~isnan(S.Seed))
    rng(S.Seed);
end

% Corrector repeatability limits (zero -> perfect, deterministic corrector).
if isempty(S.Ce)
    Ce_limits = zeros(size(S.C));
else
    Ce_limits = S.Ce;
end
%% SOLVE SYSTEM

% * Input Verification Prints *
% fprintf("Solving System....\n");
% fprintf("______________________\n");
% fprintf("Stack Name: %s\n",S.Name);
% fprintf("Samples: \tN = %d\n", S.N);
% fprintf("Input Distribution: %s\n", S.input_distribution);
% fprintf("Stack Length: %d\n", size(S.R,1));
% fprintf("______________________\n");
% Montecarlo
% fprintf("|     Montecarlo     |\n|"); fprintf("|");

% Perform Montecarlo simulation.
for i = 1:S.N
    % Relative Error and Transform Paths are output
    [S.Error(i,:), ~, ~, ~, ~, S.Tn_list, S.Tc_list] = solve_error_comp(S.R, draw_error(Re_limits, S.Nsig, S.input_distribution), S.C, S.Cv, draw_error(Ce_limits, S.Nsig, S.input_distribution));

    % Progress Bar
    % if (mod(i,S.N/100)==0)
    %     if (mod(i,S.N/20)==0)
    %         fprintf("|");
    %     end
    % end

end

% fprintf("\nMontecarlo Complete\n");fprintf("______________________\n");
%% STATISTICS

% Solve statistics from montecarlo simulation
S.mu = mean(S.Error,1);
S.sigma = std(S.Error,0,1);
S.uplusNsigma = S.mu + S.Nsig * S.sigma;
S.T_uplusNsigma = CoordTform(S.uplusNsigma, "p");
%% PLOTS

% Generate plot figures if specified.
if S.Plot
    % Generate 6 plots of histograms representing 6DOF Error in global Csys
    plot_histogram(S.Error, S.mu, S.Nsig * S.sigma, S.Name, S.Nsig)
    % Define Csys plot scale
    Coordscale = 1;
    % Define Csys plot title
    coordTitle = "\mu + N\sigma Error Transform";
    % Plot relative error between origin and error Csys
    % plot_coord(COORD*Coordscale, {S.T_uplusNsigma}, coordTitle, S.Name, 1)
    % Plot nominal transform path
    plot_coord2(COORD*Coordscale, S.Tn_list, S.Name)
end

%% SAVE RESULTS
% Place results in Excel spreadsheet where specified.
if ~isempty(S.Result)
    write_results(S.Result, S.uplusNsigma);
end
%% END SCRIPT
end