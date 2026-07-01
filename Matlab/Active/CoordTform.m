function T = CoordTform(P, order)
%% Script Description
% CoordTform.m
% This function solves the HTM by all 6 DOF transforms using 321 order.
% Author: Tyler Seawright
% Date Created: 12/11/24
% - P is a list of 6 values. The first 3 are the position vector and the last
%   three are the orientation angles. 
% - order is a character "p" or "o" to signify position or orient first. 
%     * For example an abbe error is created by first orienting then projecting the
%       position vector out from the new coordinate system. Use "o"
%       (Default)
%     * For example, a position may be well known and the orientation
%       changes at the end of the position vector. Use "p"
% - Error Handling: This function returns identity matrix and error if
%   input is incorrect.
%% Script Contents
    % Check for input errors
    if length(P) ~= 6
        errordlg("Input is not for 6DOF. P must contain exactly 6 values.");
        disp("Input is not for 6DOF. P must contain exactly 6 values.");
        T = eye(4);
        return
    end
    % Calculate T by specified order
    if order == "o" || order ~= "p"
        T = Tform(P(6),3) * Tform(P(5),2) * Tform(P(4),1) * Tform(P(1:3),0);
    elseif order == "p"
        T = Tform(P(1:3),0) * Tform(P(6),3) * Tform(P(5),2) * Tform(P(4),1);
    end