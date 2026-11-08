#pragma once
#include "cuda_runtime.h"
#include <curand_kernel.h>
using namespace std;

//#define signo(x) ((x) < 0.0 ? -1. : 1.)

// si la aplicación distinge +0 de -0 (lo cual es normal) copysign dará resultados distintos que la macro 'signo(x) ((x) < 0.0 ? -1. : 1.)'
// copysign no incrementa el tiempo de cálculo
#define signo(x) copysign(1.0, (x))

/*
Propiedades del proyecto: C/C++: Command line (opciones adicionales)
-Xptxas -0.3 maximiza la optimización, no he encontyrado ninguna mejora
-Xptxas -maxrregcount=N establece el número de registros por hilo a N, lo que determina la ocupación y el spilling
*/

#define MRG32k3a

#ifdef MRG32k3a
#define azar curandStateMRG32k3a
#else
#define azar curandStatePhilox4_32_10
#endif

// tipo de memoria para las matrices 2D: 'cotas', 'poblacion' y 'descendiente'
// si no se especifica DINAMICA será estática
#define DINAMICA

// no aporta nada y es ineficiente
//#define REGULA

// si se define BLOQUES_VARIABLES, el número de bloques del kernel 'selecciona' se ajusta al número de
// individuos factibles, lo que puede mejorar la eficiencia (al principio) y en cualquier caso no
// supone un coste adicional de tiempo
#define BLOQUES_VARIABLES

#ifdef BLOQUES_VARIABLES
const int MIN_RATIO_FACTIBLES = 99;
#endif

// solo vale la pena para MEGA4, MEGA5, MEGA6 y MEGA8
#define MEGA6

const int hNFAC = 2;
__device__ const int NFAC = 2;

#if defined(MEGA4)
const int hNDEM = 2;
const int hNSEC = 6;
__device__ const int NDEM = 2;
__device__ const int NSEC = 6;
const int hMAX_POB = 5120;
#elif defined(MEGA5)
const int hNDEM = 3;
const int hNSEC = 63;
const int hMAX_POB = 30720;
__device__ const int NDEM = 3;
__device__ const int NSEC = 63;
#elif defined(MEGA6)
const int hNDEM = 2;
const int hNSEC = 31;
__device__ const int NDEM = 2;
__device__ const int NSEC = 31;
const int hMAX_POB = 10240;
#elif defined(MEGA8)
const int NDEM = 2;
const int NSEC = 32;
__device__ const int NDEM = 2;
__device__ const int NSEC = 32;
const int hMAX_POB = 10240;
#endif

//__managed__ se usa para tener el mismo nombre de variable en el host y el device y que compartan su valor de forma automática, pero
// es menos eficiente que dos nombres de variable distintos cuyos valores se coordinan manualmente cuando es necesario
//__managed__ double Micro = 1.0e-06;
const double hMicro = 1.0e-06;
__device__ const double Micro = 1.0e-06;

const double hDeciMicro = 1.0e-07;
const double mega_byte = 1024.0 * 1024.0; // 1048576.0

typedef struct
{
public:
	int OR_PRE_EXCLUIDO;
	double PRECIO_F_EXCLUIDO;
	double VALOR_F_TRA;
	double ALFA_PHILLIPS;
	bool GE_INCLUYE_XP;
	bool GE_INCLUYE_AgH;
	bool GE_IMPUESTOS_AgH;
	bool FF_ENDOGENA;
	double ALP_FACTOR;
	int INDICE_F_TRA;
	int UTILIDAD_DEMANDA;
	bool DEM_ESENCIALES;
	int DEM_ADICIONAL_TIPO;
	double DEM_ADICIONAL[NDEM][NSEC];
	double CON_ESENCIALES[NDEM][NSEC];
	double AYD_ADICIONAL[NDEM][NSEC];
	bool RENTA_FICTICIA;
	int MODO_PSEUDOIMPTOS;
	int OPT_DESVIOS;
	bool EQ_BAL_PAGOS;
} OPCIONES;

typedef struct
{
public:
	double pF0[NFAC];
	double pY0[NSEC];
	double pQ0[NSEC];
	double pD0[NSEC];
	double pWm[NSEC];
	double pWe[NSEC];
	double epsilon0;
	double F0[NSEC][NFAC];
	double E0[NSEC];
	double M0[NSEC];
	double D0[NSEC];
	double FF0[NDEM][NFAC];
	double Alp0[NDEM][NFAC];
	double PssH0[NDEM];
	double tauz[NSEC];
	double taum[NSEC];
	double Tg0;
	double Ti0;
	double Te0;
	double Sf0;
	double Fue;
	double PobAct;
	double Z0[NSEC];
	double Ajc0[NSEC];
	double Aji0[NSEC];
} DATOS;

