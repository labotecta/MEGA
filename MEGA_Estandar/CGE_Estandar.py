import os
import sys
import copy
import numpy as np
from scipy.optimize import root, minimize
from scipy.optimize import minimize, NonlinearConstraint

import pandas as pd
from pandas import Series, DataFrame

import funciones as mfun
import calibrado
import ecuaciones_estandar as ecua
import produccion as prod
import gobierno as gob
import ahorro_inv as inv
import demanda as deho
import exterior as exte
if sys.version_info[0] != 3 or sys.version_info[1] > 9:
    raise Exception("La versión de phyton debe ser 3.9")

MINIMIZA_EXTEN = True
NCASO = 0
#              0      1     2          3                 4               5             6
etq_caso = ['base','alfa','beta','sin aranceles','doble aranceles','precios mitad','Factores']
CASO  = ('EXTENDIDO ' if MINIMIZA_EXTEN else '') +'Caso ' + etq_caso[NCASO]

SAL_CALIBRADO        = True
MUESTRA_PROGRESO     = False
MUESTRA_PRECIOS      = False
MUESTRA_DESVIOS      = False
ERROR_CUADRATICO     = True
OR_PRE_REFERENCIA    = 1    # 1 = LAB
RECAL_ax_ay          = False
#-------------------------------------------------------------------------------------------------------------
MIN_PRECIOS       = 1.e-6
MAX_PRECIOS       = None
TOLERANCIA_MIN    = 1.e-14
TOL_VERIFICAR     = 1.e-3
MAX_ITER          = 50000
METODO_MIN        = 'SLSQP'
SALVA_SOLUCION    = False

SENDA_DATOS       = 'C:/MEGA/Datos'
SENDA_SALIDAS     = 'C:/MEGA/SalEstandar/Salidas'
os.makedirs(SENDA_SALIDAS, exist_ok=True)

ESTRATEGIA = '_Min_' + ('Ext_' if MINIMIZA_EXTEN else 'Red_')
if MAX_PRECIOS == None:
    FICHERO = '{}/{}_{}_{}'.format(SENDA_SALIDAS, CASO, METODO_MIN + '_'+ '{:10.3e}'.format(MIN_PRECIOS) + ESTRATEGIA, 'A' if ERROR_CUADRATICO else 'C')
else:
    FICHERO = '{}/{}_{}_{}'.format(SENDA_SALIDAS, CASO, METODO_MIN + '_'+ '{:10.3e}'.format(MIN_PRECIOS) + '_'+ '{:10.3e}'.format(MAX_PRECIOS) + ESTRATEGIA , 'A' if ERROR_CUADRATICO else 'C')
FI_SALIDA   = FICHERO + '.csv'
FICHERO_LOG = FICHERO + '.log'
FICHERO_DES = FICHERO + '.txt'
mfun.ini(FICHERO_LOG)
FICHERO_SAM_ESTANDAR = '{}/{}.xlsx'.format(SENDA_DATOS, "SAM_estandar")

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

def valores_iniciales(sol):
    imprime('Valores iniciales')
    imprime('')
    if MINIMIZA_EXTEN:
        mfun.tabla_2D(['precios',]   , sol[0:9])
    else:
        mfun.tabla_2D(['precios',]   , sol)
    mfun.tabla_2D(['Z0',]        , datos.Z0)
    mfun.tabla_2D(['Xp0',]       , datos.Xp0)
    mfun.tabla_2D(['Xg0',]       , datos.Xg0)
    mfun.tabla_2D(['Xv0',]       , datos.Xv0)
    imprime       ('X0         --------- ---------')
    mfun.tabla_2D(ind            , datos.X0.T)    # la traspuesta para que las columnas sean las ventas a cada sector
    imprime       ('           --------- ---------')
    imprime       ('           ========= =========')
    mfun.tabla_2D(['suma',], datos.Xp0 + datos.Xg0 + datos.Xv0 + datos.X0.sum(axis=1))
    mfun.tabla_2D(['Q0',]        , datos.Q0)
    imprime       ('           ========= =========')
    mfun.tabla_2D(['Y0',]        , datos.Y0)
    imprime       ('F0         --------- ---------')
    mfun.tabla_2D(h              , datos.F0)
    imprime       ('           --------- ---------')
    mfun.tabla_2D(['FF   EXOGE',], datos.FF)
    mfun.tabla_2D(['E0',]        , datos.E0)
    mfun.tabla_2D(['M0',]        , datos.M0)
    mfun.tabla_2D(['D0',]        , datos.D0)
    imprime('Sp0        {:9.5f}'.format(datos.Sp0))
    imprime('Sg0        {:9.5f}'.format(datos.Sg0))
    imprime('Td0        {:9.5f}'.format(datos.Td0))
    mfun.tabla_2D(['Tz0',]       , datos.Tz0)
    mfun.tabla_2D(['Tm0',]       , datos.Tm0)
    imprime('bal. pagos {:9.5f}'.format(b_pini))
    imprime('Sf   EXOGE {:9.5f}'.format(datos.Sf0))
    imprime('')

def salida_calibrado(parametros):
    imprime('---------------------------------------------------------------------')
    imprime('Resultado del calibrado')
    imprime('---------------------------------------------------------------------')
    imprime('')
    imprime('tauz. Tasa de impuesto a la producción')
    imprime('')
    mfun.cabecera('', ind)
    mfun.cuerpo2D(['tauz'], datos.tauz)
    mfun.cierre(ind)
    imprime('')

    imprime('taum. Tasa de aranceles')
    imprime('')
    mfun.cabecera('', ind)
    mfun.cuerpo2D(['taum',], datos.taum)
    mfun.cierre(ind)
    imprime('')

    imprime('alfa. Parámetros de participación de los productos en la función de utilidad de la demanda')
    imprime('')
    mfun.cabecera('alfa', ind)
    mfun.cuerpo2D(['Demanda',],parametros.alfa)
    mfun.cierre(ind)
    imprime('')

    imprime('beta. Parámetros de participación de los factores en la función de producción del factor compuesto')
    imprime('')
    mfun.cabecera('Sector', h)
    mfun.cuerpo2D(ind, parametros.beta)
    mfun.cierre(h)
    imprime('')

    imprime('b. Coeficiente de escalado en la función de producción del factor compuesto')
    imprime('')
    mfun.cabecera('Sector', ['b',])
    mfun.cuerpo2D(ind, parametros.b.reshape(len(ind),1))
    mfun.cierre(['b',])
    imprime('')

    imprime('ax, ay. Coeficientes de los consumos intermedios y del factor compuesto')
    imprime('')
    la =  list(ind)
    la.append('Factor c.')
    mfun.cabecera('Sector', la)
    mfun.cuerpo2D(ind, np.c_[parametros.ax,parametros.ay])
    mfun.cierre(la)
    imprime('')

    imprime('mu. Participación de los productos en el consumo del gobierno')
    imprime('')
    mfun.cabecera('Sector', ['mu',])
    mfun.cuerpo2D(ind, parametros.mu.reshape(len(ind),1))
    mfun.cierre(['mu',])
    imprime('')

    imprime('landa. Coeficiente de participación de la demanda de inversión')
    imprime('')
    mfun.cabecera('Sector', ['landa',])
    mfun.cuerpo2D(ind, parametros.landa.reshape(len(ind),1))
    mfun.cierre(['landa',])

    imprime('deltam. Coeficiente de participación de la importación en la función del producto de Armington')
    imprime('')
    mfun.cabecera('Sector', ['deltam',])
    mfun.cuerpo2D(ind, parametros.deltam.reshape(len(ind),1))
    mfun.cierre(['deltam',])
    imprime('')

    imprime('deltad. Coeficiente de participación de la producción local en la función del producto de Armington')
    imprime('')
    mfun.cabecera('Sector', ['deltad',])
    mfun.cuerpo2D(ind, parametros.deltad.reshape(len(ind),1))
    mfun.cierre(['deltad',])
    imprime('')

    imprime('gamma. Coeficiente de escala de la función de Armington')
    imprime('')
    mfun.cabecera('Sector', ['gamma',])
    mfun.cuerpo2D(ind, parametros.gamma.reshape(len(ind),1))
    mfun.cierre(['gamma',])
    imprime('')

    imprime('xie. Coeficiente de participación en la CET de la exportación')
    imprime('')
    mfun.cabecera('Sector', ['xie',])
    mfun.cuerpo2D(ind, parametros.xie.reshape(len(ind),1))
    mfun.cierre(['xie',])
    imprime('')

    imprime('xid. Coeficiente de participación en la CET de la demanda local')
    imprime('')
    mfun.cabecera('Sector', ['xid',])
    mfun.cuerpo2D(ind, parametros.xid.reshape(len(ind),1))
    mfun.cierre(['xid',])
    imprime('')

    imprime('teta. Coeficiente de escala de la CET de exportación')
    imprime('')
    mfun.cabecera('Sector', ['teta',])
    mfun.cuerpo2D(ind, parametros.teta.reshape(len(ind),1))
    mfun.cierre(['teta',])
    imprime('')

    imprime('ssp.  Propensión al ahorro de los hogares {:9.5f}'.format(parametros.ssp))
    imprime('ssg.  Propensión al ahorro del gobierno   {:9.5f}'.format(parametros.ssg))
    imprime('taud. Tasa de impuestos directos          {:9.5f}'.format(parametros.taud))
    imprime('')

