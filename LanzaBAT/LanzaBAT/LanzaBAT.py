import os
import sys
import glob
import subprocess

FICHERO_LOG = 'C:/MEGA/BAT/LanzaBAT.log'
def imprime(texto, rc=True):
    if type(texto) is not str:
        texto = str(texto)
    if rc:
        print(texto)
        with open(FICHERO_LOG, "a", encoding="utf-8") as log: log.write(texto + '\n')
    else:
        print(texto, end='')
        with open(FICHERO_LOG, "a", encoding="utf-8") as log: log.write(texto)

carpeta = input('carpeta: ')
if os.path.exists(FICHERO_LOG):
    os.remove(FICHERO_LOG)
FICHERO_LOG = carpeta + '/_LanzaBAT.log'
if os.path.exists(FICHERO_LOG):
    os.remove(FICHERO_LOG)
patron  = carpeta + "/**/*.bat"
ficheros = glob.glob(patron, recursive=True)
n = 0
for fi in ficheros:
    n += 1
    if fi.lower().endswith('_borra.bat'):
        # de cierres anteriores, se borra
        os.remove(fi)
        continue
    imprime('{:4d} de {:4d} {}'.format(n, len(ficheros), fi))
    fi_c = fi.replace('\\','/')[:-4] + '_borra.bat'
    sal = open(fi_c, "w", encoding="utf-8")
    with open(fi, "r", encoding="utf-8") as ent:
        while True:
            s = ent.readline()
            if not s:
                break
            if len(s) == 0 or s == '\n':
                continue
            i = s.index(' ')
            nb = s[:i]
            if nb.upper() != 'TIMEOUT':
                sal.write(s)
    sal.close()
    try:
        r = subprocess.check_call([fi_c])
        if r != 0:
            imprime('Error en {}'.format(fi))
            sys.exit(1)
    except subprocess.CalledProcessError:
        imprime('Error en {}'.format(fi))
        sys.exit(1)
    if os.path.exists(fi_c):
        os.remove(fi_c)
imprime('')
imprime('Fin')
imprime('')
