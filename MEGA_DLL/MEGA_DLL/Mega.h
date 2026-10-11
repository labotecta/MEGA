#pragma once
#define MEGA_DLL_API __declspec(dllexport)
#include <Windows.h>
#include <random>

using namespace std;

/*
Sobre la reproducibilidad de los resultados.
Solo se ha conseguido en mono proceso.
Con multiproceso no ha sido posible con ninguno de los dos generadores de números aleatorios que se han probado, ni con 'minstd_rand' ni con 'mt19937'
*/

/*
para disponer de una DLL para cada modelo, hay que cambiar el '#define' siguiente antes de compilar la solución
además, hay que cambiar el nombre en 'propiedades' de la solución MEGA_DLL: 'general->Nombre de destino' y una vez compilada la solución copiar
desde la capeta 'C:\MEGA\MEGA_DLL\x64\Release' a otra carpeta, porque si se vuelve a compilar la solución, se sobreescribirá la DLL y se perderá la DLL anterior
*/

#define MEGA4
const int NFAC = 2;

#ifdef MEGA0
const int NDEM = 1;
const int NSEC = 2;
#elif defined(MEGA1)
const int NDEM = 2;
const int NSEC = 2;
#elif defined(MEGA2)
// es idéntica a MEGA1
const int NDEM = 2;
const int NSEC = 2;
#elif defined(MEGA3)
const int NDEM = 3;
const int NSEC = 2;
#elif defined(MEGA4)
const int NDEM = 2;
const int NSEC = 6;
#elif defined(MEGA5)
const int NDEM = 3;
const int NSEC = 63;
#elif defined(MEGA6)
const int NDEM = 2;
const int NSEC = 31;
#elif defined(MEGA8)
const int NDEM = 2;
const int NSEC = 32;
#endif

/*
------------------------------------------------------------------------------------------------------------
Opciones de compilación, no se trata de opciones en tiempo de ejecución.
La mayoría son inútiles, pero se mantienen para que el olvido no haga que en el futuro se repita la historia
------------------------------------------------------------------------------------------------------------
*/
// no define la matriz Xr em merito_s para ahorrar memoria, es incompatible con CONSUMO_INTERMEDIO_AX y CONSUMO_INTERMEDIO_INDESADO
//#define SIN_XR

// RAND1: Mejor + F * (I2 - I1)
// en el libro esta es la que se usa y denomina best1bin
#define RAND1

// RAND2: I0 + F * (I2 - I1) es poco eficiente, no se ajusta al Monte Carlo de aproximación a la solución que se describe en el anexo del libro
// para activar RAND2 es necesario que RAND1 esté desactivada
//#define RAND2

// si no están definidas RAND1 ni RAND2, se utiliza la estrategia: Mejor + F * (Mejor - I1), que no converge en absoluto, colapsa sobre el primer mejor individuo

// para utilizar la función 'std::copy' para copiar un 'vector' a otro, en lugar de un 'for', no hay un ahorro de tiempo significativo, si es que lo hay
#define COPIAR_CON_COPY

// seleccina la forma de generar los números aleatorios de forma segura mediante variables 'thhread_safe'
#define AZAR_HILOS_LOCAL

// usar el generador de números aleatorios 'mt19937', en caso contrario se usa el 'minstd_rand' que es menos aleatorio y tarda mucho más.
#define MT19937
// otro generador es rl 'ranlux48'

// para inicializar el generador de números aleatorios 'mt19937' con un fichero
//#define INI_AZAR_FICHERO

// si RECOMBINACION_NORMAL está definido, los cruces sin recombinación toman el valor de la variable del individuo correspondiente de la
// población, si no, se toma el valor del mejor individuo. No parece que una sea mejor que otra, pero quizás sea preferible que
// RECOMBINACION_NORMAL esté definido porque recombinar con el mejor ofrece menos variedad que con los individuos de la población.
#define RECOMBINACION_NORMAL

