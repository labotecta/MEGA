import sys
import copy
import numpy as np
from pandas import DataFrame
import ecuaciones as ecua

'''
Todas las matrices las guardaremos como numpy arrays y los sectores siempre en las filas.
Los valores únicos, como SF0, los guardamos como escalares, tal vez hubiera sido mejor guardarlos
como array (1,1) ya que durante la ejecución del modelo hay que convertirlos a arrays para
cooncatenarlos con el resto de variables.

Los valores que se muestran como comentarios son los correspondientes a la MCS 'MCA-ESP-05_ajustada_imp_final'
'''
class datos(object):

    def __init__(self, sam, h, ind, dem, idt, gov, trf, ayd, inv, ext, css, alp, INDICE_F_TRA, PARO_INICIAL):
        '''
        (sam, h, ind, dem, idt, gov, trf, retg, inv, ext, css) son los nombres de filas y columnas de la 'sam'

        los valores de la MCS son importes y necesitamos cantidades, pero podemos elegir un sistema
        de unidades para las cantidades de forma que todos los productos y factores tengan
        precio igual a 1.
        el sistema de unidades no afecta a la 'economía' de las transacciones, pero si afecta al cálculo
        de impuestos. 
        '''
        # para considerar los importes como cantidades
        # --------------------------------------------
        self.pF0 = np.ones(len(h))          # precio de los factores
        self.pY0 = np.ones(len(ind))        # precio del factor compuesto
        self.pZ0 = np.ones(len(ind))        # precio de suministro de los sectores
        self.pQ0 = np.ones(len(ind))        # precio del producto de Armington
        self.pWe = np.ones(len(ind))        # precio de exportación
        self.pWm = np.ones(len(ind))        # precio de importación
        self.pD0 = np.ones(len(ind))        # precio de los sectores para la demanda

        self.epsilon  = np.float64(1.)      # tipo de cambio (cotización)
        self.epsilon0 = self.epsilon

        # consumos (imputs -compras-) intermedios de los sectores en las columnas y ventas (outputs) intermedias en las filas
        self.X0 = DataFrame(sam, index=ind, columns=ind)
        '''
                AP1      AP2       AP3      AP4       AP5      AP6
        AP1  2316.0      1.0   25294.0     23.0    2774.0    174.0
        AP2  1461.0  42947.0   19623.0   2589.0   20463.0   3422.0
        AP3  9256.0   4288.0  196336.0  54375.0   65046.0  10935.0
        AP4   205.0    655.0    1734.0  97946.0   21050.0   1825.0
        AP5  3980.0   9878.0   85260.0  26081.0  203868.0  23912.0
        AP6     0.0      0.0       0.0      0.0       0.0      0.0
        '''
        self.X0 = self.X0.to_numpy(dtype=np.float64)                            # (len(ind), len(ind))

        # factores empleados por cada sector
        # primero, extraemos las columnas de los sectores de las filas de los factores
        self.F0 = DataFrame(sam, index=h, columns=ind)
        '''
               AP1      AP2      AP3      AP4       AP5      AP6
        K  20471.0  16143.0  42859.0  36758.0  251643.0  11109.0
        L   4407.0   3737.0  56233.0  40779.0  158634.0  70628.0
        '''
        # luego, la trasponemos para que las filas sean los sectores, ya que estamos extrayendo las filas (index) de los factores (h)
        self.F0 = self.F0.T
        '''
                    K         L
        AP1   20471.0    4407.0
        AP2   16143.0    3737.0
        AP3   42859.0   56233.0
        AP4   36758.0   40779.0
        AP5  251643.0  158634.0
        AP6   11109.0   70628.0
        '''
        self.F0 = self.F0.to_numpy(dtype=np.float64)                            # (len(ind), len(h))

        # 'FF' es el ingreso de cada uno de los hogares por los factores aportados a todos los sectores
        self.FF0 = DataFrame(sam, index=dem, columns=h)                         # (len(dem), len(h))
        '''
                   K         L
        C1  378983.0  334418.0
        C2       0.0       0.0
        '''
        self.FF0 = self.FF0.to_numpy(dtype=np.float64)

        # ingresos de los hogares recibidos de la seguridad social (pagos -columna- de la seguridad social a los hogares -fila-). Variable exógena
        self.PssH0 = DataFrame(sam, index=dem, columns=css)                     # (len(dem), 1)
        if self.PssH0.empty:
            self.PssH0 = np.zeros(len(dem), dtype=np.float64)
        else:
            '''
                    CSS
            C1      0.0
            C2  96804.0
            '''
            self.PssH0 = self.PssH0.to_numpy(dtype=np.float64).reshape(len(dem))    # pensiones consumidor (len(dem), 1)
            self.PssH0 = np.nan_to_num(self.PssH0, copy=True) # si no hay datos (NAN) se sustituye por 0

        # factor compuesto para cada sector, igual a la suma de los factores utilizados por el sector en la MCS
        self.Y0 = self.F0.sum(axis=1)                                           # (len(ind), )
        '''
        AP1     24878.0
        AP2     19880.0
        AP3     99092.0
        AP4     77537.0
        AP5    410277.0
        AP6     81737.0
        '''
        
        # producción de cada sector = factor compuesto + compras intermedias = suma de todos los inputs
        self.Z0 = self.Y0 + self.X0.sum(axis=0)                                 # (len(ind), )
        '''
        AP1     42096.0
        AP2     77649.0
        AP3    427339.0
        AP4    258551.0
        AP5    723478.0
        AP6    122005.0
        '''
        
        '''
        Aquí hay un error de nomenclatura, los impuestos se toman de la fila del gobierno cuando
        parece mejor que sean de la fila 'idt' (INP), motivado porque en las primeras MCS no existía
        la cuenta INP. Como ambos se suman cuando es necesario, no afecta a los resultados
        '''
        # impuestos directos a los hogares (en realidad otros impuestos, cuando existe la uenta 'INP')
        # ingresos (ventas) del gobierno (fila gov) de los hogares (columnas dem)
        self.Tid0 = DataFrame(sam, index=gov, columns=dem)
        '''
                 C1       C2
        SP  87393.0  11712.0
        '''
        self.Tid0 = self.Tid0.to_numpy(dtype=np.float64).reshape(len(dem))        # (1, len(dem))
        
        # otros impuestos (en realidad estos son los impuestos directos cuando existe la cuenta INP) sobre
        # los productos pagados por los hogares
        self.Toi0 = DataFrame(sam, index=idt, columns=dem)
        if self.Toi0.empty:
            self.Toi0 = np.zeros(len(dem), dtype=np.float64)
        else:
            '''
                      C1      C2
            INP  67869.0  9108.0
            '''
            self.Toi0 = self.Toi0.to_numpy(dtype=np.float64).sum(axis=0).reshape(len(dem))
        
        # sumamos todos los impuestos pagados por los hogares al gobierno
        self.Td0 = self.Tid0 + self.Toi0

        # la separación de los impuestos pagados por las empresas en directos e indirectos no se
        # utiliza para nada, debería hacerse al recalcular la MCS como se hace con los impuestos de los hogares
        self.Tiz0 = DataFrame(sam, index=idt, columns=ind)
        self.Tiz0 = self.Tiz0.to_numpy(dtype=np.float64).sum(axis=0).reshape(len(ind))

        # impuestos indirectos (fila idt) pagados por los sectores (columnas 'ind'), en realidad son
        # los impuestos a la producción (directos) cuando existe esta cuenta (INP)
        self.Toz0 = DataFrame(sam, index=gov, columns=ind)
        '''
             AP1     AP2  AP3     AP4      AP5     AP6
        INP  0.0  1257.0  0.0  2453.0  16951.0  4467.0
        '''
        self.Toz0 = self.Toz0.to_numpy(dtype=np.float64).sum(axis=0).reshape(len(ind))

        # sumamos todos los impuestos pagados por las empresas al gobierno
        self.Tz0 = self.Tiz0 + self.Toz0
            
        # impuestos (fila idt) pagados por el gobierno (columnas 'gov')
        self.Tg0 = DataFrame(sam, index=idt, columns=gov)
        '''
                SP
        INP  494.0
        '''
        self.Tg0 = self.Tg0.to_numpy(dtype=np.float64).item()
        
        # impuestos (fila idt) pagados por el ahorro+inversión (columnas 'A-I') para la NSAM == 5
        self.Ti0 = DataFrame(sam, index=idt, columns=inv)
        '''
                 A-I
        INP  21052.3
        '''
        self.Ti0 = self.Ti0.to_numpy(dtype=np.float64).item()

        # impuestos (fila idt) pagados por el sector exterior (columnas 'SE') 
        self.Te0 = DataFrame(sam, index=idt, columns=ext)
        '''
                SE
        INP -92.19
        '''
        self.Te0 = self.Te0.to_numpy(dtype=np.float64).item()

        # aranceles (fila 'TRF') pagados por los sectores (columnas 'ind')
        self.Tm0 = DataFrame(sam, index=trf, columns=ind)                       # (1, len(ind))
        '''
             AP1  AP2  AP3  AP4  AP5  AP6
        TRF  NaN  NaN  NaN  NaN  NaN  NaN
        '''
        self.Tm0 = self.Tm0.to_numpy(dtype=np.float64).reshape(len(ind))        # (len(ind), )
        self.Tm0 = np.nan_to_num(self.Tm0, copy=True) # si no hay datos (NAN) se sustituye por 0
        
        # importaciones (fila 'EXT') pagadas por los sectores (columnas 'ind')
        self.M0 = DataFrame(sam, index=ext, columns=ind)                        # (1, len(ind))
        '''
               AP1      AP2       AP3   AP4      AP5  AP6
        SE  7977.0  36798.0  191303.0  16.0  38310.0  0.0
        '''
        self.M0 = self.M0.to_numpy(dtype=np.float64).reshape(len(ind))          # (len(ind), )
        
        # demanda de los hogares a cada sector = ventas de los sectores (filas 'ind') a los hogares (columna 'HOH')
        self.Xp0 = DataFrame(sam, index=ind, columns=dem)                       # (len(ind), len(dem))
        '''
                   C1       C2
        AP1    8118.0   1111.0
        AP2   15120.0   2069.0
        AP3   87781.0  12012.0
        AP4    3767.0    516.0
        AP5  307653.0  42096.0
        AP6    1878.0    257.0
        '''
        self.Xp0 = self.Xp0.to_numpy(dtype=np.float64).T.reshape(len(dem), len(ind))    # trasponemos para que el primer indice sea la demanda (len(dem), len(ind))

        # demanda del gobierno a cada sector = ventas de los sectores (filas 'ind') al gobierno (columna 'GOV')
        self.Xg0 = DataFrame(sam, index=ind, columns=gov)                       # (len(ind), 1)
        '''
                   SP
        AP1       0.0
        AP2       0.0
        AP3    7033.0
        AP4       0.0
        AP5   18708.0
        AP6  145552.0
        '''
        self.Xg0 = self.Xg0.to_numpy(dtype=np.float64).reshape(len(ind))        # (len(ind), )

        # 'INV' recolecta inversiones de los hogares, el gobierno y sector exterior (sus ahorros) y las emplea (transfiere) en los sectores.
        # inversión recibida por cada sector = ventas de los sectores (filas 'ind') al agente inversor ('INV') 
        # dicho de otra forma                = ingresos de los sectores aportados por la inversión ('INV')
        self.Xv0 = DataFrame(sam, index=ind, columns=inv)                       # (len(ind), 1)
        '''
                  A-I
        AP1     813.0
        AP2     309.0
        AP3   55736.0
        AP4  145896.0
        AP5   42578.0
        AP6       0.0
       '''
        self.Xv0 = self.Xv0.to_numpy(dtype=np.float64).reshape(len(ind))        # (len(ind), )
        
        # exportaciones de cada sector = ventas de los sectores (filas 'ind') al agente exportador 'EXT'
        self.E0 = DataFrame(sam, index=ind, columns=ext)                        # (len(ind), 1)   
        '''
                   SE
        AP1    8175.0
        AP2    9065.0
        AP3  131366.0
        AP4      88.0
        AP5   57988.0
        AP6      39.0
        '''
        self.E0 = self.E0.to_numpy(dtype=np.float64).reshape(len(ind))          # (len(ind), )
        
        # producto de Armington. Los demandantes no importan directamente, en su lugar consumen un producto, llamada de Armington,
        # que es una combinación del producido localmente y el importado (considerando que son sustituibles entre ellos)
        # resumiendo, los sectores lo que venden es su producto de Armington y 'Q0' será el total de cantidades vendidas por
        # cada sector al total de consumidores, que son las reflejadas en la MCS.
        self.Q0 = (
              self.Xp0.sum(axis=0)  # ventas de los sectores a todos hogares, sumar por columna porque Xp0[dem,ind]
            + self.Xg0              # ventas de los sectores al gobierno
            + self.Xv0              # ventas de los sectores al agente inversor
            + self.X0.sum(axis=1)   # ventas intermedias a otros sectores
        )                                                                       # (len(ind), )
        '''
        [40624.0, 108003.0, 502798.0, 273594.0, 764014.0, 147687.0]
        '''

        # cotizaciones a la seguridad social
        
        # de las empresas
        self.CssE0 = DataFrame(sam, index=css, columns=ind)                     # (1, len(ind))
        if self.CssE0.empty:
            self.CssE0 = np.zeros(len(ind), dtype=np.float64)
        else:
            '''
                   AP1     AP2      AP3      AP4      AP5      AP6
            CSS  654.0  1364.0  17216.0  12662.0  43263.0  21254.0
            '''
            self.CssE0 = self.CssE0.to_numpy(dtype=np.float64).reshape(len(ind))    # aportación de cada sector (len(ind), )
            self.CssE0 = np.nan_to_num(self.CssE0, copy=True) # si no hay datos (NAN) se sustituye por 0, hacerlo in situ (copy=False) produce error
        
        # de los hogares
        self.CssH0 = DataFrame(sam, index=css, columns=dem)
        if self.CssH0.empty:
            self.CssH0 = np.zeros(len(dem), dtype=np.float64)
        else:
            '''
                      C1      C2
            CSS  18548.0  2486.0
            '''
            self.CssH0 = self.CssH0.to_numpy(dtype=np.float64).reshape(len(dem))    # aportación de cada consumidor (len(dem), )
            self.CssH0 = np.nan_to_num(self.CssH0, copy=True) # si no hay datos (NAN) se sustituye por 0

        # ayudas (pagos) del gobierno a los sectores (empresas) = pago (aportación) de la columna 'AYD' a la fila 'ind'
        self.AgE0 = DataFrame(sam, index=ind, columns=ayd)
        if self.AgE0.empty:
            self.AgE0 = np.zeros(len(ind), dtype=np.float64)
        else:
            '''
                    AYD
            AP1  1928.0
            AP2     0.0
            AP3  1694.0
            AP4     0.0
            AP5     0.0
            AP6     0.0
            '''
            self.AgE0 = self.AgE0.to_numpy(dtype=np.float64).reshape(len(ind))  # (len(ind), )
            self.AgE0 = np.nan_to_num(self.AgE0, copy=True) # si no hay datos (NAN) se sustituye por 0

        # ayudas (pagos) del gobierno a los hogares = pago (aportación) de la columna 'AYD' a la fila 'dem'
        self.AgH0 = DataFrame(sam, index=dem, columns=ayd)
        if self.AgH0.empty:
            self.AgH0 = np.zeros(len(dem), dtype=np.float64)
        else:
            '''
                AYD
            C1  0.0
            C2  0.0
            '''
            self.AgH0 = self.AgH0.to_numpy(dtype=np.float64).reshape(len(dem))  # (len(dem), )
            self.AgH0 = np.nan_to_num(self.AgH0, copy=True) # si no hay datos (NAN) se sustituye por 0

        # tasa de impuesto a la producción = impuestos pagados / producción
        self.tauz = np.divide(self.Tz0, self.Z0, out=np.zeros_like(self.Tz0), where=self.Z0!=0)
        # self.tauz = (self.Tz0) / self.Z0        # (len(ind), ) / (len(ind), ) se dividen uno a uno
        # np.nan_to_num(self.tauz, copy=False)    # si no hay datos (NAN) se sustituye por 0
        self.tauz[self.tauz == np.inf] = 0      # porque algún elemento de F0 puede ser 0
        '''
        [0.0, 0.01618823165784492, 0.0, 0.009487489895610537, 0.02342987623673422, 0.03661325355518216]
        '''

        # tasa de aranceles a la importación = aranceles pagados / importación
        self.taum = np.empty(len(ind))
        for i in range(len(ind)):
            if self.M0[i] == 0:
                self.taum[i] = 0.
            else:
                self.taum[i] = self.Tm0[i] / self.M0[i]

        # D0, la demanda local debe pagar todos los costes de la producción local menos las ayudas recibidas y los ingresos por exportación, además
        # deberá pagar el coste de las importaciones con lo que D0 se completa a Q0 
        #   + Z0      producción bruta (que suma las compras intermedias y los factores de producción)
        #   + tauz    impuestos a la producción 
        #   + CssE0   pagos a la seguridad social
        #   - AgE0    ayudas recibidas
        #   - E0      ingresos de la exportación
        # las importaciones es lo que le falta a D0 para ser Q0
        self.D0 = (1 + self.tauz) * self.Z0 + self.CssE0 - self.AgE0 - self.E0  # (len(ind), )
        '''
        [32647.0, 71205.0, 311495.0, 273578.0, 725704.0, 147687.0]
        '''

        # ahorro de los hogares = pago (aportación) de la columna 'HOH' a la fila 'INV'
        self.Sp0 = DataFrame(sam, index=inv, columns=dem)                       # (1, len(dem))
        '''
                   C1       C2
        A-I  115274.0  15437.0
        '''
        self.Sp0 = self.Sp0.to_numpy(dtype=np.float64).reshape(len(dem))        # ahorro de cada consumidor (len(dem), )
        
        # ahorro a largo plazo de los hogares
        self.Alp0 = DataFrame(sam, index=dem, columns=alp)
        # misteriosamente, a pesar de que no existe una columna 'alp' devuelve una slice
        if self.Alp0.empty or np.all(np.isnan(self.Alp0)):
            self.Alp0 = np.zeros((len(dem),len(h)), dtype=np.float64)
        else:
            self.Alp0 = self.Alp0.to_numpy(dtype=np.float64).reshape(len(dem),len(h))  # (len(dem), )
            self.Alp0 = np.nan_to_num(self.Alp0, copy=True) # si no hay datos (NAN) se sustituye por 0

        # ahorro del gobierno = pago (aportación) de la columna 'GOV' a la fila 'INV'
        self.Sg0 = DataFrame(sam, index=inv, columns=gov)
        '''
                  SP
        A-I  26295.0
        '''
        self.Sg0 = self.Sg0.to_numpy(dtype=np.float64).item()                   # () escalar

        # ahorro de la seguridad social
        if self.PssH0.sum().item() == 0:
            # las pensiones las paga el gobierno, por lo que la seguridad social le transfiere todos sus ingresos
            self.Sc0 = 0.
        else:
            self.Sc0 = self.CssE0.sum() + self.CssH0.sum() - self.PssH0.sum().item()    # () escalar

        # balanza de pagos = ahorro exterior = pago (aportación) de la columna 'EXT' a la fila 'INV'
        # esto no parece correcto si hay algún pago o ingreso adicional en el sector exterior, como
        #por ejemplo: un pago de impuestos en la columna de exportaciones (positivo o negativo)
        self.Sf0 = DataFrame(sam, index=inv, columns=ext)
        '''
                  SE
        A-I  67683.0
        '''
        self.Sf0 = self.Sf0.to_numpy(dtype=np.float64).item()                   # () escalar
        
        # variable de holgura para corregir que las aportaciones a la seguridad social y las ayudas del gobierno
        # no son proporcionales a la producción bruta (Z)
        self.Apz0 = 0.                                                          # () escalar
        self.PobAct = ecua.poblacion_activa_PobAct(INDICE_F_TRA, self.FF0, PARO_INICIAL)

