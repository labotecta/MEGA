'''
El esquema del modelo de cálculo es el siguiente:

1.  Usamos la función de máxima utilidad (Cobb Douglas o CES) para determinar la demanda de productos optima (de máxima utilidad) para cada consumidor de
    acuerdo a unos precios iniciales (exógenos) de los productos. Será un vector para cada consumidor con el consumo (cantidad) de cada uno de los productos
2.  Comparada la demanda (cantidad) optima total (por todos los consumidores) de cada producto con la demanda objetivo total (exógena:cantidades iniciales) de ese producto,
    aparecen unas diferencias.
3.  Calculamos cuales deben ser los precios de los productos (en lugar de los precios iniciales) para que esas diferencias se anulen. Para el sistema, la demanda
    total de cada producto será igual al dato exógeno, pero no para cada consumidor por separado.

El resultado serán un vector de demandas (cantidades) optimas (de equilibrio) para cada consumidor
y un vector de precios (de equilibrio) optimos de los productos.

Antes de crear un modelo, se presentan unos casos (def introduccion) con el único objetivo de
ver las demandas de productos optimas sin dar el paso (3), es decir no se calcularán los
precios de equilibrio.
Estos casos se pueden ignorar y ver directamente los casos completos porque son
suficientemente descriptivos para entender todo el proceso.
'''
'''
ATENCION !
el parámetro 'axis' de la función 'sum' (y de otras) puede resultar engañoso, en la literatura se dice que cuando axis=0 se suma por columnas, es decir, para cada columna se suman
los valores en esa columna de todas las filas y cuando axis=1 se suma por filas, y esto es incorrecto excepto para una matriz de dos dimensiones por pura casualidad
'axis' se refiere al ordinal de la dimensión, en una matriz de dos dimensiones, el 0 es la primera dimensión que son las filas y el 1 la segunda dimensión que son las columnas
y todo es como deciamos al principio, con axis=0 se suman los valores de todas las filas, pero que pasa para un vector que solo tiene una dimensión y N elementos, esperariamos obtener el 
mismo vector, porque solo hay una fila que nosotros asimilamos inconscientemente a una matriz con una fila y N columnas, pero resulta que obtenemos la suma de
todos los elemntos del vector, porque suma todos los elementos de la dirección 0, la primera y unica dirección.
'''
#from ast import arg
import os
import sys
import copy
import numpy as np
#from scipy.misc import derivative
from scipy.optimize import root, minimize
import itertools
import matplotlib.pyplot as plt
import pandas as pd
from pandas import Series, DataFrame

import equations as eq
import calibrate
import funciones as mfun
import modelo
import ecuaciones_simple as simple

INTRO1       = False
INTRO2       = False
INTRO3       = False
INTRO4       = False
INTRO5       = True
UTILIDAD     = 'CES'
UTILIDAD     = 'COBD'
UTILIDAD     = 'LEON'
SIGMA        = 0.9 # elasticidad de sustitución
SIGMA        = 0.01
SIGMA        = 100.0
DIBUJAR      = True
DETALLE_ROOT = False
DEPURAR      = False
DEPURAR_CGE  = True
OBJETIVO_CGE = 'C'

SENDA_DATOS        = 'C:/MEGA/Datos'
SENDA_SALIDAS      = 'C:/MEGA/SalElemental/Salidas'
SENDA_GRAFICOS     = '{}/Graficos'.format(SENDA_SALIDAS)
sufijo             = 'salida_{}_{}_{}_{}_{}_{}'.format(OBJETIVO_CGE, INTRO1, INTRO2, INTRO3, INTRO4, INTRO5, '_' + str(SIGMA) if UTILIDAD == 'CES' else '')

FICHERO_LOG        = '{}/{}_{}.log'.format(SENDA_SALIDAS, sufijo, UTILIDAD)
mfun.ini(FICHERO_LOG)

FICHERO_SAM        = '{}/{}.xlsx'.format(SENDA_DATOS, "SAM")
FICHERO_SAM_SIMPLE = '{}/{}.xlsx'.format(SENDA_DATOS, "SAM_simple")

os.makedirs(SENDA_SALIDAS, exist_ok=True)
if DIBUJAR:
    os.makedirs(SENDA_GRAFICOS, exist_ok=True)

def imprime(texto, rc=True):
    mfun.imprime(texto, rc)

def utilidad(x, alfa, sigma=SIGMA):
    if UTILIDAD == 'COBD':
        return utilidad_CobbDouglas(x, alfa)
    else:
        return utilidad_CES(x, alfa, sigma)

def demanda_maxima_utilidad(p, w, alfa, I, sigma=SIGMA):
    if UTILIDAD == 'COBD':
        return demanda_maxima_utilidad_CobbDouglas(p, w, alfa, I)
    else:
        #return demanda_maxima_utilidad_CES_num(p, w, alfa, sigma)  # solución númerica
        return demanda_maxima_utilidad_CES(p, w, alfa, sigma)       # solución analítica

def utilidad_CobbDouglas(x, alfa):
    '''
    Calcula la utilidad para cada uno de los consumidores con la fórmula (preferencias) Cobb-Douglas

    x[i,j] es la cantidad consumida del producto j por el consumidor i 
    alfa[i,j] es el parámetro de participación del producto j para el consumidor i, debe ser > 0

    La función de utilidad Cobb-Douglas es una forma matemática utilizada en la teoría económica para representar
    la relación entre la cantidad de bienes o servicios consumidos y la utilidad o satisfacción que se obtiene de ellos.
    '''
    
    try:
        # el producto de los consumos de cada uno de los productos (x) elevado a la elasticidad (alfa) del producto
        u = (x ** alfa).prod(axis=1)
    except:
        u = (x ** alfa).prod()
    return u    # vector (vertical) de la utilidad de los vectores (filas) de demanda x[i]

def demanda_maxima_utilidad_CobbDouglas(p, w, alfa, I):
    '''
    Calcula el vector de cantidades demandadas optimas por cada consumidor.
    Lo que queremos es saber cuales son, para un consumidor, los consumos de cada producto, que con un determinado coste total para él,
    conducen a un máximo de la función Cobb-Douglas.
    El coste total a incurrir por el consumidor (y) lo obtenemos a partir de unos consumos iniciales (exogenos) y unos precios de partida (exógenos),
    aunque puede ser directamente un dato, el detalle de cantidades y precios son las fuentes de datos habituales y nos permite hacer comparaciones
    pero usar directamente un dato nos permite cambiar los escenarios
    '''
    if len(I) == 0:
        # el coste (y[i]) para el consumidor 'i' (total income) es la suma del precio por la cantidad consumida, para todos los productos
        y = w.dot(p)    # (N x M) * (M x 1) = (N x 1)
    else:
        # 'reshape' es para darle la misma forma que se obtiene cuando se multiplica la matriz de consumos 'w' por la de precios 'p' que es
        # una array cuyos elementos son listas de un sólo valor, [1.3] y no directamente 1.3
        ncon = w.shape[0]
        y = I.reshape(ncon, -1)
    # Este coste total (y) se reparte entre productos mediante una fórmula que se obtiene aplicando diversos teoremas y utilizando los multiplicadores de Lagrange y
    # que es en proporción a la elasticidad (alfa) del consumidor a cada producto, finalmente, la cantidad de cada producto es el coste dividido del precio del producto    

    # keepdims=True retiene el número de dimensiones de la matriz con 1 elemento para el eje sumado, si fuese False se eliminaría la dimensión sobre la que se suma
    x = ((alfa / alfa.sum(axis=1, keepdims=True) * y).T / p).T
    return x    # devuelve el vector de cantidades demandadas optimas

def utilidad_CES(x, alfa, sigma):
    '''
    x[i,j] es la cantidad consumida del producto j por el consumidor i 
    sigma es la elasticidad de sustitución, debe ser > 0
    alfa[i,j] es el parámetro de participación del producto j para el consumidor i, debe ser > 0 y Suma(j){alfa[i,j]} = 1. para todo i

    Existe un problema cuando sigma < 1 (y por tanto ro < 0) y uno de los consumos x[i,j] es 0, en este caso se intentará calcular 0 elevado a un número negativo
    que es lo mismo que 1 dividido por (0 elevado a un número positivo -que es 0-) luego tenemos una división por cero
    '''
    if alfa.ndim == 1:
        npro = alfa.shape[0]
    else:
        npro = alfa.shape[1]

    invsigma = 1. / sigma
    ro = (sigma - 1.)/sigma   # sigma = 1./(1. - ro)
    invro = sigma/(sigma - 1.)
    ncon = x.shape[0]
    u = np.zeros(ncon)
    for i in range(ncon):
        up = 0.
        for j in range(npro):
            if alfa.ndim == 1:
                # para la generación de los ´mapas de utilidad
                # los mismos valores de alfa para todos los consumidores

                up = up + (alfa[j] ** invsigma) * (x[i,j] ** ro)
            else:
                up = up + (alfa[i,j] ** invsigma) * (x[i,j] ** ro)
        u[i] = up ** invro
    return u

def demanda_maxima_utilidad_CES(p, w, alfa, sigma):
    uno_sigma = 1. - sigma

    y = w.dot(p)    # (N x M) * (M x 1) = (N x 1)
    ncon = w.shape[0]
    npro = w.shape[1]

    S = np.zeros(ncon)
    for i in range(ncon):
        for n in range(npro):
            S[i] = S[i] + (alfa[i,n] ** sigma) * (p[n][0] ** uno_sigma)

    x = np.zeros((ncon, npro))
    for i in range(ncon):
        for j in range(npro):
            x[i,j] = y[i][0] * ((alfa[i,j] / p[j][0]) ** sigma) / S[i]
    return x

