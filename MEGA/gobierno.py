def impuestos_directos_Td(taud, pf, FF, Alp, PssH, AgH):
    '''
    Td impuestos directos como una tasa sobre el total de ingresos de los hogares (CAP, LAB y Seguridad social)

    !! es posible que Alp no deba afectarse del precio !!

    taud : tasa de impuestos directos para cada hogar
    pf   : precio de los factores
    FF   : factores prestados por los hogares
    Alp  : ahorros a largo plazo de los hogares
    PssH : ingresos recibidos de la seguridad social
    AgH  : ayudas recibidas por los hogares
     '''
    return taud * ((FF + Alp).dot(pf) + PssH + AgH)

def impuestos_produccion_Tz(tauz, pz, Z):
    '''
    Tz impuestos a la producción de cada sector

    tauz : vector de tasas a la producción de cada sector
    pz   : vector precios de los productos
    Z    : vector producciones de los sectores
    '''
    return tauz * Z * pz

def aranceles_importacion_Tm(taum, pm, M):
    '''
    Tm aranceles de importación por cada producto

    taum : vector aranceles a cada producto
    pm   : vector precio de importación de cada producto
    M    : vector cantidades importadas de cada producto
    '''
    return taum * M * pm

def impuestos_directos_Ti(tai, pf, FF, INDICE_F_TRA):
    '''
    Los impuestos sobre la inversión se calculan sobre los ingreos por capital de los hogares
    tai          : tasa de impuestos directos a la inversión
    pf           : precio de los factores
    FF           : factores prestados por cada hogar
    INDICE_F_TRA : índice del factor trabajo
    '''
    return tai * FF[:, 1 - INDICE_F_TRA].sum() * pf[1 - INDICE_F_TRA]

def ayudas_empresas_AgE(cage, Td, Tz, Tm, Tg, Ti, Te):
    # no está adaptado al caso en que el gobierno paga las pensiones y que por tanto recaudaría las cotizaciones
    '''
    ayudas del gobierno a los sectores
    como un porcentaje (cage) de los ingresos regulares del gobierno (los impuestos)

    Td : impuestos pagados por los hogares
    Tz : impuestos pagados por los sectores
    Tm : aranceles de importación
    Ti : impuestos pagados por la inversión+ahorro
    Te : impuestos pagados por el sector exterior
    No sumamos Tg (impuestos que paga el gobierno) porque también hay que restarlo
    '''
    return cage * (Td.sum() + Tz.sum() + Tm.sum() + Ti + Te)

def ayudas_hogares_AgH(cagh, Td, Tz, Tm, Tg, Ti, Te, inc_ayd):
    # no está adaptado al caso en que el gobierno paga las pensiones y que por tanto recaudaría las cotizaciones
    '''
    ayudas del gobierno a los hogares
    como un porcentaje (cagh) de los ingresos regulares del gobierno (los impuestos)

    Td : impuestos pagados por los hogares
    Tz : impuestos pagados por los sectores
    Tm : aranceles de importación
    Ti : impuestos pagados por la inversión+ahorro
    Te : impuestos pagados por el sector exterior
    No sumamos Tg (impuestos que paga el gobierno) porque también hay que restarlo
    '''
    return cagh * (Td.sum() + Tz.sum() + Tm.sum() + Ti + Te) + inc_ayd

'''
Con transferencias de fondos de la UE al gobierno, hay que decidir a que se dedica este extra ingreso.
Hemos supuesto que em cualquier caso se dedicará a ayudas a los sectores y a los hogares, como estas formarán
parte de las ayudas (AgH y AgE) a traves de las ayudas adicionales consideradas (inc_ayd), debemos sumar las
transferencias de la UE allí donde restemos las ayudas AgH y AgE.
Pero nos queda ver que hacemos con el saldo neto de lo recibido de la UE y las ayudas otorgadas.
La opción elegida, por ser la más simple, es que este saldo se dedique exclusivamente al ahorro y a
la compra de productos por parte del gobierno:
    Sg = ahorro_gobierno_Sg(...)
    Xg = demanda_gobierno_Xg(...)
que son las dos ecuaciones que  restan las ayudas, de los ingresos del gobierno.  
Modificamos estas dos funciones incrementando los ingresos con 'Fue' y si hay un saldo, con respecto a
las ayudas adicionales, se empleará en ahorro y comprar productos, sin necesidad de hacer nada más, porque el
    saldo surge de la resta:
        Fue - AgH - AgE

Con esto, no tenemos que modificar ninguna otra ecuación.
'''
def demanda_gobierno_Xg(mu, pq, Td, Tz, Tm, Tg, Ti, Te, Sg, AgE, AgH, PssH, CssH, CssE, Fue):
    '''
    demanda (consumos) de productos por el gobierno
    mu   : coeficiente de reparto de la demanda del gobierno por productos
    pq   : precio de producto de Armington (producto compuesto: local + importación)
    ingresos:
    Td : impuestos pagados por los hogares
    Tz : impuestos pagados por los sectores
    Tm : aranceles de importación
    Ti : impuestos pagados por la inversión+ahorro
    Te : impuestos pagados por el sector exterior
    Css  : si es el gobierno quien paga las pensiones, ingresos recibidos de la seguridad social
    Fue  : transferencias de fondos de la UE al gobierno
    restan:
    Sg   : ahorro del gobierno
    AgE  : ayudas (pagos) del gobierno a los sectores
    AgH  : ayudas (pagos) del gobierno a los hogares
    Pss  : pago de las pensiones, si es el gobierno quien las paga
    '''
    if PssH.sum() == 0:
        # el gobierno paga las pensiones, por tanto recauda las cotizaciones
        Css = CssH.sum() + CssE.sum()
    else:
        Css = 0.
    return mu * (Td.sum() + Tz.sum() + Tm.sum() + Ti + Te + Css + Fue - (Sg + AgE.sum() + AgH.sum())) / pq

def seguridad_social_empresas_CssE(ctzsse, pf, F, INDICE_F_TRA):
    # F incluye las Alp
    return ctzsse * F[:,INDICE_F_TRA] * pf[INDICE_F_TRA]

def seguridad_social_hogares_CssH(ctzssh, pf, FF, Alp, INDICE_F_TRA):
    # las pensiones no cotizan a la seguridad social
    
    return ctzssh * (FF + Alp)[:,INDICE_F_TRA] * pf[INDICE_F_TRA]