// añade estadísticas de las mutaciones a las salidas, registra el número de genes que se toman del segundo progenitor y no del mutante
// desactivarla no ahorra tiempo
#define NUM_GENES_PROGENITOR_2

// calcula el número de individuos que mejoran
// desactivarla no ahorra tiempo
#define NUM_MEJORAS

// cacula el tiempo en los procesos de mutación y selección 
// desactivarla no ahorra tiempo
#define TPO_MUTA_SELECCION

// estadística de cuando una mutación extra se convierte en el mejor individuo. resulta insignificante menos del 0.5% de las veces
//#define MEJ_MUT_EXTA

// calcula la función de mérito como ECM y no como ECT
//#define ECM

// inviable. El descendiente se acepta (selecciona) si hay algún individuo en la población con peor mérito
//#define SELECCION_MAXIMA

// en los individuos de la población inicial se sustituyen los valores de las variables (F,E,M,D, y en su caso XP) por los que resultan de
// recalcular dos veces las ecuaciones del modelo, como se hace en la función de mérito
//#define AJUSTA_POB_INICIAL

// añade estadísticas de los cruces a las salidas
//#define ESTA_CRUCES

// para comprobar que la variable con la desviación máxima se está determinando correctamente, fue útil durante el desarrollo, pero ahora es inútil
//#define COMPROBAR_MAX_DESVIACION

// la función de merito termina cuando la desviación supera un cierto listón, no ahorra ningún tiempo
//#define FIN_MERITO_ANTICIPADO

// usar instrucciones AX2, no ahorra tiempo, quizás el compilador ya lo hace.
//#define CONSUMO_INTERMEDIO_AX

// como puede haber alrededor de una tercera parte de valores 'ax' iguales a 0
// guardamos los índices de los que no lo son, para usar solo estos en el cálculo de X
// no ahorra tiempo, es inútil.
//#define CONSUMO_INTERMEDIO_INDESADO

// para calcular las medias de los sorteos
//#define SORTEOS

// desastroso, 'FIJAR_VARIABLES' no funciona
//#define FIJAR_VARIABLES

// dar un peso distinto de 1 a PESO_YDP, ya sea mayor o menor, dificulta o imposibilita encontrar una solución
//#define USAR_PESO_YDP
/*
------------------------------------------------------------------------------------------------------------
*/

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

// funciones de la DLL que pueden ser llamadas desde otra aplicación
extern "C" MEGA_DLL_API OPCIONES recibe_opciones(OPCIONES vals);
extern "C" MEGA_DLL_API DATOS recibe_datos(DATOS vals);
extern "C" MEGA_DLL_API PARAMETROS recibe_parametros(PARAMETROS vals);
extern "C" MEGA_DLL_API double* merito_sol(double* vec_opt);
extern "C" MEGA_DLL_API double* soluciona(double* par, double* cotasInf, double* cotasSup, double* vec, int extendida, const char* senda, const char* caso);
extern "C" MEGA_DLL_API double merito_s(double* vec_opt);

// estas dos funciones fueron útiles durante el desarrollo  pero se podrían eliminar
extern "C" MEGA_DLL_API bool abre_salida(const char* senda);
extern "C" MEGA_DLL_API bool cierra_salida();

#ifdef DESVIACONES_RELATIVAS
extern "C" MEGA_DLL_API double merito_s_relativa(double* vec_opt);
extern "C" MEGA_DLL_API double* merito_sol_relativa(double* vec_opt);
#endif 
#ifdef FIN_MERITO_ANTICIPADO
double merito_d(double* vec_opt, double liston);
#endif
#ifdef COMPROBAR_MAX_DESVIACION
extern "C" MEGA_DLL_API void indice_desviaciones();
#endif

