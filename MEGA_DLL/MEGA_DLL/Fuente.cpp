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
#include <sys\timeb.h> 

#ifdef INI_AZAR_FICHERO
#include <fstream>
#include <array>
#include <functional>
#include <iterator>
#endif

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
// no parece que ahorre tiempo, más bien al contrario
#ifdef CONSUMO_INTERMEDIO_INDESADO
int ndc_ax;
int dc_ax[NSEC * NSEC][2]{};	// índices i,j de los elementos de ax distintos de cero
#endif
/*
longitud de las variables y punteros a estas, en el vector solución
  0    1    2    3      4        5    6   7   8   9   10
['pF','pY','pQ','pD','epsilon','Apz','F','E','M','D','Xp']
*/
const int N_BLO_VEC = 11;
const char* rot_blo_vec[N_BLO_VEC + 1] = {
"pF",
"pY",
"pQ",
"pD",
"epsilon",
"Apz",
"F",
"E",
"M",
"D",
"Xp",
"fin"
};
const int len_var[N_BLO_VEC] = { 1, NSEC, NSEC, NSEC, 1, 1, NSEC * NFAC, NSEC, NSEC, NSEC, NDEM * NSEC };
int pvec[N_BLO_VEC + 1]{};

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
		1 máxima desviación
		1 indice variable con la máxima desviación
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

primer pase

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
		1 Sf
		1 ebp
NDEM*NSEC Xp
NDEM*NFAC FF
NDEM*NFAC Alp
NSEC*NSEC X
		1 Ti

segundo pase

NSEC*NFAC Fr
	 NSEC Er;
	 NSEC Mr;
	 NSEC Ypr;
	 NSEC Ydr;
	 NSEC Dar;
	 NSEC Dtr;
	 NSEC Zr;
	 NSEC Xgr;
	 NSEC Xvr;
	 NSEC Qr;
	 NDEM Tdr;
	 NSEC Tzr;
	 NSEC Tmr;
	 NDEM Spr;
	 NSEC AgEr;
	 NDEM AgHr;
	 NSEC CssEr;
	 NDEM CssHr;
		1 Sgr;
		1 Scr;
		1 Sfr;
		1 ebpr;
NDEM*NSEC Xpr;
NDEM*NFAC FFr;
NDEM*NFAC Alpr;
NSEC*NSEC Xr;
		1 Tir
*/

// longitud cabecera
const int LCAB =
1 +
1 +
1 +
1 +
1 +
1 +
1
;

const int LSOL =
// longitud vector solución, incluidos 2 factores e incluida Xpi
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
// Xpi
NDEM * NSEC;

// longitud variables primer pase
const int LVARS_PP =
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
1
;
// longitud variables recalculadas
const int LVARS_SP =
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
NSEC * NSEC +
1
;
const int LVAR =
// cabecera
LCAB +
// vector solución
LSOL +
// variables primer pase
LVARS_PP +
// variables recalculadas
LVARS_SP;

double me_sol[LVAR]{};

/*
'VEC_OPT_E' igual que 'me_sol' pero solo guarda el vector solución, que es lo realmente útil ya que valor del resto
de las variables se puede obtener a partir del vector solución mediante las ecuaciones del modelo
*/
const int LVSOL =
// cabecera
LCAB +
// vector solución
LSOL +
// desviaciones por bloque (un máximo de 64 para futuras ampliaciones)
64 +
// evolución del mérito y de la desviación máxima
2 * HISTO_MAX
;

double VEC_OPT_E[LVSOL]{};

const int MAX_DESVIOS_BLOQUE = 64;
double desvios_bloque[MAX_DESVIOS_BLOQUE];

// MAX_ROT_DESVIOS_BLOQUE debería ser igual a MAX_DESVIOS_BLOQUE, pero este último lo tenemos sobredimensionado para facilitar su ampliación si fuera necesario
// MAX_ROT_DESVIOS_BLOQUE está ajustado porque hay que definir los rótulos de los bloques de forma exacta
const int MAX_ROT_DESVIOS_BLOQUE = 37;
const char* rot_desvios[MAX_ROT_DESVIOS_BLOQUE] = {
"ebp",
"Qeq",
"F-FF",
"Alp",
"Sg",
"Sp",
"vacante",
"Agh",
"CssH",
"Td",
"FF",
"Xpi",
"Xp",
"Ei",
"Mi",
"Dai",
"E",
"M",
"Ydp",
"Dat",
"Z",
"Xg",
"Xv",
"Q",
"Tz",
"Tm",
"AgE",
"CssE",
"Fi",
"F",
"X",
"Ti",
"Yp",
"Yd",
"Da",
"Dt",
"fin"
};
int puntero_bloque_desviacion = 0;
int desplazamiento_desviacion = 0;
#ifdef COMPROBAR_MAX_DESVIACION
int ind_bloque_desviacion[MAX_BLOQUES_DESVIOS];
#endif

#pragma region Genetico

/*
convertimos en matrices (vectores) las variables que cada hilo debe
utilizar de forma independiente de los otros hilos para evitar que colisionen.
para poder usar matrices fijas, definimos la constante MAX_HILOS en 128 y aunque desperdiciemos
memoria, es insignificante
*/
const int MAX_HILOS = 128;
HANDLE hilos[MAX_HILOS]{};
HANDLE semaforo_hilo[MAX_HILOS]{};
HANDLE semaforo_itera;
CRITICAL_SECTION seccion_fin_hilos;
int n_hilos;
int hilos_terminados;
bool CANCELADO;

/*
Los números aleatorios se usan en la generación de la población inicial y en la mutación de individuos
lo primero se hace en un solo hilo (el hilo principal), pero la mutación se hace en varios hilos, por lo
que cada hilo debe tener su propio generador de números aleatorios.
*/
#ifdef AZAR_HILOS_LOCAL

// mediante variables locales 'thread_local' 
// por eso solo definimos el vector 'hgen' con tamaño 1 para el caso mono proceso
#ifdef MT19937
static mt19937 hgen[1]{};
#else
static minstd_rand hgen[1]{};
#endif
/*
En cuanto a las funciones de distribución, no parece necesario que cada hilo tenga la suya propia, parece
que es suficiente con que el generador de números aleatorios sea diferente para cada hilo
*/
static uniform_int_distribution<int> hdis_entero{};
static uniform_int_distribution<int> hdis_entero_ivec{};
static uniform_real_distribution<double> hdis_double{};

#else AZAR_HILOS_LOCAL

// mediante un vector global de generadores de números aleatorios, cada hilo usa el suyo propio
#ifdef MT19937
static mt19937 hgen[MAX_HILOS]{};
#else
static minstd_rand hgen[MAX_HILOS]{};
#endif
/*
En cuanto a las funciones de distribución, no parece necesario que cada hilo tenga la suya propia, parece
que es suficiente con que el generador de números aleatorios sea diferente para cada hilo
*/
static uniform_int_distribution<int> hdis_entero{};
static uniform_int_distribution<int> hdis_entero_ivec{};
static uniform_real_distribution<double> hdis_double{};

#endif AZAR_HILOS_LOCAL

#ifdef ESTA_CRUCES
long long num_cruces_si[MAX_HILOS]{};
long long num_cruces_ok[MAX_HILOS]{};
long long num_cruces_no[MAX_HILOS]{};
long long num_cruces_fj[MAX_HILOS]{};
#else
#ifdef NUM_GENES_PROGENITOR_2
long long num_genes_progenitor_2[MAX_HILOS]{};
#endif
#endif

#ifdef NUM_MEJORAS
long long num_mejoras[MAX_HILOS]{};
long long num_mejoras_mejor{};
#endif

#ifdef SORTEOS
long long n_sor[MAX_HILOS]{};
double media[3][MAX_HILOS]{};
int v_media[3][MAX_HILOS]{};
double desviacion[3][MAX_HILOS]{};
#endif

#ifdef CONSUMO_INTERMEDIO_AX
int RESTO_NSEC4;
int NSEC4;
#endif

double** cotas = NULL;
int* fijo = NULL;
double** poblacion = NULL;
double* merito_individuo = NULL;
double* factible = NULL;
double** descendiente = NULL;
int nvar_fijas;

// el número máximo de variables en el vector solución lo establecemos en 1000, con nuestras MCS el máximo es 507, 696 si se incluye XP
const int MAX_VEC = 1000;
double vec_ini[MAX_VEC];

#ifdef AJUSTA_POB_INICIAL
double vec_opt_nuevo[MAX_VEC + 1];
#endif

bool CANCELAR;
int ind_mejor_merito;
double mejor_merito;
double mejor_merito_anterior;
int ind_peor_merito;
double peor_merito;
int generacion;
int res_Simulacion;
/*
parametros para particularizar el algoritmo genético
*/
int NPOB;
int max_intentos;
int intentos;
int regularizaciones;
int max_generaciones;
int modo_poblacion_inicial;
int modo_reinicio_poblacion;
double factor_dispersion;
double factor_sigma;
double variacion_dispersion;
int num_tramos_lhs;
// parámetro F que pondera la diferencia entre dos individuos al azar, que se suma al mejor individuo para
// obtener un mutante.
// va camviando a cada generación por un valor comprendido entre los dos valores de 'par_mutacion'
double par_mutacion[2]{};
double factor_mutacion;
// parámetro CR (probabilidad de cruce), cuanto más cerca de 1. más probable es que se produzca la recombinación, es
// decir, que el 'descendiente' tome el valor del mutante y no el del individuo correspondiente. Si es 1., el 
// 'descendiente' siempre toma el valor del mutante
double cte_recombinacion;
double tolerancia;
double tol_aceptable;
int generaciones_control_progreso;
double min_progreso;
int histo_int;
int histo_sol;
bool control_factibilidad;
unsigned int semilla;
bool poner_el_mejor_primero;
bool incluir_x0;
int NVEC;
int id_salida;
char senda_salidas[128];
int desviaciones_relativas;
double umbral_regularizacion;
double fraccion_regularizacion;

const int N_MODOS_INICIO = 15;
double factor_dispersion_actualizado = 1.0;

FILE* salida{};

struct timeb tiempo_ini;
struct timeb tiempo_ant, tiempo_act;
double dif_tpo_par;
double dif_tpo_tot;

/*
para la generación de la población inicial y el recálculo del factor de mutación cuando termina cada generación
*/
mt19937 gen;
uniform_real_distribution<double> dis_double(0.0, 1.0);
uniform_int_distribution<int> dis_entero{};

