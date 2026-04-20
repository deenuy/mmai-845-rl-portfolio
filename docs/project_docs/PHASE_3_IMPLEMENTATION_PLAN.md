# Phase 3 Implementation Plan

## Planning Goal

This plan turns the Phase 3 requirements into an execution order that is practical for the current codebase.

## Stage 1: Freeze the Phase 2 Reference

Use the current residual-freeze mainline as the Phase 3 baseline reference.

Reference configuration:

- basket: `RY`, `MSFT`, `RKLB`, `XOM`, `PG`
- `cash_yield = 0%`
- `reward_mode = log_return_with_turnover_penalty`
- `turnover_penalty_coef = 0.001`
- `strategic_review_interval_days = 63`
- `residual_freeze_enabled = true`
- `extreme_residual_drift_threshold = 0.20`

Output:

- one documented baseline row in all Phase 3 comparison reports

## Stage 2: Feature Group A

Add the first technical expansion group:

- MACD family
- refined breakout confirmation
- stronger recovery confirmation

Tasks:

- update data feature generation
- update portfolio feature panel preparation
- update observation schema documentation
- retrain on the core basket
- compare against the frozen Phase 2 baseline

Decision gate:

- keep only if risk-adjusted performance or stability improves

## Stage 3: Feature Group B

Add cross-sectional relative features:

- symbol rank within basket
- relative momentum spread
- symbol-vs-basket return spread

Tasks:

- extend feature engineering
- retrain only after Group A is evaluated
- compare Group B-on-top-of-best-current-stack versus baseline stack

Decision gate:

- do not keep if it only increases turnover without improving benchmarks

## Stage 4: Market Regime Layer

Add market-level context:

- `SPY` trend state
- `SPY` drawdown state
- realized market volatility

Optional:

- `VIX` proxy if integration remains reproducible

Decision gate:

- retain only if it improves weak-market behavior or cash handling

## Stage 5: Hyperparameter Tuning

Only after the first winning feature stack is identified.

Tuning order:

1. `learning_rate`
2. `n_steps`
3. `batch_size`
4. `gamma`
5. `ent_coef`
6. turnover penalty coefficient

Suggested process:

- manual shortlist first
- bounded Optuna sweep only after parameter ranges are narrowed

## Stage 6: Ablation and Robustness

For the best candidate stack:

- run at least three seeds
- compare to equal-weight and `SPY`
- run one alternate evaluation window
- run one extended-universe validation round

Minimum interpretation questions:

- does the gain persist across seeds?
- does the gain survive outside the main window?
- does the gain survive beyond the five-symbol basket?

## Stage 7: Phase 3 Close-Out

Prepare the final Phase 3 package:

- report
- figures
- comparison table against Phase 2 baseline
- accepted feature stack summary
- rejected feature groups summary
- final recommended mainline checkpoint

## Recommended First Development Step

Start with Feature Group A rather than tuning hyperparameters immediately.

Reason:

- the current Phase 2 mainline is already strong enough to justify a feature-led next phase
- feature expansion is the most direct interpretation of the original Phase 3 roadmap
- tuning before expanding the signal set would likely optimize the wrong plateau
