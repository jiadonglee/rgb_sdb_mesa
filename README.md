# RGB+sdB binary formation with MESA

Investigate whether stable RLOF can produce an RGB + hot-subdwarf (or proto-He WD)
binary, measure the overlap lifetime of the two phases, and test whether the
population can constrain the accretion efficiency η_acc.

## Environment

- MESA 26.4.1 (git tag 26.4.1), MESA SDK 26.6.1, gfortran 15.2.0, arm64 macOS.
- Activate: `source ~/mesa-work/use-mesa.sh` (sets MESASDK_ROOT, MESA_DIR).

## Layout

```
configs/          pilot_grid.yaml (parameter definitions, YAML)
templates/        inlist templates with {{VAR}} placeholders (rendered per run)
mesa/             working dir used to compile the `binary` executable once
scripts/          run_pilot.py (render+run grid), mesa_io.py (history readers)
runs/<run_id>/    one directory per simulation: rendered inlists, LOGS*/, FAILED on error
results/          machine-readable summary tables (CSV)
figures/          diagnostic figures
tests/            unit tests for classification and overlap integration
```

## Conventions

- Star 1 = initial donor (more massive), Star 2 = initial accretor (less massive).
- `eta_acc = 1 - mass_transfer_beta` with `mass_transfer_alpha = mass_transfer_delta = 0`.
  The prescribed beta is recorded per run; the effective integrated efficiency
  `dM2_gained / (-dM1_total)` is computed from history files, never assumed.
- mdot_scheme = 'Ritter' (baseline); circular orbits; jdot_ml on (default).
- Donor wind: Reimers (eta configurable); accretor wind off at baseline.
- pgstar disabled in all grid runs.

## Usage

```bash
source ~/mesa-work/use-mesa.sh
cd ~/rgb_sdb_mesa
python3 scripts/run_pilot.py --list          # show pilot systems
python3 scripts/run_pilot.py --runs B0       # single run
python3 scripts/run_pilot.py --jobs 2        # whole pilot grid, 2 concurrent
```

## Status / milestones

- [x] Milestone A: binary + evolve_both_stars validated (see runs/ notes + README history)
- [ ] Milestone B: end-to-end pilot (RGB RLOF -> stripped hot star + evolved companion)
- [ ] Milestone C: q_i x eta_acc mini-grid overlap map
- [ ] Milestone D: physical classification (sdB / proto-He WD / unstable / unresolved)
- [ ] Milestone E: identifiability experiment + figures + report
