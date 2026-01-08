
import numpy as np
from pandas import Series, DataFrame
import ecuaciones_estandar as simple

class datos(object):

    def __init__(self, sam, h, u, ind, dem):
        '''
        los valores de la SAM son importes y necesitamos cantidades, pero podemos elegir un sistema
        de unidades `para las cantidades de forma que todos los productos y factores tengan precio igual a 1.
        el sistema de unidades no afecta a la 'economía' de las transacciones. Si afecta al cálculo de impuestos, pero
        en este modelo no tenemos. 
        '''
        self.pX0 = np.ones(len(ind))        # precio de los sectores
        self.pF0 = np.ones(len(h))          # precio de los factores

        '''
        Vamos a extraer de la SAM algunos valores (X0 y F0) que se necesitan para calibrar los parámetros y
        el valor de una variable (FF) que consideraremos exógena
        '''

        # extraemos de las filas de los sectores la columna de la demanda (que es la producción del sector)
        self.X0 = DataFrame(sam, index=list(ind), columns=list(dem))
        '''
                 HOH
            BRD   15
            MLK   35
        '''
        # asegurarse que es una matriz 2D (con un sólo consumidor, no lo es)
        self.X0 = self.X0.to_numpy().reshape(len(dem),len(ind))


        # factores empleados por cada sector
        # primero, extraemos las columnas de los sectores de las filas de los factores
        self.F0 = DataFrame(sam, index=list(h), columns=list(ind))
        '''
                 BRD  MLK
            CAP    5   20
            LAB   10   15
        '''
        # luego, la trasponemos para que las filas sean los sectores, ya que estamos extrayendo las filas de los factores (index=h)
        self.F0 = self.F0.T
        '''
                 CAP  LAB
            BRD    5   10
            MLK   20   15
        '''
        # asegurarse que es una matriz 2D (con un sólo factor, no lo es)
        self.F0 = self.F0.to_numpy().reshape(len(ind),len(h))

        # 'FF' es el total de cada uno de los factores, aportados por los hogares, a todos los sectores
        self.FF = DataFrame(sam, index=list(dem), columns=list(h))
        '''
                 CAP  LAB
            HOH   25   25
        '''
        # se puede obtener alternativamente sumando la utilización de los factores por todos los sectores
        comprobacion = self.F0.sum(axis=0)

        assert (comprobacion == self.FF).to_numpy().all(), 'Error en la utilización de los factores'

class parametros(object):

    def __init__(self, datos):
        '''
        Tenemos que calibrar los:
            coeficientes de participación (alfa) de los productos en la utilidad de la demanda (2 valores)
            coeficientes de participación (beta) de los factores en la función de producción (2 x 2 valores)
            el coeficiente de escala de la función de producción (2 valores)
            cantidad total de factores suministrados por la demanda a las empresas (2 valores, uno por valor)
        '''
        self.alfa = simple.alfa_CobbDouglas(datos.pX0, datos.X0)
        self.beta = simple.beta_CobbDouglas(datos.pF0, datos.F0)
        self.b    = simple.b_CobbDouglas(datos.pF0, datos.F0, datos.pX0, self.beta)
