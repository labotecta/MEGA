import numpy as np

def demanda_inversion(landa, p, epsilon, ssp, ssg, pf, wf, Td, Tz, Tm):
    nsec = wf.shape[0]
    nfac = wf.shape[1]
    '''
    Ahorro de los hogares Sp
    Un porcentaje (ssp propensión al ahorro de los hogares) de sus
    ingresos (por los factores utilizados por todos los sectores)
    '''
    Sp = 0
    for i in range(nsec):
        for j in range(nfac):
            Sp += wf[i,j] * pf[j]
    Sp += ssp
    '''
    Ahorro del gobierno
    Un porcentaje (ssg propensión al ahorro del gobierno) de sus ingresos
    '''
    Sg = ssg * (Td + Tz.sum() + Tm.sum())

    X = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        X[i] = landa[i] / p[i] * (Sp + Sg + epsilon * Sf)
    return X
