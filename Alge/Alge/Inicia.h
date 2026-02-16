#pragma once
#include <Windows.h>

using namespace std;


const int NFAC = 2;
const int NDEM = 2;
const int NSEC = 6;
const int NSF = NSEC * NFAC;

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
} PARAMETROS;

int lee_parametros(const char* fichero);
int punteros_libreria(const wchar_t* fichero);
bool inicia();
void inicia_caso0();
void inicia_caso1();
bool libera_DLL(HINSTANCE hinstLib);
bool inicia_cotas();
bool fija_cotas(double* vec, double pmenor, double pmayor, double vmenor, double vmayor);
bool inicia_poblacion(double ajuste);
bool genera_poblacion();
bool libera_cotas();
bool libera_poblacion();
int avanza();
void mutacion_cruze(int desde, int hasta, int hilo);
void mutacion_cruzeH(int desde, int hasta, int hilo);
void mutacion_cruze_ax(int desde, int hasta, int hilo);
void mutacion_cruze_axH(int desde, int hasta, int hilo);
void seleccion();
void seleccionH(int hilo, int desde, int hasta);
int comprobar_final();
double distancia_clonacion();
void muestra(double clonacion);
void mejor_primero(int ind_mejor_merito);
int PreparaMP(int hasta);
bool Arranque();
int ProcesoMP(int hasta, int gh);
void ProcesarTramo(int hilo, int desde, int hasta);
unsigned int WINAPI HiloTramos(LPVOID param);
