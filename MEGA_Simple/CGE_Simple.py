import os
import sys
import copy
import numpy as np
from scipy.optimize import root, minimize
import pandas as pd
from pandas import Series, DataFrame

if sys.version_info[0] != 3 or sys.version_info[1] > 9:
    raise Exception("La versión de phyton debe ser 3.9")

import funciones as mfun
import modelo
import ecuaciones_simple as simple

DEPURAR_CGE       = False
SALIDA_EJEMPLOS   = True
SALIDA_CALIBRADO  = True
OBJETIVO_CGE      = 'A'
OR_PRE_REFERENCIA = 3

SENDA_DATOS        = 'C:/MEGA/Datos'
SENDA_SALIDAS      = 'C:/MEGA/SalSimple/Salidas'
#SUFIJO             = 'Caso wf escalado por 3'
#SUFIJO             = 'Caso wf modificado'
SUFIJO             = 'Caso alfa modificado sin restriccion pF'
#SUFIJO             = 'Caso base'

FICHERO_LOG        = '{}/salida_{}_{}.log'.format(SENDA_SALIDAS, SUFIJO, OBJETIVO_CGE)
mfun.ini(FICHERO_LOG)

FICHERO_SAM_SIMPLE = '{}/{}.xlsx'.format(SENDA_DATOS, "SAM_simple")

os.makedirs(SENDA_SALIDAS, exist_ok=True)

def imprime(texto, rc=True):
    mfun.imprime(texto, rc)

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
if SALIDA_EJEMPLOS:
    imprime('Ejemplo de demanda óptima de dos productos consumidos por un único consumidor')
    imprime('-----------------------------------------------------------------------------')

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
    
    imprime('Ejemplo de factores óptimos a utilizar por dos sectores que producen un sólo un producto cada uno de ellos')
    imprime('----------------------------------------------------------------------------------------------------------')

    # los coeficientes de participación (beta) del primer productor (sector) son:
    #   0.3 para el primer factor y 0.7 para el otro factor
    beta = np.array([[0.3, 0.7], [0.6, 0.4]])

    # vamos a obtener los consumos óptimos de factores (F) dado el precio (pp) y la
    # cantidad de productos producidos (wp), es decir, los ingresos
    wp = np.array([[10, 20]])       # demanda de cada sector
    F = simple.factores_maxima_utilidad_CobbDouglas(beta, pp, wp, pf)
    mfun.resultados_produccion(FICHERO_LOG, beta, pp, wp, pf, F, ind, h)

imprime('----------------------------------------------------------------------------------------------------------')
imprime('Modelo CGE simple. Con dos sectores, dos factores de producción y un solo consumidor ---------------------')
imprime('----------------------------------------------------------------------------------------------------------')
imprime('####################################################################################')
imprime(SUFIJO)
imprime('####################################################################################')
imprime('')
imprime('Fichero SAM {}'.format(FICHERO_SAM_SIMPLE))
imprime('')

# leemos la Matriz de contabilidad social (sam) de esta economía
sam = pd.read_excel(FICHERO_SAM_SIMPLE, index_col=0, header=0)

