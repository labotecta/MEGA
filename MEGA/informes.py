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
    mfun.i_tabla('/' , h  , dem             , datos.FF0            , False, DECIMALES)    # factores aportados por cada consumidor
    mfun.i_tabla(''  , [] , ['suma FF']     , datos.FF0.sum(axis=0), True , DECIMALES)
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
    imprime('Consumo intermedio (filas), ventas (columnas). X0')
    mfun.i_tabla(''  , [] , ind             , datos.X0.T            , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['ventas X0',]    , datos.X0.T.sum(axis=0), False, DECIMALES)
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
    mfun.i_tabla(''  , [] , ['Sf sectores',]   , Sfde                  , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['Sf',]        , Sfde.sum()            , False, DECIMALES)
    imprime('Equilibrio de la balanza de pagos')
    mfun.i_tabla(''  , [] , ['equi.bal.pag',], ebp_ini               , False, DECIMALES)
    imprime('')
    mfun.i_tabla(''  , [] , ['Apz0',]      , datos.Apz0            , False, 5)
    imprime('')
    if VALOR_F_TRA == 0:
        paro = 100. * (1. - datos.F0[:,INDICE_F_TRA].sum() / datos.PobAct)
        mfun.i_tabla(''  , []                   , ['Pobla.activa',],datos.PobAct, False, DECIMALES)
        mfun.i_tabla(''  , []                   , ['% paro',]     , paro       , False, 2)
        imprime('')
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
    TMS = parametros.deltad / parametros.deltam * ((datos.M0 / datos.D0) ** (1 - parametros.eta))
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

    imprime('alfa. Participación de los productos en la función de utilidad de la demanda')
    mfun.cabecera('alfa', ind)
    mfun.cuerpo2D(dem, parametros.alfa)
    mfun.cierre(ind)
    imprime('')
    if DEM_ESENCIALES:
        imprime('alfa. Participación de los productos en la función de utilidad de la demanda con consumos esenciales')
        mfun.cabecera('alfa esen.', ind)
        mfun.cuerpo2D(dem, parametros.alfa_esen)
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

