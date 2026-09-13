import os
import sys
import glob
import math
import numpy as np
import statsmodels.api as sm
from scipy import stats
from matplotlib import pyplot as plt
from pandas import DataFrame

NMCS = 6
MENOS_INI = 0
MENOS_FIN = 0
SUFIJO = '_0_42_dll_sol_'

if   NMCS == 4:
    # sin Alp
    SENDAS = [
        'C:/MEGA/Salidas/Mcs4/Phillips/',
        'C:/MEGA/Salidas/Mcs4/',
    ]
    # ID, N_DESVIOS, DESDE, HASTA
    IDS = [
        [
            ['120', 183, -1, -1],
            ['121', 187, -1, -1],
            ['122', 183, -1, -1],
            ['123', 187, -1, -1],
            ['125', 183, -1, -1],
            ['130', 183, -1, -1],
            ['131', 187, -1, -1],
        ],
        [
            ['101', 185, -1, -1],
            ['102', 185, -1, -1],
            ['103', 187, -1, -1],
            ['104', 183, -1, -1],
        ],
    ]
    NPOB = '2010'
    NFAC = 2
    NDEM = 2
    NSEC = 6
    N_VAR_CAL     = 165
    #             NFAC   pY pQ pD   epsilon  Apz
    #             NFAC + 3 * NSEC  +   1   +  1
    PRECIOS       = 2 + 3 * 6 + 2      # incluidos epsilon y Apz
    RESTO_SOL     = 51 - (PRECIOS - 1)     # NVEC - (PRECIOS - 1) los precios incluyen los dos factores
    V_C_UNICO     = 3 * 6      # 3 * NSEC  ( pz pe pm )
    LIN_INI_Ppase = 1 + PRECIOS + RESTO_SOL + V_C_UNICO + 1     # 347 = la siguiente a: primera línea + ...
    LIN_INI_Spase = LIN_INI_Ppase + N_VAR_CAL # 1887 = LIN_PPASE + 1540 (variables calculadas del modelo)
    ULT_LINEA     = LIN_INI_Spase + N_VAR_CAL - 1
    TOL_PRECIOS   = 0.00001
    TOL_VARIABLES = 0.001
    p_VAB = 236
    p_Ti  = 400
    p_Tz  = 310
    p_Tm  = 316
    p_Td  = 308
    p_cotizacion_SS = 332
    p_suma_Z = 284
    p_suma_Q = 302
elif NMCS == 5:
    SENDAS = [
        'C:/MEGA/Salidas/Mcs5/Phillips/',
        'C:/MEGA/Salidas/Mcs5/',
    ]
    IDS = [
        [
            ['310', 5445, -1, -1],
            ['311', 5439, -1, -1],
            ['315', 5439, -1, -1],
        ],
        [
            ['300', 5441,-1, -1],
        ],
    ]
    NPOB = '16020'
    NFAC = 2
    NDEM = 3
    NSEC = 63
    N_VAR_CAL     = 5195
    #             NFAC   pY pQ pD   epsilon  Apz
    #             NFAC + 3 * NSEC  +   1   +  1
    PRECIOS       = 193     # incluidos epsilon y Apz
    RESTO_SOL     = 313     # NVEC - (PRECIOS - 1) los precios incluyen los dos factores
    V_C_UNICO     = 189     # 3 * NSEC  ( pz pe pm )
    LIN_INI_Ppase = 699
    LIN_INI_Spase = 5894
    ULT_LINEA     = 11088
    TOL_PRECIOS   = 0.0001
    TOL_VARIABLES = 1.0
    p_VAB = 5893
    p_Ti  = 11087
    p_Tz  = 6652
    p_Tm  = 6715
    p_Td  = 6649
    p_cotizacion_SS = 6847
    p_suma_Z = 6397
    p_suma_Q = 6586
elif NMCS == 6:
    SENDAS = [
        'C:/MEGA/Salidas/Mcs6/Phillips/FUE/',
        'C:/MEGA/Salidas/Mcs6/Phillips/',
        'C:/MEGA/Salidas/Mcs6/',
    ]
    IDS = [
        [
            ['1001',1662, -1, -1],
            ['3001',1662, -1, -1],
        ],
        [
            ['210', 1658, -1, -1],
            ['211', 1662, -1, -1],
            ['212', 1658, -1, -1],
            ['213', 1662, -1, -1],
            ['215', 1658, -1, -1],
            ['220', 1658, -1, -1],
            ['221', 1662, -1, -1],
            ['230', 1658, -1, -1],
        ],
        [
            ['201', 1660, -1, -1],
            ['202', 1660, -1, -1],
            ['205', 1658, -1, -1],
            ['2050',1658, -1, -1],
            ['206', 1662, -1, -1]
        ],
    ]
    NPOB = '5400'
    NFAC = 2
    NDEM = 2
    NSEC = 31
    N_VAR_CAL     = 1540    # variables calculadas del modelo
    #             NFAC   pY pQ pD   epsilon  Apz
    #             NFAC + 3 * NSEC  +   1   +  1
    PRECIOS       = 97      # incluidos epsilon y Apz, ocupan fila_fin la línea 98 del fichero, inclusive
    RESTO_SOL     = 155     # NVEC - (PRECIOS - 1) el - 1 es porque los precios incluyen los dos factores
    V_C_UNICO     = 93      # 3 * NSEC  ( pz pe pm )

    # 347 = 
    #   +   1 primera línea
    #   +  97 precios +
    #   + 155 resto solución +
    #   +   1 el fichero contiene los dos factores y hemos quitado 1 a RESTO_SOL 
    #   +  93 V_C_UNICO
    LIN_INI_Ppase = 1 + PRECIOS + RESTO_SOL + V_C_UNICO + 1

    # 1887 = LIN_PPASE + 1540 variables calculadas del modelo
    LIN_INI_Spase = LIN_INI_Ppase + N_VAR_CAL
    
    # 3426
    ULT_LINEA     = LIN_INI_Spase + N_VAR_CAL - 1   
    
    TOL_PRECIOS   = 0.0001
    TOL_VARIABLES = 0.01
    p_VAB = 1886
    p_Ti  = 3425
    p_Tz  = 2260
    p_Tm  = 2291
    p_Td  = 2258
    p_cotizacion_SS = 2357
    p_suma_Z = 2134
    p_suma_Q = 2227
elif NMCS == 7:
    SENDAS = [
        'C:/MEGA/Salidas/Mcs6/Phillips/FUE/',
    ]
    IDS = [
        [
            ['3002',1664, -1, -1],
            ['3022',1664, -1, -1],
        ],
    ]
    NPOB = '5400'
    NFAC = 2
    NDEM = 2
    NSEC = 31
    N_VAR_CAL     = 1540    # variables calculadas del modelo
    #             NFAC   pY pQ pD   epsilon  Apz
    #             NFAC + 3 * NSEC  +   1   +  1
    PRECIOS       = 97      # incluidos epsilon y Apz, ocupan fila_fin la línea 98 del fichero, inclusive
    RESTO_SOL     = 157     # NVEC - (PRECIOS - 1) el - 1 es porque los precios incluyen los dos factores
    V_C_UNICO     = 93      # 3 * NSEC  ( pz pe pm )

    # 347 = 
    #   +   1 primera línea
    #   +  97 precios +
    #   + 155 resto solución +
    #   +   1 el fichero contiene los dos factores y hemos quitado 1 a RESTO_SOL 
    #   +  93 V_C_UNICO
    LIN_INI_Ppase = 1 + PRECIOS + RESTO_SOL + V_C_UNICO + 1

    # 1887 = LIN_PPASE + 1540 variables calculadas del modelo
    LIN_INI_Spase = LIN_INI_Ppase + N_VAR_CAL
    
    # 3426
    ULT_LINEA     = LIN_INI_Spase + N_VAR_CAL - 1   
    
    TOL_PRECIOS   = 0.0001
    TOL_VARIABLES = 0.01
    p_VAB = 1888
    p_Ti  = 3427
    p_Tz  = 2262
    p_Tm  = 2293
    p_Td  = 2260
    p_cotizacion_SS = 2359
    p_suma_Z = 2136
    p_suma_Q = 2229
