function [Ec, Tn, Tae, Tre, Tc, Tn_list, Tc_list] = solve_error_comp(Rn, Re, C, Vc, Ce)
    % Description:
    % Solve the relative error of a vector path between nominal and
    % propagated error position using HTM.
    % Compensator must be applied
    % between the first and last points in the vector path.
    % Ce (optional) is a zero-mean corrector error sample (same size as C).
    if nargin < 5 || isempty(Ce)
        Ce = zeros(size(C));
    end
 
    % Revised 7/30/25 by Tyler S. Added Tn_list and modified loop to output
    % list of all transforms for access later.

    % Initialize Transforms
    Tn = eye(4); Tae = eye(4);
    % Solve Total Transform (Iterative across vector list)
    for j = 1:size(Rn,1)
        i = j;%1+size(Rn,1)-j; % Reverse Order for Right to Left Multiplication
        % AS DEBUG, i = j and Matrix order set to left to right 10/23/25.
        % Still needs to be resolved.
        % Nominal Position Transform
        % T = T1*T2*T3*...Tn-1*Tn
        Tn = Tn * CoordTform(Rn(i,:),"o");
        Tn_list{i} = Tn;
        % Absolute Position with Error Transform
        % Tae = T1e*T1*T2e*T2*T3e*T3*...Tn-1e*Tn-1*Tne*Tn
        Tae = Tae * CoordTform(Re(i,:),"o") * CoordTform(Rn(i,:),"o");

        % Calculate Relative Error Transform
        Tre = Tn\Tae;

        % Compensate only if a corrector is actually present. (Was ~all(C),
        % which skipped a fully-populated corrector and behaved differently
        % from the Python port; any(C(:)) = "any nonzero corrector".)
        if any(C(:))
            % Compensate
            Trec = err_correct2(Tre, Tae, Tn, C, Vc, Ce);
            % Extract Error Vector
            rowC = size(C,1);
            for i = 1:rowC
                % Ec = comp(extract_HTM_error(Trec), C(i,:)); 
                Ec = extract_HTM_error(Trec); 
            end
            Tc = CoordTform(Ec, "o");
        else
            Ec = extract_HTM_error(Tre);
            Tc = Tre;
        end
        Tc_list{i} = Tc;
    end
    % Reverse order of lists
    % Tc_list = flip(Tc_list);
    % Tn_list = flip(Tn_list);
end