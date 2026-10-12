"""Evolutionary phase classification for the RGB+sdB project.

Physical phase definitions (primary) + observational approximations (secondary).
All thresholds live in CLASSIFICATION and may be tuned per science run.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Teff/logg observational window for "classical sdB" (adjustable cuts, not
# sufficient physical criteria — physical criteria are He burning + stripping).
CLASSIFICATION = {
    "sdB_teff_kk": (20.0, 45.0),      # log_Teff in kk? no: store kK range [20,45]
    "sdB_logteff": (np.log10(20_000.0), np.log10(45_000.0)),
    "sdB_logg": (4.8, 6.2),
    "sustained_yr": 1.0e6,            # min duration for "sustained" He burning
    "post_ms_h1": 0.05,               # center_h1 below this = post-MS
    "he_ignited_he4": 0.10,           # center_he4 above this = He core burning started
    "he_exhausted_he4": 0.05,         # center_he4 below this after ignition = He exhausted
    "rgb_min_log_R": np.log10(3.0),   # post-MS giant needs R > 3 Rsun (excludes SGB hook)
    "env_mass_stripped": 0.10,        # (m - he_core) below this = substantially stripped
}


def classify_donor(df: pd.DataFrame, cfg: dict | None = None) -> pd.DataFrame:
    """Per-row phase labels for Star 1 (donor/stripped star).

    Phases: ms, hg/rgb_like (pre-strip giant), sdB (core-He burning, hot, stripped),
    proto_he_wd (stripped, no sustained He burning), he_wd (contracting, cold),
    other.
    """
    c = dict(CLASSIFICATION)
    if cfg:
        c.update(cfg)
    out = pd.DataFrame(index=df.index)
    out["age"] = df["star_age"].to_numpy()

    center_h1 = df["center_h1"].to_numpy()
    center_he4 = df["center_he4"].to_numpy()
    log_teff = df["log_Teff"].to_numpy()
    log_lhe = df["log_LHe"].to_numpy()
    log_lh = df["log_LH"].to_numpy()
    he_core = df["he_core_mass"].to_numpy()
    mass = df["star_mass"].to_numpy() if "star_mass" in df else np.nan
    env_mass = mass - he_core

    he_burning = (log_lhe > log_lh) | ((center_he4 > c["he_ignited_he4"]) & (log_lhe > 0))
    in_sdb_box = ((log_teff >= c["sdB_logteff"][0]) & (log_teff <= c["sdB_logteff"][1])
                  & (df["log_g"].to_numpy() >= c["sdB_logg"][0])
                  & (df["log_g"].to_numpy() <= c["sdB_logg"][1]))
    stripped = env_mass < c["env_mass_stripped"]

    phase = np.full(len(df), "other", dtype=object)
    log_r = df["log_R"].to_numpy()
    phase[(center_h1 > c["post_ms_h1"]) & (log_r < c["rgb_min_log_R"])] = "ms"
    phase[(center_h1 > c["post_ms_h1"]) & (log_r >= c["rgb_min_log_R"])] = "giant_pre_strip"
    # post-MS, not stripped, not He burning (unstripped giant evolving normally)
    phase[(center_h1 <= c["post_ms_h1"]) & ~stripped & ~he_burning] = "giant_post_ms"
    # hot stripped star with sustained He burning (confirmed below on durations)
    phase[stripped & he_burning] = "sdB_candidate"
    # hot/stripped but no sustained He burning
    phase[stripped & ~he_burning] = "proto_he_wd_candidate"

    # sustain He burning (promote long-lived candidates to sdB; kill short-lived
    # shell flashes mislabelled sdB)
    out["phase"] = phase
    out = _enforce_sustained(out, candidate="sdB_candidate", promote="sdB",
                             fallback="proto_he_wd_candidate",
                             min_yr=c["sustained_yr"])
    # remaining candidates: stripped, not He burning -> proto-He WD
    phase = out["phase"].to_numpy()
    phase[phase == "proto_he_wd_candidate"] = "proto_he_wd"
    out["phase"] = phase

    # observational approximation column (uncertainty explicitly kept)
    obs = np.full(len(df), "", dtype=object)
    obs[in_sdb_box & he_burning & stripped] = "sdB_like_in_obsbox"
    out["obs_flag"] = obs
    out["log_Teff"] = log_teff
    out["log_g"] = df["log_g"].to_numpy()
    out["center_he4"] = center_he4
    out["he_core_mass"] = he_core
    out["env_mass"] = env_mass
    return out


def classify_accretor(df: pd.DataFrame, cfg: dict | None = None) -> pd.DataFrame:
    """Per-row phase labels for Star 2 (companion): ms, sgb, rgb, he_core_burning
    (red clump), agb_like, other."""
    c = dict(CLASSIFICATION)
    if cfg:
        c.update(cfg)
    center_h1 = df["center_h1"].to_numpy()
    center_he4 = df["center_he4"].to_numpy()
    log_lhe = df["log_LHe"].to_numpy()
    log_lh = df["log_LH"].to_numpy()
    log_r = df["log_R"].to_numpy()

    # red-clump vs RGB: clump has He-burning luminosity comparable to (or above)
    # the H shell and typically a convective He core; RGB has an inert He core.
    he_burning = ((log_lhe > log_lh - 0.3) | (df["mass_conv_core"].to_numpy() > 1e-3)) \
        if "mass_conv_core" in df else (log_lhe > log_lh - 0.3)
    he_exhausted = (center_he4 < c["he_exhausted_he4"]) & (center_h1 <= c["post_ms_h1"])
    post_ms = center_h1 <= c["post_ms_h1"]

    phase = np.full(len(df), "ms", dtype=object)
    phase[post_ms & ~he_burning & (log_r < c["rgb_min_log_R"])] = "sgb"
    phase[post_ms & ~he_burning & ~he_exhausted & (log_r >= c["rgb_min_log_R"])] = "rgb"
    phase[post_ms & he_burning & ~he_exhausted] = "he_core_burning"  # red clump
    phase[he_exhausted] = "agb_like"
    # flag obvious MS accretors that became giants purely by rejuvenation later
    out = pd.DataFrame({"age": df["star_age"].to_numpy(), "phase": phase,
                        "center_h1": center_h1, "center_he4": center_he4,
                        "log_R": log_r, "log_Teff": df["log_Teff"].to_numpy(),
                        "log_g": df["log_g"].to_numpy()})
    return out


def _enforce_sustained(df: pd.DataFrame, candidate: str, promote: str,
                       fallback: str, min_yr: float) -> pd.DataFrame:
    """Promote `candidate` runs longer than min_yr to `promote`; demote the
    rest to `fallback`."""
    phase = df["phase"].to_numpy()
    ages = df["age"].to_numpy()
    in_run = phase == candidate
    edges = np.flatnonzero(np.diff(in_run.astype(int))) + 1
    starts = np.r_[0, edges]
    ends = np.r_[edges, len(in_run)]
    for s, e in zip(starts, ends):
        if in_run[s]:
            phase[s:e] = promote if (ages[e - 1] - ages[s]) >= min_yr else fallback
    df["phase"] = phase
    return df


def phase_intervals(df: pd.DataFrame, phase: str) -> list[tuple[float, float]]:
    """Contiguous [start, end] age intervals where df.phase == phase (step model)."""
    mask = (df["phase"] == phase).to_numpy()
    ages = df["age"].to_numpy()
    intervals: list[tuple[float, float]] = []
    start = None
    for i, m in enumerate(mask):
        if m and start is None:
            start = ages[i]
        if not m and start is not None:
            intervals.append((start, ages[i]))
            start = None
    if start is not None:
        intervals.append((start, ages[-1]))
    return intervals
