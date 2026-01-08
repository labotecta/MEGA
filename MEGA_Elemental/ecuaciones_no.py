
# no
def eqDex(theta, xid, tauz, phi, pz, pd, Z):
    '''
    Demand for domestic goods by exporters.

    .. math::
        D_{i} = \left(\\theta_{i}^{\phi_{i}}\\xi^{D}_{i}(1+\\tau^{z}_{i}\\frac{pz_{i}}{pd_{i}})\\right)^{\\frac{1}{1-\phi_{i}}}Z_{i}

    Args:
        theta (1D numpy array):
        xid (1D numpy array): Share parameter for the share of domestically produced good i used by firms exporting good i
        tauz (1D numpy array): Ad valorem tax rate on commodity i
        phi (1D numpy array): Elasticity of substitution between exports (??) and domestically produced goods by firms exporting good i
        pz (1D numpy array): price of output good i
        pd (1D numpy array): price of domesically produced good i
        Z (1D numpy array): Output from exporters CET production function

    Returns:
        D (1D numpy array): Demand for domestic good i by exporters.
    '''
    D = (theta**phi * xid * (1 + tauz) * pz / pd) ** (1 / (1 - phi)) * Z
    return D

# no
def eqX(ax, Z):
    '''
    Equation representing the demand for intermediate inputs.

    .. math::
        X_{i,j} = ax_{i,j}Z_{j}

    Args:
        ax (2D numpy array): Fixed proportions of intermeidate input i
            used in production of good j (Leontif production function)
        Z (1D numpy array): Output of industry j

    Returns:
        X (2D numpy array): Demand for intermediate input i used in the
            production of good j
    '''
    X = ax * Z
    return X

# no
def eqY(ay, Z):
    '''
    Equation representing the production of value added.

    .. math::
        Y_{j} = ay_{j}Z_{j}

    Args:
        ay (1D numpy array): Leontif production parameter, share of
            output of industry j in value added of good j
        Z (1D numpy array): Output of industry j

    Returns:
        Y (1D numpy array): Value added of good j
    '''
    Y = ay * Z
    return Y

# no
def eqTd(taud, pf, Ff):
    '''
    Equation defining total direct tax revenue.

    .. math::
        Td = \tau d \sum_{h}pf_{h}FF_{h}

    Args:
        taud (float): Direct tax rate
        pf (1D numpy array): The price of factor h
        Ff (1D numpy array): Endowment of factor h

    Returns:
        Td (float): Total direct tax revenue.
    '''
    Td = taud * (pf * Ff).sum()
    return Td

# no
def eqTrf(tautr, pf, Ff):
    '''
    Equation defining total transfers to households.

    .. math::
        Trf = \tau^{tr} \sum_{h}pf_{h}FF_{h}

    Args:
        tautr (float): Tranfer rate (??)
        pf (1D numpy array): The price of factor h
        Ff (1D numpy array): Endowment of factor h

    Returns:
        Trf (float): Total transfers to households
    '''
    Trf = tautr * pf["LAB"] * Ff["LAB"]
    return Trf

# no
def eqTz(tauz, pz, Z):
    '''
    Equation representing production tax revenue from each commodity.

    .. math::
        Tz_{j} = \tau^{z}_{j} pz_{j}Z_{j}

    Args:
        tauz (1D numpy array): Ad valorem tax rate on commodity j
        pz (1D numpy array): price of output good j
        Z (1D numpy array): Output of industry j

    Returns:
        Tz (1D numpy array): Production tax revenue for each commodity j
    '''
    Tz = tauz * pz * Z
    return Tz

# no
def eqTm(taum, pm, M):
    '''
    Equation representing tariff revenue from each commodity.

    .. math::
        Tm_{j} = \tau^{m}_{j} pm_{j}M_{j}

    Args:
        taum (1D numpy array): Tariff rate on commodity j
        pm (1D numpy array): price of import good j
        M (1D numpy array): Imports of good j

    Returns:
        Tm (1D numpy array): Tariff revenue for each commodity j
    '''
    Tm = taum * pm * M
    return Tm

# no
def eqXg(mu, XXg):
    '''
    Equation representing government expenditures on commodity j

    .. math::
        X^{g}_{j} = \mu_{j}XX_{g}

    Args:
        mu (1D numpy array): Government expenditure share parameters for
            each commodity j
        XXg (float): Total government spending on goods/services

    Returns:
        Xg (1D numpy array): Government expenditures on commodity j
    '''
    Xg = mu * XXg.values
    return Xg

