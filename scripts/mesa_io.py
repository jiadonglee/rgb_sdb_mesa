"""Readers for MESA history files (star and binary) — verified against real output."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def read_history(path: str | Path) -> pd.DataFrame:
    """Read a MESA history .data file into a DataFrame.

    Read a MESA history .data file into a DataFrame.

    MESA format: lines 1-3 = metadata block, line 4 = column count,
    line 5 = count value, line 6 = column names, data from line 7.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path, sep=r"\s+", skiprows=5)
    # MESA column names can repeat across multiple output blocks; keep last
    df = df.loc[:, ~df.columns.duplicated()]
    for col in ("model_number",):
        if col in df.columns:
            df = df.drop_duplicates(subset=col, keep="last").reset_index(drop=True)
    return df


def read_binary_history(run_dir: str | Path) -> pd.DataFrame:
    return read_history(Path(run_dir) / "LOGS" / "binary_history.data")


def read_star_history(run_dir: str | Path, star: int) -> pd.DataFrame:
    return read_history(Path(run_dir) / f"LOGS{star}" / "history.data")


def interp_on_age(df: pd.DataFrame, col: str, age: float) -> float:
    """Linear interpolation of `col` at `age` (uses the `age` column)."""
    return float(np.interp(age, df["age"].to_numpy(), df[col].to_numpy()))
