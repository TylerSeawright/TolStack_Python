% TolStack_Button.m
% This script runs TolStack when a button is pressed.

%% CLEANUP
clc, clear, close all
%% INPUT
button = 1;
%% RUN SCRIPT
if button
    S = TolStackSolve(STACKRANGE);
end