'''
Se necesita float64, con float32 no es suficiente.

Aúnque scipy es muy eficiente por estar compilada en C, el punto débil es la función objetivo
que está íntegramente en Python.

Otro asunto sobre el que reflexionar, es la conveniencia de normalizar las desviaciones de las variables en el
resultado de la función objetivo. La aplicación no los normaliza, se trata de desviaciones en importes y todos
tienen el mismo peso, sea cual sea el importe absoluto de la variable. Casi seguro no serviría de nada.

scipy.differential_evolution si normaliza las variables para que todos los intervalos de existencia sean el mismo.

Los pagos de impuestos directos del gobierno no se usan para nada.

Utilizar para la demanda la función de utilidad Cobb-Douglas o la CES con cualquier valor de sigma, da prácticamente los
mismos resultados, lo cual es lógico porque los parámetros se determinan en todos los casos para que se
reproduzcan los valores Xp0 de la MCS y las variaciones que experimentan los Xp en la solución son suficientemente
pequeñas para que todas las funciones de utilidad repartan los ingresos netos en prácticamente las mismas cantidades.

Resulta increible el papel de Apz, si no se deja libre en un intervalo grande, no se encuentra solución

El tratamiento del precio de los factores es enrevesado y fuente de multitud de errores, se diseño pensando
que siempre se fijaría el precio del factor trabajo y por lo tanto no debía formar parte de las soluciones a
probar, pero los parches al considerar que se podría fijar el del capital o usar la curva Phillips hacen
incomprensible la gestión de estos precios en las soluciones de prueba.
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

import dll           as dll

# los escenarios pueden cambiar los valores iniciales de las variable y los parámetros
global datos
global parametros

VERSION = '1.3.0'

# 5 Matrices de Contabilidad Social para las pruebas, se selecciona con NSAM
# estas etiquetas solo se usan para construir el nombre del fichero de salida
#               0           1           2             3           4
etq_sam  = ['1_hogar','2_hogares','2_hogares','3_hogares_AMP','MCA-ESP-05']
# escenarios para las pruebas, se selecciona con NCASO
etq_caso = [
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
]

# extrae los argumentos de la línea de comandos y si no la hay de los valores por defecto,
# ajustando las dimensiones de las matrices 'reshape' cuando corresponde
try:
    args = argumentos.valores_opciones()
except BaseException as e:
    print('Error en la lectura de parámetros {}\n'.format(e.args))
    sys.exit()

# se guardan las notificaciones hasta que esté lista la función 'imprimir'
errores_diferidos = []
avisos_diferidos  = []

nfac = args.NFAC    # número de factores 
ndem = args.NDEM    # número de hogares
nsec = args.NSEC    # número de sectores
NSAM                = args.NSAM
DECIMALES           = args.DECIMALES
USAR_DLL            = args.USAR_DLL
SENDA_DLL           = args.SENDA_DLL

USAR_ALGE_DLL       = args.USAR_ALGE_DLL
ALGE_MAX_INTENTOS   = args.ALGE_MAX_INTENTOS
ALGE_N_HILOS        = args.ALGE_N_HILOS
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

if (USAR_DLL or USAR_ALGE_DLL) and NSAM != 4:
    if __name__ == 'MEGA':
        errores_diferidos.append('La DLL solo se puede usara con la MCS 4 y se ha especificado la {}'.format(NSAM))
    else:
        errores_diferidos.append('')
NCASO               = np.array(args.NCASO, dtype=int)
DEM_ADICIONAL_TIPO  = args.DEM_ADICIONAL_TIPO
if len(args.DEM_ADICIONAL) != ndem * nsec:
    if __name__ == 'MEGA':
        errores_diferidos.append('El número de datos para DEM_ADICIONAL {} no es el correcto {}'.format(len(args.DEM_ADICIONAL), ndem * nsec))
    else:
        errores_diferidos.append('')
else:
    DEM_ADICIONAL       = np.array(args.DEM_ADICIONAL, dtype=np.float64).reshape(ndem, nsec)
if len(args.AYD_ADICIONAL) != ndem * nsec:
    if __name__ == 'MEGA':
        errores_diferidos.append('El número de datos para AYD_ADICIONAL {} no es el correcto {}'.format(len(args.AYD_ADICIONAL), ndem * nsec))
    else:
        errores_diferidos.append('')
else:
    AYD_ADICIONAL   = np.array(args.AYD_ADICIONAL  , dtype=np.float64).reshape(ndem, nsec)
RENTA_FICTICIA      = args.RENTA_FICTICIA
if (9 in NCASO) and RENTA_FICTICIA:
    if __name__ == 'MEGA':
        avisos_diferidos.append('Se ha seleccionado el caso {} sin renta ficticia'.format(etq_caso[9]))
GE_INCLUYE_XP       = args.GE_INCLUYE_XP
DEM_ESENCIALES      = args.DEM_ESENCIALES
if len(args.CON_ESENCIALES) != ndem * nsec:
    if __name__ == 'MEGA':
        errores_diferidos.append('El número de datos para CON_ESENCIALES {} no es el correcto {}'.format(len(args.CON_ESENCIALES), ndem * nsec))
    else:
        errores_diferidos.append('')
else:
    CON_ESENCIALES      = np.array(args.CON_ESENCIALES , dtype=np.float64).reshape(ndem, nsec)
    if abs(CON_ESENCIALES).sum() == 0 and DEM_ESENCIALES == True:
        if __name__ == 'MEGA':
            avisos_diferidos.append('No se han especificado consumos esenciales pero DEM_ESENCIALES es True')
    if abs(CON_ESENCIALES.sum()) == 0:
        if (13 in NCASO) == False and (14 in NCASO) == False:
            # los casos 13 y 14 fijan los consumos esenciales
            if DEM_ESENCIALES == True:
                if __name__ == 'MEGA':
                    avisos_diferidos.append('Se ha cambiado DEM_ESENCIALES a False, sin consumos esenciales no tiene sentido calcular demandas con consumos esenciales')
                    DEM_ESENCIALES = False
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
if len(args.SIGMA_ESCENARIO) != nsec:
    if __name__ == 'MEGA':
        errores_diferidos.append('El número de datos para SIGMA_ESCENARIO {} no es el correcto {}'.format(len(args.SIGMA_ESCENARIO), nsec))
    else:
        errores_diferidos.append('')
else:
    SIGMA_ESCENARIO     = np.array(args.SIGMA_ESCENARIO, dtype=np.float64)
if len(args.ARANCELES) != nsec:
    if __name__ == 'MEGA':
        errores_diferidos.append('El número de datos para ARANCELES {} no es el correcto {}'.format(len(args.ARANCELES), nsec))
    else:
        errores_diferidos.append('')
else:
    ARANCELES           = np.array(args.ARANCELES, dtype=np.float64)
PREFIJO             = args.PREFIJO if args.PREFIJO != '"' else ''
OR_PRE_EXCLUIDO     = args.OR_PRE_EXCLUIDO
PRECIO_F_EXCLUIDO   = np.float64(args.PRECIO_F_EXCLUIDO)
VALOR_F_TRA         = np.float64(args.VALOR_F_TRA)
PARO_INICIAL        = np.float64(args.PARO_INICIAL)
ALFA_PHILLIPS       = np.float64(args.ALFA_PHILLIPS)
FF_ENDOGENA         = args.FF_ENDOGENA
ALP_FACTOR          = args.ALP_FACTOR
OPT_DESVIOS         = args.OPT_DESVIOS
PRIMERA_VALORACION  = args.PRIMERA_VALORACION
UTILIDAD_DEMANDA    = args.UTILIDAD_DEMANDA
MODO_PSEUDOIMPTOS   = args.MODO_PSEUDOIMPTOS
SAL_CALIBRADO       = args.SAL_CALIBRADO
SALIDA_VEC_OPT      = args.SALIDA_VEC_OPT
SALIDA_DESVIOS      = args.SALIDA_DESVIOS
SAL_GRAFICOS_EVOL   = args.SAL_GRAFICOS_EVOL
SAL_GRAFICO_CES_DM  = args.SAL_GRAFICO_CES_DM
SAL_ISOCUANTA       = args.SAL_ISOCUANTA
SAL_VARIACIONES     = args.SAL_VARIACIONES
SAL_MCS             = args.SAL_MCS
SAL_VAR_MCS         = args.SAL_VAR_MCS
GE_RESTRICCIONES    = args.GE_RESTRICCIONES
GE_TIPO_RE          = args.GE_TIPO_RE
GE_TOLERANCIA       = np.float64(args.GE_TOLERANCIA)
GE_VERIFICAR        = np.float64(args.GE_VERIFICAR)
GE_PROGRESO         = args.GE_PROGRESO
SAL_AUXILIARES      = args.SAL_AUXILIARES
if SAL_AUXILIARES:
    GE_HISTORIAL    = args.GE_HISTORIAL
    GE_SOLUCIONES   = args.GE_SOLUCIONES
else:
    # no tiene sentido guardarlas para luego no salvarlas
    GE_HISTORIAL    = 0
    GE_SOLUCIONES   = 0
GE_PRE_MIN          = np.float64(args.GE_PRE_MIN)
GE_PRE_MAX          = np.float64(args.GE_PRE_MAX)
GE_VAR_MIN          = np.float64(args.GE_VAR_MIN)
GE_VAR_MAX          = np.float64(args.GE_VAR_MAX)
GE_VAR_CERO         = np.float64(args.GE_VAR_CERO)
if len(args.GE_FIX) == 0 or args.GE_FIX[0] == '':
    GE_FIX = []
    GE_FIX_LIMITES = np.zeros(0, dtype=list)
else:
    GE_FIX = args.GE_FIX
    k = len(args.GE_FIX)
    n = len(args.GE_FIX_LON)
    if k != n:
        if __name__ == 'MEGA':
            errores_diferidos.append('No coincide el número de variables acotadas {} con el de límites {}'.format(k, n))
        else:
            errores_diferidos.append('')
    if len(args.GE_FIX_LIMITES) != sum(args.GE_FIX_LON) * 2:
        if __name__ == 'MEGA':
            errores_diferidos.append('No coincide el número de parejas de limites {} con el de tamaño de GE_FIX_LIMITES {}'.format(sum(args.GE_FIX_LON) * 2, args.GE_FIX_LIMITES))
        else:
            errores_diferidos.append('')
    GE_FIX_LIMITES = np.zeros(k, dtype=list)
    ni = 0
    for i in range(k):
        # para cada variable 'i'
        sec = []
        for j in range(args.GE_FIX_LON[i]):
            # para cada par (lim inferior, lim superior) de la variable
            sec.append(args.GE_FIX_LIMITES[ni:(ni + 2)])
            ni += 2
        GE_FIX_LIMITES[i] = sec
GE_MAX_ITER         = args.GE_MAX_ITER
GE_ACTUALIZACION    = args.GE_ACTUALIZACION
GE_RECONBINACION    = args.GE_RECONBINACION
GE_DIM_POBLACION    = args.GE_DIM_POBLACION
GE_WORKERS          = args.GE_WORKERS
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
if (13 in NCASO) and DEM_ESENCIALES:
    if __name__ == 'MEGA':
        errores_diferidos.append('Consumos esenciales iguales a Xp0 es incompatible con Stone-Geary (rentas 0)')
    else:
        errores_diferidos.append('')
if USAR_ALGE_DLL and GE_WORKERS != 1:
    if __name__ == 'MEGA':
        errores_diferidos.append('Para usar el algoritmo genético desde la DLL en número de Workers ({}) debe ser 1'.format(GE_WORKERS))
    else:
        errores_diferidos.append('')
if USAR_ALGE_DLL:
    # la DLL no aporta estos detalles
    GE_HISTORIAL      = False
    GE_SOLUCIONES     = False
    SAL_GRAFICOS_EVOL = False
    SAL_AUXILIARES    = False

if len(errores_diferidos) == 0:
    # acumular por hogar porque el modelo no contempla ayudas para un producto determinado, pero necesitamos los
    # valores desagregados por producto, porque modificaremos las preferencias (alfa) de consumo de cada producto en particular
    AYD_ADI_DEM = AYD_ADICIONAL.sum(axis=1)
aviso_workers = False
if GE_WORKERS != 1:
    # aunque se modifica automáticamente, no está de más especificarlo por transparencia
    GE_ACTUALIZACION = 'deferred'
    # comprobar el número de GE_WORKERS según la máquina
    n_cores = psutil.cpu_count(logical = False)
    if n_cores <= GE_WORKERS:
        aviso_workers = True

os.makedirs(SENDA_SALIDAS , exist_ok=True)  # crear el directorio si no existe
os.makedirs(SENDA_GRAFICOS, exist_ok=True)  # crear el directorio si no existe

# para el algoritmo genético de la DLL
rot_res_dll_ok = [
            "Solución encontrada",
            "No progresa, solución no aceptable",
            "No progresa, pero la solución puede ser aceptable",
            "Superado el máximo de generaciones, solución no aceptable",
            "Superado el máximo de generaciones, pero la solución puede ser aceptable"
        ]
rot_res_dll_error = [
            "Error al generar la población",
            "Error al fijar las cotas",
            "Error al reservar memoria para la población",
            "Error al generar la población",
            "Terminación inesperada",
            "Error en los parámetros",
            "Error al preparar la multitarea"
        ]
# para asimilar el formato del resultado de la DLL al que devuelve scipy
class rmin_dll(object):
    def __init__(self, sol, dnit):
        self.x = sol
        self.nit = dnit

# --------------------------------------------------------------------
# ATENCION el factor trabajo debe ser la columna 'INDICE_F_TRA' de 'h'
# --------------------------------------------------------------------
INDICE_F_TRA = 1        # índice del factor trabajo, es mejor cambiar el orden en la definición de la lista 'h' que cambiar este índice

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
    CASO += ('_Rst_' + str(GE_TIPO_RE) if GE_RESTRICCIONES else '') + ('_Fix_{:03}'.format(len(GE_FIX)) if len(GE_FIX) > 0 else '')
    CASO += '_{:05}'.format(GE_SEMILLA)

FICHERO_IMG     = CASO
SENDA_FI_SALIDA = '{}/{}'.format(SENDA_SALIDAS, CASO)
FICHERO_LOG     = SENDA_FI_SALIDA + '.log'
FI_HISTORIAL    = SENDA_FI_SALIDA + '_his.csv'
FI_SOLUCIONES   = SENDA_FI_SALIDA + '_sol.csv'

# preparar para usar la función 'imprime' que llama a la del módulo 'mfun' del mismo nombre, pasándole el nombre del fichero donde escribir
mfun.ini(FICHERO_LOG)
def imprime(texto, rc=True):
    mfun.imprime(texto, rc)

# ya podemos escribir los mensajes de error y avisos
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
    
    # con errorres se cancela la aplicación
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

def cotas(ndem, nsec, vec_opt, nvec_opt, npre_sol, or_pre_referencia, indice_f_tra, valor_f_tra,
          ge_tolerancia, ge_pre_min, ge_pre_max, ge_var_cero, ge_var_min, ge_var_max,
          ind_pvec_desde, ge_fix, ge_fix_limites, ge_incluye_xp, con_esenciales):
    # definir el rango de variación de los precios y variables en LA SOLUCION A PROBAR 'vec_opt'
    bnds = []
    # primero rellenamos 'bnds' y luego lo iremos modificando
    for i in range(nvec_opt):
        bnds.append((0.,0.))

    # precios
    for i in range(npre_sol):
        if i == 0 and or_pre_referencia != indice_f_tra and valor_f_tra > 0:
            # el precio del factor OR_PRE_EXCLUIDO no forma parte del vector solución
            # el que forma parte es el otro, luego si OR_PRE_EXCLUIDO es el capital (!= INDICE_F_TRA),
            # el incluido en la solución es el trabajo y lo hacemos igual a VALOR_F_TRA, salvo que sea 0 o -1
            vi = valor_f_tra
            vs = valor_f_tra
        else:
            v = vec_opt[i]
            if abs(v) < ge_tolerancia:
                # para evitar que los precios inicialmente a 0 queden acotados a (0,0)
                vi = 0.
                vs = 3.
            else:
                vi = v / ge_pre_min
                vs = v * ge_pre_max
        bnds[i] = ((vi,vs))

    # variables

    # preparamos las especificaciones explicitas (manuales) de límites
    if len(ge_fix) > 0:
        # se va a guardar la fila de 'GE_FIX_LIMITES' y el puntero que le corresponde, porque luego necesitamos ordenar
        # 'pt' por punteros de menor a mayor
        pt = np.zeros((len(ge_fix), 2), dtype=int)
        n = 0
        for clave in ge_fix:
            # fila de 'GE_FIX_LIMITES'
            pt[n,0] = n  
            # puntero al inicio de la variable
            pt[n,1] = ind_pvec_desde[clave]
            n += 1
        # ordenar 'pt'
        filas = np.argsort(pt[:,1]);
        pt = pt[filas]
    else:
        pt = np.zeros((1, 2), dtype=int)
        pt[0,1] = -1

    # desde el principio por si se han establecido límites explicitos (manualmente) para algún precio
    i = 0
    for ii in range(0, nvec_opt):
        n = 0
        esta = False
        if i <= pt[-1, 1]:
            # 'i' aún no ha superado el último puntero
            for nf in range(len(ge_fix)):
                if i == pt[nf,1]:
                    # se han especificado límites (en la fila n) para esta variable
                    n = pt[nf,0]
                    esta = True
                    for j in range(len(ge_fix_limites[n])):
                        # para cada pareja 'j' de limites del vector 'n'
                        
                        # límite inferior
                        if type(ge_fix_limites[n][j][0]) is str:
                            if ge_fix_limites[n][j][0] == '*':
                                # no se ha fijado valor, se usa el criterio general
                                v = vec_opt[i]
                                if abs(v) < 0.001:
                                    vi = np.float64(-ge_var_cero)
                                else:
                                    vi = v / ge_var_min
                            else:
                                vi = vec_opt[i]
                        else:
                            vi = ge_fix_limites[n][j][0]

                        # límite superior
                        if type(ge_fix_limites[n][j][1]) is str:
                            if ge_fix_limites[n][j][1] == '*':
                                # no se ha fijado valor, se usa el criterio general
                                v = vec_opt[i]
                                if abs(v) < 0.001:
                                    vs = np.float64(+ge_var_cero)
                                else:
                                    vs = v * ge_var_max
                            else:
                                vs = vec_opt[i]
                        else:
                            vs = ge_fix_limites[n][j][1]
                        bnds[i] = ((vi,vs))
                        i += 1
                    break
        if i < npre_sol:
            # ignorar si no se han establecido límites manualmente para algún precio
            i += 1
        else:
            if esta == False:
                # criterio general
                v = vec_opt[i]
                # para evitar que las variables inicialmente a 0 queden acotadas a (0,0)
                if abs(v) < 0.001:
                    vi = np.float64(-ge_var_cero)
                    vs = np.float64(+ge_var_cero)
                else:
                    vi = v / ge_var_min
                    vs = v * ge_var_max
                bnds[i] = ((vi,vs))
                i += 1
        if i == nvec_opt:
            break
    if ge_incluye_xp and abs(con_esenciales).sum() != 0:
        # acotar consumos de los hogares Xp
        i = ind_pvec_desde['Xp']
        for j in range(ndem):
            for k in range(nsec):
                vi = con_esenciales[j][k]
                bnds[i] = (vi,bnds[i][1])
                i += 1

    # resulta increible el papel de Apz, si no se deja libre en un intervalo grande, no se encuentra solución
    #--------------------------------------------------------------------------------------------------------    
    #i = ind_pvec_desde['Apz']
    #bnds[i] = (-0.000001, 0.000001)
    #--------------------------------------------------------------------------------------------------------    

    return bnds

def completa_pf(pf, F):
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

    # el precio de los factores tiene un tratamiento especial, en el vector solución solo se incluye
    # un precio: el del capital o el del trabajo, según OR_PRE_EXCLUIDO sea 0 o 1
    pf = extrae_var(vec_opt, 'pF', 0, nfac - 1)
    # if OR_PRE_EXCLUIDO == 0 and VALOR_F_TRA == 0:
    #   el valor en el vector de solución no se usará
    #   el del capital se fija (OR_PRE_EXCLUIDO == 0) y el del trabajo se calcula (VALOR_F_TRA)

    # el precio del otro factor se añade al principio o al final de 'pf'
    pf = completa_pf(pf, F)
    # calculamos los precios del comercio internacional en moneda local
    (pe, pm) = exte.precio_moneda_local_pe_pm(datos.pWe, datos.pWm, epsilon)            # 6.14 y 6.15
    
    if GE_INCLUYE_XP:
        # el vector solución incluye los consumos de los hogares, necesario si se quiere acotar el
        # valor de los mismos, por ejemplo, para usar una función de utilidad con consumos esenciales
        Xpi = copy.deepcopy(extrae_var(vec_opt, 'Xp', ndem, nsec))

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
    # (Y) factor compuesto óptimo para por cada sector, dadas las utilizaciones de factores de
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

    # La variación de la suma del factor compuesto, respecto del factor compuesto de la MCS,
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
            # si AHORRO_L_PLAZO = False, el modelo se realimenta, además de por los consumos internos, por la demanda final.
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
    # ayudas (pagos) del gobierno a las empresas, un porcentaje de lo recaudado por impuestos
    AgE  = gob.ayudas_empresas_AgE(parametros.cage, Td, Tz, Tm)
    # ayudas (pagos) del gobierno a los hogares, un porcentaje de lo recaudado por impuestos
    AgH  = gob.ayudas_hogares_AgH(parametros.cagh, Td, Tz, Tm, AYD_ADI_DEM)

    # Ahorro (privado -hogares- y del gobierno). Se invertirán íntegramente en los sectores
    # las calculamos antes que 6. 9 y 6.10, porque mo dependen de los resultados de estas y sin
    # embargo 6. 9 y 6.10 si dependen de ellos. El ahorro a corto plazo es por tanto sin Alp
    #--------------------------------------------------------------------------------------------------
    Sp = ainv.ahorro_hogares_Sp(parametros.ssp, FF, pf, datos.PssH0)                    # 6.11

    # Seguridad social
    # los pagos de la seguridad social a los hogares (pensiones -PssH0-) es un valor constante fijado de antemano (exógena).
    #--------------------------------------------------------------------------------------------------
    # cotizaciones a la seguridad social, un porcentaje del factor trabajo:

    #   de las empresas. (F) es la utilización de factores de cada sector
    CssE = gob.seguridad_social_empresas_CssE(parametros.ctzsse, pf, F, INDICE_F_TRA)
    #   de los hogares. (FF) es la prestación de factores de cada hogar (consumidor)
    CssH = gob.seguridad_social_hogares_CssH(parametros.ctzssh, pf, FF, Alp, INDICE_F_TRA)

    Sg = ainv.ahorro_gobierno_Sg(parametros.ssg, Td, Tz, Tm, AgE, AgH, datos.PssH0, CssH, CssE) # 6.12

    # El gobierno compra productos con cargo a sus ingresos disponibles que son lo que recauda por
    # impuestos menos su ahorro (Sg) y las ayudas a empresas (AgE) y hogares (AgH)
    Xg = gob.demanda_gobierno_Xg(parametros.mu, pq, Td, Tz, Tm, Sg, AgE, AgH, datos.PssH0, CssH, CssE) # 6. 9

    # Inversión con cargo a los ahorros: los ahorros privados (Sp), del gobierno (Sg) y del
    # exterior (Sf0), se reparten entre sectores proporcionalmente a la MCS (parametros.landa)
    #--------------------------------------------------------------------------------------------------
    # superhavit / déficit de la seguridad social
    if datos.PssH0.sum() == 0:
        # si no se han explicitado pensiones en la MCS, suponemos que es el gobierno quien las paga
        # y no ha lugar un déficit o superhabit de la seguridad social. Esto es un truco para que el modelo trabaje
        # con las 5 MCS que hemos definido, ya que algunas no tienene separada la cuenta de la seguridad social.
        Sc = 0.
    else:
        Sc = CssE.sum() + CssH.sum() - datos.PssH0.sum()
    Xv = ainv.demanda_inversion_Xv(parametros.landa, pq, Sp, Sg, Sc, epsilon, datos.Sf0)    # 6.10

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
    ebp = exte.equilibrio_balance_pagos_moneda_extranjera(datos.pWe, E, datos.pWm, M, datos.Sf0)                                    # 6.16
    
    # Leontief para comparar, no tiene otro uso
    Zl = prod.produccion_sector_Z(X, ax, Yd, ay)                                                                                    # 6. 5 original
    
    '''
    Para calcular el demerito de la solución de prueba 'vec_opt', que recibe está función como argumento,
    recalculamos las variables para ver cuánto se diferencian del cálculo previo.
    para que el demérito sea el correcto hay que recalcular todas las variables.
    '''

    Zr    = exte.restriccion_produccion_bruta_Z(parametros.teta, parametros.xie, parametros.xid, E, Dt, parametros.phi)             # 6.20
    Ypr   = prod.produccion_factor_compuesto_Y(F, parametros.beta, parametros.b)            # 6. 1
    Fr    = prod.uso_optimo_factores_F(parametros.beta, pf, py, Ypr)                        # 6. 2
    Xr    = prod.consumo_intermedio_X(Zr, ax)                                               # 6. 3
    Ydr   = prod.utilizacion_factor_compuesto_Y(Zr, ay)                                     # 6. 4

    if  FF_ENDOGENA:
        FFr = deho.aportacion_factores_FF(datos.FF0, F)
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
    AgEr  = gob.ayudas_empresas_AgE(parametros.cage, Tdr, Tzr, Tmr)
    AgHr  = gob.ayudas_hogares_AgH(parametros.cagh, Tdr, Tzr, Tmr, AYD_ADI_DEM)
    CssEr = gob.seguridad_social_empresas_CssE(parametros.ctzsse, pf, Fr, INDICE_F_TRA)
    CssHr = gob.seguridad_social_hogares_CssH(parametros.ctzssh, pf, FFr, Alpr, INDICE_F_TRA)
    Sgr   = ainv.ahorro_gobierno_Sg(parametros.ssg, Tdr, Tzr, Tmr, AgEr, AgHr, datos.PssH0, CssHr, CssEr)              # 6.12
    Xgr   = gob.demanda_gobierno_Xg(parametros.mu, pq, Tdr, Tzr, Tmr, Sgr, AgEr, AgHr, datos.PssH0, CssHr, CssEr)      # 6. 9
    if datos.PssH0.sum() == 0:
        Scr = 0.
    else:
        Scr = CssEr.sum() + CssHr.sum() - datos.PssH0.sum()
    Xvr   = ainv.demanda_inversion_Xv(parametros.landa, pq, Spr, Sgr, Scr, epsilon, datos.Sf0)   # 6.10
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
    ebpr  = exte.equilibrio_balance_pagos_moneda_extranjera(datos.pWe, Er, datos.pWm, Mr, datos.Sf0)                                        # 6.16

    if GE_INCLUYE_XP == False:
        Xpi = Xp

    res_ecuaciones = (Apz,Fi,Ei,Mi,Di,Xpi,pf,pq,pe,pm,
            Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,AgE ,AgH ,CssE ,CssH, ebp,Zl,pz,
            Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,AgEr,AgHr,CssEr,CssHr,ebpr
    )
    return res_ecuaciones

def calcula_desvios(res_ecuaciones, muestra_progreso):
    '''
    Calcula los desvíos (penalización) correspondientes a la ejecución de las ecuaciones 'sec_ecuaciones'
    '''
    (Apz,Fi,Ei,Mi,Di,Xpi,pf,pq,pe,pm,
        Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,AgE ,AgH ,CssE ,CssH, ebp, Zl, pz,
        Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,AgEr,AgHr,CssEr,CssHr,ebpr
    ) = res_ecuaciones

    # Se trata de forma individualizada la desviación en valor absoluto de cada variable

    # Apz es como los precios, no es el resultado de ninguna ecuación y por tanto no se puede
    # calcular un desvío para ella

    # 'ebp' y 'ebpr' deben ser ambas cero
    des_ebp = np.array([abs(ebp) + abs(ebpr)])

    # condiciones de equilibrio del mercado.
    #   Xp.sum(axis=0) = suma de lo que vende un sector a los hogares  = suma de los que compran todos los hogares a ese sector
    #   Xg             = suma de las ventas de cada sector al gobierno = lo que compra el gobierno a cada sector
    #   Xv             = suma de lo ingresado por cada sector como inversiones
    #   X.sum(axis=1)  = suma de lo que vende cada sector a los otros sectores (ventas intermedias)

    des_produccion = abs(Q - (Xp.sum(axis=0) + Xg + Xv + X.sum(axis=1))).flatten()      # 6.23

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
        des_factores   = abs(F.sum(axis=0) - FF.sum(axis=0)).flatten()  # 6.24
        des_Alp        = np.zeros(ndem, dtype=np.float64)

    des_Fi         = abs(F    - Fi  ).flatten()    
    des_Ei         = abs(E    - Ei  ).flatten()    
    des_Mi         = abs(M    - Mi  ).flatten()    
    if GE_INCLUYE_XP:
        des_Xpi = abs(Xp   - Xpi ).flatten()    
    else:
        des_Xpi = [0]

    des_F          = abs(Fr   - F   ).flatten()
    des_E          = abs(Er   - E   ).flatten()    
    des_M          = abs(Mr   - M   ).flatten()    

    des_FF         = abs(FFr  - FF  ).flatten()
    des_Ydp        = abs(Yd   - Yp  ).flatten()    
    des_Dat        = abs(Da   - Dt  ).flatten()    

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
    if OPT_DESVIOS == 0:
        # Se incluyen desvíos redundantes, pero puede acelerar la convergencia y producir mejores resultados
        des_Di         = abs(Dt   - Di  ).flatten()
        des_Da         = abs(Dar  - Da  ).flatten()    
        des_Dt         = abs(Dtr  - Dt  ).flatten()    
        des_Yp         = abs(Ypr  - Yp  ).flatten()    
        des_Yd         = abs(Ydr  - Yd  ).flatten()    
        desvios = np.concatenate(
            (   des_produccion,des_factores,des_ebp,
                des_Fi,des_Mi,des_Ei,des_Di,des_Xpi,
                des_F ,des_M ,des_E,
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
            (   des_produccion,des_factores,des_ebp,
                des_Fi,des_Mi,des_Ei,des_Xpi,
                des_F ,des_M ,des_E,
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

    if muestra_progreso and SALIDA_DESVIOS:
        if OPT_DESVIOS == 0:
            des_Di = [0]
            des_Da = [0]
            des_Dt = [0]
            des_Yp = [0]
            des_Yd = [0]

        param = (des_produccion,des_factores,des_ebp,
                des_Fi,des_Mi,des_Ei,des_Di,des_Xpi,
                des_F ,des_M ,des_E,
                des_Da,des_Dt,
                des_Dat,
                des_Yp,des_Yd,
                des_Ydp,
                des_Alp,des_FF,des_Z,des_X,des_Xp,des_Xg,des_Xv,des_Q,
                des_Td,des_Tz,des_Tm,des_Sp,des_Sg,des_AgE,des_AgH,des_CssE,des_CssH
                )
        infor.salida_desvios(res_ecuaciones, param, DECIMALES, GE_INCLUYE_XP, OPT_DESVIOS, dist)
    return dist

def fo(vec_opt):
    if USAR_DLL:
        vo = vec_opt.ctypes.data_as(ct.POINTER(ct.c_double))
        res = libc.merito_s(vo)
    else:
        res = fun_objetivo(vec_opt)
    return res

def fun_objetivo(vec_opt):
    res_ecuaciones = sec_ecuaciones(vec_opt)
    return calcula_desvios(res_ecuaciones, False)

def imprime_opciones(nvec_opt):
    imprime('-------------------------------------------------------------------')
    imprime('-------------------------------------------------------------------')
    if GE_RESTRICCIONES:
        imprime('MEGA mediante algoritmo genético. Resolución con restricciones ' + ('lineales' if GE_TIPO_RE==0 else 'no lineales'))
    else:
        imprime('MEGA mediante algoritmo genético. Resolución sin restricciones')
    imprime('Usar DLL                               {}'.format('Si' if USAR_DLL else 'No'))
    imprime('Usar genético DLL                      {}'.format('Si' if USAR_ALGE_DLL else 'No'))
    if USAR_ALGE_DLL:
        imprime('     MAX_INTENTOS   {:10}'.format(ALGE_MAX_INTENTOS))
        imprime('     N_HILOS        {:10}'.format(ALGE_N_HILOS))
        imprime('     TOL_ACEPTABLE  {:10}'.format(ALGE_TOL_ACEPTABLE))
        imprime('     MODO_POB_INI   {:10}'.format(ALGE_MODO_POB_INI))
        imprime('     F_INICIO_POB   {:10}'.format(ALGE_F_INICIO_POB))
        imprime('     SIGMA_POB_INI  {:10}'.format(ALGE_SIGMA_POB_INI))
        imprime('     TRAMOS_LHS     {:10}'.format(ALGE_TRAMOS_LHS))
        imprime('     NPOB           {:10}'.format(ALGE_NPOB))
        imprime('     F_MUTACION     {:10}'.format(ALGE_F_MUTACION))
        imprime('     RECOMBINACION      [{:5},{:5}]'.format(ALGE_RECOMBINACION[0],ALGE_RECOMBINACION[1]))
        imprime('     CTRL_FACTIBLE  {:10}'.format(ALGE_CTRL_FACTIBLE))
        imprime('     RES_EXTENSA    {:10}'.format(ALGE_RES_EXTENSA))
    imprime('')
    imprime('Rango  de validez de los precios en % -{:9.1f} +{:9.1f}'.format(100. * (GE_PRE_MIN - 1.), 100. * (GE_PRE_MAX - 1.)))
    imprime('Rango  de validez de las variables  % -{:9.1f} +{:9.1f}'.format(100. * (GE_VAR_MIN - 1.), 100. * (GE_VAR_MAX - 1.)))
    imprime('Rango  de validez de las variables  0 -{:9.1f} +{:9.1f}'.format(GE_VAR_CERO, GE_VAR_CERO))
    if len(GE_FIX) > 0:
        imprime('------------------------------------------------------------------------------------------')
        imprime('Rangos de validez explícitos')
        imprime('------------------------------------------------------------------------------------------')
        for i in range(len(GE_FIX)):
            imprime('{:8}'.format(GE_FIX[i]), False)
            for j in range(len(GE_FIX_LIMITES[i])):
                imprime(' [{:10} {:10}]'.format(GE_FIX_LIMITES[i][j][0], GE_FIX_LIMITES[i][j][1]), False)
            imprime('')
        imprime('------------------------------------------------------------------------------------------')
    imprime('El precio del factor {} es variable exógena con valor igual a {}'.format(h[OR_PRE_EXCLUIDO], PRECIO_F_EXCLUIDO))
    if VALOR_F_TRA == 0:
        imprime('El precio del factor {} se calcula con la curva Phillips [paro: {}% alfa: {}]'.format(h[INDICE_F_TRA], PARO_INICIAL * 100., ALFA_PHILLIPS))
    elif VALOR_F_TRA != -1:
        imprime('El precio del factor {} es fijo con valor igual a {}'.format(h[INDICE_F_TRA], VALOR_F_TRA))
    imprime('')
    imprime('Función de utilidad de la demanda      {}'.format('Cobb-Douglas' if UTILIDAD_DEMANDA == 0 else 'CES'))
    if UTILIDAD_DEMANDA == 1:
        mfun.cabecera('', ind)
        mfun.cuerpo2D(['sigma_ces',], parametros.sigma_ces)
        mfun.cierre(ind)
    imprime('Demanda con consumos esenciales        {}'.format('Si' if DEM_ESENCIALES else 'No'))
    imprime('Aportación de factores por los hogares {}'.format('ENDOGENA' if FF_ENDOGENA else 'exógena'))
    imprime('Factor ahorro a largo plazo            {:10.2f} %'.format(100.0 * ALP_FACTOR))
    imprime('Estrategia                             {}'.format(GE_ESTRATEGIA))
    imprime('Periodicidad actualización             {}'.format(GE_ACTUALIZACION))
    imprime('Recombinación                          {:10.3f}'.format(GE_RECONBINACION))
    imprime('Tamaño de la población                 {:10}'.format(GE_DIM_POBLACION))
    imprime('Número de workers                      {:10}'.format(GE_WORKERS))
    imprime('Tolerancia en el objetivo              {:10.3e}'.format(GE_TOLERANCIA))
    imprime('Tolerancia en las verificaciones       {:10.3e}'.format(GE_VERIFICAR))
    imprime('Número máximo de iteraciones           {:10,}'.format(GE_MAX_ITER))
    imprime('Iteraciones para valorar progreso      {:10,}'.format(GE_PROGRESO))
    imprime('Iteraciones para historial             {:10,}'.format(GE_HISTORIAL))
    imprime('Iteraciones para soluciones            {:10,}'.format(GE_SOLUCIONES))
    imprime('Semilla números aleatorios             {:10}'.format(GE_SEMILLA))
    imprime('Consumos de los hogares en la solución {}'.format('Si' if GE_INCLUYE_XP else 'No'))
    imprime('Dimensión del vector de prueba         {:10}'.format(nvec_opt))
    imprime('Cálculo desvios                        {}'.format('Redundante' if OPT_DESVIOS==0 else 'Simple'))
    if   METRICA_ERROR == 0:
        imprime('Métrica del error: Error cuadrático medio')
    elif METRICA_ERROR == 1:
        imprime('Métrica del error: Valor absoluto')
    else:
        imprime('Métrica del error: Desvios elevados a {}'.format(POT_DESVIOS))
    imprime('-------------------------------------------------------------------')
    imprime('-------------------------------------------------------------------')
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
    if aviso_workers:
        imprime('Esta máquina tiene {} cores físicos y se han especificado {} workers.'.format(n_cores, GE_WORKERS))
        imprime('')
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
sam        = pandas.read_excel(FICHERO_SAM, index_col=0, header=0)
'''
el fichero calibrado.py contiene dos clases que, como cualquier clase, ejecutan el procedimiento
'def __init__' cuando se crea una variable de la clase:
    datos     : la función 'def __init__' de esta clase crea una serie de variables y les asigna
                valores de acuerdo con la información leída de la MCS.
    parametros: la función 'def __init__' de esta clase crea unas variables que son los parámetros
                del modelo y les calcula unos valores de acuerdo a las ecuaciones correspondientes
                y los valores asignados en la clase 'datos'.
