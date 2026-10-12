"""Unit tests for phase classification and overlap integration (synthetic data)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from classify_evolution import (classify_accretor, classify_donor,
                                phase_intervals)  # noqa: E402
from compute_overlap import overlap_time  # noqa: E402


def fake_star_row(age, center_h1, center_he4, log_teff, log_g, log_R,
                  he_core, mass, log_lh, log_lhe):
    return dict(star_age=age, center_h1=center_h1, center_he4=center_he4,
                log_Teff=log_teff, log_g=log_g, log_R=log_R,
                he_core_mass=he_core, star_mass=mass,
                log_LH=log_lh, log_LHe=log_lhe)


def test_donor_sdb_classification():
    rows = [
        # MS phase: H burning dominant, not stripped
        fake_star_row(1e9, 0.70, 0.28, np.log10(5800), 4.4, np.log10(1.0), 0.0, 1.2, 1.0, -5),
        # giant pre-strip: big radius
        fake_star_row(5e9, 0.02, 0.98, np.log10(4500), 2.5, 1.5, 0.15, 1.15, 2.0, -1),
        # sdB: hot, stripped, He burning dominant
        fake_star_row(5.05e9, 0.001, 0.98, np.log10(30000), 5.3, -0.5, 0.45, 0.47, -2, 1.5),
        # long sdB stretch (sustained) — add points across 5e7 yr
        fake_star_row(5.08e9, 0.001, 0.50, np.log10(28000), 5.3, -0.5, 0.45, 0.46, -3, 1.2),
        # proto-He WD afterwards: cooling, no He burning
        fake_star_row(5.5e9, 0.001, 0.98, np.log10(12000), 5.5, -1.0, 0.45, 0.452, -6, -6),
    ]
    df = classify_donor(pd.DataFrame(rows))
    phases = df["phase"].tolist()
    assert phases[0] == "ms", phases
    assert phases[1] == "giant_post_ms", phases
    assert phases[2] == "sdB", phases  # 2-row run spans 3e7 yr -> sustained
    assert phases[3] == "sdB", phases
    assert phases[4] == "proto_he_wd", phases
    ivals = phase_intervals(df, "sdB")
    assert len(ivals) == 1 and ivals[0][1] > ivals[0][0]


def test_accretor_rgb_classification():
    rows = [
        fake_star_row(1e9, 0.70, 0.28, np.log10(6000), 4.4, 0.95, 0.0, 1.0, 1.0, -5),
        fake_star_row(6e9, 0.03, 0.97, np.log10(4200), 2.0, 1.7, 0.18, 1.02, 2.5, -1),
        fake_star_row(7e9, 0.001, 0.20, np.log10(5000), 1.8, 1.6, 0.30, 1.02, 2.0, 1.8),
    ]
    df = classify_accretor(pd.DataFrame(rows))
    assert df["phase"].tolist() == ["ms", "rgb", "he_core_burning"]


def test_overlap_rectangles():
    # star1 sdB holds [10, 20); star2 rgb holds [15, 30) -> overlap 5 (same units)
    ages1 = np.array([0, 10, 20, 40], dtype=float)
    df1 = pd.DataFrame({"age": ages1, "phase": ["x", "sdB", "x", "x"]})
    ages2 = np.array([0, 15, 30, 40], dtype=float)
    df2 = pd.DataFrame({"age": ages2, "phase": ["x", "rgb", "rgb", "x"]})
    t = overlap_time(df1, "sdB", df2, "rgb")
    assert abs(t - 5.0) < 1e-9, t

    # no overlap -> 0
    df3 = pd.DataFrame({"age": ages2, "phase": ["x", "x", "rgb", "rgb"]})
    assert overlap_time(df1, "sdB", df3, "rgb") == 0.0


def test_overlap_uneven_sampling():
    # phases defined with wildly different sampling densities on the same span
    df1 = pd.DataFrame({"age": [0, 20, 80, 100], "phase": ["a", "sdB", "a", "a"]})
    dense_ages = np.linspace(20, 80, 500)
    df2 = pd.DataFrame({"age": np.r_[0, dense_ages, 100],
                        "phase": ["x", *(["rgb"] * 500), "rgb"]})
    t = overlap_time(df1, "sdB", df2, "rgb")
    assert abs(t - (80.0 - 20.0)) < 1e-6, t


if __name__ == "__main__":
    test_donor_sdb_classification()
    test_accretor_rgb_classification()
    test_overlap_rectangles()
    test_overlap_uneven_sampling()
    print("all tests passed")
