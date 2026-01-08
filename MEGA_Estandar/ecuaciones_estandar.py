'''
Función de producción de Leontief:
La cantidad producida de un bien está determinada por la cantidad del bien más escaso
(necesario para su producción).
Se trata de obtener el mínimo de las cantidades de bienes divididas cada una de
ellas por la cantidad de bien necesaria para producir una unidad de producto.
Está asumiendo que no se pueden reemplazar unos bienes por otros.
'''
import numpy as np

def utilidad_CobbDouglas(x, alfa, b=1.):
    '''
    Calcula la utilidad para cada uno de los consumidores con la fórmula Cobb-Douglas
    
    La función de utilidad Cobb-Douglas es una formula matemática utilizada en la teoría económica
    para representar la relación entre la cantidad de bienes o servicios consumidos y la
    utilidad o satisfacción que se obtiene de ellos.

    x[i,j] es la cantidad consumida del producto j por el consumidor i 
    alfa[i,j] es el parámetro de participación del producto j para el consumidor i, debe ser > 0
    b es un parámetro de escala
    '''
    try:
        # el producto de los consumos de cada uno de los productos (x) elevado a la elasticidad
        # (alfa) del producto
        u = (x ** alfa).prod(axis=1)
    except:
        u = (x ** alfa).prod()
    
    # 'u' vector (vertical) de la utilidad de los vectores (filas) de demanda x[i]
    return b * u    

def demanda_maxima_utilidad_CobbDouglas(alfa, pp, pf, wf):
    # devuelve el vector con las cantidades óptima de productos demandados
    # solo sirve para un consumidor único porque wf son los suministros totales de cada factor

    # 'y' ingresos por la venta de todos los factores por todos los consumidores, un escalar
    y = (wf.sum(axis=0, keepdims=True)).dot(pf)
    '''
    'alfa * y' es el importe óptimo de cada producto y lo dividimos por el precio de
    cada producto para pasarlo a cantidad
    alfa * y tiene las dimensiones de alfa (1, num productos)
    pp tiene las dimensiones (num productos, 1)
    trasponemos (alfa * y) para que tenga la misma dimensión que el precio y la
    división sea componente a componente [0]/[0], [1]/[1], ...
    finalmente trasponemos el resultado para que la demanda sea un vector (num productos, 1)
    con la misma forma que los precios
    '''
    x = ((alfa * y).T / pp).T
    #x = ((alfa * y) / pp)
    return x

def factores_maxima_utilidad_CobbDouglas(beta, pp, wp, pf):
    # devuelve el vector con las cantidades de factores demandados optimas

    # ingresos para cada sector por la venta de sus productos a todos los consumidores, vector fila con las ventas de cada sector
    # calculada a partir de la demanda a cada sector
    #y = wp.dot(pp)
    y = (wp.sum(axis=0, keepdims=True)) * pp.T
    '''
    y = np.zeros(len(pp))
    for i in range(wp.shape[0]):
        for j in range(len(pp)):
            y[j] += wp[i,j] * pp[j]
    '''
    # 'beta * y'        # es el importe óptimo de cada factor y lo dividimos por el precio de
    # cada factor para pasar a cantidad

    nsec = beta.shape[0]
    nfac = beta.shape[1]

    F = np.zeros((nsec, nfac), dtype=np.float64)
    for i in range(nsec):
        for j in range(nfac):
            F[i,j] = beta[i,j] / pf[j] * y[0][i]

    #F = ((beta * y).T / pf).T
    return F

def ingreso_sectores(pp, wp):
    # ingreso de cada sector a través de las compras de los consumidores
    ncon = wp.shape[0]
    npro = len(pp)
    ing = np.zeros(npro, dtype=np.float64) 
    for i in range(ncon):
        for j in range(npro):
            ing[j] += wp[i,j] * pp[j][0]
    return ing

def coste_factores_por_sectores(pf, wf):
    # renta de cada factor para el total de consumidores
    nsec = wf.shape[0]
    nfac = len(pf)
    coste = np.zeros(nsec, dtype=np.float64) 
    for i in range(nsec):
        for j in range(nfac):
            coste[i] += wf[i,j] * pf[j][0]
    return coste

def producciones(beta, b, wf):
    nsec = wf.shape[0]
    nfac = wf.shape[1]
    Z = np.zeros(nsec, dtype=np.float64)
    for i in range(nsec):
        Z[i] = b[i]
        for j in range(nfac):
            Z[i] *= wf[i,j] ** beta[i,j]
    return Z

def alfa_CobbDouglas(X):
    '''
    calcula los valores del parámetro alfa de la funcion de utilidad.
    La fórmula se obtiene despejando alfa de la formula de máxima utilidad y
    teniendo en cuenta que los ingresos por los factores deben igualar al gasto en productos
    (gastamos todo lo que tenemos)
    suma (cantidades demandadas * precio productos) = 
    suma (cantidad de factores suministrados * precio de los factores)
    
    argumentos:
        X: demanda de los hogares a cada sector
    '''
    return X / X.sum()  # (2, ) / (0) escalar

