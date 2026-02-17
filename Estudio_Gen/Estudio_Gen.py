import os
import sys
import copy
import numpy as np
import random as az
from matplotlib import pyplot as plt
import pandas

CASO  = 5
SUFIJO = '_fin_'

# estas opciones pueden cambiar según el caso ---------------------------------------------------
NPOB = 16                           # número de individuos de la población (número de caminantes)
NVEC  = 2                           # 2 coordenadas
LPI = 0.1                           # longitud de paso para Monte Carlo
nLp = 0                             # para Monte Carlo sucesivo de paso variable
# -----------------------------------------------------------------------------------------------

ERROR_MAXIMO = np.float32(1.0e-05)  # para considerar alcanzado el objetivo
MAX_GENERACIONES = 154              # número máximo de generaciones (pasos) a simular
MUTACION  = np.float32(0.5)         # parámetro de mutación
RECOMBINA = np.float32(0.8)         # parámetro de recombinación
NORMALIZAR = False                  # normalizar las variaciones de las variablkes entre 0 y 1
FRECUENCIA_IMPRIMIR = 5             # cada cuantas iteraciones mostrar resultados
FRECUENCIA_GRAFICOS = 2             # cada cuantas iteraciones dibujar gráfico (solo NVEC = 2)
FRECUENCIA_LP       = 1             # cada cuantas iteraciones registrar la longitud de paso que resulta del genético
EVOLUCION = False                   # mostrar evolución de los cálculos

if   CASO == 0:
    '''
    el más sencillo, las dos ecueciones a cumplirse son:
        x = coefs[0]
        y = coefs[1]
    '''
    NVEC = 2
    
    # rango de variación de las coordenadas
    rango = np.array([
        [ 0.,   10.],
        [ 0.,   10.],
    ])
    # vector solución 
    objetivo = [
          6.,
          4.,
    ]
    objetivo = np.array(objetivo, dtype=np.float32)
    # en este caso, la solución es el punto que debe alcanzar el caminante
    coefs = [
        objetivo[0],
        objetivo[1],
    ]
    # semilla para iniciar el generador de números aleatorios, en forma de lista porque el
    # algoritmo genético se puede repetir automáticamente para todos los elementos de la lista
    semillas = [42]
    # longitud de paso del Monte Carlo
    LPI = 0.01
elif CASO == 1:
    '''
    como el CASO 0 pero con 6 variables 
        coor[i] = coefs[i]
    los coeficientes coinciden con el objetivo
    '''
    NPOB = 28
    NVEC = 6
    # rango de variación de las coordenadas
    rango = np.array([
        [ 0.,   10.],
        [30.,   50.],
        [ 5.,  100.],
        [10.,  200.],
        [ 0.,  500.],
        [ 0., 1000.]
    ])
    objetivo = [
          6.,
         35.,
         16.,
         90.,
        200.,
         40.
    ]
    objetivo = np.array(objetivo, dtype=np.float32)
    # la solución es el punto que debe alcanzar el caminante
    coefs = [
        objetivo[0],
        objetivo[1],
        objetivo[2],
        objetivo[3],
        objetivo[4],
        objetivo[5]
    ]
    semillas = [42]
    LPI = 0.01
elif CASO == 2:
    '''
    otro caso con dos variables
        x + y = coefs[0]
        x - y = coefs[1]
    '''
    NVEC = 2
    # rango de variación de las coordenadas
    rango = np.array([
        [1., 80.],
        [10., 30.]
    ])
    coefs = [
        60.,
        20.
    ]
    # la solución es el punto que debe alcanzar el caminante porque es la solución a las dos ecuaciones
    # (secx, secy) es la solución analítica, por tanto el objetivo
    secx = (coefs[0] + coefs[1]) / 2.
    secy = coefs[0] - secx
    objetivo = [
        secx,
        secy
    ]
    objetivo = np.array(objetivo, dtype=np.float32)
    # semilla para iniciar los números aleatorios
    semillas = [42]
elif CASO == 3:
    '''
    seguimos con 2 variables
        x = a * y**2
        y = x / b
    '''
    NVEC = 2
    coefs = [
        10.,
        20.
    ]
    # rango de variación de las coordenadas
    rango = np.array([
        [20., 50.],
        [1.0, 10.]
    ])
    # la solución es el punto que debe alcanzar el caminante porque es la solución a las dos ecuaciones
    # (secx, secy) es la solución analítica, por tanto el objetivo
    secx = (coefs[1] * coefs[1]) / coefs[0]
    secy = secx / coefs[1]
    objetivo = [
        secx,
        secy
    ]
    objetivo = np.array(objetivo, dtype=np.float32)
    semillas = [42]
