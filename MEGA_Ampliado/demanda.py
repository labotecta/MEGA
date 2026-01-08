import numpy as np

def utilidad_CobbDouglas(Xp, alfa, b=1.):
    '''

    Calcula la utilidad para cada uno de los consumidores con la fórmula Cobb-Douglas
    
    La función de utilidad Cobb-Douglas es una formula matemática utilizada en la teoría económica
    para representar la relación entre la cantidad de bienes o servicios consumidos y la
    utilidad o satisfacción que se obtiene de ellos.

    Xp[i,j] es la cantidad consumida del producto j por el consumidor i 
    alfa[i,j] es el parámetro de participación del producto j para el consumidor i, debe ser > 0
    b es un parámetro de escala, se usa para producciones, para la demanda es 1.
    '''
    # el producto de los consumos de cada uno de los productos (Xp) elevado a la elasticidad
    # (alfa) del producto

    if len(Xp.shape) == 1:
        # para el caso de un solo consumidor en forma de vector y no de matriz, nunca debería pasar por aquí
        u_cd = (np.sign(Xp) * (np.abs(Xp)) ** alfa).prod()
    else:
        u_cd = (np.sign(Xp) * (np.abs(Xp)) ** alfa).prod(axis=1)
    
    # 'u_cd' vector (vertical) de la utilidad de los vectores (filas) de demanda Xp[i]
    return b * u_cd    

def variacion_hicksiana(Xp0, Xp, alfa, b=1.):
    uu0 = utilidad_CobbDouglas(Xp0, alfa)
    uu1 = utilidad_CobbDouglas(Xp, alfa)
    denominador = (alfa ** alfa).prod(axis=1)
    ep0 = uu0 / denominador
    ep1 = uu1 / denominador
    return ep1 - ep0

def demanda_maxima_utilidad_CobbDouglas_Xp(alfa, pq, pf, FF, Sp, Td, CssH, AgH, PssH, inc_dem):
    '''
    devuelve la matriz con las cantidades óptimas de productos demandados Xp

    FF : factores aportados por cada hogar (consumidor). Variable endógena

    'ingreso' : '(ff.dot(pf)-Sp-Td-CssH)' ingresos de cada hogar por la venta de todos sus factores más
    los ingresos de la seguridad social y las ayudas del gobierno (Agh), menos la cantidad que ahorran (Sp),
    los impuestos directos (Td), y la cotización a la seguridad social (CssH). Es un vector len(dem)

    el importe óptimo de cada producto lo dividimos por el precio de cada producto (pq) para pasarlo a cantidad.
    pp tiene las dimensiones (num productos, 1)
    trasponemos alfa para que tenga la misma dimensión que el precio y la
    división sea componente a componente [0]/[0], [1]/[1], ...
    finalmente trasponemos el resultado para que la demanda sea un vector (num productos, 1)
    con la misma forma que los precios

    ndem = alfa.shape[0]
    nsec = alfa.shape[1]
    Xp = np.zeros((ndem, nsec), dtype=np.float64)
    nfac = FF.shape[1]

    # ingresos de cada consumidor, incluidas las ayudas del gobierno y los ingresos recibidos de
    # la seguridad social, y netos de ahorros e impuestos
    ingreso = AgH + PssH - (Sp + Td + CssH)
    for consu in range(ndem):
        # ingresos del consumidor 'consu' por la prestación de factores
        for factor in range(nfac):
            ingreso[consu] += FF[consu,factor] * pf[factor]
        # consumo optimo de productos
        for sector in range(nsec):
            Xp[consu,sector] = alfa[consu,sector] * ingreso[consu]  / pq[sector]
    '''
    Xp = ((alfa.T * (FF.dot(pf) + AgH + PssH - (Sp + Td + CssH))).T + inc_dem) / pq 
    return Xp

def aportacion_factores_FF(FF0, F):
    '''
    calcula los factores FF que deben aportarse como iguales a la utilización F por los sectores

    FF0  : Factores aportados por los hogares inicialmente
    F    : Factores utilizados por la producción
    '''
    
    '''
    ndem = FF0.shape[0]
    nsec = F.shape[0]
    nfac = F.shape[1]
    FF = np.zeros((ndem,nfac), dtype=np.float64)
    # tanto por uno de participación en la aportación de factores de cada hogar
    paH = FF0 / FF0.sum(axis=0)
    # agregar para cada hogar los factores necesarios por los sectores, proporcionamente al consumo de estos
    for dem in range(ndem):
        for fac in range(nfac):
            # agregar la utilización de los factores por los sectores
            for sec in range(nsec):
                FF[dem,fac] += F[sec,fac] * paH[dem,fac]
    '''
    FF = F.sum(axis=0) * FF0 / FF0.sum(axis=0)
    #assert all(abs(FF.sum(axis=0) - F.sum(axis=0)) < 0.0001), 'aportación:\n{}\nuso:\n{}'.format(FF.sum(axis=0), F.sum(axis=0))
    return FF

