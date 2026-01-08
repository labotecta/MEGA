# import packages
import numpy as np
from pandas import Series, DataFrame


class model_data(object):

    def __init__(self, sam, h, u, ind):
        '''
        Esta función inicializa los valores de las variables usando los datos de la SAM. Se llama automáticamente cuando se crea una variable de esta clase.
        En realidad todas las variables creadas aquí no son tales ya que no cambian de valor durante la ejecución del modelo por lo que realmente son parámetros
        Están en esta clase porque es la misma que sirve para el modelo grande y tal vez en este si sean variables

        Args:
            sam (DataFrame): DataFrame conteniendo la SAM

        Returns:
            model_data (data class): Un objeto 'model_data' para su uso en el modelo CGE. Esta clase sólo es un almacen para las variables, las empaqueta
            para pasar información en las llamadas a determinadas funciones con un solo parámetro que es un objeto de esta clase.
        '''
        # self es la referencia al objeto que se crea al asignar esta clase a una variable, lo añade python,
        # por lo que no se especifica (no se sabe de antemano en que parte de la memoria lo situará python) en la sentencia que crea una variable de esta clase

        # impuestos a la producción (production tax) para ind = ("AGR", "OIL", "IND", "SER"), valores de la fila 'ACT' para los sectores
        self.Tz0 = DataFrame(sam, index=["ACT"], columns=list(ind))
        '''
             AGR  OIL  IND  SER
        ACT   -4  0.0    1   12
        '''
        # aranceles de importación (import tariff) para ind = ("AGR", "OIL", "IND", "SER"), valores en la fila 'IDT' para los sectores
        self.Tm0 = DataFrame(sam, index=["IDT"], columns=list(ind))
        '''
             AGR  OIL  IND  SER
        IDT    1  0.0   20    0
        '''
        # entradas (compras -consumos -) que hacen los factores h = ("LAB", "CAP", "LAND", "NTR") de los sectores ind = ("AGR", "OIL", "IND", "SER") (the h-th factor input by the i-th firm)
        # matriz 2D que contiene los valores en las filas h (factores) de las columnas ind de la SAM (sectores)
        self.F0 = DataFrame(sam, index=list(h), columns=list(ind))
        '''
              AGR         OIL  IND  SER
        LAB     7   28.000000   87  429
        CAP    26   68.000000  351  606
        LAND   24    0.000000    0    0
        NTR     0  890.435052    0    0
        '''
        # suma para cada sector de sus consumos de todos los factores (axis=0 suma de los valores en la columna, luego un valor para cada columna) (composite factor (value added))
        self.Y0 = self.F0.sum(axis=0)   # una Serie
        '''
        AGR      57.000000
        OIL     986.435052
        IND     438.000000
        SER    1035.000000
        '''
        # imputs intermedios, matriz con las transacciones entre sectores (como en las TIO), cada fila es lo que vende un sector a los demas y las columnas lo que compra (intermediate input)
        self.X0 = DataFrame(sam, index=list(ind), columns=list(ind))
        '''
             AGR   OIL  IND  SER
        AGR    7   2.0   56   15
        OIL    0   4.0  134   11
        IND   15  13.0  316  312
        SER    9   8.0  147  250
        '''
        # total compras de cada sector a todos los demás, suma de los valores en la columna de cada sector (total intermediate input by the j-th sector)
        self.Xx0 = self.X0.sum(axis=0)  # una Serie
        '''
        AGR     31.0
        OIL     27.0
        IND    653.0
        SER    588.0
        '''
        # para cada sector, suma de las compras a otros sectores y a los factores, lo que es igual a la producción del sector (producto) (output of the j-th good)
        self.Z0 = self.Y0 + self.Xx0    # una Serie
        '''
        AGR      88.000000
        OIL    1013.435052
        IND    1091.000000
        SER    1623.000000
        '''
        # consumo por los hogares de los distintos productos (household consumption of the i-th good), valores en la columna "HOH", vector columna
        self.Xp0 = DataFrame(sam, index=list(ind), columns=["HOH"])
        '''
               HOH
        AGR   34.0
        OIL    0.0
        IND  396.0
        SER  408.0
        '''
        # consumo por el gobierno de los distintos productos  (government consumption), valores en la columna "GOV", vector columna
        self.Xg0 = DataFrame(sam, index=list(ind), columns=["GOV"])
        '''
             GOV
        AGR    2
        OIL    0
        IND  265
        SER  611
        '''
        # demanda (consumo) de inversión (investment demand), valores en la columna "INV", vector columna 
        self.Xv0 = DataFrame(sam, index=list(ind), columns=["INV"])
        '''
             INV
        AGR    0
        OIL    0
        IND  115
        SER  370
        '''
        # exportaciones (exports)
        # un dataframe con una sola columna que contiene los valores de la columna EXT para los sectores, cada valor es una lista de un elemento, ej: [306.0]
        self.E0 = DataFrame(sam, index=list(ind), columns=["EXT"])
        '''
                    EXT
        AGR    2.000000
        OIL  866.435052
        IND  306.000000
        SER   34.000000
        '''
        # en un DataFrame cada columna es una Serie y cuando extraemos una columna, extraemos la Serie
        # por lo que 'E0' pasa a ser una Serie
        self.E0 = self.E0["EXT"]
        '''
        AGR      2.000000
        OIL    866.435052
        IND    306.000000
        SER     34.000000
        '''
        # importaciones (imports)
        # un dattaframe con una sola línea fila que contiene las columnas de 'ind' (sectores) en la fila EXT
        self.M0 = DataFrame(sam, index=["EXT"], columns=list(ind)) 
        '''
             AGR  OIL  IND  SER
        EXT   33  2.0  626  202
        '''
        # con esta sentencia convertimos el dataframe en una Serie con valores, no vale hacer self.Mo["EXT"] que intentaría extraer una columna (que no existe) cuando
        # lo que queremos es extraer una fila, que es lo hace 'loc' cuando su argumento corresponde a una sola fila, si hubier varias produciría un dataframe.
        self.M0 = self.M0.loc["EXT"]
        '''
        AGR     33.0
        OIL      2.0
        IND    626.0
        SER    202.0
        '''
        # tasa de impuesto a la producción de cada sector (production tax rate) =
        # impuesto a la producción del sector (valor ACT en la columna del sector)  / producción del sector (suma de todos los valores en su columna, incluido ACT)
        # tambien está definido como parámetro con la misma fórmula, puede ser que aquí sea solo un cálculo intermedio para el cálculo de 'D0'
        tauz = self.Tz0 / self.Z0   # es una dataframe
        '''
                  AGR  OIL       IND       SER
        ACT -0.045455  0.0  0.000917  0.007394
        '''
        # Añadimos los impuestos a las producciones de los sectores y les restamos las exportaciones, sería el consumo doméstico con impuestos
        # tauz.loc["ACT"] es una Serie porque el dataframe 'tauz' sólo tiene una fila 'ACT'
        self.D0 = (1 + tauz.loc["ACT"]) * self.Z0 - self.E0
        '''
                  AGR  OIL       IND       SER
        ACT -0.045455  0.0  0.000917  0.007394
        '''
        # Calcula agregados
        self.XXg0 = self.Xg0.sum()      # consumo del gobierno del total de productos
        '''
        GOV    878
        '''
        self.pWm = np.ones(len(ind))    # indice de precios de importación para cada sector
        '''
        array([1., 1., 1., 1.])
        '''
        # lo transformamos en una Serie con las etipetas 'ind'
        self.pWm = Series(self.pWm, index=list(ind))
        '''
        AGR    1.0
        OIL    1.0
        IND    1.0
        SER    1.0
        '''

