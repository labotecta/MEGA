import numpy as np

def CobbDouglas_alfa(X):
    '''
    calcula los valores del parámetro alfa de la funcion de utilidad.
    igual a la fracción de producto demandado por cada consumidor, dividido por su total demandado
    
    argumentos:
        X: demanda de los hogares a cada sector len(dem) x len(ind)
    '''
    ndem = X.shape[0]
    nsec = X.shape[1]
    suma = X.sum(axis=1)    # demanda total de cada hogar
    alfa = np.zeros((ndem,nsec), dtype=np.float64)
    for k in range(ndem):
        for i in range(nsec):
            alfa[k,i] = X[k,i] / suma[k]
    return alfa

def CobbDouglas_beta(F):
    '''
    Obtiene, para cada sector, los coeficientes de participación (beta) de los factores en la función de producción
    F : utilización de factores por cada sector (2, 2)
    '''
    nsec = F.shape[0]
    nfac = F.shape[1]
    beta = np.ones((nsec,nfac))
    denominador = F.sum(axis=1) # suma por fila (sector) (len(ind), )
    for i in range(nsec):
        for j in range(nfac):
            beta[i,j] = F[i,j] / denominador[i]
    return beta

def CobbDouglas_b(Y, F, beta):
    '''
    El factor de escala, en el contexto de la función de producción, se refiere a cómo cambia
    la producción cuando todos los factores de producción se incrementan en la misma proporción
    '''
    nsec = F.shape[0]
    nfac = F.shape[1]
    denominador = np.ones(nsec)
    for i in range(nsec):
        for j in range(nfac):
            denominador[i] *= F[i,j] ** beta[i,j]
    return Y / denominador

def coeficientes_consumos_intermedios_ax(X, Z):
    '''
    Cantidad de producto intermedio 'j' necesario para producir una unidad de producto 'i'
    X : consumos (imputs) intermedios de los sectores en las columnas  (2, 2)
    Z : producción de cada sector = factor compuesto + ventas intermedias  (2, )
    '''
    nsec = X.shape[0]
    ax = np.zeros((nsec,nsec),dtype=np.float64)
    for i in range(nsec):
        for j in range(nsec):
            ax[i,j] = X[j,i] / Z[i]
    ax[ax == np.inf] = 0                    # porque el denominador puede ser 0, antes de np.nan_to_num porque puede cambiar el inf por un número
    np.nan_to_num(ax, copy=False)           # si no hay datos (NAN) se sustituye por 0
    return ax

def coeficientes_factor_compuesto_ay(Y, Z):
    '''
    Cantidad de factor compuesto necesario para producir una unidad de producto 'i'
    Y = factor compuesto para cada sector, igual a la suma de los factores utilizados por el sector en la MCS (2, )
    Z : producción de cada sector = factor compuesto + ventas intermedias (2, )
    '''
    # división elemento a elemnto
    ay = Y / Z
    ay[ay == np.inf] = 0                    # porque el denominador puede ser 0, antes de np.nan_to_num porque puede cambiar el inf por un número
    np.nan_to_num(ay, copy=False)           # si no hay datos (NAN) se sustituye por 0
    return ay

def coeficientes_demanda_gobierno_mu(X):
    '''
    Coeficiente para repartir la demanda total del gobierno entre sectores
    X : demanda del gobierno a cada sector
    '''
    return X / X.sum()

def coeficientes_inversiones_landa(Xv, Sp, Sg, Sf):
    '''
    Coeficiente para repartir por sectores los ahorros
    Xv : ingresos de los sectores aportados por 'INV'
    Sp : ahorro de los hogares
    Sg : ahorro del gobierno
    Sf : ahorro exterior
    '''
    landa = Xv / (Sp.sum() + Sg + Sf)
    return landa
    
def coeficientes_armington_deltam_deltad(taum, eta, M, D):
    '''
    Coeficiente de participación (deltam) de la importación (M) y coeficiente (deltad) de la producción local (D)
    en la función del producto de Armington. Suman 1.

    taum : tasa de aranceles a la importación
    eta  : parámetro de elasticidad de sustitución, entre local e importación, del producto de Argminton (CES)
    M    : importaciones pagadas por los sectores
    D    : demanda local de cada sector
    '''
    a = (1 + taum) * (M ** (1 - eta)) # se añaden los aranceles a la importación
    b = (1 + taum) * (M ** (1 - eta)) + D ** (1 - eta)
    deltam = a / b
    a = D ** (1 - eta)
    deltad = a / b
    return (deltam, deltad)

