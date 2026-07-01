function write_results(RESULT, data)
    % Open active Excel
    excel = actxGetRunningServer('Excel.Application');
    excel.visible = true;
    
    workbook = excel.Workbooks.Item(1); % Assuming the workbook is already open
    sheet = workbook.ActiveSheet;
    
    % Write data to the next 6 columns
    for j = 1:6
        sheetRange = get(sheet, 'Cells');
        targetCell = get(sheetRange, 'Item', RESULT(1), RESULT(2) + j);
        set(targetCell, 'Value', data(j));
    end

    workbook.Save();
    
end