else:
    print('número de MCS (NMCS) incorrecto')
    sys.exit()

titulo = []
for ids in IDS:
    for eids,n, d, h in ids:
        titulo.append(eids)
titulo_s = ['VAB', 'impuestos', 'cotización SS', 'Suma Z', 'Suma Q']

g_log_ep = []
g_log_ev = []
g_log_m  = []
g_log_d  = []
gr_m_ep  = []
gr_m_ev  = []
gr_m_d   = []
gr_ep_ev = []

COL_ADD_INI  = 3    # columnas iniciales al principio: 'N','variable' y 'indice'
'''
'FIL_ADD_INI' filas adicionales al principio:

 0 'Generaciones'
 1 'Prec.max.err'
 2 'Err.max.prec'
 3 'Vari.max.err'
 4 'Err.max.vari'
 5 'Error maximo'
 6 'Vari.max.dif'
 7 'Dif.max.pases'
 8 'Suma diferencias'
 9 'suma error'
10 log10(Error maximo)
11 log10(Dif.max.pases)
12 VAB
13 impuestos
14 cotizacion SS
15 suma Z
16 suma Q
'''
rot_filas = [
    'Generaciones',
    'Prec.max.err',
    'Err.max.prec',
    'Vari.max.err',
    'Err.max.vari',
    'Error maximo',
    'Vari.max.dif',
    'Dif.max.pases',
    'Suma diferencias',
    'Suma error',
    'log10(Error maximo)',
    'log10(Dif.max.pases)',
    'VAB',
    'impuestos',
    'cotizacion SS',
    'suma Z',
    'suma Q'
]
FIL_ADD_INI = len(rot_filas)

def imprime(texto, rc=True):
    if type(texto) is not str:
        texto = str(texto)
    if rc:
        print(texto)
        with open(FICHERO_LOG, "a", encoding="utf-8") as log: log.write(texto + '\n')
    else:
        print(texto, end='')
        with open(FICHERO_LOG, "a", encoding="utf-8") as log: log.write(texto)

def GraficoEvolucion(x, log_ep, log_ev, log_d, log_m, corte_x_ep, corte_x_ev, corte_x_d, corte_x_m, senda, nombre):
    fig = plt.figure(dpi=300, figsize=(15.0,7.0), clear=True)
    plt.title('Evolución del máximo error y de la máxima diferencia entre pases, de una variable', fontsize=20)
    nm1     = len(x) - 1
    ymin_ev = min(log_ev)
    ymax_ev = max(log_ev)
    ymin_d  = min(log_d)
    ymax_d  = max(log_d)
    ymin    = min(ymin_ev,ymin_d)
    ymax    = max(ymax_ev,ymax_d)
    ymin_ep = min(log_ep)
    ymax_ep = max(log_ep)
    ymin    = min(ymin,ymin_ep)
    ymax    = max(ymax,ymax_ep)
    ymin_m  = min(log_m)
    ymax_m  = max(log_m)
    ymin    = min(ymin,ymin_m)
    ymax    = max(ymax,ymax_m)

    tolp    = math.log10(TOL_PRECIOS)
    tolv    = math.log10(TOL_VARIABLES)

    plt.xlabel('generaciones. Tolerancia: precios={} [log {:.1f}]; variables={} [log {:.1f}]'.format(TOL_PRECIOS,tolp,TOL_VARIABLES,tolv), fontsize=18)
    plt.ylabel('logaritmo base 10', fontsize=18)

    plt.plot(x, log_ep, label = 'error pre'      , linewidth=2                    , color ='blue')
    plt.vlines(x=corte_x_ep, ymin=ymin, ymax=ymax, linewidth=1, linestyle='dotted', colors='blue')
    plt.hlines(y=tolp, xmin=x[0], xmax=x[nm1]    , linewidth=1, linestyle='dotted', colors='blue')
    plt.text(corte_x_ep, ymax * 0.55,'p:{}'.format(int(corte_x_ep)), fontsize=16  , color ='blue')
    plt.text(x[0], tolp * 0.96,'p:{:.1f}'.format(tolp)             , fontsize=16  , color ='blue')
    plt.plot(corte_x_ep, tolp, 'bo') 

    plt.plot(x, log_ev, label = 'error var'      , linewidth=2                    , color ='red')
    plt.vlines(x=corte_x_ev, ymin=ymin, ymax=ymax, linewidth=1, linestyle='dotted', colors='red')
    plt.hlines(y=tolv, xmin=x[0], xmax=x[nm1]    , linewidth=1, linestyle='dotted', colors='red')
    plt.text(corte_x_ev,ymax * 0.96,'v:{}'.format(int(corte_x_ev))    ,fontsize=16, color ='red')
    plt.text((x[nm1] - x[0]) / 5., tolv * 0.96,'v:{:.1f}'.format(tolv),fontsize=16, color ='red')
    plt.plot(corte_x_ev, tolv, 'ro') 

    plt.plot(x, log_d, label = 'dif.pases'      , linewidth=2                     , color ='green')
    plt.vlines(x=corte_x_d, ymin=ymin, ymax=ymax, linewidth=1                     , colors='green')
    plt.text(corte_x_d, ymin * 0.76,'d:{}'.format(int(corte_x_d)) , fontsize=16   , color ='green')
    plt.plot(corte_x_d, tolv, 'go') 

    plt.plot(x, log_m, label = 'raíz mérito'    , linewidth=2                        , color ='black')
    plt.vlines(x=corte_x_m, ymin=ymin, ymax=ymax, linewidth=1    , linestyle='dashed', colors='black')
    plt.hlines(y=corte_y_m, xmin=x[0], xmax=x[nm1],linewidth=1   , linestyle='dashed', colors='black')
    plt.text(corte_x_m, ymax * 0.76,'m:{}'.format(int(corte_x_m)), fontsize=16       , color ='black')
    plt.text(x[0], corte_y_m * 0.96,'m:{:.1f}'.format(corte_y_m) , fontsize=16       , color ='black')
    plt.plot(corte_x_m, corte_y_m, 'ko') 
    
    plt.legend(fontsize=16)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    ax = plt.gca()
    tx = ax.xaxis.get_offset_text()
    tx.set_backgroundcolor('black')
    tx.set_color('white')
    tx.set_fontsize(16)
    ty = ax.yaxis.get_offset_text()
    ty.set_backgroundcolor('black')
    ty.set_color('white')
    ty.set_fontsize(16)

    plt.savefig(senda + ID + '_' + nombre + '.png', dpi=300, facecolor='w', edgecolor='w', orientation='portrait', format='png', transparent=False, bbox_inches=None, pad_inches=0.1, metadata=None)
    plt.close(fig)

def GraficoPares(x, y, b, m, R2, rot_x, rot_y, senda, nombre):
    nm1     = len(x) - 1
    fig = plt.figure(dpi=300, figsize=(15.0,7.0), clear=True)
    plt.title('Relación entre pares', fontsize=20)

    plt.xlabel(rot_x, fontsize=18)
    plt.ylabel(rot_y, fontsize=18)
    
    plt.plot(x, y, 'ro')
    xmin = min(x)
    xmax = max(x)
    y1 = b + m * xmin
    y2 = b + m * xmax
    ymax = max(max(y), y1, y2)
    plt.plot([xmin,xmax], [y1,y2], linewidth=2, color='blue')

    plt.text(xmin, ymax, 'y = {:.3f} + {:.3f} * x    R2={:.3f}  10**b={:9.2e}'.format(b, m, R2, 10**b), fontsize=16, color='blue')

    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.savefig(senda + ID + '_' + nombre + '.png', dpi=300, facecolor='w', edgecolor='w', orientation='portrait', format='png', transparent=False, bbox_inches=None, pad_inches=0.1, metadata=None)
    plt.close(fig)