typedef struct
{
public:
	double ax[NSEC][NSEC];
	double ay[NSEC];
	double beta[NSEC][NFAC];
	double b[NSEC];
	double teta[NSEC];
	double xie[NSEC];
	double xid[NSEC];
	double phi[NSEC];
	double taud[NDEM];
	double cage[NSEC];
	double cagh[NDEM];
	double ssp[NDEM];
	double ctzsse[NSEC];
	double ctzssh[NDEM];
	double ctzssez[NSEC];
	double ctzagez[NSEC];
	double ssg;
	double mu[NSEC];
	double landa[NSEC];
	double alfa[NDEM][NSEC];
	double alfa_esen[NDEM][NSEC];
	double eta_ces[NDEM];
	double alfa_ces[NDEM][NSEC];
	double gamma[NSEC];
	double deltam[NSEC];
	double deltad[NSEC];
	double eta[NSEC];
	double tai;
} PARAMETROS;

#pragma region Merito

__device__ double merito_s(double* vec_opt);
__device__ double* merito_sol(double* vec_opt);
__device__ void produccion_factor_compuesto_Y(double* Y, double F[NSEC][NFAC], double beta[NSEC][NFAC], double* b);
__device__ void restriccion_produccion_bruta_Z(double* Z, double* teta, double* xie, double* xid, double* E, double* D, double* phi);
__device__ void consumo_intermedio_X(double X[NSEC][NSEC], double* Z, double ax[NSEC][NSEC]);
__device__ void utilizacion_factor_compuesto_Y(double* Y, double* Z, double* ay);
__device__ void uso_optimo_factores_F(double F[NSEC][NFAC], double beta[NSEC][NFAC], double* pf, double* py, double* Ypd);
__device__ void coste_unitario_produccion_pz(double* pz, double* ay, double* py, double ax[NSEC][NSEC], double* pq, double Ajc[NSEC], double Z0[NSEC]);
__device__ void aportacion_factores_FF(double FF[NDEM][NFAC], double FF0[NDEM][NFAC], double F[NSEC][NFAC]);
__device__ void impuestos_directos_Td(double* Td, double* taud, double* pf, double FF[NDEM][NFAC], double Alp[NDEM][NFAC], double* PssH0, double AgH[NDEM]);
__device__ void impuestos_produccion_Tz(double* Tz, double* tauz, double* pz, double* Z);
__device__ void aranceles_importacion_Tm(double* Tm, double* taum, double* pm, double* M);
__device__ void ahorro_hogares_Sp(double* Sp, double* ssp, double* pf, double FF[NDEM][NFAC], double* PssH0);
__device__ double impuestos_directos_Ti(double tai, double* pf, double FF[NDEM][NFAC], int INDICE_F_TRA);
__device__ void ayudas_AgE_AgH(double* AgE, double* AgH, double* cage, double* cagh, double* Td, double* Tz, double* Tm, double Tg, double Ti, double Te, double* AYD_ADI_DEM);
__device__ void seguridad_social_empresas_CssE(double* CssE, double* ctzsse, double* pf, double F[NSEC][NFAC], int INDICE_F_TRA);
__device__ void seguridad_social_hogares_CssH(double* CssH, double* ctzssh, double* pf, double FF[NDEM][NFAC], double Alp[NDEM][NFAC], int INDICE_F_TRA);
__device__ double gobierno_Sg_Xg(double* Xg, double ssg, double* mu, double* pq, double* Td, double* Tz, double* Tm, double Tg, double Ti, double Te, double* AgE, double* AgH, double* PssH0, double* CssH, double* CssE, double Fue);
__device__ double ahorro_exterior_Sf(double* M, double* E, double* pm, double* pe);
__device__ void demanda_inversion_Xv(double* Xv, double* landa, double* pq, double* Sp, double Sg, double Sc, double epsilon, double Sf, double Ti, double Te);
__device__ void demanda_maxima_utilidad_StoneGeary_Xp(double Xp[NDEM][NSEC], double alfa_esen[NDEM][NSEC], double CON_ESENCIALES[NDEM][NSEC], double* pq, double* pf, double FF[NDEM][NFAC], double* Sp, double* Td, double* CssH, double* AgH, double* PssH0, int DEM_ADICIONAL_TIPO, double DEM_ADICIONAL[NDEM][NSEC], bool RENTA_FICTICIA);
__device__ void demanda_maxima_utilidad_CobbDouglas_Xp(double Xp[NDEM][NSEC], double alfa[NDEM][NSEC], double* pq, double* pf, double FF[NDEM][NFAC], double* Sp, double* Td, double* CssH, double* AgH, double* PssH0, int DEM_ADICIONAL_TIPO, double DEM_ADICIONAL[NDEM][NSEC], bool RENTA_FICTICIA);
__device__ void demanda_maxima_utilidad_CES_Xp(double Xp[NDEM][NSEC], double* eta_ces, double alfa_ces[NDEM][NSEC], double* pq, double* pf, double FF[NDEM][NFAC], double* Sp, double* Td, double* CssH, double* AgH, double* PssH0, int DEM_ADICIONAL_TIPO, double DEM_ADICIONAL[NDEM][NSEC], bool RENTA_FICTICIA);
__device__ void produccion_armington_Q(double* Q, double* gamma, double* deltam, double* deltad, double* M, double* D, double* eta);
__device__ void importacion_local_maxima_utilidad_armington_MD(double* M, double* Da, double* gamma, double* deltam, double* deltad, double* pq, double* pm, double* pd, double* Q, double* eta, double* taum);
__device__ void produccion_para_exportacion_local_ED(double* E, double* Dt, double* teta, double* xie, double* xid, double* pz, double* pe, double* pd, double* Z, double* phi, double* tauz, double* CssE, double* AgE, double Apz, double* ctzssez, double* ctzagez, int MODO_PSEUDOIMPTOS);
__device__ double equilibrio_balance_pagos_moneda_extranjera(double* pWe, double* E, double* pWm, double* M, double Sf);
__device__ double precio_factor_trabajo_pFL(int INDICE_F_TRA, double PobAct, double alfa, double pF0L, double F0[NSEC][NFAC], double F[NSEC][NFAC]);
#pragma endregion