# no
def eqXv(lam, XXv):
    '''
    Equation representing investment demand for each good j

    .. math::
        Xv_{j} = \lambda_{j}XXv

    Args:
        lam (1D numpy array): Fixed shares of investment for each good j
        XXv (float??): Total investment

    Returns:
        Xv (1D numpy array): Investment demand for each good j
    '''
    Xv = lam * XXv.values
    return Xv

# no
def eqXXv(g, Kk):
    '''
    Equation representing total investment.

    .. math::
        XXv = g \cdot KK

    Args:
        g (float): Exogenous long run growth rate of the economy
        Kk (float): Total capital stock

    Returns:
        XXv (float): Total investment.
    '''
    XXv = g * Kk
    return XXv

# no
def eqSp(ssp, pf, Ff, Fsh, Trf):
    '''
    Equation representing total household savings.

    .. math::
        Sp = ssp \cdot \left(\sum_{h}pf_{h}FF_{h} \\right)

    Args:
        ssp (float): Fixed household savings rate
        pf (1D numpy array): The price of factor h
        Ff (1D numpy array): Endowment of factor h
        Fsh (float): Repatriated profits
        Trf (float): Total transfers to households

    Returns:
        Sp (float): Total household savings
    '''
    Sp = ssp * ((pf * Ff).sum() - Fsh + Trf)
    return Sp

# no
def eqSg(mu, Td, Tz, Tm, XXg, Trf, pq):
    '''
    Equation representing total government savings.

    .. math::
        Sg = Td + \sum_{j}Tz_{j} + \sum_{j}Tm_{j} - (Trf + \sum_{j}Xg_{j})

    Args:
        mu (1D numpy array): Government expenditure share parameters for
            each commodity j
        Td (float): Total direct tax revenue
        Tz (1D numpy array): Production tax revenue for each commodity j
        Tm (1D numpy array): Tariff revenue for each commodity j
        XXg (float): Total government spending on goods/services
        Trf (float): Total transfers to households
        pq (1D numpy array): price of the Armington good (domestic + imports) for each good i

    Returns:
        Sg (float): Total government savings
    '''
    Sg = Td + Tz.sum() + Tm.sum() - (Trf + XXg * (mu * pq).sum())
    return Sg

# no
def eqFsh(R, Kf, er):
    '''
    Equation representing domestic profits that are repatriated to foreign owners of capital.

    .. math::
        FSH = R \cdot KF \cdot \\varepsilon

    Args:
        R (float): Real return on capital
        Kf (float): Foreign holdings of domestic capital
        er (float): The real exchange rate

    Returns:
        Fsh = Repatriated profits
    '''
    Fsh = R * Kf * er
    return Fsh

# no
def eqKd(g, Sp, lam, pq):
    '''
    Equation representing domestic capital holdings.

    .. math::
        K^{d} = \\frac{S^{p}}{g\sum_{j}\lambda_{j}pq_{j}}

    Args:
        g (float): Exogenous long run growth rate of the economy
        Sp (float): Total household savings
        lam (1D numpy array): Fixed shares of investment for each good j
        pq (1D numpy array): price of the Armington good (domestic + imports) for each good i

    Returns:
        Kd (float): Domestically owned capital ??
    '''
    Kd = Sp / (g * (lam * pq).sum())
    return Kd

# no
def eqKf(Kk, Kd):
    '''
    Equation representing foreign holdings of domestically used capital.

    .. math::
        K^{f} = KK - K^{d}

    Args:
        Kk (float): Total capital stock
        Kd (float): Domestically owned capital

    Returns:
        Kf (float): Foreign owned domestic capital
    '''
    Kf = Kk - Kd
    return Kf

# no
def eqKk(pf, Ff, R, lam, pq):
    '''
    Equation describing the capital market clearing equation.

    .. math::
        KK = \\frac{pf * FF}{R \sum_{j}\lambda_{j}pq_{j}}

    Args:
        pf (1D numpy array): The price of factor h
        Ff (1D numpy array): Endowment of factor h
        R (float): Real return on capital
        lam (1D numpy array): Fixed shares of investment for each good j
        pq (1D numpy array): price of the Armington good (domestic + imports) for each good i

    Returns:
        Kk (float): Total capital stock
    '''
    #    R = ( (pf['CAP'] * Ff['CAP']) / Kk) / ((lam * pq).sum())
    Kk = (pf["CAP"] * Ff["CAP"]) / (R * ((lam * pq).sum()))
    return Kk

