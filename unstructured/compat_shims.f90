subroutine mark_vector_for_solutiontransfer(v)
  use vector_mod
  implicit none
  type(vector_type), intent(inout) :: v
  ! no-op for PETSc vectors in this build path
end subroutine mark_vector_for_solutiontransfer

subroutine get_zone(itri, izone)
  use mesh_mod, only: mesh_get_zone => get_zone
  implicit none
  integer, intent(in) :: itri
  integer, intent(out) :: izone
  call mesh_get_zone(itri, izone)
end subroutine get_zone

subroutine get_zone_index(itri, izone)
  use mesh_mod, only: mesh_get_zone_index => get_zone_index
  implicit none
  integer, intent(in) :: itri
  integer, intent(out) :: izone
  call mesh_get_zone_index(itri, izone)
end subroutine get_zone_index

subroutine populate_adjacency_matrix()
  use mesh_mod, only: mesh_populate_adjacency => populate_adjacency_matrix
  implicit none
  call mesh_populate_adjacency()
end subroutine populate_adjacency_matrix

subroutine clear_adjacency_matrix()
  use mesh_mod, only: mesh_clear_adjacency => clear_adjacency_matrix
  implicit none
  call mesh_clear_adjacency()
end subroutine clear_adjacency_matrix

subroutine newsolve_with_guess(mat, v, x_guess, ierr)
  use matrix_mod, only: matrix_type, newsolve
  use vector_mod, only: vector_type
  implicit none
  type(matrix_type), intent(in) :: mat
  type(vector_type), intent(inout) :: v
  type(vector_type), intent(in) :: x_guess
  integer, intent(out) :: ierr

  call newsolve(mat, v, ierr)
end subroutine newsolve_with_guess

subroutine zero_mat(mat)
  use matrix_mod, only: matrix_type, clear_mat
  implicit none
  type(matrix_type), intent(inout) :: mat
  call clear_mat(mat)
end subroutine zero_mat

subroutine update_mat(mat)
  use matrix_mod, only: matrix_type, finalize
  implicit none
  type(matrix_type), intent(inout) :: mat
  call finalize(mat)
end subroutine update_mat

subroutine allocate_kspits()
  use petsc_matrix_mod, only: kspits, maxnumofsolves
  implicit none
  if (.not. allocated(kspits)) then
    allocate(kspits(maxnumofsolves))
    kspits = 0.
  end if
end subroutine allocate_kspits
