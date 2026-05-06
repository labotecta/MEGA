#pragma once
#define MEGA_DLL_API __declspec(dllexport)
#include <Windows.h>

using namespace std;

#define MEGA6

#ifdef MEGA4
const int NDEM = 2;
const int NSEC = 6;
#elif defined(MEGA5)
const int NDEM = 3;
const int NSEC = 63;
#elif defined(MEGA6)
const int NDEM = 2;
const int NSEC = 31;
#endif

// añade a las salidas estadísticas de los cruces
//#define ESTA_CRUCES

// se pueden usar desviaciones relativas en lugar de absolutas al calcular la función de error, las desviaciones relativas son inútiles
//#define DESVIACONES_RELATIVAS

// para comprobar que la variable con la desviación máxima se está determinando correctamente, fue útil durante el desarrollo, pero ahora es inútil
//#define COMPROBAR_MAX_DESVIACION

// la función de merito termina cuando la desviación supera un cierto liston, no ahorra ningún tiempo
//#define FIN_MERITO_ANTICIPADO

// no ahorra tiempo, quizás el compilador ya lo hace.
//#define CONSUMO_INTERMEDIO_AX

// como puede haber alrededor de una tercera parte de valores 'ax' iguales a 0
// guardamos los índices de los que no lo son, para usar solo estos en el cálculo de X
// no ahorra tiempo, es inútil.
//#define CONSUMO_INTERMEDIO_INDESADO

#define COPIAR_CON_COPY

const int NFAC = 2;