def GraficoResumenPares(n_filas, n_cols, x, y, rl, senda, nombnre, titulo):
    if n_filas == 1:
        # asegurar un mosaico de gráficos con dos dimensiones
        n_filas = 2
    nimg = len(y)
    n_filas_cal = int(nimg / n_cols)
    if n_filas_cal * n_cols < nimg:
        n_filas_cal += 1
    if n_filas_cal > n_filas:
        n_filas_img = n_filas_cal
    else:
        n_filas_img = n_filas
    alto = 12. * n_filas_img / n_filas
    fig, axes = plt.subplots(nrows=n_filas_img, ncols=n_cols, figsize=(24., alto))
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    m = 0
    for fil in range(n_filas_img):
        for col in range(n_cols):
            axes[fil, col].tick_params(axis='both', which='major', labelsize=16)
            axes[fil, col].title.set_size(20)
            if m < nimg:
                axes[fil, col].scatter(x[m], y[m], s=48, c='red', marker='o')
                xmin = min(x[m])
                xmax = max(x[m])
                if len(rl) > 0:
                    b = rl[m][0]
                    p = rl[m][1]
                    y1 = b + p * xmin
                    y2 = b + p * xmax
                    ymin = min(min(y[m]), y1, y2)
                    ymax = max(max(y[m]), y1, y2)
                    axes[fil, col].text(xmin, ymin + 5./6. * (ymax - ymin), 'y = {:.3f} + {:.3f} * x'.format(b, p), fontsize=20, color='blue')
                    axes[fil, col].plot([xmin,xmax], [y1,y2], linewidth=2, color='blue')
                else:
                    # para mostrar mejor detalle
                    k = len(y[m])//2 - 1
                    if k < 0:
                        k = 0
                    ymax = max(y[m][k:-1])
                    ymin = min(y[m][k:-1])
                    dif = abs(ymax - ymin)
                    ymax += dif * 0.1
                    ymin -= dif * 0.1
                    if ymax < dif * 0.1:
                        ymax = dif * 0.1
                    if ymin > -dif * 0.1:
                        ymin = -dif * 0.1
                    axes[fil, col].set_ylim(ymin, ymax)

                    axes[fil, col].hlines(y=0., xmin=xmin, xmax=xmax, linewidth=3, linestyle='dotted', colors='gray')
                axes[fil, col].title.set_text(titulo[m])
            else:
                axes[fil, col].set_xticks([])
                axes[fil, col].set_yticks([])
            m += 1
    fig.tight_layout()
    plt.savefig('{}/{}.png'.format(senda, nombnre), dpi=300, facecolor='w', edgecolor='w', orientation='portrait', format='png', transparent=False, bbox_inches=None, pad_inches=0.1, metadata=None)
    plt.close()

def GraficoEvolucionDerivadas(x, ep, ev, d, m, roty, senda, nombre):
    if len(ep) == 0 and len(ev) == 0 and len(d) == 0 and len(m) == 0:
        return
    fig = plt.figure(dpi=300, figsize=(15.0,7.0), clear=True)
    plt.title('Evolución de la derivada', fontsize=20)
    plt.xlabel('generaciones', fontsize=18)
    plt.ylabel(roty, fontsize=18)
    plt.hlines(y=0., xmin=x[0], xmax=x[len(x) - 1], linewidth=1, linestyle='dotted', colors='gray')
    if len(ep) > 0:
        plt.plot(x, ep, label = 'error pre'  , linewidth=2, color='blue')
    if len(ev) > 0:
        plt.plot(x, ev, label = 'error var'  , linewidth=2, color='red')
    if len(d) > 0:
        plt.plot(x, d , label = 'dif.pases'  , linewidth=2, color='green')
    if len(m) > 0:
        plt.plot(x, m , label = 'raíz mérito', linewidth=2, color='black')

    plt.legend(fontsize=16)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    ax = plt.gca()
    tx = ax.xaxis.get_offset_text()
    tx.set_backgroundcolor('black')
    tx.set_color('white')
    tx.set_fontsize(16)
    ty = ax.yaxis.get_offset_text()
    ty.set_backgroundcolor('black')
    ty.set_color('white')
    ty.set_fontsize(16)
    
    val_ini = plt.gca().get_yticks().tolist()
    val_mod = []
    for v in val_ini:
        val_mod.append('{:8.1e}'.format(v) if v != 0 else '{:8.1f}'.format(v))
    plt.gca().set_yticks(np.array(val_mod,dtype=np.float64), labels=val_mod)

    plt.savefig(senda + ID + nombre + '.png', dpi=300, facecolor='w', edgecolor='w', orientation='portrait', format='png', transparent=False, bbox_inches=None, pad_inches=0.1, metadata=None)
    plt.close(fig)

def GraficoRangosY(x, vmin_y, vmax_y, vmin_ddvc, vmax_ddvc, senda, nombre, roty):
    fig = plt.figure(dpi=300, figsize=(15.0,7.0), clear=True)
    plt.title('Evolución del rango de variación de la "diferencia entre pases" y del "error"', fontsize=20)
    plt.xlabel('generaciones', fontsize=18)
    plt.ylabel(roty, fontsize=18)

    plt.plot(x, vmax_y   , color='blue'  , linewidth=1)
    plt.plot(x, vmin_y   , color='red'   , linewidth=1)
    plt.plot(x, vmax_ddvc, color='orange', linewidth=1)
    plt.plot(x, vmin_ddvc, color='green' , linewidth=1)

    plt.scatter(x, vmax_y,    s=28, c='blue'  , marker='o', label='dif max')
    plt.scatter(x, vmin_y,    s=10, c='red'   , marker='o', label='dif min')
    plt.scatter(x, vmax_ddvc, s=28, c='orange', marker='o', label='err max')
    plt.scatter(x, vmin_ddvc, s=10, c='green' , marker='o', label='err min')

    plt.legend(fontsize=16)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    ax = plt.gca()
    tx = ax.xaxis.get_offset_text()
    tx.set_backgroundcolor('black')
    tx.set_color('white')
    tx.set_fontsize(16)
    ty = ax.yaxis.get_offset_text()
    ty.set_backgroundcolor('black')
    ty.set_color('white')
    ty.set_fontsize(16)
    
    val_ini = plt.gca().get_yticks().tolist()
    val_mod = []
    for v in val_ini:
        val_mod.append('{:8.1e}'.format(v) if v != 0 else '{:8.1f}'.format(v))
    plt.gca().set_yticks(np.array(val_mod,dtype=np.float64), labels=val_mod)

    plt.savefig(senda + ID + nombre + '.png', dpi=300, facecolor='w', edgecolor='w', orientation='portrait', format='png', transparent=False, bbox_inches=None, pad_inches=0.1, metadata=None)
    plt.close(fig)

