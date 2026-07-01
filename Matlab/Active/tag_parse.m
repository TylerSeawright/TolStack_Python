function [output, idx] = tag_parse(data, tag, tag_length)
    % Loop through the matrix
    val = {}; idx = {};
    [rows, cols] = size(data); i = 1;
    for r = 1:rows
        for c = 1:cols
            value = data{r, c};
            % Check if string matches tag
            if ischar(value) || isstring(value)
                if strcmp(value, tag)
                    % Store index
                    idx{i} = [r, c];
                    % Grab input string
                    input = data(r,c+1:c+tag_length);
                    % If string is converted to double and is NaN, set val
                    % to input string. Note limit 1 string input.
                    if isnan(str2double(input)) % If input is a string, replace with string
                        val{1} = input;
                    else
                        val{1}(i, 1:tag_length) = str2double(input);
                    end
                    i = i+1;
                end
            end
        end
    end
    output = val{1};
end