#pragma region Merito
void produccion_factor_compuesto_Y(double* Y, double F[NSEC][NFAC], double beta[NSEC][NFAC], double* b);
void restriccion_produccion_bruta_Z(double* Z, double* teta, double* xie, double* xid, double* E, double* D, double* phi);
void consumo_intermedio_X(double X[NSEC][NSEC], double* Z, double ax[NSEC][NSEC]);
#ifdef SIN_XR
void consumo_intermedio_Xr(double X[NSEC][NSEC], double* Z, double ax[NSEC][NSEC]);
#endif
void utilizacion_factor_compuesto_Y(double* Y, double* Z, double* ay);
void uso_optimo_factores_F(double F[NSEC][NFAC], double beta[NSEC][NFAC], double* pf, double* py, double* Ypd);
void coste_unitario_produccion_pz(double* pz, double* ay, double* py, double ax[NSEC][NSEC], double* pq, double Ajc[NSEC], double Z0[NSEC]);
void aportacion_factores_FF(double FF[NDEM][NFAC], double FF0[NDEM][NFAC], double F[NSEC][NFAC]);
void impuestos_directos_Td(double* Td, double* taud, double* pf, double FF[NDEM][NFAC], double Alp[NDEM][NFAC], double* PssH0, double AgH[NDEM]);
void impuestos_produccion_Tz(double* Tz, double* tauz, double* pz, double* Z);
void aranceles_importacion_Tm(double* Tm, double* taum, double* pm, double* M);
void ahorro_hogares_Sp(double* Sp, double* ssp, double* pf, double FF[NDEM][NFAC], double* PssH0);
double impuestos_directos_Ti(double tai, double* pf, double FF[NDEM][NFAC], int INDICE_F_TRA);
void ayudas_AgE_AgH(double* AgE, double* AgH, double* cage, double* cagh, double* Td, double* Tz, double* Tm, double Tg, double Ti, double Te, double* AYD_ADI_DEM);
void seguridad_social_empresas_CssE(double* CssE, double* ctzsse, double* pf, double F[NSEC][NFAC], int INDICE_F_TRA);
void seguridad_social_hogares_CssH(double* CssH, double* ctzssh, double* pf, double FF[NDEM][NFAC], double Alp[NDEM][NFAC], int INDICE_F_TRA);
double gobierno_Sg_Xg(double* Xg, double ssg, double* mu, double* pq, double* Td, double* Tz, double* Tm, double Tg, double Ti, double Te, double* AgE, double* AgH, double* PssH0, double* CssH, double* CssE, double Fue);
double ahorro_exterior_Sf(double* M, double* E, double* pm, double* pe);
void demanda_inversion_Xv(double* Xv, double* landa, double* pq, double* Sp, double Sg, double Sc, double epsilon, double Sf, double Ti, double Te);
void demanda_maxima_utilidad_StoneGeary_Xp(double Xp[NDEM][NSEC], double alfa_esen[NDEM][NSEC], double CON_ESENCIALES[NDEM][NSEC], double* pq, double* pf, double FF[NDEM][NFAC], double* Sp, double* Td, double* CssH, double* AgH, double* PssH0, int DEM_ADICIONAL_TIPO, double DEM_ADICIONAL[NDEM][NSEC], bool RENTA_FICTICIA);
void demanda_maxima_utilidad_CobbDouglas_Xp(double Xp[NDEM][NSEC], double alfa[NDEM][NSEC], double* pq, double* pf, double FF[NDEM][NFAC], double* Sp, double* Td, double* CssH, double* AgH, double* PssH0, int DEM_ADICIONAL_TIPO, double DEM_ADICIONAL[NDEM][NSEC], bool RENTA_FICTICIA);
void demanda_maxima_utilidad_CES_Xp(double Xp[NDEM][NSEC], double* eta_ces, double alfa_ces[NDEM][NSEC], double* pq, double* pf, double FF[NDEM][NFAC], double* Sp, double* Td, double* CssH, double* AgH, double* PssH0, int DEM_ADICIONAL_TIPO, double DEM_ADICIONAL[NDEM][NSEC], bool RENTA_FICTICIA);
void produccion_armington_Q(double* Q, double* gamma, double* deltam, double* deltad, double* M, double* D, double* eta);
void importacion_maxima_utilidad_armington_M(double* M, double* gamma, double* deltam, double* pq, double* pm, double* Q, double* eta, double* taum);
void produccion_maxima_utilidad_armington_D(double* Da, double* gamma, double* deltad, double* pq, double* pd, double* Q, double* eta);
void importacion_local_maxima_utilidad_armington_MD(double* M, double* Da, double* gamma, double* deltam, double* deltad, double* pq, double* pm, double* pd, double* Q, double* eta, double* taum);
void produccion_para_exportacion_E(double* E, double* teta, double* xie, double* pz, double* pe, double* Z, double* phi, double* tauz, double* CssE, double* AgE, double Apz, double* ctzssez, double* ctzagez, int MODO_PSEUDOIMPTOS);
void produccion_para_local_D(double* Dt, double* teta, double* xid, double* pz, double* pd, double* Z, double* phi, double* tauz, double* CssE, double* AgE, double Apz, double* ctzssez, double* ctzagez, int MODO_PSEUDOIMPTOS);
void produccion_para_exportacion_local_ED(double* E, double* Dt, double* teta, double* xie, double* xid, double* pz, double* pe, double* pd, double* Z, double* phi, double* tauz, double* CssE, double* AgE, double Apz, double* ctzssez, double* ctzagez, int MODO_PSEUDOIMPTOS);
double equilibrio_balance_pagos_moneda_extranjera(double* pWe, double* E, double* pWm, double* M, double Sf);
double precio_factor_trabajo_pFL(int INDICE_F_TRA, double PobAct, double alfa, double pF0L, double F0[NSEC][NFAC], double F[NSEC][NFAC]);
#pragma endregion

