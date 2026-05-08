module runaway_advection
  implicit none
  private
  public :: runaway_advection_initialize, runaway_advection_step

contains

  subroutine runaway_advection_initialize
    implicit none
  end subroutine runaway_advection_initialize

  subroutine runaway_advection_step(pdt)
    implicit none
    real, intent(in) :: pdt
  end subroutine runaway_advection_step

end module runaway_advection
