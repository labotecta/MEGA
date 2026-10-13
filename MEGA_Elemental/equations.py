# Este módulo define las ecuaciones del modelo CGE

def eqpm(er, pWm):
    '''
    Ecuación que calcula los precios de importación en moneda local
    Simplemente multiplica los precios en moneda extranjera por el tipo de cambio
    
    .. math::
        pm_{i} = \\varepsilon \cdot pWm_{i}

    Args:
        er (float): The real exchange rate
                    1
        pWm (1D numpy array): The world price of commodity i in foreign currency.
            AGR    1.0
            OIL    1.0
            IND    1.0
            SER    1.0

    Returns:
        pm (1D numpy array): The price of commodity i imports in domestic currency.
    '''
    pm = er * pWm
    '''
    AGR    1.0
    OIL    1.0
    IND    1.0
    SER    1.0
    '''
    return pm

def eqpy(pf, beta):
    '''
    Ecuación para calcular el precio del valor añadido de cada sector.
    Es simplemente la ponderación de los precios de los factores 'pf' por sus coeficientes de participación 'beta' en la producción de cada sector

    El valor añadido es la diferencia entre el valor de los costes de producción (costes intermedios) y los ingresos de una empresa (sector).
    fijandonos en las c olumnas: para cada sector los costes de producción son la suma de las filas de los otros sectores y el valos añadido
    la suma de resto de filas, la suma de ambos da el ingreso total del sector que coincide con la suma de todos los conceptos de la fila del sector
    Los factores de producción empleados por las actividades son los que generan el valor agregado de la economía en cuestión,
    es decir, su uso es el que genera la riqueza adicional de la comunidad durante el año.
    A la suma del valor agregado de todas las actividades se le llama producto interno bruto o PIB.

    .. math::
        ????   py_{j} = \sum_{h}F_{h,j}{\\beta_{h,j}}

    Args:
        ????? esto está mal: F    (2D numpy array): The use of factor h in the production of good j

        pf (1D numpy array): Precio de los factores h = ("LAB", "CAP", "LAND", "NTR").  Esta puesto a 1 para todos los factores y no cambia nunca
                                                                                        con un precio de 1, cantidades e importes tienen el mismo valor
            LAB     1.0
            CAP     1.0
            LAND    1.0
            NTR     1.0
        beta (1D numpy array):
            Parámetro de participación en el coste del factor h = ("LAB", "CAP", "LAND", "NTR") de cada una de las producción de los sectores ind = ("AGR", "OIL", "IND", "SER")
            es una matriz len(h) x len(ind). Cada fila contie las participaciones para el factor correspondiente a esa fila, de los productos de cada uno de los sectores (columnas)
            beta (2D numpy array)
                       AGR       OIL      IND       SER
            LAB   0.122807  0.028385  0.19863  0.414493
            CAP   0.456140  0.068935  0.80137  0.585507
            LAND  0.421053  0.000000  0.00000  0.000000
            NTR   0.000000  0.902680  0.00000  0.000000
    Returns:
        'beta.mul(pf, axis=0)' Es una matriz len(h) x len(ind). Se obtiene multiplicando los elementos de cada columna (axis=0) de 'beta' por los elemtos del vector 'pf'

            import numpy as np
            res = np.ndarray([4,4])
            for i in range(4):      # filas de beta
                for j in range(4):  # columnas de beta
                    res[i, j] = beta.values[i, j] * pf.values[i]

        el precio del valor añadido por el sector ind = ("AGR", "OIL", "IND", "SER")
                       AGR       OIL      IND       SER
            LAB   0.122807  0.028385  0.19863  0.414493
            CAP   0.456140  0.068935  0.80137  0.585507
            LAND  0.421053  0.000000  0.00000  0.000000
            NTR   0.000000  0.902680  0.00000  0.000000

        otro ejemplo:
            cuando pf =[1.  2.  3.  4.]:
                       AGR         OIL        IND         SER
            LAB   0.12280702  0.02838504  0.19863014  0.41449275
            CAP   0.9122807   0.1378702   1.60273973  1.17101449
            LAND  1.26315789  0.00000000  0.00000000  0.00000000
            NTR   0.00000000  3.61071943  0.00000000  0.00000000

        py (1D numpy array): suma por columnas axis=0, por tanto suma para cada sector
            AGR    1.0
            OIL    1.0
            IND    1.0
            SER    1.0
        otro ejemplo:
            cuando pf =[1.  2.  3.  4.]:
                     LAB         CAP        LAND         NTR
                2.29824561, 3.77697467, 1.80136986, 1.58550725
    '''
    py = beta.mul(pf, axis=0).sum(axis=0)
    return py

def eqpz(ay, ax, py, pq):
    '''
    Ecuación para calcular el precio de la producción bruta

    .. math::
        pz_{j} = ay_{j}py_{j} + \sum_{i}ax_{i,j}pq_{i}

    Args:
        ay (1D numpy array): Leontif production parameter, share of output of industry j in value added of good j
            AGR    0.647727
            OIL    0.973358
            IND    0.401467
            SER    0.637708

        ax (2D numpy array): Fixed proportions of intermeidate input i used in production of good j (Leontif production function)
                      AGR       OIL       IND       SER
            AGR  0.079545  0.001973  0.051329  0.009242
            OIL  0.000000  0.003947  0.122823  0.006778
            IND  0.170455  0.012828  0.289643  0.192237
            SER  0.102273  0.007894  0.134739  0.154036

        py (1D numpy array): The price of value added for each good j
            AGR    1.0
            OIL    1.0
            IND    1.0
            SER    1.0

        pq (1D numpy array): price of the Armington good (domestic + imports) for each good i
            AGR    1.0
            OIL    1.0
            IND    1.0
            SER    1.0

    Returns:
        pz (1D numpy array): price of output good j
            AGR    1.0
            OIL    1.0
            IND    1.0
            SER    1.0
    '''
    pz = ay * py + (ax * pq).sum(axis=0)
    return pz