/*
Permite que la aplicación que llama a la DLL abra el archivo de salida y
así poder escribir en este fichero información util para depurar errores, por ejemplo, en las
funciones de 'merito' sin necesidad de haber llamado a la función 'soluciona'
*/
bool abre_salida(const char* senda) {
	sprintf_s(senda_salidas, 127, "%s", senda);
	char fichero[128];
	sprintf_s(fichero, 127, "%s/%d_%d_%d_%d_dll.log", senda_salidas, 0, 0, 0, 0);
	salida = _fsopen(fichero, "w", _SH_DENYWR);
	if (salida == 0) {
		// Error al abrir el fichero de salida
		return false;
	}
	return true;
}
/*
el complemento de 'abre_salida'
*/
bool cierra_salida() {
	if (salida != 0) {
		fclose(salida);
	}
	return true;
}
/*
cunado se pulsa Ctrl+C, se establece la variable global 'CANCELAR' a true para que el algoritmo genético termine lo antes posible
*/
void cancelar(int sig)
{
	CANCELAR = true;
}
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
double* soluciona(double* par, double* cotasInf, double* cotasSup, double* vec, int extendida, const char* senda) {
	sprintf_s(senda_salidas, 127, "%s", senda);
	CANCELAR = false;

	// capturar la señal Ctrl+C, al pulsar esta combinación de teclas se ejecuta la funciín 'cancelar'
	signal(SIGINT, &cancelar);

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
	sprintf_s(fichero, 127, "%s/%d_%d_%d_%d_dll.log", senda_salidas, id_salida, NPOB, modo_poblacion_inicial, (unsigned int)semilla);
	if (salida != 0) {
		fclose(salida);
	}
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

	/*
			NO PARECE TENER NINGUN EFECTO
	dar la máxima prioridad al proceso principal (base)
		ABOVE_NORMAL_PRIORITY_CLASS es menos crítica y REALTIME_PRIORITY_CLASS la más crítica
	*/
	if (!SetPriorityClass(GetCurrentProcess(), HIGH_PRIORITY_CLASS)) {
		fprintf(salida, "*--* Error (%d) al establecer la priodidad base\n", GetLastError());
	}
	auto t_inicio = chrono::system_clock::now();
	auto inicio = chrono::system_clock::to_time_t(t_inicio);
	char tmBuff[30];
	ctime_s(tmBuff, sizeof(tmBuff), &inicio);
	fprintf(salida, "inicio: %s\n", tmBuff);
	fflush(salida);

#ifdef CONSUMO_INTERMEDIO_INDESADO
	/*
	// la comprobación de si esto ahorra tiempo de cálculo, o todo lo contrario, resulta incoherente

	fprintf(salida, "pares de 'ax'                  %d\n", NSEC * NSEC);
	fprintf(salida, "pares de 'ax' distinto de cero %d\n\n", ndc_ax);
	fflush(salida);
	struct timeb tiempo_ini, tiempo_fin;
	int diff;
	double Z[NSEC]{ 10000 };
	ftime(&tiempo_ini);
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
	ftime(&tiempo_fin);
	diff = (int)(1000.0 * (tiempo_fin.time - tiempo_ini.time) + (tiempo_fin.millitm - tiempo_ini.millitm));
	fprintf(salida, "tiempo Optimizado mili s : %d\n", diff);
	fflush(salida);
	ftime(&tiempo_ini);
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
	ftime(&tiempo_fin);
	diff = (int)(1000.0 * (tiempo_fin.time - tiempo_ini.time) + (tiempo_fin.millitm - tiempo_ini.millitm));
	fprintf(salida, "tiempo            mili s : %d\n", diff);
	fflush(salida);
	ftime(&tiempo_ini);
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
	ftime(&tiempo_fin);
	diff = (int)(1000.0 * (tiempo_fin.time - tiempo_ini.time) + (tiempo_fin.millitm - tiempo_ini.millitm));
	fprintf(salida, "tiempo referencia mili s : %d\n\n", diff);
	fflush(salida);
	*/
#endif
	if (inicia_cotas() == false) {
		// Error al generar la poblacion
		fin_soluciona();
		if (extendida == 1) {
			me_sol[0] = -2.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -2.;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			return VEC_OPT_E;
		}
	}
	if (fija_cotas(cotasInf, cotasSup) == false) {
		// Error al fijar las cotas
		fin_soluciona();
		if (extendida == 1) {
			me_sol[0] = -3.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -3;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			return VEC_OPT_E;
		}
	}
	fprintf(salida, "Número factores        : %12d\n", NFAC);
	fprintf(salida, "Número hogares         : %12d\n", NDEM);
	fprintf(salida, "Número sectores        : %12d\n\n", NSEC);
	fprintf(salida, "Número procesos        : %12d\n", n_hilos);
#ifdef AZAR_HILOS_LOCAL
	fprintf(salida, "Modo azar hilos        : local\n");
#else
	fprintf(salida, "Modo azar hilos        : vector global\n");
#endif
#ifdef MT19937
	fprintf(salida, "Números aleatorios     : mt19937\n");
#else
	fprintf(salida, "Números aleatorios     : minstd_rand\n");
#endif
#ifdef INI_AZAR_FICHERO
	fprintf(salida, "Ini.aleatorios fichero : si\n");
#else
	fprintf(salida, "Ini.aleatorios fichero : no\n");
#endif
	fprintf(salida, "Semilla num.aleatorios : %12d\n\n", (unsigned int)semilla);
#ifdef FIJAR_VARIABLES
	fprintf(salida, "FIJAR_VARIABLES\n");
	fprintf(salida, "Generaciones calentar  : %12d\n", GENS_CALENTAR);
	fprintf(salida, "Cada n generaciones    : %12d\n", BLOQUE_FIJAR);
	fprintf(salida, "Valor mínimo variable  : %12.5e\n", MIN_FIJAR);
	fprintf(salida, "Tolerancia para fijar  : %12.5e\n", TOL_DISPERSION);
#endif
	fprintf(salida, "Intentos (reinicios)   : %12d\n", max_intentos);
	fprintf(salida, "Población              : %12d\n", NPOB);
	fprintf(salida, "Modo población inicial : %12d\n", modo_poblacion_inicial);
	fprintf(salida, "Factor dispersión unif.: %12.5e\n", factor_dispersion);
	fprintf(salida, "Sigma dispersión normal: %12.5e\n", factor_sigma);
#ifdef AJUSTA_POB_INICIAL
	fprintf(salida, "Población inicial ajustada\n");
#endif
	fprintf(salida, "-------------------------------------\n");
	fprintf(salida, "Progreso mínimo        : %12.3f %%\n", 100. * min_progreso);
	fprintf(salida, "Umbral regularización  : %12.5e veces el progreso mínimo\n", umbral_regularizacion);
	fprintf(salida, "Regularización         : %12.3f %% = %d individuos\n", 100. * fraccion_regularizacion, (int)(fraccion_regularizacion * NPOB));
	fprintf(salida, "Modo reinicio población: %12d\n", modo_reinicio_poblacion);
	if (modo_reinicio_poblacion == 0) {
		fprintf(salida, "Factor dispersión reini: %12.5e\n", 1.0);
	}
	else {
		fprintf(salida, "Factor dispersión reini: %12.5e\n", variacion_dispersion);
	}
	fprintf(salida, "-------------------------------------\n");
	fprintf(salida, "Factor mutación (F)    : %12.5e %12.5e\n", par_mutacion[0], par_mutacion[1]);
	fprintf(salida, "Recombinación (CR)     : %12.5e\n", cte_recombinacion);
#ifdef RECOMBINACION_NORMAL
	fprintf(salida, "Recombinación normal\n");
#else
	fprintf(salida, "Recombinación con el mejor individuo\n");
#endif
	fprintf(salida, "Opción cálculo desvios : %12d\n", op.OPT_DESVIOS);
	// llamamos a 'merito_sol' para que calcule N_DESVIACIONES
	merito_sol(vec_ini);
	fprintf(salida, "Número de desviaciones : %12d\n", N_DESVIACIONES);
	fprintf(salida, "-------------------------------------\n");
	fprintf(salida, "Variables cabecera     : %12d\n", LCAB);
	int lsol = LSOL - 1;
	// no restamos 1 a LVAR porque en la solución no se incluye el precio de uno de los factores, por
	// eso se lo sumamos a LVARS_PP para obtener el total de variables del modelo
	int lvar = LVAR;
	if (op.GE_INCLUYE_XP == false) {
		lsol -= NDEM * NSEC;
		lvar -= NDEM * NSEC;
	}
	fprintf(salida, "Variables solución     : %12d\n", lsol);
	fprintf(salida, "Resto variables modelo : %12d\n", LVARS_PP + 1);
	fprintf(salida, "Variables recalculadas : %12d\n", LVARS_SP);
	fprintf(salida, "-------------------------------------\n");
	fprintf(salida, "Total                  : %12d\n\n", lvar);
	fprintf(salida, "Variables fijas en sol : %12d\n", nvar_fijas);

#ifdef DESVIACONES_RELATIVAS
	fprintf(salida, "Desviaciones relativas : %12d\n", desviaciones_relativas);
#endif
	if (nvar_fijas > 0) {
		fprintf(salida, "Variables con valores fijos\n");
		int p;
		int d;
		for (int i = 0; i < NVEC; i++) {
			if (fijo[i] == 1) {
				p = 0;
				d = 0;
				for (int j = 0; j < N_BLO_VEC; j++) {
					if (i >= pvec[j] && i < pvec[j + 1]) {
						p = j;
						d = i - pvec[j];
						break;
					}
				}
				fprintf(salida, "%5d %-8s %5d %15.8e\n", i, rot_blo_vec[p], d, cotasInf[i]);
			}
		}
	}
	fprintf(salida, "\n");
#ifdef NUM_GENES_PROGENITOR_2
	fprintf(salida, "n.gen.pro2 máximoxtramo:%13lld\n\n", (unsigned long long)((unsigned long long)(lsol - nvar_fijas)) * (unsigned long long)NPOB * (unsigned long long)histo_int);
#endif
	fflush(salida);

#ifdef SORTEOS
	for (int i = 0; i < n_hilos; i++) {
		v_media[0][i] = NPOB / 2;
		v_media[1][i] = NPOB / 2;
		v_media[2][i] = NVEC / 2;
	}
#endif

#ifdef COMPROBAR_MAX_DESVIACION
	// 'indice_desviaciones' es totalmente prescindible, solo se usa para comprobar la variable con la máxima desviación
	indice_desviaciones();
	for (int i = 0; i < MAX_BLOQUES_DESVIOS; i++) {
		fprintf(salida, "Bloque %3d :  %-8s %6d\n", i, rot_desvios[i], ind_bloque_desviacion[i]);
	}
	fprintf(salida, "\n");
	fflush(salida);
#endif
#ifdef ESTA_CRUCES
#ifdef ECM
	fprintf(salida, "generacio d.est.poblac      ECM     var.max.err  ind.v.  bloque  despl segs.p mins.tot  n.cruce si n.cruce ok n.cruce no n.cruce fj  n.mejoras n.mejs.mej\n");
#else
	fprintf(salida, "generacio d.est.poblac      ECT     var.max.err  ind.v.  bloque  despl segs.p mins.tot  n.cruce si n.cruce ok n.cruce no n.cruce fj  n.mejoras n.mejs.mej\n");
#endif
	fprintf(salida, "--------- ------------ ------------ ------------ ------ -------- ----- ------ --------  ---------- ---------- ---------- ---------- ---------- ----------\n");
#else
#ifdef FIJAR_VARIABLES
#ifdef ECM
	fprintf(salida, "generacio d.est.poblac      ECM     var.max.err  ind.v.  bloque  despl segs.p mins.tot  n.gen.pro2  var.fijas\n");
#else
	fprintf(salida, "generacio d.est.poblac      ECT     var.max.err  ind.v.  bloque  despl segs.p mins.tot  n.gen.pro2  var.fijas\n");
#endif
#else
#ifdef ECM
	fprintf(salida, "generacio d.est.poblac      ECM     var.max.err  ind.v.  bloque  despl segs.p mins.tot  n.gen.pro2  n.mejoras n.mejs.mej\n");
#else
	fprintf(salida, "generacio d.est.poblac      ECT     var.max.err  ind.v.  bloque  despl segs.p mins.tot  n.gen.pro2  n.mejoras n.mejs.mej\n");
#endif
#endif
	fprintf(salida, "--------- ------------ ------------ ------------ ------ -------- ----- ------ --------  ---------- ---------- ----------\n");
#endif
	if (inicia_poblacion(factor_dispersion) == false) {
		// Error al reservar memoria para la poblacion
		fin_soluciona();
		if (extendida == 1) {
			me_sol[0] = -4.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -4.;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			return VEC_OPT_E;
		}
	}
	for (int i = 0; i < NVEC; i++) {
		vec_ini[i] = vec[i];
	}
	gen.seed((unsigned int)semilla);
	dis_entero = uniform_int_distribution<int>{ 0, (int)(NPOB - 1) };
	if (genera_poblacion(vec_ini, modo_poblacion_inicial, 1.0) == false) {
		// Error al generar la poblacion
		fin_soluciona();
		if (extendida == 1) {
			me_sol[0] = -5.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -5.;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			return VEC_OPT_E;
		}
	}

	/*
	// estadística de la población inicial
	double* media;
	media = (double*)malloc(NVEC * sizeof(double));
	if (media == NULL) {
		// Error, terminacion inesperada
		fin_soluciona();
		if (extendida == 1) {
			me_sol[0] = -10.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -10.;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			return VEC_OPT_E;
		}
	}
	double* desest;
	desest = (double*)malloc(NVEC * sizeof(double));
	if (desest == NULL) {
		// Error, terminacion inesperada
		fin_soluciona();
		if (extendida == 1) {
			me_sol[0] = -10.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -10.;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
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
	sprintf_s(fichero, 127, "%s/%d_dll_esta.log", senda_salidas, id_salida);
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
		fin_soluciona();
		if (extendida == 1) {
			me_sol[0] = 0;
			me_sol[2] = 0;
			me_sol[3] = 0;
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = 0;
			VEC_OPT_E[2] = 0;
			VEC_OPT_E[3] = 0;
			return VEC_OPT_E;
		}
	}

	histo_n = 0;
	mejor_merito_anterior = 1.0e+99;
	generacion = 0;
	intentos = 0;
	regularizaciones = 0;
	ftime(&tiempo_ant);

	if (poner_el_mejor_primero) {
		hdis_entero = uniform_int_distribution<int>{ 1, (int)(NPOB - 1) };
	}
	else {
		hdis_entero = uniform_int_distribution<int>{ 0, (int)(NPOB - 1) };
	}
	hdis_entero_ivec = uniform_int_distribution<int>{ 0, (int)(NVEC - 1) };
	hdis_double = uniform_real_distribution<double>{ 0.0, 1.0 };

	if (n_hilos > 0) {
		for (int i = 0; i < n_hilos; i++) {
#ifndef AZAR_HILOS_LOCAL
			// establecemos los vectores globales
#ifdef MT19937
#ifdef INI_AZAR_FICHERO
			// pasamos 'hgen' y el número de hilo 'i' y no hgen[i], para que sea un paso por referencia y hgen[i] se inicialice correctamente
			inicia_azar(hgen, i, (unsigned int)(semilla + i));
#else
			hgen[i] = mt19937((unsigned int)(semilla + i));
#endif INI_AZAR_FICHERO
#else
			hgen[i] = minstd_rand((unsigned int)(semilla + i));
#endif MT19937
#endif AZAR_HILOS_LOCAL

#ifdef ESTA_CRUCES
			num_cruces_si[i] = 0;
			num_cruces_ok[i] = 0;
			num_cruces_no[i] = 0;
			num_cruces_fj[i] = 0;
#else
#ifdef NUM_GENES_PROGENITOR_2
			num_genes_progenitor_2[i] = 0;
#endif
#endif
		}
		if (PreparaMP() == -1) {
			fin_soluciona();
			if (extendida == 1) {
				me_sol[0] = -8.;
				me_sol[2] = intentos;
				me_sol[3] = generacion;
				return me_sol;
			}
			else {
				VEC_OPT_E[0] = -8.;
				VEC_OPT_E[2] = intentos;
				VEC_OPT_E[3] = generacion;
				return VEC_OPT_E;
			}
		}
	}
	else {

#ifdef MT19937
#ifdef INI_AZAR_FICHERO
		inicia_azar(hgen, 0, (unsigned int)(semilla));
#else
		hgen[0] = mt19937((unsigned int)semilla);
#endif

#else
		hgen[0] = minstd_rand((unsigned int)semilla);
#endif
		res_Simulacion = avanza();
	}
#ifdef ESTA_CRUCES
	fprintf(salida, "--------- ------------ ------------ ------------ ------ -------- ----- ------ --------  ---------- ---------- ---------- ---------- ---------- ----------\n");
#else
	fprintf(salida, "--------- ------------ ------------ ------------ ------ -------- ----- ------ --------  ---------- ---------- ----------\n");
#endif
	if (res_Simulacion == -1) {
		// Cancelado
		fin_soluciona();
		if (extendida == 1) {
			me_sol[0] = 5.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = 5.;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			return VEC_OPT_E;
		}
	}
	else if (res_Simulacion == -2) {
		// Encontrada solucion
		fin_soluciona();
		if (extendida == 1) {
			me_sol[0] = 0.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = 0.;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			return VEC_OPT_E;
		}
	}
	else if (res_Simulacion == -3) {
		if (mejor_merito > tol_aceptable) {
			// No progresa, solucion no aceptable
			fin_soluciona();
			if (extendida == 1) {
				me_sol[0] = 1.;
				me_sol[2] = intentos;
				me_sol[3] = generacion;
				return me_sol;
			}
			else {
				VEC_OPT_E[0] = 1.;
				VEC_OPT_E[2] = intentos;
				VEC_OPT_E[3] = generacion;
				return VEC_OPT_E;
			}
		}
		else {
			// No progresa, pero la solucion puede ser aceptable
			fin_soluciona();
			if (extendida == 1) {
				me_sol[0] = 2.;
				me_sol[2] = intentos;
				me_sol[3] = generacion;
				return me_sol;
			}
			else {
				VEC_OPT_E[0] = 2.;
				VEC_OPT_E[2] = intentos;
				VEC_OPT_E[3] = generacion;
				return VEC_OPT_E;
			}
		}
	}
	else if (res_Simulacion == -5) {
		if (mejor_merito > 0.0001) {
			// Superado el maximo de generaciones, solucion no aceptable
			fin_soluciona();
			if (extendida == 1) {
				me_sol[0] = 3.;
				me_sol[2] = intentos;
				me_sol[3] = generacion;
				return me_sol;
			}
			else {
				VEC_OPT_E[0] = 3.;
				VEC_OPT_E[2] = intentos;
				VEC_OPT_E[3] = generacion;
				return VEC_OPT_E;
			}
		}
		else {
			// Superado el maximo de generaciones, pero la solucion puede ser aceptable
			fin_soluciona();
			if (extendida == 1) {
				me_sol[0] = 4.;
				me_sol[2] = intentos;
				me_sol[3] = generacion;
				return me_sol;
			}
			else {
				VEC_OPT_E[0] = 4.;
				VEC_OPT_E[2] = intentos;
				VEC_OPT_E[3] = generacion;
				return VEC_OPT_E;
			}
		}
	}
	else {
		// Error, terminacion inesperada
		fin_soluciona();
		if (extendida == 1) {
			me_sol[0] = -10.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -10.;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			return VEC_OPT_E;
		}
	}
}

void fin_soluciona() {
#ifdef DESVIACONES_RELATIVAS
	merito_sol_relativa(poblacion[ind_mejor_merito]);
#else
	merito_sol(poblacion[ind_mejor_merito]);
#endif
	auto t_fin = chrono::system_clock::now();
	auto fin = chrono::system_clock::to_time_t(t_fin);
	char tmBuff[30];
	ctime_s(tmBuff, sizeof(tmBuff), &fin);
	double dist = distancia_clonacion();
	ftime(&tiempo_act);
	dif_tpo_par = (double)(tiempo_act.time - tiempo_ant.time) + (double)(tiempo_act.millitm - tiempo_ant.millitm) / 1000.;
	ftime(&tiempo_ant);
	dif_tpo_tot = ((double)(tiempo_act.time - tiempo_ini.time) + (double)(tiempo_act.millitm - tiempo_ini.millitm) / 1000.) / 60.;
#ifdef ESTA_CRUCES
	long long n_c_s = 0;
	long long n_c_o = 0;
	long long n_c_n = 0;
	long long n_c_f = 0;
	for (int i = 0; i < n_hilos; i++) {
		n_c_s += num_cruces_si[i];
		n_c_o += num_cruces_ok[i];
		n_c_n += num_cruces_no[i];
		n_c_f += num_cruces_fj[i];
		num_cruces_si[i] = 0;
		num_cruces_ok[i] = 0;
		num_cruces_no[i] = 0;
		num_cruces_fj[i] = 0;
	}
	fprintf(salida, "%9d %12.5e %12.5e %12.5e %6d %-8s %5d %6.1f %8.1f  %10lld %10lld %10lld %10lld %10lld %10lld\n", generacion, dist, mejor_merito, VEC_OPT_E[5], (int)VEC_OPT_E[6], rot_desvios[puntero_bloque_desviacion], desplazamiento_desviacion, dif_tpo_par, dif_tpo_tot, n_c_s, n_c_o, n_c_n, n_c_f, n_mej, n_mej_mej);
#else
	fprintf(salida, "%9d %12.5e %12.5e %12.5e %6d %-8s %5d %6.1f %8.1f  %10d\n", generacion, dist, mejor_merito, VEC_OPT_E[5], (int)VEC_OPT_E[6], rot_desvios[puntero_bloque_desviacion], desplazamiento_desviacion, dif_tpo_par, dif_tpo_tot, ind_mejor_merito);
#endif
#ifdef SORTEOS
	fprintf(salida, "\n");
	fprintf(salida, " nh   media i1     media i2     media i3       desv. i1     desv. i2     desv. i3\n");
	fprintf(salida, "--- ------------ ------------ ------------   ------------ ------------ ------------\n");
	for (int i = 0; i < n_hilos; i++) {
		media[0][i] /= (double)n_sor[i];
		media[1][i] /= (double)n_sor[i];
		media[2][i] /= (double)n_sor[i];
		desviacion[0][i] /= (double)n_sor[i];
		desviacion[1][i] /= (double)n_sor[i];
		desviacion[2][i] /= (double)n_sor[i];
		fprintf(salida, "%3d %12.5e %12.5e %12.5e   %12.5e %12.5e %12.5e\n", i, media[0][i], media[1][i], media[2][i], sqrt(desviacion[0][i]), sqrt(desviacion[1][i]), sqrt(desviacion[2][i]));
	}
	fprintf(salida, "--- ------------ ------------ ------------   ------------ ------------ ------------\n\n");
#endif
	fprintf(salida, "\nfin   : %s\n", tmBuff);
	fclose(salida);
	if (histo_sol != 0) {
		// se guarda el vector solución final, incluido cuando histo_sol = -1, solo se omite si histo_sol = 0
		char fichero[128];
		sprintf_s(fichero, 127, "%s/%d_%d_%d_%d_dll_sol_fin.log", senda_salidas, id_salida, NPOB, modo_poblacion_inicial, (unsigned int)semilla);
		salida_solucion(fichero);
	}
}
/*
separar los parámetros del algoritmo genético que se reciben como un vector de valores 'double' en la función 'soluciona'
*/
int parametros_alge(double* par) {
	int ipar = 0;
	max_intentos = (int)par[ipar++];
	n_hilos = (int)par[ipar++];
	max_generaciones = (int)par[ipar++];
	tolerancia = par[ipar++];
	tol_aceptable = par[ipar++];
	generaciones_control_progreso = (int)par[ipar++];
	min_progreso = par[ipar++];
	umbral_regularizacion = par[ipar++];
	fraccion_regularizacion = par[ipar++];
	histo_int = (int)par[ipar++];
	histo_sol = (int)par[ipar++];
	modo_poblacion_inicial = (int)par[ipar++];
	modo_reinicio_poblacion = (int)par[ipar++];
	factor_dispersion = par[ipar++];
	factor_sigma = par[ipar++];
	variacion_dispersion = par[ipar++];
	num_tramos_lhs = (int)par[ipar++];
	NPOB = (int)par[ipar++];
	par_mutacion[0] = par[ipar++];
	par_mutacion[1] = par[ipar++];
	cte_recombinacion = par[ipar++];
	control_factibilidad = (int)par[ipar++] == 1;
	semilla = (unsigned int)par[ipar++];
	poner_el_mejor_primero = (int)par[ipar++] == 1;
	incluir_x0 = (int)par[ipar++] == 1;
	NVEC = (int)par[ipar++];
	id_salida = (int)par[ipar++];
	desviaciones_relativas = (int)par[ipar++];

	if (fraccion_regularizacion > 0.9) fraccion_regularizacion = 0.9;
	if (NVEC >= MAX_VEC) {
		return -1;
	}
#ifdef CONSUMO_INTERMEDIO_AX
	RESTO_NSEC4 = NSEC % 4;
	NSEC4 = NSEC - RESTO_NSEC4;
#endif
	if (modo_reinicio_poblacion == 0) {
		variacion_dispersion = 1.0;
	}
	if (modo_poblacion_inicial < 0 || modo_poblacion_inicial > N_MODOS_INICIO) {
		return -1;
	}
	int lsol = LSOL - 1;
	if (op.GE_INCLUYE_XP == false) {
		lsol -= NDEM * NSEC;
	}
	if (NVEC != lsol) {
		return -1;
	}
#ifdef FIJAR_VARIABLES
	TOL_DISPERSION = tolerancia;
#endif
	return 0;
}
/*
crea las matrices dinámicas para las cotas (entornos de validez de las variables)
*/
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
/*
crea las variables dinámicas para la población, los descendientes, el mérito de cada individuo y si un vector de prueba es factible o no
*/
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
/*
da valores a las cotas de cada variable, y marca como fijas aquellas variables que tienen el mismo valor en la cota inferior y en la superior
*/
bool fija_cotas(double* cotasInf, double* cotasSup) {
	nvar_fijas = 0;
	for (int i = 0; i < NVEC; i++) {
		cotas[0][i] = cotasInf[i];
		cotas[1][i] = cotasSup[i];
		if (abs(cotas[1][i] - cotas[0][i]) < 0.000001) {
			fijo[i] = 1;
			nvar_fijas++;
		}
		else {
			fijo[i] = 0;
		}
	}
	return true;
}
/*
genera la población inicial de individuos, dependiendo del valor de 'modo_poblacion_inicial', lo ortodoso es el modo 0, las otras opciones se
han incluido para valorar si pueden mejorar el rendimiento del algoritmo, aunque NO se ha observado que esto ocurra, y en
algunos casos incluso empeora el rendimiento
*/
bool genera_poblacion(double* vec_central, int modo, double modulacion) {
	regularizaciones = 0;
	double semi_izq;
	double semi_dch;
	double semi_intervalo;
	double desplazamiento;
	double a;
	double v;
	double f;
	/*
	---------------------------------------------------------------------------------------------------------------------------------
	Estrategía inutil

	En caso de reinicio, tratamos de partir de un vector que no coincida con el mínimo local en el que se ha caido

	en cualquier caso, 'vec_ini' no cambiará de valor cuando se pasa como parámetro a esta función, en caso de reinicios con
	el mejor individuo de la población, será este el que cambie, lo cual es intrancendente para la generación de la población inicial
	*/
	/*
	for (int j = 0; j < NVEC; j++) {
		vec_central[j] = (vec_central[j] + vec_ini[j]) / 2.;
	}
	---------------------------------------------------------------------------------------------------------------------------------
	A cada reinicio se va ampliando el coeficiete 'modulación', no afecta los modos 4 a 7

	*/
	if (modo == 0) {
		// intérvalo simétrico centrado en 'vec_central' con distribución uniforme

		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					poblacion[i][j] = cotas[0][j];
				}
				else {
					semi_izq = vec_central[j] - cotas[0][j];
					semi_dch = cotas[1][j] - vec_central[j];
					if (semi_izq < semi_dch) {
						semi_intervalo = semi_izq;
					}
					else {
						semi_intervalo = semi_dch;
					}
					f = (semi_izq + semi_dch) / (2. * semi_intervalo);
					a = dis_double(gen);
					desplazamiento = f * modulacion * factor_dispersion * a * semi_intervalo;
					a = dis_double(gen);
					if (a < 0.5) {
						v = vec_central[j] - desplazamiento;
					}
					else {
						v = vec_central[j] + desplazamiento;
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
	else if (modo == 1) {
		// centrado en el centro del intervalo de validez de la variable con distribución uniforme

		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					poblacion[i][j] = cotas[0][j];
				}
				else {
					semi_intervalo = (cotas[1][j] - cotas[0][j]) / 2.;
					a = dis_double(gen);
					desplazamiento = modulacion * factor_dispersion * a * semi_intervalo;
					a = dis_double(gen);
					if (a < 0.5) {
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
	else if (modo == 2) {
		// intérvalo simétrico centrado en 'vec_central' con distribución normal

		mt19937 gent((unsigned int)semilla);
		normal_distribution<double> dis_normal{ 0.0, modulacion * factor_sigma };
		for (int i = 2; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					poblacion[i][j] = cotas[0][j];
				}
				else {
					semi_izq = vec_central[j] - cotas[0][j];
					semi_dch = cotas[1][j] - vec_central[j];
					if (semi_izq < semi_dch) {
						semi_intervalo = semi_izq;
					}
					else {
						semi_intervalo = semi_dch;
					}
					desplazamiento = dis_normal(gent) * semi_intervalo;
					a = dis_double(gen);
					if (a < 0.5) {
						v = vec_central[j] - desplazamiento;
					}
					else {
						v = vec_central[j] + desplazamiento;
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
	else if (modo == 3) {
		// centrado en el centro del intervalo de validez de la variable con distribución normal

		mt19937 gent((unsigned int)semilla);
		normal_distribution<double> dis_normal{ 0.0, modulacion * factor_sigma };
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					poblacion[i][j] = cotas[0][j];
				}
				else {
					semi_intervalo = (cotas[1][j] - cotas[0][j]) / 2.;
					desplazamiento = dis_normal(gent) * semi_intervalo;
					a = dis_double(gen);
					if (a < 0.5) {
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
	else if (modo == 4) {
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
					descendiente[i][j] = cotas[0][j];
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

						desplazamiento = factor_dispersion * dis_double(gen) * semi_intervalo;
						a = dis_double(gen);
						if (a < 0.5) {
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

		std::mt19937 rng((unsigned int)semilla);

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
	else if (modo == 5) {
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
					descendiente[i][j] = cotas[0][j];
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

						desplazamiento = factor_dispersion * dis_double(gen) * semi_intervalo;
						a = dis_double(gen);
						if (a < 0.5) {
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
		std::mt19937 rng((unsigned int)semilla);
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
	else if (modo == 6) {
		// secuencia de valores uniformemente espacionados entre cotas y permutaciones distintas para cada variable

		double v;
		double incremento;
		// recorremos las variables (NVEC), para determinar la secuencia de valores de cada una de ellas
		for (int j = 0; j < NVEC; j++) {
			if (fijo[j] == 1) {
				for (int i = 0; i < NPOB; i++) {
					descendiente[i][j] = cotas[0][j];
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
		std::mt19937 rng((unsigned int)semilla);

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
	else if (modo == 7) {
		double v;
		double incremento;
		// recorremos las variables (NVEC), para determinar la secuencia de valores de cada una de ellas
		for (int j = 0; j < NVEC; j++) {
			if (fijo[j] == 1) {
				for (int i = 0; i < NPOB; i++) {
					descendiente[i][j] = cotas[0][j];
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
		std::mt19937 rng((unsigned int)semilla);
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
	else if (modo == 8) {
		// valores próximos al extremo inferior del entorno de existencia de las variables
		// con permutaciones distintas de los valores obtenidos para cada una
		double intervalo;
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					descendiente[i][j] = cotas[0][j];
				}
				else {
					intervalo = cotas[1][j] - cotas[0][j];
					a = dis_double(gen);
					desplazamiento = modulacion * factor_dispersion * intervalo * a;
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

		std::mt19937 rng((unsigned int)semilla);

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
	else if (modo == 9) {
		// valores próximos al extremo inferior del entorno de existencia de las variables
		// la misma permutación a todas las variables
		double intervalo;
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					descendiente[i][j] = cotas[0][j];
				}
				else {
					intervalo = cotas[1][j] - cotas[0][j];
					a = dis_double(gen);
					desplazamiento = modulacion * factor_dispersion * intervalo * a;
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
		std::mt19937 rng((unsigned int)semilla);
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
	else if (modo == 10) {
		// valores próximos al extremo superior del entorno de existencia de las variables
		// con permutaciones distintas de los valores obtenidos para cada una
		double intervalo;
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					descendiente[i][j] = cotas[0][j];
				}
				else {
					intervalo = cotas[1][j] - cotas[0][j];
					a = dis_double(gen);
					desplazamiento = factor_dispersion * intervalo * a;
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

		std::mt19937 rng((unsigned int)semilla);

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
	else if (modo == 11) {
		// valores próximos a los extremos de los entornos de existencia de las variables
		// con permutaciones distintas de los valores obtenidos para cada una

		double intervalo;
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					descendiente[i][j] = cotas[0][j];
				}
				else {
					intervalo = cotas[1][j] - cotas[0][j];
					a = dis_double(gen);
					desplazamiento = modulacion * factor_dispersion * a * intervalo;
					a = dis_double(gen);
					if (a > 0.5) {
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

		std::mt19937 rng((unsigned int)semilla);

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
	else if (modo == 12) {
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
					descendiente[i][j] = cotas[0][j];
				}
				else {
					a = dis_double(gen);
					if (a < factor_sigma) {
						v = cotas[0][j];
						ci++;
						if (v <= 0.000001) cic++;
					}
					else {
						intervalo = cotas[1][j] - cotas[0][j];
						a = dis_double(gen);
						desplazamiento = modulacion * factor_dispersion * intervalo * a;
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

		std::mt19937 rng((unsigned int)semilla);

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
	else if (modo == 13) {
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
					poblacion[i][j] = cotas[0][j];
				}
				else {
					a = dis_double(gen);
					if (a < factor_sigma) {
						v = cotas[0][j];
						ci++;
						if (v <= 0.000001) cic++;
					}
					else {
						intervalo = cotas[1][j] - cotas[0][j];
						a = dis_double(gen);
						desplazamiento = factor_dispersion * intervalo * a;
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
	else if (modo == 14) {
		/*
		valores próximos o iguales al extremo superior del entorno de existencia de las variables
		con permutaciones distintas de los valores obtenidos para cada una
		*/
		long cs = 0;
		double intervalo;
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					descendiente[i][j] = cotas[0][j];
				}
				else {
					a = dis_double(gen);
					if (a < factor_sigma) {
						v = cotas[1][j];
						cs++;
					}
					else {
						intervalo = cotas[1][j] - cotas[0][j];
						a = dis_double(gen);
						desplazamiento = modulacion * factor_dispersion * intervalo * a;
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

		std::mt19937 rng((unsigned int)semilla);

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
	else if (modo == 15) {
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
					descendiente[i][j] = cotas[0][j];
				}
				else {
					a = dis_double(gen);
					if (a < factor_sigma) {
						v = cotas[0][j];
						ci++;
						if (v <= 0.000001) cic++;
					}
					else {
						a = dis_double(gen);
						desplazamiento = factor_dispersion * a;
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

		std::mt19937 rng((unsigned int)semilla);

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
			poblacion[0][j] = vec_central[j];
		}
	}

	// seleccionar el mejor
	mejor_merito = 1.0e+99;
	ind_mejor_merito = NPOB + 1;
	peor_merito = -1;
	ind_peor_merito = NPOB + 1;
	for (int i = 0; i < NPOB; i++) {
#ifdef DESVIACONES_RELATIVAS
		v = merito_s_relativa(poblacion[i]);
#else

#ifdef AJUSTA_POB_INICIAL
		ajustar_vec_solucion(poblacion[i]);
		for (int j = 0; j < NVEC; j++) {
			poblacion[i][j] = vec_opt_nuevo[j];
		}
		v = merito_s(poblacion[i]);
#else
		v = merito_s(poblacion[i]);
#endif

#endif
		merito_individuo[i] = v;
		factible[i] = true;
		if (v < mejor_merito) {
			mejor_merito = v;
			ind_mejor_merito = i;
		}
#ifdef SELECCION_MAXIMA
		if (v > peor_merito) {
			peor_merito = v;
			ind_peor_merito = i;
		}
#endif
	}
	/*
	fflush(salida);
	*/
	return true;
}
/*
la implementación 'habitual' de este algoritmo es colocar el mejor individuo de la población en la primera posición del array 'poblacion',
esto solo tiene sentido si se quiere evitar que el mejor individuo de la población pueda ser seleccionado como parte del par de individuos que se van a cruzar para generar un descendiente,
lo que se consigue si se empieza a cruzar a partir del segundo individuo de la población (poner_el_mejor_primero == true)
no he observado ninguna ventaja en hacerlo.
*/
void recolocar_al_mejor(int ind_mejor_merito) {
	double* p = poblacion[0];
	poblacion[0] = poblacion[ind_mejor_merito];
	poblacion[ind_mejor_merito] = p;
	double me = merito_individuo[0];
	merito_individuo[0] = merito_individuo[ind_mejor_merito];
	merito_individuo[ind_mejor_merito] = me;
	ind_mejor_merito = 0;
}
/*
inicia la ejecuciín en mono proceso (sin hilos), tiene poca utilidad o ninguna
*/
int avanza() {
	double a;
	int desde = poner_el_mejor_primero ? 1 : 0;
	factor_mutacion = (par_mutacion[0] + par_mutacion[1]) / 2.;
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
		a = dis_double(gen);
		factor_mutacion = par_mutacion[0] + a * (par_mutacion[1] - par_mutacion[0]);
		generacion++;
	}
	if (generacion == max_generaciones) {
		return -5;
	}
	return -6;
}
/*
versión mono proceso
*/
void mutacion_cruze(int desde, int hasta, int hilo) {
	int i1;
	int i2;
	int i3;
	double v;
	bool es_factible;
	for (int i = desde; i < hasta; i++) {
		i1 = hdis_entero(hgen[hilo]);
		i2 = hdis_entero(hgen[hilo]);
		// 'i3' es el índice de la variable que se va a cruzar obligatoriamente, para asegurar que el descendiente no sea igual al individuo de la población
		i3 = hdis_entero_ivec(hgen[hilo]);
		es_factible = true;
		// vamos a cruzar los individuos 'poblacion[i]' de la población con los mutantes 'v'
		for (int j = 0; j < NVEC; j++) {
			if (fijo[j] == 0 && (hdis_double(hgen[hilo]) <= cte_recombinacion || j == i3)) {
				// la variable 'j' del 'descendiente' toma el valor mutante 'v' si la variable 'j' no es fija (fijo[j] == 0) y se cumple la condición de
				//  recombinación, o si se trata de la variable (i3) que se debe cruzar obligatoriamente

				// mutación diferencial: el valor se obtiene a partir del mejor individuo de la población y de la diferencia entre dos individuos aleatorios
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
				// la variable 'j' del 'descendiente' toma el valor del individuo de la población, bien porque es una variable de valor fijo y todos los
				// individuos tienen el mismo valor, o porque no se cumple la condición de recombinación y no se trata de la variable 'i3' que se
				// debe cruzar obligatoriamente
#ifdef RECOMBINACION_NORMAL
				descendiente[i][j] = poblacion[i][j];
#else
				descendiente[i][j] = poblacion[ind_mejor_merito][j];
#endif
			}
		}
		if (control_factibilidad) {
			factible[i] = es_factible;
		}
	}
}
/*
versión multi proceso, cada hilo se encarga de cruzar una parte de la población, determinada por los parámetros 'desde' y 'hasta'
*/
void mutacion_cruzeH(int desde, int hasta, int hilo) {
	int i1;
	int i2;
	int i3;
	double v;
	bool es_factible;
	// vamos a cruzar los individuos 'poblacion[i]' de la población con los mutantes 'v'
	for (int i = desde; i < hasta; i++) {
		i1 = hdis_entero(hgen[hilo]);
		i2 = hdis_entero(hgen[hilo]);
		// 'i3' es el índice de la variable que se va a cruzar obligatoriamente, para asegurar que el descendiente no sea igual al individuo de la población
		i3 = hdis_entero_ivec(hgen[hilo]);

#ifdef SORTEOS
		n_sor[hilo]++;
		media[0][hilo] += i1;
		media[1][hilo] += i2;
		media[2][hilo] += i3;
		v = i1 - v_media[0][hilo];
		desviacion[0][hilo] += v * v;
		v = i2 - v_media[1][hilo];
		desviacion[1][hilo] += v * v;
		v = i3 - v_media[2][hilo];
		desviacion[2][hilo] += v * v;
#endif

		es_factible = true;
		for (int j = 0; j < NVEC; j++) {
			if (fijo[j] == 0 && (hdis_double(hgen[hilo]) <= cte_recombinacion || j == i3)) {
				// la variable 'j' del 'descendiente' toma el valor mutante 'v' si la variable 'j' no es fija (fijo[j] == 0) y se cumple la condición de
				//  recombinación, o si se trata de la variable (i3) que se debe cruzar obligatoriamente

				// mutación diferencial: el valor se obtiene a partir del mejor individuo de la población y de la diferencia entre dos individuos aleatorios
#ifdef ESTA_CRUCES
				num_cruces_si[hilo]++;
#endif
				v = poblacion[ind_mejor_merito][j] + factor_mutacion * (poblacion[i1][j] - poblacion[i2][j]);
				if (control_factibilidad) {
					if (v < cotas[0][j] || v > cotas[1][j]) {
						es_factible = false;
						break;
					}
				}
				descendiente[i][j] = v;
#ifdef ESTA_CRUCES
				num_cruces_ok[hilo]++;
#endif
			}
			else {
				// la variable 'j' del 'descendiente' toma el valor del individuo de la población, bien porque es una variable de valor fijo (todos los
				// individuos tienen el mismo valor), o porque no se cumple la condición de recombinación y no se trata de la variable 'i3' que se
				// debe cruzar obligatoriamente
#ifdef RECOMBINACION_NORMAL
				descendiente[i][j] = poblacion[i][j];
#else
				descendiente[i][j] = poblacion[ind_mejor_merito][j];
#endif
#ifdef ESTA_CRUCES
				num_cruces_no[hilo]++;
				if (fijo[j] == 1) {
					num_cruces_fj[hilo]++;
				}
#else
#ifdef NUM_GENES_PROGENITOR_2
				if (fijo[j] == 0) {
					num_genes_progenitor_2[hilo]++;
				}
#endif
#endif
			}
		}
		if (control_factibilidad) {
			factible[i] = es_factible;
		}
	}
}

void mutacion_cruzeH(int desde, int hasta, int hilo, mt19937& gh, uniform_int_distribution<int>& he, uniform_int_distribution<int>& hi, uniform_real_distribution<double>& hd) {
	int i1;
	int i2;
	int i3;
	double v;
	bool es_factible;
	// vamos a cruzar los individuos 'poblacion[i]' de la población con los mutantes 'v'
	for (int i = desde; i < hasta; i++) {
		i1 = he(gh);
		i2 = he(gh);
		// 'i3' es el índice de la variable que se va a cruzar obligatoriamente, para asegurar que el descendiente no sea igual al individuo de la población
		i3 = hi(gh);

#ifdef SORTEOS
		n_sor[hilo]++;
		media[0][hilo] += i1;
		media[1][hilo] += i2;
		media[2][hilo] += i3;
		v = i1 - v_media[0][hilo];
		desviacion[0][hilo] += v * v;
		v = i2 - v_media[1][hilo];
		desviacion[1][hilo] += v * v;
		v = i3 - v_media[2][hilo];
		desviacion[2][hilo] += v * v;
#endif

		es_factible = true;
		for (int j = 0; j < NVEC; j++) {
			if (fijo[j] == 0 && (hd(gh) <= cte_recombinacion || j == i3)) {
				// la variable 'j' del 'descendiente' toma el valor mutante 'v' si la variable 'j' no es fija (fijo[j] == 0) y se cumple la condición de
				//  recombinación, o si se trata de la variable (i3) que se debe cruzar obligatoriamente

				// mutación diferencial: el valor se obtiene a partir del mejor individuo de la población y de la diferencia entre dos individuos aleatorios
#ifdef ESTA_CRUCES
				num_cruces_si[hilo]++;
#endif
				v = poblacion[ind_mejor_merito][j] + factor_mutacion * (poblacion[i1][j] - poblacion[i2][j]);
				if (control_factibilidad) {
					if (v < cotas[0][j] || v > cotas[1][j]) {
						es_factible = false;
						break;
					}
				}
				descendiente[i][j] = v;
#ifdef ESTA_CRUCES
				num_cruces_ok[hilo]++;
#endif
			}
			else {
				// la variable 'j' del 'descendiente' toma el valor del individuo de la población, bien porque es una variable de valor fijo (todos los
				// individuos tienen el mismo valor), o porque no se cumple la condición de recombinación y no se trata de la variable 'i3' que se
				// debe cruzar obligatoriamente
#ifdef RECOMBINACION_NORMAL
				descendiente[i][j] = poblacion[i][j];
#else
				descendiente[i][j] = poblacion[ind_mejor_merito][j];
#endif

#ifdef ESTA_CRUCES
				num_cruces_no[hilo]++;
				if (fijo[j] == 1) {
					num_cruces_fj[hilo]++;
				}
#else
#ifdef NUM_GENES_PROGENITOR_2
				if (fijo[j] == 0) {
					num_genes_progenitor_2[hilo]++;
				}
#endif
#endif
			}
		}
		if (control_factibilidad) {
			factible[i] = es_factible;
		}
	}
}
/*
versión mono proceso
*/
void seleccion(int desde) {
	double me_descendiente;
	for (int i = desde; i < NPOB; i++) {
		if (!control_factibilidad || factible[i]) {
#ifdef DESVIACONES_RELATIVAS
			me_descendiente = merito_s_relativa(descendiente[i]);
#else
#ifdef FIN_MERITO_ANTICIPADO
			me_descendiente = merito_d(descendiente[i], merito_individuo[i]);
#else
			me_descendiente = merito_s(descendiente[i]);
#endif
#endif
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
/*
versión multiproceso, cada hilo se encarga de seleccionar una parte de la población, determinada por los parámetros 'desde' y 'hasta'
*/
void seleccionH(int desde, int hasta) {
	double me_descendiente;
	for (int i = desde; i < hasta; i++) {
		if (!control_factibilidad || factible[i]) {
#ifdef DESVIACONES_RELATIVAS
			me_descendiente = merito_s_relativa(descendiente[i]);
#else
#ifdef FIN_MERITO_ANTICIPADO
			me_descendiente = merito_d(descendiente[i], merito_individuo[i]);
#else
			me_descendiente = merito_s(descendiente[i]);
#endif
#endif
			if (me_descendiente < merito_individuo[i]) {
#ifdef COPIAR_CON_COPY
				std::copy(descendiente[i], descendiente[i] + NVEC, poblacion[i]);
#else
				for (int j = 0; j < NVEC; j++) {
					poblacion[i][j] = descendiente[i][j];
				}
#endif
				merito_individuo[i] = me_descendiente;
			}
		}
	}
}
/*
versión multiproceso, cada hilo se encarga de seleccionar una parte de la población, determinada por los parámetros 'desde' y 'hasta'
esta variante incluye el número del hilo que la llama, para poder contabilizar el número de mejoras que se producen en cada hilo
*/
void seleccionH(int desde, int hasta, int hilo) {
	double me_descendiente;
	for (int i = desde; i < hasta; i++) {
		if (!control_factibilidad || factible[i]) {
#ifdef DESVIACONES_RELATIVAS
			me_descendiente = merito_s_relativa(descendiente[i]);
#else
#ifdef FIN_MERITO_ANTICIPADO
			me_descendiente = merito_d(descendiente[i], merito_individuo[i]);
#else
			me_descendiente = merito_s(descendiente[i]);
#endif
#endif
			if (me_descendiente < merito_individuo[i]) {
#ifdef COPIAR_CON_COPY
				std::copy(descendiente[i], descendiente[i] + NVEC, poblacion[i]);
#else
				for (int j = 0; j < NVEC; j++) {
					poblacion[i][j] = descendiente[i][j];
				}
#endif
				merito_individuo[i] = me_descendiente;
#ifdef NUM_MEJORAS
				num_mejoras[hilo]++;
#endif
			}
		}
	}
}
#ifdef SELECCION_MAXIMA
void seleccion_maxima() {
	// para no sustiyuir más de una vez el mismo individuo de la población, se marca con 'ya' los individuos que ya han sido sustituidos
	int ya[30000] = { 0 };
	double me_descendiente;
	for (int i = 0; i < NPOB; i++) {
		if (!control_factibilidad || factible[i]) {
			me_descendiente = merito_s(descendiente[i]);
			if (me_descendiente < peor_merito) {
				// hay algún individuo con peor mérito que el descendiente, se busca uno de ellos que no haya sido sustituido todavía
				for (int j = 0; j < NPOB; j++) {
					if (ya[j] == 0) {
						if (me_descendiente < merito_individuo[j]) {
							ya[j] = 1;
							for (int k = 0; k < NVEC; k++) {
								poblacion[j][k] = descendiente[i][k];
							}
							merito_individuo[j] = me_descendiente;
							if (me_descendiente < mejor_merito) {
								mejor_merito = me_descendiente;
								ind_mejor_merito = j;
							}
							if (j == ind_peor_merito) {
								// hay que buscar el nuevo peor mérito de la población
								peor_merito = -1.;
								for (int k = 0; k < NPOB; k++) {
									if (merito_individuo[k] > peor_merito) {
										peor_merito = merito_individuo[k];
										ind_peor_merito = k;
									}
								}
							}
							break;
						}
					}
				}
			}
		}
	}
}
#endif
/*
se llama cada vez que se completa una generación, para comprobar si se ha alcanzado el número máximo de
generaciones, o para salvar la solución cada 'histo_sol' generaciones, o para imprimir información cada 'histo_int' generaciones
*/
int comprobar_final() {
#ifdef FIJAR_VARIABLES
	if (generacion > GENS_CALENTAR && (generacion % BLOQUE_FIJAR) == 0) {

		//desastroso, no funciona

		// tal vez si se computan las diferencias entre todos los pares posibles de individuos y si la diferencia máxima es inferior a 'TOL_DISPERSION' se
		// pueda fijar la variable en el valor medio de la población, pero no creo que el gasto de tiempo compense

		// las variables con una dipersión, en tanto por uno, inferior a 'TOL_DISPERSION' se fijan en el valor medio de la población
		int nc = 0;
		double d;
		for (int j = 0; j < NVEC; j++) {
			if (fijo[j] == 0) {
				// par cada variable no fija 'j'
				double med = 0.;
				for (int i = 0; i < NPOB; i++) {
					med += poblacion[i][j];
				}
				med /= NPOB;
				if (med > MIN_FIJAR) {
					double des = 0.;
					for (int i = 0; i < NPOB; i++) {
						d = poblacion[i][j] - med;
						des += d * d;
					}
					des = sqrt(des / (NPOB - 1));
					des /= med;							// em tamto por 1
					des /= 2.;							// la desviación es a los 2 lados de la media
					if (des < TOL_DISPERSION) {
						nc++;
						nvar_fijas++;
						fijo[j] = 1;
						for (int i = 0; i < NPOB; i++) {
							poblacion[i][j] = med;
						}
						fprintf(salida, "          %6d %12.5e %12.5e\n", j, med, des);
						fflush(salida);
					}
				}
			}
		}
		if (nc > 0) {
			// para mantener la coherencia se recalculan los méritos y el mejor
			mejor_merito = 1.0e+99;
			ind_mejor_merito = NPOB + 1;
			double v;
			for (int i = 0; i < NPOB; i++) {
#ifdef DESVIACONES_RELATIVAS
				v = merito_s_relativa(poblacion[i]);
#else
				v = merito_s(poblacion[i]);
#endif
				merito_individuo[i] = v;
				if (v < mejor_merito) {
					mejor_merito = v;
					ind_mejor_merito = i;
				}
			}
		}
	}
#endif
	if (histo_sol > 0 && (generacion % histo_sol) == 0) {
		char fichero[128];
		int n_sol = (int)(generacion / histo_sol);
		sprintf_s(fichero, 127, "%s/%d_%d_%d_%d_dll_sol_%03d.log", senda_salidas, id_salida, NPOB, modo_poblacion_inicial, (unsigned int)semilla, n_sol);
		salida_solucion(fichero);
	}
	if (histo_int > 0 && (generacion % histo_int) == 0) {
		double dist = distancia_clonacion();
#ifdef DESVIACONES_RELATIVAS
		merito_sol_relativa(poblacion[ind_mejor_merito]);
#else
		merito_sol(poblacion[ind_mejor_merito]);
#endif
		if (generacion == 0) {
#ifdef ESTA_CRUCES
			long long n_c_s = 0;
			long long n_c_o = 0;
			long long n_c_n = 0;
			long long n_c_f = 0;
			for (int i = 0; i < n_hilos; i++) {
				n_c_s += num_cruces_si[i];
				n_c_o += num_cruces_ok[i];
				n_c_n += num_cruces_no[i];
				n_c_f += num_cruces_fj[i];
				num_cruces_si[i] = 0;
				num_cruces_ok[i] = 0;
				num_cruces_no[i] = 0;
				num_cruces_fj[i] = 0;
			}
			fprintf(salida, "%9d %12.5e %12.5e %12.5e %6d %-8s %5d %6.1f %8.1f  %10lld %10lld %10lld %10lld %10lld %10lld\n", generacion, dist, mejor_merito, VEC_OPT_E[5], (int)VEC_OPT_E[6], rot_desvios[puntero_bloque_desviacion], desplazamiento_desviacion, dif_tpo_par, dif_tpo_tot, n_c_s, n_c_o, n_c_n, n_c_f, n_mej, n_mej_mej);
#else
			fprintf(salida, "%9d %12.5e %12.5e %12.5e %6d %-8s %5d                      %6d\n", generacion, dist, mejor_merito, VEC_OPT_E[5], (int)VEC_OPT_E[6], rot_desvios[puntero_bloque_desviacion], desplazamiento_desviacion, ind_mejor_merito);
#endif
			ftime(&tiempo_ini);
			ftime(&tiempo_ant);
		}
		else {
			ftime(&tiempo_act);
			// 'time' da el número de segundos transcurridos desde el 1 de enero de 1970, y 'millitm' da los milisegundos transcurridos desde el último segundo completo
			dif_tpo_par = (double)(tiempo_act.time - tiempo_ant.time) + (double)(tiempo_act.millitm - tiempo_ant.millitm) / 1000.;
			ftime(&tiempo_ant);
			// tiempo total desde el inicio del proceso en minutos
			dif_tpo_tot = ((double)(tiempo_act.time - tiempo_ini.time) + (double)(tiempo_act.millitm - tiempo_ini.millitm) / 1000.) / 60.;
			long long n_mej = 0;
			long long n_mej_mej = num_mejoras_mejor;
#ifdef NUM_MEJORAS
			for (int i = 0; i < n_hilos; i++) {
				n_mej += num_mejoras[i];
				num_mejoras[i] = 0;
			}
			num_mejoras_mejor = 0;
#endif
#ifdef ESTA_CRUCES
			long long n_c_s = 0;
			long long n_c_o = 0;
			long long n_c_n = 0;
			long long n_c_f = 0;
			for (int i = 0; i < n_hilos; i++) {
				n_c_s += num_cruces_si[i];
				n_c_o += num_cruces_ok[i];
				n_c_n += num_cruces_no[i];
				n_c_f += num_cruces_fj[i];
				num_cruces_si[i] = 0;
				num_cruces_ok[i] = 0;
				num_cruces_no[i] = 0;
				num_cruces_fj[i] = 0;
			}
			fprintf(salida, "%9d %12.5e %12.5e %12.5e %6d %-8s %5d %6.1f %8.1f  %10lld %10lld %10lld %10lld %10lld %10lld\n", generacion, dist, mejor_merito, VEC_OPT_E[5], (int)VEC_OPT_E[6], rot_desvios[puntero_bloque_desviacion], desplazamiento_desviacion, dif_tpo_par, dif_tpo_tot, n_c_s, n_c_o, n_c_n, n_c_f, n_mej, n_mej_mej);
#else
			long long n_v_h = 0;
#ifdef NUM_GENES_PROGENITOR_2
			for (int i = 0; i < n_hilos; i++) {
				n_v_h += num_genes_progenitor_2[i];
				num_genes_progenitor_2[i] = 0;
			}
#endif
#ifdef FIJAR_VARIABLES
			fprintf(salida, "%9d %12.5e %12.5e %12.5e %6d %-8s %5d %6.1f %8.1f  %10lld %10d\n", generacion, dist, mejor_merito, VEC_OPT_E[5], (int)VEC_OPT_E[6], rot_desvios[puntero_bloque_desviacion], desplazamiento_desviacion, dif_tpo_par, dif_tpo_tot, n_v_h, nvar_fijas);
#else
			fprintf(salida, "%9d %12.5e %12.5e %12.5e %6d %-8s %5d %6.1f %8.1f  %10lld %10lld %10lld\n", generacion, dist, mejor_merito, VEC_OPT_E[5], (int)VEC_OPT_E[6], rot_desvios[puntero_bloque_desviacion], desplazamiento_desviacion, dif_tpo_par, dif_tpo_tot, n_v_h, n_mej, n_mej_mej);
#endif
#endif
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
			// el mérito no ha progresado el valor mínimo establecido
			if (mejor_merito < tol_aceptable) {
				// terminar porque el error es aceptable
				histogenera[histo_n] = generacion;
				histograma[histo_n] = mejor_merito;
				return -3;
			}
			intentos++;
#ifdef FIJAR_VARIABLES
			GENS_CALENTAR += generacion;
#endif
			if (intentos < max_intentos) {
				// intentar con una nueva población inicial
				if (histo_sol != 0) {
					// salvar la mejor solución obtenida hasta ahora
					char fichero[128];
					sprintf_s(fichero, 127, "%s/%d_%d_%d_%d_dll_gen_%08d_iter_%03d.log", senda_salidas, id_salida, NPOB, modo_poblacion_inicial, (unsigned int)semilla, generacion, intentos - 1);
					salida_solucion(fichero);
				}
				histogenera[histo_n] = generacion;
				histograma[histo_n] = mejor_merito;
				histo_n++;
				if (histo_n == HISTO_MAX) {
					// registro circular
					histo_n = 0;
				}
				if (modo_reinicio_poblacion == 0) {
					genera_poblacion(vec_ini, modo_poblacion_inicial, 1.0);
					fprintf(salida, "Reinicio. Factor dispersión : %12.5e\n", factor_dispersion_actualizado * factor_dispersion);
				}
				else {
					factor_dispersion_actualizado *= variacion_dispersion;
					genera_poblacion(vec_ini, modo_poblacion_inicial, factor_dispersion_actualizado);
					fprintf(salida, "Reinicio. Factor dispersión : %12.5e\n", factor_dispersion_actualizado * factor_dispersion);
				}
				double dist = distancia_clonacion();
#ifdef DESVIACONES_RELATIVAS
				merito_sol_relativa(poblacion[ind_mejor_merito]);
#else
				merito_sol(poblacion[ind_mejor_merito]);
#endif
				ftime(&tiempo_act);
				dif_tpo_par = (double)(tiempo_act.time - tiempo_ant.time) + (double)(tiempo_act.millitm - tiempo_ant.millitm) / 1000.;
				ftime(&tiempo_ant);
				dif_tpo_tot = ((double)(tiempo_act.time - tiempo_ini.time) + (double)(tiempo_act.millitm - tiempo_ini.millitm) / 1000.) / 60.;
#ifdef ESTA_CRUCES
				long long n_c_s = 0;
				long long n_c_o = 0;
				long long n_c_n = 0;
				long long n_c_f = 0;
				for (int i = 0; i < n_hilos; i++) {
					n_c_s += num_cruces_si[i];
					n_c_o += num_cruces_ok[i];
					n_c_n += num_cruces_no[i];
					n_c_f += num_cruces_fj[i];
					num_cruces_si[i] = 0;
					num_cruces_ok[i] = 0;
					num_cruces_no[i] = 0;
					num_cruces_fj[i] = 0;
				}
				fprintf(salida, "%9d %12.5e %12.5e %12.5e %6d %-8s %5d %6.1f %8.1f  %10lld %10lld %10lld %10lld %10lld %10lld\n", generacion, dist, mejor_merito, VEC_OPT_E[5], (int)VEC_OPT_E[6], rot_desvios[puntero_bloque_desviacion], desplazamiento_desviacion, dif_tpo_par, dif_tpo_tot, n_c_s, n_c_o, n_c_n, n_c_f, n_mej, n_mej_mej);
#else
				fprintf(salida, "%9d %12.5e %12.5e %12.5e %6d %-8s %5d %6.1f %8.1f  %10d\n", generacion, dist, mejor_merito, VEC_OPT_E[5], (int)VEC_OPT_E[6], rot_desvios[puntero_bloque_desviacion], desplazamiento_desviacion, dif_tpo_par, dif_tpo_tot, ind_mejor_merito);
#endif
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
				// se han superado los intentos disponibles
				intentos--;
				histogenera[histo_n] = generacion;
				histograma[histo_n] = mejor_merito;
				return -3;
			}
		}
		else if ((int)(fraccion_regularizacion * NPOB) > 0 && ((mejor_merito_anterior - mejor_merito) < umbral_regularizacion * mejor_merito_anterior * min_progreso)) {
			// "regularización", sustituir un porcentaje de individuos (seleccionados al azar) por otros con valores generados aleatoriamente (modo 0)
			if (regularizaciones == max_intentos) {
				// agotadas las regularizaciones, reiniciar la población si procede
				if (intentos < max_intentos) {
					// intentar con una nueva población inicial
					if (histo_sol != 0) {
						// salvar la mejor solución obtenida hasta ahora
						char fichero[128];
						sprintf_s(fichero, 127, "%s/%d_%d_%d_%d_dll_gen_%08d_iter_%03d.log", senda_salidas, id_salida, NPOB, modo_poblacion_inicial, (unsigned int)semilla, generacion, intentos - 1);
						salida_solucion(fichero);
					}
					histogenera[histo_n] = generacion;
					histograma[histo_n] = mejor_merito;
					histo_n++;
					if (histo_n == HISTO_MAX) {
						// registro circular
						histo_n = 0;
					}
					if (modo_reinicio_poblacion == 0) {
						genera_poblacion(vec_ini, modo_poblacion_inicial, 1.0);
						fprintf(salida, "Reinicio. Factor dispersión : %12.5e\n", factor_dispersion_actualizado * factor_dispersion);
					}
					else {
						factor_dispersion_actualizado *= variacion_dispersion;
						genera_poblacion(vec_ini, modo_poblacion_inicial, factor_dispersion_actualizado);
						fprintf(salida, "Reinicio. Factor dispersión : %12.5e\n", factor_dispersion_actualizado * factor_dispersion);
					}
					double dist = distancia_clonacion();
#ifdef DESVIACONES_RELATIVAS
					merito_sol_relativa(poblacion[ind_mejor_merito]);
#else
					merito_sol(poblacion[ind_mejor_merito]);
#endif
					ftime(&tiempo_act);
					dif_tpo_par = (double)(tiempo_act.time - tiempo_ant.time) + (double)(tiempo_act.millitm - tiempo_ant.millitm) / 1000.;
					ftime(&tiempo_ant);
					dif_tpo_tot = ((double)(tiempo_act.time - tiempo_ini.time) + (double)(tiempo_act.millitm - tiempo_ini.millitm) / 1000.) / 60.;
#ifdef ESTA_CRUCES
					long long n_c_s = 0;
					long long n_c_o = 0;
					long long n_c_n = 0;
					long long n_c_f = 0;
					for (int i = 0; i < n_hilos; i++) {
						n_c_s += num_cruces_si[i];
						n_c_o += num_cruces_ok[i];
						n_c_n += num_cruces_no[i];
						n_c_f += num_cruces_fj[i];
						num_cruces_si[i] = 0;
						num_cruces_ok[i] = 0;
						num_cruces_no[i] = 0;
						num_cruces_fj[i] = 0;
					}
					fprintf(salida, "%9d %12.5e %12.5e %12.5e %6d %-8s %5d %6.1f %8.1f  %10lld %10lld %10lld %10lld %10lld %10lld\n", generacion, dist, mejor_merito, VEC_OPT_E[5], (int)VEC_OPT_E[6], rot_desvios[puntero_bloque_desviacion], desplazamiento_desviacion, dif_tpo_par, dif_tpo_tot, n_c_s, n_c_o, n_c_n, n_c_f, n_mej, n_mej_mej);
#else
					fprintf(salida, "%9d %12.5e %12.5e %12.5e %6d %-8s %5d %6.1f %8.1f  %10d\n", generacion, dist, mejor_merito, VEC_OPT_E[5], (int)VEC_OPT_E[6], rot_desvios[puntero_bloque_desviacion], desplazamiento_desviacion, dif_tpo_par, dif_tpo_tot, ind_mejor_merito);
#endif
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
					// se han superado los intentos disponibles
					intentos--;
					histogenera[histo_n] = generacion;
					histograma[histo_n] = mejor_merito;
					return -3;
				}
			}
			else {
				regularizaciones++;
				double var_merito = mejor_merito_anterior - mejor_merito;
				double semi_izq;
				double semi_dch;
				double semi_intervalo;
				double desplazamiento;
				double f;
				double v;
				int i;
				int nindis = (int)(fraccion_regularizacion * NPOB);
				// sustituir al mejor individuo
				i = ind_mejor_merito;
				for (int j = 0; j < NVEC; j++) {
					if (fijo[j] == 1) {
						poblacion[i][j] = cotas[0][j];
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
						desplazamiento = f * factor_dispersion * dis_double(gen) * semi_intervalo;
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
				int susti = 1;
				while (susti < nindis) {
					i = dis_entero(gen);
					// al mejor individuo ya se ha sustituido
					if (i != ind_mejor_merito) {
						for (int j = 0; j < NVEC; j++) {
							if (fijo[j] == 1) {
								poblacion[i][j] = cotas[0][j];
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
								desplazamiento = f * factor_dispersion * dis_double(gen) * semi_intervalo;
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
#ifdef DESVIACONES_RELATIVAS
						v = merito_s_relativa(poblacion[i]);
#else
						v = merito_s(poblacion[i]);
#endif
						factible[i] = true;	// es innecesario
						susti++;
					}
				}
				// recalcular el mejor individuo
				for (int i = 0; i < NPOB; i++) {
					v = merito_individuo[i];
					if (v < mejor_merito) {
						mejor_merito = v;
						ind_mejor_merito = i;
					}
#ifdef SELECCION_MAXIMA
					if (v > peor_merito) {
						peor_merito = v;
						ind_peor_merito = i;
					}
#endif
				}
				fprintf(salida, "          Regularización    : %12.5e < %12.5e    nuevo mejor: %12.5e\n", var_merito, umbral_regularizacion * mejor_merito_anterior * min_progreso, mejor_merito);
				mejor_merito_anterior = 1.0e+99;
			}
		}
		else {
			if (!control_factibilidad) {
				// sin 'control_factibilidad' la dispersión de población puede dispersarse
				double dist = distancia_clonacion();
				if (dist > 1.e+24) {
					// si la dipersión es muy alta, hay que reiniciar la población
					intentos++;
#ifdef FIJAR_VARIABLES
					GENS_CALENTAR += generacion;
#endif
					if (intentos < max_intentos) {
						if (histo_sol != 0) {
							// salvar la mejor solución obtenida hasta ahora
							char fichero[128];
							sprintf_s(fichero, 127, "%s/%d_%d_%d_%d_dll_gen_%08d_iter_%03d.log", senda_salidas, id_salida, NPOB, modo_poblacion_inicial, (unsigned int)semilla, generacion, intentos - 1);
							salida_solucion(fichero);
						}
						histogenera[histo_n] = generacion;
						histograma[histo_n] = mejor_merito;
						histo_n++;
						if (histo_n == HISTO_MAX) {
							// registro circular
							histo_n = 0;
						}
						if (modo_reinicio_poblacion == 0) {
							genera_poblacion(vec_ini, modo_poblacion_inicial, 1.0);
							fprintf(salida, "Reinicio. Factor dispersión : %12.5e\n", factor_dispersion_actualizado * factor_dispersion);
						}
						else {
							factor_dispersion_actualizado *= variacion_dispersion;
							genera_poblacion(vec_ini, modo_poblacion_inicial, factor_dispersion_actualizado);
							fprintf(salida, "Reinicio. Factor dispersión : %12.5e\n", factor_dispersion_actualizado * factor_dispersion);
						}
						double dist = distancia_clonacion();
#ifdef DESVIACONES_RELATIVAS
						merito_sol_relativa(poblacion[ind_mejor_merito]);
#else
						merito_sol(poblacion[ind_mejor_merito]);
#endif
						ftime(&tiempo_act);
						dif_tpo_par = (double)(tiempo_act.time - tiempo_ant.time) + (double)(tiempo_act.millitm - tiempo_ant.millitm) / 1000.;
						ftime(&tiempo_ant);
						dif_tpo_tot = ((double)(tiempo_act.time - tiempo_ini.time) + (double)(tiempo_act.millitm - tiempo_ini.millitm) / 1000.) / 60.;
#ifdef ESTA_CRUCES
						long long n_c_s = 0;
						long long n_c_o = 0;
						long long n_c_n = 0;
						long long n_c_f = 0;
						for (int i = 0; i < n_hilos; i++) {
							n_c_s += num_cruces_si[i];
							n_c_o += num_cruces_ok[i];
							n_c_n += num_cruces_no[i];
							n_c_f += num_cruces_fj[i];
							num_cruces_si[i] = 0;
							num_cruces_ok[i] = 0;
							num_cruces_no[i] = 0;
							num_cruces_fj[i] = 0;
						}
						fprintf(salida, "%9d %12.5e %12.5e %12.5e %6d %-8s %5d %6.1f %8.1f  %10lld %10lld %10lld %10lld %10lld %10lld\n", generacion, dist, mejor_merito, VEC_OPT_E[5], (int)VEC_OPT_E[6], rot_desvios[puntero_bloque_desviacion], desplazamiento_desviacion, dif_tpo_par, dif_tpo_tot, n_c_s, n_c_o, n_c_n, n_c_f, n_mej, n_mej_mej);
#else
						fprintf(salida, "%9d %12.5e %12.5e %12.5e %6d %-8s %5d %6.1f %8.1f  %10d\n", generacion, dist, mejor_merito, VEC_OPT_E[5], (int)VEC_OPT_E[6], rot_desvios[puntero_bloque_desviacion], desplazamiento_desviacion, dif_tpo_par, dif_tpo_tot, ind_mejor_merito);
#endif
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

void salida_solucion(char* fichero) {
#ifdef DESVIACONES_RELATIVAS
	merito_sol_relativa(poblacion[ind_mejor_merito]);
#else
	merito_sol(poblacion[ind_mejor_merito]);
#endif
	FILE* sal_sol = _fsopen(fichero, "w", _SH_DENYWR);
	if (sal_sol != 0) {

		// mérito

		fprintf(sal_sol, "%10d;%-8s;;%17.9e\n", generacion, "Error", me_sol[4]);

		// vector solución ampliado por el precio del factor que no forma parte del vector solución
		// pero si de 'me_sol'

		int n = 0;
		int nsol = LCAB;
		fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "pF", 0, me_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "pF", 1, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "pY", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "pQ", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "pD", i, me_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "epsilon", 0, me_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Apz", 0, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) {
			for (int j = 0; j < NFAC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Fi", i * NFAC + j, me_sol[nsol++]);
			}
		}
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Ei", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Mi", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Di", i, me_sol[nsol++]);
		if (op.GE_INCLUYE_XP) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NSEC; j++) {
					fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Xpi", i * NSEC + j, me_sol[nsol++]);
				}
			}
		}

		// variables que se calculan una sola vez

		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "pz", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "pe", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "pm", i, me_sol[nsol++]);

		// variables calculadas en el primer pase

		for (int i = 0; i < NSEC; i++) {
			for (int j = 0; j < NFAC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "F", i * NFAC + j, me_sol[nsol++]);
			}
		}
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "E", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "M", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Yp", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Yd", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Da", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Dt", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Z", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Xg", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Xv", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Q", i, me_sol[nsol++]);
		for (int i = 0; i < NDEM; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Td", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Tz", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Tm", i, me_sol[nsol++]);
		for (int i = 0; i < NDEM; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Sp", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "AgE", i, me_sol[nsol++]);
		for (int i = 0; i < NDEM; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "AgH", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "CssE", i, me_sol[nsol++]);
		for (int i = 0; i < NDEM; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "CssH", i, me_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Sg", 0, me_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Sc", 0, me_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Sf", 0, me_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "ebp", 0, me_sol[nsol++]);
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NSEC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Xp", i * NSEC + j, me_sol[nsol++]);
			}
		}
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NFAC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "FF", i * NFAC + j, me_sol[nsol++]);
			}
		}
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NFAC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Alp", i * NFAC + j, me_sol[nsol++]);
			}
		}
		for (int i = 0; i < NSEC; i++) {
			for (int j = 0; j < NSEC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "X", i * NSEC + j, me_sol[nsol++]);
			}
		}
		fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Ti", 0, me_sol[nsol++]);

		// recálculos de las variables, saltamos los valores del primer paso 'LVARS_PP' (incluidas las que se calculan una sola vez)

		// nsol = LCAB + NVEC + 1 + LVARS_PP;	// innecesario, 'nsol' es continuación de lo anterior
		for (int i = 0; i < NSEC; i++) {
			for (int j = 0; j < NFAC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Fr", i * NFAC + j, me_sol[nsol++]);
			}
		}
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Er", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Mr", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Ypr", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Ydr", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Dar", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Dtr", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Zr", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Xgr", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Xvr", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Qr", i, me_sol[nsol++]);
		for (int i = 0; i < NDEM; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Tdr", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Tzr", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Tmr", i, me_sol[nsol++]);
		for (int i = 0; i < NDEM; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Spr", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "AgEr", i, me_sol[nsol++]);
		for (int i = 0; i < NDEM; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "AgHr", i, me_sol[nsol++]);
		for (int i = 0; i < NSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "CssEr", i, me_sol[nsol++]);
		for (int i = 0; i < NDEM; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "CssHr", i, me_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Sgr", 0, me_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Scr", 0, me_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Sfr", 0, me_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "ebpr", 0, me_sol[nsol++]);
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NSEC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Xpr", i * NSEC + j, me_sol[nsol++]);
			}
		}
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NFAC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "FFr", i * NFAC + j, me_sol[nsol++]);
			}
		}
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NFAC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Alpr", i * NFAC + j, me_sol[nsol++]);
			}
		}
		for (int i = 0; i < NSEC; i++) {
			for (int j = 0; j < NSEC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Xr", i * NSEC + j, me_sol[nsol++]);
			}
		}
		fprintf(sal_sol, "%5d;%-8s;%5d;%17.9e\n", n++, "Tir", 0, me_sol[nsol++]);

		fclose(sal_sol);
	}
	else {
		fprintf(salida, "*--* No se pudo abrir el fichero [%s] para salvar la solución [g:%d i:%d]\n", fichero, generacion, intentos - 1);
	}
}
/*
mide lo proximo que estan todos los individuos de la población, en relación al mejor individuo, para tener una idea de la diversidad de la población
*/
double distancia_clonacion() {
	// desviación estándar de la población respecto al mejor individuo
	double d;
	double des = 0.;
	for (int i = 0; i < NPOB; i++) {
		for (int j = 0; j < NVEC; j++) {
			d = poblacion[i][j] - poblacion[ind_mejor_merito][j];
			des += d * d;
		}
	}
	return sqrt(des / (double)((NPOB - 1) * NVEC));
}
/*
**********************************************************************************************************************************************************************************
Multi proceso con hilos cerrados. Cada hilo calcula un tramo de la población y el ciclo temporal espera a que terminen todos los hilos para continuar con la siguiente generación.
**********************************************************************************************************************************************************************************
*/
bool Arranque() {
	factor_mutacion = (par_mutacion[0] + par_mutacion[1]) / 2.;
	CANCELADO = false;
	return true;
}
int PreparaMP() {
	// Comprobar que el número de individuos de la población es múltiplo del número de hilos (procesos)

	int bloques = NPOB / n_hilos;
	if (bloques * n_hilos != NPOB) {
		//printf("Cancelado. El numero de individuos debe ser multiplo del numero de hilos (procesos)\n");
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
#ifdef SELECCION_MAXIMA
			seleccion_maxima();
#else
			for (int i = 0; i < NPOB; i++) {
				if (merito_individuo[i] < mejor_merito) {
					mejor_merito = merito_individuo[i];
					ind_mejor_merito = i;
					num_mejoras_mejor++;
				}
			}
#endif
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
			factor_mutacion = par_mutacion[0] + dis_double(gen) * (par_mutacion[1] - par_mutacion[0]);
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
			fprintf(salida, "El hilo %d: superó el tiempo de espera\n", GetCurrentThreadId());
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
/*
los hilos se crean una sola vez, crearlos y cerrarlos a cada generación consume más tiempo del que ahorran, para esto se usa un
ciclo perpetuo, donde cada cada hilo espera a que se le permita calcular su tramo, y avisando al hilo 'director' cuando termina,
para que este decida iniciar una nueva generación, o terminar, si se ha alcanzado el número máximo de generaciones o se ha cancelado el proceso
*/
unsigned int WINAPI HiloTramos(LPVOID param)
{
	int* parametros = (int*)param;
	int hilo = parametros[0];
	int desde = parametros[1];
	int hasta = parametros[2];

	/*
			NO PARECE TENER NINGUN EFECTO
	establece la prioridad del hilo respecto a la prioridad base (clase)
		THREAD_PRIORITY_ABOVE_NORMAL es menos crítica
	*/
	/*
	if (!SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_HIGHEST))
	{
		fprintf(salida, "*--* Error (%d) al establecer la priodidad del hilo %d\n", GetLastError(), hilo);
	}
	*/
#ifdef AZAR_HILOS_LOCAL
	// variables locales para cada hilo, para que no se solapen los números aleatorios generados por los hilos
	thread_local mt19937 gh;

#ifdef MT19937
#ifdef INI_AZAR_FICHERO
	inicia_azar(gh, (unsigned int)(semilla + indice));
#else
	gh = mt19937((unsigned int)(semilla + hilo));
#endif INI_AZAR_FICHERO
#else MT19937
	gh = minstd_rand((unsigned int)(semilla + indice));
#endif MT19937

	thread_local uniform_int_distribution<int> he{};
	thread_local uniform_int_distribution<int> hi{};
	thread_local uniform_real_distribution<double> hd{};
	if (poner_el_mejor_primero) {
		he = uniform_int_distribution<int>{ 1, (int)(NPOB - 1) };
	}
	else {
		he = uniform_int_distribution<int>{ 0, (int)(NPOB - 1) };
	}
	hi = uniform_int_distribution<int>{ 0, (int)(NVEC - 1) };
	hd = uniform_real_distribution<double>{ 0.0, 1.0 };
#endif AZAR_HILOS_LOCAL

	// Ciclo perpetuo

	DWORD resSemaforo;
	while (TRUE)
	{
		// pone en espera el hilo 'indice'

		//printf("el hilo %d entra en espera\n", indice);

		resSemaforo = WaitForSingleObject(semaforo_hilo[hilo], INFINITE);

		//printf("el hilo %d sale de la espera\n", indice);

		switch (resSemaforo)
		{
		case WAIT_OBJECT_0:
			//printf("el hilo %d empieza a calcular\n", indice);
#ifdef AZAR_HILOS_LOCAL	
			// 'ProcesarTramo' recibe 'gh, he, hi, hd' mediante referencia
			ProcesarTramo(hilo, desde, hasta, gh, he, hi, hd);
#else
			ProcesarTramo(indice, desde, hasta);
#endif
			EnterCriticalSection(&seccion_fin_hilos);

			//printf("el hilo %d termina de calcular\n", indice);

			hilos_terminados++;
			if (hilos_terminados == n_hilos) {

				// Libera el semaforo para iterar

				//printf("orden de terminar la espera del hilo de iterar\n");

				while (ReleaseSemaphore(semaforo_itera, 1, NULL) == FALSE);
			}
			LeaveCriticalSection(&seccion_fin_hilos);
			break;
		case WAIT_TIMEOUT:
			fprintf(salida, "\nEl hilo %d superó el tiempo de espera\n", hilo);
			break;
		}
	}
	return 0;
}
/*
función que hace que cada hilo procese un tramo de la población, realizando mutación, cruce y selección.
*/
void ProcesarTramo(int hilo, int desde, int hasta) {
	mutacion_cruzeH(desde, hasta, hilo);

	// si está definido 'SELECCION_MAXIMA' la selección se hace al final de cada generación, en el hilo director
#ifndef SELECCION_MAXIMA

#ifdef NUM_MEJORAS
	seleccionH(desde, hasta, hilo);
#else
	seleccionH(desde, hasta);
#endif

#endif
}
/*
'ProcesarTramo' recibe 'gh, he, hi, hd' mediante referencia
*/
void ProcesarTramo(int hilo, int desde, int hasta, mt19937& gh, uniform_int_distribution<int>& he, uniform_int_distribution<int>& hi, uniform_real_distribution<double>& hd) {
	mutacion_cruzeH(desde, hasta, hilo, gh, he, hi, hd);
#ifndef SELECCION_MAXIMA

#ifdef NUM_MEJORAS
	seleccionH(desde, hasta, hilo);
#else
	seleccionH(desde, hasta);
#endif

#endif
}
#ifdef INI_AZAR_FICHERO
// recibimos '*g' (g por referencia) y el número de hilo 'hilo' y no hgen[i], para que sea un paso por referencia y hgen[i] se inicialice correctamente
void inicia_azar(mt19937* g, int hilo, unsigned int semilla)
{
	char fichero[128];
	sprintf_s(fichero, 127, "%s/%d.dat", senda_salidas, semilla);
	ifstream frand(fichero);
	if (frand.is_open())
		// si existe el fichero con la semilla, se carga el generador de números aleatorios con los datos guardados en el fichero
		frand >> g[hilo];
	else
	{
		// si no existe el fichero con la semilla, se genera un nuevo generador de números aleatorios y se guarda en el fichero
		array<int, 624> seed_data;
		random_device r;
		generate_n(seed_data.data(), seed_data.size(), std::ref(r));
		seed_seq seq(begin(seed_data), end(seed_data));
		g[hilo].seed(seq);

		ofstream frand(fichero);
		if (frand.is_open())
			frand << g[hilo];
		frand.close();
	}
	frand.close();
}
void inicia_azar(mt19937& g, unsigned int semilla)
{
	char fichero[128];
	sprintf_s(fichero, 127, "%s/%d.dat", senda_salidas, semilla);
	ifstream frand(fichero);
	if (frand.is_open())
		// si existe el fichero con la semilla, se carga el generador de números aleatorios con los datos guardados en el fichero
		frand >> g;
	else
	{
		// si no existe el fichero con la semilla, se genera un nuevo generador de números aleatorios y se guarda en el fichero
		array<int, 624> seed_data;
		random_device r;
		generate_n(seed_data.data(), seed_data.size(), std::ref(r));
		seed_seq seq(begin(seed_data), end(seed_data));
		g.seed(seq);

		ofstream frand(fichero);
		if (frand.is_open())
			frand << g;
		frand.close();
	}
	frand.close();
}
#endif
#pragma endregion

#pragma region Merito

/*
la parte de la DLL relacionada con el modelo: ecuaciones, parámetros, datos iniciales y opciones de cálculo del 'merito'
*/

double AYD_ADI_DEM[NDEM]{};

OPCIONES recibe_opciones(OPCIONES vopt) {
	op = vopt;
	pvec[0] = 0;
	for (int i = 1; i < N_BLO_VEC + 1; i++) {
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
#ifdef CONSUMO_INTERMEDIO_INDESADO
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
#endif
	parametros = vpar;
	return parametros;
}
/*
función objetivo multiproceso, la que hay que usar siempre, aunque no se utilice multiproceso
*/
double merito_s(double* vec_opt) {
	/*
	No se pueden poner restricciones a variables que no formen parte de 'vec_opt'
	una cosa es que no haya gradientes y otra que la función objetivo dependa de cosas distintas a sus variables,
	el proceso de cruce va reduciendo, para cada variable, las diferencias, de su valor, entre los distintos individuos de la población

	al definir las matices no se inicializan porque es innecesario ya que a todas las variables se les asigna un valor como parte del proceso de cálculo
	*/
	double pf[NFAC];
	double py[NSEC];
	double pq[NSEC];
	double pd[NSEC];
	double Fi[NSEC][NFAC];
	double Ei[NSEC];
	double Mi[NSEC];
	double Di[NSEC];
	double Xpi[NDEM][NSEC];

	double pe[NSEC];
	double pm[NSEC];
	double pz[NSEC];
	double F[NSEC][NFAC];
	double E[NSEC];
	double M[NSEC];
	double D[NSEC];
	double Yp[NSEC];
	double Yd[NSEC];
	double Ypd[NSEC];		// no es una variable del modelo, es la media de Yp y Yd, para el cálculo de la optimización de los factores
	double Z[NSEC];
#ifdef CONSUMO_INTERMEDIO_INDESADO
	double X[NSEC][NSEC]{};	// es necesario inicializar a cero cuando se usa CONSUMO_INTERMEDIO_INDESADO
#else
	double X[NSEC][NSEC];
#endif
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
	double Da[NSEC];
	double Dt[NSEC];

	double Fr[NSEC][NFAC];
	double Er[NSEC];
	double Mr[NSEC];
	double Ypr[NSEC];
	double Ydr[NSEC];
	double Zr[NSEC];
	double Xr[NSEC][NSEC]{};	// es necesario inicializar a cero cuando se usa CONSUMO_INTERMEDIO_INDESADO
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

	double Ti;
	double Sg;
	double Sc;
	double Sf;
	double ebp;

	double Tir;
	double Sgr;
	double Scr;
	double Sfr;
	double ebpr;

	double exceso;
	double suma_F;
	double suma_FF;
	double sum_Xp;
	double sum_X;

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
		if (op.ALP_FACTOR > 0.) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					exceso = FF[i][j] - datos.FF0[i][j];
					Alp[i][j] = exceso * op.ALP_FACTOR;
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
	ahorro_hogares_Sp(Sp, parametros.ssp, pf, FF, datos.PssH0);
	Ti = impuestos_directos_Ti(parametros.tai, pf, FF, op.INDICE_F_TRA);
	ayudas_AgE_AgH(AgE, AgH, parametros.cage, parametros.cagh, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssE, parametros.ctzsse, pf, F, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssH, parametros.ctzssh, pf, FF, Alp, op.INDICE_F_TRA);
	Sg = gobierno_Sg_Xg(Xg, parametros.ssg, parametros.mu, pq, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AgE, AgH, datos.PssH0, CssH, CssE);
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
	demanda_inversion_Xv(Xv, parametros.landa, pq, Sp, Sg, Sc, epsilon, Sf, Ti, datos.Te0);
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
	produccion_factor_compuesto_Y(Ypr, F, parametros.beta, parametros.b);
	restriccion_produccion_bruta_Z(Zr, parametros.teta, parametros.xie, parametros.xid, E, Dt, parametros.phi);
	consumo_intermedio_X(Xr, Zr, parametros.ax);
	utilizacion_factor_compuesto_Y(Ydr, Zr, parametros.ay);
	for (int i = 0; i < NSEC; i++) {
		Ypd[i] = (Ypr[i] + Ydr[i]) / 2.;
	}
	uso_optimo_factores_F(Fr, parametros.beta, pf, py, Ypd);
	if (op.FF_ENDOGENA) {
		aportacion_factores_FF(FFr, datos.FF0, Fr);
		if (op.ALP_FACTOR > 0.) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					exceso = FFr[i][j] - datos.FF0[i][j];
					Alpr[i][j] = exceso * op.ALP_FACTOR;
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
	ahorro_hogares_Sp(Spr, parametros.ssp, pf, FFr, datos.PssH0);
	Tir = impuestos_directos_Ti(parametros.tai, pf, FFr, op.INDICE_F_TRA);
	ayudas_AgE_AgH(AgEr, AgHr, parametros.cage, parametros.cagh, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssEr, parametros.ctzsse, pf, Fr, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssHr, parametros.ctzssh, pf, FFr, Alpr, op.INDICE_F_TRA);
	Sgr = gobierno_Sg_Xg(Xgr, parametros.ssg, parametros.mu, pq, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, AgEr, AgHr, datos.PssH0, CssHr, CssEr);
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
	demanda_inversion_Xv(Xvr, parametros.landa, pq, Spr, Sgr, Scr, epsilon, Sfr, Tir, datos.Te0);
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
		// trata de que 'ebpr' sea igual a 'ebp' y a cero
		dd = abs(ebp) + abs(ebpr);
	}
	else {
		dd = Sfr - Sf;
	}
	dist += dd * dd;

	// se calcula solo para los valores del segundo pase
	/*
	for (int i = 0; i < NSEC; i++) {
		sum_Xp = 0.;
		for (int j = 0; j < NDEM; j++) {
			sum_Xp += Xp[j][i];
		}
		sum_X = 0.;
		for (int j = 0; j < NSEC; j++) {
			sum_X += X[j][i];
		}
		dd = Q[i] - (sum_Xp + Xg[i] + Xv[i] + sum_X);
		dist += dd * dd;
	}
	*/
	for (int i = 0; i < NSEC; i++) {
		sum_Xp = 0.;
		for (int j = 0; j < NDEM; j++) {
			sum_Xp += Xpr[j][i];
		}
		sum_X = 0.;
		for (int j = 0; j < NSEC; j++) {
			sum_X += Xr[j][i];
		}
		dd = Qr[i] - (sum_Xp + Xgr[i] + Xvr[i] + sum_X);
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
		// se calcula solo para los valores del segundo pase
		/*
		for (int i = 0; i < NFAC; i++) {
			suma_F = 0.;
			for (int j = 0; j < NSEC; j++) {
				suma_F += abs(F[j][i]);
			}
			suma_FF = 0.;
			for (int j = 0; j < NDEM; j++) {
				suma_FF += abs(FF[j][i]);
			}
			dd = suma_F - suma_FF;
			dist += dd * dd;
		}
		*/
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
#ifdef USAR_PESO_YDP
		dd = (Ydr[i] - Ypr[i]) * PESO_YDP;
#else
		dd = Ydr[i] - Ypr[i];
#endif
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
	dd = Tir - Ti;
	dist += dd * dd;
	if (op.OPT_DESVIOS == 0) {
		for (int i = 0; i < NSEC; i++) {
			dd = Ypr[i] - Yp[i];
			dist += dd * dd;
			dd = Ydr[i] - Yd[i];
			dist += dd * dd;
			dd = Dar[i] - Da[i];
			dist += dd * dd;
			dd = Dtr[i] - Dt[i];
			dist += dd * dd;
		}
	}
#ifdef ECM
	dist = sqrt(dist / N_DESVIACIONES);
#endif
	return dist;
}
#ifdef AJUSTA_POB_INICIAL
double ajustar_vec_solucion(double* vec_opt) {
	/*
	No se pueden poner restricciones a variables que no formen parte de 'vec_opt'
	una cosa es que no haya gradientes y otra que la función objetivo dependa de cosas distintas a sus variables,
	el proceso de cruce va reduciendo, para cada variable, las diferencias, de su valor, entre los distintos individuos de la población

	al definir las matices no se inicializan porque es innecesario ya que a todas las variables se les asigna un valor como parte del proceso de cálculo
	*/
	double pf[NFAC];
	double py[NSEC];
	double pq[NSEC];
	double pd[NSEC];
	double Fi[NSEC][NFAC];
	double Ei[NSEC];
	double Mi[NSEC];
	double Di[NSEC];
	double Xpi[NDEM][NSEC];

	double pe[NSEC];
	double pm[NSEC];
	double pz[NSEC];
	double F[NSEC][NFAC];
	double E[NSEC];
	double M[NSEC];
	double D[NSEC];
	double Yp[NSEC];
	double Yd[NSEC];
	double Ypd[NSEC];		// no es una variable del modelo, es la media de Yp y Yd, para el cálculo de la optimización de los factores
	double Z[NSEC];
#ifdef CONSUMO_INTERMEDIO_INDESADO
	double X[NSEC][NSEC]{};	// es necesario inicializar a cero cuando se usa CONSUMO_INTERMEDIO_INDESADO
#else
	double X[NSEC][NSEC];
#endif
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
	double Da[NSEC];
	double Dt[NSEC];

	double Fr[NSEC][NFAC];
	double Er[NSEC];
	double Mr[NSEC];
	double Ypr[NSEC];
	double Ydr[NSEC];
	double Zr[NSEC];
	double Xr[NSEC][NSEC]{};	// es necesario inicializar a cero cuando se usa CONSUMO_INTERMEDIO_INDESADO
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

	double Ti;
	double Sg;
	double Sc;
	double Sf;
	double ebp;

	double Tir;
	double Sgr;
	double Scr;
	double Sfr;
	double ebpr;

	double exceso;
	double suma_F;
	double suma_FF;
	double sum_Xp;
	double sum_X;

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
		if (op.ALP_FACTOR > 0.) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					exceso = FF[i][j] - datos.FF0[i][j];
					Alp[i][j] = exceso * op.ALP_FACTOR;
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
	ahorro_hogares_Sp(Sp, parametros.ssp, pf, FF, datos.PssH0);
	Ti = impuestos_directos_Ti(parametros.tai, pf, FF, op.INDICE_F_TRA);
	ayudas_AgE_AgH(AgE, AgH, parametros.cage, parametros.cagh, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssE, parametros.ctzsse, pf, F, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssH, parametros.ctzssh, pf, FF, Alp, op.INDICE_F_TRA);
	Sg = gobierno_Sg_Xg(Xg, parametros.ssg, parametros.mu, pq, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AgE, AgH, datos.PssH0, CssH, CssE);
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
	demanda_inversion_Xv(Xv, parametros.landa, pq, Sp, Sg, Sc, epsilon, Sf, Ti, datos.Te0);
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
	produccion_factor_compuesto_Y(Ypr, F, parametros.beta, parametros.b);
	restriccion_produccion_bruta_Z(Zr, parametros.teta, parametros.xie, parametros.xid, E, Dt, parametros.phi);
	consumo_intermedio_X(Xr, Zr, parametros.ax);
	utilizacion_factor_compuesto_Y(Ydr, Zr, parametros.ay);
	for (int i = 0; i < NSEC; i++) {
		Ypd[i] = (Ypr[i] + Ydr[i]) / 2.;
	}
	uso_optimo_factores_F(Fr, parametros.beta, pf, py, Ypd);
	if (op.FF_ENDOGENA) {
		aportacion_factores_FF(FFr, datos.FF0, Fr);
		if (op.ALP_FACTOR > 0.) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					exceso = FFr[i][j] - datos.FF0[i][j];
					Alpr[i][j] = exceso * op.ALP_FACTOR;
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
	ahorro_hogares_Sp(Spr, parametros.ssp, pf, FFr, datos.PssH0);
	Tir = impuestos_directos_Ti(parametros.tai, pf, FFr, op.INDICE_F_TRA);
	ayudas_AgE_AgH(AgEr, AgHr, parametros.cage, parametros.cagh, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssEr, parametros.ctzsse, pf, Fr, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssHr, parametros.ctzssh, pf, FFr, Alpr, op.INDICE_F_TRA);
	Sgr = gobierno_Sg_Xg(Xgr, parametros.ssg, parametros.mu, pq, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, AgEr, AgHr, datos.PssH0, CssHr, CssEr);
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
	demanda_inversion_Xv(Xvr, parametros.landa, pq, Spr, Sgr, Scr, epsilon, Sfr, Tir, datos.Te0);
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
		// trata de que 'ebpr' sea igual a 'ebp' y a cero
		dd = abs(ebp) + abs(ebpr);
	}
	else {
		dd = Sfr - Sf;
	}
	dist += dd * dd;

	// se calcula solo para los valores del segundo pase
	/*
	for (int i = 0; i < NSEC; i++) {
		sum_Xp = 0.;
		for (int j = 0; j < NDEM; j++) {
			sum_Xp += Xp[j][i];
		}
		sum_X = 0.;
		for (int j = 0; j < NSEC; j++) {
			sum_X += X[j][i];
		}
		dd = Q[i] - (sum_Xp + Xg[i] + Xv[i] + sum_X);
		dist += dd * dd;
	}
	*/
	for (int i = 0; i < NSEC; i++) {
		sum_Xp = 0.;
		for (int j = 0; j < NDEM; j++) {
			sum_Xp += Xpr[j][i];
		}
		sum_X = 0.;
		for (int j = 0; j < NSEC; j++) {
			sum_X += Xr[j][i];
		}
		dd = Qr[i] - (sum_Xp + Xgr[i] + Xvr[i] + sum_X);
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
		// se calcula solo para los valores del segundo pase
		/*
		for (int i = 0; i < NFAC; i++) {
			suma_F = 0.;
			for (int j = 0; j < NSEC; j++) {
				suma_F += abs(F[j][i]);
			}
			suma_FF = 0.;
			for (int j = 0; j < NDEM; j++) {
				suma_FF += abs(FF[j][i]);
			}
			dd = suma_F - suma_FF;
			dist += dd * dd;
		}
		*/
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
#ifdef USAR_PESO_YDP
		dd = (Ydr[i] - Ypr[i]) * PESO_YDP;
#else
		dd = Ydr[i] - Ypr[i];
#endif
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
	dd = Tir - Ti;
	dist += dd * dd;
	if (op.OPT_DESVIOS == 0) {
		for (int i = 0; i < NSEC; i++) {
			dd = Ypr[i] - Yp[i];
			dist += dd * dd;
			dd = Ydr[i] - Yd[i];
			dist += dd * dd;
			dd = Dar[i] - Da[i];
			dist += dd * dd;
			dd = Dtr[i] - Dt[i];
			dist += dd * dd;
		}
	}

	// vector solución recalculado + distancia
	int nv = 0;
	vec_opt_nuevo[nv++] = pf[0];
	for (int i = 0; i < len_var[1]; i++) vec_opt_nuevo[nv++] = py[i];
	for (int i = 0; i < len_var[2]; i++) vec_opt_nuevo[nv++] = pq[i];
	for (int i = 0; i < len_var[3]; i++) vec_opt_nuevo[nv++] = pd[i];
	vec_opt_nuevo[nv++] = epsilon;
	vec_opt_nuevo[nv++] = Apz;
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			vec_opt_nuevo[nv++] = Fr[i][j];
		}
	}
	for (int i = 0; i < len_var[7]; i++) vec_opt_nuevo[nv++] = Er[i];
	for (int i = 0; i < len_var[8]; i++) vec_opt_nuevo[nv++] = Mr[i];
	for (int i = 0; i < len_var[9]; i++) vec_opt_nuevo[nv++] = (Dar[i] + Dtr[i]) / 2.;
	if (op.GE_INCLUYE_XP) {
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NSEC; j++) {
				Xpi[i][j] = vec_opt[n++];
				vec_opt_nuevo[nv++] = Xpr[i][j];
			}
		}
	}
	vec_opt_nuevo[nv] = dist;

	return dist;
}
#endif
#ifdef FIN_MERITO_ANTICIPADO
double merito_d(double* vec_opt, double liston) {
	// la función se termina cuando la desviación supera un cierto liston, no ahorra ningún tiempo

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
#ifdef CONSUMO_INTERMEDIO_INDESADO
	double X[NSEC][NSEC]{};	// es necesario inicializar a cero cuando se usa CONSUMO_INTERMEDIO_INDESADO
#else
	double X[NSEC][NSEC];
#endif
	double Yd[NSEC];
	double Ypd[NSEC];
	double pz[NSEC];
	double FF[NDEM][NFAC];
	double Alp[NDEM][NFAC];
	double Td[NDEM];
	double Tz[NSEC];
	double Tm[NSEC];
	double Ti;
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
	double Xr[NSEC][NSEC]{};	// es necesario inicializar a cero cuando se usa CONSUMO_INTERMEDIO_INDESADO
	double Ydr[NSEC];
	double FFr[NDEM][NFAC];
	double Alpr[NDEM][NFAC];
	double Tdr[NDEM];
	double Tzr[NSEC];
	double Tmr[NSEC];
	double Tir;
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

	double exceso;
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
					exceso = FF[i][j] - datos.FF0[i][j];
					Alp[i][j] = exceso * op.ALP_FACTOR;
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
	ahorro_hogares_Sp(Sp, parametros.ssp, pf, FF, datos.PssH0);
	Ti = impuestos_directos_Ti(parametros.tai, pf, FF, op.INDICE_F_TRA);
	ayudas_AgE_AgH(AgE, AgH, parametros.cage, parametros.cagh, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssE, parametros.ctzsse, pf, F, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssH, parametros.ctzssh, pf, FF, Alp, op.INDICE_F_TRA);
	Sg = gobierno_Sg_Xg(Xg, parametros.ssg, parametros.mu, pq, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AgE, AgH, datos.PssH0, CssH, CssE);
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
	demanda_inversion_Xv(Xv, parametros.landa, pq, Sp, Sg, Sc, epsilon, Sf, Ti, datos.Te0);
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
	double dd;
	double dist = 0.;
	restriccion_produccion_bruta_Z(Zr, parametros.teta, parametros.xie, parametros.xid, E, Dt, parametros.phi);
	for (int i = 0; i < NSEC; i++) {
		dd = Zr[i] - Z[i];
		dist += dd * dd;
	}
	if (dist > liston) return dist;
	produccion_factor_compuesto_Y(Ypr, F, parametros.beta, parametros.b);
	utilizacion_factor_compuesto_Y(Ydr, Zr, parametros.ay);
	for (int i = 0; i < NSEC; i++) {
#ifdef USAR_PESO_YDP
		dd = (Ydr[i] - Ypr[i]) * PESO_YDP;
#else
		dd = Ydr[i] - Ypr[i];
#endif
		dist += dd * dd;
	}
	if (dist > liston) return dist;
	for (int i = 0; i < NSEC; i++) {
		Ypd[i] = (Ypr[i] + Ydr[i]) / 2.;
	}
	uso_optimo_factores_F(Fr, parametros.beta, pf, py, Ypd);
	if (op.FF_ENDOGENA) {
		aportacion_factores_FF(FFr, datos.FF0, Fr);
		if (op.ALP_FACTOR > 0) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					exceso = FFr[i][j] - datos.FF0[i][j];
					Alpr[i][j] = exceso * op.ALP_FACTOR;
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
	for (int i = 0; i < NDEM; i++) {
		for (int j = 0; j < NFAC; j++) {
			dd = FFr[i][j] - FF[i][j];
			dist += dd * dd;
		}
	}
	if (dist > liston) return dist;
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			dd = Fr[i][j] - Fi[i][j];
			dist += dd * dd;
			dd = Fr[i][j] - F[i][j];
			dist += dd * dd;
		}
	}
	if (dist > liston) return dist;
	consumo_intermedio_X(Xr, Zr, parametros.ax);
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NSEC; j++) {
			dd = Xr[i][j] - X[i][j];
			dist += dd * dd;
		}
	}
	if (dist > liston) return dist;
	produccion_armington_Q(Qr, parametros.gamma, parametros.deltam, parametros.deltad, M, Dt, parametros.eta);
	for (int i = 0; i < NSEC; i++) {
		dd = Qr[i] - Q[i];
		dist += dd * dd;
	}
	if (dist > liston) return dist;
	impuestos_directos_Td(Tdr, parametros.taud, pf, FFr, Alpr, datos.PssH0);
	for (int i = 0; i < NDEM; i++) {
		dd = Tdr[i] - Td[i];
		dist += dd * dd;
	}
	if (dist > liston) return dist;
	impuestos_produccion_Tz(Tzr, datos.tauz, pz, Zr);
	for (int i = 0; i < NSEC; i++) {
		dd = Tzr[i] - Tz[i];
		dist += dd * dd;
	}
	if (dist > liston) return dist;
	aranceles_importacion_Tm(Tmr, datos.taum, pm, M);
	for (int i = 0; i < NSEC; i++) {
		dd = Tmr[i] - Tm[i];
		dist += dd * dd;
	}
	if (dist > liston) return dist;
	ahorro_hogares_Sp(Spr, parametros.ssp, pf, FFr, datos.PssH0);
	for (int i = 0; i < NDEM; i++) {
		dd = Spr[i] - Sp[i];
		dist += dd * dd;
	}
	if (dist > liston) return dist;
	Tir = impuestos_directos_Ti(parametros.tai, pf, FFr, op.INDICE_F_TRA);
	dd = Tir - Ti;
	dist += dd * dd;
	if (dist > liston) return dist;
	ayudas_AgE_AgH(AgEr, AgHr, parametros.cage, parametros.cagh, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, AYD_ADI_DEM);
	for (int i = 0; i < NSEC; i++) {
		dd = AgEr[i] - AgE[i];
		dist += dd * dd;
	}
	if (dist > liston) return dist;
	for (int i = 0; i < NDEM; i++) {
		dd = AgHr[i] - AgH[i];
		dist += dd * dd;
	}
	if (dist > liston) return dist;
	seguridad_social_empresas_CssE(CssEr, parametros.ctzsse, pf, Fr, op.INDICE_F_TRA);
	for (int i = 0; i < NSEC; i++) {
		dd = CssEr[i] - CssE[i];
		dist += dd * dd;
	}
	if (dist > liston) return dist;
	seguridad_social_hogares_CssH(CssHr, parametros.ctzssh, pf, FFr, Alpr, op.INDICE_F_TRA);
	for (int i = 0; i < NDEM; i++) {
		dd = CssHr[i] - CssH[i];
		dist += dd * dd;
	}
	if (dist > liston) return dist;
	Sgr = gobierno_Sg_Xg(Xgr, parametros.ssg, parametros.mu, pq, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, AgEr, AgHr, datos.PssH0, CssHr, CssEr);
	for (int i = 0; i < NSEC; i++) {
		dd = Xgr[i] - Xg[i];
		dist += dd * dd;
	}
	if (dist > liston) return dist;
	dd = Sgr - Sg;
	dist += dd * dd;
	if (dist > liston) return dist;
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
	demanda_inversion_Xv(Xvr, parametros.landa, pq, Spr, Sgr, Scr, epsilon, Sfr, Tir, datos.Te0);
	for (int i = 0; i < NSEC; i++) {
		dd = Xvr[i] - Xv[i];
		dist += dd * dd;
	}
	if (dist > liston) return dist;
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
	for (int i = 0; i < NDEM; i++) {
		for (int j = 0; j < NSEC; j++) {
			dd = Xpr[i][j] - Xp[i][j];
			dist += dd * dd;
		}
	}
	if (dist > liston) return dist;
	if (op.GE_INCLUYE_XP) {
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NSEC; j++) {
				dd = Xp[i][j] - Xpi[i][j];
				dist += dd * dd;
			}
		}
	}
	if (dist > liston) return dist;
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
	if (dist > liston) return dist;
	importacion_maxima_utilidad_armington_M(Mr, parametros.gamma, parametros.deltam, pq, pm, Qr, parametros.eta, datos.taum);
	for (int i = 0; i < NSEC; i++) {
		dd = Mr[i] - Mi[i];
		dist += dd * dd;
		dd = Mr[i] - M[i];
		dist += dd * dd;
	}
	if (dist > liston) return dist;
	produccion_maxima_utilidad_armington_D(Dar, parametros.gamma, parametros.deltad, pq, pd, Qr, parametros.eta);
	for (int i = 0; i < NSEC; i++) {
		dd = Dar[i] - Di[i];
		dist += dd * dd;
	}
	if (dist > liston) return dist;
	produccion_para_exportacion_E(Er, parametros.teta, parametros.xie, pz, pe, Zr, parametros.phi, datos.tauz, CssEr, AgEr, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	for (int i = 0; i < NSEC; i++) {
		dd = Er[i] - Ei[i];
		dist += dd * dd;
		dd = Er[i] - E[i];
		dist += dd * dd;
	}
	if (dist > liston) return dist;
	produccion_para_local_D(Dtr, parametros.teta, parametros.xid, pz, pd, Zr, parametros.phi, datos.tauz, CssEr, AgEr, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	for (int i = 0; i < NSEC; i++) {
		dd = Dar[i] - Dtr[i];
		dist += dd * dd;
	}
	if (dist > liston) return dist;
	if (op.EQ_BAL_PAGOS) {
		ebpr = equilibrio_balance_pagos_moneda_extranjera(datos.pWe, Er, datos.pWm, Mr, Sfr);
	}
	else {
		ebpr = 0.;
	}
	if (op.EQ_BAL_PAGOS) {
		// trata de que 'ebpr' sea igual a 'ebp' y a cero
		dd = abs(ebp) + abs(ebpr);
	}
	else {
		dd = Sfr - Sf;
	}
	dist += dd * dd;
	if (op.OPT_DESVIOS == 0) {
		for (int i = 0; i < NSEC; i++) {
			dd = Ypr[i] - Yp[i];
			dist += dd * dd;
			dd = Ydr[i] - Yd[i];
			dist += dd * dd;
			dd = Dar[i] - Da[i];
			dist += dd * dd;
			dd = Dtr[i] - Dt[i];
			dist += dd * dd;
		}
	}
	return dist;
}
#endif
/*
prepara los vectores 'me_sol' y 'VEC_OPT_E' con todas las variables del modelo, o solo las variables de la solución. Al
ser estas variables globales quedan en memoria a disposición de cualquier otra función, como 'soluciona', para
devolverlas a quien llame a la DLL.
no es multiproceso, porque 'me_sol' y 'VEC_OPT_E' son variables globales, pero es segura porque está pensada para ser llamada
una vez que los hilos que calculan los cruces y selección han completado una generación y están es espera.
*/
double* merito_sol(double* vec_opt) {
	double pf[NFAC];
	double py[NSEC];
	double pq[NSEC];
	double pd[NSEC];
	double Fi[NSEC][NFAC];
	double Ei[NSEC];
	double Mi[NSEC];
	double Di[NSEC];
	double Xpi[NDEM][NSEC];

	double pe[NSEC];
	double pm[NSEC];
	double pz[NSEC];
	double F[NSEC][NFAC];
	double E[NSEC];
	double M[NSEC];
	double Da[NSEC];
	double Dt[NSEC];
	double Yp[NSEC];
	double Yd[NSEC];
	double Ypd[NSEC];		// no es una variable del modelo, es la media de Yp y Yd, para el cálculo de la optimización de los factores
	double Z[NSEC];
#ifdef CONSUMO_INTERMEDIO_INDESADO
	double X[NSEC][NSEC]{};	// es necesario inicializar a cero cuando se usa CONSUMO_INTERMEDIO_INDESADO
#else
	double X[NSEC][NSEC];
#endif
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
	double Xr[NSEC][NSEC]{};	// es necesario inicializar a cero cuando se usa CONSUMO_INTERMEDIO_INDESADO
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

	double Ti;
	double Sg;
	double Sc;
	double Sf;
	double ebp;

	double Tir;
	double Sgr;
	double Scr;
	double Sfr;
	double ebpr;

	double exceso;
	double suma_F;
	double suma_FF;
	double sum_Xp;
	double sum_X;

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
					exceso = FF[i][j] - datos.FF0[i][j];
					Alp[i][j] = exceso * op.ALP_FACTOR;
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
	ahorro_hogares_Sp(Sp, parametros.ssp, pf, FF, datos.PssH0);
	Ti = impuestos_directos_Ti(parametros.tai, pf, FF, op.INDICE_F_TRA);
	ayudas_AgE_AgH(AgE, AgH, parametros.cage, parametros.cagh, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssE, parametros.ctzsse, pf, F, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssH, parametros.ctzssh, pf, FF, Alp, op.INDICE_F_TRA);
	Sg = gobierno_Sg_Xg(Xg, parametros.ssg, parametros.mu, pq, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AgE, AgH, datos.PssH0, CssH, CssE);
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
	demanda_inversion_Xv(Xv, parametros.landa, pq, Sp, Sg, Sc, epsilon, Sf, Ti, datos.Te0);
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
	produccion_factor_compuesto_Y(Ypr, F, parametros.beta, parametros.b);
	restriccion_produccion_bruta_Z(Zr, parametros.teta, parametros.xie, parametros.xid, E, Dt, parametros.phi);
	consumo_intermedio_X(Xr, Zr, parametros.ax);
	utilizacion_factor_compuesto_Y(Ydr, Zr, parametros.ay);
	for (int i = 0; i < NSEC; i++) {
		Ypd[i] = (Ypr[i] + Ydr[i]) / 2.;
	}
	uso_optimo_factores_F(Fr, parametros.beta, pf, py, Ypd);
	if (op.FF_ENDOGENA) {
		aportacion_factores_FF(FFr, datos.FF0, Fr);
		if (op.ALP_FACTOR > 0) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					exceso = FFr[i][j] - datos.FF0[i][j];
					Alpr[i][j] = exceso * op.ALP_FACTOR;
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
	ahorro_hogares_Sp(Spr, parametros.ssp, pf, FFr, datos.PssH0);
	Tir = impuestos_directos_Ti(parametros.tai, pf, FFr, op.INDICE_F_TRA);
	ayudas_AgE_AgH(AgEr, AgHr, parametros.cage, parametros.cagh, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssEr, parametros.ctzsse, pf, Fr, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssHr, parametros.ctzssh, pf, FFr, Alpr, op.INDICE_F_TRA);
	Sgr = gobierno_Sg_Xg(Xgr, parametros.ssg, parametros.mu, pq, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, AgEr, AgHr, datos.PssH0, CssHr, CssEr);
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
	demanda_inversion_Xv(Xvr, parametros.landa, pq, Spr, Sgr, Scr, epsilon, Sfr, Tir, datos.Te0);
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

	// cálculo de desvios
	double dd;
	double dist = 0.;
	double dist_max = -1.;
	int ndv = 0;
	int ndm = 0;
	int idm = -1;
	int pdm = -1;
	int ddm = -1;

	// ebp
	if (op.EQ_BAL_PAGOS) {
		// trata de que 'ebpr' sea igual a 'ebp' y a cero
		dd = abs(ebp) + abs(ebpr);
	}
	else {
		dd = abs(Sfr - Sf);
	}
	if (dd > dist_max) {
		dist_max = dd;
		idm = ndm;
		pdm = 0;
		ddm = 0;
	};
	ndm++;
	dist += dd * dd;
	desvios_bloque[ndv++] = dist;
	// Q eq
	// se calcula solo para los valores del segundo pase
	/*
	for (int i = 0; i < NSEC; i++) {
		sum_Xp = 0.;
		for (int j = 0; j < NDEM; j++) {
			sum_Xp += Xp[j][i];
		}
		sum_X = 0.;
		for (int j = 0; j < NSEC; j++) {
			sum_X += X[j][i];
		}
		dd = abs(Q[i] - (sum_Xp + Xg[i] + Xv[i] + sum_X));
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 1;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	*/
	for (int i = 0; i < NSEC; i++) {
		sum_Xp = 0.;
		for (int j = 0; j < NDEM; j++) {
			sum_Xp += Xpr[j][i];
		}
		sum_X = 0.;
		for (int j = 0; j < NSEC; j++) {
			sum_X += Xr[j][i];
		}
		dd = abs(Qr[i] - (sum_Xp + Xgr[i] + Xvr[i] + sum_X));
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 1;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}

	desvios_bloque[ndv++] = dist;
	if (op.FF_ENDOGENA) {
		// desvio en factores
		ndm += NFAC;
		desvios_bloque[ndv++] = dist;
		// desvios Alp
		if (op.ALP_FACTOR > 0) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					dd = abs(Alpr[i][j] - Alp[i][j]);
					if (dd > dist_max) {
						dist_max = dd;
						idm = ndm;
						pdm = 3;
						ddm = i * NFAC + j;
					};
					ndm++;
					dist += dd * dd;
				}
			}
		}
		else {
			ndm += NDEM * NFAC;
		}
		desvios_bloque[ndv++] = dist;
	}
	else {
		// desvio en factores
		// se calcula solo para los valores del segundo pase
		/*
		for (int i = 0; i < NFAC; i++) {
			suma_F = 0.;
			for (int j = 0; j < NSEC; j++) {
				suma_F += abs(F[j][i]);
			}
			suma_FF = 0.;
			for (int j = 0; j < NDEM; j++) {
				suma_FF += abs(FF[j][i]);
			}
			dd = abs(suma_F - suma_FF);
			if (dd > dist_max) {
				dist_max = dd;
				idm = ndm;
				pdm = 2;
				ddm = i;
			};
			ndm++;
			dist += dd * dd;
		}
		*/
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
			if (dd > dist_max) {
				dist_max = dd;
				idm = ndm;
				pdm = 2;
				ddm = i;
			};
			ndm++;
			dist += dd * dd;
		}
		desvios_bloque[ndv++] = dist;

		// desvios Alp
		ndm += NDEM * NFAC;
		desvios_bloque[ndv++] = dist;
	}
	// Sg
	dd = abs(Sgr - Sg);
	if (dd > dist_max) {
		dist_max = dd;
		idm = ndm;
		pdm = 4;
		ddm = 0;
	};
	ndm++;
	dist += dd * dd;
	desvios_bloque[ndv++] = dist;
	// Sp
	for (int i = 0; i < NDEM; i++) {
		dd = abs(Spr[i] - Sp[i]);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 5;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// vacante
	ndm++;
	desvios_bloque[ndv++] = dist;
	// Agh
	for (int i = 0; i < NDEM; i++) {
		dd = abs(AgHr[i] - AgH[i]);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 7;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// CssH
	for (int i = 0; i < NDEM; i++) {
		dd = abs(CssHr[i] - CssH[i]);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 8;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// Td
	for (int i = 0; i < NDEM; i++) {
		dd = abs(Tdr[i] - Td[i]);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 9;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// FF
	for (int i = 0; i < NDEM; i++) {
		for (int j = 0; j < NFAC; j++) {
			dd = abs(FFr[i][j] - FF[i][j]);
			if (dd > dist_max) {
				dist_max = dd;
				idm = ndm;
				pdm = 10;
				ddm = i * NFAC + j;
			};
			ndm++;
			dist += dd * dd;
		}
	}
	desvios_bloque[ndv++] = dist;
	// Xpi
	if (op.GE_INCLUYE_XP) {
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NSEC; j++) {
				dd = abs(Xpr[i][j] - Xpi[i][j]);
				if (dd > dist_max) {
					dist_max = dd;
					idm = ndm;
					pdm = 11;
					ddm = i * NSEC + j;
				};
				ndm++;
				dist += dd * dd;
			}
		}
	}
	else {
		ndm += NDEM * NSEC;
	}
	desvios_bloque[ndv++] = dist;
	// Xp
	for (int i = 0; i < NDEM; i++) {
		for (int j = 0; j < NSEC; j++) {
			dd = abs(Xpr[i][j] - Xp[i][j]);
			if (dd > dist_max) {
				dist_max = dd;
				idm = ndm;
				pdm = 12;
				ddm = i * NSEC + j;
			};
			ndm++;
			dist += dd * dd;
		}
	}
	desvios_bloque[ndv++] = dist;
	// Ei
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Er[i] - Ei[i]);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 13;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// Mi
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Mr[i] - Mi[i]);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 14;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// Dai
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Dar[i] - Di[i]);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 15;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// E
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Er[i] - E[i]);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 16;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// M
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Mr[i] - M[i]);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 17;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// Ydp
	for (int i = 0; i < NSEC; i++) {
#ifdef USAR_PESO_YDP
		dd = abs(Ydr[i] - Ypr[i]) * PESO_YDP;
#else
		dd = abs(Ydr[i] - Ypr[i]);
#endif
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 18;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// Dat
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Dar[i] - Dtr[i]);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 19;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// Z
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Zr[i] - Z[i]);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 20;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// Xg
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Xgr[i] - Xg[i]);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 21;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// Xv
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Xvr[i] - Xv[i]);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 22;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// Q
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Qr[i] - Q[i]);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 23;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// Tz
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Tzr[i] - Tz[i]);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 24;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// Tm
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Tmr[i] - Tm[i]);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 25;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// Age
	for (int i = 0; i < NSEC; i++) {
		dd = abs(AgEr[i] - AgE[i]);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 26;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// CssE
	for (int i = 0; i < NSEC; i++) {
		dd = abs(CssEr[i] - CssE[i]);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 27;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios_bloque[ndv++] = dist;
	// Fi
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			dd = abs(Fr[i][j] - Fi[i][j]);
			if (dd > dist_max) {
				dist_max = dd;
				idm = ndm;
				pdm = 28;
				ddm = i * NFAC + j;
			};
			ndm++;
			dist += dd * dd;
		}
	}
	desvios_bloque[ndv++] = dist;
	// F
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			dd = abs(Fr[i][j] - F[i][j]);
			if (dd > dist_max) {
				dist_max = dd;
				idm = ndm;
				pdm = 29;
				ddm = i * NFAC + j;
			};
			ndm++;
			dist += dd * dd;
		}
	}
	desvios_bloque[ndv++] = dist;
	// X
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NSEC; j++) {
			dd = abs(Xr[i][j] - X[i][j]);
			if (dd > dist_max) {
				dist_max = dd;
				idm = ndm;
				pdm = 30;
				ddm = i * NSEC + j;
			};
			ndm++;
			dist += dd * dd;
		}
	}
	desvios_bloque[ndv++] = dist;
	// Ti
	dd = abs(Tir - Ti);
	if (dd > dist_max) {
		dist_max = dd;
		idm = ndm;
		pdm = 31;
		ddm = 0;
	};
	ndm++;
	dist += dd * dd;
	desvios_bloque[ndv++] = dist;
	if (op.OPT_DESVIOS == 0) {
		// Yp
		for (int i = 0; i < NSEC; i++) {
			dd = abs(Ypr[i] - Yp[i]);
			if (dd > dist_max) {
				dist_max = dd;
				idm = ndm;
				pdm = 32;
				ddm = i;
			};
			ndm++;
			dist += dd * dd;
		}
		desvios_bloque[ndv++] = dist;
		// Yd
		for (int i = 0; i < NSEC; i++) {
			dd = abs(Ydr[i] - Yd[i]);
			if (dd > dist_max) {
				dist_max = dd;
				idm = ndm;
				pdm = 33;
				ddm = i;
			};
			ndm++;
			dist += dd * dd;
		}
		desvios_bloque[ndv++] = dist;
		// Da
		for (int i = 0; i < NSEC; i++) {
			dd = abs(Dar[i] - Da[i]);
			if (dd > dist_max) {
				dist_max = dd;
				idm = ndm;
				pdm = 34;
				ddm = i;
			};
			ndm++;
			dist += dd * dd;
		}
		desvios_bloque[ndv++] = dist;
		// Dt
		for (int i = 0; i < NSEC; i++) {
			dd = abs(Dtr[i] - Dt[i]);
			if (dd > dist_max) {
				dist_max = dd;
				idm = ndm;
				pdm = 35;
				ddm = i;
			};
			ndm++;
			dist += dd * dd;
		}
		desvios_bloque[ndv++] = dist;
	}
	puntero_bloque_desviacion = pdm;
	desplazamiento_desviacion = ddm;
	// hay una posición de desvío que está vacante
	N_DESVIACIONES = ndm - 1;
	if (op.GE_INCLUYE_XP == false) {
		N_DESVIACIONES -= NDEM * NSEC;
	}
	if (op.FF_ENDOGENA) {
		N_DESVIACIONES -= NFAC;
	}
	if (op.FF_ENDOGENA == FALSE || op.ALP_FACTOR == 0) {
		N_DESVIACIONES -= NDEM * NFAC;
	}
#ifdef ECM
	dist = sqrt(dist / N_DESVIACIONES);
#endif

#ifdef COMPROBAR_MAX_DESVIACION
	// buscar el rótulo del bloque de máxima desviación
	puntero_bloque_desviacion = -1;
	desplazamiento_desviacion = -1;
	for (int i = 0; i < MAX_BLOQUES_DESVIOS - 1; i++) {
		if (idm >= ind_bloque_desviacion[i] && idm < ind_bloque_desviacion[i + 1]) {
			puntero_bloque_desviacion = i;
			desplazamiento_desviacion = idm - ind_bloque_desviacion[i];
			break;
		}
	}
	if (puntero_bloque_desviacion != pdm || puntero_bloque_desviacion == -1 || pdm == -1) {
		fprintf(salida, "Error: el bloque de desviación identificado %d no coincide con el bloque esperado %d.\n", puntero_bloque_desviacion, pdm);
		fflush(salida);
		puntero_bloque_desviacion = 0;
		desplazamiento_desviacion = 0;
	}
	if (desplazamiento_desviacion != ddm || desplazamiento_desviacion == -1 || ddm == -1) {
		fprintf(salida, "Error: el desplazamiento de desviación identificado %d no coincide con el desplazamiento esperado %d.\n", desplazamiento_desviacion, ddm);
		fflush(salida);
		puntero_bloque_desviacion = 0;
		desplazamiento_desviacion = 0;
	}
#endif
	// cabecera + vector solución + valores para todas las demás variables

	// cabecera
	int nsol = 0;
	me_sol[nsol++] = 0;			// resultado
	me_sol[nsol++] = 0;			// número de datos
	me_sol[nsol++] = 0;			// intentos
	me_sol[nsol++] = 0;			// generaciones
	me_sol[nsol++] = dist;		// mérito
	me_sol[nsol++] = dist_max;	// desviación máxima
	me_sol[nsol++] = idm;		// índice de desviación máxima

	// el vector solución inmediatamente después de la cabecera
	for (int i = 0; i < NFAC; i++)	me_sol[nsol++] = pf[i];	// incluye el precio de los 2 factores
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
	me_sol[nsol++] = Ti;

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
	me_sol[nsol++] = Tir;
	me_sol[1] = nsol;

	// cabecera	+ vector solucion + detalle desvios + evolución error
	nsol = 0;
	VEC_OPT_E[nsol++] = 0;			// resultado
	VEC_OPT_E[nsol++] = 0;			// número de datos
	VEC_OPT_E[nsol++] = 0;			// intentos
	VEC_OPT_E[nsol++] = 0;			// generaciones
	VEC_OPT_E[nsol++] = dist;		// mérito
	VEC_OPT_E[nsol++] = dist_max;	// desviación máxima
	VEC_OPT_E[nsol++] = idm;		// índice de desviación máxima

	VEC_OPT_E[nsol++] = pf[0];
	VEC_OPT_E[nsol++] = pf[1];

	// vector solución
	for (int i = 1; i < NVEC; i++) {
		VEC_OPT_E[nsol++] = vec_opt[i];
	}
	VEC_OPT_E[1] = nsol;

	// desglose de las desviaciones (un máximo de 64)
	VEC_OPT_E[nsol++] = ndv;
	for (int i = 0; i < ndv; i++) {
		VEC_OPT_E[nsol++] = desvios_bloque[i];
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

#ifdef DESVIACONES_RELATIVAS
double merito_s_relativa(double* vec_opt) {
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
#ifdef CONSUMO_INTERMEDIO_INDESADO
	double X[NSEC][NSEC]{};	// es necesario inicializar a cero cuando se usa CONSUMO_INTERMEDIO_INDESADO
#else
	double X[NSEC][NSEC];
#endif
	double Yd[NSEC];
	double Ypd[NSEC];
	double pz[NSEC];
	double FF[NDEM][NFAC];
	double Alp[NDEM][NFAC];
	double Td[NDEM];
	double Tz[NSEC];
	double Tm[NSEC];
	double Ti;
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
	double Xr[NSEC][NSEC]{};	// es necesario inicializar a cero cuando se usa CONSUMO_INTERMEDIO_INDESADO
	double Ydr[NSEC];
	double FFr[NDEM][NFAC];
	double Alpr[NDEM][NFAC];
	double Tdr[NDEM];
	double Tzr[NSEC];
	double Tmr[NSEC];
	double Tir[NSEC];
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

	double exceso;
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
					exceso = FF[i][j] - datos.FF0[i][j];
					Alp[i][j] = exceso * op.ALP_FACTOR;
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
	ahorro_hogares_Sp(Sp, parametros.ssp, pf, FF, datos.PssH0);
	Ti = impuestos_directos_Ti(parametros.tai, pf, FF, op.INDICE_F_TRA);
	ayudas_AgE_AgH(AgE, AgH, parametros.cage, parametros.cagh, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssE, parametros.ctzsse, pf, F, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssH, parametros.ctzssh, pf, FF, Alp, op.INDICE_F_TRA);
	Sg = gobierno_Sg_Xg(Xg, parametros.ssg, parametros.mu, pq, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AgE, AgH, datos.PssH0, CssH, CssE);
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
	demanda_inversion_Xv(Xv, parametros.landa, pq, Sp, Sg, Sc, epsilon, Sf, Ti, datos.Te0);
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
	consumo_intermedio_X(Xr, Zr, parametros.ax);
	utilizacion_factor_compuesto_Y(Ydr, Zr, parametros.ay);
	for (int i = 0; i < NSEC; i++) {
		Ypd[i] = (Ypr[i] + Ydr[i]) / 2.;
	}
	uso_optimo_factores_F(Fr, parametros.beta, pf, py, Ypd);
	if (op.FF_ENDOGENA) {
		aportacion_factores_FF(FFr, datos.FF0, Fr);
		if (op.ALP_FACTOR > 0) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					exceso = FFr[i][j] - datos.FF0[i][j];
					Alpr[i][j] = exceso * op.ALP_FACTOR;
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
	ahorro_hogares_Sp(Spr, parametros.ssp, pf, FFr, datos.PssH0);
	Tir = impuestos_directos_Ti(parametros.tai, pf, FFr, op.INDICE_F_TRA);
	ayudas_AgE_AgH(AgEr, AgHr, parametros.cage, parametros.cagh, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssEr, parametros.ctzsse, pf, Fr, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssHr, parametros.ctzssh, pf, FFr, Alpr, op.INDICE_F_TRA);
	Sgr = gobierno_Sg_Xg(Xgr, parametros.ssg, parametros.mu, pq, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, AgEr, AgHr, datos.PssH0, CssHr, CssEr);
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
	demanda_inversion_Xv(Xvr, parametros.landa, pq, Spr, Sgr, Scr, epsilon, Sfr, Tir, datos.Te0);
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
		// trata de que 'ebpr' sea igual a 'ebp' y a cero
		dd = abs(ebp) + abs(ebpr);
		dd = dd / (abs(ebp) + 0.000001);
	}
	else {
		dd = Sfr - Sf;
		dd = dd / (abs(Sfr) + 0.000001);
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
		dd = dd / (abs(Qr[i]) + 0.000001);
		dist += dd * dd;
	}
	if (op.FF_ENDOGENA) {
		if (op.ALP_FACTOR > 0) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					dd = Alpr[i][j] - Alp[i][j];
					dd = dd / (abs(Alp[i][j]) + 0.000001);
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
			dd = dd / (abs(suma_F) + 0.000001);
			dist += dd * dd;
		}
	}
	dd = Sgr - Sg;
	dd = dd / (abs(Sgr) + 0.000001);
	dist += dd * dd;
	for (int i = 0; i < NDEM; i++) {
		dd = Spr[i] - Sp[i];
		dd = dd / (abs(Spr[i]) + 0.000001);
		dist += dd * dd;
		dd = AgHr[i] - AgH[i];
		dd = dd / (abs(AgHr[i]) + 0.000001);
		dist += dd * dd;
		dd = CssHr[i] - CssH[i];
		dd = dd / (abs(CssHr[i]) + 0.000001);
		dist += dd * dd;
		dd = Tdr[i] - Td[i];
		dd = dd / (abs(Tdr[i]) + 0.000001);
		dist += dd * dd;
		for (int j = 0; j < NFAC; j++) {
			dd = FFr[i][j] - FF[i][j];
			dd = dd / (abs(FF[i][j]) + 0.000001);
			dist += dd * dd;
		}
		for (int j = 0; j < NSEC; j++) {
			if (op.GE_INCLUYE_XP) {
				dd = Xp[i][j] - Xpi[i][j];
				dd = dd / (abs(Xp[i][j]) + 0.000001);
				dist += dd * dd;
			}
			dd = Xpr[i][j] - Xp[i][j];
			dd = dd / (abs(Xp[i][j]) + 0.000001);
			dist += dd * dd;
		}
	}
	for (int i = 0; i < NSEC; i++) {
		dd = Er[i] - Ei[i];
		dd = dd / (abs(Er[i]) + 0.000001);
		dist += dd * dd;
		dd = Mr[i] - Mi[i];
		dd = dd / (abs(Mr[i]) + 0.000001);
		dist += dd * dd;
		dd = Dar[i] - Di[i];
		dd = dd / (abs(Dar[i]) + 0.000001);
		dist += dd * dd;
		dd = Er[i] - E[i];
		dd = dd / (abs(Er[i]) + 0.000001);
		dist += dd * dd;
		dd = Mr[i] - M[i];
		dd = dd / (abs(Mr[i]) + 0.000001);
		dist += dd * dd;
#ifdef USAR_PESO_YDP
		dd = (Ydr[i] - Ypr[i]) * PESO_YDP;
#else
		dd = Ydr[i] - Ypr[i];
#endif
		dd = dd / (abs(Ydr[i]) + 0.000001);
		dist += dd * dd;
		dd = Dar[i] - Dtr[i];
		dd = dd / (abs(Dar[i]) + 0.000001);
		dist += dd * dd;
		dd = Zr[i] - Z[i];
		dd = dd / (abs(Zr[i]) + 0.000001);
		dist += dd * dd;
		dd = Xgr[i] - Xg[i];
		dd = dd / (abs(Xgr[i]) + 0.000001);
		dist += dd * dd;
		dd = Xvr[i] - Xv[i];
		dd = dd / (abs(Xvr[i]) + 0.000001);
		dist += dd * dd;
		dd = Qr[i] - Q[i];
		dd = dd / (abs(Qr[i]) + 0.000001);
		dist += dd * dd;
		dd = Tzr[i] - Tz[i];
		dd = dd / (abs(Tzr[i]) + 0.000001);
		dist += dd * dd;
		dd = Tmr[i] - Tm[i];
		dd = dd / (abs(Tmr[i]) + 0.000001);
		dist += dd * dd;
		dd = AgEr[i] - AgE[i];
		dd = dd / (abs(AgEr[i]) + 0.000001);
		dist += dd * dd;
		dd = CssEr[i] - CssE[i];
		dd = dd / (abs(CssEr[i]) + 0.000001);
		dist += dd * dd;
		for (int j = 0; j < NFAC; j++) {
			dd = Fr[i][j] - Fi[i][j];
			dd = dd / (abs(Fr[i][j]) + 0.000001);
			dist += dd * dd;
			dd = Fr[i][j] - F[i][j];
			dd = dd / (abs(Fr[i][j]) + 0.000001);
			dist += dd * dd;
		}
		for (int j = 0; j < NSEC; j++) {
			dd = Xr[i][j] - X[i][j];
			dd = dd / (abs(Xr[i][j]) + 0.000001);
			dist += dd * dd;
		}
	}
	dd = Tir - Ti;
	dd = dd / (abs(Tir) + 0.000001);
	dist += dd * dd;
	if (op.OPT_DESVIOS == 0) {
		for (int i = 0; i < NSEC; i++) {
			dd = Ypr[i] - Yp[i];
			dist += dd * dd;
			dd = Ydr[i] - Yd[i];
			dist += dd * dd;
			dd = Dar[i] - Da[i];
			dist += dd * dd;
			dd = Dtr[i] - Dt[i];
			dist += dd * dd;
		}
	}
	return dist;
}

double* merito_sol_relativa(double* vec_opt) {
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
	double Ypd[NSEC];

	double F[NSEC][NFAC];
	double E[NSEC];
	double M[NSEC];
	double Da[NSEC];
	double Dt[NSEC];
	double Yp[NSEC];
	double Yd[NSEC];
	double Z[NSEC];
#ifdef CONSUMO_INTERMEDIO_INDESADO
	double X[NSEC][NSEC]{};	// es necesario inicializar a cero cuando se usa CONSUMO_INTERMEDIO_INDESADO
#else
	double X[NSEC][NSEC];
#endif
	double FF[NDEM][NFAC];
	double Alp[NDEM][NFAC];
	double Td[NDEM];
	double Tz[NSEC];
	double Tm[NSEC];
	double Ti;
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
	double Xr[NSEC][NSEC]{};	// es necesario inicializar a cero cuando se usa CONSUMO_INTERMEDIO_INDESADO
	double FFr[NDEM][NFAC];
	double Alpr[NDEM][NFAC];
	double Tdr[NDEM];
	double Tzr[NSEC];
	double Tmr[NSEC];
	double Tir;
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

	double exceso;
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
					exceso = FF[i][j] - datos.FF0[i][j];
					Alp[i][j] = exceso * op.ALP_FACTOR;
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
	ahorro_hogares_Sp(Sp, parametros.ssp, pf, FF, datos.PssH0);
	Ti = impuestos_directos_Ti(parametros.tai, pf, FF, op.INDICE_F_TRA);
	ayudas_AgE_AgH(AgE, AgH, parametros.cage, parametros.cagh, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssE, parametros.ctzsse, pf, F, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssH, parametros.ctzssh, pf, FF, Alp, op.INDICE_F_TRA);
	Sg = gobierno_Sg_Xg(Xg, parametros.ssg, parametros.mu, pq, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AgE, AgH, datos.PssH0, CssH, CssE);
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
	demanda_inversion_Xv(Xv, parametros.landa, pq, Sp, Sg, Sc, epsilon, Sf, Ti, datos.Te0);
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
	consumo_intermedio_X(Xr, Zr, parametros.ax);
	utilizacion_factor_compuesto_Y(Ydr, Zr, parametros.ay);
	for (int i = 0; i < NSEC; i++) {
		Ypd[i] = (Ypr[i] + Ydr[i]) / 2.;
	}
	uso_optimo_factores_F(Fr, parametros.beta, pf, py, Ypd);
	if (op.FF_ENDOGENA) {
		aportacion_factores_FF(FFr, datos.FF0, Fr);
		if (op.ALP_FACTOR > 0) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					exceso = FFr[i][j] - datos.FF0[i][j];
					Alpr[i][j] = exceso * op.ALP_FACTOR;
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
	ahorro_hogares_Sp(Spr, parametros.ssp, pf, FFr, datos.PssH0);
	Tir = impuestos_directos_Ti(parametros.tai, pf, FFr, op.INDICE_F_TRA);
	ayudas_AgE_AgH(AgEr, AgHr, parametros.cage, parametros.cagh, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssEr, parametros.ctzsse, pf, Fr, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssHr, parametros.ctzssh, pf, FFr, Alpr, op.INDICE_F_TRA);
	Sgr = gobierno_Sg_Xg(Xgr, parametros.ssg, parametros.mu, pq, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, AgEr, AgHr, datos.PssH0, CssHr, CssEr);
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
	demanda_inversion_Xv(Xvr, parametros.landa, pq, Spr, Sgr, Scr, epsilon, Sfr, Tir, datos.Te0);
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

	// cálculo de desviaciones
	double dd;
	double dist = 0.;
	double dist_max = -1.;
	int ndv = 0;
	int ndm = 0;
	int idm = -1;
	int pdm = -1;
	int ddm = -1;

	// ebp
	if (op.EQ_BAL_PAGOS) {
		// trata de que 'ebpr' sea igual a 'ebp' y a cero
		dd = abs(ebp) + abs(ebpr);
		dd = dd / (abs(ebp) + 0.000001);
	}
	else {
		dd = abs(Sfr - Sf);
		dd = dd / (abs(Sfr) + 0.000001);
	}
	if (dd > dist_max) {
		dist_max = dd;
		idm = ndm;
		pdm = 0;
		ddm = 0;
	};
	ndm++;
	dist += dd * dd;
	desvios[ndv++] = dist;
	// Q eq
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
		dd = dd / (abs(Qr[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 1;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	if (op.FF_ENDOGENA) {
		// desvio en factores
		ndm += NFAC;
		desvios[ndv++] = dist;

		// desvios Alp
		if (op.ALP_FACTOR > 0) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					dd = abs(Alpr[i][j] - Alp[i][j]);
					dd = dd / (abs(Alp[i][j]) + 0.000001);
					if (dd > dist_max) {
						dist_max = dd;
						idm = ndm;
						pdm = 3;
						ddm = i * NFAC + j;
					};
					ndm++;
					dist += dd * dd;
				}
			}
		}
		else {
			ndm += NDEM * NFAC;
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
			dd = dd / (abs(suma_F) + 0.000001);
			if (dd > dist_max) {
				dist_max = dd;
				idm = ndm;
				pdm = 2;
				ddm = i;
			};
			ndm++;
			dist += dd * dd;
		}
		desvios[ndv++] = dist;

		// desvios Alp
		ndm += NDEM * NFAC;
		desvios[ndv++] = dist;
	}
	// Sg
	dd = abs(Sgr - Sg);
	dd = dd / (abs(Sg) + 0.000001);
	if (dd > dist_max) {
		dist_max = dd;
		idm = ndm;
		pdm = 4;
		ddm = 0;
	};
	ndm++;
	dist += dd * dd;
	desvios[ndv++] = dist;
	// Sp
	for (int i = 0; i < NDEM; i++) {
		dd = abs(Spr[i] - Sp[i]);
		dd = dd / (abs(Sp[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 5;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// vacante
	ndm++;
	desvios[ndv++] = dist;
	// Agh
	for (int i = 0; i < NDEM; i++) {
		dd = abs(AgHr[i] - AgH[i]);
		dd = dd / (abs(AgH[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 7;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// CssH
	for (int i = 0; i < NDEM; i++) {
		dd = abs(CssHr[i] - CssH[i]);
		dd = dd / (abs(CssH[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 8;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// Td
	for (int i = 0; i < NDEM; i++) {
		dd = abs(Tdr[i] - Td[i]);
		dd = dd / (abs(Td[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 9;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// FF
	for (int i = 0; i < NDEM; i++) {
		for (int j = 0; j < NFAC; j++) {
			dd = abs(FFr[i][j] - FF[i][j]);
			dd = dd / (abs(FF[i][j]) + 0.000001);
			if (dd > dist_max) {
				dist_max = dd;
				idm = ndm;
				pdm = 10;
				ddm = i * NFAC + j;
			};
			ndm++;
			dist += dd * dd;
		}
	}
	desvios[ndv++] = dist;
	// Xpi
	if (op.GE_INCLUYE_XP) {
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NSEC; j++) {
				dd = abs(Xpr[i][j] - Xpi[i][j]);
				dd = dd / (abs(Xpi[i][j]) + 0.000001);
				if (dd > dist_max) {
					dist_max = dd;
					idm = ndm;
					pdm = 11;
					ddm = i * NSEC + j;
				};
				ndm++;
				dist += dd * dd;
			}
		}
	}
	else {
		ndm += NDEM * NSEC;
	}
	desvios[ndv++] = dist;
	// Xp
	for (int i = 0; i < NDEM; i++) {
		for (int j = 0; j < NSEC; j++) {
			dd = abs(Xpr[i][j] - Xp[i][j]);
			dd = dd / (abs(Xp[i][j]) + 0.000001);
			if (dd > dist_max) {
				dist_max = dd;
				idm = ndm;
				pdm = 12;
				ddm = i * NSEC + j;
			};
			ndm++;
			dist += dd * dd;
		}
	}
	desvios[ndv++] = dist;
	// Ei
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Er[i] - Ei[i]);
		dd = dd / (abs(Ei[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 13;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// Mi
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Mr[i] - Mi[i]);
		dd = dd / (abs(Mi[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 14;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// Dai
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Dar[i] - Di[i]);
		dd = dd / (abs(Di[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 15;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// E
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Er[i] - E[i]);
		dd = dd / (abs(E[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 16;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// M
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Mr[i] - M[i]);
		dd = dd / (abs(M[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 17;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// Ydp
	for (int i = 0; i < NSEC; i++) {
#ifdef USAR_PESO_YDP
		dd = abs(Ydr[i] - Ypr[i]) * PESO_YDP;
#else
		dd = abs(Ydr[i] - Ypr[i]);
#endif
		dd = dd / (abs(Ypr[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 18;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// Dat
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Dar[i] - Dtr[i]);
		dd = dd / (abs(Dtr[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 19;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// Z
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Zr[i] - Z[i]);
		dd = dd / (abs(Z[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 20;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// Xg
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Xgr[i] - Xg[i]);
		dd = dd / (abs(Xg[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 21;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// Xv
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Xvr[i] - Xv[i]);
		dd = dd / (abs(Xv[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 22;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// Q
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Qr[i] - Q[i]);
		dd = dd / (abs(Q[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 23;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// Tz
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Tzr[i] - Tz[i]);
		dd = dd / (abs(Tz[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 24;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// Tm
	for (int i = 0; i < NSEC; i++) {
		dd = abs(Tmr[i] - Tm[i]);
		dd = dd / (abs(Tm[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 25;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// Age
	for (int i = 0; i < NSEC; i++) {
		dd = abs(AgEr[i] - AgE[i]);
		dd = dd / (abs(AgE[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 26;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// CssE
	for (int i = 0; i < NSEC; i++) {
		dd = abs(CssEr[i] - CssE[i]);
		dd = dd / (abs(CssE[i]) + 0.000001);
		if (dd > dist_max) {
			dist_max = dd;
			idm = ndm;
			pdm = 27;
			ddm = i;
		};
		ndm++;
		dist += dd * dd;
	}
	desvios[ndv++] = dist;
	// Fi
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			dd = abs(Fr[i][j] - Fi[i][j]);
			dd = dd / (abs(Fi[i][j]) + 0.000001);
			if (dd > dist_max) {
				dist_max = dd;
				idm = ndm;
				pdm = 28;
				ddm = i * NFAC + j;
			};
			ndm++;
			dist += dd * dd;
		}
	}
	desvios[ndv++] = dist;
	// F
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			dd = abs(Fr[i][j] - F[i][j]);
			dd = dd / (abs(F[i][j]) + 0.000001);
			if (dd > dist_max) {
				dist_max = dd;
				idm = ndm;
				pdm = 29;
				ddm = i * NFAC + j;
			};
			ndm++;
			dist += dd * dd;
		}
	}
	desvios[ndv++] = dist;
	// X
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NSEC; j++) {
			dd = abs(Xr[i][j] - X[i][j]);
			dd = dd / (abs(X[i][j]) + 0.000001);
			if (dd > dist_max) {
				dist_max = dd;
				idm = ndm;
				pdm = 30;
				ddm = i * NSEC + j;
			};
			ndm++;
			dist += dd * dd;
		}
	}
	desvios[ndv++] = dist;

	puntero_bloque_desviacion = pdm;
	desplazamiento_desviacion = ddm;
#ifdef COMPROBAR_DESVIACION
	// buscar el rótulo del bloque de máxima desviación
	puntero_bloque_desviacion = -1;
	desplazamiento_desviacion = -1;
	for (int i = 0; i < MAX_BLOQUES_DESVIOS - 1; i++) {
		if (idm >= ind_bloque_desviacion[i] && idm < ind_bloque_desviacion[i + 1]) {
			puntero_bloque_desviacion = i;
			desplazamiento_desviacion = idm - ind_bloque_desviacion[i];
			break;
		}
	}
	if (puntero_bloque_desviacion != pdm || puntero_bloque_desviacion == -1 || pdm == -1) {
		fprintf(salida, "Error: el bloque de desviación identificado %d no coincide con el bloque esperado %d.\n", puntero_bloque_desviacion, pdm);
		fflush(salida);
		puntero_bloque_desviacion = 0;
		desplazamiento_desviacion = 0;
	}
	if (desplazamiento_desviacion != ddm || desplazamiento_desviacion == -1 || ddm == -1) {
		fprintf(salida, "Error: el desplazamiento de desviación identificado %d no coincide con el desplazamiento esperado %d.\n", desplazamiento_desviacion, ddm);
		fflush(salida);
		puntero_bloque_desviacion = 0;
		desplazamiento_desviacion = 0;
	}
#endif
	// cabecera + vector solución + valores para todas las demás variables

	// cabecera
	int nsol = 0;
	me_sol[nsol++] = 0;			// resultado
	me_sol[nsol++] = 0;			// número de datos
	me_sol[nsol++] = 0;			// intentos
	me_sol[nsol++] = 0;			// generaciones
	me_sol[nsol++] = dist;		// mérito
	me_sol[nsol++] = dist_max;	// desviación máxima
	me_sol[nsol++] = idm;		// índice de desviación máxima

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

	// los recálculos (segundo pase)
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
	me_sol[nsol++] = Tir;
	me_sol[1] = nsol;

	// cabecera	+ vector solucion + detalle desvios + evolución error
	nsol = 0;
	VEC_OPT_E[nsol++] = 0;			// resultado
	VEC_OPT_E[nsol++] = 0;			// número de datos
	VEC_OPT_E[nsol++] = 0;			// intentos
	VEC_OPT_E[nsol++] = 0;			// generaciones
	VEC_OPT_E[nsol++] = dist;		// mérito
	VEC_OPT_E[nsol++] = dist_max;	// desviación máxima
	VEC_OPT_E[nsol++] = idm;		// índice de desviación máxima

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
#endif

#ifdef COMPROBAR_MAX_DESVIACION
void indice_desviaciones() {
	int idm = 0;
	ind_bloque_desviacion[idm++] = 0;												// ebp
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + 1;				// Q eq
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// F - FF
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NFAC;			// Alp
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NDEM * NFAC;	// Sg
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + 1;				// Sp
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NDEM;			// vacante
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + 1;				// Agh
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NDEM;			// CssH
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NDEM;			// Td
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NDEM;			// FF
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NDEM * NFAC;	// Xpi
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NDEM * NSEC;	// Xp
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NDEM * NSEC;	// Ei
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// Mi
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// Dai
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// E
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// M
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// Ydp
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// Dat
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// Z
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// Xg
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// Xv
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// Q
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// Tz
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// Tm
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// AgE
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// CssE
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// Fi
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC * NFAC;	// F
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC * NFAC;	// X
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC * NSEC;	// Ti
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + 1;				// Yp
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// Yd
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// Da
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// Dt
	ind_bloque_desviacion[idm++] = ind_bloque_desviacion[idm - 1] + NSEC;			// fin
}
#endif
/*
a continuación y hasta el final todas las ecuaciones del modelo.
*/
void produccion_factor_compuesto_Y(double* Y, double F[NSEC][NFAC], double beta[NSEC][NFAC], double* b) {
	for (int i = 0; i < NSEC; i++) {
		Y[i] = b[i];
		for (int j = 0; j < NFAC; j++) {
			// cero elevado a cero es 1, por eso no hay problema si F[i][j] es cero porque beta[i][j] tambien es cero
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
#ifdef CONSUMO_INTERMEDIO_AX
void consumo_intermedio_X(double X[NSEC][NSEC], double* Z, double ax[NSEC][NSEC]) {
	// no ahorra tiempo, quizás el compilador ya lo hace
	__m256d ax_Z;
	__m256d ax_ax;
	__m256d ax_X{};
	double* ax_vX = (double*)&ax_X;
	for (int i = 0; i < NSEC; i++) {
		ax_Z = _mm256_set1_pd(Z[i]);
		for (int j = 0; j < NSEC4; j += 4) {
			ax_ax = _mm256_setr_pd(ax[i][j], ax[i][j + 1], ax[i][j + 2], ax[i][j + 3]);
			ax_X = _mm256_mul_pd(ax_ax, ax_Z);
			X[i][j] = ax_vX[0];
			X[i][j + 1] = ax_vX[1];
			X[i][j + 2] = ax_vX[2];
			X[i][j + 3] = ax_vX[3];
		}
		for (int j = NSEC4; j < NSEC; j++) {
			X[i][j] = ax[i][j] * Z[i];
		}
	}
}
#else
#ifdef CONSUMO_INTERMEDIO_INDESADO
void consumo_intermedio_X(double X[NSEC][NSEC], double* Z, double ax[NSEC][NSEC]) {
	int i;
	int j;
	for (int n = 0; n < ndc_ax; n++) {
		i = dc_ax[n][0];
		j = dc_ax[n][1];
		X[i][j] = ax[i][j] * Z[i];
	}
}
#else
void consumo_intermedio_X(double X[NSEC][NSEC], double* Z, double ax[NSEC][NSEC]) {
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NSEC; j++) {
			X[i][j] = ax[i][j] * Z[i];
		}
	}
}
#endif
#endif
/*
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
		for (int i = 0; i < NDEM; i++) {
			sfachog[j] += FF0[i][j];
		}
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
double impuestos_directos_Ti(double tai, double* pf, double FF[NDEM][NFAC], int INDICE_F_TRA) {
	double ingresos = 0.;
	for (int i = 0; i < NDEM; i++) {
		ingresos += FF[i][1 - INDICE_F_TRA];
	}
	return tai * ingresos * pf[1 - INDICE_F_TRA];
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
void ahorro_hogares_Sp(double* Sp, double* ssp, double* pf, double FF[NDEM][NFAC], double* PssH0) {

	// los Alp van aparte

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
	double signo_teta;
	double abs_teta;
	double expo;
	for (int i = 0; i < NSEC; i++) {
		if (xie[i] > 0.000001) {
			signo_teta = copysign(1.0, teta[i]);
			abs_teta = abs(teta[i]);
			if (MODO_PSEUDOIMPTOS == 0) {
				base = signo_teta * pow(abs_teta, phi[i]) * (1. + tauz[i] + (CssE[i] - AgE[i]) / Z[i] + Apz) * pz[i] * xie[i] / pe[i];
			}
			else {
				base = signo_teta * pow(abs_teta, phi[i]) * (1. + tauz[i] + ctzssez[i] - ctzagez[i] + Apz) * pz[i] * xie[i] / pe[i];
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
	double signo_teta;
	double abs_teta;
	double expo;
	for (int i = 0; i < NSEC; i++) {
		if (xid[i] > 0.000001) {
			signo_teta = copysign(1.0, teta[i]);
			abs_teta = abs(teta[i]);
			if (MODO_PSEUDOIMPTOS == 0) {
				base = signo_teta * pow(abs_teta, phi[i]) * (1. + tauz[i] + (CssE[i] - AgE[i]) / Z[i] + Apz) * pz[i] * xid[i] / pd[i];
			}
			else {
				base = signo_teta * pow(abs_teta, phi[i]) * (1. + tauz[i] + ctzssez[i] - ctzagez[i] + Apz) * pz[i] * xid[i] / pd[i];
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
