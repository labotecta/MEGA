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
#include <immintrin.h>

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
'me_sol' concatena los valores de todas las variables de la solución (no solo del vector de prueba) para que la función 'solucioma' del algoritmo
genético la devuelva. La carga la función 'merito_sol', que no es adecuada para multiproceso, pero no hay problema porque solo se
la llama una vez terminado el algoritmo genético, que usa la función 'merito_s' que si es adecuada para multiproceso al no usar
variables globales (salvo las que no cambian). Se podría eliminar porque lo realmente útil es la variable 'VEC_OPT_E'.
*/
double me_sol[5 + 2 + 4 * NSEC + 1 + 2 * NSEC + 1 + 8 * NSEC + NDEM + 2 * NSEC + NDEM + NSEC + NDEM + NSEC + NDEM + 1 + 1 + 1 + NDEM * NSEC + NSEC * NFAC + 2 * NDEM * NFAC + NSEC * NSEC + NDEM * NSEC]{};
/*
igual que 'me_sol' pero solo guarda el vector solución, que es lo realmente útil ya que valor del resto
de las variables se puede obtener a partir del vector solución mediante las ecuaciones del modelo
*/
double VEC_OPT_E[5 + NFAC + 3 * NSEC + 2 + NSEC * NFAC + 3 * NSEC + NDEM * NSEC]{};

int NVEC;
#pragma region Genetico

