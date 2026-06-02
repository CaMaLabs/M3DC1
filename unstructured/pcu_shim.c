#include "PCU_C.h"
#include <mpi.h>
#include <stdbool.h>
#include <stddef.h>

static int pcu_shim_ready = 0;

static void pcu_shim_init_mpi(void)
{
  if (!pcu_shim_ready) {
    int flag = 0;
    MPI_Initialized(&flag);
    pcu_shim_ready = flag;
  }
}

void PCU_Init(int *argc, char ***argv)
{
  int flag = 0;
  MPI_Initialized(&flag);
  if (!flag) {
    MPI_Init(argc, argv);
  }
  pcu_shim_ready = 1;
}

void PCU_Finalize(void)
{
  pcu_shim_ready = 0;
}

int PCU_Comm_Init(PCU_t* h)
{
  if (h == NULL) return PCU_FAILURE;
  h->ptr = (void*)0x1;
  pcu_shim_init_mpi();
  return PCU_SUCCESS;
}

int PCU_Comm_Free(PCU_t* h)
{
  if (h == NULL) return PCU_FAILURE;
  h->ptr = NULL;
  return PCU_SUCCESS;
}

int PCU_Comm_Self(PCU_t h)
{
  int rank = 0;
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  return rank;
}

int PCU_Comm_Peers(PCU_t h)
{
  int size = 1;
  MPI_Comm_size(MPI_COMM_WORLD, &size);
  return size;
}

int PCU_Comm_Dup(PCU_t h, PCU_Comm* newcomm)
{
  if (newcomm == NULL) return PCU_FAILURE;
  *newcomm = MPI_COMM_WORLD;
  return PCU_SUCCESS;
}

void PCU_Comm_Split(PCU_t h, int color, int key, PCU_t* newpcu)
{
  (void)h;
  (void)color;
  (void)key;
  if (newpcu != NULL) newpcu->ptr = (void*)0x1;
}

void PCU_Comm_Begin(PCU_t h)
{
  (void)h;
}

int PCU_Comm_Pack(PCU_t h, int to_rank, const void* data, size_t size)
{
  (void)h; (void)to_rank; (void)data; (void)size;
  return PCU_SUCCESS;
}

int PCU_Comm_Send(PCU_t h)
{
  (void)h;
  return PCU_SUCCESS;
}

bool PCU_Comm_Receive(PCU_t h)
{
  (void)h;
  return false;
}

bool PCU_Comm_Listen(PCU_t h)
{
  (void)h;
  return false;
}

int PCU_Comm_Sender(PCU_t h)
{
  (void)h;
  return -1;
}

bool PCU_Comm_Unpacked(PCU_t h)
{
  (void)h;
  return true;
}

int PCU_Comm_Unpack(PCU_t h, void* data, size_t size)
{
  (void)h; (void)data; (void)size;
  return PCU_SUCCESS;
}

void PCU_Comm_Order(PCU_t h, bool on)
{
  (void)h; (void)on;
}

void PCU_Barrier(PCU_t h)
{
  (void)h;
  MPI_Barrier(MPI_COMM_WORLD);
}

static void pcu_allreduce(void* buf, void* out, int count, MPI_Datatype type, MPI_Op op)
{
  MPI_Allreduce(buf, out, count, type, op, MPI_COMM_WORLD);
}