elif CASO == 4:
    '''
    un caso más complicado de 2 variables, tiene dos soluciones.
    expresar las ecuaciones como igualdad a 0 es lo más cómodo para calcular la función objetivo
        x**2 + 2(x-y)**2 - 36 = 0
        x/2 + y/3         - 5 = 0
    soluciones:
        x,y = 162/23 = 7.04 , 102/23 = 4,43 
        x,y = 6, 6
    la única forma de dirigir el cálculo a uno u otra solución es a traves del rango de las variables
    '''
    NVEC = 2
    coefs = [
         2.,
       -36.,
         2.,
         3.,
        -5.
    ]
    # rango de variación de las coordenadas
    rango = np.array([
        [0.0, 10.],
        [6.5, 10.]
    ])
    # hay dos soluciones, por tanto dos objetivos
    objetivo = [
        [230./45., 330./45.],   # 5.11111, 7,33333
        [6.      , 6.      ]
    ]                       # la solución es el punto que debe alcanzar el caminante porque es la solución a las dos ecuaciones
    objetivo = np.array(objetivo, dtype=np.float32)
    semillas = [42]
elif CASO == 5:
    '''
    Un caso con 3 variables, es un ejemplo clásico donde las variables están elevadas al cuadrado.
    este tipo de sistemas suele representar la intersección de esferas o paraboloides en el espacio.
        x^2 + y^2 + z^2 - 14 = 0
        2x^2 + y - z    -  2 = 0
        x + y^2 + z     -  6 = 0
    '''
    NVEC = 3
    coefs = [
        -14.,
         2.,
        -2.,
        -6.
    ]
    # rango de variación de las coordenadas
    rango = np.array([
        [ 0., 5.],
        [ 0., 5.],
        [ 0., 5.]
    ])
    # la solución, que confieso he obtenido utilizando el algoritmo genético
    secx = 1.435231
    secy = 1.141642   
    secz = 3.261403
    objetivo = [
        secx,
        secy,
        secz
    ]                   
    objetivo = np.array(objetivo, dtype=np.float32)
    semillas = [42]
else:
    print('caso desconocido')
    sys.exit()
'''
Para que Monte Carlo sea comparable con el genético, se le asigna un
número de intentos NPOB veces mayor
'''
FRECUENCIA_IMPRIMIR_MC = FRECUENCIA_IMPRIMIR * NPOB
FRECUENCIA_GRAFICOS_MC = FRECUENCIA_GRAFICOS * NPOB

SENDA_SALIDAS  = 'C:/MEGA/Salidas/Estudio'

# fichero donde escribir los resultados, no se borra de una sesión a otra, se escribe a continuación
FICHERO_LOG    = '{}/caso_{}{}.log'.format(SENDA_SALIDAS, CASO, SUFIJO)
# si no existe la carpeta de salida, se crea
os.makedirs(SENDA_SALIDAS, exist_ok=True)

# para el mapa de gráficos, solo para casos de 2 variables (NVEC = 2)
N_FILAS_IMG = 6
N_COLS_IMG  = 13
SENDA_GRAFICOS = 'C:/MEGA/Salidas/Estudio/Graficos'
os.makedirs(SENDA_GRAFICOS, exist_ok=True)
FICHERO_IMG = SUFIJO + 'img_'
if NVEC == 2 and FRECUENCIA_GRAFICOS > 0:
    ndg = int(MAX_GENERACIONES / FRECUENCIA_GRAFICOS)
    if ndg * FRECUENCIA_GRAFICOS < MAX_GENERACIONES:
        ndg += 1
    ndg += 1
    ind_mej = np.empty(ndg, dtype=int)
    ha_mejorado = np.empty(ndg, dtype=bool)

# una matriz donde ir guardando los resultados de los distintos métodos para mostralos en una tabla al final
solucion = np.empty((4, 2 + NVEC), dtype=np.float32)

# función que escribe en el fichero de resultados y los muestra en panatalla simultáneamente
def imprime(texto, rc=True):
    if type(texto) is not str:
        texto = str(texto)
    if rc:
        print(texto)
        with open(FICHERO_LOG, "a", encoding="utf-8") as log: log.write(texto + '\n')
    else:
        print(texto, end='')
        with open(FICHERO_LOG, "a", encoding="utf-8") as log: log.write(texto)

