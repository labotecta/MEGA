'''
Se necesita float64, con float32 no es suficiente.

Aúnque scipy es muy eficiente por estar compilada en C, el punto débil es la función objetivo
que está íntegramente en Python.

Otro asunto sobre el que reflexionar, es la conveniencia de normalizar las desviaciones de las variables en el
resultado de la función objetivo. La aplicación no los normaliza, se trata de desviaciones en importes y todos
tienen el mismo peso, sea cual sea el importe absoluto de la variable. Casi seguro no serviría de nada
scipy.differential_evolution si normaliza las variables para que todos los intervalos de existencia sean el mismo.

Los pagos de impuestos directos del gobierno no se usan para nada (Tg0) los paga y los cobra el mismo agente.
Los pagos de impuestos directos del sector exterior no se usan para nada (Te0).

Utilizar para la demanda la función de utilidad Cobb-Douglas o la CES con cualquier valor de sigma, da prácticamente los
mismos resultados, lo cual es lógico porque los parámetros se determinan, en todos los casos, para que se
reproduzcan los valores Xp0 de la MCS y las variaciones que experimentan los Xp en otros esenarios son suficientemente
pequeñas para que todas las funciones de utilidad repartan los ingresos netos en prácticamente las mismas cantidades.

Resulta increible el papel de Apz, si no se deja libre en un intervalo grande, no se encuentra solución.

El tratamiento del precio de los factores es enrevesado y fuente de multitud de errores, se diseñó pensando
que siempre se fijaría el precio del factor trabajo y que por lo tanto no debía formar parte de las soluciones a
probar, pero los parches al considerar que se podría fijar el del capital o usar la curva Phillips hacen
difícil de enetender la gestión de estos precios en la aplicación, reformular esto supone mucho esfuerzo, sobre todo
si tenemos en cuenta que el planteamiento que hace la aplicación, aunque enrevesado, funciona.

Los impuestos al ahorro-inversión (Ti) se pueden interpretar de varias formas, el modelo los considera como un impuesto a las
rentas de capital (ingresos por el factor capital) que perciben los hogares, los ubica en la cuenta ahorro-inversión pero podrían incluirse en
la de impuestos pagados por cada hogar (de forma análoga a la cotización a la seguridad social por el factor trabajo), lo que
permitiría individualizarlos para cada uno de ellos. La inclusión en la cuenta ahorro-inversión es algo incoherente en el sentido de que se
"mezclan" las nuevas inversiones con los impuestos a las rentas de capital de las inversiones previas, que son dos cosas distintas y que
además no están relacionadas en nuestro modelo, aúnque numéricamente sea equivalente, ya que el disponible para invertir es el mismo anotando el
impuesto como un pago de los hogares, o como un pago de la cuenta ahorro-inversión.
'''
'''
Mejoras:
    1. Relacionar las iniversiones con uso del factor capital por los sectores y la retribición de los hogares por rentas de capital

    2. Desglosar la cuenta del IVA, en general desglosar las cuentas de impuestos, porque la base de los mismos es diferente,
       por ejemplo la del IRPF y la del IVA es muy distinta

    3. Incorporar las salidas al exterior de fondos (pagos) desde los hogares (salarios inmigrantes) y la inversión (repatriación de dividendos)

'''
import os
import sys
import psutil 
import copy
import numpy as np
import matplotlib
import pandas
import scipy
import ctypes as ct

from pandas          import Series
from scipy.optimize  import differential_evolution
from timeit          import default_timer as timer

import argumentos
import calibrado
import funciones     as mfun
import informes      as infor
import escenarios    as esce
import produccion    as prod
import gobierno      as gob
import ahorro_inv    as ainv
import demanda       as deho
import exterior      as exte
import restricciones as restri

# los escenarios pueden cambiar los valores iniciales de las variable y los parámetros
global datos
global parametros

VERSION = '1.6.0'

# 7 Matrices de Contabilidad Social para las pruebas, se selecciona con NSAM
# estas etiquetas solo se usan para construir el nombre del fichero de salida
#               0           1              2              3               4              5            6
etq_sam  = ('1_hogar', '2_hogares', '2_hogares_SS', '3_hogares_AMP', 'MCA-ESP-05', 'españa 2022', 'MCA-ESP-08')
# escenarios para las pruebas, se selecciona con NCASO
etq_caso = (
    'base',                     #  0
    'alfa',                     #  1
    'beta',                     #  2
    'sin_arancel',              #  3
    'doble_arancel',            #  4
    'pre_ini',                  #  5
    'factores',                 #  6
    'ahorro',                   #  7
    'seg_social',               #  8
    'dem_alfa',                 #  9 simplemente cambia la preferencia de los consumos, no se añade demanda porque duplicaría el efecto en los productos
    # usar el caso 0 para ayudas no es equivalente al caso 12 porque las ayudas no irán destinadas de forma diferenciada a los productos, para esto hay que modificar los alfa  
    'alfa_ayudas',              # 10
    'sigma',                    # 11
    'aranceles',                # 12
    'Xp0',                      # 13 consumos esenciales = Xp0
    'Xp0m1',                    # 14 consumos esenciales = Xp0 - 1
)

etq_mpob =(
    "intervalo simétrico centrado en 'vec_ini' con distribución uniforme",
    "centrado en el centro de intervalo de validez de la variable con distribución uniforme",
    "intervalo simétrico centrado en 'vec_ini' con distribución normal",
    "centrado en el centro de intervalo de validez de la variable con distribución normal",
    "Latin Hypercube Sampling con permutaciones distintas para cada variable",
    "Latin Hypercube Sampling con la misma permutación para todas las variables",
    "secuencia de valores uniformemente espaciados entre cotas y permutaciones distintas para cada variable",
	"secuencia de valores uniformemente espaciados entre cotas y la misma permutación para todas las variables",
    "valores próximos al extremo inferior del entorno de existencia de las variables, con permutaciones distintas para cada variable",
    "valores próximos al extremo inferior del entorno de existencia de las variables, con la misma permutación para todas las variables",
    "valores próximos al extremo superior del entorno de existencia de las variables",
    'valores próximos a los extremos de los entornos de existencia de las variables',
    'valores próximos, o iguales, al extremo inferior del entorno de existencia de las variables, con permutaciones distintas para cada variable',
    'valores próximos, o iguales, al extremo inferior del entorno de existencia de las variables',
    'valores próximos, o iguales, al extremo superior del entorno de existencia de las variables, con permutaciones distintas para cada variable',
    'valores próximos, o iguales, al extremo inferior, con permutaciones distintas para cada variable y desplazamiento independiente',
)
# extrae los argumentos de la línea de comandos y si no la hay de los valores por defecto
try:
    args = argumentos.valores_opciones()
except BaseException as e:
    print('Error en la lectura de parámetros {}\n'.format(e.args))
    sys.exit()

# se guardan las notificaciones hasta que esté lista la función 'imprimir'
errores_diferidos = []
avisos_diferidos  = []

HISTO_MAX = 201
nfac = args.NFAC    # número de factores 
ndem = args.NDEM    # número de hogares
nsec = args.NSEC    # número de sectores

#----------------------------------------------------------------------------
# retrasamos hasta aquí la importación del módulo 'dll'
# para que al importarlo ya estén definidas 'nfac, ndem y nsec'
#----------------------------------------------------------------------------
import dll           as dll
#----------------------------------------------------------------------------
'''
copiamos a variables globales los parámetros de la línea de comando, o su valor por defecto y ajustamos las dimensiones de
las matrices ('reshape') cuando corresponde, ya que en la línea de comandos solo podemos incluir vectores, además se
realizan algunas comprobaciones de la consistencia de los valores reecibidos
'''
NSAM                = args.NSAM
DECIMALES           = args.DECIMALES
FI_SOL_LEE          = args.FI_SOL_LEE
FI_SOL_SALVA        = args.FI_SOL_SALVA

USAR_DLL            = args.USAR_DLL
SENDA_DLL           = args.SENDA_DLL
USAR_ALGE_DLL       = args.USAR_ALGE_DLL
DESV_RELATIVA       = args.DESV_RELATIVA
if DESV_RELATIVA == 1:
    if USAR_DLL == False or USAR_ALGE_DLL == False:
        DESV_RELATIVA = 0
        if __name__ == 'MEGA':
            avisos_diferidos.append('Solo se puede usar DESV_RELATIVA con la DLL. Se desactiva DESV_RELATIVA')
    else:
        try:
            libc = ct.CDLL(SENDA_DLL)
            libc.merito_s_relativa.argtypes = [ct.POINTER(ct.c_double)]
            libc.merito_s_relativa.restype = ct.c_double
            libc.merito_sol_relativa.argtypes = [ct.POINTER(ct.c_double)]
            libc.merito_sol_relativa.restype = ct.POINTER(ct.c_double)
        except:
            DESV_RELATIVA = 0
            if __name__ == 'MEGA':
                avisos_diferidos.append('Para usar DESV_RELATIVA es probable que haya que recompilar la DLL. Se desactiva DESV_RELATIVA')
if (USAR_DLL or USAR_ALGE_DLL) and NSAM != 0 and NSAM != 1 and NSAM != 2 and NSAM != 3 and NSAM != 4 and NSAM != 5 and NSAM != 6:
    if __name__ == 'MEGA':
        errores_diferidos.append('La DLL solo se puede usar con las MCS 0, 1, 2, 3, 4, 5 y 6 y se ha especificado la {}'.format(NSAM))
    else:
        errores_diferidos.append('')
ALGE_ID_SALIDA      = args.ALGE_ID_SALIDA
ALGE_MAX_INTENTOS   = args.ALGE_MAX_INTENTOS
ALGE_N_HILOS        = args.ALGE_N_HILOS
GE_MIN_PROGRESO     = args.GE_MIN_PROGRESO
ALGE_TOL_ACEPTABLE  = args.ALGE_TOL_ACEPTABLE
ALGE_MODO_POB_INI   = args.ALGE_MODO_POB_INI
ALGE_F_INICIO_POB   = args.ALGE_F_INICIO_POB
ALGE_SIGMA_POB_INI  = args.ALGE_SIGMA_POB_INI
ALGE_TRAMOS_LHS     = args.ALGE_TRAMOS_LHS
ALGE_NPOB           = args.ALGE_NPOB
ALGE_F_MUTACION     = args.ALGE_F_MUTACION
ALGE_RECOMBINACION  = args.ALGE_RECOMBINACION
ALGE_CTRL_FACTIBLE  = args.ALGE_CTRL_FACTIBLE
ALGE_RES_EXTENSA    = args.ALGE_RES_EXTENSA
EL_MEJOR_PRIMERO    = args.EL_MEJOR_PRIMERO
ALGE_INCLUIR_X0     = args.ALGE_INCLUIR_X0

NCASO               = np.array(args.NCASO, dtype=int)
EQ_BAL_PAGOS        = args.EQ_BAL_PAGOS
if len(args.PRECIO_IMPORTACION) > 0:
    n_precios_importacion = len(args.PRECIO_IMPORTACION) // 2
    if n_precios_importacion * 2 != len(args.PRECIO_IMPORTACION):
        if __name__ == 'MEGA':
            errores_diferidos.append('El número de datos para DEM_ADICIONAL {} no es el correcto {}'.format(len(args.DEM_AD_HO_PRO), 3 * args.DEM_AD_LON))
        else:
            errores_diferidos.append('')
    else:
        precios_importacion = []
        for i in range(0, n_precios_importacion, 2):
            precios_importacion.append([int(args.PRECIO_IMPORTACION[i]), np.float64(args.PRECIO_IMPORTACION[i + 1])])
else:
    n_precios_importacion =  0
DEM_ADICIONAL_TIPO  = args.DEM_ADICIONAL_TIPO
DEM_ADICIONAL       = np.zeros((ndem, nsec), dtype=np.float64)
if args.DEM_AD_LON > 0:
    if len(args.DEM_AD_HO_PRO) != 3 * args.DEM_AD_LON:
        if __name__ == 'MEGA':
            errores_diferidos.append('El número de datos para DEM_ADICIONAL {} no es el correcto {}'.format(len(args.DEM_AD_HO_PRO), 3 * args.DEM_AD_LON))
        else:
            errores_diferidos.append('')
    else:
        n = args.DEM_AD_LON
        i = 0
        for _ in range(n):
            j = int(args.DEM_AD_HO_PRO[i])
            k = int(args.DEM_AD_HO_PRO[i+1])
            DEM_ADICIONAL[j][k] = args.DEM_AD_HO_PRO[i+2]
            i += 3
AYD_ADICIONAL = np.zeros((ndem, nsec), dtype=np.float64)
if args.AYD_AD_LON > 0:
    if len(args.AYD_AD_HO_PRO) != 3 * args.AYD_AD_LON:
        if __name__ == 'MEGA':
            errores_diferidos.append('El número de datos para AYD_ADICIONAL {} no es el correcto {}'.format(len(args.AYD_AD_HO_PRO), 3 * args.AYD_AD_LON))
        else:
            errores_diferidos.append('')
    else:
        n = args.AYD_AD_LON
        i = 0
        for _ in range(0,n,3):
            j = int(args.AYD_AD_HO_PRO[i])
            k = int(args.AYD_AD_HO_PRO[i+1])
            AYD_ADICIONAL[j][k] = args.AYD_AD_HO_PRO[i+2]
            i += 3
RENTA_FICTICIA      = args.RENTA_FICTICIA
if (9 in NCASO) and RENTA_FICTICIA:
    if __name__ == 'MEGA':
        avisos_diferidos.append('Se ha seleccionado el caso {} sin renta ficticia'.format(etq_caso[9]))
GE_INCLUYE_XP       = args.GE_INCLUYE_XP
DEM_ESENCIALES      = args.DEM_ESENCIALES
CON_ESENCIALES = np.zeros((ndem, nsec), dtype=np.float64)
if args.CON_AD_LON > 0:
    if len(args.CON_AD_HO_PRO) != 3 * args.CON_AD_LON:
        if __name__ == 'MEGA':
            errores_diferidos.append('El número de datos para CON_ESENCIALES {} no es el correcto {}'.format(len(args.CON_AD_HO_PRO), 3 * args.CON_AD_LON))
        else:
            errores_diferidos.append('')
    else:
        n = args.CON_AD_LON
        i = 0
        for _ in range(n):
            j = int(args.CON_AD_HO_PRO[i])
            k = int(args.CON_AD_HO_PRO[i+1])
            CON_ESENCIALES[j][k] = args.CON_AD_HO_PRO[i+2]
            i += 3
if abs(CON_ESENCIALES).sum() == 0 and DEM_ESENCIALES == True:
    if __name__ == 'MEGA':
        avisos_diferidos.append('No se han especificado consumos esenciales pero DEM_ESENCIALES es True')
if abs(CON_ESENCIALES.sum()) == 0:
    if (13 in NCASO) == False and (14 in NCASO) == False:
        # los casos 13 y 14 fijan los consumos esenciales
        if DEM_ESENCIALES == True:
            DEM_ESENCIALES = False
            if __name__ == 'MEGA':
                avisos_diferidos.append('Se ha cambiado DEM_ESENCIALES a False, sin consumos esenciales no tiene sentido calcular demandas con consumos esenciales')
        if GE_INCLUYE_XP == True:
            if __name__ == 'MEGA':
                avisos_diferidos.append('Se ha especificado GE_INCLUYE_XP = True, sin consumos esenciales')
else:
    if GE_INCLUYE_XP == False and DEM_ESENCIALES == False:
        if __name__ == 'MEGA':
            avisos_diferidos.append('Se han especificado consumos esenciales pero GE_INCLUYE_XP y DEM_ESENCIALES son False')
    if GE_INCLUYE_XP == False and DEM_ESENCIALES == True:
        if __name__ == 'MEGA':
            avisos_diferidos.append('Se han especificado consumos esenciales y GE_INCLUYE_XP es False pero DEM_ESENCIALES es True. Stone-Geary puede fallar')
if len(args.SIGMA_CES_DEMANDA) != ndem:
    if __name__ == 'MEGA':
        errores_diferidos.append('El número de datos para SIGMA_CES_DEMANDA {} no es el correcto {}'.format(len(args.SIGMA_CES_DEMANDA), ndem))
    else:
        errores_diferidos.append('')
else:
    SIGMA_CES_DEMANDA = np.array(args.SIGMA_CES_DEMANDA, dtype=np.float64).reshape(ndem)
if len(args.SIGMA_ESCENARIO) == 0:
    SIGMA_ESCENARIO = np.empty(nsec, dtype=np.float64)
    SIGMA_ESCENARIO.fill(2.)
    if args.SIGMA_ESCE_LON > 0:
        if len(args.SIGMA_ESCE) != 2 * args.SIGMA_ESCE_LON:
            if __name__ == 'MEGA':
                errores_diferidos.append('El número de datos para SIGMA_ESCENARIO {} no es el correcto {}'.format(len(args.SIGMA_ESCE), 2 * args.SIGMA_ESCE_LON))
            else:
                errores_diferidos.append('')
        else:
            n = args.SIGMA_ESCE_LON
            i = 0
            for _ in range(n):
                j = int(args.SIGMA_ESCE[i])
                SIGMA_ESCENARIO[j] = args.SIGMA_ESCE[i+1]
                i += 2
else:
    if len(args.SIGMA_ESCENARIO) != nsec:
        if __name__ == 'MEGA':
            errores_diferidos.append('El número de datos para SIGMA_ESCENARIO {} no es el correcto {}'.format(len(args.SIGMA_ESCENARIO), nsec))
        else:
            errores_diferidos.append('')
    else:
        SIGMA_ESCENARIO     = np.array(args.SIGMA_ESCENARIO, dtype=np.float64)
