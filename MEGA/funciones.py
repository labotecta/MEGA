import argparse

def ini(fichero):
    global FICHERO_LOG
    FICHERO_LOG = fichero

def imprime(texto, rc=True):
    if type(texto) is not str:
        texto = str(texto)
    if rc:
        print(texto)
        with open(FICHERO_LOG, "a", encoding="utf-8") as log: log.write(texto + '\n')
    else:
        print(texto, end='')
        with open(FICHERO_LOG, "a", encoding="utf-8") as log: log.write(texto)

def i_tabla(rot, cab, etq, valores, pie, DECIMALES=6):
    if rot == '/':
        rot = ' '
    if rot != '':
        imprime('{:12}'.format(rot), False)
    if len(cab) > 0:
        ncols = len(cab)
        for j in range(ncols):
            imprime(' {:>12}'.format(cab[j]), False)
        imprime('')
        if rot != '':
            imprime('{:12}'.format(''), False)
        for j in range(ncols):
            imprime(' ------------', False)
        imprime('')
    if type(valores) is float:
        n = 0
    else:
        n = len(valores.shape)
    if n == 0:
        # escalar
        if len(etq) > 0:
            imprime('{:12}'.format(etq[0]), False)
        else:
            imprime('{:12}'.format(''), False)
        imprime(' {:12.{prec}f}'.format(valores, prec=DECIMALES))
    elif n == 1:
        # vector
        ncols = valores.shape[0]
        if len(etq) > 0:
            imprime('{:12}'.format(etq[0]), False)
        else:
            if rot != '':
                imprime('{:12}'.format(''), False)
        suma = 0.
        for j in range (ncols):
            suma += valores[j]
            imprime(' {:12.{prec}f}'.format(valores[j], prec=DECIMALES), False)
        if ncols > 1:
            imprime(' S={:12.{prec}f}'.format(suma, prec=DECIMALES), False)
        imprime('')
    else:
        # matriz 2D
        nfils = valores.shape[0]
        ncols = valores.shape[1]
        for i in range (nfils):
            if len(etq) > 0:
                imprime('{:12}'.format(etq[i]), False)
            else:
                if rot != '':
                    imprime('{:12}'.format(''), False)
            suma = 0.
            for j in range (ncols):
                suma += valores[i,j]
                imprime(' {:12.{prec}f}'.format(valores[i,j], prec=DECIMALES), False)
            if ncols > 1:
                imprime(' S={:12.{prec}f}'.format(suma, prec=DECIMALES), False)
            imprime('')
    if pie:
        i_pie(rot, cab)

def i_pie(rot, cab):
    if rot == '/':
        rot = ' '
    if rot != '':
        imprime('{:12}'.format(''), False)
    if len(cab) > 0:
        ncols = len(cab)
        for j in range(ncols):
            imprime(' ------------', False)
        imprime('')

def cabecera(rot, etq):
    imprime('{:10}'.format(rot), False)
    ncols = len(etq)
    for j in range(ncols):
        imprime(' {:>11}'.format(etq[j]), False)
    imprime('')
    imprime('----------', False)
    for j in range(ncols):
        imprime(' -----------', False)
    imprime('')

def cuerpo(vector, DECIMALES=6):
    imprime('          ', False)
    for j in range(len(vector)):
        imprime(' {:9.{prec}f}'.format(vector[j], prec=DECIMALES), False)
    imprime('')

def cuerpo2D(etq, vector, DECIMALES=7):
    if len(vector.shape) == 1:
        nfils = 1
        ncols = vector.shape[0]
        vector = vector.reshape(1, ncols)
    else:
        nfils = vector.shape[0]
        ncols = vector.shape[1]
    for i in range(nfils):
        imprime('{:10}'.format(etq[i]), False)
        for j in range(ncols):
            imprime(' {:11.{prec}f}'.format(vector[i,j], prec=DECIMALES), False)
        imprime('')

def cierre(etq):
    imprime('{:10}'.format(''), False)
    for j in range(len(etq)):
        imprime(' -----------', False)
    imprime('')

def tabla_1D(etq, valores, DECIMALES=6):
    for i in range(len(valores)):
        imprime('{:10} {:9.{prec}f} '.format(etq[i], valores[i], prec=DECIMALES))

def tabla_1Dl(etq, valores_a, valores_b, DECIMALES=7):
    for i in range(len(valores_a)):
        imprime('{:10} {:11.{prec}f}  {:11.{prec}f} '.format(etq[i], valores_a[i], valores_b[i], prec=DECIMALES))

def tabla_2D(etq, valores, DECIMALES=6):
    if len(valores.shape) == 0:
        imprime('{:10} '.format(etq[0]), False)
        imprime('{:9.{prec}f} '.format(valores, prec=DECIMALES))
    if len(valores.shape) == 1:
        cols = valores.shape[0]
        imprime('{:10} '.format(etq[0]), False)
        for j in range(cols):
            imprime('{:9.{prec}f} '.format(valores[j], prec=DECIMALES), False)
        imprime('')
    else:
        filas = valores.shape[0]
        cols = valores.shape[1]
        for i in range(filas):
            imprime('{:10} '.format(etq[i]), False)
            for j in range(cols):
                imprime('{:9.{prec}f} '.format(valores[i,j], prec=DECIMALES), False)
            imprime('')

def tabla_2De(etq, valores, DECIMALES=2):
    if len(valores.shape) == 0:
        imprime('{:10} '.format(etq[0]), False)
        imprime('{:9.{prec}e} '.format(valores, prec=DECIMALES))
    elif len(valores.shape) == 1:
        cols = valores.shape[0]
        imprime('{:10} '.format(etq[0]), False)
        for j in range(cols):
            imprime('{:9.{prec}e} '.format(valores[j], prec=DECIMALES), False)
        imprime('')
    else:
        filas = valores.shape[0]
        cols = valores.shape[1]
        for i in range(filas):
            imprime('{:10} '.format(etq[i]), False)
            for j in range(cols):
                imprime('{:9.{prec}e} '.format(valores[i,j], prec=DECIMALES), False)
            imprime('')