# la función que dibuja los gráficos
colores = ['k','c','m']
def grafico_evolucion(n_filas_img, n_cols_img, x, y, ind_mej, mejor, ha_mejorado, etq, ndatos, SENDA_GRAFICOS, FICHERO_IMG, discri):
    if n_filas_img == 1:
        # asegurar un mosaico de graficos con dos dimensiones
        n_filas_img = 2
    fig, axes = plt.subplots(nrows=n_filas_img, ncols=n_cols_img, figsize=(24, 12), sharey=True)
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    plt.rcParams.update({'font.size': 12})
    nimg = ndatos
    margen_x = (rango[0,1]-rango[0,0]) / 10.
    margen_y = (rango[1,1]-rango[1,0]) / 10.
    m = 0
    for fil in range(n_filas_img):
        for col in range(n_cols_img):
            axes[fil, col].scatter(x[m], y[m], s=16, color='blue', marker='o')

            # el mejor individuo k
            k = ind_mej[m]
            if ha_mejorado[m]:
                axes[fil, col].scatter(x[m][k:(k+1)], y[m][k:(k+1)], s=32, color='red', marker='s')
            else:
                axes[fil, col].scatter(x[m][k:(k+1)], y[m][k:(k+1)], s=32, color='green', marker='s')
            
            axes[fil, col].annotate(etq[m], xy=(rango[0,0], rango[1,0]))
            if len(objetivo.shape) == 2:
                n = 0
                for i in range(objetivo.shape[1]):
                    axes[fil, col].vlines(x=objetivo[i][0], ymin=rango[1,0], ymax=rango[1,1], colors=colores[n], linewidth=1)
                    axes[fil, col].hlines(y=objetivo[i][1], xmin=rango[0,0], xmax=rango[0,1], colors=colores[n], linewidth=1)
                    n += 1
            else:
                axes[fil, col].vlines(x=objetivo[0], ymin=rango[1,0], ymax=rango[1,1], colors='black', linewidth=1)
                axes[fil, col].hlines(y=objetivo[1], xmin=rango[0,0], xmax=rango[0,1], colors='black', linewidth=1)
            axes[fil, col].set_xlim(rango[0,0] - 0.5, rango[0,1] + 0.5)
            axes[fil, col].set_ylim(rango[1,0] - 0.5, rango[1,1] + 0.5)
            m += 1
            if m == nimg:
                axes[fil, col].annotate('{:8.1e}'.format(mejor), xy=(rango[0,0]+margen_x, rango[1,1]-margen_y))
                break;
        if m == nimg:
            break;
    fig.tight_layout()
    plt.savefig('{}/{}_{}{}.png'.format(SENDA_GRAFICOS, CASO, FICHERO_IMG, discri), dpi = 300, facecolor = 'w', edgecolor = 'w', orientation = 'portrait', format = 'png', transparent = False, bbox_inches = None, pad_inches = 0.1, metadata = None)
    plt.close()

# normalizar las variables al rango 0,1, la entrada es un vector. Normalizar en nuestros casos no tiene utilidad. 
def nor(vec):
    nvec = np.empty(len(vec),dtype=np.float32)
    for j in range(len(vec)):
        nvec[j] = (vec[j] - rango[j,0]) / (rango[j,1] - rango[j,0])
    return nvec

# devuelve a su valor real una variable normalizada
def desnor(j, v):
    if NORMALIZAR:
        return rango[j,0] + v * (rango[j,1] - rango[j,0])
    else:
        return v

# --------------------------------------------------------------
# función objetivo cuyo valor debe ser 0 para el vector solución
# --------------------------------------------------------------
def fo(vec_o):
    # función objetivo
    '''
    vamos a desligar el vector de entrada (vec_o) del que usaremos, porque si este último lo cambiamos
    (por ejemplo, al desnormalizarlo) estaríamos cambiando el de entrada, cosas de los punteros.
    '''
    vec_p = np.empty(NVEC, dtype=np.float32)
    if NORMALIZAR:
        # si el vector está normalizado, transformarlo a sus valores reales
        for j in range(len(vec_p)):
            vec_p[j] = rango[j,0] + vec_o[j] * (rango[j,1] - rango[j,0])
    else:
        # podriamos usar copy.deepcopy pero no estamos preocupados por optimizar el código
        for j in range(len(vec_o)):
            vec_p[j] = vec_o[j]

    if CASO == 0 or CASO == 1:
        '''
        coor = coefs[j]
        '''
        vfo = 0.
        for j in (range(NVEC)):
            d = vec_p[j] - coefs[j]
            vfo += d * d
    elif CASO == 2:
        '''
        x + y = coefs[0]
        x - y = coefs[1]
        '''
        v1 = vec_p[0] + vec_p[1] - coefs[0]
        v2 = vec_p[0] - vec_p[1] - coefs[1]
        vfo = v1 * v1 + v2 * v2
    elif CASO == 3:
        '''
        x = a * y**2
        y = x / b
        '''
        v1 = coefs[0] * vec_p[1] * vec_p[1]
        v2 = v1 / coefs[1]
        v1r = coefs[0] * v2 * v2
        v2r = v1r / coefs[1]
        d1 = v1r - vec_p[0]
        d2 = v2r - vec_p[1]
        d3 = v1r - v1
        d4 = v2r - v2
        vfo = d1 * d1 + d2 * d2 + d3 * d3 + d4 * d4
    elif CASO == 4:
        '''
        x**2 + 2 (x-y)**2 - 36 = 0
        x/2 + y/3          - 5 = 0
        '''
        v1 = vec_p[0] * vec_p[0] + coefs[0] * (vec_p[0] - vec_p[1]) ** 2 + coefs[1]
        v2 = vec_p[0] / coefs[2] + vec_p[1] / coefs[3] + coefs[4]
        vfo = v1 * v1 + v2 * v2
    elif CASO == 5:
        '''
        x^2 + y^2 + z^2 = 14
        2x^2 + y - z    =  2
        x + y^2 + z     =  6
        '''
        v1 = vec_p[0] * vec_p[0] + vec_p[1] * vec_p[1] + vec_p[2] * vec_p[2] + coefs[0]
        v2 = coefs[1] * vec_p[0] * vec_p[0] + vec_p[1] - vec_p[2] + coefs[2]
        v3 = vec_p[0] + vec_p[1] * vec_p[1] + vec_p[2] + coefs[3]
        vfo = v1 * v1 + v2 * v2 + v3 * v3
    return vfo