def extrae_var(vp, clave):
    vendo = vp[ind_pvec_desde[clave]:ind_pvec_hasta[clave]]
    n = int(len(vendo) / nsec)
    if n > 1: vendo = vendo.reshape(nsec, n)
    return vendo

def extrae_precio_sol(vp, clave):
    vendo = vp[ind_pre_desde[clave]:ind_pre_hasta[clave]]
    n = int(len(vendo) / nsec)
    if n > 1: vendo = vendo.reshape(nsec, n)
    return vendo

# declara las variables (como 'tuple' que es igual que 'list' pero no modificable, lo que las hace más eficientes)
u = (
    "BRD",  # sector 1
    "MLK",  # sector 2
    "CAP",  # factor capital
    "LAB",  # factor trabajo
    "IDT",  # impuestos indirectos (colecta -recibe- impuestos de los otros agentes (valores en su fila) que se transfieren al gobierno -la fila del el gobierno los recibe-)
    "TRF",  # araceles de importación (colecta -recibe- los aranceles que pagan los otros agentes (valores en su fila) por importar y los transfiere al gobierno -la fila del el gobierno los recibe-)
    "HOH",  # demanda de los hogares
    "GOV",  # gobierno (recibe (en su fila) los impuestos indirectos 'IDT', aranceles 'TRF'  e impuestos directos a los hogares 'HOH')
    "INV",  # inversión (colecta -recibe- los inversiones de los hogares (ahorros), del gobierno y del sector exterior, en este modelo se supone que el único que invierte es este agente, pero podría establecerse que los hogares y gobierno tambien invierten)
    "EXT",  # la fila representa las importaciones (recibe de los agentes los importes para comprar fuera) y la columna las exportaciones (lo que entrega a los agentes por vender fuera) así mismo recoge otros conceptos que son transacciones como son las remesas que los inmigrantes envían al exterior (LAB) los pagos pos servicios al capital exterior (CAP), el bloque 'EXT' resume la balanza de pagos.
)
ind = ('BRD', 'MLK')    # sectores (industria)
h   = ('CAP', 'LAB')    # factores de producción
dem = ('HOH',)          # demanda de los hogares, si no se pone la coma crea una lista de caracteres
ncon = len(dem)         # número de consumidores
nsec = len(ind)         # número de sectores
nfac = len(h)           # número de factores

imprime('#########################################')
imprime('Modelo CGE estándar.---------------------')
imprime('#########################################')
imprime('-----------------------------------------')
imprime(CASO)
imprime('-----------------------------------------')
imprime('')
imprime('Fichero SAM {}'.format(FICHERO_SAM_ESTANDAR))
imprime('')

# leemos la Matriz de contabilidad social (sam) de esta economía
sam = pd.read_excel(FICHERO_SAM_ESTANDAR, index_col=0, header=0)

'''
el fichero calibrado.py contiene dos clases que, como cualquier clase, ejecutan el procedimiento
'def __init__' cuando se crea una variable de la clase:
    datos     : la función 'def __init__' de esta clase crea una serie de variables y les asigna
                valores de acuerdo a la información leida de la SAM.
    parametros: la función 'def __init__' de esta clase crea unas variables que son los parámetros
                de las funciones de utilidad y les calcula unos valores de acuerdo a las
                ecuaciones que se deducen de las funciones de utilidad-producción,
                es decir, calibra el modelo.
'''
datos = calibrado.datos(sam, h, u, ind, dem)
parametros = calibrado.parametros(datos, ncon, nsec)

if SAL_CALIBRADO:
    salida_calibrado(parametros)

# guardar los valores calibrados para comparar cuando los modificamos
# usamos 'copy.deepcopy' para que la nueva variable copie los valores y no el puntero a la otra variable 
alfa_c = copy.deepcopy(parametros.alfa)
beta_c = copy.deepcopy(parametros.beta)
b_pini = exte.balance_pagos_moneda_extranjera(datos.pWe, datos.E0, datos.pWm, datos.M0, datos.Sf0)     # 6.16
taum_ini = copy.deepcopy(datos.taum)

