import argparse
def sab(v):
    if v.lower() in ('yes', 'true', 't', 'y', 'si', 's'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n'):
        return False
    else:
        raise argparse.ArgumentTypeError('No es un valor boleano.')

def valores_opciones():
    parser = argparse.ArgumentParser()
    '''
    NCASO
        'base',                 #  0
        'alfa',                 #  1
        'beta',                 #  2
        'sin_arancel',          #  3
        'doble_arancel',        #  4
        'pre_ini',              #  5
        'factores',             #  6
        'ahorro',               #  7
        'seg_social',           #  8
        'dem_alfa',             #  9
        'dem_alfa_factores',    # 10
        'dem_factores',         # 11
        'alfa_ayudas',          # 12
        'sigma',                # 13
        'aranceles',            # 14
    '''
    # si PREFIJO empieza con el caracter '=' los caracteres del 1 en adelante se usarán como nombre de los ficheros de salida en
    # lugar de componerlos a partir de las opciones seleccionadas, en este caso NO puede haber ESPACIOS en blanco intercalados
    parser.add_argument('--NFAC'               , type=int  , default=2    , help="número de factores")
    parser.add_argument('--NDEM'               , type=int  , default=2    , help="número de hogares")
    parser.add_argument('--NSEC'               , type=int  , default=6    , help="número de sectores")
    parser.add_argument('--PREFIJO'            , type=str  , default='=N2_', help="un literal que se añade al principio del nombre de los archivos de salida")
    parser.add_argument('--NCASO'              , type=int  , default=[12], nargs='*', help="número de esenario a utilizar, se pueden combinar varios, por ejemplo default=[0,14]")
    # las matrices se especifican aplanadas como vectores
    parser.add_argument('--DEM_ADICIONAL'      , type=float, default=[0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.], nargs='*', help="demanda adicional exógena de productos para los hogares")
    parser.add_argument('--DEM_ADICIONAL_TIPO' , type=int  , default=0    , help="se añade 'DEM_ADICIONAL' al importe demandado; 1: se añade 'DEM_ADICIONAL' a la cantidad demandada")
    parser.add_argument('--AYD_ADICIONAL'      , type=float, default=[0., 0., 0., 0., 0., 0., 0., 0., 1000., 0., 0., 0.], nargs='*', help="ayuda adicional exógena por producto para el hogar 1")
    parser.add_argument('--CON_ESENCIALES'     , type=float, default=[0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.], nargs='*', help="consumos esenciales para los hogares")
    parser.add_argument('--ARANCELES'          , type=float, default=[0., 0., 0.003825, 0., 0., 0.], nargs='*', help="para el escenario 14")
    # hay que especificar estos números porque luego hay que redimensionar las matrices aplanadas

    parser.add_argument('--FF_ENDOGENA'        , type=sab  , default=True , help="Las aportaciones de factores por los hogares pueden ser variables endogenas o exogenas")
    # AHORRO_L_PLAZO solo tiene sentido si FF_ENDOGENA es True y entonces es necesario que sea True para evitar la retroalimentación de la demanda final
    # sea endógeno (VALOR_F_TRA=0)
    parser.add_argument('--AHORRO_L_PLAZO'     , type=sab  , default=False , help="llevar a la cuenta ALP (Ahorro Largo Plazo) los excesos de factores aportados sobre sus valores iniciales")
    '''
    cuando FF_ENDOGENA, hay que especificar
        OR_PRE_REFERENCIA   = 0
        PRECIO_F_REFERENCIA = 1.0
        VALOR_F_TRA         = 1.0 salvo que el precio del trabajo se quiera como endógeno en cuyo caso VALOR_F_TRA = 0

    si (OR_PRE_REFERENCIA=0) el precio del capital (PRECIO_F_REFERENCIA) es exogeno = 1.0 y no formará parte del vector solución
    parser.add_argument('--OR_PRE_REFERENCIA'  , type=int  , default=0, help="factor de referencia = ordinal (columna de h, empezando en 0) del precio para el que se fija el valor 'PRECIO_F_REFERENCIA'")
    parser.add_argument('--PRECIO_F_REFERENCIA', type=float, default=1.0   , help="precio que se fija para el factor de referencia")
    
    si OR_PRE_REFERENCIA = 0 el precio del trabajo formará parte del vector solución, puede ser:
        endogeno : si VALOR_F_TRA = -1
        fijo     : será acotado al valor VALOR_F_TRA si es > 0
        calculado: si VALOR_F_TRA = 0
    '''
    parser.add_argument('--OR_PRE_REFERENCIA'  , type=int  , default=0, help="factor de referencia = ordinal (columna de h, empezando en 0) del precio para el que se fija el valor 'PRECIO_F_REFERENCIA'")
    parser.add_argument('--PRECIO_F_REFERENCIA', type=float, default=1.0   , help="precio que se fija para el factor de referencia")
    parser.add_argument('--VALOR_F_TRA'        , type=float, default=0     , help="precio que se fija para el factor trabajo; -1 : no se fija valor, 0 : curva Phillips")
    parser.add_argument('--PARO_INICIAL'       , type=float, default=0.10  , help="tanto por uno de paro para la curva Phillips")
    parser.add_argument('--ALFA_PHILLIPS'      , type=float, default=-0.5  , help="relación desempleo salarios, en la bibliografía se encuentra -0.4566") 
    '''
    parser.add_argument('--GE_FIX'             , type=str  , default=['epsilon','M'], nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--GE_FIX_LON'         , type=int  , default=[1, 6], nargs='*', help="número de parejas para cada variable en GE_FIX")
    parser.add_argument('--GE_FIX_LIMITES'     , type=str, default=[1.0, 1.0, '*', '*', '*', '*', 'M0', 'M0', '*', '*', '*', '*', '*', '*'] , nargs='*', help="una pareja para cada indice de la variable; '*' = criterio general, cualquier 'str' el valor inicial")
    '''
    #parser.add_argument('--GE_FIX'             , type=str  , default=['epsilon'], nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--GE_FIX_LON'         , type=int  , default=[1], nargs='*', help="número de parejas para cada variable en GE_FIX")
    parser.add_argument('--GE_FIX_LIMITES'     , type=str  , default=[1.0, 1.0] , nargs='*', help="una pareja para cada indice de la variable; '*' = criterio general, cualquier 'str' el valor inicial")

    parser.add_argument('--GE_FIX'             , type=str  , default=[], nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    
    parser.add_argument('--NSAM'               , type=int  , default=3    , help="Matriz de Contabilidad Social a utilizar, ver 'etq_sam'")
    parser.add_argument('--PRECIO_INI'         , type=float, default=0.5,  help="para el caso 5 'pre_ini'")
    parser.add_argument('--FACTOR_CSSH'        , type=float, default=[0.95, 1.0], nargs='*', help="para afectar los coeficientes de la seguridad social de los hohares, caso 8")
    parser.add_argument('--FACTOR_CSSE'        , type=float, default=[1.0 , 1.0, 1.0, 1.0, 1.0, 1.0], nargs='*', help="para afectar los coeficientes de la seguridad social de las empresas, caso 8")

    '''
    factores aportados adicionales para el caso 6, si se especifica un solo valor (escalar) se afectan todos por él
    '''
    parser.add_argument('--VAR_FACTORES'       , type=float, default=[0., 0., 0., 0.], nargs='*', help="factores aportados adicionales para el caso 6. Hogar 1")
    '''
    para el caso 11, participación del valor añadido sobre la producción de cada sector para calcular 
    la variación adicional exógena de factores, derivada del incremento de la demanda 'DEM_ADICIONAL'
    su forma varia con la SAM correspondiente, en función del número de sectores.
    '''
    parser.add_argument('--COE_VAB'            , type=float, default=[0.590982516,0.256023902,0.231881481,0.299890544,0.567089808,0.669947953], nargs='*', help="para el caso 11, participación del valor añadido sobre la producción de cada sector")
    parser.add_argument('--SIGMA_ESCENARIO'    , type=float, default=[4.,2.,2.,2.,2.,2.], nargs='*', help="valor de sigma para el escenario 13")

    parser.add_argument('--OPT_DESVIOS'        , type=int  , default=0     , help="0: incluye desvíos redundantes, puede mejorar los resultados")
    parser.add_argument('--PRIMERA_VALORACION' , type=sab  , default=False , help="calcular una primera valoración de modelo")
    parser.add_argument('--SAL_CALIBRADO'      , type=sab  , default=False , help="imprimir los valores de los parámetros calibrados")
    parser.add_argument('--SALIDA_VEC_OPT'     , type=sab  , default=False , help="salida de los valores iniciales de las variables y sus límites")
    parser.add_argument('--SALIDA_DESVIOS'     , type=sab  , default=True  , help="salida con el detalla de las desviaciones")
    parser.add_argument('--SAL_AUXILIARES'     , type=sab  , default=False , help="imprimir los valores del historial y la evolución de la solución")
    parser.add_argument('--SAL_GRAFICOS_EVOL'  , type=sab  , default=False , help="generar gráficos de las evoluciones")
    parser.add_argument('--SAL_GRAFICO_CES_DM' , type=sab  , default=False , help="generar graficos de isocuantas CES")
    parser.add_argument('--SAL_ISOCUANTA'      , type=sab  , default=False , help="generar gráficos adicionales de isocuantas")
    parser.add_argument('--SAL_VARIACIONES'    , type=sab  , default=True  , help="imprime las diferencias entre los valores iniciales y finales de las variables")
    parser.add_argument('--DECIMALES'          , type=int  , default=1     , help="número de decimales en las cantidades e importes")
    parser.add_argument('--GE_RESTRICCIONES'   , type=sab  , default=False , help="restricciones en cantidad de importación (M) y exportación (E)")
    parser.add_argument('--GE_TIPO_RE'         , type=int  , default=0     , help="0: lineal; 1: No lineal")
    parser.add_argument('--GE_TOLERANCIA'      , type=float, default=1.e-11, help="límite para considerar el objetivo alcanzado")
    parser.add_argument('--GE_VERIFICAR'       , type=float, default=1.e-08, help="límite para considerar que la ecuación se cumple")
    parser.add_argument('--GE_HISTORIAL'       , type=int  , default=1000  , help="número de iteraciones para salvar el historial")
    parser.add_argument('--GE_SOLUCIONES'      , type=int  , default=500   , help="número de iteraciones para salvar la solución")
    parser.add_argument('--GE_PRE_MIN'         , type=float, default=3.0   , help="precio que se fija para el factor de referencia")
    parser.add_argument('--GE_PRE_MAX'         , type=float, default=3.0   , help="precio que se fija para el factor de referencia")
    parser.add_argument('--GE_VAR_MIN'         , type=float, default=9.0   , help="precio que se fija para el factor de referencia")
    parser.add_argument('--GE_VAR_MAX'         , type=float, default=9.0   , help="precio que se fija para el factor de referencia")
    parser.add_argument('--GE_VAR_CERO'        , type=float, default=10000.0, help="precio que se fija para el factor de referencia")
    parser.add_argument('--GE_MAX_ITER'        , type=int  , default=1000000, help="máximo número de generaciones a simular")
    parser.add_argument('--GE_ACTUALIZACION'   , type=str  , default='immediate', help="cada vez que se cambia un individuo")
    parser.add_argument('--GE_RECONBINACION'   , type=float, default=0.90  , help="recombinación")
    parser.add_argument('--GE_DIM_POBLACION'   , type=int  , default=5     , help="factor para establecer el tamaño de la población (por defecto es 15)")
    parser.add_argument('--GE_WORKERS'         , type=int  , default=32    , help="número de procesadores a utilizar (en esta máquina el máximo es 61 y el óptimo 32)")
    '''
    42, 333, 1755, 1234, 7000, 933, 2255, 1515, 29
    '''
    parser.add_argument('--GE_SEMILLA'         , type=int  , default=333   , help="valor inicial del generador de números aleatorios")
    parser.add_argument('--GE_IMG_FIL'         , type=int  , default=5     , help="número de filas del mapa de gráficos con la evolución de los precios y las variables")
    parser.add_argument('--GE_IMG_COL'         , type=int  , default=6     , help="número de columnas del mapa de gráficos con la evolución de los precios y las variables")
    '''
    Se genera un candidato a solución mediante los siguientes tres pasos:
    1. Mutación:
        A partir de una generación se pasa a la siguiente creando una nueva población de individuos mutantes:
            el método 'best1bin' genera un individuo mutante de la forma:
                mutante = mejor individuo + (factor de mutación * (individuo[rand1] – individuo[rand2]))
                el uso del 'mejor individuo' es lo que determina la denominación 'best' en 'best1bin'
                la inclusión del '1' en la denominación de método 'best1bin' hace referencia a que sólo hay una resta
            como se puede ver el individuo mutante en la posición 'n' de la población es totalmente independiente del individuo original en esa
            misma posición, la relación con el individuo original se produce en la recombinación.
    2. Recombinación:
        A continuación se procede a la recombinación (crossover) de los individuos mutantes con los de la población original.
        Se construye un vector de prueba rellenándolo secuencialmente con parámetros de 'mutante' o del individuo original.
        La decisión de usar 'mutante' o el individuo original se toma mediante una distribución binomial (el término 'bin' en 'best1bin'):
        se genera un número aleatorio en [0, 1). Si este número es menor que la constante de recombinación, el parámetro se
        carga desde 'mutante', de lo contrario, se carga desde el candidato original. Se exige que siempre se cargue como mínimo un
        parámetro, seleccionado aleatoriamente, desde 'mutante', para evitar que la nueva solución a probar sea una copia exacta de la original.
    3. Selección:
        Una vez construido el candidato a solución, se evalúa su mérito (aptitud). Si el candidato a solución es
        mejor que el individuo original, lo reemplaza. Si es también mejor que el mejor individuo en general pasa a ser el mejor.
    '''
    parser.add_argument('--GE_ESTRATEGIA'      , type=str  , default='best1bin', help="estrategia")
    '''
    el resultado de la función a minimizar lo determina la METRICA_ERROR y es:
        0: la suma del cuadrado de los desvios de cada una de las variables
        1: la suma de los valores absolutos de los desvios de cada una de las variables
        2: la suma de los desvios de cada una de las variables elevada a POT_DESVIOS, si el desvio es negatino se toma el valor absoluto
    '''
    parser.add_argument('--METRICA_ERROR'      , type=int  , default=0     , help="métrica del error: 0=cuadrado; 1=absoluto; 2=elevado a POT")
    parser.add_argument('--POT_DESVIOS'        , type=int  , default=2     , help="solo se usa en el caso de METRICA_ERROR = 2")
    parser.add_argument('--SENDA_DATOS'        , type=str  , default='C:/MEGA/Datos'   , help="debe existir")
    parser.add_argument('--SENDA_SALIDAS'      , type=str  , default='C:/MEGA/Salidas' , help="senda para las salidas")
    parser.add_argument('--SENDA_GRAFICOS'     , type=str  , default='C:/MEGA/Graficos', help="senda para los gráficos")
    args = parser.parse_args()
    return args
