import ctypes as ct
import numpy as np
import MEGA as prin

# es preciso que prin.'nfac, ndem y nsec' tengan los valores correctos cuando 'prin'
# importa este módulo para que la definición de las 'class' sea correcta

nfac  = prin.nfac
ndem  = prin.ndem
nsec  = prin.nsec

nds   = ndem * nsec
nsf   = nsec * nfac
ndf   = ndem * nfac
nsec2 = nsec * nsec

class OPCIONES(ct.Structure):
    _fields_ = (
        ('OR_PRE_EXCLUIDO'   , ct.c_int),
        ('PRECIO_F_EXCLUIDO' , ct.c_double),
        ('VALOR_F_TRA'       , ct.c_double),
        ('ALFA_PHILLIPS'     , ct.c_double),
        ('GE_INCLUYE_XP'     , ct.c_bool),
        ('GE_INCLUYE_AgH'    , ct.c_bool),
        ('GE_IMPUESTOS_AgH'  , ct.c_bool),
        ('FF_ENDOGENA'       , ct.c_bool),
        ('ALP_FACTOR'        , ct.c_double),
        ('INDICE_F_TRA'      , ct.c_int),
        ('UTILIDAD_DEMANDA'  , ct.c_int),
        ('DEM_ESENCIALES'    , ct.c_bool),
        ('DEM_ADICIONAL_TIPO', ct.c_int),
        ('DEM_ADICIONAL'     ,(ct.c_double * nds )),
        ('CON_ESENCIALES'    ,(ct.c_double * nds )),
        ('AYD_ADICIONAL'     ,(ct.c_double * nds )),
        ('RENTA_FICTICIA'    , ct.c_bool),
        ('MODO_PSEUDOIMPTOS' , ct.c_int),
        ('OPT_DESVIOS'       , ct.c_int),
        ('EQ_BAL_PAGOS'      , ct.c_bool),
    )

class DATOS(ct.Structure):
    _fields_ = (
        ('pf',      (ct.c_double * nfac)),
        ('py',      (ct.c_double * nsec)),
        ('pq',      (ct.c_double * nsec)),
        ('pd',      (ct.c_double * nsec)),
        ('pe',      (ct.c_double * nsec)),
        ('pm',      (ct.c_double * nsec)),
        ('epsilon',  ct.c_double),
        ('F',       (ct.c_double * nsf )),
        ('E',       (ct.c_double * nsec)),
        ('M',       (ct.c_double * nsec)),
        ('D',       (ct.c_double * nsec)),
        ('FF0',     (ct.c_double * ndf )),
        ('Alp0',    (ct.c_double * ndf )),
        ('PssH0',   (ct.c_double * ndem)),
        ('tauz',    (ct.c_double * nsec)),
        ('taum',    (ct.c_double * nsec)),
        ('Tg0',      ct.c_double),
        ('Ti0',      ct.c_double),
        ('Te0',      ct.c_double),
        ('Sf0',      ct.c_double),
        ('Fue',      ct.c_double),
        ('PobAct',   ct.c_double),
        ('Z',       (ct.c_double * nsec)),
        ('Ajc',     (ct.c_double * nsec)),
        ('Aji',     (ct.c_double * nsec)),
    )

class PARAMETROS(ct.Structure):
    _fields_ = (
        ('ax',        (ct.c_double * nsec2)),
        ('ay',        (ct.c_double * nsec )),
        ('beta',      (ct.c_double * nsf  )),
        ('b',         (ct.c_double * nsec )),
        ('teta',      (ct.c_double * nsec )),
        ('xie',       (ct.c_double * nsec )),
        ('xid',       (ct.c_double * nsec )),
        ('phi',       (ct.c_double * nsec )),
        ('taud',      (ct.c_double * ndem )),
        ('cage',      (ct.c_double * nsec )),
        ('cagh',      (ct.c_double * ndem )),
        ('ssp',       (ct.c_double * ndem )),
        ('ctzsse',    (ct.c_double * nsec )),
        ('ctzssh',    (ct.c_double * ndem )),
        ('ctzssez',   (ct.c_double * nsec )),
        ('ctzagez',   (ct.c_double * nsec )),
        ('ssg',        ct.c_double),
        ('mu',        (ct.c_double * nsec )),
        ('landa',     (ct.c_double * nsec )),
        ('alfa',      (ct.c_double * nds )),
        ('alfa_esen', (ct.c_double * nds )),
        ('eta_ces',   (ct.c_double * ndem)),
        ('alfa_ces',  (ct.c_double * nds )),
        ('gamma',     (ct.c_double * nsec )),
        ('deltam',    (ct.c_double * nsec )),
        ('deltad',    (ct.c_double * nsec )),
        ('eta',       (ct.c_double * nsec )),
        ('tai',        ct.c_double),
    )

