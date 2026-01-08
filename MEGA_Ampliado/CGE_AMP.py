import os
import sys
import copy
import numpy as np
import pandas as pd
import scipy
import matplotlib
from pandas import Series
from scipy.optimize import differential_evolution 
from matplotlib import pyplot as plt
from timeit import default_timer as timer

import calibrado
import funciones  as mfun
import ecuaciones as ecua
import produccion as prod
import gobierno   as gob
import ahorro_inv as ainv
import demanda    as deho
import exterior   as exte

VERSION = '1.0.5'
# 4 Matrices de Contabilidad Social para las pruebas, se selecciona con NSAM
#               0            1             2              3
etq_sam  = ['1_hogar_','2_hogares_','3_hogares_AMP_','MCA-ESP-05_']

# escenarios para las pruebas, se selecciona con NCASO
etq_caso = [
    'base',                    #  0
    'alfa',                    #  1
    'beta',                    #  2
    'sin_arancel',             #  3
    'doble_arancel',           #  4
    'pre_ini',                 #  5
    'factores',                #  6
    'ahorro',                  #  7
    'seg_social',              #  8
    'dem_alfa',                #  9
    'dem_alfa_factores',       # 10
    'dem_factores',            # 11
    'alfa_ayudas',             # 12
]
PRECIO_INI  = 0.5    # para el caso 5 'pre_ini'
FACTOR_CSSH = [0.95, 1.0]   # para afectar los coeficientes de la seguridad social de los hohares. caso 8
FACTOR_CSSE = [1.0 , 1.0, 1.0, 1.0, 1.0, 1.0]   # para afectar los coeficientes de la seguridad social de las empresas, caso 8

# demanda adicional exógena de productos (columna) por consumidor (fila), en importe
# su forma varia con la SAM correspondiente, en funciín del número de hogares y productos.
DEM_ADICIONAL = np.array([
    [0., 0.,   0., 0., 0., 0.],
    [0., 0.,   0., 0., 0., 0.],
])
# factores aportados adicionales para el caso 6, si se especifica un solo valor (escalar) se afectan todos por él.
# su forma varia con la SAM correspondiente, en funciín del número de hogares y factores.
VAR_FACTORES = np.array([
    [0., 0.],
    [0., 0.],
])
VAR_FACTORES = 1.1
# para el caso 11, participación del valor añadido sobre la producción para cada sector para calcular 
# la variación adicional exógena de factores, derivada del incremento de la demanda 'DEM_ADICIONAL'
# su forma varia con la SAM correspondiente, en funciín del número de sectores.
COE_VAB = np.array([0.590982516,0.256023902,0.231881481,0.299890544,0.567089808,0.669947953])

# ayuda adicional exógena por consumidor (fila) y producto (columna), en importe
# su forma varia con la SAM correspondiente, en funciín del número de hogares y sectores.
AYD_ADICIONAL = np.array([
    [0.,0.,   0.,0.,0.,0.],
    [0.,0.,1000.,0.,0.,0.],
])
AYD_ADI_DEM = AYD_ADICIONAL.sum(axis=1)

NSAM  = 3
NCASO = 12
PREFIJO = 'z2'

OR_PRE_REFERENCIA   = 1         # ordinal (columna de h, empezando en 0) del precio para el que se fija el valor 'PRECIO_F_REFERENCIA'
PRECIO_F_REFERENCIA = 1.0       # precio que se fija para el factor de referencia (el último)
VALOR_F_TRA         = -1        # -1 : no se fija el valor del precio del trabajo
FF_ENDOGENA         = True      # Las aportaciones de factores por los hogares pueden ser variables endogenas o exogenas
AHORRO_L_PLAZO      = True      # llevar a la cuenta ALP (Ahorro Largo Plazo) los excesos de factores aportados sobre sus valores iniciales
OPT_DESVIOS         = 0         # 0 : incluye desvíos redundantes

PRIMERA_VALORACION  = False     # calcular una primera valoración de modelo
SAL_CALIBRADO       = True      # imprimir los valores de los parámetros calibrados
SAL_AUXILIARES      = False     # imprimir los valores del historial 
SAL_GRAFICOS        = False     # generar gráficos
SAL_VARIACIONES     = True      # imprime las diferencias entre los valores iniciales y finales de las variables 
#--------------------------------------------------------------------------------------------------------------------------------------------
# algunos de estos parámetros se cambian según la MCS seleccionada
#
GE_PRE_MIN        = 3.0         # El límite inferior del rango de variaciópn de los precios es su valor inicial dividido por GE_PRE_MIN 
GE_PRE_MAX        = 3.0         # El límite superior del rango de variaciópn de los precios es su valor inicial multiplicado por GE_PRE_MAX 
GE_VAR_MIN        = 9.0         # El límite inferior del rango de variaciópn de las variables es su valor inicial dividido por GE_VAR_MIN 
GE_VAR_MAX        = 9.0         # El límite superior del rango de variaciópn de las variables es su valor inicial multiplicado por GE_VAR_MAX 
GE_VAR_CERO       = 1000.       # Si el valor inicial de una variable es cero su rango de variación es [-GE_VAR_CERO, +GE_VAR_CERO]
GE_TOLERANCIA     = 1.e-4       # límite para considerar el objetivo alcanzado.
# Si el valor de una variable al aplicar la correspondiente ecuación del modelo varía, respecto del valor antes de aplicar la
# ecuación, en menos de GE_VERIFICAR se considera que la ecuación se cumple (factibilidad de la ecuación)
GE_VERIFICAR      = 1.e-2
GE_MAX_ITER       = 1000000     # máximo número de generaciones a simular
GE_ACTUALIZACION  = 'immediate'
GE_RECONBINACION  = 0.90
GE_DIM_POBLACION  = 5           # Factor para establecer el tamaño de la población (por defecto es 15)
GE_WORKERS        = 32          # número de procesadores a utilizar

SEMAZAR = [42, 333, 1755, 1234, 7000, 933, 2255, 1515, 29]  # varios valores de la semilla para las pruebas, se selecciona una en la línea siguiente
GE_SEMILLA        = SEMAZAR[0]  # valor inicial del generador de números aleatorios

GE_HISTORIAL      = 200         # número de iteraciones para salvar el historial
GE_SOLUCIONES     = 500         # número de iteraciones para salvar la solución
GE_IMG_FIL        = 5           # número de filas del mapa de gráficos con la evolución de los precios y las variables
GE_IMG_COL        = 6           # número de columnas del mapa de gráficos con la evolución de los precios y las variables

# el método 'best1bin' genera una nueva solución de la forma:
# new = best + (mutation * (rand1 – rand2))
METODO_MIN        = 'best1bin'

if GE_WORKERS > 1:
    # aunque se modifica automáticamente, no está de más especificarlo por transparencia
    GE_ACTUALIZACION = 'deferred'

# el resultado de la función a minimizar lo determina la METRICA_ERROR y es:
#   0: la suma del cuadrado de los desvios de cada una de las variables
#   1: la suma de los valores absolutos de los desvios de cada una de las variables
#   2: la suma de los desvios de cada una de las variables elevada a POT_DESVIOS, si el desvio es negatino se toma el valor absoluto
METRICA_ERROR     = 0
POT_DESVIOS       = 2   # solo se usa en el caso de METRICA_ERROR = 2

SENDA_DATOS       = 'C:/MEGA/Datos'
SENDA_SALIDAS     = 'C:/MEGA/SalAmpliado/Salidas'
os.makedirs(SENDA_SALIDAS, exist_ok=True)   # crear el directorio si no existe

# --------------------------------------------------------------------
# ATENCION el factor trabajo debe ser la columna 'INDICE_F_TRA' de 'h'
# --------------------------------------------------------------------
INDICE_F_TRA = 1     # índice del factor trabajo, es mejor cambiar la definición de la lista 'h' que cambiar este índice

if   NSAM == 0:
    # Con un solo hogar (consumidor)
    DEM_ADICIONAL = np.array([
        [0., 0.],
    ])
    AYD_ADICIONAL = np.array([
        [0., 0.],
    ])
    AYD_ADI_DEM = AYD_ADICIONAL.sum(axis=1)

    DECIMALES = 5
    GE_TOLERANCIA     = 1.e-10  # límite para considerar el objetivo alcanzado.
    GE_VERIFICAR      = 1.e-09  # límite para considerar que la ecuación se cumple
    GE_HISTORIAL      = 50      # número de iteraciones para salvar el historial
    GE_SOLUCIONES     = 50      # número de iteraciones para salvar solución
    GE_TOLERANCIA     = 1.e-09  # límite para considerar el objetivo alcanzado.
    GE_VERIFICAR      = 1.e-08
    GE_HISTORIAL      = 50      # número de iteraciones para salvar el historial
    GE_SOLUCIONES     = 50      # número de iteraciones para salvar solución
    FICHERO_SAM = '{}/{}.xlsx'.format(SENDA_DATOS, "SAM_estandar")
    ind  = ('BRD' ,'MLK')       # sectores (industria)
    h    = ('CAP' ,'LAB')       # factores de producción
    dem  = ('HOH',)             # demanda de los hogares
    idt  = ('IDT',)             # impuestos indirectos a la producción
    trf  = ('TRF',)             # aranceles pagados por la producción (son los únicos que importan en este modelo)
    gov  = ('GOV',)             # gobierno
    retg = ()                   # ayudas del gobierno
    inv  = ('INV',)             # ahorro e inversión
    ext  = ('EXT',)             # sector exterior
    css  = ('CSS',)             # cotizaciones a la seguridad social
    #
elif NSAM == 1:
    # Con dos hogares (consumidores)
    DEM_ADICIONAL = np.array([
        [0., 0.],
        [0., 0.],
    ])
    AYD_ADICIONAL = np.array([
        [0., 0.],
        [0., 0.],
    ])
    AYD_ADI_DEM = AYD_ADICIONAL.sum(axis=1)

    DECIMALES = 3
    GE_TOLERANCIA     = 1.e-08  # límite para considerar el objetivo alcanzado.
    GE_VERIFICAR      = 1.e-07  # límite para considerar que la ecuación se cumple
    GE_HISTORIAL      = 50      # número de iteraciones para salvar el historial
    GE_SOLUCIONES     = 50      # número de iteraciones para salvar solución
    FICHERO_SAM = '{}/{}.xlsx'.format(SENDA_DATOS, "SAM_10_10")
    FICHERO_SAM = '{}/{}.xlsx'.format(SENDA_DATOS, "SAM_CSS")
    
    # declara las variables como 'tuple' (entre paréntesis) que es igual que 'list' pero no modificable, lo que las hace más eficientes)
    ind  = ('BRD' ,'MLK')       # sectores (industria)
    h    = ('CAP' ,'LAB')       # factores de producción
    dem  = ('HOH1','HOH2')      # demanda de los hogares
    idt  = ('IDT',)             # impuestos indirectos a la producción
    trf  = ('TRF',)             # aranceles pagados por la producción (son los únicos que importan en este modelo)
    gov  = ('GOV',)             # gobierno
    retg = ()                   # ayudas del gobierno
    inv  = ('INV',)             # ahorro e inversión
    ext  = ('EXT',)             # sector exterior
    css  = ('CSS',)             # cotizaciones a la seguridad social
    #
elif NSAM == 2:
    # Con tres hogares (consumidores), seguridad social independiente y ayudas del gobierno
    DEM_ADICIONAL = np.array([
        [0., 0.],
        [0., 0.],
        [0., 0.],
    ])
    AYD_ADICIONAL = np.array([
        [0., 0.],
        [0., 0.],
        [0., 0.],
    ])
    AYD_ADI_DEM = AYD_ADICIONAL.sum(axis=1)

    DECIMALES = 3
    GE_TOLERANCIA     = 1.e-08  # límite para considerar el objetivo alcanzado.
    GE_VERIFICAR      = 1.e-07  # límite para considerar que la ecuación se cumple
    GE_HISTORIAL      = 50      # número de iteraciones para salvar el historial
    GE_SOLUCIONES     = 50      # número de iteraciones para salvar solución
    FICHERO_SAM = '{}/{}.xlsx'.format(SENDA_DATOS, "SAM_AMP")
    # declara las variables como 'tuple' (entre paréntesis) que es igual que 'list' pero no modificable, lo que las hace más eficientes)
    ind  = ('BRD' ,'MLK')           # sectores (industria)
    h    = ('CAP' ,'LAB')           # factores de producción
    dem  = ('HOH1','HOH2','HOH3')   # demanda de los hogares
    idt  = ('IDT',)                 # impuestos indirectos a la producción
    trf  = ('TRF',)                 # aranceles pagados por la producción (son los únicos que importan en este modelo)
    gov  = ('GOV',)                 # gobierno
    retg = ('AYD',)                 # ayudas del gobierno
    inv  = ('INV',)                 # ahorro e inversión
    ext  = ('EXT',)                 # sector exterior
    css  = ('CSS',)                 # cotizaciones a la seguridad social
    #
elif NSAM == 3:
    # MCA-ESP-05 corregida
    '''
    Actividades_Agrarias_y_pesca	            AP1
    Energía_e_industrias_extractivas	        AP2
    Actividades_industriales	                AP3
    Construcción	                            AP4
    Servicios_destinados_a_la_venta	            AP5
    Servicios_no_destinados_a_la_venta	        AP6 (servicios de no mercado, ayudas más o menos)
    Trabajo	                                    L
    Capital	                                    K
    Consumo	                                    C
    Ahorro/Inversión	                        A-I
    Cotizaciones_sociales	                    CSS
    Impuestos_netos_sobre_los_productos	        INP
    Otros_impuestos_netos_sobre_la_producción	INPR
    IRPF	                                    IRPF
    Sector_público	                            SP
    Sector_exterior	                            SE
    '''
    DECIMALES = 1
    GE_TOLERANCIA     = 1.e-09  # límite para considerar el objetivo alcanzado
    GE_VERIFICAR      = 1.e-07  # límite para considerar que la ecuación se cumple
    GE_HISTORIAL      =  1000   # número de iteraciones para salvar el historial
    GE_SOLUCIONES     =  1000   # número de iteraciones para salvar solución
    FICHERO_SAM = '{}/{}.xlsx'.format(SENDA_DATOS, "MCA-ESP-05_ajustada_imp_final")
    ind  = ('AP1','AP2','AP3','AP4','AP5','AP6')    # sectores (industria)
    h    = ('K'  ,'L')                              # factores de producción
    dem  = ('C1','C2')                              # demanda de los hogares
    idt  = ('INP',)                                 # impuestos a la producción, otros impuestos a la producción
    trf  = ('TRF',)                                 # aranceles pagados por la producción (no los hay en esta MCS)
    gov  = ('SP',)                                  # gobierno
    retg = ('AYD',)                                 # ayudas del gobierno
    inv  = ('A-I',)                                 # ahorro e inversión
    ext  = ('SE',)                                  # sector exterior
    css  = ('CSS',)                                 # cotizaciones a la seguridad social
    #
else:
    print('Número de MCS {} incorrecto'.format(NSAM))
    sys.exit()

nsec = len(ind)         # número de sectores
nfac = len(h)           # número de factores
ndem = len(dem)         # número de hogares

# componer el nombre de los ficheros de salida en función de las opciones
CASO  = PREFIJO+ h[INDICE_F_TRA] + '_' + 'Dv_{:1d}_'.format(OPT_DESVIOS) + 'FR_{:1d}_'.format(OR_PRE_REFERENCIA) + ('END_' if FF_ENDOGENA else 'EXO_') + ('Alp_' if AHORRO_L_PLAZO else '') + 'Pref{:04.2f}_'.format(PRECIO_F_REFERENCIA) + '{:03}_{:03}_'.format(GE_DIM_POBLACION, GE_WORKERS) + etq_sam[NSAM] + etq_caso[NCASO]
rot_desvios =  'Cu'if METRICA_ERROR == 0 else ('Ab' if METRICA_ERROR == 1 else 'P'+(str(POT_DESVIOS) if METRICA_ERROR == 2 else 'Ec'))
FICHERO = '{}/{}_{}_{}'.format(SENDA_SALIDAS, CASO, METODO_MIN, rot_desvios)
FICHERO_LOG   = FICHERO + '.log'
FI_HISTORIAL  = FICHERO + '_his.csv'
FI_SOLUCIONES = FICHERO + '_sol.csv'
FICHERO_IMG   = FICHERO

