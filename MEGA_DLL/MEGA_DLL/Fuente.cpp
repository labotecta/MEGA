#include "pch.h"
#include "Mega.h"
#include <algorithm>
#include <cstdlib>
#include <cmath>
#include <Windows.h>
#include <random>
#include <cstdio>
#include <malloc.h>
#include <process.h>
#include <chrono>
#include <ctime>
#include <share.h>
#include <csignal>
//#include <stdio.h>
//#include <sys\timeb.h> 
using namespace std;
/*
para poder usar matrices de tamaño fijo, que es lo más eficiente y cómodo, NFAC, MDEM y NSEC deben ser constantes
lo que significa que si cambian en el modelo, hay que cambiar la DLL y recompilarla, pero es preferible al uso de
matrices dinámicas, con mucha diferencia.
*/

/*
estas tres estructuras 'globales' recibirán las opciones, datos y parámetros que necesita la función objetivo
a través de las funciones correspondientes para no tener que enviarlas a cada llamada a la función objetivo
*/
OPCIONES   op;
DATOS      datos;
PARAMETROS parametros;
/*
// no parece que ahorre tiempo, más bien al contrario
int ndc_ax;
int dc_ax[NSEC * NSEC][2]{};	// índices i,j de los elementos de ax distintos de cero
*/

const int HISTO_MAX = 201;
int histogenera[HISTO_MAX]{};
double histograma[HISTO_MAX]{};
int histo_n;
/*
'me_sol' concatena los valores de todas las variables de la solución (no solo del vector de prueba) para que la función 'solucioma' del algoritmo
genético la devuelva despues de llamar a 'merito_sol' que es quien la carga. 'merito_sol' no es adecuada para multiproceso, pero no hay problema porque solo se
la llama una vez terminado el algoritmo genético. Se podría eliminar porque lo realmente útil es la variable 'VEC_OPT_E'.
		1 resultado
		1 número de datos
		1 intentos
		1 generaciones
		1 mérito
	 NFAC pf
	 NSEC py
	 NSEC pq
	 NSEC pd
		1 epsilon
		1 Apz
NSEC*NFAC Fi
	 NSEC Ei
	 NSEC Mi
	 NSEC Di

NDEM*NSEC Xpi

	 NSEC pz
	 NSEC pe
	 NSEC pm
	 NSEC Yp
	 NSEC Z
	 NSEC Xg
	 NSEC Xv
	 NSEC Q
	 NDEM Td
	 NSEC Tz
	 NSEC Tm
	 NDEM Sp
	 NSEC AgE
	 NDEM AgH
	 NSEC CssE
	 NDEM CssH
		1 Sg
		1 Sc
		1 ebp
NDEM*NSEC Xp
NDEM*NFAC FF
NDEM*NFAC Alp
NSEC*NSEC X
*/
const int LVAR =
1 +
1 +
1 +
1 +
1 +
NFAC +
NSEC +
NSEC +
NSEC +
1 +
1 +
NSEC * NFAC +
NSEC +
NSEC +
NSEC +
NDEM * NSEC +

NSEC +
NSEC +
NSEC +
NSEC * NFAC +
NSEC +
NSEC +
NSEC +
NSEC +
NSEC +
NSEC +
NSEC +
NSEC +
NSEC +
NSEC +
NDEM +
NSEC +
NSEC +
NDEM +
NSEC +
NDEM +
NSEC +
NDEM +
1 +
1 +
1 +
1 +
NDEM * NSEC +
NDEM * NFAC +
NDEM * NFAC +
NSEC * NSEC +

NSEC * NFAC +
NSEC +
NSEC +
NSEC +
NSEC +
NSEC +
NSEC +
NSEC +
NSEC +
NSEC +
NSEC +
NSEC +
NSEC +
NSEC +
NDEM +
NSEC +
NSEC +
NDEM +
NSEC +
NDEM +
NSEC +
NDEM +
1 +
1 +
1 +
1 +
NDEM * NSEC +
NDEM * NFAC +
NDEM * NFAC +
NSEC * NSEC
;

double me_sol[LVAR]{};

/*
'VEC_OPT_E' igual que 'me_sol' pero solo guarda el vector solución, que es lo realmente útil ya que valor del resto
de las variables se puede obtener a partir del vector solución mediante las ecuaciones del modelo
*/
const int LVSOL =
1 +
1 +
1 +
1 +
1 +
NFAC +
NSEC +
NSEC +
NSEC +
1 +
1 +
NSEC * NFAC +
NSEC +
NSEC +
NSEC +
NDEM * NSEC +
64 +
2 * HISTO_MAX
;

double VEC_OPT_E[LVSOL]{};

const int MAX_DESVIOS = 256;
double desvios[MAX_DESVIOS];

#pragma region Genetico

/*
convertimos en matrices (vectores) las variables que cada hilo debe
utilizar de forma independiente de los otros hilos para evitar que colisionen.
para usar matrices fijas definimos la constante MAX_HILOS en 128 y aunque desperdiciemos
memoria, es insignificante
*/
int n_hilos;
const int MAX_HILOS = 128;
HANDLE hilos[MAX_HILOS]{};
HANDLE semaforo_hilo[MAX_HILOS]{};
HANDLE semaforo_itera;
mt19937 hgen[MAX_HILOS]{};
uniform_int_distribution<int> hdis_entero[MAX_HILOS]{};
uniform_int_distribution<int> hdis_entero_ivec[MAX_HILOS]{};
uniform_real_distribution<double> hdis_double[MAX_HILOS]{};
bool invalida_hilos[MAX_HILOS]{};
CRITICAL_SECTION seccion_fin_hilos;
int hilos_terminados;
bool CANCELADO;

double** cotas = NULL;
int* fijo = NULL;
double** poblacion = NULL;
double* merito_individuo = NULL;
double* factible = NULL;
double** descendiente = NULL;

const int MAX_VEC = 1000;
double vec_ini[MAX_VEC];

bool CANCELAR;
int ind_mejor_merito;
double mejor_merito;
double mejor_merito_anterior;
int generacion;
int res_Simulacion;
/*
parametros para particularizar el algoritmo genético
*/
int NPOB;
int max_intentos;
int intentos;
int max_generaciones;
int modo_poblacion_inicial;
double factor_inicio;
double sigma_inicio;
int num_tramos_lhs;
double factor_mutacion;
double recombinacion[2]{};
double cte_recombinacion;
double tolerancia;
double tol_aceptable;
int generaciones_control_progreso;
double min_progreso;
int histo_int;
int histo_sol;
bool control_factibilidad;
int semilla;
bool poner_el_mejor_primero;
bool incluir_x0;
int NVEC;
int id_salida;
FILE* salida;
FILE* sal_sol;

