import copy
import itertools
import numpy as np
from matplotlib import pyplot as plt

import MEGA          as prin
import exterior      as exte
import funciones     as mfun
import ecuaciones    as ecua
import produccion    as prod
import gobierno      as gob
import ahorro_inv    as ainv
import demanda       as deho
import exterior      as exte

def imprime(texto, rc=True):
    mfun.imprime(texto, rc)

def valores_iniciales(datos, parametros, DECIMALES, ind, dem, h, INDICE_F_TRA, VALOR_F_TRA, vec_opt, npre_sol, etq_precios, ebp_ini):
    # muestra los valores iniciales obtenidos de la MCS
    imprime('Valores iniciales de las variables')
    imprime('')
    mfun.i_tabla('precios', etq_precios[0:npre_sol], [], vec_opt[0:npre_sol], True, 7)
    respre = np.concatenate((datos.pZ0, np.array(datos.pWe), np.array(datos.pWm)))
    mfun.i_tabla('/' , etq_precios[npre_sol:len(etq_precios)] , [], respre, True, 7)
    imprime('---------------------------------------------------------------------------------------------------------')
    imprime('Cantidades')
    imprime('---------------------------------------------------------------------------------------------------------')
    imprime('Factores aportados por los hogares. FF0')
    mfun.i_tabla('/' , h  , dem             , datos.FF0             , False, DECIMALES)    # factores aportados por cada consumidor
    mfun.i_tabla(''  , [] , ['suma FF']     , datos.FF0.sum(axis=0) , True , DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Ahorro a largo plazo de los hogares. Alp0')
    mfun.i_tabla(''  , []                 , dem                     , datos.Alp0 , True , DECIMALES)
    mfun.i_tabla(''  , []                 , ['suma Alp0']           , datos.Alp0.sum(axis=0) , False, DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Factores aportados por los hogares. FF0 + Alp0')
    mfun.i_tabla(''  , []                 , dem                     , datos.FF0+datos.Alp0, False, DECIMALES)    # factores aportados por cada consumidor
    mfun.i_tabla(''  , []                 , ['sum.FF0+Alp0']        , (datos.FF0+datos.Alp0).sum(axis=0), True , DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Factores utilizados por los sectores. F0')
    mfun.i_tabla(''  , [] , ind             , datos.F0              , False, DECIMALES)    # factores utilizados por cada sector
    mfun.i_tabla(''  , [] , ['suma F0']     , datos.F0.sum(axis=0)  , False, DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Factor compuesto. Y0 (Valor Añadido Bruto)')
    mfun.i_tabla(' ' , ind , ['Y0',]        , datos.Y0              , True , DECIMALES)
    imprime('Consumo intermedio filas: ventas, columnas: compras. X0')
    mfun.i_tabla(''  , [] , ind             , datos.X0              , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['compras X0',]  , datos.X0.sum(axis=0)  , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    imprime('Consumo de los hogares. Xp0')
    mfun.i_tabla(''  , [] , dem             , datos.Xp0 , False     , DECIMALES)
    mfun.i_tabla(''  , [] , ['suma Xp0']    , datos.Xp0.sum(axis=0) , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    imprime('Consumo del gobierno. Xg0')
    mfun.i_tabla(''  , [] , ['Xg0',]        , datos.Xg0             , False, DECIMALES)
    imprime('Consumo de inversión. Xv0')
    mfun.i_tabla(''  , [] , ['Xv0',]        , datos.Xv0             , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    imprime('Consumo total')
    mfun.i_tabla(''  , [] , ['X+Xp+Xg+Xv',], datos.Xp0.sum(axis=0) + datos.Xg0 + datos.Xv0 + datos.X0.sum(axis=1), False, DECIMALES)
    imprime('Producción total')
    mfun.i_tabla(''  , [] , ['Q0',]        , datos.Q0               , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    mfun.i_tabla(''  , [] , ['D0',]        , datos.D0               , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['M0',]        , datos.M0               , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['E0',]        , datos.E0               , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['Z0',]        , datos.Z0               , False, DECIMALES)
    imprime('---------------------------------------------------------------------------------------------------------')
    imprime('Importes')
    imprime('---------------------------------------------------------------------------------------------------------')
    imprime('Impuestos')
    mfun.i_tabla(''  , [] , ['Tz0',]       , datos.Tz0              , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['Tm0',]       , datos.Tm0              , False, DECIMALES)
    mfun.i_tabla('/' , dem, ['Td0',]       , datos.Td0              , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['Ti0',]       , datos.Ti0              , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['Tg0',]       , datos.Tg0              , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['Te0',]       , datos.Te0              , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['CssH0',]     , datos.CssH0            , True , DECIMALES)
    mfun.i_tabla('/' , ind, ['CssE0',]     , datos.CssE0            , True , DECIMALES)
    mfun.i_tabla(''  , [] , ['def/sup ss',], datos.CssE0.sum() + datos.CssH0.sum() - datos.PssH0.sum(), False, DECIMALES)
    imprime('Ahorro-Inversión')
    mfun.i_tabla('/' , dem, ['Sp0',]       , datos.Sp0              , True , DECIMALES)
    mfun.i_tabla(''  , [] , ['Sg0',]       , datos.Sg0              , False, DECIMALES)
    imprime('Pensiones')
    mfun.i_tabla('/' , dem, ['PssH0',]     , datos.PssH0            , False, DECIMALES)
    imprime('Ayudas del gobierno')
    mfun.i_tabla('/' , dem, ['AgH0',]      , datos.AgH0             , False, DECIMALES)
    mfun.i_tabla('/' , ind, ['AgE0',]      , datos.AgE0             , True , DECIMALES)
    imprime('Déficit por cuenta corriente. M0 - E0')
    Sfde = datos.M0 - datos.E0
    mfun.i_tabla(''  , [] , ['Sf sectores',]   , Sfde               , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['Sf',]        , Sfde.sum()             , False, DECIMALES)
    imprime('Equilibrio de la balanza de pagos')
    mfun.i_tabla(''  , [] , ['equi.bal.pag',], ebp_ini              , False, DECIMALES)
    imprime('')
    mfun.i_tabla(''  , [] , ['Apz0',]      , datos.Apz0             , False, 5)
    imprime('')
    if VALOR_F_TRA == 0:
        paro = 100. * (1. - datos.F0[:,INDICE_F_TRA].sum() / datos.PobAct)
        mfun.i_tabla(''  , []                   , ['Pobla.activa',],datos.PobAct, False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['% paro',]     , paro        , False, 2)
    imprime('')

def salida_calibrado(datos, parametros, ind, dem, h, DEM_ESENCIALES):
    nfac = len(h)
    nsec = len(ind)
    ndem = len(dem)
    # muestra los valores calculados para los parámretros a partir de la MCS
    imprime('-------------------------------------------------------------------')
    imprime('Resultado del calibrado')
    imprime('-------------------------------------------------------------------')
    imprime('')
    imprime('eta. parámetro de sustitución entre local y importación (CES)')
    mfun.cabecera('', ind)
    mfun.cuerpo2D(['eta',], parametros.eta)
    mfun.cierre(ind)
    imprime('')
    imprime('sigma. elasticidad de sustitución entre local y importación (CES)')
    mfun.cabecera('', ind)
    mfun.cuerpo2D(['sigma',], parametros.sigma)
    mfun.cierre(ind)
    imprime('')
    imprime('deltam. Participación de la importación en la función del producto de Armington (CES)')
    mfun.cabecera('Sector', ['deltam',])
    mfun.cuerpo2D(ind, parametros.deltam.reshape(nsec,1))
    mfun.cierre(['deltam',])
    imprime('')
    imprime('deltad. Participación de la producción local en la función del producto de Armington (CES)')
    mfun.cabecera('Sector', ['deltad',])
    mfun.cuerpo2D(ind, parametros.deltad.reshape(nsec,1))
    mfun.cierre(['deltad',])
    imprime('')
    imprime('gamma. Coeficiente de escala de la función de Armington (CES)')
    mfun.cabecera('Sector', ['gamma',])
    mfun.cuerpo2D(ind, parametros.gamma.reshape(nsec,1))
    mfun.cierre(['gamma',])
    imprime('')
    imprime('TMS. Tasa Marginal de Sustitución local/importación (CES)')
    mfun.cabecera('Sector', ['TMS',])

    deno1 = copy.deepcopy(parametros.deltad)
    deno1[deno1 == 0] = 1.
    deno2 = copy.deepcopy(datos.D0)
    deno2[deno2 == 0] = 1.
    base = parametros.deltad / deno1 * (datos.M0 / deno2)
    TMS = np.copysign(1, base) * (abs(base) ** (1 - parametros.eta))
    mfun.cuerpo2D(ind, TMS.reshape(nsec,1))
    mfun.cierre(['TMS',])
    imprime('')

    imprime('phi. parámetro de transformación entre local y exportación (CET)')
    mfun.cabecera('', ind)
    mfun.cuerpo2D(['phi',], parametros.phi)
    mfun.cierre(ind)
    imprime('')
    imprime('psi. elasticidad de transformación entre local y exportación (CET)')
    mfun.cabecera('', ind)
    mfun.cuerpo2D(['psi',], parametros.psi)
    mfun.cierre(ind)
    imprime('')
    imprime('xie. Coeficiente de participación de la exportación en la CET')
    mfun.cabecera('Sector', ['xie',])
    mfun.cuerpo2D(ind, parametros.xie.reshape(nsec,1))
    mfun.cierre(['xie',])
    imprime('')
    imprime('xid. Coeficiente de participación de la demanda local en la CET')
    mfun.cabecera('Sector', ['xid',])
    mfun.cuerpo2D(ind, parametros.xid.reshape(nsec,1))
    mfun.cierre(['xid',])
    imprime('')
    imprime('teta. Coeficiente de escala de la exportación en la CET')
    mfun.cabecera('Sector', ['teta',])
    mfun.cuerpo2D(ind, parametros.teta.reshape(nsec,1))
    mfun.cierre(['teta',])
    imprime('')
    imprime('TMS. Tasa Marginal de Transformación local/exportación (CET)')
    mfun.cabecera('Sector', ['TMS',])
    TMS = parametros.xid / parametros.xie * ((datos.E0 / datos.D0) ** (1 - parametros.phi))
    mfun.cuerpo2D(ind, TMS.reshape(nsec,1))
    mfun.cierre(['TMS',])
    imprime('')

    imprime('tauz. Tasa de impuesto a la producción')
    mfun.cabecera('', ind)
    mfun.cuerpo2D(['tauz'], datos.tauz)
    mfun.cierre(ind)
    imprime('')

    imprime('taum. Tasa de aranceles')
    mfun.cabecera('', ind)
    mfun.cuerpo2D(['taum',], datos.taum)
    mfun.cierre(ind)
    imprime('')

    imprime('alfa. Participación de los productos en la función de utilidad de la demanda Cobb Douglas')
    mfun.cabecera('alfa', ind)
    mfun.cuerpo2D(dem, parametros.alfa)
    mfun.cierre(ind)
    imprime('')

    imprime('alfa. Participación de los productos en la función de utilidad de la demanda Stone Geary con consumos esenciales')
    mfun.cabecera('alfa esen.', ind)
    mfun.cuerpo2D(dem, parametros.alfa_esen)
    mfun.cierre(ind)
    imprime('')

    imprime('eta_ces. Parámetro de sustitución en la función de utilidad de la demanda CES')
    mfun.cabecera('', ind)
    mfun.cuerpo2D(['eta_ces',], parametros.eta_ces)
    mfun.cierre(ind)
    imprime('')
    imprime('sigma_ces. Elasticidad de sustitución en la función de utilidad de la demanda CES')
    mfun.cabecera('', ind)
    mfun.cuerpo2D(['sigma_ces',], parametros.sigma_ces)
    mfun.cierre(ind)
    imprime('')
    imprime('alfa_ces. Participación de los productos en la función de utilidad de la demanda CES')
    mfun.cabecera('', ind)
    mfun.cuerpo2D(dem, parametros.alfa_ces)
    mfun.cierre(ind)
    imprime('')

    imprime('beta. Participación de los factores en la función de producción del factor compuesto')
    mfun.cabecera('Sector', h)
    mfun.cuerpo2D(ind, parametros.beta)
    mfun.cierre(h)
    imprime('')

    imprime('b. Coeficiente de escalado en la función de producción del factor compuesto')
    mfun.cabecera('Sector', ['b',])
    mfun.cuerpo2D(ind, parametros.b.reshape(nsec,1))
    mfun.cierre(['b',])
    imprime('')

    imprime('ax, ay. Coeficientes de los consumos intermedios y del factor compuesto (fila i = consumos por unidad de producción bruta del sector i)')
    la =  list(ind)
    la.append('Factor c.')
    mfun.cabecera('Sector', la)
    mfun.cuerpo2D(ind, np.c_[parametros.ax, parametros.ay])
    mfun.cierre(la)
    imprime('')

    imprime('mu. Participación de los productos en el consumo del gobierno')
    mfun.cabecera('Sector', ['mu',])
    mfun.cuerpo2D(ind, parametros.mu.reshape(nsec,1))
    mfun.cierre(['mu',])
    imprime('')

    imprime('landa. Coeficiente de participación de la demanda de inversión')
    mfun.cabecera('Sector', ['landa',])
    mfun.cuerpo2D(ind, parametros.landa.reshape(nsec,1))
    mfun.cierre(['landa',])

    imprime('ssp. Propensión al ahorro de los hogares')
    mfun.cabecera('', dem)
    mfun.cuerpo2D(['ssp',], parametros.ssp)
    mfun.cierre(dem)
    imprime('')

    imprime('ssg. Propensión al ahorro del gobierno {:9.{prec}f}'.format(parametros.ssg, prec=5))
    imprime('')

    imprime('taud id. Tasa de impuestos directos')
    mfun.cabecera('', dem)
    mfun.cuerpo2D(['taud id',], parametros.taud_id)
    mfun.cierre(dem)
    imprime('')

    imprime('taud oi. Tasa de otros impuestos a los hogares')
    mfun.cabecera('', dem)
    mfun.cuerpo2D(['taud oi',], parametros.taud_oi)
    mfun.cierre(dem)
    imprime('')

    imprime('taud. Tasa de impuestos directos + otros impuestos')
    mfun.cabecera('', dem)
    mfun.cuerpo2D(['taud',], parametros.taud)
    mfun.cierre(dem)
    imprime('')

    imprime('tai. Tasa de impuestos sobre la inversión {:9.{prec}f}'.format(parametros.tai, prec=5))
    imprime('')

    imprime('ctzsse. Cotización a la seguridad social de las empresas')
    mfun.cabecera('', ind)
    mfun.cuerpo2D(['ctzsse',], parametros.ctzsse)
    mfun.cierre(ind)
    imprime('')

    imprime('ctzssh. Cotización a la seguridad social de los hogares')
    mfun.cabecera('', dem)
    mfun.cuerpo2D(['ctzssh',], parametros.ctzssh)
    mfun.cierre(dem)
    imprime('')

    imprime('cage. Ayudas del gobierno a las empresas')
    mfun.cabecera('', ind)
    mfun.cuerpo2D(['cage',], parametros.cage)
    mfun.cierre(ind)
    imprime('')

    imprime('cagh. Ayudas del gobierno a los hogares')
    mfun.cabecera('', dem)
    mfun.cuerpo2D(['cagh',], parametros.cagh)
    mfun.cierre(dem)
    imprime('')

def veri_solucion(datos, parametros, ind, dem, h,
                  vec_veri_sol, etq_veri, UTILIDAD_DEMANDA, DEM_ESENCIALES, DEM_ADICIONAL_TIPO, DEM_ADICIONAL, RENTA_FICTICIA, INDICE_F_TRA, AYD_ADI_DEM, ALP_FACTOR, CON_ESENCIALES,
                  titulo, tolerancia
                  ):
    nfac = len(h)
    nsec = len(ind)
    ndem = len(dem)
    (pf,py,pz,pq,pd,epsilon,Apz,F,Z,E,M,D,FF,Y,X,Xp,Xg,Xv,Q,ebp,Sp,Sg,Sf,Td,Tz,Tm,CssE,CssH,AgE,AgH,Alp,Ti) = vec_veri_sol

    nvar_end = 0
    nvar_end += pf.size
    nvar_end += py.size
    nvar_end += pz.size
    nvar_end += pq.size
    nvar_end += pd.size

    (pe, pm) = exte.precio_moneda_local_pe_pm(datos.pWe, datos.pWm, epsilon)

    nvar_end += pe.size
    nvar_end += pm.size

    nvar_end += 1 # Apz

    ax = parametros.ax
    ay = parametros.ay

    v_medio     = np.zeros(len(etq_veri), dtype=np.ndarray)
    v_medio[0]  = np.mean(abs(Y))
    v_medio[1]  = np.mean(abs(F))
    v_medio[2]  = np.mean(abs(X))
    v_medio[3]  = np.mean(abs(Y))
    v_medio[4]  = np.mean(abs(pz))
    v_medio[5]  = np.mean(abs(Td))
    v_medio[6]  = np.mean(abs(Tz))
    v_medio[7]  = np.mean(abs(Tm))
    v_medio[8]  = np.mean(abs(Xg))
    v_medio[9]  = np.mean(abs(Xv))
    v_medio[10] = np.mean(abs(Sp))
    v_medio[11] = np.mean(abs(Sg))
    v_medio[12] = np.mean(abs(Xp))
    v_medio[13] = np.mean(abs(ebp))
    v_medio[14] = np.mean(abs(Q))
    v_medio[15] = np.mean(abs(M))
    v_medio[16] = np.mean(abs(D))
    v_medio[17] = np.mean(abs(Z))
    v_medio[18] = np.mean(abs(E))
    v_medio[19] = np.mean(abs(D))
    v_medio[20] = np.mean(abs(CssE))
    v_medio[21] = np.mean(abs(CssH))
    v_medio[22] = np.mean(abs(AgE))
    v_medio[23] = np.mean(abs(AgH))
    v_medio[24] = np.mean(abs(Q))
    v_medio[25] = np.mean(abs(F.sum(axis=0)))

    desviacion     = np.zeros(len(etq_veri), dtype=np.ndarray)
    desviacion[0]  = Y     - prod.produccion_factor_compuesto_Y(F, parametros.beta, parametros.b)           # 6. 1
    nvar_end += Y.size
    desviacion[1]  = F     - prod.uso_optimo_factores_F(parametros.beta, pf, py, Y)                         # 6. 2
    nvar_end += F.size
    desviacion[2]  = X     - prod.consumo_intermedio_X(Z, ax)                                               # 6. 3
    nvar_end += X.size
    desviacion[3]  = Y     - prod.utilizacion_factor_compuesto_Y(Z, ay)                                     # 6. 4
    # no se incrementa nvar_end porque ya se ha calculado la variable Y
    desviacion[4]  = pz    - prod.coste_unitario_produccion_pz(ay, py, ax, pq)                              # 6. 5 alternativa
    # no se incrementa nvar_end porque ya lo hemos sumado al principio
    desviacion[5]  = Td    - gob.impuestos_directos_Td(parametros.taud, pf, FF, Alp, datos.PssH0)           # 6. 6
    nvar_end += Td.size
    desviacion[6]  = Tz    - gob.impuestos_produccion_Tz(datos.tauz, pz, Z)                                 # 6. 7
    nvar_end += Tz.size
    desviacion[7]  = Tm    - gob.aranceles_importacion_Tm(datos.taum, pm, M)                                # 6. 8
    nvar_end += Tm.size
    desviacion[8]  = Xg    - gob.demanda_gobierno_Xg(parametros.mu, pq, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, Sg, AgE, AgH, datos.PssH0, CssH, CssE) # 6. 9
    nvar_end += Xg.size
    if datos.PssH0.sum() == 0:
        Sc = 0.
    else:
        Sc = CssE.sum() + CssH.sum() - datos.PssH0.sum()
    desviacion[9]  = Xv    - ainv.demanda_inversion_Xv(parametros.landa, pq, Sp, Sg, Sc, epsilon, Sf, Ti, datos.Te0)    # 6.10
    nvar_end += Xv.size
    desviacion[10] = Sp    - ainv.ahorro_hogares_Sp(parametros.ssp, FF, pf, datos.PssH0)                    # 6.11
    nvar_end += Sp.size
    desviacion[11] = Sg    - ainv.ahorro_gobierno_Sg(parametros.ssg, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AgE, AgH, datos.PssH0, CssH, CssE) # 6.12
    nvar_end += 1
                                                                                                            # 6.13
    if DEM_ESENCIALES:
        desviacion[12] = Xp - deho.demanda_maxima_utilidad_StoneGeary_Xp(parametros.alfa_esen, CON_ESENCIALES, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL, RENTA_FICTICIA)
    else:
        if UTILIDAD_DEMANDA == 0:
            # función de demanda Cobb Douglas
            desviacion[12] = Xp - deho.demanda_maxima_utilidad_CobbDouglas_Xp(parametros.alfa, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL, RENTA_FICTICIA)
        else:
            # función de demanda CES
            desviacion[12] = Xp - deho.demanda_maxima_utilidad_CES_Xp(parametros.eta_ces, parametros.alfa_ces, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL, RENTA_FICTICIA)
    nvar_end += Xp.size
    desviacion[13] = ebp                                                                                    # 6.16
    nvar_end += ebp.size
    desviacion[14] = Q     - exte.produccion_armington_Q(parametros.gamma, parametros.deltam, parametros.deltad, M, D, parametros.eta) # 6.17
    nvar_end += Q.size
    desviacion[15] = M     - exte.importacion_maxima_utilidad_armington_M(parametros.gamma, parametros.deltam, pq, pm, Q, parametros.eta, datos.taum) # 6.18
    nvar_end += M.size
    desviacion[16] = D     - exte.produccion_maxima_utilidad_armington_D(parametros.gamma, parametros.deltad, pq, pd, Q, parametros.eta) # 6.19
    nvar_end += D.size
    desviacion[17] = Z     - exte.restriccion_produccion_bruta_Z(parametros.teta, parametros.xie, parametros.xid, E, D, parametros.phi) # 6.20
    nvar_end += Z.size
    desviacion[18] = E     - exte.produccion_para_exportacion_E(parametros.teta, parametros.xie, pz, pe, Z, parametros.phi, datos.tauz, CssE, AgE, Apz, parametros.ctzssez, parametros.ctzagez, prin.MODO_PSEUDOIMPTOS)  # 6.21
    nvar_end += E.size
    desviacion[19] = D     - exte.produccion_para_local_D(parametros.teta, parametros.xid, pz, pd, Z, parametros.phi, datos.tauz, CssE, AgE, Apz, parametros.ctzssez, parametros.ctzagez, prin.MODO_PSEUDOIMPTOS) # 6.22
    # no se incrementa nvar_end porque ya se ha calculado la variable D
    desviacion[20]  = CssE - gob.seguridad_social_empresas_CssE(parametros.ctzsse, pf, F, INDICE_F_TRA)         # CssE
    nvar_end += CssE.size
    desviacion[21]  = CssH - gob.seguridad_social_hogares_CssH(parametros.ctzssh, pf, FF, Alp, INDICE_F_TRA)    # CssH
    nvar_end += CssH.size
    desviacion[22]  = AgE  - gob.ayudas_empresas_AgE(parametros.cage, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0)                           # AgE
    nvar_end += AgE.size
    desviacion[23]  = AgH  - gob.ayudas_hogares_AgH(parametros.cagh, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AYD_ADI_DEM)               # AgH
    nvar_end += AgH.size
    desviacion[24]  = Q    - (Xp.sum(axis=0) + Xg + Xv + X.sum(axis=1))                                     # 6.23
    desviacion[25]  = F.sum(axis=0) - (FF.sum(axis=0) + Alp.sum(axis=0))                                    # 6.24

    '''
    if FF_ENDOGENA:
        nvar_end += FF.size
    if ALP_FACTOR > 0:
        nvar_end += Alp.size
    '''

    imprime(titulo)
    imprime('Número de variables endógenas :{} incluida Apz'.format(nvar_end))
    imprime('')
    imprime('--- Verificación de las ecuaciones en error acumulado {:10.3e} --'.format(tolerancia))
    imprime('ecuación      valor medio error acumula  error máximo  % error máxi')
    imprime('----------- ------------- ------------- ------------- -------------')
    desvio = 0.
    nfallos = 0
    for i in range (len(etq_veri)):
        if np.issubdtype(type(desviacion[i]), np.floating):
            suma_des_error_cua = desviacion[i] * desviacion[i]
            suma_des_abs = abs(desviacion[i])
            max_des_error = suma_des_abs
        else:
            suma_des_error_cua = (desviacion[i] * desviacion[i]).sum()
            suma_des_abs = (abs(desviacion[i])).sum()
            max_des_error  = np.max(abs(desviacion[i]))
        desvio += suma_des_error_cua
        if suma_des_abs > tolerancia:
            if abs(v_medio[i]) < 0.01:
                # los porcentajes de desviaciones respecto de 0 no son significativos
                p_error_max = '{:>13}'.format('--')
            else:
                p_error_max = '{:13.3f}'.format(100 * max_des_error / v_medio[i])
            imprime('{:11} {:13.5e} {:13.5e} {:13.5e} {}'.format(etq_veri[i], v_medio[i], suma_des_abs, max_des_error, p_error_max))
            nfallos += 1
    if nfallos == 0:
        imprime('======= Se cumplen todas las ecuaciones en error acumulado ========')
    imprime('----------- ------------- ------------- ------------- -------------')
    imprime('')
    imprime('-- Verificación de las ecuaciones en % de error máximo {:8.3}% --'.format(100.0 * 0.0001))
    imprime('ecuación      valor medio error acumula  error máximo  % error máxi')
    imprime('----------- ------------- ------------- ------------- -------------')
    nfallos = 0
    for i in range (len(etq_veri)):
        if np.issubdtype(type(desviacion[i]), np.floating):
            suma_des_error_cua = desviacion[i] * desviacion[i]
            suma_des_abs = abs(desviacion[i])
            max_des_error = suma_des_abs
        else:
            suma_des_error_cua = (desviacion[i] * desviacion[i]).sum()
            suma_des_abs = (abs(desviacion[i])).sum()
            max_des_error  = np.max(abs(desviacion[i]))
        if abs(v_medio[i]) < 0.01:
            # los porcentajes de desviaciones respecto de 0 no son significativos
            pem = max_des_error
            p_error_max = '{:>13}'.format('--')
        else:
            pem = max_des_error / v_medio[i]
            p_error_max = '{:13.3f}'.format(100 * pem)
        if pem > 0.0001:    # 0.01%
            imprime('{:11} {:13.5e} {:13.5e} {:13.5e} {}'.format(etq_veri[i], v_medio[i], suma_des_abs, max_des_error, p_error_max))
            nfallos += 1
    if nfallos == 0:
        imprime('======  Se cumplen todas las ecuaciones en % de error máximo ======')
    imprime('----------- ------------- ------------- ------------- -------------')
    imprime('')
    imprime('-------------------------------')
    imprime('Ecm.total desvios {:13.5e}'.format(desvio))
    imprime('-------------------------------')

def salida_valores(datos, parametros, DECIMALES, ind, dem, h, INDICE_F_TRA, VALOR_F_TRA, vec_opt, npre_sol, etq_precios, res_ecuaciones):
    nfac = len(h)
    nsec = len(ind)
    ndem = len(dem)
    (Apz,Fi,Ei,Mi,Di,Xpi,pf,pq,pe,pm,
        Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,Sf ,AgE ,AgH ,CssE ,CssH,ebp,Zl,pz,
        Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,Sfr,AgEr,AgHr,CssEr,CssHr,ebpr,
        Ti,Tir
    ) = res_ecuaciones
    pf = prin.extrae_var(vec_opt, 'pF', 0, nfac - 1)
    # el precio del otro factor se añade al principio o al final de 'pf'
    pf = prin.completa_pf(pf, F)
    py = prin.extrae_var(vec_opt, 'pY', 0, nsec)
    pq = prin.extrae_var(vec_opt, 'pQ', 0, nsec)
    pd = prin.extrae_var(vec_opt, 'pD', 0, nsec)
    epsilon = prin.extrae_var(vec_opt, 'epsilon', 0, 0)
    (pe, pm) = exte.precio_moneda_local_pe_pm(datos.pWe, datos.pWm, epsilon)
    respre = np.concatenate((pz, np.array(pe), np.array(pm)))
    imprime('{:10}      {:9.7f}'.format('pF_' + h[0], pf[0]))
    imprime('{:10}      {:9.7f}'.format('pF_' + h[1], pf[1]))
    mfun.i_tabla('precios', etq_precios[1:npre_sol], []       , vec_opt[1:npre_sol]  , True ,  7)
    mfun.i_tabla('/' , etq_precios[npre_sol:len(etq_precios)] , [], respre           , True ,  7)
    imprime('---------------------------------------------------------------------------------------------------------')
    imprime('Cantidades')
    imprime('---------------------------------------------------------------------------------------------------------')
    imprime('Factores aportados por los hogares. FF')
    mfun.i_tabla('/' , h                    , dem             , FFr                   , False, DECIMALES)
    mfun.i_tabla(''  , []                   , ['suma FF']     , FFr.sum(axis=0)       , False, DECIMALES)
    mfun.i_pie('/'   , h)
    imprime('Ahorro a largo plazo de los hogares. Alp')
    mfun.i_tabla(''  , []                   , dem             , Alpr                  , True , DECIMALES)
    mfun.i_tabla(''  , []                   , ['suma Alp']    , Alpr.sum(axis=0)      , False, DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Factores aportados por los hogares. FF + Alp')
    mfun.i_tabla(''  , []                   , dem             , FFr + Alpr             , False, DECIMALES)
    mfun.i_tabla(''  , []                   , ['suma FF+Alp'] , (FFr+Alpr).sum(axis=0) , False, DECIMALES)
    mfun.i_pie('/'   , h)
    imprime('Factores utilizados por los sectores. F')
    mfun.i_tabla(''  , []                   , ind             , Fr                    , False, DECIMALES)
    mfun.i_tabla(''  , []                   , ['suma F',]     , Fr.sum(axis=0)        , False, DECIMALES)
    mfun.i_pie('/'   , h)
    imprime('Factor compuesto. Y (Valor Añadido Bruto)')
    mfun.i_tabla('/' , ind                  , ['Y óptimo F',] , Ypr                   , False, DECIMALES)
    mfun.i_tabla(''  , []                   , ['Y nec.para Z',], Ydr                 , False, DECIMALES)
    imprime('Consumo intermedio filas: ventas, columnas: compras. X')
    mfun.i_tabla(''  , []                   , ind             , Xr                    , False, DECIMALES)
    mfun.i_tabla(''  , []                   , ['compras X',]   , Xr.sum(axis=0)       , False, DECIMALES)
    mfun.i_pie('/'   , ind)
    imprime('Consumo de los hogares. Xp')
    mfun.i_tabla(''  , []                   , dem             , Xpr                   , False, DECIMALES)
    mfun.i_tabla(''  , []                   , ['suma Xp',]    , Xpr.sum(axis=0)       , False, DECIMALES)
    mfun.i_pie('/'   , ind)
    imprime('Consumo del gobierno. Xg')
    mfun.i_tabla(''  , []                   , ['Xg',]         , Xgr                   , False, DECIMALES)
    imprime('Consumo de inversión. Xv')
    mfun.i_tabla(''  , []                   , ['Xv',]         , Xvr                   , False, DECIMALES)
    mfun.i_pie('/'   , ind)
    imprime('Consumo total')
    mfun.i_tabla(''  , []                   , ['X+Xp+Xg+Xv']  , Xpr.sum(axis=0) + Xg + Xv + X.sum(axis=1), False, DECIMALES)
    imprime('Producción total')
    mfun.i_tabla(''  , []                   , ['Q',]          , Qr                    , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    mfun.i_tabla(''  , []                   , ['D 6.19',]     , Dar                   , False, DECIMALES)
    mfun.i_tabla(''  , []                   , ['D 6.22',]     , Dtr                   , False, DECIMALES)
    mfun.i_tabla(''  , []                   , ['M',]          , Mr                    , False, DECIMALES)
    mfun.i_tabla(''  , []                   , ['E',]          , Er                    , False, DECIMALES)
    mfun.i_tabla(''  , []                   , ['Z',]          , Zr                    , False, DECIMALES)
    mfun.i_tabla(''  , []                   , ['Z leontief',] , Zl                    , False, DECIMALES)
    imprime('---------------------------------------------------------------------------------------------------------')
    imprime('Importes')
    imprime('---------------------------------------------------------------------------------------------------------')
    imprime('Impuestos')
    mfun.i_tabla(''  , []                   , ['Tz',]         , Tzr                   , False, DECIMALES)
    mfun.i_tabla(''  , []                   , ['Tm',]         , Tmr                   , False, DECIMALES)
    mfun.i_tabla('/' , dem                  , ['Td',]         , Tdr                   , False, DECIMALES)
    mfun.i_tabla(''  , []                   , ['Ti',]         , Tir                   , False, DECIMALES)
    mfun.i_tabla(''  , []                   , ['Tg',]         , datos.Tg0             , False, DECIMALES)
    mfun.i_tabla(''  , []                   , ['Te',]         , datos.Te0             , False, DECIMALES)
    mfun.i_tabla(''  , []                   , ['CssH',]       , CssHr                 , True , DECIMALES)
    mfun.i_tabla('/' , ind                  , ['CssE',]       , CssEr                 , True , DECIMALES)
    mfun.i_tabla(''  , []                   , ['def/sup ss',] , CssEr.sum() + CssHr.sum() - datos.PssH0.sum(), False, DECIMALES)
    imprime('Ahorro-Inversión')
    mfun.i_tabla('/' , dem                  , ['Sp',]         , Spr                   , True , DECIMALES)
    mfun.i_tabla(''  , []                   , ['Sg',]         , Sgr                   , False, DECIMALES)
    imprime('Pensiones')
    mfun.i_tabla('/' , dem                  , ['PssH0',]      , datos.PssH0           , True , DECIMALES)
    imprime('Ayudas del gobierno')
    mfun.i_tabla('/' , dem                  , ['AgH',]        , AgHr                  , False, DECIMALES)
    mfun.i_tabla('/' , ind                  , ['AgE',]        , AgEr                  , True , DECIMALES)
    imprime('Déficit por cuenta corriente. M - E')
    Sfde = Mr - Er
    mfun.i_tabla(''  , []                   , ['Sf Ind',]    , Sfde                   , False, DECIMALES)
    mfun.i_tabla(''  , []                   , ['Sf',]        , Sfde.sum()             , False, DECIMALES)
    imprime('Equilibrio de la balanza de pagos')
    mfun.i_tabla(''  , []                   , ['equi.bal.pag',], ebpr                 , False, DECIMALES)
    imprime('')
    mfun.i_tabla(''  , []                   , ['Apz',]       , Apz                    , False, 5)
    imprime('')
    if VALOR_F_TRA == 0:
        paro = 100. * (1. - F[:,INDICE_F_TRA].sum() / datos.PobAct)
        mfun.i_tabla(''  , []                   , ['Pobla.activa',],datos.PobAct, False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['% paro',]     , paro        , False, 2)
    imprime('')

def salida_desvios(res_ecuaciones, param, DECIMALES, GE_INCLUYE_XP, OPT_DESVIOS, dist):
        (Apz,Fi,Ei,Mi,Di,Xpi,pf,pq,pe,pm,
            Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,Sf ,AgE ,AgH ,CssE ,CssH, ebp, Zl, pz,
            Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,Sfr,AgEr,AgHr,CssEr,CssHr,ebpr,
            Ti,Tir
        ) = res_ecuaciones
        (des_produccion,des_factores,des_ebp,
                des_Fi,des_Mi,des_Ei,des_Di,des_Xpi,
                des_F ,des_M ,des_E,
                des_Da,des_Dt,
                des_Dat,
                des_Yp,des_Yd,
                des_Ydp,
                des_Alp,des_FF,des_Z,des_X,des_Xp,des_Xg,des_Xv,des_Q,
                des_Td,des_Tz,des_Tm,des_Sp,des_Sg,des_Sf,des_AgE,des_AgH,des_CssE,des_CssH,des_Ti
        ) = param

        # todos son positivos porque se ha guardado el valor absoluto de las diferencias
        des_produccion = des_produccion ** 2
        des_factores = des_factores ** 2
        des_Fi  = des_Fi ** 2
        des_Ei  = des_Ei ** 2
        des_Mi  = des_Mi ** 2
        des_Di  = des_Di ** 2
        des_Xpi = des_Xpi ** 2
        if OPT_DESVIOS == 0:
            des_Yp = des_Yp ** 2
            des_Yd = des_Yd ** 2
            des_Da = des_Da ** 2
            des_Dt = des_Dt ** 2
        des_Alp  = des_Alp ** 2
        des_F    = des_F ** 2
        des_FF   = des_FF ** 2
        des_Ydp  = des_Ydp ** 2
        des_Z    = des_Z ** 2
        des_X    = des_X ** 2
        des_Xp   = des_Xp ** 2
        des_Xg   = des_Xg ** 2
        des_Xv   = des_Xv ** 2
        des_Q    = des_Q ** 2
        des_M    = des_M ** 2
        des_Dat  = des_Dat ** 2
        des_E    = des_E ** 2
        des_Td   = des_Td ** 2
        des_Tz   = des_Tz ** 2
        des_Tm   = des_Tm ** 2
        des_Ti   = des_Ti ** 2
        des_Sp   = des_Sp ** 2
        des_Sg   = des_Sg ** 2
        des_Sf   = des_Sf ** 2
        des_AgE  = des_AgE ** 2
        des_AgH  = des_AgH ** 2
        des_CssE = des_CssE ** 2
        des_CssH = des_CssH ** 2
        des_ebp  = des_ebp ** 2

        suma = des_produccion.sum()
        suma += des_factores.sum()
        suma += des_Fi.sum()
        suma += des_Ei.sum()
        suma += des_Mi.sum()
        suma += des_Di.sum()
        suma += des_Xpi.sum()
        if OPT_DESVIOS == 0:
            suma += des_Yp.sum()
            suma += des_Yd.sum()
            suma += des_Da.sum()
            suma += des_Dt.sum()
        suma += des_Alp.sum()
        suma += des_F.sum()
        suma += des_FF.sum()
        suma += des_Ydp.sum()
        suma += des_Z.sum()
        suma += des_X.sum()
        suma += des_Xp.sum()
        suma += des_Xg.sum()
        suma += des_Xv.sum()
        suma += des_Q.sum()
        suma += des_M.sum()
        suma += des_Dat.sum()
        suma += des_E.sum()
        suma += des_Td.sum()
        suma += des_Tz.sum()
        suma += des_Tm.sum()
        suma += des_Ti.sum()
        suma += des_Sp.sum()
        suma += des_Sg.sum()
        suma += des_Sf.sum()
        suma += des_AgE.sum()
        suma += des_AgH.sum()
        suma += des_CssE.sum()
        suma += des_CssH.sum()
        suma += des_ebp.sum()

        mfun.tabla_2De(['equilib Q',] , des_produccion, 6)
        mfun.tabla_2De(['equilib F',] , des_factores, 6)
        mfun.tabla_2De(['des Fi',]    , des_Fi, 6)
        mfun.tabla_2De(['des Ei',]    , des_Ei, 6)
        mfun.tabla_2De(['des Mi',]    , des_Mi, 6)
        mfun.tabla_2De(['des Di',]    , des_Di, 6)
        mfun.tabla_2De(['des Xpi',]   , des_Xpi, 6)
        if OPT_DESVIOS == 0:
            mfun.tabla_2De(['des Yp',]    , des_Yp)
            mfun.tabla_2De(['des Yd',]    , des_Yd)
            mfun.tabla_2De(['des Da',]    , des_Da)
            mfun.tabla_2De(['des Dt',]    , des_Dt)

        mfun.tabla_2De(['des Alp',]   , des_Alp, 6)
        mfun.tabla_2De(['des F',]     , des_F, 6)
        mfun.tabla_2De(['des FF',]    , des_FF, 6)
        mfun.tabla_2De(['des Yd-p',]  , des_Ydp, 6)
        mfun.tabla_2De(['des Z',]     , des_Z, 6)
        mfun.tabla_2De(['des X',]     , des_X, 6)
        mfun.tabla_2De(['des Xp',]    , des_Xp, 6)
        mfun.tabla_2De(['des Xg',]    , des_Xg, 6)
        mfun.tabla_2De(['des Xv',]    , des_Xv, 6)
        mfun.tabla_2De(['des Q',]     , des_Q, 6)
        mfun.tabla_2De(['des M',]     , des_M, 6)
        mfun.tabla_2De(['des Da-t',]  , des_Dat, 6)
        mfun.tabla_2De(['des E',]     , des_E, 6)
        mfun.tabla_2De(['des Td',]    , des_Td, 6)
        mfun.tabla_2De(['des Tz',]    , des_Tz, 6)
        mfun.tabla_2De(['des Tm',]    , des_Tm, 6)
        mfun.tabla_2De(['des Ti',]    , des_Ti, 6)
        mfun.tabla_2De(['des Sp',]    , des_Sp, 6)
        mfun.tabla_2De(['des Sg',]    , des_Sg, 6)
        mfun.tabla_2De(['des Sf',]    , des_Sf, 6)
        mfun.tabla_2De(['des AgE',]   , des_AgE, 6)
        mfun.tabla_2De(['des AgH',]   , des_AgH, 6)
        mfun.tabla_2De(['des CssE',]  , des_CssE, 6)
        mfun.tabla_2De(['des CssH',]  , des_CssH, 6)
        mfun.tabla_2De(['des b.pag',] , des_ebp, 6)
        imprime('')
        imprime('{:10} {:9.{prec}e} '.format       ('Errdesvios', dist, prec=5))
        imprime('')
        imprime('---------- --------- ---------')
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('desvios Q', des_produccion.sum(), 100. * des_produccion.sum() / (1 if np.mean(Q) ==0   else np.mean(Q))    , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('desvios F', des_factores.sum()  , 100. * des_factores.sum()   / (1 if np.mean(Fi)==0   else np.mean(Fi))   , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Fi'   , des_Fi.sum()        , 100. * des_Fi.sum()         / (1 if np.mean(Fi)==0   else np.mean(Fi))   , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Ei'   , des_Ei.sum()        , 100. * des_Ei.sum()         / (1 if np.mean(Ei)==0   else np.mean(Ei))   , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Mi'   , des_Mi.sum()        , 100. * des_Mi.sum()         / (1 if np.mean(Mi)==0   else np.mean(Mi))   , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Di'   , des_Di.sum()        , 100. * des_Di.sum()         / (1 if np.mean(Di)==0   else np.mean(Di))   , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Xpi'  , des_Xpi.sum()       , 100. * des_Xpi.sum()        / (1 if np.mean(Xpi)==0  else np.mean(Xpi))  , prec=6))

        if OPT_DESVIOS == 0:
            imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Di'   , des_Di.sum()        , 100. * des_Di.sum()         / (1 if np.mean(Di)==0   else np.mean(Di))   , prec=6))
            imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Yp'   , des_Yp.sum()        , 100. * des_Yp.sum()         / (1 if np.mean(Yp)==0   else np.mean(Yp))   , prec=6))
            imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Yd'   , des_Yd.sum()        , 100. * des_Yd.sum()         / (1 if np.mean(Yd)==0   else np.mean(Yd))   , prec=6))
            imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Da '  , des_Da.sum()        , 100. * des_Da.sum()         / (1 if np.mean(Da)==0   else np.mean(Da))   , prec=6))
            imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Dt'   , des_Dt.sum()        , 100. * des_Dt.sum()         / (1 if np.mean(Dt)==0   else np.mean(Dt))   , prec=6))

        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Alp'  , des_Alp.sum()       , 100. * des_Alp.sum()        / (1 if np.mean(Alp)==0  else np.mean(Alp))  , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des F'    , des_F .sum()        , 100. * des_F.sum()          / (1 if np.mean(F)==0    else np.mean(F))    , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des FF'   , des_FF.sum()        , 100. * des_FF.sum()         / (1 if np.mean(FF)==0   else np.mean(FF))   , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Yd-Yp', des_Ydp.sum()       , 100. * des_Ydp.sum()        / (1 if np.mean(Yd)==0   else np.mean(Yd))   , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Z'    , des_Z.sum()         , 100. * des_Z.sum()          / (1 if np.mean(Z) ==0   else np.mean(Z))    , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des X'    , des_X.sum()         , 100. * des_X.sum()          / (1 if np.mean(X) ==0   else np.mean(X))    , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Xp'   , des_Xp.sum()        , 100. * des_Xp.sum()         / (1 if np.mean(Xp)==0   else np.mean(Xp))   , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Xg'   , des_Xg.sum()        , 100. * des_Xg.sum()         / (1 if np.mean(Xg)==0   else np.mean(Xg))   , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Xv'   , des_Xv.sum()        , 100. * des_Xv.sum()         / (1 if np.mean(Xv)==0   else np.mean(Xv))   , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Q'    , des_Q.sum()         , 100. * des_Q.sum()          / (1 if np.mean(Q) ==0   else np.mean(Q))    , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des M'    , des_M.sum()         , 100. * des_M.sum()          / (1 if np.mean(M) ==0   else np.mean(M))    , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Da-Dt', des_Dat.sum()       , 100. * des_Dat.sum()        / (1 if np.mean(Da)==0   else np.mean(Da))   , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des E'    , des_E.sum()         , 100. * des_E.sum()          / (1 if np.mean(E) ==0   else np.mean(E))    , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Td'   , des_Td.sum()        , 100. * des_Td.sum()         / (1 if np.mean(Td)==0   else np.mean(Td))   , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Tz'   , des_Tz.sum()        , 100. * des_Tz.sum()         / (1 if np.mean(Tz)==0   else np.mean(Tz))   , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Tm'   , des_Tm.sum()        , 100. * des_Tm.sum()         / (1 if np.mean(Tm)==0   else np.mean(Tm))   , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Ti'   , des_Ti.sum()        , 100. * des_Ti.sum()         / (1 if np.mean(Ti)==0   else np.mean(Ti))   , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Sp'   , des_Sp.sum()        , 100. * des_Sp.sum()         / (1 if np.mean(Sp)==0   else np.mean(Sp))   , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Sg'   , des_Sg.sum()        , 100. * des_Sg.sum()         / (1 if np.mean(Sg)==0   else np.mean(Sg))   , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des Sf'   , des_Sf.sum()        , 100. * des_Sf.sum()         / (1 if np.mean(Sf)==0   else np.mean(Sf))   , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des AgE'  , des_AgE.sum()       , 100. * des_AgE.sum()        / (1 if np.mean(AgE)==0  else np.mean(AgE))  , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des AgH'  , des_AgH.sum()       , 100. * des_AgH.sum()        / (1 if np.mean(AgH)==0  else np.mean(AgH))  , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des CssE' , des_CssE.sum()      , 100. * des_CssE.sum()       / (1 if np.mean(CssE)==0 else np.mean(CssE)) , prec=6))
        imprime('{:10} {:9.{prec}e} {:9.2f}'.format('des CssH' , des_CssH.sum()      , 100. * des_CssH.sum()       / (1 if np.mean(CssH)==0 else np.mean(CssH)) , prec=6))
        imprime('{:10} {:9.{prec}e} '.format       ('des b.pag', des_ebp.sum(), prec=6))
        imprime('---------- --------- ---------')
        imprime('{:10} {:9.{prec}e} '.format       ('Suma      ', suma, prec=6))
        imprime('')
    
def diferencias_cantidades_finales_iniciales(datos, parametros, DECIMALES, ind, dem, h, vec_opt_ini, vec_opt, npre_sol, etq_precios, ebp_ini, res_ecuaciones, rot):
    nfac = len(h)
    nsec = len(ind)
    ndem = len(dem)
    (Apz,Fi,Ei,Mi,Di,Xpi,pf,pq,pe,pm,
        Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,Sf ,AgE ,AgH ,CssE ,CssH,ebp,Zl,pz,
        Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,Sfr,AgEr,AgHr,CssEr,CssHr,ebpr,
        Ti,Tir
    ) = res_ecuaciones
    imprime('Diferencias entre los valores finales y los iniciales')
    imprime('')
    vec = vec_opt - vec_opt_ini

    pf = prin.extrae_var(vec_opt, 'pF', 0, nfac - 1)
    pf = prin.completa_pf(pf, F)
    imprime('{:10}      {:9.7f}'.format('pF_' + h[0], pf[0]))
    imprime('{:10}      {:9.7f}'.format('pF_' + h[1], pf[1]))
    mfun.i_tabla('precios', etq_precios[1:npre_sol], [], vec[1:npre_sol], True, 7)
    dpz = pz - datos.pZ0
    epsilon = prin.extrae_var(vec_opt, 'epsilon', 0, 0)
    (pe, pm) = exte.precio_moneda_local_pe_pm(datos.pWe, datos.pWm, epsilon)
    dpe = pe - datos.pWe
    dpm = pm - datos.pWm
    respre = np.concatenate((dpz, np.array(dpe), np.array(dpm)))
    mfun.i_tabla('/' , etq_precios[npre_sol:len(etq_precios)] , [], respre, True, 7)
    imprime(rot)
    imprime('---------------------------------------------------------------------------------------------------------')
    imprime('Factores aportados por los hogares. FF')
    dFF0 = FF - datos.FF0
    mfun.i_tabla('/' , h  , dem             , dFF0                 , False, DECIMALES)    # factores aportados por cada consumidor
    mfun.i_tabla(''  , [] , ['suma FF']     , dFF0.sum(axis=0)     , True , DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Ahorro a largo plazo de los hogares. Alp')
    dAlp0 = Alp - datos.Alp0
    mfun.i_tabla(''  , []                  , dem                   , dAlp0             , True , DECIMALES)
    mfun.i_tabla(''  , []                  , ['suma Alp']          , dAlp0.sum(axis=0) , False, DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Factores aportados por los hogares. FF + Alp')
    dFF0 = FF + Alp - datos.FF0 - datos.Alp0
    mfun.i_tabla(''  , []                  , dem                  , dFF0               , False, DECIMALES)    # factores aportados por cada consumidor
    mfun.i_tabla(''  , [] , ['suma FF+Alp'], dFF0.sum(axis=0)     , True , DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Factores utilizados por los sectores. F')
    dF0 = Fi - datos.F0
    mfun.i_tabla(''  , [] , ind            , dF0                   , False, DECIMALES)    # factores utilizados por cada sector
    mfun.i_tabla(''  , [] , ['suma F']     , dF0.sum(axis=0)       , False, DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Factor compuesto. Y (Valor Añadido Bruto)')
    dY0 = Yp - datos.Y0
    mfun.i_tabla(' ' , ind , ['Y',]        , dY0                   , True , DECIMALES)
    imprime('Consumo intermedio filas: ventas, columnas: compras. X')
    dX0 = X - datos.X0
    mfun.i_tabla(''  , [] , ind            , dX0                   , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['compras X',]  , dX0.sum(axis=0)       , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    imprime('Consumo de los hogares. Xp')
    dXp0 = Xp - datos.Xp0
    mfun.i_tabla(''  , [] , dem            , dXp0 , False          , DECIMALES)
    mfun.i_tabla(''  , [] , ['suma Xp']    , dXp0.sum(axis=0)      , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    imprime('Consumo del gobierno. Xg')
    dXg0 = Xg - datos.Xg0
    mfun.i_tabla(''  , [] , ['Xg',]        , dXg0                  , False, DECIMALES)
    imprime('Consumo de inversión. Xv')
    dXv0 = Xv - datos.Xv0
    mfun.i_tabla(''  , [] , ['Xv',]        , dXv0                  , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    imprime('Consumo total')
    mfun.i_tabla(''  , [] , ['X+Xp+Xg+Xv',], dXp0.sum(axis=0) + dXg0 + dXv0 + dX0.sum(axis=1), False, DECIMALES)
    imprime('Producción total')
    dQ0 = Q - datos.Q0
    mfun.i_tabla(''  , [] , ['Q',]        , dQ0                    , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    dD0 = Di - datos.D0
    mfun.i_tabla(''  , [] , ['D',]        , dD0                    , False, DECIMALES)
    dM0 = M - datos.M0
    mfun.i_tabla(''  , [] , ['M',]        , dM0                    , False, DECIMALES)
    dE0 = E - datos.E0
    mfun.i_tabla(''  , [] , ['E',]        , dE0                    , False, DECIMALES)
    dZ0 = Z - datos.Z0
    mfun.i_tabla(''  , [] , ['Z',]        , dZ0                    , False, DECIMALES)
    imprime('---------------------------------------------------------------------------------------------------------')
    imprime('Importes')
    imprime('---------------------------------------------------------------------------------------------------------')
    imprime('Impuestos')
    dTz0 = Tz - datos.Tz0
    mfun.i_tabla(''  , [] , ['Tz',]       , dTz0                   , False, DECIMALES)
    dTm0 = Tm - datos.Tm0
    mfun.i_tabla(''  , [] , ['Tm',]       , dTm0                   , False, DECIMALES)
    dTd0 = Td - datos.Td0
    mfun.i_tabla('/' , dem, ['Td',]       , dTd0                   , False, DECIMALES)
    dTi0 = Ti - datos.Ti0
    mfun.i_tabla(''  , [] , ['Ti',]      , dTi0                    , False, DECIMALES)
    dTg0 = datos.Tg0 - datos.Tg0
    mfun.i_tabla(''  , [] , ['Tg',]      , dTg0                    , False, DECIMALES)
    dTe0 = datos.Te0 - datos.Te0
    mfun.i_tabla(''  , [] , ['Te',]      , dTe0                    , False, DECIMALES)
    dCssH0 = CssH - datos.CssH0
    mfun.i_tabla(''  , [] , ['CssH',]     , dCssH0                 , True , DECIMALES)
    dCssE0 = CssE - datos.CssE0
    mfun.i_tabla('/' , ind, ['CssE',]     , dCssE0                 , True , DECIMALES)
    mfun.i_tabla(''  , [] , ['def/sup ss',], dCssE0.sum() + dCssH0.sum(), False, DECIMALES)
    imprime('Ahorro-Inversión')
    dSp0 = Sp - datos.Sp0
    mfun.i_tabla('/' , dem, ['Sp',]       , dSp0                   , True , DECIMALES)
    dSg0 = Sg - datos.Sg0
    mfun.i_tabla(''  , [] , ['Sg',]       , dSg0                   , False, DECIMALES)
    imprime('Pensiones')
    dPssH0 = datos.PssH0 - datos.PssH0
    mfun.i_tabla('/' , dem, ['PssH',]     , dPssH0                 , False, DECIMALES)
    imprime('Ayudas del gobierno')
    dAgH0 = AgH - datos.AgH0
    mfun.i_tabla('/' , dem, ['AgH',]      , dAgH0                  , False, DECIMALES)
    dAgE0 = AgE - datos.AgE0
    mfun.i_tabla('/' , ind, ['AgE',]      , dAgE0                  , True , DECIMALES)
    imprime('Déficit por cuenta corriente. (M - E) - (M0 - E0)')
    dSfde = (M - E) - (datos.M0 - datos.E0)
    mfun.i_tabla(''  , [] , ['Sf sectores',]  , dSfde                 , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['Sf',]       , dSfde.sum()           , False, DECIMALES)
    imprime('Equilibrio de la balanza de pagos')
    debp = ebp - ebp_ini
    mfun.i_tabla(''  , [] , ['equi.bal.pag',], debp                  , False, DECIMALES)
    imprime('')
    dApz0 = Apz - datos.Apz0
    mfun.i_tabla(''  , [] , ['Apz',]      , dApz0                  , False, 5)
    imprime('')
    imprime('')

def diferencias_importes_finales_iniciales(datos, parametros, DECIMALES, ind, dem, h, vec_opt_ini, vec_opt, npre_sol, etq_precios, ebp_ini, res_ecuaciones, rot):
    nfac = len(h)
    nsec = len(ind)
    ndem = len(dem)
    (Apz,Fi,Ei,Mi,Di,Xpi,pf,pq,pe,pm,
        Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,Sf ,AgE ,AgH ,CssE ,CssH,ebp,Zl,pz,
        Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,Sfr,AgEr,AgHr,CssEr,CssHr,ebpr,
        Ti,Tir
    ) = res_ecuaciones
    imprime('Diferencias entre los valores finales y los iniciales')
    imprime('')
    vec = vec_opt - vec_opt_ini

    pf = prin.extrae_var(vec_opt, 'pF', 0, nfac - 1)
    pf = prin.completa_pf(pf, F)
    py = prin.extrae_var(vec_opt, 'pY', 0, nsec)
    pq = prin.extrae_var(vec_opt, 'pQ', 0, nsec)
    pd = prin.extrae_var(vec_opt, 'pD', 0, nsec)
    epsilon = prin.extrae_var(vec_opt, 'epsilon', 0, 0)
    imprime('{:10}      {:9.7f}'.format('pF_' + h[0], pf[0]))
    imprime('{:10}      {:9.7f}'.format('pF_' + h[1], pf[1]))
    mfun.i_tabla('precios', etq_precios[1:npre_sol], [], vec[1:npre_sol], True, 7)
    dpz = pz - datos.pZ0
    (pe, pm) = exte.precio_moneda_local_pe_pm(datos.pWe, datos.pWm, epsilon)
    dpe = pe - datos.pWe
    dpm = pm - datos.pWm
    respre = np.concatenate((dpz, np.array(dpe), np.array(dpm)))
    mfun.i_tabla('/' , etq_precios[npre_sol:len(etq_precios)] , [], respre, True, 7)
    imprime(rot)
    imprime('---------------------------------------------------------------------------------------------------------')
    imprime('Factores aportados por los hogares. FF')
    dFF0 = FF * pf - datos.FF0 * datos.pF0
    mfun.i_tabla('/' , h  , dem             , dFF0                 , False, DECIMALES)    # factores aportados inicialmente por cada consumidor
    mfun.i_tabla(''  , [] , ['suma FF']     , dFF0.sum(axis=0)     , True , DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Ahorro a largo plazo de los hogares. Alp')
    dAlp0 = Alp * pf - datos.Alp0 * datos.pF0
    mfun.i_tabla(''  , []                   , dem                  , dAlp0             , True , DECIMALES)
    mfun.i_tabla(''  , []                   , ['suma Alp']         , dAlp0.sum(axis=0) , False, DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Factores aportados por los hogares. FF + Alp')
    dFF0 = (FF + Alp) * pf - (datos.FF0 + datos.Alp0) * datos.pF0
    mfun.i_tabla(''  , []                   , dem                  , dFF0              , False, DECIMALES)    # factores aportados en total por cada consumidor
    mfun.i_tabla(''  , [] , ['suma FF+Alp']     , dFF0.sum(axis=0) , True , DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Factores utilizados por los sectores. F')
    dF0 = Fi * pf - datos.F0 * datos.pF0
    mfun.i_tabla(''  , [] , ind            , dF0                   , False, DECIMALES)    # factores utilizados por cada sector
    mfun.i_tabla(''  , [] , ['suma F']     , dF0.sum(axis=0)       , False, DECIMALES)
    mfun.i_pie  ('/' , h)
    imprime('Factor compuesto. Y (Valor Añadido Bruto)')
    dY0 = Yp * py - datos.Y0 * datos.pY0
    mfun.i_tabla(' ' , ind , ['Y',]        , dY0                   , True , DECIMALES)
    imprime('Consumo intermedio filas: ventas, columnas: compras. X')
    dX0 = X * pq - datos.X0 * datos.pQ0
    mfun.i_tabla(''  , [] , ind            , dX0                   , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['compras X',]  , dX0.sum(axis=0)       , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    imprime('Consumo de los hogares. Xp')
    dXp0 = Xp * pq - datos.Xp0 * datos.pQ0
    mfun.i_tabla(''  , [] , dem            , dXp0 , False          , DECIMALES)
    mfun.i_tabla(''  , [] , ['suma Xp']    , dXp0.sum(axis=0)      , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    imprime('Consumo del gobierno. Xg')
    dXg0 = Xg * pq - datos.Xg0 * datos.pQ0
    mfun.i_tabla(''  , [] , ['Xg',]        , dXg0                  , False, DECIMALES)
    imprime('Consumo de inversión. Xv')
    dXv0 = Xv * pq - datos.Xv0 * datos.pQ0
    mfun.i_tabla(''  , [] , ['Xv',]        , dXv0                  , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    imprime('Consumo total')
    mfun.i_tabla(''  , [] , ['X+Xp+Xg+Xv',], dXp0.sum(axis=0) + dXg0 + dXv0 + dX0.sum(axis=1), False, DECIMALES)
    imprime('Producción total')
    dQ0 = Q * pq - datos.Q0 * datos.pQ0
    mfun.i_tabla(''  , [] , ['Q',]        , dQ0                    , False, DECIMALES)
    mfun.i_pie  ('/' , ind)
    dD0 = Di * pd - datos.D0 * datos.pD0
    mfun.i_tabla(''  , [] , ['D',]        , dD0                    , False, DECIMALES)
    dM0 = M * pm - datos.M0 * datos.pWm * datos.epsilon0
    mfun.i_tabla(''  , [] , ['M',]        , dM0                    , False, DECIMALES)
    dE0 = E * pe - datos.E0 * datos.pWe * datos.epsilon0
    mfun.i_tabla(''  , [] , ['E',]        , dE0                    , False, DECIMALES)
    dZ0 = Z * pz - datos.Z0 * datos.pZ0
    mfun.i_tabla(''  , [] , ['Z',]        , dZ0                    , False, DECIMALES)
    imprime('Impuestos')
    dTz0 = Tz * pz - datos.Tz0 * datos.pZ0
    mfun.i_tabla(''  , [] , ['Tz',]       , dTz0                   , False, DECIMALES)
    dTm0 = Tm * pm - datos.Tm0 * datos.pWm * datos.epsilon0
    mfun.i_tabla(''  , [] , ['Tm',]       , dTm0                   , False, DECIMALES)
    dTd0 = Td - datos.Td0
    mfun.i_tabla('/' , dem, ['Td',]       , dTd0                   , False, DECIMALES)
    dTi0 = Ti - datos.Ti0
    mfun.i_tabla(''  , [] , ['Ti',]      , dTi0                    , False, DECIMALES)
    dTg0 = datos.Tg0 - datos.Tg0
    mfun.i_tabla(''  , [] , ['Tg',]      , dTg0                    , False, DECIMALES)
    dTe0 = datos.Te0 - datos.Te0
    mfun.i_tabla(''  , [] , ['Te',]      , dTe0                    , False, DECIMALES)
    dCssH0 = CssH - datos.CssH0
    mfun.i_tabla(''  , [] , ['CssH',]     , dCssH0                 , True , DECIMALES)
    dCssE0 = CssE * pq - datos.CssE0 * datos.pQ0
    mfun.i_tabla('/' , ind, ['CssE',]     , dCssE0                 , True , DECIMALES)
    mfun.i_tabla(''  , [] , ['def/sup ss',], dCssE0.sum() + dCssH0.sum(), False, DECIMALES)
    imprime('Ahorro-Inversión')
    dSp0 = Sp - datos.Sp0
    mfun.i_tabla('/' , dem, ['Sp',]       , dSp0                   , True , DECIMALES)
    dSg0 = Sg - datos.Sg0
    mfun.i_tabla(''  , [] , ['Sg',]       , dSg0                   , False, DECIMALES)
    imprime('Pensiones')
    dPssH0 = datos.PssH0 - datos.PssH0
    mfun.i_tabla('/' , dem, ['PssH',]     , dPssH0                 , False, DECIMALES)
    imprime('Ayudas del gobierno')
    dAgH0 = AgH - datos.AgH0
    mfun.i_tabla('/' , dem, ['AgH',]      , dAgH0                  , False, DECIMALES)
    dAgE0 = AgE * pq - datos.AgE0 * datos.pQ0
    mfun.i_tabla('/' , ind, ['AgE',]      , dAgE0                  , True , DECIMALES)
    imprime('Déficit por cuenta corriente en "divisa"')
    dSf = (M - datos.M0) * datos.pWm * datos.epsilon0 - (E - datos.E0) * datos.pWe * datos.epsilon0
    mfun.i_tabla(''  , [] , ['Sf sectores',]   , dSf                   , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['Sf',]        , dSf.sum()             , False, DECIMALES)
    imprime('Déficit por cuenta corriente en moneda local. (M - E) * cotización - (M0 - E0) * cotización base')
    dSfde = dM0 - dE0
    mfun.i_tabla(''  , [] , ['Sf sectores',] , dSfde                  , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['Sf',]      , dSfde.sum()            , False, DECIMALES)
    imprime('Equilibrio de la balanza de pagos en "divisas"')
    debp = ebp - ebp_ini
    mfun.i_tabla(''  , [] , ['equi.bal.pag',], debp                  , False, DECIMALES)
    imprime('')
    dApz0 = Apz - datos.Apz0
    mfun.i_tabla(''  , [] , ['Apz',]      , dApz0                  , False, 5)
    imprime('')
    imprime('')

def datos_grafico_solucion(datos, parametros, ind, dem, h, v):
    nfac = len(h)
    nsec = len(ind)
    ndem = len(dem)
    res_ecuaciones = prin.sec_ecuaciones(v)
    (Apz,Fi,Ei,Mi,Di,Xpi,pf,pq,pe,pm,
        Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,Sf ,AgE ,AgH ,CssE ,CssH,ebp,Zl,pz,
        Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,Sfr,AgEr,AgHr,CssEr,CssHr,ebpr,
        Ti,Tir
    ) = res_ecuaciones
    # precios
    pf      = prin.extrae_var(v,'pF', 0, nfac - 1)
    pf      = prin.completa_pf(pf, F)
    py      = prin.extrae_var(v,'pY', 0, nsec)
    pq      = prin.extrae_var(v,'pQ', 0, nsec)
    pd      = prin.extrae_var(v,'pD', 0, nsec)
    epsilon = prin.extrae_var(v,'epsilon', 0, 0)
    (pe, pm) = exte.precio_moneda_local_pe_pm(datos.pWe, datos.pWm, epsilon)
    y_pre = np.concatenate((
        pf.flatten(),
        py.flatten(),
        pz.flatten(),
        pd.flatten(),
        pq.flatten(),
        [epsilon]
    ))
    # consumos
    y_dcan =  (Xp[0] - datos.Xp0[0]      ).flatten()
    y_dimp = ((Xp[0] - datos.Xp0[0]) * pq).flatten()
    for i in range(1, Xp.shape[0]):
        y_dcan = np.concatenate((y_dcan,  (Xp[i] - datos.Xp0[i]      ).flatten()))
        y_dimp = np.concatenate((y_dimp, ((Xp[i] - datos.Xp0[i]) * pq).flatten()))
    y_dcan = np.concatenate((y_dcan,  (Xg - datos.Xg0      ).flatten()))
    y_dimp = np.concatenate((y_dimp, ((Xg - datos.Xg0) * pq).flatten()))
    # producciones
    y_can = np.concatenate((
        Z.flatten(),
        E.flatten(),
        Da.flatten(),
        M.flatten(),
        Q.flatten()
    ))
    y_imp = np.concatenate((
        (Z  * pz).flatten(),
        (E  * pe).flatten(),
        (Da * pd).flatten(),
        (M  * pm).flatten(),
        (Q  * pq).flatten()
    ))
    # factores suministrados por los hogares
    y_sfc_c = FF[0] - datos.FF0[0]
    y_sfc_i = (FF[0] - datos.FF0[0]) * pf
    for i in range(1, ndem):
        y_sfc_c = np.concatenate((
            y_sfc_c,
            FF[i] - datos.FF0[i]
        )) 
        y_sfc_i = np.concatenate((
            y_sfc_i,
            (FF[i] - datos.FF0[i]) * pf
        )) 
    # factores utilizados por los sectores
    y_ufc_c = F[0] - datos.F0[0]
    y_ufc_i = (F[0] - datos.F0[0]) * pf
    for i in range(1, nsec):
        y_ufc_c = np.concatenate((
            y_ufc_c,
            F[i] - datos.F0[i]
        )) 
        y_ufc_i = np.concatenate((
            y_ufc_i,
            (F[i] - datos.F0[i]) * pf
        )) 
    return (y_pre, y_dcan, y_dimp, y_can, y_imp, y_sfc_c, y_ufc_c, y_sfc_i, y_ufc_i)

def parrilla_graficos(datos, parametros, ind, dem, h, SENDA_GRAFICOS, FICHERO_IMG, GE_IMG_COL, GE_IMG_FIL, GE_SOLUCIONES, soluciones, Z, Xp, Da, E, M):
    # generar gráficos de evolución
    nfac = len(h)
    nsec = len(ind)
    ndem = len(dem)
    print('')
    print('Generando gráficos ...')
    print('')
    nsol = len(soluciones)
    ncol = GE_IMG_COL
    nimg = GE_IMG_FIL * GE_IMG_COL
    if nimg > nsol:
        nfil = nsol // ncol
        if nfil * ncol < nsol:
            nfil += 1
        nimg = nfil * ncol
    else:
        nfil = GE_IMG_FIL
    nimg_real = min(nimg, nsol)
    titulo  = []
    y_pre   = []
    y_dcan  = []
    y_dimp  = []
    y_can   = []
    y_imp   = []
    y_sfc_c = []
    y_ufc_c = []
    y_sfc_i = []
    y_ufc_i = []
    n       = 0
    for v in soluciones[0:nimg_real]:
        titulo.append(n * GE_SOLUCIONES)
        n += 1
        (y1, y2, y3, y4, y5, y6, y7, y8, y9) = datos_grafico_solucion(datos, parametros, ind, dem, h, v[1])
        y_pre.append(y1)
        y_dcan.append(y2)
        y_dimp.append(y3)
        y_can.append(y4)
        y_imp.append(y5)
        y_sfc_c.append(y6)
        y_ufc_c.append(y7)
        y_sfc_i.append(y8)
        y_ufc_i.append(y9)
    x_sol   = []
    ref_sol = []
    vli_sol = []
    eli_sol = []

    # parrilla (mosaico de gráficos) de precios
    etq_x = ['pF','pY','pZ','pD','pQ','Cz']
    x   = []
    for i in range(len(y_pre[0])):
        x.append(i + 1)
    ref_y = np.concatenate((
        datos.pF0.flatten(),
        datos.pY0.flatten(),
        datos.pZ0.flatten(),
        datos.pD0.flatten(),
        datos.pQ0.flatten(),
        [datos.epsilon]
    ))
    v_marca_x = []
    p = 0.5
    v_marca_x.append(p)
    p += len(datos.pF0)
    v_marca_x.append(p)
    p += len(datos.pY0)
    v_marca_x.append(p)
    p += len(datos.pZ0)
    v_marca_x.append(p)
    p += len(datos.pD0)
    v_marca_x.append(p)
    p += len(datos.pQ0)
    v_marca_x.append(p)

    # para precios de la última solución
    x_sol.append(x)
    ref_sol.append(copy.deepcopy(ref_y))
    vli_sol.append(copy.deepcopy(v_marca_x))
    eli_sol.append(copy.deepcopy(etq_x))

    grafico_evolucion(nfil, ncol, x, y_pre, ref_y, v_marca_x, etq_x, SENDA_GRAFICOS, FICHERO_IMG, titulo, 'Pre')

    # parrillas (mosaico de graficos) variación de consumos
    v_marca_x = []
    p = 0.5
    etq_x = []
    v_marca_x.append(p)
    for i in range(ndem):
        etq_x.append('Xp' + str(i + 1))
        p += Xp.shape[1]
        v_marca_x.append(p)
    etq_x.append('Xg')
    x  = []
    for i in range(len(y_dcan[0])):
        x.append(i + 1)
    ref_y = np.zeros(((ndem + 1) * nsec),dtype=np.float64)

    grafico_evolucion(nfil, ncol, x, y_dcan, ref_y, v_marca_x, etq_x, SENDA_GRAFICOS, FICHERO_IMG, titulo, 'VdemCtd')
    grafico_evolucion(nfil, ncol, x, y_dimp, ref_y, v_marca_x, etq_x, SENDA_GRAFICOS, FICHERO_IMG, titulo, 'VdemImp')

    # parrillas (mosaico de graficos) de cantidades e importes
    etq_x = ['Z','E','D','M','Q']
    x  = []
    for i in range(len(y_can[0])):
        x.append(i + 1)
    ref_y = np.concatenate((
        datos.Z0.flatten(),
        datos.E0.flatten(),
        datos.D0.flatten(),
        datos.M0.flatten(),
        datos.Q0.flatten()
    ))
    v_marca_x = []
    p = 0.5
    v_marca_x.append(p)
    p += len(Z)
    v_marca_x.append(p)
    p += len(E)
    v_marca_x.append(p)
    p += len(Da)
    v_marca_x.append(p)
    p += len(M)
    v_marca_x.append(p)

    # para cantidades e importes de la última solución
    x_sol.append(copy.deepcopy(x))
    x_sol.append(copy.deepcopy(x))
    ref_sol.append(copy.deepcopy(ref_y))
    ref_sol.append(copy.deepcopy(ref_y))
    vli_sol.append(copy.deepcopy(v_marca_x))
    vli_sol.append(copy.deepcopy(v_marca_x))
    eli_sol.append(copy.deepcopy(etq_x))
    eli_sol.append(copy.deepcopy(etq_x))

    grafico_evolucion(nfil, ncol, x, y_can, ref_y, v_marca_x, etq_x, SENDA_GRAFICOS, FICHERO_IMG, titulo, 'Pro_Ctd')
    grafico_evolucion(nfil, ncol, x, y_imp, ref_y, v_marca_x, etq_x, SENDA_GRAFICOS, FICHERO_IMG, titulo, 'Pro_Imp')

    # parrillas (mosaico de graficos) variaciones en el suministro de factores
    etq_x = dem
    x  = []
    for i in range(len(y_sfc_c[0])):
        x.append(i + 1)
    ref_y = np.zeros((ndem * nfac),dtype=np.float64)
    v_marca_x = []
    p = 0.5
    for i in range(ndem):
        v_marca_x.append(p)
        p += nfac
    grafico_evolucion(nfil, ncol, x, y_sfc_c, ref_y, v_marca_x, etq_x, SENDA_GRAFICOS, FICHERO_IMG, titulo, 'V_apor_Fac_Ctd')
    grafico_evolucion(nfil, ncol, x, y_sfc_i, ref_y, v_marca_x, etq_x, SENDA_GRAFICOS, FICHERO_IMG, titulo, 'V_apor_Fac_Imp')

    # parrillas (mosaico de graficos) variaciones en el uso de factores
    etq_x = ind
    x  = []
    for i in range(len(y_ufc_c[0])):
        x.append(i + 1)
    v_marca_x = []
    p = 0.5
    for i in range(nsec):
        v_marca_x.append(p)
        p += nfac
    ref_y = np.zeros((nsec * nfac),dtype=np.float64)
    grafico_evolucion(nfil, ncol, x, y_ufc_c, ref_y, v_marca_x, etq_x, SENDA_GRAFICOS, FICHERO_IMG, titulo, 'V_uso_Fac_Ctd')
    grafico_evolucion(nfil, ncol, x, y_ufc_i, ref_y, v_marca_x, etq_x, SENDA_GRAFICOS, FICHERO_IMG, titulo, 'V_uso_Fac_Imp')

    # gráfico de la última solución
    titulo = ['Precios', 'Cantidades', 'Importes']
    MUESTRA_PROGRESO = False
    (y1, y2, y3, y4, y5, y6, y7, y8, y9) = datos_grafico_solucion(datos, parametros, ind, dem, h, soluciones[-1][1])
    y_sol = [y1, y4, y5]
    grafico_resumen(SENDA_GRAFICOS, FICHERO_IMG, x_sol, y_sol, ref_sol, vli_sol, eli_sol, titulo)

def grafico_evolucion(n_filas_img, n_cols_img, x, y, y_ref, v_marca_x, etq_x, SENDA_GRAFICOS, FICHERO_IMG, titulo, sufijo):
    if n_filas_img == 1:
        # asegurar un mosaico de gráficos con dos dimensiones
        n_filas_img = 2
    fig, axes = plt.subplots(nrows=n_filas_img, ncols=n_cols_img, figsize=(24, 12), sharey=True)
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    plt.rcParams.update({'font.size': 12})
    nimg = len(y)
    ymax = max(np.max(y), np.max(y_ref)) * 1.05
    yt = min(np.min(y), np.min(y_ref))
    franja = (ymax - yt) / 12.
    ymin = yt - franja
    if ymin == ymax:
        # normalmente será porque todos los valores son cero
        ymin = -0.5
        ymax =  0.5
    y_etq_x = ymin + (ymax - ymin) * 0.01
    m = 0
    for fil in range(n_filas_img):
        for col in range(n_cols_img):
            axes[fil, col].scatter(x, y_ref , s=44, c='aquamarine', marker='s')
            axes[fil, col].scatter(x, y[m], s=16, c='0'         , marker='o')
            vmin = np.min(y[m])
            vmax = np.max(y[m])
            if abs(vmin) > 100:
                vmin = '{:d}'.format(round(vmin))
            else:
                vmin = '{:.3f}'.format(round(vmin,3))
            if abs(vmax) > 100:
                vmax = '{:d}'.format(round(vmax))
            else:
                vmax = '{:.3f}'.format(round(vmax,3))
            axes[fil, col].title.set_text('{}   [{}  {}]'.format(titulo[m], vmin, vmax))
            axes[fil, col].vlines(x=v_marca_x, ymax=ymax, ymin=ymin, colors='black', linewidth=1)
            if ymin < 0:
                axes[fil, col].axhline(y=0, xmin=0, xmax=1, c='grey', linewidth=1)
            for i in range(len(etq_x)):
                axes[fil, col].annotate(etq_x[i], xy=(v_marca_x[i] + 0.2, y_etq_x))
            axes[fil, col].set_ylim(ymin, ymax)
            axes[fil, col].set_xticks([])
            axes[fil, col].title.set_size(16)
            axes[fil, col].tick_params(axis='both', which='major', labelsize=12)
            axes[fil, col].yaxis.get_major_formatter().set_scientific(False)
            m += 1
            if m == nimg:
                break;
        if m == nimg:
            break;
    fig.tight_layout()
    plt.savefig('{}/{}_{}.png'.format(SENDA_GRAFICOS, FICHERO_IMG, sufijo), dpi = 300, facecolor = 'w', edgecolor = 'w', orientation = 'portrait', format = 'png', transparent = False, bbox_inches = None, pad_inches = 0.1, metadata = None)
    plt.close()

def grafico_resumen(SENDA_GRAFICOS, FICHERO_IMG, x, y, ref, v_marca_x, etq_x, titulo):
    n_filas_img = 3
    n_cols_img  = 1
    fig, axes = plt.subplots(nrows=n_filas_img, ncols=n_cols_img, figsize=(18, 24))
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    plt.rcParams.update({'font.size': 24})
    nimg = len(y)
    ymin = []
    ymax = []
    yli  = []
    for i in range(3):
        ymaxt = max(np.max(y[i]), np.max(ref[i])) * 1.05
        yt = min(np.min(y[i]), np.min(ref[i]))
        franja = (ymaxt - yt) / 12.
        ymint = yt - franja
        if ymint == ymaxt:
            # normalmente será porque todos los valores son cero
            ymint = -0.5
            ymaxt =  0.5
        ymin.append(ymint)
        ymax.append(ymaxt)
        yli.append (ymin[i] + (ymax[i] - ymin[i]) * 0.008)
    m = 0
    for fil in range(n_filas_img):
        for col in range(n_cols_img):
            axes[m].scatter(x[m], ref[m] , s=120, c='aquamarine', marker='s')
            axes[m].scatter(x[m], y[m], s=72, c='0'         , marker='o')
            axes[m].title.set_text(titulo[m])
            axes[m].vlines(x=v_marca_x[m], ymax=ymax[m], ymin=ymin[m], colors='black', linewidth=1)
            if ymin[m] < 0:
                axes[m].axhline(y=0, xmin=0, xmax=1, c='grey', linewidth=1)
            for i in range(len(etq_x[m])):
                axes[m].annotate(etq_x[m][i], xy=(v_marca_x[m][i] + 0.2, yli[m]))
            axes[m].set_ylim(ymin[m], ymax[m])
            axes[m].set_xticks([])
            axes[m].title.set_size(32)
            axes[m].tick_params(axis='both', which='major', labelsize=24)
            axes[m].yaxis.get_major_formatter().set_scientific(False)
            m += 1
            if m == nimg:
                break;
        if m == nimg:
            break;
    fig.tight_layout()
    plt.savefig('{}/{}_Res.png'.format(SENDA_GRAFICOS, FICHERO_IMG), dpi = 300, facecolor = 'w', edgecolor = 'w', orientation = 'portrait', format = 'png', transparent = False, bbox_inches = None, pad_inches = 0.1, metadata = None)
    plt.close()
    
def grafico_CES_local_importacion(SENDA_GRAFICOS, datos, parametros, ind, dem, h):
    # vamos a repesentar un mapa con los valores de la produción Armington (Q) en función de la producción para la demanda local y la importación
    nfac = len(h)
    nsec = len(ind)
    ndem = len(dem)

    # calculamos la producción (Q) que corresponde a cada uno de los elementos de X, es decir, de cada una de las 10000 posibles combinaciones de local e importación
    puntos = 100
    Q = np.zeros((nsec, puntos * puntos), dtype=np.float64)
    for i in range(nsec):
        # generamos 100 valores que van de (0.8 * D0) a (1.2 * D0) (ambos inclusive)
        xmin = 0.8 * datos.D0[i]
        xmax = 1.2 * datos.D0[i]
        ymin = 0.8 * datos.M0[i]
        ymax = 1.2 * datos.M0[i]
        vmin = min(xmin, ymin)
        vmax = max(xmax, ymax)

        x = np.linspace(vmin, vmax, num=puntos)     
        y = np.linspace(vmin, vmax, num=puntos)     

        # ahora, 'itertools.product' genera todas las posibles combinaciones de los elementos de x e y
        # que son 'puntos * puntos' elementos = 100 * 100 = 10000
        # los elementos de X son las posibles opciones: local e importación, es decir, 2 valores por elemento
        X = np.array([i for i in itertools.product(x, y)])   
        Q[i]  = exte.produccion_armington_Q(parametros.gamma[i], parametros.deltam[i], parametros.deltad[i], X[:,0], X[:,1], parametros.eta[i]) # 6.17
        imprime('producción Q de {}: mínima= {:10.2f} máxima = {:10.2f}'.format(ind[i], min(Q[i]), max(Q[i])))

        # dibujamos (2D) la producción (Q) en función de la produción para la demanda local y la importación
        # aerea de dibujo cuadrada
        fig, ax = plt.subplots(figsize=(10,10))

        # dibuja el contorno para 'CONTORNOS' rangos de valores de la producción (especie de curvas de nivel), los contornos son polígonos
        # que encierran los puntos dentro del rango de producción correspondiente: (producción máxima - produducción mínima) / CONTORNOS
        CONTORNOS = 60
        ve = plt.contourf(x, y, Q[i].reshape(len(x), len(y)), levels=CONTORNOS)

        # acotar el área de trabajo
        ax.vlines(x=xmin, ymin=vmin, ymax=vmax, colors='blue', linewidth=4)
        ax.vlines(x=xmax, ymin=vmin, ymax=vmax, colors='red', linewidth=4)
        ax.hlines(y=ymin, xmin=vmin, xmax=vmax, colors='blue', linewidth=4)
        ax.hlines(y=ymax, xmin=vmin, xmax=vmax, colors='red', linewidth=4)

        plt.xlabel('Producción D', size=18)
        plt.ylabel('Importación M', size=18)
        nombre = '/2D_{}_{}_gam{:.3e}_dm{:.3e}_dd{:.3e}_eta{:.3e}'.format('Q', ind[i], parametros.gamma[i], parametros.deltam[i], parametros.deltad[i], parametros.eta[i]).replace('.',',')
        plt.title('equi-Q gam={:.3e} dm={:.3e} dd={:.3e} eta={:.3e}'.format(parametros.gamma[i], parametros.deltam[i], parametros.deltad[i], parametros.eta[i]).replace('.',','), size=18)
        plt.savefig(SENDA_GRAFICOS + nombre + '.png', dpi = 300, facecolor = 'w', edgecolor = 'w', orientation = 'portrait', format = 'png', transparent = False, bbox_inches = None, pad_inches = 0.1, metadata = None)
        plt.close()
        
        # dibujar el contorno central
        
        contornos = ve.allsegs                      # colección de contornos
        if len(contornos) > 0:
            CONTORNO  = len(contornos) // 2         # contorno central
            segmentos = contornos[CONTORNO]         # es 1, en nuestro caso solo hay un polígono por contorno
            vertices  = contornos[CONTORNO][0]      # un vertice por cada punto que forma parte del polígono del contorno
            if len(vertices) > 0:
                coordenadas = len(vertices[0])      # cada vertice tiene 2 coordenadas porque estamos en 2D
                imprime('contornos: {} segmentos: {} vertices:{} coordenadas: {}'.format(len(contornos), len(segmentos), len(vertices), coordenadas))
                anchoq = ve.levels[1] - ve.levels[0]
                imprime('ancho intervalos de Q {}'.format(anchoq))
                imprime('')
                plt.figure(figsize=(10,10))
                
                # el 'for' es retórico porque sólo hay un segmento (polígono)
                for segmento in segmentos:
                    plt.plot(segmento[:,0], segmento[:,1], '.')
                    plt.xlabel('Producción D', size=18)
                    plt.ylabel('Importación M', size=18)
                    nombre = '/CT_{}_gam{:.3e}_dm{:.3e}_dd{:.3e}_eta{:.3e}'.format(ind[i], parametros.gamma[i], parametros.deltam[i], parametros.deltad[i], parametros.eta[i]).replace('.',',')
                    plt.title('equi-Q {} Q ∈ [{:.0f} , {:.0f}]'.format(ind[i],ve.levels[CONTORNO],ve.levels[CONTORNO+1]).replace('.',','), size=18)
                    plt.savefig(SENDA_GRAFICOS + nombre + '.png', dpi = 300, facecolor = 'w', edgecolor = 'w', orientation = 'portrait', format = 'png', transparent = False, bbox_inches = None, pad_inches = 0.1, metadata = None)
                    plt.close()
        
        # en 3D, con el valor de la producción Q en el eje z
        xx, yy = np.meshgrid(x, y)
        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection='3d')
        surf = ax.plot_surface(xx, yy, Q[i].reshape(len(x), len(y)), rstride=1, cstride=1, cmap='viridis')
        ax.set_xlabel('Producción D', size=18)
        ax.set_ylabel('Importación M', size=18)
        ax.set_zlabel('Q', size=18)
        nombre = '/3D_{}_{}_gam{:9.3e}_dm{:9.3e}_dd{:9.3e}_eta{:9.3e}'.format('Q', ind[i], parametros.gamma[i], parametros.deltam[i], parametros.deltad[i], parametros.eta[i]).replace('.',',')
        ax.set_title('equi-Q gam:{:9.3e} dm:{:9.3e} dd:{:9.3e} eta:{:9.3e}'.format(parametros.gamma[i], parametros.deltam[i], parametros.deltad[i], parametros.eta[i]).replace('.',','), size=18)

        plt.savefig(SENDA_GRAFICOS + nombre + '.png', dpi = 300, facecolor = 'w', edgecolor = 'w', orientation = 'portrait', format = 'png', transparent = False, bbox_inches = None, pad_inches = 0.1, metadata = None)
        plt.close()

def isocuanta(SENDA_GRAFICOS, PREFIJO, datos, parametros, ind, dem, h, Dr, Mr, Dmenos, Dmas, Mmas, Dinc, Minc, tol, exten=1, modo=1, f=2.):
    nfac = len(h)
    nsec = len(ind)
    ndem = len(dem)
    
    for i in range(nsec):

        # isocuanta para los valores D y M de cada sector
        vD     = Dr[i]
        vM     = Mr[i]

        sigma  = parametros.sigma[i]
        eta    = parametros.eta[i]
        deltad_src = parametros.deltad[i]
        deltam_src = parametros.deltam[i]
        gamma_src  = parametros.gamma[i]
        vQref, apuntos = isocuanta_sector(i, SENDA_GRAFICOS, PREFIJO, datos, parametros, ind, dem, h, ind[i], gamma_src, deltad_src, deltam_src, eta, Dr[i], Mr[i], Dmenos, Dmas, Mmas, Dinc, Minc, tol)
        hay = False
        if len(apuntos) > 0:
            hay = True
            plt.figure(figsize=(10,10))
            if modo == 0:
                plt.plot(apuntos[:,0], apuntos[:,1], '-b', linewidth=2*f, label='Q ={:8.0f} sigma {:7.3f}'.format(vQref, sigma))
            else:
                plt.plot(apuntos[:,0], apuntos[:,1], '-b', linewidth=2*f, label='sigma {:7.3f}'.format(sigma))
        
        # hacer doble el valor de sigma
        sigma  = 2. * parametros.sigma[i]
        eta    = (sigma - 1.) / sigma

        # recalibrar
        (deltam_rc, deltad_rc) = ecua.coeficientes_armington_deltam_deltad(datos.taum[i], eta, datos.M0[i], datos.D0[i])
        gamma_rc = ecua.coeficiente_escala_armington_gamma(datos.Q0[i], deltam_rc, deltad_rc, eta, datos.M0[i], datos.D0[i])
        vQ, apuntos = isocuanta_sector(i, SENDA_GRAFICOS, PREFIJO, datos, parametros, ind, dem, h, ind[i], gamma_src, deltad_rc, deltam_rc, eta, Dr[i], Mr[i], Dmenos, Dmas, Mmas, Dinc, Minc, tol)
        if len(apuntos) > 0:
            if hay == False:
                hay = True
                plt.figure(figsize=(10,10))
            if modo == 0:
                plt.plot(apuntos[:,0], apuntos[:,1], ':k', linewidth=2*f, label='Q ={:8.0f} sigma {:7.3f}'.format(vQ, sigma))
            else:        
                plt.plot(apuntos[:,0], apuntos[:,1], ':k', linewidth=2*f, label='sigma {:7.3f}'.format(sigma))

        if exten == 1:

            # sin recalibrar
            deltad_src = parametros.deltad[i]
            deltam_src = parametros.deltam[i]
            gamma_src  = parametros.gamma[i]

            # con la 'eta' de 'sigma' doble

            # buscar la D (vD) de la isocuanta 'vQref' con M = vM
            # el valor de la isocuanta crece con sigma, luego debe ser inferior a 'Dr[i]'
            vD, vQ = busca_D_isocuanta(vQref, vM, gamma_src, deltad_src, deltam_src, eta, Dr[i], 0, -0.2, tol)
            if vD == -1:
                imprime('sigma = {} no se encuentra un valor de D para la isocuanta {:8.0f} con M = {:8.0f}'.format(sigma, vQref, vM))
            else:
                vQ, apuntos = isocuanta_sector(i, SENDA_GRAFICOS, PREFIJO, datos, parametros, ind, dem, h, ind[i], gamma_src, deltad_src, deltam_src, eta, vD, Mr[i], Dmenos, Dmas, Mmas, Dinc, Minc, tol)
                if len(apuntos) > 0:
                    if hay == False:
                        hay = True
                        plt.figure(figsize=(10,10))
                    if modo == 0:
                        plt.plot(apuntos[:,0], apuntos[:,1], ':r', linewidth=2*f, label='Q ={:8.0f} sigma {:7.3f} scal'.format(vQ, sigma))
                    else:        
                        plt.plot(apuntos[:,0], apuntos[:,1], ':r', linewidth=2*f, label='sigma {:7.3f} scal'.format(sigma))

            # con la 'eta' de dos tercios de 'sigma'
            sigma  = 2. / 3. * parametros.sigma[i]
            eta    = (sigma - 1.) / sigma

            # buscar la D (vD) de la isocuanta 'vQref' con M = vM
            # el valor de la isocuanta crece con sigma, luego debe ser superior a 'Dr[i]'
            vD, vQ = busca_D_isocuanta(vQref, vM, gamma_src, deltad_src, deltam_src, eta, Dr[i], Dr[i] + 50000, 0.2, tol)
            if vD == -1:
                imprime('sigma = {} no se encuentra un valor de D para la isocuanta {:8.0f} con M = {:8.0f}'.format(sigma, vQref, vM))
            else:
                vQ, apuntos = isocuanta_sector(i, SENDA_GRAFICOS, PREFIJO, datos, parametros, ind, dem, h, ind[i], gamma_src, deltad_src, deltam_src, eta, vD, Mr[i], Dmenos, Dmas, Mmas, Dinc, Minc, tol)
                if len(apuntos) > 0:
                    if hay == False:
                        hay = True
                        plt.figure(figsize=(10,10))
                    if modo == 0:
                        plt.plot(apuntos[:,0], apuntos[:,1], ':g', linewidth=2*f, label='Q ={:8.0f} sigma {:7.3f} scal'.format(vQ, sigma))
                    else:        
                        plt.plot(apuntos[:,0], apuntos[:,1], ':g', linewidth=2*f, label='sigma {:7.3f} scal'.format(sigma))
        
        if hay == True:
            xmin, xmax, ymin, ymax = plt.axis()
            plt.vlines(x=(xmin + xmax) / 2., ymin=ymin, ymax=ymax, colors='black', linewidth=1)
            plt.xlabel('Producción D', size=18*f)
            plt.ylabel('Importación M', size=18*f)
            plt.legend(loc="upper right", fontsize=12*f)

            nombre = '/IQ{}_{}_{}'.format(exten, PREFIJO, ind[i])
            plt.title('{} Q={:.0f}'.format(ind[i], vQref).replace('.',','), size=18*f)
            plt.savefig(SENDA_GRAFICOS + nombre + '.png', dpi = 300, facecolor = 'w', edgecolor = 'w', orientation = 'portrait', format = 'png', transparent = False, bbox_inches = None, pad_inches = 0.1, metadata = None)
        plt.close()

def busca_D_isocuanta(vQ, vM, gamma, deltad, deltam, eta, Dini, Dfin, Dinc, tol):
    for vx in np.arange(Dini, Dfin, Dinc):
        qt = exte.produccion_armington_Q(gamma, deltam, deltad, vM, vx, eta)
        if abs(qt - vQ) < tol:
            return vx, qt
    return -1, 0    

def isocuanta_sector(i, SENDA_GRAFICOS, PREFIJO, datos, parametros, ind, dem, h, sector, gamma, deltad, deltam, eta, Dini, Mini, Dmenos, Dmas, Mmas, Dinc, Minc, tol):
    nfac = len(h)
    nsec = len(ind)
    ndem = len(dem)
    vQ = exte.produccion_armington_Q(gamma, deltam, deltad, Mini, Dini, eta)
    imprime('-----------------------------------------------------------------------------------------------------------------------------------')
    imprime('{} gamma :{:10.6f} deltaD :{:10.6f} deltaM :{:10.6f} eta :{:10.6f}     M0/D0 :{:10.6f}'.format(
                sector, gamma, deltad, deltam, eta, datos.M0[i] / datos.D0[i]))
    imprime('Isocuanta de producción Q:{:10.0f} para los valores D:{:10.0f} M:{:10.0f}'.format(vQ, Dini, Mini))
    if deltam == 0:
        rel_coef  = 1.
    else:
        rel_coef  = deltad / deltam
    exponente = (1. - eta)
    imprime('-----------------------------------------------------------------------------------------------------------------------------------')
    puntos = []
    desde = int(Mini) + Mmas
    for vx in range(int(Dini - Dmenos), int(Dini + Dmas), Dinc):
        for vy in np.arange(desde, 0, Minc):
            qt = exte.produccion_armington_Q(gamma, deltam, deltad, vy, vx, eta)
            if abs(qt - vQ) < tol:
                puntos.append([vx, vy, qt])
                print('\r          \r', end='')
                print(len(puntos),         end='')
                # la y del próximo punto debe ser menor que la de este
                desde = vy
                break
    imprime('      D          M       D + M        dD         dM       M / D    % (M / D)     TMS       % TMS   elasticida       Q      error Q')
    imprime('---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ----------')
    if len(puntos) > 1:
        for ipunto in range(0, len(puntos)):
            D = puntos[ipunto][0]
            M = puntos[ipunto][1]
            MdvD  = M / D
            TMS   = rel_coef * MdvD ** exponente
            if ipunto == 0:
                # usar el dato posterior en lugar del anterior, que no hay
                Da     = puntos[1][0]
                Ma     = puntos[1][1]
                MdvDa  = Ma / Da
                TMSa   = rel_coef * MdvDa ** exponente
            dD    = D - Da
            dM    = M - Ma
            vMdvD = 2. * (MdvD - MdvDa) / (MdvD + MdvDa)
            vTMS  = 2. * (TMS - TMSa) / (TMS + TMSa)   
            elas  = vMdvD / vTMS 

            Da   = D
            Ma   = M
            MdvDa  = MdvD
            TMSa   = TMS

            imprime('{:10.0f} {:10.0f} {:10.0f} {:10.3f} {:10.3f} {:10.3f} {:10.3f} {:10.3f} {:10.3f} {:10.3f} {:10.0f} {:10.0f}'.format(
                        D, M, D + M, dD, dM, MdvD, 100. * vMdvD, TMS, 100. * vTMS, elas, puntos[ipunto][2], puntos[ipunto][2] - vQ))
            if ipunto == 0:
                imprime('---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ----------')

        plt.figure(figsize=(10,10))
        apuntos = np.array(puntos)
        plt.plot(apuntos[:,0], apuntos[:,1], '.')
        plt.xlabel('Producción D', size=18)
        plt.ylabel('Importación M', size=18)
        nombre = '/IS_{}_{}_gam{:.3e}_dm{:.3e}_dd{:.3e}_eta{:.3e}'.format(PREFIJO, sector, gamma, deltam, deltad, eta).replace('.',',')
        plt.title('{} equi-Q={:.0f} D={:.0f} M={:.0f} eta={:.3e}'.format(sector, vQ, Dini, Mini, eta).replace('.',','), size=18)
        plt.savefig(SENDA_GRAFICOS + nombre + '.png', dpi = 300, facecolor = 'w', edgecolor = 'w', orientation = 'portrait', format = 'png', transparent = False, bbox_inches = None, pad_inches = 0.1, metadata = None)
        plt.close()
    imprime('---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ----------')
    imprime('      D          M       D + M        dD         dM       M / D    % (M / D)     TMS       % TMS   elasticida       Q      error Q')
    imprime('')

    # resumen

    if len(puntos) > 0:
        imprime('Resumen')
        imprime('-------------------------------------------')
        cc = len(puntos) // 10
        if cc == 0:
            cc = 1
        imprime('      D          M       D + M         Q')
        imprime('---------- ---------- ---------- ----------')
        for ipunto in range(0, len(puntos), cc):
            D = puntos[ipunto][0]
            M = puntos[ipunto][1]
            imprime('{:10.0f} {:10.0f} {:10.0f} {:10.0f}'.format(D, M, D + M, puntos[ipunto][2]))
        imprime('---------- ---------- ---------- ----------')
        imprime('      D          M       D + M         Q')
        imprime('')
    if len(puntos) > 1:
        return vQ, apuntos
    else:
        return vQ, np.array([])

def reconstruye_MCS(datos, parametros, ind, dem, h, inv,css, idt, gov, trf, ext, ayd, alp,
                    indice_f_tra,pf,py,pq,pd,pz,epsilon,pe,pm,Y,X,F,Z,CssE,Tz,M,AgE,FF,Alp,Xp,Sp,CssH,AgH,Td,Xv,PssH,Xg,Sg,Tg,Ti,Te,Tm,E,Sf,tolerancia,titulo,infor_cuadre):

    Sf = (M.dot(pm) - E.dot(pe))

    fil_col_ind = 0
    nfac = len(h)
    nsec = len(ind)
    ndem = len(dem)
    fil_col_fac = fil_col_ind  + nsec
    fil_col_dem = fil_col_fac  + nfac
    fil_col_inv = fil_col_dem  + ndem
    fil_col_css = fil_col_inv  + len(inv)
    fil_col_idt = fil_col_css  + len(css)
    fil_col_trf = fil_col_idt  + len(idt)
    fil_col_gov = fil_col_trf  + len(trf)
    fil_col_ext = fil_col_gov  + len(gov)
    fil_col_ayd = fil_col_ext  + len(ext)
    fil_col_alp = fil_col_ayd  + len(ayd)
    n_fil_cols  = fil_col_alp  + len(alp)

    rot = []
    rot.extend(list(ind))
    rot.extend(list(h))
    rot.extend(list(dem))
    rot.extend(list(inv))
    rot.extend(list(css))
    rot.extend(list(idt))
    rot.extend(list(trf))
    rot.extend(list(gov))
    rot.extend(list(ext))
    rot.extend(list(ayd))
    rot.extend(list(alp))

    mcs  = np.zeros((n_fil_cols, n_fil_cols), dtype=np.float64)

    # rellenamos cada columna 'col' con los pagos (cantidades/importes) correspondientes a las sucesivas filas, de menor a mayor, 
    # la MCS de cantidades no cuadra, salvo que todos los precios sean 1, porque la que debe cuadrar es la de importes, por eso
    # cuanso se calcule la de cantidades 'cuadre' debe ser False para que no comprueba el cuadre.

    #------------------------------------------------------------------------------------------------
    # sectores. Las primeras 'nsec' columnas
    #------------------------------------------------------------------------------------------------
    # pagos por los consumos intermedios a otros sectores
    col = fil_col_ind
    for i in range(nsec):
        # sector 'i'
        fil = fil_col_ind
        for j in range(nsec):
            # rellenamos las filas (compras a j) de la columna (sector i)

            # X[j,i] compras al sector 'j' por el sector 'i' al precio de 'j'.
            # las filas 'i' de X son las ventas del sector 'i' al 'j' y las columnas 'j' las compras del sector 'i' al sector 'j'
            mcs[fil,col] = X[j,i] * pq[j]
            fil += 1
        col += 1
    # pagos por el uso de los factores de producción (F incluye Alp)
    imF = F * pf
    col = fil_col_ind
    for i in range(nsec):
        fil = fil_col_fac
        for j in range(nfac):
            mcs[fil,col] = imF[i,j]
            fil += 1
        col += 1
    # pago de las cotizaciones de las empresas a la seguridad social
    col = fil_col_ind
    fil = fil_col_css
    for i in range(nsec):
        mcs[fil,col] = CssE[i]  # ya está calculada al precio del factor trabajo (pf)
        col += 1
    # pago de los impuestos a la producción
    col = fil_col_ind
    fil = fil_col_idt
    for i in range(nsec):
        mcs[fil,col] = Tz[i]    # ya están calculados al precio de Z (pz)
        col += 1
    # pago de aranceles a la cuenta 'trf'
    col = fil_col_ind
    fil = fil_col_trf
    for i in range(nsec):
        mcs[fil,col] = Tm[i]   # ya está calculado al precio de importaión (pm)
        col += 1
    # pago por las importaciones de las empresas
    col = fil_col_ind
    fil = fil_col_ext
    imM = M * pm
    for i in range(nsec):
        mcs[fil,col] = imM[i]
        col += 1
    #------------------------------------------------------------------------------------------------
    # columnas factores de producción. Las iguientes 'nfac' columnas
    #------------------------------------------------------------------------------------------------
    # pagos de los sectores por los factores de produccion = ingresos de los hogares por los factores de produccion
    imFF = FF * pf
    # FF no contiene los Alp
    imAlp = Alp * pf
    col = fil_col_fac
    for i in range(nfac):
        fil = fil_col_dem
        for j in range(ndem):
            mcs[fil,col] = imFF[j,i] + imAlp[j,i]
            fil += 1
        col += 1
    #------------------------------------------------------------------------------------------------
    # hogares. Las siguientes 'ndem' columnas
    #------------------------------------------------------------------------------------------------
    # pagos de los hogares por sus consumos
    imXp = Xp * pq
    col = fil_col_dem
    for i in range(ndem):
        fil = fil_col_ind
        for j in range(nsec):
            mcs[fil,col] = imXp[i,j]
            fil += 1
        col += 1
    # transferencia de los ahorros (a corto) de los hogares a la cuenta de inversiones para que esta las
    # transfiera luego a los sectores como inversiones
    col = fil_col_dem
    for i in range(ndem):
        fil = fil_col_inv
        mcs[fil,col] = Sp[i]
        col += 1
    # transferencia a la cuenta de ahorro a largo plazo 
    imAlp = Alp * pf
    col = fil_col_dem
    fil = fil_col_alp
    for i in range(ndem):
        # cada hogar su ahorro a largo plazo
        mcs[fil,col] = imAlp.sum(axis=1)[i] # sumados los factores
        col += 1
    # pagos de la cotización de los hogares a la seguridad social
    col = fil_col_dem
    fil = fil_col_css
    for i in range(ndem):
        mcs[fil,col] = CssH[i]
        col += 1
    # como 'Td' es el total de impuestos directos lo repartimos en la misma relación
    # que tenían los impuestos directos y los ottros impuestos en la MCS
    # pagos de impuestos directos por los hogares
    col = fil_col_dem
    fil = fil_col_idt
    Td_id = 0.
    for i in range(ndem):
        if datos.Td0[i] > 0:
            v = Td[i] * datos.Toi0[i] / datos.Td0[i]
            mcs[fil,col] = v
            Td_id += v
            col += 1
    # añadimos los pagos de los otros impuestos sobre los productos pagados por los hogares.
    col = fil_col_dem
    fil = fil_col_idt
    Td_oi = 0.
    for i in range(ndem):
        if datos.Td0[i] > 0:
            v = Td[i] * datos.Tid0[i] / datos.Td0[i]
            mcs[fil,col] += v
            Td_oi += v
            col += 1
    #------------------------------------------------------------------------------------------------
    # ahorro + inversion´. Las siguientes 'len(inv)' columnas (una)
    #------------------------------------------------------------------------------------------------
    # ahorro que se invierte en cada sector (todos los ahorros: hogares, gobierno, css, exterior)
    imXv = Xv * pq
    col = fil_col_inv
    fil = fil_col_ind
    for i in range(nsec):
        mcs[fil,col] = imXv[i]
        fil += 1
    #------------------------------------------------------------------------------------------------
    # seguridad social. Las siguientes 'len(css)' columnas (una)
    #------------------------------------------------------------------------------------------------
    if len(css) > 0:
        if PssH.sum() == 0:
            # si no paga pensiones es que las paga el gobierno, po lo tanto
            # transferimos todos sus ingreso al gobierno
            col = fil_col_css
            fil = fil_col_gov
            mcs[fil,col] = CssH.sum() + CssE.sum()
        else:
            # es una cuenta autónoma (desligada del gobierno): ingresa, paga y ahorra
            # paga las pensiones
            col = fil_col_css
            fil = fil_col_dem
            for i in range(ndem):
                mcs[fil,col] = PssH[i]
                fil += 1
            # ahorro + inversión = todo lo recaudado menos las pensiones
            # transfiere a la cuenta de inversiones el ahorro
            col = fil_col_css
            fil = fil_col_inv
            mcs[fil,col] = CssH.sum() + CssE.sum() - PssH.sum()
    #------------------------------------------------------------------------------------------------
    # Las siguientes 'len(idt)' columnas (una)
    # transferencias al gobierno de lo recaudado por 'idt' en conepto de
    # impuestos a la producción 
    # impuestos sobre los productos pagados por los hogares.
    # impuestos pagados por el gobierno
    #------------------------------------------------------------------------------------------------
    if len(idt) > 0:
        col = fil_col_idt
        fil = fil_col_gov
        mcs[fil,col] = Tz.sum() + Td_id + Td_oi + Tg + Ti + Te
    #------------------------------------------------------------------------------------------------
    # aranceles. Las siguientes 'len(trf)' columnas  (una)
    # transferencia de los aranceles, recaudados de los sectores por 'trf', al gobierno
    #------------------------------------------------------------------------------------------------
    if len(trf) > 0:
        col = fil_col_trf
        fil = fil_col_gov
        mcs[fil,col] = Tm.sum()
    #------------------------------------------------------------------------------------------------
    # sector público (gobierno). Las siguientes 'len(gov)' columnas  (una)
    #------------------------------------------------------------------------------------------------
    # consumos
    imXg = Xg * pq
    col = fil_col_gov
    fil = fil_col_ind
    for j in range(nsec):
        mcs[fil,col] = imXg[j]
        fil += 1
    # ahorro + inversión
    col = fil_col_gov
    fil = fil_col_inv
    mcs[fil,col] = Sg
    # impuestos gobierno
    col = fil_col_gov
    fil = fil_col_idt
    mcs[fil,col] = Tg
    # impuestos ahorro
    col = fil_col_inv
    fil = fil_col_idt
    mcs[fil,col] = Ti
    # impuestos sector exterior
    col = fil_col_ext
    fil = fil_col_idt
    mcs[fil,col] = Te
    # ayudas
    col = fil_col_gov
    fil = fil_col_ayd
    mcs[fil,col] = AgE.sum() + AgH.sum()

    #------------------------------------------------------------------------------------------------
    # sector exterior. Las siguientes 'len(ext)' columnas  (una)
    #------------------------------------------------------------------------------------------------
    # exportaciones
    imE = E * pe
    col = fil_col_ext
    fil = fil_col_ind
    for i in range(nsec):
        mcs[fil,col] = imE[i]
        fil += 1
    # ahorro + inversión
    col = fil_col_ext
    fil = fil_col_inv
    #mcs[fil,col] = Sf * epsilon
    mcs[fil,col] = Sf
    #------------------------------------------------------------------------------------------------
    # ayudas. Las siguientes 'len(ayd)' columnas  (una)
    #------------------------------------------------------------------------------------------------
    # a las empresas
    if len(ayd) > 0:
        col = fil_col_ayd
        fil = fil_col_ind
        for i in range(nsec):
            mcs[fil,col] = AgE[i]
            fil += 1
        # a los hogares
        col = fil_col_ayd
        fil = fil_col_dem
        for i in range(ndem):
            mcs[fil,col] = AgH[i]
            fil += 1

    #------------------------------------------------------------------------------------------------
    # Ajuste de los Alp
    # Conceptualmente los Alp hacen que no se cierre el círculo económico y que la MCS se descuadre
    # los sectores las pagan y los hogares las cobran, pero no hacen nada con ellas por lo que las filas
    # de los sectores se descuadran, no tienen un ingreso que las respalde, que debería provenir de la
    # circularidad de las relaciones económicas. Nosotros las vamos a tratar como el ahorro a corto plazo
    # que en un modelo estático no tiene otro papel (no se hace nada con ellas) que el de cuadrar la MCS:
    #   los hogares las transfieren a la cuenta ALP, igual que los ahorros a corto a la cuenta INV
    #   la cuenta Alp las asigna a lo sectores tal como como se hace con los otros ahorrros, salvo
    #   por la forma de reparto, la única forma que el modelo tiene se saber cuanto corresponde a
    #   cada sector es por el descuadre entre la suma de la fila y columna del sector, pero esto
    #   es peligroso porque puede esconder errores, empíricamente se observa que el reparto correcto
    #   es proporcionalmente a la producción bruta Z de cada sector.
    #------------------------------------------------------------------------------------------------
    # repartir el total de Alp entre sectores en proporción a su producción bruta
    if len(alp) > 0 and abs(Alp).sum() > 0:
        imAlp  = Alp * pf
        totAlp = imAlp.sum()
        totZ   = 0.
        for i in range(nsec):
            totZ += Z[i] * pz[i]
        col = fil_col_alp
        fil = fil_col_ind
        for i in range(nsec):
            mcs[fil,col] = totAlp * Z[i] * pz[i] / totZ
            fil += 1

    #------------------------------------------------------------------------------------------------
    # comprobar cuadre de filas y columnas
    #------------------------------------------------------------------------------------------------
    recursos    = mcs.sum(axis=1) # suma de las filas
    empleos     = mcs.sum(axis=0) # suma de las columnas
    diferencias = empleos - recursos
    if infor_cuadre and (np.any(abs(diferencias) > tolerancia)):
        # al menos una cuenta difiere ( abs(columna - fila) ) en más que 'tolerancia'
        imprime('')
        imprime('ERROR. ' + titulo + '. No cuadra. La suma de fila y columna de al menos una cuenta no coincide.')
        imprime('                 empleos     recursos   diferencia')
        imprime('------------ ------------ ------------ ------------')
        for i in range(len(empleos)):
            imprime('{:<12} {:12.{prec}f} {:12.{prec}f} {:12.{prec}f}'.format(rot[i], empleos[i], recursos[i], empleos[i] - recursos[i], prec=prin.DECIMALES))
        imprime('------------ ------------ ------------ ------------')
        imprime('{:<12}                           {:12.{prec}f}'.format('suma', diferencias.sum(), prec=prin.DECIMALES))
        imprime('')
    return (rot, mcs)

def imprime_MCS(rot, mcs, DECIMALES, tolerancia, titulo, infor_cuadre):
    if DECIMALES == 0:
        ESPA = 8
        subraya = '--------'
    else:
        ESPA = 9
        subraya = '---------'
    imprime(titulo)
    imprime('')
    n = len(rot)
    # 'recursos' y 'empleos' sumaran valores redondeados a DECIMALES
    empleos  = np.zeros(n, dtype=np.float64)
    recursos = np.zeros(n, dtype=np.float64)
    imprime('{:12}'.format(''), False)
    for i in range(n):
        imprime(' {:>{espa}}'.format(rot[i], espa=ESPA), False)
    imprime(' {:>{espa}}'.format('Recursos', espa=ESPA))
    imprime('{:12}'.format('------------'), False)
    for i in range(n):
        if i == prin.nsec:
            imprime('  ', False)
        imprime(' {:>{espa}}'.format(subraya, espa=ESPA), False)
    imprime(' {:>{espa}}'.format(subraya, espa=ESPA))
    # para cada fila
    for i in range(n):
        if i == prin.nsec:
            imprime('{:12}'.format('------------'), False)
            for k in range(n):
                if k == prin.nsec:
                    imprime('  ', False)
                imprime(' {:>{espa}}'.format(subraya, espa=ESPA), False)
            imprime(' {:>{espa}}'.format(subraya, espa=ESPA))
            imprime('{:12}'.format(''), False)
            for k in range(n):
                if k == prin.nsec:
                    imprime('  ', False)
                imprime(' {:>{espa}}'.format(rot[k], espa=ESPA), False)
            imprime(' {:>{espa}}'.format('Recursos', espa=ESPA))
            imprime('{:12}'.format('------------'), False)
            for k in range(n):
                if k == prin.nsec:
                    imprime('  ', False)
                imprime(' {:>{espa}}'.format(subraya, espa=ESPA), False)
            imprime(' {:>{espa}}'.format(subraya, espa=ESPA))
        imprime('{:12}'.format(rot[i]), False)
        # para cada columna de la fila
        for j in range(n):
            if j == prin.nsec:
                imprime('  ', False)
            v = np.round(mcs[i,j], DECIMALES) 
            imprime(' {:{espa}.{prec}f}'.format(v, espa=ESPA, prec=DECIMALES), False)
            recursos[i] += v    # suma de la fila 'i'
            empleos[j]  += v    # suma de la columna 'j'
        imprime(' {:{espa}.{prec}f}'.format(recursos[i], espa=ESPA, prec=DECIMALES))
    imprime('{:>{espa}}'.format('------------', espa=ESPA), False)
    for i in range(n):
        if i == prin.nsec:
            imprime('  ', False)
        imprime(' {:>{espa}}'.format(subraya, espa=ESPA), False)
    imprime(' {:>{espa}}'.format(subraya, espa=ESPA))
    imprime('{:12}'.format('Empleos'), False)
    for i in range(n):
        if i == prin.nsec:
            imprime('  ', False)
        imprime(' {:{espa}.{prec}f}'.format(empleos[i], espa=ESPA, prec=DECIMALES), False)
    imprime('')
    imprime('')
    if infor_cuadre:
        if np.any(abs(empleos - recursos) > tolerancia):
            # al menos una cuenta difiere ( abs(columna - fila) redondeadas) en más que 'tolerancia'
            if np.all(abs(mcs.sum(axis=0) - mcs.sum(axis=1)) < tolerancia) == True:
                # las sumas de fila y columna, sin redondear, de todas las cuentas coinciden 
                imprime('Las diferencias entre empleos y recursos se deben exclusivamente a los redondeos de impresión')
            else:
                imprime('ERROR en la impresión. ' + titulo + '. No cuadra.')
            imprime('')
