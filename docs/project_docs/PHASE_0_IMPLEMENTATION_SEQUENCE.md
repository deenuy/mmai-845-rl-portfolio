# Phase 0 Implementation Sequence

## Objective

Translate the agreed environment direction into an implementation order that minimizes rework.

## Sequence

### Step 1: Freeze the Single-Stock Baseline

Define and document:

- Initial ticker: `RY`
- Data date range: start from `2010`, with `2022-2024` reserved for backtesting
- Daily frequency
- Fee model: `1.99 USD` fixed commission per trade
- Slippage: `5 bps`
- Minimum trade value: `100 USD`
- Initial cash: `100,000 USD`
- Long-only constraint
- Action mode: target position
- Execution policy: whole shares only
- Observation timing: current-day `open`
- Execution timing: current-day `close`
- Baseline comparison mode: keep discrete `Buy / Hold / Sell` mapping support
- Cash yield: fixed `2%` annualized default
- Reward baseline

### Step 2: Build the Data and Feature Layer

Deliver:

- Historical data loader
- Data schema validator
- Past-only feature generator
- Observation feature builder using restricted pre-close inputs only

### Step 3: Build the Execution and Accounting Layer

Deliver:

- Effective execution price logic
- Cash and holdings update logic
- Portfolio valuation utilities

### Step 4: Build the Gym-Compatible Environment

Deliver:

- Reset and step logic
- Observation generation
- Action parsing
- Episode termination rules

### Step 5: Run Phase 0 Gate Tests

Deliver:

- Stability results
- Accounting validation results
- Feature leakage validation

### Step 6: Prepare for Phase 1

Deliver:

- Single-stock environment ready for PPO
- Benchmark wrappers ready for random and buy-and-hold agents
- Report artifacts and figures saved