# ---------------------------------------------------------------------
# Solucíonar el CGE
# ---------------------------------------------------------------------
def sec_ecuaciones(vec_precios, args):
    # pone el precio de referencia igual a 1.
    vec_precios[OR_PRE_REFERENCIA] = 1.

    # extraemos los argumentos a sus variables correspondientes
    (F, Z, E, M, D, Sp, Sg) = args

    # separamos los precios
    desde = 0
    pf = vec_precios[desde:(desde + nfac)]     # precio de los factores
    desde += nfac
    py = vec_precios[desde:(desde + nsec)]     # precio del factor compuesto
    desde += nsec
    pq = vec_precios[desde:(desde + nsec)]     # precio del producto de Armington
    desde += nsec
    pd = vec_precios[desde:(desde + nsec)]     # precio de los sectores para la demanda
    desde += nsec
    epsilon = vec_precios[desde:(desde + 1)]   # tipo de cambio
    # precios comercio internacional
    (pe, pm) = exte.precio_moneda_local(datos.pWe, datos.pWm, epsilon)                  # 6.14 y 6.15

    ax = parametros.ax
    ay = parametros.ay

    # Producción
    #-----------------------------------------------------
    # producción (Y) del factor compuesto dados F y la función Cobb Douglas correspondiente
    Fr = copy.deepcopy(F)
    Y = prod.produccion_factor_compuesto(F, parametros.beta, parametros.b)              # 6. 1
    Yp = copy.deepcopy(Y)
    # recalculamos los F optimos. En el equilibrio los F recalculados deben coincidir con los
    # utilizados en el cálculo Y que se ha hecho inmediatamente antes
    F = prod.optimo_factores(parametros.beta, pf, py, Y)                                # 6. 2
    # recalcular con los nuevos F
    #Yp = prod.produccion_factor_compuesto(F, parametros.beta, parametros.b)

    # dada la producción Z del sector 'i' (demanda de su producto) calculamos la utilización X de consumos intermedios 'j', que
    #  hace 'i' por aplicación de los coeficientes (ax) deducidos de la SAM
    X = prod.consumo_intermedio(Z, ax)                                                  # 6. 3
    Y = prod.consumo_composite_factor(Z, ay)                                            # 6. 4
    Yd = copy.deepcopy(Y)

    # producción bruta
    #Z = prod.produccion_sector(X, parametros.ax, Y, parametros.ay)                     # 6. 5
    pz = prod.coste_unitario_produccion(ay, py, ax, pq)       # 6. 5 alternativa

    # Gobierno
    #-----------------------------------------------------
    Td = gob.impuestos_directos(parametros.taud, pf, F)                                 # 6. 6
    Tz = gob.impuestos_produccion(datos.tauz, pz, Z)                                    # 6. 7
    Tm = gob.aranceles_importacion(datos.taum, pm, M)                                   # 6. 8
    Xg = gob.demanda_gobierno(parametros.mu, pq, Td, Tz, Tm, Sg)                        # 6. 9

    # Inversion
    #-----------------------------------------------------
    Xv = inv.demanda_inversion(parametros.landa, pq, Sp, Sg, epsilon, datos.Sf0)        # 6.10

    # Ahorro
    #-----------------------------------------------------
    Sp = inv.ahorro_hogares(F, pf, parametros.ssp)                                      # 6.11
    Sg = inv.ahorro_gobierno(parametros.ssg, Td, Tz, Tm)                                # 6.12

    # Consumo de los hogares
    #-----------------------------------------------------
    Xp = deho.demanda_maxima_utilidad_CobbDouglas(parametros.alfa, pq, pf, F, Sp, Td)   # 6.13

    # Comercio internacional
    #-----------------------------------------------------
    # restricción a la balanza de pagos, las importaciones deben ser igual a las exportaciones mas la balanza de pagos inicial (exógena)
    ebp = exte.balance_pagos_moneda_extranjera(datos.pWe, E, datos.pWm, M, datos.Sf0)     # 6.16

    # Armington
    #-----------------------------------------------------
    Q  = exte.produccion_armington(parametros.gamma, parametros.deltam, parametros.deltad, M, D, parametros.eta)                # 6.17
    # sustitución óptima entre importar (M) o producir localmente (D) la demanda del producto de Armington
    M  = exte.importacion_maxima_utilidad_armington(parametros.gamma, parametros.deltam, pq, pm, Q, parametros.eta, datos.taum) # 6.18
    D  = exte.produccion_maxima_utilidad_armington(parametros.gamma, parametros.deltad, pq, pd, Q, parametros.eta)              # 6.19
    Da = copy.deepcopy(D)

    # Función de transformación
    #-----------------------------------------------------
    # restriccion a cumplir por el reparto de la producción de un sector entre exportación y suministro local
    Z  = exte.restriccion_producción_bruta(parametros.teta, parametros.xie, parametros.xid, E, D, parametros.phi)               # 6.20
    # transformacion del suministro domestico (Z) en producto para exportación (E) y para suministro local (D)
    E  = exte.produccion_para_exportacion(parametros.teta, parametros.xie, pz, pe, Z, parametros.phi, datos.tauz)               # 6.21
    D = exte.produccion_para_local(parametros.teta, parametros.xid, pz, pd, Z, parametros.phi, datos.tauz)                      # 6.22
    Dt = copy.deepcopy(D)
    
    if RECAL_ax_ay:
        ax = ecua.coeficientes_consumos_intermedios(X, Z)
        ay = ecua.coeficientes_factor_compuesto(Yp, Z)
    # Leontief para comparar
    Zl = prod.produccion_sector(X, ax, Yp, ay)

    # Para calcular el demerito de la solución de prueba 'vec_opt' que recibe está función como argumento
    # recalculamos las variables para ver cuanto se diferencian del cálculo previo.
    # No recalculamos todas las variables porque vamos calcular diferencias adicionales entre las ecuaciones
    # 6.19 y 6.22 que calculan la misma variable D (Da y Dt), entre las ecuaiones 6.1 y 6.4 (Yp y Yd) y entre el valor
    # de entrada (Fr) y la ecuación 6.2 que calcula F, con lo que de hecho estamos recalculando todas las variables.
    Xr  = prod.consumo_intermedio(Z, ax)                                                                                            # 6. 3
    Tdr = gob.impuestos_directos(parametros.taud, pf, F)                                                                            # 6. 6
    Tzr = gob.impuestos_produccion(datos.tauz, pz, Z)                                                                               # 6. 7
    Tmr = gob.aranceles_importacion(datos.taum, pm, M)                                                                              # 6. 8
    Xgr = gob.demanda_gobierno(parametros.mu, pq, Td, Tz, Tm, Sg)                                                                   # 6. 9
    Xvr = inv.demanda_inversion(parametros.landa, pq, Sp, Sg, epsilon, datos.Sf0)                                                   # 6.10
    Qr  = exte.produccion_armington(parametros.gamma, parametros.deltam, parametros.deltad, M, D, parametros.eta)                   # 6.17
    Mr  = exte.importacion_maxima_utilidad_armington(parametros.gamma, parametros.deltam, pq, pm, Q, parametros.eta, datos.taum)    # 6.18
    Zr  = exte.restriccion_producción_bruta(parametros.teta, parametros.xie, parametros.xid, E, D, parametros.phi)                  # 6.20
    Er  = exte.produccion_para_exportacion(parametros.teta, parametros.xie, pz, pe, Z, parametros.phi, datos.tauz)                  # 6.21

    if MUESTRA_PROGRESO:
        mfun.tabla_2D('precios', vec_precios)
        mfun.tabla_2D(['p.Factores',], pf)
        mfun.tabla_2D(['p.Prod',]    , py)
        mfun.tabla_2D(['p.Armingt',] , pq)
        mfun.tabla_2D(['p.Pr.Local',], pd)
        imprime('cotizacion {:9.5f}'.format(epsilon.item()))
        mfun.tabla_2D(['p.Pr.Bruta',], pz)
        mfun.tabla_2D(['p.Exp.',]    , pe)
        mfun.tabla_2D(['p.Imp.',]    , pm)
        imprime       ('---------- --------- ---------')
        mfun.tabla_2D(['Yprodu 6.1',], Yp)
        mfun.tabla_2D(['Ydeman 6.4',], Yd)
        imprime       ('F          --------- ---------')
        mfun.tabla_2D(ind            , F)
        imprime       ('Fr         --------- ---------')
        mfun.tabla_2D(ind            , Fr)
        imprime       ('X         --------- ---------')
        mfun.tabla_2D(ind            , X.T)
        imprime       ('---------- --------- ---------')
        mfun.tabla_2D(['X suma',]    , X.sum(axis=1))
        mfun.tabla_2D(['Xp',]        , Xp)
        mfun.tabla_2D(['Xg',]        , Xg)
        mfun.tabla_2D(['Xv',]        , Xv)
        imprime       ('********** ********* *********')
        mfun.tabla_2D(['X+Xp+Xg+Xv',], Xp + Xg + Xv + X.sum(axis=1))
        mfun.tabla_2D(['Q',]         , Q)
        imprime       ('********** ********* *********')
        mfun.tabla_2D(['suma F',]    , F.sum(axis=0))
        mfun.tabla_2D(['F0',]        , datos.FF)
        imprime       ('********** ********* *********')
        mfun.tabla_2D(['M',]         , M)
        mfun.tabla_2D(['E',]         , E)
        imprime       ('---------- --------- ---------')
        mfun.tabla_2D(['D 6.19',]    , Da)
        mfun.tabla_2D(['D 6.22',]    , Dt)
        imprime       ('---------- --------- ---------')
        mfun.tabla_2D(['Zleontief',] , Zl)
        mfun.tabla_2D(['Z',]         , Z)
        imprime       ('---------- --------- ---------')
        imprime('')
        imprime('bal pagos  {:9.5f}'.format(ebp))
        imprime('Sp         {:9.5f}'.format(Sp))
        imprime('Sg         {:9.5f}'.format(Sg))
        imprime('Sf         {:9.5f}'.format(datos.Sf0))
        imprime('Td         {:9.5f}'.format(Td))
        mfun.tabla_2D(['Tz',]       , Tz)
        mfun.tabla_2D(['Tm ',]      , Tm)
        imprime('')
    elif MUESTRA_PRECIOS:
        lp = np.concatenate((vec_precios, pz, epsilon))
        mfun.tabla_2D(['precios',]   , lp)
    return (F,Z,E,M,Da,Sp,Sg,   Yp,X,Yd,pz,Td,Tz,Tm,Xg,Xv,Xp,ebp,Q,Z,Dt,Fr,Zr,Xr,Xgr,Xvr,Qr,Tdr,Tzr,Tmr,Mr,Er)