ARANCELES = np.zeros(nsec, dtype=np.float64)
if args.ARANCELES_LON > 0:
    if len(args.ARANCELES_PRO) != 2 * args.ARANCELES_LON:
        if __name__ == 'MEGA':
            errores_diferidos.append('El número de datos para ARANCELES {} no es el correcto {}'.format(len(args.ARANCELES_PRO), 2 * args.ARANCELES_LON))
        else:
            errores_diferidos.append('')
    else:
        n = args.ARANCELES_LON
        i = 0
        for _ in range(n):
            j = int(args.ARANCELES_PRO[i])
            ARANCELES[j] = args.ARANCELES_PRO[i+1]
            i += 2
PREFIJO             = args.PREFIJO if args.PREFIJO != '"' else ''

OR_PRE_EXCLUIDO     = args.OR_PRE_EXCLUIDO
PRECIO_F_EXCLUIDO   = np.float64(args.PRECIO_F_EXCLUIDO)
VALOR_F_TRA         = np.float64(args.VALOR_F_TRA)
PARO_INICIAL        = np.float64(args.PARO_INICIAL)
ALFA_PHILLIPS       = np.float64(args.ALFA_PHILLIPS)
FF_ENDOGENA         = args.FF_ENDOGENA
ALP_FACTOR          = args.ALP_FACTOR
OPT_DESVIOS         = args.OPT_DESVIOS
UTILIDAD_DEMANDA    = args.UTILIDAD_DEMANDA
MODO_PSEUDOIMPTOS   = args.MODO_PSEUDOIMPTOS
SAL_CALIBRADO       = args.SAL_CALIBRADO
PRIMERA_VALORACION  = args.PRIMERA_VALORACION
SALIDA_VEC_OPT      = args.SALIDA_VEC_OPT
SALIDA_VAL_INI      = args.SALIDA_VAL_INI
SALIDA_DESVIOS      = args.SALIDA_DESVIOS
SAL_VARIACIONES     = args.SAL_VARIACIONES
SAL_MCS             = args.SAL_MCS
SAL_VAR_MCS         = args.SAL_VAR_MCS
if USAR_ALGE_DLL:
    # la DLL no aporta estos detalles
    SAL_AUXILIARES    = False
    SAL_GRAFICOS_EVOL = False
else:
    SAL_AUXILIARES      = args.SAL_AUXILIARES
    SAL_GRAFICOS_EVOL   = args.SAL_GRAFICOS_EVOL
SAL_GRAFICO_CES_DM  = args.SAL_GRAFICO_CES_DM
SAL_ISOCUANTA       = args.SAL_ISOCUANTA
GE_HISTORIAL        = args.GE_HISTORIAL
GE_SOLUCIONES       = args.GE_SOLUCIONES
GE_PRE_MIN          = np.float64(args.GE_PRE_MIN)
GE_PRE_MAX          = np.float64(args.GE_PRE_MAX)
GE_VAR_MIN          = np.float64(args.GE_VAR_MIN)
GE_VAR_MAX          = np.float64(args.GE_VAR_MAX)
GE_VAR_CERO         = np.float64(args.GE_VAR_CERO)
GE_VAR_CAN_MIN      = np.float64(args.GE_VAR_CAN_MIN)
if len(args.FIX) == 0 or args.FIX[0] == '':
    FIX = []
    FIX_LIMITES = np.zeros(0, dtype=list)
else:
    FIX     = args.FIX
    FIX_LON = args.FIX_LON
    k = len(args.FIX)
    n = len(args.FIX_LON)
    if k != n:
        if __name__ == 'MEGA':
            errores_diferidos.append('FIX. No coincide el número de variables acotadas {} con el de límites {}'.format(k, n))
        else:
            errores_diferidos.append('')
    if len(args.FIX_LIMITES) != sum(args.FIX_LON) * 3:
        if __name__ == 'MEGA':
            errores_diferidos.append('FIX. No coincide el número de ternas de limites {} con el de tamaño de FIX_LIMITES {}'.format(sum(args.FIX_LON) * 2, args.FIX_LIMITES))
        else:
            errores_diferidos.append('')

    # cada elemento de la matriz 'FIX_LIMITES' es una lista de tres valores
    FIX_LIMITES = np.zeros(k, dtype=list)
    ni = 0
    for i in range(k):
        # para cada variable 'i'
        sec = []
        for j in range(FIX_LON[i]):
            # 3 valores para cada terna (índice, lim inferior, lim superior) de la variable
            terna = args.FIX_LIMITES[ni:(ni + 3)]
            try:
                terna[0] = int(terna[0])
            except BaseException as e:
                if __name__ == 'MEGA':
                    errores_diferidos.append('FIX {}. El primer elemento de la terna {} debe ser un número'.format(FIX[i], terna[0]))
                else:
                    errores_diferidos.append('')
            try:
                terna[1] = float(terna[1])
            except BaseException as e:
                if terna[1] != '*':
                    if __name__ == 'MEGA':
                        errores_diferidos.append('FIX {}. El segundo elemento de la terna {} debe ser un número o un *'.format(FIX[i], terna[1]))
                    else:
                        errores_diferidos.append('')
            try:
                terna[2] = float(terna[2])
            except BaseException as e:
                if terna[2] != '*':
                    if __name__ == 'MEGA':
                        errores_diferidos.append('FIX {}. El tercer elemento de la terna {} debe ser un número o un *'.format(FIX[i], terna[1]))
                    else:
                        errores_diferidos.append('')
            sec.append(terna)
            ni += 3
        FIX_LIMITES[i] = sec
GE_MAX_ITER         = args.GE_MAX_ITER
GE_RESTRICCIONES    = args.GE_RESTRICCIONES
GE_TIPO_RE          = args.GE_TIPO_RE
GE_TOLERANCIA       = np.float64(args.GE_TOLERANCIA)
GE_VERIFICAR        = np.float64(args.GE_VERIFICAR)
GE_PROGRESO         = args.GE_PROGRESO
GE_ACTUALIZACION    = args.GE_ACTUALIZACION
GE_RECONBINACION    = args.GE_RECONBINACION
GE_DIM_POBLACION    = args.GE_DIM_POBLACION
GE_WORKERS          = args.GE_WORKERS
if GE_WORKERS != 1:
    if USAR_ALGE_DLL:
        if __name__ == 'MEGA':
            errores_diferidos.append('Para usar el algoritmo genético desde la DLL, el número de Workers ({}) debe ser 1'.format(GE_WORKERS))
        else:
            errores_diferidos.append('')
    # aunque 'scipy' lo modifica automáticamente (y la DLL no lo usa), no está de más, especificarlo por transparencia
    GE_ACTUALIZACION = 'deferred'
    # comprobar el número de GE_WORKERS según la máquina
    n_cores = psutil.cpu_count(logical = False)
    if n_cores <= GE_WORKERS:
        if __name__ == 'MEGA':
            avisos_diferidos.append('Esta máquina tiene {} cores físicos y se han especificado {} workers.'.format(n_cores, GE_WORKERS))
GE_SEMILLA          = args.GE_SEMILLA
GE_IMG_FIL          = args.GE_IMG_FIL
GE_IMG_COL          = args.GE_IMG_COL
GE_ESTRATEGIA       = args.GE_ESTRATEGIA
METRICA_ERROR       = args.METRICA_ERROR
POT_DESVIOS         = args.POT_DESVIOS
PRECIO_INI          = np.float64(args.PRECIO_INI)

if len(args.FACTOR_CSSH) != ndem:
    if __name__ == 'MEGA':
        errores_diferidos.append('El número de datos para FACTOR_CSSH {} no es el correcto {}'.format(len(args.FACTOR_CSSH), ndem))
    else:
        errores_diferidos.append('')
else:
    FACTOR_CSSH         = np.array(args.FACTOR_CSSH, dtype=np.float64)
if len(args.FACTOR_CSSE) == 0:
    FACTOR_CSSE = np.ones(nsec, dtype=np.float64)
    if args.F_CSSE_LON > 0:
        if len(args.F_CSSE) != 2 * args.F_CSSE_LON:
            if __name__ == 'MEGA':
                errores_diferidos.append('El número de datos para FACTOR_CSSE {} no es el correcto {}'.format(len(args.F_CSSE), 2 * args.F_CSSE_LON))
            else:
                errores_diferidos.append('')
        else:
            n = args.F_CSSE_LON
            i = 0
            for _ in range(n):
                j = int(args.F_CSSE[i])
                FACTOR_CSSE[j] = args.F_CSSE[i+1]
                i += 2
else:
    if len(args.FACTOR_CSSE) != nsec:
        if __name__ == 'MEGA':
            errores_diferidos.append('El número de datos para FACTOR_CSSE {} no es el correcto {}'.format(len(args.FACTOR_CSSE), nsec))
        else:
            errores_diferidos.append('')
    else:
        FACTOR_CSSE         = np.array(args.FACTOR_CSSE, dtype=np.float64)
if len(args.VAR_FACTORES) != ndem * nfac:
    if __name__ == 'MEGA':
        errores_diferidos.append('El número de datos para VAR_FACTORES {} no es el correcto {}'.format(len(args.VAR_FACTORES), ndem * nfac))
    else:
        errores_diferidos.append('')
else:
    VAR_FACTORES  = np.array(args.VAR_FACTORES, dtype=np.float64).reshape(ndem, nfac)

SENDA_DATOS       = args.SENDA_DATOS
SENDA_SALIDAS     = args.SENDA_SALIDAS
SENDA_GRAFICOS    = args.SENDA_GRAFICOS
SENDA_SOLUCIONES  = args.SENDA_SOLUCIONES
if (13 in NCASO) and DEM_ESENCIALES:
    if __name__ == 'MEGA':
        errores_diferidos.append('Consumos esenciales iguales a Xp0 (caso 13) es incompatible con Stone-Geary (rentas 0)')
    else:
        errores_diferidos.append('')

if len(errores_diferidos) == 0:
    # acumular por hogar porque el modelo no contempla ayudas para un producto determinado, pero necesitamos los
    # valores desagregados por producto, porque modificaremos las preferencias (alfa) de consumo de cada producto en particular
    AYD_ADI_DEM = AYD_ADICIONAL.sum(axis=1)
os.makedirs(SENDA_SALIDAS   , exist_ok=True)  # crear el directorio si no existe
os.makedirs(SENDA_GRAFICOS  , exist_ok=True)  # crear el directorio si no existe
os.makedirs(SENDA_SOLUCIONES, exist_ok=True)  # crear el directorio si no existe

# para el algoritmo genético de la DLL
rot_res_dll_ok = [
            "Solución encontrada",
            "No progresa, solución no aceptable",
            "No progresa, pero la solución puede ser aceptable",
            "Superado el máximo de generaciones, solución no aceptable",
            "Superado el máximo de generaciones, pero la solución puede ser aceptable",
            "Cancelado",
        ]
rot_res_dll_error = [
            "El número de individuos debe ser multiplo del número de hilos",
            "Error al generar la población",
            "Error al fijar las cotas",
            "Error al reservar memoria para la población",
            "Error al generar la población",
            "Terminación imposible",
            "Error en los parámetros",
            "Error al preparar la multitarea",
            "Error al abrir el fichero de salida",
            "Error inesperado",
        ]
# para asimilar el formato del resultado de la DLL al que devuelve scipy
class rmin_dll(object):
    def __init__(self, sol, dnit):
        self.x = sol
        self.nit = dnit

# --------------------------------------------------------------------
# ATENCION el factor trabajo debe ser la columna 'INDICE_F_TRA' de 'h'
# --------------------------------------------------------------------
INDICE_F_TRA = 1        # índice del factor trabajo, es más seguro cambiar el orden en la definición de la lista 'h', que cambiar este índice

# los bloques (ind, h, ...) se declaran como 'tuple' (entre paréntesis) que es igual que
# 'list' pero no modificable, lo que las hace más eficientes
if   NSAM == 0:
    # Con un solo hogar (consumidor)
    FICHERO_SAM = '{}/{}.xlsx'.format(SENDA_DATOS, "SAM_estandar")
    ind  = ('BRD' ,'MLK')       # sectores (industria)
    h    = ('CAP' ,'LAB')       # factores de producción
    dem  = ('HOH',)             # demanda de los hogares
    idt  = ('IDT',)             # impuestos indirectos a la producción
    trf  = ('TRF',)             # aranceles pagados por la producción (son los únicos que importan en este modelo)
    gov  = ('GOV',)             # gobierno
    ayd  = ('AYD',)             # ayudas del gobierno, no existe en la MCS original, pero la añadimos porque
                                # el escenario puede incluir ayudas 
    inv  = ('INV',)             # ahorro e inversión
    ext  = ('EXT',)             # sector exterior
    css  = ()                   # cotizaciones a la seguridad social
    alp  = ('ALP',)             # ahorro a largo plazo
    #
elif NSAM == 1:
    # Con dos hogares (consumidores)
    FICHERO_SAM = '{}/{}.xlsx'.format(SENDA_DATOS, "SAM_10_10")
    ind  = ('BRD' ,'MLK')       # sectores (industria)
    h    = ('CAP' ,'LAB')       # factores de producción
    dem  = ('HOH1','HOH2')      # demanda de los hogares
    idt  = ('IDT',)             # impuestos indirectos a la producción
    trf  = ('TRF',)             # aranceles pagados por la producción (son los únicos que importan en este modelo)
    gov  = ('GOV',)             # gobierno
    ayd  = ('AYD',)             # ayudas del gobierno
    inv  = ('INV',)             # ahorro e inversión
    ext  = ('EXT',)             # sector exterior
    css  = ('CSS',)             # cotizaciones a la seguridad social
    alp  = ('ALP',)             # ahorro a largo plazo
    #
elif NSAM == 2:
    # Con dos hogares (consumidores)
    FICHERO_SAM = '{}/{}.xlsx'.format(SENDA_DATOS, "SAM_CSS")
    ind  = ('BRD' ,'MLK')       # sectores (industria)
    h    = ('CAP' ,'LAB')       # factores de producción
    dem  = ('HOH1','HOH2')      # demanda de los hogares
    idt  = ('IDT',)             # impuestos indirectos a la producción
    trf  = ('TRF',)             # aranceles pagados por la producción (son los únicos que importan en este modelo)
    gov  = ('GOV',)             # gobierno
    ayd  = ('AYD',)             # ayudas del gobierno
    inv  = ('INV',)             # ahorro e inversión
    ext  = ('EXT',)             # sector exterior
    css  = ('CSS',)             # cotizaciones a la seguridad social
    alp  = ('ALP',)             # ahorro a largo plazo
    #
elif NSAM == 3:
    # Con tres hogares (consumidores), seguridad social independiente y ayudas del gobierno
    FICHERO_SAM = '{}/{}.xlsx'.format(SENDA_DATOS, "SAM_AMP")
    ind  = ('BRD' ,'MLK')           # sectores (industria)
    h    = ('CAP' ,'LAB')           # factores de producción
    dem  = ('HOH1','HOH2','HOH3')   # demanda de los hogares
    idt  = ('IDT',)                 # impuestos indirectos a la producción
    trf  = ('TRF',)                 # aranceles pagados por la producción (son los únicos que importan en este modelo)
    gov  = ('GOV',)                 # gobierno
    ayd  = ('AYD',)                 # ayudas del gobierno
    inv  = ('INV',)                 # ahorro e inversión
    ext  = ('EXT',)                 # sector exterior
    css  = ('CSS',)                 # cotizaciones a la seguridad social
    alp  = ('ALP',)                 # ahorro a largo plazo
    #
elif NSAM == 4:
    # MCA-ESP-05 corregida
    '''
    Actividades_Agrarias_y_pesca                AP1
    Energía_e_industrias_extractivas            AP2
    Actividades_industriales                    AP3
    Construcción                                AP4
    Servicios_destinados_a_la_venta             AP5
    Servicios_no_destinados_a_la_venta          AP6 (servicios de no mercado, ayudas más o menos)
    Trabajo                                     L
    Capital                                     K
    Consumo                                     C
    Ahorro/Inversión                            A-I
    Cotizaciones_sociales                       CSS
    Impuestos_netos_sobre_los_productos         INP
    Otros_impuestos_netos_sobre_la_producción   INPR
    IRPF                                        IRPF
    Sector_público                              SP
    Sector_exterior                             SE
    '''
    FICHERO_SAM = '{}/{}.xlsx'.format(SENDA_DATOS, "MCA-ESP-05_ajustada_imp_final")
    ind  = ('AP1','AP2','AP3','AP4','AP5','AP6')    # sectores (industria)
    h    = ('K'  ,'L')                              # factores de producción
    dem  = ('C1','C2')                              # demanda de los hogares
    idt  = ('INP',)                                 # impuestos a la producción, otros impuestos a la producción
    trf  = ('TRF',)                                 # aranceles pagados por la producción (no los hay en esta MCS)
    gov  = ('SP',)                                  # gobierno
    ayd  = ('AYD',)                                 # ayudas del gobierno
    inv  = ('A-I',)                                 # ahorro e inversión
    ext  = ('SE',)                                  # sector exterior
    css  = ('CSS',)                                 # cotizaciones a la seguridad social
    alp  = ('ALP',)                                 # ahorro a largo plazo
    #
