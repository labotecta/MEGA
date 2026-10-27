#include "Header.h"
#include "cuda_runtime.h"
#include <cuda_runtime_api.h>
#include <curand_kernel.h>
#include "device_launch_parameters.h"
#include <cstdlib>
#include <random>
#include <cstdio>
#include <malloc.h>
#include <chrono>
#include <ctime>
#include <share.h>
#include <csignal>
#include <sys\timeb.h> 
#include <vector_types.h>
#include <curand_uniform.h>
#include <driver_types.h>
#include <direct.h>
#include <windows.h>

using namespace std;

cudaError_t cudaStatus;

const int hMAX_DESVIOS_BLOQUE = 64;
const int hMAX_ROT_DESVIOS_BLOQUE = 38;
const int hN_BLO_VEC = 12;
/*
No se van a generar histogramas por lo que reducimos hHISTO_MAX a 0
const int hHISTO_MAX = 201;
*/
const int hHISTO_MAX = 0;

// longitud cabecera
__device__ const int LCAB =
1 +
1 +
1 +
1 +
1 +
1 +
1
;
__device__ const int LSOL =
// longitud vector solución, incluidos 2 factores e incluidas Xpi y AgHi
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
NDEM * NSEC +
// AgHi
NDEM;

// longitud variables primer pase
__device__ const int LVARS_PP =
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
__device__ const int LVARS_SP =
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
int hLVDES =
LCAB +
LSOL +
64
;
__device__ const int LVAR =
// cabecera
LCAB +
// vector solución
LSOL +
// variables primer pase
LVARS_PP +
// variables recalculadas
LVARS_SP;

int caso;
size_t ta_pob;
size_t ta_me_sol;
size_t ta_VEC_OPT_E;
int peticion_mem_comp;
size_t limite_mem_comp;

__device__ __constant__ double CeroDem[NDEM]{};
__device__ OPCIONES   op;
__device__ DATOS      datos;
__device__ PARAMETROS parametros;
__device__ int* pvec;
__device__ double* me_sol{};
__device__ double* VEC_OPT_E{};
__device__ double* AYD_ADI_DEM;
__device__ double* desvios_bloque;
__constant__ int NPOB;
__constant__ int NVEC;
__device__ double factor_mutacion;
__constant__ double cte_recombinacion;
__constant__ double cte_recombinacion_extra;
__constant__ double prob_cop_mejor;
__device__ int ind_mejor_merito;
__constant__ int histo_int;
__device__ int puntero_bloque_desviacion;
__device__ int desplazamiento_desviacion;
__device__ int N_DESVIACIONES;
__device__ double VAB;
__device__ double impuestos;
__device__ double sZ;
__device__ double sQ;
__device__ double cotizacionesSS;
__device__ int indice_desv_bloques;

int hindice_desv_bloques;

OPCIONES  hop;
OPCIONES* pro_opciones;
DATOS  hdatos;
DATOS* pro_datos;
PARAMETROS  hparametros;
PARAMETROS* pro_parametros;

char descripcion_caso[512];
char fichero_caso[384];
char senda_salidas[384];
char senda_v_solucion[384];
char senda_solucion[384];

// longitud cabecera
const int hLCAB =
1 +
1 +
1 +
1 +
1 +
1 +
1
;
const int hLSOL =
// longitud vector solución, incluidos 2 factores e incluidas Xpi y AgHi
hNFAC +
hNSEC +
hNSEC +
hNSEC +
1 +
1 +
hNSEC * hNFAC +
hNSEC +
hNSEC +
hNSEC +
// Xpi
hNDEM * hNSEC +
// AgHi
hNDEM;

// longitud variables primer pase
const int hLVARS_PP =
hNSEC +
hNSEC +
hNSEC +
hNSEC * hNFAC +
hNSEC +
hNSEC +
hNSEC +
hNSEC +
hNSEC +
hNSEC +
hNSEC +
hNSEC +
hNSEC +
hNSEC +
hNDEM +
hNSEC +
hNSEC +
hNDEM +
hNSEC +
hNDEM +
hNSEC +
hNDEM +
1 +
1 +
1 +
1 +
hNDEM * hNSEC +
hNDEM * hNFAC +
hNDEM * hNFAC +
hNSEC * hNSEC +
1
;

// longitud variables recalculadas
const int hLVARS_SP =
hNSEC * hNFAC +
hNSEC +
hNSEC +
hNSEC +
hNSEC +
hNSEC +
hNSEC +
hNSEC +
hNSEC +
hNSEC +
hNSEC +
hNSEC +
hNSEC +
hNSEC +
hNDEM +
hNSEC +
hNSEC +
hNDEM +
hNSEC +
hNDEM +
hNSEC +
hNDEM +
1 +
1 +
1 +
1 +
hNDEM * hNSEC +
hNDEM * hNFAC +
hNDEM * hNFAC +
hNSEC * hNSEC +
1
;
const int hLVAR =
// cabecera
hLCAB +
// vector solución
hLSOL +
// variables primer pase
hLVARS_PP +
// variables recalculadas
hLVARS_SP;
const int hLVSOL =
// cabecera
hLCAB +
// vector solución
hLSOL +
// desviaciones por bloque (un máximo de 64 para futuras ampliaciones)
64 +
// evolución del mérito y de la desviación máxima
2 * hHISTO_MAX
;
int hlen_var[hN_BLO_VEC] = { 1, hNSEC, hNSEC, hNSEC, 1, 1, hNSEC * hNFAC, hNSEC, hNSEC, hNSEC, hNDEM * hNSEC, hNDEM };
const char* rot_desvios[hMAX_ROT_DESVIOS_BLOQUE] = {
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
"AgHi",
"fin"
};
const char* rot_blo_vec[hN_BLO_VEC + 1] = {
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
"AgH",
"fin"
};
int* pro_pvec;
int* hpvec;

double hdesvios_bloque[hMAX_DESVIOS_BLOQUE];
double* pro_desvios_bloque;
int hpuntero_bloque_desviacion = 0;
int hdesplazamiento_desviacion = 0;
double hVAB;
double himpuestos;
double hsZ;
double hsQ;
double hcotizacionesSS;
double hme_sol[hLVAR]{};
double* pro_me_sol;

double hVEC_OPT_E[hLVSOL]{};
double* pro_VEC_OPT_E;

/*
'VEC_OPT_E' igual que 'me_sol' pero solo guarda el vector solución, que es lo realmente útil ya que valor del resto
de las variables se puede obtener a partir del vector solución mediante las ecuaciones del modelo.
Además guarda las desviaciones por bloques de ecuaciones
*/

#pragma region Genetico

/*
convertimos en matrices (vectores) las variables que cada hilo debe
utilizar de forma independiente de los otros hilos para evitar que colisionen.
para poder usar matrices fijas, definimos la constante MAX_HILOS en 128 y aunque desperdiciemos
memoria, es insignificante
*/

mt19937 gen;
uniform_int_distribution<int> dis_entero{};
uniform_real_distribution<double> dis_double(0.0, 1.0);

struct timeb tiempo_ant_ms, tiempo_act_ms;
double dif_tpo_ms;
double tot_tpo_muta{};
double tot_tpo_sele{};
double tot_tpo_tota{};
double par_tpo_segs{};
double tot_tpo_mins{};

int* hfijo;
int* hfactible;
double* hmerito_individuo;
double** hcotas;
double** hpoblacion;
double** hdescendiente;

int* pro_fijo;
int* pro_factible;
double* pro_merito_individuo;
double* pro_cotas;
double* pro_poblacion;
double* pro_descendiente;

double* hres_merito;

__device__ int* fijo;
__device__ int* factible;
__device__ double* merito_individuo;
__device__ double** cotas;
__device__ double** poblacion;
__device__ double** descendiente;

int nvar_fijas;

const int MAX_VEC = 1000;
double vec_ini[MAX_VEC];

bool CANCELAR;
int hind_mejor_merito;
double hmejor_merito;
double mejor_merito_anterior;
int generacion;
int res_Simulacion;

// parametros para particularizar el algoritmo genético
int max_intentos;
int intentos;
double factor_dispersion;
/*
parámetro F que pondera la diferencia entre dos individuos al azar, que se suma al mejor individuo para
obtener un mutante. Va camviando a cada generación por un valor comprendido entre los dos valores de 'par_mutacion'
*/
double par_mutacion[2]{};
double hfactor_mutacion;
/*
parámetro CR (probabilidad de cruce), cuanto más cerca de 1. más probable es que se produzca la recombinación, es
decir, que el 'descendiente' tome el valor del mutante y no el del individuo correspondiente. Si es 1., el
'descendiente' siempre toma el valor del mutante
*/
double hcte_recombinacion;
double hcte_recombinacion_extra;
double tolerancia;
double tol_aceptable;
int generaciones_control_progreso;
double min_progreso;
int hhisto_int;
bool incluir_x0;
int hNVEC;
/*
NO se usan los valores leidos del caso, en su lugar se usan los leidos de:
C:\\MEGA\\MEGA_GPU\\Casos\\Actual\\par_caso_cuda.txt
*/
int n_hilos;
int hNPOB;
int max_generaciones;
unsigned int semilla;
double hprob_cop_mejor_ini;
double hprob_cop_mejor;

// adicionalmente se leen de C:\\MEGA\\MEGA_GPU\\Casos\\Actual\\par_caso_cuda.txt
int sol_mem_compartida;
int NBLO_K;
int hNIF_K;
__constant__ int NIF_K;

int mem_comp_max;

// NO se usan, se mantienen por compatibilidad con MEGA y MEGA_DLL
int modo_poblacion_inicial;
int modo_reinicio_poblacion;
double factor_sigma;
double variacion_dispersion;
int num_tramos_lhs;
int hhisto_sol;
double umbral_regularizacion;
double fraccion_regularizacion;
bool hcontrol_factibilidad;
bool poner_el_mejor_primero;
int estadistica_pob_ini;
int desviaciones_relativas;

double factor_dispersion_actualizado = 1.0;

FILE* salida{};

struct timeb tiempo_ini;
struct timeb tiempo_ant, tiempo_act;
double dif_tpo_par;
double dif_tpo_tot;

void imprime_error(const char* rot) {
	printf("%s (%d) %s\n", rot, cudaStatus, cudaGetErrorString(cudaStatus));
	fprintf(salida, "%s (%d) %s\n", rot, cudaStatus, cudaGetErrorString(cudaStatus));
}

//cuando se pulsa Ctrl+C, se establece la variable global 'CANCELAR' a true para que el algoritmo genético termine lo antes posible
void cancelar(int sig)
{
	CANCELAR = true;
}
bool tarjeta() {
	int device;
	cudaGetDevice(&device);
	struct cudaDeviceProp prop;
	/*
	name is an ASCII string identifying the device;
	totalGlobalMem is the total amount of global memory available on the device in bytes;
	sharedMemPerBlock is the maximum amount of shared memory available to a thread block in bytes; this amount is shared by all thread blocks simultaneously resident on a multiprocessor;
	regsPerBlock is the maximum number of 32-bit registers available to a thread block; this number is shared by all thread blocks simultaneously resident on a multiprocessor;
	warpSize is the warp size in threads;
	memPitch is the maximum pitch in bytes allowed by the memory copy functions that involve memory regions allocated through cudaMallocPitch();
	maxThreadsPerBlock is the maximum number of threads per block;
	maxThreadsDim[3] contains the maximum size of each dimension of a block;
	maxGridSize[3] contains the maximum size of each dimension of a grid;
	clockRate is the clock frequency in kilohertz;
	totalConstMem is the total amount of constant memory available on the device in bytes;
	major, minor are the major and minor revision numbers defining the device's compute capability;
	textureAlignment is the alignment requirement; texture base addresses that are aligned to textureAlignment bytes do not need an offset applied to texture fetches;
	deviceOverlap is 1 if the device can concurrently copy memory between host and device while executing a kernel, or 0 if not;
	multiProcessorCount is the number of multiprocessors on the device;
	kernelExecTimeoutEnabled is 1 if there is a run time limit for kernels executed on the device, or 0 if not.
	integrated is 1 if the device is an integrated (motherboard) GPU and 0 if it is a discrete (card) component
	canMapHostMemory is 1 if the device can map host memory into the CUDA address space for use with cudaHostAlloc()/cudaHostGetDevicePointer(), or 0 if not;
	computeMode is the compute mode that the device is currently in. Available modes are as follows:
	cudaComputeModeDefault: Default mode - Device is not restricted and multiple threads can use cudaSetDevice() with this device.
	cudaComputeModeExclusive: Compute-exclusive mode - Only one thread will be able to use cudaSetDevice() with this device.
	cudaComputeModeProhibited: Compute-prohibited mode - No threads can use cudaSetDevice() with this device. Any errors from calling cudaSetDevice() with an exclusive (and occupied) or prohibited device will only show up after a non-device management runtime function is called. At that time, cudaErrorNoDevice will be returned.
	*/
	cudaGetDeviceProperties(&prop, device);
	fprintf(salida, "\n");
	fprintf(salida, "Device name: %s\n", prop.name);
	fprintf(salida, "Total global memory (Gbytes)     %11.1f\n", (double)(prop.totalGlobalMem) / 1024.0 / 1024.0 / 1024.0);
	fprintf(salida, "multiProcessorCount              %11d\n", prop.multiProcessorCount);
	fprintf(salida, "Shared memory per block (Kbytes) %11.1f\n", (double)(prop.sharedMemPerBlock) / 1024.0);
	fprintf(salida, "regsPerBlock                     %11d\n", prop.regsPerBlock);
	fprintf(salida, "warpSize                         %11d\n", prop.warpSize);
	fprintf(salida, "memPitch (ancho filas 2D)        %11zu\n", prop.memPitch);
	fprintf(salida, "Max Threads per Block:           %11d\n", prop.maxThreadsPerBlock);
	fprintf(salida, "maxThreadsDim:                   %d %d %d\n", prop.maxThreadsDim[0], prop.maxThreadsDim[1], prop.maxThreadsDim[2]);
	fprintf(salida, "maxGridSize:                     %d %d %d\n", prop.maxGridSize[0], prop.maxGridSize[1], prop.maxGridSize[2]);
	fprintf(salida, "totalConstMem                    %11zu\n", prop.totalConstMem);
	fprintf(salida, "major-minor:                     %d.%d\n", prop.major, prop.minor);
	fprintf(salida, "textureAlignment                 %11zu\n", prop.textureAlignment);
	fprintf(salida, "integrated (motherboard)         %11d\n", prop.integrated);
	fprintf(salida, "canMapHostMemory                 %11d\n", prop.canMapHostMemory);
	fprintf(salida, "Memory Bus Width (bits):         %11d\n", prop.memoryBusWidth);
	fprintf(salida, "Concurrent kernels:              %s\n", prop.concurrentKernels ? "si" : "no");
	fprintf(salida, "L2 Cache Size (bytes):           %11d\n", prop.l2CacheSize);

	printf("\n");
	fprintf(salida, "\n");

	// Obtener la capacidad maxima de memoria compartida por el dispositivo (GPU)
	mem_comp_max = 0;
	cudaDeviceGetAttribute(&mem_comp_max, cudaDevAttrMaxSharedMemoryPerBlockOptin, 0);
	printf("capacidad máxima de memoria compartida: %d\n\n", mem_comp_max);
	fprintf(salida, "capacidad máxima de memoria compartida: %d\n", mem_comp_max);

	// Suponiendo que el kernel necesita 'mem_compartida' KB

	//cudaFuncSetCacheConfig(kernel_seleccion, cudaFuncCachePreferL1);

	if (sol_mem_compartida > 0) {
		peticion_mem_comp = sol_mem_compartida * 1024;
		if (peticion_mem_comp == mem_comp_max) {
			printf("memoria compartida por defecto                    : %d k\n\n", sol_mem_compartida);
			fprintf(salida, "memoria compartida por defecto                    : %d k\n\n", sol_mem_compartida);
		}
		else {
			printf("memoria compartida solicitada                     : %d k\n\n", sol_mem_compartida);
			fprintf(salida, "memoria compartida solicitada                     : %d k\n\n", sol_mem_compartida);
			if (peticion_mem_comp < mem_comp_max) {
				// lo hacemos solo para el 'kernel_seleccion'
				//  Configurar explícitamente el atributo del kernel antes de lanzarlo
				cudaStatus = cudaFuncSetAttribute(kernel_seleccion, cudaFuncAttributeMaxDynamicSharedMemorySize, peticion_mem_comp);
				if (cudaStatus != cudaSuccess) {
					imprime_error("cudaFuncSetAttribute cudaFuncAttributeMaxDynamicSharedMemorySize");
					return false;
				}
				// (Opcional) Solicitar preferencia física para Shared Memory sobre la caché L1
				cudaStatus = cudaFuncSetAttribute(kernel_seleccion, cudaFuncAttributePreferredSharedMemoryCarveout, cudaSharedmemCarveoutMaxShared);
			}
			else {
				printf("La GPU no soporta la cantidad de memoria compartida solicitada.");
				return false;
			}
		}
		printf("memoria compartida por defecto\n\n");
		fprintf(salida, "memoria compartida por defecto\n\n");
	}

	int minGridSize;
	int nh_optimo;
	int numBlocks;
	int activeWarps;
	int maxWarps;
	printf("-------------------------------------------------------------------------------------------------------------\n");
	fprintf(salida, "-------------------------------------------------------------------------------------------------------------\n");
	printf("kernel_merito_s_todo:\n");
	fprintf(salida, "kernel_merito_s_todo:\n");
	cudaOccupancyMaxActiveBlocksPerMultiprocessor(
		&numBlocks,
		kernel_merito_s_todo,
		n_hilos,
		0);
	activeWarps = numBlocks * n_hilos / prop.warpSize;
	maxWarps = prop.maxThreadsPerMultiProcessor / prop.warpSize;
	printf("con %d hilos\n", n_hilos);
	fprintf(salida, "con %d hilos\n", n_hilos);
	printf("un máximo de %d bloques activos por SM, el número de warps activos es %d de un máximo de %d por SM\n", numBlocks, activeWarps, maxWarps);
	fprintf(salida, "un máximo de %d bloques activos por SM, el número de warps activos es %d de un máximo de %d por SM\n", numBlocks, activeWarps, maxWarps);
	cudaOccupancyMaxPotentialBlockSize(
		&minGridSize,			// minimum grid size needed to achieve the best potential (número de bloques)
		&nh_optimo,				// Block size (número de hilos)
		kernel_merito_s_todo,	// Kernel function
		0,						// Per-block dynamic shared memory usage intended, in bytes
		0);
	printf("óptimo para mantener el máximo número de warps activos:\n");
	printf("número mínimo de bloques: %d  hilos: %d\n\n", minGridSize, nh_optimo);
	fprintf(salida, "óptimo para mantener el máximo número de warps activos:\n");
	fprintf(salida, "número mínimo de bloques: %d  hilos: %d\n\n", minGridSize, nh_optimo);
	printf("-------------------------------------------------------------------------------------------------------------\n");
	fprintf(salida, "-------------------------------------------------------------------------------------------------------------\n");
	printf("kernel_mutacion_cruze:\n");
	fprintf(salida, "kernel_mutacion_cruze:\n");
	cudaOccupancyMaxActiveBlocksPerMultiprocessor(
		&numBlocks,
		kernel_mutacion_cruze,
		n_hilos,
		0);
	activeWarps = numBlocks * n_hilos / prop.warpSize;
	maxWarps = prop.maxThreadsPerMultiProcessor / prop.warpSize;
	printf("con %d hilos\n", n_hilos);
	fprintf(salida, "con %d hilos\n", n_hilos);
	printf("un máximo de %d bloques activos por SM, el número de warps activos es %d de un máximo de %d por SM\n", numBlocks, activeWarps, maxWarps);
	fprintf(salida, "un máximo de %d bloques activos por SM, el número de warps activos es %d de un máximo de %d por SM\n", numBlocks, activeWarps, maxWarps);
	cudaOccupancyMaxPotentialBlockSize(
		&minGridSize,			// minimum grid size needed to achieve the best potential (número de bloques)
		&nh_optimo,				// Block size (número de hilos)
		kernel_mutacion_cruze,	// Kernel function
		0,						// Per-block dynamic shared memory usage intended, in bytes
		0);
	printf("óptimo para mantener el máximo número de warps activos:\n");
	printf("número mínimo de bloques: %d  hilos: %d\n\n", minGridSize, nh_optimo);
	fprintf(salida, "óptimo para mantener el máximo número de warps activos:\n");
	fprintf(salida, "número mínimo de bloques: %d  hilos: %d\n\n", minGridSize, nh_optimo);
	printf("-------------------------------------------------------------------------------------------------------------\n");
	fprintf(salida, "-------------------------------------------------------------------------------------------------------------\n");
	printf("kernel_seleccion:\n");
	fprintf(salida, "kernel_seleccion:\n");
	cudaOccupancyMaxActiveBlocksPerMultiprocessor(
		&numBlocks,
		kernel_seleccion,
		n_hilos,
		0);
	activeWarps = numBlocks * n_hilos / prop.warpSize;
	maxWarps = prop.maxThreadsPerMultiProcessor / prop.warpSize;
	printf("con %d hilos\n", n_hilos);
	fprintf(salida, "con %d hilos\n", n_hilos);
	printf("un máximo de %d bloques activos por SM, el número de warps activos es %d de un máximo de %d por SM\n", numBlocks, activeWarps, maxWarps);
	fprintf(salida, "un máximo de %d bloques activos por SM, el número de warps activos es %d de un máximo de %d por SM\n", numBlocks, activeWarps, maxWarps);
	cudaOccupancyMaxPotentialBlockSize(
		&minGridSize,			// minimum grid size needed to achieve the best potential (número de bloques)
		&nh_optimo,				// Block size (número de hilos)
		kernel_seleccion,		// Kernel function
		0,						// Per-block dynamic shared memory usage intended, in bytes
		0);
	printf("óptimo para mantener el máximo número de warps activos:\n");
	printf("número mínimo de bloques: %d  hilos: %d\n\n", minGridSize, nh_optimo);
	fprintf(salida, "óptimo para mantener el máximo número de warps activos:\n");
	fprintf(salida, "número mínimo de bloques: %d  hilos: %d\n\n", minGridSize, nh_optimo);
	printf("-------------------------------------------------------------------------------------------------------------\n");
	fprintf(salida, "-------------------------------------------------------------------------------------------------------------\n");
	return true;
}

