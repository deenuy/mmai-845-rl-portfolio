# Phase 0 Technical Specification

## Purpose

This document freezes the initial technical specification for the single-stock environment used in Phase 0 and Phase 1.

It also clarifies how the project reconciles the original single-stock `Buy / Hold / Sell` idea with the newer target-position environment design required for later portfolio expansion.

## Design Resolution: Discrete Actions vs Target Position

The project originally started from a single-stock `Buy / Hold / Sell` concept.

That idea is still preserved, but the implementation is split into two layers:

- Environment core: use a continuous target-position action
- Baseline strategy wrappers: allow discrete `Buy / Hold / Sell` style agents for comparison

This means:

- The environment itself will not be built around hard-coded discrete trading commands
- A discrete baseline can still map:
  - `Buy` -> target stock weight `1.0`
  - `Hold` -> keep the current target weight
  - `Sell` -> target stock weight `0.0`

Reason:

- The target-position core is more compatible with future multi-asset allocation
- The discrete baseline remains available for single-stock comparison and historical consistency with the original project idea

## Market and Account Configuration

- Market scope: U.S. equities only
- Base currency: `USD`
- Initial symbol: `RY`
- Initial portfolio capital: `100,000 USD`
- Trading frequency: daily
- Observation timing: observe the current day's `open` and previously known information
- Execution timing: same-day close

## Data Window Plan

- Historical training data begins in `2010`
- Backtest focus window should include `2022-2024`

Recommended first split:

- Train: `2010-01-01` to `2021-12-31`
- Validation backtest: `2022-01-01` to `2022-12-31`
- Test backtest: `2023-01-01` to `2024-12-31`

Reason:

- This preserves a long training history
- It gives a recent stress and recovery window for out-of-sample evaluation
- It keeps the evaluation timeline interpretable

## Action Specification

### Environment Core Action

- Action type: continuous scalar
- Action range: `0.0` to `1.0`
- Meaning: target portfolio weight allocated to the stock

Derived value:

- `target_cash_weight = 1.0 - target_stock_weight`

### Discrete Baseline Mapping

For baseline comparisons, a discrete wrapper may be used:

- `Buy` -> `1.0`
- `Hold` -> keep previous target
- `Sell` -> `0.0`

## Share Execution Policy

- The implementation must use whole shares only
- Fractional shares are not allowed during the current development cycle
- Code design may preserve the ability to support fractional shares later

Execution rule:

- If `30%` of portfolio capital is allocated to the stock, the environment must first reserve transaction costs
- Only the remaining affordable cash may be used to buy whole shares
- Share count must be floored to the nearest integer that keeps cash non-negative

## Transaction Cost Model

- Commission model: fixed `1.99 USD` per executed trade
- Commission does not depend on share count
- Slippage model: fixed `5 bps`
- Minimum trade value: `100 USD`

Execution safety rule:

- The environment must account for commission and slippage before confirming the final buy size
- No trade may be executed if it causes negative cash
- Trades below `100 USD` notional value should be ignored

## Cash Return

- Cash receives a fixed annualized return
- Cash yield accrues daily on the remaining post-trade cash balance
- Current default annualized cash yield: `0%`

Daily approximation:

- `daily_cash_rate = 0.02 / 252`

## Observation Specification

Phase 0 should stay minimal.

The initial observation should only contain:

- Single-stock market information
- Account information

The observation schema should be designed as extendable so later phases can add more information without redesigning the whole environment.

### Phase 0 Placeholder Observation Set

Recommended initial fields:

1. `cash_ratio`
2. `position_weight`
3. `shares_held`
4. `open_gap`
5. `previous_close_return`

Optional first-wave indicators:

- `sma_ratio`
- `rsi_14`

Extension rule:

- Later phases may append more fields for macro, regime, cross-asset, and alternative data features
- Raw same-day `high`, `low`, and `close` must not appear in the observation before execution

## Episode Design

### Training

- Use fixed-length rolling windows
- Randomize the starting point within the training range
- Recommended window length: `252 trading days`

### Validation and Test

- Use fixed chronological windows
- Do not randomize the evaluation range

## Reward Definition

- Reward is the step log return of total portfolio value after all transaction costs

Reference form:

- `reward = log(portfolio_value_t / portfolio_value_{t-1})`

## Benchmarks to Keep

The following comparison agents should remain in scope:

- Random agent
- Buy-and-hold agent
- Discrete `Buy / Hold / Sell` style baseline

Important note:

- The third baseline may be implemented as a wrapper or policy layer on top of the target-position environment

## Open Item

- Optional first-wave indicators can be finalized during implementation if feature leakage checks remain clean
