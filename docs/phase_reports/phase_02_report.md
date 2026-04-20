# Phase 2 Working Report

## Objective

Phase 2 extends the project from a single-stock RL setup to a five-asset portfolio allocation environment with shared cash, whole-share execution, and portfolio baselines.

The working objective is to validate:

- multi-asset data alignment
- portfolio accounting and rebalancing
- meaningful portfolio baselines
- first portfolio PPO behavior against internal basket benchmarks

## Scope Delivered So Far

Implemented:

- aligned five-symbol Phase 2 dataset
- portfolio trading environment
- portfolio baseline suite
- Phase 2 PPO training and backtesting pipeline
- HTML reporting with:
  - equal-weight comparison charts
  - target and realized weight charts
  - concentration charts
  - per-symbol trade counts

Current first basket:

- `RY`
- `MSFT`
- `RKLB`
- `XOM`
- `PG`

Main evaluation window:

- `2022-01-01` to `2024-12-31`

## Key Baselines

### Equal-Weight Buy-and-Hold

- Final portfolio value: `143699.58`
- Cumulative return: `0.4370`
- Sharpe ratio: `0.7542`
- Max drawdown: `-0.2116`

Interpretation:

- this remains the main internal portfolio benchmark for Phase 2

### SPY Buy-and-Hold

- Final portfolio value: `122597.42`
- Cumulative return: `0.2260`
- Sharpe ratio: `0.4781`
- Max drawdown: `-0.2533`

Interpretation:

- the selected basket is stronger than the broad market in the current Phase 2 window
- PPO therefore must be judged against both `SPY` and the internal equal-weight basket baseline

## Initial Portfolio PPO Results

### Original PPO (`cash_yield = 0%`)

- Final portfolio value: `129842.50`
- Sharpe ratio: `0.5898`
- Max drawdown: `-0.2166`
- Executed trades: `3607`

Interpretation:

- the original flat portfolio PPO underperformed the equal-weight benchmark and traded far too often

### Mainline Residual-Freeze PPO (`cash_yield = 0%`)

- Final portfolio value: `168112.04`
- Cumulative return: `0.6811`
- Sharpe ratio: `0.9644`
- Max drawdown: `-0.2206`
- Executed trades: `907`

Per-symbol trades:

- `RY`: `180`
- `MSFT`: `138`
- `RKLB`: `127`
- `XOM`: `219`
- `PG`: `243`

Interpretation:

- this is the current best mainline Phase 2 result
- it materially improves both return and Sharpe relative to the original PPO
- it also cuts turnover sharply by freezing most residual sleeves outside strategic review steps

### Residual-Freeze PPO (`cash_yield = 2%`)

- Final portfolio value: `169166.02`
- Cumulative return: `0.6917`
- Sharpe ratio: `0.9616`
- Max drawdown: `-0.2407`
- Executed trades: `922`

Interpretation:

- the `2%` cash-yield version is only marginally better on terminal value than the `0%` version
- the large improvement comes from the residual-freeze structure rather than the cash-yield assumption

## Rebalancing Behavior Summary

The most important Phase 2 improvement so far is structural:

- portfolio PPO performs much better when non-core sleeves are not fully reshuffled on most ordinary rebalance steps
- strategic review cadence matters
- richer portfolio diagnostics now reveal:
  - concentration behavior
  - review-step cadence
  - average cash weight
  - core-symbol rotation counts

For the current best `0% residual-freeze` run:

- average cash weight: `0.1693`
- average target concentration: `0.2689`
- review steps: `12`

## Test Status

Current relevant test status:

- `12 passed`

This includes:

- portfolio environment tests
- portfolio baseline tests
- portfolio metric tests
- portfolio-structure diagnostics tests

## Main Takeaways

- Phase 2 is no longer blocked on environment or baseline validity
- equal-weight buy-and-hold remains the primary benchmark
- the original flat PPO was too high-turnover and too weak
- residual-freeze mainline structure is a major improvement
- cash yield is a secondary sensitivity factor, not the main driver

## Current Best Mainline Artifact

- `artifacts/phase_02/backtests/ppo_cash0_20k_residual_freeze/index.html`

## Remaining Risks

- turnover is still higher than the intended final discretionary-like style
- some symbols (`XOM`, `PG`) still trade more frequently than desired
- residual-freeze logic has improved performance, but it still needs broader robustness checks

## Multi-Seed Validation

The current best Phase 2 mainline configuration was evaluated across three seeds using the same residual-freeze structure:

- `cash_yield = 0%`
- `reward_mode = log_return_with_turnover_penalty`
- `turnover_penalty_coef = 0.001`
- `strategic_review_interval_days = 63`
- `residual_freeze_enabled = true`
- `extreme_residual_drift_threshold = 0.20`

Results:

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

Summary statistics:

- Mean final portfolio value: `173624.45`
- Final portfolio value standard deviation: `8525.57`
- Mean Sharpe ratio: `1.0546`
- Sharpe ratio standard deviation: `0.1119`
- Mean executed trades: `905.33`

Interpretation:

- The current Phase 2 mainline is materially more stable across seeds than the strongest Phase 1 single-stock branch
- All three seeds outperform both `SPY` and the equal-weight buy-and-hold basket on terminal value
- Drawdown remains in a comparable range across the three runs
- The main remaining issue is still turnover concentration in a few symbols rather than obvious seed collapse

## Phase 2 Closure Recommendation

Phase 2 is now closeable from a mainline engineering and research-process perspective.

Closure rationale:

- the five-asset data layer is complete
- the portfolio environment and execution logic are implemented and tested
- portfolio baselines are established and documented
- the original flat PPO branch was superseded by a clearly stronger structural portfolio design
- the current residual-freeze PPO has now passed a first multi-seed validation with healthy consistency

Recommended close-out statement:

- Phase 2 successfully established a functioning multi-asset PPO research pipeline with interpretable portfolio structure diagnostics
- the current best mainline architecture uses strategic review steps plus residual-sleeve freezing outside review periods
- the strongest remaining open issue is not environment validity, but turnover refinement and richer hierarchical portfolio control
- those next improvements should be treated as Phase 3 work rather than a reason to keep extending Phase 2 indefinitely
