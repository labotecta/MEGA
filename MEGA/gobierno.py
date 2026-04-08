def impuestos_directos_Td(taud, pf, FF, Alp, PssH):
    '''
    Td impuestos directos como una tasa sobre el total de ingresos de los hogares (CAP, LAB y Seguridad social)
    Es posible que falte aladir Alp a FF, pero complica la secuencia de cálculo de las ecuaciones del modelo

    taud : tasa de impuestos directos para cada hogar
    pf   : precio de los factores
    FF   : factores prestados por los hogares
    PssH : ingresos recibidos de la seguridad social
    '''
    return taud * ((FF + Alp).dot(pf) + PssH)

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

def ayudas_empresas_AgE(cage, Td, Tz, Tm, Tg, Ti, Te):
    # no está adaptado al caso en que el gobierno paga las pensiones, por tanto recauda las cotizaciones
    '''
    ayudas del gobierno a los sectores

    Td : impuestos pagados por los hogares
    Tz : impuestos pagados por los sectores
    Tm : aranceles de importación
    Ti : impuestos pagados por la inversión+ahorro
    Te : impuestos pagados por el sector exterior
    No sumamos Tg (impuestos que paga el gobierno) porque también hay que restarlo
    Ti   : impuestos pagados por la inversión
    '''
    return cage * (Td.sum() + Tz.sum() + Tm.sum() + Ti + Te)

def ayudas_hogares_AgH(cagh, Td, Tz, Tm, Tg, Ti, Te, inc_ayd):
    # no está adaptado al caso en que el gobierno paga las pensiones, por tanto recauda las cotizaciones
    '''
    ayudas del gobierno a los hogares

    Td : impuestos pagados por los hogares
    Tz : impuestos pagados por los sectores
    Tm : aranceles de importación
    Ti : impuestos pagados por la inversión+ahorro
    Te : impuestos pagados por el sector exterior
    No sumamos Tg (impuestos que paga el gobierno) porque también hay que restarlo
    Ti   : impuestos pagados por la inversión
    '''
    return cagh * (Td.sum() + Tz.sum() + Tm.sum() + Ti + Te) + inc_ayd

def demanda_gobierno_Xg(mu, pq, Td, Tz, Tm, Tg, Ti, Te, Sg, AgE, AgH, PssH, CssH, CssE):
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
    return mu * (Td.sum() + Tz.sum() + Tm.sum() + Ti + Te + Css - (Sg + AgE.sum() + AgH.sum())) / pq

def seguridad_social_empresas_CssE(ctzsse, pf, F, INDICE_F_TRA):
    # F incluye las Alp
    return ctzsse * F[:,INDICE_F_TRA] * pf[INDICE_F_TRA]

def seguridad_social_hogares_CssH(ctzssh, pf, FF, Alp, INDICE_F_TRA):
    # las pensiones no cotizan a la seguridad social
    
    return ctzssh * (FF + Alp)[:,INDICE_F_TRA] * pf[INDICE_F_TRA]