# crea la etiqueta de texto que se muestra en los gráficos
def etiqueta():
    cad ='{:4.2f}'.format(desnor(0, poblacion[indice_mejor][0]))
    for j in range(1, NVEC):
        cad += '  {:4.2f}'.format(desnor(j, poblacion[indice_mejor][j]))
    etq.append(cad)

# lo primero es imprimir los datos del caso
imprime('')
imprime('CASO : {:d}'.format(CASO))
imprime('Poblacion :{:5d} coordenadas :{:5d}'.format(NPOB, NVEC))
imprime('')
imprime('Normalizar {}'.format('Si' if NORMALIZAR else 'No'))
imprime('')
imprime('L.paso')
imprime('------')
imprime('{:6.3f}'.format(LPI))
imprime('------')
imprime('')
imprime('{:5d} '.format(semillas[0]), False)
imprime('')
imprime('coeficientes')
for j in (range(len(coefs))):
    imprime(' ------', False)
imprime('')
for j in (range(len(coefs))):
    imprime(' {:6.2f}'.format(coefs[j]), False)
imprime('')
for j in (range(len(coefs))):
    imprime(' ------', False)
imprime('')
imprime('')
imprime('coorde infer. super.')
imprime('------ ------ ------')
for j in (range(NVEC)):
    imprime('{:6} {:6.2f} {:6.2f}'.format(j, rango[j,0], rango[j,1]))
imprime('------ ------ ------')
imprime('')
imprime('coorde objet.')
imprime('------ ------')
if len(objetivo.shape) == 2:
    for i in range(objetivo.shape[1]):
        for j in (range(NVEC)):
            imprime('{:6} {:6.2f}'.format(j, objetivo[i][j]))
        imprime('{:13.5e}'.format(fo(objetivo[i])))
else:
    if NORMALIZAR:
        vec = nor(objetivo)
    else:
        vec = copy.deepcopy(objetivo)
    for j in (range(NVEC)):
        imprime('{:6} {:6.2f}'.format(j, objetivo[j]))
    imprime('{:13.5e}'.format(fo(vec)))
imprime('------ ------')
if EVOLUCION:
    imprime('')
    imprime('algoritmo genetico')
    imprime('')

#-------------------------------------------------------------
# algoritmo genetico
# todos los individuos se van trasladando (trabajan en equipo)
#-------------------------------------------------------------

poblacion = np.empty((NPOB, NVEC), dtype=np.float32)
descen    = np.empty((NPOB, NVEC), dtype=np.float32)
merito    = np.empty(NPOB, dtype=np.float32)
factible  = np.empty(NPOB, dtype=bool)

