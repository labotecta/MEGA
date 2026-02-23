// Alge.cpp : Este archivo contiene la función "main". La ejecución del programa comienza y termina ahí.

#include <Windows.h>
#include <random>
#include "inicia.h"
#include <cstdio>
#include <malloc.h>
#include <ctime> 
#include <cstdlib>
#include <process.h>
#include <immintrin.h>
#include <corecrt.h>
#include <algorithm>

using namespace std;

__m256d ax_F;
__m256d ax_cF;

int hilos_terminados;
bool CANCELADO;
int n_hilos;

HINSTANCE hinstLib;

const int MAX_HILOS = 128;
HANDLE hilos[MAX_HILOS]{};
HANDLE semaforo_hilo[MAX_HILOS]{};
HANDLE semaforo_itera;
CRITICAL_SECTION seccion_fin_hilos;
bool invalida_hilos[MAX_HILOS]{};

mt19937 hgen[MAX_HILOS]{};
uniform_int_distribution<int> hdis_entero[MAX_HILOS]{};
uniform_int_distribution<int> hdis_entero_ivec[MAX_HILOS]{};
uniform_real_distribution<double> hdis_double[MAX_HILOS]{};

typedef OPCIONES(*P_recibe_opciones)(OPCIONES);
typedef DATOS(*P_recibe_datos)(DATOS);
typedef PARAMETROS(*P_recibe_parametros)(PARAMETROS);
typedef double(*P_merito)(double*);
typedef double* (*P_merito_sol)(double*);
P_recibe_opciones recibe_opciones;
P_recibe_datos recibe_datos;
P_recibe_parametros recibe_parametros;
P_merito merito_s;
P_merito_sol merito_sol;

double** cotas = NULL;
int* fijo = NULL;
double** poblacion = NULL;
double* merito_individuo = NULL;
double* factible = NULL;
double** descendiente = NULL;
double** cdm_hilo = NULL;
double* cdm = NULL;
double* pon_cdm = NULL;
int ul_generacion_cdm;

long long* mutaciones = NULL;
long long* mufactibles = NULL;
long long mut_ant;
long long fac_ant;

int ind_mejor_merito;
double mejor_merito;
int generacion;
int resto;
int hbloque;
const char* calificador;

int NPOB;
int NVEC;
const int NPRE_SOL = 20;
int max_intentos;
int intentos;
int max_generaciones;
int gene_mostrar_evolucion;
int modo_poblacion_inicial;
double factor_inicio;
double factor_merito_acceso;
double sigma_inicio;
int num_tramos_lhs;
double factor_mutacion;
double recombinacion[2]{};
double cte_recombinacion;
double tolerancia;
double tol_aceptable;
int gene_control_progreso;
double min_progreso;
double pprecio_min;
double pprecio_max;
double vprecio_min;
double vprecio_max;
bool control_factibilidad;
bool calculo_ax;
bool sal_solucion;
bool fijar_epsilon;
double rango_var_cero;
int semilla;
bool el_mejor_primero;
bool usar_cdm;

mt19937 gen;
uniform_int_distribution<int> dis_entero{};
uniform_real_distribution<double> dis_double(0.0, 1.0);

int caso;
unsigned t0;
unsigned t1;
double tpo_ini;
double tpo_parcial;
double tpo_total;
double vant;
int res_Simulacion;

FILE* fp;

