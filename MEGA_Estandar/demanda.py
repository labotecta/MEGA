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

def demanda_maxima_utilidad_CobbDouglas(alfa, pq, pf, wf, Sp, Td):
    '''
    devuelve el vector con las cantidades óptima de productos demandados
    solo sirve para un consumidor único porque wf son los suministros totales de cada factor

    'y' ingresos por la venta de todos los factores por todos los consumidores menos la
    cantidad que ahorran los hogares (Sp) y los impuestos directos (Td), es un escalar
    '''
    #y = (wf.sum(axis=0, keepdims=True) - Sp - Td).dot(pf)
    '''
    'alfa * y' es el importe óptimo de cada producto y lo dividimos por el precio de
    cada producto para pasarlo a cantidad.
    (alfa * y) tiene las dimensiones de alfa (1, num productos)
    pp tiene las dimensiones (num productos, 1)
    trasponemos (alfa * y) para que tenga la misma dimensión que el precio y la
    división sea componente a componente [0]/[0], [1]/[1], ...
    finalmente trasponemos el resultado para que la demanda sea un vector (num productos, 1)
    con la misma forma que los precios
    '''
    #x = ((alfa * y).T / pp).T

    nsec = wf.shape[0]
    nfac = wf.shape[1]
    Xp = np.zeros(nsec, dtype=np.float64)
    ingreso = - (Sp + Td)
    for i in range(nsec):
        for j in range(nfac):
            ingreso += wf[i,j] * pf[j]
    for i in range(nsec):
        Xp[i] = alfa[i] * ingreso  / pq[i]
    return Xp

