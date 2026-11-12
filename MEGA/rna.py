import os

import sys
# Se requiere Python ≥3.5
assert sys.version_info >= (3, 5)

'''
# para que los caracteres escape que muestra el entrenamiento en pantalla se vean correctamente
# por contra, la salida impresa se verá mal

from colorama import just_fix_windows_console
just_fix_windows_console()
'''

import math
import numpy as np
import random
import matplotlib as mpl
from matplotlib import pyplot as plt
from timeit import default_timer as timer

import tensorflow as tf
tf.config.threading.set_inter_op_parallelism_threads(60)
tf.config.threading.set_intra_op_parallelism_threads(60)
# Se requiere TensorFlow ≥2.0
assert tf.__version__ >= "2.0"

import MEGA      as prin
import funciones as mfun

class calcula(object):

    # para aproximar la función de mérito mediante una Red Neuronal Densa

    def __init__(self, vec_opt, bnds):
        # Inicializar el generador de números aleatorios para numpy y tf
        np.random.seed(42)
        tf.random.set_seed(42)

#-------------------------------------------------------------------------------------------------------
# funciones
#-------------------------------------------------------------------------------------------------------
        def imprime(texto, rc=True):
            mfun.imprime(texto, rc)

        # Muestra un resumen del modelo de red y salva el gráfico de la misma
        def sumario(modelo, nombre=None):
            imprime("")
            stringlist = []
            modelo.summary(print_fn=lambda x: stringlist.append(x))
            resumen = "\n".join(stringlist)
            imprime(resumen)
            path = os.path.join(prin.SENDA_GRAFICOS, nombre + "_grafo.png")
            if nombre is not None:
                tf.keras.utils.plot_model(modelo, to_file=path, dpi = 300, show_shapes=True, show_layer_activations=True)
            imprime("")
            imprime("Guardada imagen: " + nombre + "_grafo.png")
            imprime("")

        # Dibuja las dos curvas de aprendizaje: la de entrenamiento y la de evaluación
        def plot_aprendizaje(loss, val_loss):
            # 'b' color blue '.-' puntos unidos por lí­neas

            plt.plot(np.arange(len(loss)) + 0.5, loss, "b.-", label="Error entrenamiento")
            # 'r' color red  '.-' puntos unidos por lí­neas
            # desplazada 0.5 respecto de la anterior para mejor visibilidad
            plt.plot(np.arange(len(val_loss)) + 1, val_loss, "r.-", label="Error validación")
            plt.gca().xaxis.set_major_locator(mpl.ticker.MaxNLocator(integer=True))
            plt.legend(fontsize=10)
            plt.xlabel("Epochs", fontsize=14)
            plt.ylabel("Error", fontsize=14)
            plt.grid(True)

        def plot_prediccion(real, pred, titulo):
            plt.plot(np.arange(len(real)) + 0.5, real, "bo", label="dato", markersize=1)
            if not (pred is None):
                plt.plot(np.arange(len(pred)) + 0.5, pred, "ro", label="predicción", markersize=1)
            plt.gca().xaxis.set_major_locator(mpl.ticker.MaxNLocator(integer=True))
            plt.legend(fontsize=10)
            plt.title(titulo, fontsize=14)
            plt.xlabel("n observación", fontsize=13)
            plt.ylabel("demérito", fontsize=13)
            plt.grid(True)

        # Salva el gráfico
        def salva_figura(fig_id, tight_layout=True, fig_extension="png", resolution=300):
            path = os.path.join(prin.SENDA_GRAFICOS, fig_id + "." + fig_extension)
            imprime("Guardada imagen: ", False)
            imprime(fig_id)
            if tight_layout:
                plt.tight_layout()
            plt.savefig(path, format=fig_extension, dpi=resolution)
            plt.close()

            # Aciertos en la tendencia
        
        def acierto(real, pred, margen):
            # nos basta con que sean del mismo orden de magnitud
            n = real.reshape(real.shape[0])
            d = pred.reshape(pred.shape[0])
            rela = abs(np.divide(n, d))
            inverso = 1. / margen
            coinciden = np.where(((rela > inverso) & (rela < margen)), 1, 0)
            return 100. * np.float64(np.sum(coinciden)) / np.float64(real.shape[0])

        def resultados(tit, nb_caso):
            ecme = modelo.evaluate(X_train, Y_train)
            ecmt = modelo.evaluate(X_test, Y_test)
            ecmv = modelo.evaluate(X_valid, Y_valid)

            imprime('ecm entrenar :{:14.5e}'.format(ecme))
            imprime('ecm test     :{:14.5e}'.format(ecmt))
            imprime('ecm validar  :{:14.5e}'.format(ecmv))
            imprime("")

            Y_pred  = modelo.predict(X_train)
            acto_e0 = acierto(Y_train, Y_pred, 1.1)
            acto_e1 = acierto(Y_train, Y_pred, 2)
            acto_e2 = acierto(Y_train, Y_pred, 5)
            acto_e3 = acierto(Y_train, Y_pred, 10)
            imprime("")
            imprime('muestra entrenar   media      des.estándar       mínimo         máximo')
            imprime('              -------------- -------------- -------------- --------------')
            imprime('DATOS         {:14.6e} {:14.6e} {:14.6e} {:14.6e}'.format(np.mean(Y_train), np.std(Y_train), np.min(Y_train), np.max(Y_train)))
            imprime('PREDICCION    {:14.6e} {:14.6e} {:14.6e} {:14.6e}'.format(np.mean(Y_pred),  np.std(Y_pred),  np.min(Y_pred),  np.max(Y_pred)))
            imprime('              -------------- -------------- -------------- --------------')
            imprime("")
            Y_pred  = modelo.predict(X_test)
            acto_t0 = acierto(Y_test, Y_pred, 1.1)
            acto_t1 = acierto(Y_test, Y_pred, 2)
            acto_t2 = acierto(Y_test, Y_pred, 5)
            acto_t3 = acierto(Y_test, Y_pred, 10)
            imprime("")
            imprime('muestra probar     media      des.estándar       mínimo         máximo')
            imprime('              -------------- -------------- -------------- --------------')
            imprime('DATOS         {:14.6e} {:14.6e} {:14.6e} {:14.6e}'.format(np.mean(Y_test), np.std(Y_test), np.min(Y_test), np.max(Y_test)))
            imprime('PREDICCION    {:14.6e} {:14.6e} {:14.6e} {:14.6e}'.format(np.mean(Y_pred),  np.std(Y_pred),  np.min(Y_pred),  np.max(Y_pred)))
            imprime('              -------------- -------------- -------------- --------------')
            imprime("")
            Y_pred  = modelo.predict(X_valid)
            acto_v0 = acierto(Y_valid, Y_pred, 1.1)
            acto_v1 = acierto(Y_valid, Y_pred, 2)
            acto_v2 = acierto(Y_valid, Y_pred, 5)
            acto_v3 = acierto(Y_valid, Y_pred, 10)
            imprime('muestra validar    media      des.estándar       mínimo         máximo')
            imprime('              -------------- -------------- -------------- --------------')
            imprime('DATOS         {:14.6e} {:14.6e} {:14.6e} {:14.6e}'.format(np.mean(Y_valid), np.std(Y_valid), np.min(Y_valid), np.max(Y_valid)))
            imprime('PREDICCION    {:14.6e} {:14.6e} {:14.6e} {:14.6e}'.format(np.mean(Y_pred),  np.std(Y_pred),  np.min(Y_pred),  np.max(Y_pred)))
            imprime('              -------------- -------------- -------------- --------------')
            imprime("")
            imprime('número de veces        1.1       2        5       10')
            imprime('                    -------- -------- -------- --------')
            imprime('% acierto entrenar :{:8.2f} {:8.2f} {:8.2f} {:8.2f}'.format(acto_e0, acto_e1, acto_e2, acto_e3))
            imprime('% acierto test     :{:8.2f} {:8.2f} {:8.2f} {:8.2f}'.format(acto_t0, acto_t1, acto_t2, acto_t3))
            imprime('% acierto validar  :{:8.2f} {:8.2f} {:8.2f} {:8.2f}'.format(acto_v0, acto_v1, acto_v2, acto_v3))
            imprime('                    -------- -------- -------- --------')
            # Dibujamos las curvas de aprendizaje
            plot_aprendizaje(historia.history["loss"], historia.history["val_loss"])
            salva_figura(tit + "_ev_" + nb_caso)
            plot_prediccion(Y_valid, Y_pred, 'predicciones para la muestra de validación')
            salva_figura(tit + "_rpv_" + nb_caso)
            vali = np.zeros(Y_valid.shape[0], dtype=np.float64)
            pred = np.zeros(Y_pred.shape[0], dtype=np.float64)
            for i in range(Y_valid.shape[0]):
                vali[i] = math.log10(Y_valid[i])
                pred[i] = math.log10(Y_pred[i][0])
            plot_prediccion(vali, pred, 'Log de las predicciones para la muestra de validación')
            salva_figura(tit + "_rpv_log_" + nb_caso)