int main()
{
	// Obtener un puntero a la librería.

	if (lee_parametros("C:/MEGA/parametros.txt") == -1) {
		printf("Error en el fichero de parametros\n");
		return -1;
	}
	if (punteros_libreria(L"C:/MEGA/MEGA_DLL/x64/Release/MEGA_DLL.dll") == -1) {
		return -1;
	}
	inicia();
}
int lee_parametros(const char* fichero) {
	errno_t err;
	FILE* etxt = NULL;
	err = fopen_s(&etxt, fichero, "rt");
	if (err != 0 || etxt == NULL) {
		printf("Error (%d) al abrir el fichero de valores iniciales: %s\n", err, fichero);
		return -1;
	}
	int n;
	char linea[128];
	if (fgets(linea, 128, etxt) == NULL) return -1;
	max_intentos = atoi(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	caso = atoi(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	n_hilos = atoi(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	max_generaciones = atoi(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	gene_mostrar_evolucion = atoi(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	tolerancia = atof(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	tol_aceptable = atof(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	gene_control_progreso = atoi(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	min_progreso = atof(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	modo_poblacion_inicial = atoi(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	factor_inicio = atof(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	factor_merito_acceso = atof(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	sigma_inicio = atof(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	num_tramos_lhs = atoi(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	NPOB = atoi(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	factor_mutacion = atof(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	recombinacion[0] = atof(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	recombinacion[1] = atof(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	pprecio_min = atof(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	pprecio_max = atof(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	vprecio_min = atof(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	vprecio_max = atof(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	n = atoi(linea);
	control_factibilidad = n == 1;
	if (fgets(linea, 128, etxt) == NULL) return -1;
	n = atoi(linea);
	calculo_ax = n == 1;
	if (fgets(linea, 128, etxt) == NULL) return -1;
	n = atoi(linea);
	sal_solucion = n == 1;
	if (fgets(linea, 128, etxt) == NULL) return -1;
	n = atoi(linea);
	fijar_epsilon = n == 1;
	if (fgets(linea, 128, etxt) == NULL) return -1;
	rango_var_cero = atof(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	semilla = (int)atoi(linea);
	if (fgets(linea, 128, etxt) == NULL) return -1;
	n = atoi(linea);
	el_mejor_primero = n == 1;
	if (fgets(linea, 128, etxt) == NULL) return -1;
	n = atoi(linea);
	usar_cdm = n == 1;
	fclose(etxt);
	ax_F = _mm256_set1_pd(factor_mutacion);
	return 0;
}
int punteros_libreria(const wchar_t* fichero) {
	hinstLib = LoadLibrary(fichero);
	if (hinstLib != NULL)
	{
		recibe_opciones = (P_recibe_opciones)GetProcAddress(hinstLib, "recibe_opciones");
		if (NULL == recibe_opciones)
		{
			printf("No se produjo el enlace con la función recibe_opciones\n");
			return -1;
		}
		recibe_datos = (P_recibe_datos)GetProcAddress(hinstLib, "recibe_datos");
		if (NULL == recibe_datos)
		{
			printf("No se produjo el enlace con la función recibe_datos\n");
			return -1;
		}
		recibe_parametros = (P_recibe_parametros)GetProcAddress(hinstLib, "recibe_parametros");
		if (NULL == recibe_parametros)
		{
			printf("No se produjo el enlace con la función recibe_parametros\n");
			return -1;
		}
		merito_s = (P_merito)GetProcAddress(hinstLib, "merito_s");
		if (NULL == merito_s)
		{
			printf("No se produjo el enlace con la función merito_s\n");
			return -1;
		}
		merito_sol = (P_merito_sol)GetProcAddress(hinstLib, "merito_sol");
		if (NULL == merito_sol)
		{
			printf("No se produjo el enlace con la función solucion\n");
			return -1;
		}
	}
	else {
		printf("No se produjo el enlace con la DLL\n");
		return -1;
	}
	return 0;
}
bool inicia() {
	printf("Iniciando la ejecucion\n\n");

	double* vec;
	if (caso == 0) {
		inicia_caso0();
		double dvec[] = { 1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,0.0,20471.0,4407.0,16143.0,3737.0,42859.0,56233.0,36758.0,40779.0,251643.0,158634.0,11109.0,70628.0,8175.0,9065.0,131366.0,88.0,57988.0,39.0,7977.0,36798.0,191303.0,16.0,38310.0,0.0,32647.0,71205.0,311495.0,273578.0,725704.0,147687.0 };
		NVEC = (int)(sizeof(dvec) / sizeof(dvec[0]));
		vec = dvec;
	}
	else {
		inicia_caso1();
		double dvec[] = { 1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,0.0,20471.0,4407.0,16143.0,3737.0,42859.0,56233.0,36758.0,40779.0,251643.0,158634.0,11109.0,70628.0,8175.0,9065.0,131366.0,88.0,57988.0,39.0,7977.0,36798.0,191303.0,16.0,38310.0,0.0,32647.0,71205.0,311495.0,273578.0,725704.0,147687.0 };
		NVEC = (int)(sizeof(dvec) / sizeof(dvec[0]));
		vec = dvec;
	}

	gen.seed(semilla);
	resto = NVEC % 4;
	hbloque = NVEC - resto;
	dis_entero = uniform_int_distribution<int>{ 0, ((int)NPOB - 1) };
#pragma region MyRegion
	fopen_s(&fp, "C:/MEGA/Salidas/alge_s.log", "a");
	if (fp == NULL) {
		printf("No se pudo abrir el fichero de salida\n");
		return false;
	}
	fprintf(fp, "\n");
	fprintf(fp, "max.intentos           : %12d\n", max_intentos);
	fprintf(fp, "caso                   : %12d\n", caso);
	fprintf(fp, "nunero de hilos        : %12d\n", n_hilos);
	fprintf(fp, "modo poblacion inicical: %12d\n", modo_poblacion_inicial);
	fprintf(fp, "factor inicio          : %12.2f\n", factor_inicio);
	fprintf(fp, "factor_merito_acceso   : %12.2f\n", factor_merito_acceso);
	fprintf(fp, "sigma inicio           : %12.2f\n", sigma_inicio);
	fprintf(fp, "poblacion              : %12d\n", NPOB);
	fprintf(fp, "max.generaciones       : %12d\n", max_generaciones);
	fprintf(fp, "N.genera.para MOSTRAR  : %12d\n", gene_mostrar_evolucion);
	fprintf(fp, "tolerancia             : %12.5e\n", tolerancia);
	fprintf(fp, "error aceptable        : %12.5e\n", tol_aceptable);
	fprintf(fp, "N.genera.Ctrl PROGRESO : %12d\n", gene_control_progreso);
	fprintf(fp, "min.progreso           : %12.5e\n", min_progreso);
	fprintf(fp, "factor_mutacion        : %12.2f\n", factor_mutacion);
	fprintf(fp, "cte.recombinacion      : %12.2f %12.2f\n", recombinacion[0], recombinacion[1]);
	fprintf(fp, "pprecio min            : %12.2f\n", pprecio_min);
	fprintf(fp, "pprecio max            : %12.2f\n", pprecio_max);
	fprintf(fp, "vprecio min            : %12.2f\n", vprecio_min);
	fprintf(fp, "vprecio max            : %12.2f\n", vprecio_max);
	fprintf(fp, "control factibilidad   : %s\n", control_factibilidad ? "Si" : "No");
	fprintf(fp, "calculo AX             : %s\n", calculo_ax ? "Si" : "No");
	fprintf(fp, "fijar epsilon          : %s\n", fijar_epsilon ? "Si" : "No");
	fprintf(fp, "rango variab.inicial 0 : %12.2f\n", rango_var_cero);
	fprintf(fp, "semilla aleatorios     : %12d\n", semilla);
	fprintf(fp, "el mejor primero       : %s\n", el_mejor_primero ? "Si" : "No");
	fprintf(fp, "incluir el c.d.m.      : %s\n", usar_cdm ? "Si" : "No");
	fprintf(fp, "\n");

	printf("\n");
	printf("max.intentos           : %12d\n", max_intentos);
	printf("caso                   : %12d\n", caso);
	printf("nunero de hilos        : %12d\n", n_hilos);
	printf("modo poblacion inicical: %12d\n", modo_poblacion_inicial);
	printf("factor inicio          : %12.2f\n", factor_inicio);
	printf("factor_merito_acceso   : %12.2f\n", factor_merito_acceso);
	printf("sigma inicio           : %12.2f\n", sigma_inicio);
	printf("poblacion              : %12d\n", NPOB);
	printf("max.generaciones       : %12d\n", max_generaciones);
	printf("N.genera.para MOSTRAR  : %12d\n", gene_mostrar_evolucion);
	printf("tolerancia             : %12.5e\n", tolerancia);
	printf("error aceptable        : %12.5e\n", tol_aceptable);
	printf("N.genera.Ctrl PROGRESO : %12d\n", gene_control_progreso);
	printf("min.progreso           : %12.5e\n", min_progreso);
	printf("factor_mutacion        : %12.2f\n", factor_mutacion);
	printf("cte.recombinacion      : %12.2f %12.2f\n", recombinacion[0], recombinacion[1]);
	printf("pprecio min            : %12.2f\n", pprecio_min);
	printf("pprecio max            : %12.2f\n", pprecio_max);
	printf("vprecio min            : %12.2f\n", vprecio_min);
	printf("vprecio max            : %12.2f\n", vprecio_max);
	printf("control factibilidad   : %s\n", control_factibilidad ? "Si" : "No");
	printf("calculo AX             : %s\n", calculo_ax ? "Si" : "No");
	printf("fijar epsilon          : %s\n", fijar_epsilon ? "Si" : "No");
	printf("rango variab.inicial 0 : %12.2f\n", rango_var_cero);
	printf("semilla aleatorios     : %12d\n", semilla);
	printf("el mejor primero       : %s\n", el_mejor_primero ? "Si" : "No");
	printf("incluir el c.d.m.      : %s\n", usar_cdm ? "Si" : "No");
	printf("\n");
#pragma endregion
	printf("dimension vector: %d\n\n", NVEC);
	fprintf(fp, "dimension vector: %d\n\n", NVEC);
	double v = merito_s(vec);
	if (caso == 0) {
		printf("resultado merito (931338.2141402321): %f\n\n", v);
	}
	else {
		printf("resultado merito (127512418.44796526): %f\n\n", v);
	}
	if (inicia_cotas() == false) {
		fprintf(fp, "Error al iniciar las cotas de las variables\n");
		printf("Error al generar la poblacion\n");
		return false;
	}
	if (fija_cotas(vec, pprecio_min, pprecio_max, vprecio_min, vprecio_max) == false) {
		fprintf(fp, "Error al fijar las cotas de las variables\n");
		printf("Error al generar la poblacion\n");
		return false;
	}
	if (inicia_poblacion(factor_inicio) == false) {
		fprintf(fp, "Error al reservar memoria para la poblacion\n");
		printf("Error al reservar memoria para la poblacion\n");
		return false;
	}
	gen.seed(semilla);
	if (genera_poblacion() == false) {
		fprintf(fp, "Error al generar la poblacion\n");
		printf("Error al generar la poblacion\n");
		return false;
	}
	vant = 1.0e+99;
	generacion = 0;
	ul_generacion_cdm = 0;

	mut_ant = 0;
	fac_ant = 0;
	tpo_ini = clock();

	intentos = 0;
	mutaciones[0] = 0;
	mufactibles[0] = 0;
	hgen[0] = mt19937(semilla);
	if (el_mejor_primero) {
		hdis_entero[0] = uniform_int_distribution<int>{ 1, ((int)NPOB - 1) };
	}
	else {
		hdis_entero[0] = uniform_int_distribution<int>{ 0, ((int)NPOB - 1) };
	}
	hdis_entero_ivec[0] = uniform_int_distribution<int>{ 0, ((int)NVEC - 1) };
	hdis_double[0] = uniform_real_distribution<double>{ 0.0, 1.0 };

	fprintf(fp, "int genera mejor.merito mutaciones  factibles    ratio   dist.clonaci  tiempo  tiempo\n");
	fprintf(fp, "--- ------ ------------ ---------- ---------- ---------- ------------ ------- -------\n");
	printf("int genera mejor.merito mutaciones  factibles    ratio   dist.clonaci  tiempo  tiempo\n");
	printf("--- ------ ------------ ---------- ---------- ---------- ------------ ------- -------\n");
	if (n_hilos > 0) {
		if (PreparaMP(max_generaciones) != 0) {
			return false;
		}
	}
	else {
		res_Simulacion = avanza();
	}
	fprintf(fp, "--- ------ ------------ ---------- ---------- ---------- ------------ ------- -------\n");
	printf("--- ------ ------------ ---------- ---------- ---------- ------------ ------- -------\n");
	printf("\n");
	fprintf(fp, "\n");
	if (res_Simulacion == -2) {
		printf("++++++++++ encontrada solucion, %6d generaciones", generacion);
		fprintf(fp, "++++++++++ encontrada solucion, %6d generaciones", generacion);
	}
	else if (res_Simulacion == -3) {
		if (mejor_merito > tol_aceptable) {
			printf("---------- no progresa, solucion no aceptable, %6d generaciones", generacion);
			fprintf(fp, "---------- no progresa, solucion no aceptable, %6d generaciones", generacion);
		}
		else {
			printf("?????????? no progresa, pero la solucion puede ser aceptable, %6d generaciones", generacion);
			fprintf(fp, "?????????? no progresa, pero la solucion puede ser aceptable, %6d generaciones", generacion);
		}
	}
	else if (res_Simulacion == -5) {
		if (mejor_merito > 0.0001) {
			printf("-------- superado el maximo de generaciones, solucion no aceptable, %6d generaciones", generacion);
			fprintf(fp, "-------- superado el maximo de generaciones, solucion no aceptable, %6d generaciones", generacion);
		}
		else {
			printf("???????? superado el maximo de generaciones, pero la solucion puede ser aceptable, %6d generaciones", generacion);
			fprintf(fp, "???????? superado el maximo de generaciones, pero la solucion puede ser aceptable, %6d generaciones", generacion);
		}
	}
	else {
		fprintf(fp, "terminacion inesperada\n\n");
		printf("terminacion inesperada\n\n");
		return false;
	}
	printf("\n\n");
	fprintf(fp, "\n\n");
	unsigned t_fin = clock();

	if (sal_solucion) {
		long long mut = 0;
		long long fac = 0;
		double rfac_mut = 100. * (double)fac / mut;
		fprintf(fp, "hilo mutaciones  factibles    ratio  \n");
		fprintf(fp, "---- ---------- ---------- ----------\n");
		printf("hilo mutaciones  factibles    ratio  \n");
		printf("---- ---------- ---------- ----------\n");
		if (n_hilos > 0) {
			long long mut_t = 0;
			long long fac_t = 0;
			for (int i = 0; i < n_hilos; i++) {
				mut = mutaciones[i];
				fac = mufactibles[i];
				mut_t += mut;
				fac_t += fac;
				rfac_mut = 100. * (double)fac / mut;
				fprintf(fp, "%4d %10lld %10lld %10.2f\n", i, mut, fac, rfac_mut);
				printf("%4d %10lld %10lld %10.2f\n", i, mut, fac, rfac_mut);
			}
			rfac_mut = 100. * (double)fac_t / mut_t;
			fprintf(fp, "---- ---------- ---------- ----------\n");
			fprintf(fp, "     %10lld %10lld %10.2f\n", mut_t, fac_t, rfac_mut);
			fprintf(fp, "---- ---------- ---------- ----------\n");
			printf("---- ---------- ---------- ----------\n");
			printf("     %10lld %10lld %10.2f\n", mut_t, fac_t, rfac_mut);
			printf("---- ---------- ---------- ----------\n");
		}
		else {
			mut = mutaciones[0];
			fac = mufactibles[0];
			rfac_mut = 100. * fac / mut;
			fprintf(fp, "    %10lld %10lld %10.2f\n", mut, fac, rfac_mut);
			fprintf(fp, "---- ---------- ---------- ----------\n");
			printf("    %10lld %10lld %10.2f\n", mut, fac, rfac_mut);
			printf("---- ---------- ---------- ----------\n");
		}

		double* sol = merito_sol(vec);

		printf("datos en la solucion inicial: %4f\n", sol[0]);
		printf("merito inicial              : %12.5e\n", sol[1]);
		double v = merito_s(poblacion[ind_mejor_merito]);
		printf("merito solucion             : %12.5e\n", v);
		sol = merito_sol(poblacion[ind_mejor_merito]);
		printf("datos en la solucion        : %4f\n", sol[0]);
		printf("merito solucion             : %12.5e\n\n", sol[1]);

		fprintf(fp, "Solucion\n");
		fprintf(fp, "------------\n");
		int n = 2;
		fprintf(fp, "pf\n");
		for (int i = 0; i < NFAC; i++)	fprintf(fp, "%12.6f\n", sol[n++]);
		fprintf(fp, "py\n");
		for (int i = 0; i < NSEC; i++)	fprintf(fp, "%12.6f\n", sol[n++]);
		fprintf(fp, "pq\n");
		for (int i = 0; i < NSEC; i++)	fprintf(fp, "%12.6f\n", sol[n++]);
		fprintf(fp, "pd\n");
		for (int i = 0; i < NSEC; i++)	fprintf(fp, "%12.6f\n", sol[n++]);
		fprintf(fp, "epsilon\n");
		fprintf(fp, "%12.6f\n", sol[n++]);
		fprintf(fp, "F\n");
		fprintf(fp, "Apz\n");
		fprintf(fp, "%12.6f\n", sol[n++]);
		for (int i = 0; i < NSEC; i++) {
			for (int j = 0; j < NFAC; j++) {
				fprintf(fp, "%12.2f\n", sol[n++]);
			}
			fprintf(fp, "\n");
		}
		fprintf(fp, "E\n");
		for (int i = 0; i < NSEC; i++)	fprintf(fp, "%12.2f\n", sol[n++]);
		fprintf(fp, "M\n");
		for (int i = 0; i < NSEC; i++)	fprintf(fp, "%12.2f\n", sol[n++]);
		fprintf(fp, "D\n");
		for (int i = 0; i < NSEC; i++)	fprintf(fp, "%12.2f\n", sol[n++]);
		fprintf(fp, "pz\n");
		for (int i = 0; i < NSEC; i++)	fprintf(fp, "%12.6f\n", sol[n++]);
		fprintf(fp, "pe\n");
		for (int i = 0; i < NSEC; i++)	fprintf(fp, "%12.6f\n", sol[n++]);
		fprintf(fp, "pm\n");
		for (int i = 0; i < NSEC; i++)	fprintf(fp, "%12.6f\n", sol[n++]);
		fprintf(fp, "Yp\n");
		for (int i = 0; i < NSEC; i++)	fprintf(fp, "%12.2f\n", sol[n++]);
		fprintf(fp, "Z\n");
		for (int i = 0; i < NSEC; i++)	fprintf(fp, "%12.2f\n", sol[n++]);
		fprintf(fp, "Xg\n");
		for (int i = 0; i < NSEC; i++)	fprintf(fp, "%12.2f\n", sol[n++]);
		fprintf(fp, "Xv\n");
		for (int i = 0; i < NSEC; i++)	fprintf(fp, "%12.2f\n", sol[n++]);
		fprintf(fp, "Q\n");
		for (int i = 0; i < NSEC; i++)	fprintf(fp, "%12.2f\n", sol[n++]);
		fprintf(fp, "Td\n");
		for (int i = 0; i < NDEM; i++)	fprintf(fp, "%12.2f\n", sol[n++]);
		fprintf(fp, "Tz\n");
		for (int i = 0; i < NSEC; i++)	fprintf(fp, "%12.2f\n", sol[n++]);
		fprintf(fp, "Tm\n");
		for (int i = 0; i < NSEC; i++)	fprintf(fp, "%12.2f\n", sol[n++]);
		fprintf(fp, "Sp\n");
		for (int i = 0; i < NDEM; i++)	fprintf(fp, "%12.2f\n", sol[n++]);
		fprintf(fp, "AgE\n");
		for (int i = 0; i < NSEC; i++)	fprintf(fp, "%12.2f\n", sol[n++]);
		fprintf(fp, "AgH\n");
		for (int i = 0; i < NDEM; i++)	fprintf(fp, "%12.2f\n", sol[n++]);
		fprintf(fp, "CssE\n");
		for (int i = 0; i < NSEC; i++)	fprintf(fp, "%12.2f\n", sol[n++]);
		fprintf(fp, "CssH\n");
		for (int i = 0; i < NDEM; i++)	fprintf(fp, "%12.2f\n", sol[n++]);
		fprintf(fp, "Sg\n");
		fprintf(fp, "%12.2f\n", sol[n++]);
		fprintf(fp, "Sc\n");
		fprintf(fp, "%12.2f\n", sol[n++]);
		fprintf(fp, "ebp\n");
		fprintf(fp, "%12.6f\n", sol[n++]);
		fprintf(fp, "Xp\n");
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NSEC; j++) {
				fprintf(fp, "%12.2f\n", sol[n++]);
			}
			fprintf(fp, "\n");
		}
		fprintf(fp, "FF\n");
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NFAC; j++) {
				fprintf(fp, "%12.2f\n", sol[n++]);
			}
			fprintf(fp, "\n");
		}
		fprintf(fp, "Alp\n");
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NFAC; j++) {
				fprintf(fp, "%12.2f\n", sol[n++]);
			}
			fprintf(fp, "\n");
		}
		fprintf(fp, "X\n");
		for (int i = 0; i < NSEC; i++) {
			for (int j = 0; j < NSEC; j++) {
				fprintf(fp, "%12.2f\n", sol[n++]);
			}
			fprintf(fp, "\n");
		}
		fprintf(fp, "------------\n");
		fprintf(fp, "\n");
	}
	double tiempo = (double(t_fin - tpo_ini) / CLOCKS_PER_SEC);
	printf("------------------------------------------------------\n");
	printf("%s %3d hilos. tiempo de ejecucion %12.3f\n", calificador, n_hilos, tiempo);
	printf("------------------------------------------------------\n\n");
	fprintf(fp, "------------------------------------------------------\n");
	fprintf(fp, "%s %3d hilos. tiempo de ejecucion %12.3f\n", calificador, n_hilos, tiempo);
	fprintf(fp, "------------------------------------------------------\n\n");

	fclose(fp);
	libera_DLL(hinstLib);
	libera_cotas();
	libera_poblacion();
	printf("\n");
	system("pause");
	return true;
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
bool fija_cotas(double* vec, double pmenor, double pmayor, double vmenor, double vmayor) {
	for (int i = 0; i < NPRE_SOL; i++) {
		cotas[0][i] = vec[i] / pmenor;
		cotas[1][i] = vec[i] * pmayor;
	}
	for (int i = NPRE_SOL; i < NVEC; i++) {
		if (abs(vec[i]) < 0.00001) {
			cotas[0][i] = -rango_var_cero;
			cotas[1][i] = rango_var_cero;
		}
		else {
			cotas[0][i] = vec[i] / vmenor;
			cotas[1][i] = vec[i] * vmayor;
		}
	}
	if (fijar_epsilon) {
		cotas[0][NPRE_SOL - 1] = 1;
		cotas[1][NPRE_SOL - 1] = 1.;
	}
	for (int i = 0; i < NVEC; i++) {
		if (abs(cotas[1][i] - cotas[0][i]) < 0.000001) {
			fijo[i] = 1;
		}
		else {
			fijo[i] = 0;
		}
	}
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

	size_t const mem_hilos = sizeof(long long) * max(1, n_hilos);
	mutaciones = (long long*)malloc(mem_hilos);
	if (mutaciones == NULL) return false;
	mufactibles = (long long*)malloc(mem_hilos);
	if (mufactibles == NULL) return false;

	size_t const mem_vec = sizeof(double*) * NVEC;
	cdm = (double*)malloc(max(mem_vec, 16));
	if (cdm == NULL) return false;
	pon_cdm = (double*)malloc(max(mem_vec, 16));
	if (pon_cdm == NULL) return false;
	size_t const mem_hilos_vec = sizeof(double*) * n_hilos;
	cdm_hilo = (double**)malloc(max(mem_hilos_vec, 16));
	if (cdm_hilo == NULL) return false;
	for (int i = 0; i < n_hilos; i++) {
		cdm_hilo[i] = (double*)malloc(mem_vec);
		if (cdm_hilo[i] == NULL) return false;
	}
	return true;
}
bool genera_poblacion() {
	double semi_intervalo;
	double desplazamiento;
	double v;
	double me;
	double mejor_media = 0.;
	double mejor_min = 0.;
	double mejor_max = 0.;
	double mejor_acumulada = 0.;
	if (usar_cdm) {
		for (int i = 0; i < NVEC; i++) {
			cdm[i] = 0.;
			pon_cdm[i] = 0.;
		}
	}
	if (factor_merito_acceso < 1.) {
		mejor_media = 1.0e+99;
		mejor_min = 1.0e+99;
	}
	int contador = 0;
	int mejoras = 0;
	int rechazos = 0;
	bool aceptado;
	if (modo_poblacion_inicial == 0) {
		int i = 0;
		/*
		for (int j = 0; j < NVEC; j++) {
			if (fijo[j] == 1) {
				poblacion[i][j] = cotas[0][j];
			}
			else {
				poblacion[i][j] = cotas[0][j] + (cotas[1][j] - cotas[0][j]) / 2.;
			}
		}
		i++;
		*/
		int hasta = usar_cdm ? NPOB - 1 : NPOB;
		while (i < hasta) {
			contador++;
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
			if (factor_merito_acceso < 1.) {
				if (dis_double(gen) < factor_merito_acceso) {
					aceptado = true;
				}
				else {
					me = merito_s(poblacion[i]);
					if (me < mejor_media) {
						mejor_acumulada += me;
						mejoras++;
						mejor_media = mejor_acumulada / mejoras;
						aceptado = true;
					}
					else {
						aceptado = false;
						rechazos++;
					}
					if (aceptado) {
						if (me > mejor_max) {
							mejor_max = me;
						}
						if (me < mejor_min) {
							mejor_min = me;
						}
					}
				}
			}
			else {
				aceptado = true;
			}
			if (aceptado) {
				if (usar_cdm) {
					me = 1. / merito_s(poblacion[i]);
					for (int j = 0; j < NVEC; j++) {
						cdm[j] += me * poblacion[i][j];
						pon_cdm[j] += me;
					}
				}
				i++;
			}
		}
		if (usar_cdm) {
			i = NPOB - 1;
			for (int j = 0; j < NVEC; j++) {
				poblacion[i][j] = cdm[j] / pon_cdm[j];
			}
			if (factor_merito_acceso < 1.) {
				me = merito_s(poblacion[i]);
				if (me > mejor_max) {
					mejor_max = me;
				}
				if (me < mejor_min) {
					mejor_min = me;
				}
			}
		}
		if (factor_merito_acceso < 1.) {
			fprintf(fp, "control de acceso poblacion %8d %8d %8d  %9.3e %9.3e %9.3e\n", contador + 1, mejoras, rechazos, mejor_min, mejor_max, mejor_media);
			printf("control de acceso poblacion %8d %8d %8d  %9.3e %9.3e %9.3e\n", contador + 1, mejoras, rechazos, mejor_min, mejor_max, mejor_media);
		}
		fprintf(fp, "\n");
		printf("\n");
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
		// Latin Hypercube Sampling
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
		p = (int*)malloc(max(8, mem_p));
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
	t0 = clock();
	t1;
	tpo_parcial;
	cte_recombinacion = (recombinacion[0] + recombinacion[1]) / 2.;
	ax_cF = _mm256_set1_pd(cte_recombinacion);
	while (generacion < max_generaciones) {
		if (calculo_ax) {
			mutacion_cruze_ax(0, NPOB, 0);
		}
		else {
			mutacion_cruze(0, NPOB, 0);
		}

		// no se hacen cambios en la población hasta completada la generación
		// para poder fraccionar la población en multitarea
		seleccion();
		res_Simulacion = comprobar_final();
		if (res_Simulacion < 0) {
			return res_Simulacion;
		}
		cte_recombinacion = recombinacion[0] + dis_double(gen) * (recombinacion[1] - recombinacion[0]);
		ax_cF = _mm256_set1_pd(cte_recombinacion);
		generacion++;
	}
	if (generacion == max_generaciones) {
		return -5;
	}
	return -5;
}
void mutacion_cruze(int desde, int hasta, int hilo) {

	// exactamente igual que 'mutacion_cruzeH'

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
			mutaciones[hilo]++;
			if (es_factible) mufactibles[hilo]++;
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
			mutaciones[hilo]++;
			if (es_factible) mufactibles[hilo]++;
		}
	}
}
void mutacion_cruze_ax(int desde, int hasta, int hilo) {
	int i1;
	int i2;
	int i3;
	int j1;
	int j2;
	int j3;
	int jib;

	__m256d ax_poblacion_mj{};
	__m256d ax_poblacion_i1{};
	__m256d ax_poblacion_i2{};
	__m256d ax_resta_i1_i2{};
	__m256d ax_mutacion{};
	double* ax_pv = (double*)&ax_mutacion;
	/*
	double a1;
	double a2;
	double a3;
	double a4;
	__m256d ax_recombinar{};
	__m256d ax_azar{};
	__m256d ax_cota_in{};
	__m256d ax_cota_sp{};
	__m256d ax_menor{};
	__m256d ax_mayor{};
	double* ax_rc = (double*)&ax_recombinar;
	double* ax_mn = (double*)&ax_menor;
	double* ax_my = (double*)&ax_mayor;
	*/
	double v;
	double recombinar;
	bool es_factible;
	for (int i = desde; i < hasta; i++) {
		i1 = hdis_entero[hilo](hgen[hilo]);
		i2 = hdis_entero[hilo](hgen[hilo]);
		i3 = hdis_entero_ivec[hilo](hgen[hilo]);
		es_factible = true;
		for (int j = 0; j < hbloque; j += 4) {
			j1 = j + 1;
			j2 = j + 2;
			j3 = j + 3;
			ax_poblacion_mj = _mm256_setr_pd(poblacion[ind_mejor_merito][j], poblacion[ind_mejor_merito][j1], poblacion[ind_mejor_merito][j2], poblacion[ind_mejor_merito][j3]);
			ax_poblacion_i1 = _mm256_setr_pd(poblacion[i1][j], poblacion[i1][j1], poblacion[i1][j2], poblacion[i1][j3]);
			ax_poblacion_i2 = _mm256_setr_pd(poblacion[i2][j], poblacion[i2][j1], poblacion[i2][j2], poblacion[i2][j3]);
			ax_resta_i1_i2 = _mm256_sub_pd(ax_poblacion_i1, ax_poblacion_i2);
			ax_mutacion = _mm256_fmadd_pd(ax_resta_i1_i2, ax_F, ax_poblacion_mj);
			/*
			a1 = hdis_double[hilo](hgen[hilo]);
			a2 = hdis_double[hilo](hgen[hilo]);
			a3 = hdis_double[hilo](hgen[hilo]);
			a4 = hdis_double[hilo](hgen[hilo]);
			ax_azar = _mm256_setr_pd(a1, a2, a3, a4);
			ax_recombinar = _mm256_cmp_pd(ax_azar, ax_cF, _CMP_LT_OQ);

			if (control_factibilidad) {
				ax_cota_in = _mm256_setr_pd(cotas[0][j], cotas[0][j1], cotas[0][j2], cotas[0][j3]);
				ax_cota_sp = _mm256_setr_pd(cotas[1][j], cotas[1][j1], cotas[1][j2], cotas[1][j3]);
				ax_menor = _mm256_cmp_pd(ax_mutacion, ax_cota_in, _CMP_LT_OQ);
				ax_mayor = _mm256_cmp_pd(ax_mutacion, ax_cota_sp, _CMP_GT_OQ);
			}
			*/
			for (int ib = 0; ib < 4; ib++) {
				recombinar = hdis_double[hilo](hgen[hilo]);
				jib = j + ib;
				if (fijo[jib] == 0 && (recombinar <= cte_recombinacion || jib == i3)) {
					//if (fijo[jib] == 0 && (ax_rc[ib] != 0 || jib == i3)) {
					if (control_factibilidad) {
						/*
						if (ax_mn[ib] != 0 || ax_my[ib] != 0) {
							es_factible = false;
							break;
						}
						*/
						v = ax_pv[ib];
						if (v < cotas[0][jib] || v > cotas[1][jib]) {
							es_factible = false;
							break;
						}
					}
					descendiente[i][jib] = ax_pv[ib];
				}
				else {
					descendiente[i][jib] = poblacion[i][jib];
				}
			}
			if (!es_factible) break;
		}
		if (es_factible) {
			for (int j = hbloque; j < NVEC; j++) {
				recombinar = hdis_double[hilo](hgen[hilo]);
				if (fijo[j] == 0 && (recombinar <= cte_recombinacion || j == i3)) {
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
		}
		if (control_factibilidad) {
			factible[i] = es_factible;
			mutaciones[hilo]++;
			if (es_factible) mufactibles[hilo]++;
		}
	}
}
void mutacion_cruze_axH(int desde, int hasta, int hilo) {
	int i1;
	int i2;
	int i3;
	int j1;
	int j2;
	int j3;
	int jib;

	__m256d ax_poblacion_mj{};
	__m256d ax_poblacion_i1{};
	__m256d ax_poblacion_i2{};
	__m256d ax_resta_i1_i2{};
	__m256d ax_mutacion{};
	double* ax_pv = (double*)&ax_mutacion;
	/*
	double a1;
	double a2;
	double a3;
	double a4;
	__m256d ax_recombinar{};
	__m256d ax_menor{};
	__m256d ax_mayor{};
	__m256d ax_azar{};
	__m256d ax_cota_in{};
	__m256d ax_cota_sp{};
	double* ax_rc = (double*)&ax_recombinar;
	double* ax_mn = (double*)&ax_menor;
	double* ax_my = (double*)&ax_mayor;
	/*/
	double v;
	double recombinar;
	bool es_factible;
	for (int i = desde; i < hasta; i++) {
		i1 = hdis_entero[hilo](hgen[hilo]);
		i2 = hdis_entero[hilo](hgen[hilo]);
		i3 = hdis_entero_ivec[hilo](hgen[hilo]);
		es_factible = true;
		for (int j = 0; j < hbloque; j += 4) {
			j1 = j + 1;
			j2 = j + 2;
			j3 = j + 3;
			ax_poblacion_mj = _mm256_setr_pd(poblacion[ind_mejor_merito][j], poblacion[ind_mejor_merito][j1], poblacion[ind_mejor_merito][j2], poblacion[ind_mejor_merito][j3]);
			ax_poblacion_i1 = _mm256_setr_pd(poblacion[i1][j], poblacion[i1][j1], poblacion[i1][j2], poblacion[i1][j3]);
			ax_poblacion_i2 = _mm256_setr_pd(poblacion[i2][j], poblacion[i2][j1], poblacion[i2][j2], poblacion[i2][j3]);
			ax_resta_i1_i2 = _mm256_sub_pd(ax_poblacion_i1, ax_poblacion_i2);
			ax_mutacion = _mm256_fmadd_pd(ax_resta_i1_i2, ax_F, ax_poblacion_mj);
			/*
			a1 = hdis_double(hgen);
			a2 = hdis_double(hgen);
			a3 = hdis_double(hgen);
			a4 = hdis_double(hgen);
			ax_azar = _mm256_setr_pd(a1, a2, a3, a4);
			ax_recombinar = _mm256_cmp_pd(ax_azar, ax_cF, _CMP_LT_OQ);

			if (control_factibilidad) {
				ax_cota_in = _mm256_setr_pd(cotas[0][j], cotas[0][j1], cotas[0][j2], cotas[0][j3]);
				ax_cota_sp = _mm256_setr_pd(cotas[1][j], cotas[1][j1], cotas[1][j2], cotas[1][j3]);
				ax_menor = _mm256_cmp_pd(ax_mutacion, ax_cota_in, _CMP_LT_OQ);
				ax_mayor = _mm256_cmp_pd(ax_mutacion, ax_cota_sp, _CMP_GT_OQ);
			}
			*/
			for (int ib = 0; ib < 4; ib++) {
				recombinar = hdis_double[hilo](hgen[hilo]);
				jib = j + ib;
				if (fijo[jib] == 0 && (recombinar <= cte_recombinacion || jib == i3)) {
					//if (fijo[jib] == 0 && (ax_rc[ib] != 0 || jib == i3)) {
					if (control_factibilidad) {
						/*
						if (ax_mn[ib] != 0 || ax_my[ib] != 0) {
							es_factible = false;
							break;
						}
						/*/
						v = ax_pv[ib];
						if (v < cotas[0][jib] || v > cotas[1][jib]) {
							es_factible = false;
							break;
						}
					}
					descendiente[i][jib] = ax_pv[ib];
				}
				else {
					descendiente[i][jib] = poblacion[i][jib];
				}
			}
			if (!es_factible) break;
		}
		if (es_factible) {
			for (int j = hbloque; j < NVEC; j++) {
				recombinar = hdis_double[hilo](hgen[hilo]);
				if (fijo[j] == 0 && (recombinar <= cte_recombinacion || j == i3)) {
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
		}
		if (control_factibilidad) {
			factible[i] = es_factible;
			mutaciones[hilo]++;
			if (es_factible) mufactibles[hilo]++;
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
void seleccionH(int hilo, int desde, int hasta) {
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
		calificador = "++++++++++";
		muestra(distancia_clonacion());
		return -2;
	}
	if (generacion > 0 && (generacion % gene_control_progreso == 0)) {
		if ((vant - mejor_merito) < min_progreso) {
			if (mejor_merito < tol_aceptable) {
				calificador = "??????????";
				muestra(distancia_clonacion());
				return -3;
			}
			intentos++;
			if (intentos < max_intentos) {
				genera_poblacion();
				vant = 1.0e+99;
			}
			else {
				calificador = "----------";
				muestra(distancia_clonacion());
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
						calificador = "----------";
						muestra(dist);
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
	if (generacion % gene_mostrar_evolucion == 0) {
		// la primera vez que pase por aquí (generacion == 0) será al terminar el cálculo de toda la
		// población una sola vez (la primera), luego será cada 'gene_mostrar_evolucion' generaciones
		muestra(distancia_clonacion());
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
void muestra(double clonacion) {
	long long mut = 0;
	long long fac = 0;
	if (n_hilos == 0) {
		mut = mutaciones[0];
		fac = mufactibles[0];
	}
	else {
		for (int i = 0; i < n_hilos; i++) {
			mut += mutaciones[i];
			fac += mufactibles[i];
		}
	}
	long long mut_p = mut - mut_ant;
	long long fac_p = fac - fac_ant;
	double rfac_mut = 100. * (double)fac_p / (mut_p != 0 ? mut_p : 1.);
	t1 = clock();
	tpo_parcial = (double(t1 - t0) / CLOCKS_PER_SEC);
	tpo_total = (double(t1 - tpo_ini) / CLOCKS_PER_SEC);
	fprintf(fp, "%3d %6d %12.5e %10lld %10lld %10.2f %12.3e %7.2f %7.2f\n", intentos + 1, generacion, mejor_merito, mut_p, fac_p, rfac_mut, clonacion, tpo_parcial, tpo_total);
	printf("%3d %6d %12.5e %10lld %10lld %10.2f %12.3e %7.2f %7.2f\n", intentos + 1, generacion, mejor_merito, mut_p, fac_p, rfac_mut, clonacion, tpo_parcial, tpo_total);
	t0 = t1;
	mut_ant = mut;
	fac_ant = fac;
}

void mejor_primero(int ind_mejor_merito) {
	double* p = poblacion[0];
	poblacion[0] = poblacion[ind_mejor_merito];
	poblacion[ind_mejor_merito] = p;
	double me = merito_individuo[0];
	merito_individuo[0] = merito_individuo[ind_mejor_merito];
	merito_individuo[ind_mejor_merito] = me;
	ind_mejor_merito = 0;
}
bool libera_DLL(HINSTANCE hinstLib) {
	bool res = FreeLibrary(hinstLib);
	if (!res) printf("No se pudo liberar la DLL\n");
	return res;
}
bool libera_cotas() {
	bool res = false;
	if (cotas != NULL) {
		for (int i = 0; i < 2; i++) {
			free(cotas[i]);
			res = sizeof(cotas[i]) == sizeof(double);
			if (!res) {
				// No se pudo liberar el individuo
				break;
			}
		}
		if (res) {
			free(cotas);
			res = sizeof(cotas) == sizeof(double);
			if (!res) {
				// No se pudo liberar las cotas
			}
		}
	}
	if (res && fijo != NULL) {
		free(fijo);
		res = sizeof(fijo) == sizeof(double);
		if (!res) {
			// No se pudo liberar vector de fijos
		}
	}
	return res;
}
bool libera_poblacion() {
	bool res = false;
	if (poblacion != NULL) {
		for (int i = 0; i < NVEC; i++) {
			free(poblacion[i]);
			res = sizeof(poblacion[i]) == sizeof(double);
			if (!res) {
				// No se pudo liberar el individuo
				break;
			}
		}
		if (res) {
			free(poblacion);
			res = sizeof(poblacion) == sizeof(double);
			if (!res) {
				// No se pudo liberar la poblacion
			}
		}
	}
	if (res && descendiente != NULL) {
		res = false;
		for (int i = 0; i < NVEC; i++) {
			free(descendiente[i]);
		}
		free(descendiente);
		res = sizeof(descendiente) == sizeof(double);
		if (!res) {
			// No se pudo liberar descendientes
		}
	}
	if (res && merito_individuo != NULL) {
		free(merito_individuo);
		res = sizeof(merito_individuo) == sizeof(double);
		if (!res) {
			// No se pudo liberar vector de meritos
		}
	}
	if (res && factible != NULL) {
		free(factible);
		res = sizeof(factible) == sizeof(double);
		if (!res) {
			// No se pudo liberar vector de factibilidad
		}
	}
	if (res && mutaciones != NULL) {
		free(mutaciones);
		res = sizeof(mutaciones) == sizeof(double);
	}
	if (res && mufactibles != NULL) {
		free(mufactibles);
		res = sizeof(mufactibles) == sizeof(double);
	}
	if (res && cdm != NULL) {
		free(cdm);
		res = sizeof(cdm) == sizeof(double);
	}
	if (res && pon_cdm != NULL) {
		free(pon_cdm);
		res = sizeof(pon_cdm) == sizeof(double);
	}
	if (res && cdm_hilo != NULL) {
		for (int i = 0; i < n_hilos; i++) {
			free(cdm_hilo[i]);
			res = sizeof(cdm_hilo[i]) == sizeof(double);
		}
		free(cdm_hilo);
		res = sizeof(cdm_hilo) == sizeof(double);
	}
	return res;
}
void inicia_caso0() {
	OPCIONES opciones{
		0,
		1.0,
		0.0,
		-0.5,
		false,
		true,
		0.0,
		1,
		0,
		false,
		0,
		{0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0},
		{0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0},
		{0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1000.0,0.0,0.0,0.0},
		false,
		0
	};
	OPCIONES op = recibe_opciones(opciones);
	DATOS datos{
		{1.0,1.0,},
		{1.0,1.0,1.0,1.0,1.0,1.0,},
		{1.0,1.0,1.0,1.0,1.0,1.0,},
		{32647.0,71205.0,311495.0,273578.0,725704.0,147687.0,},
		{1.0,1.0,1.0,1.0,1.0,1.0,},
		{1.0,1.0,1.0,1.0,1.0,1.0,},
		1.0,
		{20471.0,4407.0,16143.0,3737.0,42859.0,56233.0,36758.0,40779.0,251643.0,158634.0,11109.0,70628.0,},
		{8175.0,9065.0,131366.0,88.0,57988.0,39.0,},
		{7977.0,36798.0,191303.0,16.0,38310.0,0.0,},
		{32647.0,71205.0,311495.0,273578.0,725704.0,147687.0,},
		{378983.0,334418.0,0.0,0.0,},
		{0.0,0.0,0.0,0.0,},
		{0.0,96804.0,},
		{0.0,0.01618823165784492,0.0,0.009487489895610537,0.02342987623673422,0.03661325355518216,},
		{0.0,0.0,0.0,0.0,0.0,0.0,},
		67683.0,
		371575.55555555556,
	};
	DATOS da = recibe_datos(datos);
	PARAMETROS para{
		{0.05501710376282782,0.034706385404789056,0.21987837324211326,0.004869821360699354,0.09454580007601672,0.0,1.287846591713995e-05,0.5530914757434094,0.055222861852696106,0.008435395175726668,0.12721348632950844,0.0,0.059189542728372554,0.04591904787534019,0.4594385253861688,0.004057668502055745,0.19951373499727382,0.0,8.89573043616153e-05,0.010013498304009653,0.21030667063751446,0.37882661447838145,0.10087371543718647,0.0,0.003834256190236607,0.02828420491017004,0.08990736414928996,0.0290955633758041,0.28178880352961666,0.0,0.0014261710585631736,0.02804803081840908,0.08962747428384082,0.01495840334412524,0.19599196754231385,0.0,},
		{0.5909825161535538,0.2560239024327422,0.23188148051078886,0.29989054383854635,0.5670898078448826,0.6699479529527478,},
		{0.822855535010853,0.17714446498914704,0.8120221327967807,0.18797786720321932,0.432517256690752,0.567482743309248,0.47407044378812696,0.5259295562118731,0.6133490300455546,0.3866509699544454,0.13591152109815627,0.8640884789018437,},
		{1.5952584588412413,1.6213798250600775,1.9818118160085796,1.9973112346965698,1.948824611096008,1.4880577092152902,},
		{2.3100490069496487,2.4527633453585866,2.0198457348829635,13.954623561692186,2.5959343814410056,13.01323452805016,},
		{0.6664864078636457,0.7370266001563356,0.606279058126731,0.9823810219338371,0.7796199605472663,0.9840095573620194,},
		{0.33351359213635445,0.2629733998436644,0.393720941873269,0.01761897806616286,0.22038003945273368,0.015990442637980478,},
		{1.5,1.5,1.5,1.5,1.5,1.5,},
		{0.21763636440094702,0.2150737572827569,},
		{0.00958202872620645,0.0,0.008419064658814174,0.0,0.0,0.0,},
		{0.0,0.0,},
		{0.15809902144796545,0.18514730796248088,},
		{0.1484002722940776,0.364998662028365,0.30615474899080614,0.3105029549523039,0.2727221150573017,0.30092881010364164,},
		{0.0628973320814071,0.0,},
		{0.015535917901938427,0.01756622751097889,0.040286517261471574,0.04897292990551187,0.05979863935047092,0.17420597516495226,},
		{0.04580007601672368,0.0,0.003964065999124817,0.0,0.0,0.0,},
		0.1330799441261615,
		{0.0,0.0,0.041058303608437006,0.0,0.1092163719474818,0.8497253244440812,},
		{0.003313876705851662,0.001259517714770189,0.2271860173153115,0.5946880146087751,0.17355257365529161,0.0,},
		{0.019131922595606587,0.0356337360982473,0.2068759912989581,0.008877796553048782,0.7250546171847935,0.004425936269345796,0.01913504762232824,0.035634935671104526,0.2068858614216083,0.008887204836292864,0.7250305712957062,0.004426379152959818,},
		{0.019131922595606587,0.0356337360982473,0.2068759912989581,0.008877796553048782,0.7250546171847935,0.004425936269345796,0.01913504762232824,0.035634935671104526,0.2068858614216083,0.008887204836292864,0.7250305712957062,0.004426379152959818,},
		{0.5,0.5,},
		{0.07709294001356609,0.10521217055826942,0.2535072281684367,0.052515547168923,0.4745922717676392,0.037079842323165656,0.07709646674393261,0.10521016242595511,0.25350416993002384,0.05254147935050752,0.4745673559566882,0.037080365592892676,},
		{1.7944905717330883,1.9478978310542243,1.9710081708861555,1.0152941027369462,1.4364801655008403,0.9999999999999998,},
		{0.33079418293646096,0.4182260796836316,0.439359384589728,0.00758945822923522,0.18683386614151357,0.0,},
		{0.669205817063539,0.5817739203163684,0.560640615410272,0.9924105417707648,0.8131661338584865,1.0,},
		{0.5,0.5,0.5,0.5,0.5,0.5,},
	};
	PARAMETROS pa = recibe_parametros(para);
}
void inicia_caso1() {
	// salarios
	OPCIONES opciones{
		0,
		1.0,
		1.05,
		-0.5,
		false,
		true,
		0.0,
		1,
		0,
		false,
		0,
		{0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,},
		{0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,},
		{0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,},
		false,
		0
	};
	OPCIONES op = recibe_opciones(opciones);
	DATOS datos{
		{1.0,1.0,},
		{1.0,1.0,1.0,1.0,1.0,1.0,},
		{1.0,1.0,1.0,1.0,1.0,1.0,},
		{32647.0,71205.0,311495.0,273578.0,725704.0,147687.0,},
		{1.0,1.0,1.0,1.0,1.0,1.0,},
		{1.0,1.0,1.0,1.0,1.0,1.0,},
		1.0,
		{20471.0,4407.0,16143.0,3737.0,42859.0,56233.0,36758.0,40779.0,251643.0,158634.0,11109.0,70628.0,},
		{8175.0,9065.0,131366.0,88.0,57988.0,39.0,},
		{7977.0,36798.0,191303.0,16.0,38310.0,0.0,},
		{32647.0,71205.0,311495.0,273578.0,725704.0,147687.0,},
		{378983.0,334418.0,0.0,0.0,},
		{0.0,0.0,0.0,0.0,},
		{0.0,96804.0,},
		{0.0,0.01618823165784492,0.0,0.009487489895610537,0.02342987623673422,0.03661325355518216,},
		{0.0,0.0,0.0,0.0,0.0,0.0,},
		67683.0,
		371575.55555555556,
	};
	DATOS da = recibe_datos(datos);
	PARAMETROS para{
		{0.05501710376282782,0.034706385404789056,0.21987837324211326,0.004869821360699354,0.09454580007601672,0.0,1.287846591713995e-05,0.5530914757434094,0.055222861852696106,0.008435395175726668,0.12721348632950844,0.0,0.059189542728372554,0.04591904787534019,0.4594385253861688,0.004057668502055745,0.19951373499727382,0.0,8.89573043616153e-05,0.010013498304009653,0.21030667063751446,0.37882661447838145,0.10087371543718647,0.0,0.003834256190236607,0.02828420491017004,0.08990736414928996,0.0290955633758041,0.28178880352961666,0.0,0.0014261710585631736,0.02804803081840908,0.08962747428384082,0.01495840334412524,0.19599196754231385,0.0,},
		{0.5909825161535538,0.2560239024327422,0.23188148051078886,0.29989054383854635,0.5670898078448826,0.6699479529527478,},
		{0.822855535010853,0.17714446498914704,0.8120221327967807,0.18797786720321932,0.432517256690752,0.567482743309248,0.47407044378812696,0.5259295562118731,0.6133490300455546,0.3866509699544454,0.13591152109815627,0.8640884789018437,},
		{1.5952584588412413,1.6213798250600775,1.9818118160085796,1.9973112346965698,1.948824611096008,1.4880577092152902,},
		{2.3100490069496487,2.4527633453585866,2.0198457348829635,13.954623561692186,2.5959343814410056,13.01323452805016,},
		{0.6664864078636457,0.7370266001563356,0.606279058126731,0.9823810219338371,0.7796199605472663,0.9840095573620194,},
		{0.33351359213635445,0.2629733998436644,0.393720941873269,0.01761897806616286,0.22038003945273368,0.015990442637980478,},
		{1.5,1.5,1.5,1.5,1.5,1.5,},
		{0.21763636440094702,0.2150737572827569,},
		{0.00958202872620645,0.0,0.008419064658814174,0.0,0.0,0.0,},
		{0.0,0.0,},
		{0.15809902144796545,0.18514730796248088,},
		{0.1484002722940776,0.364998662028365,0.30615474899080614,0.3105029549523039,0.2727221150573017,0.30092881010364164,},
		{0.0628973320814071,0.0,},
		{0.015535917901938427,0.01756622751097889,0.040286517261471574,0.04897292990551187,0.05979863935047092,0.17420597516495226,},
		{0.04580007601672368,0.0,0.003964065999124817,0.0,0.0,0.0,},
		0.1330799441261615,
		{0.0,0.0,0.041058303608437006,0.0,0.1092163719474818,0.8497253244440812,},
		{0.003313876705851662,0.001259517714770189,0.2271860173153115,0.5946880146087751,0.17355257365529161,0.0,},
		{0.019131922595606587,0.0356337360982473,0.2068759912989581,0.008877796553048782,0.7250546171847935,0.004425936269345796,0.01913504762232824,0.035634935671104526,0.2068858614216083,0.008887204836292864,0.7250305712957062,0.004426379152959818,},
		{0.019131922595606587,0.0356337360982473,0.2068759912989581,0.008877796553048782,0.7250546171847935,0.004425936269345796,0.01913504762232824,0.035634935671104526,0.2068858614216083,0.008887204836292864,0.7250305712957062,0.004426379152959818,},
		{0.5,0.5,},
		{0.07709294001356609,0.10521217055826942,0.2535072281684367,0.052515547168923,0.4745922717676392,0.037079842323165656,0.07709646674393261,0.10521016242595511,0.25350416993002384,0.05254147935050752,0.4745673559566882,0.037080365592892676,},
		{1.7944905717330883,1.9478978310542243,1.9710081708861555,1.0152941027369462,1.4364801655008403,0.9999999999999998,},
		{0.33079418293646096,0.4182260796836316,0.439359384589728,0.00758945822923522,0.18683386614151357,0.0,},
		{0.669205817063539,0.5817739203163684,0.560640615410272,0.9924105417707648,0.8131661338584865,1.0,},
		{0.5,0.5,0.5,0.5,0.5,0.5,},
	};
	PARAMETROS pa = recibe_parametros(para);
}
/*
*********************
Multi tarea
*********************
*/
bool Arranque() {
	for (int i = 1; i < n_hilos; i++) {
		hgen[i] = mt19937(semilla + i);
		if (el_mejor_primero) {
			hdis_entero[i] = uniform_int_distribution<int>{ 1, ((int)NPOB - 1) };
		}
		else {
			hdis_entero[i] = uniform_int_distribution<int>{ 0, ((int)NPOB - 1) };
		}
		hdis_entero_ivec[i] = uniform_int_distribution<int>{ 0, ((int)NVEC - 1) };
		hdis_double[i] = uniform_real_distribution<double>{ 0.0, 1.0 };
		mutaciones[i] = 0;
		mufactibles[i] = 0;
	}
	t0 = clock();
	cte_recombinacion = (recombinacion[0] + recombinacion[1]) / 2.;
	ax_cF = _mm256_set1_pd(cte_recombinacion);
	for (int i = 0; i < n_hilos; i++) {
		for (int j = 0; j < NVEC; j++) {
			cdm_hilo[i][j] = 0.;
		}
	}
	CANCELADO = false;
	return true;
}
int PreparaMP(int hasta) {
	// Comprobar la relación entre el número de hilos y el de la población

	int bloques = NPOB / n_hilos;
	if (bloques * n_hilos != NPOB) {
		printf("Cancelado. El numero de individuos debe ser multiplo del numero de hilos\n");
		fprintf(fp, "Cancelado. El numero de individuos debe ser multiplo del numero de hilos\n");
		return-1;
	}
	if (!Arranque()) return-1;
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

			if (el_mejor_primero && ind_mejor_merito != 0) {
				mejor_primero(ind_mejor_merito);
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
			ax_cF = _mm256_set1_pd(cte_recombinacion);
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
	if (calculo_ax) {
		mutacion_cruze_axH(desde, hasta, hilo);
	}
	else {
		mutacion_cruzeH(desde, hasta, hilo);
	}
	seleccionH(hilo, desde, hasta);
}
