# Teacher Run Guide

## Purpose

This guide is the shortest reliable path for running the current project codebase.

It is written for an evaluator who wants to:

- install the required libraries
- run tests
- launch the local product dashboard
- regenerate the example portfolio profile

## Recommended Python Version

- Python `3.10+`

## Required Libraries

### Core dependencies

These are defined in `pyproject.toml`:

- `gymnasium`
- `matplotlib`
- `numpy`
- `pandas`
- `yfinance`

### Training / frozen-model runtime dependencies

These are needed because the dashboard and paper-trading tools load frozen PPO models:

- `stable-baselines3`
- `torch`

### Development / testing dependency

- `pytest`

## Recommended Install Command

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .[train,dev]
```

This one command installs:

- base runtime dependencies
- PPO / model-loading dependencies
- testing dependencies

## Smoke Checks

These commands should succeed:

```powershell
python scripts\run_product_dashboard.py --help
python scripts\seed_example_profiles.py --help
python scripts\export_phase_4_paper_trading.py --help
python -m pytest tests\unit -q -p no:cacheprovider
```

## Test Status At Handoff

The most recent local verification passed:

- `43 passed`

## Run The Example Product Flow

### 1. Reset the example profile

```powershell
python scripts\seed_example_profiles.py --start-date 2026-01-01 --initial-cash 100000 --reset-existing
```

### 2. Launch the dashboard

```powershell
python scripts\run_product_dashboard.py --host 127.0.0.1 --port 8080
```

### 3. Open the browser

- `http://127.0.0.1:8080`

## What The Dashboard Does

The local dashboard supports:

- creating and editing portfolio profiles
- saving them in SQLite
- generating today's recommendation from the frozen model
- reviewing sell-first / buy-second orders
- editing execution shares and prices before confirmation
- confirming rebalances back into the saved profile
- viewing operation history and rollback snapshots

## Example Profile

The example profile is:

- `Example Extended Equal Weight 2026-01-01`

It represents an equal-weight whole-share build of the 10-stock extended basket from the first available trading day on or after `2026-01-01`.

## Supported Baskets

### Core basket

- `RY`
- `MSFT`
- `RKLB`
- `XOM`
- `PG`

### Extended basket

- `RY`
- `MSFT`
- `RKLB`
- `NVDA`
- `LMT`
- `XOM`
- `FSLR`
- `PG`
- `DE`
- `FCX`

## Important Notes

- Fresh market data depends on `yfinance`.
- The product app is local-first and not deployed as a hosted web app.
- The dashboard uses frozen PPO checkpoints from `artifacts/phase_03`.
- If the evaluator only installs base dependencies without `.[train]`, the dashboard will not be able to load PPO models.
