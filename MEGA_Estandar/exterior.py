import numpy as np

def precio_moneda_local(peme, pime, epsilon):
    pm = epsilon * peme
    pi = epsilon * pime
    return (pm, pi)

def balance_pagos_moneda_extranjera(peme, E, pime, M, Sf):
    '''
    Restricción a la balanza de pagos, las importaciones deben ser igual a las exportaciones mas la balanza de pagos inicial (exógena)
    peme : precio de las exportaciones en moneda extranjera
    E    : exportaciones
    pime : precio de las importaciones en moneda extranjera
    M    : importaciones
    Sf   : déficit por cuenta corriente en moneda extranjera (igual al ahorro exterior), una variable exógena
    '''
    nsec = len(peme)
    expor = Sf
    impor = 0.
    for j in range(nsec):
        expor += pime[j] * E[j]
        impor += peme[j] * M[j]
    return expor - impor

def balance_pagos_moneda_local(pe, E, pi, M, Sf, epsilon):
    '''
    Sf : déficit por cuenta corriente en moneda extranjera (igual al ahorro exterior), una variable exógena
    '''
    nsec = len(pe)
    imp = Sf * epsilon
    exp = 0.
    for j in range(nsec):
        imp += pe[j] * E[j]
        exp += pi[j] * M[j]
    return (imp, exp)

def beneficio_produccion_armington(pa, Q, ta, pi, p, D):
    '''
    beneficio = ingreso - coste
        ingreso = precio por camtidad de producto armington
        coste   = precio del producto importado con aranceles + precio del producto local por la producción local

    pa : precio del producto armington
    Q  : cantidad de producto armington
    ta : aranceles de importación
    pi : precio de importación
    p  : precio de los productos
    D  : producción local 
    '''
    nsec = len(p)
    u = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        u[i] = pa[i] * Q[i] - ( (1 + ta[i]) * pi[i] * M[i] + p[i] * D[i])
    return u

def produccion_armington(gamma, deltam, deltad, M, D, eta):
    '''
    landa : coeficiente de escala de la función de utilidad
    dm    : coeficiente de participación de la producción importada en la función de utlidad para cada sector
    dd    : coeficiente de participación de la produccion local en la función de utlidad para cada sector
    M     : cantidad importada
    D     : produccion local
    eta   : parametro de elasticidad ro = (sigma -1) / sigma
    '''
    nsec = len(gamma)
    Q = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        Q[i] = gamma[i] * (deltam[i] * M[i] ** eta[i] + deltad[i] * D[i] ** eta[i]) ** (1./eta[i])
    return Q

def importacion_maxima_utilidad_armington(gamma, deltam, pq, pm, Q, eta, taum):
    invro = 1. / (1. - eta)
    nsec = len(gamma)
    M = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        M[i] = Q[i] * ((gamma[i] ** eta[i]) * deltam[i] * pq[i] / ((1. + taum[i]) * pm[i])) ** invro[i]
    return M

def produccion_maxima_utilidad_armington(gamma, deltad, pq, pd, Q, eta):
    invro = 1. / (1. - eta)
    nsec = len(gamma)
    D = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        D[i] = Q[i] * ((gamma[i] ** eta[i]) * deltad[i] * pq[i] / pd[i]) ** invro[i]
    return D

# transformacion de la demanda domestica (Z) de un producto en exportación (E) y sumnistro local (D)

def produccion_para_exportacion(teta, xie, pz, pe, Z, phi, tauz):
    '''
    teta : coeficiente de escala de la función de utilidad
    xie  : coefcientes de participacion del producto exportado en la función de utlidad para cada sector
    pz   : precio de los productos
    pe   : precio de exportación en moneda local
    Z    : producción total del sector
    phi  : parametro de elasticidad
    tauz : impuesto a la producción local
    '''
    invfi = 1. / (1. - phi)
    nsec = len(pz)
    E = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        #E[i] = Z[i] * ((teta[i] ** phi[i]) * xie[i] * (1. + tauz[i]) * pz[i] / pe[i]) ** invfi[i]
        E[i] = Z[i] * ((teta[i] ** phi[i]) * (1. + tauz[i]) * pz[i] * xie[i] / pe[i]) ** invfi[i]
    return E

def produccion_para_local(teta, xid, pz, pd, Z, phi, tauz):
    '''
    teta : coeficiente de escala de la función de utilidad
    xid  : coefcientes de participacion del producto local en la función de utlidad para cada sector
    pz   : precio de los productos
    pd   : precio para la demanda
    Z    : producción total del sector
    phi  : parametro de elasticidad
    tauz : impuesto a la producción local
    '''
    invfi = 1. / (1. - phi)
    nsec = len(pz)
    D = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        #D[i] = Z[i] * ((teta[i] ** phi[i]) * xid[i] * (1. + tauz[i]) * pz[i] / pd[i]) ** invfi[i]
        D[i] = Z[i] * ((teta[i] ** phi[i]) * (1. + tauz[i]) * pz[i] * xid[i] / pd[i]) ** invfi[i]
    return D

def restriccion_producción_bruta(teta, xie, xid, E, D, phi):
    invfi = 1. / phi
    nsec = len(teta)
    Z = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        Z[i] = teta[i] * (xie[i] * (E[i] ** phi[i]) + xid[i] * (D[i] ** phi[i])) ** invfi[i]
    return Z