def sec_ecuaciones_ext(vec_opt):
    '''
    Función obetivo. Cálcula el demérito de la solución de prueba 'vec_opt'
    En realidad, calcula la pareja de valores para cada variable que restará la
    función 'calcula_desvios' llamada a su vez por la función 'fun_objetivo_min_ext'
    '''
    # pone el precio de referencia (el del factor LAB) igual a 1.
    vec_opt[OR_PRE_REFERENCIA] = 1.

    # extremos los precios del vector de prueba 'vec_opt'
    pf = extrae_var(vec_opt, 'pF')
    py = extrae_var(vec_opt, 'pY')
    pq = extrae_var(vec_opt, 'pQ')
    pd = extrae_var(vec_opt, 'pD')
    epsilon = extrae_var(vec_opt, 'epsilon')

    # extraemos los valores de las 'variables imprescindibles' del vector de prueba 'vec_opt'
    F  = extrae_var(vec_opt, 'F')
    Z  = extrae_var(vec_opt, 'Z')
    E  = extrae_var(vec_opt, 'E')
    M  = extrae_var(vec_opt, 'M')
    D  = extrae_var(vec_opt, 'D')
    Sp = extrae_var(vec_opt, 'Sp')
    Sg = extrae_var(vec_opt, 'Sg')

    # calculamos los precios del comercio internacional en moneda local
    (pe, pm) = exte.precio_moneda_local(datos.pWe, datos.pWm, epsilon)                  # 6.14 y 6.15

    ax = parametros.ax
    ay = parametros.ay

    #------------------------------------------------------------------------------------------------
    # Calculamos el valor de todas las variables endógenas aplicando todas las ecuaciones del modelo
    # siguiendo el orden del libro de referencia, el número 6.?? de la ecuación es porque están en el
    # capítulo 6 del libro
    #------------------------------------------------------------------------------------------------

    # Producción
    #-----------------------------------------------------
    # producción (Y) del factor compuesto dados F y la función Cobb Douglas correspondiente
    Fr = copy.deepcopy(F)
    Y = prod.produccion_factor_compuesto(F, parametros.beta, parametros.b)              # 6. 1
    Yp = copy.deepcopy(Y)
    # recalculamos los F óptimos. En el equilibrio los F recalculados deben coincidir con los
    # utilizados en el cálculo Y que se ha hecho inmediatamente antes
    F = prod.optimo_factores(parametros.beta, pf, py, Y)                                # 6. 2
    # recalcular con los nuevos F
    #Yp = prod.produccion_factor_compuesto(F, parametros.beta, parametros.b)

    # dada la producción Z del sector 'i' (demanda de su producto) calculamos la utilización X de consumos
    # intermedios 'j', que hace 'i' por aplicación de los coeficientes (ax) deducidos de la SAM
    X = prod.consumo_intermedio(Z, ax)                                                  # 6. 3
    Y = prod.consumo_composite_factor(Z, ay)                                            # 6. 4
    Yd = copy.deepcopy(Y)

    # producción bruta
    #Z = prod.produccion_sector(X, parametros.ax, Y, parametros.ay)                     # 6. 5
    pz = prod.coste_unitario_produccion(ay, py, ax, pq)       # 6. 5 alternativa

    # Gobierno
    #-----------------------------------------------------
    Td = gob.impuestos_directos(parametros.taud, pf, F)                                 # 6. 6
    Tz = gob.impuestos_produccion(datos.tauz, pz, Z)                                    # 6. 7
    Tm = gob.aranceles_importacion(datos.taum, pm, M)                                   # 6. 8
    Xg = gob.demanda_gobierno(parametros.mu, pq, Td, Tz, Tm, Sg)                        # 6. 9

    # Inversion
    #-----------------------------------------------------
    Xv = inv.demanda_inversion(parametros.landa, pq, Sp, Sg, epsilon, datos.Sf0)        # 6.10

    # Ahorro
    #-----------------------------------------------------
    Sp = inv.ahorro_hogares(F, pf, parametros.ssp)                                      # 6.11
    Sg = inv.ahorro_gobierno(parametros.ssg, Td, Tz, Tm)                                # 6.12

    # Consumo de los hogares
    #-----------------------------------------------------
    Xp = deho.demanda_maxima_utilidad_CobbDouglas(parametros.alfa, pq, pf, F, Sp, Td)   # 6.13

    # Comercio internacional
    #-----------------------------------------------------
    # restricción a la balanza de pagos, las importaciones deben ser igual a las exportaciones más la balanza de
    # pagos inicial (exógena)
    ebp = exte.balance_pagos_moneda_extranjera(datos.pWe, E, datos.pWm, M, datos.Sf0)   # 6.16

    # Armington
    #-----------------------------------------------------
    Q  = exte.produccion_armington(parametros.gamma, parametros.deltam, parametros.deltad, M, D, parametros.eta)                    # 6.17
    # sustitución óptima entre importar (M) o producir localmente (D) la demanda del producto de Armington
    M  = exte.importacion_maxima_utilidad_armington(parametros.gamma, parametros.deltam, pq, pm, Q, parametros.eta, datos.taum)     # 6.18
    D  = exte.produccion_maxima_utilidad_armington(parametros.gamma, parametros.deltad, pq, pd, Q, parametros.eta)                  # 6.19
    Da = copy.deepcopy(D)

    # Función de transformación
    #-----------------------------------------------------
    # restricción a cumplir por el reparto de la producción de un sector entre exportación y suministro local
    Z  = exte.restriccion_producción_bruta(parametros.teta, parametros.xie, parametros.xid, E, D, parametros.phi)                   # 6.20
    # transformacion del suministro domestico (Z) en producto para exportación (E) y para suministro local (D)
    E  = exte.produccion_para_exportacion(parametros.teta, parametros.xie, pz, pe, Z, parametros.phi, datos.tauz)                   # 6.21
    D = exte.produccion_para_local(parametros.teta, parametros.xid, pz, pd, Z, parametros.phi, datos.tauz)                          # 6.22
    Dt = copy.deepcopy(D)
    
    if RECAL_ax_ay:
        ax = ecua.coeficientes_consumos_intermedios(X, Z)
        ay = ecua.coeficientes_factor_compuesto(Yp, Z)
        # recalcular desde el consumo porque ha cambiado ay
    
    # Leontief para comparar
    Zl = prod.produccion_sector(X, ax, Yp, ay)
    
    # Para calcular el demerito de la solución de prueba 'vec_precios' que recibe está función como argumento
    # recalculamos las variables para ver cuánto se diferencian del cálculo previo.
    # No recalculamos todas las variables porque vamos a calcular diferencias adicionales entre las ecuaciones
    # 6.19 y 6.22 que calculan la misma variable D (Da y Dt), entre las ecuaciones 6.1 y 6.4 (Yp y Yd) y entre el valor
    # de entrada (Fr) y la ecuación 6.2 que calcula F, con lo que de hecho estamos recalculando todas las variables.
    Xr  = prod.consumo_intermedio(Z, ax)                                                                                            # 6. 3
    Tdr = gob.impuestos_directos(parametros.taud, pf, F)                                                                            # 6. 6
    Tzr = gob.impuestos_produccion(datos.tauz, pz, Z)                                                                               # 6. 7
    Tmr = gob.aranceles_importacion(datos.taum, pm, M)                                                                              # 6. 8
    Xgr = gob.demanda_gobierno(parametros.mu, pq, Td, Tz, Tm, Sg)                                                                   # 6. 9
    Xvr = inv.demanda_inversion(parametros.landa, pq, Sp, Sg, epsilon, datos.Sf0)                                                   # 6.10
    Qr  = exte.produccion_armington(parametros.gamma, parametros.deltam, parametros.deltad, M, D, parametros.eta)                   # 6.17
    Mr  = exte.importacion_maxima_utilidad_armington(parametros.gamma, parametros.deltam, pq, pm, Q, parametros.eta, datos.taum)    # 6.18
    Zr  = exte.restriccion_producción_bruta(parametros.teta, parametros.xie, parametros.xid, E, D, parametros.phi)                  # 6.20
    Er  = exte.produccion_para_exportacion(parametros.teta, parametros.xie, pz, pe, Z, parametros.phi, datos.tauz)                  # 6.21

    if MUESTRA_PROGRESO:
        mfun.tabla_2D('precios', vec_opt[0:9])
        mfun.tabla_2D(['p.Factores',], pf)
        mfun.tabla_2D(['p.Prod',]    , py)
        mfun.tabla_2D(['p.Armingt',] , pq)
        mfun.tabla_2D(['p.Pr.Local',], pd)
        imprime('cotizacion {:9.5f}'.format(epsilon.item()))
        mfun.tabla_2D(['p.Pr.Bruta',], pz)
        mfun.tabla_2D(['p.Exp.',]    , pe)
        mfun.tabla_2D(['p.Imp.',]    , pm)
        imprime       ('---------- --------- ---------')
        mfun.tabla_2D(['Yprodu 6.1',], Yp)
        mfun.tabla_2D(['Ydeman 6.4',], Yd)
        imprime       ('F          --------- ---------')
        mfun.tabla_2D(ind            , F)
        imprime       ('Fr         --------- ---------')
        mfun.tabla_2D(ind            , Fr)
        imprime       ('X         --------- ---------')
        mfun.tabla_2D(ind            , X.T)
        imprime       ('---------- --------- ---------')
        mfun.tabla_2D(['X suma',]    , X.sum(axis=1))
        mfun.tabla_2D(['Xp',]        , Xp)
        mfun.tabla_2D(['Xg',]        , Xg)
        mfun.tabla_2D(['Xv',]        , Xv)
        imprime       ('********** ********* *********')
        mfun.tabla_2D(['X+Xp+Xg+Xv',], Xp + Xg + Xv + X.sum(axis=1))
        mfun.tabla_2D(['Q',]         , Q)
        imprime       ('********** ********* *********')
        mfun.tabla_2D(['suma F',]    , F.sum(axis=0))
        mfun.tabla_2D(['F0',]        , datos.FF)
        imprime       ('********** ********* *********')
        mfun.tabla_2D(['M',]         , M)
        mfun.tabla_2D(['E',]         , E)
        imprime       ('---------- --------- ---------')
        mfun.tabla_2D(['D 6.19',]    , Da)
        mfun.tabla_2D(['D 6.22',]    , Dt)
        imprime       ('---------- --------- ---------')
        mfun.tabla_2D(['Zleontief',] , Zl)
        mfun.tabla_2D(['Z',]         , Z)
        imprime       ('---------- --------- ---------')
        imprime('')
        imprime('bal pagos  {:9.5f}'.format(ebp))
        imprime('Sp         {:9.5f}'.format(Sp))
        imprime('Sg         {:9.5f}'.format(Sg))
        imprime('Sf         {:9.5f}'.format(datos.Sf0))
        imprime('Td         {:9.5f}'.format(Td))
        mfun.tabla_2D(['Tz',]       , Tz)
        mfun.tabla_2D(['Tm ',]      , Tm)
        imprime('')
    else:
        if MUESTRA_PRECIOS:
            mfun.tabla_2D(['valores',]   , vec_opt)
    return (F,Z,E,M,Da,Sp,Sg,   Yp,X,Yd,pz,Td,Tz,Tm,Xg,Xv,Xp,ebp,Q,Z,Dt,Fr,Zr,Xr,Xgr,Xvr,Qr,Tdr,Tzr,Tmr,Mr,Er)

