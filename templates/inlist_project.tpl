&binary_job

   inlist_names(1) = 'inlist1'
   inlist_names(2) = 'inlist2'

   evolve_both_stars = .true.

/ ! end of binary_job namelist


&binary_controls

   ! initial conditions
   m1 = {{M1}}d0                    ! donor mass, Msun (initially more massive)
   m2 = {{M2}}d0                    ! accretor mass, Msun
   initial_period_in_days = {{PORB}}d0

   ! mass transfer
   mdot_scheme = '{{MDOT_SCHEME}}'
   mass_transfer_alpha = 0d0        ! CE-free baseline (set 0 always)
   mass_transfer_beta = {{BETA}}d0  ! fraction ejected near accretor; eta_acc = 1 - beta
   mass_transfer_delta = 0d0
   limit_retention_by_mdot_edd = .false.

   ! angular momentum loss: defaults keep isotropic re-emission + systemic winds (do_jdot_ml/ls = .true.)
   jdot_multiplier = 1d0

/ ! end of binary_controls namelist