def veri_solucion(datos, parametros, ind, dem,
                  vec_veri_sol, etq_veri, DEM_ESENCIALES, DEM_ADICIONAL_TIPO, DEM_ADICIONAL, RENTA_FICTICIA, INDICE_F_TRA, AYD_ADI_DEM, AHORRO_L_PLAZO, CON_ESENCIALES,
                  titulo, tolerancia
                  ):
    (pf,py,pz,pq,pd,epsilon,Apz,F,Z,E,M,D,FF,Y,X,Xp,Xg,Xv,Q,ebp,Sp,Sg,Td,Tz,Tm,CssE,CssH,AgE,AgH,Alp) = vec_veri_sol

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
    v_medio[0]  = np.median(abs(Y))
    v_medio[1]  = np.median(abs(F))
    v_medio[2]  = np.median(abs(X))
    v_medio[3]  = np.median(abs(Y))
    v_medio[4]  = np.median(abs(pz))
    v_medio[5]  = np.median(abs(Td))
    v_medio[6]  = np.median(abs(Tz))
    v_medio[7]  = np.median(abs(Tm))
    v_medio[8]  = np.median(abs(Xg))
    v_medio[9]  = np.median(abs(Xv))
    v_medio[10] = np.median(abs(Sp))
    v_medio[11] = np.median(abs(Sg))
    v_medio[12] = np.median(abs(Xp))
    v_medio[13] = np.median(abs(ebp))
    v_medio[14] = np.median(abs(Q))
    v_medio[15] = np.median(abs(M))
    v_medio[16] = np.median(abs(D))
    v_medio[17] = np.median(abs(Z))
    v_medio[18] = np.median(abs(E))
    v_medio[19] = np.median(abs(D))
    v_medio[20] = np.median(abs(CssE))
    v_medio[21] = np.median(abs(CssH))
    v_medio[22] = np.median(abs(AgE))
    v_medio[23] = np.median(abs(AgH))
    v_medio[24] = np.median(abs(Q))
    v_medio[25] = np.median(abs(F.sum(axis=0)))

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
    desviacion[8]  = Xg    - gob.demanda_gobierno_Xg(parametros.mu, pq, Td, Tz, Tm, Sg, AgE, AgH)           # 6. 9
    nvar_end += Xg.size
    Sc = CssE.sum() + CssH.sum() - datos.PssH0.sum()
    desviacion[9]  = Xv    - ainv.demanda_inversion_Xv(parametros.landa, pq, Sp, Sg, Sc, epsilon, datos.Sf0)    # 6.10
    nvar_end += Xv.size
    desviacion[10] = Sp    - ainv.ahorro_hogares_Sp(parametros.ssp, FF, pf, datos.PssH0)                    # 6.11
    nvar_end += Sp.size
    desviacion[11] = Sg    - ainv.ahorro_gobierno_Sg(parametros.ssg, Td, Tz, Tm, AgE, AgH)                  # 6.12
    nvar_end += 1
    if DEM_ESENCIALES:
        desviacion[12] = Xp- deho.demanda_maxima_utilidad_StoneGeary_Xp(parametros.alfa_esen, CON_ESENCIALES, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL, RENTA_FICTICIA) # 6.13
    else:
        desviacion[12] = Xp- deho.demanda_maxima_utilidad_CobbDouglas_Xp(parametros.alfa, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, DEM_ADICIONAL_TIPO, DEM_ADICIONAL, RENTA_FICTICIA) # 6.13
    nvar_end += Xp.size
    desviacion[13] = ebp                                                                                    # 6.16
    nvar_end += ebp.size
    desviacion[14] = Q     - exte.produccion_armington_Q(parametros.gamma, parametros.deltam, parametros.deltad, M, D, parametros.eta) # 6.17
    nvar_end += Q.size
    desviacion[15] = M     - exte.importacion_maxima_utilidad_armington_M(parametros.gamma, parametros.deltam, pq, pm, Q, parametros.eta, datos.taum) # 6.18
    nvar_end += M.size
    desviacion[16] = D     - exte.produccion_maxima_utilidad_armington_D(parametros.gamma, parametros.deltad, pq, pd, Q, parametros.eta) # 6.19
    nvar_end += D.size
    desviacion[17] = Z     - exte.restriccion_producción_bruta_Z(parametros.teta, parametros.xie, parametros.xid, E, D, parametros.phi) # 6.20
    nvar_end += Z.size
    desviacion[18] = E     - exte.produccion_para_exportacion_E(parametros.teta, parametros.xie, pz, pe, Z, parametros.phi, datos.tauz, CssE, AgE, Apz)  # 6.21
    nvar_end += E.size
    desviacion[19] = D     - exte.produccion_para_local_D(parametros.teta, parametros.xid, pz, pd, Z, parametros.phi, datos.tauz, CssE, AgE, Apz) # 6.22
    # no se incrementa nvar_end porque ya se ha calculado la variable D
    desviacion[20]  = CssE - gob.seguridad_social_empresas_CssE(parametros.ctzsse, pf, F, INDICE_F_TRA)         # CssE
    nvar_end += CssE.size
    desviacion[21]  = CssH - gob.seguridad_social_hogares_CssH(parametros.ctzssh, pf, FF, Alp, INDICE_F_TRA)    # CssH
    nvar_end += CssH.size
    desviacion[22]  = AgE  - gob.ayudas_empresas_AgE(parametros.cage, Td, Tz, Tm)                           # AgE
    nvar_end += AgE.size
    desviacion[23]  = AgH  - gob.ayudas_hogares_AgH(parametros.cagh, Td, Tz, Tm, AYD_ADI_DEM)               # AgH
    nvar_end += AgH.size

    desviacion[24]  = Q    - (Xp.sum(axis=0) + Xg + Xv + X.sum(axis=1))                                     # 6.23
    desviacion[25]  = F.sum(axis=0) - (FF.sum(axis=0) + Alp.sum(axis=0))                                    # 6.24

    '''
    if FF_ENDOGENA:
        nvar_end += FF.size
    '''

    if AHORRO_L_PLAZO:
        nvar_end += Alp.size

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
    
