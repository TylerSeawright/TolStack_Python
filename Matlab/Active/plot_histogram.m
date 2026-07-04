function plot_histogram(E, Eavg, Estd, name, nsig)
    % Estd is the N-sigma band (nsig*sigma); label it with the real multiplier.
    if nargin < 5 || isempty(nsig)
        nlabel = 'N';
    else
        nlabel = num2str(nsig);
    end
    pax = {"X","Y","Z","TX [rad]","TY [rad]","TZ [rad]"};

    % Create a wide figure to fit 6 square plots
    figure('Units', 'normalized', 'Position', [0.05, 0.4, 0.9, 0.4]);  % [left, bottom, width, height]

    for i = 1:6
        subplot(1, 6, i);
        histogram(E(:, i));
        axis square;  % Make each subplot square
        meanval = num2str(Eavg(i),'%.2e');
        bandval = num2str(Estd(i),'%.2e');
        title(sprintf("%s\n E_{%s}\nMean %s\n\\pm%s\\sigma %s", name, pax{i}, meanval, nlabel, bandval));
        xlabel(pax{i});
    end
end
