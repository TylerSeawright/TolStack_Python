function s = fetchstack(s)
    % This function fetches and parses tol stack data from Excel based on
    % tags
    % Fetch all data as cell matrix
    [data, ~, startcell] = ReadActiveExcel();
    % Replace missing data with NaN
    data = fillmissing(data, 'constant',"NaN");

    % For all tags, find tag and store data
    for i = 1:size(s.tag,2)
        % Create vector defined by tag and tag length. Organize Later
        % fprintf("Searching for %s with length %d\n",s.tag{1,i},s.tag{2,i})
        [val{i,1},val{i,2}] = tag_parse(data, s.tag{1,i},s.tag{2,i});      
    end
    
    % Organize Data
    s.R = val{1,1};
    s.Re = val{2,1};
    s.C = val{3,1};
    s.Cv = val{4,1};
    s.N = val{5,1};
    s.Nsig = val{6,1};

    % Result and Plot is to be placed at absolute position of RESULT + 1 column
    if ~isempty(val{7,2})
        s.Result = [startcell(1), startcell(2)] + cell2mat(val{7,2})-[1,1];
    end
    if isempty(val{8,1})
        s.Plot = 0;
    else
        s.Plot = val{8,1};
    end
    s.Name = val{9,1};
    s.input_distribution = val{10,1};
    
end