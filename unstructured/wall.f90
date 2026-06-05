! This module provides routines for defining the wall_dist field.
! wall_dist is a field representing the approximate distance to the
! inner wall.  wall_dist = 0 at the inner wall, and grad(wall_dist)
! gives the inward normal gradient at the inner wall.
module wall
  implicit none

contains

  subroutine calc_wall_dist
    use basic
    use arrays
    use sparse
    use mesh_mod
    use m3dc1_nint
    use matrix_mod
    use field
    use boundary_conditions

    implicit none

    type(matrix_type) :: wall_matrix
    integer :: itri, numelms, ibound, ier
    integer :: i, index, numnodes, icounter_t
    character(len=8) :: skip_wall_dist_solve
    vectype, dimension(dofs_per_element, dofs_per_element) :: mat_dofs

    call set_matrix_index(wall_matrix, wall_mat_index)
    call create_mat(wall_matrix, 1, 1, icomplex, 1)

if (ispradapt .eq. 1) then
    call create_field(wall_dist, "wall_dist")
else
    call create_field(wall_dist)
endif
    wall_dist = 0.

    ibound = ior(BOUNDARY_DIRICHLET,BOUNDARY_NEUMANN)

    numelms = local_elements()

    do itri=1, numelms
       call define_element_quadrature(itri,int_pts_main,5)
       call define_fields(itri,0,1,0)

       mat_dofs = intxx3(mu79(:,:,OP_GS),nu79(:,:,OP_GS),ri_79)

       call apply_boundary_mask(itri, ibound, mat_dofs, tags=BOUND_FIRSTWALL)

       call insert_block(wall_matrix, itri, 1, 1, mat_dofs, MAT_ADD)
    end do

    ! Flush the accumulated element contributions, then apply boundary
    ! row replacements before the final assembly. This matches the
    ! matrix lifecycle used elsewhere in the codebase.
    call flush(wall_matrix)
    call boundary_wall_dist(wall_dist%vec, wall_matrix)
    numnodes = owned_nodes()
    do icounter_t=1,numnodes
       i = nodes_owned(icounter_t)
       index = node_index(wall_dist%vec, i, 1)
       call identity_row(wall_matrix, index)
       call identity_row(wall_matrix, index+1)
       call identity_row(wall_matrix, index+2)
       call identity_row(wall_matrix, index+3)
       call identity_row(wall_matrix, index+4)
       call identity_row(wall_matrix, index+5)
    end do
    call finalize(wall_matrix)
    
    call get_environment_variable("M3DC1_SKIP_WALL_DIST_SOLVE", skip_wall_dist_solve)
    if (trim(skip_wall_dist_solve) .eq. "1") then
       if(myrank.eq.0 .and. iprint.ge.1) print *, &
            "M3DC1_SKIP_WALL_DIST_SOLVE=1: keeping zero wall_dist smoke-field"
    else
       call newsolve(wall_matrix,wall_dist%vec,ier)
    endif

    call destroy_mat(wall_matrix)

  end subroutine calc_wall_dist

  subroutine destroy_wall_dist
    use arrays

    implicit none

    call destroy_field(wall_dist)
  end subroutine destroy_wall_dist


  subroutine boundary_wall_dist(rhs, mat)
    use basic
    use field
    use arrays
    use matrix_mod
    use boundary_conditions
    implicit none
    
    type(vector_type) :: rhs
    type(matrix_type), optional :: mat
    
    integer :: i, izone, izonedim, numnodes, icounter_t
    real :: normal(2), curv(3), x, z, phi

    logical :: is_boundary
    vectype, dimension(dofs_per_node) :: temp, temp1
    
    integer :: index
    
    if(myrank.eq.0 .and. iprint.ge.2) print *, "boundary_wall_dist called"
    
    numnodes = owned_nodes()
    do icounter_t=1,numnodes
       i = nodes_owned(icounter_t)
       index = node_index(rhs, i, 1)
       
       call boundary_node(i,is_boundary,izone,izonedim,normal,curv,x,phi,z, &
            BOUND_FIRSTWALL)
       if(.not.is_boundary) cycle
       
       temp = 0.
!       temp(2) = -normal(1)
!       temp(3) = -normal(2)
       temp(2) = -1.
       call rotate_dofs(temp, temp1, normal, curv, -1)
       temp = temp1

       call set_dirichlet_bc(index,rhs,temp,normal,curv,izonedim,mat)
       call set_normal_bc(index,rhs,temp,normal,curv,izonedim,mat)
    end do
  end subroutine boundary_wall_dist
  
end module wall