#-------------------------------------------------------------------------------------------------------
# fin funciones
#-------------------------------------------------------------------------------------------------------

        carpeta_modelos = 'C:/MEGA/Modelos/'
        os.makedirs(carpeta_modelos, exist_ok=True)  # crear el directorio si no existe
        nvec = len(vec_opt)

        # Fracciones de las muestras
        f_train           = 0.7
        f_valid           = 0.2

        CONV = True
        DENS = True

        n_observaciones   = 20000
        frac_uni_var      = -1.0
        factor_dispersion = 1.0e-08
        log_merito        = False

        observacion = np.zeros((n_observaciones, nvec, 1), dtype=np.float64)
        valor       = np.zeros((n_observaciones), dtype=np.float64)
        for j in range(nvec):
            observacion[0, j, 0] = vec_opt[j]
        if log_merito:
            valor[0] = math.log10(prin.fo(observacion[0, :, 0]))
        else:
            valor[0] = prin.fo(observacion[0, :, 0])
        imax = -1
        vmax = valor[0]
        for i in range (1,n_observaciones):
            if frac_uni_var < 0:
                cuantas = nvec
            else:
                for k in range(nvec):
                    observacion[i, k, 0] = vec_opt[k];
                a = random.uniform(0, 1)
                if a < frac_uni_var:
                    cuantas = 1
                else:
                    cuantas = int(random.uniform(0, nvec))
            for k in range(cuantas):
                if frac_uni_var < 0:
                    j = k
                else:
                    j = int(random.uniform(0, nvec-1))
                if bnds[j][0] == bnds[j][1]:
                    observacion[i, j, 0] = bnds[j][0]
                else:
                    semi_izq = vec_opt[j] - bnds[j][0]
                    semi_dch = bnds[j][1] - vec_opt[j]
                    if semi_izq < semi_dch:
                        semi_intervalo = semi_izq
                    else:
                        semi_intervalo = semi_dch
                    f = (semi_izq + semi_dch) / (2. * semi_intervalo);
                    a = random.uniform(0, 1)
                    if j < prin.npre_sol:
                        # multiplicamos por 100 porque los precios son varios ordenes de magnitud inferiores al resto de variables
                        desplazamiento = 100.* f * factor_dispersion * a * semi_intervalo;
                    else:
                        desplazamiento = f * factor_dispersion * a * semi_intervalo;
                    a = random.uniform(0, 1)
                    if a < 0.5:
                        v = vec_opt[j] - desplazamiento;
                    else:
                        v = vec_opt[j] + desplazamiento;
                    if v < bnds[j][0]:
                        v = bnds[j][0] + 0.000001;
                    elif v > bnds[j][1]:
                        v = bnds[j][1] - 0.000001;
                    observacion[i, j, 0] = v;
            if log_merito:
                valor[i] = math.log10(prin.fo(observacion[i, :, 0]))
            else:
                valor[i] = prin.fo(observacion[i, :, 0])
            if valor[i] > vmax:
                imax = i
                vmax = valor[i]
        
        plot_prediccion(valor, None, 'observaciones')
        salva_figura('OBS')

        imprime('ECT vec_opt :       {:14.5e}'.format(np.min(valor[0])))
        imprime('ECT mínimo  :       {:14.5e}'.format(np.min(valor)))
        imprime('ECT máximo  :{:6d} {:14.5e}\n'.format(imax, vmax))
        imprime("Diferencia con el valor de la variable en el equilibrio inicial")
        for j in range(nvec):
            if j % 10 == 0:
                imprime("")
            imprime(' {:9.2e}'.format(observacion[imax, j, 0] - vec_opt[j]), False)
        imprime("\n")

        n70 = int(n_observaciones * f_train)
        n90 = int(n_observaciones * (f_train + f_valid))

        X_train = observacion[0:n70]
        X_valid = observacion[n70:n90]
        X_test = observacion[n90:]

        Y_train = valor[0:n70]
        Y_valid = valor[n70:n90]
        Y_test = valor[n90:]

        imprime('Número de observaciones     : {:12d} x {:5d}'.format(n_observaciones, nvec))
        imprime('  entrenar                  : {:12d}'.format(X_train.shape[0]))
        imprime('  validar                   : {:12d}'.format(X_valid.shape[0]))
        imprime('  probar                    : {:12d}'.format(X_test.shape[0]))
        imprime('Fracción variaciones únicas : {:12.3e}'.format(frac_uni_var))
        imprime('Factor de dispersión        : {:12.3e}'.format(factor_dispersion))

