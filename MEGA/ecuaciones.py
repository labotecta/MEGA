import numpy as np

def demanda_CobbDouglas_alfa(Xp):
    '''
    calcula los valores del parámetro alfa de la funcion de utilidad.
    igual a la fracción de producto demandado por cada consumidor, dividido por su total demandado
    al normalizarlos a 1 no se necesitan los precios de los productos ni la renta de los hogares
    
    argumentos:
        X: demanda de los hogares a cada sector len(dem) x len(ind)
    '''
    ndem = Xp.shape[0]
    nsec = Xp.shape[1]
    suma = Xp.sum(axis=1)    # demanda total de cada hogar
    suma[suma == 0] = 1.
    alfa = np.zeros((ndem,nsec), dtype=np.float64)
    for consu in range(ndem):
        for sector in range(nsec):
            alfa[consu,sector] = Xp[consu,sector] / suma[consu]
    '''
    #def demanda_CobbDouglas_alfa(FF, PssH, AgH, Sp, Td, CssH, Xp, pf, pq, inc_dem_tipo, inc_dem):
    nfac = FF.shape[1]
    alfa_2 = np.zeros((ndem,nsec), dtype=np.float64)
    ingreso_neto = AgH + PssH - (Sp + Td + CssH)            # ingreso total de cada hogar
    for consu in range(ndem):
        for factor in range(nfac):
            ingreso_neto[consu] += FF[consu,factor] * pf[factor]

    # se detrae de los ingresos lo que costará el incremento de demanda
    for sector in range(nsec):
        if inc_dem_tipo == 0:
            ingreso_neto[consu] -= inc_dem[consu, sector]
        else:
            ingreso_neto[consu] -= inc_dem[consu, sector] * pq[sector]
    for consu in range(ndem):
        for sector in range(nsec):
            alfa_2[consu,sector] = Xp[consu,sector] / ingreso_neto[consu]
    
    assert np.all(alfa - alfa_2 < 0.0001), 'calculo a:\n{}\ncalculo b:\n{}'.format(alfa, alfa_2)
    '''
    return alfa

def demanda_CES_alfa(sigma, Xp):
    '''
    1. - eta = 1. / sigma
    '''
    ndem = Xp.shape[0]
    nsec = Xp.shape[1]
    alfa = np.zeros((ndem,nsec), dtype=np.float64)
    for consu in range(ndem):
        a = Xp[consu] ** (1. / sigma[consu])
        suma = a.sum()
        if suma == 0:
           suma = 1.
        for sector in range(nsec):
            alfa[consu,sector] = a[sector] / suma
    return alfa

def demanda_StoneGeary_renta(FF, PssH, AgH, Sp, Td, CssH, Xp, con_esen, pf, pq):
    '''
    para comprobar que todas las rentas son mayores que los consumos esenciales
    '''
    nfac = FF.shape[1]
    ndem = Xp.shape[0]
    ingreso_neto = AgH + PssH - (Sp + Td + CssH)            # ingreso total de cada hogar
    for consu in range(ndem):
        for factor in range(nfac):
            ingreso_neto[consu] += FF[consu,factor] * pf[factor]
    gasto_esencial   = (con_esen * pq).sum(axis=1)          # gasto esencial de cada hogar
    renta_disponible = ingreso_neto - gasto_esencial        # renta una vez pagados los consumos esenciales
    return renta_disponible

def demanda_StoneGeary_alfa(FF, PssH, AgH, Sp, Td, CssH, Xp, con_esen, pf, pq):
    '''
    calcula los valores del parámetro alfa de la funcion de utilidad con consumos esenciales (Stone Geary).
    
    argumentos:
        renta    : ingresos de  cada hogar
        X        : cantidad demandada por cada hogar a cada sector len(dem) x len(ind)
        con_esen : cantidad de consumo esencial de cada producto por cada hogar
        pQ       : precio de los produtos
    '''
    nfac = FF.shape[1]
    ndem = Xp.shape[0]
    nsec = Xp.shape[1]
    ingreso_neto = AgH + PssH - (Sp + Td + CssH)            # ingreso total de cada hogar
    for consu in range(ndem):
        for factor in range(nfac):
            ingreso_neto[consu] += FF[consu,factor] * pf[factor]
    gasto_esencial      = (con_esen * pq).sum(axis=1)       # gasto esencial de cada hogar
    renta_disponible    = ingreso_neto - gasto_esencial     # renta una vez pagados los consumos esenciales
    consumo_no_esencial = Xp - con_esen                     # cantidad de consumo de cada producto por encima del esencial
    alfa = np.zeros((ndem,nsec), dtype=np.float64)
    for k in range(ndem):
        for i in range(nsec):
            alfa[k,i] = consumo_no_esencial[k,i] * pq[i] / renta_disponible[k]
    return alfa