# solución numérica ---->
def utilidad_CES_num(x, alfa, sigma):
    '''
    la diferencia con 'utilidad_CES' es que aquella calcula de un golpe para todos los consumidores
    y esta para un solo consumidor ('x' y 'alfa' son las filas del consumidor y no las matrices completas) y además devuelve el menos valor,
    porque queremos maximizar y usamos la función de 'scipy.optimize' de minimizar 'minimize'
    '''
    invsigma = 1. / sigma
    ro = (sigma - 1.)/sigma
    invro = sigma/(sigma - 1.)
    npro = alfa.shape[0]
    # x, alfa deben ser vectores porque la solución numérica se hace consumidor a consumidor ('ncon = 1'), por lo tanto 'u' tambien será un vector
    ncon = 1
    u = np.zeros(ncon)
    for i in range(ncon):
        up = 0.
        for j in range(npro):
            up = up + (alfa[j] ** invsigma) * (x[j] ** ro)
        # cambiada de signo 
        u[i] = -(up ** invro)
    return u

def restriccion_CES(x, p, w, i):
    # una restricción con 'type': 'ineq' significa que 'res' debe ser '>= 0' para que se cumpla la restricción
    '''
    x: vector de cantidades a probar
    p: vector de precios
    w: matriz inicial de cantidades (consumidores, productos)
    i: número de consumidor
    '''
    npro = w.shape[1]
    s1 = 0
    s2 = 0
    for j in range(npro):
        s1 = s1 + p[j] * x[j]
        s2 = s2 + p[j] * w[i,j]
    # la solución 's1' debe tener un coste <= que el dato 's2'
    res = s2 - s1
    return res

def demanda_maxima_utilidad_CES_num(p, w, alfa, sigma):
    '''
    la utilidad crece indefinidamente con el aumento de las cantidades consumidas
    hay que incorporar la resticción de que el coste de la solución debe ser inferior o igual al dato
    de hecho será igual al dato por lo dicho en la primera línea de este comentario
    '''
    ncon = w.shape[0]
    npro = w.shape[1]
    bnds = (((0, None), ) * npro)
    u = np.zeros((ncon, npro))
    '''
    Type of solver. Should be one of
    'Nelder-Mead'
    'Powell'
    'CG'
    'BFGS'
    'Newton-CG'
    'L-BFGS-B'
    'TNC'
    'COBYLA'
    'COBYQA'
    'SLSQP'
    'trust-constr'
    'dogleg'
    'trust-ncg'
    'trust-exact'
    'trust-krylov'
    custom - a callable object
    '''
    x0 = np.ones((1, npro)).reshape(npro)
    # hay que minimizar para cada consumidor por separado
    for i in range(ncon):
        # la restricción hay que definirla dentro del 'for' porque la fila de 'w' a procesar cambia para cada consumidor
        cons = ({'type': 'ineq', 'fun': restriccion_CES, 'args':(p,w,i)})
        sol = minimize(utilidad_CES_num, x0, args=(alfa[i], sigma),method='SLSQP', bounds=bnds, constraints=cons)
        u[i] = sol.x
    return u
# <---- solución numérica

def exceso_demanda_productos(p, w, alfa):
    # Demanda optima - demanda dato (exógena)

    z = demanda_maxima_utilidad(p, w, alfa, []).sum(axis=0) - w.sum(axis=0)
    return z

def exceso_demanda_productos_primer_precio_1(p, depurar, w, alfa, I):
    # calcula los excesos de demanda suponiendo que el precio del primer producto siempre es 1
    #   p = vector de precios de los productos 2 en adelante, porque el primero lo haremos 1

    p = p.reshape((np.max(p.shape), 1))
    p = np.vstack([[1], p]) # añade un primer precio igual a 1
    dmu = demanda_maxima_utilidad(p, w, alfa, I)
    # exceso del total de demanda de cada producto, por eso se suma para todos los consumidores (axis=0, para cada columna suma todas las filas que son la primera dirección)
    z = dmu.sum(axis=0) - w.sum(axis=0)
    if depurar:
        for i in range(dmu.shape[0]):
            imprime('{:3} '.format(i+1), False)
            for j in range(dmu.shape[1]):
                imprime('{:9.5f} '.format(dmu[i,j]), False)
            imprime('')
        imprime('{:3} '.format('Exc'), False)
        for j in range(z.shape[0]):
            imprime('{:9.2e} '.format(z[j]), False)
        imprime('')
        imprime('')

    return z[1:]    # devuelve los excesos de demanda de los productos 2 en adelante

def exceso_gasto_consumidor(p, depurar, w, alfa, I):
    # la dimensión del vector salida debe ser mayor o igual que la dimensión del vector de entrada (en este caso el precio)
    
    #p = p.reshape((np.max(p.shape), 1))
    #p = np.vstack([[1], p]) # añade un primer precio igual a 1

    gasto = np.zeros(N)
    for i in range(N):
        for j in range (M):
            gasto[i] = gasto[i] + w[i,j] * p[j]
    z = ((gasto - I) ** 2).sum()
    if depurar:
        for i in range(N):
            imprime('{:3} {:9.5f} {:9.5f} {:9.5f}'.format(i+1, gasto[i], I[i], gasto[i] - I[i]))
        imprime('')
    return z

def tabla_resultados(de, do, pe, po, nombre_con='', nombre_pro=''):
    # función para mostrar los resultados
    #   de : demánmda exogena
    #   do : demanda óptima
    ye = de.dot(pe)
    yo = do.dot(po)
    ncon = de.shape[0]    # número de consumidores
    npro = de.shape[1]    # número de productos
    if len(nombre_con) == 0:
        nombre_con = []
        for j in range(ncon):
            nombre_con.append(str(j+1))
    if len(nombre_pro) == 0:
        nombre_pro = []
        for j in range(npro):
            nombre_pro.append(str(j+1))
    
    exoge  = np.zeros(npro)
    equil  = np.zeros(npro)
    exceso = np.zeros(npro)
    imprime('')
    imprime('Productos ->                 ', False)
    for j in range(npro):
        imprime('--------- {:>8} --------  '.format(nombre_pro[j]), False)
    imprime('')
    imprime('Consumid  renta Me  renta Mo', False)
    for j in range(npro):
        imprime('   exógena equilibri  exceso ', False)
    imprime('')
    imprime('-------- --------- --------- ', False)
    for j in range(npro):
        imprime('--------- --------- -------  ', False)
    imprime('')
    for i in range(ncon):
        imprime('{:8} {:9.2f} {:9.2f} '.format(nombre_con[i], ye[i][0], yo[i][0]), False)
        for j in range(npro):
            exoge[j] = exoge[j] + de[i,j]
            equil[j] = equil[j] + do[i,j]
            ex = do[i,j] - de[i,j]
            exceso[j] = exceso[j] + ex
            imprime('{:9.2f} {:9.2f} {:7.2f}  '.format(de[i,j], do[i,j], ex), False)
        imprime('')
    imprime('-------- --------- --------- ', False)
    for j in range(npro):
        imprime('--------- --------- -------  ', False)
    imprime('')
    imprime('                             ', False)
    for j in range(npro):
        imprime('{:9.2f} {:9.2f} {:7.3f}  '.format(exoge[j], equil[j], exceso[j]), False)
    imprime('')

def tabla_precios(pe, po, nombre_pro=''):
    npro = len(pe)
    if len(nombre_pro) == 0:
        nombre_pro = []
        for j in range(npro):
            nombre_pro.add(str(j+1))
    imprime('          - precio exógeno -  precio de')
    imprime('Producto     dato relativo-1 equilibrio')
    imprime('-------- -------- ---------- ----------')
    for i in range(npro):
        imprime('{:8} {:8.5f} {:10.6f} {:10.6f}'.format(nombre_pro[i], pe[i][0], pe[i][0]/p[0][0], po[i][0]))
    imprime('-------- -------- ---------- ----------')

def tabla_cantidades_importes(de, pr, alfa, nombre_con='', nombre_pro=''):
    ncon = de.shape[0]
    npro = de.shape[1]
    if len(nombre_con) == 0:
        nombre_con = []
        for j in range(ncon):
            nombre_con.append(str(j+1))
    if len(nombre_pro) == 0:
        nombre_pro = []
        for j in range(npro):
            nombre_pro.append(str(j+1))
    imprime('         ', False)
    for j in range(npro):
        imprime(' {:>8} '.format(nombre_pro[j]), False)
    imprime('')
    imprime('         ', False)
    for j in range(npro):
        imprime('--------- '.format(j+1), False)
    imprime('')
    imprime('precios  ', False)
    for j in range(npro):
        imprime('{:9.4f} '.format(pr[j][0]), False)
    imprime('')
    imprime('         ', False)
    for j in range(npro):
        imprime('--------- '.format(j+1), False)
    imprime('')
    imprime('cantidades / utilidad')
    u = utilidad(de, alfa)
    sp = np.zeros(npro)
    for i in range(ncon):
        imprime('{:8} '.format(nombre_con[i]), False)
        for j in range(npro):
            imprime('{:9.4f} '.format(de[i,j]), False)
            sp[j] = sp[j] + de[i,j]
        imprime('{:9.4f} '.format(u[i]))
    imprime('         ', False)
    for j in range(npro):
        imprime('--------- '.format(j+1), False)
    imprime('')

    imprime('         ', False)
    for j in range(npro):
        imprime('{:9.4f} '.format(sp[j]), False)
    imprime('')
    imprime('importes / total importe')
    si = np.zeros(npro)
    for i in range(ncon):
        imprime('{:8} '.format(nombre_con[i]), False)
        suma = 0.
        for j in range(npro):
            v = de[i,j] * pr[j][0]
            suma = suma + v
            imprime('{:9.4f} '.format(v), False)
            si[j] = si[j] + v
        imprime('{:9.4f} '.format(suma))
    imprime('         ', False)
    for j in range(npro):
        imprime('--------- '.format(j+1), False)
    imprime('')
    imprime('         ', False)
    for j in range(npro):
        imprime('{:9.4f} '.format(si[j]), False)
    imprime('{:9.4f} '.format(si.sum(axis=0)))
    imprime('')
    return si

