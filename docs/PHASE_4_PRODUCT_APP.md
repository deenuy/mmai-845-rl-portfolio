# Phase 4 Product App

## Objective

This local product shell turns the Phase 4 mainline policy into a usable workflow:

- create and save portfolio profiles
- store profiles in a backend SQLite database
- load an existing profile later
- generate today's rebalance instruction from the frozen model
- display a holdings dashboard with live mark-to-market values

## Current Scope

The current MVP supports two frozen baskets:

- core:
  - `RY`
  - `MSFT`
  - `RKLB`
  - `XOM`
  - `PG`
- extended:
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

Profiles can currently store:

- profile name
- available cash
- symbol
- average cost
- held shares
- automatic basket selection:
  - core model when the profile symbols are a subset of the core basket
  - extended model when the profile symbols are a subset of the extended basket

## Current Architecture

Backend:

- SQLite store:
  - `src/rl_portfolio/profile_store.py`
- paper-trading service layer:
  - `src/rl_portfolio/paper_trading.py`

Frontend:

- local Python HTTP server:
  - `scripts/run_product_dashboard.py`

## User Flow

1. Create a profile from the browser.
2. Input current cash and holdings.
3. Save the profile to SQLite.
4. Open the profile page.
5. Refresh today's recommendation.
6. Review:
   - today's core symbol
   - current cash and target cash
   - sell-first orders
   - buy-second orders
   - current holdings dashboard
   - unrealized P&L by symbol

## Recommendation Logic

The product app separates:

- model-side target generation
- user-side real holdings

The frozen model still runs from `2026-01-01` under the Phase 4 mainline policy to produce today's target weights.

Then the app compares those target weights against the selected profile's:

- current shares
- average cost
- cash

The trade plan is generated with the existing whole-share execution engine and outputs:

- sell orders first
- buy orders second
- share deltas
- notional amounts
- execution prices

## Run Command

```powershell
python scripts\run_product_dashboard.py --host 127.0.0.1 --port 8080
```

Then open:

- `http://127.0.0.1:8080`

## Example Profile Seeder

You can pre-create an example extended-universe profile based on an equal-weight build from the first available trading date on or after `2026-01-01`.

```powershell
python scripts\seed_example_profiles.py --start-date 2026-01-01 --initial-cash 100000
```

## Current Constraints

- The app currently supports only the frozen core and frozen extended baskets.
- Unsupported profile symbols are shown but excluded from the rebalance engine.
- The recommendation page uses the latest daily data available at run time.
- The current implementation is local-first and file-based; it is not yet deployed as a hosted web app.
