# Phase 3 Closure Note

## Closure Decision

Phase 3 can be soft-closed on the main branch.

This means the current development round is complete enough to freeze a mainline best candidate, document the feature-learning conclusions, and move future work into narrower follow-up refinement rather than open-ended exploration.

## Why Phase 3 Is Considered Complete for This Round

The following Phase 3 goals are now satisfied:

- the project started from a frozen, validated Phase 2 reference
- controlled feature groups were introduced instead of mixing many changes at once
- feature redundancy was audited before promotion decisions
- `Group A` was tested in both full and reduced form
- `Group B core` produced a clear improvement over the Phase 2 reference
- `Group B core` survived multi-seed validation on the five-symbol basket
- `Group B core` survived an alternate `2025` evaluation window
- `Group C` market-context features were tested and explicitly rejected for now
- bounded tuning was completed and shown not to beat the untuned `Group B core`
- `Group B core` transferred to the ten-symbol extended universe
- the ten-symbol extended-universe result was also validated across multiple seeds

## Current Mainline Best Branch

The current best Phase 3 mainline branch is:

- `Group B core`

Configuration summary:

- portfolio structure: Phase 2 residual-freeze mainline
- basket for development ranking: `RY`, `MSFT`, `RKLB`, `XOM`, `PG`
- reward: `log_return_with_turnover_penalty`
- `turnover_penalty_coef = 0.001`
- `cash_yield = 0%`
- `strategic_review_interval_days = 63`
- `residual_freeze_enabled = true`
- `extreme_residual_drift_threshold = 0.20`

Feature additions relative to the Phase 2 reference:

- `cs_momentum_rank_20`
- `cs_momentum_spread_20`
- `cs_breakout_rank_20`
- `cs_breakout_spread_20`
- `cs_drawdown_rank_30`
- `cs_drawdown_spread_30`

## Main Results

### Five-Symbol Basket (`2022-01-01` to `2024-12-31`)

Reference seed (`42`) result:

- Final portfolio value: `170650.83`
- Cumulative return: `0.7065`
- Sharpe ratio: `1.0267`
- Max drawdown: `-0.1973`
- Executed trades: `898`

### Five-Symbol Basket Multi-Seed Summary

- `seed = 7`
  - Final portfolio value: `164923.30`
  - Sharpe ratio: `0.9665`
  - Max drawdown: `-0.2128`
  - Executed trades: `904`
- `seed = 42`
  - Final portfolio value: `170650.83`
  - Sharpe ratio: `1.0267`
  - Max drawdown: `-0.1973`
  - Executed trades: `898`
- `seed = 123`
  - Final portfolio value: `184387.71`
  - Sharpe ratio: `1.1208`
  - Max drawdown: `-0.2344`
  - Executed trades: `876`

Interpretation:

- the branch remained strong across all tested seeds
- no seed collapse was observed

### Alternate Window (`2025`)

- Final portfolio value: `139639.89`
- Sharpe ratio: `1.7528`
- Max drawdown: `-0.1550`

Interpretation:

- the branch did not beat equal-weight on terminal value in `2025`
- but it still delivered stronger risk-adjusted performance and lower drawdown

### Ten-Symbol Extended Universe (`2022-01-01` to `2024-12-31`)

Reference seed (`42`) result:

- Final portfolio value: `181567.04`
- Cumulative return: `0.8157`
- Sharpe ratio: `1.0688`
- Max drawdown: `-0.2573`
- Executed trades: `1050`

Compared with extended-universe equal-weight buy-and-hold:

- PPO Final portfolio value: `181567.04`
- Equal-weight Final portfolio value: `170993.41`
- PPO Sharpe ratio: `1.0688`
- Equal-weight Sharpe ratio: `0.9622`

### Ten-Symbol Extended-Universe Multi-Seed Summary

- `seed = 7`
  - Final portfolio value: `202924.96`
  - Sharpe ratio: `1.2881`
  - Max drawdown: `-0.2354`
  - Executed trades: `987`
- `seed = 42`
  - Final portfolio value: `181567.04`
  - Sharpe ratio: `1.0688`
  - Max drawdown: `-0.2573`
  - Executed trades: `1050`
- `seed = 123`
  - Final portfolio value: `209247.88`
  - Sharpe ratio: `1.3231`
  - Max drawdown: `-0.2125`
  - Executed trades: `957`

Interpretation:

- the branch remained strong across all tested seeds on the broader universe
- the broader-universe result is therefore not a single-run artifact

## What Phase 3 Taught the Project

- technical expansion by itself does not guarantee improvement
- lightly reduced technical bundles are better than large redundant technical stacks
- simple market-context overlays are not automatically helpful
- the strongest new edge came from basket-relative information, not from broad-market context
- within the cross-sectional stack, `breakout` and `drawdown` appear to be the primary drivers, while momentum acts more like a supporting signal than a standalone alpha source
- bounded hyperparameter tuning did not outperform the original `Group B core`, so the gain appears to come mainly from better features rather than tuning luck

## Recommended Next Step

Future work should not restart broad exploration from scratch.

The next logical step is:

- keep `Group B core` frozen as the current Phase 3 mainline best
- treat Phase 3 as a stable intermediate milestone
- continue only with narrow follow-up work, such as:
  - finer `breakout` / `drawdown` quality filters
  - additional robustness windows
  - later-stage concentration or cash-structure refinement if needed

This keeps the project disciplined while preserving the strongest validated branch discovered so far.
