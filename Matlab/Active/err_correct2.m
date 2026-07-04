function Trec = err_correct2(Tre, Tae, Tn, C, Cv, Ce)
    % Solve Corrector Difference Transform
    % This represents coupled motion from applying compensation.
    % Ce (optional) is a zero-mean corrector error sample (same size as C)
    % modeling corrector repeatability; omit / pass zeros for a perfect corrector.
    if nargin < 6 || isempty(Ce)
        Ce = zeros(size(C));
    end
    rowC = size(C,1);
    for j = 1:rowC % For all Corrector rows provided
        if all(C(j,:) == 0) % If no corrector provided, don't perform calc.
            % Pass
        else
            Ere = extract_HTM_error(Tre);
            for i = 1:6
                if C(j,i) == 0
                    CD(i) = 0;
                else
                    CD(i) = C(j,i) - Ere(i) + Ce(j,i);
                end
            end
            
            Tvc = CoordTform(-Cv(j,:),"o"); % Transform to compensator
            Tcd = CoordTform(CD, "o"); % Transform to compensate by
            % Absolute error with corrector propagated by distance to compensator
            Tcae = Tae * (Tvc\ (Tcd * Tvc));
            % Solve Relative Error from Propagated Corrector Error
            Tcre = Tn\Tcae;    
            % Correct Error by Replacement
            Ecre = extract_HTM_error(Tcre);
            % comp(Ecre, C);
            Tre = CoordTform(Ecre,"o");
        end
    end
    % After all iterations, Trec = Tre
    Trec = Tre;

end