%% Normally Distributed Random Values for Vector or Matrix of Any Size

function out = nrd(mu, sigma)
    sz_mu = size(mu);
    sz_sigma = size(sigma);

    out = zeros(sz_mu);

    if(sz_mu(1) == sz_sigma(1) && sz_mu(2) == sz_sigma(2))
        % Apply sigma to mu element wise
        out = randn(sz_sigma) .* sigma + mu;
    elseif(sz_sigma==[1,1])
        % Apply sigma to each mu
        for i = 1:sz_mu(1)
            for j = 1:sz_mu(2)
                out(i,j) = randn * sigma + mu(i,j);
            end
        end
    else
        % Error
        % errordlg("Size of Deviation and Size of Mean MixMatch in nrd(). Size of mu and sigma must be equal or sigma is single value.")
    end
end