def normaliza_alpha(alfa):
    if alfa.ndim == 1:
        npro = alfa.shape[0]
        s = 0.
        for j in range(npro):
            s = s + alfa[j]
        for j in range(npro):
            alfa[j] = alfa[j] / s
    else:
        ncon = alfa.shape[0]
        npro = alfa.shape[1]
        for i in range(ncon):
            s = 0.
            for j in range(npro):
                s = s + alfa[i,j]
            for j in range(npro):
                alfa[i,j] = alfa[i,j] / s
    return alfa

def dibujarMapa():
    # vamos a repesentar un mapa con los valores de la utilidad para un consumidor (N=1) en función del consumo de los dos (M=2) productos
    # utilizando valores inventados para las elasticidades (alfa) y los consumos (x)

    N = 1   # consumidores
    M = 2   # productos
    # 'alfa': exponentes de la función de utilidad (elasticidad), una matriz con tantas filas como consumidores y tantas columnas como productos
    # cada consumidor tiene sus propias elasticidades para el consumo de cada uno de los productos
    alfa = np.array([0.5, 0.5])        
    normaliza_alpha(alfa)
    
    # generamos todos los valores que van de 0 a 10 (ambos inclusive) de centesima en centesima
    x = np.linspace(0, 10, num=100)     

    # ahora, 'itertools.product' genera todas las posibles combinaciones de los elementos de x, tomadas de M en M (repeat), que son 'len(x) ** M' elementos = 100 ** 2 = 10000
    # los elementos de X son las posibles cantidades demandadas por el único consumidor (N=1) de los 2 productos (M=2), es decir, 2 valores
    X = np.array([i for i in itertools.product(x, repeat=M)])   

    # calculamos la utilidad de cada uno de los elementos de X, es decir, de cada una de las 10000 posibles combinaciones de consumos de los dos productos

    if UTILIDAD == 'LEON':
        u = np.min(X/alfa, axis=1)
    else:
        u = utilidad(X, alfa)
    imprime('utilidades: máxima = {} mínima= {}'.format(max(u), min(u)))

    # dibujamos (2D) la utilidad en función del consumo de ambos productos
    fig, ax = plt.subplots(figsize=(10,7))
    plt.contourf(x, x, u.reshape(len(x), len(x)), levels=30)   # dibuja lineas de contorno para 30 valores de utilidad (30 curvas de nivel), las líneas que unen los puntos de la misma utilidad
    plt.xlabel('Producto 1', size=18)
    plt.ylabel('Producto 2', size=18)
    if UTILIDAD == 'CES':
        nombre = '/mapa_2D_{}_{}'.format(UTILIDAD, SIGMA)
        plt.title('Curvas de equi-utilidad (misma utilidad) {} {}'.format(UTILIDAD, SIGMA), size=22)
    else:
        nombre = '/mapa_2D_{}'.format(UTILIDAD)
        plt.title('Curvas de indiferencia (misma utilidad) {}'.format(UTILIDAD), size=22)

    plt.savefig(SENDA_GRAFICOS + nombre + '.png', dpi = 300, facecolor = 'w', edgecolor = 'w', orientation = 'portrait', format = 'png', transparent = False, bbox_inches = None, pad_inches = 0.1, metadata = None)
    plt.close()

    # en 3D, con el valor de la utilidad en el eje z
    from mpl_toolkits.mplot3d import Axes3D
    xx, yy = np.meshgrid(x, x)
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    surf = ax.plot_surface(xx, yy, u.reshape(len(x), len(x)), rstride=1, cstride=1, cmap='viridis')
    ax.set_xlabel('Producto 1', size=18)
    ax.set_ylabel('Producto 2', size=18)
    ax.set_zlabel('Utilidad', size=18)

    # 'plt.show()' traemos esta senrtencia aquí para que al detenerse la ejecución estén los dos gráficos ya dibujados
    # plt.show()

    if UTILIDAD == 'CES':
        nombre = '/mapa_3D_{}_{}'.format(UTILIDAD, SIGMA)
        ax.set_title('{} {}'.format(UTILIDAD, SIGMA), size=22)
    else:
        nombre = '/mapa_3D_{}'.format(UTILIDAD)
        ax.set_title(UTILIDAD, size=22)
    plt.savefig(SENDA_GRAFICOS + nombre + '.png', dpi = 300, facecolor = 'w', edgecolor = 'w', orientation = 'portrait', format = 'png', transparent = False, bbox_inches = None, pad_inches = 0.1, metadata = None)
    plt.close()
    if UTILIDAD == 'LEON':
        imprime('----------------------------')
        imprime('Fin.')
        imprime('----------------------------')
        imprime('')
        sys.exit()