'''
el fichero modelo.py contiene dos clases que, como cualquier clase, ejecutan el procedimiento 'def __init__' cuando se crea una variable de la clase
    datos       : la función 'def __init__' de esta clase crea una serie de variables y les asigna valores de acuerdo a la información leída de la SAM.
    parametros  : la función 'def __init__' de esta clase crea unas variables que son los parámetros de las funciones de utilidad y les
                  calcula unos valores de acuerdo a las ecuaciones que se deducen de la utilidad Cob Douglas, es decir, calibra el modelo.
'''
datos = modelo.datos(sam, h, u, ind, dem)
parametros = modelo.parametros(datos)
if SALIDA_CALIBRADO:
    imprime('---------------------------------------------------------------------')
    imprime('Resultado del calibrado')
    imprime('---------------------------------------------------------------------')
    imprime('')
    imprime('Parámetros de participación (alfa) de los productos en la función de utilidad de la demanda')
    imprime('')
    cs = parametros.alfa.shape[0]
    fs = parametros.alfa.shape[1]
    imprime('Cons ', False)
    for j in range(cs):
        imprime('  {:>4}   '.format(ind[j]), False)
    imprime('')
    imprime('---- ', False)
    for j in range(cs):
        imprime('-------- ', False)
    imprime('')
    for i in range(cs):
        imprime('{:<4} '.format(dem[i]), False)
        for j in range(fs):
            imprime('{:8.5f} '.format(parametros.alfa[i,j]), False)
        imprime('')
    imprime('---- ', False)
    for j in range(cs):
        imprime('-------- ', False)
    imprime('')
    imprime('')
    imprime('Parámetros de participación (beta) de los factores en la función de producción')
    imprime('')
    sc = parametros.beta.shape[0]
    fs = parametros.beta.shape[1]
    imprime('Sect ', False)
    for j in range(fs):
        imprime('  {:>4}   '.format(h[j]), False)
    imprime('')
    imprime('---- ', False)
    for j in range(fs):
        imprime('-------- ', False)
    imprime('')
    for i in range(sc):
        imprime('{:<4} '.format(ind[i]), False)
        for j in range(fs):
            imprime('{:8.5f} '.format(parametros.beta[i,j]), False)
        imprime('')
    imprime('---- ', False)
    for j in range(fs):
        imprime('-------- ', False)
    imprime('')
    imprime('')
    imprime('Coeficiente de escalado (b) en la función de producción')
    imprime('')
    imprime('Sect        b')
    imprime('---- --------')
    for i in range(sc):
        imprime('{:<4} {:8.5f} '.format(ind[i], parametros.b[i]))
    imprime('---- --------')
    imprime('')
    
# ---------------------------------------------------------------------
# Solucíonar el CGE
# ---------------------------------------------------------------------
ncon = len(dem)   # número de consumidores
nsec = len(ind)   # número de sectores
nfac = len(h)     # número de factores
imprime('-------------------------------------')
imprime('Función objetivo                 {:>3}'.format(OBJETIVO_CGE))
imprime('Ordinal del precio de referencia {:3}'.format(OR_PRE_REFERENCIA))
imprime('-------------------------------------')
imprime('')
imprime('---------------------------------------------------------------------')
imprime('Escenario')
imprime('---------------------------------------------------------------------')
imprime('')

# valores calibrados
# 'copy.deepcopy' para que la nueva variable copie los valores y no el puntero a la otra variable 
alfa_c = copy.deepcopy(parametros.alfa)
beta_c = copy.deepcopy(parametros.beta)

# valores iniciales del escenario
'''
los de la SAM, es decir, los del equilibrio de base
'''
wp = copy.deepcopy(datos.X0)
wf = copy.deepcopy(datos.F0)

# solución de prueba para 'root', todos los precios (sectores + factores) a 1.
pvec = np.ones(nsec + nfac)

'''
cambiando algunas cosas respecto al equilibrio base
'''
#wf = 3. * wf
#wf = np.array([[5, 5],[20, 15]])
parametros.alfa[0,0] = 0.35
#parametros.alfa[0,1] = 0.65

# guardar para comparar con el resultado final
wpi = copy.deepcopy(wp)
wfi = copy.deepcopy(wf)
pveci = copy.deepcopy(pvec)

imprime('Elasticidad de la demanda (alfa) calibrado / escenario')
mfun.tabla_2D(dem, alfa_c)
mfun.tabla_2D(dem, parametros.alfa)
imprime('')
imprime('Elasticidad de la producción (beta) calibrado / escenario')
mfun.tabla_2D(ind, beta_c)
mfun.tabla_2D(ind, parametros.beta)
imprime('')
if DEPURAR_CGE:
    imprime('Evolución de root')
    imprime('')