# no
def eqXp(alpha, pf, Ff, Sp, Td, Fsh, Trf, pq):
    '''
    Equation for demand for production good i by consumers.

    .. math::
        X^{p}_{i}= \\frac{}\\alpha_{i}}{pq_{i}}\left(\sum_{h}pf_{h}Ff_{h} - S^{p} - T^{d}- FSH - TRF\\right)

    Args:
        alpha (1D numpy array): Budget share of good i
        pf (1D numpy array): The price of factor h
        Ff (1D numpy array): Endowment of factor h
        Sp (float): Total household savings
        Td (float): Total direct tax revenue
        Fsh = Repatriated profits
        Trf (float): Total transfers to households
        pq (1D numpy array): price of the Armington good (domestic + imports) for each good i

    Returns:
        Xp (1D numpy array): Demand for production good i by consumers
    '''
    Xp = alpha * ((pf * Ff).sum() - Sp - Td - Fsh + Trf) / pq
    return Xp

# no
def eqpe(er, pWe):
    '''
    Equation defining export prices.

    .. math::
        pe_{i} = \\varepsilon \cdot pWe_{i}

    Args:
        er (float): The real exchange rate
        pWe (1D numpy array): The world price of commodity i in foreign currency

    Returns:
        pe (1D numpy array): Price of commodity i exports in domestic currency
    '''
    pe = er * pWe
    return pe

# no
def eqbop(pWe, pWm, E, M, Sf, Fsh, er):
    '''
    Balance of payments.

    .. math::
        \sum_{i}pWe_{i}E_{i} + \\frac{Sf}{\\varepsilon} = \sum_{i}pWm_{i}M_{i} + \\frac{Fsh}{\\varepsilon}

    Args:
        pWe (1D numpy array): The world price of commodity i in foreign currency
        pWm (1D numpy array): The world price of commodity i in foreign currency.
        E (1D numpy array): Exports of commodity i
        M (1D numpy array): Imports of commodity i
        Sf (float): Total foreign savings (??)
        Fsh = Repatriated profits
        er (float): The real exchange rate

    Returns:
        bop_error (float): Error in balance of payments equation.

    '''
    bop_error = (pWe * E).sum() + Sf / er - ((pWm * M).sum() + Fsh / er)
    return bop_error

# no
def eqSf(g, lam, pq, Kf):
    '''
    Net foreign investment/savings.

    .. math::
        Sf = g Kf \sum_{j} \lambda_{j} pq_{j}

    Args:
        g (float): Exogenous long run growth rate of the economy
        lam (1D numpy array): Fixed shares of investment for each good j
        pq (1D numpy array): price of the Armington good (domestic + imports) for each good i
        Kf (float): Foreign owned domestic capital

    Returns:
        Sf (float): Total foreign savings (??)
    '''
    Sf = g * Kf * (lam * pq).sum()
    return Sf

# no
def eqQ(gamma, deltam, deltad, eta, M, D):
    '''
    CES production function for the importing firm.

    .. math::
        Q_{i} = \gamma_{i}\left[\delta^{m}_{i}M^{\eta_{i}}_{i} + \delta^{d}_{i}D^{\eta_{i}}_{i}\\right]^{\\frac{1}{\eta_{i}}}

    Args:
        gamma (1D numpy array): Scale parameter for CES production function
        deltam (1D numpy array): Share parameter for use of imports of good i in produciton Armington good i
        deltad (1D numpy array): Share parameter for use of domestically produced good i in produciton Armington good i
        eta (1D numpy array): The elasticity of substitution between imports and domestically supplied good i
        M (1D numpy array): The imports of good i
        D (1D numpy array): The domestic supply of good i from domestic production

    Returns:
        Q (1D numpy array): The domestic supply of good i, the Armington good
    '''
    Q = gamma * (deltam * M**eta + deltad * D**eta) ** (1 / eta)
    return Q

# no
def eqM(gamma, deltam, deltad, eta, Q, pq, pm, taum):
    '''
    Demand for imports.

    .. math::
        M_{i} = \left(\gamma^{\eta_{i}}_{i}\delta^{m}_{i}\\frac{pq_{i}}{(1+\\tau^{m}_{i})pm_{i}}\\right)^{\\frac{1}{1-\eta_{i}}}Q_{i}

    Args:
        gamma (1D numpy array): Scale parameter for CES production function
        deltam (1D numpy array): Share parameter for use of imports of good i in produciton Armington good i
        deltad (1D numpy array): Share parameter for use of domestically produced good i in produciton Armington good i
        eta (1D numpy array): The elasticity of substitution between imports and domestically supplied good i
        Q (1D numpy array): The domestic supply of good i, the Armington good
        pq (1D numpy array): price of the Armington good (domestic + imports) for each good i
        pm (1D numpy array): The price of commodity i imports in domestic currency.
        taum (1D numpy array): Tariff rate on commodity i

    Returns:
        M (1D numpy array): Demand for imports of good i
    '''
    M = (gamma**eta * deltam * pq / ((1 + taum) * pm)) ** (1 / (1 - eta)) * Q
    return M