def beta_CobbDouglas(F):
    '''
    Obtiene los coeficientes de participación (beta) de los factores en la función de producción
    F : utilización de factores por cada sector (2, 2)
    '''
    nsec = F.shape[0]
    nfac = F.shape[1]
    beta = np.ones((nsec,nfac))
    denominador = F.sum(axis=1) # suma por fila (sector) (2, )
    for i in range(nsec):
        for j in range(nfac):
            beta[i,j] = F[i,j] / denominador[i]
    return beta # (2, 2)

def b_CobbDouglas(Y, F, beta):
    nsec = F.shape[0]
    nfac = F.shape[1]
    denominador = np.ones(nsec)
    for i in range(nsec):
        for j in range(nfac):
            denominador[i] *= F[i,j] ** beta[i,j]
    return Y / denominador

def coeficientes_consumos_intermedios(X, Z):
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
    return ax

def coeficientes_factor_compuesto(Y, Z):
    '''
    Cantidad de factor compuesto necesario para producir una unidad de producto 'i'
    Y = factor compuesto para cada sector, igual a la suma de los factores utilizados por el sector en la SAM (2, )
    Z : producción de cada sector = factor compuesto + ventas intermedias (2, )
    '''
    return Y / Z    # división elemento a elemnto

def coeficientes_demanda_gobierno(X):
    '''
    Coeficiente para repartir la demanda total del gobierno entre sectores
    X : demanda del gobierno a cada sector
    '''
    return X / X.sum()

def coeficientes_inversiones(Xv, Sp, Sg, Sf):
    '''
    Coeficiente para repartir por sectores los ahorros
    Xv : ingresos de los sectores aportados por 'INV'
    Sp : ahorro de los hogares
    Sg : ahorro del gobierno
    Sf : ahorro exterior
    '''
    landa = Xv / (Sp + Sg + Sf)
    return landa
    
def coeficientes_importacion_armington(taum, eta, M, D):
    '''
    Coeficiente de participación de la importación (M) en la función del producto de Armington
    taum : tasa de aranceles a la importación
    eta  : parámetro de elasticidad de sustitución, entre local e importación, del producto de Argminton (CES)
    M    : importaciones pagadas por los sectores
    D    : demanda local de cada sector
    '''
    a = (1 + taum) * (M ** (1 - eta)) # se añaden los aranceles a la importación
    b = (1 + taum) * (M ** (1 - eta)) + D ** (1 - eta)
    deltam = a / b
    return deltam

def coeficientes_local_armington(taum, eta, M, D):
    '''
    Coeficiente de participación de la demanda local (D) en la función del producto de Armington
    taum : tasa de aranceles a la importación
    eta  : parámetro de elasticidad de sustitución, entre local e importación, del producto de Argminton (CES)
    M    : importaciones pagadas por los sectores
    D    : demanda local de cada sector
    '''
    a = D ** (1 - eta)
    b = (1 + taum) * (M ** (1 - eta)) + D ** (1 - eta)
    deltad = a / b
    return deltad

def coeficiente_escala_armington(Q, deltam, deltad, eta, M, D):
    '''
    Q      : cantidades vendidas del producto de Arminton por cada sector
    deltam : coeficiente de participación de la importación (M) en la función del producto de Armington
    deltad : coeficiente de participación de la demanda local (D) en la función del producto de Armington
    eta    : parámetro de elasticidad de sustitución, entre local e importación, del producto de Argminton (CES)
    M      : importaciones pagadas por los sectores
    D      : demanda local de cada sector
    '''
    return Q / ((deltam * (M ** eta) + deltad * (D ** eta)) ** (1. / eta))

def coeficiente_CET_local(fi, E, D):
    '''
    Coeficiente de participación en la CET de la demanda local para cada sector
    '''
    umfi = 1 - fi
    xid = (D ** umfi) / (E ** umfi + D ** umfi)
    return xid

def coeficiente_CET_exportacion(fi, E, D):
    '''
    Coeficiente de participación en la CET de la exportación para cada sector
    '''
    umfi = 1 - fi
    xie = (E ** umfi) / (E ** umfi + D ** umfi)
    return xie

def coeficiente_escala_CET(Z, xie, E, xid, D, fi):
    '''
    Coeficiente de escala de la CET de exportación
    '''
    return Z / ((xie * E ** fi + xid * D ** fi) ** (1/fi))

def propension_ahorro_hogares(Sp, FF):
    '''
    Propensión al ahorro de los hogares
    '''
    ssp = Sp / FF.sum() # () escalar
    return ssp

def propension_ahorro_gobierno(Sg, Td, Tz, Tm):
    '''
    Propensión al ahorro del gobierno
    '''
    ssg = Sg / (Td + Tz.sum() + Tm.sum()).item()
    return ssg   # () escalar

def tasa_impuestos_directos(Td, FF):
    '''
    Tasa de impuestos directos
    '''
    taud = Td / FF.sum()    # () escalar
    return taud