def fun_objetivoA(pvec, args):
    '''
    dados:
        'wf' (unos valores iniciales de factores empleados por cada sector) y
        'pvec' (el vector de precios de los productos 'pp' y de los factores 'pf')
    1. calculamos la demanda (wp) correspondiente a su renta disponible ('pf' * 'wf').
    2. calculamos la utilización de factores (wf) que los sectores utilizan para producir esa demanda.
    3. calculamos las producciones (Z) derivadas de los factores calculados en el punto anterior.
    4. calculamos las diferencias entre:
        las demandas y producciones.
        entre los factores calculados y los utilizado en el punto 1 (los recibidas en los argumentos -args-).
    estas diferencias son la que 'root' intentará hacer cero probando diferentes vectores de precios.
    
    El equilibrio se produce cuando se cumplen simultáneamente las tres ecuaciones:
        a. para cada producto: demanda = producción
        b. para cada factor: factor prestado por la demanda = suma de la utilización de ese factor por todos los productores = valor inicial por ser una variable exógena
        c. para cada precio: precio de compra de la demanda = precio de venta del productor
    las condiciones a y b se cumplen cuando las diferencias calculadas en el punto 4 son cero y la condición c porque se usa el mismo vector pvec para compras y ventas
    '''

    # pone el precio de referencia igual a 1.
    #pvec[OR_PRE_REFERENCIA] = 1.

    # extraemos los argumentos a sus variables correspondientes
    (iteracion, alfa, wp, wf, beta, b) = args

    # separamos los precios de los produtos de los de los factores
    pp = pvec[0:nsec].reshape(nsec,1)
    pf = pvec[nsec:(nsec + nfac)].reshape(nfac,1)

    wf_ini       = wf.sum(axis=0)   # suma vertical de todos los sectores
    wp           = simple.demanda_maxima_utilidad_CobbDouglas(alfa, pp, pf, wf)     # consumo de productos
    wf           = simple.factores_maxima_utilidad_CobbDouglas(beta, pp, wp, pf)    # utilización de factores
    Z            = simple.producciones(beta, b, wf)                                 # producciones
    wp_fin       = wp.sum(axis=0)   # suma vertical de todos los consumidores
    wf_fin       = wf.sum(axis=0)   # suma vertical de todos los sectores

    des_dem_pro  = wp_fin - Z       # el total de producción de un producto debe ser igual al consumo de ese producto
    des_factores = wf_fin - wf_ini  # la utilización total de cada factor debe ser la inicial ya que se considera una variable exógena
    desvios      = np.concatenate((des_dem_pro, des_factores))

    if DEPURAR_CGE:
        mfun.tabla_2D(['precios   ',], pvec.reshape(1,len(pvec)))
        mfun.tabla_2D(['dem, facts',], np.concatenate((wp, wf.sum(axis=0, keepdims=True)),axis=1))
        mfun.tabla_2D(['produccion',], Z.reshape(1,len(Z)))
        imprime('')

    return desvios