def caso(N, M, alfa, w, p, nombre_con, nombre_pro, metodo='hybr'):
    imprime('')
    imprime('-----------------------------------------------------------')
    imprime('Cálculo del equilibrio. {} consumidores y {} productos.'.format(N, M))
    imprime('-----------------------------------------------------------')
    if len(nombre_con) == 0:
        nombre_con = []
        for j in range(N):
            nombre_con.append(str(j+1))
    if len(nombre_pro) == 0:
        nombre_pro = []
        for j in range(M):
            nombre_pro.append(str(j+1))

    imprime('')
    imprime('Datos exógenos')
    imprime('--------------------------------------------------------------------------------')
    imprime('')
    imprime('Matriz de coeficientes alfa (elasticidades)')
    imprime('')
    imprime('Consumid ', False)
    for j in range(M):
        imprime('{:>8}  '.format(nombre_pro[j]), False)
    imprime('')
    imprime('-------- ', False)
    for j in range(M):
        imprime('--------- ', False)
    imprime('')
    for i in range(N):
        imprime('{:8} '.format(nombre_con[i]), False)
        for j in range(M):
            imprime('{:9.4f} '.format(alfa[i,j]), False)
        imprime('')
    imprime('         ', False)
    for j in range(M):
        imprime('--------- ', False)
    imprime('')
    
    normaliza_alpha(alfa)
    suma = alfa.sum(axis=1)
    imprime('')
    imprime('Consumid  sum.alfa')
    imprime('-------- ---------')
    for i in range(suma.shape[0]):
        imprime('{:8} {:9.4f}'.format(nombre_con[i], suma[i]))
    imprime('-------- ---------')
    imprime('')

    # 'I': renta disponible
    I = np.zeros(N, dtype=float)
    Is = 0.
    suma = np.zeros(M, dtype=float)
    imprime('Consumid ', False)
    for j in range(M):
        imprime('{:>8}  '.format(nombre_pro[j]), False)
    imprime('renta dis')
    imprime('-------- ', False)
    for j in range(M):
        imprime('--------- ', False)
    imprime('---------')
    for i in range(N):
        imprime('{:8} '.format(nombre_con[i]), False)
        for j in range(M):
            suma[j] = suma[j] + w[i,j]
            I[i] = I[i] + w[i,j] * p[j][0]  # el [0] es para sacar el valor ya que 'p' es una array cuyos elementos son listas de un valor ej: [1.3]
            imprime('{:9.3f} '.format(w[i,j]), False)
        imprime('{:9.3f}'.format(I[i]))
        Is = Is + I[i]
    imprime('-------- ', False)
    for j in range(M):
        imprime('--------- ', False)
    imprime('---------')
    imprime('         ', False)
    for j in range(M):
        imprime('{:9.3f} '.format(suma[j]), False)
    imprime('{:9.3f}'.format(Is))
    imprime('')
    imprime('fin datos exógenos')
    imprime('--------------------------------------------------------------------------------')

    # demanda optima con los precios 'p'
    demanda_opt = demanda_maxima_utilidad(p, w, alfa, [])
    exceso_demanda = exceso_demanda_productos(p, w, alfa)
    imprime('\nexceso de demandas por productos con los precios iniciales\n', False)
    imprime('Producto exceso dem')
    imprime('-------- ----------')
    for i in range(exceso_demanda.shape[0]):
        imprime('{:8} {:10.3e}'.format(nombre_pro[i],exceso_demanda[i]))
    imprime('-------- ----------')
    imprime('')
    imprime('\nexceso de demandas por productos con el precio del primer producto = 1\n', False)
    # pasamos todos los precios menos el primero porque 'exceso_demanda_productos_primer_precio_1' lo añade con valor 1
    exceso_demanda2 = exceso_demanda_productos_primer_precio_1(np.ones((1, M-1)).T, False, w, alfa, []) 
    imprime('Producto exceso dem')
    imprime('-------- ----------')
    for i in range(exceso_demanda2.shape[0]):
        imprime('{:8} {:10.3e}'.format(nombre_pro[i+1], exceso_demanda2[i]))
    imprime('-------- ----------')
    imprime('')
    
    '''
    parámetros de la función 'root'
    1.    'exceso_demanda_procutos_primer_precio_1' es la función que debe converger a 0
    2.    un valor inicial para la solución (el precio p que es el primer argumento de la función y que inicializamos con 1.)
    3.    'args' resto de argumrntos de la función 'exceso_demanda_procutos_primer_precio_1'
    4.    method =
              'hybr'
              'lm'
              'broyden1'
              'broyden2'
              'anderson'
              'linearmixing'
              'diagbroyden'
              'excitingmixing'
              'krylov'
              'df-sane'
    '''

    # pasamos como solución inicial un vector con los precios de todos los productos menos uno (np.ones((1, M-1))) con valor 1.
    # para que 'exceso_demanda_productos_primer_precio_1' añada un primer precio con valor 1 (para el primer producto).

    sol = root(exceso_demanda_productos_primer_precio_1, np.ones((1, M-1)).T, args=(False, w, alfa, []), method=metodo)
    imprime('')
    if sol['success'] == False:
        clave = 'method'
        imprime('{} {}'.format(clave, sol[clave]))
        clave = 'message'
        imprime('{} {}'.format(clave, sol[clave]))
        clave = 'status'
        imprime('{} {}'.format(clave, sol[clave]))
        clave = 'nfev'
        imprime('{} {}'.format(clave, sol[clave]))
    else:
        imprime('solución')
        imprime('')
        if DETALLE_ROOT:
            claves = list(sol.keys())
            for clave in claves:
                imprime('{} {}'.format(clave, sol[clave]))
        else:
            clave = 'method'
            imprime('{} {}'.format(clave, sol[clave]))
            clave = 'message'
            imprime('{} {}'.format(clave, sol[clave]))
            clave = 'status'
            imprime('{} {}'.format(clave, sol[clave]))
            clave = 'nfev'
            imprime('{} {}'.format(clave, sol[clave]))
        imprime('')
            
        pstar = sol.x
        pstar = pstar.reshape((np.max(pstar.shape), 1))
        pstar = np.vstack([[1], pstar])
        tabla_precios(p, pstar, nombre_pro)
        '''
        con los nuevos precios las demandas optimas cambian pero la demanda total de cada producto es la misma que la exógena
        porque los precios se han elegido para que esto sea así, ya que las utilidades optimas siempre son las que tienen un
        coste igual al dato (la resticción es que sea inferior o igual, pero es evidente que será igual)
        '''
        demanda_fin = demanda_maxima_utilidad(pstar, w, alfa, [])
        tabla_resultados(w, demanda_fin, p, pstar, nombre_con, nombre_pro)

        exceso_demanda = exceso_demanda_productos(pstar, w, alfa)
        imprime('\nexceso de demandas por productos con precios de equilibrio\n', False)
        imprime('Producto exceso dem')
        imprime('-------- ----------')
        for i in range(exceso_demanda.shape[0]):
            imprime('{:8} {:10.3e}'.format(nombre_pro[i],exceso_demanda[i]))
        imprime('-------- ----------')
        imprime('')

        imprime('')
        imprime('Para los valores exógenos')
        sie = tabla_cantidades_importes(w, p, alfa, nombre_con, nombre_pro)
        imprime('')
        imprime('')
        imprime('Para los valores de equilibrio')
        sio = tabla_cantidades_importes(demanda_fin, pstar, alfa, nombre_con, nombre_pro)

        imprime('')
        imprime('')
        imprime('Para los valores de equilibrio con un importe total incurrido, por el total de consumidores, igual al dato exógeno')
        # pata poder compara, factorizar los precios para el total de importes incurridos por todos los consumidores sea igual al correspondiente dato exógeno
        f = sie.sum(axis=0)/sio.sum(axis=0)
        demanda_fin_aj = demanda_maxima_utilidad(f * pstar, w, alfa, [])
        tabla_resultados(w, demanda_fin_aj, p, f * pstar, nombre_con, nombre_pro)
        tabla_cantidades_importes(demanda_fin_aj, f * pstar, alfa, nombre_con, nombre_pro)

        # Ahora incrementamos un 10% la renta disponible del primer consumidor

        imprime('')
        imprime('..................................................................................................')
        imprime('El modelo una vez encontrado el equilibrio es el modelo calibrado')
        # los valores de demanda inicial son los del modelo calibrado (los que resultan del equilibrio) ya que vamos a comparar respeto a él
        w = demanda_fin
        # la renta disponible 'I' es la del modelo calibrado, con un incremento del 10% para el primer consumidor 'I[0]'
        I = np.zeros(N)
        for i in range (N):
            for j in range(M):
                I[i] = I[i] + demanda_fin[i,j] * pstar[j][0]
        imprime('Ahora incrementamos un 10% la renta disponible del primer consumidor, la que resultó del calibrado')
        imprime('..................................................................................................')
        I[0] = I[0] * 1.1
        '''        
        aplicamos nuestro modelo CGE para encontrar el nuevo equilibrio con el objetivo de que el gasto total de cada
        consunidor se mantenga, para ello buscamos la solución de precios que minimiza la suma de cuadrados de las
        diferencias entre el gasto de la solución y el gasto objetivo.
        Usaremos la función 'minimize' porque no es posible usar la 'root' ya que esta exige que el vector a optimizar (entrada, 'p') debe
        ser menor o igual al de salida de la función que 'root' debe anular, y en nuestro caso la entrada son los precios, uno por producto,
        y la salida una desviación del gasto para cada consumidor, y el número de consumidores puede ser inferior al de productos.
        '''
        depurar = False
        if depurar:
            imprime('')
            imprime('Con gasto.tot gasto.obj exc.gasto')
            imprime('--- --------- --------- ---------')
        sol = minimize(exceso_gasto_consumidor, np.ones((1, M)).reshape(M), args=(depurar, w, alfa, I))
        if depurar:
            imprime('--- --------- --------- ---------')
            imprime('')
        if sol['success'] == False:
            clave = 'method'
            imprime('{} {}'.format(clave, sol[clave]))
            clave = 'message'
            imprime('{} {}'.format(clave, sol[clave]))
            clave = 'status'
            imprime('{} {}'.format(clave, sol[clave]))
            clave = 'nfev'
            imprime('{} {}'.format(clave, sol[clave]))
        else:
            imprime('solución')
            imprime('')
            if DETALLE_ROOT:
                claves = list(sol.keys())
                for clave in claves:
                    imprime('{} {}'.format(clave, sol[clave]))
            else:
                clave = 'message'
                imprime('{} {}'.format(clave, sol[clave]))
                clave = 'status'
                imprime('{} {}'.format(clave, sol[clave]))
                clave = 'nfev'
                imprime('{} {}'.format(clave, sol[clave]))
            imprime('')
            
            pstar = sol.x
            pstar = pstar.reshape((np.max(pstar.shape), 1))

            imprime('')
            imprime('Para los valores de equilibrio')
            demanda_fin = demanda_maxima_utilidad(pstar, w, alfa, [])
            sio = tabla_cantidades_importes(demanda_fin, pstar, alfa, nombre_con, nombre_pro)

            # para comprobar la coherencia de resultados resolvemos el modelo con los consumos ('demanda_fin') que se acaban de obtener

            imprime('')
            imprime('Comprobación')

            f = pstar[0] 
            sol = root(exceso_demanda_productos_primer_precio_1, np.ones((1, M-1)).T, args=(False, demanda_fin, alfa, []), method=metodo)
            pstar = sol.x
            pstar = pstar.reshape((np.max(pstar.shape), 1))
            pstar = (np.vstack([[1], pstar])) * f

            # para que que esta solución sea comparable, hay que factorizar los precios porque la solución de comprobación tiene 1. para el
            # primer producto y la anterior no

            demanda_test = demanda_maxima_utilidad(pstar, demanda_fin, alfa, [])
            sio = tabla_cantidades_importes(demanda_test, pstar, alfa, nombre_con, nombre_pro)

