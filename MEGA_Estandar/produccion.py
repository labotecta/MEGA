import numpy as np

def beneficio_factor_compuesto(sector, pc, pf, wf, beta, b):
    '''
    Primer paso: ecuación 6.1 que se quiere maximizar, como vamos a usar la 
    función scipy.optimize.minimize devolvemos el -valor 

    Beneficio resultante de producir el factor compuesto (composite factor) en función del uso de los factores de producción =
    Ingreso del factor compuesto (composite factor) (pc * Y) - coste de los factores (pf * wf)
    La cantidad del factor compuesto (composite factor) (Y) viene dada por la utilidad del uso de los factores para este sector
    '''
    nfac = len(pf)
    
    # coste de los factores (valor añadido)
    coste = 0.
    for j in range(nfac):
        coste += pf[j] * wf[sector,j]

    # función Cob Duglas de la utilidad para (producción del) 'sector' de usar unas ciertas coantidades de factores wf[sector,j]
    # de acuerdo a su tecnología (beta,b). Esta es la restricción que debe cumplir el óptimo.
    Y = b
    for j in range(nfac):
        Y *= wf[sector,j] ** beta[sector,j]  

    ingreso = pc * Y

    # devolvemos el -beneficio
    return coste - ingreso

def beneficio_produccion(sector, pp, X, ax, pc, Y, ay):
    '''
    Beneficio para 'sector' de producir la cantidad (Z) de su producto demandada por el consumidor doméstico =
    Ingreso (pp[sector] * Z) 
        - coste del factor compuesto (composite factor)
        - coste de los consumos intermedios (X[sector] de la TIO) (pp * X[sector]) 
    '''
    npro = len(pp)
    # coste del factor compuesto (composite factor)
    coste = Y * pc
    # más coste de los consumos intermedios
    for j in range(npro):
        coste += X[sector, j] * pp[j]
    
    # la cantidad Z es la que puede producir el 'sector' con el procucto más escaso de los que necesita (consumos intermedios más el factor compuesto -composite factor-). Esta es la restricción que debe cumplir el óptimo         
    necesidad = np.zeros(npro+1, dtype=np.float64)
    for j in range (npro):
       necesidad[j] = X[sector,j] / ax[sector,j]
    necesidad[npro] = Y / ay
    Z = np.min(necesidad)
    
    ingreso = pp[sector] * Z

    # devolvemos el -beneficio
    return coste - ingreso

# ecuaciones de produccion

def produccion_factor_compuesto(wf, beta, b):
    '''
    ecuación 6.1 Producción del factor compuesto (composite factor) para cada sector
    dada una utilización de factores (wf) y la ecuación Cobb Douglas correspondiente
    wf  : factores utilizados por cada sector
    beta: coeficientes de participación de cada factor en la función de producción (utilidad) de cada sector
    b   : coeficiente de escala de la función de producción
    '''
    nsec = beta.shape[0]
    nfac = beta.shape[1]
    Y = np.zeros(nsec,dtype=np.float64)
    for i in range(nsec):
        Y[i] = b[i]
        for j in range(nfac):
            Y[i] *= wf[i,j] ** beta[i,j]  
    return Y

def optimo_factores(beta, pf, py, Y):
    '''
    ecuación 6.2. factores optimos para una producción Y del factor compuesto (composite factor) con precio py
    similar a 'factores_maxima_utilidad_CobbDouglas'
    beta: coeficientes de participación de cada factor en la función de producción (utilidad) de cada sector
    pf  : precio de los factores
    py  : precio del factor compuesto (composite factor)
    Y   : producción del factor compuesto (composite factor)
    '''
    nsec = beta.shape[0]
    nfac = beta.shape[1]
    F = np.zeros((nsec,nfac), dtype=np.float64)
    for i in range(nsec):
        for j in range(nfac):
            F[i,j] = beta[i,j] * py[i] * Y[i] / pf[j]
    return F

def consumo_intermedio(Z, ax):
    '''
    ecuación 6.3
    dada la producción Z del sector 'i' (demanda de su producto) calculamos la utilización X que hace 'i' de consumos intermedios 'j'
    por aplicación de los coeficientes (ax) deducidos de la SAM
    Z   : producción del sector para cubrir su demanda
    ax  : compras necesarias de un sector a otros sectores (y a el mismo) para producir una unidad
    '''
    nsec = ax.shape[0]
    X = np.zeros((nsec,nsec), dtype=np.float64)
    for i in range(nsec):
        for j in range(nsec):
            X[i,j] = ax[j,i] * Z[j] # los consumos están en las columnas de X, por eso los índices están traspuestos [j,i]
    return X

def consumo_composite_factor(Z, ay):
    '''
    ecuación 6.4
    Z   : producción del sector para cubrir la demanda del consumidor doméstico
    ay  : para cada sector, compras necesarias de su factor compuesto (composite factor) para producir una unidad
    '''
    nsec = ay.shape[0]
    Y = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        Y[i] = ay[i] * Z[i]
    return Y

def produccion_sector(X, ax, Y, ay):
    '''
    ecuación 6.5 original. Leontief
    Se puede producir (cantidad) lo que permita el menor de los recursos disponibles
    X   : compras necesarias de un sector a otros sectores (y a el mismo)
    ax  : compras necesarias de un sector a otros sectores (y a el mismo) para producir una unidad
    Y   : para cada sector, compras necesarias de su factor compuesto (composite factor)
    ay  : para cada sector, compras necesarias de su factor compuesto (composite factor) para producir una unidad

    '''
    nsec = ax.shape[0]
    producción_posible = np.zeros((nsec,nsec+1), dtype=np.float64)
    for i in range (nsec):
        for j in range (nsec):
            # cantidad producible =
            # compras necesarias del recurso j / compras necesarias para producir una unidad de j            
            producción_posible[i,j] = X[j,i] / ax[i,j]  # las compras están en las columnas de X, por eso los índices están traspuestos [j,i]
        # cantidad producible por el factor compuesto
        producción_posible[i, nsec] = Y[i] / ay[i]
    # 'i' produce lo que permita el menor de los recursos disponibles 
    Z = np.min(producción_posible, axis=1)
    return Z

def coste_unitario_produccion(ay, py, ax, pq):
    '''
    ecuación 6.5 alternativa
    ay  : para cada sector, compras necesarias de su factor compuesto (composite factor) para producir una unidad
    ax  : compras necesarias de un sector a otros sectores (y a el mismo) para producir una unidad
    '''
    nsec = ax.shape[0]
    pz = np.zeros(nsec, dtype=np.float64)
    for i in range (nsec):
        pz[i] = ay[i] * py[i]
        suma = 0.
        for j in range(nsec):
            suma += ax[i,j] * pq[j]
        pz[i] += suma 
    return pz
