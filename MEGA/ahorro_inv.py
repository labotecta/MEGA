#import numpy as np

def demanda_inversion_Xv(landa, pq, Sp, Sg, Sc, epsilon, Sf, Ti, Te):
    '''
    CANTIDAD de inversión recibida por cada sector, Xv
    es el resultado de sumar los ahorros de todos los agentes menos los impuestos que paga A-I

    landa : coeficiente de reparto por sectores del total de la inversión (ahorros)
    pq : precio del producto de Armington
    epsilon : cotización de la moneda extranjera (local/extranjera)
    Sp : ahorro de los hogares
    Sg : ahorro del gobierno
    Sc : ahorro de la seguridad social
    Sf : deficit por cuenta corriente (ahorro del exterior)
    Ti : impuestos pagados por el ahorro + inversión
    
    No se usa Te

    podría pensarse en sacar Sf del reparto y sustituirlo por el déficit comercial
    de cada sector (M -E) pero en realidad la inversión extranjera en un sector no está
    relacionada con esto.
    '''
    #return (Sp.sum() + Sg + Sc + Sf * epsilon - Ti - Te) * (landa / pq)
    return (Sp.sum() + Sg + Sc + Sf * epsilon - Ti) * (landa / pq)

def ahorro_hogares_Sp(ssp, FF, pf, PssH):
    '''
    IMPORTE ahorrado por cada hogar, Sp

    Ahorro de los hogares Sp
    Una parte de sus ingresos brutos (ingresos por su aportación de factores a los sectores más pensiones)
    se calcula previamente a las compras de los hogares para disminuir la renta disponible y con ello las compras
    Podriamos pensar en hacer al contrario: primero calcular las compras y el ahorro es lo que queda, pero no quedaría nada
    si usamos toda la renta disponible para comprar
    
    FF   : aportación de factores por cada consumidor
    pf   : precio de los factores
    PssH : ingresos por pensiones pagadas por la seguridad social
    ssp  : tasa de propensión al ahorro de cada consumidor
    '''
    Sp = ssp * (FF.dot(pf) + PssH)
    return Sp

def ahorro_gobierno_Sg(ssg, Td, Tz, Tm, Tg, Ti, Te, AgE, AgH, PssH, CssH, CssE):
    '''
    IMPORTE ahorrado por el gobierno, Sg

    Un porcentaje (ssg propensión al ahorro del gobierno) de sus ingresos
    ssg  : propensión al ahorro del gobierno
    Td   : impuestos directos
    Tz   : impuestos a la producción
    Tm   : aranceles de importación
    Tg   : impuestos que paga el gobierno. No se usa porque lo que paga lo recibe
    Ti   : impuestos pagados por la inversión
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
    return ssg * (Td.sum() + Tz.sum() + Tm.sum() + Ti + Te + Css - (AgE.sum() + AgH.sum()))

def ahorro_exterior_Sf(M, E, pm, pe):
    Sf = M.dot(pm) - E.dot(pe)
    return Sf