def GraficoDispersion(n_filas, n_cols, deca, y, senda, nombre, titulo, limy, miny, maxy):
    if n_filas == 1:
        # asegurar un mosaico de gráficos con dos dimensiones
        n_filas = 2
    x = range(y.shape[1])
    filas_y = y.shape[0]
    n_imgs = filas_y // deca
    if n_imgs * deca <= filas_y:
        # siempre se muestra la última imagen
        n_imgs += 1

    ng = n_imgs // (n_filas * n_cols)
    if ng * (n_filas * n_cols) < n_imgs:
        ng += 1
    alto = 12.
    if limy == 0:
        # misma scala 'y' igual a la del último gráfico
        ymin = np.min(y[-1])
        ymax = np.max(y[-1])
    elif limy == 1:
        # 1 : misma scala 'y' igual a la establecida por los parámetros ymin y ymax
        ymin = miny
        ymax = maxy
    else:
        # 2 : diferente scala 'y' para cada gráfico
        ymin = 0
        ymax = 0

    m = 0
    for g in range(ng):
        completar = False
        if limy == 0:
            fig, axes = plt.subplots(nrows=n_filas, ncols=n_cols, figsize=(24, alto), sharey=True)
        elif limy == 1:
            fig, axes = plt.subplots(nrows=n_filas, ncols=n_cols, figsize=(24, alto), sharey=True)
        else:
            fig, axes = plt.subplots(nrows=n_filas, ncols=n_cols, figsize=(24, alto), sharey=False)
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        plt.rcParams.update({'font.size': 12})
        for fil in range(n_filas):
            for col in range(n_cols):
                axes[fil, col].set_xticks([])
                axes[fil, col].title.set_size(16)
                axes[fil, col].tick_params(axis='both', which='major', labelsize=12)
                axes[fil, col].yaxis.get_major_formatter().set_scientific(False)
                if m < filas_y:
                    axes[fil, col].scatter(x , y[m]  , s=16, c='0', marker='o')
                    # los histogramas no muestran nada porque la inmensa mayoria de desvios son 0
                    #axes[fil, col].hist(y[m], bins=50, color='blue', edgecolor='black')
                    vmin = np.min(y[m])
                    vmax = np.max(y[m])
                    vmin = '{:.1e}'.format(vmin)
                    vmax = '{:.1e}'.format(vmax)
                    if limy == 0 or limy == 1:
                        # 0 : misma scala 'y' igual a la del último gráfico
                        # 1 : misma scala 'y' igual a la establecida por los parámetros ymin y ymax
                        axes[fil, col].set_ylim(ymin, ymax)
                        dentro = np.count_nonzero((ymin <= y[m]) & (y[m] <= ymax))
                    else:
                        dentro = y.shape[1]
                    axes[fil, col].title.set_text('{} [{} {}] {:5.1f}%'.format(titulo[m], vmin, vmax, 100. * dentro / y.shape[1]))
                um = m                
                if completar:
                    # completar las filas y columnas restantes con gráficos vacíos
                    m += 1;
                else:
                    m += deca
                    if m >= filas_y:
                        completar = True
                        m = filas_y - 1
                        if m == um:
                            m = filas_y
            # fila terminada
        # gráfico terminado
        fig.tight_layout()
        plt.savefig(senda + ID + '_' + nombre + '_{:03d}.png'.format(g), dpi=300, facecolor='w', edgecolor='w', orientation='portrait', format='png', transparent=False, bbox_inches=None, pad_inches=0.1, metadata=None)
        plt.close()
    # gráficos terminados

#--------------
# fin funciones
#--------------