def introduccion():
    ###########################################################################################################################################################################
    # En primer lugar vamos a calcular las demandas optimas en una serie de casos, pero todavía no calcularemos precios optimos (de equilibrio) por lo que la suma de demandas
    # optimas para cada producto no tiene que coincidir con las demanfas de partida
    ###########################################################################################################################################################################

    N = 1   # consumidores
    M = 2   # productos
    imprime('')
    imprime('Caso  1. {} consumidores y {} productos'.format(N,M))
    imprime('---------------------------------------')
    alfa = np.array([[0.5, 0.5]]) 
    normaliza_alpha(alfa)

    # w : cantidad consumida (demandada), por nuestro único consumidor, de cada uno de los 2 productos (-variable exógena-, 1 unidad del primero y 2 del segundo producto) matriz 1x2
    w = np.array([[1, 2]])      

    # precio unitario de cada uno de los 2 productos (-variable exógena)-, 2 para el primero y 1 para el segundo, la trasponemos (.T (2x1)) para poder multiplicarlo por w 
    p = np.array([[2, 1]]).T 

    demanda_opt = demanda_maxima_utilidad(p, w, alfa, [])
    tabla_resultados(w, demanda_opt, p, p)
    # En este caso, no hay excesos de demanda, luego hay equilibrio económico, pero es que para un consumidor individual
    # las demandas optimas por los precios optimos están en equilibrio psean cuales sean los precios optimos

    # con 1 consumidor, 2 productos y dos factores
    N = 1
    M = 2
    imprime('')
    imprime('Caso  1b. {} consumidores y {} productos'.format(N,M))
    imprime('---------------------------------------')
    alfa = np.array([[0.2, 0.8]])
    normaliza_alpha(alfa)
    p = np.array([[1, 2]]).T
    w =  np.array([[0, 0]])
    pf = np.array([[2, 1]]).T       # precio de los factores
    wf = np.array([[10, 20]])       # consumo de factores
    I = wf.dot(pf)
    demanda_opt = demanda_maxima_utilidad_CobbDouglas(p, w, alfa, I)
    tabla_resultados(w, demanda_opt, p, p)

    N = 1
    M = 2
    imprime('')
    imprime('Caso 1c. 1 consumidores, 2 productos y 2 factores')
    imprime('-------------------------------------------------')
    alfa = np.array([[0.2, 0.8]])   # coeficientes de la función de utilidad
    normaliza_alpha(alfa)
    p = np.array([[1, 2]]).T        # precio de los productos
    pf = np.array([[2, 1]]).T       # precio de los factores
    wf = np.array([[10, 20]])       # consumo de factores

    demanda_opt = simple.demanda_maxima_utilidad_CobbDouglas(alfa, p, pf, wf)
    tabla_resultados_simple(alfa, demanda_opt, p, pf, wf)

    ##########################
    # con dos consumidores
    ##########################

    N = 2
    M = 2
    imprime('')
    imprime('Caso  2. {} consumidores y {} productos'.format(N,M))
    imprime('---------------------------------------')
    alfa = np.array([[0.5, 0.5], [0.25, 0.75]])
    normaliza_alpha(alfa)
    w = np.array([[1, 2], [2, 2]])
    p = np.array([[2, 1]]).T
    demanda_opt = demanda_maxima_utilidad(p, w, alfa, [])
    tabla_resultados(w, demanda_opt, p, p)
    if UTILIDAD == 'COBD':
        imprime('')
        imprime('Hay un exceso de producción para el producto 1 y un exceso de demanda para el producto 2')
        imprime('----------------------------------------------------------------------------------------')

    # con tres consumidores
    N = 3
    M = 2
    imprime('')
    imprime('Caso  3. {} consumidores y {} productos'.format(N,M))
    imprime('---------------------------------------')
    alfa = np.array([[0.5, 0.5], [0.25, 0.75], [0.5, 0.5]])
    normaliza_alpha(alfa)
    w = np.array([[1, 2], [2, 2], [1, 2]])
    p = np.array([[2, 1]]).T
    demanda_opt = demanda_maxima_utilidad(p, w, alfa, [])
    tabla_resultados(w, demanda_opt, p, p)
    if UTILIDAD == 'COBD':
        imprime('')
        imprime('Nuevamente, hay un exceso de producción para el producto 1 y un exceso de demanda para el producto 2')
        imprime('----------------------------------------------------------------------------------------------------')

    # con 2 consumidores y 4 productos (Economy with 2 individuals of each type and 4 goods 2 groups of identical goods)
    N = 2
    M = 4
    imprime('')
    imprime('Caso 4. {} consumidores y {} productos'.format(N,M))
    imprime('---------------------------------------')
    alfa = np.array([[0.5, 0.5] * 2, [0.25, 0.75] * 2])    # '* 2' no es una multiplicación es el número de repeticiones
    normaliza_alpha(alfa)
    w = np.array([[1, 2] * 2, [2, 2] * 2] )
    p = np.array([[2, 1] * 2]).T
    demanda_opt = demanda_maxima_utilidad(p, w, alfa, [])
    tabla_resultados(w, demanda_opt, p, p)
    if UTILIDAD == 'COBD':
        imprime('')
        imprime('Hay un exceso de producción para los productos 1 y 3, y un exceso de demanda para los productos 2 y 4')
        imprime('-----------------------------------------------------------------------------------------------------')

    # Misma economía con 6 consumidores y 2 productos
    N = 6
    M = 2
    imprime('')
    imprime('Caso  5. {} consumidores y {} productos'.format(N,M))
    imprime('---------------------------------------')
    alfa = np.array([[0.5, 0.5], [0.25, 0.75]] * 6)
    normaliza_alpha(alfa)
    w = np.array([[1, 2], [2, 2]] * 6)
    p = np.array([[2, 1]]).T
    demanda_opt = demanda_maxima_utilidad(p, w, alfa, [])
    tabla_resultados(w, demanda_opt, p, p)
    if UTILIDAD == 'COBD':
        imprime('')
        imprime('Hay un exceso de producción para los productos 1 y 3, y un exceso de demanda para los productos 2 y 4')
        imprime('-----------------------------------------------------------------------------------------------------')

    # Generando los valores al azar

    np.random.seed(123456)
    N = 5
    M = 10
    imprime('')
    imprime('Caso  6. {} consumidores y {} productos. Valores aleatorios'.format(N,M))
    imprime('--------------------------------------------------------------')
    alfa = np.random.uniform(0, 1, size=(N, M))
    normaliza_alpha(alfa)
    w = np.random.uniform(0, 1, size=(N, M))
    p = np.random.uniform(0, 1, size=(1, M)).T
    demanda_opt = demanda_maxima_utilidad(p, w, alfa, [])
    tabla_resultados(w, demanda_opt, p, p)
    if UTILIDAD == 'COBD':
        imprime('')
        imprime('Hay un exceso de producción para los productos 1, 7, 8 y 10, y un exceso de demanda para los otros')
        imprime('----------------------------------------------------------------------------------------------------')

'''
def demanda_maxima_utilidad_CES1(p, w, alfa, sigma):
    uno_sigma = 1. - sigma
    m_sigma = -sigma

    y = w.dot(p)    # (N x M) * (M x 1) = (N x 1)
    ncon = w.shape[0]
    npro = w.shape[1]
    x = np.zeros((ncon,npro))

    for i in range(ncon):
        for j in range(npro):
            S = 0.
            for n in range(npro):
                S = S + alfa[i,n]/alfa[i,j] * (p[n][0] ** uno_sigma)

            x[i,j] = y[i][0] * (p[j][0] ** m_sigma) / S
            x[i,j] = x[i,j] / p[j][0]   # pasar a cantidad
    return x

def demanda_maxima_utilidad_CES2(p, w, alfa, sigma):
    uno_sigma = 1. - sigma
    m_sigma = -sigma

    y = w.dot(p)    # (N x M) * (M x 1) = (N x 1)
    ncon = w.shape[0]
    npro = w.shape[1]
    x = np.zeros((ncon,npro))

    S = 0.
    for n in range(npro):
        S = S + (p[n][0] ** uno_sigma)

    for i in range(ncon):
        for j in range(npro):
            x[i,j] = y[i][0] * alfa[i,j] * (p[j][0] ** m_sigma) * S
            x[i,j] = x[i,j] / p[j][0]   # pasar a cantidad
    return x
'''

imprime('###################################################################')
if UTILIDAD == 'COBD':
    imprime('Utilidad: Cobb Douglas')
else:
    imprime('Utilidad: Elasticidad de sustitución constante (CES) {}'.format(SIGMA))
imprime('###################################################################')
imprime('')

if DIBUJAR:
    dibujarMapa()
if INTRO1:
    introduccion()

# ------------------------------------------------------------
# Equilibrio de precios
# ------------------------------------------------------------
'''
Necesitamos que los excesos de demanda sean cero, es decir, necesitamos encontrar el cero de la ecuación (función) que nos da los excesos de demanda
cosa que haremos mediante la función 'optimize.root' del paquete 'scipy.'

Hay que tener en cuenta dos cosas:
    1.  el equilibrio de precios sólo determina precios relativos, no absolutos. Hay varias opciones:
        a. elejir un precio igual a 1 para un determinado producto, lo más cómodo es para el primero.
        b. normalizar el vector de precios para que sumen 1
        c. igual que b, pero al final se factorizan los precios de equilibrio para que el importe total correspondiente a todos los
           consumidores sea el mismo que en los datos de entrada (exógenos)
    2.  la ley de Walras establece que si un mercado con M-1 productos está en equilibrio, el mercado con M productos tambien lo está, por esto
        la función de excesos de demanda que vamos a usar no calcula exceso para el primer producto.

La Ley de Walras es, en la teoría del equilibrio general, un principio que establece que la suma de la demanda (o demanda agregada) (D) debe
igualar, tomando en consideración los precios (p), a la suma de la oferta (S). Es decir,
    Σ pD - Σ pS = 0
En este mercado, los oferentes y demandantes actuan ejerciendo subastas simultáneas.
Estas subastas permiten que se encuentre el mejor precio para los oferentes (el más alto) y el mejor precio para los demandantes (el más bajo)

Como función de exceso de demanda vamos a usar 'exceso_demanda_procutos_primer_precio_1' que es una modificación de 'exceso_demanda_procutos' en
la que simplemente asignamos un precio igual a 1 al primer producto e ignoramos el exceso de demanda de este producto.
Esta función es el primer parámetro del método 'root'
'''
if INTRO2:
    # Economía 2×2

    N = 2 # consumidores
    M = 2 # productos
    alfa = np.array([[0.5, 0.5], [0.25, 0.75]])
    w = np.array([[1., 2.], [2., 2.]])
    p = np.array([[1., 0.5]]).T
    caso(N, M, alfa, w, p, '', '')

    # Ecomomia al azar 5x10

    np.random.seed(123456)
    N = 5  # consumidores
    M = 10 # productos
    alfa = np.random.uniform(0, 1/M, size=(N, M))
    w = np.random.uniform(0, 1/M, size=(N, M))
    p = np.random.uniform(0, 1, size=(1, M)).T
    # ponemos a 1. el precio del primer producto para hacerlo coherente con el procedimiento de solución que lo fija en ese mismo valor 
    p[0] = 1.

    caso(N, M, alfa, w, p, '', '', 'lm')

# Economia mediante la Matriz de contabilidad social (SAM en inglés)

'''
La Matriz de Contabilidad Social (MCS) es una extensión de la Matriz Insumo-Producto (MIP) de Wassily Leontief, e incluye,
además de la estructura de producción, datos sobre la distribución del ingreso y la estructura de la demanda de las instituciones.
Una MCS se diferencia de una MIP, así como del sistema de cuentas nacionales en la reproducción de información detallada acerca de
los diferentes grupos sociales que ella contiene, particularmente los hogares y su fuerza de trabajo.

Un modelo I-O captura las transacciones entre industrias, mientras que un MCS (SAM) es una extensión de un modelo I-O que captura las
    transacciones y transferencias entre industrias,
    entre industrias e instituciones,
    y entre instituciones.
'''

'''
Lo que pretendemos es calibrar el modelo, que es consegir que las ecuaciones del modelo reproduzcan los datos disponibles, en nuestro caso, que reproduzca la SAM del año base
Buscaremos del precios de equilibrio que ajustan las ecuaciones a la SAM
'''

if INTRO3:
    imprime('')
    imprime('#########################################################')
    imprime('  Economía mediante Matriz de Contabilidad Social (SAM)')
    imprime('#########################################################')

    # lee la SAM
    sam = pd.read_excel(FICHERO_SAM, index_col=0, header=0)
    nombre_con = list(sam.index)
    nombre_pro = sam.columns.values.tolist()
    N = M = sam.shape[0] - 1    # quitar la fila de totales

    alfa = np.random.uniform(0, 1/M, size=(N, M))

    wv = sam.to_numpy(copy=True)
    w = wv[0:N, 0:M]
    p = np.random.uniform(0, 1/M, size=(1, M)).T
    caso(N, M, alfa, w, p, nombre_con, nombre_pro, 'lm')

