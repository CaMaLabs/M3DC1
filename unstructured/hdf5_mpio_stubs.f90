! Serial-HDF5 compatibility stubs for builds without parallel HDF5 symbols.
subroutine h5pset_fapl_mpio_f(plist_id, comm, info, hdferr)
  implicit none
  integer(kind=8), intent(in) :: plist_id
  integer, intent(in) :: comm
  integer, intent(in) :: info
  integer, intent(out) :: hdferr
  hdferr = 0
end subroutine h5pset_fapl_mpio_f

subroutine h5pset_dxpl_mpio_f(plist_id, xfer_mode, hdferr)
  implicit none
  integer(kind=8), intent(in) :: plist_id
  integer, intent(in) :: xfer_mode
  integer, intent(out) :: hdferr
  hdferr = 0
end subroutine h5pset_dxpl_mpio_f
