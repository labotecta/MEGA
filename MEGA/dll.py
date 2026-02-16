import ctypes as ct
import MEGA as prin
import numpy as np

nfac  = 2
ndem  = 2
nsec  = 6
nds   = ndem * nsec
nsf   = nsec * nfac
ndf   = ndem * nfac
nsec2 = nsec * nsec

class OPCIONES(ct.Structure):
    _fields_ = (
        ('OR_PRE_EXCLUIDO',  ct.c_int),
        ('PRECIO_F_EXCLUIDO',ct.c_double),
        ('VALOR_F_TRA',        ct.c_double),
        ('ALFA_PHILLIPS',      ct.c_double),
        ('GE_INCLUYE_XP',      ct.c_bool),
        ('FF_ENDOGENA',        ct.c_bool),
        ('ALP_FACTOR',         ct.c_double),
        ('INDICE_F_TRA',       ct.c_int),
        ('UTILIDAD_DEMANDA',   ct.c_int),
        ('DEM_ESENCIALES',     ct.c_bool),
        ('DEM_ADICIONAL_TIPO', ct.c_int),
        ('DEM_ADICIONAL',     (ct.c_double * nds )),
        ('CON_ESENCIALES',    (ct.c_double * nds )),
        ('AYD_ADICIONAL',     (ct.c_double * nds )),
        ('RENTA_FICTICIA',     ct.c_bool),
        ('MODO_PSEUDOIMPTOS',  ct.c_int),
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
        ('Sf0',      ct.c_double),
        ('PobAct',   ct.c_double),
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
    )

class SOLUCION(ct.Structure):
    _fields_ = (
        ('pf',     (ct.c_double * nfac)),
        ('py',     (ct.c_double * nsec)),
        ('pq',     (ct.c_double * nsec)),
        ('pd',     (ct.c_double * nsec)),
        ('pz',     (ct.c_double * nsec)),
        ('epsilon', ct.c_double),
        ('pe',     (ct.c_double * nsec)),
        ('pm',     (ct.c_double * nsec)),
        ('Apz',    ct.c_double),
        ('E',      (ct.c_double * nsec)),
        ('M',      (ct.c_double * nsec)),
        ('D',      (ct.c_double * nsec)),
        ('Yp',     (ct.c_double * nsec)),
        ('Z',      (ct.c_double * nsec)),
        ('Xg',     (ct.c_double * nsec)),
        ('Xv',     (ct.c_double * nsec)),
        ('Q',      (ct.c_double * nsec)),
        ('Td',     (ct.c_double * ndem)),
        ('Tz',     (ct.c_double * nsec)),
        ('Tm',     (ct.c_double * nsec)),
        ('Sp',     (ct.c_double * ndem)),
        ('AgE',    (ct.c_double * nsec)),
        ('AgH',    (ct.c_double * ndem)),
        ('CssE',   (ct.c_double * nsec)),
        ('CssH',   (ct.c_double * ndem)),
        ('Sg',      ct.c_double),
        ('Sc',      ct.c_double),
        ('ebp',     ct.c_double),
        ('Xp',     (ct.c_double * nds)),
        ('F',      (ct.c_double * nsf)),
        ('FF',     (ct.c_double * ndf)),
        ('Alp',    (ct.c_double * ndf)),
        ('X',      (ct.c_double * nsec2)),
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
    )
    libc.recibe_opciones.argtypes = [OPCIONES]
    libc.recibe_opciones.restype = OPCIONES
    libc.recibe_opciones(opciones)
    '''    
    prin.imprime('OPCIONES')
    prin.imprime('{},'.format(prin.OR_PRE_EXCLUIDO))
    prin.imprime('{},'.format(prin.PRECIO_F_EXCLUIDO))
    prin.imprime('{},'.format(prin.VALOR_F_TRA))
    prin.imprime('{},'.format(prin.ALFA_PHILLIPS))
    prin.imprime('{},'.format(prin.GE_INCLUYE_XP))
    prin.imprime('{},'.format(prin.FF_ENDOGENA))
    prin.imprime('{},'.format(prin.ALP_FACTOR))
    prin.imprime('{},'.format(prin.INDICE_F_TRA))
    prin.imprime('{},'.format(prin.UTILIDAD_DEMANDA))
    prin.imprime('{},'.format(prin.DEM_ESENCIALES))
    prin.imprime('{},'.format(prin.DEM_ADICIONAL_TIPO))
    prin.imprime('{',False)
    for i in range(nds):
        prin.imprime(('{},'.format(prin.DEM_ADICIONAL.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nds):
        prin.imprime(('{},'.format(prin.CON_ESENCIALES.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nds):
        prin.imprime(('{},'.format(prin.AYD_ADICIONAL.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{},'.format(prin.RENTA_FICTICIA))
    prin.imprime('{}'.format(prin.MODO_PSEUDOIMPTOS))
    prin.imprime('')
    '''

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
        ct.c_double(d.Sf0),
        ct.c_double(d.PobAct),
    )
    libc.recibe_datos.argtypes = [DATOS]
    libc.recibe_datos.restype = DATOS
    libc.recibe_datos(datos)
    '''
    prin.imprime('DATOS')
    prin.imprime('{',False)
    for i in range(nfac):
        prin.imprime(('{},'.format(d.pF0.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(d.pY0.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(d.pQ0.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(d.D0.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(d.pWm.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(d.pWe.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{},'.format(d.epsilon))
    prin.imprime('{',False)
    for i in range(nsf):
        prin.imprime(('{},'.format(d.F0.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(d.E0.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(d.M0.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(d.D0.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(ndf):
        prin.imprime(('{},'.format(d.FF0.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(ndf):
        prin.imprime(('{},'.format(d.Alp0.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(ndem):
        prin.imprime(('{},'.format(d.PssH0.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(d.tauz.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{',False)
    for i in range(nsec):
        prin.imprime(('{},'.format(d.taum.flatten()[i])),False)
    prin.imprime('},')
    prin.imprime('{},'.format(d.Sf0))
    prin.imprime('{},'.format(d.PobAct))
    prin.imprime('')
    '''

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
    )
    libc.recibe_parametros.argtypes = [PARAMETROS]
    libc.recibe_parametros.restype = PARAMETROS
    libc.recibe_parametros(parametros)
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

