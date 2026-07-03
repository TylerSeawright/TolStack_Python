% draw_error.m
% Draw one random error sample per element from the chosen distribution.
% Mirrors solver.py::draw_error in the Python port.
%
%   limits       : the Re block, i.e. the N-sigma error value per DOF (the value
%                  entered in the sheet) = the tolerance limit at nsig sigma.
%   nsig         : the sigma multiplier N_SIGMA.
%   distribution : 'Normal'/'N' (default) or 'Uniform'/'U'.
%
% Conventions:
%   * Normal : sigma = limits/nsig, sample N(0, sigma). This is the same
%              distribution the tool used before (nrd(0, Re/nsig)), so existing
%              Normal workbooks are unchanged.
%   * Uniform: sample U(-limits, +limits) -- error equally likely anywhere in the
%              full +/- tolerance band (standard worst-case uniform assumption).
function out = draw_error(limits, nsig, distribution)
    if nargin < 3 || isempty(distribution)
        distribution = 'Normal';
    end
    d = upper(strtrim(char(string(distribution))));
    if ~isempty(d) && d(1) == 'U'
        % Uniform over the full +/- tolerance band.
        out = (rand(size(limits))*2 - 1) .* limits;
    else
        % Default: Normal with sigma = limits/nsig.
        out = randn(size(limits)) .* (limits ./ nsig);
    end
end
