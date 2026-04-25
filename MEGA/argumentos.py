import argparse

def sab(v):
    if v.lower() in ('yes', 'true', 't', 'y', 'si', 's'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n'):
        return False
    else:
        raise argparse.ArgumentTypeError('No es un valor boleano.')

def valores_opciones0():
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
        'dem_alfa',             #  9 simplemente cambia la preferencia de los consumos, no se añade demanda porque duplicaría el efecto en los productos
        # usar el caso 0 para ayudas no es equivalente al caso 12 porque las ayudas no irán destinadas de forma diferenciada a los productos, para esto hay que modificar los alfa  
        'alfa_ayudas',          # 10
        'sigma',                # 11
        'aranceles',            # 12
        'Xp0',                  # 13 consumos esenciales = Xp0
        'Xp0m1',                # 14 consumos esenciales = Xp0 - 1
    '''
    # si PREFIJO empieza con el caracter '=' los caracteres del 1 en adelante se usarán como nombre de los ficheros de salida en
    # lugar de componerlos a partir de las opciones seleccionadas, en este caso NO puede haber ESPACIOS en blanco intercalados

    parser.add_argument('--USAR_DLL'           , type=sab  , default=False , help="si True se usa la DLL en caso contrario la función Python")
    parser.add_argument('--USAR_ALGE_DLL'      , type=sab  , default=False, help="si True se usa la DLL para el algoritmo genético")
    parser.add_argument('--ALGE_MAX_INTENTOS'  , type=int  , default=5 , help="")
    parser.add_argument('--ALGE_N_HILOS'       , type=int  , default=16 , help="")
    parser.add_argument('--ALGE_TOL_ACEPTABLE' , type=float, default=1.0e-05 , help="")
    parser.add_argument('--ALGE_MODO_POB_INI'  , type=int  , default=0 , help="")
    parser.add_argument('--ALGE_F_INICIO_POB'  , type=float, default=0.05 , help="")
    parser.add_argument('--ALGE_SIGMA_POB_INI' , type=float, default=0.1 , help="")
    parser.add_argument('--ALGE_TRAMOS_LHS'    , type=int  , default=100 , help="")
    parser.add_argument('--ALGE_NPOB'          , type=int  , default=1200 , help="")
    parser.add_argument('--ALGE_F_MUTACION'    , type=float, default=0.72 , help="")
    parser.add_argument('--ALGE_RECOMBINACION' , type=float, default=[0.99, 1.10], nargs='*', help="")
    parser.add_argument('--ALGE_CTRL_FACTIBLE' , type=int  , default=1 , help="")
    parser.add_argument('--ALGE_RES_EXTENSA'   , type=int  , default=0 , help="")
    parser.add_argument('--NSAM'               , type=int  , default=0    , help="Matriz de Contabilidad Social a utilizar, ver 'etq_sam'")
    parser.add_argument('--DECIMALES'          , type=int  , default=2    , help="número de decimales en las cantidades e importes")
    # hay que especificar estos números porque luego hay que redimensionar las matrices aplanadas
    parser.add_argument('--NFAC'               , type=int  , default=2    , help="número de factores")
    parser.add_argument('--NDEM'               , type=int  , default=1    , help="número de hogares")
    parser.add_argument('--NSEC'               , type=int  , default=2    , help="número de sectores")
    parser.add_argument('--PREFIJO'            , type=str  , default='=Mcs0' , help="un literal que se añade al principio del nombre de los archivos de salida")
    '''
    42, 333, 1755, 1234, 7000, 933, 2255, 1515, 29
    '''
    parser.add_argument('--GE_SEMILLA'         , type=int  , default=42   , help="valor inicial del generador de números aleatorios")
    parser.add_argument('--NCASO'              , type=int  , default=[0], nargs='*', help="número de esenario a utilizar, se pueden combinar varios, por ejemplo default=[0,14], atención al orden")

    #-----------------------------------------------------
    # las matrices se especifican aplanadas como vectores.
    #-----------------------------------------------------
    
    # Para ver los efectos de la demanda adicional lo apropiado es usar NCASO = 0
    parser.add_argument('--DEM_ADICIONAL_TIPO' , type=int  , default=0    , help="0: se añade 'DEM_ADICIONAL' al importe demandado; 1: se añade 'DEM_ADICIONAL' a la cantidad demandada")
    parser.add_argument('--DEM_ADICIONAL'      , type=float, default=[0., 0.], nargs='*', help="demanda adicional exógena de productos para los hogares")
    parser.add_argument('--RENTA_FICTICIA'     , type=sab  , default=False , help="si True no se proveerán fondos para los incrementos de demanda")
    
    # Para ver los efectos de las ayudas lo apropiado es usar NCASO = 10
    parser.add_argument('--AYD_ADICIONAL'      , type=float, default=[0., 0.], nargs='*', help="ayuda adicional exógena por producto para el hogar 1")

    # 'CON_ESENCIALES' cantidades de consumos esenciales. Si DEM_ESENCIALES = False, simplemente se usan como el valor mínimo de las compras, sin usar la función de demanda Stone-Geary
    '''
    parser.add_argument('--CON_ESENCIALES'     , type=float, default=[np.round(8118.*0.7,0), np.round(15120.*0.65),np.round(87781.*0.80),np.round(3767.*0.75),np.round(307653.*0.90),np.round(1878.*0.5),np.round(1111.*0.9),np.round(2069.*0.9),np.round(12012.*0.9),np.round(516.*0.9),np.round(42096.*0.9),np.round(257.*0.9)], nargs='*', help="consumos esenciales para los hogares")
    parser.add_argument('--CON_ESENCIALES'     , type=float, default=[5683., 9828., 70225., 2825., 276888., 939., 1000., 1862., 10811., 464, 37886, 231.], nargs='*', help="consumos esenciales para los hogares")
    '''
    parser.add_argument('--CON_ESENCIALES'     , type=float, default=[0., 0.], nargs='*', help="consumos esenciales para los hogares")
    parser.add_argument('--DEM_ESENCIALES'     , type=sab, default=False, help="True: usar los 'CON_ESENCIALES' en el cálculo de productos demandados (Stone-Geary)")

    parser.add_argument('--ARANCELES'          , type=float, default=[0., 0.], nargs='*', help="para el escenario 12")

    parser.add_argument('--FF_ENDOGENA'        , type=sab  , default=True , help="Las aportaciones de factores por los hogares pueden ser variables endogenas o exogenas")
    parser.add_argument('--ALP_FACTOR'         , type=float, default=0.5  , help="tanto por uno de los excesos de factores aportados, sobre sus valores iniciales, que se lleva a la cuenta Alp") 
    '''
    cuando FF_ENDOGENA, hay que especificar
        OR_PRE_EXCLUIDO   = 0
        PRECIO_F_EXCLUIDO = 1.0
        VALOR_F_TRA         = 1.0 salvo que el precio del trabajo se quiera como endógeno en cuyo caso VALOR_F_TRA = 0

    si (OR_PRE_EXCLUIDO=0) el precio del capital (PRECIO_F_EXCLUIDO) es exogeno = 1.0 y no formará parte del vector solución
    parser.add_argument('--OR_PRE_EXCLUIDO'  , type=int  , default=0, help="factor de referencia = ordinal (columna de h, empezando en 0) del precio para el que se fija el valor 'PRECIO_F_EXCLUIDO'")
    parser.add_argument('--PRECIO_F_EXCLUIDO', type=float, default=1.0   , help="precio que se fija para el factor de referencia")
    
    si OR_PRE_EXCLUIDO = 0 el precio del trabajo formará parte del vector solución, puede ser:
        endogeno : si VALOR_F_TRA = -1
        fijo     : será acotado al valor VALOR_F_TRA si es > 0
        calculado: si VALOR_F_TRA = 0
    '''
    parser.add_argument('--OR_PRE_EXCLUIDO'  , type=int  , default=0, help="factor de referencia = ordinal (columna de h, empezando en 0) del precio para el que se fija el valor 'PRECIO_F_EXCLUIDO'")
    parser.add_argument('--PRECIO_F_EXCLUIDO', type=float, default=1.0   , help="precio que se fija para el factor de referencia")
    parser.add_argument('--VALOR_F_TRA'        , type=float, default=1.05   , help="precio que se fija para el factor trabajo; -1 : no se fija valor, 0 : curva Phillips")
    parser.add_argument('--PARO_INICIAL'       , type=float, default=0.10  , help="tanto por uno de paro para la curva Phillips")
    parser.add_argument('--ALFA_PHILLIPS'      , type=float, default=-0.5  , help="relación desempleo salarios, en la bibliografía se encuentra -0.4566") 
    '''
    parser.add_argument('--GE_FIX'             , type=str  , default=[] , nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--GE_FIX_LON'         , type=int  , default=[0], nargs='*', help="número de parejas para cada variable en GE_FIX")
    parser.add_argument('--GE_FIX_LIMITES'     , type=str, default=[]   , nargs='*', help="una pareja para cada índice de la variable") 

    parser.add_argument('--GE_FIX'             , type=str  , default=['epsilon'], nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--GE_FIX_LON'         , type=int  , default=[1], nargs='*', help="número de parejas para cada variable en GE_FIX")
    parser.add_argument('--GE_FIX_LIMITES'     , type=str  , default=[1.0, 1.0] , nargs='*', help="una pareja para cada índice de la variable; '*' = criterio general, cualquier 'str' el valor inicial")

    parser.add_argument('--GE_FIX'             , type=str  , default=['M'], nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--GE_FIX_LON'         , type=int  , default=[6], nargs='*', help="número de parejas para cada variable en GE_FIX")
    parser.add_argument('--GE_FIX_LIMITES'     , type=str, default=['*', '*', '*', '*', 'M0', 'M0', '*', '*', '*', '*', '*', '*'] , nargs='*', help="una pareja para cada índice de la variable; '*' = criterio general, cualquier 'str' el valor inicial")

    parser.add_argument('--GE_FIX'             , type=str  , default=['epsilon','M'], nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--GE_FIX_LON'         , type=int  , default=[1, 6], nargs='*', help="número de parejas para cada variable en GE_FIX")
    parser.add_argument('--GE_FIX_LIMITES'     , type=str, default=[1.0, 1.0, '*', '*', '*', '*', 'M0', 'M0', '*', '*', '*', '*', '*', '*'] , nargs='*', help="una pareja para cada índice de la variable; '*' = criterio general, cualquier 'str' el valor inicial")
    '''
    parser.add_argument('--GE_FIX'             , type=str  , default=['epsilon'], nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--GE_FIX_LON'         , type=int  , default=[1], nargs='*', help="número de parejas para cada variable en GE_FIX")
    parser.add_argument('--GE_FIX_LIMITES'     , type=str  , default=[1.0, 1.0] , nargs='*', help="una pareja para cada índice de la variable; '*' = criterio general, cualquier 'str' el valor inicial")

    parser.add_argument('--UTILIDAD_DEMANDA'   , type=int  , default=0     , help="0: Cobb Douglas; 1: CES")
    parser.add_argument('--SIGMA_CES_DEMANDA'  , type=float, default=[2.], nargs='*', help="sigma de la función de demanda CES")
    parser.add_argument('--MODO_PSEUDOIMPTOS'  , type=int  , default=0     , help="0: variables según cambian las cotizaciones a la seguridad social y las ayudas del gobierno; 1: fijos iguales a los que resultam de la MCS")

    parser.add_argument('--SAL_CALIBRADO'      , type=sab  , default=False , help="imprimir los valores de los parámetros calibrados")
    parser.add_argument('--SALIDA_VEC_OPT'     , type=sab  , default=True , help="salida de los valores iniciales de las variables y sus límites")
    parser.add_argument('--SALIDA_VAL_INI'     , type=sab  , default=False , help="informe de los valores iniciales de las variables")
    parser.add_argument('--PRIMERA_VALORACION' , type=sab  , default=False , help="calcular una primera valoración de modelo")
    parser.add_argument('--SALIDA_DESVIOS'     , type=sab  , default=False , help="salida con el detalla de las desviaciones")
    parser.add_argument('--SAL_AUXILIARES'     , type=sab  , default=False , help="imprimir los valores del historial y la evolución de la solución")
    parser.add_argument('--SAL_GRAFICOS_EVOL'  , type=sab  , default=False , help="generar gráficos de las evoluciones")
    parser.add_argument('--SAL_GRAFICO_CES_DM' , type=sab  , default=False , help="generar graficos de isocuantas CES")
    parser.add_argument('--SAL_ISOCUANTA'      , type=sab  , default=False , help="generar gráficos adicionales de isocuantas")
    parser.add_argument('--SAL_VARIACIONES'    , type=sab  , default=False , help="imprime las diferencias entre los valores iniciales y finales de las variables")
    parser.add_argument('--SAL_MCS'            , type=sab  , default=True  , help="imprime la MCS")
    parser.add_argument('--SAL_VAR_MCS'        , type=sab  , default=False , help="imprime las diferencias entre los valores iniciales y finales de la MCS")

    parser.add_argument('--GE_INCLUYE_XP'      , type=sab  , default=False , help="incluir Xp en el vector solución")
    parser.add_argument('--GE_RESTRICCIONES'   , type=sab  , default=False , help="restricciones en cantidad de importación (M) y exportación (E)")
    parser.add_argument('--GE_TIPO_RE'         , type=int  , default=1     , help="0: lineal; 1: No lineal")
    parser.add_argument('--GE_TOLERANCIA'      , type=float, default=1.e-11, help="límite para considerar el objetivo alcanzado o que no hay progreso")
    parser.add_argument('--GE_VERIFICAR'       , type=float, default=1.e-08, help="límite para considerar que la ecuación se cumple")
    # GE_PROGRESO tiene su importancia porque la minimización puede terminar si tras GE_PROGRESO generaciones no mejora al menos GE_TOLERANCIA
    # Si GE_PROGRESO es demasiado pequeño, la minimización puede terminar incorrectamente porque no ha tenido tiempo de progresar
    parser.add_argument('--GE_PROGRESO'        , type=int  , default=100   , help="número de generaciones para comprobar el progreso")
    parser.add_argument('--GE_HISTORIAL'       , type=int  , default=100   , help="número de generaciones para salvar el historial")
    parser.add_argument('--GE_SOLUCIONES'      , type=int  , default=100   , help="número de generaciones para salvar la solución")
    '''
    parser.add_argument('--GE_PRE_MIN'         , type=float, default=2.0   , help="el límite inferior del rango de variación de los precios es su valor inicial dividido por GE_PRE_MIN")
    parser.add_argument('--GE_PRE_MAX'         , type=float, default=2.0   , help="el límite superior del rango de variación de los precios es su valor inicial multiplicado por GE_PRE_MAX")
    parser.add_argument('--GE_VAR_MIN'         , type=float, default=4.0   , help="el límite inferior del rango de variación de las variables es su valor inicial dividido por GE_VAR_MIN")
    parser.add_argument('--GE_VAR_MAX'         , type=float, default=4.0   , help="el límite superior del rango de variación de las variables es su valor inicial multiplicado por GE_VAR_MAX")
    '''
    parser.add_argument('--GE_PRE_MIN'         , type=float, default=40.0  , help="el límite inferior del rango de variación de los precios es su valor inicial dividido por GE_PRE_MIN")
    parser.add_argument('--GE_PRE_MAX'         , type=float, default=40.0  , help="el límite superior del rango de variación de los precios es su valor inicial multiplicado por GE_PRE_MAX")
    parser.add_argument('--GE_VAR_MIN'         , type=float, default=50.0  , help="el límite inferior del rango de variación de las variables es su valor inicial dividido por GE_VAR_MIN")
    parser.add_argument('--GE_VAR_MAX'         , type=float, default=50.0  , help="el límite superior del rango de variación de las variables es su valor inicial multiplicado por GE_VAR_MAX")
    parser.add_argument('--GE_VAR_CERO'        , type=float, default=10000.0,help="si el valor inicial de una variable es cero su rango de variación es [-GE_VAR_CERO, +GE_VAR_CERO]")
    parser.add_argument('--GE_VAR_CAN_MIN'     , type=float, default=10000.0,help="rango de variación mínimo para una variable")
    parser.add_argument('--GE_ACTUALIZACION'   , type=str  , default='immediate', help="cada vez que se cambia un individuo")
    parser.add_argument('--GE_RECONBINACION'   , type=float, default=0.90  , help="recombinación")
    parser.add_argument('--GE_DIM_POBLACION'   , type=int  , default=5     , help="factor para establecer el tamaño de la población (por defecto es 15)")
    parser.add_argument('--GE_WORKERS'         , type=int  , default=32    , help="número de procesadores a utilizar (en esta máquina el máximo es 61 y el óptimo 32)")
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
    parser.add_argument('--OPT_DESVIOS'        , type=int  , default=1     , help="0: incluye desvíos redundantes, puede mejorar los resultados")
    '''
    el resultado de la función a minimizar lo determina la METRICA_ERROR y es:
        0: la suma del cuadrado de los desvios de cada una de las variables
        1: la suma de los valores absolutos de los desvios de cada una de las variables
        2: la suma de los desvios de cada una de las variables elevada a POT_DESVIOS, si el desvio es negatino se toma el valor absoluto
    '''
    parser.add_argument('--METRICA_ERROR'      , type=int  , default=0     , help="métrica del error: 0=cuadrado; 1=absoluto; 2=elevado a POT")
    parser.add_argument('--POT_DESVIOS'        , type=int  , default=2     , help="solo se usa en el caso de METRICA_ERROR = 2")
    parser.add_argument('--PRECIO_INI'         , type=float, default=0.5   , help="para el caso 5 'pre_ini'")
    parser.add_argument('--FACTOR_CSSH'        , type=float, default=[1.0] , nargs='*', help="para afectar los coeficientes de la seguridad social de los hohares, caso 8")
    parser.add_argument('--FACTOR_CSSE'        , type=float, default=[1.0, 1.0], nargs='*', help="para afectar los coeficientes de la seguridad social de las empresas, caso 8")
    '''
    factores aportados adicionales para el caso 6, si se especifica un solo valor (escalar) se afectan todos por él
    '''
    parser.add_argument('--VAR_FACTORES'       , type=float, default=[0., 0.], nargs='*', help="factores aportados adicionales para el caso 6.")
    parser.add_argument('--SIGMA_ESCENARIO'    , type=float, default=[2., 2.], nargs='*', help="valor de sigma para el escenario 13")

    parser.add_argument('--SENDA_DATOS'        , type=str  , default='C:/MEGA/Datos'   , help="debe existir")
    parser.add_argument('--SENDA_SALIDAS'      , type=str  , default='C:/MEGA/Salidas' , help="senda para las salidas")
    parser.add_argument('--SENDA_GRAFICOS'     , type=str  , default='C:/MEGA/Graficos', help="senda para los gráficos")
    parser.add_argument('--SENDA_DLL'          , type=str  , default='C:/MEGA/Mega_DLL/x64/Debug/MEGA_DLL.dll', help="senda para la DLL")
    args = parser.parse_args()
    return args

def valores_opciones1():
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
        'dem_alfa',             #  9 simplemente cambia la preferencia de los consumos, no se añade demanda porque duplicaría el efecto en los productos
        # usar el caso 0 para ayudas no es equivalente al caso 12 porque las ayudas no irán destinadas de forma diferenciada a los productos, para esto hay que modificar los alfa  
        'alfa_ayudas',          # 10
        'sigma',                # 11
        'aranceles',            # 12
        'Xp0',                  # 13 consumos esenciales = Xp0
        'Xp0m1',                # 14 consumos esenciales = Xp0 - 1
    '''
    # si PREFIJO empieza con el caracter '=' los caracteres del 1 en adelante se usarán como nombre de los ficheros de salida en
    # lugar de componerlos a partir de las opciones seleccionadas, en este caso NO puede haber ESPACIOS en blanco intercalados

    parser.add_argument('--USAR_DLL'           , type=sab   , default=False, help="si True se usa la DLL en caso contrario la función Python")
    parser.add_argument('--USAR_ALGE_DLL'      , type=sab   , default=False, help="si True se usa la DLL para el algoritmo genético")
    parser.add_argument('--ALGE_MAX_INTENTOS'  , type=int   , default=5 , help="")
    parser.add_argument('--ALGE_N_HILOS'       , type=int   , default=16 , help="")
    parser.add_argument('--ALGE_TOL_ACEPTABLE' , type=float , default=1.0e-05 , help="")
    parser.add_argument('--ALGE_MODO_POB_INI'  , type=int   , default=0 , help="")
    parser.add_argument('--ALGE_F_INICIO_POB'  , type=float , default=0.05 , help="")
    parser.add_argument('--ALGE_SIGMA_POB_INI' , type=float , default=0.1 , help="")
    parser.add_argument('--ALGE_TRAMOS_LHS'    , type=int   , default=100 , help="")
    parser.add_argument('--ALGE_NPOB'          , type=int   , default=1200 , help="")
    parser.add_argument('--ALGE_F_MUTACION'    , type=float , default=0.72 , help="")
    parser.add_argument('--ALGE_RECOMBINACION' , type=float , default=[0.99, 1.10], nargs='*', help="")
    parser.add_argument('--ALGE_CTRL_FACTIBLE' , type=int   , default=1 , help="")
    parser.add_argument('--ALGE_RES_EXTENSA'   , type=int   , default=0 , help="")
    parser.add_argument('--NSAM'               , type=int  , default=1    , help="Matriz de Contabilidad Social a utilizar, ver 'etq_sam'")
    parser.add_argument('--DECIMALES'          , type=int  , default=4    , help="número de decimales en las cantidades e importes")
    # hay que especificar estos números porque luego hay que redimensionar las matrices aplanadas
    parser.add_argument('--NFAC'               , type=int  , default=2    , help="número de factores")
    parser.add_argument('--NDEM'               , type=int  , default=2    , help="número de hogares")
    parser.add_argument('--NSEC'               , type=int  , default=2    , help="número de sectores")
    parser.add_argument('--PREFIJO'            , type=str  , default='=Mcs1' , help="un literal que se añade al principio del nombre de los archivos de salida")
    '''
    42, 333, 1755, 1234, 7000, 933, 2255, 1515, 29
    '''
    parser.add_argument('--GE_SEMILLA'         , type=int  , default=42   , help="valor inicial del generador de números aleatorios")
    parser.add_argument('--NCASO'              , type=int  , default=[0], nargs='*', help="número de esenario a utilizar, se pueden combinar varios, por ejemplo default=[0,14], atención al orden")

    #-----------------------------------------------------
    # las matrices se especifican aplanadas como vectores.
    #-----------------------------------------------------
    
    # Para ver los efectos de la demanda adicional lo apropiado es usar NCASO = 0
    parser.add_argument('--DEM_ADICIONAL_TIPO' , type=int  , default=0    , help="0: se añade 'DEM_ADICIONAL' al importe demandado; 1: se añade 'DEM_ADICIONAL' a la cantidad demandada")
    parser.add_argument('--DEM_ADICIONAL'      , type=float, default=[0., 0., 0., 0.], nargs='*', help="demanda adicional exógena de productos para los hogares")
    parser.add_argument('--RENTA_FICTICIA'     , type=sab  , default=False , help="si True no se proveerán fondos para los incrementos de demanda")
    
    # Para ver los efectos de las ayudas lo apropiado es usar NCASO = 10
    parser.add_argument('--AYD_ADICIONAL'      , type=float, default=[0., 0., 0., 0.], nargs='*', help="ayuda adicional exógena por producto para el hogar 1")

    # 'CON_ESENCIALES' cantidades de consumos esenciales. Si DEM_ESENCIALES = False, simplemente se usan como el valor mínimo de las compras, sin usar la función de demanda Stone-Geary
    '''
    parser.add_argument('--CON_ESENCIALES'     , type=float, default=[np.round(8118.*0.7,0), np.round(15120.*0.65),np.round(87781.*0.80),np.round(3767.*0.75),np.round(307653.*0.90),np.round(1878.*0.5),np.round(1111.*0.9),np.round(2069.*0.9),np.round(12012.*0.9),np.round(516.*0.9),np.round(42096.*0.9),np.round(257.*0.9)], nargs='*', help="consumos esenciales para los hogares")
    parser.add_argument('--CON_ESENCIALES'     , type=float, default=[5683., 9828., 70225., 2825., 276888., 939., 1000., 1862., 10811., 464, 37886, 231.], nargs='*', help="consumos esenciales para los hogares")
    '''
    parser.add_argument('--CON_ESENCIALES'     , type=float, default=[0., 0., 0., 0.], nargs='*', help="consumos esenciales para los hogares")
    parser.add_argument('--DEM_ESENCIALES'     , type=sab, default=False, help="True: usar los 'CON_ESENCIALES' en el cálculo de productos demandados (Stone-Geary)")

    parser.add_argument('--ARANCELES'          , type=float, default=[0., 0.], nargs='*', help="para el escenario 12")

    parser.add_argument('--FF_ENDOGENA'        , type=sab  , default=True , help="Las aportaciones de factores por los hogares pueden ser variables endogenas o exogenas")
    parser.add_argument('--ALP_FACTOR'         , type=float, default=1.0  , help="tanto por uno de los excesos de factores aportados, sobre sus valores iniciales, que se lleva a la cuenta Alp") 
    '''
    cuando FF_ENDOGENA, hay que especificar
        OR_PRE_EXCLUIDO   = 0
        PRECIO_F_EXCLUIDO = 1.0
        VALOR_F_TRA         = 1.0 salvo que el precio del trabajo se quiera como endógeno en cuyo caso VALOR_F_TRA = 0

    si (OR_PRE_EXCLUIDO=0) el precio del capital (PRECIO_F_EXCLUIDO) es exogeno = 1.0 y no formará parte del vector solución
    parser.add_argument('--OR_PRE_EXCLUIDO'  , type=int  , default=0, help="factor de referencia = ordinal (columna de h, empezando en 0) del precio para el que se fija el valor 'PRECIO_F_EXCLUIDO'")
    parser.add_argument('--PRECIO_F_EXCLUIDO', type=float, default=1.0   , help="precio que se fija para el factor de referencia")
    
    si OR_PRE_EXCLUIDO = 0 el precio del trabajo formará parte del vector solución, puede ser:
        endogeno : si VALOR_F_TRA = -1
        fijo     : será acotado al valor VALOR_F_TRA si es > 0
        calculado: si VALOR_F_TRA = 0
    '''
    parser.add_argument('--OR_PRE_EXCLUIDO'  , type=int  , default=0, help="factor de referencia = ordinal (columna de h, empezando en 0) del precio para el que se fija el valor 'PRECIO_F_EXCLUIDO'")
    parser.add_argument('--PRECIO_F_EXCLUIDO', type=float, default=1.0   , help="precio que se fija para el factor de referencia")
    parser.add_argument('--VALOR_F_TRA'        , type=float, default=1.25   , help="precio que se fija para el factor trabajo; -1 : no se fija valor, 0 : curva Phillips")
    parser.add_argument('--PARO_INICIAL'       , type=float, default=0.10  , help="tanto por uno de paro para la curva Phillips")
    parser.add_argument('--ALFA_PHILLIPS'      , type=float, default=-0.5  , help="relación desempleo salarios, en la bibliografía se encuentra -0.4566") 
    '''
    parser.add_argument('--GE_FIX'             , type=str  , default=[] , nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--GE_FIX_LON'         , type=int  , default=[0], nargs='*', help="número de parejas para cada variable en GE_FIX")
    parser.add_argument('--GE_FIX_LIMITES'     , type=str, default=[]   , nargs='*', help="una pareja para cada índice de la variable") 

    parser.add_argument('--GE_FIX'             , type=str  , default=['epsilon'], nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--GE_FIX_LON'         , type=int  , default=[1], nargs='*', help="número de parejas para cada variable en GE_FIX")
    parser.add_argument('--GE_FIX_LIMITES'     , type=str  , default=[1.0, 1.0] , nargs='*', help="una pareja para cada índice de la variable; '*' = criterio general, cualquier 'str' el valor inicial")

    parser.add_argument('--GE_FIX'             , type=str  , default=['M'], nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--GE_FIX_LON'         , type=int  , default=[6], nargs='*', help="número de parejas para cada variable en GE_FIX")
    parser.add_argument('--GE_FIX_LIMITES'     , type=str, default=['*', '*', '*', '*', 'M0', 'M0', '*', '*', '*', '*', '*', '*'] , nargs='*', help="una pareja para cada índice de la variable; '*' = criterio general, cualquier 'str' el valor inicial")

    parser.add_argument('--GE_FIX'             , type=str  , default=['epsilon','M'], nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--GE_FIX_LON'         , type=int  , default=[1, 6], nargs='*', help="número de parejas para cada variable en GE_FIX")
    parser.add_argument('--GE_FIX_LIMITES'     , type=str, default=[1.0, 1.0, '*', '*', '*', '*', 'M0', 'M0', '*', '*', '*', '*', '*', '*'] , nargs='*', help="una pareja para cada índice de la variable; '*' = criterio general, cualquier 'str' el valor inicial")
    '''
    parser.add_argument('--GE_FIX'             , type=str  , default=['epsilon'], nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--GE_FIX_LON'         , type=int  , default=[1], nargs='*', help="número de parejas para cada variable en GE_FIX")
    parser.add_argument('--GE_FIX_LIMITES'     , type=str  , default=[1.0, 1.0] , nargs='*', help="una pareja para cada índice de la variable; '*' = criterio general, cualquier 'str' el valor inicial")

    parser.add_argument('--UTILIDAD_DEMANDA'   , type=int  , default=0     , help="0: Cobb Douglas; 1: CES")
    parser.add_argument('--SIGMA_CES_DEMANDA'  , type=float, default=[2., 2.], nargs='*', help="sigma de la función de demanda CES")
    parser.add_argument('--MODO_PSEUDOIMPTOS'  , type=int  , default=0     , help="0: variables según cambian las cotizaciones a la seguridad social y las ayudas del gobierno; 1: fijos iguales a los que resultam de la MCS")

    parser.add_argument('--SAL_CALIBRADO'      , type=sab  , default=False , help="imprimir los valores de los parámetros calibrados")
    parser.add_argument('--SALIDA_VEC_OPT'     , type=sab  , default=False , help="salida de los valores iniciales de las variables y sus límites")
    parser.add_argument('--SALIDA_VAL_INI'     , type=sab  , default=False , help="informe de los valores iniciales de las variables")
    parser.add_argument('--PRIMERA_VALORACION' , type=sab  , default=False , help="calcular una primera valoración de modelo")
    parser.add_argument('--SALIDA_DESVIOS'     , type=sab  , default=False , help="salida con el detalla de las desviaciones")
    parser.add_argument('--SAL_AUXILIARES'     , type=sab  , default=False , help="imprimir los valores del historial y la evolución de la solución")
    parser.add_argument('--SAL_GRAFICOS_EVOL'  , type=sab  , default=False , help="generar gráficos de las evoluciones")
    parser.add_argument('--SAL_GRAFICO_CES_DM' , type=sab  , default=False , help="generar graficos de isocuantas CES")
    parser.add_argument('--SAL_ISOCUANTA'      , type=sab  , default=False , help="generar gráficos adicionales de isocuantas")
    parser.add_argument('--SAL_VARIACIONES'    , type=sab  , default=False , help="imprime las diferencias entre los valores iniciales y finales de las variables")
    parser.add_argument('--SAL_MCS'            , type=sab  , default=True  , help="imprime la MCS")
    parser.add_argument('--SAL_VAR_MCS'        , type=sab  , default=False , help="imprime las diferencias entre los valores iniciales y finales de la MCS")

    parser.add_argument('--GE_INCLUYE_XP'      , type=sab  , default=False , help="incluir Xp en el vector solución")
    parser.add_argument('--GE_RESTRICCIONES'   , type=sab  , default=False , help="restricciones en cantidad de importación (M) y exportación (E)")
    parser.add_argument('--GE_TIPO_RE'         , type=int  , default=1     , help="0: lineal; 1: No lineal")
    parser.add_argument('--GE_TOLERANCIA'      , type=float, default=1.e-11, help="límite para considerar el objetivo alcanzado o que no hay progreso")
    parser.add_argument('--GE_VERIFICAR'       , type=float, default=1.e-08, help="límite para considerar que la ecuación se cumple")
    # GE_PROGRESO tiene su importancia porque la minimización puede terminar si tras GE_PROGRESO generaciones no mejora al menos GE_TOLERANCIA
    # Si GE_PROGRESO es demasiado pequeño, la minimización puede terminar incorrectamente porque no ha tenido tiempo de progresar
    parser.add_argument('--GE_PROGRESO'        , type=int  , default=100   , help="número de generaciones para comprobar el progreso")
    parser.add_argument('--GE_HISTORIAL'       , type=int  , default=100   , help="número de generaciones para salvar el historial")
    parser.add_argument('--GE_SOLUCIONES'      , type=int  , default=100   , help="número de generaciones para salvar la solución")
    '''
    parser.add_argument('--GE_PRE_MIN'         , type=float, default=3.0   , help="el límite inferior del rango de variación de los precios es su valor inicial dividido por GE_PRE_MIN")
    parser.add_argument('--GE_PRE_MAX'         , type=float, default=3.0   , help="el límite superior del rango de variación de los precios es su valor inicial multiplicado por GE_PRE_MAX")
    parser.add_argument('--GE_VAR_MIN'         , type=float, default=9.0   , help="el límite inferior del rango de variación de las variables es su valor inicial dividido por GE_VAR_MIN")
    parser.add_argument('--GE_VAR_MAX'         , type=float, default=9.0   , help="el límite superior del rango de variación de las variables es su valor inicial multiplicado por GE_VAR_MAX")
    '''
    parser.add_argument('--GE_PRE_MIN'         , type=float, default=40.0  , help="el límite inferior del rango de variación de los precios es su valor inicial dividido por GE_PRE_MIN")
    parser.add_argument('--GE_PRE_MAX'         , type=float, default=40.0  , help="el límite superior del rango de variación de los precios es su valor inicial multiplicado por GE_PRE_MAX")
    parser.add_argument('--GE_VAR_MIN'         , type=float, default=50.0  , help="el límite inferior del rango de variación de las variables es su valor inicial dividido por GE_VAR_MIN")
    parser.add_argument('--GE_VAR_MAX'         , type=float, default=50.0  , help="el límite superior del rango de variación de las variables es su valor inicial multiplicado por GE_VAR_MAX")
    parser.add_argument('--GE_VAR_CERO'        , type=float, default=10000.0,help="si el valor inicial de una variable es cero su rango de variación es [-GE_VAR_CERO, +GE_VAR_CERO]")
    parser.add_argument('--GE_VAR_CAN_MIN'     , type=float, default=5000.0 ,help="rando de variación mínimo para una variable")
    parser.add_argument('--GE_MAX_ITER'        , type=int  , default=1000000,help="máximo número de generaciones a simular")
    parser.add_argument('--GE_ACTUALIZACION'   , type=str  , default='immediate', help="cada vez que se cambia un individuo")
    parser.add_argument('--GE_RECONBINACION'   , type=float, default=0.90  , help="recombinación")
    parser.add_argument('--GE_DIM_POBLACION'   , type=int  , default=5     , help="factor para establecer el tamaño de la población (por defecto es 15)")
    parser.add_argument('--GE_WORKERS'         , type=int  , default=32    , help="número de procesadores a utilizar (en esta máquina el máximo es 61 y el óptimo 32)")
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
    parser.add_argument('--OPT_DESVIOS'        , type=int  , default=1     , help="0: incluye desvíos redundantes, puede mejorar los resultados")
    '''
    el resultado de la función a minimizar lo determina la METRICA_ERROR y es:
        0: la suma del cuadrado de los desvios de cada una de las variables
        1: la suma de los valores absolutos de los desvios de cada una de las variables
        2: la suma de los desvios de cada una de las variables elevada a POT_DESVIOS, si el desvio es negatino se toma el valor absoluto
    '''
    parser.add_argument('--METRICA_ERROR'      , type=int  , default=0     , help="métrica del error: 0=cuadrado; 1=absoluto; 2=elevado a POT")
    parser.add_argument('--POT_DESVIOS'        , type=int  , default=2     , help="solo se usa en el caso de METRICA_ERROR = 2")
    parser.add_argument('--PRECIO_INI'         , type=float, default=0.5   , help="para el caso 5 'pre_ini'")
    parser.add_argument('--FACTOR_CSSH'        , type=float, default=[1.0, 1.0] , nargs='*', help="para afectar los coeficientes de la seguridad social de los hohares, caso 8")
    parser.add_argument('--FACTOR_CSSE'        , type=float, default=[1.0, 1.0], nargs='*', help="para afectar los coeficientes de la seguridad social de las empresas, caso 8")
    '''
    factores aportados adicionales para el caso 6, si se especifica un solo valor (escalar) se afectan todos por él
    '''
    parser.add_argument('--VAR_FACTORES'       , type=float, default=[0., 0., 0., 0.], nargs='*', help="factores aportados adicionales para el caso 6.")
    parser.add_argument('--SIGMA_ESCENARIO'    , type=float, default=[4., 2.], nargs='*', help="valor de sigma para el escenario 13")

    parser.add_argument('--SENDA_DATOS'        , type=str  , default='C:/MEGA/Datos'   , help="debe existir")
    parser.add_argument('--SENDA_SALIDAS'      , type=str  , default='C:/MEGA/Salidas' , help="senda para las salidas")
    parser.add_argument('--SENDA_GRAFICOS'     , type=str  , default='C:/MEGA/Graficos', help="senda para los gráficos")
    parser.add_argument('--SENDA_DLL'          , type=str  , default='C:/MEGA/Mega_DLL/x64/Debug/MEGA_DLL.dll', help="senda para la DLL")
    args = parser.parse_args()
    return args

def valores_opciones2():
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
        'dem_alfa',             #  9 simplemente cambia la preferencia de los consumos, no se añade demanda porque duplicaría el efecto en los productos
        # usar el caso 0 para ayudas no es equivalente al caso 12 porque las ayudas no irán destinadas de forma diferenciada a los productos, para esto hay que modificar los alfa  
        'alfa_ayudas',          # 10
        'sigma',                # 11
        'aranceles',            # 12
        'Xp0',                  # 13 consumos esenciales = Xp0
        'Xp0m1',                # 14 consumos esenciales = Xp0 - 1
    '''
    # si PREFIJO empieza con el caracter '=' los caracteres del 1 en adelante se usarán como nombre de los ficheros de salida en
    # lugar de componerlos a partir de las opciones seleccionadas, en este caso NO puede haber ESPACIOS en blanco intercalados

    parser.add_argument('--USAR_DLL'           , type=sab  , default=False, help="si True se usa la DLL en caso contrario la función Python")
    parser.add_argument('--USAR_ALGE_DLL'      , type=sab  , default=False, help="si True se usa la DLL para el algoritmo genético")
    parser.add_argument('--ALGE_MAX_INTENTOS'  , type=int   , default=5 , help="")
    parser.add_argument('--ALGE_N_HILOS'       , type=int   , default=16 , help="")
    parser.add_argument('--ALGE_TOL_ACEPTABLE' , type=float , default=1.0e-05 , help="")
    parser.add_argument('--ALGE_MODO_POB_INI'  , type=int   , default=0 , help="")
    parser.add_argument('--ALGE_F_INICIO_POB'  , type=float , default=0.05 , help="")
    parser.add_argument('--ALGE_SIGMA_POB_INI' , type=float , default=0.1 , help="")
    parser.add_argument('--ALGE_TRAMOS_LHS'    , type=int   , default=100 , help="")
    parser.add_argument('--ALGE_NPOB'          , type=int   , default=1200 , help="")
    parser.add_argument('--ALGE_F_MUTACION'    , type=float , default=0.72 , help="")
    parser.add_argument('--ALGE_RECOMBINACION' , type=float , default=[0.99, 1.10], nargs='*', help="")
    parser.add_argument('--ALGE_CTRL_FACTIBLE' , type=int   , default=1 , help="")
    parser.add_argument('--ALGE_RES_EXTENSA'   , type=int   , default=0 , help="")
    parser.add_argument('--NSAM'               , type=int  , default=2    , help="Matriz de Contabilidad Social a utilizar, ver 'etq_sam'")
    parser.add_argument('--DECIMALES'          , type=int  , default=4    , help="número de decimales en las cantidades e importes")
    # hay que especificar estos números porque luego hay que redimensionar las matrices aplanadas
    parser.add_argument('--NFAC'               , type=int  , default=2    , help="número de factores")
    parser.add_argument('--NDEM'               , type=int  , default=2    , help="número de hogares")
    parser.add_argument('--NSEC'               , type=int  , default=2    , help="número de sectores")
    parser.add_argument('--PREFIJO'            , type=str  , default='=Mcs2' , help="un literal que se añade al principio del nombre de los archivos de salida")
    '''
    42, 333, 1755, 1234, 7000, 933, 2255, 1515, 29
    '''
    parser.add_argument('--GE_SEMILLA'         , type=int  , default=42   , help="valor inicial del generador de números aleatorios")
    parser.add_argument('--NCASO'              , type=int  , default=[0], nargs='*', help="número de esenario a utilizar, se pueden combinar varios, por ejemplo default=[0,14], atención al orden")

    #-----------------------------------------------------
    # las matrices se especifican aplanadas como vectores.
    #-----------------------------------------------------
    
    # Para ver los efectos de la demanda adicional lo apropiado es usar NCASO = 0
    parser.add_argument('--DEM_ADICIONAL_TIPO' , type=int  , default=0    , help="0: se añade 'DEM_ADICIONAL' al importe demandado; 1: se añade 'DEM_ADICIONAL' a la cantidad demandada")
    parser.add_argument('--DEM_ADICIONAL'      , type=float, default=[0., 0., 0., 0.], nargs='*', help="demanda adicional exógena de productos para los hogares")
    parser.add_argument('--RENTA_FICTICIA'     , type=sab  , default=False , help="si True no se proveerán fondos para los incrementos de demanda")
    
    # Para ver los efectos de las ayudas lo apropiado es usar NCASO = 10
    parser.add_argument('--AYD_ADICIONAL'      , type=float, default=[0., 0., 0., 0.], nargs='*', help="ayuda adicional exógena por producto para el hogar 1")

    # 'CON_ESENCIALES' cantidades de consumos esenciales. Si DEM_ESENCIALES = False, simplemente se usan como el valor mínimo de las compras, sin usar la función de demanda Stone-Geary
    '''
    parser.add_argument('--CON_ESENCIALES'     , type=float, default=[np.round(8118.*0.7,0), np.round(15120.*0.65),np.round(87781.*0.80),np.round(3767.*0.75),np.round(307653.*0.90),np.round(1878.*0.5),np.round(1111.*0.9),np.round(2069.*0.9),np.round(12012.*0.9),np.round(516.*0.9),np.round(42096.*0.9),np.round(257.*0.9)], nargs='*', help="consumos esenciales para los hogares")
    parser.add_argument('--CON_ESENCIALES'     , type=float, default=[5683., 9828., 70225., 2825., 276888., 939., 1000., 1862., 10811., 464, 37886, 231.], nargs='*', help="consumos esenciales para los hogares")
    '''
    parser.add_argument('--CON_ESENCIALES'     , type=float, default=[0., 0., 0., 0.], nargs='*', help="consumos esenciales para los hogares")
    parser.add_argument('--DEM_ESENCIALES'     , type=sab, default=False, help="True: usar los 'CON_ESENCIALES' en el cálculo de productos demandados (Stone-Geary)")

    parser.add_argument('--ARANCELES'          , type=float, default=[0., 0.], nargs='*', help="para el escenario 12")

    parser.add_argument('--FF_ENDOGENA'        , type=sab  , default=True , help="Las aportaciones de factores por los hogares pueden ser variables endogenas o exogenas")
    parser.add_argument('--ALP_FACTOR'         , type=float, default=0.0  , help="tanto por uno de los excesos de factores aportados, sobre sus valores iniciales, que se lleva a la cuenta Alp") 
    '''
    cuando FF_ENDOGENA, hay que especificar
        OR_PRE_EXCLUIDO   = 0
        PRECIO_F_EXCLUIDO = 1.0
        VALOR_F_TRA         = 1.0 salvo que el precio del trabajo se quiera como endógeno en cuyo caso VALOR_F_TRA = 0

    si (OR_PRE_EXCLUIDO=0) el precio del capital (PRECIO_F_EXCLUIDO) es exogeno = 1.0 y no formará parte del vector solución
    parser.add_argument('--OR_PRE_EXCLUIDO'  , type=int  , default=0, help="factor de referencia = ordinal (columna de h, empezando en 0) del precio para el que se fija el valor 'PRECIO_F_EXCLUIDO'")
    parser.add_argument('--PRECIO_F_EXCLUIDO', type=float, default=1.0   , help="precio que se fija para el factor de referencia")
    
    si OR_PRE_EXCLUIDO = 0 el precio del trabajo formará parte del vector solución, puede ser:
        endogeno : si VALOR_F_TRA = -1
        fijo     : será acotado al valor VALOR_F_TRA si es > 0
        calculado: si VALOR_F_TRA = 0
    '''
    parser.add_argument('--OR_PRE_EXCLUIDO'  , type=int  , default=0, help="factor de referencia = ordinal (columna de h, empezando en 0) del precio para el que se fija el valor 'PRECIO_F_EXCLUIDO'")
    parser.add_argument('--PRECIO_F_EXCLUIDO', type=float, default=1.0   , help="precio que se fija para el factor de referencia")
    parser.add_argument('--VALOR_F_TRA'        , type=float, default=1.05   , help="precio que se fija para el factor trabajo; -1 : no se fija valor, 0 : curva Phillips")
    parser.add_argument('--PARO_INICIAL'       , type=float, default=0.10  , help="tanto por uno de paro para la curva Phillips")
    parser.add_argument('--ALFA_PHILLIPS'      , type=float, default=-0.5  , help="relación desempleo salarios, en la bibliografía se encuentra -0.4566") 
    '''
    parser.add_argument('--GE_FIX'             , type=str  , default=[] , nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--GE_FIX_LON'         , type=int  , default=[0], nargs='*', help="número de parejas para cada variable en GE_FIX")
    parser.add_argument('--GE_FIX_LIMITES'     , type=str, default=[]   , nargs='*', help="una pareja para cada índice de la variable") 

    parser.add_argument('--GE_FIX'             , type=str  , default=['epsilon'], nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--GE_FIX_LON'         , type=int  , default=[1], nargs='*', help="número de parejas para cada variable en GE_FIX")
    parser.add_argument('--GE_FIX_LIMITES'     , type=str  , default=[1.0, 1.0] , nargs='*', help="una pareja para cada índice de la variable; '*' = criterio general, cualquier 'str' el valor inicial")

    parser.add_argument('--GE_FIX'             , type=str  , default=['M'], nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--GE_FIX_LON'         , type=int  , default=[6], nargs='*', help="número de parejas para cada variable en GE_FIX")
    parser.add_argument('--GE_FIX_LIMITES'     , type=str, default=['*', '*', '*', '*', 'M0', 'M0', '*', '*', '*', '*', '*', '*'] , nargs='*', help="una pareja para cada índice de la variable; '*' = criterio general, cualquier 'str' el valor inicial")

    parser.add_argument('--GE_FIX'             , type=str  , default=['epsilon','M'], nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--GE_FIX_LON'         , type=int  , default=[1, 6], nargs='*', help="número de parejas para cada variable en GE_FIX")
    parser.add_argument('--GE_FIX_LIMITES'     , type=str, default=[1.0, 1.0, '*', '*', '*', '*', 'M0', 'M0', '*', '*', '*', '*', '*', '*'] , nargs='*', help="una pareja para cada índice de la variable; '*' = criterio general, cualquier 'str' el valor inicial")
    '''
    parser.add_argument('--GE_FIX'             , type=str  , default=['epsilon'], nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--GE_FIX_LON'         , type=int  , default=[1], nargs='*', help="número de parejas para cada variable en GE_FIX")
    parser.add_argument('--GE_FIX_LIMITES'     , type=str  , default=[1.0, 1.0] , nargs='*', help="una pareja para cada índice de la variable; '*' = criterio general, cualquier 'str' el valor inicial")

    parser.add_argument('--UTILIDAD_DEMANDA'   , type=int  , default=0     , help="0: Cobb Douglas; 1: CES")
    parser.add_argument('--SIGMA_CES_DEMANDA'  , type=float, default=[2., 2.], nargs='*', help="sigma de la función de demanda CES")
    parser.add_argument('--MODO_PSEUDOIMPTOS'  , type=int  , default=0     , help="0: variables según cambian las cotizaciones a la seguridad social y las ayudas del gobierno; 1: fijos iguales a los que resultam de la MCS")

    parser.add_argument('--SAL_CALIBRADO'      , type=sab  , default=False , help="imprimir los valores de los parámetros calibrados")
    parser.add_argument('--SALIDA_VEC_OPT'     , type=sab  , default=False , help="salida de los valores iniciales de las variables y sus límites")
    parser.add_argument('--SALIDA_VAL_INI'     , type=sab  , default=False , help="informe de los valores iniciales de las variables")
    parser.add_argument('--PRIMERA_VALORACION' , type=sab  , default=False , help="calcular una primera valoración de modelo")
    parser.add_argument('--SALIDA_DESVIOS'     , type=sab  , default=False , help="salida con el detalla de las desviaciones")
    parser.add_argument('--SAL_AUXILIARES'     , type=sab  , default=False , help="imprimir los valores del historial y la evolución de la solución")
    parser.add_argument('--SAL_GRAFICOS_EVOL'  , type=sab  , default=False , help="generar gráficos de las evoluciones")
    parser.add_argument('--SAL_GRAFICO_CES_DM' , type=sab  , default=False , help="generar graficos de isocuantas CES")
    parser.add_argument('--SAL_ISOCUANTA'      , type=sab  , default=False , help="generar gráficos adicionales de isocuantas")
    parser.add_argument('--SAL_VARIACIONES'    , type=sab  , default=True , help="imprime las diferencias entre los valores iniciales y finales de las variables")
    parser.add_argument('--SAL_MCS'            , type=sab  , default=True  , help="imprime la MCS")
    parser.add_argument('--SAL_VAR_MCS'        , type=sab  , default=False , help="imprime las diferencias entre los valores iniciales y finales de la MCS")

    parser.add_argument('--GE_INCLUYE_XP'      , type=sab  , default=False , help="incluir Xp en el vector solución")
    parser.add_argument('--GE_RESTRICCIONES'   , type=sab  , default=False , help="restricciones en cantidad de importación (M) y exportación (E)")
    parser.add_argument('--GE_TIPO_RE'         , type=int  , default=1     , help="0: lineal; 1: No lineal")
    parser.add_argument('--GE_TOLERANCIA'      , type=float, default=1.e-11, help="límite para considerar el objetivo alcanzado o que no hay progreso")
    parser.add_argument('--GE_VERIFICAR'       , type=float, default=1.e-08, help="límite para considerar que la ecuación se cumple")
    # GE_PROGRESO tiene su importancia porque la minimización puede terminar si tras GE_PROGRESO generaciones no mejora al menos GE_TOLERANCIA
    # Si GE_PROGRESO es demasiado pequeño, la minimización puede terminar incorrectamente porque no ha tenido tiempo de progresar
    parser.add_argument('--GE_PROGRESO'        , type=int  , default=100   , help="número de generaciones para comprobar el progreso")
    parser.add_argument('--GE_HISTORIAL'       , type=int  , default=100   , help="número de generaciones para salvar el historial")
    parser.add_argument('--GE_SOLUCIONES'      , type=int  , default=100   , help="número de generaciones para salvar la solución")
    '''
    parser.add_argument('--GE_PRE_MIN'         , type=float, default=3.0   , help="el límite inferior del rango de variación de los precios es su valor inicial dividido por GE_PRE_MIN")
    parser.add_argument('--GE_PRE_MAX'         , type=float, default=3.0   , help="el límite superior del rango de variación de los precios es su valor inicial multiplicado por GE_PRE_MAX")
    parser.add_argument('--GE_VAR_MIN'         , type=float, default=9.0   , help="el límite inferior del rango de variación de las variables es su valor inicial dividido por GE_VAR_MIN")
    parser.add_argument('--GE_VAR_MAX'         , type=float, default=9.0   , help="el límite superior del rango de variación de las variables es su valor inicial multiplicado por GE_VAR_MAX")
    '''
    parser.add_argument('--GE_PRE_MIN'         , type=float, default=40.0  , help="el límite inferior del rango de variación de los precios es su valor inicial dividido por GE_PRE_MIN")
    parser.add_argument('--GE_PRE_MAX'         , type=float, default=40.0  , help="el límite superior del rango de variación de los precios es su valor inicial multiplicado por GE_PRE_MAX")
    parser.add_argument('--GE_VAR_MIN'         , type=float, default=50.0  , help="el límite inferior del rango de variación de las variables es su valor inicial dividido por GE_VAR_MIN")
    parser.add_argument('--GE_VAR_MAX'         , type=float, default=50.0  , help="el límite superior del rango de variación de las variables es su valor inicial multiplicado por GE_VAR_MAX")
    parser.add_argument('--GE_VAR_CERO'        , type=float, default=10000.0,help="si el valor inicial de una variable es cero su rango de variación es [-GE_VAR_CERO, +GE_VAR_CERO]")
    parser.add_argument('--GE_VAR_CAN_MIN'     , type=float, default=5000.0 ,help="rando de variación mínimo para una variable")
    parser.add_argument('--GE_MAX_ITER'        , type=int  , default=1000000,help="máximo número de generaciones a simular")
    parser.add_argument('--GE_ACTUALIZACION'   , type=str  , default='immediate', help="cada vez que se cambia un individuo")
    parser.add_argument('--GE_RECONBINACION'   , type=float, default=0.90  , help="recombinación")
    parser.add_argument('--GE_DIM_POBLACION'   , type=int  , default=5     , help="factor para establecer el tamaño de la población (por defecto es 15)")
    parser.add_argument('--GE_WORKERS'         , type=int  , default=32    , help="número de procesadores a utilizar (en esta máquina el máximo es 61 y el óptimo 32)")
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
    parser.add_argument('--OPT_DESVIOS'        , type=int  , default=1     , help="0: incluye desvíos redundantes, puede mejorar los resultados")
    '''
    el resultado de la función a minimizar lo determina la METRICA_ERROR y es:
        0: la suma del cuadrado de los desvios de cada una de las variables
        1: la suma de los valores absolutos de los desvios de cada una de las variables
        2: la suma de los desvios de cada una de las variables elevada a POT_DESVIOS, si el desvio es negatino se toma el valor absoluto
    '''
    parser.add_argument('--METRICA_ERROR'      , type=int  , default=0     , help="métrica del error: 0=cuadrado; 1=absoluto; 2=elevado a POT")
    parser.add_argument('--POT_DESVIOS'        , type=int  , default=2     , help="solo se usa en el caso de METRICA_ERROR = 2")
    parser.add_argument('--PRECIO_INI'         , type=float, default=0.5   , help="para el caso 5 'pre_ini'")
    parser.add_argument('--FACTOR_CSSH'        , type=float, default=[1.0, 1.0] , nargs='*', help="para afectar los coeficientes de la seguridad social de los hohares, caso 8")
    parser.add_argument('--FACTOR_CSSE'        , type=float, default=[1.0, 1.0], nargs='*', help="para afectar los coeficientes de la seguridad social de las empresas, caso 8")
    '''
    factores aportados adicionales para el caso 6, si se especifica un solo valor (escalar) se afectan todos por él
    '''
    parser.add_argument('--VAR_FACTORES'       , type=float, default=[0., 0., 0., 0.], nargs='*', help="factores aportados adicionales para el caso 6.")
    parser.add_argument('--SIGMA_ESCENARIO'    , type=float, default=[4., 2.], nargs='*', help="valor de sigma para el escenario 13")

    parser.add_argument('--SENDA_DATOS'        , type=str  , default='C:/MEGA/Datos'   , help="debe existir")
    parser.add_argument('--SENDA_SALIDAS'      , type=str  , default='C:/MEGA/Salidas' , help="senda para las salidas")
    parser.add_argument('--SENDA_GRAFICOS'     , type=str  , default='C:/MEGA/Graficos', help="senda para los gráficos")
    parser.add_argument('--SENDA_DLL'          , type=str  , default='C:/MEGA/Mega_DLL/x64/Debug/MEGA_DLL.dll', help="senda para la DLL")
    args = parser.parse_args()
    return args

def valores_opciones4():
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
        'dem_alfa',             #  9 simplemente cambia la preferencia de los consumos, no se añade demanda porque duplicaría el efecto en los productos
        # usar el caso 0 para ayudas no es equivalente al caso 12 porque las ayudas no irán destinadas de forma diferenciada a los productos, para esto hay que modificar los alfa  
        'alfa_ayudas',          # 10
        'sigma',                # 11
        'aranceles',            # 12
        'Xp0',                  # 13 consumos esenciales = Xp0
        'Xp0m1',                # 14 consumos esenciales = Xp0 - 1
    '''
    # si PREFIJO empieza con el caracter '=' los caracteres del 1 en adelante se usarán como nombre de los ficheros de salida en
    # lugar de componerlos a partir de las opciones seleccionadas, en este caso NO puede haber ESPACIOS en blanco intercalados
    parser.add_argument('--PREFIJO'            , type=str  , default='=M4' , help="un literal que se añade al principio del nombre de los archivos de salida")

    parser.add_argument('--USAR_DLL'           , type=sab   , default=True , help="si True se usa la función objetivo de la DLL, en caso contrario la función Python")
    parser.add_argument('--ALGE_MODO_POB_INI'  , type=int   , default=0   , help="")

    parser.add_argument('--GE_WORKERS'         , type=int  , default=1     , help="número de procesadores a utilizar (en esta máquina el máximo es 61 y el óptimo 32)")
    # GE_PROGRESO tiene su importancia porque la minimización puede terminar si tras GE_PROGRESO generaciones no mejora al menos GE_MIN_PROGRESO
    # Si GE_PROGRESO es demasiado pequeño, la minimización puede terminar incorrectamente porque no ha tenido tiempo de progresar
    parser.add_argument('--GE_PROGRESO'        , type=int  , default=1000  , help="número de generaciones para comprobar el progreso")
    parser.add_argument('--GE_MIN_PROGRESO'    , type=float, default=0.05   , help="% de mejora mínima para considerar que hay progreso")
    parser.add_argument('--USAR_ALGE_DLL'      , type=sab   , default=True , help="si True se usa el algoritmo genético de la DLL")
    parser.add_argument('--ALGE_ID_SALIDA'     , type=int  , default=1400  , help="")
    parser.add_argument('--ALGE_MAX_INTENTOS'  , type=int   , default=5    , help="")
    parser.add_argument('--ALGE_N_HILOS'       , type=int   , default=16   , help="")
    parser.add_argument('--ALGE_TOL_ACEPTABLE' , type=float , default=1.0e-05, help="")
    parser.add_argument('--ALGE_F_INICIO_POB'  , type=float , default=0.05 , help="")
    parser.add_argument('--ALGE_SIGMA_POB_INI' , type=float , default=0.1  , help="")
    parser.add_argument('--ALGE_TRAMOS_LHS'    , type=int   , default=400  , help="")
    parser.add_argument('--ALGE_NPOB'          , type=int   , default=1200 , help="")
    parser.add_argument('--ALGE_F_MUTACION'    , type=float , default=0.72 , help="")
    parser.add_argument('--ALGE_RECOMBINACION' , type=float , default=[0.99, 1.10], nargs='*', help="")
    parser.add_argument('--ALGE_CTRL_FACTIBLE' , type=int   , default=1    , help="")
    parser.add_argument('--ALGE_RES_EXTENSA'   , type=int   , default=0    , help="")
    parser.add_argument('--EL_MEJOR_PRIMERO'   , type=int   , default=0    , help="")
    parser.add_argument('--ALGE_INCLUIR_X0'    , type=int  , default=1     , help="")

    parser.add_argument('--NSAM'               , type=int  , default=4     , help="Matriz de Contabilidad Social a utilizar, ver 'etq_sam'")
    parser.add_argument('--DECIMALES'          , type=int  , default=1     , help="número de decimales en las cantidades e importes")
    # hay que especificar estos números porque luego hay que redimensionar las matrices aplanadas
    parser.add_argument('--NFAC'               , type=int  , default=2     , help="número de factores")
    parser.add_argument('--NDEM'               , type=int  , default=2     , help="número de hogares")
    parser.add_argument('--NSEC'               , type=int  , default=6     , help="número de sectores")
    parser.add_argument('--GE_SEMILLA'         , type=int  , default=42    , help="valor inicial del generador de números aleatorios")
    parser.add_argument('--NCASO'              , type=int  , default=[10,12], nargs='*', help="número de esenario a utilizar, se pueden combinar varios, por ejemplo default=[0,14], atención al orden")
    parser.add_argument('--FI_SOL_LEE'         , type=str  , default='' , help="un literal que se añade al principio del nombre de los archivos de salida, o el propio nombre")
    parser.add_argument('--FI_SOL_SALVA'       , type=str  , default='' , help="un literal que se añade al principio del nombre de los archivos de salida, o el propio nombre")

    parser.add_argument('--EQ_BAL_PAGOS'       , type=sab  , default=True  , help="si True no se proveerán fondos para los incrementos de demanda")
    parser.add_argument('--PRECIO_IMPORTACION' , type=float, default=[], nargs='*', help="precio de importación de determinados productos, parejas: índice, precio")

    #-----------------------------------------------------
    # las matrices se especifican aplanadas como vectores.
    #-----------------------------------------------------
    
    # Para ver los efectos de la demanda adicional lo apropiado es usar NCASO = 0
    parser.add_argument('--DEM_ADICIONAL_TIPO' , type=int  , default=0    , help="0: se añade 'DEM_ADICIONAL' al importe demandado; 1: se añade 'DEM_ADICIONAL' a la cantidad demandada")
    parser.add_argument('--DEM_ADICIONAL'      , type=float, default=[0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.], nargs='*', help="demanda adicional exógena de productos para los hogares")
    parser.add_argument('--DEM_AD_LON'         , type=int  , default=0    , help="número de demandas adicionales exógenas de productos para los hogares")
    parser.add_argument('--DEM_AD_HO_PRO'      , type=float, default=[1,2,1000.], nargs='*', help="demanda adicional exógena del hogar para el producto")
    parser.add_argument('--RENTA_FICTICIA'     , type=sab  , default=False , help="si True no se proveerán fondos para los incrementos de demanda")
    
    # Para ver los efectos de las ayudas lo apropiado es usar NCASO = 10
    parser.add_argument('--AYD_ADICIONAL'      , type=float, default=[0., 0., 0., 0., 0., 0., 0., 0., 0., 1000., 0., 0.], nargs='*', help="ayuda adicional exógena por producto para los hogares")
    parser.add_argument('--AYD_AD_LON'         , type=int  , default=1    , help="número de ayudas exógenas de productos para los hogares")
    parser.add_argument('--AYD_AD_HO_PRO'      , type=float, default=[1, 2, 1000.], nargs='*', help="ayuda exógena al hogar para el producto")

    # 'CON_ESENCIALES' cantidades de consumos esenciales. Si DEM_ESENCIALES = False, simplemente se usan como el valor mínimo de las compras, sin usar la función de demanda Stone-Geary
    '''
    parser.add_argument('--CON_ESENCIALES'     , type=float, default=[np.round(8118.*0.7,0), np.round(15120.*0.65),np.round(87781.*0.80),np.round(3767.*0.75),np.round(307653.*0.90),np.round(1878.*0.5),np.round(1111.*0.9),np.round(2069.*0.9),np.round(12012.*0.9),np.round(516.*0.9),np.round(42096.*0.9),np.round(257.*0.9)], nargs='*', help="consumos esenciales para los hogares")
    parser.add_argument('--CON_ESENCIALES'     , type=float, default=[5683., 9828., 70225., 2825., 276888., 939., 1000., 1862., 10811., 464, 37886, 231.], nargs='*', help="consumos esenciales para los hogares")
    '''
    parser.add_argument('--CON_ESENCIALES'     , type=float, default=[0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.], nargs='*', help="consumos esenciales para los hogares")
    parser.add_argument('--CON_AD_LON'         , type=int  , default=0    , help="número de consumos esenciales exógenos de productos para los hogares")
    parser.add_argument('--CON_AD_HO_PRO'      , type=float, default=[1,4,1000.], nargs='*', help="consumos esenciales exógenos al hogar para el producto")
    parser.add_argument('--DEM_ESENCIALES'     , type=sab, default=False, help="True: usar los 'CON_ESENCIALES' en el cálculo de productos demandados (Stone-Geary)")

    parser.add_argument('--ARANCELES'          , type=float, default=[0., 0., 0.002961, 0., 0., 0.], nargs='*', help="para el escenario 12")
    parser.add_argument('--ARANCELES_LON'      , type=int  , default=1    , help="número de aranceles a modificar")
    parser.add_argument('--ARANCELES_PRO'      , type=float, default=[2, 0.002961], nargs='*', help="parejas de: producto, arancel")

    parser.add_argument('--FF_ENDOGENA'        , type=sab  , default=True , help="Las aportaciones de factores por los hogares pueden ser variables endogenas o exogenas")
    parser.add_argument('--ALP_FACTOR'         , type=float, default=0.0  , help="tanto por uno de los excesos de factores aportados, sobre sus valores iniciales, que se lleva a la cuenta Alp") 
    '''
    cuando FF_ENDOGENA, hay que especificar
        OR_PRE_EXCLUIDO   = 0
        PRECIO_F_EXCLUIDO = 1.0
        VALOR_F_TRA         = 1.0 salvo que el precio del trabajo se quiera como endógeno en cuyo caso VALOR_F_TRA = 0

    si (OR_PRE_EXCLUIDO=0) el precio del capital (PRECIO_F_EXCLUIDO) es exogeno = 1.0 y no formará parte del vector solución
    parser.add_argument('--OR_PRE_EXCLUIDO'  , type=int  , default=0, help="factor de referencia = ordinal (columna de h, empezando en 0) del precio para el que se fija el valor 'PRECIO_F_EXCLUIDO'")
    parser.add_argument('--PRECIO_F_EXCLUIDO', type=float, default=1.0   , help="precio que se fija para el factor de referencia")
    
    si OR_PRE_EXCLUIDO = 0 el precio del trabajo formará parte del vector solución, puede ser:
        endogeno : si VALOR_F_TRA = -1
        fijo     : será acotado al valor VALOR_F_TRA si es > 0
        calculado: si VALOR_F_TRA = 0
    '''
    parser.add_argument('--OR_PRE_EXCLUIDO'    , type=int  , default=0    , help="factor de referencia = ordinal (columna de h, empezando en 0) del precio para el que se fija el valor 'PRECIO_F_EXCLUIDO'")
    parser.add_argument('--PRECIO_F_EXCLUIDO'  , type=float, default=1.0  , help="precio que se fija para el factor de referencia")
    parser.add_argument('--VALOR_F_TRA'        , type=float, default=0    , help="precio que se fija para el factor trabajo; -1 : no se fija valor, 0 : curva Phillips")
    parser.add_argument('--PARO_INICIAL'       , type=float, default=0.10 , help="tanto por uno de paro para la curva Phillips")
    parser.add_argument('--ALFA_PHILLIPS'      , type=float, default=-0.5 , help="relación desempleo salarios, en la bibliografía se encuentra -0.4566") 

    parser.add_argument('--FIX'                , type=str  , default=['epsilon'], nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--FIX_LON'            , type=int  , default=[1], nargs='*', help="número de ternas para cada variable en FIX")
    parser.add_argument('--FIX_LIMITES'        , type=str  , default=[0,1.0,1.0] , nargs='*', help="una terna para cada variable: indice,valor inferior,valor superior; '*' = criterio general, cualquier 'str' el valor inicial")

    parser.add_argument('--UTILIDAD_DEMANDA'   , type=int  , default=0       , help="0: Cobb Douglas; 1: CES")
    parser.add_argument('--SIGMA_CES_DEMANDA'  , type=float, default=[2., 2.], nargs='*', help="sigma de la función de demanda CES")
    parser.add_argument('--MODO_PSEUDOIMPTOS'  , type=int  , default=0       , help="0: variables según cambian las cotizaciones a la seguridad social y las ayudas del gobierno; 1: fijos iguales a los que resultam de la MCS")

    parser.add_argument('--SAL_CALIBRADO'      , type=sab  , default=False , help="imprimir los valores de los parámetros calibrados")
    parser.add_argument('--SALIDA_VEC_OPT'     , type=sab  , default=False , help="salida de los valores iniciales de las variables y sus límites")
    parser.add_argument('--SALIDA_VAL_INI'     , type=sab  , default=True  , help="informe de los valores iniciales de las variables")
    parser.add_argument('--PRIMERA_VALORACION' , type=sab  , default=False , help="calcular una primera valoración de modelo")
    parser.add_argument('--SALIDA_DESVIOS'     , type=sab  , default=False, help="salida con el detalla de las desviaciones")
    parser.add_argument('--SAL_AUXILIARES'     , type=sab  , default=False , help="imprimir los valores del historial y la evolución de la solución")
    parser.add_argument('--SAL_GRAFICOS_EVOL'  , type=sab  , default=False , help="generar gráficos de las evoluciones")
    parser.add_argument('--SAL_GRAFICO_CES_DM' , type=sab  , default=False , help="generar graficos de isocuantas CES")
    parser.add_argument('--SAL_ISOCUANTA'      , type=sab  , default=False , help="generar gráficos adicionales de isocuantas")
    parser.add_argument('--SAL_VARIACIONES'    , type=sab  , default=True  , help="imprime las diferencias entre los valores iniciales y finales de las variables")
    parser.add_argument('--SAL_MCS'            , type=sab  , default=True  , help="imprime la MCS")
    parser.add_argument('--SAL_VAR_MCS'        , type=sab  , default=False , help="imprime las diferencias entre los valores iniciales y finales de la MCS")

    parser.add_argument('--GE_INCLUYE_XP'      , type=sab  , default=False , help="incluir Xp en el vector solución")
    parser.add_argument('--GE_RESTRICCIONES'   , type=sab  , default=False , help="restricciones en cantidad de importación (M) y exportación (E)")
    parser.add_argument('--GE_TIPO_RE'         , type=int  , default=1     , help="0: lineal; 1: No lineal")
    parser.add_argument('--GE_TOLERANCIA'      , type=float, default=1.e-10, help="límite para considerar el objetivo alcanzado o que no hay progreso")
    parser.add_argument('--GE_VERIFICAR'       , type=float, default=1.e-08, help="límite para considerar que la ecuación se cumple")
    parser.add_argument('--GE_HISTORIAL'       , type=int  , default=500   , help="número de generaciones para salvar el historial")
    parser.add_argument('--GE_SOLUCIONES'      , type=int  , default=0     , help="número de generaciones para salvar la solución")
    '''
    parser.add_argument('--GE_PRE_MIN'         , type=float, default=2.0   , help="el límite inferior del rango de variación de los precios es su valor inicial dividido por GE_PRE_MIN")
    parser.add_argument('--GE_PRE_MAX'         , type=float, default=2.0   , help="el límite superior del rango de variación de los precios es su valor inicial multiplicado por GE_PRE_MAX")
    parser.add_argument('--GE_VAR_MIN'         , type=float, default=4.0   , help="el límite inferior del rango de variación de las variables es su valor inicial dividido por GE_VAR_MIN")
    parser.add_argument('--GE_VAR_MAX'         , type=float, default=4.0   , help="el límite superior del rango de variación de las variables es su valor inicial multiplicado por GE_VAR_MAX")
    '''
    parser.add_argument('--GE_PRE_MIN'         , type=float, default=30.0  , help="el límite inferior del rango de variación de los precios es su valor inicial por   (1 - GE_PRE_MIN/100)")
    parser.add_argument('--GE_PRE_MAX'         , type=float, default=30.0  , help="el límite superior del rango de variación de los precios es su valor inicial por   (1 + GE_PRE_MAX/100)")
    parser.add_argument('--GE_VAR_MIN'         , type=float, default=50.0  , help="el límite inferior del rango de variación de las variables es su valor inicial por (1 - GE_PRE_MIN/100)")
    parser.add_argument('--GE_VAR_MAX'         , type=float, default=50.0  , help="el límite superior del rango de variación de las variables es su valor inicial por (1 + GE_PRE_MAX/100)")
    parser.add_argument('--GE_VAR_CERO'        , type=float, default=10000.0,help="si el valor inicial de una variable es cero su rango de variación es [-GE_VAR_CERO, +GE_VAR_CERO]")
    parser.add_argument('--GE_VAR_CAN_MIN'     , type=float, default=0      ,help="rando de variación mínimo para una variable")
    parser.add_argument('--GE_MAX_ITER'        , type=int  , default=100000 ,help="máximo número de generaciones a simular")

    parser.add_argument('--GE_ACTUALIZACION'   , type=str  , default='immediate', help="cada vez que se cambia un individuo")
    parser.add_argument('--GE_RECONBINACION'   , type=float, default=0.99  , help="recombinación")
    parser.add_argument('--GE_DIM_POBLACION'   , type=int  , default=15    , help="factor para establecer el tamaño de la población (por defecto es 15)")
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
    parser.add_argument('--OPT_DESVIOS'        , type=int  , default=1     , help="0: incluye desvíos redundantes, puede mejorar los resultados")
    '''
    el resultado de la función a minimizar lo determina la METRICA_ERROR y es:
        0: la suma del cuadrado de los desvios de cada una de las variables
        1: la suma de los valores absolutos de los desvios de cada una de las variables
        2: la suma de los desvios de cada una de las variables elevada a POT_DESVIOS, si el desvio es negatino se toma el valor absoluto
    '''
    parser.add_argument('--METRICA_ERROR'      , type=int  , default=0     , help="métrica del error: 0=cuadrado; 1=absoluto; 2=elevado a POT")
    parser.add_argument('--POT_DESVIOS'        , type=int  , default=2     , help="solo se usa en el caso de METRICA_ERROR = 2")
    parser.add_argument('--PRECIO_INI'         , type=float, default=0.5   , help="para el caso 5 'pre_ini'")
    parser.add_argument('--FACTOR_CSSH'        , type=float, default=[1.0, 1.0] , nargs='*', help="para afectar los coeficientes de la seguridad social de los hohares, caso 8")
    parser.add_argument('--FACTOR_CSSE'        , type=float, default=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0], nargs='*', help="para afectar los coeficientes de la seguridad social de las empresas, caso 8")
    '''
    factores aportados adicionales para el caso 6, si se especifica un solo valor (escalar) se afectan todos por él
    '''
    parser.add_argument('--VAR_FACTORES'       , type=float, default=[0., 0., 0., 0.], nargs='*', help="factores aportados adicionales para el caso 6.")
    parser.add_argument('--SIGMA_ESCENARIO'    , type=float, default=[2., 2., 2., 2., 2., 2.], nargs='*', help="valor de sigma para el escenario 13")

    parser.add_argument('--SENDA_DATOS'        , type=str  , default='C:/MEGA/Datos'   , help="debe existir")
    parser.add_argument('--SENDA_SALIDAS'      , type=str  , default='C:/MEGA/Salidas' , help="senda para las salidas")
    parser.add_argument('--SENDA_GRAFICOS'     , type=str  , default='C:/MEGA/Graficos', help="senda para los gráficos")
    parser.add_argument('--SENDA_SOLUCIONES'   , type=str  , default='C:/MEGA/Soluciones', help="senda para los vectores solución")
    parser.add_argument('--SENDA_DLL'          , type=str  , default='C:/MEGA/MEGA_DLL/x64/Release/MEGA4.dll', help="senda para la DLL")
    args = parser.parse_args()
    return args

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
        'dem_alfa',             #  9 simplemente cambia la preferencia de los consumos, no se añade demanda porque duplicaría el efecto en los productos
        # usar el caso 0 para ayudas no es equivalente al caso 12 porque las ayudas no irán destinadas de forma diferenciada a los productos, para esto hay que modificar los alfa  
        'alfa_ayudas',          # 10
        'sigma',                # 11
        'aranceles',            # 12
        'Xp0',                  # 13 consumos esenciales = Xp0
        'Xp0m1',                # 14 consumos esenciales = Xp0 - 1
    '''
    # si PREFIJO empieza con el caracter '=' los caracteres del 1 en adelante se usarán como nombre de los ficheros de salida en
    # lugar de componerlos a partir de las opciones seleccionadas, en este caso NO puede haber ESPACIOS en blanco intercalados
    parser.add_argument('--PREFIJO'            , type=str  , default='=12_12000_333' , help="un literal que se añade al principio del nombre de los archivos de salida, o el propio nombre")

    parser.add_argument('--GE_WORKERS'         , type=int  , default=1      , help="número de procesadores a utilizar (en esta máquina el máximo es 61 y el óptimo 32)")
    parser.add_argument('--DESV_RELATIVA'      , type=int  , default=0      , help="1: desviaciones en términos relativos, tanto por uno")
    parser.add_argument('--USAR_DLL'           , type=sab  , default=True   , help="si True se usa la función objetivo de la DLL, en caso contrario la función Python")
    parser.add_argument('--USAR_ALGE_DLL'      , type=sab  , default=True   , help="si True se usa el algoritmo genético de la DLL")
    parser.add_argument('--ALGE_ID_SALIDA'     , type=int  , default=12000  , help="")
    parser.add_argument('--ALGE_MAX_INTENTOS'  , type=int  , default=1      , help="")
    parser.add_argument('--ALGE_N_HILOS'       , type=int  , default=20     , help="")
    parser.add_argument('--ALGE_TOL_ACEPTABLE' , type=float, default=1.0e-05, help="")
    parser.add_argument('--ALGE_MODO_POB_INI'  , type=int  , default=12      , help="")
       
    parser.add_argument('--ALGE_F_INICIO_POB'  , type=float, default=0.001 , help="factor de alcance para generar de la población inicial")
    parser.add_argument('--ALGE_SIGMA_POB_INI' , type=float, default=0.75  , help="")
    parser.add_argument('--ALGE_TRAMOS_LHS'    , type=int  , default=400   , help="")
    parser.add_argument('--ALGE_NPOB'          , type=int  , default=12800 , help="")
    parser.add_argument('--ALGE_F_MUTACION'    , type=float, default=0.80  , help="")
    parser.add_argument('--ALGE_RECOMBINACION' , type=float, default=[0.99 , 1.10], nargs='*', help="")
    parser.add_argument('--ALGE_CTRL_FACTIBLE' , type=int  , default=1     , help="")
    parser.add_argument('--ALGE_RES_EXTENSA'   , type=int  , default=0     , help="")
    parser.add_argument('--EL_MEJOR_PRIMERO'   , type=int  , default=0     , help="")
    parser.add_argument('--ALGE_INCLUIR_X0'    , type=int  , default=1     , help="")

    parser.add_argument('--NSAM'               , type=int  , default=5     , help="Matriz de Contabilidad Social a utilizar, ver 'etq_sam'")
    parser.add_argument('--DECIMALES'          , type=int  , default=1     , help="número de decimales en las cantidades e importes")
    # hay que especificar estos números porque luego hay que redimensionar las matrices aplanadas
    parser.add_argument('--NFAC'               , type=int  , default=2     , help="número de factores")
    parser.add_argument('--NDEM'               , type=int  , default=3     , help="número de hogares")
    parser.add_argument('--NSEC'               , type=int  , default=63    , help="número de sectores")
    parser.add_argument('--GE_SEMILLA'         , type=int  , default=333   , help="valor inicial del generador de números aleatorios")
    parser.add_argument('--NCASO'              , type=int  , default=[10,12], nargs='*', help="número de esenario a utilizar, se pueden combinar varios, por ejemplo default=[0,14], atención al orden")
    parser.add_argument('--FI_SOL_LEE'         , type=str  , default='' , help="un literal que se añade al principio del nombre de los archivos de salida, o el propio nombre")
    parser.add_argument('--FI_SOL_SALVA'       , type=str  , default='' , help="un literal que se añade al principio del nombre de los archivos de salida, o el propio nombre")

    parser.add_argument('--EQ_BAL_PAGOS'       , type=sab  , default=True  , help="si True no se proveerán fondos para los incrementos de demanda")
    parser.add_argument('--PRECIO_IMPORTACION' , type=float, default=[], nargs='*', help="precio de importación de determinados productos, parejas: índice, precio")

    #-----------------------------------------------------
    # las matrices se especifican aplanadas como vectores.
    #-----------------------------------------------------
    
    # Para ver los efectos de la demanda adicional lo apropiado es usar NCASO = 0
    parser.add_argument('--DEM_ADICIONAL_TIPO' , type=int  , default=0    , help="0: se añade 'DEM_ADICIONAL' al importe demandado; 1: se añade 'DEM_ADICIONAL' a la cantidad demandada")
    parser.add_argument('--DEM_ADICIONAL'      , type=float, default=[], nargs='*', help="demanda adicional exógena de productos para los hogares")
    parser.add_argument('--DEM_AD_LON'         , type=int  , default=0    , help="número de demandas adicionales exógenas de productos para los hogares")
    parser.add_argument('--DEM_AD_HO_PRO'      , type=float, default=[1,4,1000.], nargs='*', help="demanda adicional exógena del hogar para el producto")

    parser.add_argument('--RENTA_FICTICIA'     , type=sab  , default=False , help="si True no se proveerán fondos para los incrementos de demanda")
    
    # Para ver los efectos de las ayudas lo apropiado es usar NCASO = 10
    parser.add_argument('--AYD_ADICIONAL'      , type=float, default=[], nargs='*', help="ayuda adicional exógena por producto para los hogares")
    parser.add_argument('--AYD_AD_LON'         , type=int  , default=1    , help="número de ayudas exógenas de productos para los hogares")
    parser.add_argument('--AYD_AD_HO_PRO'      , type=float, default=[0,4,1000.], nargs='*', help="ayuda exógena al hogar para el producto")

    # 'CON_ESENCIALES' cantidades de consumos esenciales. Si DEM_ESENCIALES = False, simplemente se usan como el valor mínimo de las compras, sin usar la función de demanda Stone-Geary
    parser.add_argument('--CON_ESENCIALES'     , type=float, default=[], nargs='*', help="consumos esenciales para los hogares")
    parser.add_argument('--CON_AD_LON'         , type=int  , default=0    , help="número de consumos esenciales exógenos de productos para los hogares")
    parser.add_argument('--CON_AD_HO_PRO'      , type=float, default=[1,4,1000.], nargs='*', help="consumos esenciales exógenos al hogar para el producto")
    parser.add_argument('--DEM_ESENCIALES'     , type=sab, default=False, help="True: usar los 'CON_ESENCIALES' en el cálculo de productos demandados (Stone-Geary)")

    parser.add_argument('--ARANCELES'          , type=float, default=[], nargs='*', help="para el escenario 12")
    parser.add_argument('--ARANCELES_LON'      , type=int  , default=1    , help="número de aranceles a modificar")
    parser.add_argument('--ARANCELES_PRO'      , type=float, default=[4,0.005000], nargs='*', help="producto, arancel")

    parser.add_argument('--FF_ENDOGENA'        , type=sab  , default=True , help="las aportaciones de factores por los hogares pueden ser variables endogenas o exogenas")
    parser.add_argument('--ALP_FACTOR'         , type=float, default=0.0  , help="tanto por uno de los excesos de factores aportados, sobre sus valores iniciales, que se lleva a la cuenta Alp") 
    '''
    cuando FF_ENDOGENA, hay que especificar
        OR_PRE_EXCLUIDO   = 0
        PRECIO_F_EXCLUIDO = 1.0
        VALOR_F_TRA         = 1.0 salvo que el precio del trabajo se quiera como endógeno en cuyo caso VALOR_F_TRA = 0

    si (OR_PRE_EXCLUIDO=0) el precio del capital (PRECIO_F_EXCLUIDO) es exogeno = 1.0 y no formará parte del vector solución
    parser.add_argument('--OR_PRE_EXCLUIDO'  , type=int  , default=0, help="factor de referencia = ordinal (columna de h, empezando en 0) del precio para el que se fija el valor 'PRECIO_F_EXCLUIDO'")
    parser.add_argument('--PRECIO_F_EXCLUIDO', type=float, default=1.0   , help="precio que se fija para el factor de referencia")
    
    si OR_PRE_EXCLUIDO = 0 el precio del trabajo formará parte del vector solución, puede ser:
        endogeno : si VALOR_F_TRA = -1
        fijo     : será acotado al valor VALOR_F_TRA si es > 0
        calculado: si VALOR_F_TRA = 0
    '''
    parser.add_argument('--OR_PRE_EXCLUIDO'    , type=int  , default=0    , help="factor de referencia = ordinal (columna de h, empezando en 0) del precio para el que se fija el valor 'PRECIO_F_EXCLUIDO'")
    parser.add_argument('--PRECIO_F_EXCLUIDO'  , type=float, default=1.0  , help="precio que se fija para el factor de referencia")
    parser.add_argument('--VALOR_F_TRA'        , type=float, default=0    , help="precio que se fija para el factor trabajo; -1 : no se fija valor, 0 : curva Phillips")
    parser.add_argument('--PARO_INICIAL'       , type=float, default=0.10 , help="tanto por uno de paro para la curva Phillips")
    parser.add_argument('--ALFA_PHILLIPS'      , type=float, default=-0.5 , help="relación desempleo salarios, en la bibliografía se encuentra -0.4566") 

    parser.add_argument('--FIX'                , type=str  , default=['epsilon'], nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--FIX_LON'            , type=int  , default=[1], nargs='*', help="número de ternas para cada variable en FIX")
    parser.add_argument('--FIX_LIMITES'        , type=str  , default=[0,1.0,1.0] , nargs='*', help="una terna para cada variable: indice,valor inferior,valor superior; '*' = criterio general, cualquier 'str' el valor inicial")

    parser.add_argument('--UTILIDAD_DEMANDA'   , type=int  , default=0       , help="0: Cobb Douglas; 1: CES")
    parser.add_argument('--SIGMA_CES_DEMANDA'  , type=float, default=[2., 2., 2.], nargs='*', help="sigma de la función de demanda CES")
    parser.add_argument('--MODO_PSEUDOIMPTOS'  , type=int  , default=0       , help="0: variables según cambian las cotizaciones a la seguridad social y las ayudas del gobierno; 1: fijos iguales a los que resultam de la MCS")

    parser.add_argument('--SAL_CALIBRADO'      , type=sab  , default=False , help="imprimir los valores de los parámetros calibrados")
    parser.add_argument('--SALIDA_VEC_OPT'     , type=sab  , default=False , help="salida de los valores iniciales de las variables y sus límites")
    parser.add_argument('--SALIDA_VAL_INI'     , type=sab  , default=True  , help="informe de los valores iniciales de las variables")
    parser.add_argument('--PRIMERA_VALORACION' , type=sab  , default=False , help="calcular una primera valoración de modelo")
    parser.add_argument('--SALIDA_DESVIOS'     , type=sab  , default=False , help="salida con el detalla de las desviaciones")
    parser.add_argument('--SAL_AUXILIARES'     , type=sab  , default=False , help="imprimir los valores del historial y la evolución de la solución")
    parser.add_argument('--SAL_GRAFICOS_EVOL'  , type=sab  , default=False , help="generar gráficos de las evoluciones")
    parser.add_argument('--SAL_GRAFICO_CES_DM' , type=sab  , default=False , help="generar graficos de isocuantas CES")
    parser.add_argument('--SAL_ISOCUANTA'      , type=sab  , default=False , help="generar gráficos adicionales de isocuantas")
    parser.add_argument('--SAL_VARIACIONES'    , type=sab  , default=True  , help="imprime las diferencias entre los valores iniciales y finales de las variables")
    parser.add_argument('--SAL_MCS'            , type=sab  , default=True  , help="imprime la MCS")
    parser.add_argument('--SAL_VAR_MCS'        , type=sab  , default=True  , help="imprime las diferencias entre los valores iniciales y finales de la MCS")

    parser.add_argument('--GE_INCLUYE_XP'      , type=sab  , default=False, help="incluir Xp en el vector solución")
    parser.add_argument('--GE_RESTRICCIONES'   , type=sab  , default=False , help="restricciones en cantidad de importación (M) y exportación (E)")
    parser.add_argument('--GE_TIPO_RE'         , type=int  , default=1     , help="0: lineal; 1: No lineal")
    parser.add_argument('--GE_TOLERANCIA'      , type=float, default=1.e-12, help="límite para considerar el objetivo alcanzado o que no hay progreso")
    parser.add_argument('--GE_VERIFICAR'       , type=float, default=1.e-08, help="límite para considerar que la ecuación se cumple")
    # GE_PROGRESO tiene su importancia porque la minimización puede terminar si tras GE_PROGRESO generaciones no mejora al menos GE_TOLERANCIA
    # Si GE_PROGRESO es demasiado pequeño, la minimización puede terminar incorrectamente porque no ha tenido tiempo de progresar
    parser.add_argument('--GE_PROGRESO'        , type=int  , default=10000  , help="número de generaciones para comprobar el progreso")
    parser.add_argument('--GE_MIN_PROGRESO'    , type=float, default=0.05   , help="% de mejora mínima para considerar que hay progreso")
    parser.add_argument('--GE_HISTORIAL'       , type=int  , default=10000  , help="número de generaciones para mostrar evolución y en su caso salvar el historial")
    parser.add_argument('--GE_SOLUCIONES'      , type=int  , default=100000 , help="número de generaciones para salvar la solución")
    parser.add_argument('--GE_MAX_ITER'        , type=int  , default=2000000, help="máximo número de generaciones a simular")
    '''
    parser.add_argument('--GE_PRE_MIN'         , type=float, default=2.0   , help="el límite inferior del rango de variación de los precios es su valor inicial dividido por GE_PRE_MIN")
    parser.add_argument('--GE_PRE_MAX'         , type=float, default=2.0   , help="el límite superior del rango de variación de los precios es su valor inicial multiplicado por GE_PRE_MAX")
    parser.add_argument('--GE_VAR_MIN'         , type=float, default=4.0   , help="el límite inferior del rango de variación de las variables es su valor inicial dividido por GE_VAR_MIN")
    parser.add_argument('--GE_VAR_MAX'         , type=float, default=4.0   , help="el límite superior del rango de variación de las variables es su valor inicial multiplicado por GE_VAR_MAX")
    '''
    parser.add_argument('--GE_PRE_MIN'         , type=float, default=95.0  , help="el límite inferior del rango de variación de los precios es su valor inicial por   (1 - GE_PRE_MIN/100)")
    parser.add_argument('--GE_PRE_MAX'         , type=float, default=95.0  , help="el límite superior del rango de variación de los precios es su valor inicial por   (1 + GE_PRE_MAX/100)")
    parser.add_argument('--GE_VAR_MIN'         , type=float, default=95.0  , help="el límite inferior del rango de variación de las variables es su valor inicial por (1 - GE_PRE_MIN/100)")
    parser.add_argument('--GE_VAR_MAX'         , type=float, default=95.0  , help="el límite superior del rango de variación de las variables es su valor inicial por (1 + GE_PRE_MAX/100)")

    parser.add_argument('--GE_VAR_CERO'        , type=float, default=20000.0 ,help="si el valor inicial de una variable es cero su rango de variación es [-GE_VAR_CERO, +GE_VAR_CERO]")
    parser.add_argument('--GE_VAR_CAN_MIN'     , type=float, default=8000.0  ,help="rango de variación mínimo para una variable")
    parser.add_argument('--GE_ACTUALIZACION'   , type=str  , default='immediate', help="cada vez que se cambia un individuo")
    parser.add_argument('--GE_RECONBINACION'   , type=float, default=0.99    , help="recombinación")
    parser.add_argument('--GE_DIM_POBLACION'   , type=int  , default=5       , help="factor para establecer el tamaño de la población (por defecto es 15) individuos = GE_DIM_POBLACION * len(vec_opt)")
    parser.add_argument('--GE_IMG_FIL'         , type=int  , default=5       , help="número de filas del mapa de gráficos con la evolución de los precios y las variables")
    parser.add_argument('--GE_IMG_COL'         , type=int  , default=6       , help="número de columnas del mapa de gráficos con la evolución de los precios y las variables")
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
    parser.add_argument('--OPT_DESVIOS'        , type=int  , default=1       , help="0: incluye desvíos redundantes, ¿puede mejorar los resultados?")
    '''
    el resultado de la función a minimizar lo determina la METRICA_ERROR y es:
        0: la suma del cuadrado de los desvios de cada una de las variables
        1: la suma de los valores absolutos de los desvios de cada una de las variables
        2: la suma de los desvios de cada una de las variables elevada a POT_DESVIOS, si el desvio es negatino se toma el valor absoluto
    '''
    parser.add_argument('--METRICA_ERROR'      , type=int  , default=0     , help="métrica del error: 0=cuadrado; 1=absoluto; 2=elevado a POT")
    parser.add_argument('--POT_DESVIOS'        , type=int  , default=2     , help="solo se usa en el caso de METRICA_ERROR = 2")
    parser.add_argument('--PRECIO_INI'         , type=float, default=0.9   , help="para el caso 5 'pre_ini'")
    parser.add_argument('--FACTOR_CSSH'        , type=float, default=[1.0, 1.0, 1.0] , nargs='*', help="para afectar los coeficientes de la seguridad social de los hohares, caso 8")
    parser.add_argument('--FACTOR_CSSE'        , type=float, default=[]    , nargs='*', help="para afectar los coeficientes de la seguridad social de las empresas, caso 8")
    parser.add_argument('--F_CSSE_LON'         , type=int  , default=0     , help="número de coeficientes de la seguridad social")
    parser.add_argument('--F_CSSE'             , type=float, default=[3,1.0] , nargs='*', help="coeficientes de la seguridad social para el sector indicado")
    '''
    factores aportados adicionales para el caso 6, si se especifica un solo valor (escalar) se afectan todos por él
    '''
    parser.add_argument('--VAR_FACTORES'       , type=float, default=[0., 0., 0., 0., 0., 0.], nargs='*', help="factores aportados adicionales para el caso 6.")
    parser.add_argument('--SIGMA_ESCENARIO'    , type=float, default=[]    , nargs='*', help="valor de sigma para el escenario 13")
    parser.add_argument('--SIGMA_ESCE_LON'     , type=int  , default=0     , help="número de sigmas")
    parser.add_argument('--SIGMA_ESCE'         , type=int  , default=[2,2.0] , nargs='*', help="para el sector valor de sigma ")

    parser.add_argument('--SENDA_DATOS'        , type=str  , default='C:/MEGA/Datos'   , help="debe existir")
    parser.add_argument('--SENDA_SALIDAS'      , type=str  , default='C:/MEGA/Salidas' , help="senda para las salidas")
    parser.add_argument('--SENDA_GRAFICOS'     , type=str  , default='C:/MEGA/Graficos', help="senda para los gráficos")
    parser.add_argument('--SENDA_SOLUCIONES'   , type=str  , default='C:/MEGA/Soluciones', help="senda para los vectores solución")
    parser.add_argument('--SENDA_DLL'          , type=str  , default='C:/MEGA/MEGA_DLL/x64/Release/MEGA_DLL.dll', help="senda para la DLL")
    args = parser.parse_args()
    return args

def valores_opciones6():
    parser = argparse.ArgumentParser()
    '''
    las matrices se especifican aplanadas como vectores.

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
        'dem_alfa',             #  9 simplemente cambia la preferencia de los consumos, no se añade demanda porque duplicaría el efecto en los productos
    usar el caso 0 para ayudas no es equivalente al caso 10 porque las ayudas no van destinadas de forma diferenciada a los productos, para esto
    hay que modificar los alfa que es lo que hace el caso 10  
        'alfa_ayudas',          # 10
        'sigma',                # 11
        'aranceles',            # 12
        'Xp0',                  # 13 consumos esenciales = Xp0
        'Xp0m1',                # 14 consumos esenciales = Xp0 - 1

    ALGE_MODO_POB_INI
    *** 0   "intervalo simétrico centrado en 'vec_ini' con distribución uniforme",
        1   "centrado en el centro de intervalo de validez de la variable con distribución uniforme",
        2   "intervalo simétrico centrado en 'vec_ini' con distribución normal",
        3   "centrado en el centro de intervalo de validez de la variable con distribución normal",
        4   "Latin Hypercube Sampling con permutaciones distintas para cada variable",
        5   "Latin Hypercube Sampling con la misma permutación para todas las variables",
        6   "secuencia de valores uniformemente espaciados entre cotas y permutaciones distintas para cada variable",
	    7   "secuencia de valores uniformemente espaciados entre cotas y la misma permutación para todas las variables",
        8   "valores próximos al extremo inferior del entorno de existencia de las variables, con permutaciones distintas para cada variable",
    *** 9   "valores próximos al extremo inferior del entorno de existencia de las variables, con la misma permutación para todas las variables",
        10  "valores próximos al extremo superior del entorno de existencia de las variables",
        11  'valores próximos a los extremos de los entornos de existencia de las variables',
    *** 12  'valores próximos, o iguales, al extremo inferior del entorno de existencia de las variables, con permutaciones distintas para cada variable',
        13  'valores próximos, o iguales, al extremo inferior del entorno de existencia de las variables',
        14  'valores próximos, o iguales, al extremo superior del entorno de existencia de las variables, con permutaciones distintas para cada variable'
        15  'valores próximos, o iguales, al extremo inferior, con permutaciones distintas para cada variable y desplazamiento independiente',
    '''
    # si PREFIJO empieza con el caracter '=' los caracteres del 1 en adelante se usarán como nombre de los ficheros de salida en
    # lugar de componerlos a partir de las opciones seleccionadas, en este caso NO puede haber ESPACIOS en blanco intercalados
    parser.add_argument('--PREFIJO'            , type=str  , default='=PP' , help="un literal que se añade al principio del nombre de los archivos de salida, o el propio nombre si empieza con el caracter '='")
    parser.add_argument('--ALGE_MODO_POB_INI'  , type=int  , default=9      , help="de 0 a 15 formas de generar la población inicial")
    parser.add_argument('--ALGE_ID_SALIDA'     , type=int  , default=9999   , help="")
    parser.add_argument('--GE_SEMILLA'         , type=int  , default=17555  , help="valor inicial del generador de números aleatorios")

    parser.add_argument('--GE_WORKERS'         , type=int  , default=1      , help="número de procesadores a utilizar si no se usa el algoritmo genético de la DLL (en esta máquina el máximo es 61 y el óptimo 32)")
    parser.add_argument('--DESV_RELATIVA'      , type=int  , default=1      , help="1: desviaciones en términos relativos, tanto por uno")
    # GE_PROGRESO tiene su importancia porque la minimización puede terminar si tras GE_PROGRESO generaciones no mejora al menos GE_MIN_PROGRESO
    # Si GE_PROGRESO es demasiado pequeño, la minimización puede terminar incorrectamente porque no ha tenido tiempo de progresar
    parser.add_argument('--GE_PROGRESO'        , type=int  , default=10000  , help="número de generaciones para comprobar el progreso")
    parser.add_argument('--GE_MIN_PROGRESO'    , type=float, default=0.05   , help="% de mejora mínima para considerar que hay progreso")
    parser.add_argument('--USAR_DLL'           , type=sab  , default=True   , help="si True se usa la función objetivo de la DLL, en caso contrario la función Python")
    parser.add_argument('--USAR_ALGE_DLL'      , type=sab  , default=True   , help="si True se usa el algoritmo genético de la DLL")
    parser.add_argument('--ALGE_MAX_INTENTOS'  , type=int  , default=4      , help="número máximo de veces que se reinician los calculos, desde una nueva población inicial, si no se alcanza el objetico")
    parser.add_argument('--ALGE_N_HILOS'       , type=int  , default=20     , help="número de procesos simultáneos")
    parser.add_argument('--ALGE_TOL_ACEPTABLE' , type=float, default=1.e-03 , help="valor del error de la función objetivo por debajo del cual se considera una solución aceptable, si no se ha podido alcanzar el objetivo GE_TOLERANCIA, no interviene el los cálculos, solo se usa a efectos informativos")
    parser.add_argument('--ALGE_F_INICIO_POB'  , type=float, default=0.0008, help="factor de alcance para generar de la población inicial")
    parser.add_argument('--ALGE_SIGMA_POB_INI' , type=float, default=0.75  , help="sigma de la distribución normal para generar de la población inicial")
    parser.add_argument('--ALGE_TRAMOS_LHS'    , type=int  , default=400   , help="Tnúmero de tramos en los que se divide el intervalo de existencia de las variables para generar sus valores en la población inicial")
    parser.add_argument('--ALGE_NPOB'          , type=int  , default=4400  , help="Número de individuos en la población")
    parser.add_argument('--ALGE_F_MUTACION'    , type=float, default=0.80  , help="factor de mutación")
    parser.add_argument('--ALGE_RECOMBINACION' , type=float, default=[0.99 , 1.10], nargs='*', help="constante de recombinación, se modifica aleatoriamente entre los dos valores aportados")
    parser.add_argument('--ALGE_CTRL_FACTIBLE' , type=int  , default=1     , help="1: Controlar que los valores de las variables tras el cruce están dentro de sus rangos de validez")
    parser.add_argument('--ALGE_RES_EXTENSA'   , type=int  , default=0     , help="La DLL devuelve: 0= el vector solución y el detalle de los devios; 1= el valor de todas las variables")
    parser.add_argument('--EL_MEJOR_PRIMERO'   , type=int  , default=0     , help="recolocar el mejor individuo en la posición 0 de la matriz de población. No sirve de nada")
    parser.add_argument('--ALGE_INCLUIR_X0'    , type=int  , default=1     , help="incluir en la población en vector de prueba inicial")

    parser.add_argument('--NSAM'               , type=int  , default=6     , help="Matriz de Contabilidad Social a utilizar, ver 'etq_sam'")
    parser.add_argument('--DECIMALES'          , type=int  , default=1     , help="número de decimales en las cantidades e importes")
    # aunque NFAC, NDEM y NSEC se establecen el la definición de cada MCS, tenemos que especificarlos aquí porque los vamos a necesitar para redimensionar las matrices aplanadas antes
    # de llegar a la definición de la MCS
    parser.add_argument('--NFAC'               , type=int  , default=2     , help="número de factores")
    parser.add_argument('--NDEM'               , type=int  , default=2     , help="número de hogares")
    parser.add_argument('--NSEC'               , type=int  , default=31    , help="número de sectores")

    parser.add_argument('--NCASO'              , type=int  , default=[0]   , nargs='*', help="número de esenario a utilizar, se pueden combinar varios, por ejemplo default=[0,14], atención al orden")
    parser.add_argument('--FI_SOL_LEE'         , type=str  , default=''    , help="la senda de un fichero de texto con el vector solución a probar, en lugar del que se obtiene de la MCS")
    parser.add_argument('--FI_SOL_SALVA'       , type=str  , default=''    , help="la senda del fichero de texto donde guardar el vector solución obtenido")

    parser.add_argument('--EQ_BAL_PAGOS'       , type=sab  , default=True  , help="si True se exige que el importe de la balanza de pagos se amntenga constante e igual a la de la MCS, lo contrario es incoherente")
    parser.add_argument('--PRECIO_IMPORTACION' , type=float, default=[], nargs='*', help="precio inicial de importación de determinados productos, parejas: índice, precio")

    # Para ver los efectos de la demanda adicional lo apropiado es usar NCASO = 0
    parser.add_argument('--DEM_ADICIONAL_TIPO' , type=int  , default=0     , help="0: se añade 'DEM_ADICIONAL' al importe demandado; 1: se añade 'DEM_ADICIONAL' a la cantidad demandada")
    parser.add_argument('--DEM_AD_LON'         , type=int  , default=1     , help="número de demandas adicionales exógenas de productos para los hogares")
    parser.add_argument('--DEM_AD_HO_PRO'      , type=float, default=[1,4,1000.], nargs='*', help="demanda adicional exógena del hogar para el producto")
    parser.add_argument('--RENTA_FICTICIA'     , type=sab  , default=False , help="si True no se proveerán fondos para los incrementos de demanda, es un caso incoherente")
    
    # Para ver los efectos de las ayudas lo apropiado es usar NCASO = 10
    parser.add_argument('--AYD_AD_LON'         , type=int  , default=0    , help="número de ayudas exógenas de productos para los hogares")
    parser.add_argument('--AYD_AD_HO_PRO'      , type=float, default=[1, 14, 1000.], nargs='*', help="para el 'hogar' y el 'producto' la 'ayuda' exógena")

    # 'CON_ESENCIALES' cantidades de consumos esenciales. Si DEM_ESENCIALES = False, simplemente se usan como el valor mínimo de las compras, sin usar la función de demanda Stone-Geary
    parser.add_argument('--CON_AD_LON'         , type=int  , default=0    , help="número de consumos esenciales exógenos de productos para los hogares")
    parser.add_argument('--CON_AD_HO_PRO'      , type=float, default=[0, 10, 1000.], nargs='*', help="el 'hogar' del 'producto' tiene un 'consumo' esencial")
    parser.add_argument('--DEM_ESENCIALES'     , type=sab, default=False, help="True: usar los 'CON_ESENCIALES' en el cálculo de productos demandados (Stone-Geary)")

    parser.add_argument('--ARANCELES_LON'      , type=int  , default=0    , help="número de aranceles a modificar")
    parser.add_argument('--ARANCELES_PRO'      , type=float, default=[14, 0.01], nargs='*', help="producto, arancel")

    parser.add_argument('--FF_ENDOGENA'        , type=sab  , default=True , help="las aportaciones de factores por los hogares pueden ser variables endogenas o exogenas")
    parser.add_argument('--ALP_FACTOR'         , type=float, default=0.0  , help="tanto por uno de los excesos de factores aportados, sobre sus valores iniciales, que se lleva a la cuenta Alp") 
    '''
    cuando FF_ENDOGENA, hay que especificar
        OR_PRE_EXCLUIDO   = 0
        PRECIO_F_EXCLUIDO = 1.0
        VALOR_F_TRA         = 1.0 salvo que el precio del trabajo se quiera como endógeno en cuyo caso VALOR_F_TRA = 0

    si (OR_PRE_EXCLUIDO=0) el precio del capital (PRECIO_F_EXCLUIDO) es exogeno = 1.0 y no formará parte del vector solución
    parser.add_argument('--OR_PRE_EXCLUIDO'  , type=int  , default=0, help="factor de referencia = ordinal (columna de h, empezando en 0) del precio para el que se fija el valor 'PRECIO_F_EXCLUIDO'")
    parser.add_argument('--PRECIO_F_EXCLUIDO', type=float, default=1.0   , help="precio que se fija para el factor de referencia")
    
    si OR_PRE_EXCLUIDO = 0 el precio del trabajo formará parte del vector solución, puede ser:
        endogeno : si VALOR_F_TRA = -1
        fijo     : será acotado al valor VALOR_F_TRA si es > 0
        calculado: si VALOR_F_TRA = 0
    '''
    parser.add_argument('--OR_PRE_EXCLUIDO'    , type=int  , default=0    , help="factor de referencia = ordinal (columna de h, empezando en 0) del precio para el que se fija el valor 'PRECIO_F_EXCLUIDO'")
    parser.add_argument('--PRECIO_F_EXCLUIDO'  , type=float, default=1.0  , help="precio que se fija para el factor de referencia")
    parser.add_argument('--VALOR_F_TRA'        , type=float, default=1.05   , help="precio que se fija para el factor trabajo; -1 : no se fija valor, 0 : curva Phillips")
    parser.add_argument('--PARO_INICIAL'       , type=float, default=0.10 , help="tanto por uno de paro para la curva Phillips")
    parser.add_argument('--ALFA_PHILLIPS'      , type=float, default=-0.5 , help="relación desempleo salarios, en la bibliografía se encuentra -0.4566") 

    parser.add_argument('--FIX'                , type=str  , default=['epsilon'], nargs='*', help="variables para las que se fijan los límites inferior y superior expresamente")
    parser.add_argument('--FIX_LON'            , type=int  , default=[1], nargs='*', help="número de ternas para cada variable en FIX")
    parser.add_argument('--FIX_LIMITES'        , type=str  , default=[0,1.,1.] , nargs='*', help="una terna para cada variable: indice,valor inferior,valor superior; '*' = criterio general, cualquier 'str' el valor inicial")

    parser.add_argument('--UTILIDAD_DEMANDA'   , type=int  , default=0       , help="0: Cobb Douglas; 1: CES")
    parser.add_argument('--SIGMA_CES_DEMANDA'  , type=float, default=[2., 2.], nargs='*', help="sigma de la función de demanda CES")
    parser.add_argument('--MODO_PSEUDOIMPTOS'  , type=int  , default=0       , help="0: variables según cambian las cotizaciones a la seguridad social y las ayudas del gobierno; 1: fijos iguales a los que resultam de la MCS")

    parser.add_argument('--SAL_CALIBRADO'      , type=sab  , default=False  , help="imprimir los valores de los parámetros calibrados")
    parser.add_argument('--SALIDA_VEC_OPT'     , type=sab  , default=False  , help="salida de los valores iniciales de las variables y sus límites")
    parser.add_argument('--SALIDA_VAL_INI'     , type=sab  , default=True  , help="informe de los valores iniciales de las variables")
    parser.add_argument('--PRIMERA_VALORACION' , type=sab  , default=True  , help="calcular una primera valoración de modelo")
    parser.add_argument('--SALIDA_DESVIOS'     , type=sab  , default=True  , help="salida con el detalla de las desviaciones")
    parser.add_argument('--SAL_AUXILIARES'     , type=sab  , default=False  , help="imprimir los valores del historial y la evolución de la solución")
    parser.add_argument('--SAL_GRAFICOS_EVOL'  , type=sab  , default=False  , help="generar gráficos de las evoluciones")
    parser.add_argument('--SAL_GRAFICO_CES_DM' , type=sab  , default=False  , help="generar graficos de isocuantas CES")
    parser.add_argument('--SAL_ISOCUANTA'      , type=sab  , default=False  , help="generar gráficos adicionales de isocuantas")
    parser.add_argument('--SAL_VARIACIONES'    , type=sab  , default=True   , help="imprime las diferencias entre los valores iniciales y finales de las variables")
    parser.add_argument('--SAL_MCS'            , type=sab  , default=True   , help="imprime la MCS")
    parser.add_argument('--SAL_VAR_MCS'        , type=sab  , default=True   , help="imprime las diferencias entre los valores iniciales y finales de la MCS")

    parser.add_argument('--GE_INCLUYE_XP'      , type=sab  , default=False  , help="incluir Xp en el vector solución")
    parser.add_argument('--GE_TOLERANCIA'      , type=float, default=1.e-13 , help="límite para considerar el objetivo alcanzado")
    parser.add_argument('--GE_VERIFICAR'       , type=float, default=1.e-06 , help="límite para considerar que una ecuación se cumple")
    parser.add_argument('--GE_HISTORIAL'       , type=int  , default=10000  , help="número de generaciones para mostrar evolución y en su caso salvar el historial")
    parser.add_argument('--GE_SOLUCIONES'      , type=int  , default=3000000, help="número de generaciones para salvar la solución")
    parser.add_argument('--GE_MAX_ITER'        , type=int  , default=0, help="máximo número de generaciones a simular")
    parser.add_argument('--GE_PRE_MIN'         , type=float, default=90.0   , help="el límite inferior del rango de variación de los precios es su valor inicial por   (1 - GE_PRE_MIN/100)")
    parser.add_argument('--GE_PRE_MAX'         , type=float, default=99.0   , help="el límite superior del rango de variación de los precios es su valor inicial por   (1 + GE_PRE_MAX/100)")
    parser.add_argument('--GE_VAR_MIN'         , type=float, default=90.0   , help="el límite inferior del rango de variación de las variables es su valor inicial por (1 - GE_PRE_MIN/100)")
    parser.add_argument('--GE_VAR_MAX'         , type=float, default=90.0   , help="el límite superior del rango de variación de las variables es su valor inicial por (1 + GE_PRE_MAX/100)")
    parser.add_argument('--GE_VAR_CERO'        , type=float, default=20000. ,help="si el valor inicial de una variable es cero su rango de variación es [-GE_VAR_CERO, +GE_VAR_CERO]")
    parser.add_argument('--GE_VAR_CAN_MIN'     , type=float, default=8000.  ,help="rango de variación mínimo para una variable")
    # solo para scipy ->
    parser.add_argument('--GE_RESTRICCIONES'   , type=sab  , default=False  , help="restricciones en cantidad de importación (M) y exportación (E)")
    parser.add_argument('--GE_TIPO_RE'         , type=int  , default=1      , help="0: lineal; 1: No lineal")
    parser.add_argument('--GE_ACTUALIZACION'   , type=str  , default='immediate', help="cada vez que se cambia un individuo")
    parser.add_argument('--GE_RECONBINACION'   , type=float, default=0.99   , help="recombinación")
    parser.add_argument('--GE_DIM_POBLACION'   , type=int  , default=3      , help="factor para establecer el tamaño de la población (por defecto es 15) individuos = GE_DIM_POBLACION * len(vec_opt)")
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
    # <- solo para scipy
    parser.add_argument('--GE_IMG_FIL'         , type=int  , default=5      , help="número de filas del mapa de gráficos con la evolución de los precios y las variables")
    parser.add_argument('--GE_IMG_COL'         , type=int  , default=6      , help="número de columnas del mapa de gráficos con la evolución de los precios y las variables")
    parser.add_argument('--OPT_DESVIOS'        , type=int  , default=1      , help="0: incluye desvíos redundantes, ¿puede mejorar los resultados?")
    '''
    el resultado de la función a minimizar lo determina la METRICA_ERROR y es:
        0: la suma del cuadrado de los desvios de cada una de las variables
        1: la suma de los valores absolutos de los desvios de cada una de las variables
        2: la suma de los desvios de cada una de las variables elevada a POT_DESVIOS, si el desvio es negatino se toma el valor absoluto
    '''
    parser.add_argument('--METRICA_ERROR'      , type=int  , default=0      , help="métrica del error: 0=cuadrado; 1=absoluto; 2=elevado a POT")
    parser.add_argument('--POT_DESVIOS'        , type=int  , default=2      , help="solo se usa en el caso de METRICA_ERROR = 2")
    
    parser.add_argument('--PRECIO_INI'         , type=float, default=0.6    , help="para el caso 5 'pre_ini'")
    parser.add_argument('--FACTOR_CSSH'        , type=float, default=[1.0, 1.0] , nargs='*', help="para afectar los coeficientes de la seguridad social de los hohares, caso 8")
    parser.add_argument('--FACTOR_CSSE'        , type=float, default=[]     , nargs='*', help="para afectar los coeficientes de la seguridad social de las empresas, caso 8")
    parser.add_argument('--F_CSSE_LON'         , type=int  , default=0      , help="número de pares con el sector y su coeficiente de la seguridad social")
    parser.add_argument('--F_CSSE'             , type=float, default=[3,1.0] , nargs='*', help="pares número de sector y su coeficiente de la seguridad social")
    '''
    factores aportados adicionales para el caso 6, si se especifica un solo valor (escalar) se afectan todos por él
    '''
    parser.add_argument('--VAR_FACTORES'       , type=float, default=[0., 0., 0., 0.], nargs='*', help="factores aportados adicionales para el caso 6.")
    parser.add_argument('--SIGMA_ESCENARIO'    , type=float, default=[]     , nargs='*', help="valor de sigma para el escenario 13")
    parser.add_argument('--SIGMA_ESCE_LON'     , type=int  , default=0      , help="número de sigmas")
    parser.add_argument('--SIGMA_ESCE'         , type=int  , default=[2,2.0], nargs='*', help="par para el sector y su valor de sigma")

    parser.add_argument('--SENDA_DATOS'        , type=str  , default='C:/MEGA/Datos'   , help="debe existir")
    parser.add_argument('--SENDA_SALIDAS'      , type=str  , default='C:/MEGA/Salidas' , help="senda para las salidas")
    parser.add_argument('--SENDA_GRAFICOS'     , type=str  , default='C:/MEGA/Graficos', help="senda para los gráficos")
    parser.add_argument('--SENDA_SOLUCIONES'   , type=str  , default='C:/MEGA/Soluciones', help="senda para los vectores solución")
    # el valor de 'SENDA_DLL' es testimonial, ya que la senda de la DLL se establece en la definición de cada MCS porque hay DLLs distintas según el número de hogares y sectores
    parser.add_argument('--SENDA_DLL'          , type=str  , default='C:/MEGA/MEGA_DLL/x64/Release/MEGA_DLL.dll', help="senda para la DLL")
    args = parser.parse_args()
    return args