# preparar para usar la función 'imprime' que llama a la del módulo 'nfun', pasándole el nombre del fichero donde escribir
mfun.ini(FICHERO_LOG)
def imprime(texto, rc=True):
    mfun.imprime(texto, rc)

def punteros():
    # para saber la posición de las distintas variables en el vector solución en el que están
    # todas concatenadas una tras otra. Se usará en la función 'extrae_var'
    etq_vec_opt = ['pF','pY','pQ','pD','epsilon','Apz','F','E','M','D']
    pvec_desde = np.empty((len(etq_vec_opt)), dtype=np.int32)   
    pvec_hasta = np.empty((len(etq_vec_opt)), dtype=np.int32)
    i = 0   # pF
    pvec_desde[i] = 0
    # el precio del factor de referencia no forma parte de la solución ya que se fija su valor y no
    # forma parte del vector solución, por eso restamos 1
    pvec_hasta[i] = pvec_desde[i] + datos.pF0.size - 1 
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
    i += 1  # Apz
    pvec_desde[i] = pvec_hasta[i - 1] 
    pvec_hasta[i] = pvec_desde[i] + 1
    i += 1  # F
    pvec_desde[i] = pvec_hasta[i - 1] 
    pvec_hasta[i] = pvec_desde[i] + datos.F0.size
    i += 1  # E
    pvec_desde[i] = pvec_hasta[i - 1] 
    pvec_hasta[i] = pvec_desde[i] + datos.E0.size
    i += 1  # M
    pvec_desde[i] = pvec_hasta[i - 1] 
    pvec_hasta[i] = pvec_desde[i] + datos.M0.size
    i += 1  # D
    pvec_desde[i] = pvec_hasta[i - 1] 
    pvec_hasta[i] = pvec_desde[i] + datos.D0.size

    ind_pvec_desde = Series(pvec_desde, index=etq_vec_opt)
    ind_pvec_hasta = Series(pvec_hasta, index=etq_vec_opt)
    return (etq_vec_opt,ind_pvec_desde,ind_pvec_hasta)

def extrae_var(vp, clave, nfil, ncol):
    # extrae del vector solución los valores correspondientes a la variable 'clave' y le da el formato de filas y columnas adecuado
    vendo = vp[ind_pvec_desde[clave]:ind_pvec_hasta[clave]]
    if nfil > 0:
        if ncol == 0:
            return vendo.reshape(nfil)
        return vendo.reshape(nfil, ncol)
    else:
        if ncol == 0:
            return vendo.item()
        return vendo