#-------------------------------------------------------------------------------------------------------
# Red neuronal convolucional
#-------------------------------------------------------------------------------------------------------
        if CONV:
            imprime("")
            imprime("-------------------------------------------------------------------------------------------------------")
            imprime("Red neuronal convolucional")
            imprime("-------------------------------------------------------------------------------------------------------")
            imprime("")

            tpo_inicial = timer()

            pases    = 300
            filtros  = 25
            marco    = 6
            desliza  = 1
            reductor = 1
            act1     = 'tanh'

            nb_caso = '{:s}_{:d}_{:7.1e}_{:5.2f}_{:s}_{:d}_{:d}_{:d}_{:d}_{:d}'.format(act1, n_observaciones, factor_dispersion, frac_uni_var, 'log' if log_merito else 'val', filtros, marco,desliza, reductor, pases)

            imprime("Filtros    {:5}".format(filtros))
            imprime("Marco      {:5}".format(marco))
            imprime("Desliza    {:5}".format(desliza))
            imprime("Reductor   {:5}".format(reductor))
            imprime("Activación {:s}".format(act1))
            imprime("")
            imprime("Pases      {:5}".format(pases))
            imprime("")

            modelo = tf.keras.models.Sequential(
                [
                    tf.keras.layers.Conv1D(
                        input_shape=(nvec, 1),
                        filters=filtros,
                        kernel_size=marco,
                        strides=desliza,
                        padding="valid",
                        activation=act1
                    ),
                    tf.keras.layers.MaxPooling1D(pool_size=reductor),
                    tf.keras.layers.Flatten(),
                    tf.keras.layers.Dense(1),
                ]
            )
            modelo.compile(loss="mse", optimizer="adam")
            sumario(modelo, "C1D_" + nb_caso)

            senda_checkpoint = carpeta_modelos + "C1D.weights.h5"
            checkpoint = tf.keras.callbacks.ModelCheckpoint(
                senda_checkpoint,
                monitor="val_loss",
                verbose=1,
                save_best_only=True,
                mode="min",
                save_weights_only=True
            )
            callbacks_list = [checkpoint]
            historia = modelo.fit(
                X_train,
                Y_train,
                epochs=pases,
                batch_size=32,
                validation_data=(X_valid, Y_valid),
                callbacks=callbacks_list,
            )
            # Cargar los pesos del mejor modelo encontrado.
            try:
                modelo.load_weights(senda_checkpoint)
            except:
                imprime("No se cargaron los pesos del mejor modelo encontrado. Probablemente no se encontró")
                imprime("")

            # Salvar el modelo
            fichero_modelo = carpeta_modelos + "C1D.h5"
            modelo.save(fichero_modelo)

            tpo_actual = timer()
            imprime("Tiempo  :{:11,.0f} s".format(tpo_actual - tpo_inicial))
            imprime("")
            resultados('RNC', nb_caso)