def fun_objetivoB(pvec, args):
    '''
    dados 'wf' (unos valores iniciales de factores empleados por cada sector) y 'pvec' (el vector de precios de los productos 'pp' y de los factores 'pf')
    1. calculamos la demanda (wp) correspondiente a su renta disponible ('pf' * 'wf')
    2. calculamos la utilización de factores (wf) que los sectores consumen para producir esa demanda.
    3. calculamos la diferencia entre las demandas y entre los factores calculados respecto de las recibidas en los argumentos (args)
    esta diferencia es la que 'root' intentará hacer cero probando diferentes vectores de precios.
    Cuando las diferencias que calcula esta función sean cero, significa que los costes de los factores que resultan del
    paso 2 son los mismos que se usan (como ingresos) en el paso 1 y por tanto se ha alcanzado el equilibrio económico ya que los
    precios que se usan en los puntos 1 y 2 son los mismos.

    Calcularemos suponiendo que el precio del primer producto siempre es 1
    pvec = vector de precios de los productos 2 en adelante, porque el primero lo haremos 1
    Esto debería dar problemas porque estamos cambiando la solución que 'root' pasa a esta función para probarla y por lo tanto la salida de la función (desvios)
    no es exactamente la que corresponde al vector 'pvec' que root ha enviado a esta función, pero funciona
    Sin embargo, usar root para seleccionar todos los precios menos uno (el primero) que se anadiría en esta función con valor 1. (np.hstack) para realizar los cálculos, no funciona.
    # añade un primer precio igual a 1.
    #pvec = np.hstack([[1.], pvec]) 
    '''

    pvec[OR_PRE_REFERENCIA] = 1.

    # extraemos los argumentos a sus variables correspondientes
    (iteracion, alfa, wp, wf, beta, b) = args

    # separamos los precios de los produtos de los de los factores
    pp = pvec[0:nsec].reshape(nsec,1)
    pf = pvec[nsec:(nsec + nfac)].reshape(nfac,1)

    wp_ini       = wp.sum(axis=0)   # suma vertical de todos los consumidores
    wf_ini       = wf.sum(axis=0)   # suma vertical de todos los sectores
    wp           = simple.demanda_maxima_utilidad_CobbDouglas(alfa, pp, pf, wf)     # consumo de productos
    wf           = simple.factores_maxima_utilidad_CobbDouglas(beta, pp, wp, pf)    # utilización de factores
    Z            = simple.producciones(beta, b, wf)                                 # producciones
    wp_fin       = wp.sum(axis=0)   # suma vertical de todos los consumidores
    wf_fin       = wf.sum(axis=0)   # suma vertical de todos los sectores
    des_demanda  = wp_fin - wp_ini
    des_factores = wf_fin - wf_ini
    desvios      = np.concatenate((des_demanda, des_factores))
    
    '''
    # restricción : compras = ingresos
    
    compras = 0.
    for i in range(ncon):
        for j in range(nsec):
            compras += wp[i,j] * pp[j]
    ingresos = 0.
    for i in range(nsec):
        for j in range(nfac):
            ingresos += wf[i,j] * pf[j]
    desvios = np.concatenate((desvios,(ingresos-compras)))
    '''

    if DEPURAR_CGE:
        mfun.tabla_2D(['precios   ',], pvec.reshape(1,len(pvec)))
        mfun.tabla_2D(['dem, facts',], np.concatenate((wp, wf.sum(axis=0, keepdims=True)),axis=1))
        mfun.tabla_2D(['produccion',], Z.reshape(1,len(Z)))
        imprime('')

    return desvios
    
def fun_objetivo(pvec, args):
    if OBJETIVO_CGE == 'A':
        return fun_objetivoA(pvec, args)
    elif OBJETIVO_CGE == 'B':
        return fun_objetivoB(pvec, args)
    else:
        imprime('Función objetivo incorrecta ' + OBJETIVO_CGE)
        imprime('')
        sys.exit()