# para ir guardando los 'desplazaminetos' medios de las variables en cada generación
nLpGen    = 0
LpCoor    = np.zeros(NVEC, dtype=np.float32)
LpSuc     = []
'''
semillas = []
for i in range(2000):
    semillas.append(az.randint(1, 100000))
'''
for ks in semillas:
    semilla = ks
    az.seed(semilla)

    indice_mejor = -1
    merito_mejor = 1.0e+08
    # generar la poblacion y el individuo con mas merito, el de menor distancia al objetivo 
    for i in range(NPOB):
        for j in (range(NVEC)):
            na = az.random()
            if NORMALIZAR:
                poblacion[i,j] = na
            else:
                poblacion[i,j] = rango[j,0] + na * (rango[j,1] - rango[j,0])
        merito[i] = fo(poblacion[i])
        if merito[i] < merito_mejor:
            indice_mejor = i
            merito_mejor = merito[i]
    '''
    Esto ha sido un intento infructuoso de hacer intervenir el centro de masas de la población
    en los cálculos. Se generó una tabla de 2000 filas con varias magnitudes que podrían ser
    relevantes, para luego alimentar una red neuronal buscando un patrón de cuando se obtine una solución
    y cuando no (dos clases). La red no encontrón nada.

    cdm = np.zeros(NVEC, dtype=np.float32)  # centro de masas
    for i in range(NPOB):
        for j in (range(NVEC)):
            cdm[j] += poblacion[i,j]
    cdm /= NPOB
    dist = 0.
    for j in (range(NVEC)):
        #imprime(' {:8.4f}'.format(cdm[j]), False)
        d = poblacion[indice_mejor,j] - cdm[j]
        dist += d * d
    dest = 0.
    for i in range(NPOB):
        for j in (range(NVEC)):
            d = poblacion[i,j] - cdm[j]
            dest += d * d 
    dest /= (NPOB * NVEC)
    mmed = np.mean(merito)
    mdest = np.std(merito)
    merito_mejor_i = np.min(merito)
    '''
    if NVEC == 2 and FRECUENCIA_GRAFICOS_MC > 0:
        # guardar las coordenadas de los individuos en cada generación para los gráficos
        x = np.empty((ndg, NPOB), dtype=np.float32)
        y = np.empty((ndg, NPOB), dtype=np.float32)
        # la situación de partida para el gráfico
        ng = 0
        for i in range(NPOB):
            x[ng, i] = desnor(0, poblacion[i,0])
            y[ng, i] = desnor(1, poblacion[i,1])
        ind_mej[ng] = indice_mejor
        mejorado = False
        ha_mejorado[ng] = False
        etq = []
        etiqueta()
        ng += 1
    # resolver
    generacion = 0
    if EVOLUCION:
        imprime('Ngen. facti i.mej  m.merito')
        imprime('----- ----- -----  --------')
    while merito_mejor > ERROR_MAXIMO and generacion < MAX_GENERACIONES:
        generacion += 1
        nfactibles = 0
        # mutación y cruce, todos los individuos tantean una nueva posición (que ya veremos si acaban ocupando), que
        # les marca el individuo más próximo a la solución (indice_mejor) y otros dos individuos al azar: i1,i2
        for i in (range(NPOB)):
            # dos individuos (i1,i2)
            i1 = az.randint(0, NPOB - 1)
            i2 = az.randint(0, NPOB - 1)
            # una coordenada (i3), para garantizar que habrá recombinacion en al menos una coordenada del 'indice_mejor', no
            # tiene sentido repetir la posición de este, cosa que ocurriría si no hay recombinación en ninguna coordenada
            i3 = az.randint(0, NVEC - 1)

            es_factible = True
            # coordendas de la nueva posición
            nLpGen += 1
            for j in (range(NVEC)):
                if j == i3 or az.random() < RECOMBINA:
                    
                    LpCoor[j] += abs(MUTACION * (poblacion[i1,j] - poblacion[i2,j]))

                    descen[i,j] = poblacion[indice_mejor,j] + MUTACION * (poblacion[i1,j] - poblacion[i2,j])
                    if NORMALIZAR:
                        if descen[i,j] < 0.0 or descen[i,j] > 1.0:
                            # las coordenadas deben estar dentro del rango establecido
                            es_factible = False
                            break;
                    else:
                        if descen[i,j] < rango[j,0] or descen[i,j] > rango[j,1]:
                            # las coordenadas deben estar dentro del rango establecido
                            es_factible = False
                            break;
                else:
                    descen[i,j] = poblacion[i,j]
            factible[i] = es_factible
            if es_factible:
                nfactibles += 1
        # seleccion, veamos para que individuos la posición tanteda los acerca a la solución
        for i in (range(NPOB)):
            if factible[i]:
                vfo =  fo(descen[i])
                if vfo < merito[i]:
                    # la posición tanteada es mejor, movemos al individuo a ella y gurdamos su merito
                    for j in (range(NVEC)):
                        poblacion[i,j] = descen[i,j]
                    merito[i] = vfo

                    if vfo < merito_mejor:
                        # ademas es el individuo mas proximo, por ahora
                        mejorado = True
                        indice_mejor = i
                        merito_mejor = vfo
            if NVEC == 2 and FRECUENCIA_GRAFICOS > 0:
                # para los graficos
                if generacion % FRECUENCIA_GRAFICOS == 0:
                    x[ng, i] = desnor(0, poblacion[i,0])
                    y[ng, i] = desnor(1, poblacion[i,1])
        if NVEC == 2 and FRECUENCIA_GRAFICOS > 0:
            if generacion % FRECUENCIA_GRAFICOS == 0:
                ha_mejorado[ng] = mejorado
                mejorado = False
                ind_mej[ng] = indice_mejor
                etiqueta()
                ng +=1
        if generacion % FRECUENCIA_LP == 0:
                LpSuc.append(LpCoor / float(nLpGen))
                LpCoor.fill(0)
                nLpGen = 0

        if EVOLUCION:
            if generacion % FRECUENCIA_IMPRIMIR == 0:
                imprime('{:5d} {:5d} {:5d}  {:8.4f}'.format(generacion, nfactibles, indice_mejor, merito_mejor), False)
    if EVOLUCION:
        imprime('----- ----- -----  --------')
    solucion[0,0] = generacion
    solucion[0,1] = merito_mejor
    for j in (range(NVEC)):
        solucion[0,j+2] = desnor(j, poblacion[indice_mejor,j])
        if EVOLUCION:
            imprime('{:8.4f}  '.format(desnor(j, poblacion[indice_mejor,j])), False)
    if EVOLUCION:
        imprime('')
    if NVEC == 2 and FRECUENCIA_GRAFICOS > 0:
        # asegurar la última generacion
        if generacion % FRECUENCIA_GRAFICOS != 0:
            ha_mejorado[ng] = mejorado
            mejorado = False
            for i in range(NPOB):
                x[ng, i] = desnor(0, poblacion[i,0])
                y[ng, i] = desnor(1, poblacion[i,1])
            ind_mej[ng] = indice_mejor
            etiqueta()
            ng += 1
        if FRECUENCIA_GRAFICOS > 0:
            grafico_evolucion(N_FILAS_IMG, N_COLS_IMG, x, y, ind_mej, merito_mejor, ha_mejorado, etq, ng, SENDA_GRAFICOS, FICHERO_IMG,'Gen')
    '''
    para el intento infructuoso de la RNA
    imprime('{:5d} {:5d} {:5d} {:12.4e} {:12.4e} {:12.4e} {:12.4e} {:12.4e} {:12.4e} {:12.4e} {:12.4e} {:12.4e} {}'.format(semilla, generacion, nfactibles, cdm[0], cdm[1], merito_mejor, merito_mejor_i, mmed, (mmed - merito_mejor_i), mdest, dist, dest, '0' if merito_mejor > ERROR_MAXIMO else '1'))
    '''

