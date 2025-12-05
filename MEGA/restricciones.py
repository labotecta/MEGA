import numpy as np
from scipy.optimize import LinearConstraint, NonlinearConstraint

def restricciones(nvec_opt, ind_pvec_desde, datos, GE_TIPO_RE):
    '''
    With nonlinear constraints, SciPy only knows whether it is currently satisfying the constraint or not.
    With a linear constraint, SciPy can determine not only whether it is satisfying the constraint, but also what directions it can legally move along without violating the constraint.
    This is much faster than trial and error.
        
    En nuestro caso, tardan aproximadamente igual
    '''
    margen = 0          # margen +- sobre el valor inicial de M0 y E0 
    if GE_TIPO_RE == 0:
        # restricción líneal
        sector = 2      # aplicable a un sector determinado (AP3 en nuetro caso)
        lbM           = np.zeros(nvec_opt, dtype=np.float64)
        ubM           = np.zeros(nvec_opt, dtype=np.float64)
        pt            = ind_pvec_desde['M'] + sector
        lbM[pt]       = datos.M0[sector] - margen
        ubM[pt]       = datos.M0[sector] + margen
        AM            = np.zeros((nvec_opt, nvec_opt), dtype=np.float64)
        AM[pt, pt]    = 1.
        restriccion_a = LinearConstraint(AM, lbM, ubM)
        lbE           = np.zeros(nvec_opt, dtype=np.float64)
        ubE           = np.zeros(nvec_opt, dtype=np.float64)
        pt            = ind_pvec_desde['E'] + sector
        lbE[pt]       = datos.E0[sector] - margen
        ubE[pt]       = datos.E0[sector] + margen
        AE            = np.zeros((nvec_opt, nvec_opt), dtype=np.float64)
        AE[pt, pt]    = 1.
        restriccion_b = LinearConstraint(AE, lbE, ubE)
    else:
        # restricción no líneal
        def restriccion_a(x):
            return x[ind_pvec_desde['M'] + 2]
        def restriccion_b(x):
            return x[ind_pvec_desde['E'] + 2]
        restriccion_a = NonlinearConstraint(restriccion_a, datos.M0[2] - margen, datos.M0[2] + margen)
        restriccion_b = NonlinearConstraint(restriccion_b, datos.E0[2] - margen, datos.E0[2] + margen)

    return [restriccion_a, restriccion_b]