# ciclo de convergencia
max_iteraciones = 1000
tolerancia = 1.e-08
    
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
    mfun.tabla_2D(['demanda ',], wp.sum(axis=0, keepdims=True))
    mfun.tabla_2D(['factores',], wf.sum(axis=0, keepdims=True))
    imprime('Iteración {:4}'.format(iteracion))
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

    pvec = results.x
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

    # para calcular la distancia 'dist'
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
    imprime('')
    imprime('---------------------------------------------------------------------')
    imprime('Resultado del CGE')
    imprime('---------------------------------------------------------------------')
    pp = pvec[0:nsec].reshape(nsec,1)
    pf = pvec[nsec:(nsec + nfac)].reshape(nfac,1)
    wp      = simple.demanda_maxima_utilidad_CobbDouglas(parametros.alfa, pp, pf, wf)
    wf      = simple.factores_maxima_utilidad_CobbDouglas(parametros.beta, pp, wp, pf)
    Z       = simple.producciones(parametros.beta, parametros.b, wf)    # producciones
    coste   = simple.coste_factores(pf, wf)
    ingreso = simple.ingreso_sectores(pp, wp)
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
    imprime('           ', False)
    for i in range(len(ind)):
        imprime('{:>8} '.format(ind[i]), False)
    imprime('')
    imprime('Demanda inicial')
    mfun.tabla_2D(dem, wpi)
    imprime('Demanda equilibrio')
    mfun.tabla_2D(dem, wp)
    mfun.tabla_2D(['Producción',], Z.reshape(1,len(Z)))
    imprime('')
    imprime('           ', False)
    for i in range(len(h)):
        imprime('{:>8} '.format(h[i]), False)
    imprime('')
    imprime('Factores iniciales')
    mfun.tabla_2D(ind, wfi)
    imprime('Factores equilibrio')
    mfun.tabla_2D(ind, wf)
    imprime('')
    imprime('{:8.3f} = coste total de los factores'.format(coste.sum()))
    imprime('           ', False)
    for i in range(len(h)):
        imprime('{:>8} '.format(h[i]), False)
    imprime('')
    mfun.tabla_2D(['Coste Fact',], np.expand_dims(coste, 0))
    imprime('')
    imprime('{:8.3f} = ingreso total de los sectores (coste para la demanda)'.format(ingreso.sum()))
    imprime('           ', False)
    for i in range(len(ind)):
        imprime('{:>8} '.format(ind[i]), False)
    imprime('')
    mfun.tabla_2D(['Ingr.Sect.',], np.expand_dims(ingreso,0))
    imprime('')
    ev = simple.variacion_hicksiana(wpi, wp, alfa)
    imprime('Variación del bienestar económico {:10.3e}'.format(ev))

    if abs(pvec[OR_PRE_REFERENCIA] - 1.) > 0.00001 :
        # normalizamos precios haciendo 1. al primero
        pvec = pvec / pvec[0]
        pp = pvec[0:nsec].reshape(nsec,1)
        pf = pvec[nsec:(nsec + nfac)].reshape(nfac,1)
        wp      = simple.demanda_maxima_utilidad_CobbDouglas(parametros.alfa, pp, pf, wf)
        wf      = simple.factores_maxima_utilidad_CobbDouglas(parametros.beta, pp, wp, pf)
        Z       = simple.producciones(parametros.beta, parametros.b, wf)    # producciones
        coste   = simple.coste_factores(pf, wf)
        ingreso = simple.ingreso_sectores(pp, wp)
    
        imprime('--------------------------------------------------')
        imprime('Precios escalados')
        imprime('--------------------------------------------------')
        mfun.tabla_1D(ind, pvec[0:nsec])
        mfun.tabla_1D(h, pvec[nsec:nsec + nfac])
        imprime('--------------------------------------------------')
        imprime('           ', False)
        for i in range(len(ind)):
            imprime('{:>8} '.format(ind[i]), False)
        imprime('')
        imprime('Demanda equilibrio')
        mfun.tabla_2D(dem, wp)
        mfun.tabla_2D(['Producción',], Z.reshape(1,len(Z)))
        imprime('')
        imprime('           ', False)
        for i in range(len(h)):
            imprime('{:>8} '.format(h[i]), False)
        imprime('')
        imprime('Factores equilibrio')
        mfun.tabla_2D(ind, wf)
        imprime('')
        imprime('{:8.3f} = coste total de los factores'.format(coste.sum()))
        imprime('           ', False)
        for i in range(len(h)):
            imprime('{:>8} '.format(h[i]), False)
        imprime('')
        mfun.tabla_2D(['Coste Fact',], np.expand_dims(coste, 0))
        imprime('')
        imprime('{:8.3f} = ingreso total de los sectores (coste para la demanda)'.format(ingreso.sum()))
        imprime('           ', False)
        for i in range(len(ind)):
            imprime('{:>8} '.format(ind[i]), False)
        imprime('')
        mfun.tabla_2D(['Ingr.Sect.',], np.expand_dims(ingreso,0))
        imprime('')
imprime('')