mt19937 gen;
uniform_real_distribution<double> dis_double(0.0, 1.0);
uniform_int_distribution<int> dis_entero{};
/*
esta es la función que hay que llamar para que se ejecute el algoritmo genético, previamente hay que llamar
a:
	recibe_opciones
	recibe_datos
	recibe_parametros
que aportan los datos que se necesitan para la función objetivo

los parámetros del algoritmo genético ya los recibe 'soluciona' en sus propios parámetros

si 'extendida' es igual a 0, 'soluciona' devuelve el vector solución, si es igual a 1, devuelve todas las
variables del modelo, esto último carece de utilidad, es preferible que quien llama a la DLL calcule
las variables a partir del vector solución aplicando las ecuaciones del modelo.
*/
void cancelar(int sig)
{
	CANCELAR = true;
}
double* soluciona(double* par, double* cotasInf, double* cotasSup, double* vec, int extendida) {
	CANCELAR = false;

	// capurar la señal Ctrl+C
	signal(SIGINT, &cancelar);
	/*
	// dar la máxima prioridad al proceso
	// ABOVE_NORMAL_PRIORITY_CLASS es menos crítica
	SetPriorityClass(GetCurrentProcess(), HIGH_PRIORITY_CLASS);
	*/

	int res = parametros_alge(par);
	if (res != 0) {
		// Error en los parametros recibidos
		if (extendida == 1) {
			me_sol[0] = -7;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -7;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			return VEC_OPT_E;
		}
	}
	char fichero[128];
	sprintf_s(fichero, 127, "C:/MEGA/Salidas/saDLL_%d_%d_%d.log", id_salida, modo_poblacion_inicial, semilla);
	salida = _fsopen(fichero, "w", _SH_DENYWR);
	if (salida == 0) {
		if (extendida == 1) {
			me_sol[0] = -9;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -9;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			return VEC_OPT_E;
		}
	}
	auto t_inicio = chrono::system_clock::now();
	auto inicio = chrono::system_clock::to_time_t(t_inicio);
	char tmBuff[30];
	ctime_s(tmBuff, sizeof(tmBuff), &inicio);
	fprintf(salida, "inicio: %s\n\n", tmBuff);
	fprintf(salida, "Modo población: %6d\n", modo_poblacion_inicial);
	fprintf(salida, "Población     : %6d\n", NPOB);
	fprintf(salida, "Variables     : %6d\n", NVEC);
	fprintf(salida, "Intentos      : %6d\n", intentos);
	fprintf(salida, "Semilla       : %6d\n", semilla);
	fflush(salida);
	/*
	// la comprobación de si esto ahorra tiempo de cálculo, o todo lo contrario, resulta incoherente

	fprintf(salida, "pares de 'ax'                  %d\n", NSEC * NSEC);
	fprintf(salida, "pares de 'ax' distinto de cero %d\n\n", ndc_ax);
	fflush(salida);
	struct timeb start, end;
	int diff;
	double Z[NSEC]{ 10000 };
	ftime(&start);
	for (long long i = 0LL; i < 100LL; i++) {
		for (long long j = 0LL; j < 1000000LL; j++) {
			double X[NSEC][NSEC]{};
			consumo_intermedio_op_X(X, Z, parametros.ax);
			// si no hacemos nada con X, parece que el compilador omite su cálculo
			for (int i1 = 0; i1 < NSEC; i1++) {
				for (int i2 = 0; i2 < NSEC; i2++) {
					if (X[i1][i2] > 0.) {
						X[i1][i2] = X[i2][i1] + parametros.ax[i1][i2];
					}
					else {
						X[i1][i2] = X[i2][i1] - parametros.ax[i1][i2];
					}
				}
			}
		}
	}
	ftime(&end);
	diff = (int)(1000.0 * (end.time - start.time) + (end.millitm - start.millitm));
	fprintf(salida, "tiempo Optimizado mili s : %d\n", diff);
	fflush(salida);
	ftime(&start);
	for (long long i = 0LL; i < 100LL; i++) {
		for (long long j = 0LL; j < 1000000LL; j++) {
			double X[NSEC][NSEC];
			consumo_intermedio_X(X, Z, parametros.ax);
			for (int i1 = 0; i1 < NSEC; i1++) {
				for (int i2 = 0; i2 < NSEC; i2++) {
					if (X[i1][i2] > 0.) {
						X[i1][i2] = X[i2][i1] + parametros.ax[i1][i2];
					}
					else {
						X[i1][i2] = X[i2][i1] - parametros.ax[i1][i2];
					}
				}
			}
		}
	}
	ftime(&end);
	diff = (int)(1000.0 * (end.time - start.time) + (end.millitm - start.millitm));
	fprintf(salida, "tiempo            mili s : %d\n", diff);
	fflush(salida);
	ftime(&start);
	for (long long i = 0LL; i < 100LL; i++) {
		for (long long j = 0LL; j < 1000000LL; j++) {
			double X[NSEC][NSEC]{};
			for (int i1 = 0; i1 < NSEC; i1++) {
				for (int i2 = 0; i2 < NSEC; i2++) {
					if (X[i1][i2] > 0.) {
						X[i1][i2] = X[i2][i1] - parametros.ax[i1][i2];
					}
					else {
						X[i1][i2] = X[i2][i1] + parametros.ax[i1][i2];
					}
				}
			}
		}
	}
	ftime(&end);
	diff = (int)(1000.0 * (end.time - start.time) + (end.millitm - start.millitm));
	fprintf(salida, "tiempo referencia mili s : %d\n\n", diff);
	fflush(salida);
	*/

	if (inicia_cotas() == false) {
		// Error al generar la poblacion
		merito_sol(poblacion[ind_mejor_merito]);
		if (extendida == 1) {
			me_sol[0] = -2.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			fin_soluciona(t_inicio);
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -2.;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			fin_soluciona(t_inicio);
			return VEC_OPT_E;
		}
	}
	if (fija_cotas(cotasInf, cotasSup) == false) {
		// Error al fijar las cotas
		if (extendida == 1) {
			me_sol[0] = -3.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			fin_soluciona(t_inicio);
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -3;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			fin_soluciona(t_inicio);
			return VEC_OPT_E;
		}
	}
	if (inicia_poblacion(factor_inicio) == false) {
		// Error al reservar memoria para la poblacion
		if (extendida == 1) {
			me_sol[0] = -4.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			fin_soluciona(t_inicio);
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -4.;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			fin_soluciona(t_inicio);
			return VEC_OPT_E;
		}
	}
	for (int i = 0; i < NVEC; i++) {
		vec_ini[i] = vec[i];
	}
	gen.seed(semilla);
	dis_entero = uniform_int_distribution<int>{ 0, ((int)NPOB - 1) };
	if (genera_poblacion() == false) {
		// Error al generar la poblacion
		if (extendida == 1) {
			me_sol[0] = -5.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			fin_soluciona(t_inicio);
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -5.;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			fin_soluciona(t_inicio);
			return VEC_OPT_E;
		}
	}

	/*
	// estadística de la población inicial
	double* media;
	media = (double*)malloc(NVEC * sizeof(double));
	if (media == NULL) {
		// Error, terminacion inesperada
		merito_sol(poblacion[ind_mejor_merito]);
		if (extendida == 1) {
			me_sol[0] = -10.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			fin_soluciona(t_inicio);
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -10.;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			fin_soluciona(t_inicio);
			return VEC_OPT_E;
		}
	}
	double* desest;
	desest = (double*)malloc(NVEC * sizeof(double));
	if (desest == NULL) {
		// Error, terminacion inesperada
		merito_sol(poblacion[ind_mejor_merito]);
		if (extendida == 1) {
			me_sol[0] = -10.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			fin_soluciona(t_inicio);
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -10.;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			fin_soluciona(t_inicio);
			return VEC_OPT_E;
		}
	}
	for (int i = 0; i < NVEC; i++) {
		media[i] = 0;
		for (int j = 0; j < NPOB; j++) {
			media[i] += poblacion[j][i];
		}
		media[i] /= (double)NPOB;
	}
	double dd;
	for (int i = 0; i < NVEC; i++) {
		desest[i] = 0;
		for (int j = 0; j < NPOB; j++) {
			dd = poblacion[j][i] - media[i];
			desest[i] += dd * dd;
		}
		desest[i] = sqrt(desest[i] / (double)(NPOB - 1));
	}
	FILE* se;
	sprintf_s(fichero, 127, "C:/MEGA/Salidas/estaDLL_%d.log", id_salida);
	se = _fsopen(fichero, "w", _SH_DENYWR);
	if (se == 0) {
		if (extendida == 1) {
			me_sol[0] = -9;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -9;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			return VEC_OPT_E;
		}
	}
	for (int i = 0; i < NVEC; i++) {
		fprintf(se, "%7d %14.6e %14.6e %14.6e %14.6e %14.6e\n", i, vec_ini[i], cotas[0][i], cotas[1][i], media[i], desest[i]);
	}
	fclose(se);
	free(media);
	free(desest);
	*/

	if (max_generaciones == 0) {
		// para una valoración inicial del modelo
		merito_sol(vec);
		if (extendida == 1) {
			me_sol[0] = 0;
			me_sol[2] = 0;
			me_sol[3] = 0;
			fin_soluciona(t_inicio);
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = 0;
			VEC_OPT_E[2] = 0;
			VEC_OPT_E[3] = 0;
			fin_soluciona(t_inicio);
			return VEC_OPT_E;
		}
	}
	histo_n = 0;
	mejor_merito_anterior = 1.0e+99;
	generacion = 0;
	intentos = 0;
	hgen[0] = mt19937(semilla);
	if (poner_el_mejor_primero) {
		hdis_entero[0] = uniform_int_distribution<int>{ 1, ((int)NPOB - 1) };
	}
	else {
		hdis_entero[0] = uniform_int_distribution<int>{ 0, ((int)NPOB - 1) };
	}
	hdis_entero_ivec[0] = uniform_int_distribution<int>{ 0, ((int)NVEC - 1) };
	hdis_double[0] = uniform_real_distribution<double>{ 0.0, 1.0 };
	if (n_hilos > 0) {
		if (PreparaMP() == -1) {
			if (extendida == 1) {
				me_sol[0] = -8.;
				me_sol[2] = intentos;
				me_sol[3] = generacion;
				fin_soluciona(t_inicio);
				return me_sol;
			}
			else {
				VEC_OPT_E[0] = -8.;
				VEC_OPT_E[2] = intentos;
				VEC_OPT_E[3] = generacion;
				fin_soluciona(t_inicio);
				return VEC_OPT_E;
			}
		}
	}
	else {
		res_Simulacion = avanza();
	}
	if (res_Simulacion == -1) {
		// Cancelado
		merito_sol(poblacion[ind_mejor_merito]);
		if (extendida == 1) {
			me_sol[0] = 5.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			fin_soluciona(t_inicio);
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = 5.;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			fin_soluciona(t_inicio);
			return VEC_OPT_E;
		}
	}
	else if (res_Simulacion == -2) {
		// Encontrada solucion
		merito_sol(poblacion[ind_mejor_merito]);
		if (extendida == 1) {
			me_sol[0] = 0.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			fin_soluciona(t_inicio);
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = 0.;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			fin_soluciona(t_inicio);
			return VEC_OPT_E;
		}
	}
	else if (res_Simulacion == -3) {
		if (mejor_merito > tol_aceptable) {
			// No progresa, solucion no aceptable
			merito_sol(poblacion[ind_mejor_merito]);
			if (extendida == 1) {
				me_sol[0] = 1.;
				me_sol[2] = intentos;
				me_sol[3] = generacion;
				fin_soluciona(t_inicio);
				return me_sol;
			}
			else {
				VEC_OPT_E[0] = 1.;
				VEC_OPT_E[2] = intentos;
				VEC_OPT_E[3] = generacion;
				fin_soluciona(t_inicio);
				return VEC_OPT_E;
			}
		}
		else {
			// No progresa, pero la solucion puede ser aceptable
			merito_sol(poblacion[ind_mejor_merito]);
			if (extendida == 1) {
				me_sol[0] = 2.;
				me_sol[2] = intentos;
				me_sol[3] = generacion;
				fin_soluciona(t_inicio);
				return me_sol;
			}
			else {
				VEC_OPT_E[0] = 2.;
				VEC_OPT_E[2] = intentos;
				VEC_OPT_E[3] = generacion;
				fin_soluciona(t_inicio);
				return VEC_OPT_E;
			}
		}
	}
	else if (res_Simulacion == -5) {
		if (mejor_merito > 0.0001) {
			// Superado el maximo de generaciones, solucion no aceptable
			merito_sol(poblacion[ind_mejor_merito]);
			if (extendida == 1) {
				me_sol[0] = 3.;
				me_sol[2] = intentos;
				me_sol[3] = generacion;
				fin_soluciona(t_inicio);
				return me_sol;
			}
			else {
				VEC_OPT_E[0] = 3.;
				VEC_OPT_E[2] = intentos;
				VEC_OPT_E[3] = generacion;
				fin_soluciona(t_inicio);
				return VEC_OPT_E;
			}
		}
		else {
			// Superado el maximo de generaciones, pero la solucion puede ser aceptable
			merito_sol(poblacion[ind_mejor_merito]);
			if (extendida == 1) {
				me_sol[0] = 4.;
				me_sol[2] = intentos;
				me_sol[3] = generacion;
				fin_soluciona(t_inicio);
				return me_sol;
			}
			else {
				VEC_OPT_E[0] = 4.;
				VEC_OPT_E[2] = intentos;
				VEC_OPT_E[3] = generacion;
				fin_soluciona(t_inicio);
				return VEC_OPT_E;
			}
		}
	}
	else {
		// Error, terminacion inesperada
		merito_sol(poblacion[ind_mejor_merito]);
		if (extendida == 1) {
			me_sol[0] = -10.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			fin_soluciona(t_inicio);
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -10.;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			fin_soluciona(t_inicio);
			return VEC_OPT_E;
		}
	}
}
void fin_soluciona(auto t_inicio) {
	/*
	chrono::duration<double> elapsed_seconds = end - start;
	time_t end_time = chrono::system_clock::to_time_t(end);
	*/

	auto t_fin = chrono::system_clock::now();
	auto fin = chrono::system_clock::to_time_t(t_fin);
	char tmBuff[30];
	ctime_s(tmBuff, sizeof(tmBuff), &fin);
	double dist = distancia_clonacion();
	fprintf(salida, "%9d %12.5e %12.5e\n", generacion, dist, mejor_merito);
	fprintf(salida, "\nfin   : %s\n", tmBuff);
	fclose(salida);
	if (histo_sol > 0) {
		char fichero[128];
		sprintf_s(fichero, 127, "C:/MEGA/Salidas/solDLL_%d_%d_%d.txt", id_salida, modo_poblacion_inicial, semilla);
		sal_sol = _fsopen(fichero, "wt", _SH_DENYWR);
		if (sal_sol != 0) {
			for (int j = 0; j < NVEC; j++) {
				fprintf(sal_sol, "%15.5e\n", poblacion[ind_mejor_merito][j]);
			}
			fclose(sal_sol);
		}
	}
}
int parametros_alge(double* par) {
	int ipar = 0;
	max_intentos = (int)par[ipar++];
	n_hilos = (int)par[ipar++];
	max_generaciones = (int)par[ipar++];
	tolerancia = par[ipar++];
	tol_aceptable = par[ipar++];
	generaciones_control_progreso = (int)par[ipar++];
	min_progreso = par[ipar++];
	histo_int = (int)par[ipar++];
	histo_sol = (int)par[ipar++];
	modo_poblacion_inicial = (int)par[ipar++];
	factor_inicio = par[ipar++];
	sigma_inicio = par[ipar++];
	num_tramos_lhs = (int)par[ipar++];
	NPOB = (int)par[ipar++];
	factor_mutacion = par[ipar++];
	recombinacion[0] = par[ipar++];
	recombinacion[1] = par[ipar++];
	control_factibilidad = (int)par[ipar++] == 1;
	semilla = (int)par[ipar++];
	poner_el_mejor_primero = (int)par[ipar++] == 1;
	incluir_x0 = (int)par[ipar++] == 1;
	NVEC = (int)par[ipar++];
	id_salida = (int)par[ipar++];
	if (NVEC >= MAX_VEC) {
		return -1;
	}
	return 0;
}
bool inicia_cotas() {
	size_t const mem_primer_ind = 2 * sizeof(double*);
	cotas = (double**)malloc(mem_primer_ind);
	if (cotas == NULL) return false;
	size_t const memoria_fila = NVEC * sizeof(double);
	for (int i = 0; i < 2; i++) {
		cotas[i] = (double*)malloc(memoria_fila);
		if (cotas[i] == NULL) return false;
	}
	fijo = (int*)malloc(NVEC * sizeof(int));
	return true;
}
bool inicia_poblacion(double factor_inicio) {
	size_t const mem_primer_indice = sizeof(double*) * NPOB;
	poblacion = (double**)malloc(mem_primer_indice);
	if (poblacion == NULL) return false;
	descendiente = (double**)malloc(mem_primer_indice);
	if (descendiente == NULL) return false;
	size_t const memoria_fila = NVEC * sizeof(double);
	for (int i = 0; i < NPOB; i++) {
		poblacion[i] = (double*)malloc(memoria_fila);
		if (poblacion[i] == NULL) return false;
		descendiente[i] = (double*)malloc(memoria_fila);
		if (descendiente[i] == NULL) return false;
	}

	size_t const mem_npob = sizeof(double) * NPOB;
	merito_individuo = (double*)malloc(mem_npob);
	if (merito_individuo == NULL) return false;
	factible = (double*)malloc(mem_npob);
	if (factible == NULL) return false;
	return true;
}
bool fija_cotas(double* cotasInf, double* cotasSup) {
	for (int i = 0; i < NVEC; i++) {
		cotas[0][i] = cotasInf[i];
		cotas[1][i] = cotasSup[i];
		if (abs(cotas[1][i] - cotas[0][i]) < 0.000001) {
			fijo[i] = 1;
		}
		else {
			fijo[i] = 0;
		}
	}
	return true;
}
bool genera_poblacion() {
	double semi_izq;
	double semi_dch;
	double semi_intervalo;
	double desplazamiento;
	double v;
	double f;
	if (modo_poblacion_inicial == 0) {
		// intérvalo simétrico centrado en 'vec_ini' con distribución uniforme

		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					poblacion[i][j] = vec_ini[j];
				}
				else {
					semi_izq = vec_ini[j] - cotas[0][j];
					semi_dch = cotas[1][j] - vec_ini[j];
					if (semi_izq < semi_dch) {
						semi_intervalo = semi_izq;
					}
					else {
						semi_intervalo = semi_dch;
					}
					f = (semi_izq + semi_dch) / (2. * semi_intervalo);
					desplazamiento = f * factor_inicio * dis_double(gen) * semi_intervalo;
					if (dis_double(gen) < 0.5) {
						v = vec_ini[j] - desplazamiento;
					}
					else {
						v = vec_ini[j] + desplazamiento;
					}
					if (v < cotas[0][j]) {
						v = cotas[0][j] + 0.000001;
					}
					else if (v > cotas[1][j]) {
						v = cotas[1][j] - 0.000001;
					}
					poblacion[i][j] = v;
				}
			}
		}
	}
	else if (modo_poblacion_inicial == 1) {
		// centrado en el centro de intervalo de validez de la variable con distribución uniforme

		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					poblacion[i][j] = vec_ini[j];
				}
				else {
					semi_intervalo = (cotas[1][j] - cotas[0][j]) / 2.;
					desplazamiento = factor_inicio * dis_double(gen) * semi_intervalo;
					if (dis_double(gen) < 0.5) {
						v = cotas[0][j] + semi_intervalo - desplazamiento;
					}
					else {
						v = cotas[0][j] + semi_intervalo + desplazamiento;
					}
					if (v < cotas[0][j]) {
						v = cotas[0][j] + 0.000001;
					}
					else if (v > cotas[1][j]) {
						v = cotas[1][j] - 0.000001;
					}
					poblacion[i][j] = v;
				}
			}
		}
	}
	else if (modo_poblacion_inicial == 2) {
		// intérvalo simétrico centrado en 'vec_ini' con distribución normal

		mt19937 gent(semilla);
		normal_distribution<double> dis_normal{ 0.0, sigma_inicio };
		for (int i = 2; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					poblacion[i][j] = vec_ini[j];
				}
				else {
					semi_izq = vec_ini[j] - cotas[0][j];
					semi_dch = cotas[1][j] - vec_ini[j];
					if (semi_izq < semi_dch) {
						semi_intervalo = semi_izq;
					}
					else {
						semi_intervalo = semi_dch;
					}
					desplazamiento = dis_normal(gent) * semi_intervalo;
					if (dis_double(gen) < 0.5) {
						v = vec_ini[j] - desplazamiento;
					}
					else {
						v = vec_ini[j] + desplazamiento;
					}
					if (v < cotas[0][j]) {
						v = cotas[0][j] + 0.000001;
					}
					else if (v > cotas[1][j]) {
						v = cotas[1][j] - 0.000001;
					}
					poblacion[i][j] = v;
				}
			}
		}
	}
	else if (modo_poblacion_inicial == 3) {
		// intérvalo simétrico centrado en 'vec_ini' con distribución normal

		mt19937 gent(semilla);
		normal_distribution<double> dis_normal{ 0.0, sigma_inicio };
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					poblacion[i][j] = vec_ini[j];
				}
				else {
					semi_intervalo = (cotas[1][j] - cotas[0][j]) / 2.;
					desplazamiento = dis_normal(gent) * semi_intervalo;
					if (dis_double(gen) < 0.5) {
						v = cotas[0][j] + semi_intervalo - desplazamiento;
					}
					else {
						v = cotas[0][j] + semi_intervalo + desplazamiento;
					}
					if (v < cotas[0][j]) {
						v = cotas[0][j] + 0.000001;
					}
					else if (v > cotas[1][j]) {
						v = cotas[1][j] - 0.000001;
					}
					poblacion[i][j] = v;
				}
			}
		}
	}
	else if (modo_poblacion_inicial == 4) {
		/*
		Latin Hypercube Sampling con permutaciones distintas para cada variable
		distrubuye uniformemente los valores de las variables en sus rangos de variación
		dividiendo esos rangos en tramos y generando la fracción correspondiente de individuos
		en cada tramo.
		*/

		int individuos_tramo = NPOB / num_tramos_lhs;
		int indice_ini_tramo;
		int indice_fin_tramo;
		double ancho_tramo;
		double cota_desde;
		double cota_hasta;
		// recorremos las variables (NVEC), para determinar los valores inicial y final que tiene la variable en cada tramo
		for (int j = 0; j < NVEC; j++) {
			if (fijo[j] == 1) {
				for (int i = 0; i < NPOB; i++) {
					descendiente[i][j] = vec_ini[j];
				}
			}
			else {
				// rellenamos la coluna 'j' de 'descendiente' correspondiente a cada variable con la
				// secuencia uniforme de valores de la variable, desde 'cotas[0][j]' hasta 'cotas[1][j]'
				indice_ini_tramo = 0;
				indice_fin_tramo = indice_ini_tramo + individuos_tramo;
				ancho_tramo = (cotas[1][j] - cotas[0][j]) / num_tramos_lhs;
				semi_intervalo = ancho_tramo / 2.;
				cota_desde = cotas[0][j];
				// para cada tramo
				for (int k = 0; k < num_tramos_lhs; k++) {
					cota_hasta = cota_desde + ancho_tramo;
					// pra los individuos 'i' dentro del tramo
					for (int i = indice_ini_tramo; i < indice_fin_tramo; i++) {

						// 'factor_inicio' debe ser 1.0 para que la distribución sea realmente uniforme

						desplazamiento = factor_inicio * dis_double(gen) * semi_intervalo;
						if (dis_double(gen) < 0.5) {
							v = cota_desde + semi_intervalo - desplazamiento;
						}
						else {
							v = cota_desde + semi_intervalo + desplazamiento;
						}
						if (v < cotas[0][j]) {
							v = cotas[0][j] + 0.000001;
						}
						else if (v > cotas[1][j]) {
							v = cotas[1][j] - 0.000001;
						}
						descendiente[i][j] = v;
					}
					cota_desde = cota_hasta;
					indice_ini_tramo = indice_fin_tramo;
					if (k == num_tramos_lhs - 1) {
						indice_fin_tramo = NPOB;
					}
					else {
						indice_fin_tramo = indice_ini_tramo + individuos_tramo;
						if (indice_fin_tramo > NPOB) indice_fin_tramo = NPOB;
					}
				}
			}
		}
		// ponemos en 'p' la secuencia [0, NPOB)
		int* p;
		size_t const mem_p = sizeof(int) * NPOB;
		p = (int*)malloc(mem_p);
		if (p == NULL) {
			return false;
		}
		for (int i = 0; i < NPOB; i++)
		{
			p[i] = i;
		}

		std::mt19937 rng(semilla);

		int k;
		// rellenamos la población variable a variable con permutaciones distintas de los valores obtenidos para cada una
		for (int j = 0; j < NVEC; j++) {
			std::shuffle(p, p + NPOB, rng);
			for (int i = 0; i < NPOB; i++) {
				k = p[i];
				poblacion[i][j] = descendiente[k][j];
			}
		}
		free(p);
	}
	else if (modo_poblacion_inicial == 5) {
		/*
		Latin Hypercube Sampling con la misma permutación para todas las variables
		distrubuye uniformemente los valores de las variables en sus rangos de variación
		dividiendo esos rangos en tramos y generando la fracción correspondiente de individuos
		en cada tramo.

		modalidad simplificada: cada individuo tiene, en todas sus variables, el valor que
		corresponde al mismo ordinal de la secuencia de la variable correspondiente, es decir,
		si un individuo tiene en su primer elemento el valor correspondiente a la posición 17 de la secuencia
		de la primera variable, en todos los demás elementos, tambien tiene el valor correspondiente
		a la posición 17 de la secuencia de la variable correspondiente
		*/

		int individuos_tramo = NPOB / num_tramos_lhs;
		int indice_ini_tramo;
		int indice_fin_tramo;
		double ancho_tramo;
		double cota_desde;
		double cota_hasta;
		// recorremos las variables (NVEC), para determinar los valores in icial y final que tiene la variable en cada tramo
		for (int j = 0; j < NVEC; j++) {
			if (fijo[j] == 1) {
				for (int i = 0; i < NPOB; i++) {
					descendiente[i][j] = vec_ini[j];
				}
			}
			else {
				// rellenamos la coluna 'j' de 'descendiente' correspondiente a cada variable con la
				// secuencia uniforme de valores de la variable, desde 'cotas[0][j]' hasta 'cotas[1][j]'
				indice_ini_tramo = 0;
				indice_fin_tramo = indice_ini_tramo + individuos_tramo;
				ancho_tramo = (cotas[1][j] - cotas[0][j]) / num_tramos_lhs;
				semi_intervalo = ancho_tramo / 2.;
				cota_desde = cotas[0][j];
				for (int k = 0; k < num_tramos_lhs; k++) {
					cota_hasta = cota_desde + ancho_tramo;
					for (int i = indice_ini_tramo; i < indice_fin_tramo; i++) {

						// 'factor_inicio' debe ser 1.0 para que la distribución sea realmente uniforme

						desplazamiento = factor_inicio * dis_double(gen) * semi_intervalo;
						if (dis_double(gen) < 0.5) {
							v = cota_desde + semi_intervalo - desplazamiento;
						}
						else {
							v = cota_desde + semi_intervalo + desplazamiento;
						}
						if (v < cotas[0][j]) {
							v = cotas[0][j] + 0.000001;
						}
						else if (v > cotas[1][j]) {
							v = cotas[1][j] - 0.000001;
						}
						descendiente[i][j] = v;
					}
					cota_desde = cota_hasta;
					indice_ini_tramo = indice_fin_tramo;
					if (k == num_tramos_lhs - 1) {
						indice_fin_tramo = NPOB;
					}
					else {
						indice_fin_tramo = indice_ini_tramo + individuos_tramo;
						if (indice_fin_tramo > NPOB) indice_fin_tramo = NPOB;
					}
				}
			}
		}

		/*
		for (int j = 0; j < NVEC; j++) {
			fprintf(salida, "%10.3f <", cotas[0][j]);
			for (int i = 0; i < NPOB; i++) {
				fprintf(salida, " %10.3f", descendiente[i][j]);
			}
			fprintf(salida, "> %10.3f\n", cotas[1][j]);
		}
		fflush(salida);
		*/

		// ponemos en 'p' la secuencia [0, NPOB)
		int* p;
		size_t const mem_p = sizeof(int) * NPOB;
		p = (int*)malloc(mem_p);
		if (p == NULL) {
			return false;
		}
		for (int i = 0; i < NPOB; i++)
		{
			p[i] = i;
		}
		// creamos una permutación de 'p'
		std::mt19937 rng(semilla);
		std::shuffle(p, p + NPOB, rng);

		// aplicamos la misma permutación a todas las variables
		int k;
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				k = p[i];
				poblacion[i][j] = descendiente[k][j];
			}
		}
		free(p);
	}
	else if (modo_poblacion_inicial == 6) {
		// secuencia de valores uniformemente espacionados entre cotas y permutaciones distintas para cada variable

		double v;
		double incremento;
		// recorremos las variables (NVEC), para determinar la secuencia de valores de cada una de ellas
		for (int j = 0; j < NVEC; j++) {
			if (fijo[j] == 1) {
				for (int i = 0; i < NPOB; i++) {
					descendiente[i][j] = vec_ini[j];
				}
			}
			else {
				// rellenamos la coluna 'j' de 'descendiente', correspondiente a cada variable, con la
				// secuencia de valores uniformemente espacionados entre cotas
				incremento = (cotas[1][j] - cotas[0][j]) / (double)NPOB;
				v = cotas[0][j] + incremento / 2.;
				for (int i = 0; i < NPOB; i++) {
					descendiente[i][j] = v;
					v += incremento;
				}
			}
		}
		// ponemos en 'p' la secuencia [0, NPOB)
		int* p;
		size_t const mem_p = sizeof(int) * NPOB;
		p = (int*)malloc(mem_p);
		if (p == NULL) {
			return false;
		}
		for (int i = 0; i < NPOB; i++)
		{
			p[i] = i;
		}
		// creamos una permutación de 'p'
		std::mt19937 rng(semilla);

		int k;
		// rellenamos la población variable a variable con permutaciones distintas de los valores obtenidos para cada una
		for (int j = 0; j < NVEC; j++) {
			std::shuffle(p, p + NPOB, rng);
			for (int i = 0; i < NPOB; i++) {
				k = p[i];
				poblacion[i][j] = descendiente[k][j];
			}
		}
		free(p);
	}
	else if (modo_poblacion_inicial == 7) {
		double v;
		double incremento;
		// recorremos las variables (NVEC), para determinar la secuencia de valores de cada una de ellas
		for (int j = 0; j < NVEC; j++) {
			if (fijo[j] == 1) {
				for (int i = 0; i < NPOB; i++) {
					descendiente[i][j] = vec_ini[j];
				}
			}
			else {
				// rellenamos la coluna 'j' de 'descendiente', correspondiente a cada variable, con la
				// secuencia de valores uniformemente espacionados entre cotas
				incremento = (cotas[1][j] - cotas[0][j]) / (double)NPOB;
				v = cotas[0][j] + incremento / 2.;
				for (int i = 0; i < NPOB; i++) {
					descendiente[i][j] = v;
					v += incremento;
				}
			}
		}
		// ponemos en 'p' la secuencia [0, NPOB)
		int* p;
		size_t const mem_p = sizeof(int) * NPOB;
		p = (int*)malloc(mem_p);
		if (p == NULL) {
			return false;
		}
		for (int i = 0; i < NPOB; i++)
		{
			p[i] = i;
		}
		// creamos una permutación de 'p'
		std::mt19937 rng(semilla);
		std::shuffle(p, p + NPOB, rng);

		// aplicamos la misma permutación a todas las variables
		int k;
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				k = p[i];
				poblacion[i][j] = descendiente[k][j];
			}
		}
		free(p);
	}
	else if (modo_poblacion_inicial == 8) {
		// valores próximos al extremo inferior del entorno de existencia de las variables
		// con permutaciones distintas de los valores obtenidos para cada una
		double intervalo;
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					descendiente[i][j] = vec_ini[j];
				}
				else {
					intervalo = cotas[1][j] - cotas[0][j];
					desplazamiento = factor_inicio * intervalo * dis_double(gen);
					v = cotas[0][j] + desplazamiento;
					descendiente[i][j] = v;
				}
			}
		}

		// ponemos en 'p' la secuencia [0, NPOB)
		int* p;
		size_t const mem_p = sizeof(int) * NPOB;
		p = (int*)malloc(mem_p);
		if (p == NULL) {
			return false;
		}
		for (int i = 0; i < NPOB; i++)
		{
			p[i] = i;
		}

		std::mt19937 rng(semilla);

		int k;
		// rellenamos la población variable a variable con permutaciones distintas de los valores obtenidos para cada una
		for (int j = 0; j < NVEC; j++) {
			std::shuffle(p, p + NPOB, rng);
			for (int i = 0; i < NPOB; i++) {
				k = p[i];
				poblacion[i][j] = descendiente[k][j];
			}
		}
		free(p);
	}
	else if (modo_poblacion_inicial == 9) {
		// valores próximos al extremo inferior del entorno de existencia de las variables
		// la misma permutación a todas las variables
		double intervalo;
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					descendiente[i][j] = vec_ini[j];
				}
				else {
					intervalo = cotas[1][j] - cotas[0][j];
					desplazamiento = factor_inicio * intervalo * dis_double(gen);
					v = cotas[0][j] + desplazamiento;
					descendiente[i][j] = v;
				}
			}
		}

		// ponemos en 'p' la secuencia [0, NPOB)
		int* p;
		size_t const mem_p = sizeof(int) * NPOB;
		p = (int*)malloc(mem_p);
		if (p == NULL) {
			return false;
		}
		for (int i = 0; i < NPOB; i++)
		{
			p[i] = i;
		}
		// creamos una permutación de 'p'
		std::mt19937 rng(semilla);
		std::shuffle(p, p + NPOB, rng);

		// aplicamos la misma permutación a todas las variables
		int k;
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				k = p[i];
				poblacion[i][j] = descendiente[k][j];
			}
		}
		free(p);
	}
	else if (modo_poblacion_inicial == 10) {
		// valores próximos al extremo superior del entorno de existencia de las variables
		// con permutaciones distintas de los valores obtenidos para cada una
		double intervalo;
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					descendiente[i][j] = vec_ini[j];
				}
				else {
					intervalo = cotas[1][j] - cotas[0][j];
					desplazamiento = factor_inicio * intervalo * dis_double(gen);
					v = cotas[1][j] - desplazamiento;
					descendiente[i][j] = v;
				}
			}
		}

		// ponemos en 'p' la secuencia [0, NPOB)
		int* p;
		size_t const mem_p = sizeof(int) * NPOB;
		p = (int*)malloc(mem_p);
		if (p == NULL) {
			return false;
		}
		for (int i = 0; i < NPOB; i++)
		{
			p[i] = i;
		}

		std::mt19937 rng(semilla);

		int k;
		// rellenamos la población variable a variable con permutaciones distintas de los valores obtenidos para cada una
		for (int j = 0; j < NVEC; j++) {
			std::shuffle(p, p + NPOB, rng);
			for (int i = 0; i < NPOB; i++) {
				k = p[i];
				poblacion[i][j] = descendiente[k][j];
			}
		}
		free(p);
	}
	else if (modo_poblacion_inicial == 11) {
		// valores próximos a los extremos de los entornos de existencia de las variables
		// con permutaciones distintas de los valores obtenidos para cada una

		double intervalo;
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					descendiente[i][j] = vec_ini[j];
				}
				else {
					intervalo = cotas[1][j] - cotas[0][j];
					desplazamiento = factor_inicio * dis_double(gen) * intervalo;
					if (dis_double(gen) > 0.5) {
						v = cotas[0][j] + desplazamiento;
					}
					else {
						v = cotas[1][j] - desplazamiento;
					}
					descendiente[i][j] = v;
				}
			}
		}

		// ponemos en 'p' la secuencia [0, NPOB)
		int* p;
		size_t const mem_p = sizeof(int) * NPOB;
		p = (int*)malloc(mem_p);
		if (p == NULL) {
			return false;
		}
		for (int i = 0; i < NPOB; i++)
		{
			p[i] = i;
		}

		std::mt19937 rng(semilla);

		int k;
		// rellenamos la población variable a variable con permutaciones distintas de los valores obtenidos para cada una
		for (int j = 0; j < NVEC; j++) {
			std::shuffle(p, p + NPOB, rng);
			for (int i = 0; i < NPOB; i++) {
				k = p[i];
				poblacion[i][j] = descendiente[k][j];
			}
		}
		free(p);
	}
	else if (modo_poblacion_inicial == 12) {
		/*
		valores próximos o iguales al extremo inferior del entorno de existencia de las variables
		con permutaciones distintas de los valores obtenidos para cada una
		*/
		long ceros = 0;
		long ci = 0;
		long cic = 0;
		double intervalo;
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					descendiente[i][j] = vec_ini[j];
				}
				else {
					if (dis_double(gen) < sigma_inicio) {
						v = cotas[0][j];
						ci++;
						if (v <= 0.000001) cic++;
					}
					else {
						intervalo = cotas[1][j] - cotas[0][j];
						desplazamiento = factor_inicio * intervalo * dis_double(gen);
						v = cotas[0][j] + desplazamiento;
						if (v <= 0.000001) ceros++;
					}
					descendiente[i][j] = v;
				}
			}
		}
		fprintf(salida, "elementos cota inferior     : %9ld [media vector: %5ld %6.1f%%]\n", ci, (long)((double)ci / NPOB), 100. * (double)ci / NPOB / NVEC);
		fprintf(salida, "elementos cota inferior cero: %9ld [media vector: %5ld %6.1f%%]\n", cic, (long)((double)cic / NPOB), 100. * (double)cic / NPOB / NVEC);
		fprintf(salida, "elementos a cero            : %9ld [media vector: %5ld %6.1f%%]\n\n", ceros + cic, (long)((double)(ceros + cic) / NPOB), 100. * (double)(ceros + cic) / NPOB / NVEC);

		// ponemos en 'p' la secuencia [0, NPOB)
		int* p;
		size_t const mem_p = sizeof(int) * NPOB;
		p = (int*)malloc(mem_p);
		if (p == NULL) {
			return false;
		}
		for (int i = 0; i < NPOB; i++)
		{
			p[i] = i;
		}

		std::mt19937 rng(semilla);

		int k;
		// rellenamos la población variable a variable con permutaciones distintas de los valores obtenidos para cada una
		for (int j = 0; j < NVEC; j++) {
			std::shuffle(p, p + NPOB, rng);
			for (int i = 0; i < NPOB; i++) {
				k = p[i];
				poblacion[i][j] = descendiente[k][j];
			}
		}
		free(p);
	}
	else if (modo_poblacion_inicial == 13) {
		/*
		valores próximos o iguales al extremo inferior del entorno de existencia de las variables
		*/
		long ceros = 0;
		long ci = 0;
		long cic = 0;
		double intervalo;
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					poblacion[i][j] = vec_ini[j];
				}
				else {
					if (dis_double(gen) < sigma_inicio) {
						v = cotas[0][j];
						ci++;
						if (v <= 0.000001) cic++;
					}
					else {
						intervalo = cotas[1][j] - cotas[0][j];
						desplazamiento = factor_inicio * intervalo * dis_double(gen);
						v = cotas[0][j] + desplazamiento;
						if (v <= 0.000001) ceros++;
					}
					poblacion[i][j] = v;
				}
			}
		}
		fprintf(salida, "elementos cota inferior     : %9ld [media vector: %5ld %6.1f%%]\n", ci, (long)((double)ci / NPOB), 100. * (double)ci / NPOB / NVEC);
		fprintf(salida, "elementos cota inferior cero: %9ld [media vector: %5ld %6.1f%%]\n", cic, (long)((double)cic / NPOB), 100. * (double)cic / NPOB / NVEC);
		fprintf(salida, "elementos a cero            : %9ld [media vector: %5ld %6.1f%%]\n\n", ceros + cic, (long)((double)(ceros + cic) / NPOB), 100. * (double)(ceros + cic) / NPOB / NVEC);
	}
	else if (modo_poblacion_inicial == 14) {
		/*
		valores próximos o iguales al extremo superior del entorno de existencia de las variables
		con permutaciones distintas de los valores obtenidos para cada una
		*/
		long cs = 0;
		double intervalo;
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					descendiente[i][j] = vec_ini[j];
				}
				else {
					if (dis_double(gen) < sigma_inicio) {
						v = cotas[1][j];
						cs++;
					}
					else {
						intervalo = cotas[1][j] - cotas[0][j];
						desplazamiento = factor_inicio * intervalo * dis_double(gen);
						v = cotas[1][j] - desplazamiento;
					}
					descendiente[i][j] = v;
				}
			}
		}
		fprintf(salida, "elementos cota superior     : %9ld [media vector: %5ld %6.1f%%]\n\n", cs, (long)((double)cs / NPOB), 100. * (double)cs / NPOB / NVEC);

		// ponemos en 'p' la secuencia [0, NPOB)
		int* p;
		size_t const mem_p = sizeof(int) * NPOB;
		p = (int*)malloc(mem_p);
		if (p == NULL) {
			return false;
		}
		for (int i = 0; i < NPOB; i++)
		{
			p[i] = i;
		}

		std::mt19937 rng(semilla);

		int k;
		// rellenamos la población variable a variable con permutaciones distintas de los valores obtenidos para cada una
		for (int j = 0; j < NVEC; j++) {
			std::shuffle(p, p + NPOB, rng);
			for (int i = 0; i < NPOB; i++) {
				k = p[i];
				poblacion[i][j] = descendiente[k][j];
			}
		}
		free(p);
	}
	else if (modo_poblacion_inicial == 15) {
		/*
		valores próximos o iguales al extremo inferior del entorno de existencia de las variables
		con permutaciones distintas de los valores obtenidos para cada una
		desplazamientos independendientes del intervalo de existencia
		*/
		long ceros = 0;
		long ci = 0;
		long cic = 0;
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					descendiente[i][j] = vec_ini[j];
				}
				else {
					if (dis_double(gen) < sigma_inicio) {
						v = cotas[0][j];
						ci++;
						if (v <= 0.000001) cic++;
					}
					else {
						desplazamiento = factor_inicio * dis_double(gen);
						v = cotas[0][j] + desplazamiento;
						if (v <= 0.000001) ceros++;
					}
					descendiente[i][j] = v;
				}
			}
		}
		fprintf(salida, "elementos cota inferior     : %9ld [media vector: %5ld %6.1f%%]\n", ci, (long)((double)ci / NPOB), 100. * (double)ci / NPOB / NVEC);
		fprintf(salida, "elementos cota inferior cero: %9ld [media vector: %5ld %6.1f%%]\n", cic, (long)((double)cic / NPOB), 100. * (double)cic / NPOB / NVEC);
		fprintf(salida, "elementos a cero            : %9ld [media vector: %5ld %6.1f%%]\n\n", ceros + cic, (long)((double)(ceros + cic) / NPOB), 100. * (double)(ceros + cic) / NPOB / NVEC);

		// ponemos en 'p' la secuencia [0, NPOB)
		int* p;
		size_t const mem_p = sizeof(int) * NPOB;
		p = (int*)malloc(mem_p);
		if (p == NULL) {
			return false;
		}
		for (int i = 0; i < NPOB; i++)
		{
			p[i] = i;
		}

		std::mt19937 rng(semilla);

		int k;
		// rellenamos la población variable a variable con permutaciones distintas de los valores obtenidos para cada una
		for (int j = 0; j < NVEC; j++) {
			std::shuffle(p, p + NPOB, rng);
			for (int i = 0; i < NPOB; i++) {
				k = p[i];
				poblacion[i][j] = descendiente[k][j];
			}
		}
		free(p);
	}
	else {
		return false;
	}

	if (incluir_x0) {
		// incluir en la población el vector de prueba inicial 'vec' como primer individuo
		for (int j = 0; j < NVEC; j++) {
			poblacion[0][j] = vec_ini[j];
		}
	}

	// seleccionar el mejor
	mejor_merito = 1.0e+99;
	ind_mejor_merito = NPOB + 1;
	for (int i = 0; i < NPOB; i++) {
		v = merito_s(poblacion[i]);
		/*
		fprintf(salida, "%14.6e\n", v);
		*/
		merito_individuo[i] = v;
		factible[i] = true;
		if (v < mejor_merito) {
			mejor_merito = v;
			ind_mejor_merito = i;
		}
	}
	/*
	fflush(salida);
	*/
	return true;
}
void recolocar_al_mejor(int ind_mejor_merito) {
	double* p = poblacion[0];
	poblacion[0] = poblacion[ind_mejor_merito];
	poblacion[ind_mejor_merito] = p;
	double me = merito_individuo[0];
	merito_individuo[0] = merito_individuo[ind_mejor_merito];
	merito_individuo[ind_mejor_merito] = me;
	ind_mejor_merito = 0;
}
int avanza() {
	int desde = poner_el_mejor_primero ? 1 : 0;
	cte_recombinacion = (recombinacion[0] + recombinacion[1]) / 2.;
	while (generacion < max_generaciones) {
		mutacion_cruze(desde, NPOB, 0);
		/*
		no se hacen cambios en la población hasta completada la generación
		para poder fraccionar la población en multiproceso
		*/
		seleccion(desde);
		res_Simulacion = comprobar_final();
		if (res_Simulacion < 0) {
			return res_Simulacion;
		}
		cte_recombinacion = recombinacion[0] + dis_double(gen) * (recombinacion[1] - recombinacion[0]);
		generacion++;
	}
	if (generacion == max_generaciones) {
		return -5;
	}
	return -6;
}
void mutacion_cruze(int desde, int hasta, int hilo) {
	int i1;
	int i2;
	int i3;
	double v;
	bool es_factible;
	for (int i = desde; i < hasta; i++) {
		i1 = hdis_entero[hilo](hgen[hilo]);
		i2 = hdis_entero[hilo](hgen[hilo]);
		i3 = hdis_entero_ivec[hilo](hgen[hilo]);
		es_factible = true;
		for (int j = 0; j < NVEC; j++) {
			if (fijo[j] == 0 && (hdis_double[hilo](hgen[hilo]) <= cte_recombinacion || j == i3)) {
				v = poblacion[ind_mejor_merito][j] + factor_mutacion * (poblacion[i1][j] - poblacion[i2][j]);
				if (control_factibilidad) {
					if (v < cotas[0][j] || v > cotas[1][j]) {
						es_factible = false;
						break;
					}
				}
				descendiente[i][j] = v;
			}
			else {
				descendiente[i][j] = poblacion[i][j];
			}
		}
		if (control_factibilidad) {
			factible[i] = es_factible;
		}
	}
}
void mutacion_cruzeH(int desde, int hasta, int hilo) {
	int i1;
	int i2;
	int i3;
	double v;
	bool es_factible;
	for (int i = desde; i < hasta; i++) {
		i1 = hdis_entero[hilo](hgen[hilo]);
		i2 = hdis_entero[hilo](hgen[hilo]);
		i3 = hdis_entero_ivec[hilo](hgen[hilo]);
		es_factible = true;
		for (int j = 0; j < NVEC; j++) {
			if (fijo[j] == 0 && (hdis_double[hilo](hgen[hilo]) <= cte_recombinacion || j == i3)) {
				v = poblacion[ind_mejor_merito][j] + factor_mutacion * (poblacion[i1][j] - poblacion[i2][j]);
				if (control_factibilidad) {
					if (v < cotas[0][j] || v > cotas[1][j]) {
						es_factible = false;
						break;
					}
				}
				descendiente[i][j] = v;
			}
			else {
				descendiente[i][j] = poblacion[i][j];
			}
		}
		if (control_factibilidad) {
			factible[i] = es_factible;
		}
	}
}
void seleccion(int desde) {
	double me_descendiente;
	for (int i = desde; i < NPOB; i++) {
		if (!control_factibilidad || factible[i]) {
			me_descendiente = merito_s(descendiente[i]);
			if (me_descendiente < merito_individuo[i]) {
				for (int j = 0; j < NVEC; j++) {
					poblacion[i][j] = descendiente[i][j];
				}
				merito_individuo[i] = me_descendiente;
				if (me_descendiente < mejor_merito) {
					mejor_merito = me_descendiente;
					ind_mejor_merito = i;
				}
			}
		}
	}
}
void seleccionH(int desde, int hasta) {
	double me_descendiente;
	for (int i = desde; i < hasta; i++) {
		if (!control_factibilidad || factible[i]) {
			me_descendiente = merito_s(descendiente[i]);
			if (me_descendiente < merito_individuo[i]) {
				for (int j = 0; j < NVEC; j++) {
					poblacion[i][j] = descendiente[i][j];
				}
				merito_individuo[i] = me_descendiente;
			}
		}
	}
}
int comprobar_final() {
	if (histo_sol > 0 && (generacion % histo_sol) == 0) {
		char fichero[128];
		int n_sol = (int)(generacion / histo_sol);
		sprintf_s(fichero, 127, "C:/MEGA/Salidas/solDLL_%d_%d_%d_%d.txt", id_salida, modo_poblacion_inicial, semilla, n_sol);
		sal_sol = _fsopen(fichero, "w", _SH_DENYWR);
		if (sal_sol != 0) {
			for (int j = 0; j < NVEC; j++) {
				fprintf(sal_sol, "%15.7e\n", poblacion[ind_mejor_merito][j]);
			}
			fclose(sal_sol);
		}
		else {
			fprintf(salida, "*--* No se pudo abrir el fichero para salvar la solución %d\n", n_sol);
		}
	}
	if (histo_int > 0 && (generacion % histo_int) == 0) {
		double dist = distancia_clonacion();
		if (generacion == 0) {
			fprintf(salida, "%9d %12.5e %12.5e %6d\n", generacion, dist, mejor_merito, ind_mejor_merito);
		}
		else {
			fprintf(salida, "%9d %12.5e %12.5e\n", generacion, dist, mejor_merito);
		}
		fflush(salida);
		histogenera[histo_n] = generacion;
		histograma[histo_n] = mejor_merito;
		histo_n++;
		if (histo_n == HISTO_MAX) {
			// registro circular
			histo_n = 0;
		}
	}
	if (mejor_merito < tolerancia) {
		histogenera[histo_n] = generacion;
		histograma[histo_n] = mejor_merito;
		return -2;
	}
	if (generacion > 0 && (generacion % generaciones_control_progreso == 0)) {
		if ((mejor_merito_anterior - mejor_merito) < mejor_merito_anterior * min_progreso) {
			if (mejor_merito < tol_aceptable) {
				histogenera[histo_n] = generacion;
				histograma[histo_n] = mejor_merito;
				return -3;
			}
			intentos++;
			if (intentos < max_intentos) {
				histogenera[histo_n] = generacion;
				histograma[histo_n] = mejor_merito;
				histo_n++;
				if (histo_n == HISTO_MAX) {
					// registro circular
					histo_n = 0;
				}
				fprintf(salida, "\n");
				genera_poblacion();
				double dist = distancia_clonacion();
				fprintf(salida, "%9d %12.5e %12.5e %6d\n", generacion, dist, mejor_merito, ind_mejor_merito);
				max_generaciones += generacion;
				mejor_merito_anterior = 1.0e+99;
				histogenera[histo_n] = generacion;
				histograma[histo_n] = mejor_merito_anterior;
				histo_n++;
				if (histo_n == HISTO_MAX) {
					// registro circular
					histo_n = 0;
				}
			}
			else {
				intentos--;
				histogenera[histo_n] = generacion;
				histograma[histo_n] = mejor_merito;
				return -3;
			}
		}
		else {
			if (!control_factibilidad) {
				double dist = distancia_clonacion();
				if (dist > 1.e+32) {
					intentos++;
					if (intentos < max_intentos) {
						histogenera[histo_n] = generacion;
						histograma[histo_n] = mejor_merito;
						histo_n++;
						if (histo_n == HISTO_MAX) {
							// registro circular
							histo_n = 0;
						}
						fprintf(salida, "\n");
						genera_poblacion();
						double dist = distancia_clonacion();
						fprintf(salida, "%9d %12.5e %12.5e %6d\n", generacion, dist, mejor_merito, ind_mejor_merito);
						max_generaciones += generacion;
						mejor_merito_anterior = 1.0e+99;
						histogenera[histo_n] = generacion;
						histograma[histo_n] = mejor_merito_anterior;
						histo_n++;
						if (histo_n == HISTO_MAX) {
							// registro circular
							histo_n = 0;
						}
					}
					else {
						intentos--;
						histogenera[histo_n] = generacion;
						histograma[histo_n] = mejor_merito;
						return -3;
					}
				}
				else {
					mejor_merito_anterior = mejor_merito;
				}
			}
			else {
				mejor_merito_anterior = mejor_merito;
			}
		}
	}
	if (CANCELAR) {
		histogenera[histo_n] = generacion;
		histograma[histo_n] = mejor_merito;
		return -1;
	}
	return 0;
}
double distancia_clonacion() {
	double d;
	double des = 0.;
	for (int i = 0; i < NPOB; i++) {
		for (int j = 0; j < NVEC; j++) {
			d = poblacion[i][j] - poblacion[ind_mejor_merito][j];
			des += d * d;
		}
	}
	return des / (NPOB * NVEC);
}
/*
**********************************************************************************************************************************************************************************
Multi proceso con hilos cerrados. Cada hilo calcula un tramo de la población y el ciclo temporal espera a que terminen todos los hilos para continuar con la siguiente generación.
**********************************************************************************************************************************************************************************
*/
bool Arranque() {
	for (int i = 1; i < n_hilos; i++) {
		hgen[i] = mt19937(semilla + i);
		if (poner_el_mejor_primero) {
			hdis_entero[i] = uniform_int_distribution<int>{ 1, ((int)NPOB - 1) };
		}
		else {
			hdis_entero[i] = uniform_int_distribution<int>{ 0, ((int)NPOB - 1) };
		}
		hdis_entero_ivec[i] = uniform_int_distribution<int>{ 0, ((int)NVEC - 1) };
		hdis_double[i] = uniform_real_distribution<double>{ 0.0, 1.0 };
	}
	cte_recombinacion = (recombinacion[0] + recombinacion[1]) / 2.;
	CANCELADO = false;
	return true;
}
int PreparaMP() {
	// Comprobar la relación entre el número de hilos y el de la población

	int bloques = NPOB / n_hilos;
	if (bloques * n_hilos != NPOB) {
		//printf("Cancelado. El numero de individuos debe ser multiplo del numero de hilos\n");
		return -1;
	}
	if (!Arranque()) return -2;
	ProcesoMP(bloques);
	return 0;
}
int ProcesoMP(int bloques) {
	if (!InitializeCriticalSectionAndSpinCount(&seccion_fin_hilos, 0x00000400)) {
		fprintf(salida, "\nError [%d] creando la seccion critica fin_hilos\n", GetLastError());
		return 0;
	}

	// Crear el semaforo para iterar cerrado

	semaforo_itera = CreateSemaphore(NULL, 0, 1, NULL);
	if (semaforo_itera == NULL)
	{
		fprintf(salida, "\nError al crear el semaforo de iteracion: %d\n", GetLastError());
		return 0;
	}

	// Crear los semaforos para los hilos abiertos
	hilos_terminados = 0;
	for (int i = 0; i < n_hilos; i++) {
		semaforo_hilo[i] = CreateSemaphore(NULL, 1, 1, NULL);
		if (semaforo_hilo[i] == NULL)
		{
			fprintf(salida, "\nError al crear el semaforo para los hilos: %d\n", GetLastError());
			return 0;
		}
	}

	// tres parámetros para cada hilo

	int parametros_hilo[3 * MAX_HILOS]{};
	int conth = 0;
	for (int i = 0; i < n_hilos; i++) {
		// número de hilo
		parametros_hilo[conth++] = i;
		// primer individuo de la población del hilo
		parametros_hilo[conth] = i * bloques;
		if (i == 0 && poner_el_mejor_primero) {
			parametros_hilo[conth]++;
		}
		conth++;
		// primer individuo de la población del hilo siguiente
		if (i == n_hilos - 1) {
			parametros_hilo[conth] = NPOB;
		}
		else {
			parametros_hilo[conth++] = i * bloques + bloques;
		}
	}

	// Arranca los hilos con su semaforo abierto

	for (int i = 0; i < n_hilos; i++) {
		invalida_hilos[i] = false;
		hilos[i] = (HANDLE)_beginthreadex(0, 0, HiloTramos, parametros_hilo + 3 * (INT_PTR)i, 0, 0);

		// Para que los hilos comienzen a ejecutarse en orden

		Sleep(50);

		if (hilos[i] == 0) {
			fprintf(salida, "\nError al crear el hilo %d\n", i);
			return 0;
		}

		/*
		// dar la máxima prioridad al hilo dentro del proceso
		SetThreadPriority(hilos[i], THREAD_PRIORITY_HIGHEST);
		*/
	}

	// Arranca el ciclo temporal con el semaforo 'iterar' cerrado. Lo abre el ultimo hilo en terminar

	DWORD espera;
	while (!CANCELADO) {

		//printf("el hilo de iterar entra en espera\n");

		espera = WaitForSingleObject(semaforo_itera, INFINITE);

		//printf("el hilo de iterar sale de la espera\n");

		switch (espera)
		{
		case WAIT_OBJECT_0:

			// Los hilos han terminado de calcular los tramos

			//printf("todos los hilos han terminado de calcular\n");

			for (int i = 0; i < NPOB; i++) {
				if (merito_individuo[i] < mejor_merito) {
					mejor_merito = merito_individuo[i];
					ind_mejor_merito = i;
				}
			}
			if (poner_el_mejor_primero && ind_mejor_merito != 0) {
				recolocar_al_mejor(ind_mejor_merito);
			}
			res_Simulacion = comprobar_final();
			if (res_Simulacion < 0) {
				CANCELADO = true;
				break;
			}
			generacion++;
			if (generacion == max_generaciones) {
				histogenera[histo_n] = generacion;
				histograma[histo_n++] = mejor_merito;
				res_Simulacion = -5;
				CANCELADO = true;
				break;
			}
			cte_recombinacion = recombinacion[0] + dis_double(gen) * (recombinacion[1] - recombinacion[0]);
			if (!CANCELADO) {

				// Libera los hilos

				hilos_terminados = 0;
				for (int i = 0; i < n_hilos; i++) {

					//printf("orden de terminara la espera del hilo %d\n", i);

					while (ReleaseSemaphore(semaforo_hilo[i], 1, NULL) == FALSE);
				}
			}
			break;
		case WAIT_TIMEOUT:
			fprintf(salida, "El hilo %d: supero el tiempo de espera\n", GetCurrentThreadId());
			break;
		}
		if (CANCELADO) break;
	}
	CloseHandle(semaforo_itera);
	for (int i = 0; i < n_hilos; i++) {
		CloseHandle(hilos[i]);
		CloseHandle(semaforo_hilo[i]);
	}
	DeleteCriticalSection(&seccion_fin_hilos);
	return generacion;
}
unsigned int WINAPI HiloTramos(LPVOID param)
{
	int* parametros = (int*)param;
	int indice = parametros[0];
	int desde = parametros[1];
	int hasta = parametros[2];

	// Ciclo perpetuo

	DWORD resSemaforo;
	while (TRUE)
	{
		// pone en espera el hilo 'indice'

		//printf("el hilo %d entra en espera\n", indice);

		resSemaforo = WaitForSingleObject(semaforo_hilo[indice], INFINITE);

		//printf("el hilo %d sale de la espera\n", indice);

		switch (resSemaforo)
		{
		case WAIT_OBJECT_0:
			//printf("el hilo %d empieza a calcular\n", indice);

			ProcesarTramo(indice, desde, hasta);
			EnterCriticalSection(&seccion_fin_hilos);

			//printf("el hilo %d termina de calcular\n", indice);

			hilos_terminados++;
			if (hilos_terminados == n_hilos) {

				// Libera el semaforo para iterar

				//printf("orden de terminara la espera del hilo de iterar\n");

				while (ReleaseSemaphore(semaforo_itera, 1, NULL) == FALSE);
			}
			LeaveCriticalSection(&seccion_fin_hilos);
			break;
		case WAIT_TIMEOUT:
			fprintf(salida, "\nEl hilo %d superó el tiempo de espera\n", indice);
			break;
		}
	}
	return 0;
}
void ProcesarTramo(int hilo, int desde, int hasta) {
	mutacion_cruzeH(desde, hasta, hilo);
	seleccionH(desde, hasta);
}
#pragma endregion