def merito(libc, vec_opt):
    libc.merito_s.argtypes = [ct.POINTER(ct.c_double)]
    libc.merito_s.restype = ct.c_double
    vo = vec_opt.ctypes.data_as(ct.POINTER(ct.c_double))
    '''
    prin.imprime('{',False)
    for i in range(len(vec_opt)):
        prin.imprime(('{},'.format(vec_opt[i])), False)
    prin.imprime('},')
    prin.imprime('')
    '''
    return libc.merito_s(vo)

def vector_prueba(libc):
    libc.vector_prueba.argtypes = []
    libc.vector_prueba.restype = ct.POINTER(ct.c_double)
    res = libc.vector_prueba()
    return res

def solucion(libc):
    libc.solucion.argtypes = []
    libc.solucion.restype = ct.POINTER(ct.c_double)
    return libc.solucion()

def soluciona(libc, par, cotas_inf, cotas_sup, vec, extendida):
    libc.soluciona.argtypes = (ct.POINTER(ct.c_double), ct.POINTER(ct.c_double), ct.POINTER(ct.c_double), ct.POINTER(ct.c_double), ct.c_int)
    libc.soluciona.restype = ct.POINTER(ct.c_double)
    v1 = np.array(par).ctypes.data_as(ct.POINTER(ct.c_double))
    v2 = np.array(cotas_inf).ctypes.data_as(ct.POINTER(ct.c_double))
    v3 = np.array(cotas_sup).ctypes.data_as(ct.POINTER(ct.c_double))
    v4 = vec.ctypes.data_as(ct.POINTER(ct.c_double))
    res = libc.soluciona(v1, v2, v3, v4, extendida)
    '''
    for i in range(int(res[1])):
        print(i, res[i])
    print()
    '''
    return res

