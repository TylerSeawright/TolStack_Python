function plot_coord2(C, T, plot_title)

    % Plot Csys Path transformed by HTM T.
    figure;hold on

    % Autoscale C
    for i = 1:length(T)
        vec(:,i) = T{i}(1:3,4);
        normvec(i) = norm(vec(:,i));
    end
    scale = max(normvec)/10;
    C = C*scale;
    offset = 1.05;

    % Plot Origin
    plot3(C(1,:),C(2,:),C(3,:))
    text(C(1,1)*offset,C(2,1)*offset,C(3,1), sprintf("CS%d",0))
    C0 = C;

    for i = 1:length(T)
        C2 = data_transform(C,T{i}); 
        
        % Plot Next Csys
        plot3(C2(1,:),C2(2,:),C2(3,:))
        text(C2(1,1)*offset,C2(2,1)*offset,C2(3,1), sprintf("CS%d",i))

        % text(C2(1,1)*offset,C2(2,1)*offset,C2(3,1), sprintf("Transformed\n[%.3f, %.3f, %.3f]\n[%.3f, %.3f, %.3f]", C2e(1),C2e(2),C2e(3),C2e(4),C2e(5),C2e(6)))
        plot3([C0(1,1),C2(1,1)] ,[C0(2,1),C2(2,1)] ,[C0(3,1),C2(3,1)] , "r--")
        C0 = C2;
    end
    axis equal
    title(plot_title)
    xlabel("X")
    ylabel("Y")
    zlabel("Z")
    view(45, 30)
    hold off
end