def coeficiente_escala_armington_gamma(Q, deltam, deltad, eta, M, D):
    '''
    gamma

    Q      : cantidades vendidas del producto de Arminton por cada sector
    deltam : coeficiente de participación de la importación (M) en la función del producto de Armington
    deltad : coeficiente de participación de la demanda local (D) en la función del producto de Armington
    eta    : parámetro de elasticidad de sustitución, entre local e importación, del producto de Argminton (CES)
    M      : importaciones pagadas por los sectores
    D      : demanda local de cada sector
    '''
    return Q / ((deltam * (M ** eta) + deltad * (D ** eta)) ** (1. / eta))

def coeficiente_CET_local_xid(fi, E, D):
    '''
    Coeficiente de participación en la CET de la demanda local para cada sector
    '''
    umfi = 1 - fi
    xid = (D ** umfi) / (E ** umfi + D ** umfi)
    return xid

def coeficiente_CET_exportacion_xie(fi, E, D):
    '''
    Coeficiente de participación en la CET de la exportación para cada sector
    '''
    umfi = 1 - fi
    xie = (E ** umfi) / (E ** umfi + D ** umfi)
    # si E tiene algún valor a 0 y 'umfi' es negativo se produce una división por 0
    # por lo que la instrucción siguiente sustiyuiora el NAN resultante por 0
    np.nan_to_num(xie, copy=False)
    return xie

def coeficiente_escala_CET_teta(Z, xie, E, xid, D, fi):
    '''
    Coeficiente de escala de la CET de exportación
    '''
    teta = Z / ((xie * E ** fi + xid * D ** fi) ** (1/fi))
    teta[teta == np.inf] = 0                # antes de np.nan_to_num porque puede cambiar el inf por un número
    np.nan_to_num(teta, copy=False)         # si no hay datos (NAN) se sustituye por 0
    return teta

def propension_ahorro_hogares_ssp(Sp, FF, PssH):
    '''
    Propensión al ahorro de los hogares
    '''
    '''
    ndem = FF.shape[0]
    ssp = np.empty(ndem, dtype=np.float64)
    suma = FF.sum(axis=1)
    for k in range(ndem):
        ssp[k] = Sp[k] / suma[k]
    '''
    ingresos = FF.sum(axis=1) + PssH
    ingresos[Sp == 0] = 1.          # para evitar divisiones por 0
    ssp = Sp / ingresos 
    #ssp[ssp == np.inf] = 0          # antes de np.nan_to_num porque puede cambiar el inf por un número
    #np.nan_to_num(ssp, copy=False)  # si no hay datos (NAN) se sustituye por 0
    return ssp

def tasa_impuestos_directos_taud(Td, FF, PssH):
    '''
    Tasa de impuestos directos a cada hogar sobre sus ingresos por prestación de feactores + pensiones

    Td   : impuestos directos pagados por cada hogar
    FF   : factores prestados por cada hogar
    PssH : ingresos de los hogares recibidos de la seguridad social (pensiones)
    '''
    ingresos = FF.sum(axis=1) + PssH
    ingresos[Td == 0] = 1.              # para evitar divisiones por 0
    taud = Td / ingresos
    #taud[taud == np.inf] = 0            # antes de np.nan_to_num porque puede cambiar el inf por un número
    #np.nan_to_num(taud, copy=False)     # si no hay datos (NAN) se sustituye por 0
    return taud

def propension_ahorro_gobierno_ssg(Sg, Td, Tz, Tm, AgE, AgH):
    '''
    Propensión al ahorro del gobierno

    Hay que restar las pensiones porque están incluidas en Td y no las ingresa el gobierno
    '''
    ssg = Sg / (Td.sum() + Tz.sum() + Tm.sum() - AgE.sum() - AgH.sum())
    ssg = np.nan_to_num(ssg)      # si no hay datos (NAN) se sustituye por 0
    return ssg

def coeficiente_ayudas_gobierno_empresas_cage(AgE, Td, Tz, Tm):
    cage = AgE / (Td.sum() + Tz.sum() + Tm.sum())
    cage[cage == np.inf] = 0       # antes de np.nan_to_num porque puede cambiar el inf por un número
    cage = np.nan_to_num(cage)     # si no hay datos (NAN) se sustituye por 0
    return cage

def coeficiente_ayudas_gobierno_hogares_cagh(AgH, Td, Tz, Tm):
    cagh = AgH / (Td.sum() + Tz.sum() + Tm.sum())
    cagh[cagh == np.inf] = 0       # antes de np.nan_to_num porque puede cambiar el inf por un número
    cagh = np.nan_to_num(cagh)     # si no hay datos (NAN) se sustituye por 0
    return cagh

def poblacion_activa_PobAct(INDICE_F_TRA, FF0, paro):
    '''
    Población activa
    FF0  = aportación inicial de factores por los hogares
    paro = tasa de paro inicial en tanto por uno
    '''
    pobact = FF0[:,INDICE_F_TRA].sum() / (1. - paro)
    return pobact

