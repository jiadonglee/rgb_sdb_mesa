"""Overlap-time integration for the RGB+sdB project.

Integrates the intersection of two step-function phase masks on a common age
axis built from the union of both histories' ages (never counts output rows).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _mask_at(df: pd.DataFrame, phase: str, ages: np.ndarray) -> np.ndarray:
    """Evaluate `df.phase == phase` as a step function at `ages` (left-continuous
    hold from each row's age to the next)."""
    phase_arr = df["phase"].to_numpy()
    hist_ages = df["age"].to_numpy()
    idx = np.searchsorted(hist_ages, ages, side="right") - 1
    idx = np.clip(idx, 0, len(phase_arr) - 1)
    return phase_arr[idx] == phase


def overlap_time(df1: pd.DataFrame, phase1: str,
                 df2: pd.DataFrame, phase2: str,
                 t_min: float | None = None,
                 t_max: float | None = None) -> float:
    """Integral of I[df1.phase==phase1](t) * I[df2.phase==phase2](t) dt.

    Breakpoints = union of both histories' ages (plus integration bounds), so
    unequal output timesteps between the two stars are handled exactly (up to
    the step approximation of each history).
    """
    a1 = df1["age"].to_numpy()
    a2 = df2["age"].to_numpy()
    lo = max(a1[0], a2[0]) if t_min is None else max(t_min, a1[0], a2[0])
    hi = min(a1[-1], a2[-1]) if t_max is None else min(t_max, a1[-1], a2[-1])
    if hi <= lo:
        return 0.0
    grid = np.unique(np.r_[lo, a1[(a1 > lo) & (a1 < hi)], a2[(a2 > lo) & (a2 < hi)], hi])
    m1 = _mask_at(df1, phase1, grid)
    m2 = _mask_at(df2, phase2, grid)
    seg = m1[:-1] & m2[:-1]
    return float(np.sum(np.diff(grid)[seg]))


def first_entry_age(df: pd.DataFrame, phase: str) -> float | None:
    mask = (df["phase"] == phase).to_numpy()
    if not mask.any():
        return None
    return float(df["age"].to_numpy()[np.argmax(mask)])
