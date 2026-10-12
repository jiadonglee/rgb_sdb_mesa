#!/usr/bin/env python3
"""Render a movie of a MESA binary evolution from history files.

Panels: (left) HR diagram with live positions of both stars,
(right) donor radius + masses vs age with RLOF region highlighting.
Frames are rendered on a common age grid, then assembled with ffmpeg.
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mesa_io import read_star_history  # noqa: E402

FFMPEG = str(Path.home() / ".hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg")

# dark theme, restrained palette (donor=orange, accretor=blue)
BG, FG, MUTED = "#111111", "#eeeeee", "#888888"
C1, C2 = "#ff9130", "#4da6ff"


def interp(h, col, t):
    return np.interp(t, h["star_age"], h[col])


def make_movie(run_dir: Path, frames: int = 360, fps: int = 30) -> Path:
    h1 = read_star_history(run_dir, 1)
    h2 = read_star_history(run_dir, 2)
    t0 = max(h1["star_age"].iloc[0], h2["star_age"].iloc[0])
    t1 = min(h1["star_age"].iloc[-1], h2["star_age"].iloc[-1])
    # log-spaced frames: most action is late (RLOF), but keep early history visible
    t_grid = np.geomspace(max(t0, 1e8), t1, frames)

    tmp = Path(tempfile.mkdtemp(prefix="mesa_movie_"))
    for i, t in enumerate(t_grid):
        fig, (ax_hr, ax_r, ax_m) = plt.subplots(
            1, 3, figsize=(13.5, 4.2), facecolor=BG,
            gridspec_kw={"width_ratios": [1.3, 1, 1]})
        for ax in (ax_hr, ax_r, ax_m):
            ax.set_facecolor(BG)
            ax.tick_params(colors=FG, labelsize=8)
            for s in ax.spines.values():
                s.set_color(MUTED)

        # --- HR diagram ---
        ax_hr.plot(h1["log_Teff"], h1["log_L"], color=C1, lw=0.8, alpha=0.5)
        ax_hr.plot(h2["log_Teff"], h2["log_L"], color=C2, lw=0.8, alpha=0.5)
        ax_hr.invert_xaxis()
        ax_hr.set_xlim(np.log10(20000), np.log10(3000))
        ax_hr.set_xlabel("log $T_{\\rm eff}$ [K]", color=FG, fontsize=9)
        ax_hr.set_ylabel("log $L/L_\\odot$", color=FG, fontsize=9)
        lt1, ll1 = interp(h1, "log_Teff", t), interp(h1, "log_L", t)
        lt2, ll2 = interp(h2, "log_Teff", t), interp(h2, "log_L", t)
        ax_hr.plot([lt1], [ll1], "o", color=C1, ms=9)
        ax_hr.plot([lt2], [ll2], "o", color=C2, ms=9)
        ax_hr.set_title(f"t = {t/1e9:.3f} Gyr", color=FG, fontsize=10)

        # --- donor radius vs age ---
        ax_r.plot(h1["star_age"] / 1e9, 10 ** h1["log_R"], color=C1, lw=0.9)
        ax_r.plot([t / 1e9], [10 ** interp(h1, "log_R", t)], "o", color=C1, ms=8)
        ax_r.set_yscale("log")
        ax_r.set_xlabel("age [Gyr]", color=FG, fontsize=9)
        ax_r.set_ylabel("$R_1$ [$R_\\odot$]", color=FG, fontsize=9)

        # --- masses vs age ---
        ax_m.plot(h1["star_age"] / 1e9, h1["star_mass"], color=C1, lw=1.0, label="donor")
        ax_m.plot(h2["star_age"] / 1e9, h2["star_mass"], color=C2, lw=1.0, label="accretor")
        m1t, m2t = interp(h1, "star_mass", t), interp(h2, "star_mass", t)
        ax_m.plot([t / 1e9], [m1t], "o", color=C1, ms=8)
        ax_m.plot([t / 1e9], [m2t], "o", color=C2, ms=8)
        ax_m.set_ylim(0, max(h1["star_mass"].max(), h2["star_mass"].max()) * 1.15)
        ax_m.set_xlabel("age [Gyr]", color=FG, fontsize=9)
        ax_m.set_ylabel("mass [$M_\\odot$]", color=FG, fontsize=9)
        ax_m.legend(facecolor=BG, labelcolor=FG, edgecolor=MUTED, fontsize=8)

        fig.suptitle(f"RGB donor + MS accretor  (run: {run_dir.name})",
                     color=FG, fontsize=11)
        fig.tight_layout()
        fig.savefig(tmp / f"f{i:04d}.png", dpi=100, facecolor=BG)
        plt.close(fig)
        if i % 60 == 0:
            print(f"frame {i}/{frames}")

    out = run_dir / "movie.mp4"
    subprocess.run([FFMPEG, "-y", "-framerate", str(fps),
                    "-i", str(tmp / "f%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "23", str(out)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"movie: {out}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--frames", type=int, default=360)
    args = ap.parse_args()
    make_movie(args.run_dir, frames=args.frames)