if INTRO4:
    # lee la SAM
    sam = pd.read_excel(FICHERO_SAM, index_col=0, header=0)

    # declara las variables (como 'tuple' que es igual que 'list' pero no modificable, lo que las hace más eficientes)
    u = (
        "AGR",
        "OIL",
        "IND",
        "SER",
        "LAB",
        "CAP",
        "LAND",
        "NTR",
        "DTX",
        "IDT",
        "ACT",
        "HOH",
        "GOV",
        "INV",
        "EXT",
    )
    ind = ("AGR", "OIL", "IND", "SER")  # sectores
    h = ("LAB", "CAP", "LAND", "NTR")   # factores
    w = ("LAB", "LAND", "NTR")

    def io_system(pvec, args):
        '''
        Esta es la función que se debe resolver.
        Calcula la desviación en el precio de suministro del producto domestico + importaciones (Armington) dado un vector de precios 'pvec'

        Args:
            pvec (Numpy array): Vector de precios
            args (tuple): Tuple (lista) de todos parámetros (argumentos) que se pasan (utilizan) a una u otra de las ecuaciones del modelo para
                          no tener que especificarlos de forma individual en la llamada a esta función

                p:   objeto de la clase 'parameters'
                d:   objeto de la clase 'model_data'
                ind: lista (tuple) de sectores
                h:   lista (tuple) de factores
                er:  variable exógena con el valor del tipo de cambio para las importaciones (The real exchange rate)
                pf:  precio de los factores

        Returns:
            p_error (Numpy array): Error de las ecuaciones, calculado como el error en el 'Domestic supply prices'
        '''
        # extraemos los argumentos a su variable correspondiente
        (p, d, ind, h, er, pf) = args

        # precios de equilibrio 'pq' (precios de los sectores), irán cambiando a cada iteración
        # 'pq' entra en la función 'eqpz'
        pq = pvec[0 : len(ind)]
        pq = Series(pq, index=list(ind)) # en forma de Series para asociarlos a las etiquetas de los sectores
        '''
        calcula los precios de importación en moneda local, simplemente multiplica los precios de importación en moneda extranjera por el tipo de cambio
            'er':   tipo de cambio
            'd.pWm' vector (Series) 'import price index' por sectores (productos) en moneda extranjera
        '''
        # el resultado 'pm' de 'eqpm' entra en la función ('eqpqbar') del calculo del precio de suministro del producto domestico + importaciones (Armington) (Domestic supply prices.)
        # y en la 'eq.eqpq' que calcula la diferencia entre este precio y el dato
        pm = eq.eqpm(er, d.pWm)
        '''
        Ecuación para calcular el precio del valor añadido de cada sector
        Es simplemente la ponderación de los precios de los factores 'pf' por sus coeficientes de participación 'beta' en la producción de cada sector
            pf:     precio de los factores
            p.beta: parámetro de participación en el coste del factor h = ("LAB", "CAP", "LAND", "NTR") de cada una de las producción de los sectores ind = ("AGR", "OIL", "IND", "SER")

        En este modelo será simpre 1. porqué ni 'pf' ni 'p.beta' cambian
        '''
        # el resultado 'py' de 'eqpy' entra en la función 'eqpz'
        py = eq.eqpy(pf, p.beta)

        if DEPURAR: 
            imprime('')
            imprime('Precios del valor añadido')
            imprime('Sector      precio')
            imprime('-------- ---------')
            etqs = py.index.tolist()
            for et in etqs:
                imprime('{:8} {:9.5f}'.format(et, py[et]))
            imprime('-------- ---------')
    
        '''
        Equation representing domestic Production/Output prices.
        Ecuación para calcular el ratio Producción doméstica / precios de producción
        El único que cambia porque cambia 'pq'
        '''
        pz = eq.eqpz(p.ay, p.ax, py, pq)

        if DEPURAR: 
            imprime('')
            imprime('Producción doméstica / precios de producción')
            imprime('Sector      precio')
            imprime('-------- ---------')
            etqs = py.index.tolist()
            for et in etqs:
                imprime('{:8} {:9.5f}'.format(et, py[et]))
            imprime('-------- ---------')

        '''
        NO ENTIENDO NADA
        'eq.eqpq' va a comparar un 'pq' que se ha hecho igual a 'pvec' (precios de los sectores) con un cálculo del precio de suministro del producto domestico + importaciones (Armington)
        '''
        pq_error = eq.eqpq(p.deltam, p.taum, p.tauz, pm, pz, pq)
        pq_error = pq_error.values

        return pq_error

    # Resolver 'io_system' que es la función que se pasará a 'root'

    dist = 10
    tpi_iter = 0
    tpi_max_iter = 30
    tpi_tol = 1e-10
    tpi_tol = 1e-15
    xi = 0.1

    # -------------------------------------------
    # Cálculo del vector de precios de equilibrio
    # -------------------------------------------
    imprime('')
    imprime('Cálculo del vector de precios de equilibrio')
    # 'pvec' valor inicial para los precios que se buscan (precios de los sectores), es decir, los precios de equilibrio
    pvec = np.ones(len(ind))

    # Crea un objeto 'd' de la clase 'model_data' que contiene los valores iniciales de las variables del modelo, los valores se asignan en
    # la función 'def __init__' que se llama automáticamente cuando se crea un objeto de esta clase, fundamentalmente a partir de los valores de la tabla SAM.
    d = calibrate.model_data(sam, h, u, ind)

    # Crea un objeto 'p' de la clase 'parameters' que contiene los valores de los parámetros del modelo, los valores se asignan en
    # la función 'def __init__' que se llama automáticamente cuando se crea un objeto de esta clase.
    p = calibrate.parameters(d, ind)    # ind = ("AGR", "OIL", "IND", "SER") sectores

    # Variables exógenas
    XXg = d.XXg0            # consumo del gobierno
    er = 1                  # tipo de cambio para las importaciones
    pf = np.ones(len(h))    # precio de los factores h = ("LAB", "CAP", "LAND", "NTR") todos a 1.

    # convertimos 'pf' en una Serie que es una vector de una dimensión que tiene asignada una etiqueta a cada dato, por defecto el ordinal del dato, pero
    # aquí le vamos a decir cuales son las eqtiquetas mediante el parámetro 'index=', esto nos permitirá acceder a los datos mediante la etiqueta que es más
    # descritivo que un ordinal, ej: pf['CAP'] en lugar de pf[1], aunque se asignen etiquetas se podría acceder por el ordinal, pero está deprecado.
    pf = Series(pf, index=list(h))
    pf = pf * 1 # ?? misterio

    # Comprobando la calibración 'inicial' del modelo
    io_args = [p, d, ind, h, er, pf]
    errors = io_system(pvec, io_args)
    imprime('')
    imprime('Error inicial del modelo. Desviación en el precio de suministro del producto domestico + importaciones (Armington)')
    for i in range(len(errors)):
        eti = pf.index[i]
        imprime('{:8} {:9.5f} '.format(eti, errors[i]), False)
    imprime('')
    imprime('')

    # Vamos a iterar para ir adaptando los precios de equilibrio 'pvec', que es lo único que se cambia en toda la ejecución del modelo
    imprime('Bucle de iteraciones')
    imprime('')

    while (dist > tpi_tol) & (tpi_iter < tpi_max_iter):
        tpi_iter += 1
        # 'io_args' son los parametros a pasar a la función 'io_system' para la que 'root' buscque una solución de precios 'pvec' que la haga cero

        io_args = [p, d, ind, h, er, pf]

        results = root(io_system, pvec, args=io_args, method="lm", tol=tpi_tol)
        pprime = results.x
        pqprime = pprime[0 : len(ind)]
        pqprime = Series(pqprime, index=list(ind))

        pvec = pprime
        for i in range(len(pvec)):
            imprime('{:8} {:9.5f} '.format(ind[i], pvec[i]), False)
        imprime('')
        '''
        Se hace el seguimiento de la desviación 'pq_error' en el precio de suministro del producto domestico + importaciones (Armington)
        como variable para determinar la convergencia de los resultados
        '''
        pq_error = io_system(pvec, io_args)

        # Se eleva al cuadrado y se hace la raíz cuadrada, salvo que sea una forma de calcular un valor absoluto de 'pq_error' no se porqué se hace
        dist = (((pq_error) ** 2) ** (1 / 2)).sum()

        imprime('La distancia en la iteración {} es {}'.format(tpi_iter, dist))

    imprime('')
    imprime('Modelo resuelto')
    imprime('')

    pm = eq.eqpm(er, d.pWm)
    py = eq.eqpy(pf, p.beta)
    pz = eq.eqpz(p.ay, p.ax, py, pqprime)

    imprime('Precios de importación')
    imprime('Sector      precio')
    imprime('-------- ---------')
    etqs = pm.index.tolist()
    for et in etqs:
        imprime('{:8} {:9.5f}'.format(et, pm[et]))
    imprime('-------- ---------')
    imprime('')
    imprime('Precios del valor añadido')
    imprime('Sector      precio')
    imprime('-------- ---------')
    etqs = py.index.tolist()
    for et in etqs:
        imprime('{:8} {:9.5f}'.format(et, py[et]))
    imprime('-------- ---------')
    imprime('')
    imprime('Ratio Producción doméstica / precios de producción')
    imprime('Sector      precio')
    imprime('-------- ---------')
    etqs = pz.index.tolist()
    for et in etqs:
        imprime('{:8} {:9.5f}'.format(et, pz[et]))
    imprime('-------- ---------')
    imprime('')

    # Calcula el precio del producto de Armington (domestico + importaciones) para cada sector
    pqbar = eq.eqpqbar(p.deltam, p.taum, p.tauz, pm, pz)

    imprime('Precio del consumo doméstico más las importaciones (precios de Armington), que debe tener cada sector (producto) para el equilibrio')
    imprime('Sector      precio')
    imprime('-------- ---------')
    etqs = pqbar.index.tolist()
    for et in etqs:
        imprime('{:8} {:9.5f}'.format(et, pqbar[et]))
    imprime('-------- ---------')
    imprime('')

