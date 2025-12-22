import numpy as np
from scipy.optimize import LinearConstraint, NonlinearConstraint

def restricciones_M_E(nvec_opt, ind_pvec_desde, datos, GE_TIPO_RE):
    '''
    With nonlinear constraints, SciPy only knows whether it is currently satisfying the constraint or not.
    With a linear constraint, SciPy can determine not only whether it is satisfying the constraint, but also what directions it can legally move along without violating the constraint.
    This is much faster than trial and error.
        
    En nuestro caso, tardan aproximadamente igual
    '''
    margen = 0          # margen +- sobre el valor inicial de M0 y E0 
    sector = 2          # aplicable a un sector determinado (AP3 en nuestro caso)
    if GE_TIPO_RE == 0:
        #-----------------------
        # restricción líneal
        #-----------------------

        # para la importación M

        # en forma de vectores para comparar con el resultado de multiplicar 'AM' por el vector solución
        # todos los elementos cero
        val_min_M     = np.zeros(nvec_opt, dtype=np.float64)
        val_max_M     = np.zeros(nvec_opt, dtype=np.float64)
        # menos los del producto AP3 (pt) que se fijan en el valor mínimo y el máximo 
        pt            = ind_pvec_desde['M'] + sector
        val_min_M[pt] = datos.M0[sector] - margen
        val_max_M[pt] = datos.M0[sector] + margen
        # 'AM' matriz de coeficientes para la combinacón de variables (relaciones lineales)
        # al multiplicar el vector solución (1, N) por 'AM' (N x N) produce un vector de la forma (1, N))
        # todos los elementos cero
        AM            = np.zeros((nvec_opt, nvec_opt), dtype=np.float64)
        # menos el correspondiente (pt) a la M del producto AP3
        AM[pt, pt]    = 1.
        # por lo que el resultado de multiplicar la solución por 'AM' será un vector de ceros menos el correspondiente a AP3 que será su valor M
        # 'restriccion_a' se cumplirá si el valor M de AP3 está dentro de intervalo [val_min_M, val_max_M]
        restriccion_a = LinearConstraint(AM, val_min_M, val_max_M)

        # para la exportación E

        val_min_E     = np.zeros(nvec_opt, dtype=np.float64)
        val_max_E     = np.zeros(nvec_opt, dtype=np.float64)
        val_min_E[pt] = datos.E0[sector] - margen
        val_max_E[pt] = datos.E0[sector] + margen
        AE            = np.zeros((nvec_opt, nvec_opt), dtype=np.float64)
        pt            = ind_pvec_desde['E'] + sector
        AE[pt, pt]    = 1.
        restriccion_b = LinearConstraint(AE, val_min_E, val_max_E)
    else:
        #-----------------------
        # restricción no líneal
        #-----------------------

        def restriccion_a(x):
            # simplemente devuelve el valor M del producto 3 ('+ sector')
            return x[ind_pvec_desde['M'] + sector]
        def restriccion_b(x):
            # simplemente devuelve el valor E del producto 3 ('+ sector')
            return x[ind_pvec_desde['E'] + sector]

        # 'restriccion_a' se cumplirá si el valor M de AP3 está dentro de intervalo [datos.M0[sector] - margen, datos.M0[sector] + margen]
        restriccion_a = NonlinearConstraint(restriccion_a, datos.M0[sector] - margen, datos.M0[sector] + margen)
        restriccion_b = NonlinearConstraint(restriccion_b, datos.E0[sector] - margen, datos.E0[sector] + margen)

    return [restriccion_a, restriccion_b]