#pragma region Merito
/*
longitud de las variables y punteros a estas, en el vector solución
  0    1    2    3      4        5    6   7   8   9   10
['pF','pY','pQ','pD','epsilon','Apz','F','E','M','D','Xp']
  1    6    6    6      1        1   12   6   6   6   12
*/
const int len_var[11] = { 1, NSEC, NSEC, NSEC, 1, 1, NSEC * NFAC, NSEC, NSEC, NSEC, NDEM * NSEC };
int pvec[12]{};

double AYD_ADI_DEM[NDEM]{};

OPCIONES recibe_opciones(OPCIONES vopt) {
	op = vopt;
	int n = sizeof(len_var) / sizeof(*len_var) + 1;
	pvec[0] = 0;
	for (int i = 1; i < n; i++) {
		pvec[i] = pvec[i - 1] + len_var[i - 1];
	}
	for (int i = 0; i < NDEM; i++) {
		AYD_ADI_DEM[i] = 0.;
		for (int j = 0; j < NSEC; j++) {
			AYD_ADI_DEM[i] += op.AYD_ADICIONAL[i][j];
		}
	}
	return op;
}

DATOS recibe_datos(DATOS vdat) {
	datos = vdat;
	return datos;
}

PARAMETROS recibe_parametros(PARAMETROS vpar) {
	/*
	// como puede haber alrededor de una tercera parte de valores 'ax' iguales a 0
	// guardamos los índices de los que no lo son, para usar solo estos en el cálculo de X
	ndc_ax = 0;
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NSEC; j++) {
			if (vpar.ax[i][j] > 0.0000001) {
				dc_ax[ndc_ax][0] = i;
				dc_ax[ndc_ax][1] = j;
				ndc_ax++;
			}
		}
	}
	*/
	parametros = vpar;
	return parametros;
}
/*
función objetivo multiproceso, la que hay que usar siempre, aunque no se utilice multiproceso
*/
double merito_s(double* vec_opt) {
	/*
	No se pueden poner restricciones a variables que no formen parte de 'vec_opt'
	una cosa es que no haya gradientes y otra que la función objetivo dependa de cosas distintas a sus variables
	el proceso de cruce va reduciendo, para cada variable, las diferencias, de su valor, entre los distintos individuos de la población
	*/
	double pf[NFAC];
	double py[NSEC];
	double pq[NSEC];
	double pd[NSEC];
	double F[NSEC][NFAC];
	double E[NSEC];
	double M[NSEC];
	double D[NSEC];

	double Fi[NSEC][NFAC];
	double Ei[NSEC];
	double Mi[NSEC];
	double Di[NSEC];
	double Xpi[NDEM][NSEC];

	double pe[NSEC];
	double pm[NSEC];
	double Yp[NSEC];
	double Z[NSEC];
	double X[NSEC][NSEC]{};
	double Yd[NSEC];
	double Ypd[NSEC];
	double pz[NSEC];
	double FF[NDEM][NFAC];
	double exceso[NDEM][NFAC];
	double Alp[NDEM][NFAC];
	double Td[NDEM];
	double Tz[NSEC];
	double Tm[NSEC];
	double Sp[NDEM];
	double AgE[NSEC];
	double AgH[NDEM];
	double CssE[NSEC];
	double CssH[NDEM];
	double Xg[NSEC];
	double Xv[NSEC];
	double Xp[NDEM][NSEC];
	double Q[NSEC];
	double Da[NSEC];
	double Dt[NSEC];

	double Fr[NSEC][NFAC];
	double Er[NSEC];
	double Mr[NSEC];
	double Ypr[NSEC];
	double Zr[NSEC];
	double Xr[NSEC][NSEC]{};
	double Ydr[NSEC];
	double FFr[NDEM][NFAC];
	double Alpr[NDEM][NFAC];
	double Tdr[NDEM];
	double Tzr[NSEC];
	double Tmr[NSEC];
	double Spr[NDEM];
	double AgEr[NSEC];
	double AgHr[NDEM];
	double CssEr[NSEC];
	double CssHr[NDEM];
	double Xgr[NSEC];
	double Xvr[NSEC];
	double Xpr[NDEM][NSEC];
	double Qr[NSEC];
	double Dar[NSEC];
	double Dtr[NSEC];

	double epsilon;
	double Apz;

	double Sg;
	double Sc;
	double Sf;
	double ebp;

	double Sgr;
	double Scr;
	double Sfr;
	double ebpr;

	double suma_F;
	double suma_FF;
	double sum_Xpr;
	double sum_Xr;

	std::copy(vec_opt + pvec[1], vec_opt + pvec[1] + len_var[1], py);
	std::copy(vec_opt + pvec[2], vec_opt + pvec[2] + len_var[2], pq);
	std::copy(vec_opt + pvec[3], vec_opt + pvec[3] + len_var[3], pd);
	epsilon = vec_opt[pvec[4]];
	Apz = vec_opt[pvec[5]];
	int n = pvec[6];
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			Fi[i][j] = F[i][j] = vec_opt[n++];
		}
	}
	std::copy(vec_opt + pvec[7], vec_opt + pvec[7] + len_var[7], E);
	std::copy(vec_opt + pvec[8], vec_opt + pvec[8] + len_var[8], M);
	std::copy(vec_opt + pvec[9], vec_opt + pvec[9] + len_var[9], D);
	if (op.GE_INCLUYE_XP) {
		int n = pvec[10];
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NSEC; j++) {
				Xpi[i][j] = vec_opt[n++];
			}
		}
	}
	std::copy(E, E + NSEC, Ei);
	std::copy(M, M + NSEC, Mi);
	std::copy(D, D + NSEC, Di);
	for (int i = 0; i < NSEC; i++) {
		pe[i] = datos.pWe[i] * epsilon;
		pm[i] = datos.pWm[i] * epsilon;
	}
	if (op.OR_PRE_EXCLUIDO == 1) {
		pf[0] = vec_opt[pvec[0]];
		if (op.VALOR_F_TRA == 0) {
			pf[1] = precio_factor_trabajo_pFL(op.INDICE_F_TRA, datos.PobAct, op.ALFA_PHILLIPS, datos.pF0[op.INDICE_F_TRA], datos.F0, F);
		}
		else {
			pf[1] = op.PRECIO_F_EXCLUIDO;
		}
	}
	else {
		pf[0] = op.PRECIO_F_EXCLUIDO;
		if (op.VALOR_F_TRA < 0) {
			pf[1] = vec_opt[pvec[0]];
		}
		else if (op.VALOR_F_TRA > 0) {
			pf[1] = op.VALOR_F_TRA;
		}
		else {
			pf[1] = precio_factor_trabajo_pFL(op.INDICE_F_TRA, datos.PobAct, op.ALFA_PHILLIPS, datos.pF0[op.INDICE_F_TRA], datos.F0, F);
		}
	}
	produccion_factor_compuesto_Y(Yp, F, parametros.beta, parametros.b);
	restriccion_produccion_bruta_Z(Z, parametros.teta, parametros.xie, parametros.xid, E, D, parametros.phi);
	consumo_intermedio_X(X, Z, parametros.ax);
	utilizacion_factor_compuesto_Y(Yd, Z, parametros.ay);
	for (int i = 0; i < NSEC; i++) {
		Ypd[i] = (Yp[i] + Yd[i]) / 2.;
	}
	uso_optimo_factores_F(F, parametros.beta, pf, py, Ypd);
	coste_unitario_produccion_pz(pz, parametros.ay, py, parametros.ax, pq);
	if (op.FF_ENDOGENA) {
		aportacion_factores_FF(FF, datos.FF0, F);
		if (op.ALP_FACTOR > 0) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					exceso[i][j] = FF[i][j] - datos.FF0[i][j];
					Alp[i][j] = exceso[i][j] * op.ALP_FACTOR;
					FF[i][j] -= Alp[i][j];
				}
			}
		}
		else {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					Alp[i][j] = datos.Alp0[i][j];
				}
			}
		}
	}
	else {
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NFAC; j++) {
				FF[i][j] = datos.FF0[i][j];
				Alp[i][j] = datos.Alp0[i][j];
			}
		}
	}
	impuestos_directos_Td(Td, parametros.taud, pf, FF, Alp, datos.PssH0);
	impuestos_produccion_Tz(Tz, datos.tauz, pz, Z);
	aranceles_importacion_Tm(Tm, datos.taum, pm, M);
	ayudas_AgE_AgH(AgE, AgH, parametros.cage, parametros.cagh, Td, Tz, Tm, datos.Tg0, datos.Ti0, datos.Te0, AYD_ADI_DEM);
	//ayudas_empresas_AgE(AgE, parametros.cage, Td, Tz, Tm, datos.Tg0, datos.Ti0, datos.Te0);
	//ayudas_hogares_AgH(AgH, parametros.cagh, Td, Tz, Tm, datos.Tg0, datos.Ti0, datos.Te0, AYD_ADI_DEM);
	ahorro_hogares_Sp(Sp, parametros.ssp, FF, pf, datos.PssH0);
	seguridad_social_empresas_CssE(CssE, parametros.ctzsse, pf, F, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssH, parametros.ctzssh, pf, FF, Alp, op.INDICE_F_TRA);
	Sg = gobierno_Sg_Xg(Xg, parametros.ssg, parametros.mu, pq, Td, Tz, Tm, datos.Tg0, datos.Ti0, datos.Te0, AgE, AgH, datos.PssH0, CssH, CssE);
	//Sg = ahorro_gobierno_Sg(parametros.ssg, Td, Tz, Tm, datos.Tg0, datos.Ti0, datos.Te0, AgE, AgH, datos.PssH0, CssH, CssE);
	//demanda_gobierno_Xg(Xg, parametros.mu, pq, Td, Tz, Tm, datos.Tg0, datos.Ti0, datos.Te0, Sg, AgE, AgH, datos.PssH0, CssH, CssE);
	double PssH0_sum = 0.;
	for (int i = 0; i < NDEM; i++) {
		PssH0_sum += datos.PssH0[i];
	}
	if (abs(PssH0_sum) < 0.000001) {
		Sc = 0.;
	}
	else {
		Sc = -PssH0_sum;
		for (int i = 0; i < NDEM; i++) {
			Sc += CssH[i];
		}
		for (int i = 0; i < NSEC; i++) {
			Sc += CssE[i];
		}
	}
	if (op.EQ_BAL_PAGOS) {
		Sf = datos.Sf0;
	}
	else {
		Sf = ahorro_exterior_Sf(M, E, pm, pe);
	}
	demanda_inversion_Xv(Xv, parametros.landa, pq, Sp, Sg, Sc, epsilon, Sf, datos.Ti0, datos.Te0);
	if (op.DEM_ESENCIALES) {
		demanda_maxima_utilidad_StoneGeary_Xp(Xp, parametros.alfa_esen, op.CON_ESENCIALES, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, op.DEM_ADICIONAL_TIPO, op.DEM_ADICIONAL, op.RENTA_FICTICIA);
	}
	else {
		if (op.UTILIDAD_DEMANDA == 0) {
			demanda_maxima_utilidad_CobbDouglas_Xp(Xp, parametros.alfa, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, op.DEM_ADICIONAL_TIPO, op.DEM_ADICIONAL, op.RENTA_FICTICIA);
		}
		else {
			demanda_maxima_utilidad_CES_Xp(Xp, parametros.eta_ces, parametros.alfa_ces, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, op.DEM_ADICIONAL_TIPO, op.DEM_ADICIONAL, op.RENTA_FICTICIA);
		}
	}
	produccion_armington_Q(Q, parametros.gamma, parametros.deltam, parametros.deltad, M, D, parametros.eta);
	importacion_maxima_utilidad_armington_M(M, parametros.gamma, parametros.deltam, pq, pm, Q, parametros.eta, datos.taum);
	produccion_maxima_utilidad_armington_D(Da, parametros.gamma, parametros.deltad, pq, pd, Q, parametros.eta);
	produccion_para_exportacion_E(E, parametros.teta, parametros.xie, pz, pe, Z, parametros.phi, datos.tauz, CssE, AgE, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	produccion_para_local_D(Dt, parametros.teta, parametros.xid, pz, pd, Z, parametros.phi, datos.tauz, CssE, AgE, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	if (op.EQ_BAL_PAGOS) {
		ebp = equilibrio_balance_pagos_moneda_extranjera(datos.pWe, E, datos.pWm, M, Sf);
	}
	else {
		ebp = 0.;
	}

	// -----------------------
	// segundo pase
	// -----------------------
	restriccion_produccion_bruta_Z(Zr, parametros.teta, parametros.xie, parametros.xid, E, Dt, parametros.phi);
	produccion_factor_compuesto_Y(Ypr, F, parametros.beta, parametros.b);
	uso_optimo_factores_F(Fr, parametros.beta, pf, py, Ypr);
	consumo_intermedio_X(Xr, Zr, parametros.ax);
	utilizacion_factor_compuesto_Y(Ydr, Zr, parametros.ay);
	if (op.FF_ENDOGENA) {
		aportacion_factores_FF(FFr, datos.FF0, Fr);
		if (op.ALP_FACTOR > 0) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					exceso[i][j] = FFr[i][j] - datos.FF0[i][j];
					Alpr[i][j] = exceso[i][j] * op.ALP_FACTOR;
					FFr[i][j] -= Alp[i][j];
				}
			}
		}
		else {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					Alpr[i][j] = datos.Alp0[i][j];
				}
			}
		}
	}
	else {
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NFAC; j++) {
				FFr[i][j] = datos.FF0[i][j];
				Alpr[i][j] = datos.Alp0[i][j];
			}
		}
	}
	impuestos_directos_Td(Tdr, parametros.taud, pf, FFr, Alpr, datos.PssH0);
	impuestos_produccion_Tz(Tzr, datos.tauz, pz, Zr);
	aranceles_importacion_Tm(Tmr, datos.taum, pm, M);
	ahorro_hogares_Sp(Spr, parametros.ssp, FFr, pf, datos.PssH0);
	ayudas_AgE_AgH(AgEr, AgHr, parametros.cage, parametros.cagh, Tdr, Tzr, Tmr, datos.Tg0, datos.Ti0, datos.Te0, AYD_ADI_DEM);
	//ayudas_empresas_AgE(AgEr, parametros.cage, Tdr, Tzr, Tmr, datos.Tg0, datos.Ti0, datos.Te0);
	//ayudas_hogares_AgH(AgHr, parametros.cagh, Tdr, Tzr, Tmr, datos.Tg0, datos.Ti0, datos.Te0, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssEr, parametros.ctzsse, pf, Fr, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssHr, parametros.ctzssh, pf, FFr, Alpr, op.INDICE_F_TRA);
	Sgr = gobierno_Sg_Xg(Xgr, parametros.ssg, parametros.mu, pq, Tdr, Tzr, Tmr, datos.Tg0, datos.Ti0, datos.Te0, AgEr, AgHr, datos.PssH0, CssHr, CssEr);
	//Sgr = ahorro_gobierno_Sg(parametros.ssg, Tdr, Tzr, Tmr, datos.Tg0, datos.Ti0, datos.Te0, AgEr, AgHr, datos.PssH0, CssHr, CssEr);
	//demanda_gobierno_Xg(Xgr, parametros.mu, pq, Tdr, Tzr, Tmr, datos.Tg0, datos.Ti0, datos.Te0, Sgr, AgEr, AgHr, datos.PssH0, CssHr, CssEr);
	if (abs(PssH0_sum) < 0.000001) {
		Scr = 0.;
	}
	else {
		Scr = -PssH0_sum;
		for (int i = 0; i < NDEM; i++) {
			Scr += CssHr[i];
		}
		for (int i = 0; i < NSEC; i++) {
			Scr += CssEr[i];
		}
	}
	if (op.EQ_BAL_PAGOS) {
		Sfr = datos.Sf0;
	}
	else {
		Sfr = ahorro_exterior_Sf(M, E, pm, pe);
	}
	demanda_inversion_Xv(Xvr, parametros.landa, pq, Spr, Sgr, Scr, epsilon, Sfr, datos.Ti0, datos.Te0);
	if (op.DEM_ESENCIALES) {
		demanda_maxima_utilidad_StoneGeary_Xp(Xpr, parametros.alfa_esen, op.CON_ESENCIALES, pq, pf, FFr, Spr, Tdr, CssHr, AgHr, datos.PssH0, op.DEM_ADICIONAL_TIPO, op.DEM_ADICIONAL, op.RENTA_FICTICIA);
	}
	else {
		if (op.UTILIDAD_DEMANDA == 0) {
			demanda_maxima_utilidad_CobbDouglas_Xp(Xpr, parametros.alfa, pq, pf, FFr, Spr, Tdr, CssHr, AgHr, datos.PssH0, op.DEM_ADICIONAL_TIPO, op.DEM_ADICIONAL, op.RENTA_FICTICIA);
		}
		else {
			demanda_maxima_utilidad_CES_Xp(Xpr, parametros.eta_ces, parametros.alfa_ces, pq, pf, FFr, Spr, Tdr, CssHr, AgHr, datos.PssH0, op.DEM_ADICIONAL_TIPO, op.DEM_ADICIONAL, op.RENTA_FICTICIA);
		}
	}
	produccion_armington_Q(Qr, parametros.gamma, parametros.deltam, parametros.deltad, M, Dt, parametros.eta);
	importacion_maxima_utilidad_armington_M(Mr, parametros.gamma, parametros.deltam, pq, pm, Qr, parametros.eta, datos.taum);
	produccion_maxima_utilidad_armington_D(Dar, parametros.gamma, parametros.deltad, pq, pd, Qr, parametros.eta);
	produccion_para_exportacion_E(Er, parametros.teta, parametros.xie, pz, pe, Zr, parametros.phi, datos.tauz, CssEr, AgEr, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	produccion_para_local_D(Dtr, parametros.teta, parametros.xid, pz, pd, Zr, parametros.phi, datos.tauz, CssEr, AgEr, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	if (op.EQ_BAL_PAGOS) {
		ebpr = equilibrio_balance_pagos_moneda_extranjera(datos.pWe, Er, datos.pWm, Mr, Sfr);
	}
	else {
		ebpr = 0.;
	}
	double dd;
	double dist = 0.;
	if (op.EQ_BAL_PAGOS) {
		dd = abs(ebp) + abs(ebpr);
	}
	else {
		dd = Sfr - Sf;
	}
	dist += dd * dd;

	for (int i = 0; i < NSEC; i++) {
		sum_Xpr = 0.;
		for (int j = 0; j < NDEM; j++) {
			sum_Xpr += Xpr[j][i];
		}
		sum_Xr = 0.;
		for (int j = 0; j < NSEC; j++) {
			sum_Xr += Xr[j][i];
		}
		dd = Qr[i] - (sum_Xpr + Xgr[i] + Xvr[i] + sum_Xr);
		dist += dd * dd;
	}
	if (op.FF_ENDOGENA) {
		if (op.ALP_FACTOR > 0) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					dd = Alpr[i][j] - Alp[i][j];
					dist += dd * dd;
				}
			}
		}
	}
	else {
		for (int i = 0; i < NFAC; i++) {
			suma_F = 0.;
			for (int j = 0; j < NSEC; j++) {
				suma_F += abs(Fr[j][i]);
			}
			suma_FF = 0.;
			for (int j = 0; j < NDEM; j++) {
				suma_FF += abs(FFr[j][i]);
			}
			dd = suma_F - suma_FF;
			dist += dd * dd;
		}
	}
	dd = Sgr - Sg;
	dist += dd * dd;
	for (int i = 0; i < NDEM; i++) {
		dd = Spr[i] - Sp[i];
		dist += dd * dd;
		dd = AgHr[i] - AgH[i];
		dist += dd * dd;
		dd = CssHr[i] - CssH[i];
		dist += dd * dd;
		dd = Tdr[i] - Td[i];
		dist += dd * dd;
		for (int j = 0; j < NFAC; j++) {
			dd = FFr[i][j] - FF[i][j];
			dist += dd * dd;
		}
		for (int j = 0; j < NSEC; j++) {
			if (op.GE_INCLUYE_XP) {
				dd = Xp[i][j] - Xpi[i][j];
				dist += dd * dd;
			}
			dd = Xpr[i][j] - Xp[i][j];
			dist += dd * dd;
		}
	}
	for (int i = 0; i < NSEC; i++) {
		dd = Er[i] - Ei[i];
		dist += dd * dd;
		dd = Mr[i] - Mi[i];
		dist += dd * dd;
		dd = Dar[i] - Di[i];
		dist += dd * dd;
		dd = Er[i] - E[i];
		dist += dd * dd;
		dd = Mr[i] - M[i];
		dist += dd * dd;
		dd = Ydr[i] - Ypr[i];
		dist += dd * dd;
		dd = Dar[i] - Dtr[i];
		dist += dd * dd;
		dd = Zr[i] - Z[i];
		dist += dd * dd;
		dd = Xgr[i] - Xg[i];
		dist += dd * dd;
		dd = Xvr[i] - Xv[i];
		dist += dd * dd;
		dd = Qr[i] - Q[i];
		dist += dd * dd;
		dd = Tzr[i] - Tz[i];
		dist += dd * dd;
		dd = Tmr[i] - Tm[i];
		dist += dd * dd;
		dd = AgEr[i] - AgE[i];
		dist += dd * dd;
		dd = CssEr[i] - CssE[i];
		dist += dd * dd;
		for (int j = 0; j < NFAC; j++) {
			dd = Fr[i][j] - Fi[i][j];
			dist += dd * dd;
			dd = Fr[i][j] - F[i][j];
			dist += dd * dd;
		}
		for (int j = 0; j < NSEC; j++) {
			dd = Xr[i][j] - X[i][j];
			dist += dd * dd;
		}
	}


	return dist;
}
/*
prepara los vectores 'me_sol' y 'VEC_OPT_E' con todas las variables del modelo, o las variables de la solución. Al
ser estas variables globales quedan en memoria a disposición de cualquier otra función, como 'soluciona', para
devolverlas a quien llame a la DLL.
no es multiproceso, porque 'me_sol' y 'VEC_OPT_E' son variables globales, pero es segura porque está pensada para ser llamada
una vez que el algoritmo genético ha terminado.
*/
double* merito_sol(double* vec_opt) {
	double pf[NFAC];
	double py[NSEC];
	double pq[NSEC];
	double pd[NSEC];
	double pe[NSEC];
	double pm[NSEC];
	double Fi[NSEC][NFAC];
	double Ei[NSEC];
	double Mi[NSEC];
	double Di[NSEC];
	double Xpi[NDEM][NSEC];

	double pz[NSEC];
	double exceso[NDEM][NFAC];
	double Ypd[NSEC];

	double F[NSEC][NFAC];
	double E[NSEC];
	double M[NSEC];
	double Da[NSEC];
	double Dt[NSEC];
	double Yp[NSEC];
	double Yd[NSEC];
	double Z[NSEC];
	double X[NSEC][NSEC]{};
	double FF[NDEM][NFAC];
	double Alp[NDEM][NFAC];
	double Td[NDEM];
	double Tz[NSEC];
	double Tm[NSEC];
	double Sp[NDEM];
	double AgE[NSEC];
	double AgH[NDEM];
	double CssE[NSEC];
	double CssH[NDEM];
	double Xg[NSEC];
	double Xv[NSEC];
	double Xp[NDEM][NSEC];
	double Q[NSEC];

	double Fr[NSEC][NFAC];
	double Er[NSEC];
	double Mr[NSEC];
	double Dar[NSEC];
	double Dtr[NSEC];
	double Ypr[NSEC];
	double Ydr[NSEC];
	double Zr[NSEC];
	double Xr[NSEC][NSEC]{};
	double FFr[NDEM][NFAC];
	double Alpr[NDEM][NFAC];
	double Tdr[NDEM];
	double Tzr[NSEC];
	double Tmr[NSEC];
	double Spr[NDEM];
	double AgEr[NSEC];
	double AgHr[NDEM];
	double CssEr[NSEC];
	double CssHr[NDEM];
	double Xgr[NSEC];
	double Xvr[NSEC];
	double Xpr[NDEM][NSEC];
	double Qr[NSEC];

	double epsilon;
	double Apz;

	double Sg;
	double Sc;
	double Sf;
	double ebp;

	double Sgr;
	double Scr;
	double Sfr;
	double ebpr;

	double suma_F;
	double suma_FF;
	double sum_Xpr;
	double sum_Xr;

	std::copy(vec_opt + pvec[1], vec_opt + pvec[1] + len_var[1], py);
	std::copy(vec_opt + pvec[2], vec_opt + pvec[2] + len_var[2], pq);
	std::copy(vec_opt + pvec[3], vec_opt + pvec[3] + len_var[3], pd);
	epsilon = vec_opt[pvec[4]];
	Apz = vec_opt[pvec[5]];
	int n = pvec[6];
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			Fi[i][j] = vec_opt[n];
			F[i][j] = vec_opt[n++];
		}
	}
	std::copy(vec_opt + pvec[7], vec_opt + pvec[7] + len_var[7], E);
	std::copy(vec_opt + pvec[8], vec_opt + pvec[8] + len_var[8], M);
	std::copy(vec_opt + pvec[9], vec_opt + pvec[9] + len_var[9], Di);
	if (op.GE_INCLUYE_XP) {
		int n = pvec[10];
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NSEC; j++) {
				Xpi[i][j] = vec_opt[n++];
			}
		}
	}
	std::copy(E, E + NSEC, Ei);
	std::copy(M, M + NSEC, Mi);
	for (int i = 0; i < NSEC; i++) {
		pe[i] = datos.pWe[i] * epsilon;
		pm[i] = datos.pWm[i] * epsilon;
	}
	if (op.OR_PRE_EXCLUIDO == 1) {
		pf[0] = vec_opt[pvec[0]];
		if (op.VALOR_F_TRA == 0) {
			pf[1] = precio_factor_trabajo_pFL(op.INDICE_F_TRA, datos.PobAct, op.ALFA_PHILLIPS, datos.pF0[op.INDICE_F_TRA], datos.F0, F);
		}
		else {
			pf[1] = op.PRECIO_F_EXCLUIDO;
		}
	}
	else {
		pf[0] = op.PRECIO_F_EXCLUIDO;
		if (op.VALOR_F_TRA < 0) {
			pf[1] = vec_opt[pvec[0]];
		}
		else if (op.VALOR_F_TRA > 0) {
			pf[1] = op.VALOR_F_TRA;
		}
		else {
			pf[1] = precio_factor_trabajo_pFL(op.INDICE_F_TRA, datos.PobAct, op.ALFA_PHILLIPS, datos.pF0[op.INDICE_F_TRA], datos.F0, F);
		}
	}
	produccion_factor_compuesto_Y(Yp, F, parametros.beta, parametros.b);
	restriccion_produccion_bruta_Z(Z, parametros.teta, parametros.xie, parametros.xid, E, Di, parametros.phi);
	consumo_intermedio_X(X, Z, parametros.ax);
	utilizacion_factor_compuesto_Y(Yd, Z, parametros.ay);
	for (int i = 0; i < NSEC; i++) {
		Ypd[i] = (Yp[i] + Yd[i]) / 2.;
	}
	uso_optimo_factores_F(F, parametros.beta, pf, py, Ypd);
	coste_unitario_produccion_pz(pz, parametros.ay, py, parametros.ax, pq);
	if (op.FF_ENDOGENA) {
		aportacion_factores_FF(FF, datos.FF0, F);
		if (op.ALP_FACTOR > 0) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					exceso[i][j] = FF[i][j] - datos.FF0[i][j];
					Alp[i][j] = exceso[i][j] * op.ALP_FACTOR;
					FF[i][j] -= Alp[i][j];
				}
			}
		}
		else {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					Alp[i][j] = datos.Alp0[i][j];
				}
			}
		}
	}
	else {
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NFAC; j++) {
				FF[i][j] = datos.FF0[i][j];
				Alp[i][j] = datos.Alp0[i][j];
			}
		}
	}
	impuestos_directos_Td(Td, parametros.taud, pf, FF, Alp, datos.PssH0);
	impuestos_produccion_Tz(Tz, datos.tauz, pz, Z);
	aranceles_importacion_Tm(Tm, datos.taum, pm, M);
	ayudas_AgE_AgH(AgE, AgH, parametros.cage, parametros.cagh, Td, Tz, Tm, datos.Tg0, datos.Ti0, datos.Te0, AYD_ADI_DEM);
	//ayudas_empresas_AgE(AgE, parametros.cage, Td, Tz, Tm, datos.Tg0, datos.Ti0, datos.Te0);
	//ayudas_hogares_AgH(AgH, parametros.cagh, Td, Tz, Tm, datos.Tg0, datos.Ti0, datos.Te0, AYD_ADI_DEM);
	ahorro_hogares_Sp(Sp, parametros.ssp, FF, pf, datos.PssH0);
	seguridad_social_empresas_CssE(CssE, parametros.ctzsse, pf, F, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssH, parametros.ctzssh, pf, FF, Alp, op.INDICE_F_TRA);
	Sg = gobierno_Sg_Xg(Xg, parametros.ssg, parametros.mu, pq, Td, Tz, Tm, datos.Tg0, datos.Ti0, datos.Te0, AgE, AgH, datos.PssH0, CssH, CssE);
	//Sg = ahorro_gobierno_Sg(parametros.ssg, Td, Tz, Tm, datos.Tg0, datos.Ti0, datos.Te0, AgE, AgH, datos.PssH0, CssH, CssE);
	//demanda_gobierno_Xg(Xg, parametros.mu, pq, Td, Tz, Tm, datos.Tg0, datos.Ti0, datos.Te0, Sg, AgE, AgH, datos.PssH0, CssH, CssE);
	double PssH0_sum = 0.;
	for (int i = 0; i < NDEM; i++) {
		PssH0_sum += datos.PssH0[i];
	}
	if (abs(PssH0_sum) < 0.000001) {
		Sc = 0.;
	}
	else {
		Sc = -PssH0_sum;
		for (int i = 0; i < NDEM; i++) {
			Sc += CssH[i];
		}
		for (int i = 0; i < NSEC; i++) {
			Sc += CssE[i];
		}
	}
	if (op.EQ_BAL_PAGOS) {
		Sf = datos.Sf0;
	}
	else {
		Sf = ahorro_exterior_Sf(M, E, pm, pe);
	}
	demanda_inversion_Xv(Xv, parametros.landa, pq, Sp, Sg, Sc, epsilon, Sf, datos.Ti0, datos.Te0);
	if (op.DEM_ESENCIALES) {
		demanda_maxima_utilidad_StoneGeary_Xp(Xp, parametros.alfa_esen, op.CON_ESENCIALES, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, op.DEM_ADICIONAL_TIPO, op.DEM_ADICIONAL, op.RENTA_FICTICIA);
	}
	else {
		if (op.UTILIDAD_DEMANDA == 0) {
			demanda_maxima_utilidad_CobbDouglas_Xp(Xp, parametros.alfa, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, op.DEM_ADICIONAL_TIPO, op.DEM_ADICIONAL, op.RENTA_FICTICIA);
		}
		else {
			demanda_maxima_utilidad_CES_Xp(Xp, parametros.eta_ces, parametros.alfa_ces, pq, pf, FF, Sp, Td, CssH, AgH, datos.PssH0, op.DEM_ADICIONAL_TIPO, op.DEM_ADICIONAL, op.RENTA_FICTICIA);
		}
	}
	produccion_armington_Q(Q, parametros.gamma, parametros.deltam, parametros.deltad, M, Di, parametros.eta);
	importacion_maxima_utilidad_armington_M(M, parametros.gamma, parametros.deltam, pq, pm, Q, parametros.eta, datos.taum);
	produccion_maxima_utilidad_armington_D(Da, parametros.gamma, parametros.deltad, pq, pd, Q, parametros.eta);
	produccion_para_exportacion_E(E, parametros.teta, parametros.xie, pz, pe, Z, parametros.phi, datos.tauz, CssE, AgE, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	produccion_para_local_D(Dt, parametros.teta, parametros.xid, pz, pd, Z, parametros.phi, datos.tauz, CssE, AgE, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	if (op.EQ_BAL_PAGOS) {
		ebp = equilibrio_balance_pagos_moneda_extranjera(datos.pWe, E, datos.pWm, M, Sf);
	}
	else {
		ebp = 0.;
	}

	// -----------------------
	// segundo pase
	// -----------------------
	restriccion_produccion_bruta_Z(Zr, parametros.teta, parametros.xie, parametros.xid, E, Dt, parametros.phi);
	produccion_factor_compuesto_Y(Ypr, F, parametros.beta, parametros.b);
	uso_optimo_factores_F(Fr, parametros.beta, pf, py, Ypr);
	consumo_intermedio_X(Xr, Zr, parametros.ax);
	utilizacion_factor_compuesto_Y(Ydr, Zr, parametros.ay);
	if (op.FF_ENDOGENA) {
		aportacion_factores_FF(FFr, datos.FF0, Fr);
		if (op.ALP_FACTOR > 0) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					exceso[i][j] = FFr[i][j] - datos.FF0[i][j];
					Alpr[i][j] = exceso[i][j] * op.ALP_FACTOR;
					FFr[i][j] -= Alp[i][j];
				}
			}
		}
		else {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					Alpr[i][j] = datos.Alp0[i][j];
				}
			}
		}
	}
	else {
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NFAC; j++) {
				FFr[i][j] = datos.FF0[i][j];
				Alpr[i][j] = datos.Alp0[i][j];
			}
		}
	}
	impuestos_directos_Td(Tdr, parametros.taud, pf, FFr, Alpr, datos.PssH0);
	impuestos_produccion_Tz(Tzr, datos.tauz, pz, Zr);
	aranceles_importacion_Tm(Tmr, datos.taum, pm, M);
	ahorro_hogares_Sp(Spr, parametros.ssp, FFr, pf, datos.PssH0);
	ayudas_AgE_AgH(AgEr, AgHr, parametros.cage, parametros.cagh, Tdr, Tzr, Tmr, datos.Tg0, datos.Ti0, datos.Te0, AYD_ADI_DEM);
	//ayudas_empresas_AgE(AgEr, parametros.cage, Tdr, Tzr, Tmr, datos.Tg0, datos.Ti0, datos.Te0);
	//ayudas_hogares_AgH(AgHr, parametros.cagh, Tdr, Tzr, Tmr, datos.Tg0, datos.Ti0, datos.Te0, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssEr, parametros.ctzsse, pf, Fr, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssHr, parametros.ctzssh, pf, FFr, Alpr, op.INDICE_F_TRA);
	Sgr = gobierno_Sg_Xg(Xgr, parametros.ssg, parametros.mu, pq, Tdr, Tzr, Tmr, datos.Tg0, datos.Ti0, datos.Te0, AgEr, AgHr, datos.PssH0, CssHr, CssEr);
	//Sgr = ahorro_gobierno_Sg(parametros.ssg, Tdr, Tzr, Tmr, datos.Tg0, datos.Ti0, datos.Te0, AgEr, AgHr, datos.PssH0, CssHr, CssEr);
	//demanda_gobierno_Xg(Xgr, parametros.mu, pq, Tdr, Tzr, Tmr, datos.Tg0, datos.Ti0, datos.Te0, Sgr, AgEr, AgHr, datos.PssH0, CssHr, CssEr);
	if (abs(PssH0_sum) < 0.000001) {
		Scr = 0.;
	}
	else {
		Scr = -PssH0_sum;
		for (int i = 0; i < NDEM; i++) {
			Scr += CssHr[i];
		}
		for (int i = 0; i < NSEC; i++) {
			Scr += CssEr[i];
		}
	}
	if (op.EQ_BAL_PAGOS) {
		Sfr = datos.Sf0;
	}
	else {
		Sfr = ahorro_exterior_Sf(M, E, pm, pe);
	}
	demanda_inversion_Xv(Xvr, parametros.landa, pq, Spr, Sgr, Scr, epsilon, Sfr, datos.Ti0, datos.Te0);
	if (op.DEM_ESENCIALES) {
		demanda_maxima_utilidad_StoneGeary_Xp(Xpr, parametros.alfa_esen, op.CON_ESENCIALES, pq, pf, FFr, Spr, Tdr, CssHr, AgHr, datos.PssH0, op.DEM_ADICIONAL_TIPO, op.DEM_ADICIONAL, op.RENTA_FICTICIA);
	}
	else {
		if (op.UTILIDAD_DEMANDA == 0) {
			demanda_maxima_utilidad_CobbDouglas_Xp(Xpr, parametros.alfa, pq, pf, FFr, Spr, Tdr, CssHr, AgHr, datos.PssH0, op.DEM_ADICIONAL_TIPO, op.DEM_ADICIONAL, op.RENTA_FICTICIA);
		}
		else {
			demanda_maxima_utilidad_CES_Xp(Xpr, parametros.eta_ces, parametros.alfa_ces, pq, pf, FFr, Spr, Tdr, CssHr, AgHr, datos.PssH0, op.DEM_ADICIONAL_TIPO, op.DEM_ADICIONAL, op.RENTA_FICTICIA);
		}
	}
	produccion_armington_Q(Qr, parametros.gamma, parametros.deltam, parametros.deltad, M, Dt, parametros.eta);
	importacion_maxima_utilidad_armington_M(Mr, parametros.gamma, parametros.deltam, pq, pm, Qr, parametros.eta, datos.taum);
	produccion_maxima_utilidad_armington_D(Dar, parametros.gamma, parametros.deltad, pq, pd, Qr, parametros.eta);
	produccion_para_exportacion_E(Er, parametros.teta, parametros.xie, pz, pe, Zr, parametros.phi, datos.tauz, CssEr, AgEr, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	produccion_para_local_D(Dtr, parametros.teta, parametros.xid, pz, pd, Zr, parametros.phi, datos.tauz, CssEr, AgEr, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	if (op.EQ_BAL_PAGOS) {
		ebpr = equilibrio_balance_pagos_moneda_extranjera(datos.pWe, Er, datos.pWm, Mr, Sfr);
	}
	else {
		ebpr = 0.;
	}
	// no se necesitan los 'abs' porque 'dd' se eleva al cuadrado, salvo en 'dd = abs(ebp) + abs(ebpr)'
	// pero esta función se llama una sola vez por lo que el incremento del tiempo de cálculo es insignificante
	double dd;
	double dist = 0.;
	int ndv = 0;
	if (op.EQ_BAL_PAGOS) {
		dd = abs(ebp) + abs(ebpr);
	}
	else {
		dd = abs(Sfr - Sf);
	}
	dist += dd * dd;
	// ebp / Sf
	desvios[ndv++] = dist;

	for (int i = 0; i < NSEC; i++) {
		sum_Xpr = 0.;
		for (int j = 0; j < NDEM; j++) {
			sum_Xpr += Xpr[j][i];
		}
		sum_Xr = 0.;
		for (int j = 0; j < NSEC; j++) {
			sum_Xr += Xr[j][i];
		}
		dd = abs(Qr[i] - (sum_Xpr + Xgr[i] + Xvr[i] + sum_Xr));
		dist += dd * dd;
	}
	// Q eq
	desvios[ndv++] = dist;
	if (op.FF_ENDOGENA) {
		// desvio en factores
		desvios[ndv++] = dist;

		// desvios Alp
		if (op.ALP_FACTOR > 0) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					dd = abs(Alpr[i][j] - Alp[i][j]);
					dist += dd * dd;
				}
			}
		}
		desvios[ndv++] = dist;
	}
	else {
		// desvio en factores
		for (int i = 0; i < NFAC; i++) {
			suma_F = 0.;
			for (int j = 0; j < NSEC; j++) {
				suma_F += abs(Fr[j][i]);
			}
			suma_FF = 0.;
			for (int j = 0; j < NDEM; j++) {
				suma_FF += abs(FFr[j][i]);
			}
			dd = abs(suma_F - suma_FF);
			dist += dd * dd;
		}
		desvios[ndv++] = dist;

		// desvios Alp
		desvios[ndv++] = dist;
	}
	dd = abs(Sgr - Sg);
	dist += dd * dd;
	// Sg
	desvios[ndv++] = dist;
	for (int i = 0; i < NDEM; i++) {
		dd = abs(Spr[i] - Sp[i]);
		dist += dd * dd;
	}
	// Sp
	desvios[ndv++] = dist;
	// vacante
	desvios[ndv++] = dist;
	for (int i = 0; i < NDEM; i++) {
		dd = abs(AgHr[i] - AgH[i]);
		dist += dd * dd;
	}
	// Agh
	desvios[ndv++] = dist;
	for (int i = 0; i < NDEM; i++) {
		dd = abs(CssHr[i] - CssH[i]);
		dist += dd * dd;
	}
	// CssH
	desvios[ndv++] = dist;
	for (int i = 0; i < NDEM; i++) {
		dd = abs(Tdr[i] - Td[i]);
		dist += dd * dd;
	}
	// Td
	desvios[ndv++] = dist;
	for (int i = 0; i < NDEM; i++) {
		for (int j = 0; j < NFAC; j++) {
			dd = abs(FFr[i][j] - FF[i][j]);
			dist += dd * dd;
		}
	}
	// FF
	desvios[ndv++] = dist;
	if (op.GE_INCLUYE_XP) {
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NSEC; j++) {
				dd = abs(Xpr[i][j] - Xpi[i][j]);
				dist += dd * dd;
			}
		}
	}
	// Xpi
	desvios[ndv++] = dist;
	for (int i = 0; i < NDEM; i++) {
		for (int j = 0; j < NSEC; j++) {
			dd = abs(Xpr[i][j] - Xp[i][j]);
			dist += dd * dd;
		}
	}
	// Xp
	desvios[ndv++] = dist;
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Er[i] - Ei[i]);
		dist += dd * dd;
	}
	// Ei
	desvios[ndv++] = dist;
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Mr[i] - Mi[i]);
		dist += dd * dd;
	}
	// Mi
	desvios[ndv++] = dist;
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Dar[i] - Di[i]);
		dist += dd * dd;
	}
	// Dai
	desvios[ndv++] = dist;
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Er[i] - E[i]);
		dist += dd * dd;
	}
	// E
	desvios[ndv++] = dist;
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Mr[i] - M[i]);
		dist += dd * dd;
	}
	// M
	desvios[ndv++] = dist;
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Ydr[i] - Ypr[i]);
		dist += dd * dd;
	}
	// Ydp
	desvios[ndv++] = dist;
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Dar[i] - Dtr[i]);
		dist += dd * dd;
	}
	// Dat
	desvios[ndv++] = dist;
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Zr[i] - Z[i]);
		dist += dd * dd;
	}
	// Z
	desvios[ndv++] = dist;
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Xgr[i] - Xg[i]);
		dist += dd * dd;
	}
	// Xg
	desvios[ndv++] = dist;
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Xvr[i] - Xv[i]);
		dist += dd * dd;
	}
	// Xv
	desvios[ndv++] = dist;
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Qr[i] - Q[i]);
		dist += dd * dd;
	}
	// Q
	desvios[ndv++] = dist;
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Tzr[i] - Tz[i]);
		dist += dd * dd;
	}
	// Tz
	desvios[ndv++] = dist;
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Tmr[i] - Tm[i]);
		dist += dd * dd;
	}
	// Tm
	desvios[ndv++] = dist;
	for (int i = 0; i < NSEC; i++) {
		dd = abs(AgEr[i] - AgE[i]);
		dist += dd * dd;
	}
	// Age
	desvios[ndv++] = dist;
	for (int i = 0; i < NSEC; i++) {
		dd = abs(CssEr[i] - CssE[i]);
		dist += dd * dd;
	}
	// CssE
	desvios[ndv++] = dist;
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			dd = abs(Fr[i][j] - Fi[i][j]);
			dist += dd * dd;
		}
	}
	// Fi
	desvios[ndv++] = dist;
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			dd = abs(Fr[i][j] - F[i][j]);
			dist += dd * dd;
		}
	}
	// F
	desvios[ndv++] = dist;
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NSEC; j++) {
			dd = abs(Xr[i][j] - X[i][j]);
			dist += dd * dd;
		}
	}
	// X
	desvios[ndv++] = dist;

	// cabecera + vectoe solución + valores para todas las demás variables

	// cabecera
	int nsol = 0;
	me_sol[nsol++] = 0;		// resultado
	me_sol[nsol++] = 0;		// número de datos
	me_sol[nsol++] = 0;		// intentos
	me_sol[nsol++] = 0;		// generaciones
	me_sol[nsol++] = dist;	// mérito

	// el vector solución inmediatamente después de la cabecera
	for (int i = 0; i < NFAC; i++)	me_sol[nsol++] = pf[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = py[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = pq[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = pd[i];
	me_sol[nsol++] = epsilon;
	me_sol[nsol++] = Apz;
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			me_sol[nsol++] = Fi[i][j];
		}
	}
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Ei[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Mi[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Di[i];
	if (op.GE_INCLUYE_XP) {
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NSEC; j++) {
				me_sol[nsol++] = Xpi[i][j];
			}
		}
	}
	// hasta aquí el vector solución

	// resto de variables
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = pz[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = pe[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = pm[i];
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			me_sol[nsol++] = F[i][j];
		}
	}
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = E[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = M[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Yp[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Yd[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Da[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Dt[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Z[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Xg[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Xv[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Q[i];
	for (int i = 0; i < NDEM; i++)	me_sol[nsol++] = Td[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Tz[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Tm[i];
	for (int i = 0; i < NDEM; i++)	me_sol[nsol++] = Sp[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = AgE[i];
	for (int i = 0; i < NDEM; i++)	me_sol[nsol++] = AgH[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = CssE[i];
	for (int i = 0; i < NDEM; i++)	me_sol[nsol++] = CssH[i];
	me_sol[nsol++] = Sg;
	me_sol[nsol++] = Sc;
	me_sol[nsol++] = Sf;
	me_sol[nsol++] = ebp;
	for (int i = 0; i < NDEM; i++) {
		for (int j = 0; j < NSEC; j++) {
			me_sol[nsol++] = Xp[i][j];
		}
	}
	for (int i = 0; i < NDEM; i++) {
		for (int j = 0; j < NFAC; j++) {
			me_sol[nsol++] = FF[i][j];
		}
	}
	for (int i = 0; i < NDEM; i++) {
		for (int j = 0; j < NFAC; j++) {
			me_sol[nsol++] = Alp[i][j];
		}
	}
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NSEC; j++) {
			me_sol[nsol++] = X[i][j];
		}
	}

	// los recálculos
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			me_sol[nsol++] = Fr[i][j];
		}
	}
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Er[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Mr[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Ypr[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Ydr[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Dar[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Dtr[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Zr[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Xgr[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Xvr[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Qr[i];
	for (int i = 0; i < NDEM; i++)	me_sol[nsol++] = Tdr[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Tzr[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Tmr[i];
	for (int i = 0; i < NDEM; i++)	me_sol[nsol++] = Spr[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = AgEr[i];
	for (int i = 0; i < NDEM; i++)	me_sol[nsol++] = AgHr[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = CssEr[i];
	for (int i = 0; i < NDEM; i++)	me_sol[nsol++] = CssHr[i];
	me_sol[nsol++] = Sgr;
	me_sol[nsol++] = Scr;
	me_sol[nsol++] = Sfr;
	me_sol[nsol++] = ebpr;
	for (int i = 0; i < NDEM; i++) {
		for (int j = 0; j < NSEC; j++) {
			me_sol[nsol++] = Xpr[i][j];
		}
	}
	for (int i = 0; i < NDEM; i++) {
		for (int j = 0; j < NFAC; j++) {
			me_sol[nsol++] = FFr[i][j];
		}
	}
	for (int i = 0; i < NDEM; i++) {
		for (int j = 0; j < NFAC; j++) {
			me_sol[nsol++] = Alpr[i][j];
		}
	}
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NSEC; j++) {
			me_sol[nsol++] = Xr[i][j];
		}
	}

	me_sol[1] = nsol;

	// cabecera	+ vector solucion + detalle desvios + evolución error
	nsol = 0;
	VEC_OPT_E[nsol++] = 0;		// resultado
	VEC_OPT_E[nsol++] = 0;		// número de datos
	VEC_OPT_E[nsol++] = 0;		// intentos
	VEC_OPT_E[nsol++] = 0;		// generaciones
	VEC_OPT_E[nsol++] = dist;	// mérito
	VEC_OPT_E[nsol++] = pf[0];
	VEC_OPT_E[nsol++] = pf[1];

	// vector solución
	for (int i = 1; i < NVEC; i++) {
		VEC_OPT_E[nsol++] = vec_opt[i];
	}
	VEC_OPT_E[1] = nsol;

	// desglose de las desviaciones
	VEC_OPT_E[nsol++] = ndv;
	for (int i = 0; i < ndv; i++) {
		VEC_OPT_E[nsol++] = desvios[i];
	}

	// evolución del error
	if (histo_int > 0) {
		VEC_OPT_E[nsol++] = HISTO_MAX;
		for (int i = 0; i < HISTO_MAX; i++) {
			VEC_OPT_E[nsol++] = histogenera[i];
			VEC_OPT_E[nsol++] = histograma[i];
		}
	}
	return me_sol;
}
/*
a continuación y hasta el final todas las ecuaciones del modelo.
*/
void produccion_factor_compuesto_Y(double* Y, double F[NSEC][NFAC], double beta[NSEC][NFAC], double* b) {
	for (int i = 0; i < NSEC; i++) {
		Y[i] = b[i];
		for (int j = 0; j < NFAC; j++) {
			Y[i] *= copysign(1.0, F[i][j]) * pow(abs(F[i][j]), beta[i][j]);
		}
	}
}
void restriccion_produccion_bruta_Z(double* Z, double* teta, double* xie, double* xid, double* E, double* D, double* phi) {
	double base;
	for (int i = 0; i < NSEC; i++) {
		base = xie[i] * copysign(1.0, E[i]) * pow(abs(E[i]), phi[i]) + xid[i] * copysign(1.0, D[i]) * pow(abs(D[i]), phi[i]);
		Z[i] = teta[i] * copysign(1.0, base) * pow(abs(base), (1. / phi[i]));
	}
}
void consumo_intermedio_X(double X[NSEC][NSEC], double* Z, double ax[NSEC][NSEC]) {
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NSEC; j++) {
			X[i][j] = ax[i][j] * Z[i];
		}
	}
}
/*
void consumo_intermedio_op_X(double X[NSEC][NSEC], double* Z, double ax[NSEC][NSEC]) {
	int i;
	int j;
	for (int n = 0; n < ndc_ax; n++) {
		i = dc_ax[n][0];
		j = dc_ax[n][1];
		X[i][j] = ax[i][j] * Z[i];
	}
}
*/
void utilizacion_factor_compuesto_Y(double* Y, double* Z, double* ay) {
	for (int i = 0; i < NSEC; i++) {
		Y[i] = ay[i] * Z[i];
	}
}
void uso_optimo_factores_F(double F[NSEC][NFAC], double beta[NSEC][NFAC], double* pf, double* py, double* Y) {
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			F[i][j] = beta[i][j] * py[i] * Y[i] / pf[j];
		}
	}
}
void coste_unitario_produccion_pz(double* pz, double* ay, double* py, double ax[NSEC][NSEC], double* pq) {
	for (int i = 0; i < NSEC; i++) {
		pz[i] = ay[i] * py[i];
		for (int j = 0; j < NSEC; j++) {
			pz[i] += ax[i][j] * pq[j];
		}
	}
}
void aportacion_factores_FF(double FF[NDEM][NFAC], double FF0[NDEM][NFAC], double F[NSEC][NFAC]) {
	double sfachog[NFAC]{};
	double sfacsec[NFAC]{};
	for (int j = 0; j < NFAC; j++) {
		sfachog[j] = 0.;
		for (int i = 0; i < NDEM; i++) {
			sfachog[j] += FF0[i][j];
		}
		sfacsec[j] = 0.;
		for (int i = 0; i < NSEC; i++) {
			sfacsec[j] += F[i][j];
		}
	}
	for (int i = 0; i < NDEM; i++) {
		for (int j = 0; j < NFAC; j++) {
			FF[i][j] = sfacsec[j] * FF0[i][j] / sfachog[j];
		}
	}
}
void impuestos_directos_Td(double* Td, double* taud, double* pf, double FF[NDEM][NFAC], double Alp[NDEM][NFAC], double* PssH0) {
	double ingresos;
	for (int i = 0; i < NDEM; i++) {
		ingresos = PssH0[i];
		for (int j = 0; j < NFAC; j++) {
			ingresos += (FF[i][j] + Alp[i][j]) * pf[j];
		}
		Td[i] = taud[i] * ingresos;
	}
}
void impuestos_produccion_Tz(double* Tz, double* tauz, double* pz, double* Z) {
	for (int i = 0; i < NSEC; i++) {
		Tz[i] = tauz[i] * Z[i] * pz[i];
	}
}
void aranceles_importacion_Tm(double* Tm, double* taum, double* pm, double* M) {
	for (int i = 0; i < NSEC; i++) {
		Tm[i] = taum[i] * M[i] * pm[i];
	}
}
void ayudas_AgE_AgH(double* AgE, double* AgH, double* cage, double* cagh, double* Td, double* Tz, double* Tm, double Tg, double Ti, double Te, double* AYD_ADI_DEM) {
	double ingresos = Ti + Te;
	for (int i = 0; i < NDEM; i++) {
		ingresos += Td[i];
	}
	for (int i = 0; i < NSEC; i++) {
		ingresos += Tz[i] + Tm[i];
	}
	for (int i = 0; i < NSEC; i++) {
		AgE[i] = cage[i] * ingresos;
	}
	for (int i = 0; i < NDEM; i++) {
		AgH[i] = cagh[i] * ingresos + AYD_ADI_DEM[i];
	}
}

void ayudas_empresas_AgE(double* AgE, double* cage, double* Td, double* Tz, double* Tm, double Tg, double Ti, double Te) {
	double ingresos = Ti + Te;
	for (int i = 0; i < NDEM; i++) {
		ingresos += Td[i];
	}
	for (int i = 0; i < NSEC; i++) {
		ingresos += Tz[i] + Tm[i];
	}
	for (int i = 0; i < NSEC; i++) {
		AgE[i] = cage[i] * ingresos;
	}
}
void ayudas_hogares_AgH(double* AgH, double* cagh, double* Td, double* Tz, double* Tm, double Tg, double Ti, double Te, double* AYD_ADI_DEM) {
	double ingresos = Ti + Te;
	for (int i = 0; i < NDEM; i++) {
		ingresos += Td[i];
	}
	for (int i = 0; i < NSEC; i++) {
		ingresos += Tz[i] + Tm[i];
	}
	for (int i = 0; i < NDEM; i++) {
		AgH[i] = cagh[i] * ingresos + AYD_ADI_DEM[i];
	}
}

void ahorro_hogares_Sp(double* Sp, double* ssp, double FF[NDEM][NFAC], double* pf, double* PssH0) {

	// parece que faltan los Alp

	double ingresos;
	for (int i = 0; i < NDEM; i++) {
		ingresos = PssH0[i];
		for (int j = 0; j < NFAC; j++) {
			ingresos += FF[i][j] * pf[j];
		}
		Sp[i] = ssp[i] * ingresos;
	}
}
void seguridad_social_empresas_CssE(double* CssE, double* ctzsse, double* pf, double F[NSEC][NFAC], int INDICE_F_TRA) {
	for (int i = 0; i < NSEC; i++) {
		CssE[i] = ctzsse[i] * F[i][INDICE_F_TRA] * pf[INDICE_F_TRA];
	}
}
void seguridad_social_hogares_CssH(double* CssH, double* ctzssh, double* pf, double FF[NDEM][NFAC], double Alp[NDEM][NFAC], int INDICE_F_TRA) {
	for (int i = 0; i < NDEM; i++) {
		CssH[i] = ctzssh[i] * (FF[i][INDICE_F_TRA] + Alp[i][INDICE_F_TRA]) * pf[INDICE_F_TRA];
	}
}
double gobierno_Sg_Xg(double* Xg, double ssg, double* mu, double* pq, double* Td, double* Tz, double* Tm, double Tg, double Ti, double Te, double* AgE, double* AgH, double* PssH0, double* CssH, double* CssE) {
	double Sg;
	double sPssH = 0.;
	for (int i = 0; i < NDEM; i++) {
		sPssH += PssH0[i];
	}
	double Css = 0.;
	if (abs(sPssH) < 0.000001) {
		for (int i = 0; i < NDEM; i++) {
			Css += CssH[i];
		}
		for (int i = 0; i < NSEC; i++) {
			Css += CssE[i];
		}
	}
	double neto = Ti + Te + Css;
	for (int i = 0; i < NDEM; i++) {
		neto += (Td[i] - AgH[i]);
	}
	for (int i = 0; i < NSEC; i++) {
		neto += (Tz[i] + Tm[i] - AgE[i]);
	}
	Sg = ssg * neto;
	neto -= Sg;
	for (int i = 0; i < NSEC; i++) {
		Xg[i] = mu[i] * neto / pq[i];
	}
	return Sg;
}

double ahorro_gobierno_Sg(double ssg, double* Td, double* Tz, double* Tm, double Tg, double Ti, double Te, double* AgE, double* AgH, double* PssH0, double* CssH, double* CssE) {
	double sPssH = 0.;
	for (int i = 0; i < NDEM; i++) {
		sPssH += PssH0[i];
	}
	double Css = 0.;
	if (abs(sPssH) < 0.000001) {
		for (int i = 0; i < NDEM; i++) {
			Css += CssH[i];
		}
		for (int i = 0; i < NSEC; i++) {
			Css += CssE[i];
		}
	}
	double neto = Ti + Te + Css;
	for (int i = 0; i < NDEM; i++) {
		neto += (Td[i] - AgH[i]);
	}
	for (int i = 0; i < NSEC; i++) {
		neto += (Tz[i] + Tm[i] - AgE[i]);
	}
	return ssg * neto;
}
void demanda_gobierno_Xg(double* Xg, double* mu, double* pq, double* Td, double* Tz, double* Tm, double Tg, double Ti, double Te, double Sg, double* AgE, double* AgH, double* PssH0, double* CssH, double* CssE) {
	double sPssH = 0.;
	for (int i = 0; i < NDEM; i++) {
		sPssH += PssH0[i];
	}
	double Css = 0.;
	if (abs(sPssH) < 0.000001) {
		for (int i = 0; i < NDEM; i++) {
			Css += CssH[i];
		}
		for (int i = 0; i < NSEC; i++) {
			Css += CssE[i];
		}
	}
	double neto = Ti + Te + Css - Sg;
	for (int i = 0; i < NDEM; i++) {
		neto += (Td[i] - AgH[i]);
	}
	for (int i = 0; i < NSEC; i++) {
		neto += (Tz[i] + Tm[i] - AgE[i]);
	}
	for (int i = 0; i < NSEC; i++) {
		Xg[i] = mu[i] * neto / pq[i];
	}
}

double ahorro_exterior_Sf(double* M, double* E, double* pm, double* pe) {
	double Sf = 0.;
	for (int i = 0; i < NSEC; i++) {
		Sf += M[i] * pm[i] - E[i] * pe[i];
	}
	return Sf;
}
void demanda_inversion_Xv(double* Xv, double* landa, double* pq, double* Sp, double Sg, double Sc, double epsilon, double Sf, double Ti, double Te) {
	// no se usa Te
	double ahorros = Sg + Sc + Sf * epsilon - Ti;
	for (int i = 0; i < NDEM; i++) {
		ahorros += Sp[i];
	}
	for (int i = 0; i < NSEC; i++) {
		Xv[i] = ahorros * landa[i] / pq[i];
	}
}
void demanda_maxima_utilidad_StoneGeary_Xp(double Xp[NDEM][NSEC], double alfa_esen[NDEM][NSEC], double CON_ESENCIALES[NDEM][NSEC], double* pq, double* pf, double FF[NDEM][NFAC], double* Sp, double* Td, double* CssH, double* AgH, double* PssH0, int DEM_ADICIONAL_TIPO, double DEM_ADICIONAL[NDEM][NSEC], bool RENTA_FICTICIA) {
	double ingreso_neto[NDEM]{};
	for (int i = 0; i < NDEM; i++) {
		ingreso_neto[i] = AgH[i] + PssH0[i] - (Sp[i] + Td[i] + CssH[i]);
		for (int j = 0; j < NFAC; j++) {
			ingreso_neto[i] += FF[i][j] * pf[j];
		}
		if (RENTA_FICTICIA == false) {
			for (int k = 0; k < NSEC; k++) {
				if (DEM_ADICIONAL_TIPO == 0) {
					ingreso_neto[i] -= DEM_ADICIONAL[i][k];
				}
				else {
					ingreso_neto[i] -= DEM_ADICIONAL[i][k] * pq[k];
				}
			}
		}
	}
	double gasto_esencial[NDEM]{};
	for (int i = 0; i < NDEM; i++) {
		gasto_esencial[i] = 0.;
		for (int k = 0; k < NSEC; k++) {
			gasto_esencial[i] += CON_ESENCIALES[i][k] * pq[k];
		}
	}
	double renta_disponible[NDEM]{};
	for (int i = 0; i < NDEM; i++) {
		renta_disponible[i] = ingreso_neto[i] - gasto_esencial[i];
	}
	for (int i = 0; i < NDEM; i++) {
		for (int k = 0; k < NSEC; k++) {
			if (DEM_ADICIONAL_TIPO == 0) {
				Xp[i][k] = CON_ESENCIALES[i][k] + (alfa_esen[i][k] * renta_disponible[i] + DEM_ADICIONAL[i][k]) / pq[k];
			}
			else {
				Xp[i][k] = CON_ESENCIALES[i][k] + alfa_esen[i][k] * renta_disponible[i] + DEM_ADICIONAL[i][k];
			}
		}
	}
}
void demanda_maxima_utilidad_CobbDouglas_Xp(double Xp[NDEM][NSEC], double alfa[NDEM][NSEC], double* pq, double* pf, double FF[NDEM][NFAC], double* Sp, double* Td, double* CssH, double* AgH, double* PssH0, int DEM_ADICIONAL_TIPO, double DEM_ADICIONAL[NDEM][NSEC], bool RENTA_FICTICIA) {
	double ingreso_neto[NDEM];
	for (int i = 0; i < NDEM; i++) {
		ingreso_neto[i] = AgH[i] + PssH0[i] - (Sp[i] + Td[i] + CssH[i]);
		for (int j = 0; j < NFAC; j++) {
			ingreso_neto[i] += FF[i][j] * pf[j];
		}
		if (RENTA_FICTICIA == false) {
			for (int k = 0; k < NSEC; k++) {
				if (DEM_ADICIONAL_TIPO == 0) {
					ingreso_neto[i] -= DEM_ADICIONAL[i][k];
				}
				else {
					ingreso_neto[i] -= DEM_ADICIONAL[i][k] * pq[k];
				}
			}
		}
		for (int k = 0; k < NSEC; k++) {
			Xp[i][k] = alfa[i][k] * ingreso_neto[i] / pq[k];
			if (DEM_ADICIONAL_TIPO == 0) {
				Xp[i][k] += DEM_ADICIONAL[i][k] / pq[k];
			}
			else {
				Xp[i][k] += DEM_ADICIONAL[i][k];
			}
		}
	}
}
void demanda_maxima_utilidad_CES_Xp(double Xp[NDEM][NSEC], double* eta_ces, double alfa_ces[NDEM][NSEC], double* pq, double* pf, double FF[NDEM][NFAC], double* Sp, double* Td, double* CssH, double* AgH, double* PssH0, int DEM_ADICIONAL_TIPO, double DEM_ADICIONAL[NDEM][NSEC], bool RENTA_FICTICIA) {
	double sigma[NDEM];
	double uno_sigma[NDEM];
	double S[NDEM];
	double ingreso_neto[NDEM];
	for (int i = 0; i < NDEM; i++) {
		ingreso_neto[i] = AgH[i] + PssH0[i] - (Sp[i] + Td[i] + CssH[i]);
		for (int j = 0; j < NFAC; j++) {
			ingreso_neto[i] += FF[i][j] * pf[j];
		}
		if (RENTA_FICTICIA == false) {
			for (int k = 0; k < NSEC; k++) {
				if (DEM_ADICIONAL_TIPO == 0) {
					ingreso_neto[i] -= DEM_ADICIONAL[i][k];
				}
				else {
					ingreso_neto[i] -= DEM_ADICIONAL[i][k] * pq[k];
				}
			}
		}
		sigma[i] = 1. / (1. - eta_ces[i]);
		uno_sigma[i] = 1. - sigma[i];
		S[i] = 0.;
		for (int k = 0; k < NSEC; k++) {
			S[i] += pow(alfa_ces[i][k], sigma[i]) * pow(pq[k], uno_sigma[i]);
		}
		for (int k = 0; k < NSEC; k++) {
			Xp[i][k] = ingreso_neto[i] * pow((alfa_ces[i][k] / pq[k]), sigma[i]) / S[i];
			if (DEM_ADICIONAL_TIPO == 0) {
				Xp[i][k] += DEM_ADICIONAL[i][k] / pq[k];
			}
			else {
				Xp[i][k] += DEM_ADICIONAL[i][k];
			}
		}
	}
}
void produccion_armington_Q(double* Q, double* gamma, double* deltam, double* deltad, double* M, double* D, double* eta) {
	for (int i = 0; i < NSEC; i++) {
		Q[i] = gamma[i] * pow(deltam[i] * copysign(1.0, M[i]) * pow(abs(M[i]), eta[i]) + deltad[i] * copysign(1.0, D[i]) * pow(abs(D[i]), eta[i]), 1. / eta[i]);
	}
}
void importacion_maxima_utilidad_armington_M(double* M, double* gamma, double* deltam, double* pq, double* pm, double* Q, double* eta, double* taum) {
	for (int i = 0; i < NSEC; i++) {
		M[i] = Q[i] * pow(pow(gamma[i], eta[i]) * deltam[i] * pq[i] / ((1. + taum[i]) * pm[i]), 1. / (1. - eta[i]));
	}
}
void produccion_maxima_utilidad_armington_D(double* Da, double* gamma, double* deltad, double* pq, double* pd, double* Q, double* eta) {
	for (int i = 0; i < NSEC; i++) {
		Da[i] = Q[i] * pow(pow(gamma[i], eta[i]) * deltad[i] * pq[i] / pd[i], 1. / (1. - eta[i]));
	}
}
void produccion_para_exportacion_E(double* E, double* teta, double* xie, double* pz, double* pe, double* Z, double* phi, double* tauz, double* CssE, double* AgE, double Apz, double* ctzssez, double* ctzagez, int MODO_PSEUDOIMPTOS) {
	double base;
	double s_teta;
	double b_teta;
	double expo;
	for (int i = 0; i < NSEC; i++) {
		if (xie[i] > 0.000001) {
			s_teta = copysign(1.0, teta[i]);
			b_teta = abs(teta[i]);
			if (MODO_PSEUDOIMPTOS == 0) {
				base = s_teta * pow(b_teta, phi[i]) * (1. + tauz[i] + (CssE[i] - AgE[i]) / Z[i] + Apz) * pz[i] * xie[i] / pe[i];
			}
			else {
				base = s_teta * pow(b_teta, phi[i]) * (1. + tauz[i] + ctzssez[i] - ctzagez[i] + Apz) * pz[i] * xie[i] / pe[i];
			}
			expo = 1. / (1. - phi[i]);
			E[i] = Z[i] * copysign(1.0, base) * pow(abs(base), expo);
		}
		else {
			E[i] = 0.;
		}
	}
}
void produccion_para_local_D(double* Dt, double* teta, double* xid, double* pz, double* pd, double* Z, double* phi, double* tauz, double* CssE, double* AgE, double Apz, double* ctzssez, double* ctzagez, int MODO_PSEUDOIMPTOS) {
	double base;
	double s_teta;
	double b_teta;
	double expo;
	for (int i = 0; i < NSEC; i++) {
		if (xid[i] > 0.000001) {
			s_teta = copysign(1.0, teta[i]);
			b_teta = abs(teta[i]);
			if (MODO_PSEUDOIMPTOS == 0) {
				base = s_teta * pow(b_teta, phi[i]) * (1. + tauz[i] + (CssE[i] - AgE[i]) / Z[i] + Apz) * pz[i] * xid[i] / pd[i];
			}
			else {
				base = s_teta * pow(b_teta, phi[i]) * (1. + tauz[i] + ctzssez[i] - ctzagez[i] + Apz) * pz[i] * xid[i] / pd[i];
			}
			expo = 1. / (1. - phi[i]);
			Dt[i] = Z[i] * copysign(1.0, base) * pow(abs(base), expo);
		}
		else {
			Dt[i] = 0.;
		}
	}
}
double equilibrio_balance_pagos_moneda_extranjera(double* pWe, double* E, double* pWm, double* M, double Sf) {
	double ebp = Sf;
	for (int i = 0; i < NSEC; i++) {
		ebp += pWe[i] * E[i] - pWm[i] * M[i];
	}
	return ebp;
}
double precio_factor_trabajo_pFL(int INDICE_F_TRA, double PobAct, double alfa, double pF0L, double F0[NSEC][NFAC], double F[NSEC][NFAC]) {
	double var_desempleo = 0.;
	for (int i = 0; i < NSEC; i++) {
		var_desempleo += F0[i][INDICE_F_TRA] - F[i][INDICE_F_TRA];
	}
	var_desempleo /= PobAct;
	return pF0L + alfa * var_desempleo;
}
#pragma endregion