void PCU_Add_Doubles(PCU_t h, double* p, size_t n) { (void)h; pcu_allreduce(p, p, (int)n, MPI_DOUBLE, MPI_SUM); }
double PCU_Add_Double(PCU_t h, double x) { (void)h; double y = x; pcu_allreduce(&x, &y, 1, MPI_DOUBLE, MPI_SUM); return y; }
void PCU_Min_Doubles(PCU_t h, double* p, size_t n) { (void)h; pcu_allreduce(p, p, (int)n, MPI_DOUBLE, MPI_MIN); }
double PCU_Min_Double(PCU_t h, double x) { (void)h; double y = x; pcu_allreduce(&x, &y, 1, MPI_DOUBLE, MPI_MIN); return y; }
void PCU_Max_Doubles(PCU_t h, double* p, size_t n) { (void)h; pcu_allreduce(p, p, (int)n, MPI_DOUBLE, MPI_MAX); }
double PCU_Max_Double(PCU_t h, double x) { (void)h; double y = x; pcu_allreduce(&x, &y, 1, MPI_DOUBLE, MPI_MAX); return y; }
void PCU_Add_Ints(PCU_t h, int* p, size_t n) { (void)h; pcu_allreduce(p, p, (int)n, MPI_INT, MPI_SUM); }
int PCU_Add_Int(PCU_t h, int x) { (void)h; int y = x; pcu_allreduce(&x, &y, 1, MPI_INT, MPI_SUM); return y; }
void PCU_Add_Longs(PCU_t h, long* p, size_t n) { (void)h; pcu_allreduce(p, p, (int)n, MPI_LONG, MPI_SUM); }
long PCU_Add_Long(PCU_t h, long x) { (void)h; long y = x; pcu_allreduce(&x, &y, 1, MPI_LONG, MPI_SUM); return y; }
void PCU_Exscan_Ints(PCU_t h, int* p, size_t n) { (void)h; pcu_allreduce(p, p, (int)n, MPI_INT, MPI_SUM); }
int PCU_Exscan_Int(PCU_t h, int x) { (void)h; return x; }
void PCU_Exscan_Longs(PCU_t h, long* p, size_t n) { (void)h; pcu_allreduce(p, p, (int)n, MPI_LONG, MPI_SUM); }
long PCU_Exscan_Long(PCU_t h, long x) { (void)h; return x; }
void PCU_Add_SizeTs(PCU_t h, size_t* p, size_t n) { (void)h; pcu_allreduce(p, p, (int)n, MPI_UNSIGNED_LONG, MPI_SUM); }
size_t PCU_Add_SizeT(PCU_t h, size_t x) { (void)h; size_t y = x; pcu_allreduce(&x, &y, 1, MPI_UNSIGNED_LONG, MPI_SUM); return y; }
void PCU_Min_SizeTs(PCU_t h, size_t* p, size_t n) { (void)h; pcu_allreduce(p, p, (int)n, MPI_UNSIGNED_LONG, MPI_MIN); }
size_t PCU_Min_SizeT(PCU_t h, size_t x) { (void)h; size_t y = x; pcu_allreduce(&x, &y, 1, MPI_UNSIGNED_LONG, MPI_MIN); return y; }
void PCU_Max_SizeTs(PCU_t h, size_t* p, size_t n) { (void)h; pcu_allreduce(p, p, (int)n, MPI_UNSIGNED_LONG, MPI_MAX); }
size_t PCU_Max_SizeT(PCU_t h, size_t x) { (void)h; size_t y = x; pcu_allreduce(&x, &y, 1, MPI_UNSIGNED_LONG, MPI_MAX); return y; }
void PCU_Min_Ints(PCU_t h, int* p, size_t n) { (void)h; pcu_allreduce(p, p, (int)n, MPI_INT, MPI_MIN); }
int PCU_Min_Int(PCU_t h, int x) { (void)h; int y = x; pcu_allreduce(&x, &y, 1, MPI_INT, MPI_MIN); return y; }
void PCU_Max_Ints(PCU_t h, int* p, size_t n) { (void)h; pcu_allreduce(p, p, (int)n, MPI_INT, MPI_MAX); }
int PCU_Max_Int(PCU_t h, int x) { (void)h; int y = x; pcu_allreduce(&x, &y, 1, MPI_INT, MPI_MAX); return y; }
void PCU_Max_Longs(PCU_t h, long* p, size_t n) { (void)h; pcu_allreduce(p, p, (int)n, MPI_LONG, MPI_MAX); }
long PCU_Max_Long(PCU_t h, long x) { (void)h; long y = x; pcu_allreduce(&x, &y, 1, MPI_LONG, MPI_MAX); return y; }
int PCU_Or(PCU_t h, int c) { (void)h; int y = c; pcu_allreduce(&c, &y, 1, MPI_INT, MPI_LOR); return y; }
int PCU_And(PCU_t h, int c) { (void)h; int y = c; pcu_allreduce(&c, &y, 1, MPI_INT, MPI_LAND); return y; }

int PCU_Proc_Self(PCU_t h) { return PCU_Comm_Self(h); }
int PCU_Proc_Peers(PCU_t h) { return PCU_Comm_Peers(h); }

int PCU_Comm_Write(PCU_t h, int to_rank, const void* data, size_t size)
{
  (void)h; (void)to_rank; (void)data; (void)size;
  return PCU_SUCCESS;
}

bool PCU_Comm_Read(PCU_t h, int* from_rank, void** data, size_t* size)
{
  (void)h; (void)from_rank; (void)data; (void)size;
  return false;
}

void PCU_Debug_Open(PCU_t h) { (void)h; }
void PCU_Debug_Print(PCU_t h, const char* format, ...) { (void)h; (void)format; }
bool PCU_Comm_Initialized(PCU_t h) { return h.ptr != NULL; }
int PCU_Comm_Packed(PCU_t h, int to_rank, size_t* size) { (void)h; (void)to_rank; if (size) *size = 0; return PCU_SUCCESS; }
int PCU_Comm_From(PCU_t h, int* from_rank) { (void)h; if (from_rank) *from_rank = -1; return PCU_SUCCESS; }
int PCU_Comm_Received(PCU_t h, size_t* size) { (void)h; if (size) *size = 0; return PCU_SUCCESS; }
void* PCU_Comm_Extract(PCU_t h, size_t size) { (void)h; (void)size; return NULL; }
int PCU_Comm_Rank(PCU_t h, int* rank) { if (rank) *rank = PCU_Comm_Self(h); return PCU_SUCCESS; }
int PCU_Comm_Size(PCU_t h, int* size) { if (size) *size = PCU_Comm_Peers(h); return PCU_SUCCESS; }
void PCU_Protect(void) {}
double PCU_Time(void) { return MPI_Wtime(); }
double PCU_GetMem(void) { return 0.0; }