# no
def eqD(gamma, deltam, deltad, eta, Q, pq, pd):
    '''
    Demand for domestically produced goods from importers.

    .. math::
        D_{i} = \left(\gamma_{i}^{\eta_{i}}\delta^{d}_{i}\\frac{pq_{i}}{pd_{i}}\\right)^{\\frac{1}{1-\eta_{i}}}Q_{i}

    Args:
        gamma (1D numpy array): Scale parameter for CES production function
        deltam (1D numpy array): Share parameter for use of imports of good i in produciton Armington good i
        deltad (1D numpy array): Share parameter for use of domestically produced good i in produciton Armington good i
        eta (1D numpy array): The elasticity of substitution between imports and domestically supplied good i
        Q (1D numpy array): The domestic supply of good i, the Armington good
        pq (1D numpy array): price of the Armington good (domestic + imports) for each good i
        pd (1D numpy array): price of domesically produced good i

    Returns:
        D (1D numpy array): Demand for domestically produced good i from importers
    '''
    D = (gamma**eta * deltad * pq / pd) ** (1 / (1 - eta)) * Q
    return pd

# no
def eqpd(gamma, deltam, deltad, eta, Q, pq, D):
    '''
    Price of domestically produced goods from importers.

    .. math::
        pd_{i} = \left(\gamma_{i}^{\eta_{i}}\delta^{d}_{i}pq_{i}\\right)\left(\\frac{D_{i}}{Q_{i}}\\right)^{\eta_{i}-1}

    Args:
        gamma (1D numpy array): Scale parameter for CES production function
        deltam (1D numpy array): Share parameter for use of imports of good i in produciton Armington good i
        deltad (1D numpy array): Share parameter for use of domestically produced good i in produciton Armington good i
        eta (1D numpy array): The elasticity of substitution between imports and domestically supplied good i
        Q (1D numpy array): The domestic supply of good i, the Armington good
        pq (1D numpy array): price of the Armington good (domestic + imports) for each good i
        D (1D numpy array): Demand for domestically produced good i from importers

    Returns:
        pd (1D numpy array): price of domesically produced good i
    '''
    pd = (gamma**eta * deltad * pq) * (D / Q) ** (eta - 1)
    return pd

# no
def eqZ(theta, xie, xid, phi, E, D):
    '''
    Exporting firm production function.

    .. math::
        Z_{i} = \\theta_{i}\left[\\xi_{i}^{E}E_{i}^{\phi_{i}} + \\xi_{i}^{D}D_{i}^{\phi_{i}}\\right]^{\\frac{1}{\phi_{i}}}

    Args:
        theta (1D numpy array):
        xie (1D numpy array): Share parameter for the share of exports of good i used by firms exporting good i
        xie (1D numpy array): Share parameter for the share of domestically produced good i used by firms exporting good i
        phi (1D numpy array): Elasticity of substitution between exports (??) and domestically produced goods by firms exporting good i
        E (1D numpy array): Exports of good i
        D (1D numpy array): Domestically produced good i

    Returns:
        Z (1D numpy array): Output from exporters CET production function
    '''
    Z = theta * (xie * E**phi + xid * D**phi) ** (1 / phi)
    return Z

# no
def eqE(theta, xie, tauz, phi, pz, pe, Z):
    '''
    Supply of exports.

    .. math::
        E_{i} = \left(\\theta_{i}^{\phi_{i}}\\xi^{E}_{i}(1+\\tau^{z}_{i}\\frac{pz_{i}}{pe_{i}})\\right)^{\\frac{1}{1-\phi_{i}}}Z_{i}

    Args:
        theta (1D numpy array):
        xie (1D numpy array): Share parameter for the share of exports of good i used by firms exporting good i
        tauz (1D numpy array): Ad valorem tax rate on commodity i
        phi (1D numpy array): Elasticity of substitution between exports (??) and domestically produced goods by firms exporting good i
        pz (1D numpy array): price of output good i
        pe (1D numpy array): Price of commodity i exports in domestic currency
        Z (1D numpy array): Output from exporters CET production function

    Returns:
        E (1D numpy array): Exports of good i
    '''
    E = (theta**phi * xie * (1 + tauz) * pz / pe) ** (1 / (1 - phi)) * Z
    return E

