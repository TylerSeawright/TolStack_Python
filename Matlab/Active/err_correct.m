function Trec = err_correct(Tre, Tae, Tn, C, Vc)
    % Solve Corrector Difference Transform
    % This represents coupled motion from applying compensation
    Ere = extract_HTM_error(Tre);
    for i = 1:6
        if C(i) == 0
            CD(i) = 0;
        else
            CD(i) = C(i) - Ere(i);
        end
    end
    Tvc = CoordTform(-Vc,"o"); % Transform to compensator
    Tcd = CoordTform(CD, "o"); % Transform to compensate by
    % Absolute error with corrector propagated by distance to compensator
    Tcae = Tae * (Tvc\ (Tcd * Tvc));
    % Solve Relative Error from Propagated Corrector Error
    Tcre = Tn\Tcae;    
    % Correct Error by Replacement
    Ecre = extract_HTM_error(Tcre);
    comp(Ecre, C);
    Trec = CoordTform(Ecre,"o"); 
end