def diferencias_cantidades_finales_iniciales(datos, parametros, DECIMALES, ind, dem, h, vec_opt_ini, vec_opt, npre_sol, etq_precios, ebp_ini, res_ecuaciones, rot):
    nfac = len(h)
    nsec = len(ind)
    ndem = len(dem)
    (Apz,Fi,Ei,Mi,Di,Xpi,
        Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,AgE ,AgH ,CssE ,CssH,ebp,Zl,pz,
        Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,AgEr,AgHr,CssEr,CssHr,ebpr
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
    imprime('Consumo intermedio (filas), ventas (columnas). X')
    dX0 = X - datos.X0
    mfun.i_tabla(''  , [] , ind            , dX0.T                 , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['ventas X',]    , dX0.T.sum(axis=0)     , False, DECIMALES)
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
    (Apz,Fi,Ei,Mi,Di,Xpi,
        Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,AgE ,AgH ,CssE ,CssH,ebp,Zl,pz,
        Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,AgEr,AgHr,CssEr,CssHr,ebpr
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
    imprime('Consumo intermedio (filas), ventas (columnas). X')
    dX0 = X * pz - datos.X0 * datos.pZ0
    mfun.i_tabla(''  , [] , ind            , dX0.T                 , False, DECIMALES)
    mfun.i_tabla(''  , [] , ['ventas X',]    , dX0.T.sum(axis=0)     , False, DECIMALES)
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
    res_ecuaciones = prin.sec_ecuaciones(v, False)
    (Apz,Fi,Ei,Mi,Di,Xpi,
        Alp, F, FF, Yp, Yd ,Z ,X ,Xp ,Xg ,Xv ,Q ,M ,Da ,Dt, E ,Td ,Tz ,Tm ,Sp ,Sg ,AgE ,AgH ,CssE ,CssH,ebp,Zl,pz,
        Alpr,Fr,FFr,Ypr,Ydr,Zr,Xr,Xpr,Xgr,Xvr,Qr,Mr,Dar,Dtr,Er,Tdr,Tzr,Tmr,Spr,Sgr,AgEr,AgHr,CssEr,CssHr,ebpr
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

def reconstruye_MCS(datos, parametros, ind, dem, h, inv,css, idt, gov, ext, ayd,
                    indice_f_tra,pf,py,pq,pd,pz,epsilon,pe,pm,X,F,CssE,Tz,M,AgE,FF,Alp,Xp,Sp,CssH,AgH,Td,Xv,PssH,Xg,Sg,Tg,Tm,E,Sf,tolerancia=0.1):
    fil_col_ind = 0
    nfac = len(h)
    nsec = len(ind)
    ndem = len(dem)
    fil_col_fac = fil_col_ind  + nsec
    fil_col_dem = fil_col_fac  + nfac
    fil_col_inv = fil_col_dem  + ndem
    fil_col_css = fil_col_inv  + len(inv)
    fil_col_idt = fil_col_css  + len(css)
    fil_col_gov = fil_col_idt  + len(idt)
    fil_col_ext = fil_col_gov  + len(gov)
    fil_col_ayd = fil_col_ext  + len(ext)
    fil_col_alp = fil_col_ayd  + len(ayd)
    n_fil_cols  = fil_col_alp  + 1

    mcs  = np.zeros((n_fil_cols, n_fil_cols), dtype=np.float64)

    rot = []
    rot.extend(list(ind))
    rot.extend(list(h))
    rot.extend(list(dem))
    rot.extend(list(inv))
    rot.extend(list(css))
    rot.extend(list(idt))
    rot.extend(list(gov))
    rot.extend(list(ext))
    rot.extend(list(ayd))
    rot.append('Alp')

    # rellenamos cada columna 'col' con las filas de menor a mayor con los IMPORTES correspondientes

    #------------------------------------------------------------------------------------------------
    # sectores
    #------------------------------------------------------------------------------------------------
    # consumos intermedios
    col = fil_col_ind
    for i in range(nsec):
        # sector 'i'
        fil = fil_col_ind
        for j in range(nsec):
            # compras al sector 'j' por el sector 'i' al precio de 'j'. X está traspuesta, sus filas son las ventas y las columnas las compras
            mcs[fil,col] = X[j,i] * pz[j]
            fil += 1
        col += 1
    # uso de los factores de producción (incluye Alp)
    imF = F * pf
    col = fil_col_ind
    for i in range(nsec):
        fil = fil_col_fac
        for j in range(nfac):
            mcs[fil,col] = imF[i,j]
            fil += 1
        col += 1
    # cotización de las empresas a la seguridad social
    col = fil_col_ind
    fil = fil_col_css
    for i in range(nsec):
        mcs[fil,col] = CssE[i]
        col += 1
    # impuestos a las empresas
    col = fil_col_ind
    fil = fil_col_idt
    for i in range(nsec):
        mcs[fil,col] = Tz[i]
        col += 1
    # aranceles
    col = fil_col_ind
    fil = fil_col_gov
    for i in range(nsec):
        mcs[fil,col] =  Tm[i]
        col += 1
    # importaciones de las empresas
    col = fil_col_ind
    fil = fil_col_ext
    imM = M * pm
    for i in range(nsec):
        mcs[fil,col] = imM[i]
        col += 1
    #------------------------------------------------------------------------------------------------
    # factores de producción
    #------------------------------------------------------------------------------------------------
    # aportacion de factores de produccion
    imFF = FF * pf
    col = fil_col_fac
    for i in range(nfac):
        fil = fil_col_dem
        for j in range(ndem):
            mcs[fil,col] = imFF[j,i]
            fil += 1
        col += 1
    # ahorro a largo plazo
    imAlp = Alp * pf
    col = fil_col_alp
    fil = fil_col_dem
    for j in range(ndem):
        mcs[fil,col] = imAlp.sum(axis=1)[j]
        fil += 1
    col = fil_col_fac
    fil = fil_col_alp
    for i in range(nfac):
        mcs[fil,col] = imAlp.sum(axis=0)[i]
        col += 1
    #------------------------------------------------------------------------------------------------
    # hogares
    #------------------------------------------------------------------------------------------------
    # consumos de los hogares
    imXp = Xp * pq
    col = fil_col_dem
    for i in range(ndem):
        fil = fil_col_ind
        for j in range(nsec):
            mcs[fil,col] = imXp[i,j]
            fil += 1
        col += 1
    # ahorro + inversión de los hogares
    col = fil_col_dem
    for i in range(ndem):
        fil = fil_col_inv
        mcs[fil,col] = Sp[i]
        col += 1
    # cotización de los hogares a la seguridad social
    col = fil_col_dem
    for i in range(ndem):
        fil = fil_col_css
        mcs[fil,col] = CssH[i]
        col += 1
    # otros impuestos sobre los productos pagados por los hogares
    col = fil_col_dem
    fil = fil_col_idt
    Td_oi = Td * (parametros.taud_oi / parametros.taud)
    for i in range(ndem):
        mcs[fil,col] = Td_oi[i]
        col += 1
    # impuestos directos a los hogares
    col = fil_col_dem
    fil = fil_col_gov
    Td_id = Td * (parametros.taud_id / parametros.taud)
    for i in range(ndem):
        mcs[fil,col] = Td_id[i]
        col += 1
    # Alp
    imAlp = Alp * pf
    col = fil_col_dem
    fil = fil_col_alp
    for i in range(ndem):
        mcs[fil,col] = imAlp.sum(axis=1)[i]
        col += 1
    #------------------------------------------------------------------------------------------------
    # ahorro + inversion
    #------------------------------------------------------------------------------------------------
    imXv = Xv * pq
    col = fil_col_inv
    fil = fil_col_ind
    for i in range(nsec):
        mcs[fil,col] = imXv[i]
        fil += 1
    #------------------------------------------------------------------------------------------------
    # seguridad social
    #------------------------------------------------------------------------------------------------
    # pensiones
    col = fil_col_css
    fil = fil_col_dem
    for i in range(ndem):
        mcs[fil,col] = PssH[i]
        fil += 1
    # ahorro + inversión
    col = fil_col_css
    fil = fil_col_inv
    mcs[fil,col] = CssE.sum() + CssH.sum() - PssH.sum()
    #------------------------------------------------------------------------------------------------
    # impuestos a la producción + otros impuestos sobre los productos pagados por los hogares
    #------------------------------------------------------------------------------------------------
    col = fil_col_idt
    fil = fil_col_gov
    mcs[fil,col] = Tz.sum() + Td_oi.sum() + Tg
    #------------------------------------------------------------------------------------------------
    # sector público (gobierno)
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
    # impuestos
    col = fil_col_gov
    fil = fil_col_idt
    mcs[fil,col] = Tg
    # ayudas
    col = fil_col_gov
    fil = fil_col_ayd
    mcs[fil,col] = AgE.sum() + AgH.sum()
    #------------------------------------------------------------------------------------------------
    # sector exterior
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
    mcs[fil,col] = Sf * epsilon
    #------------------------------------------------------------------------------------------------
    # ayudas
    #------------------------------------------------------------------------------------------------
    # a las empresas
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
    if prin.FF_ENDOGENA and prin.AHORRO_L_PLAZO:
        #------------------------------------------------------------------------------------------------
        # ajustes a los recursos de los sectores por el Alp, como no se tiene el
        # detalle del Alp por sectores, lo obtenemos por el descuadre 'empleos-recursos'
        #------------------------------------------------------------------------------------------------
        recursos = mcs.sum(axis=1) # suma de las filas
        empleos  = mcs.sum(axis=0) # suma de las columnas
        ajustes = (empleos - recursos)[0:nsec]
        col = fil_col_alp
        fil = fil_col_ind
        for i in range(nsec):
            mcs[fil,col] = ajustes[i]
            fil += 1
    #------------------------------------------------------------------------------------------------
    # comprobar cuadre de filas y columnas
    #------------------------------------------------------------------------------------------------
    recursos = mcs.sum(axis=1) # suma de las filas
    empleos  = mcs.sum(axis=0) # suma de las columnas
    # np.all(abs(empleos - recursos) < 0.1) solo será True si todas las comparaciones son ciertas
    if np.all(abs(empleos - recursos) < tolerancia) == False:
        # el criterio no se cumple para algún elemento
        imprime('')
        imprime('ERROR. La MCS no cuadra')
        imprime('                 empleos     recursos   diferencia')
        imprime('------------ ------------ ------------ ------------')
        for i in range(len(empleos)):
            imprime('{:<12} {:12.1f} {:12.1f} {:12.1f}'.format(rot[i], empleos[i], recursos[i], empleos[i] - recursos[i]))
        imprime('------------ ------------ ------------ ------------')
        imprime('')
    return (rot, mcs)

def imprime_MCS(rot, mcs, DECIMALES, titulo='MCS', tolerancia=0.1):
    if DECIMALES == 0:
        ESPA = 8
        subraya = '--------'
    else:
        ESPA = 9
        subraya = '---------'
    imprime(titulo)
    imprime('')
    n = len(rot)
    empleos  = np.zeros(n, dtype=np.float64)
    recursos = np.zeros(n, dtype=np.float64)
    imprime('{:12}'.format(''), False)
    for i in range(n):
        imprime(' {:>{espa}}'.format(rot[i], espa=ESPA), False)
    imprime('{:>{espa}}'.format('Recursos', espa=ESPA))
    imprime('{:12}'.format('------------'), False)
    for i in range(n):
        imprime(' {:>{espa}}'.format(subraya, espa=ESPA), False)
    imprime(' {:>{espa}}'.format(subraya, espa=ESPA))
    for i in range(n):
        # para cada fila
        imprime('{:12}'.format(rot[i]), False)
        for j in range(n):
            # para cada columna de la fila
            v = np.round(mcs[i,j], DECIMALES) 
            imprime(' {:{espa}.{prec}f}'.format(v, espa=ESPA, prec=DECIMALES), False)
            recursos[i] += v    # suma de la fila 'i'
            empleos[j]  += v    # suma de la columna 'j'
        imprime(' {:{espa}.{prec}f}'.format(recursos[i], espa=ESPA, prec=DECIMALES))
    imprime('{:>{espa}}'.format('------------', espa=ESPA), False)
    for i in range(n):
        imprime(' {:>{espa}}'.format(subraya, espa=ESPA), False)
    imprime(' {:>{espa}}'.format(subraya, espa=ESPA))
    imprime('{:12}'.format('Empleos'), False)
    for i in range(n):
        imprime(' {:{espa}.{prec}f}'.format(empleos[i], espa=ESPA, prec=DECIMALES), False)
    imprime('')
    imprime('')
    if np.all(abs(empleos - recursos) < tolerancia) == False:
        # el criterio no se cumple para algún elemento
        if np.all(abs(mcs.sum(axis=0) - mcs.sum(axis=1)) < tolerancia) == True:
            # el criterio se cumple para todos los elementos
            imprime('Las diferencias entre empleos y recursos se deben exclusivamente a los redondeos de impresión')
        else:
            imprime('ERROR. La MCS no cuadra. Imprimir')
        imprime('')
