
'''

PRECIO_INI  = 0.5                               # para el caso 5 'pre_ini'
FACTOR_CSSH = [0.95, 1.0]                       # para afectar los coeficientes de la seguridad social de los hohares, caso 8
FACTOR_CSSE = [1.0 , 1.0, 1.0, 1.0, 1.0, 1.0]   # para afectar los coeficientes de la seguridad social de las empresas, caso 8

# factores aportados adicionales para el caso 6, si se especifica un solo valor (escalar) se afectan todos por él.
# su forma varia con la SAM correspondiente, en función del número de hogares y factores.
VAR_FACTORES = np.array([
    [0., 0.],
    [0., 0.],
])
VAR_FACTORES = 1.1
# para el caso 11, participación del valor añadido sobre la producción de cada sector para calcular 
# la variación adicional exógena de factores, derivada del incremento de la demanda 'DEM_ADICIONAL'
# su forma varia con la SAM correspondiente, en función del número de sectores.
COE_VAB = np.array([0.590982516,0.256023902,0.231881481,0.299890544,0.567089808,0.669947953])

# demanda adicional exógena de productos (columna) por consumidor (fila).
# su forma varia con la SAM correspondiente, en función del número de hogares y productos.
DEM_ADICIONAL      = np.array([
    [0., 0.,    0., 0., 0., 0.],
    [0., 0., 1000., 0., 0., 0.],
])
DEM_ADICIONAL_TIPO = 0  # 0: se añade 'DEM_ADICIONAL' al importe demandado; 1: se añade 'DEM_ADICIONAL' a la cantidad demandada

# ayuda adicional exógena por consumidor (fila) y producto (columna), en importe
# su forma varía con la SAM correspondiente, en función del número de hogares y sectores.
AYD_ADICIONAL = np.array([
    [0.,0.,    0.,0.,0.,0.],
    [0.,0.,    0.,0.,0.,0.],
])

# valor de sigma para el escenario 13
SIGMA_ESCENARIO = np.array(
    [4.,2.,2.,2.,2.,2.], dtype=np.float64
)
# para el caso 14
ARANCELES = np.array(
    [0., 0., 0.003825, 0., 0., 0.], dtype=np.float64
)


PREFIJO = ''                    # un literal que se añade al principio del nombre de los archivos de salida
NSAM  = 3                       # Matriz de Contabilidad Social a utilizar, ver 'etq_sam'
NCASO = [0, 14]                # número de esenario a utilizar, ver 'etq_caso', se pueden combinar varios
#NCASO = [0]                    # número de esenario a utilizar, ver 'etq_caso', se pueden combinar varios
'''
'''
Hay dos formas de convertir una variable endógena en exógena con un valor prefijado:
    1. Darle un valor y no incluirla en el vector de soluciones a probar.
    2. Establecer los valores mínimos y máximos que puede adoptar en el mismo valor.
a continuación se usan ambos casos:
    1. OR_PRE_REFERENCIA y PRECIO_F_REFERENCIA corresponden a la forma 1
    2. VALOR_F_TRA se usa de la forma 2

En la versión FF_ENDOGENA hay que fijar el valor de 3 variables, lo más cómodo es hacer:

        OR_PRE_REFERENCIA   = 0
        PRECIO_F_REFERENCIA = 1.0
        VALOR_F_TRA         = 1.0
    para fijar 2 de ellas : precios del capital y trabajo

        GE_FIX              = ['epsilon']
        GE_FIX_LIMITES      = [ [ [1.0, 1.0] ]
    para fijar la tercera variable: cotización moneda local/extranjera

OR_PRE_REFERENCIA   = 0         # factor de referencia = ordinal (columna de h, empezando en 0) del precio para el que se fija el valor 'PRECIO_F_REFERENCIA'
PRECIO_F_REFERENCIA = 1.0       # precio que se fija para el factor de referencia
VALOR_F_TRA         = 1.0       # precio que se fija para el factor trabajo; -1 : no se fija el valor del precio del trabajo
FF_ENDOGENA         = True      # Las aportaciones de factores por los hogares pueden ser variables endogenas o exogenas
AHORRO_L_PLAZO      = True      # llevar a la cuenta ALP (Ahorro Largo Plazo) los excesos de factores aportados sobre sus valores iniciales
OPT_DESVIOS         = 0         # 0 : incluye desvíos redundantes, suele mejorar los resultados y acelerar la convergencia

PRIMERA_VALORACION  = False     # calcular una primera valoración de modelo
SAL_CALIBRADO       = False     # imprimir los valores de los parámetros calibrados
SALIDA_VEC_OPT      = False     # salida de los valores iniciales de las variables y sus límites
SALIDA_DESVIOS      = False     # salida con el detalla de las desviaciones
SAL_AUXILIARES      = True      # imprimir los valores del historial y la evolución de la solución
SAL_GRAFICOS_EVOL   = True      # generar gráficos de las evoluciones
SAL_GRAFICO_CES_DM  = False     # generar graficos de isocuantas CES
SAL_ISOCUANTA       = False     # generar gráficos adicionales de isocuantas
SAL_VARIACIONES     = True      # imprime las diferencias entre los valores iniciales y finales de las variables 
#--------------------------------------------------------------------------------------------------------------------------------------------
GE_RESTRICCIONES   = False      # restricciones en cantidad de importación (M) y exportación (E)
GE_TIPO_RE         = 0          # 0: lineal; 1: No lineal

GE_PRE_MIN         = 3.0        # el límite inferior del rango de variación de los precios es su valor inicial dividido por GE_PRE_MIN 
GE_PRE_MAX         = 3.0        # el límite superior del rango de variación de los precios es su valor inicial multiplicado por GE_PRE_MAX

GE_VAR_MIN         = 9.0        # el límite inferior del rango de variación de las variables es su valor inicial dividido por GE_VAR_MIN 
GE_VAR_MAX         = 9.0        # el límite superior del rango de variación de las variables es su valor inicial multiplicado por GE_VAR_MAX 
GE_VAR_CERO        = 10000.      # si el valor inicial de una variable es cero su rango de variación es [-GE_VAR_CERO, +GE_VAR_CERO]
'''
'''
GE_FIX             = ['M']       # variables para las que se fijan los límites inferior y superior expresamente
GE_FIX_LIMITES     = [           # una fila para cada variable; una pareja para cada indice de la variable; '*' = criterio general, cualquier 'str' el valor inicial
    [ ['*','*'], ['*','*'], ['M0','M0'], ['*','*'], ['*','*'], ['*','*'] ]
]
GE_FIX             = ['M']       # variables para las que se fijan los límites inferior y superior expresamente
GE_FIX_LIMITES     = [           # una fila para cada variable; una pareja para cada indice de la variable; '*' = criterio general, cualquier 'str' el valor inicial
    [ ['*','*'], ['*','*'], [191981.3,191981.3], ['*','*'], ['*','*'], ['*','*'] ]
]
GE_FIX             = ['M','E']  # variables para las que se fijan los límites inferior y superior expresamente
GE_FIX_LIMITES     = [          # una fila para cada variable; una pareja para cada indice de la variable; '*' = criterio general, cualquier 'str' el valor inicial
    [ ['*','*'], ['*','*'], ['M0','M0'], ['*','*'], ['*','*'], ['*','*'] ],
    [ ['*','*'], ['*','*'], ['E0','E0'], ['*','*'], ['*','*'], ['*','*'] ]
]
GE_FIX             = ['pF']     # variables para las que se fijan los límites inferior y superior expresamente
GE_FIX_LIMITES     = [          # una fila para cada variable; una pareja para cada indice de la variable; '*' = criterio general, cualquier 'str' el valor inicial
    [ [1.0, 1.0] ]
]
GE_FIX             = ['pY']     # variables para las que se fijan los límites inferior y superior expresamente
GE_FIX_LIMITES     = [          # una fila para cada variable; una pareja para cada indice de la variable; '*' = criterio general, cualquier 'str' el valor inicial
    [ ['*','*'], [1.0, 1.0], [1.0, 1.0], ['*','*'], ['*','*'], ['*','*'] ]
]
GE_FIX             = []         # no se modifican explicitamente los límites de ninguna variable
GE_FIX             = ['pY','epsilon']     # variables para las que se fijan los límites inferior y superior expresamente
GE_FIX_LIMITES     = [          # una fila para cada variable; una pareja para cada indice de la variable; '*' = criterio general, cualquier 'str' el valor inicial
    [ [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0] ],
    [ [1.0, 1.0] ]
]
GE_FIX             = ['epsilon']       # variables para las que se fijan los límites inferior y superior expresamente
GE_FIX_LIMITES     = [                      # una fila para cada variable; una pareja para cada indice de la variable; '*' = criterio general, cualquier 'str' el valor inicial
    [ [1.0, 1.0] ]
]
GE_FIX             = []         # no se modifican explicitamente los límites de ninguna variable

GE_FIX             = ['epsilon']       # variables para las que se fijan los límites inferior y superior expresamente
GE_FIX_LIMITES     = [                      # una fila para cada variable; una pareja para cada indice de la variable; '*' = criterio general, cualquier 'str' el valor inicial
    [ [1.0, 1.0] ]
]

GE_MAX_ITER        = 1000000    # máximo número de generaciones a simular
GE_ACTUALIZACION   = 'immediate'
GE_RECONBINACION   = 0.90
GE_DIM_POBLACION   = 5          # factor para establecer el tamaño de la población (por defecto es 15)
GE_WORKERS         = 32         # número de procesadores a utilizar (en esta máquina el máximo es 61 y el óptimo 32)
SEMAZAR = [42, 333, 1755, 1234, 7000, 933, 2255, 1515, 29]  # varios valores de la semilla para las pruebas, se selecciona una en la línea siguiente
GE_SEMILLA         = SEMAZAR[1] # valor inicial del generador de números aleatorios

GE_IMG_FIL         = 5          # número de filas del mapa de gráficos con la evolución de los precios y las variables
GE_IMG_COL         = 6          # número de columnas del mapa de gráficos con la evolución de los precios y las variables
'''
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

GE_ESTRATEGIA      = 'best1bin'
'''
'''
el resultado de la función a minimizar lo determina la METRICA_ERROR y es:
    0: la suma del cuadrado de los desvios de cada una de las variables
    1: la suma de los valores absolutos de los desvios de cada una de las variables
    2: la suma de los desvios de cada una de las variables elevada a POT_DESVIOS, si el desvio es negatino se toma el valor absoluto

METRICA_ERROR     = 0
POT_DESVIOS       = 2   # solo se usa en el caso de METRICA_ERROR = 2

SENDA_DATOS       = 'C:/MEGA/Datos'         # debe existir
SENDA_SALIDAS     = 'C:/MEGA/Salidas'
SENDA_GRAFICOS    = 'C:/MEGA/Graficos'
'''


