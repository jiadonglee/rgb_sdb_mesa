#!/usr/bin/env python3
"""Render inlists from configs/pilot_grid.yaml and run MESA binary simulations.

Each run gets runs/<id>/ with rendered inlists and its own copy of the compiled
`binary` executable. Failures leave runs/<id>/FAILED with a log tail.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
RUNS = ROOT / "runs"


def render(template: str, values: dict) -> str:
    out = template
    for key, val in values.items():
        out = out.replace("{{%s}}" % key, str(val))
    return out


def system_params(sys_def: dict, defaults: dict) -> dict:
    p = dict(defaults)
    p.update(sys_def)
    m1 = float(p["M1"])
    q = float(p["q"])
    eta = float(p["eta_acc"])
    z = float(p["Z"])
    return {
        "M1": m1,
        "M2": round(m1 * q, 6),
        "Q": q,
        "PORB": float(p["P_days"]),
        "Z": z,
        "BETA": round(1.0 - eta, 6),   # eta_acc = 1 - beta (alpha = delta = 0)
        "ETA_ACC": eta,
        "MDOT_SCHEME": p["mdot_scheme"],
        "WIND1": float(p["wind1"]),
        "MAXAGE": float(p["max_age_yr"]),
        "MAXMODEL": int(p["max_model_number"]),
    }


def prepare_run(run_id: str, params: dict, binary_exe: Path) -> Path:
    run_dir = RUNS / run_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    for name in ("inlist_project", "inlist1", "inlist2"):
        tpl = (TEMPLATES / (name + ".tpl")).read_text()
        (run_dir / name).write_text(render(tpl, params))
    # top-level `inlist` required by the binary executable -> points at inlist_project
    shutil.copy2(TEMPLATES / "inlist.tpl", run_dir / "inlist")
    (run_dir / "params.yaml").write_text(yaml.safe_dump(params, sort_keys=False))
    (run_dir / "LOGS").mkdir(exist_ok=True)
    shutil.copy2(binary_exe, run_dir / "binary")
    return run_dir


def run_one(run_id: str, params: dict, binary_exe: Path, timeout_s: int | None) -> int:
    run_dir = prepare_run(run_id, params, binary_exe)
    print(f"[{run_id}] starting: M1={params['M1']} M2={params['M2']} "
          f"P={params['PORB']}d Z={params['Z']} eta={params['ETA_ACC']}")
    log_path = run_dir / "run.log"
    with log_path.open("w") as log:
        proc = subprocess.run(["./binary"], cwd=run_dir, stdout=log,
                              stderr=subprocess.STDOUT, timeout=timeout_s)
    if proc.returncode != 0:
        tail = log_path.read_text(errors="replace")[-2000:]
        (run_dir / "FAILED").write_text(tail)
        print(f"[{run_id}] FAILED (exit {proc.returncode}) — see {run_dir/'FAILED'}")
    else:
        print(f"[{run_id}] done (exit 0)")
    return proc.returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "configs" / "pilot_grid.yaml"))
    ap.add_argument("--runs", nargs="*", help="system ids to run (default: all)")
    ap.add_argument("--jobs", type=int, default=2, help="concurrent simulations")
    ap.add_argument("--timeout-s", type=int, default=None)
    args = ap.parse_args()

    mesa_dir = os.environ.get("MESA_DIR")
    if not mesa_dir:
        sys.exit("error: source ~/mesa-work/use-mesa.sh first (MESA_DIR not set)")
    binary_exe = Path(mesa_dir) / "binary" / "work" / "binary"
    if not binary_exe.exists():
        sys.exit(f"error: {binary_exe} missing — run ./mk in $MESA_DIR/binary/work")

    cfg = yaml.safe_load(Path(args.config).read_text())
    systems = cfg["systems"]
    if args.runs:
        systems = [s for s in systems if s["id"] in set(args.runs)]
        missing = set(args.runs) - {s["id"] for s in systems}
        if missing:
            sys.exit(f"error: unknown run ids {sorted(missing)}")

    RUNS.mkdir(exist_ok=True)
    queue = [(s["id"], system_params(s, cfg["defaults"])) for s in systems]

    # simple process-pool execution with bounded concurrency
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = [pool.submit(run_one, rid, prm, binary_exe, args.timeout_s)
                   for rid, prm in queue]
        codes = [f.result() for f in futures]

    failed = [rid for (rid, _), c in zip(queue, codes) if c != 0]
    print(f"\n{len(queue) - len(failed)}/{len(queue)} runs succeeded")
    if failed:
        print("failed:", ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
