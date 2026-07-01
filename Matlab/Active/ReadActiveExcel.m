function [data, range, startcell] = ReadActiveExcel()
    % Open active Excel
    excel = actxGetRunningServer('Excel.Application');
    excel.visible = true;
    selectedRange = excel.Selection;
    range = selectedRange.Address;
    % Store starting cell
    firstrow = selectedRange.Cells.Item(1).row;
    firstcol = selectedRange.Cells.Item(1).column;
    startcell = [firstrow, firstcol];
    % Read the data in range
    data = string(selectedRange.Value);
end
