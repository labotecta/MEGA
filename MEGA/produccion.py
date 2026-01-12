import numpy as np

# ecuaciones de produccion

def produccion_factor_compuesto_Y(F, beta, b):
    '''
    ecuación 6.1 Producción óptima de factor compuesto (composite factor) 'Y' para cada sector,
    dadas las utilización de factores de producción 'F' y la función de producción Cobb Douglas correspondiente

    F   : factores utilizados por cada sector
    beta: coeficientes de participación de cada factor en la función de producción (utilidad) de cada sector
    b   : coeficiente de escala de la función de producción
    '''
    nsec = beta.shape[0]
    nfac = beta.shape[1]
    Y = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        Y[i] = b[i]
        for j in range(nfac):
            Y[i] *= np.sign(F[i,j]) * (np.abs(F[i,j])) ** beta[i,j]
    return Y

def consumo_intermedio_X(Z, ax):
    '''
    ecuación 6.3
    dada la producción bruta Z del sector 'i' calculamos la utilización X que hace 'i' de consumos intermedios 'j'
    por aplicación de los coeficientes (ax) deducidos de la MCS
    Z   : producción bruta del sector
    ax  : compras necesarias de un sector a otros sectores (y a el mismo) para producir una unidad
    '''
    nsec = ax.shape[0]
    X = np.zeros((nsec,nsec), dtype=np.float64)
    for i in range(nsec):
        for j in range(nsec):
            # X[j,i] son las compras de 'i' a los sectores 'j'
            # Z[i] producción bruta del sector 'i'
            # ax[i,j] compras intermedias, por unidad de producción bruta, que hace el sector 'i' a los sectores 'j'
            X[j,i] = ax[i,j] * Z[i] # los consumos están en las columnas de X, por eso los índices están traspuestos [j,i]
    return X
    '''
    return ax.T * Z
    '''

def utilizacion_factor_compuesto_Y(Z, ay):
    '''
    ecuación 6.4
    Z   : producción bruta del sector
    ay  : para cada sector, compras necesarias de su factor compuesto (composite factor) para producir una unidad
    '''
    '''
    nsec = ay.shape[0]
    Y = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        Y[i] = ay[i] * Z[i]
    return Y
    '''
    return ay * Z

def uso_optimo_factores_F(beta, pf, py, Y):
    '''
    ecuación 6.2. factores optimos para una producción Y del factor compuesto (composite factor) con precio py
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

def produccion_sector_Z(X, ax, Y, ay):
    '''
    ecuación 6.5 original. Leontief
    Se puede producir (cantidad) lo que permita el menor de los recursos disponibles
    X   : compras de un sector a otros sectores (y a el mismo)
    ax  : compras necesarias de un sector a otros sectores (y a el mismo) para producir una unidad
    Y   : para cada sector, compras necesarias de su factor compuesto (composite factor)
    ay  : para cada sector, compras necesarias de su factor compuesto (composite factor) para producir una unidad

    '''
    nsec = ax.shape[0]
    # cada fila son lo que podría producir el sector 'i' de acuerdo a lo que le compra a cada 'j'; -compra X[j,i] porque X está transpuesta-
    producción_posible = np.zeros((nsec,nsec+1), dtype=np.float64)
    for i in range (nsec):
        for j in range (nsec):
            if ax[i,j] == 0:
                producción_posible[i,j] = 1.e+09
            else:
                # la cantidad que el sector 'i' puede producir con las compras que hace al sector 'j' es =
                # compras al sector j (X[j,i]) / cantidad de j necesaria para que i pueda producir una unidad (ax[i,j])
                producción_posible[i,j] = X[j,i] / ax[i,j]  # las compras están en las columnas de X, por eso los índices están traspuestos [j,i]
        # cantidad producible por el factor compuesto
        if ay[i] == 0:
            producción_posible[i, nsec] = 1.e+09
        else:
            producción_posible[i, nsec] = Y[i] / ay[i]
    # 'i' produce lo que le permite el menor de los recursos disponibles 
    Z = np.min(producción_posible, axis=1)
    return Z

def coste_unitario_produccion_pz(ay, py, ax, pq):
    '''
    ecuación 6.5 alternativa
    ay  : para cada sector, compras necesarias de su factor compuesto (composite factor) para producir una unidad
    ax  : compras necesarias de un sector a otros sectores (y a el mismo) para producir una unidad
    '''
    nsec = ax.shape[0]
    pz = np.zeros(nsec, dtype=np.float64)
    for i in range (nsec):
        pz[i] = ay[i] * py[i]
        for j in range(nsec):
            pz[i] += ax[i,j] * pq[j]
    return pz
