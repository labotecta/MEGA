'''
Se necesita float64, con float32 no es suficiente.

Aúnque scipy es muy eficiente por estar compilada en C, el punto débil es la función objetivo
que está íntegramente en Python.

Otro asunto sobre el que reflexionar, es la conveniencia de normalizar las desviaciones de las variables en el
resultado de la función objetivo. La aplicación no los normaliza, se trata de desviaciones en importes y todos
tienen el mismo peso, sea cual sea el importe absoluto de la variable.

Los pagos de impuestos directos del gobierno no se usan para nada
'''
import os
import sys
import copy
import itertools
import numpy as np
import matplotlib
import pandas
import scipy
import psutil 

from pandas          import Series
from scipy.optimize  import differential_evolution
from matplotlib      import pyplot as plt
from timeit          import default_timer as timer

import argumentos
import calibrado
import funciones     as mfun
import informes      as infor
import ecuaciones    as ecua
import produccion    as prod
import gobierno      as gob
import ahorro_inv    as ainv
import demanda       as deho
import exterior      as exte
import restricciones as restri

VERSION = '1.0.9'
# 4 Matrices de Contabilidad Social para las pruebas, se selecciona con NSAM
#               0            1             2              3
etq_sam  = ['1_hogar','2_hogares','3_hogares_AMP','MCA-ESP-05']
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
]

'''
if __name__ == '__main__':
    with open('C:/MEGA/Salidas/erroresMEGA.log', "a", encoding="utf-8") as log:
        log.write('lectura de parámetros\n')
'''
# extrae los argumentos de la línea de comandos y si no la hay de los valores por defecto,
# ajustando las dimensiones de las matrices 'reshape' cuando corresponde
try:
    args = argumentos.valores_opciones()
except BaseException as e:
    if __name__ == '__main__':
        '''
        with open('C:/MEGA/Salidas/erroresMEGA.log', "a", encoding="utf-8") as log:
            log.write('Error en la lectura de parámetros\n')
            log.write(str(e))
        '''
    print('Error en la lectura de parámetros')
    sys.exit()

nfac = args.NFAC    # número de factores
ndem = args.NDEM    # número de hogares
nsec = args.NSEC    # número de sectores
NSAM                = args.NSAM
DECIMALES           = args.DECIMALES
NCASO               = np.array(args.NCASO, dtype=int)
DEM_ADICIONAL_TIPO  = args.DEM_ADICIONAL_TIPO
if len(args.DEM_ADICIONAL) != ndem * nsec:
    if __name__ == '__main__':
        '''
        with open('C:/MEGA/Salidas/erroresMEGA.log', "a", encoding="utf-8") as log:
            log.write('Error. El número de datos para DEM_ADICIONAL {} no es el correcto {}'.format(len(args.DEM_ADICIONAL, ndem * nsec)) + '\n')
        '''
        print('Error. El número de datos para DEM_ADICIONAL {} no es el correcto {}'.format(len(args.DEM_ADICIONAL), ndem * nsec))
    sys.exit()
DEM_ADICIONAL       = np.array(args.DEM_ADICIONAL, dtype=np.float64).reshape(ndem, nsec)
if len(args.AYD_ADICIONAL) != ndem * nsec:
    if __name__ == '__main__':
        '''
        with open('C:/MEGA/Salidas/erroresMEGA.log', "a", encoding="utf-8") as log:
            log.write('Error. El número de datos para AYD_ADICIONAL {} no es el correcto {}'.format(len(args.AYD_ADICIONAL, ndem * nsec)) + '\n')
        '''
        print('Error. El número de datos para AYD_ADICIONAL {} no es el correcto {}'.format(len(args.AYD_ADICIONAL), ndem * nsec))
    sys.exit()
AYD_ADICIONAL       = np.array(args.AYD_ADICIONAL  , dtype=np.float64).reshape(ndem, nsec)
if len(args.CON_ESENCIALES) != ndem * nsec:
    if __name__ == '__main__':
        '''
        with open('C:/MEGA/Salidas/erroresMEGA.log', "a", encoding="utf-8") as log:
            log.write('Error. El número de datos para CON_ESENCIALES {} no es el correcto {}'.format(len(args.CON_ESENCIALES, ndem * nsec)) + '\n')
        '''
        print('Error. El número de datos para CON_ESENCIALES {} no es el correcto {}'.format(len(args.CON_ESENCIALES), ndem * nsec))
    sys.exit()
CON_ESENCIALES      = np.array(args.CON_ESENCIALES , dtype=np.float64).reshape(ndem, nsec)
DEM_ESENCIALES      = args.DEM_ESENCIALES
if CON_ESENCIALES.sum() == 0:
    if (13 in NCASO) == False:
        # si no se han especificado consumos esenciales no tiene sentido calcular demandas con consumos esenciales
        DEM_ESENCIALES = False
SIGMA_ESCENARIO     = np.array(args.SIGMA_ESCENARIO, dtype=np.float64)
ARANCELES           = np.array(args.ARANCELES, dtype=np.float64)
PREFIJO             = args.PREFIJO if args.PREFIJO != '"' else ''
OR_PRE_REFERENCIA   = args.OR_PRE_REFERENCIA
PRECIO_F_REFERENCIA = np.float64(args.PRECIO_F_REFERENCIA)
VALOR_F_TRA         = np.float64(args.VALOR_F_TRA)
PARO_INICIAL        = np.float64(args.PARO_INICIAL)
ALFA_PHILLIPS       = np.float64(args.ALFA_PHILLIPS)
FF_ENDOGENA         = args.FF_ENDOGENA
AHORRO_L_PLAZO      = args.AHORRO_L_PLAZO
OPT_DESVIOS         = args.OPT_DESVIOS
PRIMERA_VALORACION  = args.PRIMERA_VALORACION

SAL_CALIBRADO       = args.SAL_CALIBRADO
SALIDA_VEC_OPT      = args.SALIDA_VEC_OPT
SALIDA_DESVIOS      = args.SALIDA_DESVIOS
SAL_GRAFICOS_EVOL   = args.SAL_GRAFICOS_EVOL
SAL_GRAFICO_CES_DM  = args.SAL_GRAFICO_CES_DM
SAL_ISOCUANTA       = args.SAL_ISOCUANTA
SAL_VARIACIONES     = args.SAL_VARIACIONES
SAL_MCS             = args.SAL_MCS
SAL_VAR_MCS         = args.SAL_VAR_MCS

GE_INCLUYE_XP       = args.GE_INCLUYE_XP
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
        if __name__ == '__main__':
            '''
            with open('C:/MEGA/Salidas/erroresMEGA.log', "a", encoding="utf-8") as log:
                log.write('Error. No coincide el número de variables acotadas {} con el de límites {}'.format(k, n) + '\n')
            '''
            print('Error. No coincide el número de variables acotadas {} con el de límites {}'.format(k, n))
        sys.exit()
    if len(args.GE_FIX_LIMITES) != sum(args.GE_FIX_LON) * 2:
        if __name__ == '__main__':
            '''
            with open('C:/MEGA/Salidas/erroresMEGA.log', "a", encoding="utf-8") as log:
                log.write('Error. No coincide el número de parejas de limites {} con el de tamaño de GE_FIX_LIMITES {}'.format(sum(args.GE_FIX_LON) * 2, args.GE_FIX_LIMITES) + '\n')
            '''
            print('Error. No coincide el número de parejas de limites {} con el de tamaño de GE_FIX_LIMITES {}'.format(sum(args.GE_FIX_LON) * 2, args.GE_FIX_LIMITES))
        sys.exit()
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
FACTOR_CSSH         = np.array(args.FACTOR_CSSH, dtype=np.float64)
FACTOR_CSSE         = np.array(args.FACTOR_CSSE, dtype=np.float64)
if len(args.VAR_FACTORES) != ndem * nfac:
    if __name__ == '__main__':
        '''
        with open('C:/MEGA/Salidas/erroresMEGA.log', "a", encoding="utf-8") as log:
            log.write('Error. El número de datos para VAR_FACTORES {} no es el correcto {}'.format(len(args.VAR_FACTORES), ndem * nfac) + '\n')
        '''
        print('Error. El número de datos para VAR_FACTORES {} no es el correcto {}'.format(len(args.VAR_FACTORES), ndem * nfac))
    sys.exit()