#-------------------------------------------------------------
# monte carlo simple
#-------------------------------------------------------------
if EVOLUCION:
    imprime('')
    imprime('monte carlo simple')
    imprime('')
# un solo individuo trasladandose
i = 0   
# para igualar el coste de computo al genético aumentamos el máximo de generaciones 
max_generaciones_MC = MAX_GENERACIONES * NPOB
pob_ini   = np.empty((1, NVEC), dtype=np.float32)
poblacion = np.empty((1, NVEC), dtype=np.float32)
descen    = np.empty((1, NVEC), dtype=np.float32)
if EVOLUCION:
    imprime('monte carlo simple, puntos enteramente al azar')
    imprime('')
az.seed(semilla)
for j in (range(NVEC)):
    # guardamos em punto de partida en 'pob_ini' para que sea el mismo en todos los monte carlo
    na = az.random()
    if NORMALIZAR:
        poblacion[0,j] = pob_ini[0,j] = na 
    else:
        poblacion[0,j] = pob_ini[0,j] = rango[j,0] + na * (rango[j,1] - rango[j,0])
# calculamos su mérito, la distancia al objetivo
indice_mejor = 0
merito_mejor = fo(poblacion[0])
if NVEC == 2 and FRECUENCIA_GRAFICOS_MC > 0:
    x = np.empty((ndg, 1), dtype=np.float32)
    y = np.empty((ndg, 1), dtype=np.float32)
    # la situación de partida para el gráfico
    ng = 0
    x[ng, 0] = desnor(0, poblacion[0,0])
    y[ng, 0] = desnor(1, poblacion[0,1])
    ind_mej[ng] = 0
    mejorado = False
    ha_mejorado[ng] = False
    etq = []
    etiqueta()
    ng += 1
# resolver
generacion = 0
if EVOLUCION:
    imprime('Ngen.  m.merito')
    imprime('-----  --------')
while merito_mejor > ERROR_MAXIMO and generacion < max_generaciones_MC:
    generacion += 1
    # generamos un nuevo punto al azar, en lugar de la mutación y cruce del algoritmo genético
    for j in (range(NVEC)):
        na = az.random()
        if NORMALIZAR:
            descen[i,j] = az.random()
        else:
            descen[i,j] = rango[j,0] + az.random() * (rango[j,1] - rango[j,0])
    vfo = fo(descen[i])

    # selecciona, nos movemos si está mas cerca de la solución
    if vfo < merito_mejor:
        mejorado = True
        merito_mejor = vfo
        for j in (range(NVEC)):
            poblacion[i,j] = descen[i,j]
    if NVEC == 2 and FRECUENCIA_GRAFICOS_MC > 0:
        # para los gráficos
        if generacion % FRECUENCIA_GRAFICOS_MC == 0:
            ha_mejorado[ng] = mejorado
            mejorado = False
            x[ng, i] = desnor(0, poblacion[i,0])
            y[ng, i] = desnor(1, poblacion[i,1])
            ind_mej[ng] = 0
            etiqueta()
            ng += 1
    if EVOLUCION:
        if FRECUENCIA_IMPRIMIR_MC > 0 and generacion % FRECUENCIA_IMPRIMIR_MC == 0:
            imprime('{:5d}  {:8.4f}'.format(generacion, merito_mejor))
if EVOLUCION:
    imprime('{:5d}  {:8.4f}'.format(generacion, merito_mejor))
    imprime('-----  --------')
solucion[1,0] = generacion
solucion[1,1] = merito_mejor
for j in (range(NVEC)):
    solucion[1,j+2] = desnor(j, poblacion[indice_mejor,j])
    if EVOLUCION:
        imprime('{:8.4f}  '.format(desnor(j, poblacion[indice_mejor,j])), False)
if EVOLUCION:
    imprime('')
if NVEC == 2 and FRECUENCIA_GRAFICOS_MC > 0:
    if generacion % FRECUENCIA_GRAFICOS_MC != 0:
        ha_mejorado[ng] = mejorado
        mejorado = False
        x[ng, i] = desnor(0, poblacion[indice_mejor,0])
        y[ng, i] = desnor(1, poblacion[indice_mejor,1])
        ind_mej[ng] = indice_mejor
        etiqueta()
        ng += 1
    grafico_evolucion(N_FILAS_IMG, N_COLS_IMG, x, y, ind_mej, merito_mejor, ha_mejorado, etq, ng, SENDA_GRAFICOS, FICHERO_IMG,'Azar')

#-------------------------------------------------------------
# monte carlo sucesivo
#-------------------------------------------------------------
if EVOLUCION:
    imprime('')
    imprime('monte carlo sucesivo')
    imprime('')
# un solo individuo trasladandose
i = 0   
az.seed(semilla)

# Lp es una logitud de paso moderadamente pequeña, es el desplazamiento máximo en cada coordenada, a cada paso
LpCoor.fill(LPI)

# recuperamos el punto de partida
for j in (range(NVEC)):
    poblacion[0,j] = pob_ini[0,j]