ns = -1
for SENDA in SENDAS:
    SENDA_SALIDAS = SENDA + 'pSol/' + str(MENOS_INI) + '_' + str(MENOS_FIN) + '/'
    FICHERO_LOG   = SENDA_SALIDAS   + 'correlaciones.log'
    os.makedirs(SENDA_SALIDAS, exist_ok=True)
    imprime(SENDA)
    ns += 1
    for ID, N_DESVIOS, DESDE, HASTA in IDS[ns]:
        imprime('    ' + ID, False)
        FUENTE  = SENDA + ID + '_' + NPOB + SUFIJO
        DESTINO = SENDA_SALIDAS + ID + '_tabla.csv'
        patron  = FUENTE + "???.log"
        ficheros = glob.glob(patron)
        if DESDE == -1:
            DESDE = MENOS_INI
        if HASTA == -1:
            HASTA = MENOS_FIN
        imprime(' [{:4d} ficheros. Omitir los {:4d} primeros y los {:4d} últimos]'.format(len(ficheros), MENOS_INI, DESDE))
        NUM_FICHEROS = len(ficheros) - 1    # quitar el 'fin.log'
        FI_FIN = NUM_FICHEROS 
        if NUM_FICHEROS < MENOS_INI + MENOS_FIN + 1:
            imprime('Se necesitan al menos {} ficheros de soluciones'.format(MENOS_INI + MENOS_FIN + 1 + 1))
            continue
        
        fichero = FUENTE + 'fin' + '.log'
        if os.path.isfile(fichero) == False:
            # al no encontrarse 'fin.log, se excluye el último para utilizarlo como 'fin.log'
            NUM_FICHEROS -= 1
            if NUM_FICHEROS < MENOS_INI + MENOS_FIN + 1:
                imprime('Si no existe el final, se necesitan al menos {} ficheros de soluciones'.format(MENOS_INI + MENOS_FIN + 1 + 1))
                continue
            else:
                imprime('No existe el fichero final:\n    {}\nse utilizará el último de los ficheros de soluciones:\n    {}{:03d}.log'.format(fichero, FUENTE, FI_FIN))

        # excluir los primeros MENOS_INI ficheros de soluciones
        NUM_FICHEROS -= MENOS_INI
        # excluir los últimos MENOS_FIN ficheros de soluciones
        NUM_FICHEROS -= MENOS_FIN

        # contar el número de líneas en el primer fichero        
        fichero = FUENTE + '{:03d}'.format(MENOS_INI) + '.log'
        with open(fichero, "r", encoding="utf-8") as f:
            LINEAS_FICHERO = sum(1 for linea in f)
        if LINEAS_FICHERO != ULT_LINEA:
            imprime('inconsistencia en el número de líneas de los ficheros {} vs {}'.format(LINEAS_FICHERO, ULT_LINEA))
            sys.exit()

        # el número de columnas añade las tres iniciales: 'N','variable' y 'indice' y la final 'fin'
        cabeceras = ['N','variable','indice'] + list(range(0,NUM_FICHEROS)) + ['fin',]
        '''
        al número de filas del fichero se añaden:
          las primeras FIL_ADD_INI:
               0 'Generaciones'
               1 'Prec.max.err'
               2 'Err.max.prec'
               3 'Vari.max.err'
               4 'Err.max.vari'
               5 'Error maximo'
               6 'Vari.max.dif'
               7 'Dif.max.pases'
               8 'Suma diferencias'
               9 'suma error'
              10 log10(Error maximo)
              11 log10(Dif.max.pases)
              12 VAB
              13 impuestos
              14 cotizacion SS
              15 suma Z
              16 suma Q
          las N_VAR_CAL al final:
               para las diferencias entre el primer y el segundo pase de cada variable
        '''
        tabla = DataFrame(columns=cabeceras,index=range(0, FIL_ADD_INI + LINEAS_FICHERO + N_VAR_CAL))
        # rotulos de las tres primeras columnas (COL_ADD_INI) de las filas adicionales al principio
        for i in range(FIL_ADD_INI):
            tabla.iloc[i,0]  = rot_filas[i]
            tabla.iloc[i,1] = ''
            tabla.iloc[i,2] = ''
        # poner a 0 la columna 'fin' de las filas adicionales al principio
        for i in range(1, FIL_ADD_INI):
            tabla.loc[i,'fin'] = 0.

        # procesar los ficheros con las soluciones, excepto el de la última ('fin')

        for i in range(0, NUM_FICHEROS):
            fichero = FUENTE + '{:03d}'.format(MENOS_INI + i) + '.log'
            with open(fichero, "r", encoding="utf-8") as f:
                n = FIL_ADD_INI
                while True:
                    line = f.readline()
                    if line == "":
                        break
                    s = line.split(';')
                    if i == 0:
                        # extraer del primer fichero las tres primeras columnas de todas las filas, excepto de la primera línea
                        if n == FIL_ADD_INI:
                            # primera línea del fichero
                            tabla.iloc[n,0] = 'Merito'
                            tabla.iloc[n,1] = ''
                            tabla.iloc[n,2] = ''
                        else:
                            tabla.iloc[n,0] = int(s[0])
                            tabla.iloc[n,1] = s[1].strip()
                            tabla.iloc[n,2] = int(s[2])
                    # en todos los ficheros, la primera fila aporta dos valores
                    if n == FIL_ADD_INI:
                        # la primera linea aporta el número de generaciones y hay que colocarlo en la
                        # columna correspondiente de la fila 0
                        tabla.iloc[0,COL_ADD_INI + i] = int(s[0])
                    # todas las líneas, incluida la primera, aportan el valor de una variable 
                    tabla.iloc[n,COL_ADD_INI + i] = np.float64(s[3])
                    n += 1

        # procesar el fichero con la solución final

        fichero = FUENTE + 'fin' + '.log'
        if os.path.isfile(fichero) == False:
            # utilizar el último que previamente hemos excluido
            fichero = FUENTE + '{:03d}'.format(FI_FIN) + '.log'

        with open(fichero, "r", encoding="utf-8") as f:
            n = FIL_ADD_INI
            while True:
                line = f.readline()
                if line == "":
                    break
                s = line.split(';')
                if n == FIL_ADD_INI:
                    # la primera linea aporta el número de generaciones y hay que colocarlo en la
                    # columna correspondiente de la fila 0
                    tabla.iloc[0,COL_ADD_INI + NUM_FICHEROS] = int(s[0])
                # todas las líneas, incluida la primera, aportan el valor de una variable 
                tabla.iloc[n,COL_ADD_INI + NUM_FICHEROS] = np.float64(s[3])
                n += 1

        # calcular las diferencias de cada columna 'i' con la columna final 'fin', es decir, el error de cada columna respecto a la solución final
        dvc = []    # almacena las diferencias de cada columna respecto a la columna final 'fin' para los gráficos de dispersión de errores de las variables 'GraficoDispersion'
        for i in range(0, NUM_FICHEROS):
            # precios
            fila_ini = FIL_ADD_INI + 1
            fila_fin = fila_ini + PRECIOS
            dp = abs(tabla[i][fila_ini:fila_fin] - tabla['fin'][fila_ini:fila_fin])
            # Prec.max.err nombre de la variable con el error máximo
            tabla.iloc[1,COL_ADD_INI + i] = tabla.iloc[dp.idxmax(),1] + '  ' + str(tabla.iloc[dp.idxmax(),2])
            # Err.max.prec valor del error máximo
            tabla.iloc[2,COL_ADD_INI + i] = max(dp)

            # variables, incluidas Fi, Ei, Mi, Di, pz, pe, pm = 8 * NSEC 
            fila_ini = FIL_ADD_INI + 1 + PRECIOS
            fila_fin = FIL_ADD_INI + LIN_INI_Spase - 1 # fila_ini + V_C_UNICO + N_VAR_CAL
            dva = tabla[i][fila_ini:fila_fin] - tabla['fin'][fila_ini:fila_fin]
            dv = abs(dva)
            # Vari.max.err nombre de la variable con el error máximo
            tabla.iloc[3,COL_ADD_INI + i] = tabla.iloc[dv.idxmax(),1] + '  ' + str(tabla.iloc[dv.idxmax(),2])
            # Err.max.vari valor del error máximo
            tabla.iloc[4,COL_ADD_INI + i] = max(dv)
            dvc.append(dva)

            # Error maximo
            tabla.iloc[5,COL_ADD_INI + i] = max(tabla.iloc[2,COL_ADD_INI + i],tabla.iloc[4,COL_ADD_INI + i])
            # Suma error
            tabla.iloc[9,COL_ADD_INI + i] = sum(dp) + sum(dv)
        del dp
        del dv
        ddvc = np.array(dvc)
        del dvc

        # añadir las diferencias entre el primer y segundo pase en las últimas N_VAR_CAL filas

        f1 = FIL_ADD_INI + LIN_INI_Ppase - 1
        f2 = FIL_ADD_INI + LIN_INI_Spase - 1
        fd = FIL_ADD_INI + ULT_LINEA

        # las tres primeras columnas

        n = 0
        for i in range(N_VAR_CAL):
            tabla.iloc[fd,0] = tabla.iloc[f2,0]                             # indice del sustraendo
            tabla.iloc[fd,1] = tabla.iloc[f2,1] + ' - ' + tabla.iloc[f1,1]  # variables que se restan
            if tabla.iloc[f1,1] != tabla.iloc[f1 - 1,1]:
                # cambio de bloque
                n = 0
            tabla.iloc[fd,2] = n    # desplazamiento dentro del bloque de la variable
            f1 += 1
            f2 += 1
            fd += 1
            n  += 1

        # las columnas con datos

        for j in range(NUM_FICHEROS + 1):
            f1 = FIL_ADD_INI + LIN_INI_Ppase - 1
            f2 = FIL_ADD_INI + LIN_INI_Spase - 1
            fd = FIL_ADD_INI + ULT_LINEA
            for i in range(N_VAR_CAL):
                tabla.iloc[fd,COL_ADD_INI + j] = tabla.iloc[f2,COL_ADD_INI + j] - tabla.iloc[f1,COL_ADD_INI + j]
                f1 += 1
                f2 += 1
                fd += 1
        
        # rango de filas con las diferencias entre pases
        fila_ini = FIL_ADD_INI + ULT_LINEA
        fila_fin = fila_ini + N_VAR_CAL
        # 'COL_ADD_INI:-1]' para que 'tab_dif' no tenga una fila más que el de errores 'ddvc' porque contiene las diferencias entre pases de la columna final 'fin' 
        tab_dif = tabla[fila_ini:fila_fin].iloc[:,COL_ADD_INI:-1]
        im = abs(tab_dif).idxmax()
        # 'y' es una matriz donde las filas son las diferencias (entre variables) a cada generación (NUM_FICHEROS, N_VAR_CAL)
        y = np.transpose(tab_dif.to_numpy(dtype=float))
        # las filas de errores 'ddvc' tienen mas valores que las de diferencias, especialmente porque incluyen Fi, Ei, Mi, Di, pz, pe, pm = 8 * NSEC
        # además las diferencias entre pases no coinciden una a una con los errores porque no se refieren a las mismas magnitudes
        # esto hace que la comparación de los gráficos de unas y otras no sea equivalente, aunque si suficientemente explicativa
        del tab_dif
        # mínimo y máximo de las difrencias entre pases de la (última generación - 1), escala del último gráfico
        miny = min(np.min(y[-1]), np.min(ddvc[-1]))
        maxy = max(np.max(y[-1]), np.max(ddvc[-1]))
        nf = 5
        nc = 5
        deca = y.shape[0] // (nf * nc)
        if deca * (nf * nc) <= y.shape[0]:
            deca += 1
        # 0 : misma scala 'y' igual a la del último gráfico
        # 1 : misma scala 'y' igual a la establecida por los parámetros ymin y ymax
        # 2 : diferente scala 'y' para cada gráfico
        GraficoDispersion(nf, nc, deca, y, SENDA_SALIDAS   , 'distri_dif=y' , tabla.iloc[0,COL_ADD_INI:].values, 0, miny, maxy)
        GraficoDispersion(nf, nc, deca, y, SENDA_SALIDAS   , 'distri_dif=yc', tabla.iloc[0,COL_ADD_INI:].values, 1, miny, maxy)
        GraficoDispersion(nf, nc, deca, y, SENDA_SALIDAS   , 'distri_dif'   , tabla.iloc[0,COL_ADD_INI:].values, 2, miny, maxy)
        
        deca = ddvc.shape[0] // (nf * nc)
        if deca * (nf * nc) <= ddvc.shape[0]:
            deca += 1
        GraficoDispersion(nf, nc, deca, ddvc, SENDA_SALIDAS, 'distri_err=y'   , tabla.iloc[0,COL_ADD_INI:].values, 0, miny, maxy)
        GraficoDispersion(nf, nc, deca, ddvc, SENDA_SALIDAS, 'distri_err=yc'  , tabla.iloc[0,COL_ADD_INI:].values, 1, miny, maxy)
        GraficoDispersion(nf, nc, deca, ddvc, SENDA_SALIDAS, 'distri_err'     , tabla.iloc[0,COL_ADD_INI:].values, 2, miny, maxy)
        ddvc = ddvc[:, 8 * NSEC:]
        GraficoDispersion(nf, nc, deca, ddvc, SENDA_SALIDAS, 'distri_erraj=y' , tabla.iloc[0,COL_ADD_INI:].values, 0, miny, maxy)
        GraficoDispersion(nf, nc, deca, ddvc, SENDA_SALIDAS, 'distri_erraj=yc', tabla.iloc[0,COL_ADD_INI:].values, 1, miny, maxy)
        GraficoDispersion(nf, nc, deca, ddvc, SENDA_SALIDAS, 'distri_erraj'   , tabla.iloc[0,COL_ADD_INI:].values, 2, miny, maxy)

        # prescindir del primer valor de cada fila
        x = tabla.iloc[0, COL_ADD_INI + 1:COL_ADD_INI + y.shape[0]].values
        vmin_y = []
        vmax_y = []
        for m in range(1, y.shape[0]):
            vmin_y.append(np.min(y[m]))
            vmax_y.append(np.max(y[m]))
        del y
        vmin_ddvc = []
        vmax_ddvc = []
        for m in range(1, ddvc.shape[0]):
            vmin_ddvc.append(np.min(ddvc[m]))
            vmax_ddvc.append(np.max(ddvc[m]))
        del ddvc
        GraficoRangosY(x, vmin_y, vmax_y, vmin_ddvc, vmax_ddvc, SENDA_SALIDAS, '_rango_y', '"diferencia entre pases" /  "error"')
        if len(x) < 6:
            saltar = len(x) - 1
        else:
            saltar = 5
        GraficoRangosY(x[saltar:], vmin_y[saltar:], vmax_y[saltar:], vmin_ddvc[saltar:], vmax_ddvc[saltar:], SENDA_SALIDAS, '_rango_red_y', '"diferencia entre pases" /  "error"')

        # valores máximos
        for i in range(NUM_FICHEROS):
            tabla.iloc[6,COL_ADD_INI + i] = tabla.iloc[im[i],1] + '  ' + str(tabla.iloc[im[i],2])
        # Dif.max.pases
        tabla.iloc[7,COL_ADD_INI:] = abs(tabla[fila_ini:fila_fin].iloc[:,COL_ADD_INI:]).max(axis=0)
        # Suma diferencias
        tabla.iloc[8,COL_ADD_INI:] = abs(tabla[fila_ini:fila_fin].iloc[:,COL_ADD_INI:]).sum(axis=0)

        log_raiz_merito = []
        for i in range(NUM_FICHEROS):
            col = COL_ADD_INI + i
            if tabla.iloc[5,col] != 0 and tabla.iloc[7,col] != 0:
                tabla.iloc[10,col] = math.log10(tabla.iloc[4,col])
                tabla.iloc[11,col] = math.log10(tabla.iloc[7,col])
                '''
                para poder comparar 'merito', que es el Error Cuadrático Total, con las otras series hay que:
                    1. dividirlo del número de variables pazra las que se calculan desviaciones
                    entre pases 'N_DESVIOS' y obtener el Error Cuadrático medio.
                    2. calcular la raiz cuadrada.
                '''
                log_raiz_merito.append(math.log10(math.sqrt(tabla.iloc[FIL_ADD_INI,col] / N_DESVIOS)))
            else:
                tabla.iloc[10,col] = 0.
                tabla.iloc[11,col] = 0.
                log_raiz_merito.append(0.)

            # VAB
            tabla.iloc[12,col] = 0
            for j in range(NSEC * NFAC):
                tabla.iloc[12,col] += tabla.iloc[FIL_ADD_INI + p_VAB + j,col] - tabla.iloc[FIL_ADD_INI + p_VAB + j, NUM_FICHEROS]
            # impuestos
            tabla.iloc[13,col] = tabla.iloc[FIL_ADD_INI + p_Ti,col] - tabla.iloc[FIL_ADD_INI + p_Ti, NUM_FICHEROS]
            for j in range(NSEC):
                tabla.iloc[13,col] += tabla.iloc[FIL_ADD_INI + p_Tz + j,col] - tabla.iloc[FIL_ADD_INI + p_Tz + j, NUM_FICHEROS]
                tabla.iloc[13,col] += tabla.iloc[FIL_ADD_INI + p_Tm + j,col] - tabla.iloc[FIL_ADD_INI + p_Tm + j, NUM_FICHEROS]
            for j in range(NDEM):
                tabla.iloc[13,col] += tabla.iloc[FIL_ADD_INI + p_Td + j,col] - tabla.iloc[FIL_ADD_INI + p_Td + j, NUM_FICHEROS]
            # cotización SS
            tabla.iloc[14,col] = 0
            for j in range(NSEC + NDEM):
                tabla.iloc[14,col] += tabla.iloc[FIL_ADD_INI + p_cotizacion_SS + j,col] - tabla.iloc[FIL_ADD_INI + p_cotizacion_SS + j, NUM_FICHEROS]
            # Suma Z
            tabla.iloc[15,col] = 0
            tabla.iloc[16,col] = 0
            for j in range(NSEC):
                tabla.iloc[15,col] += tabla.iloc[FIL_ADD_INI + p_suma_Z + j,col] - tabla.iloc[FIL_ADD_INI +  p_suma_Z + j, NUM_FICHEROS]
                tabla.iloc[16,col] += tabla.iloc[FIL_ADD_INI + p_suma_Q + j,col] - tabla.iloc[FIL_ADD_INI +  p_suma_Q + j, NUM_FICHEROS]

        # guardar la tabla a un fichero

        tabla.to_csv(DESTINO, sep=';', index=False, encoding="utf-8")

        # buscar la columna a partir de la cual Las mejoras son inferiores a la tolerancia

        imprime('tolerancia precios   {}'.format(TOL_PRECIOS))
        imprime('tolerancia variables {}'.format(TOL_VARIABLES))

        # 'COL_ADD_INI+1' para evitar el primer punto (solución 0)

        x      = tabla.iloc[0, COL_ADD_INI + 1:-1].values
        n      = len(x)
        if n < 2:
            continue
        nm1    = n - 1
        log_ep = []
        for i in range(1,NUM_FICHEROS):
            if tabla.iloc[2, COL_ADD_INI + i] == 0:
                log_ep.append(0.)
            else:
                log_ep.append(math.log10(tabla.iloc[2, COL_ADD_INI + i]))

        log_ev = tabla.iloc[10, COL_ADD_INI + 1:-1].values
        log_d  = tabla.iloc[11, COL_ADD_INI + 1:-1].values
        log_m  = log_raiz_merito[1:]
        if n!= len(log_ev):
            imprime('la dimensión de x {} no coincide con la de log_ev {}'.format(n,len(log_ev)))
            sys.exit()
        if len(log_ep) != 0 and n!= len(log_ep):
            imprime('la dimensión de x {} no coincide con la de log_ep {}'.format(n,len(log_ep)))
            sys.exit()
        if n!= len(log_d):
            imprime('la dimensión de x {} no coincide con la de log_d {}'.format(n,len(log_d)))
            sys.exit()
        if n!= len(log_m):
            imprime('la dimensión de x {} no coincide con la de log_m {}'.format(n,len(log_m)))
            sys.exit()

        a_ep = tabla.iloc[2, COL_ADD_INI + 1:-1].values
        a_ev = tabla.iloc[4, COL_ADD_INI + 1:-1].values
        a_d  = tabla.iloc[7, COL_ADD_INI + 1:-1].values
        a_m  = []
        for i in range(1,NUM_FICHEROS):
            a_m.append(math.sqrt(tabla.iloc[FIL_ADD_INI,COL_ADD_INI + i] / N_DESVIOS))

        tolp = math.log10(TOL_PRECIOS)
        tolv = math.log10(TOL_VARIABLES)

        log_ep = np.array(log_ep,dtype=float)
        log_ev = np.array(log_ev,dtype=float)
        log_m  = np.array(log_m,dtype=float)
        log_d  = np.array(log_d,dtype=float)

        g_log_ep.append(log_ep)
        g_log_ev.append(log_ev)
        g_log_m.append(log_m)
        g_log_d.append(log_d)

        corte_x_ep = x[nm1]
        for i in range(nm1,-1,-1):
            v = log_ep[i]
            if v > tolp:
                if i == 0:
                    corte_x_ep = x[0]
                elif i == nm1:
                    corte_x_ep = x[nm1] + (x[nm1] - x[nm1-1]) / 2.
                else:
                    # interpolar linealmente
                    corte_x_ep =x[i] + (x[i] - x[i+1]) * (v-tolp) / (log_ep[i+1]-log_ep[i])
                break
        corte_x_ev = x[nm1]
        for i in range(nm1,-1,-1):
            v = log_ev[i]
            if v > tolv:
                if i == 0:
                    corte_x_ev = x[0]
                elif i == nm1:
                    corte_x_ev = x[nm1] + (x[nm1] - x[nm1-1]) / 2.
                else:
                    # interpolar linealmente
                    corte_x_ev =x[i] + (x[i] - x[i+1]) * (v-tolv) / (log_ev[i+1]-log_ev[i])
                break
        corte_x_d = x[nm1]
        for i in range(nm1,-1,-1):
            v = log_d[i]
            if v > tolv:
                if i == 0:
                    corte_x_d = x[0]
                elif i == nm1:
                    corte_x_d = x[nm1] + (x[nm1] - x[nm1-1]) / 2.
                else:
                    # interpolar linealmente
                    corte_x_d = x[i] + (x[i] - x[i+1]) * (v-tolv) / (log_d[i+1]-log_d[i])
                break
        corte_x_m = max(corte_x_ev, corte_x_ep)
        corte_y_m = log_m[0]
        for i in range(n):
            v = x[i]
            if v > corte_x_m:
                # interpolar linealmente
                corte_y_m = log_m[i] + (log_m[i] - log_m[i-1]) * (v - corte_x_m) / (x[i-1]-x[i])
                break
        imprime  ('generacion de corte {:.0f}\n'.format(corte_x_m))
        GraficoEvolucion(
            x,
            log_ep,
            log_ev,
            log_d,
            log_m,
            corte_x_ep,
            corte_x_ev,
            corte_x_d,
            corte_x_m,
            SENDA_SALIDAS,
            '_evError_{}_{}'.format(TOL_PRECIOS,TOL_VARIABLES)
        )

        # derivadas

        dx      = []
        dlog_ep = []
        dlog_ev = []
        dlog_d  = []
        dlog_m  = []

        da_ep = []
        da_ev = []
        da_d  = []
        da_m  = []
        for i in range(n-1):
            vx = x[i+1] - x[i]
            dx.append((x[i+1] + x[i]) / 2.)
            dlog_ep.append((log_ep[i+1] - log_ep[i]) / vx)
            dlog_ev.append((log_ev[i+1] - log_ev[i]) / vx)
            dlog_d.append((log_d  [i+1] - log_d [i]) / vx)
            dlog_m.append((log_m  [i+1] - log_m [i]) / vx)

            da_ep.append((a_ep[i+1] - a_ep[i]) / vx)
            da_ev.append((a_ev[i+1] - a_ev[i]) / vx)
            da_d.append((a_d [i+1]  - a_d [i]) / vx)
            da_m.append((a_m [i+1]  - a_m [i]) / vx)

        if len(dx) < 3:
            saltar = len(dx) - 1
        else:
            saltar = 3
        GraficoEvolucionDerivadas(
            dx[saltar:],
            dlog_ep[saltar:],
            dlog_ev[saltar:],
            dlog_d[saltar:],
            dlog_m[saltar:],
            'derivada del logaritmo base 10',
            SENDA_SALIDAS,
            '_De_log_{}_{}'.format(TOL_PRECIOS,TOL_VARIABLES),
        )
        if len(dx) < 4:
            saltar = len(dx) - 1
        else:
            saltar = 3
        GraficoEvolucionDerivadas(
            dx[saltar:],
            da_ep[saltar:],
            da_ev[saltar:],
            da_d[saltar:],
            da_m[saltar:],
            'derivada de los valores',
            SENDA_SALIDAS,
            '_De_abs_{}_{}'.format(TOL_PRECIOS,TOL_VARIABLES),
        )
        GraficoEvolucionDerivadas(
            dx[saltar:],
            [],
            da_ev[saltar:],
            [],
            [],
            'derivada del error máximo de una variable',
            SENDA_SALIDAS,
            '_De_abs_ev_{}_{}'.format(TOL_PRECIOS,TOL_VARIABLES),
        )
        GraficoEvolucionDerivadas(
            dx[saltar:],
            [],
            [],
            [],
            da_m[saltar:],
            'derivada de la raíz del mérito',
            SENDA_SALIDAS,
            '_De_abs_m_{}_{}'.format(TOL_PRECIOS,TOL_VARIABLES),
        )

        cova_m_ep  = np.cov(log_m, log_ep)[0][1]
        cova_m_ev  = np.cov(log_m, log_ev)[0][1]
        cova_m_d   = np.cov(log_m , log_d)[0][1]
        cova_ep_ev = np.cov(log_ep, log_ev)[0][1]
        imprime('covarianza merito  - precios     {:.3f}'.format(cova_m_ep))
        imprime('covarianza merito  - variables   {:.3f}'.format(cova_m_ev))
        imprime('covarianza merito  - diferencias {:.3f}'.format(cova_m_d))
        imprime('covarianza precios - variables   {:.3f}\n'.format(cova_ep_ev))
        
        '''
        El valor p nos muestra la probabilidad de haber obtenido el resultado que
        hemos obtenido suponiendo que la hipótesis nula H0 es cierta.
        
        Cuanto menor sea el valor p, menor será la probabilidad de obtener ese resultado si la hipótesis nula fuera cierta
        Los valores de p pueden indicar cómo son los datos de incompatibles con cierto modelo estadístico.
        Los valores de p no miden la probabilidad de que la hipótesis nula sea cierta, ni tampoco
        la probabilidad de que los datos hayan sido producidos enteramente al azar.
        El valor de p no representa la probabilidad de que la hipótesis nula sea cierta: partimos del supuesto de que la hipótesis nula es
        cierta y es bajo ese supuesto en el que calculamos el valor de p.

        En el contexto de 'sm.OLS', el valor p es una medida estadística que ayuda a determinar si los coeficientes de
        la línea de regresión son significativamente diferente de cero. Se deriva de una prueba de hipótesis
        donde la hipótesis nula asume, para cada coeficiente, que este es cero. Si la pendiente es cero significa que
        no existe una relación lineal entre las dos variables.
        Un valor p bajo (típicamente inferior a 0.05) indica que la hipótesis nula puede ser rechazada, lo que
        sugiere que la pendiente es significativamente diferente de cero. Esto implica una relación
        lineal estadísticamente significativa entre las variables predictor (x) y respuesta (y).
        Por el contrario, un valor p alto (superior a 0,05) sugiere que la hipótesis nula no puede ser rechazada, lo
        que significa que no hay evidencia suficiente para concluir una relación lineal significativa entre las variables.
        '''

        xm  = sm.add_constant(log_m)
        xep = sm.add_constant(log_ep)
        res_m_ep = sm.OLS(log_ep , xm ).fit()
        res_m_ev = sm.OLS(log_ev , xm ).fit()
        res_m_d  = sm.OLS(log_d  , xm ).fit()
        res_ep_ev= sm.OLS(log_ev , xep).fit()
        imprime('    xy         y0         10**y0          m            R2      p-value y0    p-value m')
        imprime('--------- ------------ ------------ ------------ ------------ ------------ ------------')
        imprime('{:9s} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e}'.format('par m_ep' , res_m_ep.params[0],10**res_m_ep.params[0],res_m_ep.params[1],res_m_ep.rsquared,res_m_ep.pvalues[0],res_m_ep.pvalues[1]))
        imprime('{:9s} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e}'.format('par m_ev' , res_m_ev.params[0],10**res_m_ev.params[0],res_m_ev.params[1],res_m_ev.rsquared,res_m_ev.pvalues[0],res_m_ev.pvalues[1]))
        imprime('{:9s} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e}'.format('par m_d'  , res_m_d.params[0],10**res_m_d.params[0],res_m_d.params[1],res_m_d.rsquared,res_m_d.pvalues[0],res_m_d.pvalues[1]))
        imprime('{:9s} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e}'.format('par ep_ev', res_ep_ev.params[0],10**res_ep_ev.params[0],res_ep_ev.params[1],res_ep_ev.rsquared,res_ep_ev.pvalues[0],res_ep_ev.pvalues[1]))
        imprime('--------- ------------ ------------ ------------ ------------ ------------ ------------')

        GraficoPares(log_m, log_ep, res_m_ep.params[0] , res_m_ep.params[1] , res_m_ep.rsquared , 'log_merito' , 'log_precios'    , SENDA_SALIDAS, 'par_m_ep')
        GraficoPares(log_m, log_ev, res_m_ev.params[0] , res_m_ev.params[1] , res_m_ev.rsquared , 'log_merito' , 'log_variables'  , SENDA_SALIDAS, 'par_m_ev')
        GraficoPares(log_m ,log_d , res_m_d.params[0]  , res_m_d.params[1]  , res_m_d.rsquared  , 'log_merito' , 'log_diferencias', SENDA_SALIDAS, 'par_m_d')
        GraficoPares(log_ep,log_ev, res_ep_ev.params[0], res_ep_ev.params[1], res_ep_ev.rsquared, 'log_precios', 'log_variables'  , SENDA_SALIDAS, 'par_ep_ev')

        gr_m_ep.append ([res_m_ep.params[0] , res_m_ep.params[1]])
        gr_m_ev.append ([res_m_ev.params[0] , res_m_ev.params[1]])
        gr_m_d.append  ([res_m_d.params[0]  , res_m_d.params[1]])
        gr_ep_ev.append([res_ep_ev.params[0], res_ep_ev.params[1]])

        g_log_m_s = []
        g_log_m_s.append(log_m)
        g_log_m_s.append(log_m)
        g_log_m_s.append(log_m)
        g_log_m_s.append(log_m)
        g_log_m_s.append(log_m)
        g_agregados = []
        g_agregados.append(tabla.iloc[12, COL_ADD_INI + 1:-1].values)
        g_agregados.append(tabla.iloc[13, COL_ADD_INI + 1:-1].values)
        g_agregados.append(tabla.iloc[14, COL_ADD_INI + 1:-1].values)
        g_agregados.append(tabla.iloc[15, COL_ADD_INI + 1:-1].values)
        g_agregados.append(tabla.iloc[16, COL_ADD_INI + 1:-1].values)
        GraficoResumenPares(3, 2, g_log_m_s, g_agregados, [], SENDA_SALIDAS, 'resumen_m_sumas_' + ID, titulo_s)

        xd  = sm.add_constant(log_d)
        res_d_ep = sm.OLS(log_ep , xd ).fit()
        res_d_ev = sm.OLS(log_ev , xd ).fit()
        res_d_m  = sm.OLS(log_m  , xd ).fit()
        imprime('    xy         y0         10**y0          m            R2      p-value y0    p-value m')
        imprime('--------- ------------ ------------ ------------ ------------ ------------ ------------')
        imprime('{:9s} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e}'.format('par d_ep' , res_d_ep.params[0], 10**res_d_ep.params[0], res_d_ep.params[1],res_d_ep.rsquared,res_d_ep.pvalues[0],res_d_ep.pvalues[1]))
        imprime('{:9s} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e}'.format('par d_ev' , res_d_ev.params[0], 10**res_d_ev.params[0], res_d_ev.params[1],res_d_ev.rsquared,res_d_ev.pvalues[0],res_d_ev.pvalues[1]))
        imprime('{:9s} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e}'.format('par d_m' , res_d_m.params[0], 10**res_d_m.params[0], res_d_m.params[1],res_d_m.rsquared,res_d_m.pvalues[0],res_d_m.pvalues[1]))
        imprime('--------- ------------ ------------ ------------ ------------ ------------ ------------')

        with open(DESTINO, "a", encoding="utf-8") as f:
            f.write('tolerancia precios   {}\n'.format(TOL_PRECIOS))
            f.write('tolerancia variables {}\n'.format(TOL_VARIABLES))
            f.write('generacion de corte {:.0f}\n'.format(corte_x_m))
            f.write('covarianza merito  - precios     {:.3f}\n'.format(cova_m_ep))
            f.write('covarianza merito  - variables   {:.3f}\n'.format(cova_m_ev))
            f.write('covarianza merito  - diferencias {:.3f}\n'.format(cova_m_d))
            f.write('covarianza precios - variables   {:.3f}\n\n'.format(cova_ep_ev))

            f.write('xy;y0;10**y0;m;R2;p-value y0;p-value m\n')
            f.write('{:9s} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e}\n'.format('par m_ep' , res_m_ep.params[0], 10**res_m_ep.params[0], res_m_ep.params[1],res_m_ep.rsquared,res_m_ep.pvalues[0],res_m_ep.pvalues[1]))
            f.write('{:9s} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e}\n'.format('par m_ev' , res_m_ev.params[0], 10**res_m_ev.params[0], res_m_ev.params[1],res_m_ev.rsquared,res_m_ev.pvalues[0],res_m_ev.pvalues[1]))
            f.write('{:9s} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e}\n'.format('par m_ d' , res_m_d.params[0], 10**res_m_d.params[0], res_m_d.params[1],res_m_d.rsquared,res_m_d.pvalues[0],res_m_d.pvalues[1]))
            f.write('{:9s} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e} {:12.3e}\n'.format('par ep_ev', res_ep_ev.params[0], 10**res_ep_ev.params[0], res_ep_ev.params[1],res_ep_ev.rsquared,res_ep_ev.pvalues[0],res_ep_ev.pvalues[1]))

GraficoResumenPares(3, 3, g_log_m, g_log_ep  , gr_m_ep , SENDA_SALIDAS, 'resumen_m_ep'  , titulo)
GraficoResumenPares(3, 3, g_log_m, g_log_ev  , gr_m_ev , SENDA_SALIDAS, 'resumen_m_ev'  , titulo)
GraficoResumenPares(3, 3, g_log_m, g_log_d   , gr_m_d  , SENDA_SALIDAS, 'resumen_m_d'   , titulo)
GraficoResumenPares(3, 3, g_log_ep, g_log_ev , gr_ep_ev, SENDA_SALIDAS, 'resumen_ep_ev' , titulo)

imprime('fin')