import sys
import copy
import numpy as np
import ecuaciones as ecua
import funciones  as mfun

'''
Cambia los valores de algunos datos o parámetros, de acuerdo a los diferentes escenarios prefijados
incluidos los incluidos en el libro
'''
def imprime(texto, rc=True):
    mfun.imprime(texto, rc)

def escenarios(imprimir, datos, parametros, DECIMALES, ind, dem, h,
              NCASO, DEM_ADICIONAL, DEM_ADICIONAL_TIPO, DEM_ESENCIALES, CON_ESENCIALES, UTILIDAD_DEMANDA, RENTA_FICTICIA,
              AYD_ADICIONAL, GE_INCLUYE_XP, GE_INCLUYE_AgH,
              PRECIO_INI, VAR_FACTORES, FACTOR_CSSH, FACTOR_CSSE,
              SIGMA_ESCENARIO, ARANCELES
              ):
    # NCASO selecciona el escenario a calcular, los escenarios se han elegido sin más sentido que el de probar la aplicación 
    nfac = len(h)
    nsec = len(ind)
    ndem = len(dem)
    if imprimir:
        if abs(DEM_ADICIONAL).sum() != 0:
            csr = ' Con renta ficticia' if RENTA_FICTICIA else ''
            if DEM_ADICIONAL_TIPO == 0:
                imprime('Demanda adicional (importe).' + csr)
            else:
                imprime('Demanda adicional (cantidad).' + csr)
            mfun.i_tabla(''  , [] , dem             , DEM_ADICIONAL, False     , DECIMALES)
            imprime('')
    if abs(DEM_ADICIONAL).sum() != 0 and RENTA_FICTICIA == False:
        # recalcular los alfa
        if imprimir:
            # recalcular los alfa para que no se reduzca el consumo de los productos con demanda adicional, tal como
            # ocurrirá con los otros por la obligación de reservar renta para las compras adicionales
            imprime('Consumos calibrado')
            mfun.i_tabla('', [], dem , datos.Xp0, False, DECIMALES)
            imprime('')
            if DEM_ESENCIALES:
                imprime('Elasticidad (Stone-Geary) de la demanda (alfa) calibrado')
                mfun.tabla_2D(dem, parametros.alfa_esen)
            else:
                if UTILIDAD_DEMANDA == 0:
                    imprime('Elasticidad (Cobb-Douglas) de la demanda (alfa) escenario')
                    mfun.tabla_2D(dem, parametros.alfa)
                else:
                    imprime('Elasticidad (CES) de la demanda (alfa) escenario')
                    mfun.tabla_2D(dem, parametros.alfa_ces)
            imprime('')
        suma_resto = np.zeros((ndem), dtype=np.float64)
        for i in range(ndem):
            for j in range(nsec):
                if DEM_ADICIONAL[i,j] == 0:
                    suma_resto[i] += datos.Xp0[i,j] 
        # ajustar los consumos de los productos sin incremento de demanda para que la suma total de consumos sea
        # igual a la del caso base. Lo que vamos a sumar a unos se lo restamos a los otros
        norma = (suma_resto - DEM_ADICIONAL.sum(axis=1))/ suma_resto
        Xp0 = copy.deepcopy(datos.Xp0)
        for i in range(ndem):
            for j in range(nsec):
                # queremos que las compras optimas de productos con incremento de demanda sean los de la MCS
                # la función del calculo de los Xp ya les sumara el incremento
                # por tanto sólo cambiamos el consumo de los productos sin incremento de demanda
                if DEM_ADICIONAL[i,j] == 0:
                    Xp0[i,j] *= norma[i] 
        if DEM_ESENCIALES:
            renta = ecua.demanda_StoneGeary_renta(datos.FF0, datos.PssH0, datos.AgH0, datos.Sp0, datos.Td0, datos.CssH0, Xp0, CON_ESENCIALES, datos.pF0, datos.pQ0)
            if np.any(renta < 0):
                imprime('Renta menor o igual a 0')
                for i in range(len(renta)):
                    imprime('{:3} {:12.5e}'.format(i + 1, renta[i]))
                sys.exit()
            parametros.alfa_esen = ecua.demanda_StoneGeary_alfa(datos.FF0, datos.PssH0, datos.AgH0, datos.Sp0, datos.Td0, datos.CssH0, Xp0, CON_ESENCIALES, datos.pF0, datos.pQ0)
        else:
            if UTILIDAD_DEMANDA == 0:
                parametros.alfa = ecua.demanda_CobbDouglas_alfa(Xp0)
                #parametros.alfa = ecua.demanda_CobbDouglas_alfa(datos.FF0, datos.PssH0, datos.AgH0, datos.Sp0, datos.Td0, datos.CssH0, Xp0, datos.pF0, datos.pQ0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL)
            else:
                parametros.alfa_ces = ecua.demanda_CES_alfa(parametros.sigma_ces, Xp0)
        if imprimir:
            imprime('Consumos para el recálculo de alfa (sin las demandas adicionales)')
            mfun.i_tabla('', [], dem, Xp0, False, DECIMALES)
            imprime('')
            if DEM_ESENCIALES:
                imprime('Elasticidad (Stone-Geary) de la demanda (alfa) escenario')
                mfun.tabla_2D(dem, parametros.alfa_esen)
            else:
                if UTILIDAD_DEMANDA == 0:
                    imprime('Elasticidad (Cobb-Douglas) de la demanda (alfa) escenario')
                    mfun.tabla_2D(dem, parametros.alfa)
                else:
                    imprime('Elasticidad (CES) de la demanda (alfa) escenario')
                    mfun.tabla_2D(dem, parametros.alfa_ces)
    if imprimir:
        if abs(AYD_ADICIONAL).sum() != 0:
            imprime('Ayudas adicionales')
            mfun.i_tabla(''  , [] , dem             , AYD_ADICIONAL, False     , DECIMALES)
            imprime('')
    
    # si hay ayudas o demandas adicionales, como conducirán a demandas adicionales de determinados productos, se incrementan las 
    # variables F0 y D0 que forman parte del vector solución
    if abs(DEM_ADICIONAL).sum() != 0 or abs(AYD_ADICIONAL).sum() != 0:
        factor = np.ones((nsec,2), dtype=np.float64)
        if abs(DEM_ADICIONAL).sum() != 0:
            for i in range(nsec):
                a = DEM_ADICIONAL[:,i].sum()
                if abs(a) != 0:
                    factor[i,0] = factor[i,1] = 1. + a / datos.Z0[i]
        if abs(AYD_ADICIONAL).sum() != 0:
            for i in range(nsec):
                a = AYD_ADICIONAL[:,i].sum()
                if abs(a) != 0:
                    factor[i,0] = factor[i,1] = 1. + a / datos.Z0[i]
        datos.F0 = factor * datos.F0
        datos.D0 = factor[:,0] * datos.D0
    
    for nc in NCASO:
        if nc > 0:
            if imprimir:
                imprime('---------------------------------------------------------------------------------------------------')
                imprime('Escenario {}'.format(nc))
                imprime('---------------------------------------------------------------------------------------------------')
            if   nc == 1:
                if imprimir:
                    imprime('Elasticidad de la demanda (alfa) calibrado / escenario')
                    mfun.tabla_2D(dem, parametros.alfa)
                    imprime('')

                for i in range(ndem):
                    for j in range(nsec):
                        parametros.alfa[i,j] = 1.0 / nsec

                if imprimir:
                    mfun.tabla_2D(dem, parametros.alfa)
            elif nc == 2:
                if imprimir:
                    imprime('Elasticidad de la producción (beta) calibrado / escenario')
                    mfun.tabla_2D(ind, parametros.beta)
                    imprime('')

                for i in range(nsec):
                    for j in range(nfac):
                        parametros.beta[i,j] = 0.5

                if imprimir:
                    mfun.tabla_2D(ind, parametros.beta)
            elif nc == 3:
                if imprimir:
                    imprime('Aranceles de importación (taum) calibrado / escenario')
                    mfun.tabla_2D(['Productos',], datos.taum)
                    imprime('')

                for i in range(nsec):
                    datos.taum[i] = 0.

                if imprimir:
                    mfun.tabla_2D(['Productos',], datos.taum)
            elif nc == 4:
                if imprimir:
                    imprime('Aranceles de importación (taum) calibrado / escenario')
                    mfun.tabla_2D(['Productos',], datos.taum)
                    imprime('')

                for i in range(nsec):
                    if datos.taum[i] > 0:
                        datos.taum[i] *= 2.
                    else:
                        # si previamente no hay aranceles se fijan en el 10%
                        datos.taum[i] = 0.10

                if imprimir:
                    mfun.tabla_2D(['Productos',], datos.taum)
            elif nc == 5:
                if imprimir:
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

                if imprimir:
                    for i in range(nfac):
                        imprime('{:9.7f}'.format(datos.pF0[i]))
                    for i in range(nsec):
                        imprime('{:9.7f}'.format(datos.pY0[i]))
                        imprime('{:9.7f}'.format(datos.pZ0[i]))
                        imprime('{:9.7f}'.format(datos.pQ0[i]))
                        imprime('{:9.7f}'.format(datos.pD0[i]))
                    imprime('{:9.7f}'.format(datos.epsilon))
            elif nc == 6:
                if imprimir:
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

                if imprimir:
                    # factores aportados por cada consumidor
                    imprime('Factores escenario')
                    mfun.i_tabla('FF0',h , dem, datos.FF0, False, DECIMALES)
            elif nc == 7:
                if imprimir:
                    imprime('Propensión al ahorro')
                    for et in dem:
                        imprime('{:4} {:9.5f}'.format(et, parametros.ssp[0]))
                    imprime('')

                parametros.ssp[0] = parametros.ssp[0] / 2.

                if imprimir:
                    for et in dem:
                        imprime('{:4} {:9.5f}'.format(et, parametros.ssp[0]))
            elif nc == 8:
                if imprimir:
                    imprime('Seguridad social')
                    mfun.i_tabla('/' , dem, ['CssH',], parametros.ctzssh, False, 5)
                    mfun.i_tabla('/' , ind, ['CssE',], parametros.ctzsse, False, 5)
                    imprime('')

                parametros.ctzssh *= FACTOR_CSSH
                parametros.ctzsse *= FACTOR_CSSE

                if imprimir:
                    imprime('Seguridad social')
                    mfun.i_tabla('/' , dem, ['CssH',], parametros.ctzssh, False, 5)
                    mfun.i_tabla('/' , ind, ['CssE',], parametros.ctzsse, False, 5)
            elif nc == 9:
                # simplemente cambia la preferencia de los consumos, no se añade demanda
                if imprimir:
                    if DEM_ESENCIALES:
                        imprime('Elasticidad (Stone-Geary) de la demanda (alfa) calibrado')
                        mfun.tabla_2D(dem, parametros.alfa_esen)
                    else:
                        imprime('Elasticidad de la demanda (alfa) calibrado')
                        mfun.tabla_2D(dem, parametros.alfa)
                    imprime('')

                # modificar preferencias (alfa) de consumo con la demanda adicional
                Xp0 = datos.Xp0 + DEM_ADICIONAL
                if DEM_ESENCIALES:
                    renta = ecua.demanda_StoneGeary_renta(datos.FF0, datos.PssH0, datos.AgH0, datos.Sp0, datos.Td0, datos.CssH0, Xp0, CON_ESENCIALES, datos.pF0, datos.pQ0)
                    if np.any(renta < 0):
                        imprime('Renta menor o igual a 0')
                        for i in range(len(renta)):
                            imprime('{:3} {:12.5e}'.format(i + 1, renta[i]))
                        sys.exit()
                    parametros.alfa_esen = ecua.demanda_StoneGeary_alfa(datos.FF0, datos.PssH0, datos.AgH0, datos.Sp0, datos.Td0, datos.CssH0, Xp0, CON_ESENCIALES, datos.pF0, datos.pQ0)
                else:
                    parametros.alfa = ecua.demanda_CobbDouglas_alfa(Xp0)
                    #parametros.alfa = ecua.demanda_CobbDouglas_alfa(datos.FF0, datos.PssH0, datos.AgH0, datos.Sp0, datos.Td0, datos.CssH0, Xp0, datos.pF0, datos.pQ0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL)
        
                # para evitar que se sume el efecto en preferencia con el incremento en demanda
                DEM_ADICIONAL.fill(0.)

                if imprimir:
                    if DEM_ESENCIALES:
                        imprime('Elasticidad (Stone-Geary) de la demanda (alfa) escenario')
                        mfun.tabla_2D(dem, parametros.alfa_esen)
                    else:
                        imprime('Elasticidad de la demanda (alfa) escenario')
                        mfun.tabla_2D(dem, parametros.alfa)
                    imprime('---------------------------------------------------------------------------------------------------')
                    imprime('Demanda adicional no suma en consumos')
            elif nc == 10:
                if imprimir:
                    if DEM_ESENCIALES:
                        imprime('Elasticidad (Stone-Geary) de la demanda (alfa) calibrado')
                        mfun.tabla_2D(dem, parametros.alfa_esen)
                    else:
                        imprime('Elasticidad de la demanda (alfa) calibrado') 
                        mfun.tabla_2D(dem, parametros.alfa)
                    imprime('')

                # modificar preferencias (alfa) de consumo porque las ayudas son para adquirir productos en concreto
                Xp0 = datos.Xp0 + AYD_ADICIONAL
                if DEM_ESENCIALES:
                    renta = ecua.demanda_StoneGeary_renta(datos.FF0, datos.PssH0, datos.AgH0 + AYD_ADICIONAL.sum(axis=1), datos.Sp0, datos.Td0, datos.CssH0, Xp0, CON_ESENCIALES, datos.pF0, datos.pQ0)
                    if np.any(renta < 0):
                        imprime('Renta menor o igual a 0')
                        for i in range(len(renta)):
                            imprime('{:3} {:12.5e}'.format(i + 1, renta[i]))
                        sys.exit()
                    parametros.alfa_esen = ecua.demanda_StoneGeary_alfa(datos.FF0, datos.PssH0, datos.AgH0 + AYD_ADICIONAL.sum(axis=1), datos.Sp0, datos.Td0, datos.CssH0, Xp0, CON_ESENCIALES, datos.pF0, datos.pQ0)
                else:
                    parametros.alfa = ecua.demanda_CobbDouglas_alfa(Xp0)
                    #parametros.alfa = ecua.demanda_CobbDouglas_alfa(datos.FF0, datos.PssH0, datos.AgH0, datos.Sp0, datos.Td0, datos.CssH0, Xp0, datos.pF0, datos.pQ0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL)

                if imprimir:
                    if DEM_ESENCIALES:
                        imprime('Elasticidad (Stone-Geary) de la demanda (alfa) escenario')
                        mfun.tabla_2D(dem, parametros.alfa_esen)
                    else:
                        imprime('Elasticidad de la demanda (alfa) escenario')
                        mfun.tabla_2D(dem, parametros.alfa)
            elif nc == 11:
                if imprimir:
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

                if imprimir:
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
                if imprimir:
                    imprime('Aranceles de importación (taum) calibrado / escenario')
                    mfun.tabla_2D(['Productos',], datos.taum)
                    imprime('')

                datos.taum = ARANCELES

                if imprimir:
                    mfun.tabla_2D(['Productos',], datos.taum)
            elif nc == 13:
                if DEM_ESENCIALES == False:
                    print('Número de caso {} es incorrecto si no hay DEM_ESENCIALES'.format(nc))
                    sys.exit()
                if GE_INCLUYE_XP == False:
                    print('Número de caso {} es incorrecto cuando no se incluyen los Xp en la solución (se ha establecido GE_INCLUYE_XP=False)'.format(nc))
                    sys.exit()
                else:
                    CON_ESENCIALES = datos.Xp0
                    CON_ESENCIALES = np.where(CON_ESENCIALES < 0, -1, CON_ESENCIALES)
                    if imprimir:
                        imprime('Consumos esenciales = Xp0. Cantidades (si 0 entonces -1)')
                        mfun.i_tabla(''  , [] , dem             , CON_ESENCIALES, False     , DECIMALES)
                        imprime('')
            elif nc == 14:
                if DEM_ESENCIALES == False:
                    print('Número de caso {} es incorrecto sin DEM_ESENCIALES'.format(nc))
                    sys.exit()
                if GE_INCLUYE_XP == False:
                    print('Número de caso {} es incorrecto cuando no se incluyen los Xp en la solución (se ha establecido GE_INCLUYE_XP=False)'.format(nc))
                    sys.exit()
                else:
                    CON_ESENCIALES = datos.Xp0 - 1
                    CON_ESENCIALES = np.where(CON_ESENCIALES < 0, -1, CON_ESENCIALES)
                    if imprimir:
                        imprime('Consumos esenciales = Xp0 - 1. Cantidades (si 0 entonces -1)')
                        mfun.i_tabla(''  , [] , dem             , CON_ESENCIALES, False     , DECIMALES)
                        imprime('')
            elif nc == 15:
                if DEM_ESENCIALES == False:
                    print('Número de caso {} es incorrecto sin DEM_ESENCIALES'.format(nc))
                    sys.exit()
                if GE_INCLUYE_XP == False:
                    print('Número de caso {} es incorrecto cuando no se incluyen los Xp en la solución (se ha establecido GE_INCLUYE_XP=False)'.format(nc))
                    sys.exit()
                else:
                    CON_ESENCIALES = 0.9 * datos.Xp0
                    CON_ESENCIALES = np.where(CON_ESENCIALES <= 0, -1, CON_ESENCIALES)
                    if imprimir:
                        imprime('Consumos esenciales = 0.9 * Xp0. Cantidades (si 0 entonces -1)')
                        mfun.i_tabla(''  , [] , dem             , CON_ESENCIALES, False     , DECIMALES)
                        imprime('')
            elif nc == 16:
                if DEM_ESENCIALES == False:
                    print('Número de caso {} es incorrecto sin DEM_ESENCIALES'.format(nc))
                    sys.exit()
                if GE_INCLUYE_XP == False:
                    print('Número de caso {} es incorrecto cuando no se incluyen los Xp en la solución (se ha establecido GE_INCLUYE_XP=False)'.format(nc))
                    sys.exit()
                else:
                    CON_ESENCIALES = datos.Xp0 - DEM_ADICIONAL - 1
                    CON_ESENCIALES = np.where(CON_ESENCIALES < 0, -1, CON_ESENCIALES)
                    if imprimir:
                        imprime('Consumos esenciales = Xp0 - demanda adicional - 1. Cantidades (si 0 entonces -1)')
                        mfun.i_tabla(''  , [] , dem             , CON_ESENCIALES, False     , DECIMALES)
                        imprime('')
            else:
                print('Número de caso {} incorrecto'.format(nc))
                sys.exit()
        if imprimir:
            imprime('')
    if imprimir:
        imprime('')
    return (CON_ESENCIALES)