VAR_FACTORES        = np.array(args.VAR_FACTORES, dtype=np.float64).reshape(ndem, nfac)
if len(args.VAR_FACTORES) != ndem * nfac:
    if __name__ == '__main__':
        '''
        with open('C:/MEGA/Salidas/erroresMEGA.log', "a", encoding="utf-8") as log:
            log.write('Error. El número de datos para DEM_ADICIONAL {} no es el correcto {}'.format(len(args.DEM_ADICIONAL), ndem * nsec) + '\n')
        '''
        print('Error. El número de datos para DEM_ADICIONAL {} no es el correcto {}'.format(len(args.DEM_ADICIONAL), ndem * nsec))
    sys.exit()
COE_VAB             = np.array(args.COE_VAB, dtype=np.float64)
SENDA_DATOS         = args.SENDA_DATOS
SENDA_SALIDAS       = args.SENDA_SALIDAS
SENDA_GRAFICOS      = args.SENDA_GRAFICOS

if __name__ == '__main__':
    '''
    with open('C:/MEGA/Salidas/erroresMEGA.log', "a", encoding="utf-8") as log:
        log.write('OK\n')
    '''

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

# --------------------------------------------------------------------
# ATENCION el factor trabajo debe ser la columna 'INDICE_F_TRA' de 'h'
# --------------------------------------------------------------------
INDICE_F_TRA = 1        # índice del factor trabajo, es mejor cambiar el orden en la definición de la lista 'h' que cambiar este índice

if   NSAM == 0:
    # Con un solo hogar (consumidor)
    DEM_ADICIONAL = np.array([
        [0., 0.],
    ])
    AYD_ADICIONAL = np.array([
        [0., 0.],
    ])
    AYD_ADI_DEM = AYD_ADICIONAL.sum(axis=1)
    '''
    DECIMALES = 5
    GE_TOLERANCIA     = 1.e-09  # límite para considerar el objetivo alcanzado.
    # Si el valor de una variable al aplicar la correspondiente ecuación del modelo varía, respecto del valor antes de aplicar la
    # ecuación, en menos de GE_VERIFICAR se considera que la ecuación se cumple (factibilidad de la ecuación)
    GE_VERIFICAR      = 1.e-08
    GE_HISTORIAL      = 50      # número de iteraciones para salvar el historial
    GE_SOLUCIONES     = 50      # número de iteraciones para salvar solución
    '''
    FICHERO_SAM = '{}/{}.xlsx'.format(SENDA_DATOS, "SAM_estandar")
    ind  = ('BRD' ,'MLK')       # sectores (industria)
    h    = ('CAP' ,'LAB')       # factores de producción
    dem  = ('HOH',)             # demanda de los hogares
    idt  = ('IDT',)             # impuestos indirectos a la producción
    trf  = ('TRF',)             # aranceles pagados por la producción (son los únicos que importan en este modelo)
    gov  = ('GOV',)             # gobierno
    ayd = ()                   # ayudas del gobierno
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
    '''
    DECIMALES = 3
    GE_TOLERANCIA     = 1.e-08  # límite para considerar el objetivo alcanzado.
    GE_VERIFICAR      = 1.e-07  # límite para considerar que la ecuación se cumple
    GE_HISTORIAL      = 50      # número de iteraciones para salvar el historial
    GE_SOLUCIONES     = 50      # número de iteraciones para salvar solución
    '''
    FICHERO_SAM = '{}/{}.xlsx'.format(SENDA_DATOS, "SAM_10_10")
    FICHERO_SAM = '{}/{}.xlsx'.format(SENDA_DATOS, "SAM_CSS")
    
    # declara las variables como 'tuple' (entre paréntesis) que es igual que 'list' pero no modificable, lo que las hace más eficientes)
    ind  = ('BRD' ,'MLK')       # sectores (industria)
    h    = ('CAP' ,'LAB')       # factores de producción
    dem  = ('HOH1','HOH2')      # demanda de los hogares
    idt  = ('IDT',)             # impuestos indirectos a la producción
    trf  = ('TRF',)             # aranceles pagados por la producción (son los únicos que importan en este modelo)
    gov  = ('GOV',)             # gobierno
    ayd = ()                   # ayudas del gobierno
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
    '''
    DECIMALES = 3
    GE_TOLERANCIA     = 1.e-08  # límite para considerar el objetivo alcanzado.
    GE_VERIFICAR      = 1.e-07  # límite para considerar que la ecuación se cumple
    GE_HISTORIAL      = 50      # número de iteraciones para salvar el historial
    GE_SOLUCIONES     = 50      # número de iteraciones para salvar solución
    '''
    FICHERO_SAM = '{}/{}.xlsx'.format(SENDA_DATOS, "SAM_AMP")
    # declara las variables como 'tuple' (entre paréntesis) que es igual que 'list' pero no modificable, lo que las hace más eficientes)
    ind  = ('BRD' ,'MLK')           # sectores (industria)
    h    = ('CAP' ,'LAB')           # factores de producción
    dem  = ('HOH1','HOH2','HOH3')   # demanda de los hogares
    idt  = ('IDT',)                 # impuestos indirectos a la producción
    trf  = ('TRF',)                 # aranceles pagados por la producción (son los únicos que importan en este modelo)
    gov  = ('GOV',)                 # gobierno
    ayd = ('AYD',)                 # ayudas del gobierno
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
    '''
    DECIMALES = 1
    GE_TOLERANCIA     = 1.e-11  # límite para considerar el objetivo alcanzado
    GE_VERIFICAR      = 1.e-08  # límite para considerar que la ecuación se cumple
    GE_HISTORIAL      =   500   # número de iteraciones para salvar el historial
    GE_SOLUCIONES     =  1000   # número de iteraciones para salvar solución
    '''
    FICHERO_SAM = '{}/{}.xlsx'.format(SENDA_DATOS, "MCA-ESP-05_ajustada_imp_final")
    ind  = ('AP1','AP2','AP3','AP4','AP5','AP6')    # sectores (industria)
    h    = ('K'  ,'L')                              # factores de producción
    dem  = ('C1','C2')                              # demanda de los hogares
    idt  = ('INP',)                                 # impuestos a la producción, otros impuestos a la producción
    trf  = ('TRF',)                                 # aranceles pagados por la producción (no los hay en esta MCS)
    gov  = ('SP',)                                  # gobierno
    ayd = ('AYD',)                                 # ayudas del gobierno
    inv  = ('A-I',)                                 # ahorro e inversión
    ext  = ('SE',)                                  # sector exterior
    css  = ('CSS',)                                 # cotizaciones a la seguridad social
    #
else:
    print('Número de MCS {} incorrecto'.format(NSAM))
    sys.exit()

TOLERA_MCS = 1.0 / 10.0 ** DECIMALES

if nfac != len(h):
    if __name__ == '__main__':
        '''
        with open('C:/MEGA/Salidas/erroresMEGA.log', "a", encoding="utf-8") as log:
            log.write('Error. El número de factores en la MCS {} no coincide con el especificado {}'.format(len(h), nfac) + '\n')
        '''
        print('Error. El número de factores en la MCS {} no coincide con el especificado {}'.format(len(h), nfac) + '\n')
    sys.exit()
if ndem != len(dem):
    if __name__ == '__main__':
        '''
        with open('C:/MEGA/Salidas/erroresMEGA.log', "a", encoding="utf-8") as log:
            log.write('Error. El número de hogares en la MCS {} no coincide con el especificado {}'.format(len(dem), ndem) + '\n')
        '''
        print('Error. El número de hogares en la MCS {} no coincide con el especificado {}'.format(len(dem), ndem) + '\n')
    sys.exit()
if nsec != len(ind):
    if __name__ == '__main__':
        '''
        with open('C:/MEGA/Salidas/erroresMEGA.log', "a", encoding="utf-8") as log:
            log.write('Error. El número de sectores en la MCS {} no coincide con el especificado {}'.format(len(ind), nsec) + '\n')
        '''
        print('Error. El número de sectores en la MCS {} no coincide con el especificado {}'.format(len(ind), nsec) + '\n')
    sys.exit()