class parametros(object):
    def __init__(self, datos, ndem, nsec, INDICE_F_TRA, DEM_ESENCIALES, CON_ESENCIALES, SIGMA_CES_DEMANDA):
        # elasticidad de sustitución, entre local e importación, del producto de Argminton (CES)
        # la elasticidad de sustitución es la misma en cualquier punto a lo largo de una isocuanta, sin importar cual sea la relación en que son utilizados los insumos. 
        # variable exógena puesta a 2.
        '''
        La relación marginal de sustitución mide la relación en que el consumidor está dispuesto a sustituir un bien por el otro. 
        La Tasa Marginal de Sustitución (TMS) nos indica cuánto se debe modificar la cantidad de un bien cuando aumentamos o disminuimos la
        cantidad de otro, todo con el objetivo de mantener la utilidad o la producción constante. Es el cociente de las productividades marginales de los factores
        La TMS mide la pendiente de la curva de utilidad ya que es la derivada
        TMS = alfa1 / alfa2 * (factor2 / factor1) ** (1 - ro)

        sigma    :  elasticidad de sustitución  = 1 / (1 - ro)
                    Mide la facilidad de sustituir un factor por otro
                    La elasticidad de sustitución, es el porcentaje de cambio en el ratio de utilización o consumo de dos bienes, dividido por el porcentaje de cambio de la TMS.

        eta = ro :  parámetro de sustituciín (<= 1)
        ro < 1   :  las curvas de indiferencia son estrictamente convexas
                    ro = 0  -> Cobb Douglas
                    ro = -infinito -> Leontief, elasticidad de sustitución 0, se dice que son complementos perfectos
                        x < y -> recta vertical   : Unidades adicionalesde y, manteniendo x constante no cambian la utilidad,
                        es decir, unidades adicionales de y son neutrales a la utilidad.
                        x > y -> recta horizontal : Unidades adicionalesde x, manteniendo y constante no cambian la utilidad,
                        es decir, unidades adicionales de x son neutrales a la utilidad.
        ro = 1   :  las curvas de indiferencia son líneas rectas. sustitutos perfectos (elasticidad de sustitución infinita)
        ro > 1   :  las curvas de indiferencia son concavas, para evitar este caso se exige 'ro <= 1'

        Si un país importa un determinado producto es porque es menos eficiente en su producción que los otros paises.

        Si el producto Y es más valioso cuanto más escaso, neceitamos un gran incremento de X para compensar una pequeña reducción de Y, lo
        cual se cumple en una curva convexa pero no en una cóncava.
        '''
        self.sigma = np.zeros(nsec, dtype=np.float64)
        self.sigma.fill(2.)
        self.eta = (self.sigma - 1.) / self.sigma   # normalmente se anota como ρ (ro)
        # sigma = 1. / (1. - eta)

        # elasticidad de transformación entre local y exportación (CET)
        # variable exógena puesta a 2.
        '''
        Relación marginal de transformación
        La relación marginal de transformación (RMT) se puede definir como el número de unidades del bien X que tienen que dejar de ser producidas con el fin de producir una
        unidad adicional del bien Y, mientras se mantiene constante la utilización de factores de producción y la tecnología que se utiliza. Se trata de la relación entre la
        producción de diferentes productos, mientras se mantiene constante el mismo nivel de factores de producción. Se puede determinar utilizando la siguiente fórmula:
        RMT = dX/dY

        Frontera de posibilidades de producción
        La frontera de posibilidades de producción (FPP) representa la cantidad de producción que se puede obtener de una determinada cantidad de factores de producción utilizando una
        tecnología dada. Dependiendo de la tecnología, la FPP tendrá una forma u otra.

        Frontera de posibilidades de produccion, como se puede ver en la figura adyacente, esta FPP (curva azul) tiene pendiente descendiente.
        Esta pendiente, que es igual a la relación marginal de transformación entre X e Y, nos muestra cómo, con el fin de aumentar la producción de X, la
        cantidad de Y debe disminuir. De hecho, la relación marginal de transformación mide la desventaja de producir más X en términos de Y.

        Esta frontera determina la producción máxima (de ambos X e Y) que se pueden obtener dada la tecnología. La producción en el punto A produce más cantidad de Y y
        menos de X que la producción en el punto B. Sin embargo, ambos son técnicamente eficientes, ya que maximizan la producción total. Por ejemplo, la
        producción en el punto C es técnicamente ineficiente, ya que podemos reajustar los factores para alcanzar cualquier punto sobre la FPP. Por otro lado, el
        punto D es inalcanzable dada la tecnología, siendo esta la razón por la que está fuera de la FPP.

        Si una empresa decide aumentar la producción de un producto, esto puede venir con el coste de reducir la producción de otro.

        Coste de oportunidad
        Desde un punto de partida en la frontera, si no hay aumento de recursos productivos, aumentar la producción de un primer bien implica disminuir la
        producción de un segundo, ya que es necesario transferir recursos al primero y alejarlos del segundo. Los puntos a lo largo de la curva describen la
        disyuntiva entre los bienes. El sacrificio en la producción del segundo bien se denomina coste de oportunidad (ya que aumentar la producción del primero
        implica perder la oportunidad de producir cierta cantidad del segundo -el coste de oportunidad de un bien es la cantidad de otro bien al que hay que renunciar
        para para obtener el primero-). El coste de oportunidad se mide por el número de unidades del segundo bien que se sacrifican a cambio de una o más
        unidades del primero. Si el coste de oportunidad es creciente, la FPP será cóncava​, a cada paso estaremos más por debajo de
        la recta en la cual el coste de oportunidad es constante. La isocuante es cóncava.

        El coste de oportunidad está determinado por la ley de rendimientos decrecientes (a medida que se dedican más recursos para producir un bien, el aumento marginal de
        la producción disminuirá cada vez más.). Si pasamos del estremo en el que todo lo que se produce es X y nada Y,
        a producir algo de Y a costa de un poco de X, tendremos un gran aumento del rendimiento en pasar de nada a algo en Y (el rendimiento irá decreciendo según aumenta Y) y
        una pequeña disminución del rendimiento de pasar de todo X a todo X menos un poco (la pérdida de rendimiento ira en aumento al reducir X).
        Si un país exporta un determinado producto es porque es más eficiente en su producción que los otros paises (ventaja comparativa).
        '''
        self.psi = np.zeros(nsec, dtype=np.float64)
        self.psi.fill(2.)
        self.phi = (self.psi + 1.) / self.psi
        '''
        calibrar
        '''
        # coeficientes de participación (alfa) de los productos en la utilidad de la demanda
        self.alfa = ecua.demanda_CobbDouglas_alfa(datos.Xp0)
        #self.alfa = ecua.demanda_CobbDouglas_alfa(datos.FF0, datos.PssH0, datos.AgH0, datos.Sp0, datos.Td0, datos.CssH0, datos.Xp0, datos.pF0, datos.pQ0, 0, np.zeros((ncon,nsec), dtype=np.float64))
        if DEM_ESENCIALES:
            renta = ecua.demanda_StoneGeary_renta(datos.FF0, datos.PssH0, datos.AgH0, datos.Sp0, datos.Td0, datos.CssH0, datos.Xp0, CON_ESENCIALES, datos.pF0, datos.pQ0)
            if np.any(renta <= 0):
                print('Renta menor o igual a 0')
                for i in range(len(renta)):
                    print('{:3} {:12.5e}'.format(i + 1, renta[i]))
                sys.exit()
            self.alfa_esen = ecua.demanda_StoneGeary_alfa(datos.FF0, datos.PssH0, datos.AgH0, datos.Sp0, datos.Td0, datos.CssH0, datos.Xp0, CON_ESENCIALES, datos.pF0, datos.pQ0)
        else:
            self.alfa_esen = np.zeros((ndem,nsec), dtype=np.float64)

        self.sigma_ces = SIGMA_CES_DEMANDA
        self.eta_ces = (self.sigma_ces - 1.) / self.sigma_ces
        self.alfa_ces = ecua.demanda_CES_alfa(self.sigma_ces, datos.Xp0)

        # coeficientes de participación (beta) de los factores en la función del factor compuesto de cada sector
        self.beta  = ecua.demanda_CobbDouglas_beta(datos.F0)
        # coeficiente de escala de la función del factor compuesto
        self.b     = ecua.demanda_CobbDouglas_b(datos.Y0, datos.F0, self.beta)
        
        # coeficientes de consumos intermedios
        self.ax    = ecua.coeficientes_consumos_intermedios_ax(datos.X0, datos.Z0)

        # coeficientes del factor compuesto
        self.ay    = ecua.coeficientes_factor_compuesto_ay(datos.Y0, datos.Z0)

        # coeficientes de participación de la demanda del gobierno
        self.mu    = ecua.coeficientes_demanda_gobierno_mu(datos.Xg0)

        # coeficientes de participaciones en las inversiones
        self.landa = ecua.coeficientes_inversiones_landa(datos.Xv0, datos.Sp0, datos.Sg0, datos.Sc0, datos.epsilon, datos.Sf0, datos.Ti0, datos.Te0)

        # ------
        # elasticidad de sustitución, entre local e importación, del producto de Argminton (Utilidad CES)

        # coeficientes de participación de la importación (deltam) y la producción local (deltad) en la función del producto de Armington
        (self.deltam, self.deltad) = ecua.coeficientes_armington_deltam_deltad(datos.taum, self.eta, datos.M0, datos.D0)
        # coeficiente de escala de la función de Armington
        self.gamma = ecua.coeficiente_escala_armington_gamma(datos.Q0, self.deltam, self.deltad, self.eta, datos.M0, datos.D0)
        # ------
        
        # ------
        # elasticidad de transformación entre local y exportación (utilidad CET)

        # coeficiente de participación en la CET de la demanda local
        self.xid   = ecua.coeficiente_CET_local_xid(self.phi, datos.E0, datos.D0)
        # coeficiente de participación en la CET de la exportación
        self.xie   = ecua.coeficiente_CET_exportacion_xie(self.phi, datos.E0, datos.D0)
        xid_neg = [self.xid < 0.][0]
        self.xid[xid_neg] = 0.
        self.xie[xid_neg] = 1.
        xie_neg = [self.xie < 0.][0]
        self.xid[xie_neg] = 1.
        self.xie[xie_neg] = 0.
        # coeficiente de escala de la CET de exportación
        self.teta  = ecua.coeficiente_escala_CET_teta(datos.Z0, self.xie, datos.E0, self.xid, datos.D0, self.phi)
        # ------

        # propensión al ahorro de los hogares
        self.ssp   = ecua.propension_ahorro_hogares_ssp(datos.Sp0, datos.FF0, datos.PssH0)
        # tasa de impuestos directos
        self.taud     = ecua.tasa_impuestos_directos_taud(datos.Td0, datos.FF0, datos.PssH0)
        self.taud_id  = ecua.tasa_impuestos_directos_taud(datos.Tid0, datos.FF0, datos.PssH0)
        self.taud_oi  = ecua.tasa_impuestos_directos_taud(datos.Toi0, datos.FF0, datos.PssH0)
        # tasa de impuestos al ahorro-inversion
        self.tai = ecua.tasa_impuestos_directos_tai(datos.Ti0, datos.FF0, INDICE_F_TRA)

        # propensión al ahorro del gobierno
        self.ssg   = ecua.propension_ahorro_gobierno_ssg(datos.Sg0, datos.Td0, datos.Tz0, datos.Tm0, datos.Tg0, datos.Ti0, datos.Te0, datos.AgE0, datos.AgH0, datos.CssE0, datos.CssH0, datos.PssH0)

        # ayudas del gobierno a las empresas
        self.cage = ecua.coeficiente_ayudas_gobierno_empresas_cage(datos.AgE0, datos.Td0, datos.Tz0, datos.Tm0, datos.Tg0, datos.Ti0, datos.Te0)
        
        # ayudas del gobierno a los hogares
        self.cagh = ecua.coeficiente_ayudas_gobierno_hogares_cagh(datos.AgH0, datos.Td0, datos.Tz0, datos.Tm0, datos.Tg0, datos.Ti0, datos.Te0)
        
        # ATENCION se está suponiendo que el trabajo es la coluna 1 (segunda columna) de FF

        # porcentaje de la seguridad social sobre el empleo de factor laboral por los sectores (F0)
        divisor = copy.deepcopy(datos.F0[:,INDICE_F_TRA])
        divisor[divisor == 0] = 1.      # para evitar divisiones por 0
        self.ctzsse = datos.CssE0 / divisor
        np.nan_to_num(self.ctzsse, copy=False)      # si no hay datos (NAN) se sustituye por 0
        self.ctzsse[self.ctzsse == np.inf] = 0      # porque algún elemento de F0 puede ser 0

        self.ctzssez = np.divide(datos.CssE0, datos.Z0, out=np.zeros_like(datos.CssE0), where=datos.Z0!=0)
        self.ctzagez = np.divide(datos.AgE0, datos.Z0, out=np.zeros_like(datos.AgE0), where=datos.Z0!=0)

        # porcentaje de la seguridad social sobre la prestación de factor laboral por los hogares (FF0)
        # las pensiones no cotizan a la seguridad social

        divisor = copy.deepcopy(datos.FF0[:,INDICE_F_TRA])
        divisor[divisor == 0] = 1.      # para evitar divisiones por 0
        self.ctzssh = datos.CssH0 / divisor
        np.nan_to_num(self.ctzssh, copy=False)      # si no hay datos (NAN) se sustituye por 0
        self.ctzssh[self.ctzssh == np.inf] = 0      # porque el denominador puede ser 0

