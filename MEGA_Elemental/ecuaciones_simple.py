import numpy as np
import pandas as pd

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

    F = np.zeros((nsec, nfac))
    for i in range(nsec):
        for j in range(nfac):
            F[i,j] = beta[i,j] / pf[j] * y[0][i]

    #F = ((beta * y).T / pf).T
    return F

def ingreso_sectores(pp, wp):
    # ingreso de cada sector a través de las compras de los consumidores
    ncon = wp.shape[0]
    npro = len(pp)
    ing = np.zeros(npro) 
    for i in range(ncon):
        for j in range(npro):
            ing[j] += wp[i,j] * pp[j][0]
    return ing

def coste_factores_por_sectores(pf, wf):
    # renta de cada factor para el total de consumidores
    nsec = wf.shape[0]
    nfac = len(pf)
    coste = np.zeros(nsec) 
    for i in range(nsec):
        for j in range(nfac):
            coste[i] += wf[i,j] * pf[j][0]
    return coste

def alfa_CobbDouglas(p, X):
    '''
    calcula los valores del parámetro alfa de la funcion de utilidad.
    La fórmula se obtiene despejando alfa de la formula de máxima utilidad y
    teniendo en cuenta que los ingresos por los factores deben igualar al gasto en productos
    (gastamos todo lo que tenemos)
    suma (cantidades demandadas * precio productos) = 
    suma (cantidad de factores suministrados * precio de los factores)
    
    argumentos:
        p: precio de los productos
        x: demanda de productos
    '''
    return X * p / X.dot(p)

def beta_CobbDouglas(pf, F):
    '''
    Obtiene los coeficientes de participación (beta) de los factores en la función de producción
    '''
    Z = F * pf
    # sumamos cada fila que es un sector
    denominador = Z.sum(axis=1)
    '''
    beta2 = np.zeros((F.shape[0], F.shape[1]))
    for i in range(F.shape[0]):
        for j in range(F.shape[1]):
            beta2[i,j] = F[i,j] / denominador[i]
    '''
    beta = (Z.T / denominador).T
    return beta

def b_CobbDouglas(pf, F, p, beta):
    
    Z = (F * pf).sum(axis=1) / p
    ns = F.shape[0]
    nh = F.shape[1]
    denominador = np.ones(ns)
    for i in range(ns):
        for j in range(nh):
            denominador[i] = denominador[i] * (F[i,j] ** beta[i,j])
    return Z / denominador