indice_mejor = 0
merito_mejor = fo(poblacion[0])
if NVEC == 2 and FRECUENCIA_GRAFICOS_MC > 0:
    ng = 0
    x[ng, 0] = desnor(0, poblacion[0,0])
    y[ng, 0] = desnor(1, poblacion[0,1])
    ind_mej[ng] = 0
    mejorado = False
    ha_mejorado[ng] = False
    etq = []
    etiqueta()
    ng += 1
generacion = 0
if EVOLUCION:
    imprime('Ngen.  m.merito')
    imprime('-----  --------')
while merito_mejor > ERROR_MAXIMO and generacion < max_generaciones_MC:
    generacion += 1
    # mutación y cruce
    es_factible = True
    for j in (range(NVEC)):
        '''
        guarda un evidente parecido con el algoritmo genetico, aunque el desplazamiento no viene determinado por
        el vector entre dos individuos (i1,i2), es un vector al azar con una longitud maxima determinada (Lp)
        '''
        if NORMALIZAR:
            if az.random() < 0.5:
                descen[i,j] = poblacion[i,j] + LpCoor[j] * az.random()
            else:
                descen[i,j] = poblacion[i,j] - LpCoor[j] * az.random()
            if descen[i,j] < 0.0 or descen[i,j] > 1.0:
                es_factible = False
                break;
        else:
            if az.random() < 0.5:
                descen[i,j] = poblacion[i,j] + LpCoor[j] * az.random() * (rango[j,1] - rango[j,0])
            else:
                descen[i,j] = poblacion[i,j] - LpCoor[j] * az.random() * (rango[j,1] - rango[j,0])
            if descen[i,j] < rango[j,0] or descen[i,j] > rango[j,1]:
                es_factible = False
                break;
    # selecciona
    if es_factible:    
        vfo = fo(descen[i])
        if vfo < merito_mejor:
            merito_mejor = vfo
            mejorado = True
            for j in (range(NVEC)):
                poblacion[i,j] = descen[i,j]
    if NVEC == 2 and FRECUENCIA_GRAFICOS_MC > 0:
        if generacion % FRECUENCIA_GRAFICOS_MC == 0:
            ha_mejorado[ng] = mejorado
            mejorado = False
            x[ng, i] = desnor(0, poblacion[i,0])
            y[ng, i] = desnor(1, poblacion[i,1])
            ind_mej[ng] = 0
            etiqueta()
            ng += 1
    if EVOLUCION:
        if FRECUENCIA_IMPRIMIR_MC > 0 and generacion % FRECUENCIA_IMPRIMIR_MC == 0:
            imprime('{:5d}  {:8.4f}'.format(generacion, merito_mejor))
if EVOLUCION:
    imprime('{:5d}  {:8.4f}'.format(generacion, merito_mejor))
    imprime('-----  --------')
solucion[2,0] = generacion
solucion[2,1] = merito_mejor
for j in (range(NVEC)):
    solucion[2,j+2] = desnor(j, poblacion[indice_mejor,j])
    if EVOLUCION:
        imprime('{:8.4f}  '.format(desnor(j, poblacion[indice_mejor,j])), False)
if EVOLUCION:
    imprime('')
if NVEC == 2 and FRECUENCIA_GRAFICOS_MC > 0:
    if generacion % FRECUENCIA_GRAFICOS_MC != 0:
        ha_mejorado[ng] = mejorado
        mejorado = False
        x[ng, i] = desnor(0, poblacion[indice_mejor,0])
        y[ng, i] = desnor(1, poblacion[indice_mejor,1])
        ind_mej[ng] = indice_mejor
        etiqueta()
        ng += 1
    grafico_evolucion(N_FILAS_IMG, N_COLS_IMG, x, y, ind_mej, merito_mejor, ha_mejorado, etq, ng, SENDA_GRAFICOS, FICHERO_IMG, 'Lp_' + str(LPI))

#-------------------------------------------------------------
# monte carlo sucesivo con modulación
#-------------------------------------------------------------
if EVOLUCION:
    imprime('')
    imprime('monte carlo sucesivo con modulacion')
    imprime('')
# un solo individuo trasladandose
i = 0   
az.seed(semilla)

# recuperamos el punto de partida
for j in (range(NVEC)):
    poblacion[0,j] = pob_ini[0,j]
indice_mejor = 0
merito_mejor = fo(poblacion[0])

# si se ha normalizado no podemos usar desplazamientos obtenidos del genético
if NORMALIZAR: nLp = -1

if nLp == -1:
    # partimos con un determinado desplazamiento máximo Lp que iremos reduciendo 
    
    LpCoor.fill(LPI)
else:
    # a cada generación usaremos los desplazamientos obtenidos del genético

    LpSuc = np.array(LpSuc, dtype=np.float32)
    imprime('')
    for k in range(len(LpSuc)):
        for j in range(NVEC):
            imprime(' {:9.2e}'.format(LpSuc[k,j]), False)
        imprime('')
    imprime('')
    LpSuc *= MUTACION
    LpCoor = copy.deepcopy(LpSuc[nLp])

