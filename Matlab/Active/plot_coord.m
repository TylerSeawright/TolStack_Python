function plot_coord(C, T, plot_title, coordname, scale_fac)
    % Plot Csys transformed by HTM T.
    T = cell2mat(T);
    Re = extract_HTM_error(T);
    Re_scaled = Re * scale_fac;
    T_scaled = CoordTform(Re_scaled, "o");
    C2 = data_transform(C,T_scaled); % Scale fac exaggerates results
    C2e = extract_HTM_error(T);
    offset = 1.4;
    figure;
    hold on
    plot3(C(1,:),C(2,:),C(3,:))
    text(C(1,1)*offset,C(2,1)*offset,C(3,1), sprintf("Origin"))
    plot3(C2(1,:),C2(2,:),C2(3,:))
    text(C2(1,1)*offset,C2(2,1)*offset,C2(3,1), sprintf("%s Transform\n[%.3f, %.3f, %.3f]\n[%.3f, %.3f, %.3f]", coordname, C2e(1),C2e(2),C2e(3),C2e(4),C2e(5),C2e(6)))
    plot3([C(1,1),C2(1,1)] ,[C(2,1),C2(2,1)] ,[C(3,1),C2(3,1)] , "--")
    axis equal
    title(plot_title)
    xlabel("X")
    ylabel("Y")
    zlabel("Z")
    legend(" C_{Origin}"," C_{Transformed}", " Transform Vector")
    view(45, 30)
    hold off
end