def calcula_desvios(res):
    (F,Z,E,M,Da,Sp,Sg,   Yp,X,Yd,pz,Td,Tz,Tm,Xg,Xv,Xp,ebp,Q,Z,Dt,Fr,Zr,Xr,Xgr,Xvr,Qr,Tdr,Tzr,Tmr,Mr,Er) = res
    # condiciones de equilibrio del mercado
    des_produccion = Q - (Xp + Xg + Xv + X.sum(axis=1))     # 6.23
    # la utilización total de cada factor debe ser la inicial ya que se considera una variable exógena
    des_factores   = F.sum(axis=0) - datos.FF               # 6.24
    des_Fr         = np.array([abs(F - Fr  ).sum()])    
    des_ebp        = np.array([ebp])
    des_Ydp        = np.array([abs(Yd - Yp ).sum()])    
    des_X          = np.array([abs(X  - Xr ).sum()])    
    des_Xg         = np.array([abs(Xg - Xgr).sum()])    
    des_Xv         = np.array([abs(Xv - Xvr).sum()])    
    des_D          = np.array([abs(Da - Dt ).sum()])    
    des_M          = np.array([abs(M  - Mr ).sum()])    
    des_E          = np.array([abs(E  - Er ).sum()])    
    des_Z          = np.array([abs(Z  - Zr ).sum()])    
    des_Q          = np.array([abs(Q  - Qr ).sum()])    
    des_Td         = np.array([abs(Td - Tdr).sum()])    
    des_Tz         = np.array([abs(Tz - Tzr).sum()])    
    des_Tm         = np.array([abs(Tm - Tmr).sum()])    
    desvios        = np.concatenate((des_produccion,des_factores,des_Fr,des_ebp,des_Ydp,des_X,des_Xg,des_Xv,des_D,des_Z,des_Q,des_Td,des_Tz,des_Tm,des_M,des_E))
    if ERROR_CUADRATICO:
        dist = (desvios ** 2).sum()
    else:
        dist = (abs(desvios)).sum()
    if MUESTRA_PROGRESO or MUESTRA_DESVIOS:
        mfun.tabla_2De(['desvios Q',], des_produccion)
        mfun.tabla_2De(['desvios F',], des_factores)
        mfun.tabla_2De(['des Fr',]   , des_Fr)
        mfun.tabla_2De(['des b.pag',], des_ebp)
        mfun.tabla_2De(['des Yd-Yp',], des_Ydp)
        mfun.tabla_2De(['des X',]    , des_X)
        mfun.tabla_2De(['des Xg',]   , des_Xg)
        mfun.tabla_2De(['des Xv',]   , des_Xv)
        mfun.tabla_2De(['des Da-Dt',], des_D)
        mfun.tabla_2De(['des M',]    , des_M)
        mfun.tabla_2De(['des E',]    , des_E)
        mfun.tabla_2De(['des Z',]    , des_Z)
        mfun.tabla_2De(['des Q',]    , des_Q)
        mfun.tabla_2De(['des Td',]   , des_Td)
        mfun.tabla_2De(['des Tz',]   , des_Tz)
        mfun.tabla_2De(['des Tm',]   , des_Tm)
        mfun.tabla_2De(['Errdesvios',], dist)
        imprime('')
    return dist

