"""I/O helpers for loading prepared Phase 0 datasets."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_feature_data(path: str | Path) -> pd.DataFrame:
    """Load the prepared feature dataset from disk."""

    frame = pd.read_csv(path, parse_dates=["date"])
    return frame


def filter_date_range(
    frame: pd.DataFrame,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """Filter a dataframe to an inclusive date range."""

    filtered = frame.copy()
    if start_date is not None:
        filtered = filtered[filtered["date"] >= pd.Timestamp(start_date)]
    if end_date is not None:
        filtered = filtered[filtered["date"] <= pd.Timestamp(end_date)]
    return filtered.reset_index(drop=True)