if INTRO5:
    # declara las variables (como 'tuple' que es igual que 'list' pero no modificable, lo que las hace más eficientes)
    u = (
        "BRD",
        "MLK",
        "CAP",
        "LAB",
        "HOH",
    )
    ind = ("BRD", "MLK")    # sectores (industria)
    h = ("CAP", "LAB")      # factores de producción
    dem = ("HOH",)          # si no se pone la coma crea una lista de caracteres
    #dem = ("HOH1", "HOH2")

    # ejemplo de demanda óptima de dos productos consumidos por un único consumidor

    alfa = np.array([[0.2, 0.8]])
    normaliza_alpha(alfa)
    # vamos a calcular la cantidad óptima de productos (X), dado el precio (pf) y
    # la cantidad de factores (wf) suministrados, es decir, los ingresos
    pp = np.array([[1, 2]]).T       # precio de los productos

    # para calcular los ingresos
    pf = np.array([[2, 1]]).T       # precio de los factores
    wf = np.array([[10, 20]])       # cantidad de factores consumidos por los sectores (vendidos por HOH)

    X = simple.demanda_maxima_utilidad_CobbDouglas(alfa, pp, pf, wf)
    mfun.resultados_demanda(FICHERO_LOG, alfa, pp, X, pf, wf, dem, ind)
    
    # ejemplo de factores óptimos a utilizar por dos sectores que producen un sólo un producto cada uno de ellos

    # los coeficientes de participación (beta) del primer productor (sector) son:
    #   0.3 para el primer factor y 0.7 para el otro factor
    beta = np.array([[0.3, 0.7], [0.6, 0.4]])

    # vamos a obtener los consumos óptimos de factores (F) dado el precio (pp) y la
    # cantidad de productos producidos (wp), es decir, los ingresos
    wp = np.array([[10, 20]])       # demanda de cada sector
    F = simple.factores_maxima_utilidad_CobbDouglas(beta, pp, wp, pf)
    mfun.resultados_produccion(FICHERO_LOG, beta, pp, wp, pf, F, ind, h)

    #--------------------------------------------------------------------------------------
    # modelo CGE simple. Con dos sectores, dos factores de producción y un solo consumidor
    #--------------------------------------------------------------------------------------

    # leemos la Matriz de contabilidad social (sam) de esta economía

    sam = pd.read_excel(FICHERO_SAM_SIMPLE, index_col=0, header=0)

    # crea una clase (un simple contenedor) con las magnitudes a utilizar en el modelo y les asigna unos valores de acuerdo a la SAM
    datos = modelo.datos(sam, h, u, ind, dem)

    # crea una clase (un simple contenedor) con los parámetros del modelo y obtiene unos valores a partir de los datos de la SAM
    # obtener los valores de los parámetros es calibrar el modelo 
    parametros = modelo.parametros(datos)
    imprime('---------------------------------------------------------------------')
    imprime('Resultado del calibrado')
    imprime('---------------------------------------------------------------------')
    imprime('')
    imprime('Parámetros de paticipación (alfa) de los productos en la función de utilidad de la demanda')
    imprime('')
    fs = parametros.alfa.shape[0]
    cs = parametros.alfa.shape[1]
    imprime('Cons ', False)
    for j in range(cs):
        imprime('  {:>4}   '.format(ind[j]), False)
    imprime('')
    imprime('---- ', False)
    for j in range(cs):
        imprime('-------- ', False)
    imprime('')
    for i in range(fs):
        imprime('{:<4} '.format(dem[i]), False)
        for j in range(cs):
            imprime('{:8.5f} '.format(parametros.alfa[i,j]), False)
        imprime('')
    imprime('---- ', False)
    for j in range(cs):
        imprime('-------- ', False)
    imprime('')
    imprime('')
    imprime('Parámetros de paticipación (beta) de los factores en la función de producción')
    imprime('')
    fs = parametros.beta.shape[0]
    cs = parametros.beta.shape[1]
    imprime('Sect ', False)
    for j in range(cs):
        imprime('  {:>4}   '.format(h[j]), False)
    imprime('')
    imprime('---- ', False)
    for j in range(cs):
        imprime('-------- ', False)
    imprime('')
    for i in range(fs):
        imprime('{:<4} '.format(ind[i]), False)
        for j in range(cs):
            imprime('{:8.5f} '.format(parametros.beta[i,j]), False)
        imprime('')
    imprime('---- ', False)
    for j in range(cs):
        imprime('-------- ', False)
    imprime('')
    imprime('')
    imprime('Coeficiente de escalado (b) en la función de producción')
    imprime('')
    fs = parametros.beta.shape[0]
    cs = parametros.beta.shape[1]
    imprime('Sect        b')
    imprime('---- --------')
    for i in range(fs):
        imprime('{:<4} {:8.5f} '.format(ind[i], parametros.b[i]))
    imprime('---- --------')
    imprime('')
    
    # ---------------------------------------------------------------------
    # Solucíonar el CGE
    # ---------------------------------------------------------------------
    imprime('-------------------')
    imprime('Función objetivo {}'.format(OBJETIVO_CGE))
    imprime('-------------------')
    imprime('')

    def fun_objetivoA(pvec, args):
        '''
        dados 'wf' (unos valores iniciales de factores empleados por cada sector) y 'pvec' (el vector de precios de los productos 'pp' y de los factores 'pf')
        1. calculamos la demanda (wp) correspondiente a su renta disponible ('pf' * 'wf')
        2. calculamos la utilización de factores (wf) que los sectores consumen para producir esa demanda.
        3. calculamos la diferencia entre las demandas y entre los factores calculados respecto de las recibidas en los argumentos (args)
        esta diferencia es la que 'root' intentará hacer cero probando diferentes vectores de precios.
        Cuando las diferencias que calcula esta función sean cero, significa que los costes de los factores que resultan del paso 2 son los mismos que se
        usan (como ingresos) en el paso 1 y por tanto se ha alcanzado el equilibrio económico ya que los precios que se usan en los puntos 1 y 2 son los mismos.
        '''
        # extraemos los argumentos a sus variables correspondientes
        (iteracion, alfa, wp, wf, beta, b) = args

        # separamos los precios de los produtos de los de los factores
        pp = pvec[0:nsec].reshape(nsec,1)
        pf = pvec[nsec:(nsec + nfac)].reshape(nfac,1)

        wp_ini       = wp.sum(axis=0)   # suma vertical de todos los consumidores
        wf_ini       = wf.sum(axis=0)   # suma vertical de todos los sectores
        wp           = simple.demanda_maxima_utilidad_CobbDouglas(alfa, pp, pf, wf)
        wf           = simple.factores_maxima_utilidad_CobbDouglas(beta, pp, wp, pf)
        wp_fin       = wp.sum(axis=0)
        wf_fin       = wf.sum(axis=0)
        des_demanda  = wp_fin - wp_ini
        des_factores = wf_fin - wf_ini
        desvios      = np.concatenate((des_demanda, des_factores))
        if DEPURAR_CGE:
            mfun.tabla_2D(['dem. fin',], wp)
            mfun.tabla_2D(['fac. fin',], wf.sum(axis=0, keepdims=True))
            imprime('')

        return desvios
    
    def fun_objetivoB(pvec, args):
        '''
        dados 'wf y 'pvec'
        1. calculamos la demanda (wp) correspondiente a su renta disponible ('pf', 'wf').
        2. calculamos la utilización de factores (wf) que los sectores consumen para producir esa demanda.
        3. calculamos la diferencia entre las demandas y rentas disponibles calculadas respecto de las recibidas en los argumentos (args)
        '''
        # extraemos los argumentos a su variable correspondiente
        (iteracion, alfa, wp, wf, beta, b) = args

        # separamos precios de los productos 'pp' y precios de los factores ''
        pp = pvec[0:nsec].reshape(nsec,1)
        pf = pvec[nsec:(nsec + nfac)].reshape(nfac,1)

        wp_ini      = wp.sum(axis=0)    # suma vertical de todos los consumidores
        wf_ini      = wf.sum(axis=0)    # suma vertical de todos los sectores
        renta_ini   = simple.coste_factores_por_sectores(pf, wf)
        wp          = simple.demanda_maxima_utilidad_CobbDouglas(alfa, pp, pf, wf)
        wf          = simple.factores_maxima_utilidad_CobbDouglas(beta, pp, wp, pf)
        des_demanda = wp.sum(axis=0) - wp_ini
        renta_fin   = simple.coste_factores_por_sectores(pf, wf)
        des_renta   = renta_fin - renta_ini
        desvios     = np.concatenate((des_demanda, des_renta))

        #desvios = des_demanda[0]

        if DEPURAR_CGE:
            mfun.tabla_2D(['dem. fin',], wp)
            mfun.tabla_2D(['fac. fin',], wf.sum(axis=0, keepdims=True))
            mfun.tabla_2D(['rent fin',], np.expand_dims(renta_fin, 0))
            imprime('')
        return desvios
    
    def fun_objetivoC(pvec, args):
        '''
        dados 'wf' (unos valores iniciales de factores empleados por cada sector) y 'pvec' (el vector de precios de los productos 'pp' y de los factores 'pf')
        1. calculamos la demanda (wp) correspondiente a su renta disponible ('pf' * 'wf')
        2. calculamos la utilización de factores (wf) que los sectores consumen para producir esa demanda.
        3. calculamos la diferencia entre las demandas y entre los factores calculados respecto de las recibidas en los argumentos (args)
        esta diferencia es la que 'root' intentará hacer cero probando diferentes vectores de precios.
        Cuando las diferencias que calcula esta función sean cero, significa que los costes de los factores que resultan del paso 2 son los mismos que se
        usan (como ingresos) en el paso 1 y por tanto se ha alcanzado el equilibrio económico ya que los precios que se usan en los puntos 1 y 2 son los mismos.
        '''
        # extraemos los argumentos a sus variables correspondientes
        (iteracion, alfa, wp, wf, beta, b) = args

        # calcularemos suponiendo que el precio del primer producto siempre es 1
        # pvec = vector de precios de los productos 2 en adelante, porque el primero lo haremos 1
        #pvec = p.reshape((np.max(pvec.shape), 1))
        #pvec = np.vstack([[1.], pvec]) # añade un primer precio igual a 1
        pvec[0] = 1.

        # separamos los precios de los produtos de los de los factores
        pp = pvec[0:nsec].reshape(nsec,1)
        pf = pvec[nsec:(nsec + nfac)].reshape(nfac,1)

        wp_ini       = wp.sum(axis=0)   # suma vertical de todos los consumidores
        wf_ini       = wf.sum(axis=0)   # suma vertical de todos los sectores
        wp           = simple.demanda_maxima_utilidad_CobbDouglas(alfa, pp, pf, wf)
        wf           = simple.factores_maxima_utilidad_CobbDouglas(beta, pp, wp, pf)
        wp_fin       = wp.sum(axis=0)
        wf_fin       = wf.sum(axis=0)
        des_demanda  = wp_fin - wp_ini
        des_factores = wf_fin - wf_ini
        desvios      = np.concatenate((des_demanda, des_factores))
        if DEPURAR_CGE:
            mfun.tabla_2D(['dem. fin',], wp)
            mfun.tabla_2D(['fac. fin',], wf.sum(axis=0, keepdims=True))
            imprime('')

        return desvios

    def fun_objetivo(pvec, args):
        if OBJETIVO_CGE == 'A':
            return fun_objetivoA(pvec, args)
        elif OBJETIVO_CGE == 'B':
            return fun_objetivoB(pvec, args)
        elif OBJETIVO_CGE == 'C':
            return fun_objetivoC(pvec, args)
        else:
            sys.exit()

    # ciclo de convergencia
    max_iteraciones = 30
    tolerancia = 1.e-10
    ncon = len(dem)   # número de consumidores
    nsec = len(ind)   # número de sectores
    nfac = len(h)     # número de factores
    wp = np.full((ncon, nsec), 20.)
    wf = np.full((nsec, nfac), 10.)
    pvec = np.ones(nsec + nfac) # todos los precios (sectores + factores)
    
    # valores calibrados
    alfa_c = copy.deepcopy(parametros.alfa) # para que la nueva variable copie los valores y no el puntero a la otra variable 
    beta_c = copy.deepcopy(parametros.beta)

    # valores iniciales (escenario)    
    wp = np.array([[15, 35]])
    wf = np.array([[5, 10],[20, 15]])
    #wf = np.array([[5, 5],[20, 15]])
    #parametros.alfa[0,0] = 0.25
    #parametros.alfa[0,1] = 0.75

    # guardar para comparar con el resultado final
    pveci = copy.deepcopy(pvec)
    wpi = copy.deepcopy(wp)
    wfi = copy.deepcopy(wf)

    dist = 1.e+10
    iteracion = 0
    while (dist > tolerancia) & (iteracion < max_iteraciones):
        iteracion += 1
        wp_ini = wp
        '''
        'io_args' son los parametros a pasar a la función 'fun_objetivo' para la que 'root'
        buscque una solución de precios 'pvec' que la haga cero
        'root' iterará cambiando el valor de precios pero siempre con los mismos valores pasados en 'io_args'
        '''
        mfun.tabla_2D(['dem ini',], wp.sum(axis=0, keepdims=True))
        mfun.tabla_2D(['fac ini',], wf.sum(axis=0, keepdims=True))
        imprime('')
        imprime('')

        io_args = [iteracion, parametros.alfa, wp, wf, parametros.beta, parametros.b]
        results = root(fun_objetivo, pvec, args=io_args, method="lm", tol=tolerancia)
        if results['success'] == False:
            clave = 'method'
            imprime('{} {}'.format(clave, results[clave]))
            clave = 'message'
            imprime('{} {}'.format(clave, results[clave]))
            clave = 'status'
            imprime('{} {}'.format(clave, results[clave]))
            clave = 'nfev'
            imprime('{} {}'.format(clave, results[clave]))
            imprime('')
            sys.exit()

        pprime  = results.x
        pqprime = pprime[0 : nsec + nfac]
        pvec    = pprime

        if DEPURAR_CGE:
            imprime('terminada la iteración {:4}'.format(iteracion))
            imprime('Precios')
            imprime('--------------------------------------------------')
            for i in range(nsec):
                imprime('{:8} {:9.5f} '.format(ind[i], pvec[i]))
            for i in range(nfac):
                imprime('{:8} {:9.5f} '.format(h[i], pvec[nsec + i]))
            imprime('--------------------------------------------------')
            imprime('')

        # para calcular la distancia 'dist' y el valor de 'wf' a usar en la siguiente iteración

        pp = pvec[0:nsec].reshape(nsec,1)
        pf = pvec[nsec:(nsec + nfac)].reshape(nfac,1)
        (it, alfa, wp, wf, beta, b) = io_args
        wp      = simple.demanda_maxima_utilidad_CobbDouglas(alfa, pp, pf, wf)
        wf      = simple.factores_maxima_utilidad_CobbDouglas(beta, pp, wp, pf)
        coste   = simple.coste_factores_por_sectores(pf, wf)
        ingreso = simple.ingreso_sectores(pf, wf)
        desvios = fun_objetivo(pvec, io_args)
        dist = abs(desvios).sum()

        if DEPURAR_CGE:
            imprime('La distancia en la iteración {:4} es {:10.3e}'.format(iteracion, dist))

    if iteracion == max_iteraciones:
        imprime('')
        imprime('Superado el número máximo de iteraciones {:6}'.format(max_iteraciones))
        imprime('')
        imprime('Precios')
        for i in range(nsec):
            imprime('{:8} {:9.5f} '.format(ind[i], pvec[i]), False)
        imprime('')
        imprime('---------------------------------------------------------------------')
    else:
        imprime('---------------------------------------------------------------------')
        imprime('')
        imprime('Escenario')
        imprime('---------------------------------------------------------------------')
        imprime('')
        imprime('Elasticidad de la demanda (alfa) calibrado / escenario')
        mfun.tabla_2D(dem, alfa_c)
        mfun.tabla_2D(dem, parametros.alfa)
        imprime('')
        imprime('Elasticidad de la producción (beta) calibrado / escenario')
        mfun.tabla_2D(ind, beta_c)
        mfun.tabla_2D(ind, parametros.beta)
        imprime('')
        imprime('---------------------------------------------------------------------')
        imprime('Resultado del CGE')
        imprime('---------------------------------------------------------------------')
        imprime('')
        imprime('Precios iniciales / equilibrio')
        imprime('--------------------------------------------------')
        mfun.tabla_1D(ind, pveci[0:nsec])
        mfun.tabla_1D(h, pveci[nsec:nsec + nfac])
        imprime('')
        mfun.tabla_1D(ind, pvec[0:nsec])
        mfun.tabla_1D(h, pvec[nsec:nsec + nfac])
        imprime('--------------------------------------------------')
        imprime('')
        imprime('Demanda inicial / equilibrio')
        mfun.tabla_2D(dem, wpi)
        imprime('')
        mfun.tabla_2D(dem, wp)
        imprime('')
        imprime('Factores iniciales / equilibrio')
        mfun.tabla_2D(ind, wfi)
        imprime('')
        mfun.tabla_2D(ind, wf)
        imprime('')
        imprime('{:8.3f} Coste total de cada factor para cada sector'.format(coste.sum()))
        mfun.tabla_2D(['Factores',], np.expand_dims(coste, 0))
        imprime('')
        imprime('{:8.3f} Ingreso del total de los sectores (coste para la demanda de los productos)'.format(ingreso.sum()))
        mfun.tabla_2D(['Sectores',], np.expand_dims(ingreso,0))
        imprime('')

        if abs(pvec[0] - 1.) > 0.00001 :
            # normalizamos precios haciendo 1. al primero
            pvec = pvec / pvec[0]
            pp = pvec[0:nsec].reshape(nsec,1)
            pf = pvec[nsec:(nsec + nfac)].reshape(nfac,1)
            wp      = simple.demanda_maxima_utilidad_CobbDouglas(alfa, pp, pf, wf)
            wf      = simple.factores_maxima_utilidad_CobbDouglas(beta, pp, wp, pf)
            coste   = simple.coste_factores_por_sectores(pf, wf)
            ingreso = simple.ingreso_sectores(pp, wp)

            imprime('--------------------------------------------------')
            imprime('Precios escalados')
            imprime('--------------------------------------------------')
            mfun.tabla_1D(ind, pvec[0:nsec])
            mfun.tabla_1D(h, pvec[nsec:nsec + nfac])
            imprime('--------------------------------------------------')
            imprime('Demanda')
            mfun.tabla_2D(dem, wp)
            imprime('')
            imprime('Factores')
            mfun.tabla_2D(ind, wf)
            imprime('')
            imprime('{:8.3f} Coste total de cada factor para cada sector'.format(coste.sum()))
            mfun.tabla_2D(['Factores',], np.expand_dims(coste, 0))
            imprime('')
            imprime('{:8.3f} Ingreso del total de los sectores (coste para la demanda de los productos)'.format(ingreso.sum()))
            mfun.tabla_2D(['Sectores',], np.expand_dims(ingreso,0))
    imprime('')
