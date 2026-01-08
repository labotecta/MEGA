def demanda_inversion_Xv(landa, pq, Sp, Sg, epsilon, Sf):
    '''
    landa : coeficiente de reparto por productos del total de la inversión
    pq : precio del producto de Armington
    epsilon : cotización de la moneda extranjera (local/extranjera)
    Sp : ahorro de los hogares
    Sg ; ahorro del gobierno
    Sf : deficit por cuenta corriente (ahorro del exterior)
    '''
    '''
    nsec = len(pq)
    Xv = np.zeros(nsec, dtype=np.float64)
    ahorros = Sp.sum() + Sg + epsilon * Sf
    for i in range(nsec):
        Xv[i] += landa[i] / pq[i]
    '''
    return (Sp.sum() + Sg + epsilon * Sf) * (landa / pq)

def ahorro_hogares_Sp(ssp, FF, pf, PssH):
    '''
    Ahorro de los hogares Sp
    Una parte de sus ingresos (los factores utilizados por todos los sectores)
    
    FF   : aportación de factores por cada consumidor
    pf   : precio de los factores
    PssH : pagos de la seguridad social a los hogares
    ssp  : tasa de propensión al ahorro de cada consumidor
    '''
    '''
    ndem = FF.shape[0]
    nfac = FF.shape[1]
    # ingresos de los hogares pagados por la seguridad social
    #Sp = deepcopy(PssH)
    Sp = np.zeros(ndem, dtype=np.float64)
    Sp += PssH
    for consu in range(ndem):
        # ingresos de cada consumidor por los factores prestados
        for factor in range(nfac):
            Sp[consu] += FF[consu,factor] * pf[factor]
        Sp[consu] *= ssp[consu]
    '''
    Sp = ssp * (FF.dot(pf) + PssH)
    return Sp

def ahorro_gobierno_Sg(ssg, Td, Tz, Tm, AgE, AgH):
    '''
    Ahorro del gobierno Sg
    Un porcentaje (ssg propensión al ahorro del gobierno) de sus ingresos
    ssg  : propensión al ahorro del gobierno
    Td   : impuestos directos
    Tz   : impuestos a la producción
    Tm   : aranceles de importación
    restan
    AgE: ayudas del gobierno a las empresas
    AgH: ayudas del gobierno a los hogares
    PssH : pagos de la seguridad social a los hogares incluidos en Td
    '''
    return ssg * (Td.sum() + Tz.sum() + Tm.sum() - AgE.sum() - AgH.sum())
