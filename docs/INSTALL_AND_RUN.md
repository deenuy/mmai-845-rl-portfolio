# Install And Run

## Recommended Environment

- Python `3.10+`
- Windows PowerShell

## Install

This is the safest and most complete install path.

From the root of this handoff folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .[train,dev]
```

## Quick Verification

Run these commands before opening the dashboard:

```powershell
python scripts\run_product_dashboard.py --help
python scripts\seed_example_profiles.py --help
python -m pytest tests\unit -q -p no:cacheprovider
```

Expected result:

- tests should pass
- help commands should print usage text

## Reset The Example Profile

```powershell
python scripts\seed_example_profiles.py --start-date 2026-01-01 --initial-cash 100000 --reset-existing
```

## Start The Dashboard

```powershell
python scripts\run_product_dashboard.py --host 127.0.0.1 --port 8080
```

Open:

- `http://127.0.0.1:8080`

## One-Click Option

After dependencies are installed:

- double-click `RESET_EXAMPLE_PROFILE.bat`
- double-click `START_DASHBOARD.bat`

These two files are the easiest path for a reviewer or teammate.

## Common Workflow

1. Open the example profile.
2. Click `Refresh Today's Recommendation`.
3. Open `Review And Confirm Rebalance`.
4. Adjust shares or execution prices if needed.
5. Click `Confirm Rebalance Complete`.
6. Check `View Operation History` for the saved execution log.

## Product Features In This Package

- create and edit profiles
- view current holdings dashboard
- build today’s order ticket
- manually edit ticket shares and execution price
- confirm rebalance into the saved profile
- operation history and rollback

## If Something Fails

1. Make sure the virtual environment is active.
2. Make sure `pip install -e .[train,dev]` completed successfully.
3. Re-run the example reset command.
4. Re-run the dashboard start command.

If model-loading fails, the usual cause is missing `stable-baselines3` or `torch`.

## Important Paths

- product database:
  - `artifacts/phase_04/product/profiles.db`
- dashboard entry:
  - `scripts/run_product_dashboard.py`
- example seeder:
  - `scripts/seed_example_profiles.py`
- frozen models:
  - `artifacts/phase_03/ppo_group_b_core_20k`
  - `artifacts/phase_03/ppo_group_b_core_extended_20k`