def demanda_CobbDouglas_beta(F):
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
            if denominador[i] < 0:
                beta[i,j] = 0.
            else:
                beta[i,j] = F[i,j] / denominador[i]
    return beta

def demanda_CobbDouglas_b(Y, F, beta):
    '''
    El factor de escala, en el contexto de la función de producción, se refiere a cómo cambia
    la producción cuando todos los factores de producción se incrementan en la misma proporción
    '''
    nsec = F.shape[0]
    nfac = F.shape[1]
    denominador = np.ones(nsec)
    for i in range(nsec):
        for j in range(nfac):
            if F[i,j] < 0:
                denominador[i] = 1.
                break
            else:
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
            # X[j,i] son las compras de 'i' a los sectores 'j'
            # Z[i] producción bruta del sector 'i'
            # ax[i,j] compras intermedias, por unidad de producción bruta, que hace el sector 'i' a los sectores 'j'
            if X[j,i] > 0.000001 and Z[i] != 0:
                ax[i,j] = X[j,i] / Z[i]
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

def coeficientes_inversiones_landa(Xv, Sp, Sg, Sc, epsilon, Sf, Ti, Te):
    '''
    Coeficiente para repartir por sectores los ahorros menos los impuestos al ahorro + inversión
    es el resultado de dividir la inversión en cada sector por la suma de los
    ahorros de todos los agentes menos los impuestos que paga A-I

    Xv : ingresos de los sectores aportados por 'INV'
    Sp : ahorro de los hogares
    Sg : ahorro del gobierno
    Sc : ahorro de la seguridad social
    Sf : ahorro exterior
    Ti : impuestos pagados por el ahorro

    Te : impuestos pagados por el sector exterior
    '''
    #return Xv / (Sp.sum() + Sg + Sc + Sf * epsilon - Ti - Te)
    return Xv / (Sp.sum() + Sg + Sc + Sf * epsilon - Ti)
    
def coeficientes_armington_deltam_deltad(taum, eta, M, D):
    '''
    Coeficiente de participación (deltam) de la importación (M) y coeficiente (deltad) de la producción local (D)
    en la función del producto de Armington. Suman 1.

    taum : tasa de aranceles a la importación
    eta  : parámetro de elasticidad de sustitución, entre local e importación, del producto de Argminton (CES)
    M    : importaciones pagadas por los sectores
    D    : demanda local de cada sector
    '''
    # mientras 'eta' sea menor que 1, no hay problema en que algún elemento de M sea 0
    Me = np.copysign(1, M) * (abs(M) ** (1. - eta))
    De = np.copysign(1, D) * (abs(D) ** (1. - eta))
    # se añaden los aranceles a la importación
    a = (1. + taum) * Me
    b = (1. + taum) * Me + De

    deltam = a / b
    deltad = De / b
    assert np.all(deltam >= 0.), 'detam negativo\n'
    assert np.all(deltad >= 0.), 'detad negativo\n'
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
    # mientras 'eta' sea positivo no hay problema en que algún elemento de M sea 0
    Me = np.copysign(1, M) * (abs(M) ** eta)
    De = np.copysign(1, D) * (abs(D) ** eta)
    return Q / ((deltam * Me + deltad * De) ** (1. / eta))

def coeficiente_CET_local_xid(fi, E, D):
    '''
    Coeficiente de participación en la CET de la demanda local para cada sector
    '''
    # si E tiene algún valor a 0 y 'umfi' es negativo (que es lo normal) se produce una división por 0
    umfi = 1. - fi
    De = np.copysign(1, D) * (abs(D) ** umfi)
    nsec = fi.shape[0]
    xid = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        if E[i] == 0:
            xid[i] = 1.
        else:
            Ee = np.copysign(1, E[i]) * (abs(E[i]) ** umfi[i])
            xid[i] = De[i] / (Ee + De[i])
    #np.nan_to_num(xid, copy=False) # convierte nan a 0, por lo que NO es una alternativa
    return xid

def coeficiente_CET_exportacion_xie(fi, E, D):
    '''
    Coeficiente de participación en la CET de la exportación para cada sector
    '''
    # si E tiene algún valor a 0 y 'umfi' es negativo (que es lo normal) se produce una división por 0
    umfi = 1. - fi
    De = np.copysign(1, D) * (abs(D) ** umfi)
    nsec = fi.shape[0]
    xie = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        if E[i] == 0:
            xie[i] = 0.
        else:
            Ee = np.copysign(1, E[i]) * (abs(E[i]) ** umfi[i])
            xie[i] = Ee / (Ee + De[i])
    #np.nan_to_num(xie, copy=False) # convierte nan a 0, por lo que SI es una alternativa
    return xie