typedef struct
{
public:
	int OR_PRE_EXCLUIDO;
	double PRECIO_F_EXCLUIDO;
	double VALOR_F_TRA;
	double ALFA_PHILLIPS;
	bool GE_INCLUYE_XP;
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
	double PobAct;
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

extern "C" MEGA_DLL_API OPCIONES recibe_opciones(OPCIONES vals);
extern "C" MEGA_DLL_API DATOS recibe_datos(DATOS vals);
extern "C" MEGA_DLL_API PARAMETROS recibe_parametros(PARAMETROS vals);
extern "C" MEGA_DLL_API double merito_s(double* vec_opt);
extern "C" MEGA_DLL_API double* merito_sol(double* vec_opt);

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

extern "C" MEGA_DLL_API double* soluciona(double* par, double* cotasInf, double* cotasSup, double* vec, int extendida, const char* senda);

#pragma region Merito
void produccion_factor_compuesto_Y(double* Y, double F[NSEC][NFAC], double beta[NSEC][NFAC], double* b);
void restriccion_produccion_bruta_Z(double* Z, double* teta, double* xie, double* xid, double* E, double* D, double* phi);
void consumo_intermedio_X(double X[NSEC][NSEC], double* Z, double ax[NSEC][NSEC]);
void utilizacion_factor_compuesto_Y(double* Y, double* Z, double* ay);
void uso_optimo_factores_F(double F[NSEC][NFAC], double beta[NSEC][NFAC], double* pf, double* py, double* Ypd);
void coste_unitario_produccion_pz(double* pz, double* ay, double* py, double ax[NSEC][NSEC], double* pq);
void aportacion_factores_FF(double FF[NDEM][NFAC], double FF0[NDEM][NFAC], double F[NSEC][NFAC]);
void impuestos_directos_Td(double* Td, double* taud, double* pf, double FF[NDEM][NFAC], double Alp[NDEM][NFAC], double* PssH0);
void impuestos_produccion_Tz(double* Tz, double* tauz, double* pz, double* Z);
void aranceles_importacion_Tm(double* Tm, double* taum, double* pm, double* M);
double impuestos_directos_Ti(double tai, double* Sp);
void ayudas_AgE_AgH(double* AgE, double* AgH, double* cage, double* cagh, double* Td, double* Tz, double* Tm, double Tg, double Ti, double Te, double* AYD_ADI_DEM);
void ahorro_hogares_Sp(double* Sp, double* ssp, double FF[NDEM][NFAC], double* pf, double* PssH0);
void seguridad_social_empresas_CssE(double* CssE, double* ctzsse, double* pf, double F[NSEC][NFAC], int INDICE_F_TRA);
void seguridad_social_hogares_CssH(double* CssH, double* ctzssh, double* pf, double FF[NDEM][NFAC], double Alp[NDEM][NFAC], int INDICE_F_TRA);
double gobierno_Sg_Xg(double* Xg, double ssg, double* mu, double* pq, double* Td, double* Tz, double* Tm, double Tg, double Ti, double Te, double* AgE, double* AgH, double* PssH0, double* CssH, double* CssE);
double ahorro_exterior_Sf(double* M, double* E, double* pm, double* pe);
void demanda_inversion_Xv(double* Xv, double* landa, double* pq, double* Sp, double Sg, double Sc, double epsilon, double Sf, double Ti, double Te);
void demanda_maxima_utilidad_StoneGeary_Xp(double Xp[NDEM][NSEC], double alfa_esen[NDEM][NSEC], double CON_ESENCIALES[NDEM][NSEC], double* pq, double* pf, double FF[NDEM][NFAC], double* Sp, double* Td, double* CssH, double* AgH, double* PssH0, int DEM_ADICIONAL_TIPO, double DEM_ADICIONAL[NDEM][NSEC], bool RENTA_FICTICIA);
void demanda_maxima_utilidad_CobbDouglas_Xp(double Xp[NDEM][NSEC], double alfa[NDEM][NSEC], double* pq, double* pf, double FF[NDEM][NFAC], double* Sp, double* Td, double* CssH, double* AgH, double* PssH0, int DEM_ADICIONAL_TIPO, double DEM_ADICIONAL[NDEM][NSEC], bool RENTA_FICTICIA);
void demanda_maxima_utilidad_CES_Xp(double Xp[NDEM][NSEC], double* eta_ces, double alfa_ces[NDEM][NSEC], double* pq, double* pf, double FF[NDEM][NFAC], double* Sp, double* Td, double* CssH, double* AgH, double* PssH0, int DEM_ADICIONAL_TIPO, double DEM_ADICIONAL[NDEM][NSEC], bool RENTA_FICTICIA);
void produccion_armington_Q(double* Q, double* gamma, double* deltam, double* deltad, double* M, double* D, double* eta);
void importacion_maxima_utilidad_armington_M(double* M, double* gamma, double* deltam, double* pq, double* pm, double* Q, double* eta, double* taum);
void produccion_maxima_utilidad_armington_D(double* Da, double* gamma, double* deltad, double* pq, double* pd, double* Q, double* eta);
void produccion_para_exportacion_E(double* E, double* teta, double* xie, double* pz, double* pe, double* Z, double* phi, double* tauz, double* CssE, double* AgE, double Apz, double* ctzssez, double* ctzagez, int MODO_PSEUDOIMPTOS);
void produccion_para_local_D(double* Dt, double* teta, double* xid, double* pz, double* pd, double* Z, double* phi, double* tauz, double* CssE, double* AgE, double Apz, double* ctzssez, double* ctzagez, int MODO_PSEUDOIMPTOS);
double equilibrio_balance_pagos_moneda_extranjera(double* pWe, double* E, double* pWm, double* M, double Sf);
double precio_factor_trabajo_pFL(int INDICE_F_TRA, double PobAct, double alfa, double pF0L, double F0[NSEC][NFAC], double F[NSEC][NFAC]);
#ifdef COMPROBAR_MAX_DESVIACION
void indice_desviaciones();
#endif 
#pragma endregion

#pragma region Genetico

void cancelar(int sig);
int parametros_alge(double* par);
bool inicia_cotas();
bool fija_cotas(double* cotasInf, double* cotasSup);
bool inicia_poblacion(double ajuste);
static bool genera_poblacion();
void recolocar_al_mejor(int ind_mejor_merito);
int avanza();
void mutacion_cruze(int desde, int hasta, int hilo);
void mutacion_cruzeH(int desde, int hasta, int hilo);
void seleccion(int desde);
void seleccionH(int desde, int hasta, int hilo);
int comprobar_final();
double distancia_clonacion();

int PreparaMP();
bool Arranque();
int ProcesoMP(int gh);
void ProcesarTramo(int hilo, int desde, int hasta);
unsigned int WINAPI HiloTramos(LPVOID param);
void fin_soluciona(auto t_inicio);
#pragma endregion
