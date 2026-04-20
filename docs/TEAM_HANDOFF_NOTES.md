# Team Handoff Notes

## Project State

This package reflects the current productized state after Phases 0 to 4.

### Frozen Strategy Basis

- product app uses the frozen `Phase 3 Group B core` family
- basket selection is automatic:
  - core model for core-only profiles
  - extended model for extended-universe profiles

### Product Scope

The app is local-first and profile-based:

- users input their own holdings
- the app stores them in SQLite
- the frozen policy generates target weights
- the app outputs a sell-first / buy-second order ticket

## Main Files To Read First

- `docs/PHASE_4_PRODUCT_APP.md`
- `scripts/run_product_dashboard.py`
- `src/rl_portfolio/paper_trading.py`
- `src/rl_portfolio/profile_store.py`

## What Is Safe To Change

Usually safe:

- dashboard HTML layout in `scripts/run_product_dashboard.py`
- text, labels, and product copy
- profile form fields
- operation history UI

Be more careful:

- order application logic in `_apply_orders_to_profile`
- frozen model path selection in `paper_trading.py`
- recommendation building in `build_profile_recommendation`

## Current Known Constraints

- only the frozen core and extended baskets are supported
- latest data depends on `yfinance`
- unsupported symbols are excluded from rebalance logic
- execution uses whole shares and fixed commission

## Example Share Flow

The example profile can be reset at any time:

```powershell
python scripts\seed_example_profiles.py --start-date 2026-01-01 --initial-cash 100000 --reset-existing
```

## Included Visual References

- paper-trading latest export:
  - `artifacts/phase_04/paper_trading/latest/index.html`
- Phase 4 defense summary:
  - `artifacts/phase_04/defense_summary/index.html`
