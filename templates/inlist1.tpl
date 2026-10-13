! Donor (Star 1, initially more massive) — rendered from inlist1.tpl

&star_job

   mesa_dir = ''
   show_log_description_at_start = .false.
   pgstar_flag = .false.
   create_pre_main_sequence_model = .true.

/ ! end of star_job namelist


&eos
/ ! end of eos namelist


&kap
   use_Type2_opacities = .true.
   Zbase = {{Z}}d0
/ ! end of kap namelist


&controls

   ! initial conditions
   initial_mass = {{M1}}d0
   initial_z = {{Z}}d0

   ! stellar wind (RGB-sensitive; Reimers, scaled)
   cool_wind_RGB_scheme = 'Reimers'
   Reimers_scaling_factor = {{WIND1}}d0

   ! termination cap (binary run ends when either star stops)
   max_age = {{MAXAGE}}d0
   max_model_number = {{MAXMODEL}}

   ! flash-phase settings (from 1M_pre_ms_to_wd inlist_to_start_he_core_flash;
   ! must be active from the start — switching mid-run breaks energy conservation)
   energy_eqn_option = 'eps_grav'
   use_gold2_tolerances = .true.
   delta_lgL_He_limit = 0.01d0

   ! output
   extra_terminal_output_file = 'log1'
   log_directory = 'LOGS1'
   history_interval = 5
   terminal_interval = 100
   profile_interval = 200
   write_header_frequency = 50

/ ! end of controls namelist
