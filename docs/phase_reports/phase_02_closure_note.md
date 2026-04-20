# Phase 2 Closure Note

## Closure Decision

Phase 2 can now be closed on the main branch.

## Why Phase 2 Is Considered Complete

The following Phase 2 goals are now satisfied:

- aligned five-asset dataset is in place
- portfolio environment and accounting are implemented
- portfolio baselines are documented
- PPO portfolio training and backtesting are implemented
- HTML reports and portfolio diagnostics are available
- a stronger structured mainline PPO architecture has replaced the original flat portfolio PPO
- multi-seed validation has been completed for the best current mainline configuration

## Best Current Mainline Configuration

- `cash_yield = 0%`
- `reward_mode = log_return_with_turnover_penalty`
- `turnover_penalty_coef = 0.001`
- `strategic_review_interval_days = 63`
- `residual_freeze_enabled = true`
- `extreme_residual_drift_threshold = 0.20`

## Main Result

Reference seed (`42`) result on `2022-01-01` to `2024-12-31`:

- Final portfolio value: `168112.04`
- Cumulative return: `0.6811`
- Sharpe ratio: `0.9644`
- Max drawdown: `-0.2206`
- Executed trades: `907`

## Multi-Seed Summary

- `seed = 7`
  - Final portfolio value: `185533.12`
  - Sharpe ratio: `1.2106`
  - Max drawdown: `-0.1789`
  - Executed trades: `887`
- `seed = 42`
  - Final portfolio value: `168112.04`
  - Sharpe ratio: `0.9644`
  - Max drawdown: `-0.2206`
  - Executed trades: `907`
- `seed = 123`
  - Final portfolio value: `167228.20`
  - Sharpe ratio: `0.9889`
  - Max drawdown: `-0.2222`
  - Executed trades: `922`

Interpretation:

- the strategy is stable enough across seeds to justify Phase 2 closure
- the remaining weaknesses are turnover concentration and hierarchical portfolio refinement
- those are appropriate follow-up topics for Phase 3 rather than incomplete Phase 2 blockers

## Recommended Phase 3 Starting Point

Phase 3 should begin from the current residual-freeze mainline and focus on:

- richer core / residual / cash interpretation
- turnover refinement for high-activity symbols
- stronger concentration control
- broader feature engineering and tuning