double* soluciona(double* par_h, double* cotasInf_h, double* cotasSup_h, double* vec, int extendida, const char* senda) {
	CANCELAR = false;

	// capturar la señal Ctrl+C, al pulsar esta combinación de teclas se ejecuta la funciín 'cancelar'
	signal(SIGINT, &cancelar);

	int res = parametros_alge(par_h);
	if (res != 0) {
		printf("Error en los parámetros recibidos\n");
		fprintf(salida, "Error en los parámetros recibidos\n");
		return nullptr;
	}
	salida = _fsopen(senda_salidas, "w", _SH_DENYWR);
	if (salida == 0) {
		printf("Error al abrir el fichero de salidas\n");
		fprintf(salida, "Error al abrir el fichero de salidas\n");
		return nullptr;
	}
	auto t_inicio = chrono::system_clock::now();
	auto inicio = chrono::system_clock::to_time_t(t_inicio);
	char tmBuff[30];
	ctime_s(tmBuff, sizeof(tmBuff), &inicio);

	printf("%s\n", descripcion_caso);
	printf("caso              :%s\n", fichero_caso);
	printf("salidas           :%s\n", senda_salidas);
	printf("vector solución   :%s\n", senda_v_solucion);
	printf("solución completa :%s\n", senda_solucion);

	fprintf(salida, "%s\n", descripcion_caso);
	fprintf(salida, "caso              :%s\n", fichero_caso);
	fprintf(salida, "salidas           :%s\n", senda_salidas);
	fprintf(salida, "vector solución   :%s\n", senda_v_solucion);
	fprintf(salida, "solución completa :%s\n", senda_solucion);

	fprintf(salida, "-------------------------------------------------------------------------------------------------------------\n");
	fprintf(salida, "-------------------------------------------------------------------------------------------------------------\n");
	if (tarjeta() == false) {
		printf("\nError al identificar la GPU\n");
		fprintf(salida, "\nError al identificar la GPU\n");
		return nullptr;
	}
	fprintf(salida, "-------------------------------------------------------------------------------------------------------------\n");
	fflush(salida);
	fprintf(salida, "inicio: %s\n", tmBuff);
	fflush(salida);

	if (copiaIniGPU() == false) {
		return nullptr;
	}
	if (inicia_cotas() == false) {
		printf("\nError al iniciar las cotas\n");
		fprintf(salida, "\nError al iniciar las cotas\n");
		return nullptr;
	}
	if (fija_cotas(cotasInf_h, cotasSup_h) == false) {
		printf("\nError al fijar las cotas\n");
		fprintf(salida, "\nError al fijar las cotas\n");
		return nullptr;
	}
	if (inicia_poblacion(factor_dispersion) == false) {
		printf("\nError al iniciar la población\n");
		fprintf(salida, "\nError al iniciar la población\n");
		return nullptr;
	}
	for (int i = 0; i < hNVEC; i++) {
		vec_ini[i] = vec[i];
	}
	gen.seed((unsigned int)semilla);
	dis_entero = uniform_int_distribution<int>{ 0, (int)(hNPOB - 1) };
	if (genera_poblacion(vec_ini, modo_poblacion_inicial, 1.0) == false) {
		printf("\nError al generar la población\n");
		fprintf(salida, "\nError al generar la población\n");
		return nullptr;
	}
	if (copiaGeneticoGPU() == false) {
		return nullptr;
	}
	fprintf(salida, "Número factores        : %12d\n", hNFAC);
	fprintf(salida, "Número hogares         : %12d\n", hNDEM);
	fprintf(salida, "Número sectores        : %12d\n", hNSEC);
	fprintf(salida, "-------------------------------------\n");
	fprintf(salida, "Población              : %12d\n", hNPOB);
	fprintf(salida, "Número de hilos        : %12d\n", n_hilos);
	fprintf(salida, "Número de bloques      : %12d\n", NBLO_K);
	fprintf(salida, "Individuos por hilo    : %12d\n", hNIF_K);
	if (sol_mem_compartida > 0) {
		fprintf(salida, "Memoria compartida     : %12d k\n", sol_mem_compartida);
	}
	else {
		fprintf(salida, "Memoria compartida     : por defecto\n");
	}
	fprintf(salida, "-------------------------------------\n");
	fprintf(salida, "Tolerancia en el mérito: %12.5e\n", tolerancia);
	fprintf(salida, "Intentos (reinicios)   : %12d\n", max_intentos);
#ifdef MRG32k3a
	fprintf(salida, "Números aleatorios     : %s\n", "MRG32k3a");
#else azar==curandStatePhilox4_32_10
	fprintf(salida, "Números aleatorios     : %s\n", "Philox4_32_10");
#endif
	fprintf(salida, "Semilla num.aleatorios : %12d\n", (unsigned int)semilla);
	fprintf(salida, "-------------------------------------\n");
	fprintf(salida, "Factor dispersión unif.: %12.5e\n", factor_dispersion);
	fprintf(salida, "Factor mutación (F)    : %12.5e %12.5e\n", par_mutacion[0], par_mutacion[1]);
	fprintf(salida, "Recombinación (CR)     : %12.5e\n", hcte_recombinacion);
	fprintf(salida, "Recombinación extra    : %12.5e\n", hcte_recombinacion_extra);
	fprintf(salida, "Probab.copiar el mejor : %12.5e\n", hprob_cop_mejor_ini);
	fprintf(salida, "-------------------------------------\n");
	fprintf(salida, "Control progreso cada  : %12d generaciones\n", generaciones_control_progreso);
	fprintf(salida, "Progreso mínimo        : %12.3f %%\n", 100. * min_progreso);
	fprintf(salida, "-------------------------------------\n");
	fprintf(salida, "Factor Alp             : %12.5e\n", hop.ALP_FACTOR);
	fprintf(salida, "Fondos UE              : %12.5e\n", hdatos.Fue);
	if (hop.RENTA_FICTICIA == true) {
		fprintf(salida, "Inc.demanda            : CON renta ficticia\n");
	}
	else {
		fprintf(salida, "Inc.demanda            : SIN renta ficticia\n");
	}
	fprintf(salida, "-------------------------------------\n");
	if (hop.GE_INCLUYE_XP == true) {
		fprintf(salida, "Xp incluido en la solución\n");
	}
	else {
		fprintf(salida, "Xp NO incluido en la solución\n");

	}
	if (hop.GE_INCLUYE_AgH == true) {
		fprintf(salida, "AgH incluido en la solución\n");
		fprintf(salida, "Impuestos a las ayudas AgH\n");
	}
	else {
		fprintf(salida, "AgH NO incluido en la solución\n");
	}
	fprintf(salida, "Datos de cabecera      : %12d\n", LCAB);
	int lsol = LSOL - 1;
	// no restamos 1 a LVAR porque en la solución no se incluye el precio de uno de los factores, por
	// eso se lo sumamos a LVARS_PP para obtener el total de variables del modelo
	int lvar = LVAR;
	if (hop.GE_INCLUYE_XP == false) {
		lsol -= hNDEM * hNSEC;
		lvar -= hNDEM * hNSEC;
	}
	if (hop.GE_INCLUYE_AgH == false) {
		lsol -= hNDEM;
		lvar -= hNDEM;
	}
	fprintf(salida, "Variables solución     : %12d\n", lsol);
	fprintf(salida, "Resto variables modelo : %12d\n", LVARS_PP + 1);
	fprintf(salida, "Variables recalculadas : %12d\n", LVARS_SP);
	fprintf(salida, "-------------------------------------\n");
	fprintf(salida, "Total                  : %12d\n\n", lvar);
	fprintf(salida, "Variables fijas en sol : %12d\n", nvar_fijas);
	if (nvar_fijas > 0) {
		fprintf(salida, "-------------------------------------\n");
		fprintf(salida, "Variables con valores fijos\n");
		int p;
		int d;
		for (int i = 0; i < hNVEC; i++) {
			if (hfijo[i] == 1) {
				p = 0;
				d = 0;
				for (int j = 0; j < hN_BLO_VEC; j++) {
					if (i >= hpvec[j] && i < hpvec[j + 1]) {
						p = j;
						d = i - hpvec[j];
						break;
					}
				}
				fprintf(salida, "%5d %-8s %5d %15.8e\n", i, rot_blo_vec[p], d, cotasInf_h[i]);
			}
		}
		fprintf(salida, "-------------------------------------\n");
	}
	fflush(salida);

	res_Simulacion = resuelve();

	fin_soluciona();
	return nullptr;
}

void fin_soluciona() {
	salida_solucion(senda_v_solucion, senda_solucion);
	auto t_fin = chrono::system_clock::now();
	auto fin = chrono::system_clock::to_time_t(t_fin);
	char tmBuff[30];
	ctime_s(tmBuff, sizeof(tmBuff), &fin);
	fprintf(salida, "\nfin : %s\n", tmBuff);
	fclose(salida);
}

int* host_ptr_int;
int* dev_ptr_int;
double* host_ptr_double;
double* dev_ptr_double;
static bool copiaMtDoubleHostDevice(double* fte, int ta, double*& des) {
	/*
	reserva memoria device en la dirección 'des' y le
	copia el contenido de la variable host 'fte'
	'des' se pasa mediante referencia (&) para que tengamos el valor de este puntero
	como resultado de esta función
	*/
	// reservamos memoria en el device
	cudaStatus = cudaMalloc((void**)&des, ta * sizeof(double));
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaMalloc copiaMtDoubleHostDevice");
		return false;
	}
	// copiamos los datos 'fte' en la memoria que acabamos de reservar
	/*
	no podemos copiar los datos haciendo referenci a una variable device, 'des' es una dirección de memoria device sin nombre
	lo que si podemos es copiar los datos a esta dirección 'des' y en luego en
	'kernelIniGene' asignar este puntero a un nombre de variable device
	*/
	cudaStatus = cudaMemcpy(des, fte, ta * sizeof(double), cudaMemcpyHostToDevice);
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaMemcpy copiaMtDoubleHostDevice");
		return false;
	}
	return true;
}
static bool copiaMtIntHostDevice(int* fte, int ta, int*& des) {
	cudaStatus = cudaMalloc((void**)&des, ta * sizeof(int));
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaMalloc copiaMtIntHostDevice");
		return false;
	}
	cudaStatus = cudaMemcpy(des, fte, ta * sizeof(int), cudaMemcpyHostToDevice);
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaMemcpy copiaMtIntHostDevice");
		return false;
	}
	return true;
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
	umbral_regularizacion = par[ipar++];
	fraccion_regularizacion = par[ipar++];
	hhisto_int = (int)par[ipar++];
	hhisto_sol = (int)par[ipar++];
	modo_poblacion_inicial = (int)par[ipar++];
	modo_reinicio_poblacion = (int)par[ipar++];
	factor_dispersion = par[ipar++];
	factor_sigma = par[ipar++];
	variacion_dispersion = par[ipar++];
	num_tramos_lhs = (int)par[ipar++];
	hNPOB = (int)par[ipar++];
	par_mutacion[0] = par[ipar++];
	par_mutacion[1] = par[ipar++];
	hcte_recombinacion = par[ipar++];
	hcte_recombinacion_extra = par[ipar++];
	hcontrol_factibilidad = (int)par[ipar++] == 1;
	semilla = (unsigned int)par[ipar++];
	poner_el_mejor_primero = (int)par[ipar++] == 1;
	incluir_x0 = (int)par[ipar++] == 1;
	hNVEC = (int)par[ipar++];
	estadistica_pob_ini = (int)par[ipar++];
	desviaciones_relativas = (int)par[ipar++];
	hprob_cop_mejor_ini = par[ipar++];
	hprob_cop_mejor = hprob_cop_mejor_ini;

	if (hNPOB != (NBLO_K * n_hilos * hNIF_K)) {
		printf("error. inconsistencia en las dimensiones para los kernels: hNPOB %d != (NBLO_K * n_hilos * hNIF_K) %d\n", hNPOB, NBLO_K * n_hilos * hNIF_K);
		fprintf(salida, "error. inconsistencia en las dimensiones para los kernels: hNPOB %d != (NBLO_K * n_hilos * hNIF_K) %d\n", hNPOB, NBLO_K * n_hilos * hNIF_K);
		return -1;
	}
	if (hNVEC >= MAX_VEC) {
		printf("Error. hNVEC >= MAX_VEC\n");
		fprintf(salida, "Error. hNVEC >= MAX_VEC\n");
		return -1;
	}
	int lsol = LSOL - 1;
	if (hop.GE_INCLUYE_XP == false) {
		lsol -= hNDEM * hNSEC;
	}
	if (hop.GE_INCLUYE_AgH == false) {
		lsol -= hNDEM;
	}
	if (hNVEC != lsol) {
		printf("Error. inconsistencia en la dimensión del vector solución lsol %d != hNVEC %d\n", lsol, hNVEC);
		fprintf(salida, "Error. inconsistencia en la dimensión del vector solución lsol %d != hNVEC %d\n", lsol, hNVEC);
		return -1;
	}
	return 0;
}
// crea las matrices dinámicas para las cotas (entornos de validez de las variables)
bool inicia_cotas() {
	size_t const mem_primer_ind = 2 * sizeof(double*);
	hcotas = (double**)malloc(mem_primer_ind);
	if (hcotas == NULL) return false;
	size_t const memoria_fila = hNVEC * sizeof(double);
	for (int i = 0; i < 2; i++) {
		hcotas[i] = (double*)malloc(memoria_fila);
		if (hcotas[i] == NULL) return false;
	}
	hfijo = (int*)malloc(hNVEC * sizeof(int));
	return true;
}
// crea las variables dinámicas para la población, los descendientes, el mérito de cada individuo y si un vector de prueba es factible o no
bool inicia_poblacion(double factor_inicio) {
	size_t const mem_primer_indice = sizeof(double*) * hNPOB;
	hpoblacion = (double**)malloc(mem_primer_indice);
	if (hpoblacion == NULL) return false;
	hdescendiente = (double**)malloc(mem_primer_indice);
	if (hdescendiente == NULL) return false;
	size_t const memoria_fila = hNVEC * sizeof(double);
	for (int i = 0; i < hNPOB; i++) {
		hpoblacion[i] = (double*)malloc(memoria_fila);
		if (hpoblacion[i] == NULL) return false;
		hdescendiente[i] = (double*)malloc(memoria_fila);
		if (hdescendiente[i] == NULL) return false;
	}

	size_t const mem_npob = sizeof(double) * hNPOB;
	hmerito_individuo = (double*)malloc(mem_npob);
	if (hmerito_individuo == NULL) return false;
	hfactible = (int*)malloc(sizeof(int) * hNPOB);
	if (hfactible == NULL) return false;
	return true;
}
// da valores a las cotas de cada variable, y marca como fijas aquellas variables que tienen el mismo valor en la cota inferior y en la superior
bool fija_cotas(double* cotasInf, double* cotasSup) {
	nvar_fijas = 0;
	for (int i = 0; i < hNVEC; i++) {
		hcotas[0][i] = cotasInf[i];
		hcotas[1][i] = cotasSup[i];
		if (abs(hcotas[1][i] - hcotas[0][i]) < hMicro) {
			hfijo[i] = 1;
			nvar_fijas++;
		}
		else {
			hfijo[i] = 0;
		}
	}
	return true;
}
// genera la población inicial de individuos
bool genera_poblacion(double* vec_central, int modo, double modulacion) {
	double semi_izq;
	double semi_dch;
	double semi_intervalo;
	double desplazamiento;
	double a;
	double v;
	double f;
	// intérvalo simétrico centrado en 'vec_central' con distribución uniforme

	for (int i = 0; i < hNPOB; i++) {
		for (int j = 0; j < hNVEC; j++) {
			if (hfijo[j] == 1) {
				hpoblacion[i][j] = hcotas[0][j];
			}
			else {
				semi_izq = vec_central[j] - hcotas[0][j];
				semi_dch = hcotas[1][j] - vec_central[j];
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
				if (v < hcotas[0][j]) {
					v = hcotas[0][j] + hMicro;
				}
				else if (v > hcotas[1][j]) {
					v = hcotas[1][j] - hMicro;
				}
				hpoblacion[i][j] = v;
			}
		}
	}

	if (incluir_x0) {
		// incluir en la población el vector de prueba inicial 'vec_central' como primer individuo
		for (int j = 0; j < hNVEC; j++) {
			hpoblacion[0][j] = vec_central[j];
		}
	}

	hres_merito = (double*)malloc(hNPOB * sizeof(double));
	bool r = hllama_merito_s_todo(hpoblacion, NBLO_K, n_hilos);
	if (r == false) {
		printf("hllama_merito_s_todo error\n");
		return false;
	}
	// seleccionar el mejor
	hmejor_merito = 1.0e+99;
	hind_mejor_merito = hNPOB + 1;
	for (int i = 0; i < hNPOB; i++) {
		v = hmerito_individuo[i] = hres_merito[i];
		hfactible[i] = 1;
		if (v < hmejor_merito) {
			hmejor_merito = v;
			hind_mejor_merito = i;
		}
	}
	free(hres_merito);
	return true;
}