def valores_iniciales(vec_opt):
    # muestra los valores iniciales obtenidos de la MCS
    imprime('Valores iniciales')
    imprime('')
    mfun.i_tabla('precios', etq_precios[0:npre_sol], [], vec_opt[0:npre_sol], True, 5)
    respre = np.concatenate((datos.pZ0, np.array(datos.pWe), np.array(datos.pWm)))
    mfun.i_tabla('/' , etq_precios[npre_sol:len(etq_precios)] , [], respre, True, 5)
    imprime('Cantidades')
    imprime('---------------------------------------------------------------------------------------------')
    imprime('Factores aportados por los hogares. FF0')
    mfun.i_tabla('/' , h  , dem             , datos.FF0             , False, DECIMALES)    # factores aportados por cada consumidor
    mfun.i_tabla(''  , [] , ['suma FF']     , datos.FF0.sum(axis=0) , True , DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Factores utilizados por los sectores. F0')
    mfun.i_tabla(''  , [] , ind             , datos.F0              , False, DECIMALES)    # factores utilizados por cada sector
    mfun.i_tabla(''  , [] , ['suma F0']     , datos.F0.sum(axis=0)  , False, DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Factor compuesto, suma de factores para cada sector. Y0')
    mfun.i_tabla(' ' , ind , ['Y0',]        , datos.Y0              , True , DECIMALES)
    imprime('Consumo intermedio. X0')
    mfun.i_tabla(''  , [] , ind             , datos.X0.T            , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['suma X0',]    , datos.X0.T.sum(axis=0), False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    imprime('Consumo de los hogares. Xp0')
    mfun.i_tabla(''  , [] , dem             , datos.Xp0 , False     , DECIMALES)
    mfun.i_tabla(''  , [] , ['suma Xp0']    , datos.Xp0.sum(axis=0) , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    imprime('Consumo del gobierno. Xg0')
    mfun.i_tabla(''  , [] , ['Xg0',]        , datos.Xg0             , False, DECIMALES)
    imprime('Consumo de inversión. Xv0')
    mfun.i_tabla(''  , [] , ['Xv0',]        , datos.Xv0             , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    imprime('Consumo total')
    mfun.i_tabla(''  , [] , ['X+Xp+Xg+Xv',], datos.Xp0.sum(axis=0) + datos.Xg0 + datos.Xv0 + datos.X0.sum(axis=1), False, DECIMALES)
    imprime('Producción total')
    mfun.i_tabla(''  , [] , ['Q0',]        , datos.Q0               , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    mfun.i_tabla(''  , [] , ['D0',]        , datos.D0               , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['M0',]        , datos.M0               , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['E0',]        , datos.E0               , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['Z0',]        , datos.Z0               , False, DECIMALES)
    imprime('Impuestos')
    mfun.i_tabla(''  , [] , ['Tz0',]       , datos.Tz0              , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['Tm0',]       , datos.Tm0              , False, DECIMALES)
    mfun.i_tabla('/' , dem, ['Td0',]       , datos.Td0              , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['CssH0',]     , datos.CssH0            , True , DECIMALES)
    mfun.i_tabla('/' , ind, ['CssE0',]     , datos.CssE0            , True , DECIMALES)
    mfun.i_tabla(''  , [] , ['def/sup ss',], datos.CssE0.sum() + datos.CssH0.sum() - datos.PssH0.sum(), False, DECIMALES)
    imprime('Ahorro-Inversión')
    mfun.i_tabla('/' , dem, ['Sp0',]       , datos.Sp0              , True , DECIMALES)
    mfun.i_tabla(''  , [] , ['Sg0',]       , datos.Sg0              , False, DECIMALES)
    imprime('Ahorro a largo plazo de los hogares. Alp')
    mfun.i_tabla('/' , h                  , dem                     , datos.Alp0 , True , DECIMALES)
    mfun.i_tabla(''  , []                 , ['suma Alp']            , datos.Alp0.sum(axis=0) , False, DECIMALES)
    imprime('Pensiones')
    mfun.i_tabla('/' , dem, ['PssH0',]     , datos.PssH0            , False, DECIMALES)
    imprime('Ayudas del gobierno')
    mfun.i_tabla('/' , dem, ['AgH0',]      , datos.AgH0             , False, DECIMALES)
    mfun.i_tabla('/' , ind, ['AgE0',]      , datos.AgE0             , True , DECIMALES)
    mfun.i_tabla(''  , [] , ['Sf',]        , datos.Sf0              , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['bal. pagos',], b_pini                 , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['Apz0',]      , datos.Apz0             , False, 5)
    imprime('')
    imprime('')

def salida_calibrado(parametros):
    # muestra los valores calculados para los parámretros a partir de la MCS
    imprime('---------------------------------------------------')
    imprime('Resultado del calibrado')
    imprime('---------------------------------------------------')
    imprime('')
    imprime('phi. elasticidad de transformación entre local y exportación (CET)')
    mfun.cabecera('', ind)
    mfun.cuerpo2D(['phi',], parametros.phi)
    mfun.cierre(ind)
    imprime('')
    imprime('tauz. Tasa de impuesto a la producción')
    mfun.cabecera('', ind)
    mfun.cuerpo2D(['tauz'], datos.tauz)
    mfun.cierre(ind)
    imprime('')

    imprime('taum. Tasa de aranceles')
    mfun.cabecera('', ind)
    mfun.cuerpo2D(['taum',], datos.taum)
    mfun.cierre(ind)
    imprime('')

    imprime('alfa. Participación de los productos en la función de utilidad de la demanda')
    mfun.cabecera('alfa', ind)
    mfun.cuerpo2D(dem, parametros.alfa)
    mfun.cierre(ind)
    imprime('')

    imprime('beta. Participación de los factores en la función de producción del factor compuesto')
    mfun.cabecera('Sector', h)
    mfun.cuerpo2D(ind, parametros.beta)
    mfun.cierre(h)
    imprime('')

    imprime('b. Coeficiente de escalado en la función de producción del factor compuesto')
    mfun.cabecera('Sector', ['b',])
    mfun.cuerpo2D(ind, parametros.b.reshape(nsec,1))
    mfun.cierre(['b',])
    imprime('')

    imprime('ax, ay. Coeficientes de los consumos intermedios y del factor compuesto')
    la =  list(ind)
    la.append('Factor c.')
    mfun.cabecera('Sector', la)
    mfun.cuerpo2D(ind, np.c_[parametros.ax,parametros.ay])
    mfun.cierre(la)
    imprime('')

    imprime('mu. Participación de los productos en el consumo del gobierno')
    mfun.cabecera('Sector', ['mu',])
    mfun.cuerpo2D(ind, parametros.mu.reshape(nsec,1))
    mfun.cierre(['mu',])
    imprime('')

    imprime('landa. Coeficiente de participación de la demanda de inversión')
    mfun.cabecera('Sector', ['landa',])
    mfun.cuerpo2D(ind, parametros.landa.reshape(nsec,1))
    mfun.cierre(['landa',])

    imprime('deltam. Participación de la importación en la función del producto de Armington')
    mfun.cabecera('Sector', ['deltam',])
    mfun.cuerpo2D(ind, parametros.deltam.reshape(nsec,1))
    mfun.cierre(['deltam',])
    imprime('')

    imprime('deltad. Participación de la producción local en la función del producto de Armington')
    mfun.cabecera('Sector', ['deltad',])
    mfun.cuerpo2D(ind, parametros.deltad.reshape(nsec,1))
    mfun.cierre(['deltad',])
    imprime('')

    imprime('gamma. Coeficiente de escala de la función de Armington')
    mfun.cabecera('Sector', ['gamma',])
    mfun.cuerpo2D(ind, parametros.gamma.reshape(nsec,1))
    mfun.cierre(['gamma',])
    imprime('')

    imprime('xie. Coeficiente de participación en la CET de la exportación')
    mfun.cabecera('Sector', ['xie',])
    mfun.cuerpo2D(ind, parametros.xie.reshape(nsec,1))
    mfun.cierre(['xie',])
    imprime('')

    imprime('xid. Coeficiente de participación en la CET de la demanda local')
    mfun.cabecera('Sector', ['xid',])
    mfun.cuerpo2D(ind, parametros.xid.reshape(nsec,1))
    mfun.cierre(['xid',])
    imprime('')

    imprime('teta. Coeficiente de escala de la CET de exportación')
    mfun.cabecera('Sector', ['teta',])
    mfun.cuerpo2D(ind, parametros.teta.reshape(nsec,1))
    mfun.cierre(['teta',])
    imprime('')

    imprime('ssp. Propensión al ahorro de los hogares')
    mfun.cabecera('', dem)
    mfun.cuerpo2D(['ssp',], parametros.ssp)
    mfun.cierre(dem)
    imprime('')

    imprime('ssg. Propensión al ahorro del gobierno {:9.{prec}f}'.format(parametros.ssg, prec=5))
    imprime('')

    imprime('taud. Tasa de impuestos directos')
    mfun.cabecera('', dem)
    mfun.cuerpo2D(['taud',], parametros.taud)
    mfun.cierre(dem)
    imprime('')

    imprime('ctzsse. Cotización a la seguridad social de las empresas')
    mfun.cabecera('', ind)
    mfun.cuerpo2D(['ctzsse',], parametros.ctzsse)
    mfun.cierre(ind)
    imprime('')

    imprime('ctzssh. Cotización a la seguridad social de los hogares')
    mfun.cabecera('', dem)
    mfun.cuerpo2D(['ctzssh',], parametros.ctzssh)
    mfun.cierre(dem)
    imprime('')

    imprime('cage. Ayudas del gobierno a las empresas')
    mfun.cabecera('', ind)
    mfun.cuerpo2D(['cage',], parametros.cage)
    mfun.cierre(ind)
    imprime('')

    imprime('cagh. Ayudas del gobierno a los hogares')
    mfun.cabecera('', dem)
    mfun.cuerpo2D(['cagh',], parametros.cagh)
    mfun.cierre(dem)
    imprime('')

def sec_ecuaciones(vec_opt, MUESTRA_PROGRESO):
    '''
    Elemento esencial de la función objetivo que calcula el demérito (o penalización) de la solución de
    prueba 'vec_opt'.
    Esta función calcula una pareja de valores para cada variable y los pasa a la
    función 'fun_objetivo', que su vez los pasa a la función 'calcula_desvios' que los resta entre sí y
    devuelve un valor escalar que es el mismo que devuelve 'fun_objetivo'.
    Esta secuencia de llamadas es útil porque en otras partes de la aplicación necesitamos los valores
    calculados por esta función y no sirve llamar a 'fun_objetivo' que solo devuelve un escalar, así
    mismo, en otros momentos necesitamos calcular los desvíos y de aquí que estos se calculen en
    una función a propósito.
    '''
    '''
    No tiene sentido que la función 'minimize' pruebe valores para otras variables que no sean las
    que aquí se extraen, porque su valor no se usará ya que son recalculadas inmediatamente en
    esta función con independencia del valor que tengan en el vector de prueba
    '''
    # extraemos los precios del vector de prueba 'vec_opt'
    pf = extrae_var(vec_opt, 'pF', 0, nfac - 1)
    if OR_PRE_REFERENCIA == 1:
        # Como el vector de prueba no incluye el precio del último factor, añadimos el precio del
        # último factor con valor 'PRECIO_F_REFERENCIA'
        pf = np.append(pf, np.array([PRECIO_F_REFERENCIA]), axis=0)
    else:
        # Como el vector de prueba no incluye el precio del primer factor, insertamos al principio (0) el
        # precio del primer factor con valor 'PRECIO_F_REFERENCIA'
        pf = np.insert(pf, 0, np.array([PRECIO_F_REFERENCIA]), axis=0)
    py = extrae_var(vec_opt, 'pY', 0, nsec)
    pq = extrae_var(vec_opt, 'pQ', 0, nsec)
    pd = extrae_var(vec_opt, 'pD', 0, nsec)
    epsilon = extrae_var(vec_opt, 'epsilon', 0, 0)
    Apz = extrae_var(vec_opt, 'Apz', 0, nsec)

    # extraemos los valores de las 'variables de inicio' del vector de prueba 'vec_opt'
    F  = extrae_var(vec_opt, 'F', nsec, nfac)
    E  = extrae_var(vec_opt, 'E', 0, nsec)
    M  = extrae_var(vec_opt, 'M', 0, nsec)
    D  = extrae_var(vec_opt, 'D', 0, nsec)

    # guardamos los valores de la solución de prueba para luego compararlos con los calculados
    Fi = copy.deepcopy(F)
    Ei = copy.deepcopy(E)
    Mi = copy.deepcopy(M)
    Di = copy.deepcopy(D)

    # calculamos los precios del comercio internacional en moneda local
    (pe, pm) = exte.precio_moneda_local_pe_pm(datos.pWe, datos.pWm, epsilon)        # 6.14 y 6.15

    ax = parametros.ax
    ay = parametros.ay
    
    #----------------------------------------------------------------------------------------
    # Calculamos el valor de todas las variables endógenas aplicando todas las ecuaciones del
    # modelo, siguiendo el orden del libro de referencia (con algunas excepciones), el número 6.??
    # de la ecuación es porque están en el capítulo 6 del libro
    #----------------------------------------------------------------------------------------

    # Producción
    #-----------------------------------------------------
    # 'Y' factor compuesto optimo para por cada sector, dadas las utilizaciones de factores de
    # producción F y la función de producción Cobb Douglas correspondiente
    # en el equilibrio debe ser igual a la necesidad (Yd) de factor compuesto dada una producción bruta Z (6. 4)
    Yp = prod.produccion_factor_compuesto_Y(F, parametros.beta, parametros.b)               # 6. 1
    
    # traemos el cálculo de Z aquí porque solo depende de las endógenas E y D que forman parte del vector de prueba
    # el reparto de la producción bruta de un sector (Z) entre exportación (E) y suministro local (D) debe cumplir la
    # relación siguiente
    Z  = exte.restriccion_producción_bruta_Z(parametros.teta, parametros.xie, parametros.xid, E, D, parametros.phi) # 6.20

    # dada la producción Z del sector 'i' (demanda de su producto) calculamos la utilización 'X' de
    # consumos intermedios 'j', que hace 'i' por aplicación de los coeficientes 'ax' deducidos de la MCS
    X = prod.consumo_intermedio_X(Z, ax)                                                    # 6. 3

    # la utilización (consumo) de factor compuesto por cada sector no es más que su 
    # producción bruta 'Z' por lo que necesita por unidad de producción 'ay'
    Yd = prod.utilizacion_factor_compuesto_Y(Z, ay)                                         # 6. 4

    # recalculamos los F óptimos de los sectores. En el equilibrio los (F) recalculados deben coincidir con los
    # (Fi) utilizados en el cálculo de 'Yp' que se ha hecho antes.
    # Esta ecuación determina la combinación óptima de factores, el total de los mismos (Yp) para cada sector debe coincidir
    # con (Yd) que es el obtenido en la ecuación (6.4), es decir, igual al parámetro de factores necesarios por
    # unidad de produción (ay) por la producción bruta (Z)
    # de momento usamos la media de los dos cálculos de Y
    F = prod.uso_optimo_factores_F(parametros.beta, pf, py, (Yp + Yd) / 2.)                 # 6. 2


    # La variación de la suma del factor compuesto respecto del factor compuesto de la MCS
    # es la variación de factores de producción que deben aportar los hogares FF
    # en el caso de que los FF sean constantes la ecuación de cierre exige que la suma de
    # variaciones sea cero
    # Si FF es endógena este es lo que hay que incrementar FF0

    # producción bruta
    # se usa la ecuación alternativa que no necesita el cálculo de un valor mínimo
    pz = prod.coste_unitario_produccion_pz(ay, py, ax, pq)                                  # 6. 5 alternativa

    if  FF_ENDOGENA:
        # se calcula la aportación de factores (FF) como igual a la necesidad de factores (F) por los sectores
        # en el equilibrio (F) debe ser igual al parámetro de factores necesarios por unidad de
        # produción (ay) por la producción bruta (Z) (6.4)
        FF = deho.aportacion_factores_FF(datos.FF0, F)
        if AHORRO_L_PLAZO:
            # se ahorra a largo plazo (Alp) el exceso de ingresos (FF) respecto a los iniciales (FF0)
            Alp = FF - datos.FF0
            FF = datos.FF0
        else:
            Alp = datos.Alp0
    else:
        FF = datos.FF0
        Alp = datos.Alp0
    # Gobierno
    #-------------------------------------------------------------
    # impuestos
    Td = gob.impuestos_directos_Td(parametros.taud, pf, FF, datos.PssH0)                # 6. 6
    Tz = gob.impuestos_produccion_Tz(datos.tauz, pz, Z)                                 # 6. 7
    Tm = gob.aranceles_importacion_Tm(datos.taum, pm, M)                                # 6. 8
    # ayudas (pagos) del gobierno a las empresas, un porcentaje de lo recaudado por impuestos
    AgE  = gob.ayudas_empresas_AgE(parametros.cage, Td, Tz, Tm)
    # ayudas (pagos) del gobierno a los hogares, un porcentaje de lo recaudado por impuestos
    AgH  = gob.ayudas_hogares_AgH(parametros.cagh, Td, Tz, Tm, AYD_ADI_DEM)

    # Ahorro (privado -hogares- y del gobierno). Se invertirán íntegramente en los sectores
    # las calculamos antes que 6. 9 y 6.10 porque mo dependen de los resultados de estas y sin
    # embargo 6. 9 y 6.10 si dependen de ellos
    #-------------------------------------------------------------
    Sp = ainv.ahorro_hogares_Sp(parametros.ssp, FF, pf, datos.PssH0)                    # 6.11
    Sg = ainv.ahorro_gobierno_Sg(parametros.ssg, Td, Tz, Tm, AgE, AgH)                  # 6.12

    # El gobierno compra productos con cargo a sus ingresos disponibles que son lo que recauda por
    # impuestos menos su ahorro (Sg) y las ayudas a empresas (AgE) y hogares (AgH)
    Xg = gob.demanda_gobierno_Xg(parametros.mu, pq, Td, Tz, Tm, Sg, AgE, AgH)           # 6. 9

    # Seguridad social
    #-------------------------------------------------------------
    # cotizaciones a la seguridad social, un porcentaje del factor trabajo:

    #   de las empresas (F es la utilización de factores de cada sector)
    CssE = gob.seguridad_social_empresas_CssE(parametros.ctzsse, F, INDICE_F_TRA)
    #   de los hogares (FF es la prestación de factores de cada hogar -consumidor- que es exógena)
    CssH = gob.seguridad_social_hogares_CssH(parametros.ctzssh, FF, Alp, INDICE_F_TRA)
    # los pagos de la seguridad social a los hogares (pensiones -PssH0-) es un valor constante fijado de antemano (exógena).
    # variable exógena PssH0

    # Inversión con cargo a los ahorros: los ahorros privados (Sp), del gobierno (Sg) y del
    # exterior (Sf0), se reparten entre sectores proporcionalmente a la MCS (parametros.landa)
    #-------------------------------------------------------------
    Xv = ainv.demanda_inversion_Xv(parametros.landa, pq, Sp, Sg, epsilon, datos.Sf0)    # 6.10

    # Consumo de productos de los hogares. Mediante la función que optimiza la utilidad (pq, parametros.alfa) a
    # partir de los ingresos netos:
    # ingresos brutos: (pf, FF) + datos.PssH0 + AgH
    # gastos         : Sp + Td + CssH 
    #-------------------------------------------------------------
    Xp = deho.demanda_maxima_utilidad_CobbDouglas_Xp(parametros.alfa, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, DEM_ADICIONAL)    # 6.13

    # Armington. Cálculo circular: calculamos Q en función de M y D y luego calculamos M y D en función de Q
    #-------------------------------------------------------------
    Q  = exte.produccion_armington_Q(parametros.gamma, parametros.deltam, parametros.deltad, M, D, parametros.eta)                  # 6.17
    # función CES de sustitución con la que determinar el óptimo entre importar 'M' o
    # producir localmente 'D', la demanda del producto de Armington 'Q'
    M  = exte.importacion_maxima_utilidad_armington_M(parametros.gamma, parametros.deltam, pq, pm, Q, parametros.eta, datos.taum)   # 6.18
    Da = exte.produccion_maxima_utilidad_armington_D(parametros.gamma, parametros.deltad, pq, pd, Q, parametros.eta)                # 6.19

    # Función CES de transformación (CET). Cálculo circular, Z es función (6.20) de E y D y luego E y D son función (6.21 y 6.22) de Z
    #-----------------------------------------------------
    
    # transformación de la producción bruta 'Z', en producto para exportación 'E' y para suministro local 'D'
    # hay que considerar la cotización a la seguridad social 'CssE' como un mayor coste de la producción bruta 'Z' en
    # el cálculo de 'E' y 'D', es decir, hay que incrementar 'pz' por los pagos a la seguridad social al
    # igual que con los impuestos a la producción 'tauz'
    E  = exte.produccion_para_exportacion_E(parametros.teta, parametros.xie, pz, pe, Z, parametros.phi, datos.tauz, CssE, AgE, Apz) # 6.21
    Dt  = exte.produccion_para_local_D(parametros.teta, parametros.xid, pz, pd, Z, parametros.phi, datos.tauz, CssE, AgE, Apz)      # 6.22

    # Comercio internacional. Lo traemos aquí para usar los últimos valores calculados para E y M
    #-------------------------------------------------------------
    # restricción a la balanza de pagos, las importaciones deben ser igual a las exportaciones más
    # la balanza de pagos inicial 'datos.Sf0' que es exógena.
    ebp = exte.balance_pagos_moneda_extranjera(datos.pWe, E, datos.pWm, M, datos.Sf0)                                               # 6.16
    
    # Leontief para comparar, no tiene otro uso
    Zl = prod.produccion_sector_Z(X, ax, Yd, ay)                                                                                    # 6. 5 original
    '''
    Para calcular el demerito de la solución de prueba 'vec_opt', que recibe está función como argumento,
    recalculamos las variables para ver cuánto se diferencian del cálculo previo.
    '''
    Zr    = exte.restriccion_producción_bruta_Z(parametros.teta, parametros.xie, parametros.xid, E, Dt, parametros.phi)             # 6.20

    Ypr   = prod.produccion_factor_compuesto_Y(F, parametros.beta, parametros.b)            # 6. 1
    Fr    = prod.uso_optimo_factores_F(parametros.beta, pf, py, Ypr)                        # 6. 2
    Xr    = prod.consumo_intermedio_X(Zr, ax)                                               # 6. 3
    Ydr   = prod.utilizacion_factor_compuesto_Y(Zr, ay)                                     # 6. 4

    if  FF_ENDOGENA:
        FFr = deho.aportacion_factores_FF(datos.FF0, F)
        if AHORRO_L_PLAZO:
            Alpr = FFr - datos.FF0
            FFr  = datos.FF0
        else:
            Alpr = datos.Alp0
    else:
        FFr  = copy.deepcopy(FF)
        Alpr = datos.Alp0

    Tdr   = gob.impuestos_directos_Td(parametros.taud, pf, FFr, datos.PssH0)                # 6. 6
    Tzr   = gob.impuestos_produccion_Tz(datos.tauz, pz, Zr)                                 # 6. 7
    Tmr   = gob.aranceles_importacion_Tm(datos.taum, pm, M)                                 # 6. 8
    
    Spr   = ainv.ahorro_hogares_Sp(parametros.ssp, FFr, pf, datos.PssH0)                    # 6.11
    AgEr  = gob.ayudas_empresas_AgE(parametros.cage, Tdr, Tzr, Tmr)
    AgHr  = gob.ayudas_hogares_AgH(parametros.cagh, Tdr, Tzr, Tmr, AYD_ADI_DEM)
    Sgr   = ainv.ahorro_gobierno_Sg(parametros.ssg, Tdr, Tzr, Tmr, AgEr, AgHr)              # 6.12
    Xgr   = gob.demanda_gobierno_Xg(parametros.mu, pq, Tdr, Tzr, Tmr, Sgr, AgEr, AgHr)      # 6. 9
    CssEr = gob.seguridad_social_empresas_CssE(parametros.ctzsse, Fr, INDICE_F_TRA)
    CssHr = gob.seguridad_social_hogares_CssH(parametros.ctzssh, FFr, Alpr, INDICE_F_TRA)
    Xvr   = ainv.demanda_inversion_Xv(parametros.landa, pq, Spr, Sgr, epsilon, datos.Sf0)   # 6.10

    Xpr   = deho.demanda_maxima_utilidad_CobbDouglas_Xp(parametros.alfa, pq, pf, FFr, Spr, Tdr, CssHr, AgHr, datos.PssH0, DEM_ADICIONAL)    # 6.13
    Qr    = exte.produccion_armington_Q(parametros.gamma, parametros.deltam, parametros.deltad, M, Dt, parametros.eta)                      # 6.17
    Mr    = exte.importacion_maxima_utilidad_armington_M(parametros.gamma, parametros.deltam, pq, pm, Qr, parametros.eta, datos.taum)       # 6.18
    Dar   = exte.produccion_maxima_utilidad_armington_D(parametros.gamma, parametros.deltad, pq, pd, Qr, parametros.eta)                    # 6.19
    Er    = exte.produccion_para_exportacion_E(parametros.teta, parametros.xie, pz, pe, Zr, parametros.phi, datos.tauz, CssEr, AgEr, Apz)   # 6.21
    Dtr   = exte.produccion_para_local_D(parametros.teta, parametros.xid, pz, pd, Zr, parametros.phi, datos.tauz, CssEr, AgEr, Apz)         # 6.22
    ebpr  = exte.balance_pagos_moneda_extranjera(datos.pWe, Er, datos.pWm, Mr, datos.Sf0)                                                   # 6.16

    if MUESTRA_PROGRESO:
        respre = np.concatenate((pz, np.array(pe), np.array(pm)))
        mfun.i_tabla('precios', etq_precios[0:npre_sol], []       , vec_opt[0:npre_sol]  , True ,  5)
        mfun.i_tabla('/' , etq_precios[npre_sol:len(etq_precios)] , [], respre           , True ,  5)
        imprime('Cantidades')
        imprime('---------------------------------------------------------------------------------------------')
        imprime('Factores aportados por los hogares. FF')
        mfun.i_tabla('/' , h                    , dem             , FF                   , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['suma FF']     , FF.sum(axis=0)       , False, DECIMALES)
        mfun.i_pie('/'   , h)
        imprime('Factores utilizados por los sectores. F')
        mfun.i_tabla(''  , []                   , ind             , F                    , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['suma F',]     , F.sum(axis=0)        , False, DECIMALES)
        mfun.i_pie('/'   , h)
        imprime('Factor compuesto, suma de factores para cada sector. Y')
        mfun.i_tabla('/' , ind                  , ['Yprodu 6.1',] , Yp                   , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['Yprodu 6.4',] , Yd                   , False, DECIMALES)
        imprime('Consumo intermedio. X')
        mfun.i_tabla(''  , []                   , ind             , X.T                  , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['suma X',]     , X.T.sum(axis=0)      , False, DECIMALES)
        mfun.i_pie('/'   , ind)
        imprime('Consumo de los hogares. Xp')
        mfun.i_tabla(''  , []                   , dem             , Xp                   , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['suma Xp',]    , Xp.sum(axis=0)       , False, DECIMALES)
        mfun.i_pie('/'   , ind)
        imprime('Consumo del gobierno. Xg')
        mfun.i_tabla(''  , []                   , ['Xg',]         , Xg                   , False, DECIMALES)
        imprime('Consumo de inversión. Xv')
        mfun.i_tabla(''  , []                   , ['Xv',]         , Xv                   , False, DECIMALES)
        mfun.i_pie('/'   , ind)
        imprime('Consumo total')
        mfun.i_tabla(''  , []                   , ['X+Xp+Xg+Xv']  , Xp.sum(axis=0) + Xg + Xv + X.sum(axis=1), False, DECIMALES)
        imprime('Producción total')
        mfun.i_tabla(''  , []                   , ['Q',]          , Q                    , False, DECIMALES)
        mfun.i_pie  ('/' , ind)
        mfun.i_tabla(''  , []                   , ['D 6.19',]     , Da                   , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['D 6.22',]     , Dt                   , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['M',]          , M                    , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['E',]          , E                    , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['Z',]          , Z                   , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['Z leontief',] , Zl                   , False, DECIMALES)
        imprime('Impuestos')
        mfun.i_tabla(''  , []                   , ['Tz',]         , Tz                   , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['Tm',]         , Tm                   , False, DECIMALES)
        mfun.i_tabla('/' , dem                  , ['Td',]         , Td                   , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['CssH',]       , CssH                 , True , DECIMALES)
        mfun.i_tabla('/' , ind                  , ['CssE',]       , CssE                 , True , DECIMALES)
        mfun.i_tabla(''  , []                   , ['def/sup ss',] , CssE.sum() + CssH.sum() - datos.PssH0.sum(), False, DECIMALES)
        imprime('Ahorro-Inversión')
        mfun.i_tabla('/' , dem                  , ['Sp',]         , Sp                   , True , DECIMALES)
        mfun.i_tabla(''  , []                   , ['Sg',]         , Sg                   , False, DECIMALES)
        imprime('Ahorro a largo plazo de los hogares. Alp')
        mfun.i_tabla('/' , h                    , dem             , Alp                  , True , DECIMALES)
        mfun.i_tabla(''  , []                   , ['suma Alp']    , Alp.sum(axis=0)      , False, DECIMALES)
        imprime('Pensiones')
        mfun.i_tabla('/' , dem                  , ['PssH0',]      , datos.PssH0          , True , DECIMALES)
        imprime('Ayudas del gobierno')
        mfun.i_tabla('/' , dem                  , ['AgH',]        , AgH                  , False, DECIMALES)
        mfun.i_tabla('/' , ind                  , ['AgE',]        , AgE                  , True , DECIMALES)
        mfun.i_tabla(''  , []                   , ['Sf',]         , datos.Sf0            , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['bal. pagos',] , ebp                  , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['Apz',]        , Apz                  , False, 5)
        imprime('')
        imprime('')
    else:
        global iteracion
        iteracion += 1
    res_ecuaciones = (Apz,Fi,Ei,Mi,Di,
            Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,AgE ,AgH ,CssE ,CssH, ebp,Zl,pz,
            Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,AgEr,AgHr,CssEr,CssHr,ebpr
    )
    return res_ecuaciones

def calcula_desvios(res_ecuaciones, MUESTRA_PROGRESO):
    '''
    Calcula los desvíos (penalización) correspondientes a la ejecución de las ecuaciones 'sec_ecuaciones'
    '''
    (Apz,Fi,Ei,Mi,Di,
        Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,AgE ,AgH ,CssE ,CssH,ebp,Zl,pz,
        Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,AgEr,AgHr,CssEr,CssHr,ebpr
    ) = res_ecuaciones

    # Se trata de forma individualizada la desviación en valor absoluto de cada variable

    # Apz no se puede afectar de un coeficiente grande, como se hace en GAMS, porque nuestro método
    # sacrificaría la convergencia de las otras variables para facilitar la anulación de Apz
    des_Apz = abs(Apz)

    des_ebp = np.array([abs(ebp) + abs(ebpr)])

    # condiciones de equilibrio del mercado
    des_produccion = abs(Q - (Xp.sum(axis=0) + Xg + Xv + X.sum(axis=1))).flatten()      # 6.23
    # la utilización total de cada factor por los sectores 'F.sum(axis=0)' debe ser igual a la
    # aportación inicial de los mismos por los hogares 'FF.sum(axis=0)' más el ahorro a largo plazo
    des_factores   = abs(F.sum(axis=0) - (FF.sum(axis=0) + Alp.sum(axis=0))).flatten()  # 6.24

    des_Fi         = abs(F    - Fi  ).flatten()    
    des_F          = abs(Fr   - F   ).flatten()

    des_Ei         = abs(E    - Ei  ).flatten()    
    des_E          = abs(Er   - E   ).flatten()    

    des_Mi         = abs(M    - Mi  ).flatten()    
    des_M          = abs(Mr   - M   ).flatten()    

    if OPT_DESVIOS == 0:
        des_Di         = abs(Dt   - Di  ).flatten()
        des_Da         = abs(Dar  - Da  ).flatten()    
        des_Dt         = abs(Dtr  - Dt  ).flatten()    
        des_Yp         = abs(Ypr  - Yp  ).flatten()    
        des_Yd         = abs(Ydr  - Yd  ).flatten()    

    des_Dat        = abs(Da   - Dt  ).flatten()    

    des_FF         = abs(FFr  - FF  ).flatten()

    des_Ydp        = abs(Yd   - Yp  ).flatten()    

    des_Z          = abs(Zr   - Z   ).flatten()
    des_X          = abs(Xr   - X   ).flatten()    
    des_Xp         = abs(Xpr  - Xp  ).flatten()    
    des_Xg         = abs(Xgr  - Xg  ).flatten()    
    des_Xv         = abs(Xvr  - Xv  ).flatten()    
    des_Q          = abs(Qr   - Q   ).flatten()    
    des_Td         = abs(Tdr  - Td  ).flatten()    
    des_Tz         = abs(Tzr  - Tz  ).flatten()    
    des_Tm         = abs(Tmr  - Tm  ).flatten()    
    des_Sp         = abs(Spr  - Sp  ).flatten()    
    des_Sg         = abs(Sgr  - Sg  ).flatten()    
    des_AgE        = abs(AgEr - AgE ).flatten()    
    des_AgH        = abs(AgHr - AgH ).flatten()    
    des_CssE       = abs(CssEr- CssE).flatten()    
    des_CssH       = abs(CssHr- CssH).flatten()    
    des_Alp        = abs(Alpr - Alp ).flatten()
    
    if OPT_DESVIOS == 0:
        # Se incluyen desvíos redundantes, pero puede acelerar la convergencia y producir mejores resultados
        desvios = np.concatenate(
            (   des_produccion,des_factores,des_Apz,des_ebp,
                des_Fi,des_Ei,des_Mi,des_Di,
                des_F,des_M,des_E,
                des_Da,des_Dt,
                des_Dat,
                des_Yp,des_Yd,
                des_Ydp,
                des_Alp,des_FF,des_Z,des_X,des_Xp,des_Xg,des_Xv,des_Q,
                des_Td,des_Tz,des_Tm,des_Sp,des_Sg,des_AgE,des_AgH,des_CssE,des_CssH
            )
        )
    else:
        desvios = np.concatenate(
            (   des_produccion,des_factores,des_Apz,des_ebp,
                des_Fi,des_Ei,des_M,
                des_F,des_M,des_E,
                des_Dat,
                des_Ydp,
                des_Alp,des_FF,des_Z,des_X,des_Xp,des_Xg,des_Xv,des_Q,
                des_Td,des_Tz,des_Tm,des_Sp,des_Sg,des_AgE,des_AgH,des_CssE,des_CssH
            )
        )
    if METRICA_ERROR == 0:
        dist = (desvios ** 2).sum()
    elif METRICA_ERROR == 1:
        dist = desvios.sum()
    elif METRICA_ERROR == 2:
        if POT_DESVIOS % 2 == 0:
            # exponente par
            dist = (desvios ** POT_DESVIOS).sum()
        else:
            dist = (abs(desvios) ** POT_DESVIOS).sum()

    if MUESTRA_PROGRESO:
        mfun.tabla_2De(['equilib Q',] , des_produccion)
        mfun.tabla_2De(['equilib F',] , des_factores)
        mfun.tabla_2De(['des Fi',]    , des_Fi)
        mfun.tabla_2De(['des Ei',]    , des_Ei)
        mfun.tabla_2De(['des Mi',]    , des_Mi)

        if OPT_DESVIOS == 0:
            mfun.tabla_2De(['des Di',]    , des_Di)
            mfun.tabla_2De(['des Yp',]    , des_Yp)
            mfun.tabla_2De(['des Yd',]    , des_Yd)
            mfun.tabla_2De(['des Da',]    , des_Da)
            mfun.tabla_2De(['des Dt',]    , des_Dt)

        mfun.tabla_2De(['des Alp',]   , des_Xg)
        mfun.tabla_2De(['des F',]     , des_FF)
        mfun.tabla_2De(['des FF',]    , des_FF)
        mfun.tabla_2De(['des Yd-p',]  , des_Ydp)
        mfun.tabla_2De(['des Z',]     , des_Z)
        mfun.tabla_2De(['des X',]     , des_X)
        mfun.tabla_2De(['des Xp',]    , des_Xp)
        mfun.tabla_2De(['des Xg',]    , des_Xg)
        mfun.tabla_2De(['des Xv',]    , des_Xv)
        mfun.tabla_2De(['des Q',]     , des_Q)
        mfun.tabla_2De(['des M',]     , des_M)
        mfun.tabla_2De(['des Da-t',]  , des_Dat)
        mfun.tabla_2De(['des E',]     , des_E)
        mfun.tabla_2De(['des Td',]    , des_Td)
        mfun.tabla_2De(['des Tz',]    , des_Tz)
        mfun.tabla_2De(['des Tm',]    , des_Tm)
        mfun.tabla_2De(['des Sp',]    , des_Sp)
        mfun.tabla_2De(['des Sg',]    , des_Sg)
        mfun.tabla_2De(['des AgE',]   , des_AgE)
        mfun.tabla_2De(['des AgH',]   , des_AgH)
        mfun.tabla_2De(['des CssE',]  , des_CssE)
        mfun.tabla_2De(['des CssH',]  , des_CssH)
        mfun.tabla_2De(['des b.pag',] , des_ebp)
        mfun.tabla_2De(['des Apz',]   , des_Apz)
        imprime('')
        mfun.tabla_2De(['Errdesvios',], dist)
        imprime('')
        imprime('---------- --------- ---------')
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('desvios Q', des_produccion.sum(), 100. * des_produccion.sum() / (1 if np.mean(Q) ==0   else np.mean(Q))    , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('desvios F', des_factores.sum()  , 100. * des_factores.sum()   / (1 if np.mean(Fi)==0   else np.mean(Fi))   , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Fi'   , des_Fi.sum()        , 100. * des_Fi.sum()         / (1 if np.mean(Fi)==0   else np.mean(Fi))   , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Ei'   , des_Ei.sum()        , 100. * des_Ei.sum()         / (1 if np.mean(Ei)==0   else np.mean(Ei))   , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Mi'   , des_Mi.sum()        , 100. * des_Mi.sum()         / (1 if np.mean(Mi)==0   else np.mean(Mi))   , prec=DECIMALES))

        if OPT_DESVIOS == 0:
            imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Di'   , des_Di.sum()        , 100. * des_Di.sum()         / (1 if np.mean(Di)==0   else np.mean(Di))   , prec=DECIMALES))
            imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Yp'   , des_Yp.sum()        , 100. * des_Yp.sum()         / (1 if np.mean(Yp)==0   else np.mean(Yp))   , prec=DECIMALES))
            imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Yd'   , des_Yd.sum()        , 100. * des_Yd.sum()         / (1 if np.mean(Yd)==0   else np.mean(Yd))   , prec=DECIMALES))
            imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Da '  , des_Da.sum()        , 100. * des_Da.sum()         / (1 if np.mean(Da)==0   else np.mean(Da))   , prec=DECIMALES))
            imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Dt'   , des_Dt.sum()        , 100. * des_Dt.sum()         / (1 if np.mean(Dt)==0   else np.mean(Dt))   , prec=DECIMALES))

        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Alp'  , des_Alp.sum()       , 100. * des_Alp.sum()        / (1 if np.mean(Alp)==0  else np.mean(Alp))  , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des F'    , des_F .sum()        , 100. * des_F.sum()          / (1 if np.mean(F)==0    else np.mean(F))    , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des FF'   , des_FF.sum()        , 100. * des_FF.sum()         / (1 if np.mean(FF)==0   else np.mean(FF))   , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Yd-Yp', des_Ydp.sum()       , 100. * des_Ydp.sum()        / (1 if np.mean(Yd)==0   else np.mean(Yd))   , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Z'    , des_Z.sum()         , 100. * des_Z.sum()          / (1 if np.mean(Z) ==0   else np.mean(Z))    , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des X'    , des_X.sum()         , 100. * des_X.sum()          / (1 if np.mean(X) ==0   else np.mean(X))    , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Xp'   , des_Xp.sum()        , 100. * des_Xp.sum()         / (1 if np.mean(Xp)==0   else np.mean(Xp))   , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Xg'   , des_Xg.sum()        , 100. * des_Xg.sum()         / (1 if np.mean(Xg)==0   else np.mean(Xg))   , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Xv'   , des_Xv.sum()        , 100. * des_Xv.sum()         / (1 if np.mean(Xv)==0   else np.mean(Xv))   , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Q'    , des_Q.sum()         , 100. * des_Q.sum()          / (1 if np.mean(Q) ==0   else np.mean(Q))    , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des M'    , des_M.sum()         , 100. * des_M.sum()          / (1 if np.mean(M) ==0   else np.mean(M))    , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Da-Dt', des_Dat.sum()       , 100. * des_Dat.sum()        / (1 if np.mean(Da)==0   else np.mean(Da))   , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des E'    , des_E.sum()         , 100. * des_E.sum()          / (1 if np.mean(E) ==0   else np.mean(E))    , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Td'   , des_Td.sum()        , 100. * des_Td.sum()         / (1 if np.mean(Td)==0   else np.mean(Td))   , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Tz'   , des_Tz.sum()        , 100. * des_Tz.sum()         / (1 if np.mean(Tz)==0   else np.mean(Tz))   , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Tm'   , des_Tm.sum()        , 100. * des_Tm.sum()         / (1 if np.mean(Tm)==0   else np.mean(Tm))   , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Sp'   , des_Sp.sum()        , 100. * des_Sp.sum()         / (1 if np.mean(Sp)==0   else np.mean(Sp))   , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Sg'   , des_Sg.sum()        , 100. * des_Sg.sum()         / (1 if np.mean(Sg)==0   else np.mean(Sg))   , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des AgE'  , des_AgE.sum()       , 100. * des_AgE.sum()        / (1 if np.mean(AgE)==0  else np.mean(AgE))  , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des AgH'  , des_AgH.sum()       , 100. * des_AgH.sum()        / (1 if np.mean(AgH)==0  else np.mean(AgH))  , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des CssE' , des_CssE.sum()      , 100. * des_CssE.sum()       / (1 if np.mean(CssE)==0 else np.mean(CssE)) , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des CssH' , des_CssH.sum()      , 100. * des_CssH.sum()       / (1 if np.mean(CssH)==0 else np.mean(CssH)) , prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} '.format       ('des b.pag', des_ebp.sum(), prec=DECIMALES))
        imprime('{:10} {:9.{prec}e} '.format       ('des Apz'  , des_Apz.sum(), prec=DECIMALES))
        imprime('---------- --------- ---------')
        imprime('')
    return dist

def fun_objetivo(vec_opt):
    res_ecuaciones = sec_ecuaciones(vec_opt, False)
    return calcula_desvios(res_ecuaciones, False)

def veri_solucion(vec_veri_sol, titulo, tolerancia):
    (pf,py,pz,pq,pd,epsilon,Apz,F,Z,E,M,D,FF,Y,X,Xp,Xg,Xv,Q,ebp,Sp,Sg,Td,Tz,Tm,CssE,CssH,AgE,AgH,Alp) = vec_veri_sol

    (pe, pm) = exte.precio_moneda_local_pe_pm(datos.pWe, datos.pWm, epsilon)
    ax = parametros.ax
    ay = parametros.ay

    v_medio     = np.zeros(len(etq_veri), dtype=np.ndarray)
    v_medio[0]  = np.median(abs(Y))
    v_medio[1]  = np.median(abs(F))
    v_medio[2]  = np.median(abs(X))
    v_medio[3]  = np.median(abs(Y))
    v_medio[4]  = np.median(abs(pz))
    v_medio[5]  = np.median(abs(Td))
    v_medio[6]  = np.median(abs(Tz))
    v_medio[7]  = np.median(abs(Tm))
    v_medio[8]  = np.median(abs(Xg))
    v_medio[9]  = np.median(abs(Xv))
    v_medio[10] = np.median(abs(Sp))
    v_medio[11] = np.median(abs(Sg))
    v_medio[12] = np.median(abs(Xp))
    v_medio[13] = np.median(abs(ebp))
    v_medio[14] = np.median(abs(Q))
    v_medio[15] = np.median(abs(M))
    v_medio[16] = np.median(abs(D))
    v_medio[17] = np.median(abs(Z))
    v_medio[18] = np.median(abs(E))
    v_medio[19] = np.median(abs(D))
    v_medio[20] = np.median(abs(CssE))
    v_medio[21] = 0
    v_medio[22] = np.median(abs(AgE))
    v_medio[23] = np.median(abs(AgH))
    v_medio[24] = np.median(abs(Q))
    v_medio[25] = np.median(abs(F.sum(axis=0)))

    desviacion     = np.zeros(len(etq_veri), dtype=np.ndarray)
    desviacion[0]  = Y     - prod.produccion_factor_compuesto_Y(F, parametros.beta, parametros.b)           # 6. 1
    desviacion[1]  = F     - prod.uso_optimo_factores_F(parametros.beta, pf, py, Y)                         # 6. 2
    desviacion[2]  = X     - prod.consumo_intermedio_X(Z, ax)                                               # 6. 3
    desviacion[3]  = Y     - prod.utilizacion_factor_compuesto_Y(Z, ay)                                     # 6. 4
    desviacion[4]  = pz    - prod.coste_unitario_produccion_pz(ay, py, ax, pq)                              # 6. 5 alternativa
    desviacion[5]  = Td    - gob.impuestos_directos_Td(parametros.taud, pf, FF, datos.PssH0)                # 6. 6
    desviacion[6]  = Tz    - gob.impuestos_produccion_Tz(datos.tauz, pz, Z)                                 # 6. 7
    desviacion[7]  = Tm    - gob.aranceles_importacion_Tm(datos.taum, pm, M)                                # 6. 8
    desviacion[8]  = Xg    - gob.demanda_gobierno_Xg(parametros.mu, pq, Td, Tz, Tm, Sg, AgE, AgH)           # 6. 9
    desviacion[9]  = Xv    - ainv.demanda_inversion_Xv(parametros.landa, pq, Sp, Sg, epsilon, datos.Sf0)    # 6.10
    desviacion[10] = Sp    - ainv.ahorro_hogares_Sp(parametros.ssp, FF, pf, datos.PssH0)                    # 6.11
    desviacion[11] = Sg    - ainv.ahorro_gobierno_Sg(parametros.ssg, Td, Tz, Tm, AgE, AgH)                  # 6.12
    desviacion[12] = Xp    - deho.demanda_maxima_utilidad_CobbDouglas_Xp(parametros.alfa, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, DEM_ADICIONAL) # 6.13
    desviacion[13] = ebp                                                                                    # 6.16
    desviacion[14] = Q     - exte.produccion_armington_Q(parametros.gamma, parametros.deltam, parametros.deltad, M, D, parametros.eta) # 6.17
    desviacion[15] = M     - exte.importacion_maxima_utilidad_armington_M(parametros.gamma, parametros.deltam, pq, pm, Q, parametros.eta, datos.taum) # 6.18
    desviacion[16] = D     - exte.produccion_maxima_utilidad_armington_D(parametros.gamma, parametros.deltad, pq, pd, Q, parametros.eta) # 6.19
    desviacion[17] = Z     - exte.restriccion_producción_bruta_Z(parametros.teta, parametros.xie, parametros.xid, E, D, parametros.phi) # 6.20
    desviacion[18] = E     - exte.produccion_para_exportacion_E(parametros.teta, parametros.xie, pz, pe, Z, parametros.phi, datos.tauz, CssE, AgE, Apz)  # 6.21
    desviacion[19] = D     - exte.produccion_para_local_D(parametros.teta, parametros.xid, pz, pd, Z, parametros.phi, datos.tauz, CssE, AgE, Apz) # 6.22
    desviacion[20]  = CssE - gob.seguridad_social_empresas_CssE(parametros.ctzsse, F, INDICE_F_TRA)         # CssE
    desviacion[21]  = CssH - gob.seguridad_social_hogares_CssH(parametros.ctzssh, FF, Alp, INDICE_F_TRA)    # CssH
    desviacion[22]  = AgE  - gob.ayudas_empresas_AgE(parametros.cage, Td, Tz, Tm)                           # AgE
    desviacion[23]  = AgH  - gob.ayudas_hogares_AgH(parametros.cagh, Td, Tz, Tm, AYD_ADI_DEM)               # AgH
    desviacion[24]  = Q    - (Xp.sum(axis=0) + Xg + Xv + X.sum(axis=1))                                     # 6.23
    desviacion[25]  = F.sum(axis=0) - (FF.sum(axis=0) + Alp.sum(axis=0))                                    # 6.24

    imprime(titulo)
    imprime('--- Verificación de las ecuaciones en error acumulado {:10.3e} --'.format(tolerancia))
    imprime('ecuación      valor medio error acumula  error máximo  % error máxi')
    imprime('----------- ------------- ------------- ------------- -------------')
    desvio = 0.
    nfallos = 0
    for i in range (len(etq_veri)):
        if np.issubdtype(type(desviacion[i]), np.floating):
            suma_des_error_cua = desviacion[i] * desviacion[i]
            suma_des_abs = abs(desviacion[i])
            max_des_error = suma_des_abs
        else:
            suma_des_error_cua = (desviacion[i] * desviacion[i]).sum()
            suma_des_abs = (abs(desviacion[i])).sum()
            max_des_error  = np.max(abs(desviacion[i]))
        desvio += suma_des_error_cua
        if suma_des_abs > tolerancia:
            if abs(v_medio[i]) < 0.01:
                # los porcentajes de desviaciones respecto de 0 no son significativos
                max_des_error  = 0
                p_error_max = 0.
            else:
                p_error_max = max_des_error / v_medio[i]
            imprime('{:11} {:13.5e} {:13.5e} {:13.5e} {:13.3f}'.format(etq_veri[i], v_medio[i], suma_des_abs, max_des_error, 100. * p_error_max))
            nfallos += 1
    if nfallos == 0:
        imprime('======= Se cumplen todas las ecuaciones en error acumulado ========')
    imprime('----------- ------------- ------------- ------------- -------------')
    imprime('')
    imprime('-- Verificación de las ecuaciones en % de error máximo {:8.3}% --'.format(100.0 * 0.0001))
    imprime('ecuación      valor medio error acumula  error máximo  % error máxi')
    imprime('----------- ------------- ------------- ------------- -------------')
    nfallos = 0
    for i in range (len(etq_veri)):
        if np.issubdtype(type(desviacion[i]), np.floating):
            suma_des_error_cua = desviacion[i] * desviacion[i]
            suma_des_abs = abs(desviacion[i])
            max_des_error = suma_des_abs
        else:
            suma_des_error_cua = (desviacion[i] * desviacion[i]).sum()
            suma_des_abs = (abs(desviacion[i])).sum()
            max_des_error  = np.max(abs(desviacion[i]))
        if abs(v_medio[i]) < 0.01:
            # los porcentajes de desviaciones respecto de 0 no son significativos
            max_des_error  = 0
            p_error_max = 0.
        else:
            p_error_max = max_des_error / v_medio[i]
        if p_error_max > 0.0001:    # 0.01%
            imprime('{:11} {:13.5e} {:13.5e} {:13.5e} {:13.3f}'.format(etq_veri[i], v_medio[i], suma_des_abs, max_des_error, 100. * p_error_max))
            nfallos += 1
    if nfallos == 0:
        imprime('======  Se cumplen todas las ecuaciones en % de error máximo ======')
    imprime('----------- ------------- ------------- ------------- -------------')
    imprime('')
    imprime('-------------------------------')
    imprime('Ecm.total desvios {:13.5e}'.format(desvio))
    imprime('-------------------------------')

def diferencias_cantidades_finales_iniciales(vec_opt_ini, vec_opt, res_ecuaciones, rot):
    (Apz,Fi,Ei,Mi,Di,
        Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,AgE ,AgH ,CssE ,CssH,ebp,Zl,pz,
        Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,AgEr,AgHr,CssEr,CssHr,ebpr
    ) = res_ecuaciones
    imprime('Diferencias entre los valores finales y los iniciales')
    imprime('')
    vec = vec_opt - vec_opt_ini
    mfun.i_tabla('precios', etq_precios[0:npre_sol], [], vec[0:npre_sol], True, 5)
    dpz = pz - datos.pZ0
    epsilon = extrae_var(vec_opt, 'epsilon', 0, 0)
    (pe, pm) = exte.precio_moneda_local_pe_pm(datos.pWe, datos.pWm, epsilon)
    dpe = pe - datos.pWe
    dpm = pm - datos.pWm
    respre = np.concatenate((dpz, np.array(dpe), np.array(dpm)))
    mfun.i_tabla('/' , etq_precios[npre_sol:len(etq_precios)] , [], respre, True, 5)
    imprime(rot)
    imprime('---------------------------------------------------------------------------------------------')
    imprime('Factores aportados por los hogares. FF')
    dFF0 = FF - datos.FF0
    mfun.i_tabla('/' , h  , dem             , dFF0                 , False, DECIMALES)    # factores aportados por cada consumidor
    mfun.i_tabla(''  , [] , ['suma FF']     , dFF0.sum(axis=0)     , True , DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Factores utilizados por los sectores. F')
    dF0 = Fi - datos.F0
    mfun.i_tabla(''  , [] , ind             , dF0                   , False, DECIMALES)    # factores utilizados por cada sector
    mfun.i_tabla(''  , [] , ['suma F']     , dF0.sum(axis=0)       , False, DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Factor compuesto, suma de factores para cada sector. Y')
    dY0 = Yp - datos.Y0
    mfun.i_tabla(' ' , ind , ['Y',]        , dY0                    , True , DECIMALES)
    imprime('Consumo intermedio. X')
    dX0 = X - datos.X0
    mfun.i_tabla(''  , [] , ind             , dX0.T                 , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['suma X',]    , dX0.T.sum(axis=0)     , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    imprime('Consumo de los hogares. Xp')
    dXp0 = Xp - datos.Xp0
    mfun.i_tabla(''  , [] , dem             , dXp0 , False          , DECIMALES)
    mfun.i_tabla(''  , [] , ['suma Xp']    , dXp0.sum(axis=0)      , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    imprime('Consumo del gobierno. Xg')
    dXg0 = Xg - datos.Xg0
    mfun.i_tabla(''  , [] , ['Xg',]        , dXg0                  , False, DECIMALES)
    imprime('Consumo de inversión. Xv')
    dXv0 = Xv - datos.Xv0
    mfun.i_tabla(''  , [] , ['Xv',]        , dXv0                  , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    imprime('Consumo total')
    mfun.i_tabla(''  , [] , ['X+Xp+Xg+Xv',], dXp0.sum(axis=0) + dXg0 + dXv0 + dX0.sum(axis=1), False, DECIMALES)
    imprime('Producción total')
    dQ0 = Q - datos.Q0
    mfun.i_tabla(''  , [] , ['Q',]        , dQ0                    , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    dD0 = Di - datos.D0
    mfun.i_tabla(''  , [] , ['D',]        , dD0                    , False, DECIMALES)
    dM0 = M - datos.M0
    mfun.i_tabla(''  , [] , ['M',]        , dM0                    , False, DECIMALES)
    dE0 = E - datos.E0
    mfun.i_tabla(''  , [] , ['E',]        , dE0                    , False, DECIMALES)
    dZ0 = Z - datos.Z0
    mfun.i_tabla(''  , [] , ['Z',]        , dZ0                    , False, DECIMALES)
    imprime('Impuestos')
    dTz0 = Tz - datos.Tz0
    mfun.i_tabla(''  , [] , ['Tz',]       , dTz0                   , False, DECIMALES)
    dTm0 = Tm - datos.Tm0
    mfun.i_tabla(''  , [] , ['Tm',]       , dTm0                   , False, DECIMALES)
    dTd0 = Td - datos.Td0
    mfun.i_tabla('/' , dem, ['Td',]       , dTd0                   , False, DECIMALES)
    dCssH0 = CssH - datos.CssH0
    mfun.i_tabla(''  , [] , ['CssH',]     , dCssH0                 , True , DECIMALES)
    dCssE0 = CssE - datos.CssE0
    mfun.i_tabla('/' , ind, ['CssE',]     , dCssE0                 , True , DECIMALES)
    mfun.i_tabla(''  , [] , ['def/sup ss',], dCssE0.sum() + dCssH0.sum(), False, DECIMALES)
    imprime('Ahorro-Inversión')
    dSp0 = Sp - datos.Sp0
    mfun.i_tabla('/' , dem, ['Sp',]       , dSp0                   , True , DECIMALES)
    dSg0 = Sg - datos.Sg0
    mfun.i_tabla(''  , [] , ['Sg',]       , dSg0                   , False, DECIMALES)
    imprime('Ahorro a largo plazo de los hogares. Alp')
    dAlp0 = Alp - datos.Alp0
    mfun.i_tabla('/' , h                  , dem                    , dAlp0             , True , DECIMALES)
    mfun.i_tabla(''  , []                 , ['suma Alp']           , dAlp0.sum(axis=0) , False, DECIMALES)
    imprime('Pensiones')
    dPssH0 = datos.PssH0 - datos.PssH0
    mfun.i_tabla('/' , dem, ['PssH',]     , dPssH0                 , False, DECIMALES)
    imprime('Ayudas del gobierno')
    dAgH0 = AgH - datos.AgH0
    mfun.i_tabla('/' , dem, ['AgH',]      , dAgH0                  , False, DECIMALES)
    dAgE0 = AgE - datos.AgE0
    mfun.i_tabla('/' , ind, ['AgE',]      , dAgE0                  , True , DECIMALES)
    dSf0 = datos.Sf0 - datos.Sf0
    mfun.i_tabla(''  , [] , ['Sf',]        , dSf0                  , False, DECIMALES)
    debp = ebp - b_pini
    mfun.i_tabla(''  , [] , ['bal. pagos',], debp                  , False, DECIMALES)
    dApz0 = Apz - datos.Apz0
    mfun.i_tabla(''  , [] , ['Apz',]      , dApz0                  , False, 5)
    imprime('')
    imprime('')

def diferencias_importes_finales_iniciales(vec_opt_ini, vec_opt, res_ecuaciones, rot):
    (Apz,Fi,Ei,Mi,Di,
        Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,AgE ,AgH ,CssE ,CssH,ebp,Zl,pz,
        Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,AgEr,AgHr,CssEr,CssHr,ebpr
    ) = res_ecuaciones
    pf = extrae_var(vec_opt, 'pF', 0, nfac - 1)
    if OR_PRE_REFERENCIA == 1:
        # Como el vector de prueba no incluye el precio del último factor, añadimos el precio del último factor con valor 'PRECIO_F_REFERENCIA'
        pf = np.append(pf, np.array([PRECIO_F_REFERENCIA]), axis=0)
    else:
        # Como el vector de prueba no incluye el precio del primer factor, insertamos al principio (0) el precio del primer factor con valor 'PRECIO_F_REFERENCIA'
        pf = np.insert(pf, 0, np.array([PRECIO_F_REFERENCIA]), axis=0)
    py = extrae_var(vec_opt, 'pY', 0, nsec)
    pq = extrae_var(vec_opt, 'pQ', 0, nsec)
    pd = extrae_var(vec_opt, 'pD', 0, nsec)
    epsilon = extrae_var(vec_opt, 'epsilon', 0, 0)
    imprime('Diferencias entre los valores finales y los iniciales')
    imprime('')
    vec = vec_opt - vec_opt_ini
    mfun.i_tabla('precios', etq_precios[0:npre_sol], [], vec[0:npre_sol], True, 5)
    dpz = pz - datos.pZ0
    (pe, pm) = exte.precio_moneda_local_pe_pm(datos.pWe, datos.pWm, epsilon)
    dpe = pe - datos.pWe
    dpm = pm - datos.pWm
    respre = np.concatenate((dpz, np.array(dpe), np.array(dpm)))
    mfun.i_tabla('/' , etq_precios[npre_sol:len(etq_precios)] , [], respre, True, 5)
    imprime(rot)
    imprime('---------------------------------------------------------------------------------------------')
    imprime('Factores aportados por los hogares. FF')
    dFF0 = FF * pf - datos.FF0 * datos.pF0
    mfun.i_tabla('/' , h  , dem             , dFF0                 , False, DECIMALES)    # factores aportados por cada consumidor
    mfun.i_tabla(''  , [] , ['suma FF']     , dFF0.sum(axis=0)     , True , DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Factores utilizados por los sectores. F')
    dF0 = Fi * pf - datos.F0 * datos.pF0
    mfun.i_tabla(''  , [] , ind             , dF0                   , False, DECIMALES)    # factores utilizados por cada sector
    mfun.i_tabla(''  , [] , ['suma F']     , dF0.sum(axis=0)       , False, DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Factor compuesto, suma de factores para cada sector. Y')
    dY0 = Yp * py - datos.Y0 * datos.pY0
    mfun.i_tabla(' ' , ind , ['Y',]        , dY0                    , True , DECIMALES)
    imprime('Consumo intermedio. X')
    dX0 = X * pz - datos.X0 * datos.pZ0
    mfun.i_tabla(''  , [] , ind             , dX0.T                 , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['suma X',]    , dX0.T.sum(axis=0)     , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    imprime('Consumo de los hogares. Xp')
    dXp0 = Xp * pq - datos.Xp0 * datos.pQ0
    mfun.i_tabla(''  , [] , dem             , dXp0 , False          , DECIMALES)
    mfun.i_tabla(''  , [] , ['suma Xp']    , dXp0.sum(axis=0)      , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    imprime('Consumo del gobierno. Xg')
    dXg0 = Xg * pq - datos.Xg0 * datos.pQ0
    mfun.i_tabla(''  , [] , ['Xg',]        , dXg0                  , False, DECIMALES)
    imprime('Consumo de inversión. Xv')
    dXv0 = Xv * pq - datos.Xv0 * datos.pQ0
    mfun.i_tabla(''  , [] , ['Xv',]        , dXv0                  , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    imprime('Consumo total')
    mfun.i_tabla(''  , [] , ['X+Xp+Xg+Xv',], dXp0.sum(axis=0) + dXg0 + dXv0 + dX0.sum(axis=1), False, DECIMALES)
    imprime('Producción total')
    dQ0 = Q * pq - datos.Q0 * datos.pQ0
    mfun.i_tabla(''  , [] , ['Q',]        , dQ0                    , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    dD0 = Di * pd - datos.D0 * datos.pD0
    mfun.i_tabla(''  , [] , ['D',]        , dD0                    , False, DECIMALES)
    dM0 = M * pm - datos.M0 * datos.pWm * datos.epsilon_ini
    mfun.i_tabla(''  , [] , ['M',]        , dM0                    , False, DECIMALES)
    dE0 = E * pe - datos.E0 * datos.pWe * datos.epsilon_ini
    mfun.i_tabla(''  , [] , ['E',]        , dE0                    , False, DECIMALES)
    dZ0 = Z * pz - datos.Z0 * datos.pZ0
    mfun.i_tabla(''  , [] , ['Z',]        , dZ0                    , False, DECIMALES)
    imprime('Impuestos')
    dTz0 = Tz * pz - datos.Tz0 * datos.pZ0
    mfun.i_tabla(''  , [] , ['Tz',]       , dTz0                   , False, DECIMALES)
    dTm0 = Tm * pm - datos.Tm0 * datos.pWm * datos.epsilon_ini
    mfun.i_tabla(''  , [] , ['Tm',]       , dTm0                   , False, DECIMALES)

    dTd0 = Td - datos.Td0
    mfun.i_tabla('/' , dem, ['Td',]       , dTd0                   , False, DECIMALES)
    dCssH0 = CssH - datos.CssH0
    mfun.i_tabla(''  , [] , ['CssH',]     , dCssH0                 , True , DECIMALES)

    dCssE0 = CssE * pq - datos.CssE0 * datos.pQ0
    mfun.i_tabla('/' , ind, ['CssE',]     , dCssE0                 , True , DECIMALES)
    mfun.i_tabla(''  , [] , ['def/sup ss',], dCssE0.sum() + dCssH0.sum(), False, DECIMALES)
    imprime('Ahorro-Inversión')
    dSp0 = Sp - datos.Sp0
    mfun.i_tabla('/' , dem, ['Sp',]       , dSp0                   , True , DECIMALES)
    dSg0 = Sg - datos.Sg0
    mfun.i_tabla(''  , [] , ['Sg',]       , dSg0                   , False, DECIMALES)
    imprime('Ahorro a largo plazo de los hogares. Alp')
    dAlp0 = Alp - datos.Alp0
    mfun.i_tabla('/' , h                  , dem                    , dAlp0             , True , DECIMALES)
    mfun.i_tabla(''  , []                 , ['suma Alp']           , dAlp0.sum(axis=0) , False, DECIMALES)
    imprime('Pensiones')
    dPssH0 = datos.PssH0 - datos.PssH0
    mfun.i_tabla('/' , dem, ['PssH',]     , dPssH0                 , False, DECIMALES)
    imprime('Ayudas del gobierno')
    dAgH0 = AgH - datos.AgH0
    mfun.i_tabla('/' , dem, ['AgH',]      , dAgH0                  , False, DECIMALES)

    dAgE0 = AgE * pq - datos.AgE0 * datos.pQ0
    mfun.i_tabla('/' , ind, ['AgE',]      , dAgE0                  , True , DECIMALES)
    dSf0 = datos.Sf0 * pq - datos.Sf0 * datos.pQ0
    mfun.i_tabla(''  , [] , ['Sf',]        , dSf0                  , False, DECIMALES)
    
    debp = ebp - b_pini
    mfun.i_tabla(''  , [] , ['bal. pagos',], debp                  , False, DECIMALES)
    dApz0 = Apz - datos.Apz0
    mfun.i_tabla(''  , [] , ['Apz',]      , dApz0                  , False, 5)
    imprime('')
    imprime('')

def datos_grafico_solucion(v):
    res_ecuaciones = sec_ecuaciones(v, False)
    (Apz,Fi,Ei,Mi,Di,
        Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,AgE ,AgH ,CssE ,CssH,ebp,Zl,pz,
        Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,AgEr,AgHr,CssEr,CssHr,ebpr
    ) = res_ecuaciones
    pf = extrae_var(v,'pF', 0, nfac - 1)
    if OR_PRE_REFERENCIA == 1:
        # Como el vector de prueba no incluye el precio del último factor, añadimos el precio del último factor con valor 'PRECIO_F_REFERENCIA'
        pf = np.append(pf, np.array([PRECIO_F_REFERENCIA]), axis=0)
    else:
        # Como el vector de prueba no incluye el precio del primer factor, insertamos al principio (0) el precio del primer factor con valor 'PRECIO_F_REFERENCIA'
        pf = np.insert(pf, 0, np.array([PRECIO_F_REFERENCIA]), axis=0)
    py = extrae_var(v,'pY', 0, nsec)
    pq = extrae_var(v,'pQ', 0, nsec)
    pd = extrae_var(v,'pD', 0, nsec)
    eP = extrae_var(v,'epsilon', 0, 0)
    (pe, pm) = exte.precio_moneda_local_pe_pm(datos.pWe, datos.pWm, eP)
    y_pre = np.concatenate((
        pf.flatten(),
        py.flatten(),
        pz.flatten(),
        pd.flatten(),
        pq.flatten(),
        [eP]
    ))
    y_can = np.concatenate((
        Z.flatten(),
        E.flatten(),
        Da.flatten(),
        M.flatten(),
        Q.flatten()
    ))
    y_imp = np.concatenate((
        (Z  * pz).flatten(),
        (E  * pe).flatten(),
        (Da * pd).flatten(),
        (M  * pm).flatten(),
        (Q  * pq).flatten()
    ))
    # variación de los factores suministrados por los hogares
    y_sfc_c = FF[0] - datos.FF0[0]
    y_sfc_i = (FF[0] - datos.FF0[0]) * pf
    for i in range(1, ndem):
        y_sfc_c = np.concatenate((
            y_sfc_c,
            FF[i] - datos.FF0[i]
        )) 
        y_sfc_i = np.concatenate((
            y_sfc_i,
            (FF[i] - datos.FF0[i]) * pf
        )) 
    # variación de los factores utilizados por los sectores
    y_ufc_c = F[0] - datos.F0[0]
    y_ufc_i = (F[0] - datos.F0[0]) * pf
    for i in range(1, nsec):
        y_ufc_c = np.concatenate((
            y_ufc_c,
            F[i] - datos.F0[i]
        )) 
        y_ufc_i = np.concatenate((
            y_ufc_i,
            (F[i] - datos.F0[i]) * pf
        )) 
    return (y_pre, y_can, y_imp, y_sfc_c, y_ufc_c, y_sfc_i, y_ufc_i)

def grafico_evolucion(n_filas_img, n_cols_img, x, y, y_ref, v_marca_x, etq_x, titulo, sufijo):
    if n_filas_img == 1:
        # asegurar un mosaico de gráficos con dos dimensiones
        n_filas_img = 2
    fig, axes = plt.subplots(nrows=n_filas_img, ncols=n_cols_img, figsize=(24, 12), sharey=True)
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    plt.rcParams.update({'font.size': 12})
    nimg = len(y)
    ymax = max(np.max(y), np.max(y_ref)) * 1.05
    yt = min(np.min(y), np.min(y_ref))
    franja = (ymax - yt) / 12.
    ymin = yt - franja
    if ymin == ymax:
        # normalmente será porque todos los valores son cero
        ymin = -0.5
        ymax =  0.5
    y_etq_x = ymin + (ymax - ymin) * 0.01
    m = 0
    for fil in range(n_filas_img):
        for col in range(n_cols_img):
            axes[fil, col].scatter(x, y_ref , s=44, c='aquamarine', marker='s')
            axes[fil, col].scatter(x, y[m], s=16, c='0'         , marker='o')
            vmin = np.min(y[m])
            vmax = np.max(y[m])
            if abs(vmin) > 100:
                vmin = '{:d}'.format(round(vmin))
            else:
                vmin = '{:.3f}'.format(round(vmin,3))
            if abs(vmax) > 100:
                vmax = '{:d}'.format(round(vmax))
            else:
                vmax = '{:.3f}'.format(round(vmax,3))
            axes[fil, col].title.set_text('{}   [{}  {}]'.format(titulo[m], vmin, vmax))
            axes[fil, col].vlines(x=v_marca_x, ymax=ymax, ymin=ymin, colors='black', linewidth=1)
            if ymin < 0:
                axes[fil, col].axhline(y=0, xmin=0, xmax=1, c='grey', linewidth=1)
            for i in range(len(etq_x)):
                axes[fil, col].annotate(etq_x[i], xy=(v_marca_x[i] + 0.2, y_etq_x))
            axes[fil, col].set_ylim(ymin, ymax)
            axes[fil, col].set_xticks([])
            axes[fil, col].title.set_size(16)
            axes[fil, col].tick_params(axis='both', which='major', labelsize=12)
            axes[fil, col].yaxis.get_major_formatter().set_scientific(False)
            m += 1
            if m == nimg:
                break;
        if m == nimg:
            break;
    fig.tight_layout()
    plt.savefig('{}_{}.png'.format(FICHERO_IMG, sufijo), dpi = 300, facecolor = 'w', edgecolor = 'w', orientation = 'portrait', format = 'png', transparent = False, bbox_inches = None, pad_inches = 0.1, metadata = None)
    plt.close()

def grafico_resumen(x, y, ref, v_marca_x, etq_x, titulo):
    n_filas_img = 3
    n_cols_img  = 1
    fig, axes = plt.subplots(nrows=n_filas_img, ncols=n_cols_img, figsize=(18, 24))
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    plt.rcParams.update({'font.size': 24})
    nimg = len(y)
    ymin = []
    ymax = []
    yli  = []
    for i in range(3):
        ymaxt = max(np.max(y[i]), np.max(ref[i])) * 1.05
        yt = min(np.min(y[i]), np.min(ref[i]))
        franja = (ymaxt - yt) / 12.
        ymint = yt - franja
        if ymint == ymaxt:
            # normalmente será porque todos los valores son cero
            ymint = -0.5
            ymaxt =  0.5
        ymin.append(ymint)
        ymax.append(ymaxt)
        yli.append (ymin[i] + (ymax[i] - ymin[i]) * 0.008)
    m = 0
    for fil in range(n_filas_img):
        for col in range(n_cols_img):
            axes[m].scatter(x[m], ref[m] , s=120, c='aquamarine', marker='s')
            axes[m].scatter(x[m], y[m], s=72, c='0'         , marker='o')
            axes[m].title.set_text(titulo[m])
            axes[m].vlines(x=v_marca_x[m], ymax=ymax[m], ymin=ymin[m], colors='black', linewidth=1)
            if ymin[m] < 0:
                axes[m].axhline(y=0, xmin=0, xmax=1, c='grey', linewidth=1)
            for i in range(len(etq_x[m])):
                axes[m].annotate(etq_x[m][i], xy=(v_marca_x[m][i] + 0.2, yli[m]))
            axes[m].set_ylim(ymin[m], ymax[m])
            axes[m].set_xticks([])
            axes[m].title.set_size(32)
            axes[m].tick_params(axis='both', which='major', labelsize=24)
            axes[m].yaxis.get_major_formatter().set_scientific(False)
            m += 1
            if m == nimg:
                break;
        if m == nimg:
            break;
    fig.tight_layout()
    plt.savefig('{}_Res.png'.format(FICHERO_IMG), dpi = 300, facecolor = 'w', edgecolor = 'w', orientation = 'portrait', format = 'png', transparent = False, bbox_inches = None, pad_inches = 0.1, metadata = None)
    plt.close()

# rótulos para los resultados de verificar la factibilidad de las ecuaciones
etq_veri = [
        ' 1.Yp  6. 1',
        ' 2.F   6. 2',
        ' 3.X   6. 3',
        ' 4.Yd  6. 4',
        ' 5.pz a6. 5',
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
        '21.Css E',
        '22.Css D',
        '23.AgE E',
        '24.AgH D',
        '25.Qeq 6.23',
        '26.Feq 6.24',
]
# rótulos para componer los rótulos de los precios incluidos en las soluciones 'etq_precios'
vetq_sol = [
        'pF',
        'pY',
        'pQ',
        'pD',
        'epsilon',
]
etq_precios = []
# precios de los factores
if OR_PRE_REFERENCIA == 1:
    # sin el precio del último factor
    for i in range(nfac - 1):
        etq_precios.append(vetq_sol[0] + '_' + h[i])
else:
    # sin el precio del primer factor
    for i in range(1, nfac):
        etq_precios.append(vetq_sol[0] + '_' + h[i])
# precios pY, pQ y pD
for i in range(3):
    for k in range(nsec):
        etq_precios.append(vetq_sol[i+1] + '_' + ind[k])
# epsilon
etq_precios.append(vetq_sol[4])
npre_sol = len(etq_precios)
for k in range(nsec):
    etq_precios.append('pZ_' + ind[k])
for k in range(nsec):
    etq_precios.append('pE_' + ind[k])
for k in range(nsec):
    etq_precios.append('pM_' + ind[k])
global datos
global parametros
if __name__ == '__main__':
    # necesitamos este control porque el uso de workers en Windows reinicia el programa desde el
    # principio para cada worker y así evitamos que se impriman estos textos tantas veces como workers, ya que el
    # '__name__' de los reinicios no es igual a '__main__', la asignación de variables hay que repetirla
    # en todos los workers por eso deben quedar fuera de este contol.
    # encontraremos este control en númerosdos puntos de la aplicación
    imprime('python           {}'.format(sys.version))
    imprime('numpy            {}'.format(np.__version__))
    imprime('scipy            {}'.format(scipy.__version__))
    imprime('pandas           {}'.format(pd.__version__))
    imprime('matplotlib       {}'.format(matplotlib.__version__))
    imprime('')
    imprime('####################################################')
    imprime('Modelo MEGA ampliado. versión {:6} ---------------'.format(VERSION))
    imprime('####################################################')
    imprime('----------------------------------------------------')
    imprime(CASO)
    imprime('----------------------------------------------------')
    imprime('')
    imprime('Fichero Matriz Contabilidad Social (MCS) {}'.format(FICHERO_SAM))
'''
el fichero calibrado.py contiene dos clases que, como cualquier clase, ejecutan el procedimiento
'def __init__' cuando se crea una variable de la clase:
    datos     : la función 'def __init__' de esta clase crea una serie de variables y les asigna
                valores de acuerdo a la información leida de la MCS.
    parametros: la función 'def __init__' de esta clase crea unas variables que son los parámetros
                de las funciones de utilidad y les calcula unos valores de acuerdo a las
                ecuaciones que se deducen de las funciones de utilidad-producción,
                es decir, calibra el modelo.
'''
# leemos la Matriz de contabilidad social (sam) de esta economía
sam = pd.read_excel(FICHERO_SAM, index_col=0, header=0)
datos = calibrado.datos(sam, h, ind, dem, idt, trf, gov, retg, inv, ext, css)
parametros = calibrado.parametros(datos, ndem, nsec, INDICE_F_TRA)
if __name__ == '__main__':
    imprime('')
    if SAL_CALIBRADO:
        salida_calibrado(parametros)

# punteros para extraer variables del vector solución
(etq_vec_opt,ind_pvec_desde,ind_pvec_hasta) = punteros()

# balace de pagos inicial
b_pini = exte.balance_pagos_moneda_extranjera(datos.pWe, datos.E0, datos.pWm, datos.M0, datos.Sf0)     # 6.16

# ---------------------------------------------------------------------
# Solucíonar el MEGA
# ---------------------------------------------------------------------
# NCASO selecciona el escenario a calcular, los escenarios se han elegido sin más sentido que el de probar la aplicación 
if __name__ == '__main__':
    if abs(DEM_ADICIONAL).sum() != 0:
        imprime('Demanda adicional')
        mfun.i_tabla(''  , [] , dem             , DEM_ADICIONAL, False     , DECIMALES)
        imprime('')
    if abs(AYD_ADICIONAL).sum() != 0:
        imprime('Ayudas adicionales')
        mfun.i_tabla(''  , [] , dem             , AYD_ADICIONAL, False     , DECIMALES)
        imprime('')
if NCASO > 0:
    if __name__ == '__main__':
        imprime('---------------------------------------------------------------------------------------------------')
        imprime('Escenario')
        imprime('---------------------------------------------------------------------------------------------------')
    if   NCASO == 1:
        if __name__ == '__main__':
            imprime('Elasticidad de la demanda (alfa) calibrado / escenario')
            mfun.tabla_2D(dem, parametros.alfa)
            imprime('')

        for i in range(ndem):
            for j in range(nsec):
                parametros.alfa[i,j] = 1.0 / nsec

        if __name__ == '__main__':
            mfun.tabla_2D(dem, parametros.alfa)
    elif NCASO == 2:
        if __name__ == '__main__':
            imprime('Elasticidad de la producción (beta) calibrado / escenario')
            mfun.tabla_2D(ind, parametros.beta)
            imprime('')

        for i in range(nsec):
            for j in range(nfac):
                parametros.beta[i,j] = 0.5

        if __name__ == '__main__':
            mfun.tabla_2D(ind, parametros.beta)
    elif NCASO == 3:
        if __name__ == '__main__':
            imprime('Aranceles de importación (taum) calibrado / escenario')
            mfun.tabla_2D(['Productos',], datos.taum)
            imprime('')

        for i in range(nsec):
            datos.taum[i] = 0.

        if __name__ == '__main__':
            mfun.tabla_2D(['Productos',], datos.taum)
    elif NCASO == 4:
        if __name__ == '__main__':
            imprime('Aranceles de importación (taum) calibrado / escenario')
            mfun.tabla_2D(['Productos',], datos.taum)
            imprime('')

        for i in range(nsec):
            if datos.taum[i] > 0:
                datos.taum[i] *= 2.
            else:
                # si previamente no hay aranceles se fijan en el 10%
                datos.taum[i] = 0.10

        if __name__ == '__main__':
            mfun.tabla_2D(['Productos',], datos.taum)
    elif NCASO == 5:
        if __name__ == '__main__':
            imprime('Precios')
            for i in range(nfac):
                imprime('{:9.5f}'.format(datos.pF0[i]))
            for i in range(nsec):
                imprime('{:9.5f}'.format(datos.pY0[i]))
                imprime('{:9.5f}'.format(datos.pZ0[i]))
                imprime('{:9.5f}'.format(datos.pQ0[i]))
                imprime('{:9.5f}'.format(datos.pD0[i]))
            imprime('{:9.5f}'.format(datos.epsilon))
            imprime('')

        for i in range(nfac):
            datos.pF0[i] = PRECIO_INI
        for i in range(nsec):
            datos.pY0[i]  = PRECIO_INI
            datos.pZ0[i]  = PRECIO_INI
            datos.pQ0[i]  = PRECIO_INI
            datos.pD0[i]  = PRECIO_INI
            datos.epsilon = PRECIO_INI

        if __name__ == '__main__':
            for i in range(nfac):
                imprime('{:9.5f}'.format(datos.pF0[i]))
            for i in range(nsec):
                imprime('{:9.5f}'.format(datos.pY0[i]))
                imprime('{:9.5f}'.format(datos.pZ0[i]))
                imprime('{:9.5f}'.format(datos.pQ0[i]))
                imprime('{:9.5f}'.format(datos.pD0[i]))
            imprime('{:9.5f}'.format(datos.epsilon))
    elif NCASO == 6:
        if __name__ == '__main__':
            # factores aportados por cada consumidor
            imprime('Factores')
            mfun.i_tabla('FF0',h , dem, datos.FF0, False, DECIMALES)
            imprime('')
        if np.issubdtype(type(VAR_FACTORES), np.floating):
            # un multiplicador 
            datos.FF0 *= VAR_FACTORES
        else:
            # valores concretos
            datos.FF0 += VAR_FACTORES

        if __name__ == '__main__':
            # factores aportados por cada consumidor
            imprime('Factores escenario')
            mfun.i_tabla('FF0',h , dem, datos.FF0, False, DECIMALES)
    elif NCASO == 7:
        if __name__ == '__main__':
            imprime('Propensión al ahorro')
            for et in dem:
                imprime('{:4} {:9.5f}'.format(et, parametros.ssp[0]))
            imprime('')

        parametros.ssp[0] = parametros.ssp[0] / 2.

        if __name__ == '__main__':
            for et in dem:
                imprime('{:4} {:9.5f}'.format(et, parametros.ssp[0]))
    elif NCASO == 8:
        if __name__ == '__main__':
            imprime('Seguridad social')
            mfun.i_tabla('/' , dem, ['CssH',], parametros.ctzssh, False, 5)
            mfun.i_tabla('/' , ind, ['CssE',], parametros.ctzsse, False, 5)
            imprime('')

        parametros.ctzssh *= FACTOR_CSSH
        parametros.ctzsse *= FACTOR_CSSE

        if __name__ == '__main__':
            imprime('Seguridad social')
            mfun.i_tabla('/' , dem, ['CssH',], parametros.ctzssh, False, 5)
            mfun.i_tabla('/' , ind, ['CssE',], parametros.ctzsse, False, 5)
    elif NCASO == 9:
        if __name__ == '__main__':
            imprime('Elasticidad de la demanda (alfa) calibrado')
            mfun.tabla_2D(dem, parametros.alfa)
            imprime('')

        # modificar preferencias (alfa) de consumo con la demanda adicional
        Xp0 = datos.Xp0 + DEM_ADICIONAL
        parametros.alfa = ecua.CobbDouglas_alfa(Xp0)
        
        # para evitar que se sume el efecto en preferencia con el incremento de demanda
        DEM_ADICIONAL.fill(0.)

        if __name__ == '__main__':
            imprime('Elasticidad de la demanda (alfa) escenario')
            mfun.tabla_2D(dem, parametros.alfa)
            imprime('---------------------------------------------------------------------------------------------------')
            imprime('Demanda adicional no suma en consumos')
    elif NCASO == 10:
        if __name__ == '__main__':
            imprime('Elasticidad de la demanda (alfa) calibrado')
            mfun.tabla_2D(dem, parametros.alfa)
            imprime('Factores')
            mfun.i_tabla('FF0'  , h   , dem, datos.FF0, False, DECIMALES)    # factores aportados por cada consumidor
            imprime('Tasa de cotización a la seguridad social de los hogares')
            mfun.i_tabla('ctzssh', dem , dem, parametros.ctzssh, False, 6) 
            imprime('')

        # modificar preferencias (alfa) de consumo con la demanda adicional
        Xp0 = datos.Xp0 + DEM_ADICIONAL
        parametros.alfa = ecua.CobbDouglas_alfa(Xp0)

        # incrementar factores en proporción a la demanda adicional
        inc_factor = np .zeros((nsec,nfac), dtype=np.float64)
        for i in range(ndem):
            for j in range(nfac):
                for k in range(nsec):
                    if datos.F0[k].sum() != 0:
                        # proporcional a los factores utilizados por el sector 'k', 'datos.F0[k,j] / datos.F0[k].sum()'
                        inc_factor[k,j] = DEM_ADICIONAL[i,k] * datos.F0[k,j] / datos.F0[k].sum()
                    else:
                        # todos los factores utilizados por el sector 'k' por igual 
                        inc_factor[k,j] = DEM_ADICIONAL[i,k] / np.float64(j)
                    datos.FF0[i,j] += inc_factor[k,j]
        '''
        esto es incorrecto, un sector individualmente no necesita un incremento de factores igual al de la demanda
        aunque dará los mismos resultados porque F se adaptará a Z y a FF
        datos.F0 += inc_factor
        '''
        '''        
        # primer término de producciones inducidas
        for i1 in range(ndem):
            print(i)
            for j1 in range(nfac):
                for k1 in range(nsec):
                    # compras inducidas por k1 en todos los sectores (k2)
                    print(i)
                    for k2 in range(nsec):
                        datos.FF0[i1,j1] += incf[k1,j1] * parametros.ax[k1,k2]
        '''
        # como no hay cotizacción a la seguridad social de C2, se le pone la de C1
        parametros.ctzssh[1] = parametros.ctzssh[0]
        
        # para evitar que se sume el efecto en preferencia con el incremento de demanda
        DEM_ADICIONAL.fill(0.)

        if __name__ == '__main__':
            imprime('Elasticidad de la demanda (alfa) escenario')
            mfun.tabla_2D(dem, parametros.alfa)
            imprime('Factores escenario')
            mfun.i_tabla('FF0'  , h   , dem, datos.FF0, False, DECIMALES)    # factores aportados por cada consumidor
            imprime('Tasa de cotización a la seguridad social de los hogares')
            mfun.i_tabla('ctzssh', dem , dem, parametros.ctzssh, False, 6) 
            imprime('---------------------------------------------------------------------------------------------------')
            imprime('Demanda adicional no suma en consumos')
    elif NCASO == 11:
        # sin modificar preferencias (alfa) de consumo
        # no se anula el incremento de demanda porque no se modifican los alfa
        if __name__ == '__main__':
            imprime('Factores calibrado')
            mfun.i_tabla('FF0',h , dem, datos.FF0, False, DECIMALES)    # factores aportados por cada consumidor
            imprime('')
            if parametros.ctzssh[1] == 0:
                imprime('Seguridad social')
                imprime('{:4} {:9.5f}'.format(dem[1], parametros.ctzssh[1]))
            imprime('')

        # incrementar factores en proporción a la demanda adicional
        for i in range(ndem):
            for j in range(nfac):
                for k in range(nsec):
                    if datos.F0[k].sum() != 0:
                        # proporcional a los factores utilizados por el sector 'k'
                        datos.FF0[i,j] += COE_VAB[k] * DEM_ADICIONAL[i,k] * datos.F0[k,j] / datos.F0[k].sum()
                    else:
                        # todos los factores utilizados por el sector 'k' por igual 
                        datos.FF0[i,j] += COE_VAB[k] * DEM_ADICIONAL[i,k] / np.float64(j)

        # como no hay cotizacción a la seguridad social de C2, se le pone la de C1
        if parametros.ctzssh[1] == 0:
            parametros.ctzssh[1] = 0.062897 

        if __name__ == '__main__':
            imprime('Factores escenario')
            mfun.i_tabla('FF0'  , h   , dem, datos.FF0, False, DECIMALES)    # factores aportados por cada consumidor
            if parametros.ctzssh[1] == 0:
                imprime('Seguridad social')
                imprime('{:4} {:9.5f}'.format(dem[1], parametros.ctzssh[1]))
    elif NCASO == 12:
        if __name__ == '__main__':
            imprime('Elasticidad de la demanda (alfa) calibrado')
            mfun.tabla_2D(dem, parametros.alfa)
            imprime('')

        # modificar preferencias (alfa) de consumo
        Xp0 = datos.Xp0 + AYD_ADICIONAL
        parametros.alfa = ecua.CobbDouglas_alfa(Xp0)

        if __name__ == '__main__':
            imprime('Elasticidad de la demanda (alfa) escenario')
            mfun.tabla_2D(dem, parametros.alfa)
    else:
        imprime('Número de caso {} incorrecto'.format(NCASO))
        sys.exit
    if __name__ == '__main__':
        imprime('---------------------------------------------------------------------------------------------------')
        imprime('')
global iteracion
iteracion = 0

if __name__ == '__main__':
    # sin el precio del último factor ya que su valor se fija de forma exógena
    pf0 = datos.pF0[0:nfac-1].flatten()
    # sólución inicial para la función minimizar
    vec_opt = np.concatenate((
                pf0,                        # precio de los factores
                datos.pY0.flatten(),        # precio del factor compuesto
                datos.pQ0.flatten(),        # precio del producto de Armington
                datos.pD0.flatten(),        # precio de los sectores para la demanda
                np.array([datos.epsilon]),  # tipo de cambio
                np.array([datos.Apz0]),     # ajuste pseudo impuestos
                datos.F0.flatten(),
                datos.E0.flatten(),
                datos.M0.flatten(),
                datos.D0.flatten(),
    ))

    vec_opt_ini = copy.deepcopy(vec_opt)
    pzi = copy.deepcopy(datos.pZ0)
    valores_iniciales(vec_opt)
    imprime('-------------------------------------------------------------------')
    imprime('-------------------------------------------------------------------')
    imprime('MEGA mediante algoritmo genético')
    imprime('Aportación de factores por los hogares {}'.format('ENDOGENA' if FF_ENDOGENA else 'exógena'))
    imprime('Ahorro a largo plazo de los hogares    {}'.format('Si' if AHORRO_L_PLAZO else 'No'))
    imprime('Rango de validez de los precios en % -{:9.1f} +{:9.1f}'.format(100. * (GE_PRE_MIN - 1.), 100. * (GE_PRE_MAX - 1.)))
    imprime('Rango de validez de las variables  % -{:9.1f} +{:9.1f}'.format(100. * (GE_VAR_MIN - 1.), 100. * (GE_VAR_MAX - 1.)))
    imprime('Rango de validez de las variables  0 -{:9.1f} +{:9.1f}'.format(GE_VAR_CERO, GE_VAR_CERO))
    imprime('Estrategia                       : {}'.format(METODO_MIN))
    imprime('Periodicidad actualización       : {}'.format(GE_ACTUALIZACION))
    imprime('Recombinación                    {:10.3f}'.format(GE_RECONBINACION))
    imprime('Tamaño de la población           {:10}'.format(GE_DIM_POBLACION))
    imprime('Número de workers                {:10}'.format(GE_WORKERS))
    imprime('Tolerancia en el objetivo        {:10.3e}'.format(GE_TOLERANCIA))
    imprime('Tolerancia en las verificaciones {:10.3e}'.format(GE_VERIFICAR))
    imprime('Número máximo de iteraciones     {:10,}'.format(GE_MAX_ITER))
    imprime('Iteraciones para historial       {:10,}'.format(GE_HISTORIAL))
    imprime('Iteraciones para soluciones      {:10,}'.format(GE_SOLUCIONES))
    imprime('Semilla números aleatorios       {:10}'.format(GE_SEMILLA))
    imprime('Dimensión del vector de prueba   {:10}'.format(len(vec_opt)))
    if   METRICA_ERROR == 0:
        imprime('Métrica del error: Error cuadrático medio')
    elif METRICA_ERROR == 1:
        imprime('Métrica del error: Valor absoluto')
    else:
        imprime('Métrica del error: Desvios elevados a {}'.format(POT_DESVIOS))
    imprime('El precio del factor {} es variable exógena con valor igual a {}'.format(h[OR_PRE_REFERENCIA], PRECIO_F_REFERENCIA))
    if VALOR_F_TRA != -1:
        imprime('El precio del factor {} es fijo con valor igual a {}'.format(h[INDICE_F_TRA], VALOR_F_TRA))
    imprime('-------------------------------------------------------------------')
    imprime('-------------------------------------------------------------------')
    imprime('')

    iteracion = 0
    # se prepara el vector que se pasará como parámetro a la función 'veri_solucion'
    ebp = exte.balance_pagos_moneda_extranjera(datos.pWe, datos.E0, datos.pWm, datos.M0, datos.Sf0)
    vec_veri_sol = (
                datos.pF0,
                datos.pY0,
                datos.pZ0,
                datos.pQ0,
                datos.pD0,
                datos.epsilon,
                datos.Apz0,
                datos.F0,
                datos.Z0,
                datos.E0,
                datos.M0,
                datos.D0,
                datos.FF0,
                datos.Y0,
                datos.X0,
                datos.Xp0,
                datos.Xg0,
                datos.Xv0,
                datos.Q0,
                ebp,
                datos.Sp0,
                datos.Sg0,
                datos.Td0,
                datos.Tz0,
                datos.Tm0,
                datos.CssE0,
                datos.CssH0,
                datos.AgE0,
                datos.AgH0,
                datos.Alp0,
    )
    vec_veri_sol_ini = copy.deepcopy(vec_veri_sol)
    # verifica solución
    veri_solucion(vec_veri_sol, 'Verifica con los valores iniciales', GE_VERIFICAR)
    imprime('')
    if PRIMERA_VALORACION:
        imprime('Una primera valoración del modelo')
        imprime('---------------------------------')
        res_ecuaciones = sec_ecuaciones(vec_opt, True)
        (Apz,Fi,Ei,Mi,Di,
            Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,AgE ,AgH ,CssE ,CssH,ebp,Zl,pz,
            Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,AgEr,AgHr,CssEr,CssHr,ebpr
        ) = res_ecuaciones
        # verificar la solución
        pf = extrae_var(vec_opt,'pF', 0, nfac - 1)
        if OR_PRE_REFERENCIA == 1:
            # Como el vector de prueba no incluye el precio del último factor, añadimos el precio del último factor con valor 'PRECIO_F_REFERENCIA'
            pf = np.append(pf, np.array([PRECIO_F_REFERENCIA]), axis=0)
        else:
            # Como el vector de prueba no incluye el precio del primer factor, insertamos al principio (0) el precio del primer factor con valor 'PRECIO_F_REFERENCIA'
            pf = np.insert(pf, 0, np.array([PRECIO_F_REFERENCIA]), axis=0)
        py = extrae_var(vec_opt,'pY', 0, nsec)
        pq = extrae_var(vec_opt,'pQ', 0, nsec)
        pd = extrae_var(vec_opt,'pD', 0, nsec)
        eP = extrae_var(vec_opt,'epsilon', 0, 0)
        vec_veri_sol = (
                    pf,
                    py,
                    pz,
                    pq,
                    pd,
                    eP,
                    Apz,
                    F,
                    Z,
                    E,
                    M,
                    Da,
                    FF,
                    Yp,
                    X,
                    Xp,
                    Xg,
                    Xv,
                    Q,
                    ebp,
                    Sp,
                    Sg,
                    Td,
                    Tz,
                    Tm,
                    CssE,
                    CssH,
                    AgE,
                    AgH,
                    Alp,
        )
        veri_solucion(vec_veri_sol,'Verifica en la primera valoración', GE_VERIFICAR)
        imprime('')
        imprime('---------------------------------')
        imprime('')

    t_inicio = timer()
    print('Evolución de la minimización')
    print('')
    historial = []
    soluciones = []

    # función que 'differential_evolution' llamará despues de probar cada posible solución 
    def vigila(intermediate_result):
        vf  = intermediate_result.fun   # valor de la función objetivo
        nit = intermediate_result.nit   # número de iteraciones
        if GE_HISTORIAL > 0 and nit == 1 or (nit % GE_HISTORIAL == 0):
            # guardar el valor del error que, al final, se escribirá en un fichero CSV
            historial.append([nit,vf])
            print('{:9} {:12.5e}'.format(nit, vf))
        if GE_SOLUCIONES > 0 and nit == 1 or (nit % GE_SOLUCIONES == 0):
            # guardar el vector solución que, al final, se escribirá en un fichero CSV
            soluciones.append([nit,intermediate_result.x])
        if vf < GE_TOLERANCIA:
            #historial.append([nit,vf])
            #print('{:9} {:12.5e}'.format(nit, vf))
            # El desvio de la función objetivo es inferior al valor establecido, por lo que se da por terminada la minimización
            raise StopIteration

    # definir el rango de variación de los precios y variables
    bnds = []
    for i in range(npre_sol):
        if OR_PRE_REFERENCIA != INDICE_F_TRA and i == 0 and VALOR_F_TRA != -1:
            vi = VALOR_F_TRA
            vs = VALOR_F_TRA
        else:
            v = vec_opt[i]
            if abs(v) < GE_TOLERANCIA:
                # para evitar que los precios inicialmente a 0 queden acotados a (0,0)
                vi = 0.
                vs = 3.
            else:
                vi = v / GE_PRE_MIN
                vs = v * GE_PRE_MAX
        bnds.append((vi,vs))
    for i in range(npre_sol,len(vec_opt)):
        v = vec_opt[i]
            # para evitar que las variables inicialmente a 0 queden acotadas a (0,0)
        if abs(v) < 0.001:
            vi = -GE_VAR_CERO
            vs = +GE_VAR_CERO
        else:
            vi = v / GE_VAR_MIN
            vs = v * GE_VAR_MAX
        bnds.append((vi,vs))

    # minimizar el error de la función objetivo
    if GE_WORKERS > 1:
        rmin = differential_evolution(func=fun_objetivo,
                x0=vec_opt,
                bounds=bnds,
                strategy=METODO_MIN,
                popsize=GE_DIM_POBLACION,   # 15 es por defecto, 3 es mucho más rápido
                #mutation=1., 
                tol=GE_TOLERANCIA,
                disp=False,
                callback=vigila,
                maxiter=GE_MAX_ITER,
                updating=GE_ACTUALIZACION,
                #vectorized=6,
                workers=GE_WORKERS,         # en WINDOWS funciona de aquella manera
                recombination=GE_RECONBINACION,
                seed=GE_SEMILLA
        )
    else:
        rmin = differential_evolution(func=fun_objetivo,
                x0=vec_opt,
                bounds=bnds,
                strategy=METODO_MIN,
                popsize=GE_DIM_POBLACION,   # 15 es por defecto, 3 es mucho más rápido
                #mutation=1., 
                tol=GE_TOLERANCIA,
                disp=False,
                callback=vigila,
                maxiter=GE_MAX_ITER,
                updating=GE_ACTUALIZACION,
                #vectorized=6,
                recombination=GE_RECONBINACION,
                seed=GE_SEMILLA
        )

    t_fin = timer()
    sol = rmin.x
    imprime('Valoración final')
    imprime('')
    res_ecuaciones = sec_ecuaciones(sol, True)
    dist = calcula_desvios(res_ecuaciones, True)
    (Apz,Fi,Ei,Mi,Di,
        Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,AgE ,AgH ,CssE ,CssH,ebp,Zl,pz,
        Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,AgEr,AgHr,CssEr,CssHr,ebpr
    ) = res_ecuaciones

    if GE_HISTORIAL > 0:
        # guardar el valor del error que, al final, se escribirá en un fichero CSV
        historial.append([rmin.nit,dist])
    if GE_SOLUCIONES > 0:
        # guardar el vector solución que, al final, se escribirá en un fichero CSV
        soluciones.append([rmin.nit,sol])
    if SAL_GRAFICOS:
        # generar gráfico
        print('')
        print('Generando gráficos ...')
        print('')
        nsol = len(soluciones)
        ncol = GE_IMG_COL
        nimg = GE_IMG_FIL * GE_IMG_COL
        if nimg > nsol:
            nfil = nsol // ncol
            if nfil * ncol < nsol:
                nfil += 1
            nimg = nfil * ncol
        else:
            nfil = GE_IMG_FIL
        nimg_real = min(nimg, nsol)
        titulo  = []
        y_pre   = []
        y_can   = []
        y_imp   = []
        y_sfc_c = []
        y_ufc_c = []
        y_sfc_i = []
        y_ufc_i = []
        n       = 0
        for v in soluciones[0:nimg_real]:
            titulo.append(n * GE_SOLUCIONES)
            n += 1
            (y1, y2, y3, y4, y5, y6, y7) = datos_grafico_solucion(v[1])
            y_pre.append(y1)
            y_can.append(y2)
            y_imp.append(y3)
            y_sfc_c.append(y4)
            y_ufc_c.append(y5)
            y_sfc_i.append(y6)
            y_ufc_i.append(y7)
        x_sol   = []
        ref_sol = []
        vli_sol = []
        eli_sol = []

        # parrilla (mosaico de gráficos) de precios
        etq_x = ['pF','pY','pZ','pD','pQ','Cz']
        x   = []
        for i in range(len(y_pre[0])):
            x.append(i + 1)
        ref_y = np.concatenate((
            datos.pF0.flatten(),
            datos.pY0.flatten(),
            datos.pZ0.flatten(),
            datos.pD0.flatten(),
            datos.pQ0.flatten(),
            [datos.epsilon]
        ))
        v_marca_x = []
        p = 0.5
        v_marca_x.append(p)
        p += len(pf)
        v_marca_x.append(p)
        p += len(py)
        v_marca_x.append(p)
        p += len(pz)
        v_marca_x.append(p)
        p += len(pd)
        v_marca_x.append(p)
        p += len(pq)
        v_marca_x.append(p)

        # para precios de la última solución
        x_sol.append(x)
        ref_sol.append(copy.deepcopy(ref_y))
        vli_sol.append(copy.deepcopy(v_marca_x))
        eli_sol.append(copy.deepcopy(etq_x))

        grafico_evolucion(nfil, ncol, x, y_pre, ref_y, v_marca_x, etq_x, titulo, 'Pre')

        # parrillas (mosaico de graficos) de cantidades e importes
        etq_x = ['Z','E','D','M','Q']
        x  = []
        for i in range(len(y_can[0])):
            x.append(i + 1)
        ref_y = np.concatenate((
            datos.Z0.flatten(),
            datos.E0.flatten(),
            datos.D0.flatten(),
            datos.M0.flatten(),
            datos.Q0.flatten()
        ))
        v_marca_x = []
        p = 0.5
        v_marca_x.append(p)
        p += len(Z)
        v_marca_x.append(p)
        p += len(E)
        v_marca_x.append(p)
        p += len(Da)
        v_marca_x.append(p)
        p += len(M)
        v_marca_x.append(p)

        # para cantidades e importes de la última solución
        x_sol.append(copy.deepcopy(x))
        x_sol.append(copy.deepcopy(x))
        ref_sol.append(copy.deepcopy(ref_y))
        ref_sol.append(copy.deepcopy(ref_y))
        vli_sol.append(copy.deepcopy(v_marca_x))
        vli_sol.append(copy.deepcopy(v_marca_x))
        eli_sol.append(copy.deepcopy(etq_x))
        eli_sol.append(copy.deepcopy(etq_x))

        grafico_evolucion(nfil, ncol, x, y_can, ref_y, v_marca_x, etq_x, titulo, 'Ctd')
        grafico_evolucion(nfil, ncol, x, y_imp, ref_y, v_marca_x, etq_x, titulo, 'Imp')

        # parrillas (mosaico de graficos) variaciones en el suministro de factores
        etq_x = dem
        x  = []
        for i in range(len(y_sfc_c[0])):
            x.append(i + 1)
        ref_y = np.zeros((ndem * nfac),dtype=np.float64)
        v_marca_x = []
        p = 0.5
        for i in range(ndem):
            v_marca_x.append(p)
            p += nfac
        grafico_evolucion(nfil, ncol, x, y_sfc_c, ref_y, v_marca_x, etq_x, titulo, 'VsFc')
        grafico_evolucion(nfil, ncol, x, y_sfc_i, ref_y, v_marca_x, etq_x, titulo, 'VsFi')

        # parrillas (mosaico de graficos) variaciones en el uso de factores
        etq_x = ind
        x  = []
        for i in range(len(y_ufc_c[0])):
            x.append(i + 1)
        v_marca_x = []
        p = 0.5
        for i in range(nsec):
            v_marca_x.append(p)
            p += nfac
        ref_y = np.zeros((nsec * nfac),dtype=np.float64)
        grafico_evolucion(nfil, ncol, x, y_ufc_c, ref_y, v_marca_x, etq_x, titulo, 'VuFc')
        grafico_evolucion(nfil, ncol, x, y_ufc_i, ref_y, v_marca_x, etq_x, titulo, 'VuFi')

        # gráfico de la última solución
        titulo = ['Precios', 'Cantidades', 'Importes']
        MUESTRA_PROGRESO = False
        (y1, y2, y3, y4, y5, y6, y7) = datos_grafico_solucion(soluciones[-1][1])
        y_sol = [y1 ,y2, y3]
        grafico_resumen(x_sol, y_sol, ref_sol, vli_sol, eli_sol, titulo)
    if SAL_AUXILIARES:
        # escribir el fichero con el historial 
        with open(FI_HISTORIAL, "w", encoding="utf-8") as sal:
            for v in historial:
                sal.write('{};{}\n'.format(v[0],v[1]))
        # escribir el fichero con las soluciones
        with open(FI_SOLUCIONES, "w", encoding="utf-8") as sal:
            for v in soluciones:
                sal.write('{}'.format(v[0]))
                vv = v[1]
                for i in range(len(vv)):
                    sal.write(';{}'.format(vv[i]))
                sal.write('\n')

    imprime('-----------------------------------------------------------')
    imprime('La distancia (error de la función objetivo) es {:9.3e}'.format(dist))
    imprime('-----------------------------------------------------------')
    imprime('')
    pf = extrae_var(sol,'pF', 0, nfac - 1)
    if OR_PRE_REFERENCIA == 1:
        # Como el vector de prueba no incluye el precio del último factor, añadimos el precio del último factor con valor 'PRECIO_F_REFERENCIA'
        pf = np.append(pf, np.array([PRECIO_F_REFERENCIA]), axis=0)
    else:
        # Como el vector de prueba no incluye el precio del primer factor, insertamos al principio (0) el precio del primer factor con valor 'PRECIO_F_REFERENCIA'
        pf = np.insert(pf, 0, np.array([PRECIO_F_REFERENCIA]), axis=0)
    # verificar la solución, se prepara el vector que se pasará como parámetro a la función 'veri_solucion'
    vec_veri_sol = (
                pf,
                extrae_var(sol,'pY', 0, nsec),
                pz,
                extrae_var(sol,'pQ', 0, nsec),
                extrae_var(sol,'pD', 0, nsec),
                extrae_var(sol,'epsilon', 0, 0),
                Apz,
                F,
                Z,
                E,
                M,
                Da,
                FF,
                Yp,
                X,
                Xp,
                Xg,
                Xv,
                Q,
                ebp,
                Sp,
                Sg,
                Td,
                Tz,
                Tm,
                CssE,
                CssH,
                AgE,
                AgH,
                Alp,
    )
    veri_solucion(vec_veri_sol,'Verifica con la solución final', GE_VERIFICAR)
    if (dist > GE_TOLERANCIA):
        imprime('')
        imprime('***********************************************************************')
        imprime('No se alcanzó el mínimo deseado {:9.3e} [{:9.3e}]'.format(GE_TOLERANCIA, dist))
        imprime('***********************************************************************')
    imprime('')
    imprime("Tiempo de cálculo:{:11,.0f} s".format(t_fin - t_inicio))
    imprime('')
    clave = 'message'
    mensaje = rmin[clave]
    imprime('{}'.format(mensaje))
    if mensaje != 'callback function requested stop early':
        clave = 'success'
        imprime('exito :{}'.format('Si' if rmin[clave]==True else 'No'))
    clave = 'nit'
    imprime('Número de iteraciones {}'.format(rmin[clave]))
    imprime('')
    imprime('Precios    iniciales equilibrio')
    imprime('--------- ---------- ----------')
    mfun.tabla_1Dl(etq_precios[0:npre_sol], vec_opt_ini[0:npre_sol], sol[0:npre_sol])
    imprime('--------- ---------- ----------')
    (pe, pm) = exte.precio_moneda_local_pe_pm(datos.pWe, datos.pWm, extrae_var(sol,'epsilon', 0, 0))
    respre = np.concatenate((pzi, np.array(datos.pWe*datos.epsilon_ini), np.array(datos.pWm*datos.epsilon_ini)))
    mfun.i_tabla('' , etq_precios[npre_sol:len(etq_precios)] , [], respre           , True ,  5)
    respre = np.concatenate((pz, np.array(pe), np.array(pm)))
    mfun.i_tabla('' , etq_precios[npre_sol:len(etq_precios)] , [], respre           , True ,  5)
    imprime('')
    ev = deho.variacion_hicksiana(datos.Xp0, Xp, parametros.alfa)
    imprime('--------------------------------------------')
    imprime('Variación del bienestar económico {:10.3e}'.format(ev.sum()))
    imprime('--------------------------------------------')
    mfun.i_tabla('/', dem, ['Var.Equiv.',], ev , False, 3)
    ingresos = FF.sum(axis=1) + datos.PssH0
    ev      [ingresos == 0] = 0. 
    ingresos[ingresos == 0] = 1. 
    mfun.i_tabla('', '', ['% ingresos',], 100.0 * ev / ingresos , False, 3)
    mfun.i_pie  ('/' , dem)
    imprime('')
    imprime('')
    MUESTRA_PROGRESO = False
    if SAL_VARIACIONES:
        diferencias_cantidades_finales_iniciales(vec_opt_ini, sol, res_ecuaciones, 'Cantidades')
        diferencias_importes_finales_iniciales(vec_opt_ini, sol, res_ecuaciones, 'Importes')