def coeficiente_escala_CET_teta(Z, xie, E, xid, D, fi):
    '''
    Coeficiente de escala de la CET de exportación
    '''
    #no hay problema si E tiene algún valor a 0 ya que 'fi' es normalmente positivo, y por tanto '1. / fi' tambien, con lo que no produce una división por 0

    teta = Z / ((xie * E ** fi + xid * D ** fi) ** (1. / fi))

    assert np.all(np.isnan(teta)==False), 'coeficiente_escala_CET_teta incorrecto\n'

    #teta[teta == np.inf] = 0                # antes de np.nan_to_num porque puede cambiar el inf por un número
    #np.nan_to_num(teta, copy=False)         # si no hay datos (NAN) se sustituye por 0
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
    ingresos[ingresos == 0] = 1.          # para evitar divisiones por 0
    ssp = Sp / ingresos 
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
    return taud

def tasa_impuestos_directos_tai(Ti, FF, INDICE_F_TRA):
    '''
    Tasa de impuestos directos a las rentas de capital por el ahorro+inversión de los hogares

    Ti           : impuestos directos a la inversión
    FF           : factores prestados por cada hogar
    INDICE_F_TRA : índice del factor trabajo
    '''
    ingresos = FF[:, 1 - INDICE_F_TRA].sum()
    if ingresos == 0:
        tai = 0.
    else:
        tai = Ti / ingresos
    return tai

def propension_ahorro_gobierno_ssg(Sg, Td, Tz, Tm, Tg, Ti, Te, AgE, AgH, CssE, CssH, PssH):
    '''
    Propensión al ahorro del gobierno
    No contemplamos (pura pereza) que el gobierno recaude las cotizaciones de la seguridad social y pague las
    pensiones, como hacemos en otros apartados, pero somos coherentes al calcular el ahorro 'ayudas_empresas_AgE'
    Td : impuestos pagados por los hogares
    Tz : impuestos pagados por los sectores
    Tm : aranceles de importación
    Ti : impuestos pagados por la inversión+ahorro
    Te : impuestos pagados por el sector exterior
    No sumamos Tg (impuestos que paga el gobierno) porque también hay que restarlo
    AgE: ayudas a las empresas pagadas por el gobierno
    Agh: ayudas a los hogares pagadas por el gobierno
    '''
    if PssH.sum() == 0:
        # el gobierno paga las pensiones, por tanto recauda las cotizaciones
        Css = CssH.sum() + CssE.sum()
    else:
        Css = 0.
    ssg = Sg / (Td.sum() + Tz.sum() + Tm.sum() + Ti + Te + Css - AgE.sum() - AgH.sum())
    assert np.isnan(ssg).any() == False, 'error en el cálculo del coeficiente de ahorro del gobierno\n'
    return ssg

def coeficiente_ayudas_gobierno_empresas_cage(AgE, Td, Tz, Tm, Tg, Ti, Te):
    # no está adaptado al caso en que el gobierno paga las pensiones, por tanto recauda las cotizaciones
    # No sumamos Tg porque tambien hay que restarlo
    '''
    No contemplamos (pura pereza) que el gobierno recaude las cotizaciones de la seguridad social y pague las
    pensiones, como hacemos en otros apartados, pero somos coherentes al calcular las ayudas en 'ayudas_empresas_AgE'
    '''
    cage = AgE / (Td.sum() + Tz.sum() + Tm.sum() + Ti + Te)
    assert np.isnan(cage).any() == False, 'error en el cálculo del coeficiente de ayudas del gobierno a las empresas\n'
    return cage

def coeficiente_ayudas_gobierno_hogares_cagh(AgH, Td, Tz, Tm, Tg, Ti, Te):
    # no está adaptado al caso en que el gobierno paga las pensiones, por tanto recauda las cotizaciones
    # No sumamos Tg porque tambien hay que restarlo
    '''
    No contemplamos (pura pereza) que el gobierno recaude las cotizaciones de la seguridad social y pague las
    pensiones, como hacemos en otros apartados, pero somos coherentes al calcular las ayudas en 'ayudas_hogares_AgH'
    '''
    cagh = AgH / (Td.sum() + Tz.sum() + Tm.sum() + Ti + Te)
    assert np.isnan(cagh).any() == False, 'error en el cálculo del coeficiente de ayudas del gobierno a los hogares\n'
    return cagh

def poblacion_activa_PobAct(INDICE_F_TRA, FF0, paro):
    '''
    Población activa
    FF0  = aportación inicial de factores por los hogares
    paro = tasa de paro inicial en tanto por uno
    '''
    pobact = FF0[:,INDICE_F_TRA].sum() / (1. - paro)
    return pobact