/*
convertimos en matrices (vectores) las variables que cada hilo debe
utilizar de forma independiente de los otros hilos para evitar que colisionen.
para usar matrices fijas definimos la constante MAX_HILOS en 128 que aunque desperdiciemos
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

int ind_mejor_merito;
double mejor_merito;
int generacion;
int resto;
int hbloque;
double vant;
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
int gene_control_progreso;
double min_progreso;
bool control_factibilidad;
bool sal_solucion;
int semilla;

mt19937 gen;
uniform_real_distribution<double> dis_double(0.0, 1.0);
uniform_int_distribution<int> dis_entero{};
/*
esta es la función que hay que llamar para que se ejeute el algorimo genético, previamente hay que llamar
a:
	recibe_opciones
	recibe_datos
	recibe_parametros
que aportan los datos que se necesitan para la función objetivo

los parámetros del algoritmo genético ya los recibe 'soluciona' en sus propios parámetros

si 'extendida' es igual a 0, 'soluciona' devuelve el vector solución, si es igual a 1 devuelve todas las
variables del modelo, esto último carece de utilidad, es preferible que quien llama a la DLL calcule
las variables a partir del vector solución aplicando las ecuaciones del modelo.
*/
double* soluciona(double* par, double* cotasInf, double* cotasSup, double* vec, int extendida) {
	// Error en los parametros recibidos
	int res = parametros_alge(par);
	if (res != 0) {
		if (extendida == 1) {
			me_sol[0] = -6;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -100. + res;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			return VEC_OPT_E;
		}
	}
	if (inicia_cotas() == false) {
		// Error al generar la poblacion
		merito_sol(poblacion[ind_mejor_merito]);
		if (extendida == 1) {
			me_sol[0] = -1.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -1.;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			return VEC_OPT_E;
		}
	}
	if (fija_cotas(cotasInf, cotasSup) == false) {
		// Error al fijar las cotas
		if (extendida == 1) {
			me_sol[0] = -2.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -2;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			return VEC_OPT_E;
		}
	}
	if (inicia_poblacion(factor_inicio) == false) {
		// Error al reservar memoria para la poblacion
		if (extendida == 1) {
			me_sol[0] = -3.;
			me_sol[2] = intentos;
			me_sol[3] = generacion;
			return me_sol;
		}
		else {
			VEC_OPT_E[0] = -3.;
			VEC_OPT_E[2] = intentos;
			VEC_OPT_E[3] = generacion;
			return VEC_OPT_E;
		}
	}
	gen.seed(semilla);
	dis_entero = uniform_int_distribution<int>{ 0, ((int)NPOB - 1) };
	if (genera_poblacion() == false) {
		// Error al generar la poblacion
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
	vant = 1.0e+99;
	generacion = 0;
	intentos = 0;
	hgen[0] = mt19937(semilla);
	hdis_entero[0] = uniform_int_distribution<int>{ 0, ((int)NPOB - 1) };
	hdis_entero_ivec[0] = uniform_int_distribution<int>{ 0, ((int)NVEC - 1) };
	hdis_double[0] = uniform_real_distribution<double>{ 0.0, 1.0 };
	if (n_hilos > 0) {
		if (PreparaMP(max_generaciones) == -1) {
			if (extendida == 1) {
				me_sol[0] = -7.;
				me_sol[2] = intentos;
				me_sol[3] = generacion;
				return me_sol;
			}
			else {
				VEC_OPT_E[0] = -7.;
				VEC_OPT_E[2] = intentos;
				VEC_OPT_E[3] = generacion;
				return VEC_OPT_E;
			}
		}
	}
	else {
		res_Simulacion = avanza();
	}
	if (res_Simulacion == -2) {
		// Encontrada solucion
		merito_sol(poblacion[ind_mejor_merito]);
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
			merito_sol(poblacion[ind_mejor_merito]);
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
			merito_sol(poblacion[ind_mejor_merito]);
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
			merito_sol(poblacion[ind_mejor_merito]);
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
			merito_sol(poblacion[ind_mejor_merito]);
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
		merito_sol(poblacion[ind_mejor_merito]);
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
}
int parametros_alge(double* par) {
	int ipar = 0;
	max_intentos = (int)par[ipar++];
	n_hilos = (int)par[ipar++];
	max_generaciones = (int)par[ipar++];
	tolerancia = par[ipar++];
	tol_aceptable = par[ipar++];
	gene_control_progreso = (int)par[ipar++];
	min_progreso = par[ipar++];
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
	NVEC = (int)par[ipar++];

	resto = NVEC % 4;
	hbloque = NVEC - resto;

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
	double semi_intervalo;
	double desplazamiento;
	double v;
	if (modo_poblacion_inicial == 0) {
		for (int j = 0; j < NVEC; j++) {
			if (fijo[j] == 1) {
				poblacion[0][j] = cotas[0][j];
			}
			else {
				poblacion[0][j] = cotas[0][j] + (cotas[1][j] - cotas[0][j]) / 2.;
			}
		}
		for (int i = 1; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				if (fijo[j] == 1) {
					poblacion[i][j] = cotas[0][j];
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
	else if (modo_poblacion_inicial == 1) {
		mt19937 gent(semilla);
		normal_distribution<double> dis_normal{ 0.0, sigma_inicio };
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
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
	else if (modo_poblacion_inicial == 2) {
		/*
		Latin Hypercube Sampling
		distrubuye uniformemente los valores de las variables en sus rangos de variación
		dividiendo esos rangos en tramos y generando la fracción correspondiente de individuos
		en cada tramo.
		No es la más adecuada para nuestro problema donde se ha encontrado que lo mejor
		es generar en entornos muy estrechos en torno al valor inicial de las variables (+ - 1%), aunque
		los rangos de variación sean suficientemente grandes para que las variables puedan evolucionar
		hasta el valor de la solución.
		*/

		int individuos_tramo = NPOB / num_tramos_lhs;
		int indice_ini_tramo;
		int indice_fin_tramo;
		double ancho_tramo;
		double cota_desde;
		double cota_hasta;
		for (int j = 0; j < NVEC; j++) {
			if (fijo[j] == 1) {
				for (int i = 0; i < NPOB; i++) {
					descendiente[i][j] = cotas[0][j];
				}
			}
			else {
				indice_ini_tramo = 0;
				indice_fin_tramo = indice_ini_tramo + individuos_tramo;
				ancho_tramo = (cotas[1][j] - cotas[0][j]) / num_tramos_lhs;
				cota_desde = cotas[0][j];
				for (int k = 0; k < num_tramos_lhs; k++) {
					for (int i = indice_ini_tramo; i < indice_fin_tramo; i++) {
						cota_hasta = cota_desde + ancho_tramo;
						semi_intervalo = (cota_hasta - cota_desde) / 2.;
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
						descendiente[i][j] = v;
						cota_desde = cota_hasta;
					}
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
		std::shuffle(p, p + NPOB, rng);
		for (int i = 0; i < NPOB; i++) {
			for (int j = 0; j < NVEC; j++) {
				poblacion[i][j] = descendiente[p[i]][j];
			}
		}
		free(p);
	}
	mejor_merito = 1.0e+99;
	ind_mejor_merito = NPOB + 1;
	for (int i = 0; i < NPOB; i++) {
		v = merito_s(poblacion[i]);
		merito_individuo[i] = v;
		factible[i] = true;
		if (v < mejor_merito) {
			mejor_merito = v;
			ind_mejor_merito = i;
		}
	}
	return true;
}
int avanza() {
	cte_recombinacion = (recombinacion[0] + recombinacion[1]) / 2.;
	while (generacion < max_generaciones) {
		mutacion_cruze(0, NPOB, 0);
		/*
		no se hacen cambios en la población hasta completada la generación
		para poder fraccionar la población en multiproceso
		*/
		seleccion();
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
void mutacion_cruzeH(int desde, int hasta, int hilo
) {
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
void seleccion() {
	double me_descendiente;
	for (int i = 0; i < NPOB; i++) {
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
	if (mejor_merito < tolerancia) {
		return -2;
	}
	if (generacion > 0 && (generacion % gene_control_progreso == 0)) {
		if ((vant - mejor_merito) < min_progreso) {
			if (mejor_merito < tol_aceptable) {
				return -3;
			}
			intentos++;
			if (intentos < max_intentos) {
				genera_poblacion();
				vant = 1.0e+99;
			}
			else {
				return -3;
			}
		}
		else {
			if (!control_factibilidad) {
				double dist = distancia_clonacion();
				if (dist > 1.e+32) {
					intentos++;
					if (intentos < max_intentos) {
						genera_poblacion();
						vant = 1.0e+99;
					}
					else {
						return -3;
					}
				}
				else {
					vant = mejor_merito;
				}
			}
			else {
				vant = mejor_merito;
			}
		}
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
*********************
Multi tarea
*********************
*/
bool Arranque() {
	for (int i = 1; i < n_hilos; i++) {
		hgen[i] = mt19937(semilla + i);
		hdis_entero[i] = uniform_int_distribution<int>{ 0, ((int)NPOB - 1) };
		hdis_entero_ivec[i] = uniform_int_distribution<int>{ 0, ((int)NVEC - 1) };
		hdis_double[i] = uniform_real_distribution<double>{ 0.0, 1.0 };
	}
	cte_recombinacion = (recombinacion[0] + recombinacion[1]) / 2.;
	CANCELADO = false;
	return true;
}
int PreparaMP(int hasta) {
	// Comprobar la relación entre el número de hilos y el de la población

	int bloques = NPOB / n_hilos;
	if (bloques * n_hilos != NPOB) {
		//printf("Cancelado. El numero de individuos debe ser multiplo del numero de hilos\n");
		return-1;
	}
	if (!Arranque()) return-2;
	ProcesoMP(hasta, bloques);
	return 0;
}
int ProcesoMP(int hasta, int bloques) {
	if (!InitializeCriticalSectionAndSpinCount(&seccion_fin_hilos, 0x00000400)) {
		printf("Error [%d] creando la seccion critica fin_hilos\n", GetLastError());
		return 0;
	}

	// Crear el semaforo para iterar cerrado

	semaforo_itera = CreateSemaphore(NULL, 0, 1, NULL);
	if (semaforo_itera == NULL)
	{
		printf("Error al crear el semaforo de iteracion: %d\n", GetLastError());
		return 0;
	}

	// Crear los semaforos para los hilos abiertos
	hilos_terminados = 0;
	for (int i = 0; i < n_hilos; i++) {
		semaforo_hilo[i] = CreateSemaphore(NULL, 1, 1, NULL);
		if (semaforo_hilo[i] == NULL)
		{
			printf("Error al crear el semaforo para los hilos: %d\n", GetLastError());
			return 0;
		}
	}

	// Arranca los hilos con su semaforo abierto

	int parametros_hilo[3 * MAX_HILOS]{};
	int conth = 0;
	for (int i = 0; i < n_hilos; i++) {
		parametros_hilo[conth++] = i;
		parametros_hilo[conth++] = i * bloques;
		if (i == n_hilos - 1) {
			parametros_hilo[conth] = NPOB;
		}
		else {
			parametros_hilo[conth++] = i * bloques + bloques;
		}
	}
	for (int i = 0; i < n_hilos; i++) {
		invalida_hilos[i] = false;
		hilos[i] = (HANDLE)_beginthreadex(0, 0, HiloTramos, parametros_hilo + 3 * (INT_PTR)i, 0, 0);

		// Para que los hilos comienzen a ejecutarse en orden

		Sleep(50);

		if (hilos[i] == 0) {
			printf("Error al crear un hilo");
			return 0;
		}
	}

	// Arranca el ciclo temporal con el semaforo iterar cerrado. Lo abre el ultimo hilo en terminar

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
			res_Simulacion = comprobar_final();
			if (res_Simulacion < 0) {
				CANCELADO = true;
				break;
			}
			generacion++;
			if (generacion == hasta) {
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
			printf("El hilo %d: supero el tiempo de espera\n", GetCurrentThreadId());
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
			printf("El hilo %d supero el tiempo de espera\n", indice);
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

//   0    1    2    3      4        5    6   7   8   9   10
// ['pF','pY','pQ','pD','epsilon','Apz','F','E','M','D','Xp']
//   1    6    6    6      1        1   12   6   6   6   12
const int len_var[] = { 1, 6, 6, 6, 1, 1, 12, 6, 6, 6, 12 };
const int pvec[12] = { 0, 1, 7, 13, 19, 20, 21, 33, 39, 45, 51, 63 };

double AYD_ADI_DEM[NDEM]{};

/*
fin de las variables globales que necesita 'mérito' y que son inútiles
*/

OPCIONES recibe_opciones(OPCIONES vopt) {
	op = vopt;
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
	parametros = vpar;
	return parametros;
}
/*
función objetivo multiproceso, la que hay que usar siempre, aunque no se utilice multiproceso
*/
double merito_s(double* vec_opt) {
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
	double X[NSEC][NSEC];
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
	double Xr[NSEC][NSEC];
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
	double ebp;
	double Sgr;
	double Scr;
	double ebpr;

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
	ayudas_empresas_AgE(AgE, parametros.cage, Td, Tz, Tm);
	ayudas_hogares_AgH(AgH, parametros.cagh, Td, Tz, Tm, AYD_ADI_DEM);
	ahorro_hogares_Sp(Sp, parametros.ssp, FF, pf, datos.PssH0);
	seguridad_social_empresas_CssE(CssE, parametros.ctzsse, pf, F, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssH, parametros.ctzssh, pf, FF, Alp, op.INDICE_F_TRA);
	Sg = ahorro_gobierno_Sg(parametros.ssg, Td, Tz, Tm, AgE, AgH, datos.PssH0, CssH, CssE);
	demanda_gobierno_Xg(Xg, parametros.mu, pq, Td, Tz, Tm, Sg, AgE, AgH, datos.PssH0, CssH, CssE);
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
	demanda_inversion_Xv(Xv, parametros.landa, pq, Sp, Sg, Sc, epsilon, datos.Sf0);
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
	ebp = equilibrio_balance_pagos_moneda_extranjera(datos.pWe, E, datos.pWm, M, datos.Sf0);

	// -----------------------
	// segundo pase
	// -----------------------
	restriccion_produccion_bruta_Z(Zr, parametros.teta, parametros.xie, parametros.xid, E, Dt, parametros.phi);
	produccion_factor_compuesto_Y(Ypr, F, parametros.beta, parametros.b);
	uso_optimo_factores_F(Fr, parametros.beta, pf, py, Ypr);
	consumo_intermedio_X(Xr, Zr, parametros.ax);
	utilizacion_factor_compuesto_Y(Ydr, Zr, parametros.ay);
	if (op.FF_ENDOGENA) {
		aportacion_factores_FF(FFr, datos.FF0, F);
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
	ayudas_empresas_AgE(AgEr, parametros.cage, Tdr, Tzr, Tmr);
	ayudas_hogares_AgH(AgHr, parametros.cagh, Tdr, Tzr, Tmr, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssEr, parametros.ctzsse, pf, Fr, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssHr, parametros.ctzssh, pf, FFr, Alp, op.INDICE_F_TRA);
	Sgr = ahorro_gobierno_Sg(parametros.ssg, Tdr, Tzr, Tmr, AgEr, AgHr, datos.PssH0, CssHr, CssEr);
	demanda_gobierno_Xg(Xgr, parametros.mu, pq, Tdr, Tzr, Tmr, Sgr, AgEr, AgHr, datos.PssH0, CssHr, CssEr);
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
	demanda_inversion_Xv(Xvr, parametros.landa, pq, Sp, Sg, Scr, epsilon, datos.Sf0);
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
	produccion_para_local_D(Dtr, parametros.teta, parametros.xid, pz, pd, Z, parametros.phi, datos.tauz, CssE, AgE, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	ebpr = equilibrio_balance_pagos_moneda_extranjera(datos.pWe, Er, datos.pWm, Mr, datos.Sf0);

	double dd;
	double dist = 0.;

	dd = abs(Apz);
	dist += dd * dd;
	dd = abs(ebp) + abs(ebpr);
	dist += dd * dd;
	for (int i = 0; i < NSEC; i++) {
		sum_Xp = 0.;
		for (int j = 0; j < NDEM; j++) {
			sum_Xp += Xpr[j][i];
		}
		sum_X = 0.;
		for (int j = 0; j < NSEC; j++) {
			sum_X += Xr[j][i];
		}
		dd = abs(Qr[i] - (sum_Xp + Xg[i] + Xv[i] + sum_X));
		dist += dd * dd;
	}
	if (op.FF_ENDOGENA) {
		if (op.ALP_FACTOR > 0) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					dd = abs(Alpr[i][j] - Alp[i][j]);
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
			dd = abs(suma_F - suma_FF);
			dist += dd * dd;
		}
	}
	dd = abs(Sgr - Sg);
	dist += dd * dd;
	for (int i = 0; i < NDEM; i++) {
		dd = abs(Spr[i] - Sp[i]);
		dist += dd * dd;
		dd = abs(AgHr[i] - AgH[i]);
		dist += dd * dd;
		dd = abs(CssHr[i] - CssH[i]);
		dist += dd * dd;
		dd = abs(Tdr[i] - Td[i]);
		dist += dd * dd;
		for (int j = 0; j < NFAC; j++) {
			dd = abs(FFr[i][j] - FF[i][j]);
			dist += dd * dd;
		}
		for (int j = 0; j < NSEC; j++) {
			if (op.GE_INCLUYE_XP) {
				dd = abs(Xp[i][j] - Xpi[i][j]);
				dist += dd * dd;
			}
			dd = abs(Xpr[i][j] - Xp[i][j]);
			dist += dd * dd;
		}
	}
	for (int i = 0; i < NSEC; i++) {
		dd = abs(E[i] - Ei[i]);
		dist += dd * dd;
		dd = abs(M[i] - Mi[i]);
		dist += dd * dd;
		dd = abs(Er[i] - E[i]);
		dist += dd * dd;
		dd = abs(Mr[i] - M[i]);
		dist += dd * dd;
		dd = abs(Yd[i] - Yp[i]);
		dist += dd * dd;
		dd = abs(Da[i] - Dt[i]);
		dist += dd * dd;
		dd = abs(Zr[i] - Z[i]);
		dist += dd * dd;
		dd = abs(Xgr[i] - Xg[i]);
		dist += dd * dd;
		dd = abs(Xvr[i] - Xv[i]);
		dist += dd * dd;
		dd = abs(Qr[i] - Q[i]);
		dist += dd * dd;
		dd = abs(Tzr[i] - Tz[i]);
		dist += dd * dd;
		dd = abs(Tmr[i] - Tm[i]);
		dist += dd * dd;
		dd = abs(AgEr[i] - AgE[i]);
		dist += dd * dd;
		dd = abs(CssEr[i] - CssE[i]);
		dist += dd * dd;
		for (int j = 0; j < NFAC; j++) {
			dd = abs(F[i][j] - Fi[i][j]);
			dist += dd * dd;
			dd = abs(Fr[i][j] - F[i][j]);
			dist += dd * dd;
		}
		for (int j = 0; j < NSEC; j++) {
			dd = abs(Xr[i][j] - X[i][j]);
			dist += dd * dd;
		}
	}
	return dist;
}
/*
prepara los vectores 'me_sol' y 'VEC_OPT_E' con todas las variables del modelo, o las variables de la solución, respectivamente y
que al ser variables globales quedan en memoria a disposición de cualquier otra función, como 'soluciona', para 
devolverlas a quien llame a la DLL
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
	double F[NSEC][NFAC];
	double E[NSEC];
	double M[NSEC];
	double D[NSEC];

	double Fi[NSEC][NFAC];
	double Ei[NSEC];
	double Mi[NSEC];
	double Di[NSEC];
	double Xpi[NDEM][NSEC];

	double Yp[NSEC];
	double Z[NSEC];
	double X[NSEC][NSEC];
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
	double Xr[NSEC][NSEC];
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
	double ebp;
	double Sgr;
	double Scr;
	double ebpr;

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
	ayudas_empresas_AgE(AgE, parametros.cage, Td, Tz, Tm);
	ayudas_hogares_AgH(AgH, parametros.cagh, Td, Tz, Tm, AYD_ADI_DEM);
	ahorro_hogares_Sp(Sp, parametros.ssp, FF, pf, datos.PssH0);
	seguridad_social_empresas_CssE(CssE, parametros.ctzsse, pf, F, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssH, parametros.ctzssh, pf, FF, Alp, op.INDICE_F_TRA);
	Sg = ahorro_gobierno_Sg(parametros.ssg, Td, Tz, Tm, AgE, AgH, datos.PssH0, CssH, CssE);
	demanda_gobierno_Xg(Xg, parametros.mu, pq, Td, Tz, Tm, Sg, AgE, AgH, datos.PssH0, CssH, CssE);
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
	demanda_inversion_Xv(Xv, parametros.landa, pq, Sp, Sg, Sc, epsilon, datos.Sf0);
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
	ebp = equilibrio_balance_pagos_moneda_extranjera(datos.pWe, E, datos.pWm, M, datos.Sf0);

	// -----------------------
	// segundo pase
	// -----------------------
	restriccion_produccion_bruta_Z(Zr, parametros.teta, parametros.xie, parametros.xid, E, Dt, parametros.phi);
	produccion_factor_compuesto_Y(Ypr, F, parametros.beta, parametros.b);
	uso_optimo_factores_F(Fr, parametros.beta, pf, py, Ypr);
	consumo_intermedio_X(Xr, Zr, parametros.ax);
	utilizacion_factor_compuesto_Y(Ydr, Zr, parametros.ay);
	if (op.FF_ENDOGENA) {
		aportacion_factores_FF(FFr, datos.FF0, F);
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
	ayudas_empresas_AgE(AgEr, parametros.cage, Tdr, Tzr, Tmr);
	ayudas_hogares_AgH(AgHr, parametros.cagh, Tdr, Tzr, Tmr, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssEr, parametros.ctzsse, pf, Fr, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssHr, parametros.ctzssh, pf, FFr, Alp, op.INDICE_F_TRA);
	Sgr = ahorro_gobierno_Sg(parametros.ssg, Tdr, Tzr, Tmr, AgEr, AgHr, datos.PssH0, CssHr, CssEr);
	demanda_gobierno_Xg(Xgr, parametros.mu, pq, Tdr, Tzr, Tmr, Sgr, AgEr, AgHr, datos.PssH0, CssHr, CssEr);
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
	demanda_inversion_Xv(Xvr, parametros.landa, pq, Sp, Sg, Scr, epsilon, datos.Sf0);
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
	produccion_para_local_D(Dtr, parametros.teta, parametros.xid, pz, pd, Z, parametros.phi, datos.tauz, CssE, AgE, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	ebpr = equilibrio_balance_pagos_moneda_extranjera(datos.pWe, Er, datos.pWm, Mr, datos.Sf0);

	double dd;
	double dist = 0.;

	dd = abs(Apz);
	dist += dd * dd;
	dd = abs(ebp) + abs(ebpr);
	dist += dd * dd;
	for (int i = 0; i < NSEC; i++) {
		sum_Xp = 0.;
		for (int j = 0; j < NDEM; j++) {
			sum_Xp += Xpr[j][i];
		}
		sum_X = 0.;
		for (int j = 0; j < NSEC; j++) {
			sum_X += Xr[j][i];
		}
		dd = abs(Qr[i] - (sum_Xp + Xg[i] + Xv[i] + sum_X));
		dist += dd * dd;
	}
	if (op.FF_ENDOGENA) {
		if (op.ALP_FACTOR > 0) {
			for (int i = 0; i < NDEM; i++) {
				for (int j = 0; j < NFAC; j++) {
					dd = abs(Alpr[i][j] - Alp[i][j]);
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
			dd = abs(suma_F - suma_FF);
			dist += dd * dd;
		}
	}
	dd = abs(Sgr - Sg);
	dist += dd * dd;

	for (int i = 0; i < NDEM; i++) {
		dd = abs(Spr[i] - Sp[i]);
		dist += dd * dd;
		dd = abs(AgHr[i] - AgH[i]);
		dist += dd * dd;
		dd = abs(CssHr[i] - CssH[i]);
		dist += dd * dd;
		dd = abs(Tdr[i] - Td[i]);
		dist += dd * dd;
		for (int j = 0; j < NFAC; j++) {
			dd = abs(FFr[i][j] - FF[i][j]);
			dist += dd * dd;
		}
		for (int j = 0; j < NSEC; j++) {
			if (op.GE_INCLUYE_XP) {
				dd = abs(Xp[i][j] - Xpi[i][j]);
				dist += dd * dd;
			}
			dd = abs(Xpr[i][j] - Xp[i][j]);
			dist += dd * dd;
		}
	}
	for (int i = 0; i < NSEC; i++) {
		dd = abs(E[i] - Ei[i]);
		dist += dd * dd;
		dd = abs(M[i] - Mi[i]);
		dist += dd * dd;
		dd = abs(Er[i] - E[i]);
		dist += dd * dd;
		dd = abs(Mr[i] - M[i]);
		dist += dd * dd;
		dd = abs(Yd[i] - Yp[i]);
		dist += dd * dd;
		dd = abs(Da[i] - Dt[i]);
		dist += dd * dd;
		dd = abs(Zr[i] - Z[i]);
		dist += dd * dd;
		dd = abs(Xgr[i] - Xg[i]);
		dist += dd * dd;
		dd = abs(Xvr[i] - Xv[i]);
		dist += dd * dd;
		dd = abs(Qr[i] - Q[i]);
		dist += dd * dd;
		dd = abs(Tzr[i] - Tz[i]);
		dist += dd * dd;
		dd = abs(Tmr[i] - Tm[i]);
		dist += dd * dd;
		dd = abs(AgEr[i] - AgE[i]);
		dist += dd * dd;
		dd = abs(CssEr[i] - CssE[i]);
		dist += dd * dd;
		for (int j = 0; j < NFAC; j++) {
			dd = abs(F[i][j] - Fi[i][j]);
			dist += dd * dd;
			dd = abs(Fr[i][j] - F[i][j]);
			dist += dd * dd;
		}
		for (int j = 0; j < NSEC; j++) {
			dd = abs(Xr[i][j] - X[i][j]);
			dist += dd * dd;
		}
	}

	int nsol = 0;
	me_sol[nsol++] = 0;		// resultado
	me_sol[nsol++] = 0;		// número de datos
	me_sol[nsol++] = 0;		// intentos
	me_sol[nsol++] = 0;		// generaciones
	me_sol[nsol++] = dist;	// mérito

	for (int i = 0; i < NFAC; i++)	me_sol[nsol++] = pf[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = py[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = pq[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = pd[i];
	me_sol[nsol++] = epsilon;
	me_sol[nsol++] = Apz;
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			me_sol[nsol++] = F[i][j];
		}
	}
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = E[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = M[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = D[i];

	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = pz[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = pe[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = pm[i];
	for (int i = 0; i < NSEC; i++)	me_sol[nsol++] = Yp[i];
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

	me_sol[1] = nsol;

	nsol = 0;
	VEC_OPT_E[nsol++] = 0;		// resultado
	VEC_OPT_E[nsol++] = 0;		// número de datos
	VEC_OPT_E[nsol++] = 0;		// intentos
	VEC_OPT_E[nsol++] = 0;		// generaciones
	VEC_OPT_E[nsol++] = dist;	// mérito
	VEC_OPT_E[nsol++] = pf[0];
	VEC_OPT_E[nsol++] = pf[1];
	for (int i = 1; i < NVEC; i++) {
		VEC_OPT_E[nsol++] = vec_opt[i];
	}
	VEC_OPT_E[1] = nsol;
	return me_sol;
}
/*
a continuación y hasta el final todas las ecuaciones del modelo.
'demanda_maxima_utilidad_CES_Xp' está sin definir por pura pereza
*/
void produccion_factor_compuesto_Y(double* Y, double F[NSEC][NFAC], double beta[NSEC][NFAC], double* b) {
	for (int i = 0; i < NSEC; i++) {
		Y[i] = b[i];
		for (int j = 0; j < NFAC; j++) {
			Y[i] *= copysign(1.0, F[i][j]) * pow(abs(F[i][j]), beta[i][j]);
			//Y[i] *= sgn(F[i][j]) * pow(abs(F[i][j]), beta[i][j]);
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
void ayudas_empresas_AgE(double* AgE, double* cage, double* Td, double* Tz, double* Tm) {
	double ingresos = 0.;
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
void ayudas_hogares_AgH(double* AgH, double* cagh, double* Td, double* Tz, double* Tm, double* AYD_ADI_DEM) {
	double ingresos = 0.;
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
double ahorro_gobierno_Sg(double ssg, double* Td, double* Tz, double* Tm, double* AgE, double* AgH, double* PssH0, double* CssH, double* CssE) {
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
	double neto = Css;
	for (int i = 0; i < NDEM; i++) {
		neto += (Td[i] - AgH[i]);
	}
	for (int i = 0; i < NSEC; i++) {
		neto += (Tz[i] + Tm[i] - AgE[i]);
	}
	return ssg * neto;
}
void demanda_gobierno_Xg(double* Xg, double* mu, double* pq, double* Td, double* Tz, double* Tm, double Sg, double* AgE, double* AgH, double* PssH0, double* CssH, double* CssE) {
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
	double neto = Css - Sg;
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
void demanda_inversion_Xv(double* Xv, double* landa, double* pq, double* Sp, double Sg, double Sc, double epsilon, double Sf0) {
	double ahorros = Sg + Sc + Sf0 * epsilon;
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
	for (int i = 0; i < NSEC; i++) {
		if (MODO_PSEUDOIMPTOS == 0) {
			E[i] = Z[i] * pow(pow(teta[i], phi[i]) * (1. + tauz[i] + CssE[i] / Z[i] - AgE[i] / Z[i] + Apz) * pz[i] * xie[i] / pe[i], 1. / (1. - phi[i]));
		}
		else {
			E[i] = Z[i] * pow(pow(teta[i], phi[i]) * (1. + tauz[i] + ctzssez[i] - ctzagez[i] + Apz) * pz[i] * xie[i] / pe[i], 1. / (1. - phi[i]));
		}
	}
}
void produccion_para_local_D(double* Dt, double* teta, double* xid, double* pz, double* pd, double* Z, double* phi, double* tauz, double* CssE, double* AgE, double Apz, double* ctzssez, double* ctzagez, int MODO_PSEUDOIMPTOS) {
	for (int i = 0; i < NSEC; i++) {
		if (MODO_PSEUDOIMPTOS == 0) {
			Dt[i] = Z[i] * pow(pow(teta[i], phi[i]) * (1. + tauz[i] + CssE[i] / Z[i] - AgE[i] / Z[i] + Apz) * pz[i] * xid[i] / pd[i], 1. / (1. - phi[i]));
		}
		else {
			Dt[i] = Z[i] * pow(pow(teta[i], phi[i]) * (1. + tauz[i] + ctzssez[i] - ctzagez[i] + Apz) * pz[i] * xid[i] / pd[i], 1. / (1. - phi[i]));
		}
	}
}
double equilibrio_balance_pagos_moneda_extranjera(double* pWe, double* E, double* pWm, double* M, double Sf0) {
	double ebp = Sf0;
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