#-------------------------------------------------------------------------------------------------------
# Red neuronal densa
#-------------------------------------------------------------------------------------------------------
        if DENS:
            imprime("")
            imprime("-------------------------------------------------------------------------------------------------------")
            imprime("Red neuronal densa")
            imprime("-------------------------------------------------------------------------------------------------------")
            imprime("")

            pases = 1000
            nn1   = nvec * 2
            nn2   = nvec * 2
            nn3   = nvec * 2
            nn4   = nvec * 2
            act1  = 'tanh'
            act2  = 'tanh'
            act3  = 'tanh'
            act4  = 'tanh'

            ncapas = 1
            if nn1 > 0:
                imprime("Capa {:1d}: {:5} {:s}".format(ncapas, nn1, act1))
                ncapas += 1
            if nn2 > 0:
                imprime("Capa {:1d}: {:5} {:s}".format(ncapas, nn2, act2))
                ncapas += 1
            if nn3 > 0:
                imprime("Capa {:1d}: {:5} {:s}".format(ncapas, nn3, act3))
                ncapas += 1
            if nn4 > 0:
                imprime("Capa {:1d}: {:5} {:s}".format(ncapas, nn4, act4))
                ncapas += 1
            if ncapas == 1:
                imprime("Mérito = combinación lineal de las variables")
            imprime("")
            imprime("Pases    {:5}".format(pases))
            imprime("")

            tpo_inicial = timer()

            nb_caso = '{:d}_{:d}_{:d}_{:d}_{:s}_{:s}_{:s}_{:s}_{:d}_{:7.1e}_{:5.2f}_{:s}_{:d}'.format(nn1, nn2, nn3, nn4, act1, act2, act3, act4, n_observaciones, factor_dispersion, frac_uni_var, 'log' if log_merito else 'val', pases)

            modelo = tf.keras.models.Sequential()
            modelo.add(tf.keras.layers.Flatten(input_shape=[nvec, 1]))
            if nn1 > 0: modelo.add(tf.keras.layers.Dense(nn1, activation=act1))
            if nn2 > 0: modelo.add(tf.keras.layers.Dense(nn2, activation=act2))
            if nn3 > 0: modelo.add(tf.keras.layers.Dense(nn3, activation=act3))
            if nn4 > 0: modelo.add(tf.keras.layers.Dense(nn4, activation=act4))
            modelo.add(tf.keras.layers.Dense(1,   activation='linear'))

            modelo.compile(loss="mse", optimizer="adam")
            sumario(modelo, "RND_" + nb_caso)

            senda_checkpoint = carpeta_modelos + "RND.weights.h5"
            checkpoint = tf.keras.callbacks.ModelCheckpoint(
                senda_checkpoint,
                monitor="val_loss",
                verbose=1,
                save_best_only=True,
                mode="min",
                save_weights_only=True,
            )
            callbacks_list = [checkpoint]
            historia = modelo.fit(
                X_train,
                Y_train,
                epochs=pases,
                batch_size=32,
                validation_data=(X_valid, Y_valid),
                callbacks=callbacks_list,
            )
            # Cargar los pesos del mejor modelo encontrado.
            try:
                modelo.load_weights(senda_checkpoint)
            except:
                imprime("No se cargaron los pesos del mejor modelo encontrado. Probablemente no se encontró\n")

            # Salvar el modelo
            fichero_modelo = carpeta_modelos + "RND.h5"
            modelo.save(fichero_modelo)

            tpo_actual = timer()
            imprime("Tiempo  :{:11,.0f} s".format(tpo_actual - tpo_inicial))
            imprime("")

            resultados('RND', nb_caso)

            if ncapas == 1:
                imax = -1
                imin = -1
                vmax = -1.
                vmin = 1.0e+10
                pesos = modelo.layers[1].get_weights()[0]
                sesgo = modelo.layers[1].get_weights()[1].item()
                imprime('sesgo {:14.6e} '.format(sesgo))
                imprime("pesos:", False)
                for j in range(nvec):
                    if j % 10 == 0:
                        imprime("")
                    v = pesos[j].item()
                    if v < vmin:
                        imin = j
                        vmin = v
                    if v > vmax:
                        imax = j
                        vmax = v
                    imprime(' {:10.3e}'.format(v), False)
                imprime("\n")
                imprime('mínimo {:4d} {:12.5e}'.format(imin, vmin))
                imprime('máximo {:4d} {:12.5e}'.format(imax, vmax))
                imprime("")


print('\nfin.\n')
