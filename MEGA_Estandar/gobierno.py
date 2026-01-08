import numpy as np

def impuestos_directos(tid, pf, wf):
    '''
    impuestos directos como una tasa sobre el total de ingresos de los hogares (CAP y LAB)

    tid : tasa de impuestos directos
    '''
    nsec = wf.shape[0]
    nfac = wf.shape[1]
    # suma de todos los factores utilizados por los el total de sectores
    Td = 0.
    for i in range(nsec):
        for j in range(nfac):
            Td += wf[i,j] * pf[j]
    Td *= tid
    return Td

def impuestos_produccion(tauz, pz, Z):
    '''
    impuestos a la producción de cada sector

    tauz : vector de tasas a la producción de cada sector
    pz   : vector precios de los productos
    Z    : vector producciones de los sectores
    '''
    nsec = len(pz)
    Tz = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        Tz[i] = tauz[i] * Z[i] * pz[i]
    return Tz

def aranceles_importacion(ta, pi, M):
    '''
    aranceles de importación por cada producto

    ta : vector aranceles a cada producto
    pi : vector precio de importación de cada producto
    M : vector cantidades importadas de cada producto
    '''
    nsec = len(pi)
    Tm = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        Tm[i] = ta[i] * M[i] * pi[i]
    return Tm

def demanda_gobierno(mu, pq, Td, Tz, Tm, Sg):
    '''
    demanda (consumos) de productos por el gobierno

    mu : coeficiente de reparto de la demanda del gobierno por productos
    pq : precio de producto de Armington (producto compuesto local + importación)
    Td : impuestos directos
    Tz : impuestos a la producción
    Tm : aranceles de importación
    Sg : ahorro del gobierno
    '''
    nsec = len(pq)
    Xg = np.zeros(nsec, dtype=np.float64)
    ingresos = Td + Tz.sum() + Tm.sum() - Sg
    for i in range(nsec):
        Xg[i] = mu[i] * ingresos / pq[i]
    return Xg
