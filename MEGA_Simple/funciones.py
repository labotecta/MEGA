import ecuaciones_simple as simple

def ini(fichero):
    global FICHERO_LOG
    FICHERO_LOG = fichero

def imprime(texto, rc=True):
    if rc:
        print(texto)
        with open(FICHERO_LOG, "a", encoding="utf-8") as log: log.write(texto + '\n')
    else:
        print(texto, end='')
        with open(FICHERO_LOG, "a", encoding="utf-8") as log: log.write(texto)

def tabla_1D(etq, p):
    for i in range(len(p)):
        imprime('{:10} {:9.5f} '.format(etq[i], p[i]))

def tabla_2D(etq, w):
    ncon = w.shape[0]
    npro = w.shape[1]
    for i in range(ncon):
        imprime('{:10} '.format(etq[i]), False)
        for j in range(npro):
            imprime('{:8.4f} '.format(w[i,j]), False)
        imprime('')

def resultados_demanda(FICHERO_LOG, alfa, pp, dp, pf, wf, nombre_con='', nombre_pro=''):
    '''
    FICHERO_LOG: fichero de resultados
    alfa: coeficientes de la función de utilidad
    pp: precio de los productos
    dp: demanda de productos
    para el cálculo de los ingreso (renta)
        pf: precio de los factores
        wf: cantidad de factores vendidos
    nombre_con=''
    nombre_pro=''
    '''
    ncon = dp.shape[0]  # número de consumidores
    npro = dp.shape[1]  # número de productos
    # ingresos disponibles por el total de consumidores, un escalar que para un solo consumidor se puede calcular de dos
    # formas ya que la renta debe ser igual a sus compras
    renta = wf.dot(pf)  # por la venta de factores
    coste = dp.dot(pp)  # por las compras de productos

    if len(nombre_con) == 0:
        nombre_con = []
        for j in range(ncon):
            nombre_con.append(str(j+1))
    if len(nombre_pro) == 0:
        nombre_pro = []
        for j in range(npro):
            nombre_pro.append(str(j+1))
    
    imprime('Precio productos             ', False)
    for j in range(npro):
        imprime('{:>8} '.format(nombre_pro[j]), False)
    imprime('')
    imprime('                             ', False)
    for j in range(npro):
        imprime('-------- ', False)
    imprime('')
    imprime('                             ', False)
    for j in range(npro):
        imprime('{:8.3f} '.format(pp[j][0]), False)
    imprime('')
    imprime('Consumidor    renta    coste ', False)
    for j in range(npro):
        imprime('{:>8} '.format(nombre_pro[j]), False)
    imprime('utilidad')
    imprime('           -------- -------- ', False)
    for j in range(npro):
        imprime('-------- ', False)
    imprime('--------')
    for i in range(ncon):
        imprime('{:10}          {:8.2f} '.format(nombre_con[i], coste[i][0]), False)
        for j in range(npro):
            imprime('{:8.2f} '.format(dp[i,j]), False)
        u = simple.utilidad_CobbDouglas(dp[i], alfa[i])        
        imprime('{:8.3f}'.format(u))
    imprime('           -------- -------- ', False)
    for j in range(npro):
        imprime('-------- ', False)
    imprime('--------')
    imprime('           {:8.2f}'.format(renta[0][0]))
    imprime('')

def resultados_produccion(FICHERO_LOG, beta, pp, wp, pf, wf, nombre_sector='', nombre_factor=''):
    '''
    FICHERO_LOG: fichero de resultados
    beta: coeficientes de la función de utilidad
    ingresos
        pp: precio de los productos
        op: oferta de productos
    para el cálculo de los costes
        pf: precio de los factores
        wf: cantidad de factores demandados
    nombre_sector=''
    nombre_factor=''
    '''
    nsec = wf.shape[0]  # número de sectores
    nfac = wf.shape[1]  # número de factores
    npro = len(pp)      # número de productos
    renta = simple.ingreso_sectores(pp, wp)                # a través de las compras de los consumidores
    coste = simple.coste_factores_por_sectores(pf, wf)     # a traves de la utilización por cada sector y el precio de los factores

    #renta = wp.dot(pp)     # ingresos disponibles de cada sector por la venta de productos
    #coste = wf.dot(pf)      # coste por el consumo de factores de cada sector, que debe ser igual al ingreso
    if len(nombre_sector) == 0:
        nombre_sector = []
        for j in range(nsec):
            nombre_sector.append(str(j+1))
    if len(nombre_factor) == 0:
        nombre_factor = []
        for j in range(nfac):
            nombre_factor.append(str(j+1))
    imprime('Precio factores              ', False)
    for j in range(nfac):
        imprime('{:>8} '.format(nombre_factor[j]), False)
    imprime('')
    imprime('                             ', False)
    for j in range(nfac):
        imprime('-------- ', False)
    imprime('')
    imprime('                             ', False)
    for j in range(nfac):
        imprime('{:8.3f} '.format(pf[j][0]), False)
    imprime('')
    imprime('Sector        renta    coste ', False)
    for j in range(nfac):
        imprime('{:>8} '.format(nombre_factor[j]), False)
    imprime('utilidad')
    imprime('           -------- -------- ', False)
    for j in range(nfac):
        imprime('-------- ', False)
    imprime('--------')
    for i in range(nsec):
        imprime('{:10} {:8.2f} {:8.2f} '.format(nombre_sector[i], renta[i], coste[i]), False)
        for j in range(nfac):
            imprime('{:8.2f} '.format(wf[i,j]), False)
        u = simple.utilidad_CobbDouglas(wf[i], beta[i], 1.)    # coeficiente de escala a 1.        
        imprime('{:8.3f}'.format(u))
    imprime('           -------- -------- ', False)
    for j in range(nfac):
        imprime('-------- ', False)
    imprime('--------')
    imprime('')


