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

def ayudas_empresas_AgE(cage, Td, Tz, Tm):
    '''
    ayudas del gobierno a los sectores
    '''
    return cage * (Td.sum() + Tz.sum() + Tm.sum())

def ayudas_hogares_AgH(cagh, Td, Tz, Tm, inc_ayd):
    '''
    ayudas del gobierno a los hogares

    PssH : pensiones que paga la seguridad social pero que están incluidas en Td
    '''
    return cagh * (Td.sum() + Tz.sum() + Tm.sum()) + inc_ayd

def demanda_gobierno_Xg(mu, pq, Td, Tz, Tm, Sg, AgE, AgH, PssH, CssH, CssE):
    '''
    demanda (consumos) de productos por el gobierno

    mu   : coeficiente de reparto de la demanda del gobierno por productos
    pq   : precio de producto de Armington (producto compuesto: local + importación)
    ingresos:
    Td   : impuestos directos a los hogares
    Tz   : impuestos indirectos a las empresas
    Tm   : aranceles de importación
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
    return mu * (Td.sum() + Tz.sum() + Tm.sum() + Css - (Sg + AgE.sum() + AgH.sum())) / pq

def seguridad_social_empresas_CssE(ctzsse, pf, F, INDICE_F_TRA):
    # F incluye las Alp
    return ctzsse * F[:,INDICE_F_TRA] * pf[INDICE_F_TRA]

def seguridad_social_hogares_CssH(ctzssh, pf, FF, Alp, INDICE_F_TRA):
    # las pensiones no cotizan a la seguridad social
    
    return ctzssh * (FF + Alp)[:,INDICE_F_TRA] * pf[INDICE_F_TRA]

