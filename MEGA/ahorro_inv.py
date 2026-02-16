#import numpy as np

def demanda_inversion_Xv(landa, pq, Sp, Sg, Sc, epsilon, Sf):
    '''
    landa : coeficiente de reparto por sectores del total de la inversión
    pq : precio del producto de Armington
    epsilon : cotización de la moneda extranjera (local/extranjera)
    Sp : ahorro de los hogares
    Sg : ahorro del gobierno
    Sc : ahorro de la seguridad social
    Sf : deficit por cuenta corriente (ahorro del exterior)

    podría pensarse en sacar Sf del reparto y sustituirlo por el déficit comercial
    de cada sector (M -E) pero en realidad la inversión en un sector extranjera no está
    relacionada con esto.
    '''
    return (Sp.sum() + Sg + Sc + Sf * epsilon) * (landa / pq)

def ahorro_hogares_Sp(ssp, FF, pf, PssH):
    '''
    Ahorro de los hogares Sp
    Una parte de sus ingresos brutos (ingresos por su aportación de factores a los sectores más pensiones)
    
    FF   : aportación de factores por cada consumidor
    pf   : precio de los factores
    PssH : ingresos por pensiones pagadas por la seguridad social
    ssp  : tasa de propensión al ahorro de cada consumidor
    '''
    Sp = ssp * (FF.dot(pf) + PssH)
    return Sp

def ahorro_gobierno_Sg(ssg, Td, Tz, Tm, AgE, AgH, PssH, CssH, CssE):
    '''
    Ahorro del gobierno Sg
    Un porcentaje (ssg propensión al ahorro del gobierno) de sus ingresos
    ssg  : propensión al ahorro del gobierno
    Td   : impuestos directos
    Tz   : impuestos a la producción
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
    return ssg * (Td.sum() + Tz.sum() + Tm.sum() + Css - (AgE.sum() + AgH.sum()))