def fun_objetivo_min(vec_precios, args):
    res = sec_ecuaciones(vec_precios, io_args)
    return calcula_desvios(res)

def fun_objetivo_min_ext(vec_opt):
    res = sec_ecuaciones_ext(vec_opt)
    return calcula_desvios(res)

def veri_solucion(vec_veri_sol, titulo):
    (pf,py,pz,pq,pd,epsilon,Y,F,X,Z,Xp,Xg,Xv,E,M,Q,D,ebp,Sp,Sg,Td,Tz,Tm) = vec_veri_sol

    (pe, pm) = exte.precio_moneda_local(datos.pWe, datos.pWm, epsilon)                                                                          # 6.14 y 6.15

    if RECAL_ax_ay:
        ax = ecua.coeficientes_consumos_intermedios(X, Z)
        ay = ecua.coeficientes_factor_compuesto(Y, Z)
    else:
        ax = parametros.ax
        ay = parametros.ay
    veri_a = np.zeros(len(etq_veri), dtype=np.ndarray)
    veri_a[0]  = Y   - prod.produccion_factor_compuesto(F, parametros.beta, parametros.b)                                                       # 6. 1
    veri_a[1]  = F   - prod.optimo_factores(parametros.beta, pf, py, Y)                                                                         # 6. 2
    veri_a[2]  = X   - prod.consumo_intermedio(Z, ax)                                                                                           # 6. 3
    veri_a[3]  = Y   - prod.consumo_composite_factor(Z, ay)                                                                                     # 6. 4
    veri_a[4]  = pz  - prod.coste_unitario_produccion(ay, py, ax, pq)                                                                           # 6. 5 alternativa
    veri_a[5]  = Td  - gob.impuestos_directos(parametros.taud, pf, F)                                                                           # 6. 6
    veri_a[6]  = Tz  - gob.impuestos_produccion(datos.tauz, pz, Z)                                                                              # 6. 7
    veri_a[7]  = Tm  - gob.aranceles_importacion(datos.taum, pm, M)                                                                             # 6. 8
    veri_a[8]  = Xg  - gob.demanda_gobierno(parametros.mu, pq, Td, Tz, Tm, Sg)                                                                  # 6. 9
    veri_a[9]  = Xv  - inv.demanda_inversion(parametros.landa, pq, Sp, Sg, epsilon, datos.Sf0)                                                  # 6.10
    veri_a[10] = Sp  - inv.ahorro_hogares(F, pf, parametros.ssp)                                                                                # 6.11
    veri_a[11] = Sg  - inv.ahorro_gobierno(parametros.ssg, Td, Tz, Tm)                                                                          # 6.12
    veri_a[12] = Xp  - deho.demanda_maxima_utilidad_CobbDouglas(parametros.alfa, pq, pf, F, Sp, Td)                                             # 6.13
    veri_a[13] = ebp                                                                                                                            # 6.16
    veri_a[14] = Q   - exte.produccion_armington(parametros.gamma, parametros.deltam, parametros.deltad, M, D, parametros.eta)                  # 6.17
    veri_a[15] = M   - exte.importacion_maxima_utilidad_armington(parametros.gamma, parametros.deltam, pq, pm, Q, parametros.eta, datos.taum)   # 6.18
    veri_a[16] = D   - exte.produccion_maxima_utilidad_armington(parametros.gamma, parametros.deltad, pq, pd, Q, parametros.eta)                # 6.19
    veri_a[17] = Z   - exte.restriccion_producción_bruta(parametros.teta, parametros.xie, parametros.xid, E, D, parametros.phi)                 # 6.20
    veri_a[18] = E   - exte.produccion_para_exportacion(parametros.teta, parametros.xie, pz, pe, Z, parametros.phi, datos.tauz)                 # 6.21
    veri_a[19] = D   - exte.produccion_para_local(parametros.teta, parametros.xid, pz, pd, Z, parametros.phi, datos.tauz)                       # 6.22
    veri_a[20]  = Q - (Xp + Xg + Xv + X.sum(axis=1))                                                                                            # 6.23
    veri_a[21]  = F.sum(axis=0) - datos.FF                                                                                                      # 6.24
    veri_c = np.zeros(len(etq_veri), dtype=np.float64)
    imprime('Verifica solución')
    imprime('    {}'.format(titulo))
    imprime('-----------  ------------')
    desvio = 0.
    nfallos = 0
    for i in range (len(etq_veri)):
        dc = (veri_a[i] ** 2).sum()
        veri_c[i] = dc
        veri_a[i] = abs(veri_a[i]).sum()
        desvio += dc
        if veri_a[i] > TOL_VERIFICAR:
            imprime('{:11} {:13.5e}'.format(etq_veri[i], veri_a[i]))
            nfallos += 1
    if nfallos == 0:
        imprime('se cumplen todas las ecuaciones')
    imprime('-----------  ------------')
    imprime('Ecm.desvios {:13.5e}'.format(desvio))
    imprime('-----------  ------------')
    
imprime('---------------------------------------------------------------------')
imprime('Escenario')
imprime('---------------------------------------------------------------------')
imprime('')
if NCASO == 1:
    parametros.alfa[0] = 0.5
    parametros.alfa[1] = 0.5
if NCASO == 2:
    parametros.beta[0,0] = 0.5
    parametros.beta[0,1] = 0.5
if NCASO == 3:
    for i in range(nsec):
        datos.taum[i] = 0.
if NCASO == 4:
    for i in range(nsec):
        datos.taum[i] *= 2.
if NCASO == 5:
    for i in range(nfac):
        datos.pF0[i] = 0.5
    for i in range(nsec):
        datos.pY0[i] = 0.5
        datos.pZ0[i] = 0.5
        datos.pQ0[i] = 0.5
        datos.pD0[i] = 0.5
if NCASO == 6:
    datos.F0[0,0] = 25
    datos.F0[0,1] = 15
    datos.F0[1,0] = 30
    datos.F0[1,1] = 25
imprime('Elasticidad de la demanda (alfa) calibrado / escenario')
mfun.tabla_2D(dem, alfa_c)
mfun.tabla_2D(dem, parametros.alfa)
imprime('')
imprime('Elasticidad de la producción (beta) calibrado / escenario')
mfun.tabla_2D(ind, beta_c)
imprime('')
mfun.tabla_2D(ind, parametros.beta)
imprime('')
imprime('Aranceles de importación (taum) calibrado / escenario')
mfun.tabla_2D(['Productos',], taum_ini)
imprime('')
mfun.tabla_2D(['Productos',], datos.taum)
imprime('')

pzi = copy.deepcopy(datos.pZ0)
etq_veri = [
            ' 1.Yp  6. 1',
            ' 2.F   6. 2',
            ' 3.X   6. 3',
            ' 4.Yd  6. 4',
            ' 5.pz  6. 5',
            ' 6.Td  6. 6',
            ' 7.Tz  6. 7',
            ' 8.Tm  6. 8',
            ' 9.Xg  6. 9',
            '10.Xv  6.10',
            '11.Sp  6.11',
            '12.Sg  6.12',
            '13.Xp  6.13',
            '14.ebp 6.16',
            '15.Q   6.17',
            '16.M   6.18',
            '17.Dar 6.19',
            '18.Z   6.20',
            '19.E   6.21',
            '20.Dtr 6.22',
            '21.Qeq 6.23',
            '22.Feq 6.24',
    ]
etq_veri_sol = [
            'pF',
            'pY',
            'pZ',
            'pQ',
            'pD',
            'epsilon',
            'Y',
            'F',
            'X',
            'Z',
            'Xp',
            'Xg',
            'Xv',
            'E',
            'M',
            'Q',
            'D',
            'ebp',
            'Sp',
            'Sg',
            'Td',
            'Tz',
            'Tm',
        ]