#pragma region Genetico
void cancelar(int sig);
int parametros_alge(double* par);
bool inicia_cotas();
bool fija_cotas(double* cotasInf, double* cotasSup);
bool inicia_poblacion(double ajuste);
static bool genera_poblacion(double* vec_central, int modo, double modulacion);
void recolocar_al_mejor(int ind_mejor_merito);
int avanza();
void mutacion_cruze(int desde, int hasta);
void seleccion(int desde);
void seleccionH(int desde, int hasta);
void seleccionH(int desde, int hasta, int hilo);
int comprobar_final();
void salida_solucion(char* fichero);
double distancia_clonacion();
int PreparaMP();
bool Arranque();
int ProcesoMP(int gh);
#ifdef AZAR_HILOS_LOCAL
// las variables relacionadas con el generador de números aleatorios hay que pasarlas por referencia (& = punteros) para que estado del generador se actualice
// correctamente cada vez que se le llama, en caso contrario se generaría el mismo número una y otra vez
void mutacion_cruzeH(int desde, int hasta, int hilo, mt19937& gh, uniform_int_distribution<int>& he, uniform_int_distribution<int>& hi, uniform_real_distribution<double>& hd);
void ProcesarTramo(int hilo, int desde, int hasta, mt19937& gh, uniform_int_distribution<int>& he, uniform_int_distribution<int>& hi, uniform_real_distribution<double>& hd);
#else
void mutacion_cruzeH(int desde, int hasta, int hilo);
void ProcesarTramo(int hilo, int desde, int hasta);
#endif
unsigned int WINAPI HiloTramos(LPVOID param);
void fin_soluciona();
#ifdef INI_AZAR_FICHERO
void inicia_azar(mt19937* g, int hilo, unsigned int semilla);
void inicia_azar(mt19937& g, unsigned int semilla);
#endif
#ifdef SELECCION_MAXIMA
void seleccion_maxima();
#endif
#ifdef AJUSTA_POB_INICIAL
double ajustar_vec_solucion(double* vec_opt);
#endif
#pragma endregion