def abre_dll(fichero):
    libc = ct.WinDLL(fichero)
    return libc

def envia_opciones(libc):
    opciones = OPCIONES(
            ct.c_int(prin.OR_PRE_EXCLUIDO),
            ct.c_double(prin.PRECIO_F_EXCLUIDO),
            ct.c_double(prin.VALOR_F_TRA),
            ct.c_double(prin.ALFA_PHILLIPS),
            ct.c_bool(prin.GE_INCLUYE_XP),
            ct.c_bool(prin.GE_INCLUYE_AgH),
            ct.c_bool(prin.GE_IMPUESTOS_AgH),
            ct.c_bool(prin.FF_ENDOGENA),
            ct.c_double(prin.ALP_FACTOR),
            ct.c_int(prin.INDICE_F_TRA),
            ct.c_int(prin.UTILIDAD_DEMANDA),
            ct.c_bool(prin.DEM_ESENCIALES),
            ct.c_int(prin.DEM_ADICIONAL_TIPO),
            (ct.c_double * nds) (*(prin.DEM_ADICIONAL .flatten())),
            (ct.c_double * nds) (*(prin.CON_ESENCIALES.flatten())),
            (ct.c_double * nds) (*(prin.AYD_ADICIONAL .flatten())),
            ct.c_bool(prin.RENTA_FICTICIA),
            ct.c_int(prin.MODO_PSEUDOIMPTOS),
            ct.c_int(prin.OPT_DESVIOS),
            ct.c_bool(prin.EQ_BAL_PAGOS),
    )
    libc.recibe_opciones.argtypes = [OPCIONES]
    libc.recibe_opciones.restype = OPCIONES
    res = libc.recibe_opciones(opciones)
    return 

def envia_datos(libc, d):
    datos = DATOS(
        (ct.c_double * nfac) (*(d.pF0  .flatten())),
        (ct.c_double * nsec) (*(d.pY0  .flatten())),
        (ct.c_double * nsec) (*(d.pQ0  .flatten())),
        (ct.c_double * nsec) (*(d.pD0  .flatten())),
        (ct.c_double * nsec) (*(d.pWm  .flatten())),
        (ct.c_double * nsec) (*(d.pWe  .flatten())),
        ct.c_double(d.epsilon0),
        (ct.c_double * nsf ) (*(d.F0   .flatten())),
        (ct.c_double * nsec) (*(d.E0   .flatten())),
        (ct.c_double * nsec) (*(d.M0   .flatten())),
        (ct.c_double * nsec) (*(d.D0   .flatten())),
        (ct.c_double * ndf ) (*(d.FF0  .flatten())),
        (ct.c_double * ndf ) (*(d.Alp0 .flatten())),
        (ct.c_double * ndem) (*(d.PssH0.flatten())),
        (ct.c_double * nsec) (*(d.tauz. flatten())),
        (ct.c_double * nsec) (*(d.taum. flatten())),
        ct.c_double(d.Tg0),
        ct.c_double(d.Ti0),
        ct.c_double(d.Te0),
        ct.c_double(d.Sf0),
        ct.c_double(prin.FDO_UE),
        ct.c_double(d.PobAct),
        (ct.c_double * nsec) (*(d.Z0  .flatten())),
        (ct.c_double * nsec) (*(d.Ajc0.flatten())),
        (ct.c_double * nsec) (*(d.Aji0.flatten())),
    )
    libc.recibe_datos.argtypes = [DATOS]
    libc.recibe_datos.restype = DATOS
    res = libc.recibe_datos(datos)
    return 

