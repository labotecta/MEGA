import copy
import numpy as np

def precio_moneda_local_pe_pm(pWe, pWm, epsilon):
    return (pWe * epsilon, pWm * epsilon)

def equilibrio_balance_pagos_moneda_extranjera(pWe, E, pWm, M, Sf):
    '''
    Restricción a la balanza de pagos, se debe mantener la misma diferencia 'Sf' entre las importaciones y las exportaciones en divisas que hay en la MCS 
    ya que debe haber una correlación entre los ingresos (exportaciones) y pagos (importaciones) en divisas: la que muestra la MCS
    pWe  : precio de las exportaciones con la cotización inicial de la MCS, para que sea comparable a Sf (lo que equivale a moneda extranjera de la unidad de cantidad arbitraria para que sea 1.) 
    E    : exportaciones
    pWm  : precio de las importaciones con la cotización inicial de la MCS, para que sea comparable a Sf  (lo que equivale a moneda extranjera de la unidad de cantidad arbitraria para que sea 1.)
    M    : importaciones
    Sf   : déficit por cuenta corriente en moneda extranjera (igual al ahorro exterior), una variable exógena = importaciones - exportaciones
    Lo calculamos con los precios iniciales (pWe, pWm) para que los cambios en la cotización no distorsionen el equilibrio en divisas
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
    return gamma * (deltam * np.copysign(1, M) * (np.abs(M) ** eta) + deltad * np.copysign(1, D) * (np.abs(D) ** eta)) ** (1./eta)

def importacion_maxima_utilidad_armington_M(gamma, deltam, pq, pm, Q, eta, taum):
    #return Q * ((gamma ** eta) * deltam * pq / ((1. + taum) * pm)) ** (1. / (1. - eta))

    ImM = (gamma ** eta) * deltam * pq
    tasa = taum
    # se incrementa el precio con el arancel
    precio = pm * (1. + tasa)
    return Q * (ImM / precio) ** (1. / (1. - eta))

def produccion_maxima_utilidad_armington_D(gamma, deltad, pq, pd, Q, eta):
    #return Q * ((gamma ** eta) * deltad * pq / pd) ** (1. / (1. - eta))

    ImD = (gamma ** eta) * deltad * pq
    base = ImD / pd
    return Q * np.copysign(1, base) * (abs(base) ** (1. / (1. - eta)))

# función CET de transformacion de la producción bruta (Z) de un producto, en exportación (E) y sumnistro local (D)

def produccion_para_exportacion_E(teta, xie, pz, pe, Z, phi, tauz, CssE, AgE, Apz, ctzssez, ctzagez, modo_pseudoimptos):
    '''
    Cuanto de la producción bruta 'Z' se exporta es función de la diferenca entre el precio
    total de producir 'Z', es decir 'pz + impuestos y otras posibles cargas (como la seguridad social)' y el
    precio de exportación 'pe'. Si 'pz incrementado' es mucho MAYOR que 'pe', no se produciría nada 
    para exportación.

    Transformamos la cotización a la seguridad social en un precio a la producción
    hay que considerar la cotización a la seguridad social (CssE) como un mayor coste de la producción bruta (Z) en el cálculo de
    'E' y 'D', es decir, un mayor precio (pz) al igual que (tauz)
    transformamos los ayudas del gobierno en un menor impuesto

    Para corregir estos pseudoimpuestos introducimos la variable de holgura Apz
    Apz es único para todos los sectores lo que implica 'transferencias' entre sectores
    que se ponen de manifiesto en la MCS reconstruida.
    No podemos usar un Apz por sector porque es aumentar el número de variables endógenas y
    el modelo se hace infactible

    teta : coeficiente de escala de la función de utilidad
    xie  : coefcientes de participacion del producto exportado en la función de utlidad para cada sector
    pz   : precio de los productos
    pe   : precio de exportación en moneda local
    Z    : producción total del sector
    phi  : parametro de elasticidad
    tauz : impuesto a la producción local
    '''
    s_teta = np.copysign(1, teta)
    b_teta = abs(teta)
    expo = 1. / (1. - phi)
    if modo_pseudoimptos == 0:
        if np.any(xie == 0):
            nsec = xie.shape[0]
            E = np.zeros(nsec, dtype=np.float64)
            for i in range(nsec):
                if xie[i] > 0:
                    base = (s_teta[i] * (b_teta[i] ** phi[i]) * (1. + tauz[i] + (CssE[i] - AgE[i]) / Z[i] + Apz) * pz[i] * xie[i] / pe[i]).item()
                    E[i] = Z[i] * np.copysign(1, base) * (abs(base) ** expo[i])
        else:
            base = s_teta * (b_teta ** phi) * (1. + tauz + (CssE - AgE) / Z + Apz) * pz * xie / pe
            E = Z * np.copysign(1, base) * (abs(base) ** expo)
    else:
        if np.any(xie < 0.000001):
            nsec = xie.shape[0]
            E = np.zeros(nsec, dtype=np.float64)
            for i in range(nsec):
                if xie[i] > 0.000001:
                    base = (s_teta[i] * (b_teta[i] ** phi[i]) * (1. + tauz[i] + ctzssez[i] - ctzagez[i] + Apz) * pz[i] * xie[i] / pe[i]).item()
                    E[i] = Z[i] * np.copysign(1, base) * (abs(base) ** expo[i])
        else:
            base = s_teta * (b_teta ** phi) * (1. + tauz + ctzssez - ctzagez + Apz) * pz * xie / pe
            E = Z * np.copysign(1, base) * (abs(base) ** expo)
    return E

def produccion_para_local_D(teta, xid, pz, pd, Z, phi, tauz, CssE, AgE, Apz, ctzssez, ctzagez, modo_pseudoimptos):
    '''
    Cuanto de la producción bruta 'Z' es fruto de la importación es función de la diferenca entre el precio
    total de producir 'Z', es decir 'pz + impuestos y otras posibles cargas (como la seguridad social)' y el
    precio de importación (pm). Si 'pz incrementado' es mucho MENOR que 'pm', no se importaría nada ya que
    es preferible producirlo localmente.

    Transformamos la cotización a la seguridad social en un precio a la producción
    hay que considerar la cotización a la seguridad social (CssE) como un mayor coste de la producción bruta (Z) en el cálculo de
    'E' y 'D', es decir, un mayor precio (pz) al igual que (tauz)
    transformamos los ayudas del gobierno en un menor impuesto

    Para corregir estos pseudoimpuestos introducimos la variable de holgura Apz
    Apz es único para todos los sectores lo que implica 'transferencias' entre sectores
    que se ponen de manifiesto en la MCS reconstruida.
    No podemos usar un Apz por sector porque es aumentar el número de variables endógenas y
    el modelo se hace infactible

    teta : coeficiente de escala de la función de utilidad
    xid  : coefcientes de participacion del producto local en la función de utlidad para cada sector
    pz   : precio de los productos
    pd   : precio para la demanda
    Z    : producción total del sector
    phi  : parametro de elasticidad
    tauz : impuesto a la producción local
    '''
    s_teta = np.copysign(1, teta)
    b_teta = abs(teta)
    expo = 1. / (1. - phi)
    if modo_pseudoimptos == 0:
        if np.any(xid < 0.000001):
            nsec = xid.shape[0]
            D = np.zeros(nsec, dtype=np.float64)
            for i in range(nsec):
                if xid[i] > 0.000001:
                    base = (s_teta[i] * (b_teta[i] ** phi[i]) * (1. + tauz[i] + (CssE[i] - AgE[i]) / Z[i] + Apz) * pz[i] * xid[i] / pd[i]).item()
                    D[i] = Z[i] * np.copysign(1, base) * (abs(base) ** expo[i])
        else:
            base = s_teta * (b_teta ** phi) * (1. + tauz + (CssE - AgE) / Z + Apz) * pz * xid / pd
            D = Z * np.copysign(1, base) * (abs(base) ** expo)
    else:
        if np.any(xid < 0.000001):
            nsec = xid.shape[0]
            D = np.zeros(nsec, dtype=np.float64)
            for i in range(nsec):
                if xid[i] >  0.000001:
                    base = (s_teta[i] * (b_teta[i] ** phi[i]) * (1. + tauz[i] + ctzssez[i] - ctzagez[i] + Apz) * pz[i] * xid[i] / pd[i]).item()
                    D[i] = Z[i] * np.copysign(1, base) * (abs(base) ** expo[i])
        else:
            base = s_teta * (b_teta ** phi) * (1. + tauz + ctzssez - ctzagez + Apz) * pz * xid / pd
            D = Z * np.copysign(1, base) * (abs(base) ** expo)
    return D

def restriccion_produccion_bruta_Z(teta, xie, xid, E, D, phi):
    # phi es normalmente positivo luego no importa que E sea 0
    base1 = xie * np.copysign(1, E) * (np.abs(E) ** phi)
    base2 = xid * np.copysign(1, D) * (np.abs(D) ** phi)
    base  =  base1 + base2
    Z = teta * np.copysign(1, base) * (np.abs(base) ** (1. / phi))
    return Z
