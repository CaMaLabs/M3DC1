#ifndef M3DC1_SCOREC_PCU_LEGACY_SHIM_H
#define M3DC1_SCOREC_PCU_LEGACY_SHIM_H

// Pull in the SCOREC-provided C++ PCU interface first.
#include_next "PCU.h"
#include "PCU_C.h"
#include "pcu_util.h"

// Legacy no-handle PCU API compatibility for M3DC1 SCOREC sources.
// Modern SCOREC uses handle-based C API; this shim maintains one active
// communicator handle and maps old calls onto the new interface.
static inline PCU_t& m3dc1_pcu_legacy_handle() {
  static PCU_t h = {nullptr};
  if (h.ptr == nullptr)
    PCU_Comm_Init(&h);
  return h;
}

static inline int m3dc1_PCU_Comm_Self() {
  return ::PCU_Comm_Self(m3dc1_pcu_legacy_handle());
}

static inline int m3dc1_PCU_Comm_Peers() {
  return ::PCU_Comm_Peers(m3dc1_pcu_legacy_handle());
}

static inline void m3dc1_PCU_Comm_Begin() {
  ::PCU_Comm_Begin(m3dc1_pcu_legacy_handle());
}

static inline int m3dc1_PCU_Comm_Pack(int to_rank, const void* data, size_t size) {
  return ::PCU_Comm_Pack(m3dc1_pcu_legacy_handle(), to_rank, data, size);
}

static inline int m3dc1_PCU_Comm_Send() {
  return ::PCU_Comm_Send(m3dc1_pcu_legacy_handle());
}

static inline bool m3dc1_PCU_Comm_Listen() {
  return ::PCU_Comm_Listen(m3dc1_pcu_legacy_handle());
}

static inline int m3dc1_PCU_Comm_Sender() {
  return ::PCU_Comm_Sender(m3dc1_pcu_legacy_handle());
}

static inline bool m3dc1_PCU_Comm_Unpacked() {
  return ::PCU_Comm_Unpacked(m3dc1_pcu_legacy_handle());
}

static inline int m3dc1_PCU_Comm_Unpack(void* data, size_t size) {
  return ::PCU_Comm_Unpack(m3dc1_pcu_legacy_handle(), data, size);
}

static inline int m3dc1_PCU_Comm_Write(int to_rank, const void* data, size_t size) {
  return ::PCU_Comm_Write(m3dc1_pcu_legacy_handle(), to_rank, data, size);
}

static inline bool m3dc1_PCU_Comm_Read(int* from_rank, void** data, size_t* size) {
  return ::PCU_Comm_Read(m3dc1_pcu_legacy_handle(), from_rank, data, size);
}

static inline void m3dc1_PCU_Barrier() {
  ::PCU_Barrier(m3dc1_pcu_legacy_handle());
}

static inline void m3dc1_PCU_Exscan_Ints(int* p, size_t n) {
  ::PCU_Exscan_Ints(m3dc1_pcu_legacy_handle(), p, n);
}

static inline void m3dc1_PCU_Max_Doubles(double* p, size_t n) {
  ::PCU_Max_Doubles(m3dc1_pcu_legacy_handle(), p, n);
}

static inline int m3dc1_PCU_Max_Int(int x) {
  return ::PCU_Max_Int(m3dc1_pcu_legacy_handle(), x);
}

static inline void m3dc1_PCU_Min_Doubles(double* p, size_t n) {
  ::PCU_Min_Doubles(m3dc1_pcu_legacy_handle(), p, n);
}

static inline PCU_Comm m3dc1_PCU_Get_Comm() {
  static PCU_Comm cached = MPI_COMM_NULL;
  if (cached != MPI_COMM_NULL)
    MPI_Comm_free(&cached);
  ::PCU_Comm_Dup(m3dc1_pcu_legacy_handle(), &cached);
  return cached;
}

static inline void m3dc1_PCU_Switch_Comm(PCU_Comm comm) {
  PCU_t& h = m3dc1_pcu_legacy_handle();
  if (h.ptr != nullptr) {
    delete static_cast<pcu::PCU*>(h.ptr);
    h.ptr = nullptr;
  }
  pcu::PCU* pcu_obj = new pcu::PCU(comm);
  h.ptr = static_cast<void*>(pcu_obj);
}

#ifdef PCU_COMM_PACK
#undef PCU_COMM_PACK
#endif
#define PCU_COMM_PACK(to_rank, object) \
  PCU_Comm_Pack((to_rank), &(object), sizeof(object))

#ifdef PCU_COMM_UNPACK
#undef PCU_COMM_UNPACK
#endif
#define PCU_COMM_UNPACK(object) \
  PCU_Comm_Unpack(&(object), sizeof(object))

#define PCU_Comm_Self() m3dc1_PCU_Comm_Self()
#define PCU_Comm_Peers() m3dc1_PCU_Comm_Peers()
#define PCU_Comm_Begin() m3dc1_PCU_Comm_Begin()
#define PCU_Comm_Pack(to_rank, data, size) m3dc1_PCU_Comm_Pack((to_rank), (data), (size))
#define PCU_Comm_Send() m3dc1_PCU_Comm_Send()
#define PCU_Comm_Listen() m3dc1_PCU_Comm_Listen()
#define PCU_Comm_Sender() m3dc1_PCU_Comm_Sender()
#define PCU_Comm_Unpacked() m3dc1_PCU_Comm_Unpacked()
#define PCU_Comm_Unpack(data, size) m3dc1_PCU_Comm_Unpack((data), (size))
#define PCU_Comm_Write(to_rank, data, size) m3dc1_PCU_Comm_Write((to_rank), (data), (size))
#define PCU_Comm_Read(from_rank, data, size) m3dc1_PCU_Comm_Read((from_rank), (data), (size))
#define PCU_Barrier() m3dc1_PCU_Barrier()
#define PCU_Exscan_Ints(p, n) m3dc1_PCU_Exscan_Ints((p), (n))
#define PCU_Max_Doubles(p, n) m3dc1_PCU_Max_Doubles((p), (n))
#define PCU_Max_Int(x) m3dc1_PCU_Max_Int((x))
#define PCU_Min_Doubles(p, n) m3dc1_PCU_Min_Doubles((p), (n))
#define PCU_Get_Comm() m3dc1_PCU_Get_Comm()
#define PCU_Switch_Comm(comm) m3dc1_PCU_Switch_Comm((comm))

#endif
