
import numpy as np
from pandas import Series, DataFrame
import ecuaciones_estandar as ecua
'''
Todas las matrices las guardaremos como numpy arrays y los sectores siempre en filas

'''
class datos(object):

    def __init__(self, sam, h, u, ind, dem):
        '''
        los valores de la SAM son importes y necesitamos cantidades, pero podemos elegir un sistema
        de unidades `para las cantidades de forma que todos los productos y factores tengan
        precio igual a 1.
        el sistema de unidades no afecta a la 'economía' de las transacciones. Si afecta al cálculo
        de impuestos, pero en este modelo no tenemos. 
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

        self.epsilon = np.ones(1)           # tipo de cambio (cotización)

        # consumos (imputs) intermedios de los sectores en las columnas y ventas (outputs) intermedias en las filas
        self.X0 = DataFrame(sam, index=list(ind), columns=list(ind))
        '''
             BRD  MLK
        BRD   21    8
        MLK   17    9
        '''
        self.X0 = self.X0.to_numpy(dtype=np.float64)    # (2, 2)

        # factores empleados por cada sector
        # primero, extraemos las columnas de los sectores de las filas de los factores
        self.F0 = DataFrame(sam, index=list(h), columns=list(ind))
        '''
             BRD  MLK
        CAP   20   30
        LAB   15   25
        '''
        # luego, la trasponemos para que las filas sean los sectores, ya que estamos extrayendo las filas de los factores (index=h)
        self.F0 = self.F0.T
        '''
             CAP  LAB
        BRD   20   15
        MLK   30   25
        '''
        self.F0 = self.F0.to_numpy(dtype=np.float64)    # (2, 2)

        # 'FF' es el total de cada uno de los factores, aportados por los hogares, a todos los sectores
        self.FF = DataFrame(sam, index=list(dem), columns=list(h))      # (1, 2)
        '''
             CAP  LAB
        HOH   50   40
        '''
        self.FF = self.FF.to_numpy(dtype=np.float64).reshape(len(h))    # (2, )

        # factor compuesto para cada sector, igual a la suma de los factores utilizados por el sector en la SAM
        self.Y0 = self.F0.sum(axis=1)   # (2, )
        '''
        BRD: 35
        MLK: 55
        '''
        
        # producción de cada sector = factor compuesto + ventas intermedias
        self.Z0 = self.Y0 + self.X0.sum(axis=0)     # (2, )
        '''
        BRD    73
        MLK    72
        '''
        
        # impuestos directos a los hogares = ventas del govierno (fila GOV) a los hogares (columna dem -HOH-)
        self.Td0 = DataFrame(sam, index=['GOV',], columns=list(dem))    # (1, 1)
        '''
             HOH
        GOV   23
        '''
        self.Td0 = self.Td0.to_numpy(dtype=np.float64).item()    # () escalar
        
        # impuestos indirectos (fila 'IDT') pagados por los sectores (columnas 'ind')
        self.Tz0 = DataFrame(sam, index=['IDT',], columns=list(ind))
        '''
             BRD  MLK
        IDT    5    4
        '''
        self.Tz0 = self.Tz0.to_numpy(dtype=np.float64).reshape(len(ind))
        
        # aranceles (fila 'TRF') pagados por los sectores (columnas 'ind')
        self.Tm0 = DataFrame(sam, index=['TRF',], columns=list(ind))    # (1, 2)
        '''
             BRD  MLK
        TRF    1    2
        '''
        self.Tm0 = self.Tm0.to_numpy(dtype=np.float64).reshape(len(ind))    # (2, )
        
        # importaciones (fila 'EXT') pagadas por los sectores (columnas 'ind')
        self.M0 = DataFrame(sam, index=['EXT',], columns=list(ind)) # (1, 2)
        '''
             BRD  MLK
        EXT   13   11
        '''
        self.M0 = self.M0.to_numpy(dtype=np.float64).reshape(len(ind))  # (2, )
        
        # demanda de los hogares a cada sector = ventas de los sectores (filas 'ind') a los hogares (columna 'HOH')
        self.Xp0 = DataFrame(sam, index=list(ind), columns=list(dem))   # (2, 1)
        '''
             HOH
        BRD   20
        MLK   30
        '''
        self.Xp0 = self.Xp0.to_numpy(dtype=np.float64).reshape(len(ind))    # (2, )
        
        # demanda del gobierno a cada sector = ventas de los sectores (filas 'ind') al gobierno (columna 'GOV')
        self.Xg0 = DataFrame(sam, index=list(ind), columns=['GOV',])        # (2, 1)
        '''
             GOV
        BRD   19
        MLK   14
        '''
        self.Xg0 = self.Xg0.to_numpy(dtype=np.float64).reshape(len(ind))    # (2, )

        # 'INV' recolecta inversiones de los hogares, el gobierno y sector exterior (sus ahorros) y las emplea (transfiere) en los sectores
        # inversión recibida por cada sector = ventas de los sectores (filas 'ind') al agente inversor ('INV') 
        # dicho de otra forma                = ingresos de los sectores aportados por 'INV'
        self.Xv0 = DataFrame(sam, index=list(ind), columns=['INV',])        # (2, 1)
        '''
              INV
        BRD   16
        MLK   15
       '''
        self.Xv0 = self.Xv0.to_numpy(dtype=np.float64).reshape(len(ind))    # (2, )
        
        # exportaciones de cada sector = ventas de los sectores (filas 'ind') al agente exportador 'EXT'
        self.E0 = DataFrame(sam, index=list(ind), columns=['EXT',])         # (2, 1)   
        '''
             EXT
        BRD    8
        MLK    4
        '''
        self.E0 = self.E0.to_numpy(dtype=np.float64).reshape(len(ind))      # (2,)
        
        # producto de Armington. Los demandantes no importan directamente, en su lugar consumen un producto, llamada de Armington,
        # que es una combinación del producido localmente y el importado (considerando que son sustituibles entre ellos)
        # resumiendo, los sectores lo que venden es su producto de Armington y 'Q0' será el total de cantidades vendidas por
        # cada sector, que son las reflejadas en la SAM.
        self.Q0 = (
              self.Xp0              # ventas de los sectores a los hogares
            + self.Xg0              # ventas de los sectores al gobierno
            + self.Xv0              # ventas de los sectores al agente inversor
            + self.X0.sum(axis=1)   # ventas intermedias a otros sectores
        )                                                                   # (2, )
        '''
        [84., 85.]
        '''

        # tasa de impuesto a la producción = impuestos pagados / producción
        self.tauz = self.Tz0 / self.Z0  # (2, ) / (2, ) se dividen uno a uno
        '''
        [0.06849315, 0.05555556]
        '''

        # tasa de aranceles a la importación = aranceles pagados / importación
        self.taum = self.Tm0 / self.M0  # (2, )
        '''
        [0.07692308, 0.18181818]
        '''

        # demanda local de cada producto. A la producción (Z0) se le
        # añaden los impuestos a la producción y se restan las exportaciones
        self.D0 = (1 + self.tauz) * self.Z0 - self.E0   # (2, )
        '''
        [70., 72.]
        '''

        # ahorro de los hogares = pago (aportación) de la columna 'HOH' a la fila 'INV'
        self.Sp0 = DataFrame(sam, index=['INV',], columns=list(dem))        # (1, 1)
        '''
             HOH
        INV   17
        '''
        self.Sp0 = self.Sp0.to_numpy(dtype=np.float64).item()    # () escalar

        # ahorro del gobierno = pago (aportación) de la columna 'GOV' a la fila 'INV'
        self.Sg0 = DataFrame(sam, index=['INV',], columns=['GOV',])
        '''
             GOV
        INV    2
        '''
        self.Sg0 = self.Sg0.to_numpy(dtype=np.float64).item()   # () escalar

        # balanza de pagos = ahorro exterior = pago (aportación) de la columna 'EXT' a la fila 'INV'
        self.Sf0 = DataFrame(sam, index=['INV',], columns=['EXT',])
        '''
             EXT
        INV   12
        '''
        self.Sf0 = self.Sf0.to_numpy(dtype=np.float64).item()   # () escalar

class parametros(object):

    def __init__(self, datos, ncon, nsec):
        # elasticidad de sustitución, entre local e importación, del producto de Argminton (CES)
        # variable exógena puesta a 2.
        self.sigma = np.zeros(nsec, dtype=np.float64)
        self.sigma.fill(2.)
        self.eta = (self.sigma - 1) / self.sigma

        # elasticidad de transformación entre local y exportación (CET)
        # variable exógena puesta a 2.
        self.psi = np.zeros(nsec, dtype=np.float64)
        self.psi.fill(2.)
        self.phi = (self.psi + 1) / self.psi

        '''
        calibrar
        '''
        # coeficientes de participación (alfa) de los productos en la utilidad de la demanda (2, )
        self.alfa = ecua.alfa_CobbDouglas(datos.Xp0)
        
        # coeficientes de participación (beta) de los factores en la función del factor compuesto (2, 2)
        self.beta  = ecua.beta_CobbDouglas(datos.F0)
        # coeficiente de escala de la función del factor compuesto (2, )
        self.b     = ecua.b_CobbDouglas(datos.Y0, datos.F0, self.beta)
        
        # coeficientes de consumos intermedios
        self.ax    = ecua.coeficientes_consumos_intermedios(datos.X0, datos.Z0)
        # coeficientes del factor compuesto
        
        self.ay    = ecua.coeficientes_factor_compuesto(datos.Y0, datos.Z0)
        # coeficientes de participación de la demanda del gobierno
        
        self.mu    = ecua.coeficientes_demanda_gobierno(datos.Xg0)
        # coeficientes de participaciones en las inversiones
        
        self.landa = ecua.coeficientes_inversiones(datos.Xv0, datos.Sp0, datos.Sg0, datos.Sf0)

        # elasticidad de sustitución, entre local e importación, del producto de Argminton (Utilidad CES)

        # coeficiente de participación de la importación en la función del producto de Armington
        self.deltam= ecua.coeficientes_importacion_armington(datos.taum, self.eta, datos.M0, datos.D0)
        # coeficiente de participación de la producción local en la función CES del producto de Armington
        self.deltad= ecua.coeficientes_local_armington      (datos.taum, self.eta, datos.M0, datos.D0)
        # coeficiente de escala de la función de Armington
        self.gamma = ecua.coeficiente_escala_armington(datos.Q0, self.deltam, self.deltad, self.eta, datos.M0, datos.D0)
        
        # elasticidad de transformación entre local y exportación (utilidad CET)

        # coeficiente de participación en la CET de la demanda local
        self.xid   = ecua.coeficiente_CET_local(self.phi, datos.E0, datos.D0)
        # coeficiente de participación en la CET de la exportación
        self.xie   = ecua.coeficiente_CET_exportacion(self.phi, datos.E0, datos.D0)
        # coeficiente de escala de la CET de exportación
        self.teta  = ecua.coeficiente_escala_CET(datos.Z0, self.xie, datos.E0, self.xid, datos.D0, self.phi)

        # propensión al ahorro de los hogares
        self.ssp   = ecua.propension_ahorro_hogares(datos.Sp0, datos.FF)
        # propensión al ahorro del gobierno
        self.ssg   = ecua.propension_ahorro_gobierno(datos.Sg0, datos.Td0, datos.Tz0, datos.Tm0)
        # tasa de impuestos directos
        self.taud  = ecua.tasa_impuestos_directos(datos.Td0, datos.FF)