static __global__ void kernel_inicia_estados_azar(azar* state, unsigned long semilla) {
	int idx = threadIdx.x + blockDim.x * blockIdx.x;
	int desde = idx * NIF_K;
	int hasta = desde + NIF_K;
	for (int i = desde; i < hasta; i++) {
		// Inicializa 'state[idx]' que es el estado para cada hilo 'idx'
		// cada hilo obtiene la misma semilla, una secuencia distinta (idx), sin desplazamiento (0)
		curand_init(semilla, idx, 0, &state[idx]);
	}
}

static __global__ void kernel_mutacion_cruze(azar* estado_gen_azar) {
	int i1;
	int i2;
	int i3;
	double v;
	int es_factible;
	int idx = threadIdx.x + blockDim.x * blockIdx.x;

	// recupera el estado del generador aleatorio asociado a este hilo

	azar ult_estado = estado_gen_azar[idx];
	int desde = idx * NIF_K;
	int hasta = desde + NIF_K;
	unsigned int r;
	double vazar;
	for (int i = desde; i < hasta; i++) {
		r = curand(&ult_estado);
		i1 = (r % NPOB);
		r = curand(&ult_estado);
		i2 = (r % NPOB);
		vazar = curand_uniform_double(&ult_estado);
		if (i1 == i2 || (prob_cop_mejor > Micro && vazar < prob_cop_mejor)) {
			if (prob_cop_mejor < 0) {
				factible[i] = 0;
				continue;
			}
			for (int j = 0; j < NVEC; j++) {
				vazar = curand_uniform_double(&ult_estado);
				if (fijo[j] == 0 && vazar <= cte_recombinacion_extra) {
					descendiente[i][j] = poblacion[ind_mejor_merito][j];
				}
				else {
					descendiente[i][j] = poblacion[i][j];
				}
			}
			factible[i] = 1;
			continue;
		}
		r = curand(&ult_estado);
		i3 = (r % NVEC);
		es_factible = 1;
		for (int j = 0; j < NVEC; j++) {
			vazar = curand_uniform_double(&ult_estado);
			if (fijo[j] == 0 && (j == i3 || vazar <= cte_recombinacion)) {
				v = poblacion[ind_mejor_merito][j] + factor_mutacion * (poblacion[i1][j] - poblacion[i2][j]);
				if (v < cotas[0][j] || v > cotas[1][j]) {
					es_factible = 0;
					break;
				}
				descendiente[i][j] = v;
			}
			else {
				descendiente[i][j] = poblacion[i][j];
			}
		}
		factible[i] = es_factible;
	}
	// salva el estado del generador aleatorio asociado a este hilo
	estado_gen_azar[idx] = ult_estado;
}
static __global__ void kernel_mutacion_cruze_1(azar* estado_gen_azar) {
	int i1;
	int i2;
	int i3;
	double v;
	int es_factible;
	int idx = threadIdx.x + blockDim.x * blockIdx.x;

	// recupera el estado del generador aleatorio asociado a este hilo

	azar ult_estado = estado_gen_azar[idx];
	unsigned int r;
	double vazar;
	r = curand(&ult_estado);
	i1 = (r % NPOB);
	r = curand(&ult_estado);
	i2 = (r % NPOB);
	vazar = curand_uniform_double(&ult_estado);
	if (i1 == i2 || (prob_cop_mejor > Micro && vazar < prob_cop_mejor)) {
		if (prob_cop_mejor < 0) {
			factible[idx] = 0;
		}
		for (int j = 0; j < NVEC; j++) {
			vazar = curand_uniform_double(&ult_estado);
			if (fijo[j] == 0 && vazar <= cte_recombinacion_extra) {
				descendiente[idx][j] = poblacion[ind_mejor_merito][j];
			}
			else {
				descendiente[idx][j] = poblacion[idx][j];
			}
		}
		factible[idx] = 1;
	}
	else {
		r = curand(&ult_estado);
		i3 = (r % NVEC);
		es_factible = 1;
		for (int j = 0; j < NVEC; j++) {
			vazar = curand_uniform_double(&ult_estado);
			if (fijo[j] == 0 && (j == i3 || vazar <= cte_recombinacion)) {
				v = poblacion[ind_mejor_merito][j] + factor_mutacion * (poblacion[i1][j] - poblacion[i2][j]);
				if (v < cotas[0][j] || v > cotas[1][j]) {
					es_factible = 0;
					break;
				}
				descendiente[idx][j] = v;
			}
			else {
				descendiente[idx][j] = poblacion[idx][j];
			}
		}
		factible[idx] = es_factible;
	}
	// salva el estado del generador aleatorio asociado a este hilo
	estado_gen_azar[idx] = ult_estado;
}
//static __global__ __launch_bounds__(512) void  kernel_seleccion() {
static __global__ void  kernel_seleccion() {
	// No parece tener ningún efecto
	//asm(".pragma \"enable_smem_spilling\";");
	double me_descendiente;
	int idx = threadIdx.x + blockDim.x * blockIdx.x;
	int desde = idx * NIF_K;
	int hasta = desde + NIF_K;
	for (int i = desde; i < hasta; i++) {
		if (factible[i] == 1) {
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
static __global__ void kernel_seleccion_1() {
	// No parece tener ningún efecto
	//asm(".pragma \"enable_smem_spilling\";");
	double me_descendiente;
	int idx = threadIdx.x + blockDim.x * blockIdx.x;
	if (factible[idx] == 1) {
		me_descendiente = merito_s(descendiente[idx]);
		if (me_descendiente < merito_individuo[idx]) {
			for (int j = 0; j < NVEC; j++) {
				poblacion[idx][j] = descendiente[idx][j];
			}
			merito_individuo[idx] = me_descendiente;
		}
	}
}
/*
*************************
Busca la solución
*************************
*/
int resuelve() {
	cudaStatus = cudaMemcpyToSymbol(ind_mejor_merito, &hind_mejor_merito, sizeof(int), size_t(0), cudaMemcpyHostToDevice);
	if (cudaStatus != cudaSuccess) {
		imprime_error("resuelve ini. cudaMemcpy error copiar ind_mejor_merito al device");
		return -6;
	}
	// podemos realizar este cálculo porque 'hpoblacion' y 'poblacion' son iguales en este momento
	double vi = hllama_merito_s(hpoblacion[hind_mejor_merito]);
	if (diferencia_relativa(vi, hmejor_merito) > hDeciMicro) {
		printf("resuelve. incongruencia en el mejor mérito de la población inicial\n%18.10e\n%18.10e\n\n", vi, hmejor_merito);
		fprintf(salida, "resuelve. incongruencia en el mejor mérito de la población inicial\n%18.10e\n%18.10e\n\n", vi, hmejor_merito);
		return -6;
	}
	double tpo_var;
	tot_tpo_muta = 0.;
	tot_tpo_sele = 0.;
	par_tpo_segs = 0.;
	tot_tpo_mins = 0.;
	generacion = 0;
	intentos = 0;
	mejor_merito_anterior = 1.0e+99;

	if (hllama_sol_mejor_merito() == false) {
		fprintf(salida, "inicio resuelve\n");
		printf("inicio resuelve\n");
		return -6;
	}
	printf("\nmejor mérito inicial %23.15e\n\n", hmejor_merito);
	fprintf(salida, "\nmejor mérito inicial  : %23.15e\n", hmejor_merito);
	fprintf(salida, "VAB                   : %23.15e\n", hVAB);
	fprintf(salida, "Impuestos             : %23.15e\n", himpuestos);
	fprintf(salida, "Cotización SS         : %23.15e\n", hcotizacionesSS);
	fprintf(salida, "Z                     : %23.15e\n", hsZ);
	fprintf(salida, "Q                     : %23.15e\n\n", hsQ);

	printf("generac. ind.m      ECT          VAB         impuestos   cotizacionSS     suma Z        suma Q      segs.p   mins.tot\n");
	printf("-------- ----- ------------ ------------- ------------- ------------- ------------- ------------- --------- ---------\n");
	fprintf(salida, "generac. ind.m      ECT          VAB         impuestos   cotizacionSS     suma Z        suma Q      segs.p   mins.tot\n");
	fprintf(salida, "-------- ----- ------------ ------------- ------------- ------------- ------------- ------------- --------- ---------\n");
	if (muestra_evolucion("inicio resuelve") == false) {
		return -6;
	}

	// prepara un estado del generador aleatorio para cada hilo
	azar* estado_gen_azar;
	cudaMalloc((void**)&estado_gen_azar, hNPOB * sizeof(azar));
	kernel_inicia_estados_azar << <NBLO_K, n_hilos >> > (estado_gen_azar, semilla);
	cudaStatus = cudaDeviceSynchronize();
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaDeviceSynchronize devuelve codigo de error tras lanzar setup_kernelMRG");
		return -6;
	}

	ftime(&tiempo_ini);
	dim3 grid(NBLO_K);
	dim3 block(n_hilos);
	while (generacion < max_generaciones) {
		ftime(&tiempo_ant);
		hfactor_mutacion = par_mutacion[0] + dis_double(gen) * (par_mutacion[1] - par_mutacion[0]);
		cudaStatus = cudaMemcpyToSymbol(factor_mutacion, &hfactor_mutacion, sizeof(double), size_t(0), cudaMemcpyHostToDevice);
		if (cudaStatus != cudaSuccess) {
			imprime_error("cudaMemcpy error copiar hfactor_mutacion al device");
			return -6;
		}
		// ---------------------------------------------------------------------------------------------------------------------------------------
		if (hNIF_K == 1) {
			kernel_mutacion_cruze_1 << <NBLO_K, n_hilos >> > (estado_gen_azar);
		}
		else {
			kernel_mutacion_cruze << <NBLO_K, n_hilos >> > (estado_gen_azar);
		}
		cudaStatus = cudaDeviceSynchronize();
		if (cudaStatus != cudaSuccess) {
			imprime_error("cudaDeviceSynchronize devuelve codigo de error tras lanzar mutacion_cruze");
			return -6;
		}
		ftime(&tiempo_act);
		tpo_var = (double)(tiempo_act.time - tiempo_ant.time) + (double)(tiempo_act.millitm - tiempo_ant.millitm) / 1000.;
		tot_tpo_muta += tpo_var;
		par_tpo_segs += tpo_var;
		tot_tpo_mins += tpo_var;

		ftime(&tiempo_ant);
		if (sol_mem_compartida > 0) {
			// Lanzar el kernel pasando el tamaño dinámico como tercer parámetro de los brackets <<< >>>
			if (hNIF_K == 1) {
				kernel_seleccion_1 << <grid, block, peticion_mem_comp >> > ();
			}
			else {
				kernel_seleccion << <grid, block, peticion_mem_comp >> > ();
			}
		}
		else {
			if (hNIF_K == 1) {
				kernel_seleccion_1 << <grid, block >> > ();
			}
			else {
				kernel_seleccion << <grid, block >> > ();
			}
		}
		cudaStatus = cudaDeviceSynchronize();
		if (cudaStatus != cudaSuccess) {
			imprime_error("cudaDeviceSynchronize devuelve codigo de error tras lanzar seleccion");
			return -6;
		}
		// ---------------------------------------------------------------------------------------------------------------------------------------
		// copia del device al host
		// ---------------------------------------------------------------------------------------------------------------------------------------
		// extraer los méritos del device para identificar al mejor individuo
		cudaStatus = cudaMemcpy(hmerito_individuo, pro_merito_individuo, hNPOB * sizeof(double), cudaMemcpyDeviceToHost);
		if (cudaStatus != cudaSuccess) {
			imprime_error("cudaMemcpy extraer merito_individuo");
			return -6;
		}
		for (int k = 0; k < hNPOB; k++) {
			if (hmerito_individuo[k] < hmejor_merito) {
				hind_mejor_merito = k;
				hmejor_merito = hmerito_individuo[k];
			}
		}
		// ---------------------------------------------------------------------------------------------------------------------------------------
		// copia del host al device
		// ---------------------------------------------------------------------------------------------------------------------------------------
		// copiar al device el indice del individuo con el mejor mérito
		// el device no necesita saber el valor del mejor mérito
		cudaStatus = cudaMemcpyToSymbol(ind_mejor_merito, &hind_mejor_merito, sizeof(int), size_t(0), cudaMemcpyHostToDevice);
		if (cudaStatus != cudaSuccess) {
			imprime_error("resuelve. cudaMemcpy error copiar ind_mejor_merito al device");
			return -6;
		}
		// ---------------------------------------------------------------------------------------------------------------------------------------
		// generación completada

		generacion++;

		ftime(&tiempo_act);
		tpo_var = (double)(tiempo_act.time - tiempo_ant.time) + (double)(tiempo_act.millitm - tiempo_ant.millitm) / 1000.;
		tot_tpo_sele += tpo_var;
		par_tpo_segs += tpo_var;
		tot_tpo_mins += tpo_var;

		res_Simulacion = comprobar_final();
		if (res_Simulacion < 0) {
			// se ha llegado el final por algún motivo
			resuelveHaTerminado();
			return res_Simulacion;
		}
	}
	// Superado el máximo de generaciones
	resuelveHaTerminado();
	return -5;
}
/*
*************************
*/
bool muestra_evolucion(const char* rotulo) {
	if (hllama_sol_mejor_merito() == false) {
		printf("%s. muestra_evolucion\n", rotulo);
		fprintf(salida, "%s. muestra_evolucion\n", rotulo);
		return false;
	}
	printf("%8d %5d %12.5e %13.6e %13.6e %13.6e %13.6e %13.6e %9.1f %9.2f\n", generacion, hind_mejor_merito, hmerito_individuo[hind_mejor_merito], hVAB, himpuestos, hcotizacionesSS, hsZ, hsQ, par_tpo_segs, tot_tpo_mins / 60.);
	fprintf(salida, "%8d %5d %12.5e %13.6e %13.6e %13.6e %13.6e %13.6e %9.1f %9.2f\n", generacion, hind_mejor_merito, hmerito_individuo[hind_mejor_merito], hVAB, himpuestos, hcotizacionesSS, hsZ, hsQ, par_tpo_segs, tot_tpo_mins / 60.);
	fflush(salida);
	return true;
}
int comprobar_final() {
	if (hmejor_merito < tolerancia) {
		// Encontrada solución
		return -2;
	}
	if (generacion == 1 || (generacion % hhisto_int) == 0) {
		// mostrar evolución
		if (muestra_evolucion("comprobar final") == false) {
			return -6;
		}
		par_tpo_segs = 0.;
	}
	if (CANCELAR) {
		// cancelado
		return -1;
	}
	if (generacion > 1 && (generacion % generaciones_control_progreso == 0)) {
		if ((mejor_merito_anterior - hmejor_merito) < mejor_merito_anterior * min_progreso) {
			// el mérito no ha progresado el valor mínimo establecido
			intentos++;
			if (intentos < max_intentos) {
				// intentar con una nueva población inicial
				genera_poblacion(vec_ini, modo_poblacion_inicial, 1.0);
				copiaPoblacionAlDevice();
				if (hprob_cop_mejor > 0) {
					hprob_cop_mejor = hprob_cop_mejor_ini * (1. - (double)intentos / (double)max_intentos);
					cudaStatus = cudaMemcpyToSymbol(prob_cop_mejor, &hprob_cop_mejor, sizeof(double), size_t(0), cudaMemcpyHostToDevice);
					printf("Reinicio. Factor dispersión: %12.5e  probabilidad copiar el mejor %11.5e\n", factor_dispersion_actualizado * factor_dispersion, hprob_cop_mejor);
					fprintf(salida, "Reinicio. Factor dispersión: %12.5e  probabilidad copiar el mejor %11.5e\n", factor_dispersion_actualizado * factor_dispersion, hprob_cop_mejor);
				}
				else {
					printf("Reinicio. Factor dispersión: %12.5e\n", factor_dispersion_actualizado * factor_dispersion);
					fprintf(salida, "Reinicio. Factor dispersión: %12.5e\n", factor_dispersion_actualizado * factor_dispersion);
				}
				max_generaciones += generacion;
				mejor_merito_anterior = 1.0e+99;
			}
			else {
				// se han superado los intentos disponibles
				intentos--;
				return -3;
			}
		}
		else {
			mejor_merito_anterior = hmejor_merito;
		}
	}
	return 0;
}
void resuelveHaTerminado() {
	ftime(&tiempo_act);
	tot_tpo_tota = (double)(tiempo_act.time - tiempo_ini.time) + (double)(tiempo_act.millitm - tiempo_ini.millitm) / 1000.;
	printf("-------- ----- ------------ ------------- ------------- ------------- ------------- ------------- --------- ---------\n");
	fprintf(salida, "-------- ----- ------------ ------------- ------------- ------------- ------------- ------------- --------- ---------\n");

	// no comprobamos si muestra_solucion da error porque la simulación está terminada
	// y mostraremos los resultados en cualquier caso
	muestra_evolucion("resuelve terminado");
	if (res_Simulacion == -1) {
		printf("\nCancelado\n");
		fprintf(salida, "\nCancelado\n");
	}
	else if (res_Simulacion == -2) {
		printf("\nEncontrada solución\n");
		fprintf(salida, "\nEncontrada solución\n");
	}
	else if (res_Simulacion == -3) {
		if (hmejor_merito < tol_aceptable) {
			printf("\nNo progresa, pero la solución puede ser aceptable\n");
			fprintf(salida, "\nNo progresa, pero la solución puede ser aceptable\n");
		}
		else {
			printf("\nNo progresa, solución no aceptable\n");
			fprintf(salida, "\nNo progresa, solución no aceptable\n");
		}
	}
	else if (res_Simulacion == -5) {
		if (hmejor_merito < tol_aceptable) {
			printf("\nSuperado el máximo de generaciones, pero la solución puede ser aceptable\n");
			fprintf(salida, "\nSuperado el máximo de generaciones, pero la solución puede ser aceptable\n");
		}
		else {
			printf("\nSuperado el máximo de generaciones, solución no aceptable\n");
			fprintf(salida, "\nSuperado el máximo de generaciones, solución no aceptable\n");
		}
	}
	else
	{
		printf("\nError, terminación inesperada\n");
		fprintf(salida, "\nError, terminación inesperada\n");
	}
	printf("\n");
	printf("tiempo de %d generaciones = %9.1f s | tiempo cada 10000 generaciones %9.1f s\n", generacion, tot_tpo_tota, 10000.0 * tot_tpo_tota / (double)generacion);
	printf("tiempo: mutación y cruce = %9.1f s | selección = %9.1f s\n", tot_tpo_muta, tot_tpo_sele);
	fprintf(salida, "\n");
	fprintf(salida, "tiempo de %d generaciones = %9.1f s | tiempo cada 10000 generaciones %9.1f s\n", generacion, tot_tpo_tota, 10000.0 * tot_tpo_tota / (double)generacion);
	fprintf(salida, "tiempo: mutación y cruce = %9.1f s | selección = %9.2f s\n\n", tot_tpo_muta, tot_tpo_sele);

	fprintf(salida, "mejor mérito final    : %23.15e\n", hmejor_merito);
	fprintf(salida, "VAB final             : %23.15e\n", hVAB);
	fprintf(salida, "Impuestos final       : %23.15e\n", himpuestos);
	fprintf(salida, "Cotización SS final   : %23.15e\n", hcotizacionesSS);
	fprintf(salida, "Z final               : %23.15e\n", hsZ);
	fprintf(salida, "Q final               : %23.15e\n\n", hsQ);

	int i_nsol = hindice_desv_bloques;
	int n_nsol = (int)hVEC_OPT_E[i_nsol];
	fprintf(salida, "Desviaciones por bloques de ecuaciones\n");
	fprintf(salida, "-------- -----------------------\n");
	for (int i = 0; i < n_nsol; i++) {
		fprintf(salida, "%8s %23.15e\n", rot_desvios[i], hVEC_OPT_E[i_nsol + 1 + i]);
	}
	fprintf(salida, "-------- -----------------------\n");
	fflush(salida);
}
bool salida_solucion(char* vfichero, char* fichero) {
	if (hllama_sol_mejor_merito() == false) {
		printf("salida_solución\n");
		fprintf(salida, "salida_solución\n");
		return false;
	}

	FILE* sal_sol;
	int nsol;

	// vector solución
	sal_sol = _fsopen(vfichero, "w", _SH_DENYWR);
	if (sal_sol != 0) {
		nsol = LCAB;
		// evitar el precio del factor que no forma parte del vector solución pero si de 'hme_sol'
		if (hop.OR_PRE_EXCLUIDO == 1) {
			fprintf(sal_sol, "%23.15e\n", hme_sol[nsol++]);
			nsol++;
		}
		else {
			nsol++;
			fprintf(sal_sol, "%23.15e\n", hme_sol[nsol++]);
		}
		for (int i = 1; i < hNVEC; i++) {
			fprintf(sal_sol, "%23.15e\n", hme_sol[nsol++]);
		}
		fclose(sal_sol);
	}
	else {
		printf("*--* No se pudo abrir el fichero [%s] para salvar el vector solución [g:%d i:%d]\n\n", vfichero, generacion, intentos - 1);
		fprintf(salida, "*--* No se pudo abrir el fichero [%s] para salvar el vector solución [g:%d i:%d]\n\n", vfichero, generacion, intentos - 1);
		return false;
	}

	// solución completa
	sal_sol = _fsopen(fichero, "w", _SH_DENYWR);
	if (sal_sol != 0) {

		// mérito
		fprintf(sal_sol, "%10d;%-8s;;%23.15e\n", generacion, "Error", hme_sol[4]);

		// vector solución ampliado por el precio del factor que no forma parte del vector solución
		// pero si de 'hme_sol'
		int n = 0;
		nsol = LCAB;
		fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "pF", 0, hme_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "pF", 1, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "pY", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "pQ", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "pD", i, hme_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "epsilon", 0, hme_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Apz", 0, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) {
			for (int j = 0; j < hNFAC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Fi", i * hNFAC + j, hme_sol[nsol++]);
			}
		}
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Ei", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Mi", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Di", i, hme_sol[nsol++]);
		if (hop.GE_INCLUYE_XP) {
			for (int i = 0; i < hNDEM; i++) {
				for (int j = 0; j < hNSEC; j++) {
					fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Xpi", i * hNSEC + j, hme_sol[nsol++]);
				}
			}
		}
		if (hop.GE_INCLUYE_AgH) {
			for (int i = 0; i < hNDEM; i++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "AgHi", i, hme_sol[nsol++]);
			}
		}

		// variables que se calculan una sola vez

		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "pz", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "pe", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "pm", i, hme_sol[nsol++]);

		// variables calculadas en el primer pase

		for (int i = 0; i < hNSEC; i++) {
			for (int j = 0; j < hNFAC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "F", i * hNFAC + j, hme_sol[nsol++]);
			}
		}
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "E", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "M", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Yp", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Yd", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Da", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Dt", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Z", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Xg", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Xv", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Q", i, hme_sol[nsol++]);
		for (int i = 0; i < hNDEM; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Td", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Tz", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Tm", i, hme_sol[nsol++]);
		for (int i = 0; i < hNDEM; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Sp", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "AgE", i, hme_sol[nsol++]);
		for (int i = 0; i < hNDEM; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "AgH", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "CssE", i, hme_sol[nsol++]);
		for (int i = 0; i < hNDEM; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "CssH", i, hme_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Sg", 0, hme_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Sc", 0, hme_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Sf", 0, hme_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "ebp", 0, hme_sol[nsol++]);
		for (int i = 0; i < hNDEM; i++) {
			for (int j = 0; j < hNSEC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Xp", i * hNSEC + j, hme_sol[nsol++]);
			}
		}
		for (int i = 0; i < hNDEM; i++) {
			for (int j = 0; j < hNFAC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "FF", i * hNFAC + j, hme_sol[nsol++]);
			}
		}
		for (int i = 0; i < hNDEM; i++) {
			for (int j = 0; j < hNFAC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Alp", i * hNFAC + j, hme_sol[nsol++]);
			}
		}
		for (int i = 0; i < hNSEC; i++) {
			for (int j = 0; j < hNSEC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "X", i * hNSEC + j, hme_sol[nsol++]);
			}
		}
		fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Ti", 0, hme_sol[nsol++]);

		// recálculos de las variables, saltamos los valores del primer paso 'LVARS_PP' (incluidas las que se calculan una sola vez)

		// nsol = LCAB + NVEC + 1 + LVARS_PP;	// innecesario, 'nsol' es continuación de lo anterior
		for (int i = 0; i < hNSEC; i++) {
			for (int j = 0; j < hNFAC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Fr", i * hNFAC + j, hme_sol[nsol++]);
			}
		}
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Er", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Mr", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Ypr", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Ydr", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Dar", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Dtr", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Zr", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Xgr", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Xvr", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Qr", i, hme_sol[nsol++]);
		for (int i = 0; i < hNDEM; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Tdr", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Tzr", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Tmr", i, hme_sol[nsol++]);
		for (int i = 0; i < hNDEM; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Spr", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "AgEr", i, hme_sol[nsol++]);
		for (int i = 0; i < hNDEM; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "AgHr", i, hme_sol[nsol++]);
		for (int i = 0; i < hNSEC; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "CssEr", i, hme_sol[nsol++]);
		for (int i = 0; i < hNDEM; i++) fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "CssHr", i, hme_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Sgr", 0, hme_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Scr", 0, hme_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Sfr", 0, hme_sol[nsol++]);
		fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "ebpr", 0, hme_sol[nsol++]);
		for (int i = 0; i < hNDEM; i++) {
			for (int j = 0; j < hNSEC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Xpr", i * hNSEC + j, hme_sol[nsol++]);
			}
		}
		for (int i = 0; i < hNDEM; i++) {
			for (int j = 0; j < hNFAC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "FFr", i * hNFAC + j, hme_sol[nsol++]);
			}
		}
		for (int i = 0; i < hNDEM; i++) {
			for (int j = 0; j < hNFAC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Alpr", i * hNFAC + j, hme_sol[nsol++]);
			}
		}
		for (int i = 0; i < hNSEC; i++) {
			for (int j = 0; j < hNSEC; j++) {
				fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Xr", i * hNSEC + j, hme_sol[nsol++]);
			}
		}
		fprintf(sal_sol, "%5d;%-8s;%5d;%23.15e\n", n++, "Tir", 0, hme_sol[nsol++]);
		fclose(sal_sol);
	}
	else {
		printf("*--* No se pudo abrir el fichero [%s] para salvar la solución [g:%d i:%d]\n\n", fichero, generacion, intentos - 1);
		fprintf(salida, "*--* No se pudo abrir el fichero [%s] para salvar la solución [g:%d i:%d]\n\n", fichero, generacion, intentos - 1);
		return false;
	}
	return true;
}