elif NSAM == 5:
    # España 2022
    FICHERO_SAM = '{}/{}.xlsx'.format('C:/MEGA/INE', "mcs_22_sin_R32_R64")
    SAM_HOJA    = 'MCS'
    # B3
    SAM_COL     = 1     # B = 1 contando desde 0
    SAM_FIL     = 2     # 3 = 2 contando desde 0
    
    # sectores (industria)
    ind = []
    for i in range(63):
        ind.append('R' + str(i + 1))
    ind = tuple(ind)
    h    = ('K'  ,'L')                              # factores de producción
    dem  = ('C1','C2','C3')                         # demanda de los hogares
    idt  = ('INP',)                                 # impuestos a la producción, otros impuestos a la producción
    trf  = ('TRF',)                                 # aranceles pagados por la producción (no los hay en esta MCS)
    gov  = ('SP',)                                  # gobierno
    ayd  = ('AYD',)                                 # ayudas del gobierno
    inv  = ('A-I',)                                 # ahorro e inversión
    ext  = ('SE',)                                  # sector exterior
    css  = ('CSS',)                                 # cotizaciones a la seguridad social
    alp  = ('ALP',)                                 # ahorro a largo plazo
    #
elif NSAM == 6:
    # España 2008
    FICHERO_SAM = '{}/{}.xlsx'.format('C:/MEGA/Datos', "MCS-ESP-RENO")
    SAM_HOJA    = 'Ajustada'
    # C3
    SAM_COL     = 2     # C = 2 contando desde 0
    SAM_FIL     = 2     # 3 = 2 contando desde 0
    
    # sectores (industria)
    ind = []
    for i in range(31):
        ind.append('R' + str(i + 1))
    ind = tuple(ind)
    h    = ('K'  ,'L')                              # factores de producción
    dem  = ('C1','C2')                              # demanda de los hogares
    idt  = ('INP',)                                 # impuestos a la producción, otros impuestos a la producción
    trf  = ('TRF',)                                 # aranceles pagados por la producción (no los hay en esta MCS)
    gov  = ('SP',)                                  # gobierno
    ayd  = ('AYD',)                                 # ayudas del gobierno
    inv  = ('A-I',)                                 # ahorro e inversión
    ext  = ('SE',)                                  # sector exterior
    css  = ('CSS',)                                 # cotizaciones a la seguridad social
    alp  = ('ALP',)                                 # ahorro a largo plazo
    #
else:
    if __name__ == 'MEGA':
        errores_diferidos.append('Número de MCS {} incorrecto'.format(NSAM))
    else:
        errores_diferidos.append('')

# error máximo para diagnosticar una discrepacia en la MCS recalculada
TOLERA_MCS = 1.0 / (10.0 ** DECIMALES)

if nfac != len(h):
    if __name__ == 'MEGA':
        errores_diferidos.append('El número de factores en la MCS {} no coincide con el especificado {}'.format(len(h), nfac) + '\n')
    else:
        errores_diferidos.append('')
if ndem != len(dem):
    if __name__ == 'MEGA':
        errores_diferidos.append('El número de hogares en la MCS {} no coincide con el especificado {}'.format(len(dem), ndem) + '\n')
    else:
        errores_diferidos.append('')
if nsec != len(ind):
    if __name__ == 'MEGA':
        errores_diferidos.append('El número de sectores en la MCS {} no coincide con el especificado {}'.format(len(ind), nsec) + '\n')
    else:
        errores_diferidos.append('')

if len(PREFIJO) > 1 and PREFIJO[0] == '=':
    # si PREFIJO empieza con el caracter '=' los caracteres del 1 en adelante se usarán como nombre de los
    # ficheros de salida en lugar de componerlos a partir de las opciones seleccionadas
    CASO = PREFIJO[1:]
else:
    # componer el nombre de los ficheros de salida en función de las opciones
    CASO  = PREFIJO + h[INDICE_F_TRA] + '_Desv_{:1d}_'.format(OPT_DESVIOS) 
    CASO += 'Fref_{:1d}_'.format(OR_PRE_EXCLUIDO) + 'Pref_{:04.2f}_'.format(PRECIO_F_EXCLUIDO) + ('PfL_{:05.3f}_'.format(VALOR_F_TRA) if  VALOR_F_TRA != -1 else '')
    CASO += ('END' if FF_ENDOGENA else 'EXO') + '_Alp_{:04.2f}'.format(ALP_FACTOR)
    CASO += '_DimPb_{:03}_W_{:03}_'.format(GE_DIM_POBLACION, GE_WORKERS) + etq_sam[NSAM]
    for nc in NCASO:
        CASO += '_' + etq_caso[nc] 
    CASO += '_' + GE_ESTRATEGIA + '_' + 'Mcu' if METRICA_ERROR == 0 else ('Mab' if METRICA_ERROR == 1 else 'Mpt' + str(POT_DESVIOS))
    CASO += '_Da_{:1}_{}'.format(DEM_ADICIONAL_TIPO,'SR' if RENTA_FICTICIA else 'CR') if abs(DEM_ADICIONAL).sum() != 0 else ''
    CASO += '_Ay_' if abs(AYD_ADICIONAL).sum() != 0 else ''
    CASO += ('_Rst_' + str(GE_TIPO_RE) if GE_RESTRICCIONES else '') + ('_Fix_{:03}'.format(len(FIX)) if len(FIX) > 0 else '')
    CASO += '_{:05}'.format(GE_SEMILLA)

FICHERO_IMG     = CASO
SENDA_FI_SALIDA = '{}/{}'.format(SENDA_SALIDAS, CASO)
FICHERO_LOG     = SENDA_FI_SALIDA + '.log'
FI_HISTORIAL    = SENDA_FI_SALIDA + '_his.csv'
FI_SOLUCIONES   = SENDA_FI_SALIDA + '_sol.csv'

# preparar para usar la función 'imprime', que llama a la del módulo 'mfun' del mismo nombre, pasándole el nombre del fichero donde escribir
mfun.ini(FICHERO_LOG)
def imprime(texto, rc=True):
    mfun.imprime(texto, rc)

# ya que sabemos el nombre del fichero de log, podemos escribir los mensajes de error y avisos
if len(avisos_diferidos) > 0:
    imprime('')
    imprime('....................................................................................................................................')
    for mensaje in avisos_diferidos:
        imprime('Aviso. ' + mensaje)
    imprime('....................................................................................................................................')
    imprime('')
