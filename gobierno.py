def impuestos_directos_Td(taud, pf, FF, Alp, PssH):
    '''
    Td impuestos directos como una tasa sobre el total de ingresos de los hogares (CAP, LAB y Seguridad social)
    Es posible que falte aladir Alp a FF, pero complica la secuencia de cálculo de las ecuaciones del modelo

    taud : tasa de impuestos directos para cada hogar
    pf   : precio de los factores
    FF   : factores prestados por los hogares
    PssH : ingresos recibidos de la seguridad social
    '''
    '''
    ndem = FF.shape[0]
    nfac = FF.shape[1]
    # suma de todos los ingresos de los consumidores a partir de los factores prestados y las pensiones cobradas
    #Td = deepcopy(PssH)
    Td = np.zeros(ndem,dtype=np.float64)
    Td += PssH
    for i in range(ndem):
        for j in range(nfac):
            Td[i] += (FF[i,j] + Alp[i,j]) * pf[j]
    Td *= taud
    Td2 = taud * ((FF + Alp).dot(pf) + PssH)
    assert np.all(abs(Td - Td2)<0.00001)
    '''
    return taud * ((FF + Alp).dot(pf) + PssH)

def impuestos_produccion_Tz(tauz, pz, Z):
    '''
    Tz impuestos a la producción de cada sector

    tauz : vector de tasas a la producción de cada sector
    pz   : vector precios de los productos
    Z    : vector producciones de los sectores
    '''
    '''
    nsec = len(pz)
    Tz = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        Tz[i] = tauz[i] * Z[i] * pz[i]
    return Tz
    '''
    return tauz * Z * pz

def aranceles_importacion_Tm(ta, pi, M):
    '''
    Tm aranceles de importación por cada producto

    ta : vector aranceles a cada producto
    pi : vector precio de importación de cada producto
    M : vector cantidades importadas de cada producto
    '''
    '''
    nsec = len(pi)
    Tm = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        Tm[i] = ta[i] * M[i] * pi[i]
    return Tm
    '''
    return ta * M * pi

def ayudas_empresas_AgE(cage, Td, Tz, Tm):
    '''
    ayudas del gobierno a los sectores
    '''
    '''
    nsec = len(cage)
    AgE = np.zeros(nsec, dtype=np.float64)
    ingresos = Td.sum() + Tz.sum() + Tm.sum()
    for i in range(nsec):
        AgE[i] = cage[i] * ingresos
    #return AgE
    AgE2 = cage * (Td.sum() + Tz.sum() + Tm.sum())
    assert np.all(abs(AgE - AgE2)<0.00001)
    '''
    return cage * (Td.sum() + Tz.sum() + Tm.sum())

def ayudas_hogares_AgH(cagh, Td, Tz, Tm, inc_ayd):
    '''
    ayudas del gobierno a los hogares

    PssH : pensiones que paga la seguridad social pero que están incluidas en Td
    '''
    '''
    ncon = len(cagh)
    AgH = np.zeros(ncon, dtype=np.float64)
    ingresos = Td.sum() + Tz.sum() + Tm.sum()
    for i in range(ncon):
        AgH[i] = cagh[i] * ingresos
    #return AgH
    AgH2 = cagh * (Td.sum() + Tz.sum() + Tm.sum())
    assert np.all(abs(AgH - AgH2)<0.00001)
    '''
    return cagh * (Td.sum() + Tz.sum() + Tm.sum()) + inc_ayd

def demanda_gobierno_Xg(mu, pq, Td, Tz, Tm, Sg, AgE, AgH):
    '''
    demanda (consumos) de productos por el gobierno

    mu   : coeficiente de reparto de la demanda del gobierno por productos
    pq   : precio de producto de Armington (producto compuesto: local + importación)
    Td   : impuestos directos a los hogares
    Tz   : impuestos indirectos a las empresas
    Tm   : aranceles de importación
    restan:
    Sg   : ahorro del gobierno
    AgE  : ayudas (pagos) del gobierno a los sectores
    AgH  : ayudas (pagos) del gobierno a los hogares
    '''
    '''
    ingresos = Td.sum() + Tz.sum() + Tm.sum() - Sg - AgE.sum() - AgH.sum()
    nsec = len(pq)
    Xg = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        Xg[i] = mu[i] * ingresos / pq[i]
    '''
    return mu * (Td.sum() + Tz.sum() + Tm.sum() - Sg - AgE.sum() - AgH.sum()) / pq

def seguridad_social_empresas_CssE(ctzsse, F, INDICE_F_TRA):
    return ctzsse * F[:,INDICE_F_TRA]

def seguridad_social_hogares_CssH(ctzssh, FF, Alp, INDICE_F_TRA):
    # las pensiones no cotizan a la seguridad social
    
    return ctzssh * (FF + Alp)[:,INDICE_F_TRA]