#pragma endregion

#pragma region Merito

// la parte de la aplicación relacionada con el modelo: ecuaciones, parámetros, datos iniciales y opciones de cálculo del 'mérito'

double hAYD_ADI_DEM[hNDEM]{};
double* pro_AYD_ADI_DEM;

__global__ void kernel_merito_s_todo(double* pobla, double* res, int cuantos) {
	int idx = threadIdx.x + blockDim.x * blockIdx.x;
	int indic = idx * NIF_K;
	int desde = indic * NVEC;
	double* vec_opt;
	vec_opt = (double*)malloc(NVEC * sizeof(double));
	if (vec_opt == nullptr) {
		printf("Fallo \n");
		return;
	}
	int n = desde;
	for (int j = indic; j < indic + cuantos; j++) {
		for (int i = 0; i < NVEC; i++) {
			vec_opt[i] = pobla[n];
			n++;
		}
		res[j] = merito_s(vec_opt);
	}
	free(vec_opt);
}
bool hllama_merito_s_todo(double** pobla, int bloques, int hilos) {
	double* pro_res;
	cudaStatus = cudaMalloc((void**)&pro_res, hNPOB * sizeof(double));
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaMalloc hmerito_s_todo dres");
		return false;
	}
	double* hplano;
	aplana(pobla, hNPOB, hNVEC, hplano);
	double* pro_pobla;
	bool res = copiaMtDoubleHostDevice(hplano, hNPOB * hNVEC, pro_pobla);
	if (res == false) {
		return false;
	}
	kernel_merito_s_todo << <bloques, hilos >> > (pro_pobla, pro_res, hNIF_K);
	cudaStatus = cudaDeviceSynchronize();
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaDeviceSynchronize devuelve codigo de error tras lanzar llama_merito_s");
		return false;
	}
	cudaMemcpy(hres_merito, pro_res, hNPOB * sizeof(double), cudaMemcpyDeviceToHost);
	cudaFree(pro_res);
	free(hplano);
	cudaFree(pro_pobla);
	return true;
}
__global__ void kernel_merito_s(double* vec_opt, double* res) {
	res[0] = merito_s(vec_opt);
}
double hllama_merito_s(double* vec_opt) {
	double* pro_res;
	cudaStatus = cudaMalloc((void**)&pro_res, sizeof(double));
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaMalloc hmerito_s dres");
		return -1.0;
	}
	double* dvec_opt;
	cudaStatus = cudaMalloc((void**)&dvec_opt, hNVEC * sizeof(double));
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaMalloc hmerito_s dvec_opt");
		return -1.0;
	}
	cudaMemcpy(dvec_opt, vec_opt, hNVEC * sizeof(double), cudaMemcpyHostToDevice);
	kernel_merito_s << <1, 1 >> > (dvec_opt, pro_res);
	cudaStatus = cudaDeviceSynchronize();
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaDeviceSynchronize devuelve codigo de error tras lanzar llama_merito_s");
		return -1.0;
	}
	double* hres_s;
	hres_s = (double*)malloc(sizeof(double));
	if (hres_s == nullptr) {
		fprintf(salida, "malloc llama_merito_s\n");
		return -1.0;
	}
	cudaMemcpy(hres_s, pro_res, sizeof(double), cudaMemcpyDeviceToHost);
	return *hres_s;
}

__global__ void kernel_sol_mejor_merito() {
	merito_sol(poblacion[ind_mejor_merito]);
}
bool hllama_sol_mejor_merito() {
	kernel_sol_mejor_merito << <1, 1 >> > ();
	cudaStatus = cudaDeviceSynchronize();
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaDeviceSynchronize devuelve codigo de error tras lanzar llama_merito_sol");
		return false;
	}

	// copia valores del device al host

	cudaStatus = cudaMemcpy(hVEC_OPT_E, pro_VEC_OPT_E, hLVSOL * sizeof(double), cudaMemcpyDeviceToHost);
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaMemcpy devuelve codigo de error 'hVEC_OPT_E, pro_VEC_OPT_E'");
		return false;
	}
	cudaStatus = cudaMemcpy(hme_sol, pro_me_sol, hLVAR * sizeof(double), cudaMemcpyDeviceToHost);
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaMemcpy devuelve codigo de error 'hme_sol, pro_me_sol'");
		return false;
	}
	cudaStatus = cudaMemcpyFromSymbol(&hindice_desv_bloques, indice_desv_bloques, sizeof(int));
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaMemcpyFromSymbol devuelve codigo de error '&hindice_desv_bloques, indice_desv_bloques'");
		return false;
	}
	cudaStatus = cudaMemcpyFromSymbol(&hVAB, VAB, sizeof(double));
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaMemcpyFromSymbol devuelve codigo de error '&hVAB, VAB'");
		return false;
	}
	cudaStatus = cudaMemcpyFromSymbol(&himpuestos, impuestos, sizeof(double));
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaMemcpyFromSymbol devuelve codigo de error '&himpuestos, impuestos'");
		return false;
	}
	cudaStatus = cudaMemcpyFromSymbol(&hcotizacionesSS, cotizacionesSS, sizeof(double));
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaMemcpyFromSymbol devuelve codigo de error '&hcotizacionesSS, cotizacionesSS'");
		return false;
	}
	cudaStatus = cudaMemcpyFromSymbol(&hsZ, sZ, sizeof(double));
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaMemcpyFromSymbol devuelve codigo de error '&hsZ, sZ'");
		return false;
	}
	cudaStatus = cudaMemcpyFromSymbol(&hsQ, sQ, sizeof(double));
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaMemcpyFromSymbol devuelve codigo de error '&hsQ, sQ'");
		return false;
	}
	// esta comparación es innecesaria, sería totalmente extraordinario que no se cumpliera, salvo
	// que haya un error en las funciones 'merito_s' o 'merito_sol'
	if (diferencia_relativa(hme_sol[4], hmerito_individuo[hind_mejor_merito]) > hDeciMicro) {
		int dind_mejor_merito = -1;
		cudaStatus = cudaMemcpyFromSymbol(&dind_mejor_merito, ind_mejor_merito, sizeof(int));
		if (hind_mejor_merito != dind_mejor_merito) {
			printf("generación %d. inconsistencia en el índice del individuo con el mejor mérito:\nen el device: %6d\nen el host  : %6d\n", generacion, dind_mejor_merito, hind_mejor_merito);
			fprintf(salida, "generación %d. inconsistencia en el índice del individuo con el mejor mérito:\nen el device: %6d\nen el host  : %6d\n", generacion, dind_mejor_merito, hind_mejor_merito);
			return false;
		}
		printf("generación %d. inconsistencia en el mejor mérito calculado:\nindice: %6d merito_sol:%23.15e\nindice: %6d merito_s  :%23.15e\n", generacion, dind_mejor_merito, hme_sol[4], hind_mejor_merito, hmerito_individuo[hind_mejor_merito]);
		fprintf(salida, "generación %d. inconsistencia en el mejor mérito calculado:\nindice: %6d merito_sol:%23.15e\nindice: %6d merito_s  :%23.15e\n", generacion, dind_mejor_merito, hme_sol[4], hind_mejor_merito, hmerito_individuo[hind_mejor_merito]);
	}
	return true;
}