if MINIMIZA_EXTEN:

    # minimiza extendida

    etq_vec_opt   = ['pF','pY','pQ','pD','epsilon','F','Z','E','M','D','Sp','Sg',]
    etq_vec_opt_d = [
            'pF CAP','pF LAB',
            'pY BRD', 'pY MLK',
            'pQ BRD', 'pQ MLK',
            'pD BRD', 'pD MLK',
            'epsilon',
            'F CAP BRD', 'F LAB BRD',
            'F CAP MLK', 'F LAB MLK',
            'Z BRD', 'Z MLK',
            'E BRD', 'E MLK',
            'M BRD', 'M MLK',
            'D BRD', 'D MLK',
            'Sp', 
            'Sg',
            ]
    vec_opt = np.concatenate((
                            datos.pF0.flatten(),    # precio de los factores
                            datos.pY0.flatten(),    # precio del factor compuesto
                            datos.pQ0.flatten(),    # precio del producto de Armington
                            datos.pD0.flatten(),    # precio de los sectores para la demanda
                            datos.epsilon,          # tipo de cambio
                            datos.F0.flatten(),
                            datos.Z0.flatten(),
                            datos.E0.flatten(),
                            datos.M0.flatten(),
                            datos.D0.flatten(),
                            [datos.Sp0],
                            [datos.Sg0],
                           ))
    vec_opt_ini = copy.deepcopy(vec_opt)
    pvec_desde = np.empty((len(etq_vec_opt)), dtype=np.int32)
    pvec_hasta = np.empty((len(etq_vec_opt)), dtype=np.int32)
    i = 0   # pF
    pvec_desde[i] = 0
    pvec_hasta[i] = pvec_desde[i] + datos.pF0.size
    i += 1  # pY
    pvec_desde[i] = pvec_hasta[i - 1] 
    pvec_hasta[i] = pvec_desde[i] + datos.pY0.size
    i += 1  # pQ
    pvec_desde[i] = pvec_hasta[i - 1] 
    pvec_hasta[i] = pvec_desde[i] + datos.pQ0.size
    i += 1  # pD
    pvec_desde[i] = pvec_hasta[i - 1] 
    pvec_hasta[i] = pvec_desde[i] + datos.pD0.size
    i += 1  # epsilon
    pvec_desde[i] = pvec_hasta[i - 1] 
    pvec_hasta[i] = pvec_desde[i] + 1

    i += 1  # F
    pvec_desde[i] = pvec_hasta[i - 1] 
    pvec_hasta[i] = pvec_desde[i] + datos.F0.size
    i += 1  # Z
    pvec_desde[i] = pvec_hasta[i - 1] 
    pvec_hasta[i] = pvec_desde[i] + datos.Z0.size
    i += 1  # E
    pvec_desde[i] = pvec_hasta[i - 1] 
    pvec_hasta[i] = pvec_desde[i] + datos.E0.size
    i += 1  # M
    pvec_desde[i] = pvec_hasta[i - 1] 
    pvec_hasta[i] = pvec_desde[i] + datos.M0.size
    i += 1  # D
    pvec_desde[i] = pvec_hasta[i - 1] 
    pvec_hasta[i] = pvec_desde[i] + datos.D0.size
    i += 1  # Sp
    pvec_desde[i] = pvec_hasta[i - 1] 
    pvec_hasta[i] = pvec_desde[i] + 1
    i += 1  # Sg
    pvec_desde[i] = pvec_hasta[i - 1] 
    pvec_hasta[i] = pvec_desde[i] + 1
    ind_pvec_desde = Series(pvec_desde, index=etq_vec_opt)
    ind_pvec_hasta = Series(pvec_hasta, index=etq_vec_opt)

    valores_iniciales(vec_opt[0:9])
    DTMP = MUESTRA_PROGRESO
    MUESTRA_PROGRESO = True
    imprime('Una primera valoración del modelo')
    imprime('---------------------------------')
    fun_objetivo_min_ext(vec_opt)
    imprime('---------------------------------')
    imprime('')
    MUESTRA_PROGRESO = DTMP
else:

    # minimiza restringida a precios

    vec_precios     = np.concatenate((datos.pF0,  # precio de los factores
                       datos.pY0,       # precio del factor compuesto
                       datos.pQ0,       # precio del producto de Armington
                       datos.pD0,       # precio de los sectores para la demanda
                       datos.epsilon,   # tipo de cambio
                       ))
    etq_vec_precios  = ['CAP', 'LAB',
            'F.cpto_BRD', 'F.cpto_MLK',
            'Arming_BRD', 'Arming_MLK',
            'Demand_BRD', 'Demand_MLK',
            'Cotización',]
    
    # guardar para comparar con el resultado final
    vec_precios_ini = copy.deepcopy(vec_precios)
    F  = datos.F0
    Z  = datos.Z0
    E  = datos.E0
    M  = datos.M0
    De  = datos.D0
    Sp = datos.Sp0
    Sg = datos.Sg0
    valores_iniciales(vec_precios)
    DTMP = MUESTRA_PROGRESO
    MUESTRA_PROGRESO = True
    imprime('Una primera valoración del modelo')
    imprime('---------------------------------')
    io_args  = [F, Z, E, M, De, Sp, Sg] 
    fun_objetivo_min(vec_precios, io_args)
    imprime('---------------------------------')
    imprime('')
    MUESTRA_PROGRESO = DTMP

# vector para verificar la solución
ebp = exte.balance_pagos_moneda_extranjera(datos.pWe, datos.E0, datos.pWm, datos.M0, datos.Sf0)
vec_veri_sol = (
                datos.pF0,
                datos.pY0,
                datos.pZ0,
                datos.pQ0,
                datos.pD0,
                datos.epsilon,
                datos.Y0,
                datos.F0,
                datos.X0,
                datos.Z0,
                datos.Xp0,
                datos.Xg0,
                datos.Xv0,
                datos.E0,
                datos.M0,
                datos.Q0,
                datos.D0,
                ebp,
                datos.Sp0,
                datos.Sg0,
                datos.Td0,
                datos.Tz0,
                datos.Tm0
                )
vec_veri_sol_ini = copy.deepcopy(vec_veri_sol)

# vector de precios a optimizar, común a minimizar solo con precios y minimizar extendido 
vetq_sol = [
        'pF',
        'pY',
        'pQ',
        'pD',
        'epsilon',
]
vsol_desde = np.empty((len(vetq_sol)), dtype=np.int32)
vsol_hasta = np.empty((len(vetq_sol)), dtype=np.int32)
i = 0   # pF
vsol_desde[i] = 0
vsol_hasta[i] = vsol_desde[i] + datos.pF0.size
i += 1  # pY
vsol_desde[i] = vsol_hasta[i - 1] 
vsol_hasta[i] = vsol_desde[i] + datos.pY0.size
i += 1  # pQ
vsol_desde[i] = vsol_hasta[i - 1] 
vsol_hasta[i] = vsol_desde[i] + datos.pQ0.size
i += 1  # pD
vsol_desde[i] = vsol_hasta[i - 1] 
vsol_hasta[i] = vsol_desde[i] + datos.pD0.size
i += 1  # epsilon
vsol_desde[i] = vsol_hasta[i - 1] 
vsol_hasta[i] = vsol_desde[i] + 1
ind_pre_desde = Series(vsol_desde, index=vetq_sol)
ind_pre_hasta = Series(vsol_hasta, index=vetq_sol)
# verifica solución
veri_solucion(vec_veri_sol, 'inicial')
imprime('')

# intervalos de variación de los valores a optimizar (cota mínima, cota máxima)
if MINIMIZA_EXTEN:
    bnds = (((MIN_PRECIOS, MAX_PRECIOS), ) * len(vec_opt))