#pragma region Genetico

static __global__ void kernelIni(
	int* pro_pvec,
	double* pro_me_sol,
	double* pro_VEC_OPT_E,
	double* pro_AYD_ADI_DEM,
	double* pro_desvios_bloque,
	OPCIONES* pro_opciones,
	DATOS* pro_datos,
	PARAMETROS* pro_parametros
);
static __global__ void kernelIniGene(
	int* pro_fijo,
	int* pro_factible,
	double* pro_merito_individuo,
	double* pro_cotas,
	double* pro_poblacion,
	double* pro_descendiente
);
static __global__ void kernelConstantes();
static __global__ void kernelPoblacionAdevice(double* pro_poblacion);
static __global__ void kernel_inicia_estados_azar(azar* state, unsigned long semilla);
__global__ void kernel_mutacion_cruze(azar* estado_gen_azar);
__global__ void kernel_mutacion_cruze_1(azar* estado_gen_azar);
__global__ void kernel_seleccion();
__global__ void kernel_seleccion_1();
__device__ bool planoA2D(double* fte, double**& dest, int fils, int cols);
__global__ void kernel_merito_s_todo(double* vec_opt_todo, double* res, int hNIF_K);
__global__ void kernel_merito_s(double* vec_opt, double* res);
__global__ void kernel_sol_mejor_merito();

bool hllama_merito_s_todo(double** pobla, int bloques, int hilos);
double hllama_merito_s(double* vec_opt);
bool hllama_sol_mejor_merito();
bool copiaPoblacionAlDevice();
double* soluciona(double* par, double* cotasInf, double* cotasSup, double* vec, int extendida, const char* senda);
static bool copiaVectorIntHostDevice(int* fte, int ta, int*& des);
static bool copiaVectorDoubleHostDevice(double* fte, int ta, double*& des);
//void imprime(const char* f, ...);
void imprime_error(const char* rot);
void cancelar(int sig);
int parametros_alge(double* par);
bool inicia_cotas();
bool fija_cotas(double* cotasInf, double* cotasSup);
bool inicia_poblacion();
static bool genera_poblacion(double* vec_central);
double diferencia_relativa(double a, double b);
int resuelve();
void resuelveHaTerminado();
bool muestra_evolucion(const char* rotulo);
int comprobar_final();
bool salida_solucion(char* ficherov, char* fichero);
void fin_soluciona();
void aplana(double** fte, int fils, int cols, double*& des);
bool copiaIniGPU();
bool copiaGeneticoGPU();
#pragma endregion
bool hllama_merito_s_todo(double** pobla, int bloques, int hilos);
bool tarjeta(); 
void rtrim_string(char* cadena, char caracter);
bool crear_carpeta_si_no_existe(char* cadena);
int main(int argc, char* argv[]);
