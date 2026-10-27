import os
import sys
import glob
import numpy as np

FICHERO_LOG = 'C:/MEGA/BAT/gBAT.log'
def imprime(texto, rc=True):
    if type(texto) is not str:
        texto = str(texto)
    if rc:
        print(texto)
        with open(FICHERO_LOG, "a", encoding="utf-8") as log: log.write(texto + '\n')
    else:
        print(texto, end="")
        with open(FICHERO_LOG, "a", encoding="utf-8") as log: log.write(texto)

ancho = 22

add = []
nbs = []
dts = []
FI_SOL_LEE = 'parametros.txt'
with open(FI_SOL_LEE, "r", encoding="utf-8") as log:
    while True:
        s = log.readline()
        if not s:
            break
        if len(s) == 0 or s == '\n':
            continue
        if s[0] == '+':
            add.append(1)
            s = s[1:]
        else:
            add.append(0)
        i = s.index(' ')
        nb = s[:i]
        nbs.append(nb)
        dts.append(s[i + 1:-1])
n = len(nbs)
carpeta = input('carpeta: ')
patron  = carpeta + "/**/*.bat"
while(True):
    borrar = input('borrar ficheros antiguos (s/n): ')
    if borrar=='s' or borrar=='n':
        break
ficheros = glob.glob(patron, recursive=True)
for fi in ficheros:
    imprime(fi)
    e_nbs = []
    e_dts = []
    fi = fi.replace('\\','/')
    with open(fi, "r", encoding="utf-8") as ent:
        while True:
            s = ent.readline()
            if not s:
                break
            if len(s) == 0 or s == '\n':
                continue
            i = s.index(' ')
            nb = s[:i]
            e_nbs.append(nb)
            e_dts.append(s)
    e_n = len(e_nbs)
    imprime('sobran:')
    for nb, dt in zip(e_nbs, e_dts):
        try:
            i = nbs.index(nb)
        except:
            imprime('{}'.format(nb))
    imprime('---------------------------------------------------\n')
    i = fi.rindex('/')
    if borrar == 'n':
        os.rename(fi, fi[:i + 1] + "_"+ fi[i + 1:])
    sal = open(fi, "w", encoding="utf-8")
    # la cabecera del original
    for i in range(5):
        sal.write(e_dts[i])
    imprime('faltan:')
    # se repasa el patrón
    # los que no están en el patrón se omiten
    for ad, nb , dt in zip(add, nbs, dts):
        if ad == 1:
            # copia forzosa del patrón
            sf = nb.ljust(ancho, ' ') + dt + ' ^\n'
            sal.write(sf)
            imprime('+{}'.format(sf), False)
        else:
            try:
                # se copia el original
                i = e_nbs.index(nb)
                sal.write(e_dts[i])
            except Exception as err:
                # se copia el que falta
                sf = nb.ljust(ancho, ' ') + dt + ' ^\n'
                sal.write(sf)
                imprime('{}'.format(sf), False)
    # por si la última línea añadida terminaba en '^'
    sal.write('\n')
    # la línea final del original
    sal.write(e_dts[-1])
    sal.close()
    imprime('---------------------------------------------------\n')
imprime("")
imprime('fin')