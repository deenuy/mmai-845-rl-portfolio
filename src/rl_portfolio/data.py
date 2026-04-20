"""Data download and cleaning utilities for single-asset and multi-asset phases."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import pandas as pd
import yfinance as yf

from .config import DataConfig

REQUIRED_COLUMNS = ["date", "open", "high", "low", "close", "volume"]
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class CleaningReport:
    """Summary of cleaning actions applied to a raw market dataset."""

    original_rows: int
    rows_after_dropna: int
    dropped_rows: int

    def to_dict(self) -> dict[str, int]:
        """Return a JSON-serializable representation of the report."""

        return asdict(self)


def download_daily_data(config: DataConfig) -> pd.DataFrame:
    """Download daily OHLCV data from yfinance and normalize column names."""

    cache_dir = PROJECT_ROOT / "data" / "cache" / "yfinance_tz"
    cache_dir.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(cache_dir))

    frame = yf.download(
        tickers=config.symbol,
        start=config.start_date,
        end=config.end_date,
        auto_adjust=config.auto_adjust,
        progress=False,
        interval="1d",
    )
    if frame.empty:
        raise ValueError(f"No data returned for symbol {config.symbol}.")

    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)

    frame = frame.reset_index()
    frame.columns = [_normalize_column_name(column) for column in frame.columns]

    if "adj_close" in frame.columns:
        frame = frame.drop(columns=["adj_close"])

    return frame


def clean_ohlcv_data(frame: pd.DataFrame) -> tuple[pd.DataFrame, CleaningReport]:
    """Validate the Phase 0 schema and drop rows with missing critical values."""

    normalized = frame.copy()
    normalized.columns = [_normalize_column_name(column) for column in normalized.columns]

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in normalized.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    original_rows = len(normalized)
    normalized["date"] = pd.to_datetime(normalized["date"], utc=False)
    normalized = normalized.sort_values("date").reset_index(drop=True)
    normalized = normalized.dropna(subset=REQUIRED_COLUMNS).reset_index(drop=True)

    for column in ["open", "high", "low", "close", "volume"]:
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")

    report = CleaningReport(
        original_rows=original_rows,
        rows_after_dropna=len(normalized),
        dropped_rows=original_rows - len(normalized),
    )
    return normalized[REQUIRED_COLUMNS].copy(), report


def save_cleaning_report(report: CleaningReport, output_path: str | Path) -> None:
    """Write the cleaning report to a JSON file."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")


def download_symbol_dataset(
    symbol: str,
    *,
    start_date: str,
    end_date: str | None = None,
    auto_adjust: bool = False,
) -> pd.DataFrame:
    """Download one symbol using the same schema contract as the single-asset flow."""

    return download_daily_data(
        DataConfig(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            auto_adjust=auto_adjust,
        )
    )


def prepare_symbol_dataset(
    symbol: str,
    *,
    start_date: str,
    end_date: str | None = None,
    auto_adjust: bool = False,
) -> tuple[pd.DataFrame, CleaningReport]:
    """Download and clean a single symbol dataset."""

    downloaded = download_symbol_dataset(
        symbol,
        start_date=start_date,
        end_date=end_date,
        auto_adjust=auto_adjust,
    )
    return clean_ohlcv_data(downloaded)


def prepare_multi_asset_raw_panel(
    symbols: list[str],
    *,
    start_date: str,
    end_date: str | None = None,
    auto_adjust: bool = False,
) -> tuple[dict[str, pd.DataFrame], dict[str, CleaningReport]]:
    """Prepare cleaned raw datasets for a list of symbols."""

    frames: dict[str, pd.DataFrame] = {}
    reports: dict[str, CleaningReport] = {}

    for symbol in symbols:
        cleaned, report = prepare_symbol_dataset(
            symbol,
            start_date=start_date,
            end_date=end_date,
            auto_adjust=auto_adjust,
        )
        frames[symbol] = cleaned
        reports[symbol] = report

    return frames, reports


def save_multi_asset_cleaning_report(
    reports: dict[str, CleaningReport],
    output_path: str | Path,
) -> None:
    """Write a multi-symbol cleaning report to JSON."""

    payload = {symbol: report.to_dict() for symbol, report in reports.items()}
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _normalize_column_name(column: object) -> str:
    """Convert provider column names into lowercase snake_case."""

    return str(column).strip().lower().replace(" ", "_")