if NVEC == 2 and FRECUENCIA_GRAFICOS_MC > 0:
    ng = 0
    x[ng, 0] = desnor(0, poblacion[0,0])
    y[ng, 0] = desnor(1, poblacion[0,1])
    ind_mej[ng] = 0
    mejorado = False
    ha_mejorado[ng] = False
    etq = []
    etiqueta()
    ng += 1
generacion = 0
if EVOLUCION:
    imprime('Ngen.  m.merito')
    imprime('-----  --------')
while merito_mejor > ERROR_MAXIMO and generacion < max_generaciones_MC:
    generacion += 1
    # mutación y cruce
    es_factible = True
    for j in (range(NVEC)):
        '''
        ahora se parece un poco más al algoritmo genético, porque el desplazamiento tiene una
        longitud máxima variable, como ocurre con el vector entre dos individuos (i1,i2) 
        '''
        if NORMALIZAR:
            if az.random() < 0.5:
                descen[i,j] = poblacion[i,j] + LpCoor[j] * az.random()
            else:
                descen[i,j] = poblacion[i,j] - LpCoor[j] * az.random()
            if descen[i,j] < 0.0 or descen[i,j] > 1.0:
                es_factible = False
                break;
        else:
            if az.random() < 0.5:
                descen[i,j] = poblacion[i,j] + LpCoor[j] * az.random() * (rango[j,1] - rango[j,0])
            else:
                descen[i,j] = poblacion[i,j] - LpCoor[j] * az.random() * (rango[j,1] - rango[j,0])
            if descen[i,j] < rango[j,0] or descen[i,j] > rango[j,1]:
                es_factible = False
                break;
    # selecciona
    if es_factible:    
        vfo = fo(descen[i])
        if vfo < merito_mejor:
            if nLp == -1:
                if vfo < np.min(LpCoor):
                    '''
                    la longitud máxima de los desplazamientos se va reducciendo según se
                    reduce la distancia al objetivo
                    '''
                    LpCoor.fill(vfo)
                    if EVOLUCION:
                        imprime('Lp = {:8.6f}'.format(vfo))
            merito_mejor = vfo
            mejorado = True
            for j in (range(NVEC)):
                poblacion[i,j] = descen[i,j]
    if NVEC == 2 and FRECUENCIA_GRAFICOS_MC > 0:
        if generacion % FRECUENCIA_GRAFICOS_MC == 0:
            ha_mejorado[ng] = mejorado
            mejorado = False
            x[ng, i] = desnor(0, poblacion[i,0])
            y[ng, i] = desnor(1, poblacion[i,1])
            ind_mej[ng] = 0
            etiqueta()
            ng += 1
    if nLp != -1:
        if generacion % (FRECUENCIA_LP * NPOB) == 0:
            if nLp < LpSuc.shape[0] - 1:
                nLp += 1
                LpCoor = copy.deepcopy(LpSuc[nLp])
    if EVOLUCION:
        if FRECUENCIA_IMPRIMIR_MC > 0 and generacion % FRECUENCIA_IMPRIMIR_MC == 0:
            imprime('{:5d}  {:8.4f}'.format(generacion, merito_mejor))
if EVOLUCION:
    imprime('{:5d}  {:8.4f}'.format(generacion, merito_mejor))
    imprime('-----  --------')
solucion[3,0] = generacion
solucion[3,1] = merito_mejor
for j in (range(NVEC)):
    solucion[3,j+2] = desnor(j, poblacion[indice_mejor,j])
    if EVOLUCION:
        imprime('{:8.4f}  '.format(desnor(j, poblacion[indice_mejor,j])), False)
if EVOLUCION:
    imprime('')
if NVEC == 2 and FRECUENCIA_GRAFICOS_MC > 0:
    # asegurar la última generación
    if generacion % FRECUENCIA_GRAFICOS_MC != 0:
        ha_mejorado[ng] = mejorado
        mejorado = False
        x[ng, i] = desnor(0, poblacion[indice_mejor,0])
        y[ng, i] = desnor(1, poblacion[indice_mejor,1])
        ind_mej[ng] = indice_mejor
        etiqueta()
        ng += 1
    grafico_evolucion(N_FILAS_IMG, N_COLS_IMG, x, y, ind_mej, merito_mejor, ha_mejorado, etq, ng, SENDA_GRAFICOS, FICHERO_IMG, 'LpMod_' + str(LPI))

# mostramos la tabla final
imprime('')
imprime('número máximo de generaciones {:6d}'.format(MAX_GENERACIONES))
imprime('')
rot = ['geneti', 'mc sim', 'mc suc', 'mc mod']
imprime('       n.geners    merito ', False)
for j in (range(NVEC)):
    imprime(' {:8.4f}'.format(coefs[j]), False)
imprime('')
imprime('       -------- ----------', False)
for j in (range(NVEC)):
    imprime(' --------', False)
imprime('')
for i in range(4):
    imprime('{:6} {:8} {:10.5f}'.format(rot[i], solucion[i,0], solucion[i,1]), False)
    for j in (range(NVEC)):
        imprime(' {:8.4f}'.format(solucion[i,2+j]), False)
    imprime('')
imprime('       -------- ----------', False)
for j in (range(NVEC)):
    imprime(' --------', False)
imprime('')

imprime('\nfin.\n')