if len(errores_diferidos) > 0:
    imprime('')
    imprime('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
    for mensaje in errores_diferidos:
        imprime('Error. ' + mensaje)
    imprime('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
    # con errores se cancela la aplicación
    sys.exit()

def punteros():
    # para saber la posición de las distintas variables en el vector solución en el que están
    # todas concatenadas una tras otra. Se usará en la función 'extrae_var'
    etq_vec_opt = ['pF','pY','pQ','pD','epsilon','Apz','F','E','M','D']
    if GE_INCLUYE_XP:
        etq_vec_opt.append('Xp')
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
    if GE_INCLUYE_XP:
        i += 1  # Xp
        pvec_desde[i] = pvec_hasta[i - 1] 
        pvec_hasta[i] = pvec_desde[i] + datos.Xp0.size
    ind_pvec_desde = Series(pvec_desde, index=etq_vec_opt)
    ind_pvec_hasta = Series(pvec_hasta, index=etq_vec_opt)
    return (etq_vec_opt,ind_pvec_desde,ind_pvec_hasta)

def extrae_var(vp, clave, nfil, ncol):
    # extrae del vector solución los valores correspondientes a la variable 'clave' y le da el formato de filas y columnas adecuado
    vendo = vp[ind_pvec_desde[clave]:ind_pvec_hasta[clave]]
    if nfil > 0:
        # una matriz con 'nfil' filas
        if ncol == 0:
            # una sola columna
            return vendo.reshape(nfil)
        return vendo.reshape(nfil, ncol)
    else:
        if ncol == 0:
            # sin filas ni columnas es un escalar
            return vendo.item()
        # es un vector
        return vendo

def cotas(ndem, nsec, vec_opt, nvec_opt, npre_sol, ind_pvec_desde):
    # definir el rango de variación de los precios y variables en LA SOLUCION A PROBAR 'vec_opt'
    # primero rellenamos 'bnds' con 0 y luego lo iremos modificando
    bnds = []
    for i in range(nvec_opt):
        bnds.append((0.,0.))

    # limites con criterio general para todas las variables en el vector solución
    #----------------------------------------------------------------------------
    # en el vector solución sólo se incluye el precio de un factor y sus cotas están en la posición 0 de 'bnds' con
    # indepemdencia de que sea el del capital, o el del trabajo
    if OR_PRE_EXCLUIDO == 1:
        # if 'OR_PRE_EXCLUIDO' es 1 (trabajo), en el vector solución debe estar el de capital como variable endogena,
        # sin valor fijo, con el rango establecido para los precios
        v = vec_opt[0]
        vi = v * (1. - GE_PRE_MIN / 100.)
        vs = v * (1. + GE_PRE_MAX / 100.)
    elif OR_PRE_EXCLUIDO == 0:
        # if 'OR_PRE_EXCLUIDO' es 0 (capital), en el vector solución está el precio del trabajo
        if VALOR_F_TRA > 0:
            # si VALOR_F_TRA es > 0 el precio del trabajo es el valor fijo VALOR_F_TRA
            vi = VALOR_F_TRA
            vs = VALOR_F_TRA
        elif VALOR_F_TRA == 0:
            #aunque en el vector solución se incluye el precio del tabajo su valor no se usará porque se calcula con la fórmula Phillips, por
            # lo tanto le pondremos un valor fijo (1.) para que el algoritmo genético no "pruebe" valores para él
            vi = 1.
            vs = 1.
        elif VALOR_F_TRA == -1:
            # Si VALOR_F_TRA = -1 el precio del factor trabajo es endógeno, sin valor fijo, con el rango establecido para los precios
            v = vec_opt[0]
            vi = v * (1. - GE_PRE_MIN / 100.)
            vs = v * (1. + GE_PRE_MAX / 100.)
        else:
            imprime('El valor de VALOR_F_TRA {} no es válido. Debe ser -1, 0 o un valor positivo.\n'.format(VALOR_F_TRA))
            sys.exit()
    bnds[0] = ((vi,vs))
    for i in range(1, nvec_opt):
        v = vec_opt[i]
        if abs(v) < 0.001:
            # para evitar que las variables inicialmente a 0, queden acotados a (0,0)
            if i < npre_sol:
                # aunque no tiene mucho sentido un precio inicialmente a 0, le ponemos un rango razonable: positivo a partir de 0
                vi = 0.
                vs = 3.
            else:
                vi = np.float64(-GE_VAR_CERO)
                vs = np.float64(+GE_VAR_CERO)
        else:
            if i < npre_sol:
                vi = v * (1. - GE_PRE_MIN / 100.)
                vs = v * (1. + GE_PRE_MAX / 100.)
            else:
                vi = v * (1. - GE_VAR_MIN / 100.)
                vs = v * (1. + GE_VAR_MAX / 100.)
        bnds[i] = ((vi,vs))

    # procesamos las especificaciones explicitas de límites (especificadas manualmente)
    #----------------------------------------------------------------------------------
    if len(FIX) > 0:
        for n in range(len(FIX)):
            # 'n' es la fila de 'FIX_LIMITES' que corresponde a la variable
            clave = FIX[n]
            # puntero al inicio de la variable
            i = ind_pvec_desde[clave]
            # para cada terna 'j' de limites de la variable 'n'
            for j in range(len(FIX_LIMITES[n])):
                # 'k' es el primer elemento de la terna y es el índice dentro de la variable (desplazamiento desde su origen)
                k = FIX_LIMITES[n][j][0]
                # límite inferior
                if type(FIX_LIMITES[n][j][1]) is str:
                    # cualquier caracter hace que se ponga el valor inicial de la variable en el vector de prueba
                    vi = vec_opt[i + k]
                else:
                    # ...[1] es el segundo elemento, de la terna 'j', de la variable 'n'
                    vi = FIX_LIMITES[n][j][1]
                # límite superior
                if type(FIX_LIMITES[n][j][2]) is str:
                    # cualquier caracter hace que se ponga el valor inicial de la variable en el vector de prueba
                    vs = vec_opt[i + k]
                else:
                    # ...[2] es el tercere elemento, de la terna 'j', de la variable 'n'
                    vs = FIX_LIMITES[n][j][2]
                bnds[i + k] = ((vi,vs))
            # <- fin de la terna 'j'
        # <- fin de la variable 'n'

    if GE_INCLUYE_XP and abs(CON_ESENCIALES).sum() != 0:
        # acotar consumos de los hogares Xp
        i = ind_pvec_desde['Xp']
        for j in range(ndem):
            for k in range(nsec):
                vi = CON_ESENCIALES[j][k]
                bnds[i] = (vi,bnds[i][1])
                i += 1
    # si no hay exportaciones o importaciones en la MCS, nuestro modelo las mantendrá a cero, por lo tanto, fijamos sus
    # intervalos en (0, 0), igual valor mínimo que máximo, para que el algoritmo genético no pierda tiempo "probando" valores para ellos
    n_Efijas = 0
    i = ind_pvec_desde['E']
    for j in range(nsec):
        if abs(vec_opt[i]) < 0.000001:
            vec_opt[i] = 0.
            bnds[i] = (0., 0.)
            n_Efijas += 1
        i += 1
    n_Mfijas = 0
    i = ind_pvec_desde['M']
    for j in range(nsec):
        if abs(vec_opt[i]) < 0.000001:
            vec_opt[i] = 0.
            bnds[i] = (0., 0.)
            n_Mfijas += 1
        i += 1

    # ajustar los entornos de validez al valor mínimo de intervalo ''GE_VAR_CAN_MIN'
    if GE_VAR_CAN_MIN > 0:
        cuenta = 0
        for i in range(npre_sol, nvec_opt):
            ancho = bnds[i][1] - bnds[i][0]
            if ancho > 0.000001 and ancho < GE_VAR_CAN_MIN:
                cuenta += 1
                d = (GE_VAR_CAN_MIN - ancho) / 2.
                vi = bnds[i][0] - d
                if vi < 0. and bnds[i][0] > 0:
                    vi = 0.000001
                    vs = GE_VAR_CAN_MIN
                else:
                    vs = bnds[i][1] + d
                #imprime('{:6d} {:12.5e} {:12.5e}   {:12.5e} {:12.5e}'.format(i, bnds[i][0], bnds[i][1], vi, vs))
                bnds[i] = (vi,vs)
        if cuenta > 0:
            if __name__ == '__main__':
                imprime('*--* Se han modificado {} intervalos para ajustarlos al valor mínimo'.format(cuenta))
                imprime('')
    #-------------------------------------------------------------------------------------------------------------------------------------    
    # resulta increible el papel de Apz, si no se deja libre en un intervalo grande (-GE_VAR_CERO, +GE_VAR_CERO), no se encuentra solución
    #-------------------------------------------------------------------------------------------------------------------------------------    
    return (bnds, n_Efijas, n_Mfijas)

def completa_pf(pf, F):
    # 'parche' para completar el vector de precios de los factores 'pf' con el precio del factor excluido (capital o trabajo), que no forma parte del
    # vector solución por culpa de un mal planteamiento de partida de la aplicación.
    if OR_PRE_EXCLUIDO == 1:
        # el precio del factor OR_PRE_EXCLUIDO no forma parte del vector solución, luego
        # si es 1, el trabajo es el que no forma parte y estará prefijado (PRECIO_F_EXCLUIDO) o debemos calcularlo (precio_factor_trabajo_pFL)

        # Como el vector de prueba no incluye el precio del último factor (el trabajo), AÑADIMOS al final de 'pf' el precio del
        # último factor con valor 'PRECIO_F_EXCLUIDO' si VALOR_F_TRA > 0 o lo calculamos con la curva Phillips si VALOR_F_TRA = 0
        if VALOR_F_TRA == 0:
            pf = np.append(pf, deho.precio_factor_trabajo_pFL(INDICE_F_TRA, datos.PobAct, ALFA_PHILLIPS, datos.pF0[INDICE_F_TRA], datos.F0, F))
        else:
            # se fja el precio del capital en PRECIO_F_EXCLUIDO
            pf = np.append(pf, np.array([PRECIO_F_EXCLUIDO]))
    else:
        # Como el vector de prueba no incluye el precio del primer factor (el capital), INSERTAMOS al principio de 'pf' el
        # precio del primer factor con valor 'PRECIO_F_EXCLUIDO' 
        pf = np.insert(pf, 0, np.array([PRECIO_F_EXCLUIDO]))

        if VALOR_F_TRA == 0:
            # El precio del factor trabajo es el único que está incluido en el vector de prueba pero
            # no se usará ya que se calcula con la curva Phillips
            pf[INDICE_F_TRA] = deho.precio_factor_trabajo_pFL(INDICE_F_TRA, datos.PobAct, ALFA_PHILLIPS, datos.pF0[INDICE_F_TRA], datos.F0, F)
        elif VALOR_F_TRA > 0:
            # si VALOR_F_TRA == 1 el precio del factor trabajo está fijado en VALOR_F_TRA, tampoco se usará el
            # incluido en el factor de prueba  
            pf[INDICE_F_TRA] = VALOR_F_TRA 
        # Si VALOR_F_TRA = -1 el precio del factor trabajo es endógeno, es decir, es el incluido en el vector de prueba

    return pf

def sec_ecuaciones(vec_opt):
    '''
    Elemento esencial de la función objetivo que calcula el demérito (penalización, o falta de aptitud) de la solución de
    prueba 'vec_opt'.
    
    Esta función calcula una pareja de valores para cada variable y los pasa a la función 'fun_objetivo'
    en realidad es 'fun_objetivo' quien llama a esta función para luego pasar el resultado a
    la función 'calcula_desvios' que los resta entre sí y devuelve un valor escalar que
    es el valor que devolverá 'fun_objetivo'.
    Esta secuencia de llamadas es útil porque en otras partes de la aplicación necesitamos los valores
    calculados por esta función y no sirve llamar a 'fun_objetivo' que solo devuelve un escalar, así
    mismo, en otros momentos necesitamos calcular los desvíos y de aquí que estos se calculen en
    una función a propósito.

    No tiene sentido que la función 'differential_evolution' pruebe valores para otras variables que no sean las
    que aquí se extraen, porque su valor no se usará ya que son recalculadas inmediatamente en
    esta función, con independencia del valor que tengan en el vector de prueba

    Podría pensarse en mejorar la eficiencia de esta función si en el momento en que los dos
    cálculos de una variable difieran significtivamente, no seguir calculando, pero es un error,
    necesitamos asignar un valor a cada solución de prueba y poder diferenciar unas de otras por su
    verdadero mérito lo que exige calcular todas las parejas de valores.
    '''
    # extraemos los precios del vector de prueba 'vec_opt'
    py = extrae_var(vec_opt, 'pY', 0, nsec)
    pq = extrae_var(vec_opt, 'pQ', 0, nsec)
    pd = extrae_var(vec_opt, 'pD', 0, nsec)
    epsilon = extrae_var(vec_opt, 'epsilon', 0, 0)
    
    # variable de holgura
    Apz = extrae_var(vec_opt, 'Apz', 0, nsec)

    # extraemos los valores de las 'variables de inicio' del vector de prueba 'vec_opt'
    F  = extrae_var(vec_opt, 'F', nsec, nfac)
    E  = extrae_var(vec_opt, 'E', 0, nsec)
    M  = extrae_var(vec_opt, 'M', 0, nsec)
    D  = extrae_var(vec_opt, 'D', 0, nsec)

    # guardamos los valores de la solución de prueba para luego compararlos con los calculados.

    # hay que tener mucho cuidado al igualar variables porque lo que se hace es igualar el puntero
    # de ambas (la posición de la memoria a la que apuntan) de forma que al modificar una, estaremos
    # modificando la otra, aunque no sea lo que queramos. Usamos ‘copy.deepcopy’ que no iguala punteros
    # hace una copia independiente en otra parte de la memoria.
    Fi = copy.deepcopy(F)
    Ei = copy.deepcopy(E)
    Mi = copy.deepcopy(M)
    Di = copy.deepcopy(D)
    if GE_INCLUYE_XP:
        # el vector solución incluye los consumos de los hogares, necesario si se quiere acotar el
        # valor de los mismos, por ejemplo, para usar una función de utilidad con consumos esenciales
        Xpi = copy.deepcopy(extrae_var(vec_opt, 'Xp', ndem, nsec))

    # el precio de los factores tiene un tratamiento especial, en el vector solución solo se incluye
    # un precio: el del capital o el del trabajo, según OR_PRE_EXCLUIDO sea 0 o 1
    pf = extrae_var(vec_opt, 'pF', 0, nfac - 1)
    # if OR_PRE_EXCLUIDO == 0 and VALOR_F_TRA == 0:
    #   el valor en el vector de solución no se usará
    #   el del capital se fija (OR_PRE_EXCLUIDO == 0) y el del trabajo se calcula (VALOR_F_TRA)

    # para los cálculos en esta función, el precio del otro factor se añade al principio o al final de 'pf'
    pf = completa_pf(pf, F)

    # calculamos los precios del comercio internacional en moneda local
    (pe, pm) = exte.precio_moneda_local_pe_pm(datos.pWe, datos.pWm, epsilon)            # 6.14 y 6.15
    
    # Los coeficientes de consumos intermedios 'ax' y factor compuesto 'ay' se consideran constantes.
    # no hay problema en igualar las variables porque ni 'ax' ni 'ay' se van a modificar y por tanto
    # ni 'parametros.ax' ni 'parametros.ay' se verán afectados
    ax = parametros.ax
    ay = parametros.ay
    
    #--------------------------------------------------------------------------------------------------
    # Calculamos el valor de todas las variables endógenas aplicando todas las ecuaciones del
    # modelo, siguiendo el orden del libro de referencia (con algunas excepciones), el número 6.??
    # de la ecuación es porque están en el capítulo 6 del libro
    #--------------------------------------------------------------------------------------------------

    # Producción
    #--------------------------------------------------------------------------------------------------
    # (Y) factor compuesto óptimo, para cada sector, dadas las utilizaciones de factores de
    # producción (F) y la función de producción Cobb Douglas correspondiente.
    # en el equilibrio debe ser igual a la necesidad (Yd) de factor compuesto dada una producción bruta (Z) (6. 4)
    Yp = prod.produccion_factor_compuesto_Y(F, parametros.beta, parametros.b)           # 6. 1
    
    # traemos el cálculo de (Z) aquí porque solo depende de las endógenas (E) y (D) que forman parte del vector de prueba
    # el reparto de la producción bruta de un sector (Z) entre exportación (E) y suministro local (D) debe cumplir la
    # relación siguiente
    Z  = exte.restriccion_produccion_bruta_Z(parametros.teta, parametros.xie, parametros.xid, E, D, parametros.phi) # 6.20

    # dada la producción (Z) del sector 'i' (demanda de su producto) calculamos la utilización (X) de
    # consumos intermedios 'j', que hace 'i' por aplicación de los coeficientes 'ax' deducidos de la MCS
    X = prod.consumo_intermedio_X(Z, ax)                                                # 6. 3

    # la utilización (consumo) de factor compuesto por cada sector no es más que su 
    # producción bruta (Z) por lo que necesita por unidad de producción (ay)
    Yd = prod.utilizacion_factor_compuesto_Y(Z, ay)                                     # 6. 4

    # recalculamos los (F) óptimos de los sectores. En el equilibrio los (F) recalculados deben coincidir con los
    # (Fi) utilizados en el cálculo de 'Yp' que se ha hecho antes.
    # Esta ecuación determina la combinación óptima de factores, el total de los mismos (Yp) para cada sector debe coincidir
    # con (Yd) que es el obtenido en la ecuación (6.4), es decir, igual al producto del parámetro de factores necesarios por
    # unidad de produción (ay) por la producción bruta (Z).
    # de momento usamos la media de los dos cálculos de (Y)
    F = prod.uso_optimo_factores_F(parametros.beta, pf, py, (Yp + Yd) / 2.)             # 6. 2

    # producción bruta, se usa la ecuación alternativa que no necesita el cálculo de un valor mínimo
    pz = prod.coste_unitario_produccion_pz(ay, py, ax, pq)                              # 6. 5 alternativa

    # la variación de la suma del factor compuesto, respecto del factor compuesto de la MCS,
    # es la variación de factores de producción que deben aportar los hogares (FF).
    # en el caso de que los (FF) sean constantes la ecuación de cierre exige que la suma de
    # variaciones sea cero.
    # Si (FF) es endógena, esto es lo que hay que incrementar (FF0)
    if  FF_ENDOGENA:
        # se calcula la aportación de factores (FF) como igual a la necesidad de factores (F) por los sectores.
        # en el equilibrio (F) debe ser igual al parámetro de factores necesarios por unidad de
        # produción (ay) por la producción bruta (Z) (6.4)
        FF = deho.aportacion_factores_FF(datos.FF0, F)
        if ALP_FACTOR > 0:
            # se ahorra a largo plazo (Alp) un porcentaje del exceso de ingresos (FF) respecto a los iniciales (FF0)
            # lo que significa que no se usará en comprar productos
            # en la medida que ALP_FACTOR sea mayor que 0, el modelo se realimenta, además de por los consumos internos, por la demanda final.
            exceso = FF - datos.FF0
            Alp = exceso * ALP_FACTOR
            FF -= Alp
        else:
            Alp = datos.Alp0
    else:
        # la igualación es correcta porque ni 'FF' ni 'Alp' los vamos a cambiar
        FF = datos.FF0
        Alp = datos.Alp0

    # Gobierno
    #--------------------------------------------------------------------------------------------------
    # impuestos
    Td = gob.impuestos_directos_Td(parametros.taud, pf, FF, Alp, datos.PssH0)           # 6. 6
    Tz = gob.impuestos_produccion_Tz(datos.tauz, pz, Z)                                 # 6. 7
    Tm = gob.aranceles_importacion_Tm(datos.taum, pm, M)                                # 6. 8

    # horro (privado -hogares- y del gobierno). Se invertirán íntegramente (menos impuestos) en los sectores
    # las calculamos antes que 6. 9, 6.10 y 6.11, porque mo dependen de los resultados de estas y sin
    # embargo 6. 9, 6.10 y 'Ti' si dependen del ahoro. El ahorro a corto plazo es por tanto sin Alp
    #--------------------------------------------------------------------------------------------------
    Sp = ainv.ahorro_hogares_Sp(parametros.ssp, FF, pf, datos.PssH0)                    # 6.11
    
    # solo calculamos impuestos a la inversión de los hogares (inversores) porque los que el gobierno pague son un ingreso para él
    Ti = gob.impuestos_directos_Ti(parametros.tai, pf, FF, INDICE_F_TRA)

    # ayudas (pagos) del gobierno a las empresas, un porcentaje de lo recaudado por impuestos
    AgE  = gob.ayudas_empresas_AgE(parametros.cage, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0)
    # ayudas (pagos) del gobierno a los hogares, un porcentaje de lo recaudado por impuestos
    AgH  = gob.ayudas_hogares_AgH(parametros.cagh, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AYD_ADI_DEM)

    # Seguridad social
    # los pagos de la seguridad social a los hogares (pensiones -PssH0-) es un valor constante fijado de antemano (exógena).
    #--------------------------------------------------------------------------------------------------
    # cotizaciones a la seguridad social, un porcentaje del factor trabajo:

    #   de las empresas. (F) es la utilización de factores de cada sector
    CssE = gob.seguridad_social_empresas_CssE(parametros.ctzsse, pf, F, INDICE_F_TRA)
    #   de los hogares. (FF) es la prestación de factores de cada hogar (consumidor)
    CssH = gob.seguridad_social_hogares_CssH(parametros.ctzssh, pf, FF, Alp, INDICE_F_TRA)

    # ahorro del gobierno
    Sg = ainv.ahorro_gobierno_Sg(parametros.ssg, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AgE, AgH, datos.PssH0, CssH, CssE)           # 6.12

    # El gobierno compra productos con cargo a sus ingresos disponibles que son lo que recauda por
    # impuestos menos su ahorro (Sg) y las ayudas a empresas (AgE) y hogares (AgH)
    Xg = gob.demanda_gobierno_Xg(parametros.mu, pq, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, Sg, AgE, AgH, datos.PssH0, CssH, CssE)    # 6. 9

    # Inversión con cargo a los ahorros: los ahorros privados (Sp), del gobierno (Sg) y del
    # exterior (Sf0), se reparten entre sectores proporcionalmente a la MCS (parametros.landa)
    #--------------------------------------------------------------------------------------------------
    # superhavit / déficit de la seguridad social
    if datos.PssH0.sum() == 0:
        # si no se han explicitado pensiones en la MCS, suponemos que es el gobierno quien las paga
        # y no ha lugar un déficit o superhabit de la seguridad social. Esto es un truco para que el modelo trabaje
        # con las 7 MCS que hemos definido, ya que algunas no tienene separada la cuenta de la seguridad social.
        Sc = 0.
    else:
        Sc = CssE.sum() + CssH.sum() - datos.PssH0.sum()
    if EQ_BAL_PAGOS:
        # mantener la balanza de pagos igual a la inicial (MCS)
        Sf = np.float64(datos.Sf0)    
    else:
        # la balanza de pagos no tiene un valor predeterminado, no es una opción realista
        Sf = ainv.ahorro_exterior_Sf(M, E, pm, pe)
    Xv = ainv.demanda_inversion_Xv(parametros.landa, pq, Sp, Sg, Sc, epsilon, Sf, Ti, datos.Te0)    # 6.10

    # Consumo de productos de los hogares. Mediante la función que optimiza la utilidad (pq, parametros.alfa) a
    # partir de los ingresos netos:
    # ingresos brutos: (pf, FF) + datos.PssH0 + AgH. El consumo es sin el Alp
    # gastos         : Sp + Td + CssH 
    #--------------------------------------------------------------------------------------------------
    if DEM_ESENCIALES:
        # función de demanda con consumos esenciales (Stone Geary)
        Xp = deho.demanda_maxima_utilidad_StoneGeary_Xp(parametros.alfa_esen, CON_ESENCIALES, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL, RENTA_FICTICIA)  # 6.13
    else:
        if UTILIDAD_DEMANDA == 0:
            # función de demanda Cobb Douglas
            Xp = deho.demanda_maxima_utilidad_CobbDouglas_Xp(parametros.alfa, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL, RENTA_FICTICIA)
        else:
            # función de demanda CES
            Xp = deho.demanda_maxima_utilidad_CES_Xp(parametros.eta_ces, parametros.alfa_ces, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL, RENTA_FICTICIA)

    # función CES de sustitución con la que determinar el óptimo entre importar (M) o
    # producir localmente (D), la demanda del producto de Armington (Q)
    #--------------------------------------------------------------------------------------------------

    # Armington. Cálculo circular: calculamos Q en función de M y D y luego calculamos M y D en función de Q
    Q  = exte.produccion_armington_Q(parametros.gamma, parametros.deltam, parametros.deltad, M, D, parametros.eta)                  # 6.17
    M  = exte.importacion_maxima_utilidad_armington_M(parametros.gamma, parametros.deltam, pq, pm, Q, parametros.eta, datos.taum)   # 6.18
    Da = exte.produccion_maxima_utilidad_armington_D(parametros.gamma, parametros.deltad, pq, pd, Q, parametros.eta)                # 6.19

    # Función CET de transformación de la producción bruta (Z), en producto para exportación (E) y para suministro local (D)
    #--------------------------------------------------------------------------------------------------
    
    # Cálculo circular, (Z) es función (6.20) de (E) y (D) y luego (E) y (D) son función (6.21 y 6.22) de (Z)
    # hay que considerar la cotización a la seguridad social (CssE) como un mayor coste de la producción bruta (Z) en
    # el cálculo de (E) y (D), es decir, hay que incrementar (pz) por los pagos a la seguridad social al
    # igual que con los impuestos a la producción (tauz), en la misma línea hay que descontar las ayudas (AgE)
    E  = exte.produccion_para_exportacion_E(parametros.teta, parametros.xie, pz, pe, Z, parametros.phi, datos.tauz, CssE, AgE, Apz, parametros.ctzssez, parametros.ctzagez, MODO_PSEUDOIMPTOS) # 6.21
    Dt  = exte.produccion_para_local_D(parametros.teta, parametros.xid, pz, pd, Z, parametros.phi, datos.tauz, CssE, AgE, Apz, parametros.ctzssez, parametros.ctzagez, MODO_PSEUDOIMPTOS)      # 6.22

    # Comercio internacional. Lo traemos aquí para usar los últimos valores calculados para E y M
    #--------------------------------------------------------------------------------------------------
    # Restricción a la balanza de pagos, las exportaciones menos las importaciones en divisas se debe mantener igual al valor inicial 'Sf0'
    # ya que debe haber una correlación entre los ingresos (exportaciones) y pagos (importaciones) en divisas: la que muestra la MCS

    # restricción a la balanza de pagos, las importaciones deben ser igual a las exportaciones más
    # la balanza de pagos inicial (datos.Sf0), que es exógena, en moneda extranjera
    if EQ_BAL_PAGOS:
        # se calculará el desvio en la balanza de pagos respecto al valor de la MCS
        ebp = exte.equilibrio_balance_pagos_moneda_extranjera(datos.pWe, E, datos.pWm, M, Sf)                                       # 6.16
    else:
        # el desvio por la balanza de pagos será exclusivamente por la diferencia entre 'Sf' y 'Sfr', no por 'ebp' 
        ebp = np.float64(0.)
    
    # Leontief para comparar, no tiene otro uso
    Zl = prod.produccion_sector_Z(X, ax, Yd, ay)                                                                                    # 6. 5 original
    
    '''
    Para calcular el demerito de la solución de prueba 'vec_opt', que recibe está función como argumento,
    recalculamos las variables para ver cuánto se diferencian del cálculo previo.
    para que el demérito sea el correcto hay que recalcular todas las variables.
    '''

    Zr    = exte.restriccion_produccion_bruta_Z(parametros.teta, parametros.xie, parametros.xid, E, Dt, parametros.phi)             # 6.20
    Ypr   = prod.produccion_factor_compuesto_Y(F, parametros.beta, parametros.b)                                                    # 6. 1
    Fr    = prod.uso_optimo_factores_F(parametros.beta, pf, py, Ypr)                                                                # 6. 2
    Xr    = prod.consumo_intermedio_X(Zr, ax)                                                                                       # 6. 3
    Ydr   = prod.utilizacion_factor_compuesto_Y(Zr, ay)                                                                             # 6. 4

    if  FF_ENDOGENA:
        FFr = deho.aportacion_factores_FF(datos.FF0, Fr)
        if ALP_FACTOR > 0:
            exceso = FFr - datos.FF0
            Alpr = exceso * ALP_FACTOR
            FFr -= Alp
        else:
            Alpr = datos.Alp0
    else:
        FFr  = datos.FF0
        Alpr = datos.Alp0

    Tdr   = gob.impuestos_directos_Td(parametros.taud, pf, FFr, Alpr, datos.PssH0)          # 6. 6
    Tzr   = gob.impuestos_produccion_Tz(datos.tauz, pz, Zr)                                 # 6. 7
    Tmr   = gob.aranceles_importacion_Tm(datos.taum, pm, M)                                 # 6. 8

    Spr   = ainv.ahorro_hogares_Sp(parametros.ssp, FFr, pf, datos.PssH0)                    # 6.11
    Tir   = gob.impuestos_directos_Ti(parametros.tai, pf, FFr, INDICE_F_TRA)
    
    AgEr  = gob.ayudas_empresas_AgE(parametros.cage, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0)
    AgHr  = gob.ayudas_hogares_AgH(parametros.cagh, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, AYD_ADI_DEM)
    CssEr = gob.seguridad_social_empresas_CssE(parametros.ctzsse, pf, Fr, INDICE_F_TRA)
    CssHr = gob.seguridad_social_hogares_CssH(parametros.ctzssh, pf, FFr, Alpr, INDICE_F_TRA)
    Sgr   = ainv.ahorro_gobierno_Sg(parametros.ssg, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, AgEr, AgHr, datos.PssH0, CssHr, CssEr)            # 6.12
    Xgr   = gob.demanda_gobierno_Xg(parametros.mu, pq, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, Sgr, AgEr, AgHr, datos.PssH0, CssHr, CssEr)    # 6. 9
    if datos.PssH0.sum() == 0:
        Scr = 0.
    else:
        Scr = CssEr.sum() + CssHr.sum() - datos.PssH0.sum()

    if EQ_BAL_PAGOS:
        Sfr = np.float64(datos.Sf0)    
    else:
        Sfr = ainv.ahorro_exterior_Sf(M, E, pm, pe)
    Xvr   = ainv.demanda_inversion_Xv(parametros.landa, pq, Spr, Sgr, Scr, epsilon, Sfr, Tir, datos.Te0)   # 6.10
    if DEM_ESENCIALES:
        Xpr   = deho.demanda_maxima_utilidad_StoneGeary_Xp(parametros.alfa_esen, CON_ESENCIALES, pq, pf, FFr, Spr, Tdr, CssHr, AgHr, datos.PssH0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL, RENTA_FICTICIA)
    else:
        if UTILIDAD_DEMANDA == 0:
            # función de demanda Cobb Douglas
            Xpr = deho.demanda_maxima_utilidad_CobbDouglas_Xp(parametros.alfa, pq, pf, FFr, Spr, Tdr, CssHr, AgHr, datos.PssH0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL, RENTA_FICTICIA)
        else:
            # función de demanda CES
            Xpr = deho.demanda_maxima_utilidad_CES_Xp(parametros.eta_ces, parametros.alfa_ces, pq, pf, FFr, Spr, Tdr, CssHr, AgHr, datos.PssH0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL, RENTA_FICTICIA)
    Qr    = exte.produccion_armington_Q(parametros.gamma, parametros.deltam, parametros.deltad, M, Dt, parametros.eta)                      # 6.17
    Mr    = exte.importacion_maxima_utilidad_armington_M(parametros.gamma, parametros.deltam, pq, pm, Qr, parametros.eta, datos.taum)       # 6.18
    Dar   = exte.produccion_maxima_utilidad_armington_D(parametros.gamma, parametros.deltad, pq, pd, Qr, parametros.eta)                    # 6.19
    Er    = exte.produccion_para_exportacion_E(parametros.teta, parametros.xie, pz, pe, Zr, parametros.phi, datos.tauz, CssEr, AgEr, Apz, parametros.ctzssez, parametros.ctzagez, MODO_PSEUDOIMPTOS)   # 6.21
    Dtr   = exte.produccion_para_local_D(parametros.teta, parametros.xid, pz, pd, Zr, parametros.phi, datos.tauz, CssEr, AgEr, Apz, parametros.ctzssez, parametros.ctzagez, MODO_PSEUDOIMPTOS)         # 6.22
    if EQ_BAL_PAGOS:
        # se calculará el desvio en la balanza de pagos respecto al valor de la MCS (Sfr = Sf0)
        ebpr  = exte.equilibrio_balance_pagos_moneda_extranjera(datos.pWe, Er, datos.pWm, Mr, Sfr)                                        # 6.16
    else:
        # el desvio por la balanza de pagos será exclusivamente por la diferencia entre 'Sf' y 'Sfr', no por 'ebp' 
        ebpr = np.float64(0.)

    if GE_INCLUYE_XP == False:
        Xpi = Xp

    res_ecuaciones = (Apz,Fi,Ei,Mi,Di,Xpi,pf,pq,pe,pm,
            Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,Sf ,AgE ,AgH ,CssE ,CssH, ebp,Zl,pz,
            Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,Sfr,AgEr,AgHr,CssEr,CssHr,ebpr,
            Ti,Tir
    )
    return res_ecuaciones

def calcula_desvios(res_ecuaciones, muestra_progreso):
    '''
    Calcula los desvíos (penalización) correspondientes a la ejecución de las ecuaciones 'sec_ecuaciones'
    '''
    (Apz,Fi,Ei,Mi,Di,Xpi,pf,pq,pe,pm,
        Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,Sf ,AgE ,AgH ,CssE ,CssH, ebp, Zl, pz,
        Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,Sfr,AgEr,AgHr,CssEr,CssHr,ebpr,
        Ti,Tir
    ) = res_ecuaciones

    # Se trata de forma individualizada la desviación, en valor absoluto, de cada variable

    # Apz es como los precios, no es el resultado de ninguna ecuación y por tanto no procede
    # calcular un desvío para ella

    if EQ_BAL_PAGOS:
        # 'ebp' y 'ebpr' deben ser ambas cero
        des_ebp = np.array([abs(ebp) + abs(ebpr)])
        des_Sf  = np.array([0.])    
    else:
        # el desvio por la balanza de pagos será exclusivamente por la diferencia entre 'Sf' y 'Sfr', no por 'ebp' 
        des_ebp = np.array([0.])
        des_Sf  = abs(Sfr  - Sf  ).flatten()    

    # condiciones de equilibrio del mercado.
    #   Xp.sum(axis=0) = suma de lo que vende un sector a los hogares  = suma de los que compran todos los hogares a ese sector
    #   Xg             = suma de las ventas de cada sector al gobierno = lo que compra el gobierno a cada sector
    #   Xv             = suma de lo ingresado por cada sector como inversiones
    #   X.sum(axis=1)  = suma de lo que vende cada sector a los otros sectores (ventas intermedias)

    des_produccion = abs(Qr - (Xpr.sum(axis=0) + Xgr + Xvr + Xr.sum(axis=1))).flatten()      # 6.23

    # la utilización total de cada factor por los sectores 'F.sum(axis=0)' debe ser igual a la
    # aportación de los mismos por los hogares 'FF.sum(axis=0)'
    if  FF_ENDOGENA:
        # ya está garantizado el cumplimiento de la ecuación 6.24, luego no hay desvios por este concepto
        des_factores   = np.zeros(nfac, dtype=np.float64)
        if ALP_FACTOR > 0:
            # el desglose de los ahorros por factor es importante porque cada factor tiene su precio y la renta disponible
            # para adquirir productos depende de ello
            des_Alp        = abs(Alpr - Alp).flatten()
        else:
            des_Alp        = np.zeros(ndem, dtype=np.float64)
    else:
        des_factores   = abs(Fr.sum(axis=0) - FFr.sum(axis=0)).flatten()  # 6.24
        des_Alp        = np.zeros(ndem, dtype=np.float64)

    des_Fi         = abs(Fr   - Fi  ).flatten()    
    des_Ei         = abs(Er   - Ei  ).flatten()    
    des_Mi         = abs(Mr   - Mi  ).flatten()
    des_Di         = abs(Dar  - Di  ).flatten()
    if GE_INCLUYE_XP:
        des_Xpi = abs(Xpr  - Xpi ).flatten()    
    else:
        des_Xpi = np.array([0], dtype=np.float64)
    des_F          = abs(Fr   - F   ).flatten()
    des_E          = abs(Er   - E   ).flatten()    
    des_M          = abs(Mr   - M   ).flatten()    

    des_FF         = abs(FFr  - FF  ).flatten()
    des_Ydp        = abs(Ydr  - Ypr ).flatten()    
    des_Dat        = abs(Dar  - Dtr ).flatten()    

    des_Z          = abs(Zr   - Z   ).flatten()
    des_X          = abs(Xr   - X   ).flatten()    
    des_Xp         = abs(Xpr  - Xp  ).flatten()
    des_Xg         = abs(Xgr  - Xg  ).flatten()    
    des_Xv         = abs(Xvr  - Xv  ).flatten()    
    des_Q          = abs(Qr   - Q   ).flatten()    
    des_Td         = abs(Tdr  - Td  ).flatten()    
    des_Tz         = abs(Tzr  - Tz  ).flatten()    
    des_Tm         = abs(Tmr  - Tm  ).flatten()    
    des_Ti         = abs(Tir  - Ti  ).flatten()    
    des_Sp         = abs(Spr  - Sp  ).flatten()    
    des_Sg         = abs(Sgr  - Sg  ).flatten()    
    des_AgE        = abs(AgEr - AgE ).flatten()    
    des_AgH        = abs(AgHr - AgH ).flatten()    
    des_CssE       = abs(CssEr- CssE).flatten()    
    des_CssH       = abs(CssHr- CssH).flatten()
    if OPT_DESVIOS == 0:
        # Se incluyen desvíos redundantes
        des_Yp         = abs(Ypr  - Yp  ).flatten()    
        des_Yd         = abs(Ydr  - Yd  ).flatten()    
        des_Da         = abs(Dar  - Da  ).flatten()    
        des_Dt         = abs(Dtr  - Dt  ).flatten()    
        desvios = np.concatenate(
            (   des_produccion,des_factores,des_ebp,
                des_Fi,des_Mi,des_Ei,des_Di,des_Xpi,
                des_F ,des_M ,des_E,
                des_Da,des_Dt,
                des_Dat,
                des_Yp,des_Yd,
                des_Ydp,
                des_Alp,des_FF,des_Z,des_X,des_Xp,des_Xg,des_Xv,des_Q,
                des_Td,des_Tz,des_Tm,des_Sp,des_Sg,des_Sf,des_AgE,des_AgH,des_CssE,des_CssH,des_Ti
            )
        )
    else:
        desvios = np.concatenate(
            (   des_produccion,des_factores,des_ebp,
                des_Fi,des_Mi,des_Ei,des_Di,des_Xpi,
                des_F ,des_M ,des_E,
                des_Dat,
                des_Ydp,
                des_Alp,des_FF,des_Z,des_X,des_Xp,des_Xg,des_Xv,des_Q,
                des_Td,des_Tz,des_Tm,des_Sp,des_Sg,des_Sf,des_AgE,des_AgH,des_CssE,des_CssH,des_Ti
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

    if muestra_progreso and SALIDA_DESVIOS:
        if OPT_DESVIOS == 1:
            des_Yp = [0]
            des_Yd = [0]
            des_Da = [0]
            des_Dt = [0]
        param = (
                des_produccion,des_factores,des_ebp,
                des_Fi,des_Mi,des_Ei,des_Di,des_Xpi,
                des_F ,des_M ,des_E,
                des_Da,des_Dt,
                des_Dat,
                des_Yp,des_Yd,
                des_Ydp,
                des_Alp,des_FF,des_Z,des_X,des_Xp,des_Xg,des_Xv,des_Q,
                des_Td,des_Tz,des_Tm,des_Sp,des_Sg,des_Sf,des_AgE,des_AgH,des_CssE,des_CssH,des_Ti
                )

        infor.salida_desvios(res_ecuaciones, param, DECIMALES, GE_INCLUYE_XP, OPT_DESVIOS, dist)
    return dist

# función objetivo intermedia para llamar a la correspondiente Python o a la de la DLL, según el caso
def fo(vec_opt):
    if USAR_DLL:
        vo = vec_opt.ctypes.data_as(ct.POINTER(ct.c_double))
        if DESV_RELATIVA == 1:
            res = libc.merito_s_relativa(vo)
        else:
            res = libc.merito_s(vo)
    else:
        res = fun_objetivo(vec_opt)
    return res

# función objetivo Python, se llama desde 'fo' si no se usa la DLL
def fun_objetivo(vec_opt):
    res_ecuaciones = sec_ecuaciones(vec_opt)
    return calcula_desvios(res_ecuaciones, False)

def imprime_opciones(nvec_opt):
    imprime('-------------------------------------------------------------------')
    imprime('-------------------------------------------------------------------')
    nfijas = 0
    for i in range(nvec_opt):
        if bnds[i][1] - bnds[i][0] < 0.000001:
            nfijas += 1
    if GE_RESTRICCIONES:
        imprime('MEGA mediante algoritmo genético. Resolución con restricciones ' + ('lineales' if GE_TIPO_RE==0 else 'no lineales'))
    else:
        imprime('MEGA mediante algoritmo genético. Resolución sin restricciones')
    if len(FI_SOL_LEE) > 0:
        imprime('Solución inicial leida de              {}'.format(SENDA_SOLUCIONES + '/' + FI_SOL_LEE))
    if len(FI_SOL_SALVA) > 0:
        imprime('Solución final guardada en             {}'.format(SENDA_SOLUCIONES + '/' + FI_SOL_SALVA))
    imprime('Desviaciones relativas en tanto por 1  {}'.format('Si' if DESV_RELATIVA == 1 else 'No'))
    imprime('Semilla números aleatorios             {:10}'.format(GE_SEMILLA))
    imprime('Número máximo de generaciones          {:10,}'.format(GE_MAX_ITER))
    imprime('Tolerancia en el objetivo              {:10.3e}'.format(GE_TOLERANCIA))
    imprime('Iteraciones para valorar progreso      {:10,}'.format(GE_PROGRESO))
    imprime('Mejora mínima para considerar progreso {:10.4f} %'.format(GE_MIN_PROGRESO))
    imprime('Tolerancia en las verificaciones       {:10.3e}'.format(GE_VERIFICAR))
    imprime('Iteraciones para historial             {:10,}'.format(GE_HISTORIAL))
    imprime('Iteraciones para soluciones            {:10,}'.format(GE_SOLUCIONES))
    imprime('Balanza de pagos                       {}'.format('Mantenerla constante' if EQ_BAL_PAGOS else 'Endógena'))
    imprime('Función de utilidad de la demanda      {}'.format('Cobb-Douglas' if UTILIDAD_DEMANDA == 0 else 'CES'))
    imprime('Consumos de los hogares en la solución {}'.format('Si' if GE_INCLUYE_XP else 'No'))
    if UTILIDAD_DEMANDA == 1:
        mfun.cabecera('', ind)
        mfun.cuerpo2D(['sigma_ces',], parametros.sigma_ces)
        mfun.cierre(ind)
    imprime('Modo pseudo impuestos (Css y Ag)       {}'.format('Variable' if MODO_PSEUDOIMPTOS == 0 else 'Fijo'))
    imprime('Demanda con consumos esenciales        {}'.format('Si' if DEM_ESENCIALES else 'No'))
    imprime('Aportación de factores por los hogares {}'.format('ENDOGENA' if FF_ENDOGENA else 'exógena'))
    imprime('Factor ahorro a largo plazo            {:10.2f} %'.format(100.0 * ALP_FACTOR))
    imprime('Cálculo desvios                        {}'.format('Redundante' if OPT_DESVIOS == 0 else 'Simple'))
    if   METRICA_ERROR == 0:
        imprime('Métrica del error: Error cuadrático medio')
    elif METRICA_ERROR == 1:
        imprime('Métrica del error: Valor absoluto')
    else:
        imprime('Métrica del error: Desvios elevados a {}'.format(POT_DESVIOS))

    imprime('Usar DLL                               {}'.format('Si' if USAR_DLL else 'No'))
    if USAR_DLL == True:
        imprime('    Factor de recombinación                                 [{:5},{:5}]'.format(ALGE_RECOMBINACION[0], ALGE_RECOMBINACION[1]))
    else:
        imprime('Recombinación                          {:10.3f}'.format(GE_RECONBINACION))
        imprime('Estrategia                             {}'.format(GE_ESTRATEGIA))
        imprime('Tamaño de la población                 {:10} {:10} individuos'.format(GE_DIM_POBLACION, GE_DIM_POBLACION * (nvec_opt - nfijas)))
        imprime('Número de workers                      {:10}'.format(GE_WORKERS))
        imprime('Periodicidad actualización             {}'.format(GE_ACTUALIZACION))

    imprime('Usar genético DLL                      {}'.format('Si' if USAR_ALGE_DLL else 'No'))
    if USAR_ALGE_DLL:
        imprime('    Fichero log de la DLL                               {}/{}_{}_{}_{}_dll.log'.format(SENDA_SALIDAS, ALGE_ID_SALIDA, ALGE_NPOB, ALGE_MODO_POB_INI, GE_SEMILLA))
        imprime('    Número de hilos multiproceso                        {:10}'.format(ALGE_N_HILOS))
        imprime('    Número máximo de reinicios por falta de progreso    {:10}'.format(ALGE_MAX_INTENTOS))
        imprime('    Error máximo para calificar aceptable una solución  {:10}'.format(ALGE_TOL_ACEPTABLE))
        imprime('    Modo para generar la población inicial              {:10} {}'.format(ALGE_MODO_POB_INI, etq_mpob[ALGE_MODO_POB_INI]))
        imprime('    Factor de alcance para generar la población inicial {:10}'.format(ALGE_F_INICIO_POB))
        if ALGE_MODO_POB_INI == 12:
            imprime('    Igual a la cota inferior en la población inicial si <{:9.3f}'.format(ALGE_SIGMA_POB_INI))
        else:
            imprime('    Sigma para generar población inicial normal         {:10}'.format(ALGE_SIGMA_POB_INI))
        imprime('    Número de tramos para generar población inicial LHS {:10}'.format(ALGE_TRAMOS_LHS))
        imprime('    Número de individuos de la población inicial        {:10}'.format(ALGE_NPOB))
        imprime('    Factor de mutación                                  {:10}'.format(ALGE_F_MUTACION))
        imprime('    Control de factibilidad                             {}'.format('Si' if ALGE_CTRL_FACTIBLE == 1 else 'No'))
        imprime('    Solución en formato extenso                         {}'.format('Si' if ALGE_RES_EXTENSA == 1 else 'No'))
        imprime('    El mejor primero                                    {}'.format('Si' if EL_MEJOR_PRIMERO == 1 else 'No'))
        imprime('    Incluir x0                                          {}'.format('Si' if ALGE_INCLUIR_X0 == 1 else 'No'))
    imprime('')
    imprime('Rango de validez de los precios en % -{:9.1f} +{:9.1f}'.format(GE_PRE_MIN, GE_PRE_MAX))
    imprime('Rango de validez de las variables  % -{:9.1f} +{:9.1f}'.format(GE_VAR_MIN, GE_VAR_MAX))
    imprime('Rango de validez de las variables  0 -{:9.1f} +{:9.1f}'.format(GE_VAR_CERO, GE_VAR_CERO))
    if GE_VAR_CAN_MIN > 0:
        imprime('Rango mínimo de las variables         {:9.1f}'.format(GE_VAR_CAN_MIN))
    if len(FIX) > 0:
        imprime('------------------------------------------------------------------------------------------')
        imprime('Rangos de validez explícitos')
        imprime('------------------------------------------------------------------------------------------')
        for i in range(len(FIX)):
            imprime('{:8}'.format(FIX[i]), False)
            for j in range(len(FIX_LIMITES[i])):
                imprime(' i:{:10} vi:{:10} vs:{:10}'.format(FIX_LIMITES[i][j][0], FIX_LIMITES[i][j][1], FIX_LIMITES[i][j][2]))
        imprime('------------------------------------------------------------------------------------------')
    if n_precios_importacion > 0:
        imprime('Precio de importación')
        imprime('sector     precio')
        imprime('------ ------------')
        for pre_m in precios_importacion:
            i = pre_m[0]
            imprime('{:6} {:12.4e}'.format(i, datos.pWm[i]))
        imprime('------ ------------')
        imprime('------------------------------------------------------------------------------------------')
    imprime('El precio del factor {} es variable exógena con valor igual a {}'.format(h[OR_PRE_EXCLUIDO], PRECIO_F_EXCLUIDO))
    if VALOR_F_TRA == 0:
        imprime('El precio del factor {} se calcula con la curva Phillips [paro: {}% alfa: {}]'.format(h[INDICE_F_TRA], PARO_INICIAL * 100., ALFA_PHILLIPS))
    elif VALOR_F_TRA != -1:
        imprime('El precio del factor {} es fijo con valor igual a {}'.format(h[INDICE_F_TRA], VALOR_F_TRA))
    imprime('')
    imprime('Dimensión del vector de prueba: {:6} variables; con valor fijo: {:5} (E:{:4} M:{:4})'.format(nvec_opt, nfijas, n_Efijas, n_Mfijas))
    imprime('------------------------------------------------------------------------------------------')
    imprime('------------------------------------------------------------------------------------------')
    imprime('')

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
        '22.Css H',
        '23.AgE E',
        '24.AgH H',
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
if OR_PRE_EXCLUIDO == 1:
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
# epsilon (tipo de cambio)
etq_precios.append(vetq_sol[4])
npre_sol = len(etq_precios)
for k in range(nsec):
    etq_precios.append('pZ_' + ind[k])
for k in range(nsec):
    etq_precios.append('pE_' + ind[k])
for k in range(nsec):
    etq_precios.append('pM_' + ind[k])

if __name__ == '__main__':
    '''
    necesitamos este control porque el uso de workers en Windows reinicia el programa desde el
    principio para cada worker y así evitamos que se impriman estos textos tantas veces como workers, ya que el
    '__name__' de los reinicios no es igual a '__main__' (es igual a __mp_main__), la asignación de variables hay que
    repetirla en todos los workers por eso deben quedar fuera de este contol.
    encontraremos este control en númerosos puntos de la aplicación
    '''
    imprime('python           {}'.format(sys.version))
    imprime('numpy            {}'.format(np.__version__))
    imprime('scipy            {}'.format(scipy.__version__))
    imprime('pandas           {}'.format(pandas.__version__))
    imprime('matplotlib       {}'.format(matplotlib.__version__))
    imprime('')
    imprime('####################################################')
    imprime('MEGA ampliado. versión {:6} ---------------'.format(VERSION))
    imprime('####################################################')
    imprime('-------------------------------------------------------------------------------------------------')
    imprime(CASO)
    imprime('-------------------------------------------------------------------------------------------------')
    imprime('')
    imprime('Fichero Matriz Contabilidad Social (MCS) {}'.format(FICHERO_SAM))

# leemos la Matriz de Contabilidad Social (MCS o SAM) de esta economía
xls = pandas.ExcelFile(FICHERO_SAM)
if NSAM == 5:
    # 'dsam' las filas a procesar a partir de la fila con las cabeceras de las columnas 
    # el 8 = 7 cuentas + la suma (recursos)
    dsam = nsec + nfac + ndem + 8
    # 'lsam' columnas a procesar, como la primera es la coluna de los rótulos de las filas (SAM_COL), index_col debe ser 0
    lsam = np.arange(SAM_COL, SAM_COL + dsam).tolist()
    sam = pandas.read_excel(xls, sheet_name=SAM_HOJA, usecols=lsam, index_col=0, header=SAM_FIL, nrows=dsam)
    '''
    nombre filas    : sam.index
    nombre columnas : sam.columns
    primera columna : sam.iloc[:, 1]        TIO.iloc[:, 0] tiene los nombres de las filas 
    primera fila    : sam.iloc[0,  0:]      TIO.iloc[:, 0] tiene nan
    datos           : sam.iloc[0:, 0:]
    '''
elif NSAM == 6:
    # 'dsam' las filas a procesar a partir de la fila con las cabeceras de las columnas 
    # el 8 = 7 cuentas + la suma (recursos)
    dsam = nsec + nfac + ndem + 8
    # 'lsam' columnas a procesar, como la primera es la coluna de los rótulos de las filas (SAM_COL), index_col debe ser 0
    lsam = np.arange(SAM_COL, SAM_COL + dsam).tolist()
    sam = pandas.read_excel(xls, sheet_name=SAM_HOJA, usecols=lsam, index_col=0, header=SAM_FIL, nrows=dsam)
else:
    sam = pandas.read_excel(xls, index_col=0, header=0)
xls.close()
'''
el fichero calibrado.py contiene dos clases que, como cualquier clase, ejecutan el procedimiento
'def __init__' cuando se crea una variable de la clase:
    datos     : la función 'def __init__' de esta clase crea una serie de variables y les asigna
                valores de acuerdo con la información leída de la MCS.
    parametros: la función 'def __init__' de esta clase crea unas variables que son los parámetros
                del modelo y les calcula unos valores de acuerdo a las ecuaciones correspondientes
                y los valores asignados en la clase 'datos'.
'''
datos = calibrado.datos(sam, h, ind, dem, idt, gov, trf, ayd, inv, ext, css, alp, INDICE_F_TRA, PARO_INICIAL)
parametros = calibrado.parametros(datos, ndem, nsec, INDICE_F_TRA, DEM_ESENCIALES, CON_ESENCIALES, SIGMA_CES_DEMANDA)
if __name__ == '__main__':
    # realizamos algunas comprobaciones sobre los datos y parámetros
    linea_blanca = True
    if np.any(datos.F0    < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Error. Factor de producción (F0) negativo')
    if np.any(datos.Z0    < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Error. Producción bruta (Z0) negativa')
    if np.any(datos.D0    < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Error. Demanda local (D0) negativa')
    if np.any(datos.M0    < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Aviso. Importaciones (M0) negativas')
    if np.any(datos.E0    < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Aviso. Exportaciones (E0) negativas')
    if np.any(datos.X0    < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Error. Consumo intermedio (X) negativo')
    if np.any(datos.Xp0   < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Aviso. Consumo hogar (Xp) negativo')
    if np.any(datos.Xg0   < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Aviso. Consumo gobierno (Xg) negativo')
    if np.any(datos.Xv0   < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Aviso. Inversión (Xv) negativa')
    if np.any(datos.CssH0 < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Aviso. Cotización seguridad social (CssH) hogares negativa')
    if np.any(datos.CssE0 < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Aviso. Cotización seguridad social (CssE) empresas negativa')
    if np.any(datos.AgH0  < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Aviso. Ayuda del gobierno a hogares (AgH) negativa')
    if np.any(datos.AgE0  < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Aviso. Ayuda del gobierno a empresas (AgE) negativa')
    if np.any(datos.Td0   < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Aviso. Impuesto a la hogares (Td0) negativo')
    if np.any(datos.Tz0   < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Aviso. Impuesto a la producción (Tz0) negativo')
    if np.any(datos.Tm0   < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Aviso. Aranceles (Tm0) negativos')
    if datos.Te0 != 0:
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Error. El modelo no está preparado para el pago (positivo o negativo) de impuestos por la exportación (Te0)')
    if abs(parametros.landa.sum() - 1.) > 0.000001:
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Error. Los coeficientes de reparto de la inversión (landa) no suman 1.')
    if np.any(parametros.deltam < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Error. Al menos un coeficiente deltam (importación) de reparto en la CESes negativo')
    if np.any(parametros.deltad < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Error. Al menos un coeficiente deltdm (demanda local) de reparto en la CESes negativo')
    if np.any(abs(parametros.deltam + parametros.deltad - 1.) > 0.000001):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Error. Los coeficientes de reparto en la CES, deltam (importación) y deltad (demanda local) no suman 1.')
    if np.any(parametros.xid < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Error. Al menos un coeficiente de reparto xid (demanda local) en la CET, es negativo.')
    if np.any(parametros.xie < 0.):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Error. Al menos un coeficiente de reparto xie (exportación) en la CET, es negativo.')
    if np.any(abs(parametros.xid + parametros.xie - 1.) > 0.000001):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Error. Los coeficientes de reparto en la CET, xie (exportación) y xid (demanda local) no suman 1.')
    if np.any(abs(parametros.beta.sum(axis=1) - 1.) > 0.000001):
        if linea_blanca:
            imprime('')
            linea_blanca = False
        imprime('*--* Error. Los coeficientes de uso de los factores (beta) no suman 1., para algún sector')
    if linea_blanca == False:
        imprime('')

# punteros para extraer variables del vector solución
(etq_vec_opt,ind_pvec_desde,ind_pvec_hasta) = punteros()
if __name__ == '__main__':
    imprime('')
    if SAL_CALIBRADO:
        infor.salida_calibrado(datos, parametros, ind, dem, h, DEM_ESENCIALES)
    if SAL_GRAFICO_CES_DM:
        infor.grafico_CES_local_importacion(SENDA_GRAFICOS, datos, parametros, ind, dem, h)
    if SAL_ISOCUANTA:
        infor.isocuanta(SENDA_GRAFICOS, PREFIJO, datos, parametros, ind, dem, h, datos.D0, datos.M0, 0, 50000, 0, 100, -0.20, 0.5)

# equilibrio del balace de pagos inicial
ebp_ini = exte.equilibrio_balance_pagos_moneda_extranjera(datos.pWe, datos.E0, datos.pWm, datos.M0, datos.Sf0)     # 6.16

# ---------------------------------------------------------------------
# Solucíonar el MEGA
# ---------------------------------------------------------------------
# en primer lugar, adaptar algunos valores y parámetros según el escenario que se haya seleccionado
(CON_ESENCIALES) = esce.escenarios(__name__ == '__main__', datos, parametros, DECIMALES, ind, dem, h,
               NCASO, DEM_ADICIONAL, DEM_ADICIONAL_TIPO, DEM_ESENCIALES, CON_ESENCIALES, UTILIDAD_DEMANDA, RENTA_FICTICIA,
               AYD_ADICIONAL, GE_INCLUYE_XP,
               PRECIO_INI, VAR_FACTORES, FACTOR_CSSH, FACTOR_CSSE,
               SIGMA_ESCENARIO, ARANCELES
               )

if n_precios_importacion > 0:
    for pre_m in precios_importacion:
        i = pre_m[0]
        v = pre_m[1]
        datos.pWm[i] = v

if USAR_DLL:
    # conectar con la DLL y enviarle las opciones, datos y parámetros que necesita la DLL para calcular la función objetivo.
    # si además se usa el algoritmo genético de la DLL, se enviarán los parámetros de este más adelante
    # la aplicación no conoce la dirección de las funciones hasta que no se las llama, lo cual no es problema para llamarlas
    libc = dll.abre_dll(SENDA_DLL)
    dll.envia_opciones  (libc)
    dll.envia_datos     (libc, datos)
    dll.envia_parametros(libc, parametros)
    # si la DLL está compilada para comprobar desviaciones (lo que no es probable), necesitamos llamar explicitamente a
    # 'indice_desviaciones' porque llamaremos a las funciones de merito antes de llamar a 'soluciona'
    #libc.indice_desviaciones()

    libc.merito_s.argtypes = [ct.POINTER(ct.c_double)]
    libc.merito_s.restype = ct.c_double
    if DESV_RELATIVA == 1:
        libc.merito_s_relativa.argtypes = [ct.POINTER(ct.c_double)]
        libc.merito_s_relativa.restype = ct.c_double
        libc.merito_sol_relativa.argtypes = [ct.POINTER(ct.c_double)]
        libc.merito_sol_relativa.restype = ct.POINTER(ct.c_double)
    libc.merito_sol.argtypes = [ct.POINTER(ct.c_double)]
    libc.merito_sol.restype = ct.POINTER(ct.c_double)

if __name__ == '__main__':
    # sin el precio del último factor ya que su valor se fija de forma exógena, esto es realmente incorrecto
    # porque según las opciones, el precio del factor que se incluirá en el vector de prueba pueser el del
    # capital o el del trabajo, pero inicialmente ambos están puestos a 1.0 en 'datos.pF0'
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
    if GE_INCLUYE_XP:
        vec_opt = np.concatenate((vec_opt, datos.Xp0.flatten()))
    nvec_opt = len(vec_opt)

    if len(FI_SOL_LEE) > 0:
        # sustituir el vector de prueba inicial por el contenido en el fichero
        vec_opt = []
        with open(SENDA_SOLUCIONES + '/' + FI_SOL_LEE, "r", encoding="utf-8") as log:
            for i in range(nvec_opt):
                v = np.float64(log.readline())
                vec_opt.append(v)
        vec_opt = np.array(vec_opt, dtype=np.float64)
        if nvec_opt != len(vec_opt):
            imprime('*--* Error. El número de variables en la solución leida del fichero no coincide con el número de variables del modelo')
            sys.exit()
    pzi = copy.deepcopy(datos.pZ0)
    vec_opt_ini = copy.deepcopy(vec_opt)

    # 'vigila' función que 'differential_evolution' llamará después de probar cada posible solución 
    historial   = []
    soluciones  = []
    mensaje_fin = []
    vfa         = 1.0e+18
    def vigila(intermediate_result):
        nit = intermediate_result.nit   # número de generaciones
        vf  = intermediate_result.fun   # valor de la función objetivo
        if vf < GE_TOLERANCIA:
            # El desvio de la función objetivo es inferior al valor establecido, por lo que se da por terminada la minimización
            mensaje_fin.append('nit:{:9} fo:{:12.5e} valor función objetivo inferior a la tolerancia '.format(nit, vf))
            imprime('')
            imprime('')
            raise StopIteration
        if nit % GE_PROGRESO == 0:
            global vfa
            if (vfa - vf) < GE_MIN_PROGRESO / 100. * vfa:
                # no progresa significativamente, por lo que se da por terminada la minimización.
                # es importante que GE_TOLERANCIA sea lo suficientemente grande par que no se camcele antes de tiempo
                mensaje_fin.append('nit:{:9} mejora:{:12.5e} no progresa más'.format(nit, vfa - vf))
                raise StopIteration
            vfa = vf
        if GE_HISTORIAL > 0 and (nit == 1 or (nit % GE_HISTORIAL == 0)):
            if SAL_AUXILIARES:
                # guardar el valor del error (función objetivo) que, al final, se escribirá en un fichero CSV
                historial.append([nit,vf])
            imprime('{:9} {:12.5e}'.format(nit, vf))
        if SAL_AUXILIARES and GE_SOLUCIONES > 0 and (nit == 1 or (nit % GE_SOLUCIONES == 0)):
            # guardar el vector solución que, al final, se escribirá en un fichero CSV
            soluciones.append([nit,intermediate_result.x])
    
    # definir el rango de variación de los precios y variables
    (bnds, n_Efijas, n_Mfijas) = cotas(ndem, nsec, vec_opt, nvec_opt, npre_sol, ind_pvec_desde)
    # hacer compatible el vector de prueba inicial con los límites de variación de las variables
    cuenta = 0
    for i in range(len(vec_opt)):
        if (bnds[i][1] - bnds[i][0]) > 0.000001:
            if vec_opt[i]  < bnds[i][0]:
                cuenta += 1
                imprime('{:6} {:12.5e} {:12.5e}'.format(i, vec_opt[i], bnds[i][0]))
                vec_opt[i] = bnds[i][0]
            if vec_opt[i]  > bnds[i][1]:
                cuenta += 1
                imprime('{:6} {:12.5e} {:12.5e}'.format(i, vec_opt[i], bnds[i][1]))
                vec_opt[i] = bnds[i][1]
    if cuenta > 0:
        imprime('')
        imprime('*--* Se han modificado {} valores del vector inicial de prueba para ajustarlos a sus entornos de validez'.format(cuenta))
        imprime('')
    imprime_opciones(nvec_opt)

    if SALIDA_VAL_INI:
        if n_precios_importacion > 0:
            for pre_m in precios_importacion:
                i = pre_m[0]
                v = 1.
                datos.pWm[i] = v
        if SAL_MCS:
            (rot, mcs0) = infor.reconstruye_MCS(datos, parametros, ind, dem, h, inv,css, idt, gov, trf, ext, ayd, alp,
                                                  INDICE_F_TRA,datos.pF0,datos.pY0,datos.pQ0,datos.pD0,datos.pZ0,datos.epsilon0,datos.pWe,datos.pWm,
                                                  datos.Y0,datos.X0,datos.F0,datos.Z0,datos.CssE0,datos.Tz0,datos.M0,datos.AgE0,
                                                  datos.FF0,datos.Alp0,datos.Xp0,datos.Sp0,datos.CssH0,datos.AgH0,datos.Td0,datos.Xv0,datos.PssH0,
                                                  datos.Xg0,datos.Sg0,datos.Tg0,datos.Ti0, datos.Te0,datos.Tm0,
                                                  datos.E0,datos.Sf0,
                                                  TOLERA_MCS,'MCS base. Importes', True
                                                 )
            infor.imprime_MCS(rot, mcs0, DECIMALES, TOLERA_MCS, 'MCS base. Importes', True)
        infor.valores_iniciales(datos, parametros, DECIMALES, ind, dem, h, INDICE_F_TRA, VALOR_F_TRA, vec_opt, npre_sol, etq_precios, ebp_ini)
        # se prepara el vector que se pasará como parámetro a la función 'veri_solucion'
        ebp = exte.equilibrio_balance_pagos_moneda_extranjera(datos.pWe, datos.E0, datos.pWm, datos.M0, datos.Sf0)
        vec_veri_sol = (
                    datos.pF0,
                    datos.pY0,
                    datos.pZ0,
                    datos.pQ0,
                    datos.pD0,
                    datos.epsilon0,
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
                    datos.Sf0,
                    datos.Td0,
                    datos.Tz0,
                    datos.Tm0,
                    datos.CssE0,
                    datos.CssH0,
                    datos.AgE0,
                    datos.AgH0,
                    datos.Alp0,
                    datos.Ti0,
        )
        # verifica solución
        infor.veri_solucion(datos, parametros, ind, dem, h,
                            vec_veri_sol, etq_veri, UTILIDAD_DEMANDA, DEM_ESENCIALES, DEM_ADICIONAL_TIPO, DEM_ADICIONAL, RENTA_FICTICIA, INDICE_F_TRA, AYD_ADI_DEM, ALP_FACTOR, CON_ESENCIALES,
                            'Verifica con los valores iniciales', GE_VERIFICAR
                            )
        imprime('')
        if n_precios_importacion > 0:
            for pre_m in precios_importacion:
                i = pre_m[0]
                v = pre_m[1]
                datos.pWm[i] = v

    if PRIMERA_VALORACION:
        imprime('Una primera valoración del modelo')
        imprime('---------------------------------')
        res_ecuaciones = sec_ecuaciones(vec_opt)
        infor.salida_valores(datos, parametros, DECIMALES, ind, dem, h, INDICE_F_TRA, VALOR_F_TRA, vec_opt, npre_sol, etq_precios, res_ecuaciones)

        calcula_desvios(res_ecuaciones, True)
        # verificar la solución
        (Apz,Fi,Ei,Mi,Di,Xpi,pf,pq,pe,pm,
            Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,Sf ,AgE ,AgH ,CssE ,CssH,ebp,Zl,pz,
            Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,Sfr,AgEr,AgHr,CssEr,CssHr,ebpr,
            Ti,Tir
        ) = res_ecuaciones
        pf      = extrae_var(vec_opt,'pF', 0, nfac - 1)
        pf      = completa_pf(pf, F)
        py      = extrae_var(vec_opt,'pY', 0, nsec)
        pq      = extrae_var(vec_opt,'pQ', 0, nsec)
        pd      = extrae_var(vec_opt,'pD', 0, nsec)
        epsilon = extrae_var(vec_opt,'epsilon', 0, 0)
        vec_veri_sol = (
                    pf,
                    py,
                    pz,
                    pq,
                    pd,
                    epsilon,
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
                    Sf,
                    Td,
                    Tz,
                    Tm,
                    CssE,
                    CssH,
                    AgE,
                    AgH,
                    Alp,
                    Ti,
        )
        infor.veri_solucion(datos, parametros, ind, dem, h,
                            vec_veri_sol, etq_veri, UTILIDAD_DEMANDA, DEM_ESENCIALES, DEM_ADICIONAL_TIPO, DEM_ADICIONAL, RENTA_FICTICIA, INDICE_F_TRA, AYD_ADI_DEM, ALP_FACTOR, CON_ESENCIALES,
                            'Verifica en la primera valoración', GE_VERIFICAR
                            )
        imprime('')
        imprime('---------------------------------')
        imprime('')
        if SAL_MCS:
            pe = datos.pWe * epsilon
            pm = datos.pWm * epsilon
            (rot, mcs) = infor.reconstruye_MCS(datos, parametros, ind, dem, h, inv,css, idt, gov, trf, ext, ayd, alp,
                                                INDICE_F_TRA,pf,py,pq,pd,pz,epsilon,pe,pm,
                                                Yp,X,F,Z,CssE,Tz,M,AgE,
                                                FF,Alp,Xp,Sp,CssH,AgH,Td,Xv,datos.PssH0,
                                                Xg,Sg,datos.Tg0,Ti,datos.Te0,Tm,
                                                E,Sf,TOLERA_MCS,
                                                'MCS primera valoración. Importes', True
                                              )
            infor.imprime_MCS(rot, mcs, DECIMALES, TOLERA_MCS, 'MCS primera valoración. Importes', True)
    if SALIDA_VEC_OPT:
        imprime('    L.INF         V0          L.SUP')
        imprime('------------ ------------ ------------')
        n = 0
        imprime(etq_vec_opt[n])
        for i in range(len(vec_opt)):
            if i == ind_pvec_hasta.index[n]:
                n += 1 
                imprime(etq_vec_opt[n])
            imprime('{:12.5e} {:12.5e} {:12.5e}'.format(bnds[i][0], vec_opt[i], bnds[i][1]))
        imprime('------------ ------------ ------------')
        imprime('')
    
    if GE_RESTRICCIONES:
        # restricciones para 'differential_evolution', estás son un ejemplo
        restricciones = restri.restricciones_M_E(nvec_opt, ind_pvec_desde, datos,GE_TIPO_RE)
    else:
        restricciones = []
    if USAR_ALGE_DLL:
        imprime('No se muestra en pantalla la evolución de los cálculos. Ver el fichero {}/{}_{}_{}_{}_dll.log'.format(SENDA_SALIDAS, ALGE_ID_SALIDA, ALGE_NPOB, ALGE_MODO_POB_INI, GE_SEMILLA))
    else:
        imprime('Evolución de la minimización')
    imprime('')
    res_ecuaciones = sec_ecuaciones(vec_opt)
    dist = calcula_desvios(res_ecuaciones, False)
    imprime('{:>9} {:12.5e}'.format('Python ', dist))
    if USAR_DLL:
        '''
        libc.abre_salida.argtypes = [ct.c_char_p]
        libc.abre_salida.restype = ct.c_bool
        v5 = ct.c_char_p(SENDA_SALIDAS.encode('utf-8'))
        res = libc.abre_salida(v5)
        if res == False:
            imprime('*--* Error al abrir la salida en la DLL')
            imprime('aplicación terminada')
            imprime('')
            sys.exit()
        '''
        dist_dll = fo(vec_opt);
        imprime('{:>9} {:12.5e}'.format('DLL    ', dist_dll))
        dist_dll = dll.merito_sol(libc, vec_opt);
        imprime('{:>9} {:12.5e}'.format('DLL sol', dist_dll))
        '''
        res = libc.cierra_salida()
        if res == False:
            imprime('*--* Error al cerrar la salida en la DLL')
            imprime('aplicación terminada')
            imprime('')
            sys.exit()

        sys.exit()
        '''
    imprime('')

    t_inicio = timer()

    # minimizar el error de la función objetivo
    if GE_WORKERS != 1:
        rmin = differential_evolution(func=fo,
                x0=vec_opt,
                bounds=bnds,
                strategy=GE_ESTRATEGIA,
                popsize=GE_DIM_POBLACION,   # 15 es por defecto
                #mutation=1., 
                tol=GE_TOLERANCIA,
                disp=False,
                polish = False,
                callback=vigila,
                maxiter=GE_MAX_ITER,
                updating=GE_ACTUALIZACION,
                #vectorized=6,
                workers=GE_WORKERS,         # en WINDOWS funciona de aquella manera
                recombination=GE_RECONBINACION,
                seed=GE_SEMILLA,
                constraints=restricciones,
        )
    else:
        if USAR_ALGE_DLL:
            # llamar al procedimiento en la DLL pasandole como vectores:
            #   los parámetros de configuración del algoritmo
            #   los cotas de variación de las variables
            #   el vector solución inicial
            par = []
            par.append(np.float64(ALGE_MAX_INTENTOS))
            par.append(np.float64(ALGE_N_HILOS))
            par.append(np.float64(GE_MAX_ITER))
            par.append(np.float64(GE_TOLERANCIA))
            par.append(np.float64(ALGE_TOL_ACEPTABLE))
            par.append(np.float64(GE_PROGRESO))
            par.append(np.float64(GE_MIN_PROGRESO / 100.))
            par.append(np.float64(GE_HISTORIAL))
            par.append(np.float64(GE_SOLUCIONES))
            par.append(np.float64(ALGE_MODO_POB_INI))
            par.append(np.float64(ALGE_F_INICIO_POB))
            par.append(np.float64(ALGE_SIGMA_POB_INI))
            par.append(np.float64(ALGE_TRAMOS_LHS))
            par.append(np.float64(ALGE_NPOB))
            par.append(np.float64(ALGE_F_MUTACION))
            par.append(np.float64(ALGE_RECOMBINACION[0]))
            par.append(np.float64(ALGE_RECOMBINACION[1]))
            par.append(np.float64(ALGE_CTRL_FACTIBLE))
            par.append(np.float64(GE_SEMILLA))
            par.append(np.float64(EL_MEJOR_PRIMERO))
            par.append(np.float64(ALGE_INCLUIR_X0))
            par.append(np.float64(nvec_opt));
            par.append(np.float64(ALGE_ID_SALIDA));
            par.append(np.float64(DESV_RELATIVA))

            cotas_inf =[]
            cotas_sup =[]
            for i in range(nvec_opt):
                cotas_inf.append(np.float64(bnds[i][0]))
                cotas_sup.append(np.float64(bnds[i][1]))
            '''
            'dll.soluciona' devuelve un vector double donde los primeros 5 datos del vector son:
                0. el código de terminación (si es menor que 0 es finalización con error)
                1. el número de datos de la solución (aicionales a los 7 de cabecera)
                2. el número de intentos utilizados para encontrar la solución, si el algoritmo no progresa se hace
                    un nuevo intento a partir de una poblacion inicial nueva, así hasta los 'ALGE_MAX_INTENTOS'
                    especificados en los parámetros
                3. el número de generaciones calculadas
                4. el valor de la función objetivo
                5. el valo5 de la máxima desviación
                6. el índice de la variable con la máxima desviación
            '''
            cabecera = 7
            r_sol = dll.soluciona(libc, par, cotas_inf, cotas_sup, vec_opt, ALGE_RES_EXTENSA, SENDA_SALIDAS)
            r_res   = int(r_sol[0])
            r_datos = int(r_sol[1])
            imprime('')
            imprime('*****************************************************************')
            imprime('-------------------------- DLL genético -------------------------')
            if r_res < 0:
                imprime('error ({:15}) {}'.format(r_res, rot_res_dll_error[- (r_res + 1)]))
                imprime('aplicación terminada')
                imprime('')
                sys.exit()
            else:
                imprime('respuesta ({:3}) {}'.format(r_res, rot_res_dll_ok[r_res]))
                imprime('número de datos         :{:15}'.format(r_datos))
                imprime('intentos                :{:15}'.format(int(r_sol[2] + 1)))
                imprime('generaciones            :{:15}'.format(int(r_sol[3])))
                imprime('merito                  :{:15.5e}'.format(r_sol[4]))
                imprime('máxima desviación       :{:15.5e}'.format(r_sol[5]))
                imprime('variable max desviación :{:15}'.format(int(r_sol[6])))
            imprime('*****************************************************************')
            if ALGE_RES_EXTENSA == 1:
                # devuelve el valor de todas las variables concatenadas en un vector de valores double
                pf   = np.zeros(nfac)
                py   = np.zeros(nsec)
                pq   = np.zeros(nsec)
                pd   = np.zeros(nsec)
                Fi   = np.zeros((nsec,nfac))
                Ei   = np.zeros(nsec)
                Mi   = np.zeros(nsec)
                Di   = np.zeros(nsec)
                Xpi  = np.zeros((ndem,nsec))
                pz   = np.zeros(nsec)
                pe   = np.zeros(nsec)
                pm   = np.zeros(nsec)
                F    = np.zeros((nsec,nfac))
                E    = np.zeros(nsec)
                M    = np.zeros(nsec)
                Yp   = np.zeros(nsec)
                Yd   = np.zeros(nsec)
                Da   = np.zeros(nsec)
                Dt   = np.zeros(nsec)
                Z    = np.zeros(nsec)
                Xg   = np.zeros(nsec)
                Xv   = np.zeros(nsec)
                Q    = np.zeros(nsec)
                Td   = np.zeros(ndem)
                Tz   = np.zeros(nsec)
                Tm   = np.zeros(nsec)
                Sp   = np.zeros(ndem)
                AgE  = np.zeros(nsec)
                AgH  = np.zeros(ndem)
                CssE = np.zeros(nsec)
                CssH = np.zeros(ndem)
                Xp   = np.zeros((ndem,nsec))
                FF   = np.zeros((ndem,nfac))
                Alp  = np.zeros((ndem,nfac))
                X    = np.zeros((nsec,nsec))

                Fr    = np.zeros((nsec,nfac))
                Er    = np.zeros(nsec)
                Mr    = np.zeros(nsec)
                Ypr   = np.zeros(nsec)
                Ydr   = np.zeros(nsec)
                Dar   = np.zeros(nsec)
                Dtr   = np.zeros(nsec)
                Zr    = np.zeros(nsec)
                Xgr   = np.zeros(nsec)
                Xvr   = np.zeros(nsec)
                Qr    = np.zeros(nsec)
                Tdr   = np.zeros(ndem)
                Tzr   = np.zeros(nsec)
                Tmr   = np.zeros(nsec)
                Spr   = np.zeros(ndem)
                AgEr  = np.zeros(nsec)
                AgHr  = np.zeros(ndem)
                CssEr = np.zeros(nsec)
                CssHr = np.zeros(ndem)
                Xpr   = np.zeros((ndem,nsec))
                FFr   = np.zeros((ndem,nfac))
                Alpr  = np.zeros((ndem,nfac))
                Xr    = np.zeros((nsec,nsec))

                # vector solución
                n = cabecera;
                for i in range(nfac):	pf[i]   = r_sol[n];n += 1
                for i in range(nsec):	py[i]   = r_sol[n];n += 1
                for i in range(nsec):	pq[i]   = r_sol[n];n += 1
                for i in range(nsec):	pd[i]   = r_sol[n];n += 1
                epsilon = r_sol[n];n += 1
                Apz = r_sol[n];n += 1
                for i in range(nsec):
                    for j in range(nfac):
                        Fi[i,j] = r_sol[n];n += 1
                for i in range(nsec):	Ei[i]   = r_sol[n];n += 1
                for i in range(nsec):	Mi[i]   = r_sol[n];n += 1
                for i in range(nsec):	Di[i]   = r_sol[n];n += 1
                if GE_INCLUYE_XP:
                    for i in range(ndem): 
                        for j in range(nsec):
                            Xpi[i,j] = r_sol[n];n += 1
                else:
                    for i in range(ndem): 
                        for j in range(nsec):
                            Xpi[i,j] = Xp[i,j]

                # resto variables
                for i in range(nsec):	pz[i]   = r_sol[n];n += 1
                for i in range(nsec):	pe[i]   = r_sol[n];n += 1
                for i in range(nsec):	pm[i]   = r_sol[n];n += 1
                for i in range(nsec):
                    for j in range(nfac):
                        F[i,j] = r_sol[n];n += 1
                for i in range(nsec):	E[i]    = r_sol[n];n += 1
                for i in range(nsec):	M[i]    = r_sol[n];n += 1
                for i in range(nsec):	Yp[i]   = r_sol[n];n += 1
                for i in range(nsec):	Yd[i]   = r_sol[n];n += 1
                for i in range(nsec):	Da[i]   = r_sol[n];n += 1
                for i in range(nsec):	Dt[i]   = r_sol[n];n += 1
                for i in range(nsec):	Z[i]    = r_sol[n];n += 1
                for i in range(nsec):	Xg[i]   = r_sol[n];n += 1
                for i in range(nsec):	Xv[i]   = r_sol[n];n += 1
                for i in range(nsec):	Q[i]    = r_sol[n];n += 1
                for i in range(ndem):	Td[i]   = r_sol[n];n += 1
                for i in range(nsec):	Tz[i]   = r_sol[n];n += 1
                for i in range(nsec):	Tm[i]   = r_sol[n];n += 1
                for i in range(ndem):	Sp[i]   = r_sol[n];n += 1
                for i in range(nsec):	AgE[i]  = r_sol[n];n += 1
                for i in range(ndem):	AgH[i]  = r_sol[n];n += 1
                for i in range(nsec):	CssE[i] = r_sol[n];n += 1
                for i in range(ndem):	CssH[i] = r_sol[n];n += 1
                Sg = np.array(r_sol[n],dtype=np.float64);n += 1
                Sc = np.array(r_sol[n],dtype=np.float64);n += 1
                Sf = np.array(r_sol[n],dtype=np.float64);n += 1
                ebp = np.array(r_sol[n],dtype=np.float64);n += 1
                for i in range(ndem): 
                    for j in range(nsec):
                        Xp[i,j] = r_sol[n];n += 1
                for i in range(ndem): 
                    for j in range(nfac):
                        FF[i,j] = r_sol[n];n += 1
                for i in range(ndem):
                    for j in range(nfac):
                        Alp[i,j] = r_sol[n];n += 1
                for i in range(nsec):
                    for j in range(nsec):
                        X[i,j] = r_sol[n];n += 1
                Ti = np.array(r_sol[n],dtype=np.float64);n += 1
                # recálculos
                for i in range(nsec):
                    for j in range(nfac):
                        Fr[i,j] = r_sol[n];n += 1
                for i in range(nsec):	Er[i]    = r_sol[n];n += 1
                for i in range(nsec):	Mr[i]    = r_sol[n];n += 1
                for i in range(nsec):	Ypr[i]   = r_sol[n];n += 1
                for i in range(nsec):	Ydr[i]   = r_sol[n];n += 1
                for i in range(nsec):	Dar[i]   = r_sol[n];n += 1
                for i in range(nsec):	Dtr[i]   = r_sol[n];n += 1
                for i in range(nsec):	Zr[i]    = r_sol[n];n += 1
                for i in range(nsec):	Xgr[i]   = r_sol[n];n += 1
                for i in range(nsec):	Xvr[i]   = r_sol[n];n += 1
                for i in range(nsec):	Qr[i]    = r_sol[n];n += 1
                for i in range(ndem):	Tdr[i]   = r_sol[n];n += 1
                for i in range(nsec):	Tzr[i]   = r_sol[n];n += 1
                for i in range(nsec):	Tmr[i]   = r_sol[n];n += 1
                for i in range(ndem):	Spr[i]   = r_sol[n];n += 1
                for i in range(nsec):	AgEr[i]  = r_sol[n];n += 1
                for i in range(ndem):	AgHr[i]  = r_sol[n];n += 1
                for i in range(nsec):	CssEr[i] = r_sol[n];n += 1
                for i in range(ndem):	CssHr[i] = r_sol[n];n += 1
                Sgr = np.array(r_sol[n],dtype=np.float64);n += 1
                Scr = np.array(r_sol[n],dtype=np.float64);n += 1
                Sfr = np.array(r_sol[n],dtype=np.float64);n += 1
                ebpr = np.array(r_sol[n],dtype=np.float64);n += 1
                for i in range(ndem): 
                    for j in range(nsec):
                        Xpr[i,j] = r_sol[n];n += 1
                for i in range(ndem): 
                    for j in range(nfac):
                        FFr[i,j] = r_sol[n];n += 1
                for i in range(ndem):
                    for j in range(nfac):
                        Alpr[i,j] = r_sol[n];n += 1
                for i in range(nsec):
                    for j in range(nsec):
                        Xr[i,j] = r_sol[n];n += 1
                Tir = np.array(r_sol[n],dtype=np.float64);n += 1
                
                # la DLL las devuelve transpuestas
                X  = X.T
                Xr = Xr.T

                if OR_PRE_EXCLUIDO == 0:
                    spf = np.array([pf[1]])
                else:
                    spf = np.array([pf[0]])
                sol = np.concatenate((
                                    spf,
                                    py.flatten(),
                                    pq.flatten(),
                                    pd.flatten(),
                                    np.array([epsilon]),
                                    np.array([Apz]),
                                    Fi.flatten(),
                                    Ei.flatten(),
                                    Mi.flatten(),
                                    Di.flatten(),
                ))
            else:
                rot_des = [
                        'ebp/Sf',
                        'Qeq',
                        'Feq',
                        'Alp',
                        'Sg',
                        'Sp',
                        'Sf',
                        'AgH',
                        'CssH',
                        'Td',
                        'FF',
                        'Xpi',
                        'Xp',
                        'Ei',
                        'Mi',
                        'Dai',
                        'E',
                        'M',
                        'Ydp',
                        'Dat',
                        'Z',
                        'Xg',
                        'Xv',
                        'Q',
                        'Tz',
                        'Tm',
                        'AgE',
                        'CssE',
                        'Fi',
                        'F',
                        'X',
                        'Ti',
                        '???'
                    ]
                ind_des = [
                        1,
                        2,
                        28,
                        13,
                        14,
                        15,
                        6,
                        11,
                        3,
                        29,
                        10,
                        18,
                        20,
                        30,
                        12,
                        21,
                        22,
                        23,
                        17,
                        19,
                        16,
                        9,
                        24,
                        25,
                        5,
                        4,
                        26,
                        7,
                        27,
                        8,
                        0,
                        31,
                        32
                    ]
                ids = copy.deepcopy(ind_des)
                ids.sort()
                if ids[0] != 0:
                    imprime('*--* Error en el índice 0 de las desviaciones')
                for i in range(1, len(ids)):
                    if ids[i] != ids[i-1] + 1:
                        imprime('*--* Error en el índice {} de las desviaciones'.format(i))
                # devuelve el vector solución
                if OR_PRE_EXCLUIDO == 1:
                    # ajustar la ubicación del precio de los factores, porque se devuelven los dos 
                    r_sol[cabecera + 1] = r_sol[cabecera]
                sol = np.array([r_sol[i] for i in range(cabecera + 1, r_datos)], dtype=np.float64)
                ne = r_datos
                nd = int(r_sol[ne])
                if nd != len(ind_des) - 1:
                    imprime('*--* Error en el número de desviaciones, {} en lugar de {}'.format(nd, len(ind_des) - 1))
                ne += 1

                val_des = []
                val_des.append(r_sol[ne])
                suma = r_sol[ne]
                ne += 1
                for i in range(1, nd):
                    val_des.append(r_sol[ne] - r_sol[ne - 1])
                    suma += r_sol[ne] - r_sol[ne - 1]
                    ne += 1
                imprime('')
                imprime('bloque    desvio')
                imprime('------ ------------')
                for i in range(nd):
                    imprime('{:6} {:12.6e}'.format(rot_des[ind_des[i]], val_des[ind_des[i]]))
                imprime('------ ------------')
                imprime('{:6} {:12.6e}'.format('total', suma))
                if GE_HISTORIAL > 0:
                    if r_sol[ne] != HISTO_MAX:
                        imprime('*--* Error el número de datos de evolución {} no es coherente {}'.format(r_sol[r_datos + i], HISTO_MAX))
                        sys.exit()
                    ne += 1
                    imprime('')
                    imprime('generac.    merito')
                    imprime('-------- ------------')
                    for i in range(HISTO_MAX):
                        if i > 0 and r_sol[ne] == 0:
                            break;
                        imprime('{:8.0f} {:12.6e}'.format(r_sol[ne], r_sol[ne + 1]))
                        ne += 2
                    imprime('-------- ------------')
            rmin = rmin_dll(sol, int(sol[3]))
            imprime('')
        else:
            rmin = differential_evolution(func=fo,
                    x0=vec_opt,
                    bounds=bnds,
                    strategy=GE_ESTRATEGIA,
                    popsize=GE_DIM_POBLACION,   # 15 es por defecto
                    #mutation=1., 
                    tol=GE_TOLERANCIA,
                    disp=False,
                    polish = False,
                    callback=vigila,
                    maxiter=GE_MAX_ITER,
                    updating=GE_ACTUALIZACION,
                    #vectorized=6,
                    recombination=GE_RECONBINACION,
                    seed=GE_SEMILLA,
                    constraints=restricciones,
            )

    t_fin = timer()

    sol = rmin.x
    if len(FI_SOL_SALVA) > 0:
        with open(SENDA_SOLUCIONES + '/' + FI_SOL_SALVA, "w", encoding="utf-8") as log:
            for i in range(len(sol)):
                log.write('{}\n'.format(sol[i]))

    if USAR_ALGE_DLL and ALGE_RES_EXTENSA == 1:
        res_ecuaciones = (Apz,Fi,Ei,Mi,Di,Xpi,pf,pq,pe,pm,
            Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,Sf ,AgE ,AgH ,CssE ,CssH,ebp,Z,pz,
            Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,Sfr,AgEr,AgHr,CssEr,CssHr,ebpr,
            Ti,Tir
        )
    else:
        res_ecuaciones = sec_ecuaciones(sol)
    imprime('-----------------------------------------------------------')
    imprime('VALORES FINALES')
    imprime('-----------------------------------------------------------')
    imprime('')
    if SALIDA_DESVIOS:
        imprime('Detalle de las desviaciones')
        imprime('')
    dist = calcula_desvios(res_ecuaciones, SALIDA_DESVIOS)
    infor.salida_valores(datos, parametros, DECIMALES, ind, dem, h, INDICE_F_TRA, VALOR_F_TRA, sol, npre_sol, etq_precios, res_ecuaciones)
    (Apz,Fi,Ei,Mi,Di,Xpi,pf,pq,pe,pm,
        Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,Sf ,AgE ,AgH ,CssE ,CssH,ebp,Zl,pz,
        Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,Srf,AgEr,AgHr,CssEr,CssHr,ebpr,
        Ti,Tir
    ) = res_ecuaciones
    if SAL_MCS:
        pf = extrae_var(sol,'pF', 0, nfac - 1)
        pf = completa_pf(pf, F)
        py = extrae_var(sol,'pY', 0, nsec)
        pq = extrae_var(sol,'pQ', 0, nsec)
        pd = extrae_var(sol,'pD', 0, nsec)
        epsilon = extrae_var(sol,'epsilon', 0, 0)
        (pe, pm) = exte.precio_moneda_local_pe_pm(datos.pWe, datos.pWm, epsilon)
        (rot, mcs) = infor.reconstruye_MCS(datos, parametros, ind, dem, h, inv,css, idt, gov, trf, ext, ayd, alp,
                                            INDICE_F_TRA,pf,py,pq,pd,pz,epsilon,pe,pm,
                                            Yp,X,F,Z,CssE,Tz,M,AgE,
                                            FF,Alp,Xp,Sp,CssH,AgH,Td,Xv,datos.PssH0,
                                            Xg,Sg,datos.Tg0,Ti,datos.Te0,Tm,
                                            E,Sf,
                                            TOLERA_MCS,'MCS final. Importes',True
                                          )
        infor.imprime_MCS(rot, mcs, DECIMALES, TOLERA_MCS, 'MCS final. Importes',True)

        (rot_t, mcs_t) = infor.reconstruye_MCS(datos, parametros, ind, dem, h, inv,css, idt, gov, trf, ext, ayd, alp,
                                            INDICE_F_TRA,datos.pF0,datos.pY0,datos.pQ0,datos.pD0,datos.pZ0,datos.epsilon0,datos.pWe,datos.pWm,
                                            Yp,X,F,Z,CssE,Tz,M,AgE,
                                            FF,Alp,Xp,Sp,CssH,AgH,Td,Xv,datos.PssH0,
                                            Xg,Sg,datos.Tg0,Ti,datos.Te0,Tm,
                                            E,Sf,
                                            TOLERA_MCS,'MCS final. Cantidades',False
                                          )
        infor.imprime_MCS(rot_t, mcs_t, DECIMALES, TOLERA_MCS, 'MCS final. Cantidades', False)

        if SAL_VAR_MCS and SALIDA_VAL_INI:
            infor.imprime_MCS(rot, mcs-mcs0, DECIMALES, 2.0 * TOLERA_MCS, 'Diferencias entre los valores finales y los iniciales de la MCS', True)

    if GE_HISTORIAL > 0:
        # guardar el valor del error que, al final, se escribirá en un fichero CSV
        historial.append([rmin.nit,dist])
    if GE_SOLUCIONES > 0:
        # guardar el vector solución que, al final, se escribirá en un fichero CSV
        soluciones.append([rmin.nit,sol])
    if SAL_GRAFICOS_EVOL:
        infor.parrilla_graficos(datos, parametros, ind, dem, h, SENDA_GRAFICOS, FICHERO_IMG, GE_IMG_COL, GE_IMG_FIL, GE_SOLUCIONES, soluciones, Z, Xp, Da, E, M)
    if SAL_AUXILIARES:
        # escribir el fichero con el historial 
        with open(FI_HISTORIAL, "w", encoding="utf-8") as sal:
            for v in historial:
                sal.write('{}\n'.format(v[0],v[1]))
        # escribir el fichero con las soluciones
        with open(FI_SOLUCIONES, "w", encoding="utf-8") as sal:
            for v in soluciones:
                sal.write('{}'.format(v[0]))
                vv = v[1]
                for i in range(len(vv)):
                    sal.write(';{}'.format(vv[i]))
                sal.write('\n')

    imprime('La distancia (error de la función objetivo) es {:11.5e}'.format(dist))
    if USAR_DLL:
        dist_dll = fo(sol);
        imprime('                                           DLL {:11.5e}'.format(dist_dll))
    imprime('-----------------------------------------------------------')
    imprime('')
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
                Sf,
                Td,
                Tz,
                Tm,
                CssE,
                CssH,
                AgE,
                AgH,
                Alp,
                Ti,
    )
    infor.veri_solucion(datos, parametros, ind, dem, h,
                        vec_veri_sol, etq_veri, UTILIDAD_DEMANDA, DEM_ESENCIALES, DEM_ADICIONAL_TIPO, DEM_ADICIONAL, RENTA_FICTICIA, INDICE_F_TRA, AYD_ADI_DEM, ALP_FACTOR, CON_ESENCIALES,
                        'Verifica con la solución final', GE_VERIFICAR
                        )
    if len(mensaje_fin) > 0 or dist > GE_TOLERANCIA:
        imprime('')
        imprime('***********************************************************************')
        for mensaje in mensaje_fin:
            imprime(mensaje)
        if (dist > GE_TOLERANCIA):
            imprime('No se alcanzó el mínimo deseado {:9.3e} [{:9.3e}]'.format(GE_TOLERANCIA, dist))
        imprime('***********************************************************************')
    imprime('')
    imprime("Tiempo de cálculo de la aplicación:{:11,.0f} s".format(t_fin - t_inicio))
    imprime('')
    
    # comprobar que los valores de las variables no tienen el valor mínimo, o máximo, de su rango de existencia

    topes = []
    for i in range(nvec_opt):
        if bnds[i][1] - bnds[i][0] > 0.001:
            j = -1
            if abs(sol[i] - bnds[i][0]) < 0.001:
                j = 0
            if abs(bnds[i][1] - sol[i]) < 0.001:
                j = 1
            if j != -1:
                nbe_var = 'Error'
                des_var = -1
                for k in range(len(etq_vec_opt)):
                    clave = etq_vec_opt[k]
                    if i >= ind_pvec_desde[clave] and i < ind_pvec_hasta[clave]:
                        nbe_var = clave
                        des_var = i - ind_pvec_desde[clave]
                        break;
                topes.append([j, sol[i], i, nbe_var, des_var])
    if len(topes) > 0:
        imprime('')
        imprime('*--* {} variables tienen el valor mínimo, o máximo, de su rango de existencia'.format(len(topes)))
        imprime('igual al        valor      n      bloque    indice')
        imprime('-------- --------------- ----- ------------ ------')
        for v in topes:
            if v[0] == 0:
                imprime('mínimo  ', False)
            else:
                imprime('máximo  ', False)
            imprime('{:15.5e} {:5} {:12} {:6}'.format(v[1], v[2], v[3], v[4]))
        imprime('-------- --------------- ----- ------------ ------')
        imprime('')

    if not USAR_ALGE_DLL:
        clave = 'message'
        mensaje = rmin[clave]
        imprime('{}'.format(mensaje))
        if mensaje != 'callback function requested stop early':
            clave = 'success'
            imprime('exito :{}'.format('Si' if rmin[clave]==True else 'No'))
        clave = 'nit'
        imprime('Número de generaciones {}'.format(rmin[clave]))
        imprime('')
    imprime('Precios    iniciales equilibrio')
    imprime('--------- ---------- ----------')
    imprime('{:10}                {:9.7f}'.format('pF_' + h[0], pf[0]))
    imprime('{:10}                {:9.7f}'.format('pF_' + h[1], pf[1]))
    mfun.tabla_1Dl(etq_precios[1:npre_sol], vec_opt_ini[1:npre_sol], sol[1:npre_sol], 7)
    imprime('--------- ---------- ----------')
    respre = np.concatenate((pzi, np.array(datos.pWe * datos.epsilon0), np.array(datos.pWm * datos.epsilon0)))
    mfun.i_tabla('' , etq_precios[npre_sol:len(etq_precios)] , [], respre           , True ,  7)
    respre = np.concatenate((pz, np.array(pe), np.array(pm)))
    mfun.i_tabla('' , etq_precios[npre_sol:len(etq_precios)] , [], respre           , True ,  7)
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
        # datos, parametros, DECIMALES, ind, dem, h, vec_opt_ini, vec_opt, npre_sol, etq_precios, ebp_ini, res_ecuaciones, rot
        infor.diferencias_cantidades_finales_iniciales(datos, parametros, DECIMALES, ind, dem, h, vec_opt_ini, sol, npre_sol, etq_precios, ebp_ini, res_ecuaciones, 'Cantidades')
        infor.diferencias_importes_finales_iniciales  (datos, parametros, DECIMALES, ind, dem, h, vec_opt_ini, sol, npre_sol, etq_precios, ebp_ini, res_ecuaciones, 'Importes')