class parameters(object):

    def __init__(self, d, ind):
        '''
        Esta función asigna valores a los parámetros del modelo usando los datos empaquetados en un objeto de la clase 'model_data'.
        Se llama automáticamente cuando se crea una variable de esta clase.

        Args:
            d (data class): Objeto de la case clase 'model_data'
            ind (list): Lista de nombres de los sectores industriales, ind = ("AGR", "OIL", "IND", "SER")

        Returns:
            parameters (parameters class): Un objeto 'parameters' para su uso en el modelo CGE. Esta clase sólo es un almacen para las parámetros, las empaqueta
            para pasar información en las llamadas a determinadas funciones con un solo parámetro que es un objeto de esta clase.
        '''
        # coeficientes de participación en la función de producción. Para cada factor 'h', es el tanto por uno de lo que el factor consume de cada sector 'ind'
        # (share parameter in production function)
            # d.F0 = matriz 2D que contiene los valores en las filas h (factores) de las columnas ind de la SAM (sectores)
            # d.Y0 = suma para cada sector de sus consumos de todos los factores (axis=0 suma de los valores en la columna, luego un valor para cada columna) (composite factor (value added))
        self.beta = d.F0 / d.Y0     # un dataframe
        '''
                   AGR       OIL      IND       SER
        LAB   0.122807  0.028385  0.19863  0.414493
        CAP   0.456140  0.068935  0.80137  0.585507
        LAND  0.421053  0.000000  0.00000  0.000000
        NTR   0.000000  0.902680  0.00000  0.000000
        '''
        # para cada sector: coeficientes de consumos de  los sectores (imputs intermedios). Matriz 2D sectores x sectores (intermediate input requirement coefficient)
            # d.X0 = imputs intermedios, transacciones entre sectores (intermediate input)
            # d.Z0 = producción de cada sector (compras a otros sectores y a los factores) (output of the j-th good)
        self.ax = d.X0 / d.Z0  
        '''
                  AGR       OIL       IND       SER
        AGR  0.079545  0.001973  0.051329  0.009242
        OIL  0.000000  0.003947  0.122823  0.006778
        IND  0.170455  0.012828  0.289643  0.192237
        SER  0.102273  0.007894  0.134739  0.154036
        '''
        # para cada sector: coeficiente de participación del total de sus consumos de factores, sobre su total de consumos (composite factor input requirement coefficient)
            # d.Y0 = suma para cada sector de sus consumos de todos los factores (composite factor (value added))
            # d.Z0 = producción de cada producto (output of the j-th good)
        self.ay = d.Y0 / d.Z0
        '''
        AGR    0.647727
        OIL    0.973358
        IND    0.401467
        SER    0.637708
        '''
        # tasa de impuesto a la producción de cada sector (production tax rate) =
        # impuesto a la producción del sector (valor ACT en la columna del sector -d.Tz0-)  / producción del sector (suma de todos los valores en su columna, incluido ACT -d.Z0-)
        self.tauz = d.Tz0 / d.Z0
        '''
                  AGR  OIL       IND       SER
        ACT -0.045455  0.0  0.000917  0.007394
        '''
        self.tauz = self.tauz.loc["ACT"]
        '''
        AGR   -0.045455
        OIL    0.000000
        IND    0.000917
        SER    0.007394
        '''
        # tasa de aranceles de importación
        # import tariff rate
            # d.Tm0 = aranceles de importación (import tariff) para ind = ("AGR", "OIL", "IND", "SER")
            # d.M0 = una fila con los valores de EXT para los sectores, es una lista dode cada elemento (en nuestro caso sólo 1) es a su vez una lista, ej: [[ 33.,   2., 626., 202.]]

        self.taum = d.Tm0 / d.M0
        '''
                  AGR  OIL       IND  SER
        IDT  0.030303  0.0  0.031949  0.0
        '''
        self.taum = self.taum.loc["IDT"]
        '''
        AGR    0.030303
        OIL    0.000000
        IND    0.031949
        SER    0.000000
        '''
        # propensión a la importación. Añadimos los aranceles a las exportaciones (d.M0) y lo dividimos por estas mismas exportaciones con aranceles más el consumo domestico con impuestos
        # import propensity
        self.deltam = (1 + self.taum) * d.M0 / ((1 + self.taum) * d.M0 + d.D0)
        '''
        self.deltam
        AGR    0.293103
        OIL    0.013423
        IND    0.451117
        SER    0.112035
        '''
