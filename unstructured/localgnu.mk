CC = mpicc.mpich
CPP = mpicxx.mpich
F90 = mpif90.mpich
F77 = mpif90.mpich
LOADER = mpif90.mpich
LDOPTS += -Wl,--allow-shlib-undefined -fno-lto

# Use the local PETSc 3.25 install discovered through pkg-config.
PETSC_PKGCFG := PKG_CONFIG_PATH=/root/petsc-3.25-install/lib/pkgconfig
PETSC_CFLAGS := $(shell $(PETSC_PKGCFG) pkg-config --cflags petsc)
PETSC_LIBS := $(shell $(PETSC_PKGCFG) pkg-config --libs petsc)
PETSC_FROOT := $(shell $(PETSC_PKGCFG) pkg-config --variable=includedir petsc)
HDF5_CFLAGS := $(shell pkg-config --cflags hdf5-serial)
HDF5_LIBS := $(shell pkg-config --libs hdf5-serial)
NETCDF_F_CFLAGS := $(shell pkg-config --cflags netcdf-fortran)
NETCDF_F_LIBS := $(shell pkg-config --libs netcdf-fortran)
GSL_FFTW_LIBS := $(shell pkg-config --libs gsl fftw3)
SCOREC_PREFIX := /root/scorec-mpich-install
M3DC1_SCOREC_PREFIX := /root/m3dc1-scorec-mpich-install
SCOREC_CFLAGS := -I$(SCOREC_PREFIX)/include -I$(M3DC1_SCOREC_PREFIX)/include
SCOREC_LIBS := -L$(M3DC1_SCOREC_PREFIX)/lib -L$(SCOREC_PREFIX)/lib \
	-Wl,-rpath,$(M3DC1_SCOREC_PREFIX)/lib -Wl,-rpath,$(SCOREC_PREFIX)/lib \
	-lm3dc1_scorec -lpumi -lapf -lapf_metis -lapf_zoltan -lcrv -lsam -lspr -lma \
	-lparma -lmds -lgmi -llion -lmth -lpcu -lparmetis -lmetis

FOPTS = $(OPTS) -DPETSC_VERSION=325 -DUSEBLAS -c -fdefault-real-8 -cpp -fallow-argument-mismatch -ffree-line-length-512 -fno-lto
CCOPTS = -c -DPETSC_VERSION=325 -O2
R8OPTS = -fdefault-real-8

ifeq ($(OPT), 1)
  FOPTS := $(FOPTS) -O2
else
  FOPTS := $(FOPTS) -g
  CCOPTS := $(CCOPTS) -g
endif

ifeq ($(PAR), 1)
  FOPTS := $(FOPTS) -DUSEPARTICLES
endif

ifeq ($(OMP), 1)
  FOPTS := $(FOPTS) -fopenmp
  CCOPTS := $(CCOPTS) -fopenmp
  LDOPTS := $(LDOPTS) -fopenmp
endif

F90OPTS = $(F90FLAGS) $(FOPTS)
F77OPTS = $(F77FLAGS) $(FOPTS)

INCLUDE = $(PETSC_CFLAGS) -I$(PETSC_FROOT) -I$(SRCDIR) $(HDF5_CFLAGS) $(NETCDF_F_CFLAGS) $(SCOREC_CFLAGS)
LIBS = $(SCOREC_LIBS) $(PETSC_LIBS) $(HDF5_LIBS) -lhdf5hl_fortran -lhdf5_fortran -lhdf5_hl -lhdf5 $(NETCDF_F_LIBS) $(GSL_FFTW_LIBS) -llapack -lblas -lz -ldl -lstdc++ -lapf -lapf_metis -lapf_zoltan

%.o : %.c
	$(CC)  $(CCOPTS) $(INCLUDE) $< -o $@

%.o : %.cpp
	$(CPP) $(CCOPTS) $(INCLUDE) $< -o $@

%.o: %.f
	$(F77) $(F77OPTS) $(INCLUDE) $< -o $@

%.o: %.for
	$(F77) $(F77OPTS) $(INCLUDE) $< -o $@

%.o: %.F
	$(F77) $(F77OPTS) $(INCLUDE) $< -o $@

%.o: %.f90
	$(F90) $(F90OPTS) $(INCLUDE) -fPIC $< -o $@