// dejamos los '#ifdef ... #endif' porque no en esta aplicación no hay ningún #define y así es una copia exacta del modelo de la DLL
__device__ double merito_s(double* vec_opt) {
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
	double AgHi[NDEM];

	double pe[NSEC];
	double pm[NSEC];
	double pz[NSEC];
	double F[NSEC][NFAC];
	double E[NSEC];
	double M[NSEC];
	double Yp[NSEC];
	double Yd[NSEC];
	// Ypd no es una variable del modelo, es la media de Yp y Yd, para el cálculo de la optimización de los factores
	// es decisiva en comparación con usar Yp o Yd en 'uso_optimo_factores_F'
	double Ypd[NSEC];
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
#ifdef SIN_XR
	double sum_Xi[NSEC];
#else
	double sum_X;
#ifdef CONSUMO_INTERMEDIO_INDESADO
	double Xr[NSEC][NSEC]{};	// es necesario inicializar a cero cuando se usa CONSUMO_INTERMEDIO_INDESADO
#else
	double Xr[NSEC][NSEC];
#endif
#endif
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

	int n = pvec[1];
	for (int i = 0; i < NSEC; i++) py[i] = vec_opt[n++];
	for (int i = 0; i < NSEC; i++) pq[i] = vec_opt[n++];
	for (int i = 0; i < NSEC; i++) pd[i] = vec_opt[n++];
	epsilon = vec_opt[n++];
	Apz = vec_opt[n++];
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			Fi[i][j] = F[i][j] = vec_opt[n++];
		}
	}
	for (int i = 0; i < NSEC; i++) Ei[i] = E[i] = vec_opt[n++];
	for (int i = 0; i < NSEC; i++) Mi[i] = M[i] = vec_opt[n++];
	for (int i = 0; i < NSEC; i++) Di[i] = vec_opt[n++];
	if (op.GE_INCLUYE_XP) {
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NSEC; j++) {
				Xpi[i][j] = vec_opt[n++];
			}
		}
	}
	if (op.GE_INCLUYE_AgH) {
		for (int i = 0; i < NDEM; i++) {
			AgHi[i] = vec_opt[n++];
		}
	}
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
	restriccion_produccion_bruta_Z(Z, parametros.teta, parametros.xie, parametros.xid, E, Di, parametros.phi);
	consumo_intermedio_X(X, Z, parametros.ax);

	// la mayor desviación se produce casi siempre entre Yp y Yd
	produccion_factor_compuesto_Y(Yp, F, parametros.beta, parametros.b);
	utilizacion_factor_compuesto_Y(Yd, Z, parametros.ay);
	for (int i = 0; i < NSEC; i++) {
		Ypd[i] = (Yp[i] + Yd[i]) / 2.;
	}
	uso_optimo_factores_F(F, parametros.beta, pf, py, Ypd);

	coste_unitario_produccion_pz(pz, parametros.ay, py, parametros.ax, pq, datos.Ajc0, datos.Z0);
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
	if (op.GE_INCLUYE_AgH && op.GE_IMPUESTOS_AgH) {
		impuestos_directos_Td(Td, parametros.taud, pf, FF, Alp, datos.PssH0, AgHi);
	}
	else {
		impuestos_directos_Td(Td, parametros.taud, pf, FF, Alp, datos.PssH0, CeroDem);
	}
	impuestos_produccion_Tz(Tz, datos.tauz, pz, Z);
	aranceles_importacion_Tm(Tm, datos.taum, pm, M);
	ahorro_hogares_Sp(Sp, parametros.ssp, pf, FF, datos.PssH0);
	Ti = impuestos_directos_Ti(parametros.tai, pf, FF, op.INDICE_F_TRA);
	ayudas_AgE_AgH(AgE, AgH, parametros.cage, parametros.cagh, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssE, parametros.ctzsse, pf, F, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssH, parametros.ctzssh, pf, FF, Alp, op.INDICE_F_TRA);
	Sg = gobierno_Sg_Xg(Xg, parametros.ssg, parametros.mu, pq, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AgE, AgH, datos.PssH0, CssH, CssE, datos.Fue);
	double PssH0_sum = 0.;
	for (int i = 0; i < NDEM; i++) {
		PssH0_sum += datos.PssH0[i];
	}
	if (abs(PssH0_sum) < Micro) {
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
	/*
	importacion_maxima_utilidad_armington_M(M, parametros.gamma, parametros.deltam, pq, pm, Q, parametros.eta, datos.taum);
	produccion_maxima_utilidad_armington_D(Da, parametros.gamma, parametros.deltad, pq, pd, Q, parametros.eta);
	produccion_para_exportacion_E(E, parametros.teta, parametros.xie, pz, pe, Z, parametros.phi, datos.tauz, CssE, AgE, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	produccion_para_local_D(Dt, parametros.teta, parametros.xid, pz, pd, Z, parametros.phi, datos.tauz, CssE, AgE, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	*/
	importacion_local_maxima_utilidad_armington_MD(M, Da, parametros.gamma, parametros.deltam, parametros.deltad, pq, pm, pd, Q, parametros.eta, datos.taum);
	produccion_para_exportacion_local_ED(E, Dt, parametros.teta, parametros.xie, parametros.xid, pz, pe, pd, Z, parametros.phi, datos.tauz, CssE, AgE, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);

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
#ifdef SIN_XR
	// como no se calcula Xr, se calcula la suma de cada columna de X (sum_Xi), para usarla en el cálculo de la desviación del cierre del mercado
	for (int i = 0; i < NSEC; i++) {
		sum_Xi[i] = 0.;
		for (int j = 0; j < NSEC; j++) {
			sum_Xi[i] += X[j][i];
		}
	}
	// X será la diferencia entre pases
	consumo_intermedio_X_Xr(X, Zr, parametros.ax);
#else
	consumo_intermedio_X(Xr, Zr, parametros.ax);
#endif
	produccion_factor_compuesto_Y(Ypr, F, parametros.beta, parametros.b);
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
	if (op.GE_INCLUYE_AgH && op.GE_IMPUESTOS_AgH) {
		impuestos_directos_Td(Tdr, parametros.taud, pf, FFr, Alpr, datos.PssH0, AgH);
	}
	else {
		impuestos_directos_Td(Tdr, parametros.taud, pf, FFr, Alpr, datos.PssH0, CeroDem);
	}
	impuestos_produccion_Tz(Tzr, datos.tauz, pz, Zr);
	aranceles_importacion_Tm(Tmr, datos.taum, pm, M);
	ahorro_hogares_Sp(Spr, parametros.ssp, pf, FFr, datos.PssH0);
	Tir = impuestos_directos_Ti(parametros.tai, pf, FFr, op.INDICE_F_TRA);
	ayudas_AgE_AgH(AgEr, AgHr, parametros.cage, parametros.cagh, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssEr, parametros.ctzsse, pf, Fr, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssHr, parametros.ctzssh, pf, FFr, Alpr, op.INDICE_F_TRA);
	Sgr = gobierno_Sg_Xg(Xgr, parametros.ssg, parametros.mu, pq, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, AgEr, AgHr, datos.PssH0, CssHr, CssEr, datos.Fue);
	if (abs(PssH0_sum) < Micro) {
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
	/*
	importacion_maxima_utilidad_armington_M(Mr, parametros.gamma, parametros.deltam, pq, pm, Qr, parametros.eta, datos.taum);
	produccion_maxima_utilidad_armington_D(Dar, parametros.gamma, parametros.deltad, pq, pd, Qr, parametros.eta);
	produccion_para_exportacion_E(Er, parametros.teta, parametros.xie, pz, pe, Zr, parametros.phi, datos.tauz, CssEr, AgEr, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	produccion_para_local_D(Dtr, parametros.teta, parametros.xid, pz, pd, Zr, parametros.phi, datos.tauz, CssEr, AgEr, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	*/
	importacion_local_maxima_utilidad_armington_MD(Mr, Dar, parametros.gamma, parametros.deltam, parametros.deltad, pq, pm, pd, Qr, parametros.eta, datos.taum);
	produccion_para_exportacion_local_ED(Er, Dtr, parametros.teta, parametros.xie, parametros.xid, pz, pe, pd, Zr, parametros.phi, datos.tauz, CssEr, AgEr, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);

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
#ifdef SIN_XR
		dd = Qr[i] - (datos.Aji0[i] + sum_Xp + Xgr[i] + Xvr[i] + sum_Xi[i]);
#else
		sum_X = 0.;
		for (int j = 0; j < NSEC; j++) {
			sum_X += Xr[j][i];
		}
		dd = Qr[i] - (datos.Aji0[i] + sum_Xp + Xgr[i] + Xvr[i] + sum_X);
#endif
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
		if (op.GE_INCLUYE_AgH) {
			dd = AgHr[i] - AgHi[i];
			dist += dd * dd;
		}
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
#ifdef SIN_XR
			dd = X[i][j];
#else
			dd = Xr[i][j] - X[i][j];
#endif
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
__device__ double* merito_sol(double* vec_opt) {
	double pf[NFAC];
	double py[NSEC];
	double pq[NSEC];
	double pd[NSEC];
	double Fi[NSEC][NFAC];
	double Ei[NSEC];
	double Mi[NSEC];
	double Di[NSEC];
	double Xpi[NDEM][NSEC];
	double AgHi[NDEM];

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
#ifdef SIN_XR
	double sum_Xi[NSEC];
#else
	double sum_X;
#ifdef CONSUMO_INTERMEDIO_INDESADO
	double Xr[NSEC][NSEC]{};	// es necesario inicializar a cero cuando se usa CONSUMO_INTERMEDIO_INDESADO
#else
	double Xr[NSEC][NSEC];
#endif
#endif
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

	int n = pvec[1];
	for (int i = 0; i < NSEC; i++) py[i] = vec_opt[n++];
	for (int i = 0; i < NSEC; i++) pq[i] = vec_opt[n++];
	for (int i = 0; i < NSEC; i++) pd[i] = vec_opt[n++];
	epsilon = vec_opt[n++];
	Apz = vec_opt[n++];
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			Fi[i][j] = F[i][j] = vec_opt[n++];
		}
	}
	for (int i = 0; i < NSEC; i++) Ei[i] = E[i] = vec_opt[n++];
	for (int i = 0; i < NSEC; i++) Mi[i] = M[i] = vec_opt[n++];
	for (int i = 0; i < NSEC; i++) Di[i] = vec_opt[n++];
	if (op.GE_INCLUYE_XP) {
		for (int i = 0; i < NDEM; i++) {
			for (int j = 0; j < NSEC; j++) {
				Xpi[i][j] = vec_opt[n++];
			}
		}
	}
	if (op.GE_INCLUYE_AgH) {
		for (int i = 0; i < NDEM; i++) {
			AgHi[i] = vec_opt[n++];
		}
	}
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
	restriccion_produccion_bruta_Z(Z, parametros.teta, parametros.xie, parametros.xid, E, Di, parametros.phi);
	consumo_intermedio_X(X, Z, parametros.ax);
	// la mayor desviación se produce casi siempre entre Yp y Yd
	produccion_factor_compuesto_Y(Yp, F, parametros.beta, parametros.b);
	utilizacion_factor_compuesto_Y(Yd, Z, parametros.ay);
	for (int i = 0; i < NSEC; i++) {
		Ypd[i] = (Yp[i] + Yd[i]) / 2.;
	}
	uso_optimo_factores_F(F, parametros.beta, pf, py, Ypd);

	coste_unitario_produccion_pz(pz, parametros.ay, py, parametros.ax, pq, datos.Ajc0, datos.Z0);
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
	if (op.GE_INCLUYE_AgH && op.GE_IMPUESTOS_AgH) {
		impuestos_directos_Td(Td, parametros.taud, pf, FF, Alp, datos.PssH0, AgHi);
	}
	else {
		impuestos_directos_Td(Td, parametros.taud, pf, FF, Alp, datos.PssH0, CeroDem);
	}
	impuestos_produccion_Tz(Tz, datos.tauz, pz, Z);
	aranceles_importacion_Tm(Tm, datos.taum, pm, M);
	ahorro_hogares_Sp(Sp, parametros.ssp, pf, FF, datos.PssH0);
	Ti = impuestos_directos_Ti(parametros.tai, pf, FF, op.INDICE_F_TRA);
	ayudas_AgE_AgH(AgE, AgH, parametros.cage, parametros.cagh, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssE, parametros.ctzsse, pf, F, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssH, parametros.ctzssh, pf, FF, Alp, op.INDICE_F_TRA);
	Sg = gobierno_Sg_Xg(Xg, parametros.ssg, parametros.mu, pq, Td, Tz, Tm, datos.Tg0, Ti, datos.Te0, AgE, AgH, datos.PssH0, CssH, CssE, datos.Fue);
	double PssH0_sum = 0.;
	for (int i = 0; i < NDEM; i++) {
		PssH0_sum += datos.PssH0[i];
	}
	if (abs(PssH0_sum) < Micro) {
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
	/*
	importacion_maxima_utilidad_armington_M(M, parametros.gamma, parametros.deltam, pq, pm, Q, parametros.eta, datos.taum);
	produccion_maxima_utilidad_armington_D(Da, parametros.gamma, parametros.deltad, pq, pd, Q, parametros.eta);
	produccion_para_exportacion_E(E, parametros.teta, parametros.xie, pz, pe, Z, parametros.phi, datos.tauz, CssE, AgE, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	produccion_para_local_D(Dt, parametros.teta, parametros.xid, pz, pd, Z, parametros.phi, datos.tauz, CssE, AgE, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	*/
	importacion_local_maxima_utilidad_armington_MD(M, Da, parametros.gamma, parametros.deltam, parametros.deltad, pq, pm, pd, Q, parametros.eta, datos.taum);
	produccion_para_exportacion_local_ED(E, Dt, parametros.teta, parametros.xie, parametros.xid, pz, pe, pd, Z, parametros.phi, datos.tauz, CssE, AgE, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);

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
#ifdef SIN_XR
	// como no se calcula Xr, se calcula la suma de cada columna de X (sum_Xi), para usarla en el cálculo de la desviación del cierre del mercado
	for (int i = 0; i < NSEC; i++) {
		sum_Xi[i] = 0.;
		for (int j = 0; j < NSEC; j++) {
			sum_Xi[i] += X[j][i];
		}
	}
	// X será la diferencia entre pases
	consumo_intermedio_X_Xr(X, Zr, parametros.ax);
#else
	consumo_intermedio_X(Xr, Zr, parametros.ax);
#endif
	produccion_factor_compuesto_Y(Ypr, F, parametros.beta, parametros.b);
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
	if (op.GE_INCLUYE_AgH && op.GE_IMPUESTOS_AgH) {
		impuestos_directos_Td(Tdr, parametros.taud, pf, FFr, Alpr, datos.PssH0, AgH);
	}
	else {
		impuestos_directos_Td(Tdr, parametros.taud, pf, FFr, Alpr, datos.PssH0, CeroDem);
	}
	impuestos_produccion_Tz(Tzr, datos.tauz, pz, Zr);
	aranceles_importacion_Tm(Tmr, datos.taum, pm, M);
	ahorro_hogares_Sp(Spr, parametros.ssp, pf, FFr, datos.PssH0);
	Tir = impuestos_directos_Ti(parametros.tai, pf, FFr, op.INDICE_F_TRA);
	ayudas_AgE_AgH(AgEr, AgHr, parametros.cage, parametros.cagh, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, AYD_ADI_DEM);
	seguridad_social_empresas_CssE(CssEr, parametros.ctzsse, pf, Fr, op.INDICE_F_TRA);
	seguridad_social_hogares_CssH(CssHr, parametros.ctzssh, pf, FFr, Alpr, op.INDICE_F_TRA);
	Sgr = gobierno_Sg_Xg(Xgr, parametros.ssg, parametros.mu, pq, Tdr, Tzr, Tmr, datos.Tg0, Tir, datos.Te0, AgEr, AgHr, datos.PssH0, CssHr, CssEr, datos.Fue);
	if (abs(PssH0_sum) < Micro) {
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
	/*
	importacion_maxima_utilidad_armington_M(Mr, parametros.gamma, parametros.deltam, pq, pm, Qr, parametros.eta, datos.taum);
	produccion_maxima_utilidad_armington_D(Dar, parametros.gamma, parametros.deltad, pq, pd, Qr, parametros.eta);
	produccion_para_exportacion_E(Er, parametros.teta, parametros.xie, pz, pe, Zr, parametros.phi, datos.tauz, CssEr, AgEr, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	produccion_para_local_D(Dtr, parametros.teta, parametros.xid, pz, pd, Zr, parametros.phi, datos.tauz, CssEr, AgEr, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);
	*/
	importacion_local_maxima_utilidad_armington_MD(Mr, Dar, parametros.gamma, parametros.deltam, parametros.deltad, pq, pm, pd, Qr, parametros.eta, datos.taum);
	produccion_para_exportacion_local_ED(Er, Dtr, parametros.teta, parametros.xie, parametros.xid, pz, pe, pd, Zr, parametros.phi, datos.tauz, CssEr, AgEr, Apz, parametros.ctzssez, parametros.ctzagez, op.MODO_PSEUDOIMPTOS);

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
#ifdef SIN_XR
		dd = Qr[i] - (datos.Aji0[i] + sum_Xp + Xgr[i] + Xvr[i] + sum_Xi[i]);
#else
		sum_X = 0.;
		for (int j = 0; j < NSEC; j++) {
			sum_X += Xr[j][i];
		}
		dd = Qr[i] - (datos.Aji0[i] + sum_Xp + Xgr[i] + Xvr[i] + sum_X);
#endif
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
	// AgH
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
		dd = abs(Ydr[i] - Ypr[i]);
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

#ifdef SIN_XR
			dd = abs(X[i][j]);
#else
			dd = abs(Xr[i][j] - X[i][j]);
#endif
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
	else {
		// Yp, Yd, Da, Dt
		desvios_bloque[ndv++] = dist;
		desvios_bloque[ndv++] = dist;
		desvios_bloque[ndv++] = dist;
		desvios_bloque[ndv++] = dist;
	}
	if (op.GE_INCLUYE_AgH) {
		// AgHi
		for (int i = 0; i < NDEM; i++) {
			dd = abs(AgHr[i] - AgHi[i]);
			if (dd > dist_max) {
				dist_max = dd;
				idm = ndm;
				pdm = 36;
				ddm = i;
			};
			ndm++;
			dist += dd * dd;
		}
	}
	desvios_bloque[ndv++] = dist;

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
	if (op.FF_ENDOGENA == false || op.ALP_FACTOR == 0) {
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
	if (op.GE_INCLUYE_AgH) {
		for (int i = 0; i < NDEM; i++) {
			me_sol[nsol++] = AgHi[i];
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
#ifdef SIN_XR
			me_sol[nsol++] = X[i][j];
#else
			me_sol[nsol++] = Xr[i][j];
#endif
		}
	}
	me_sol[nsol++] = Tir;
	me_sol[1] = nsol;

	// cabecera	+ vector solución + detalle desvios + evolución error
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
	indice_desv_bloques = nsol;
	VEC_OPT_E[nsol++] = ndv;
	for (int i = 0; i < ndv; i++) {
		VEC_OPT_E[nsol++] = desvios_bloque[i];
	}


	VAB = 0;
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			VAB += Fr[i][j];
		}
	}
	impuestos = Tir + datos.Tg0 + datos.Te0;
	for (int i = 0; i < NSEC; i++) {
		impuestos += Tzr[i];
		impuestos += Tmr[i];
	}
	for (int i = 0; i < NDEM; i++) {
		impuestos += Tdr[i];
	}
	cotizacionesSS = 0.;
	for (int i = 0; i < NSEC; i++) {
		cotizacionesSS += CssEr[i];
	}
	for (int i = 0; i < NDEM; i++) {
		cotizacionesSS += CssHr[i];
	}
	sZ = 0;
	sQ = 0;
	for (int i = 0; i < NSEC; i++) {
		sZ += Zr[i];
		sQ += Qr[i];
	}
	return me_sol;
}

__device__ void   produccion_factor_compuesto_Y(double* Y, double F[NSEC][NFAC], double beta[NSEC][NFAC], double* b) {
	for (int i = 0; i < NSEC; i++) {
		Y[i] = b[i];
		for (int j = 0; j < NFAC; j++) {
			// cero elevado a cero es 1, por eso no hay problema si F[i][j] es cero porque beta[i][j] tambien es cero
			Y[i] *= signo(F[i][j]) * pow(abs(F[i][j]), beta[i][j]);
		}
	}
}
__device__ void   restriccion_produccion_bruta_Z(double* Z, double* teta, double* xie, double* xid, double* E, double* D, double* phi) {
	double base;
	for (int i = 0; i < NSEC; i++) {
		base = xie[i] * signo(E[i]) * pow(abs(E[i]), phi[i]) + xid[i] * signo(D[i]) * pow(abs(D[i]), phi[i]);
		Z[i] = teta[i] * signo(base) * pow(abs(base), (1. / phi[i]));
	}
}
__device__ void   consumo_intermedio_X(double X[NSEC][NSEC], double* Z, double ax[NSEC][NSEC]) {
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NSEC; j++) {
			X[i][j] = ax[i][j] * Z[i];
		}
	}
}
__device__ void   utilizacion_factor_compuesto_Y(double* Y, double* Z, double* ay) {
	for (int i = 0; i < NSEC; i++) {
		Y[i] = ay[i] * Z[i];
	}
}
__device__ void   uso_optimo_factores_F(double F[NSEC][NFAC], double beta[NSEC][NFAC], double* pf, double* py, double* Y) {
	for (int i = 0; i < NSEC; i++) {
		for (int j = 0; j < NFAC; j++) {
			F[i][j] = beta[i][j] * py[i] * Y[i] / pf[j];
		}
	}
}
__device__ void   coste_unitario_produccion_pz(double* pz, double* ay, double* py, double ax[NSEC][NSEC], double* pq, double Ajc[NSEC], double Z0[NSEC]) {
	for (int i = 0; i < NSEC; i++) {
		pz[i] = ay[i] * py[i] + Ajc[i] / Z0[i] * pq[i];
		for (int j = 0; j < NSEC; j++) {
			pz[i] += ax[i][j] * pq[j];
		}
	}
}
__device__ void   aportacion_factores_FF(double FF[NDEM][NFAC], double FF0[NDEM][NFAC], double F[NSEC][NFAC]) {
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
__device__ void   impuestos_directos_Td(double* Td, double* taud, double* pf, double FF[NDEM][NFAC], double Alp[NDEM][NFAC], double* PssH0, double AgH[NDEM]) {
	double ingresos;
	for (int i = 0; i < NDEM; i++) {
		// queda la duda de si las ayudas del gobierno tributan, aquí se supone que si
		ingresos = PssH0[i] + AgH[i];
		for (int j = 0; j < NFAC; j++) {
			ingresos += (FF[i][j] + Alp[i][j]) * pf[j];
		}
		Td[i] = taud[i] * ingresos;
	}
}
__device__ void   impuestos_produccion_Tz(double* Tz, double* tauz, double* pz, double* Z) {
	for (int i = 0; i < NSEC; i++) {
		Tz[i] = tauz[i] * Z[i] * pz[i];
	}
}
__device__ void   aranceles_importacion_Tm(double* Tm, double* taum, double* pm, double* M) {
	for (int i = 0; i < NSEC; i++) {
		Tm[i] = taum[i] * M[i] * pm[i];
	}
}
__device__ double impuestos_directos_Ti(double tai, double* pf, double FF[NDEM][NFAC], int INDICE_F_TRA) {
	double ingresos = 0.;
	for (int i = 0; i < NDEM; i++) {
		ingresos += FF[i][1 - INDICE_F_TRA];
	}
	return tai * ingresos * pf[1 - INDICE_F_TRA];
}
__device__ void   ayudas_AgE_AgH(double* AgE, double* AgH, double* cage, double* cagh, double* Td, double* Tz, double* Tm, double Tg, double Ti, double Te, double* AYD_ADI_DEM) {
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
__device__ void   ahorro_hogares_Sp(double* Sp, double* ssp, double* pf, double FF[NDEM][NFAC], double* PssH0) {

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
__device__ void   seguridad_social_empresas_CssE(double* CssE, double* ctzsse, double* pf, double F[NSEC][NFAC], int INDICE_F_TRA) {
	for (int i = 0; i < NSEC; i++) {
		CssE[i] = ctzsse[i] * F[i][INDICE_F_TRA] * pf[INDICE_F_TRA];
	}
}
__device__ void   seguridad_social_hogares_CssH(double* CssH, double* ctzssh, double* pf, double FF[NDEM][NFAC], double Alp[NDEM][NFAC], int INDICE_F_TRA) {
	for (int i = 0; i < NDEM; i++) {
		CssH[i] = ctzssh[i] * (FF[i][INDICE_F_TRA] + Alp[i][INDICE_F_TRA]) * pf[INDICE_F_TRA];
	}
}
__device__ double gobierno_Sg_Xg(double* Xg, double ssg, double* mu, double* pq, double* Td, double* Tz, double* Tm, double Tg, double Ti, double Te, double* AgE, double* AgH, double* PssH0, double* CssH, double* CssE, double Fue) {
	double Sg;
	double sPssH = 0.;
	for (int i = 0; i < NDEM; i++) {
		sPssH += PssH0[i];
	}
	double Css = 0.;
	if (abs(sPssH) < Micro) {
		for (int i = 0; i < NDEM; i++) {
			Css += CssH[i];
		}
		for (int i = 0; i < NSEC; i++) {
			Css += CssE[i];
		}
	}
	double neto = Ti + Te + Css + Fue;
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
__device__ double ahorro_exterior_Sf(double* M, double* E, double* pm, double* pe) {
	double Sf = 0.;
	for (int i = 0; i < NSEC; i++) {
		Sf += M[i] * pm[i] - E[i] * pe[i];
	}
	return Sf;
}
__device__ void   demanda_inversion_Xv(double* Xv, double* landa, double* pq, double* Sp, double Sg, double Sc, double epsilon, double Sf, double Ti, double Te) {
	// no se usa Te
	double ahorros = Sg + Sc + Sf * epsilon - Ti;
	for (int i = 0; i < NDEM; i++) {
		ahorros += Sp[i];
	}
	for (int i = 0; i < NSEC; i++) {
		Xv[i] = ahorros * landa[i] / pq[i];
	}
}
__device__ void   demanda_maxima_utilidad_StoneGeary_Xp(double Xp[NDEM][NSEC], double alfa_esen[NDEM][NSEC], double CON_ESENCIALES[NDEM][NSEC], double* pq, double* pf, double FF[NDEM][NFAC], double* Sp, double* Td, double* CssH, double* AgH, double* PssH0, int DEM_ADICIONAL_TIPO, double DEM_ADICIONAL[NDEM][NSEC], bool RENTA_FICTICIA) {
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
__device__ void   demanda_maxima_utilidad_CobbDouglas_Xp(double Xp[NDEM][NSEC], double alfa[NDEM][NSEC], double* pq, double* pf, double FF[NDEM][NFAC], double* Sp, double* Td, double* CssH, double* AgH, double* PssH0, int DEM_ADICIONAL_TIPO, double DEM_ADICIONAL[NDEM][NSEC], bool RENTA_FICTICIA) {
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
__device__ void   demanda_maxima_utilidad_CES_Xp(double Xp[NDEM][NSEC], double* eta_ces, double alfa_ces[NDEM][NSEC], double* pq, double* pf, double FF[NDEM][NFAC], double* Sp, double* Td, double* CssH, double* AgH, double* PssH0, int DEM_ADICIONAL_TIPO, double DEM_ADICIONAL[NDEM][NSEC], bool RENTA_FICTICIA) {
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
__device__ void   produccion_armington_Q(double* Q, double* gamma, double* deltam, double* deltad, double* M, double* D, double* eta) {
	for (int i = 0; i < NSEC; i++) {
		Q[i] = gamma[i] * pow(deltam[i] * signo(M[i]) * pow(abs(M[i]), eta[i]) + deltad[i] * signo(D[i]) * pow(abs(D[i]), eta[i]), 1. / eta[i]);
	}
}
__device__ void   importacion_local_maxima_utilidad_armington_MD(double* M, double* Da, double* gamma, double* deltam, double* deltad, double* pq, double* pm, double* pd, double* Q, double* eta, double* taum) {
	double expo;
	double qg;
	for (int i = 0; i < NSEC; i++) {
		expo = 1. / (1. - eta[i]);
		qg = pow(gamma[i], eta[i]) * pq[i];
		M[i] = Q[i] * pow(qg * deltam[i] / ((1. + taum[i]) * pm[i]), expo);
		Da[i] = Q[i] * pow(qg * deltad[i] / pd[i], expo);
	}
}
__device__ void   produccion_para_exportacion_local_ED(double* E, double* Dt, double* teta, double* xie, double* xid, double* pz, double* pe, double* pd, double* Z, double* phi, double* tauz, double* CssE, double* AgE, double Apz, double* ctzssez, double* ctzagez, int MODO_PSEUDOIMPTOS) {
	double basec;
	double base;
	double signo_teta;
	double abs_teta;
	double tasa_c;
	double expo;
	for (int i = 0; i < NSEC; i++) {
		if (xie[i] < Micro && xid[i] < Micro) {
			E[i] = 0.;
			Dt[i] = 0.;
			continue;
		}
		signo_teta = signo(teta[i]);
		abs_teta = abs(teta[i]);
		expo = 1. / (1. - phi[i]);
		if (MODO_PSEUDOIMPTOS == 0) {
			if (Z[i] > Micro) {
				tasa_c = (CssE[i] - AgE[i]) / Z[i];
			}
			else {
				tasa_c = 0.;
			}
		}
		else {
			tasa_c = ctzssez[i] - ctzagez[i];
		}
		basec = signo_teta * pow(abs_teta, phi[i]) * (1. + tauz[i] + tasa_c + Apz) * pz[i];
		if (xie[i] > Micro) {
			base = basec * xie[i] / pe[i];
			if (base < Micro) {
				E[i] = 0.;
			}
			else {
				E[i] = Z[i] * signo(base) * pow(abs(base), expo);
			}
		}
		else {
			E[i] = 0.;
		}
		if (xid[i] > Micro) {
			base = basec * xid[i] / pd[i];
			if (base < Micro) {
				Dt[i] = 0.;
			}
			else {
				Dt[i] = Z[i] * signo(base) * pow(abs(base), expo);
			}
		}
		else {
			Dt[i] = 0.;
		}
	}
}
__device__ double equilibrio_balance_pagos_moneda_extranjera(double* pWe, double* E, double* pWm, double* M, double Sf) {
	double ebp = Sf;
	for (int i = 0; i < NSEC; i++) {
		ebp += pWe[i] * E[i] - pWm[i] * M[i];
	}
	return ebp;
}
__device__ double precio_factor_trabajo_pFL(int INDICE_F_TRA, double PobAct, double alfa, double pF0L, double F0[NSEC][NFAC], double F[NSEC][NFAC]) {
	double var_desempleo = 0.;
	for (int i = 0; i < NSEC; i++) {
		var_desempleo += F0[i][INDICE_F_TRA] - F[i][INDICE_F_TRA];
	}
	var_desempleo /= PobAct;
	return pF0L + alfa * var_desempleo;
}
#pragma endregion

__device__ bool planoA2D(double* fte, double**& dest, int fils, int cols) {
	if (dest != nullptr) {
		for (int i = 0; i < fils; i++) {
			if (dest[i] != nullptr) {
				free(dest[i]);
			}
		}
		free(dest);
	}
	size_t const mem_primer_ind = fils * sizeof(double*);
	dest = (double**)malloc(mem_primer_ind);
	if (dest == nullptr) {
		printf("error al asignar memoria para 2D\n");
		return false;
	}
	size_t const memoria_fila = cols * sizeof(double);
	for (int i = 0; i < fils; i++) {
		dest[i] = (double*)malloc(memoria_fila);
		if (dest[i] == nullptr) {
			printf("error al asignar memoria para 2D fila %d\n", i);
			return false;
		}
	}
	int n = 0;
	for (int i = 0; i < fils; i++) {
		for (int j = 0; j < cols; j++) {
			dest[i][j] = fte[n++];
		}
	}
	return true;
}

static __global__ void kernelIni(
	int* pro_pvec,
	double* pro_me_sol,
	double* pro_VEC_OPT_E,
	double* pro_AYD_ADI_DEM,
	double* pro_desvios_bloque,
	OPCIONES* pro_opciones,
	DATOS* pro_datos,
	PARAMETROS* pro_parametros
)
{
	// hace que las 'variables device' apunten a las correspondientes 'direcciones de memoria device'
	// variable = dirección
	pvec = pro_pvec;
	me_sol = pro_me_sol;
	VEC_OPT_E = pro_VEC_OPT_E;
	AYD_ADI_DEM = pro_AYD_ADI_DEM;
	desvios_bloque = pro_desvios_bloque;
	// no se puede cambiar la dirección de una struct en C++ pero se puede crear una nueva
	op = *pro_opciones;
	datos = *pro_datos;
	parametros = *pro_parametros;
}

static __global__ void kernelIniGene(
	int* pro_fijo,
	int* pro_factible,
	double* pro_merito_individuo,
	double* pro_cotas,
	double* pro_poblacion,
	double* pro_descendiente
)
{
	// hace que las 'variables device' apunten a las correspondientes 'direcciones de memoria device'
	// variable = dirección

	fijo = pro_fijo;
	factible = pro_factible;
	merito_individuo = pro_merito_individuo;
	if (planoA2D(pro_cotas, cotas, 2, NVEC) == false) {
		printf("IniGene para cotas\n\n");
		return;
	}
	if (planoA2D(pro_poblacion, poblacion, NPOB, NVEC) == false) {
		printf("IniGene para poblacion\n\n");
		return;
	}
	if (planoA2D(pro_descendiente, descendiente, NPOB, NVEC) == false) {
		printf("IniGene para descendiente\n\n");
		return;
	}
}
static __global__ void kernelPoblacion(double* pro_poblacion)
{
	if (planoA2D(pro_poblacion, poblacion, NPOB, NVEC) == false) {
		printf("kernelPoblacion para poblacion\n\n");
		return;
	}
}
/*
static __global__ void kernelConprueba()
{
	printf("NPOB %d\n", NPOB);
	printf("NVEC %d\n", NVEC);
	printf("ind_mejor_merito %d\n", ind_mejor_merito);
	printf("histo_int %d\n", histo_int);
	printf("puntero_bloque_desviacion %d\n", puntero_bloque_desviacion);
	printf("desplazamiento_desviacion %d\n", desplazamiento_desviacion);
	printf("factor_mutacion %f\n", factor_mutacion);
	printf("cte_recombinacion %f\n", cte_recombinacion);
	printf("cte_recombinacion extra %f\n", cte_recombinacion_extra);
	printf("prob_cop_mejor %f\n", prob_cop_mejor);
	printf("VAB %f\n", VAB);
	printf("impuestos %f\n", impuestos);
	printf("sZ %f\n", sZ);
	printf("sQ %f\n", sQ);
	printf("cotizacionesSS %f\n", cotizacionesSS);
	for (int i = 0; i < N_BLO_VEC; i++) {
		printf("pvec[%d] %d\n", i, pvec[i]);
	}
	printf("me_sol[0] %f\n", me_sol[0]);
	printf("VEC_OPT_E[0] %f\n", VEC_OPT_E[0]);
	printf("AYD_ADI_DEM[0] %f\n", AYD_ADI_DEM[0]);
	printf("AYD_ADI_DEM[1] %f\n", AYD_ADI_DEM[1]);

	printf("\nop.ALP_FACTOR %f\n", op.ALP_FACTOR);
	printf("op.INDICE_F_TRA %d\n", op.INDICE_F_TRA);
	printf("op.UTILIDAD_DEMANDA %d\n", op.UTILIDAD_DEMANDA);
	printf("op.DEM_ESENCIALES %s\n\n", op.DEM_ESENCIALES ? "si" : "no");

	printf("datos.FF0\n");
	for (int i = 0; i < NDEM; i++) {
		for (int j = 0; j < NFAC; j++) {
			printf("%3d %3d %6.1f\n", i, j, datos.FF0[i][j]);
		}
	}
	printf("parametros.alfa\n");
	for (int i = 0; i < NDEM; i++) {
		printf("%3d ", i);
		for (int j = 0; j < NSEC; j++) {
			printf(" %7.5f", parametros.alfa[i][j]);
		}
		printf("\n");
	}
	int n = NVEC - 1;
	int m = NPOB - 1;
	printf("\n");
	printf("fijo          %s %s\n", fijo[0] ? "si" : "no", fijo[n] ? "si" : "no");
	printf("factible      %1d %1d\n", factible[0], factible[n]);
	printf("mérito 0      %12.5e\n", merito_individuo[0]);
	printf("mérito N      %12.5e\n", merito_individuo[m]);
	printf("\n");
	printf("cotas 0       %12f %12f\n", cotas[0][0], cotas[1][0]);
	printf("cotas 1       %12f %12f\n", cotas[0][1], cotas[1][1]);
	printf("cotas NVEC-1  %12f %12f\n", cotas[0][n], cotas[1][n]);
	printf("\n");
	printf("poblacion 0       %12f %12f\n", poblacion[0][0], poblacion[0][n]);
	printf("poblacion 1       %12f %12f\n", poblacion[1][0], poblacion[1][n]);
	printf("poblacion 2       %12f %12f\n", poblacion[m][0], poblacion[m][n]);
	printf("\n");
	printf("descendiente 1    %12f %12f\n", descendiente[0][0], descendiente[0][n]);
	printf("descendiente 2    %12f %12f\n", descendiente[1][0], descendiente[1][n]);
	printf("descendiente 3    %12f %12f\n", descendiente[m][0], descendiente[m][n]);
	printf("\n");
}
*/
void rtrim_string(char* cadena, char caracter)
{
	size_t len = strlen(cadena);
	if (!len) return;
	size_t end = len - 1;
	while (end && cadena[end] == caracter) end--;
	cadena[end + 1] = '\0';
}

double diferencia_relativa(double a, double b) {
	double mayor;
	double menor;
	// puede ocurrir que siendo a y b muy pequeños su diferencia, en tanto por uno, sea grande
	// por eso comprobamos en primer lugar la diferenia absoluta.
	if (abs(a - b) < hDeciMicro) {
		return 0.;
	}
	if (a > b) {
		mayor = a;
		menor = b;
	}
	else {
		mayor = b;
		menor = a;
	}
	double dif = 2.0 * (mayor - menor) / (mayor + menor);
	return dif;
}

void aplana(double** fte, int fils, int cols, double*& des) {
	des = (double*)malloc(fils * cols * sizeof(double));
	int n = 0;
	for (int i = 0; i < fils; i++) {
		for (int j = 0; j < cols; j++) {
			des[n++] = fte[i][j];
		}
	}
}

bool copiaIniGPU() {
	bool res;

	// copiar valores de variables del host a variables del device

	cudaStatus = cudaMemcpyToSymbol(NPOB, &hNPOB, sizeof(int), size_t(0), cudaMemcpyHostToDevice);
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaMemcpyToSymbol error hNPOB->");
		return false;
	}
	cudaStatus = cudaMemcpyToSymbol(NVEC, &hNVEC, sizeof(int), size_t(0), cudaMemcpyHostToDevice);
	cudaStatus = cudaMemcpyToSymbol(histo_int, &hhisto_int, sizeof(int), size_t(0), cudaMemcpyHostToDevice);
	cudaStatus = cudaMemcpyToSymbol(puntero_bloque_desviacion, &hpuntero_bloque_desviacion, sizeof(int), size_t(0), cudaMemcpyHostToDevice);
	cudaStatus = cudaMemcpyToSymbol(desplazamiento_desviacion, &hdesplazamiento_desviacion, sizeof(int), size_t(0), cudaMemcpyHostToDevice);

	hfactor_mutacion = par_mutacion[0] + dis_double(gen) * (par_mutacion[1] - par_mutacion[0]);
	cudaStatus = cudaMemcpyToSymbol(factor_mutacion, &hfactor_mutacion, sizeof(double), size_t(0), cudaMemcpyHostToDevice);
	cudaStatus = cudaMemcpyToSymbol(cte_recombinacion, &hcte_recombinacion, sizeof(double), size_t(0), cudaMemcpyHostToDevice);
	cudaStatus = cudaMemcpyToSymbol(cte_recombinacion_extra, &hcte_recombinacion_extra, sizeof(double), size_t(0), cudaMemcpyHostToDevice);
	cudaStatus = cudaMemcpyToSymbol(prob_cop_mejor, &hprob_cop_mejor, sizeof(double), size_t(0), cudaMemcpyHostToDevice);
	cudaStatus = cudaMemcpyToSymbol(NIF_K, &hNIF_K, sizeof(int), size_t(0), cudaMemcpyHostToDevice);

	// reserva memoria para algunas matrices en el device y las cargar con los valores iniciales de las correspondientes matrices host

	// reserva memoria en la dirección 'pro_pvec', a la que apuntará la variable device 'pvec' mediante 'kernelIni' y le
	// copia el contenido de la variable host 'hpvec'
	res = copiaMtIntHostDevice(hpvec, hN_BLO_VEC + 1, pro_pvec);
	if (res == false) {
		return false;
	}
	// reserva memoria en la dirección 'pro_me_sol' a la que apuntará la variable device 'me_sol' mediante 'kernelIni' y le
	// copia el contenido de la variable host 'hme_sol'
	hme_sol[0] = 100.1;
	res = copiaMtDoubleHostDevice(hme_sol, hLVAR, pro_me_sol);
	if (res == false) {
		return false;
	}
	res = copiaMtDoubleHostDevice(hVEC_OPT_E, hLVSOL, pro_VEC_OPT_E);
	if (res == false) {
		return false;
	}
	res = copiaMtDoubleHostDevice(hAYD_ADI_DEM, hNDEM, pro_AYD_ADI_DEM);
	if (res == false) {
		return false;
	}
	res = copiaMtDoubleHostDevice(hdesvios_bloque, hMAX_DESVIOS_BLOQUE, pro_desvios_bloque);
	if (res == false) {
		return false;
	}

	// copiar las estructuras hopciones, hdatos y hparametros al device

	cudaStatus = cudaMalloc((void**)&pro_opciones, sizeof(OPCIONES));
	cudaStatus = cudaMemcpy(pro_opciones, &hop, sizeof(OPCIONES), cudaMemcpyHostToDevice);

	cudaStatus = cudaMalloc((void**)&pro_datos, sizeof(DATOS));
	cudaStatus = cudaMemcpy(pro_datos, &hdatos, sizeof(DATOS), cudaMemcpyHostToDevice);

	cudaStatus = cudaMalloc((void**)&pro_parametros, sizeof(PARAMETROS));
	cudaStatus = cudaMemcpy(pro_parametros, &hparametros, sizeof(PARAMETROS), cudaMemcpyHostToDevice);
	kernelIni << <1, 1 >> > (
		pro_pvec,
		pro_me_sol,
		pro_VEC_OPT_E,
		pro_AYD_ADI_DEM,
		pro_desvios_bloque,
		pro_opciones,
		pro_datos,
		pro_parametros
		);
	cudaStatus = cudaGetLastError();
	if (cudaStatus != cudaSuccess) {
		imprime_error("lanzar kernelIni");
		return false;
	}
	// esperar a que termine el kernel y si hubo errores en su ejecucion
	cudaStatus = cudaDeviceSynchronize();
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaDeviceSynchronize devuelve codigo de error tras lanzar kernelIni");
		return false;
	}

	return true;
}

bool copiaGeneticoGPU() {
	float free_m, total_m, used_m;
	size_t free_t, total_t;
	bool res;

	// matrices del algoritmo

	// valores fijos
	res = copiaMtIntHostDevice(hfijo, hNVEC, pro_fijo);
	if (res == false) {
		return false;
	}
	// factible
	res = copiaMtIntHostDevice(hfactible, hNPOB, pro_factible);
	if (res == false) {
		return false;
	}
	res = copiaMtDoubleHostDevice(hmerito_individuo, hNPOB, pro_merito_individuo);
	if (res == false) {
		return false;
	}
	// cotas
	double* hplano;
	aplana(hcotas, 2, hNVEC, hplano);
	res = copiaMtDoubleHostDevice(hplano, 2 * hNVEC, pro_cotas);
	if (res == false) {
		return false;
	}
	free(hplano);
	// poblacion
	aplana(hpoblacion, hNPOB, hNVEC, hplano);
	res = copiaMtDoubleHostDevice(hplano, hNPOB * hNVEC, pro_poblacion);
	if (res == false) {
		return false;
	}
	free(hplano);
	// descendientes
	aplana(hdescendiente, hNPOB, hNVEC, hplano);
	res = copiaMtDoubleHostDevice(hplano, hNPOB * hNVEC, pro_descendiente);
	if (res == false) {
		return false;
	}
	free(hplano);

	// relaciona los nombres de algunas variables device con los datos puestos en la memoria device mediante 'copiaMt???HostDEvice'
	kernelIniGene << <1, 1 >> > (
		pro_fijo,
		pro_factible,
		pro_merito_individuo,
		pro_cotas,
		pro_poblacion,
		pro_descendiente
		);
	cudaStatus = cudaGetLastError();
	if (cudaStatus != cudaSuccess) {
		imprime_error("lanzar kernelIniGene");
		return false;
	}
	// esperar a que termine el kernel y si hubo errores en su ejecucion
	cudaStatus = cudaDeviceSynchronize();
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaDeviceSynchronize devuelve codigo de error tras lanzar kernelIniGene");
		return false;
	}

	/*
	// comprobamos que las variables device apuntan a la memoria que les corresponden
	kernelConprueba << <1, 1 >> > ();
	cudaStatus = cudaGetLastError();
	if (cudaStatus != cudaSuccess) {
		imprime_error("lanzar kernelConprueba");
		return false;
	}
	// esperar a que termine el kernel y si hubo errores en su ejecucion
	cudaStatus = cudaDeviceSynchronize();
	if (cudaStatus != cudaSuccess) {
		imprime_error("cudaDeviceSynchronize devuelve codigo de error tras lanzar kernelConprueba");
		return false;
	}
	*/

	cudaMemGetInfo(&free_t, &total_t);
	free_m = (float)(free_t / mega_byte);
	total_m = (float)(total_t / mega_byte);
	used_m = total_m - free_m;
	printf("tamaño matriz de población : %14u %9.2f MB\n", (unsigned long)ta_pob, ta_pob / mega_byte);
	printf("tamaño variables me_sol    : %14u %9.2f MB\n", (unsigned long)ta_me_sol, ta_me_sol / mega_byte);
	printf("tamaño variables VEC_OPT_E : %14u %9.2f MB\n", (unsigned long)ta_VEC_OPT_E, ta_VEC_OPT_E / mega_byte);
	printf("cudaLimitMallocHeapSize    : %14u %9.2f MB\n", (unsigned long)limite_mem_comp, limite_mem_comp / mega_byte);
	printf("memoria usada              :                %9.2f MB\n", used_m);
	printf("memoria libre              : %14zu %9.2f MB\n\n", free_t, free_m);

	fprintf(salida, "tamaño matriz de población : %14u %9.2f MB\n", (unsigned long)ta_pob, ta_pob / mega_byte);
	fprintf(salida, "tamaño variables me_sol    : %14u %9.2f MB\n", (unsigned long)ta_me_sol, ta_me_sol / mega_byte);
	fprintf(salida, "tamaño variables VEC_OPT_E : %14u %9.2f MB\n", (unsigned long)ta_VEC_OPT_E, ta_VEC_OPT_E / mega_byte);
	fprintf(salida, "cudaLimitMallocHeapSize    : %14u %9.2f MB\n", (unsigned long)limite_mem_comp, limite_mem_comp / mega_byte);
	fprintf(salida, "memoria usada              :                %9.2f MB\n", used_m);
	fprintf(salida, "memoria libre              : %14zu %9.2f MB\n\n", free_t, free_m);
	return true;
}

bool copiaPoblacionAlDevice() {
	double* hplano;
	aplana(hpoblacion, hNPOB, hNVEC, hplano);
	bool res = copiaMtDoubleHostDevice(hplano, hNPOB * hNVEC, pro_poblacion);
	if (res == false) {
		return false;
	}
	free(hplano);
	kernelPoblacion << <1, 1 >> > (pro_poblacion);
	cudaStatus = cudaGetLastError();
	if (cudaStatus != cudaSuccess) {
		imprime_error("copiaPoblacionAlDevice. lanzar kernelPoblacion");
		return false;
	}
	cudaStatus = cudaDeviceSynchronize();
	if (cudaStatus != cudaSuccess) {
		imprime_error("copiaPoblacionAlDevice. cudaDeviceSynchronize devuelve codigo de error tras lanzar kernelPoblacion");
		return false;
	}
	cudaStatus = cudaMemcpyToSymbol(ind_mejor_merito, &hind_mejor_merito, sizeof(int), size_t(0), cudaMemcpyHostToDevice);
	cudaStatus = cudaMemcpy(pro_merito_individuo, hmerito_individuo, hNPOB * sizeof(double), cudaMemcpyHostToDevice);
	if (cudaStatus != cudaSuccess) {
		imprime_error("copiaPoblacionAlDevice. cudaMemcpy copiar merito_individuo al device");
		return false;
	}
	return true;
}

bool comprueba_carpeta(const char* senda) {
	char* carpeta;
	carpeta = (char*)malloc(512);
	strcpy(carpeta, senda);
	int n = strlen(carpeta);
	int i;
	for (i = 0; i < n; i++) {
		if (carpeta[i] == '\\') carpeta[i] = '/';
	}
	i = 0;
	while (i < n - 1) {
		if (carpeta[i] == '/' && carpeta[i + 1] == '/') {
			for (int j = i + 1; j <= n; j++) {
				carpeta[j] = carpeta[j + 1];
			}
			n--;
		}
		i++;
	}
	while (n > 0 && carpeta[n] != '/') {
		n--;
	}
	carpeta[n] = 0;
	if (_mkdir(carpeta) == 0) {
		printf("\nSe ha creado la carpeta %s\n\n", carpeta);
		free(carpeta);
		return true;
	}
	else {
		if (errno != EEXIST) {
			printf("\nError al crear la carpeta %s\n\n", carpeta);
			free(carpeta);
			return false;
		}
	}
	free(carpeta);
	return true;
}

int main(int argc, char* argv[]) {
	// Configura la salida de la consola a UTF-8 o similar cambia tambien la puntuación lo cual es inconveniente
	//SetConsoleOutputCP(CP_UTF8);
	SetConsoleOutputCP(1252);
	float free_m, total_m, used_m;
	size_t free_t, total_t;
	cudaMemGetInfo(&free_t, &total_t);
	free_m = (float)(free_t / mega_byte);
	total_m = (float)(total_t / mega_byte);
	used_m = total_m - free_m;
	printf("memoria:\n");
	printf("total %16zu (%12.2f MB)\n", total_t, total_m);
	printf("libre %16zu (%12.2f MB)\n", free_t, free_m);
	printf("usada                   %12.2f MB\n\n", used_m);

	hpvec = (int*)malloc((hN_BLO_VEC + 1) * sizeof(int));
	hpvec[0] = 0;
	for (int i = 1; i < hN_BLO_VEC + 1; i++) {
		hpvec[i] = hpvec[i - 1] + hlen_var[i - 1];
	}

	// fichero auxiliar de parámetros cuyo valores prevalecen sobre los del caso
	FILE* fop;
	bool datos_nuevos = true;
	char c[64];
	if (argc == 1 || argc == 2) {
		if (argc == 1) {
			fopen_s(&fop, "C:\\MEGA\\MEGA_GPU\\Casos\\Actual\\par_caso_cuda.txt", "r");
			printf("argumentos leidos de \n%s\n\n", "C:\\MEGA\\MEGA_GPU\\Casos\\Actual\\par_caso_cuda.txt");
		}
		else {
			fopen_s(&fop, argv[1], "r");
			printf("argumentos leidos de \n%s\n\n", argv[1]);

		}
		if (fop == nullptr) {
			if (argc == 2) {
				printf("\nNo se pudo abrir el fichero:\n%s\n\n", argv[1]);
			}
			else {
				printf("No se pudo abrir el fichero:\n%s\n\n", "C:\\MEGA\\MEGA_GPU\\Casos\\Actual\\par_caso_cuda.txt");
			}
			return -1;
		}
		if (fgets(descripcion_caso, 511, fop) == NULL) {
			fclose(fop);
			printf("error lectura descripcion_caso\n");
			return -1;
		};
		if (fgets(fichero_caso, 383, fop) == NULL) {
			fclose(fop);
			printf("error lectura fichero_caso\n");
			return -1;
		};
		if (fgets(senda_salidas, 383, fop) == NULL) {
			fclose(fop);
			printf("error lectura senda_salidas\n");
			return -1;
		};
		if (fgets(senda_v_solucion, 383, fop) == NULL) {
			fclose(fop);
			printf("error lectura senda_v_solucion\n");
			return -1;
		};
		if (fgets(senda_solucion, 383, fop) == NULL) {
			fclose(fop);
			printf("error lectura senda_solucion\n");
			return -1;
		};
		if (fgets(c, 64, fop) == NULL) {
			fclose(fop);
			printf("error lectura n_hilos\n");
			return -1;
		};
		n_hilos = atoi(c);
		if (fgets(c, 64, fop) == NULL) {
			fclose(fop);
			printf("error lectura hNPOB\n");
			return -1;
		};
		hNPOB = atoi(c);
		if (fgets(c, 64, fop) == NULL) {
			fclose(fop);
			printf("error lectura NBLO_K\n");
			return -1;
		};
		NBLO_K = atoi(c);
		if (fgets(c, 64, fop) == NULL) {
			fclose(fop);
			printf("error hNIF_K\n");
			return -1;
		};
		hNIF_K = atoi(c);
		if (hNPOB != (NBLO_K * n_hilos * hNIF_K)) {
			printf("error. inconsistencia en las dimensiones para los kernels: hNPOB %d != (NBLO_K * n_hilos * hNIF_K) %d\n", hNPOB, NBLO_K * n_hilos * hNIF_K);
			return -1;
		}
		if (fgets(c, 64, fop) == NULL) {
			fclose(fop);
			printf("error lectura mem_compartida\n");
			return -1;
		};
		sol_mem_compartida = atoi(c);
		if (fgets(c, 64, fop) == NULL) {
			if (feof(fop)) {
				datos_nuevos = false;
			}
			else {
				fclose(fop);
				printf("error lectura max_generaciones\n");
				return -1;
			}
		}
		if (datos_nuevos) {
			max_generaciones = atoi(c);
			if (fgets(c, 64, fop) == NULL) {
				fclose(fop);
				printf("error lectura semilla\n");
				return -1;
			};
			semilla = atoi(c);
			if (fgets(c, 64, fop) == NULL) {
				fclose(fop);
				printf("error lectura hprob_cop_mejor\n");
				return -1;
			};
			hprob_cop_mejor = atof(c);
		}
		fclose(fop);
		rtrim_string(descripcion_caso, '\n');
		rtrim_string(fichero_caso, '\n');
		rtrim_string(senda_salidas, '\n');
		rtrim_string(senda_v_solucion, '\n');
		rtrim_string(senda_solucion, '\n');
	}
	else if (argc == 3) {
		printf("argumentos leidos de \n%s\n%s\n\n", argv[1], argv[2]);
		char senda_fte[384];
		char senda_sal[384];
		char senda_sol[384];
		// datos CUDA
		datos_nuevos = false;
		fopen_s(&fop, argv[1], "r");
		if (fop == nullptr) {
			printf("\nNo se pudo abrir el fichero:\n%s\n\n", argv[1]);
			return -1;
		}
		if (fgets(senda_fte, 383, fop) == NULL) {
			fclose(fop);
			printf("error lectura senda fuente\n");
			return -1;
		};
		if (fgets(senda_sal, 383, fop) == NULL) {
			fclose(fop);
			printf("error lectura senda salidas\n");
			return -1;
		};
		if (fgets(senda_sol, 383, fop) == NULL) {
			fclose(fop);
			printf("error lectura senda solución\n");
			return -1;
		};
		if (fgets(c, 64, fop) == NULL) {
			fclose(fop);
			printf("error lectura n_hilos\n");
			return -1;
		};
		n_hilos = atoi(c);
		if (fgets(c, 64, fop) == NULL) {
			fclose(fop);
			printf("error lectura hNPOB\n");
			return -1;
		};
		hNPOB = atoi(c);
		if (fgets(c, 64, fop) == NULL) {
			fclose(fop);
			printf("error lectura NBLO_K\n");
			return -1;
		};
		NBLO_K = atoi(c);
		if (fgets(c, 64, fop) == NULL) {
			fclose(fop);
			printf("error hNIF_K\n");
			return -1;
		};
		hNIF_K = atoi(c);
		if (hNPOB != (NBLO_K * n_hilos * hNIF_K)) {
			printf("error. inconsistencia en las dimensiones para los kernels: hNPOB %d != (NBLO_K * n_hilos * hNIF_K) %d\n", hNPOB, NBLO_K * n_hilos * hNIF_K);
			return -1;
		}
		if (fgets(c, 64, fop) == NULL) {
			fclose(fop);
			printf("error lectura mem_compartida\n");
			return -1;
		};
		sol_mem_compartida = atoi(c);
		fclose(fop);
		rtrim_string(senda_fte, '\n');
		rtrim_string(senda_sal, '\n');
		rtrim_string(senda_sol, '\n');
		sprintf(descripcion_caso, "%s", argv[2]);
		sprintf(fichero_caso, "%s%s.txt", senda_fte, argv[2]);
		sprintf(senda_salidas, "%s%s_sal.log", senda_sal, argv[2]);
		sprintf(senda_v_solucion, "%s%s_vsol.txt", senda_sol, argv[2]);
		sprintf(senda_solucion, "%s%s_modelo.txt", senda_sol, argv[2]);
	}
	else {
		printf("número de argumentos %d incorrecto\n\n", argc);
		return -1;
	}
	comprueba_carpeta(senda_salidas);
	comprueba_carpeta(senda_v_solucion);
	comprueba_carpeta(senda_solucion);

	// fichero con todas las opciones, datos, parámetros y argumentos del caso
	fopen_s(&fop, fichero_caso, "r");
	if (fop == nullptr) {
		printf("\nNo se pudo abrir el fichero:\n%s\n", fichero_caso);
		return -1;
	}

	// opciones
	fgets(c, 32, fop);
	hop.OR_PRE_EXCLUIDO = atoi(c);
	fgets(c, 32, fop);
	hop.PRECIO_F_EXCLUIDO = atof(c);
	fgets(c, 32, fop);
	hop.VALOR_F_TRA = atof(c);
	fgets(c, 32, fop);
	hop.ALFA_PHILLIPS = atof(c);
	fgets(c, 32, fop);
	hop.GE_INCLUYE_XP = atoi(c) == 0 ? false : true;
	fgets(c, 32, fop);
	hop.GE_INCLUYE_AgH = atoi(c) == 0 ? false : true;
	fgets(c, 32, fop);
	hop.GE_IMPUESTOS_AgH = atoi(c) == 0 ? false : true;
	fgets(c, 32, fop);
	hop.FF_ENDOGENA = atoi(c) == 0 ? false : true;
	fgets(c, 32, fop);
	hop.ALP_FACTOR = atof(c);
	fgets(c, 32, fop);
	hop.INDICE_F_TRA = atoi(c);
	fgets(c, 32, fop);
	hop.UTILIDAD_DEMANDA = atoi(c);
	fgets(c, 32, fop);
	hop.DEM_ESENCIALES = atoi(c) == 0 ? false : true;
	fgets(c, 32, fop);
	hop.DEM_ADICIONAL_TIPO = atoi(c);
	for (int i = 0; i < hNDEM; i++) {
		for (int j = 0; j < hNSEC; j++) {
			fgets(c, 32, fop);
			hop.DEM_ADICIONAL[i][j] = atof(c);
		}
	}
	for (int i = 0; i < hNDEM; i++) {
		for (int j = 0; j < hNSEC; j++) {
			fgets(c, 32, fop);
			hop.AYD_ADICIONAL[i][j] = atof(c);
		}
	}
	for (int i = 0; i < hNDEM; i++) {
		hAYD_ADI_DEM[i] = 0.;
		for (int j = 0; j < hNSEC; j++) {
			hAYD_ADI_DEM[i] += hop.AYD_ADICIONAL[i][j];
		}
	}
	for (int i = 0; i < hNDEM; i++) {
		for (int j = 0; j < hNSEC; j++) {
			fgets(c, 32, fop);
			hop.CON_ESENCIALES[i][j] = atof(c);
		}
	}
	fgets(c, 32, fop);
	hop.RENTA_FICTICIA = atoi(c) == 0 ? false : true;
	fgets(c, 32, fop);
	hop.MODO_PSEUDOIMPTOS = atoi(c);
	fgets(c, 32, fop);
	hop.OPT_DESVIOS = atoi(c);
	fgets(c, 32, fop);
	hop.EQ_BAL_PAGOS = atoi(c) == 0 ? false : true;

	// datos
	fgets(c, 32, fop);
	hdatos.pF0[0] = atof(c);
	fgets(c, 32, fop);
	hdatos.pF0[1] = atof(c);
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hdatos.pY0[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hdatos.pQ0[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hdatos.pD0[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hdatos.pWm[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hdatos.pWe[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hdatos.E0[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hdatos.M0[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hdatos.D0[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hdatos.tauz[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hdatos.taum[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		for (int j = 0; j < hNFAC; j++) {
			fgets(c, 32, fop);
			hdatos.F0[i][j] = atof(c);
		}
	}
	for (int i = 0; i < hNDEM; i++) {
		fgets(c, 32, fop);
		hdatos.PssH0[i] = atof(c);
	}
	for (int i = 0; i < hNDEM; i++) {
		for (int j = 0; j < hNFAC; j++) {
			fgets(c, 32, fop);
			hdatos.FF0[i][j] = atof(c);
		}
	}
	for (int i = 0; i < hNDEM; i++) {
		for (int j = 0; j < hNFAC; j++) {
			fgets(c, 32, fop);
			hdatos.Alp0[i][j] = atof(c);
		}
	}
	fgets(c, 32, fop);
	hdatos.epsilon0 = atof(c);
	fgets(c, 32, fop);
	hdatos.Tg0 = atof(c);
	fgets(c, 32, fop);
	hdatos.Ti0 = atof(c);
	fgets(c, 32, fop);
	hdatos.Te0 = atof(c);
	fgets(c, 32, fop);
	hdatos.Sf0 = atof(c);
	fgets(c, 32, fop);
	hdatos.Fue = atof(c);
	fgets(c, 32, fop);
	hdatos.PobAct = atof(c);
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hdatos.Z0[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hdatos.Ajc0[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hdatos.Aji0[i] = atof(c);
	}

	// parámetros
	for (int i = 0; i < hNSEC; i++) {
		for (int j = 0; j < hNSEC; j++) {
			fgets(c, 32, fop);
			hparametros.ax[i][j] = atof(c);
		}
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hparametros.ay[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		for (int j = 0; j < hNFAC; j++) {
			fgets(c, 32, fop);
			hparametros.beta[i][j] = atof(c);
		}
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hparametros.b[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hparametros.teta[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hparametros.xie[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hparametros.xid[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hparametros.phi[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hparametros.cage[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hparametros.ctzsse[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hparametros.mu[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hparametros.landa[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hparametros.gamma[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hparametros.deltam[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hparametros.deltad[i] = atof(c);
	}
	for (int i = 0; i < hNSEC; i++) {
		fgets(c, 32, fop);
		hparametros.eta[i] = atof(c);
	}
	for (int i = 0; i < hNDEM; i++) {
		fgets(c, 32, fop);
		hparametros.taud[i] = atof(c);
	}
	for (int i = 0; i < hNDEM; i++) {
		fgets(c, 32, fop);
		hparametros.cagh[i] = atof(c);
	}
	for (int i = 0; i < hNDEM; i++) {
		fgets(c, 32, fop);
		hparametros.ssp[i] = atof(c);
	}
	for (int i = 0; i < hNDEM; i++) {
		fgets(c, 32, fop);
		hparametros.ctzssh[i] = atof(c);
	}
	for (int i = 0; i < hNDEM; i++) {
		fgets(c, 32, fop);
		hparametros.eta_ces[i] = atof(c);
	}
	for (int i = 0; i < hNDEM; i++) {
		for (int j = 0; j < hNSEC; j++) {
			fgets(c, 32, fop);
			hparametros.alfa_ces[i][j] = atof(c);
		}
	}
	for (int i = 0; i < hNDEM; i++) {
		for (int j = 0; j < hNSEC; j++) {
			fgets(c, 32, fop);
			hparametros.alfa[i][j] = atof(c);
		}
	}
	for (int i = 0; i < hNDEM; i++) {
		for (int j = 0; j < hNSEC; j++) {
			fgets(c, 32, fop);
			hparametros.alfa_esen[i][j] = atof(c);
		}
	}
	fgets(c, 32, fop);
	hparametros.ssg = atof(c);
	fgets(c, 32, fop);
	hparametros.tai = atof(c);

	// argumentos
	double hpar[64];
	int hipar = 0;
	fgets(c, 32, fop);
	hpar[hipar++] = max_intentos = atoi(c);
	fgets(c, 32, fop);
	hpar[hipar++] = n_hilos;
	fgets(c, 32, fop);
	if (datos_nuevos == true) {
		hpar[hipar++] = max_generaciones;
	}
	else {
		hpar[hipar++] = max_generaciones = atoi(c);
	}
	fgets(c, 32, fop);
	hpar[hipar++] = tolerancia = atof(c);
	fgets(c, 32, fop);
	hpar[hipar++] = tol_aceptable = atof(c);
	fgets(c, 32, fop);
	hpar[hipar++] = generaciones_control_progreso = atoi(c);
	fgets(c, 32, fop);
	hpar[hipar++] = min_progreso = atof(c);
	fgets(c, 32, fop);
	hpar[hipar++] = umbral_regularizacion = atof(c);
	fgets(c, 32, fop);
	hpar[hipar++] = fraccion_regularizacion = atof(c);
	fgets(c, 32, fop);
	hpar[hipar++] = hhisto_int = atoi(c);
	fgets(c, 32, fop);
	hpar[hipar++] = hhisto_sol = atoi(c);
	fgets(c, 32, fop);
	hpar[hipar++] = modo_poblacion_inicial = atoi(c);
	fgets(c, 32, fop);
	hpar[hipar++] = modo_reinicio_poblacion = atoi(c);
	fgets(c, 32, fop);
	hpar[hipar++] = factor_dispersion = atof(c);
	fgets(c, 32, fop);
	hpar[hipar++] = factor_sigma = atof(c);
	fgets(c, 32, fop);
	hpar[hipar++] = variacion_dispersion = atof(c);
	fgets(c, 32, fop);
	hpar[hipar++] = num_tramos_lhs = atoi(c);
	fgets(c, 32, fop);
	hpar[hipar++] = hNPOB;
	fgets(c, 32, fop);
	hpar[hipar++] = par_mutacion[0] = atof(c);
	fgets(c, 32, fop);
	hpar[hipar++] = par_mutacion[1] = atof(c);
	fgets(c, 32, fop);
	hpar[hipar++] = hcte_recombinacion = atof(c);
	fgets(c, 32, fop);
	hpar[hipar++] = hcte_recombinacion_extra = atof(c);
	fgets(c, 32, fop);
	hpar[hipar++] = hcontrol_factibilidad = atoi(c) == 0 ? false : true;
	fgets(c, 32, fop);
	if (datos_nuevos == true) {
		hpar[hipar++] = semilla;
	}
	else {
		hpar[hipar++] = semilla = atoi(c);
	}
	fgets(c, 32, fop);
	hpar[hipar++] = poner_el_mejor_primero = atoi(c) == 0 ? false : true;
	fgets(c, 32, fop);
	hpar[hipar++] = incluir_x0 = atoi(c) == 0 ? false : true;
	fgets(c, 32, fop);
	int nvec = atoi(c);
	hpar[hipar++] = hNVEC = nvec;
	fgets(c, 32, fop);
	hpar[hipar++] = estadistica_pob_ini = atoi(c);
	fgets(c, 32, fop);
	hpar[hipar++] = desviaciones_relativas = atoi(c);
	fgets(c, 32, fop);
	if (datos_nuevos == true) {
		hpar[hipar++] = hprob_cop_mejor;
	}
	else {
		hpar[hipar++] = hprob_cop_mejor = atof(c);
	}
	double* cotasInf_h;
	double* cotasSup_h;
	double* vec;
	cotasInf_h = (double*)malloc(nvec * sizeof(double));
	cotasSup_h = (double*)malloc(nvec * sizeof(double));
	vec = (double*)malloc(nvec * sizeof(double));
	for (int i = 0; i < nvec; i++) {
		fgets(c, 32, fop);
		cotasInf_h[i] = atof(c);
		fgets(c, 32, fop);
		vec[i] = atof(c);
		fgets(c, 32, fop);
		cotasSup_h[i] = atof(c);
	}
	fclose(fop);

	size_t limit = 0;
	cudaDeviceGetLimit(&limit, cudaLimitStackSize);
	printf("cudaLimitStackSize     : %14u %9.2f MB\n", (unsigned long)limit, limit / mega_byte);
	cudaDeviceGetLimit(&limit, cudaLimitPrintfFifoSize);
	printf("cudaLimitPrintfFifoSize: %14u %9.2f MB\n", (unsigned long)limit, limit / mega_byte);
	cudaDeviceGetLimit(&limit, cudaLimitMallocHeapSize);
	printf("cudaLimitMallocHeapSize: %14u %9.2f MB\n", (unsigned long)limit, limit / mega_byte);
	ta_pob = (unsigned)(sizeof(double) * (hNPOB + 1) * (hNVEC + 1));
	printf("poblacion              : %14u %9.2f MB\n", (unsigned long)ta_pob, ta_pob / mega_byte);
	ta_me_sol = hLVAR * sizeof(double);
	printf("variables me_sol       : %14u %9.2f MB\n", (unsigned long)ta_me_sol, ta_me_sol / mega_byte);
	ta_VEC_OPT_E = hLVSOL * sizeof(double);
	printf("variables VEC_OPT_E    : %14u %9.2f MB\n", (unsigned long)ta_VEC_OPT_E, ta_VEC_OPT_E / mega_byte);
	// establecer un límite suficiente para la memoria de las matrices en el device (no se asigna memoria), debe hacerse
	// antes de lanzar ningón kernel
	cudaStatus = cudaDeviceSetLimit(cudaLimitMallocHeapSize, 16 * ta_pob);
	if (cudaStatus != cudaSuccess) {
		imprime_error("Error al ejecutar cudaDeviceSetLimit");
		return false;
	}
	cudaDeviceGetLimit(&limite_mem_comp, cudaLimitMallocHeapSize);
	printf("Cambiando cudaLimitMallocHeapSize\n");
	printf("cudaLimitMallocHeapSize: %14u %9.2f MB\n", (unsigned long)limite_mem_comp, limite_mem_comp / mega_byte);

	int extendida = 0;
	soluciona(hpar, cotasInf_h, cotasSup_h, vec, extendida, senda_salidas);
	free(cotasInf_h);
	free(cotasSup_h);
	free(vec);
}
