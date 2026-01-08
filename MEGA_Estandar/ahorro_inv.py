import numpy as np

def demanda_inversion(landa, pq, Sp, Sg, epsilon, Sf):
    '''
    landa : coeficiente de reparto por productos del total de la inversión
    pq : precio del producto de Armington
    epsilon : cotización de la moneda extranjera (local/extranjera)
    Sp : ahorro de los hogares
    Sg ; ahorro del gobierno
    Sf : deficit por cuenta corriente (ahorro del exterior)
    '''
    nsec = len(pq)
    Xv = np.zeros(nsec, dtype=np.float64)
    ahorros = Sp + Sg + epsilon * Sf
    for i in range(nsec):
        Xv[i] = landa[i] / pq[i] * ahorros
    return Xv

def ahorro_hogares(wf, pf, ssp):
    '''
    Ahorro de los hogares Sp
    Una parte de sus ingresos (los factores utilizados por todos los sectores)
    
    wf : utilización de los factores
    pf : precio de los factores
    ssp : propensión al ahorro de los hogares
    '''
    nsec = wf.shape[0]
    nfac = wf.shape[1]
    Sp = 0.
    for i in range(nsec):
        for j in range(nfac):
            Sp += wf[i,j] * pf[j]
    Sp *= ssp
    return Sp

def ahorro_gobierno(ssg, Td, Tz, Tm):
    '''
    Ahorro del gobierno
    Un porcentaje (ssg propensión al ahorro del gobierno) de sus ingresos
    ssg : propensión al ahorro del gobierno
    Td : impuestos directos
    Tz : impuestos a la producción
    Tm : aranceles de importación
    '''
    Sg = ssg * (Td + Tz.sum() + Tm.sum())
    return Sg