# Team Handoff Package

This folder is a runnable handoff package for the current productized Phase 4 dashboard workflow.

If you only want the simplest path, do this:

1. Open `START_HERE_IF_YOU_KNOW_NOTHING.md`
2. Run the install commands
3. Run `RESET_EXAMPLE_PROFILE.bat`
4. Run `START_DASHBOARD.bat`
5. Open `http://127.0.0.1:8080`

## What Is Included

- full project journey notes from Phase 0 to Phase 4
- condensed key decision summaries
- phase reports and roadmap notes
- frozen Phase 3 model bundles:
  - `artifacts/phase_03/ppo_group_b_core_20k`
  - `artifacts/phase_03/ppo_group_b_core_extended_20k`
- local product dashboard:
  - `scripts/run_product_dashboard.py`
- example profile seeder:
  - `scripts/seed_example_profiles.py`
- paper-trading service layer and profile store:
  - `src/rl_portfolio/`
- example SQLite database:
  - `artifacts/phase_04/product/profiles.db`
- example HTML exports:
  - `artifacts/phase_04/paper_trading/latest`
  - `artifacts/phase_04/defense_summary`

## Fastest Start

1. Install dependencies.
2. Reset the example profile.
3. Start the local dashboard.
4. Open `http://127.0.0.1:8080`.

Detailed steps are in `INSTALL_AND_RUN.md`.

## Read These First

For handoff context:

- `START_HERE_IF_YOU_KNOW_NOTHING.md`
- `WHAT_EACH_FOLDER_IS_FOR.md`
- `PROJECT_JOURNEY_PHASE_0_TO_4.md`
- `LESSONS_LEARNED_BY_PHASE.md`
- `KEY_DECISIONS_SUMMARY.md`
- `EXPERIMENT_ENVIRONMENT_AND_DECISIONS.md`
- `TEAM_HANDOFF_NOTES.md`

## Included Example Profile

The database already includes:

- `Example Extended Equal Weight 2026-01-01`

This profile represents an equal-weight whole-share build of the 10-stock extended basket from the first available trading date on or after `2026-01-01`.

## Current Basket Support

Core basket:

- `RY`
- `MSFT`
- `RKLB`
- `XOM`
- `PG`

Extended basket:

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

## Notes

- The dashboard uses the latest available daily market data at run time.
- Internet access is needed for fresh `yfinance` downloads.
- The frozen policies are already included in this package.
- The example database is shareable and can be reset with the provided script.
