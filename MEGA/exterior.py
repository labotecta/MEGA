import numpy as np

def precio_moneda_local_pe_pm(pWe, pWm, epsilon):
    return (pWe * epsilon, pWm * epsilon)

def equilibrio_balance_pagos_moneda_extranjera(pWe, E, pWm, M, Sf):
    '''
    Restricción a la balanza de pagos, se debe mantener la misma diferencia 'Sf' entre las importaciones y las exportaciones en divisas que hay en la MCS 
    ya que debe haber una correlación entre los ingresos (exportaciones) y pagos (importaciones) en divisas: la que muestra la MCS
    pWe  : precio de las exportaciones con la cotización inicial de la MCS (lo que equivale a moneda extranjera de la unidad de cantidad arbitraria para que sea 1.) 
    E    : exportaciones
    pWm  : precio de las importaciones con la cotización inicial de la MCS (lo que equivale a moneda extranjera de la unidad de cantidad arbitraria para que sea 1.)
    M    : importaciones
    Sf   : déficit por cuenta corriente en moneda extranjera (igual al ahorro exterior), una variable exógena = importaciones - exportaciones
    Lo calculamos con los precios iniciales (pWe, pWm) para que los cambios en la cotización no distorsionen el equilibrio en divisas
    '''
    '''
    nsec = len(pWe)
    impor = 0.
    expor = 0.
    for j in range(nsec):
        impor += pWm[j] * M[j]
        expor += pWe[j] * E[j]
    return Sf - (impor - expor)
    '''
    return Sf - (M.dot(pWm) - E.dot(pWe))

# función CES de sustitución con la que determinar el óptimo entre importar (M) o
# producir localmente (D), para cubrir la demanda del producto de Armington (Q)

def produccion_armington_Q(gamma, deltam, deltad, M, D, eta):
    '''
    gamma : coeficiente de escala de la función de utilidad. Productividad total de los factores

    dm    : coeficiente de participación de la producción importada en la función de utlidad para cada sector
    dd    : coeficiente de participación de la produccion local en la función de utlidad para cada sector
    M     : cantidad importada
    D     : produccion para la demanda local
    eta   : parametro de elasticidad ro = (sigma - 1) / sigma
    '''
    '''
    nsec = gamma.shape[0]
    Q = np.empty((nsec), dtype=np.float64)
    for i in range(nsec):
        Q[i] = gamma[i] * (deltam[i] * M[i] ** eta[i] + deltad[i] * D[i] ** eta[i]) ** (1. / eta[i])
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

# función CET de transformacion de la producción bruta (Z) de un producto, en exportación (E) y sumnistro local (D)

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