else:
    bnds = (((MIN_PRECIOS, MAX_PRECIOS), ) * len(vec_precios))
if MUESTRA_PROGRESO:
    imprime('Evolución de la minimización')
    imprime('')
if MINIMIZA_EXTEN:
    vec_opt = copy.deepcopy(vec_opt_ini)
    results = minimize(fun_objetivo_min_ext, vec_opt, method=METODO_MIN, bounds=bnds, tol=TOLERANCIA_MIN, options={'maxiter':MAX_ITER, 'ftol':TOLERANCIA_MIN})
else:
    vec_precios = copy.deepcopy(vec_precios_ini)
    io_args = [F, Z, E, M, De, Sp, Sg] 
    results = minimize(fun_objetivo_min, vec_precios, args=io_args, method=METODO_MIN, bounds=bnds, tol=TOLERANCIA_MIN, options={'maxiter':MAX_ITER, 'ftol':TOLERANCIA_MIN})
    
if results['success'] == False:
    clave = 'message'
    imprime('{}'.format(results[clave]))
    clave = 'status'
    imprime('{} {}'.format(clave, results[clave]))
    imprime('')
    sys.exit()

sol = results.x
MUESTRA_PROGRESO = True  # asegurar la salida de la solución
imprime('Valoración final')
imprime('')
if MINIMIZA_EXTEN:
    res = sec_ecuaciones_ext(sol)
else:
    res = sec_ecuaciones(sol, io_args)
dist = calcula_desvios(res)
imprime('---------------------------------------------------------')
imprime('La distancia es {:9.3e}'.format(dist))
imprime('---------------------------------------------------------')
imprime('')

# verificar la solución
(F,Z,E,M,Da,Sp,Sg,   Yp,X,Yd,pz,Td,Tz,Tm,Xg,Xv,Xp,ebp,Q,Z,Dt,Fr,Zr,Xr,Xgr,Xvr,Qr,Tdr,Tzr,Tmr,Mr,Er) = res
vec_veri_sol = (
                extrae_precio_sol(sol,'pF'),
                extrae_precio_sol(sol,'pY'),
                pz,
                extrae_precio_sol(sol,'pQ'),
                extrae_precio_sol(sol,'pD'),
                extrae_precio_sol(sol,'epsilon'),
                Yp,
                F,
                X,
                Z,
                Xp,
                Xg,
                Xv,
                E,
                M,
                Q,
                Da,
                ebp,
                Sp,
                Sg,
                Td,
                Tz,
                Tm,
                )
veri_solucion(vec_veri_sol,'  final')

if (dist > TOLERANCIA_MIN):
    imprime('')
    imprime('**************************************************************************')
    imprime('No se alcanó el mínimo deseado {:9.3e} [{:9.3e}]'.format(TOLERANCIA_MIN, dist))
    imprime('**************************************************************************')
imprime('')
imprime('------------------------------------------------------------------------------------------------')
if MIN_PRECIOS == None:
    if MAX_PRECIOS == None:
        imprime('Resultado del CGE mediante minimización {} min.precio    None max.precio  None'.format(METODO_MIN))
    else:
        imprime('Resultado del CGE mediante minimización {} min.precio    None max.precio {:10.3e}'.format(METODO_MIN, MAX_PRECIOS))
else:
    if MAX_PRECIOS == None:
        imprime('Resultado del CGE mediante minimización {} min.precio {:10.3e} max.precio    None'.format(METODO_MIN, MIN_PRECIOS))
    else:
        imprime('Resultado del CGE mediante minimización {} min.precio {:10.3e} max.precio {:10.3e}'.format(METODO_MIN, MIN_PRECIOS, MAX_PRECIOS))
imprime('------------------------------------------------------------------------------------------------')
imprime('')
imprime('{:25} {:10.3e}'.format('Tolerancia', TOLERANCIA_MIN))
imprime('{:25} {:10,}'.format('Max iteraciones',MAX_ITER))
imprime('')
clave = 'message'
imprime('{}'.format(results[clave]))
clave = 'nfev'
imprime('{:25} {:10,} '.format('Número de iteraciones', results[clave]))
clave = 'fun'
imprime('{:25} {:10.3e}'.format('Función objetivo', results[clave]))
imprime('')
imprime('Precios    iniciales equilibrio')
imprime('-------------------- ----------')
if MINIMIZA_EXTEN:
    mfun.tabla_1Dl(etq_vec_opt_d[0:8], vec_opt_ini[0:8], sol[0:8])
    mfun.tabla_1Dl(['pZ BRD',], pzi[0:1], pz[0:1])
    mfun.tabla_1Dl(['pZ MLK',], pzi[1:], pz[1:])
    mfun.tabla_1Dl(etq_vec_opt_d[8:9], vec_opt_ini[8:9], sol[8:9])
else:
    mfun.tabla_1Dl(etq_vec_precios, vec_precios_ini, sol)
    mfun.tabla_1Dl(['p.Prod BRD','p.Prod MLK'], pzi, pz)
    imprime('')
imprime('-------------------------------')
imprime('')
if SALVA_SOLUCION:
    def salva_var(sw, etiqueta, v):
        s = v.shape
        v = v.flatten()
        sw.write('- {};{};'.format(etiqueta,len(s)))
        for j in range(len(s)):
            sw.write('{};'.format(s[j]))
        sw.write('\n')
        for k in range(len(v)):
            sw.write('{};'.format(v[k]))
        sw.write('\n')
        
    sw = open(FI_SALIDA, "w", encoding="utf-8")
    if MINIMIZA_EXTEN:
        for i in range(len(etq_vec_opt[0:5])):
            v = extrae_var(sol, etq_vec_opt[i])
            s = v.shape
            v = v.flatten()
            sw.write('- {};{};'.format(etq_vec_opt[i],len(s)))
            for j in range(len(s)):
                sw.write('{};'.format(s[j]))
            sw.write('\n')
            for k in range(len(v)):
                sw.write('{};'.format(v[k]))
            sw.write('\n')
    else:
        for i in range(len(etq_vec_precios)):
            v = sol[i]
            s = v.shape
            v = v.flatten()
            sw.write('- {};{};'.format(etq_vec_precios[i],len(s)))
            for j in range(len(s)):
                sw.write('{};'.format(s[j]))
            sw.write('\n')
            for k in range(len(v)):
                sw.write('{};'.format(v[k]))
            sw.write('\n')
    epsilon = extrae_precio_sol(sol,'epsilon')
    pe = datos.pWe * epsilon
    pm = datos.pWm * epsilon
    salva_var(sw, 'pz', pz)
    salva_var(sw, 'pe', pe)
    salva_var(sw, 'pm', pm)
    salva_var(sw, 'F' , F)
    salva_var(sw, 'Yd', Yd)
    salva_var(sw, 'Yp', Yp)
    salva_var(sw, 'X' , X)
    salva_var(sw, 'Xp', Xp)
    salva_var(sw, 'Xg', Xg)
    salva_var(sw, 'Xv', Xv)
    salva_var(sw, 'Q' , Q)
    salva_var(sw, 'Z' , Z)
    salva_var(sw, 'E' , E)
    salva_var(sw, 'M' , M)
    salva_var(sw, 'De', De)
    salva_var(sw, 'Di', Di)
    salva_var(sw, 'Sp', Sp)
    salva_var(sw, 'Sg', Sg)
    salva_var(sw, 'Td', Td)
    salva_var(sw, 'Tz', Tz)
    salva_var(sw, 'Tm', Tm)
    salva_var(sw, 'res_bal_pagos', ebp)
    salva_var(sw, 'Xr', Xr)
    salva_var(sw, 'Zr', Zr)
    sw.close()


