function D = data_transform(data, T)
%% Script Description
% Transform a 3xn dataset by HTM T
%% Script Init

% Verify size of input matrices are valid.
szT = size(T);
szD = size(data,1);
if szT(1)~=szT(2)
    error("Error in data_transform(data, T). T is not square matrix.")
    return
end
if szT(1)~=szD+1
    error("Error in data_transform(data, T). Number of rows in data is not equal to number of columns in transform matrix.")
    return
end

%% Script Contents
n = size(data,2);

for i = 1:n
    d(1:4,i) = T * [data(1:3,i);1];
end
D = d(1:3,:);
end