def envia_parametros(libc, p):
    parametros = PARAMETROS(
        (ct.c_double * nsec2) (*p.ax       .flatten()),
        (ct.c_double * nsec ) (*p.ay       .flatten()),
        (ct.c_double * nsf  ) (*p.beta     .flatten()),
        (ct.c_double * nsec ) (*p.b        .flatten()),
        (ct.c_double * nsec ) (*p.teta     .flatten()),
        (ct.c_double * nsec ) (*p.xie      .flatten()),
        (ct.c_double * nsec ) (*p.xid      .flatten()),
        (ct.c_double * nsec ) (*p.phi      .flatten()),
        (ct.c_double * ndem ) (*p.taud     .flatten()),
        (ct.c_double * nsec ) (*p.cage     .flatten()),
        (ct.c_double * ndem ) (*p.cagh     .flatten()),
        (ct.c_double * ndem ) (*p.ssp      .flatten()),
        (ct.c_double * nsec ) (*p.ctzsse   .flatten()),
        (ct.c_double * ndem ) (*p.ctzssh   .flatten()),
        (ct.c_double * nsec ) (*p.ctzssez  .flatten()),
        (ct.c_double * nsec ) (*p.ctzagez  .flatten()),
        ct.c_double(p.ssg),
        (ct.c_double * nsec ) (*p.mu       .flatten()),
        (ct.c_double * nsec ) (*p.landa    .flatten()),
        (ct.c_double * nds  ) (*p.alfa     .flatten()),
        (ct.c_double * nds  ) (*p.alfa_esen.flatten()),
        (ct.c_double * ndem ) (*p.eta_ces  .flatten()),
        (ct.c_double * nds  ) (*p.alfa_ces .flatten()),
        (ct.c_double * nsec ) (*p.gamma    .flatten()),
        (ct.c_double * nsec ) (*p.deltam   .flatten()),
        (ct.c_double * nsec ) (*p.deltad   .flatten()),
        (ct.c_double * nsec ) (*p.eta      .flatten()),
        ct.c_double(p.tai),
    )
    libc.recibe_parametros.argtypes = [PARAMETROS]
    libc.recibe_parametros.restype = PARAMETROS
    res = libc.recibe_parametros(parametros)
    return 
    '''
    prin.imprime('PARAMETROS')
    prin.imprime('{',False)
    for i in range(nsec2):
        prin.imprime(('{},'.format(p.ax.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(p.ay.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsf):
        prin.imprime(('{},'.format(p.beta.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(p.b.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(p.teta.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(p.xie.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(p.xid.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(p.phi.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(ndem):
        prin.imprime(('{},'.format(p.taud.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(p.cage.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(ndem):
        prin.imprime(('{},'.format(p.cagh.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(ndem):
        prin.imprime(('{},'.format(p.ssp.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(p.ctzsse.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(ndem):
        prin.imprime(('{},'.format(p.ctzssh.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(p.ctzssez.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(p.ctzagez.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{},'.format(p.ssg))
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(p.mu.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(p.landa.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nds):
        prin.imprime(('{},'.format(p.alfa.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nds):
        prin.imprime(('{},'.format(p.alfa_esen.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(ndem):
        prin.imprime(('{},'.format(p.eta_ces.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nds):
        prin.imprime(('{},'.format(p.alfa_ces.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(p.gamma.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(p.deltam.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(p.deltad.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(p.eta.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('')
    '''

def merito_s(libc, vec_opt):
    vo = vec_opt.ctypes.data_as(ct.POINTER(ct.c_double))
    if prin.DESV_RELATIVA == 1:
        libc.merito_s_relativa.argtypes = [ct.POINTER(ct.c_double)]
        libc.merito_s_relativa.restype = ct.c_double
        return libc.merito_s_relativa(vo)
    else:
        libc.merito_s.argtypes = [ct.POINTER(ct.c_double)]
        libc.merito_s.restype = ct.c_double
        return libc.merito_s(vo)

