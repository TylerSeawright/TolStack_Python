% Function to define coordinate system plot as an object
function coord = COORD()

    origin = [0,0,0]';
    x_ax = [1,0,0]';
    y_ax = [0,1,0]';
    z_ax = [0,0,1]';

    coord = [origin, x_ax, origin, y_ax, origin, z_ax];
end