'''
datos      = calibrado.datos(sam, h, ind, dem, idt, gov, trf, ayd, inv, ext, css, alp, INDICE_F_TRA, PARO_INICIAL)
parametros = calibrado.parametros(datos, ndem, nsec, INDICE_F_TRA, DEM_ESENCIALES, CON_ESENCIALES, SIGMA_CES_DEMANDA)
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
# adaptar algunos valores y parámetros según el escenario que se haya seleccionado
(CON_ESENCIALES) = esce.escenarios(__name__ == '__main__', datos, parametros, DECIMALES, ind, dem, h,
               NCASO, DEM_ADICIONAL, DEM_ADICIONAL_TIPO, DEM_ESENCIALES, CON_ESENCIALES, UTILIDAD_DEMANDA, RENTA_FICTICIA,
               AYD_ADICIONAL, GE_INCLUYE_XP,
               PRECIO_INI, VAR_FACTORES, FACTOR_CSSH, FACTOR_CSSE,
               SIGMA_ESCENARIO, ARANCELES
               )

if USAR_DLL:
    # conectar con la DLL y enviarle las opciones, datos y parámetros que necesita la DLL para calcular la función objetivo.
    # si además se usa el algoritmo genético de la DLL, se enviarán los parámetros de este más adelante
    libc = dll.abre_dll(SENDA_DLL)
    dll.envia_opciones  (libc)
    dll.envia_datos     (libc, datos)
    dll.envia_parametros(libc, parametros)
    libc.merito_s.argtypes = [ct.POINTER(ct.c_double)]
    libc.merito_s.restype = ct.c_double

if __name__ == '__main__':
    # sin el precio del último factor ya que su valor se fija de forma exógena, esto es realmente incorrecto
    # porque según las opciones el precio del factor que se incluirá en el vector de prueba pueser el del
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
    imprime_opciones(nvec_opt)
    if SAL_MCS:
        (rot, mcs0) = infor.reconstruye_MCS(datos, parametros, ind, dem, h, inv,css, idt, gov, trf, ext, ayd, alp,
                                              INDICE_F_TRA,datos.pF0,datos.pY0,datos.pQ0,datos.pD0,datos.pZ0,datos.epsilon0,datos.pWe,datos.pWm,
                                              datos.Y0,datos.X0,datos.F0,datos.Z0,datos.CssE0,datos.Tz0,datos.M0,datos.AgE0,
                                              datos.FF0,datos.Alp0,datos.Xp0,datos.Sp0,datos.CssH0,datos.AgH0,datos.Td0,datos.Xv0,datos.PssH0,
                                              datos.Xg0,datos.Sg0,datos.Tg0,datos.Tm0,
                                              datos.E0,datos.Sf0,
                                              TOLERA_MCS,'MCS base. Importes',True
                                             )

        infor.imprime_MCS(rot, mcs0, DECIMALES, TOLERA_MCS, 'MCS base. Importes',True)
    #valores_iniciales(vec_opt)
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
                datos.Td0,
                datos.Tz0,
                datos.Tm0,
                datos.CssE0,
                datos.CssH0,
                datos.AgE0,
                datos.AgH0,
                datos.Alp0,
    )
    # verifica solución
    infor.veri_solucion(datos, parametros, ind, dem, h,
                        vec_veri_sol, etq_veri, UTILIDAD_DEMANDA, DEM_ESENCIALES, DEM_ADICIONAL_TIPO, DEM_ADICIONAL, RENTA_FICTICIA, INDICE_F_TRA, AYD_ADI_DEM, ALP_FACTOR, CON_ESENCIALES,
                        'Verifica con los valores iniciales', GE_VERIFICAR
                        )
    if PRIMERA_VALORACION:
        imprime('Una primera valoración del modelo')
        imprime('---------------------------------')
        res_ecuaciones = sec_ecuaciones(vec_opt)
        infor.salida_valores(datos, parametros, DECIMALES, ind, dem, h, INDICE_F_TRA, VALOR_F_TRA, vec_opt, npre_sol, etq_precios, res_ecuaciones)

        calcula_desvios(res_ecuaciones, True)
        # verificar la solución
        (Apz,Fi,Ei,Mi,Di,Xpi,pf,pq,pe,pm,
            Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,AgE ,AgH ,CssE ,CssH,ebp,Zl,pz,
            Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,AgEr,AgHr,CssEr,CssHr,ebpr
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
                    Td,
                    Tz,
                    Tm,
                    CssE,
                    CssH,
                    AgE,
                    AgH,
                    Alp,
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
                                                Xg,Sg,datos.Tg0,Tm,
                                                E,datos.Sf0,TOLERA_MCS,
                                                'MCS primera valoración. Importes',True
                                              )
            infor.imprime_MCS(rot, mcs, DECIMALES, TOLERA_MCS, 'MCS primera valoración. Importes',True)
    
    historial   = []
    soluciones  = []
    mensaje_fin = []
    vfa         = 1.0e+18

    # función que 'differential_evolution' llamará después de probar cada posible solución 
    def vigila(intermediate_result):
        vf  = intermediate_result.fun   # valor de la función objetivo
        nit = intermediate_result.nit   # número de iteraciones
        if vf < GE_TOLERANCIA:
            # El desvio de la función objetivo es inferior al valor establecido, por lo que se da por terminada la minimización
            mensaje_fin.append('nit:{:9} fo:{:12.5e} valor función objetivo inferior a la tolerancia '.format(nit, vf))
            imprime('')
            imprime('')
            raise StopIteration
        if nit % GE_PROGRESO == 0:
            global vfa
            if (vfa - vf) < GE_TOLERANCIA:
                # no progresa significativamente, por lo que se da por terminada la minimización.
                # es importante que GE_TOLERANCIA sea lo suficientemente grande par que no se camcele antes de tiempo
                mensaje_fin.append('nit:{:9} mejora:{:12.5e} no progresa más'.format(nit, vfa - vf))
                raise StopIteration
            vfa = vf
            print('{:9} {:12.5e}'.format(nit, vf))
        if SAL_AUXILIARES:
            if GE_HISTORIAL > 0 and (nit == 1 or (nit % GE_HISTORIAL == 0)):
                # guardar el valor del error (función objetivo) que, al final, se escribirá en un fichero CSV
                historial.append([nit,vf])
            if GE_SOLUCIONES > 0 and (nit == 1 or (nit % GE_SOLUCIONES == 0)):
                # guardar el vector solución que, al final, se escribirá en un fichero CSV
                soluciones.append([nit,intermediate_result.x])
    
    # definir el rango de variación de los precios y variables
    bnds = cotas(ndem,nsec, vec_opt, nvec_opt, npre_sol, OR_PRE_EXCLUIDO, INDICE_F_TRA, VALOR_F_TRA,
                 GE_TOLERANCIA, GE_PRE_MIN, GE_PRE_MAX, GE_VAR_CERO, GE_VAR_MIN, GE_VAR_MAX,
                 ind_pvec_desde, GE_FIX, GE_FIX_LIMITES, GE_INCLUYE_XP, CON_ESENCIALES)
    # hacer compatible el vector de prueba inicial con los límites de variación de las variables
    for i in range(len(vec_opt)):
        if vec_opt[i]  < bnds[i][0]:
            vec_opt[i] = bnds[i][0]
        if vec_opt[i]  > bnds[i][1]:
            vec_opt[i] = bnds[i][1]
    pzi = copy.deepcopy(datos.pZ0)
    vec_opt_ini = copy.deepcopy(vec_opt)
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
    print('Evolución de la minimización')
    print('')
    res_ecuaciones = sec_ecuaciones(vec_opt)
    dist = calcula_desvios(res_ecuaciones, False)
    print('{:>9} {:12.5e}'.format('inicio', dist))

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
            # llamar al procedimiento en la DLL pasandole como vectors:
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
            par.append(np.float64(GE_TOLERANCIA))
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
            par.append(np.float64(nvec_opt));
            
            cotas_inf =[]
            cotas_sup =[]
            for i in range(nvec_opt):
                cotas_inf.append(np.float64(bnds[i][0]))
                cotas_sup.append(np.float64(bnds[i][1]))
            '''
            'dll.soluciona' devuelve un vector double donde los primeros 5 datos del vector son:
                0. el código de terminación (si es menor que 0 es finalización con error)
                1. el número de datos de la solución (aicionales a los 5 de cabecera)
                2. el número de intentos utilizados para encontrar la solución, si el algoritmo no progresa se hace
                    un nuevo intento a partir de una poblacion inicial nueva, así hasta los 'ALGE_MAX_INTENTOS'
                    especificados en los parámetros
                3. el número de generaciones calculadas por el último intento
                4. el valor de la función objetivo 
            '''
            cabecera = 5
            r_sol = dll.soluciona(libc, par, cotas_inf, cotas_sup, vec_opt, ALGE_RES_EXTENSA)
            r_res = r_sol[0]
            r_datos = int(r_sol[1])
            if ALGE_RES_EXTENSA == 1:
                # devuelve el valor de todas las variables concatenadas en un vector de valores double
                pf   = np.zeros(nfac)
                py   = np.zeros(nsec)
                pq   = np.zeros(nsec)
                pd   = np.zeros(nsec)
                F    = np.zeros((nsec,nfac))
                E    = np.zeros(nsec)
                M    = np.zeros(nsec)
                D    = np.zeros(nsec)
            
                pz   = np.zeros(nsec)
                pe   = np.zeros(nsec)
                pm   = np.zeros(nsec)
                Yp   = np.zeros(nsec)
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
                n = cabecera;
                for i in range(nfac):	pf[i]   = r_sol[n];n += 1
                for i in range(nsec):	py[i]   = r_sol[n];n += 1
                for i in range(nsec):	pq[i]   = r_sol[n];n += 1
                for i in range(nsec):	pd[i]   = r_sol[n];n += 1
                epsilon = r_sol[n];n += 1
                Apz = r_sol[n];n += 1
                for i in range(nsec):
                    for j in range(nfac):
                        F[i,j] = r_sol[n];n += 1
                for i in range(nsec):	E[i]    = r_sol[n];n += 1
                for i in range(nsec):	M[i]    = r_sol[n];n += 1
                for i in range(nsec):	D[i]    = r_sol[n];n += 1

                for i in range(nsec):	pz[i]   = r_sol[n];n += 1
                for i in range(nsec):	pe[i]   = r_sol[n];n += 1
                for i in range(nsec):	pm[i]   = r_sol[n];n += 1
                for i in range(nsec):	Yp[i]   = r_sol[n];n += 1
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
                Sg = r_sol[n];n += 1
                Sc = r_sol[n];n += 1
                ebp = r_sol[n];n += 1
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
                                    F.flatten(),
                                    E.flatten(),
                                    M.flatten(),
                                    D.flatten(),
                ))
            else:
                # devuelve el vector solución
                if OR_PRE_EXCLUIDO == 1:
                    # ajustar la ubicación del precio de los factores, porque se devuelven los dos 
                    r_sol[cabecera + 1] = r_sol[cabecera]
                sol = np.array([r_sol[i] for i in range(cabecera + 1, r_datos)], dtype=np.float64)

            imprime('')
            imprime('*****************************************************************')
            imprime('-------------------------- DLL genético -------------------------')
            if r_res < 0:
                imprime('error ({:15}) {}'.format(int(r_sol[0]), rot_res_dll_error[-int(r_sol[0])]))
                imprime('aplicación cancelada')
                imprime('')
                sys.exit()
            else:
                imprime('respuesta ({:3}) {}'.format(int(r_sol[0]),rot_res_dll_ok[int(r_sol[0])]))
                imprime('número de datos         :{:15}'.format(r_datos))
                imprime('intentos                :{:15}'.format(int(r_sol[2] + 1)))
                imprime('generaciones            :{:15}'.format(int(r_sol[3])))
                imprime('merito                  :{:15.5e}'.format(r_sol[4]))
            imprime('*****************************************************************')
            imprime('')
            rmin = rmin_dll(sol, int(sol[3]))
        else:
            rmin = differential_evolution(func=fo,
                    x0=vec_opt,
                    bounds=bnds,
                    strategy=GE_ESTRATEGIA,
                    popsize=GE_DIM_POBLACION,   # 15 es por defecto
                    #mutation=1., 
                    tol=GE_TOLERANCIA,
                    disp=False,
                    callback=vigila,
                    maxiter=GE_MAX_ITER,
                    updating=GE_ACTUALIZACION,
                    #vectorized=6,
                    recombination=GE_RECONBINACION,
                    seed=GE_SEMILLA,
                    constraints=restricciones,
            )

    t_fin = timer()

    imprime('Valores finales de las variables')
    imprime('')
    sol = rmin.x
    res_ecuaciones = sec_ecuaciones(sol)
    dist = calcula_desvios(res_ecuaciones, True)
    infor.salida_valores(datos, parametros, DECIMALES, ind, dem, h, INDICE_F_TRA, VALOR_F_TRA, sol, npre_sol, etq_precios, res_ecuaciones)
    (Apz,Fi,Ei,Mi,Di,Xpi,pf,pq,pe,pm,
        Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,AgE ,AgH ,CssE ,CssH,ebp,Zl,pz,
        Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,AgEr,AgHr,CssEr,CssHr,ebpr
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
                                            Xg,Sg,datos.Tg0,Tm,
                                            E,datos.Sf0,
                                            TOLERA_MCS,'MCS final. Importes',True
                                          )
        infor.imprime_MCS(rot, mcs, DECIMALES, TOLERA_MCS, 'MCS final. Importes',True)

        (rot_t, mcs_t) = infor.reconstruye_MCS(datos, parametros, ind, dem, h, inv,css, idt, gov, trf, ext, ayd, alp,
                                            INDICE_F_TRA,datos.pF0,datos.pY0,datos.pQ0,datos.pD0,datos.pZ0,datos.epsilon0,datos.pWe,datos.pWm,
                                            Yp,X,F,Z,CssE,Tz,M,AgE,
                                            FF,Alp,Xp,Sp,CssH,AgH,Td,Xv,datos.PssH0,
                                            Xg,Sg,datos.Tg0,Tm,
                                            E,datos.Sf0,
                                            TOLERA_MCS,'MCS final. Cantidades',False
                                          )
        infor.imprime_MCS(rot_t, mcs_t, DECIMALES, TOLERA_MCS, 'MCS final. Cantidades', False)

        if SAL_VAR_MCS:
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

    imprime('-----------------------------------------------------------')
    imprime('La distancia (error de la función objetivo) es {:9.3e}'.format(dist))
    if USAR_DLL:
        dist_dll = fo(sol);
        imprime('                                           DLL {:9.3e}'.format(dist_dll))
    imprime('-----------------------------------------------------------')
    imprime('')
    # verificar la solución, se prepara el vector que se pasará como parámetro a la función 'veri_solucion'
    vec_veri_sol = (
                pf,
                extrae_var(sol,'pY', 0, nsec),
                pz,
                extrae_var(sol,'pQ', 0, nsec),
                extrae_var(sol,'pD', 0, nsec),
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
                Td,
                Tz,
                Tm,
                CssE,
                CssH,
                AgE,
                AgH,
                Alp,
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
    if not USAR_ALGE_DLL:
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