def merito_sol(libc, vec_opt):
    vo = vec_opt.ctypes.data_as(ct.POINTER(ct.c_double))
    if prin.DESV_RELATIVA == 1:
        libc.merito_sol_relativa.argtypes = [ct.POINTER(ct.c_double)]
        libc.merito_sol_relativa.restype = ct.POINTER(ct.c_double)
        r_sol = libc.merito_sol_relativa(vo)
    else:
        libc.merito_sol.argtypes = [ct.POINTER(ct.c_double)]
        libc.merito_sol.restype = ct.POINTER(ct.c_double)
        r_sol = libc.merito_sol(vo)
    return r_sol[4]
    '''
    NFAC = nfac
    NDEM = ndem
    NSEC = nsec
    LVAR = 1+1+1+1+1+NFAC+NSEC+NSEC+NSEC+1+1+NSEC*NFAC+NSEC+NSEC+NSEC+NDEM*NSEC+NSEC+NSEC+NSEC+NSEC+NSEC+NSEC+NSEC+NSEC+NDEM+NSEC+NSEC+NDEM+NSEC+NDEM+NSEC+NDEM+1+1+1+NDEM*NSEC+NDEM*NFAC+NDEM*NFAC+NSEC*NSEC
    if prin.GE_INCLUYE_XP == False:
        LVAR -= NDEM * NSEC
    r_res = r_sol[0]
    r_datos = int(r_sol[1])
    if r_datos != LVAR:
        print('Error número de datos no coincide {} {}'.format(LVAR, r_datos))
    print(r_res)
    print(r_datos)
    print(r_sol[2])
    print(r_sol[3])
    print(r_sol[4])
    N = 5;
    for i in range(NFAC):
        prin.imprime('{:10.1f} '.format(r_sol[N]),False)
        N += 1
    prin.imprime('')
    for k in range(3):
        for i in range(NSEC):
            prin.imprime('{:10.1f} '.format(r_sol[N]),False)
            N += 1
        prin.imprime('')
    prin.imprime(r_sol[N])
    N += 1
    prin.imprime(r_sol[N])
    N += 1
    for k in range(NFAC):
        for i in range(NSEC):
            prin.imprime('{:10.1f} '.format(r_sol[N]),False)
            N += 1
        prin.imprime('')
    for k in range(3):
        for i in range(NSEC):
            prin.imprime('{:10.1f} '.format(r_sol[N]),False)
            N += 1
        prin.imprime('')

    print(r_sol[LVAR-2])
    print(r_sol[LVAR-1])
    return r_sol
    '''

def soluciona(libc, par, cotas_inf, cotas_sup, vec, extendida, senda_salidas, caso, fi_lee_caso):
    libc.soluciona.argtypes = (ct.POINTER(ct.c_double), ct.POINTER(ct.c_double), ct.POINTER(ct.c_double), ct.POINTER(ct.c_double), ct.c_int, ct.c_char_p, ct.c_char_p, ct.c_char_p)
    libc.soluciona.restype = ct.POINTER(ct.c_double)
    v1 = np.array(par).ctypes.data_as(ct.POINTER(ct.c_double))
    v2 = np.array(cotas_inf).ctypes.data_as(ct.POINTER(ct.c_double))
    v3 = np.array(cotas_sup).ctypes.data_as(ct.POINTER(ct.c_double))
    v4 = vec.ctypes.data_as(ct.POINTER(ct.c_double))
    v5 = ct.c_char_p(senda_salidas.encode('utf-8'))
    v6 = ct.c_char_p(caso.encode('utf-8'))
    v7 = ct.c_char_p(fi_lee_caso.encode('utf-8'))
    res = libc.soluciona(v1, v2, v3, v4, extendida, v5, v6, v7)
    return res