def eqpqbar(deltam, taum, tauz, pm, pz):
    '''
    Calcula el precio del producto domestico + importaciones (Armington) (Equation describing the price of the Armington good)

    .. math::
        pq_{j} = deltam_{j}pm_{j}(1+\\tau^{m}_{i}) + (1-deltam_{j})pz_{j}(1+\\tau^{z}_{i})
        ponedera mediente el coeficiente de propensión a la importación, el precio de importación con aranceles y el preción de producción con impuestos

    Args:
        deltam (1D numpy array): propensión a la importación de cada producto, un coeficiente
        taum (1D numpy array): tasa de aranceles de importación (?? Tariff rate on commodity i)
        tauz (1D numpy array): tasa de impuestos a la producción (?? Ad valorem tax rate on commodity i)
        pm (1D numpy array): precio de importación de cada producto en moneda local (The price of commodity i imports in domestic currency)
        pz (1D numpy array): precio de producción de cada producto (sector) (price of output good i)

    Returns:
        pq (1D numpy array): precio del producto (domestico + importaciones) de Armington para cada producto (sector) (price of the Armington good (domestic + imports) for each good i)
    '''
    '''
    La elasticidad de Armington es un parámetro económico comúnmente utilizado en modelos de teoría del consumidor y comercio internacional.
    Representa la elasticidad de sustitución entre productos de diferentes países y se basa en el supuesto de Paul Armington en 1969 de
    que los productos comercializados internacionalmente se diferencian por país de origen.
    El supuesto de Armington se ha convertido en un supuesto estándar en los modelos internacionales de equilibrio general computable.
    Estos modelos generan respuestas del comercio a las variaciones de precios más pequeñas y realistas que las implícitas en los modelos de productos homogéneos.
    Sin embargo, no existe consenso sobre la magnitud de la elasticidad.
    En diferentes contextos, los investigadores tienden a obtener estimaciones sustancialmente diferentes.
    Un estudio cuantitativo de 3524 estimaciones de la elasticidad de Armington disponibles en 2019 muestra que, condicionada a estas diferencias y
    corregida por el sesgo de publicación mediante técnicas de metarregresión, la elasticidad de Armington se encuentra en el rango de 2,5 a 5,1, con una mediana estimada de 3,8.

    En el supuesto de Armington, el agente representativo maximiza su bienestar a través de un proceso de optimización de dos etapas:
    En primer lugar, dado un índice general de precios, se escoge el nivel de gasto/consumo total sobre un "bien compuesto" (por ejemplo, el consumo agregado de plátanos).
    La relación entre los cambios en el índice de precio y el impacto en el gasto total se determina por una determinada elasticidad de demanda por importaciones.
    Luego, dentro de este bien compuesto, se asign el nivel elegido de gasto entre las diferentes “variedades" del bien, dependiendo del precio relativo de 
    cada variedad (digamos, elegir más plátanos de Ecuador y menos de Santa Lucía).
    El alcance de la respuesta distributiva entre variedades a los cambios en el precio relativo está determinada por la elasticidad de substitución de Armington.
    '''
    pq = deltam * pm * (1 + taum) + (1 - deltam) * pz * (1 + tauz)
    return pq

def eqpq(deltam, taum, tauz, pm, pz, pq):
    '''
    Calcula la desviación en el precio de suministro del producto domestico + importaciones (Armington) (Domestic supply prices.)

    .. math::
        pq_{j} = deltam_{j}pm_{j}(1+\\tau^{m}_{i}) + (1-deltam_{j})pz_{j}(1+\\tau^{z}_{i})

    Args:
        deltam (1D numpy array): propensión a la importación de cada producto, un coeficiente
        taum (1D numpy array): tasa de aranceles de importación (?? Tariff rate on commodity i)
        tauz (1D numpy array): tasa de impuestos a la producción (?? Ad valorem tax rate on commodity i)
        pm (1D numpy array): precio de importación de cada producto en moneda local (The price of commodity i imports in domestic currency)
        pz (1D numpy array): precio de producción de cada producto (sector) (price of output good i)
        pq (1D numpy array): precio de equilibrio

        (?? deltam (1D numpy array): import propensity for good j
        tauz (1D numpy array): Ad valorem tax rate on commodity i
        taum (1D numpy array): Tariff rate on commodity i
        pz (1D numpy array): price of output good i
        pm (1D numpy array): The price of commodity i imports in domestic currency.)

    Returns:
        pq_error (1D numpy array): Difference between current value of pq and model calculated value of pq 
        (deltam * pm * (1 + taum) + (1 - deltam) * pz * (1 + tauz)) # es el mismo valor que calcula la función 'eqpqbar'
    '''

    #     pq = deltam * pm * (1 + taum) + (1 - deltam) * pz * (1 + tauz)

    pq_error = pq - (deltam * pm * (1 + taum) + (1 - deltam) * pz * (1 + tauz))
    return pq_error

