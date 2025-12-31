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

def demanda_maxima_utilidad_CobbDouglas_Xp(alfa, pq, pf, FF, Sp, Td, CssH, AgH, PssH, inc_dem_tipo, inc_dem):
    '''
    devuelve la matriz con las cantidades óptimas de productos demandados Xp

    FF : factores aportados por cada hogar (consumidor). Variable endógena

    'ingreso' : '(FF.dot(pf)-Sp-Td-CssH)' ingresos de cada hogar por la venta de todos sus factores más
    los ingresos de la seguridad social y las ayudas del gobierno (Agh), menos la cantidad que ahorran (Sp),
    los impuestos directos (Td), y la cotización a la seguridad social (CssH). Es un vector len(dem)

    el importe óptimo de cada producto lo dividimos por el precio de cada producto (pq) para pasarlo a cantidad.
    pp tiene las dimensiones (num productos, 1)
    trasponemos alfa para que tenga la misma dimensión que el precio y la
    división sea componente a componente [0]/[0], [1]/[1], ...
    finalmente trasponemos el resultado para que la demanda sea un vector (num productos, 1)
    con la misma forma que los precios
    '''
    nfac = FF.shape[1]
    ndem = alfa.shape[0]
    nsec = alfa.shape[1]
    Xp = np.zeros((ndem, nsec), dtype=np.float64)

    # ingresos de cada consumidor, incluidas las ayudas del gobierno y los ingresos recibidos de
    # la seguridad social, y netos de ahorros e impuestos
    ingreso = AgH + PssH - (Sp + Td + CssH)
    for consu in range(ndem):
        # ingresos del consumidor 'consu' por la prestación de factores
        for factor in range(nfac):
            ingreso[consu] += FF[consu, factor] * pf[factor]
        # consumo optimo de productos
        for sector in range(nsec):
            if inc_dem_tipo == 0:
                Xp[consu,sector] = (alfa[consu, sector] * ingreso[consu] + inc_dem[consu, sector]) / pq[sector]
            else:
                Xp[consu,sector] = alfa[consu, sector] * ingreso[consu]  / pq[sector] + inc_dem[consu, sector]
    '''
    if inc_dem_tipo == 0:
        # se añade 'inc_dem' al importe demandado 
        Xp = ((alfa.T * (FF.dot(pf) + AgH + PssH - (Sp + Td + CssH))).T + inc_dem) / pq 
    else:
        # se añade 'inc_dem' a la cantidad demandada 
        Xp = ((alfa.T * (FF.dot(pf) + AgH + PssH - (Sp + Td + CssH))).T) / pq  + inc_dem
    '''
    return Xp

def demanda_maxima_utilidad_StoneGeary_Xp(alfa, con_esen, pq, pf, FF, Sp, Td, CssH, AgH, PssH, inc_dem_tipo, inc_dem):
    '''
    devuelve la matriz con las cantidades óptimas de productos demandados Xp calculada con la función Stone Geary

    FF : factores aportados por cada hogar (consumidor). Variable endógena

    'ingreso' : '(FF.dot(pf)-Sp-Td-CssH)' ingresos de cada hogar por la venta de todos sus factores más
    los ingresos de la seguridad social y las ayudas del gobierno (Agh), menos la cantidad que ahorran (Sp),
    los impuestos directos (Td), y la cotización a la seguridad social (CssH). Es un vector len(dem)

    el importe óptimo de cada producto lo dividimos por el precio de cada producto (pq) para pasarlo a cantidad.
    pp tiene las dimensiones (num productos, 1)
    trasponemos alfa para que tenga la misma dimensión que el precio y la
    división sea componente a componente [0]/[0], [1]/[1], ...
    finalmente trasponemos el resultado para que la demanda sea un vector (num productos, 1)
    con la misma forma que los precios
    '''

    nfac = FF.shape[1]
    ndem = alfa.shape[0]
    nsec = alfa.shape[1]

    # ingresos de cada consumidor, incluidas las ayudas del gobierno y los ingresos recibidos de
    # la seguridad social, y netos de ahorros e impuestos
    ingreso_neto   = AgH + PssH - (Sp + Td + CssH)             # ingreso total de cada hogar
    for consu in range(ndem):
        # ingresos del consumidor 'consu' por la prestación de factores
        for factor in range(nfac):
            ingreso_neto[consu] += FF[consu,factor] * pf[factor]
    gasto_esencial   = (con_esen * pq).sum(axis=1)        # gasto esencial de cada hogar
    renta_disponible = ingreso_neto - gasto_esencial
    # consumo optimo de productos
    Xp = np.zeros((ndem, nsec), dtype=np.float64)
    for consu in range(ndem):
        for sector in range(nsec):
            if inc_dem_tipo == 0:
                Xp[consu,sector] = con_esen[consu,sector] + (alfa[consu,sector] * renta_disponible[consu] + inc_dem[consu,sector]) / pq[sector]
            else:
                Xp[consu,sector] = con_esen[consu,sector] + (alfa[consu,sector] * renta_disponible[consu]) / pq[sector] + inc_dem[consu,sector]
    return Xp

def aportacion_factores_FF(FF0, F):
    '''
    calcula los factores FF que deben aportarse como iguales a la utilización F por los sectores
    
    reparte la suma de todos sectores para cada factor, entre los hogares, proporcionalmente a la
    aportación inicial, en el total de ese factor, de cada hogar.

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

def precio_factor_trabajo_pFL(INDICE_F_TRA, PobAct, alfa, pF0L, F0, F):
    '''
    tasa de inflacion = C + alfa * tasa desempleo 
    C    =  0,4957
    alfa = -0.4566

    var inflacion = alfa * var_desempleo
    
    Si la tasa de desempleo sube un 1 punto porcentual la inflación cae 0,4566 puntos porcentuales.
    Esto es lo que se espera de la curva de Phillips: una relación negativa entre inflación y desempleo.
    Si el desempleo baja la inflacción sube

    Hacemos inflacción equivalente a precio del factor trabajo (era la idea original de Phillips)

    calcula el precio del factor trabajo
    pF0L   = precio inicial del factor trabajo
    PobAct = población activa
    alfa   = elasticidad de Phillips
    F0     = utilización de factores por los sectores inicialmente
    F      = utilización de factores por los sectores final
    '''
    var_desempleo = (F0[:,INDICE_F_TRA].sum() - F[:,INDICE_F_TRA].sum()) / PobAct
    var_pFL = alfa * var_desempleo
    return pF0L + var_pFL
    