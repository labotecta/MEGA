import numpy as np

def precio_moneda_local_pe_pm(pWe, pWm, epsilon):
    return (epsilon * pWe, epsilon * pWm)

def balance_pagos_moneda_extranjera(pWe, E, pWm, M, Sf):
    '''
    Restricción a la balanza de pagos, las importaciones deben ser igual a las exportaciones más la balanza de pagos inicial (exógena)
    pWe  : precio de las exportaciones en moneda extranjera
    E    : exportaciones
    pWm  : precio de las importaciones en moneda extranjera
    M    : importaciones
    Sf   : déficit por cuenta corriente en moneda extranjera (igual al ahorro exterior), una variable exógena
    '''
    '''
    nsec = len(pWe)
    expor = Sf
    impor = 0.
    for j in range(nsec):
        expor += pWe[j] * E[j]
        impor += pWm[j] * M[j]
    return expor - impor
    '''
    return (Sf + E.dot(pWe)) - M.dot(pWm)

def produccion_armington_Q(gamma, deltam, deltad, M, D, eta):
    '''
    gamma : coeficiente de escala de la función de utilidad
    dm    : coeficiente de participación de la producción importada en la función de utlidad para cada sector
    dd    : coeficiente de participación de la produccion local en la función de utlidad para cada sector
    M     : cantidad importada
    D     : produccion para la demanda local
    eta   : parametro de elasticidad ro = (sigma -1) / sigma
    '''
    '''
    nsec = gamma.shape[0]
    Q = np.empty((nsec), dtype=np.float64)
    for i in range(nsec):
        Q[i] = gamma[i] * (deltam[i] * M[i] ** eta[i] + deltad[i] * D[i] ** eta[i]) ** (1./eta[i])
    return Q
    '''
    return gamma * (deltam * np.sign(M) * (np.abs(M) ** eta) + deltad * np.sign(D) * (np.abs(D) ** eta)) ** (1./eta)

def importacion_maxima_utilidad_armington_M(gamma, deltam, pq, pm, Q, eta, taum):
    '''
    invro = 1. / (1. - eta)
    nsec = gamma.shape[0]
    M = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        M[i] = Q[i] * ((gamma[i] ** eta[i]) * deltam[i] * pq[i] / ((1. + taum[i]) * pm[i])) ** invro[i]
    return M
    '''
    return Q * ((gamma ** eta) * deltam * pq / ((1. + taum) * pm)) ** (1. / (1. - eta))

def produccion_maxima_utilidad_armington_D(gamma, deltad, pq, pd, Q, eta):
    '''
    invro = 1. / (1. - eta)
    nsec = gamma.shape[0]
    D = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        D[i] = Q[i] * ((gamma[i] ** eta[i]) * deltad[i] * pq[i] / pd[i]) ** invro[i]
    return D
    '''
    return Q * ((gamma ** eta) * deltad * pq / pd) ** (1. / (1. - eta))

# transformacion de la producción bruta (Z) de un producto en exportación (E) y sumnistro local (D)

def produccion_para_exportacion_E(teta, xie, pz, pe, Z, phi, tauz, CssE, AgE, Apz):
    '''
    Cuanto de la producción bruta 'Z' se exporta es función de la diferenca entre el precio
    total de producir 'Z', es decir 'pz + impuestos y otras posibles cargas (como la seguridad social)' y el
    precio de exportación 'pe'. Si 'pz incrementado' es mucho MAYOR que 'pe', no se produciría nada 
    para exportación.

    teta : coeficiente de escala de la función de utilidad
    xie  : coefcientes de participacion del producto exportado en la función de utlidad para cada sector
    pz   : precio de los productos
    pe   : precio de exportación en moneda local
    Z    : producción total del sector
    phi  : parametro de elasticidad
    tauz : impuesto a la producción local
    '''
    '''
    invfi = 1. / (1. - phi)
    nsec = len(pz)
    E = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        E[i] = Z[i] * ((teta[i] ** phi[i]) * (1. + tauz[i]) * pz[i] * xie[i] / pe[i]) ** invfi[i]
    return E
    '''
    # transformamos la cotización a la seguridad social en un precio a la producción
    # hay que considerar la cotización a la seguridad social (CssE) como un mayor coste de la producción bruta (Z) en el cálculo de
    # 'E' y 'D', es decir, un mayor precio (pz) al igual que (tauz)
    # transformamos los ayudas del gobierno en un menor impuesto
    return Z * ((teta ** phi) * (1. + tauz + CssE / Z - AgE / Z + Apz) * pz * xie / pe) ** (1. / (1. - phi))

def produccion_para_local_D(teta, xid, pz, pd, Z, phi, tauz, CssE, AgE, Apz):
    '''
    Cuanto de la producción bruta 'Z' es fruto de la importación es función de la diferenca entre el precio
    total de producir 'Z', es decir 'pz + impuestos y otras posibles cargas (como la seguridad social)' y el
    precio de importación (pm). Si 'pz incrementado' es mucho MENOR que 'pm', no se importaría nada ya que
    es preferible producirlo localmente.

    teta : coeficiente de escala de la función de utilidad
    xid  : coefcientes de participacion del producto local en la función de utlidad para cada sector
    pz   : precio de los productos
    pd   : precio para la demanda
    Z    : producción total del sector
    phi  : parametro de elasticidad
    tauz : impuesto a la producción local
    '''
    '''
    invfi = 1. / (1. - phi)
    nsec = len(pz)
    D = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        D[i] = Z[i] * ((teta[i] ** phi[i]) * (1. + tauz[i]) * pz[i] * xid[i] / pd[i]) ** invfi[i]
    return D
    '''
    # transformamos la cotización a la seguridad social en un precio a la producción
    # hay que considerar la cotización a la seguridad social (CssE) como un mayor coste de la producción bruta (Z) en el cálculo de
    # 'E' y 'D', es decir, un mayor precio (pz) al igual que 'tauz'
    # transformamos los ayudas del gobierno en un menor impuesto
    return Z * ((teta ** phi) * (1. + tauz + CssE / Z - AgE / Z + Apz) * pz * xid / pd) ** (1. / (1. - phi))

def restriccion_producción_bruta_Z(teta, xie, xid, E, D, phi):
    '''
    invfi = 1. / phi
    nsec = len(teta)
    Z = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        Z[i] = teta[i] * (xie[i] * (E[i] ** phi[i]) + xid[i] * (D[i] ** phi[i])) ** invfi[i]
    return Z
    '''
    base = xie * np.sign(E) * (np.abs(E) ** phi) + xid * np.sign(D) * (np.abs(D) ** phi)
    return teta * np.sign(base) * (np.abs(base) ** (1. / phi))