if len(PREFIJO) > 1 and PREFIJO[0] == '=':
    # si PREFIJO empieza con el caracter '=' los caracteres del 1 en adelante se usarán como nombre de los
    # ficheros de salida en lugar de componerlos a partir de las opciones seleccionadas
    CASO = PREFIJO[1:]
else:
    # componer el nombre de los ficheros de salida en función de las opciones
    CASO  = PREFIJO + h[INDICE_F_TRA] + '_Desv_{:1d}_'.format(OPT_DESVIOS) 
    CASO += 'Fref_{:1d}_'.format(OR_PRE_REFERENCIA) + 'Pref_{:04.2f}_'.format(PRECIO_F_REFERENCIA) + ('PfL_{:05.3f}_'.format(VALOR_F_TRA) if  VALOR_F_TRA != -1 else '')
    CASO += ('END' if FF_ENDOGENA else 'EXO') + ('_Alp' if AHORRO_L_PLAZO else '')
    CASO += '_DimPb_{:03}_W_{:03}_'.format(GE_DIM_POBLACION, GE_WORKERS) + etq_sam[NSAM]
    for nc in NCASO:
        CASO += '_' + etq_caso[nc] 
    CASO += '_' + GE_ESTRATEGIA + '_' + 'Mcu' if METRICA_ERROR == 0 else ('Mab' if METRICA_ERROR == 1 else 'Mpt' + str(POT_DESVIOS))
    CASO += '_Da_{:1}'.format(DEM_ADICIONAL_TIPO) if abs(DEM_ADICIONAL).sum() != 0 else ''
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
        if ncol == 0:
            return vendo.reshape(nfil)
        return vendo.reshape(nfil, ncol)
    else:
        if ncol == 0:
            return vendo.item()
        return vendo

def cotas(ndem, nsec, vec_opt, nvec_opt, npre_sol, or_pre_referencia, indice_f_tra, valor_f_tra,
          ge_tolerancia, ge_pre_min, ge_pre_max, ge_var_cero, ge_var_min, ge_var_max,
          ind_pvec_desde, ge_fix, ge_fix_limites, ge_incluye_xp, con_esenciales):
    # definir el rango de variación de los precios y variables
    bnds = []
    for i in range(nvec_opt):
        bnds.append((0.,0.))

    # precios
    for i in range(npre_sol):
        if i == 0 and or_pre_referencia != indice_f_tra and valor_f_tra > 0:
            # el precio del factor OR_PRE_REFERENCIA no forma parte del vector solución
            # el que forma parte es el otro, luego si OR_PRE_REFERENCIA es el capital (!= INDICE_F_TRA),
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

    # desde el principio por si se han establecido límites manualmente para algún precio
    i = 0
    for ii in range(0, nvec_opt):
        n = 0
        esta = False
        if i <= pt[-1, 1]:
            # 'i' aún no ha superado el último puntero
            for nf in range(len(ge_fix)):
                if i == pt[nf,1]:
                    # se han especificado limites (en la fila n) para esta variable
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
    return bnds

def completa_pf(pf, F):
    if OR_PRE_REFERENCIA == 1:
        # el precio del factor OR_PRE_REFERENCIA no forma parte del vector solución, luego
        # si es 1, el trabajo es el que no forma parte y estará prefijado (PRECIO_F_REFERENCIA) o debemos calcularlo (precio_factor_trabajo_pFL)

        # Como el vector de prueba no incluye el precio del último factor (el trabajo), añadimos el precio del
        # último factor con valor 'PRECIO_F_REFERENCIA' si VALOR_F_TRA > 0 o lo calculamos con la curva Phillips si VALOR_F_TRA = 0
        if VALOR_F_TRA == 0:
            pf = np.append(pf, deho.precio_factor_trabajo_pFL(INDICE_F_TRA, datos.PobAct, ALFA_PHILLIPS, datos.pF0[INDICE_F_TRA], datos.F0, F))
        else:
            # se fja el precio del capital en PRECIO_F_REFERENCIA
            pf = np.append(pf, np.array([PRECIO_F_REFERENCIA]))
    else:
        # Como el vector de prueba no incluye el precio del primer factor (el capital), insertamos al principio el
        # precio del primer factor con valor 'PRECIO_F_REFERENCIA' 
        pf = np.insert(pf, 0, np.array([PRECIO_F_REFERENCIA]))
        # si VALOR_F_TRA = -1 el precio del factor trabajo es endógeno
        # si VALOR_F_TRA > 0 el precio del factor trabajo está acotado a VALOR_F_TRA 
        if VALOR_F_TRA == 0:
            # El precio del factor trabajo se calcula con la curva Phillips
            pf[INDICE_F_TRA] = deho.precio_factor_trabajo_pFL(INDICE_F_TRA, datos.PobAct, ALFA_PHILLIPS, datos.pF0[INDICE_F_TRA], datos.F0, F)
    return pf

def sec_ecuaciones(vec_opt, muestra_progreso):
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

    # guardamos los valores de la solución de prueba para luego compararlos con los calculados
    Fi = copy.deepcopy(F)
    Ei = copy.deepcopy(E)
    Mi = copy.deepcopy(M)
    Di = copy.deepcopy(D)

    # el precio de los factores tiene un tratamiento especial, en el vector solución solo se incluye
    # un precio: el del capital o el del trabajo, según OR_PRE_REFERENCIA sea 0 o 1
    pf = extrae_var(vec_opt, 'pF', 0, nfac - 1)
    # el precio del otro factor se añade al principio o al final de 'pf'
    pf = completa_pf(pf, F)
    # calculamos los precios del comercio internacional en moneda local
    (pe, pm) = exte.precio_moneda_local_pe_pm(datos.pWe, datos.pWm, epsilon)            # 6.14 y 6.15
    
    if GE_INCLUYE_XP:
        # el vector solución incluye los consumos de los hogares, necesario si se quiere acotar el
        # valor de los mismos, por ejemplo, para usar una función de utilidad con consumos esenciales
        Xpi = copy.deepcopy(extrae_var(vec_opt, 'Xp', ndem, nsec))

    # Los coeficientes de consumos intermedios 'ax' y factor compuesto 'ay' se consideran constantes
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
    Z  = exte.restriccion_producción_bruta_Z(parametros.teta, parametros.xie, parametros.xid, E, D, parametros.phi) # 6.20

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
        if AHORRO_L_PLAZO:
            # se ahorra a largo plazo (Alp) el exceso de ingresos (FF) respecto a los iniciales (FF0)
            # lo que significa que no se usará en comprar productos o invertir en los sectores
            # si AHORRO_L_PLAZO = False, el modelo se retroalimenta además de por los consumos internos, por la demanda final.
            Alp = FF - datos.FF0
            FF = datos.FF0
        else:
            Alp = datos.Alp0
    else:
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
    Sg = ainv.ahorro_gobierno_Sg(parametros.ssg, Td, Tz, Tm, AgE, AgH)                  # 6.12

    # El gobierno compra productos con cargo a sus ingresos disponibles que son lo que recauda por
    # impuestos menos su ahorro (Sg) y las ayudas a empresas (AgE) y hogares (AgH)
    Xg = gob.demanda_gobierno_Xg(parametros.mu, pq, Td, Tz, Tm, Sg, AgE, AgH)           # 6. 9

    # Seguridad social
    #--------------------------------------------------------------------------------------------------
    # cotizaciones a la seguridad social, un porcentaje del factor trabajo:

    #   de las empresas. (F) es la utilización de factores de cada sector
    CssE = gob.seguridad_social_empresas_CssE(parametros.ctzsse, pf, F, INDICE_F_TRA)
    #   de los hogares. (FF) es la prestación de factores de cada hogar (consumidor)
    CssH = gob.seguridad_social_hogares_CssH(parametros.ctzssh, pf, FF, Alp, INDICE_F_TRA)

    # los pagos de la seguridad social a los hogares (pensiones -PssH0-) es un valor constante fijado de antemano (exógena).

    # Inversión con cargo a los ahorros: los ahorros privados (Sp), del gobierno (Sg) y del
    # exterior (Sf0), se reparten entre sectores proporcionalmente a la MCS (parametros.landa)
    #--------------------------------------------------------------------------------------------------
    # superhavit / déficit de la seguridad social
    Sc = CssE.sum() + CssH.sum() - datos.PssH0.sum()
    Xv = ainv.demanda_inversion_Xv(parametros.landa, pq, Sp, Sg, Sc, epsilon, datos.Sf0)    # 6.10

    # Consumo de productos de los hogares. Mediante la función que optimiza la utilidad (pq, parametros.alfa) a
    # partir de los ingresos netos:
    # ingresos brutos: (pf, FF) + datos.PssH0 + AgH. El consumo es sin el Alp
    # gastos         : Sp + Td + CssH 
    #--------------------------------------------------------------------------------------------------
    if DEM_ESENCIALES:
        # función de demanda con consumos esenciales (Stone Geary)
        Xp = deho.demanda_maxima_utilidad_StoneGeary_Xp(parametros.alfa_esen, CON_ESENCIALES, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL)  # 6.13
    else:
        # función de demanda Cobb Douglas
        Xp = deho.demanda_maxima_utilidad_CobbDouglas_Xp(parametros.alfa, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL)                        # 6.13

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
    E  = exte.produccion_para_exportacion_E(parametros.teta, parametros.xie, pz, pe, Z, parametros.phi, datos.tauz, CssE, AgE, Apz) # 6.21
    Dt  = exte.produccion_para_local_D(parametros.teta, parametros.xid, pz, pd, Z, parametros.phi, datos.tauz, CssE, AgE, Apz)      # 6.22

    # Comercio internacional. Lo traemos aquí para usar los últimos valores calculados para E y M
    #--------------------------------------------------------------------------------------------------
    # Restricción a la balanza de pagos, las exportaciones menos las importaciones en divisas se debe mantener igual al valor inicial 'Sf0'
    # ya que debe haber una correlación entre los ingresos (exportaciones) y pagos (importaciones) en divisas: la que muestra la MCS

    # restricción a la balanza de pagos, las importaciones deben ser igual a las exportaciones más
    # la balanza de pagos inicial (datos.Sf0) que es exógena, en moneda extranjera
    ebp = exte.equilibrio_balance_pagos_moneda_extranjera(datos.pWe, E, datos.pWm, M, datos.Sf0)                                    # 6.16
    
    # Leontief para comparar, no tiene otro uso
    Zl = prod.produccion_sector_Z(X, ax, Yd, ay)                                                                                    # 6. 5 original
    
    '''
    Para calcular el demerito de la solución de prueba 'vec_opt', que recibe está función como argumento,
    recalculamos las variables para ver cuánto se diferencian del cálculo previo.
    para que el demérito sea el correcto hay que recalcular todas las variables.
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

    Tdr   = gob.impuestos_directos_Td(parametros.taud, pf, FFr, Alpr, datos.PssH0)          # 6. 6
    Tzr   = gob.impuestos_produccion_Tz(datos.tauz, pz, Zr)                                 # 6. 7
    Tmr   = gob.aranceles_importacion_Tm(datos.taum, pm, M)                                 # 6. 8
    
    Spr   = ainv.ahorro_hogares_Sp(parametros.ssp, FFr, pf, datos.PssH0)                    # 6.11
    AgEr  = gob.ayudas_empresas_AgE(parametros.cage, Tdr, Tzr, Tmr)
    AgHr  = gob.ayudas_hogares_AgH(parametros.cagh, Tdr, Tzr, Tmr, AYD_ADI_DEM)
    Sgr   = ainv.ahorro_gobierno_Sg(parametros.ssg, Tdr, Tzr, Tmr, AgEr, AgHr)              # 6.12
    Xgr   = gob.demanda_gobierno_Xg(parametros.mu, pq, Tdr, Tzr, Tmr, Sgr, AgEr, AgHr)      # 6. 9
    CssEr = gob.seguridad_social_empresas_CssE(parametros.ctzsse, pf, Fr, INDICE_F_TRA)
    CssHr = gob.seguridad_social_hogares_CssH(parametros.ctzssh, pf, FFr, Alpr, INDICE_F_TRA)
    Scr = CssEr.sum() + CssHr.sum() - datos.PssH0.sum()
    Xvr   = ainv.demanda_inversion_Xv(parametros.landa, pq, Spr, Sgr, Scr, epsilon, datos.Sf0)   # 6.10
    if DEM_ESENCIALES:
        Xpr   = deho.demanda_maxima_utilidad_StoneGeary_Xp(parametros.alfa_esen, CON_ESENCIALES, pq, pf, FFr, Spr, Tdr, CssHr, AgHr, datos.PssH0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL)    # 6.13
    else:
        Xpr   = deho.demanda_maxima_utilidad_CobbDouglas_Xp(parametros.alfa, pq, pf, FFr, Spr, Tdr, CssHr, AgHr, datos.PssH0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL)    # 6.13
    Qr    = exte.produccion_armington_Q(parametros.gamma, parametros.deltam, parametros.deltad, M, Dt, parametros.eta)                      # 6.17
    Mr    = exte.importacion_maxima_utilidad_armington_M(parametros.gamma, parametros.deltam, pq, pm, Qr, parametros.eta, datos.taum)       # 6.18
    Dar   = exte.produccion_maxima_utilidad_armington_D(parametros.gamma, parametros.deltad, pq, pd, Qr, parametros.eta)                    # 6.19
    Er    = exte.produccion_para_exportacion_E(parametros.teta, parametros.xie, pz, pe, Zr, parametros.phi, datos.tauz, CssEr, AgEr, Apz)   # 6.21
    Dtr   = exte.produccion_para_local_D(parametros.teta, parametros.xid, pz, pd, Zr, parametros.phi, datos.tauz, CssEr, AgEr, Apz)         # 6.22
    ebpr  = exte.equilibrio_balance_pagos_moneda_extranjera(datos.pWe, Er, datos.pWm, Mr, datos.Sf0)                                        # 6.16

    if muestra_progreso:
        respre = np.concatenate((pz, np.array(pe), np.array(pm)))
        imprime('{:10}      {:9.7f}'.format('pF_' + h[0], pf[0]))
        imprime('{:10}      {:9.7f}'.format('pF_' + h[1], pf[1]))
        mfun.i_tabla('precios', etq_precios[1:npre_sol], []       , vec_opt[1:npre_sol]  , True ,  7)
        mfun.i_tabla('/' , etq_precios[npre_sol:len(etq_precios)] , [], respre           , True ,  7)
        imprime('---------------------------------------------------------------------------------------------------------')
        imprime('Cantidades')
        imprime('---------------------------------------------------------------------------------------------------------')
        imprime('Factores aportados por los hogares. FF')
        mfun.i_tabla('/' , h                    , dem             , FF                   , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['suma FF']     , FF.sum(axis=0)       , False, DECIMALES)
        mfun.i_pie('/'   , h)
        imprime('Ahorro a largo plazo de los hogares. Alp')
        mfun.i_tabla(''  , []                   , dem             , Alp                  , True , DECIMALES)
        mfun.i_tabla(''  , []                   , ['suma Alp']    , Alp.sum(axis=0)      , False, DECIMALES)
        mfun.i_pie  ('/' , h)
        imprime('Factores aportados por los hogares. FF + Alp')
        mfun.i_tabla(''  , []                   , dem             , FF + Alp             , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['suma FF+Alp'] , (FF+Alp).sum(axis=0) , False, DECIMALES)
        mfun.i_pie('/'   , h)
        imprime('Factores utilizados por los sectores. F')
        mfun.i_tabla(''  , []                   , ind             , F                    , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['suma F',]     , F.sum(axis=0)        , False, DECIMALES)
        mfun.i_pie('/'   , h)
        imprime('Factor compuesto. Y (Valor Añadido Bruto)')
        mfun.i_tabla('/' , ind                  , ['Y óptimo F',] , Yp                   , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['Y nec.para Z',] , Yd                 , False, DECIMALES)
        imprime('Consumo intermedio (filas), ventas (columnas). X')
        mfun.i_tabla(''  , []                   , ind             , X.T                  , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['ventas X',]     , X.T.sum(axis=0)    , False, DECIMALES)
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
        mfun.i_tabla(''  , []                   , ['Z',]          , Z                    , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['Z leontief',] , Zl                   , False, DECIMALES)
        imprime('---------------------------------------------------------------------------------------------------------')
        imprime('Importes')
        imprime('---------------------------------------------------------------------------------------------------------')
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
        imprime('Pensiones')
        mfun.i_tabla('/' , dem                  , ['PssH0',]      , datos.PssH0          , True , DECIMALES)
        imprime('Ayudas del gobierno')
        mfun.i_tabla('/' , dem                  , ['AgH',]        , AgH                  , False, DECIMALES)
        mfun.i_tabla('/' , ind                  , ['AgE',]        , AgE                  , True , DECIMALES)
        imprime('Déficit por cuenta corriente. M - E')
        Sfde = M - E
        mfun.i_tabla(''  , []                   , ['Sf Ind',]    , Sfde                  , False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['Sf',]        , Sfde.sum()            , False, DECIMALES)
        imprime('Equilibrio de la balanza de pagos')
        mfun.i_tabla(''  , []                   , ['equi.bal.pag',], ebp                 , False, DECIMALES)
        imprime('')
        mfun.i_tabla(''  , []                   , ['Apz',]       , Apz                   , False, 5)
        imprime('')
        if VALOR_F_TRA == 0:
            paro = 100. * (1. - F[:,INDICE_F_TRA].sum() / datos.PobAct)
            mfun.i_tabla(''  , []                   , ['Pobla.activa',],datos.PobAct          , False, DECIMALES)
            mfun.i_tabla(''  , []                   , ['% paro',]     , paro                 , False, 2)
            imprime('')
        imprime('')
    if GE_INCLUYE_XP == False:
        Xpi = Xp
    res_ecuaciones = (Apz,Fi,Ei,Mi,Di,Xpi,
            Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,AgE ,AgH ,CssE ,CssH, ebp,Zl,pz,
            Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,AgEr,AgHr,CssEr,CssHr,ebpr
    )
    return res_ecuaciones

def calcula_desvios(res_ecuaciones, muestra_progreso):
    '''
    Calcula los desvíos (penalización) correspondientes a la ejecución de las ecuaciones 'sec_ecuaciones'
    '''
    (Apz,Fi,Ei,Mi,Di,Xpi,
        Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,AgE ,AgH ,CssE ,CssH, ebp, Zl, pz,
        Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,AgEr,AgHr,CssEr,CssHr,ebpr
    ) = res_ecuaciones

    # Se trata de forma individualizada la desviación en valor absoluto de cada variable

    # Apz no se puede afectar de un coeficiente grande, como se hace en GAMS, porque nuestro método
    # sacrificaría la convergencia de las otras variables para facilitar la anulación de Apz
    des_Apz = abs(Apz)

    # 'ebp' y 'ebpr' deben ser cero
    des_ebp = np.array([abs(ebp) + abs(ebpr)])

    # condiciones de equilibrio del mercado
    des_produccion = abs(Q - (Xp.sum(axis=0) + Xg + Xv + X.sum(axis=1))).flatten()      # 6.23

    # la utilización total de cada factor por los sectores 'F.sum(axis=0)' debe ser igual a la
    # aportación de los mismos por los hogares 'FF.sum(axis=0)'
    if  FF_ENDOGENA:
        # está garantizado el cumplimiento de la ecuación 6.24
        #des_factores = abs(F.sum(axis=0) - FF.sum(axis=0) - Alp.sum(axis=0)).flatten()  # 6.24
        des_factores   = np.zeros(2, dtype=np.float64)
        if AHORRO_L_PLAZO:
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
            (   des_produccion,des_factores,des_Apz,des_ebp,
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
            (   des_produccion,des_factores,des_Apz,des_ebp,
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
        mfun.tabla_2De(['equilib Q',] , des_produccion)
        mfun.tabla_2De(['equilib F',] , des_factores)
        mfun.tabla_2De(['des Fi',]    , des_Fi)
        mfun.tabla_2De(['des Ei',]    , des_Ei)
        mfun.tabla_2De(['des Mi',]    , des_Mi)
        if GE_INCLUYE_XP:
            mfun.tabla_2De(['des Xpi',], des_Xpi)

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
        if GE_INCLUYE_XP:
            imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Xpi', des_Xpi.sum()     , 100. * des_Xpi.sum()        / (1 if np.mean(Xpi)==0  else np.mean(Xpi))  , prec=DECIMALES))

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

    nvar_end = 0
    nvar_end += pf.size
    nvar_end += py.size
    nvar_end += pz.size
    nvar_end += pq.size
    nvar_end += pd.size

    (pe, pm) = exte.precio_moneda_local_pe_pm(datos.pWe, datos.pWm, epsilon)

    nvar_end += pe.size
    nvar_end += pm.size

    nvar_end += 1 # Apz

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
    v_medio[21] = np.median(abs(CssH))
    v_medio[22] = np.median(abs(AgE))
    v_medio[23] = np.median(abs(AgH))
    v_medio[24] = np.median(abs(Q))
    v_medio[25] = np.median(abs(F.sum(axis=0)))

    desviacion     = np.zeros(len(etq_veri), dtype=np.ndarray)
    desviacion[0]  = Y     - prod.produccion_factor_compuesto_Y(F, parametros.beta, parametros.b)           # 6. 1
    nvar_end += Y.size
    desviacion[1]  = F     - prod.uso_optimo_factores_F(parametros.beta, pf, py, Y)                         # 6. 2
    nvar_end += F.size
    desviacion[2]  = X     - prod.consumo_intermedio_X(Z, ax)                                               # 6. 3
    nvar_end += X.size
    desviacion[3]  = Y     - prod.utilizacion_factor_compuesto_Y(Z, ay)                                     # 6. 4
    # no se incrementa nvar_end porque ya se ha calculado la variable Y
    desviacion[4]  = pz    - prod.coste_unitario_produccion_pz(ay, py, ax, pq)                              # 6. 5 alternativa
    # no se incrementa nvar_end porque ya lo hemos sumado al principio
    desviacion[5]  = Td    - gob.impuestos_directos_Td(parametros.taud, pf, FF, Alp, datos.PssH0)           # 6. 6
    nvar_end += Td.size
    desviacion[6]  = Tz    - gob.impuestos_produccion_Tz(datos.tauz, pz, Z)                                 # 6. 7
    nvar_end += Tz.size
    desviacion[7]  = Tm    - gob.aranceles_importacion_Tm(datos.taum, pm, M)                                # 6. 8
    nvar_end += Tm.size
    desviacion[8]  = Xg    - gob.demanda_gobierno_Xg(parametros.mu, pq, Td, Tz, Tm, Sg, AgE, AgH)           # 6. 9
    nvar_end += Xg.size
    Sc = CssE.sum() + CssH.sum() - datos.PssH0.sum()
    desviacion[9]  = Xv    - ainv.demanda_inversion_Xv(parametros.landa, pq, Sp, Sg, Sc, epsilon, datos.Sf0)    # 6.10
    nvar_end += Xv.size
    desviacion[10] = Sp    - ainv.ahorro_hogares_Sp(parametros.ssp, FF, pf, datos.PssH0)                    # 6.11
    nvar_end += Sp.size
    desviacion[11] = Sg    - ainv.ahorro_gobierno_Sg(parametros.ssg, Td, Tz, Tm, AgE, AgH)                  # 6.12
    nvar_end += 1
    if DEM_ESENCIALES:
        desviacion[12] = Xp- deho.demanda_maxima_utilidad_StoneGeary_Xp(parametros.alfa_esen, CON_ESENCIALES, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL) # 6.13
    else:
        desviacion[12] = Xp- deho.demanda_maxima_utilidad_CobbDouglas_Xp(parametros.alfa, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL) # 6.13
    nvar_end += Xp.size
    desviacion[13] = ebp                                                                                    # 6.16
    nvar_end += ebp.size
    desviacion[14] = Q     - exte.produccion_armington_Q(parametros.gamma, parametros.deltam, parametros.deltad, M, D, parametros.eta) # 6.17
    nvar_end += Q.size
    desviacion[15] = M     - exte.importacion_maxima_utilidad_armington_M(parametros.gamma, parametros.deltam, pq, pm, Q, parametros.eta, datos.taum) # 6.18
    nvar_end += M.size
    desviacion[16] = D     - exte.produccion_maxima_utilidad_armington_D(parametros.gamma, parametros.deltad, pq, pd, Q, parametros.eta) # 6.19
    nvar_end += D.size
    desviacion[17] = Z     - exte.restriccion_producción_bruta_Z(parametros.teta, parametros.xie, parametros.xid, E, D, parametros.phi) # 6.20
    nvar_end += Z.size
    desviacion[18] = E     - exte.produccion_para_exportacion_E(parametros.teta, parametros.xie, pz, pe, Z, parametros.phi, datos.tauz, CssE, AgE, Apz)  # 6.21
    nvar_end += E.size
    desviacion[19] = D     - exte.produccion_para_local_D(parametros.teta, parametros.xid, pz, pd, Z, parametros.phi, datos.tauz, CssE, AgE, Apz) # 6.22
    # no se incrementa nvar_end porque ya se ha calculado la variable D
    desviacion[20]  = CssE - gob.seguridad_social_empresas_CssE(parametros.ctzsse, pf, F, INDICE_F_TRA)         # CssE
    nvar_end += CssE.size
    desviacion[21]  = CssH - gob.seguridad_social_hogares_CssH(parametros.ctzssh, pf, FF, Alp, INDICE_F_TRA)    # CssH
    nvar_end += CssH.size
    desviacion[22]  = AgE  - gob.ayudas_empresas_AgE(parametros.cage, Td, Tz, Tm)                           # AgE
    nvar_end += AgE.size
    desviacion[23]  = AgH  - gob.ayudas_hogares_AgH(parametros.cagh, Td, Tz, Tm, AYD_ADI_DEM)               # AgH
    nvar_end += AgH.size

    desviacion[24]  = Q    - (Xp.sum(axis=0) + Xg + Xv + X.sum(axis=1))                                     # 6.23
    desviacion[25]  = F.sum(axis=0) - (FF.sum(axis=0) + Alp.sum(axis=0))                                    # 6.24

    '''
    if FF_ENDOGENA:
        nvar_end += FF.size
    '''

    if AHORRO_L_PLAZO:
        nvar_end += Alp.size

    imprime(titulo)
    imprime('Número de variables endógenas :{} incluida Apz'.format(nvar_end))
    imprime('')
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
                p_error_max = '{:>13}'.format('--')
            else:
                p_error_max = '{:13.3f}'.format(100 * max_des_error / v_medio[i])
            imprime('{:11} {:13.5e} {:13.5e} {:13.5e} {}'.format(etq_veri[i], v_medio[i], suma_des_abs, max_des_error, p_error_max))
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
            pem = max_des_error
            p_error_max = '{:>13}'.format('--')
        else:
            pem = max_des_error / v_medio[i]
            p_error_max = '{:13.3f}'.format(100 * pem)
        if pem > 0.0001:    # 0.01%
            imprime('{:11} {:13.5e} {:13.5e} {:13.5e} {}'.format(etq_veri[i], v_medio[i], suma_des_abs, max_des_error, p_error_max))
            nfallos += 1
    if nfallos == 0:
        imprime('======  Se cumplen todas las ecuaciones en % de error máximo ======')
    imprime('----------- ------------- ------------- ------------- -------------')
    imprime('')
    imprime('-------------------------------')
    imprime('Ecm.total desvios {:13.5e}'.format(desvio))
    imprime('-------------------------------')

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
# epsilon (tipo de cambio)
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
# leemos la Matriz de contabilidad social (SAM) de esta economía
sam        = pandas.read_excel(FICHERO_SAM, index_col=0, header=0)
datos      = calibrado.datos(sam, h, ind, dem, idt, trf, gov, ayd, inv, ext, css, INDICE_F_TRA, PARO_INICIAL)
parametros = calibrado.parametros(datos, ndem, nsec, INDICE_F_TRA, DEM_ESENCIALES, CON_ESENCIALES)
if __name__ == '__main__':
    imprime('')
    if SAL_CALIBRADO:
        infor.salida_calibrado(datos, parametros, ind, dem, h, DEM_ESENCIALES)
    if SAL_GRAFICO_CES_DM:
        infor.grafico_CES_local_importacion(SENDA_GRAFICOS, datos, parametros, ind, dem, h)
    if SAL_ISOCUANTA:
        infor.isocuanta(SENDA_GRAFICOS, PREFIJO, datos, parametros, ind, dem, h, datos.D0, datos.M0, 0, 50000, 0, 100, -0.20, 0.5)
# punteros para extraer variables del vector solución
(etq_vec_opt,ind_pvec_desde,ind_pvec_hasta) = punteros()

# equilibrio del balace de pagos inicial
ebp_ini = exte.equilibrio_balance_pagos_moneda_extranjera(datos.pWe, datos.E0, datos.pWm, datos.M0, datos.Sf0)     # 6.16

# ---------------------------------------------------------------------
# Solucíonar el MEGA
# ---------------------------------------------------------------------
# NCASO selecciona el escenario a calcular, los escenarios se han elegido sin más sentido que el de probar la aplicación 
if __name__ == '__main__':
    if abs(DEM_ADICIONAL).sum() != 0:
        if DEM_ADICIONAL_TIPO == 0:
            imprime('Demanda adicional (importe)')
        else:
            imprime('Demanda adicional (cantidad)')
        mfun.i_tabla(''  , [] , dem             , DEM_ADICIONAL, False     , DECIMALES)
        imprime('')
    if abs(AYD_ADICIONAL).sum() != 0:
        imprime('Ayudas adicionales')
        mfun.i_tabla(''  , [] , dem             , AYD_ADICIONAL, False     , DECIMALES)
        imprime('')
    if abs(CON_ESENCIALES).sum() != 0 and GE_INCLUYE_XP and (13 in NCASO) == False:
        # se han especificado consumos esenciales, Xp se incluye en la solución y no es el caso 13 que hace CON_ESENCIALES = Xp0
        imprime('Consumos esenciales. Cantidades')
        mfun.i_tabla(''  , [] , dem             , CON_ESENCIALES, False     , DECIMALES)
        imprime('')
for nc in NCASO:
    if nc > 0:
        if __name__ == '__main__':
            imprime('---------------------------------------------------------------------------------------------------')
            imprime('Escenario {}'.format(nc))
            imprime('---------------------------------------------------------------------------------------------------')
        if   nc == 1:
            if __name__ == '__main__':
                imprime('Elasticidad de la demanda (alfa) calibrado / escenario')
                mfun.tabla_2D(dem, parametros.alfa)
                imprime('')

            for i in range(ndem):
                for j in range(nsec):
                    parametros.alfa[i,j] = 1.0 / nsec

            if __name__ == '__main__':
                mfun.tabla_2D(dem, parametros.alfa)
        elif nc == 2:
            if __name__ == '__main__':
                imprime('Elasticidad de la producción (beta) calibrado / escenario')
                mfun.tabla_2D(ind, parametros.beta)
                imprime('')

            for i in range(nsec):
                for j in range(nfac):
                    parametros.beta[i,j] = 0.5

            if __name__ == '__main__':
                mfun.tabla_2D(ind, parametros.beta)
        elif nc == 3:
            if __name__ == '__main__':
                imprime('Aranceles de importación (taum) calibrado / escenario')
                mfun.tabla_2D(['Productos',], datos.taum)
                imprime('')

            for i in range(nsec):
                datos.taum[i] = 0.

            if __name__ == '__main__':
                mfun.tabla_2D(['Productos',], datos.taum)
        elif nc == 4:
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
        elif nc == 5:
            if __name__ == '__main__':
                imprime('Precios')
                for i in range(nfac):
                    imprime('{:9.7f}'.format(datos.pF0[i]))
                for i in range(nsec):
                    imprime('{:9.7f}'.format(datos.pY0[i]))
                    imprime('{:9.7f}'.format(datos.pZ0[i]))
                    imprime('{:9.7f}'.format(datos.pQ0[i]))
                    imprime('{:9.7f}'.format(datos.pD0[i]))
                imprime('{:9.7f}'.format(datos.epsilon))
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
                    imprime('{:9.7f}'.format(datos.pF0[i]))
                for i in range(nsec):
                    imprime('{:9.7f}'.format(datos.pY0[i]))
                    imprime('{:9.7f}'.format(datos.pZ0[i]))
                    imprime('{:9.7f}'.format(datos.pQ0[i]))
                    imprime('{:9.7f}'.format(datos.pD0[i]))
                imprime('{:9.7f}'.format(datos.epsilon))
        elif nc == 6:
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
        elif nc == 7:
            if __name__ == '__main__':
                imprime('Propensión al ahorro')
                for et in dem:
                    imprime('{:4} {:9.5f}'.format(et, parametros.ssp[0]))
                imprime('')

            parametros.ssp[0] = parametros.ssp[0] / 2.

            if __name__ == '__main__':
                for et in dem:
                    imprime('{:4} {:9.5f}'.format(et, parametros.ssp[0]))
        elif nc == 8:
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
        elif nc == 9:
            # simplemente cambia la preferencia de los consumos, no se añade demanda
            if __name__ == '__main__':
                imprime('Elasticidad de la demanda (alfa) calibrado')
                if DEM_ESENCIALES:
                    mfun.tabla_2D(dem, parametros.alfa_esen)
                else:
                    mfun.tabla_2D(dem, parametros.alfa)
                imprime('')

            # modificar preferencias (alfa) de consumo con la demanda adicional
            Xp0 = datos.Xp0 + DEM_ADICIONAL
            if DEM_ESENCIALES:
                renta = ecua.demanda_StoneGeary_renta(datos.FF0, datos.PssH0, datos.AgH0, datos.Sp0, datos.Td0, datos.CssH0, Xp0, CON_ESENCIALES, datos.pF0, datos.pQ0)
                if np.any(renta <= 0):
                    imprime('Renta menor o igual a 0')
                    for i in range(len(renta)):
                        imprime('{:3} {:12.5e}'.format(i + 1, renta[i]))
                    sys.exit()
                parametros.alfa_esen = ecua.demanda_StoneGeary_alfa(datos.FF0, datos.PssH0, datos.AgH0, datos.Sp0, datos.Td0, datos.CssH0, Xp0, CON_ESENCIALES, datos.pF0, datos.pQ0)
            else:
                parametros.alfa = ecua.demanda_CobbDouglas_alfa(Xp0)
        
            # para evitar que se sume el efecto en preferencia con el incremento en demanda
            DEM_ADICIONAL.fill(0.)

            if __name__ == '__main__':
                imprime('Elasticidad de la demanda (alfa) escenario')
                if DEM_ESENCIALES:
                    mfun.tabla_2D(dem, parametros.alfa_esen)
                else:
                    mfun.tabla_2D(dem, parametros.alfa)
                imprime('---------------------------------------------------------------------------------------------------')
                imprime('Demanda adicional no suma en consumos')
        elif nc == 10:
            if __name__ == '__main__':
                imprime('Elasticidad de la demanda (alfa) calibrado')
                if DEM_ESENCIALES:
                    mfun.tabla_2D(dem, parametros.alfa_esen)
                else:
                    mfun.tabla_2D(dem, parametros.alfa)
                imprime('')

            # modificar preferencias (alfa) de consumo porque las ayudas son para adquirir productos en concreto
            Xp0 = datos.Xp0 + AYD_ADICIONAL
            if DEM_ESENCIALES:
                renta = ecua.demanda_StoneGeary_renta(datos.FF0, datos.PssH0, datos.AgH0, datos.Sp0, datos.Td0, datos.CssH0, Xp0, CON_ESENCIALES, datos.pF0, datos.pQ0)
                if np.any(renta <= 0):
                    imprime('Renta menor o igual a 0')
                    for i in range(len(renta)):
                        imprime('{:3} {:12.5e}'.format(i + 1, renta[i]))
                    sys.exit()
                parametros.alfa_esen = ecua.demanda_StoneGeary_alfa(datos.FF0, datos.PssH0, datos.AgH0, datos.Sp0, datos.Td0, datos.CssH0, Xp0, CON_ESENCIALES, datos.pF0, datos.pQ0)
            else:
                parametros.alfa = ecua.demanda_CobbDouglas_alfa(Xp0)

            if __name__ == '__main__':
                imprime('Elasticidad de la demanda (alfa) escenario')
                if DEM_ESENCIALES:
                    mfun.tabla_2D(dem, parametros.alfa_esen)
                else:
                    mfun.tabla_2D(dem, parametros.alfa)
        elif nc == 11:
            if __name__ == '__main__':
                imprime('Elasticidad de sustitución (sigma) calibrado')
                mfun.tabla_2D(ind, parametros.sigma)
                imprime('Parámetro de elasticidad (eta) calibrado')
                mfun.tabla_2D(ind, parametros.eta)
                imprime('Coeficiente de escala de la función de Armington (gamma) calibrado')
                mfun.tabla_2D(ind, parametros.gamma)
                imprime('Participación local en la función del producto de Armington (deltad) calibrado')
                mfun.tabla_2D(ind, parametros.deltad)
                imprime('Participación de la importación en la función del producto de Armington (deltam) calibrado')
                mfun.tabla_2D(ind, parametros.deltam)
                imprime('')

            # modificar sigma y eta pero no gamma, deltam ni deltad
            parametros.sigma = SIGMA_ESCENARIO
            parametros.eta = (parametros.sigma - 1.) / parametros.sigma

            if __name__ == '__main__':
                imprime('Elasticidad de sustitución (sigma) escenario')
                mfun.tabla_2D(ind, parametros.sigma)
                imprime('Parámetro de elasticidad (eta) escenario')
                mfun.tabla_2D(ind, parametros.eta)
                imprime('Coeficiente de escala de la función de Armington (gamma) escenario')
                mfun.tabla_2D(ind, parametros.gamma)
                imprime('Participación local en la función del producto de Armington (deltad) escenario')
                mfun.tabla_2D(ind, parametros.deltad)
                imprime('Participación de la importación en la función del producto de Armington (deltam) escenario')
                mfun.tabla_2D(ind, parametros.deltam)
        elif nc == 12:
            if __name__ == '__main__':
                imprime('Aranceles de importación (taum) calibrado / escenario')
                mfun.tabla_2D(['Productos',], datos.taum)
                imprime('')

            datos.taum = ARANCELES

            if __name__ == '__main__':
                mfun.tabla_2D(['Productos',], datos.taum)
        elif nc == 13:
            if GE_INCLUYE_XP == False:
                if __name__ == '__main__':
                    imprime('Número de caso {} es incorrecto cuando no se incluyen los Xp en la solución (se ha establecido GE_INCLUYE_XP=False)'.format(NCASO))
                sys.exit()
            else:
                if __name__ == '__main__':
                    CON_ESENCIALES = datos.Xp0
                    imprime('Consumos esenciales = Xp0. Cantidades')
                    mfun.i_tabla(''  , [] , dem             , CON_ESENCIALES, False     , DECIMALES)
                    imprime('')
        else:
            if __name__ == '__main__':
                imprime('Número de caso {} incorrecto'.format(NCASO))
            sys.exit()
    if __name__ == '__main__':
        imprime('---------------------------------------------------------------------------------------------------')
if __name__ == '__main__':
    imprime('')

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
    if GE_INCLUYE_XP:
        vec_opt = np.concatenate((vec_opt, datos.Xp0.flatten()))
    nvec_opt = len(vec_opt)
    vec_opt_ini = copy.deepcopy(vec_opt)
    pzi = copy.deepcopy(datos.pZ0)
    if SAL_MCS:
        (rot, mcs0) = infor.reconstruye_MCS(datos, parametros, ind, dem, h, inv,css, idt, gov, ext, ayd,
                                              INDICE_F_TRA,datos.pF0,datos.pY0,datos.pQ0,datos.pD0,datos.pZ0,datos.epsilon0,datos.pWe,datos.pWm,
                                              datos.X0,datos.F0,datos.CssE0,datos.Tz0,datos.M0,datos.AgE0,
                                              datos.FF0,datos.Alp0,datos.Xp0,datos.Sp0,datos.CssH0,datos.AgH0,datos.Td0,datos.Xv0,datos.PssH0,
                                              datos.Xg0,datos.Sg0,datos.Tg0,
                                              datos.E0,datos.Sf0,
                                              TOLERA_MCS
                                             )

        infor.imprime_MCS(rot, mcs0, DECIMALES, 'MCS base. Importes', TOLERA_MCS)
    #valores_iniciales(vec_opt)
    infor.valores_iniciales(datos, parametros, DECIMALES, ind, dem, h, INDICE_F_TRA, VALOR_F_TRA, vec_opt, npre_sol, etq_precios, ebp_ini)

    imprime('-------------------------------------------------------------------')
    imprime('-------------------------------------------------------------------')
    if GE_RESTRICCIONES:
        imprime('MEGA mediante algoritmo genético. Resolución con restricciones ' + ('lineales' if GE_TIPO_RE==0 else 'no lineales'))
    else:
        imprime('MEGA mediante algoritmo genético. Resolución sin restricciones')
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
    imprime('El precio del factor {} es variable exógena con valor igual a {}'.format(h[OR_PRE_REFERENCIA], PRECIO_F_REFERENCIA))
    if VALOR_F_TRA == 0:
        imprime('El precio del factor {} se calcula con la curva Phillips [paro: {}% alfa: {}]'.format(h[INDICE_F_TRA], PARO_INICIAL * 100., ALFA_PHILLIPS))
    elif VALOR_F_TRA != -1:
        imprime('El precio del factor {} es fijo con valor igual a {}'.format(h[INDICE_F_TRA], VALOR_F_TRA))
    imprime('')    
    imprime('Demanda con consumos esenciales        {}'.format('Si' if DEM_ESENCIALES else 'No'))
    imprime('Aportación de factores por los hogares {}'.format('ENDOGENA' if FF_ENDOGENA else 'exógena'))
    imprime('Ahorro a largo plazo de los hogares    {}'.format('Si' if AHORRO_L_PLAZO else 'No'))
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
    veri_solucion(vec_veri_sol, 'Verifica con los valores iniciales', GE_VERIFICAR)
    imprime('')
    if PRIMERA_VALORACION:
        imprime('Una primera valoración del modelo')
        imprime('---------------------------------')
        res_ecuaciones = sec_ecuaciones(vec_opt, True)
        calcula_desvios(res_ecuaciones, True)
        # verificar la solución
        (Apz,Fi,Ei,Mi,Di,Xpi,
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
        veri_solucion(vec_veri_sol,'Verifica en la primera valoración', GE_VERIFICAR)
        imprime('')
        imprime('---------------------------------')
        imprime('')
        if SAL_MCS:
            pe = datos.pWe * epsilon
            pm = datos.pWm * epsilon
            (rot, mcs) = infor.reconstruye_MCS(datos, parametros, ind, dem, h, inv,css, idt, gov, ext, ayd,
                                                INDICE_F_TRA,pf,py,pq,pd,pz,epsilon,pe,pm,
                                                X,F,CssE,Tz,M,AgE,
                                                FF,Alp,Xp,Sp,CssH,AgH,Td,Xv,datos.PssH0,
                                                Xg,Sg,datos.Tg0,
                                                E,datos.Sf0,
                                                TOLERA_MCS
                                              )
            infor.imprime_MCS(rot, mcs, DECIMALES, 'MCS primera valoración. Importes', TOLERA_MCS)
    
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
    bnds = cotas(ndem,nsec, vec_opt, nvec_opt, npre_sol, OR_PRE_REFERENCIA, INDICE_F_TRA, VALOR_F_TRA,
                 GE_TOLERANCIA, GE_PRE_MIN, GE_PRE_MAX, GE_VAR_CERO, GE_VAR_MIN, GE_VAR_MAX,
                 ind_pvec_desde, GE_FIX, GE_FIX_LIMITES, GE_INCLUYE_XP,CON_ESENCIALES)
    # hacer compatible el vector de prueba inicial con los límites de variación de las variables
    for i in range(len(vec_opt)):
        if vec_opt[i]  < bnds[i][0]:
            vec_opt[i] = bnds[i][0]
        if vec_opt[i]  > bnds[i][1]:
            vec_opt[i] = bnds[i][1]
    vec_opt_ini = copy.deepcopy(vec_opt)
    if SALIDA_VEC_OPT:
        imprime('    L.INF         V0          L.SUP')
        imprime('------------ ------------ ------------')
        n = 0
        imprime(etq_vec_opt[n])
        for i in range(len(vec_opt)):
            if i == ind_pvec_hasta[n]:
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
    res_ecuaciones = sec_ecuaciones(vec_opt, False)
    dist = calcula_desvios(res_ecuaciones, False)
    print('{:>9} {:12.5e}'.format('inicio', dist))
    t_inicio = timer()

    # minimizar el error de la función objetivo
    if GE_WORKERS != 1:
        rmin = differential_evolution(func=fun_objetivo,
                x0=vec_opt,
                bounds=bnds,
                strategy=GE_ESTRATEGIA,
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
                seed=GE_SEMILLA,
                constraints=restricciones,
        )
    else:
        rmin = differential_evolution(func=fun_objetivo,
                x0=vec_opt,
                bounds=bnds,
                strategy=GE_ESTRATEGIA,
                popsize=GE_DIM_POBLACION,   # 15 es por defecto, 3 es mucho más rápido
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
    sol = rmin.x
    imprime('Valores finales de las variables')
    imprime('')
    res_ecuaciones = sec_ecuaciones(sol, True)
    dist = calcula_desvios(res_ecuaciones, True)
    (Apz,Fi,Ei,Mi,Di,Xpi,
        Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,AgE ,AgH ,CssE ,CssH,ebp,Zl,pz,
        Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,AgEr,AgHr,CssEr,CssHr,ebpr
    ) = res_ecuaciones
    pf = extrae_var(sol,'pF', 0, nfac - 1)
    pf = completa_pf(pf, F)
    if SAL_MCS:
        py = extrae_var(sol,'pY', 0, nsec)
        pq = extrae_var(sol,'pQ', 0, nsec)
        pd = extrae_var(sol,'pD', 0, nsec)
        epsilon = extrae_var(sol,'epsilon', 0, 0)
        (pe, pm) = exte.precio_moneda_local_pe_pm(datos.pWe, datos.pWm, epsilon)
        (rot, mcs) = infor.reconstruye_MCS(datos, parametros, ind, dem, h, inv,css, idt, gov, ext, ayd,
                                            INDICE_F_TRA,pf,py,pq,pd,pz,epsilon,pe,pm,
                                                X,F,CssE,Tz,M,AgE,
                                                FF,Alp,Xp,Sp,CssH,AgH,Td,Xv,datos.PssH0,
                                                Xg,Sg,datos.Tg0,
                                                E,datos.Sf0,
                                                TOLERA_MCS
                                          )
        infor.imprime_MCS(rot, mcs, DECIMALES, 'MCS final. Importes', TOLERA_MCS)
        if SAL_VAR_MCS:
            infor.imprime_MCS(rot, mcs-mcs0, DECIMALES, 'Diferencias entre los valores finales y los iniciales de la MCS. Cantidades', 2.0 * TOLERA_MCS)

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
    veri_solucion(vec_veri_sol,'Verifica con la solución final', GE_VERIFICAR)
    if len(mensaje_fin) > 0 or dist > GE_TOLERANCIA:
        imprime('')
        imprime('***********************************************************************')
        for mensaje in mensaje_fin:
            imprime(mensaje)
        if (dist > GE_TOLERANCIA):
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
