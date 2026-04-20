# Phase 0 Data Contract

## Purpose

This document defines the Phase 0 data contract for the single-stock RL environment.

The data contract separates:

- Storage-layer market data
- Environment observation data

This separation is required to keep the raw dataset reusable while preventing information leakage into the RL agent.

## Data Source

- Primary source: `yfinance`
- Download as much available daily market data as practical for the target symbol
- Initial target symbol: `RY`

## Storage Layer Rules

The storage layer should retain the daily market dataset downloaded from `yfinance`, subject to cleaning and schema validation.

### Required Raw Fields

- `date`
- `open`
- `high`
- `low`
- `close`
- `volume`

### Excluded Field in Phase 0

- `adj_close` is not used in Phase 0

Reason:

- Phase 0 should keep the first environment price logic simple and internally consistent
- Adjusted price handling can be introduced later as a deliberate pipeline upgrade

## Naming Convention

All stored fields and engineered fields must use lowercase snake_case.

Examples:

- `date`
- `open`
- `high`
- `low`
- `close`
- `volume`
- `previous_close_return`
- `open_gap`

## Trading Calendar Rule

- Keep only real trading days
- Do not create synthetic rows for weekends or holidays

## Missing Data Rule

- Rows with missing critical fields must be removed
- Missing-data removals must be recorded in logs or reports

Critical fields in Phase 0:

- `date`
- `open`
- `high`
- `low`
- `close`
- `volume`

## Observation Layer Rules

The observation layer must be much more restricted than the storage layer.

The agent may not see all stored fields.

### Phase 0 Observation Scope

Observation must be limited to:

- Single-stock information
- Account information
- Only information known before same-day close execution

### Allowed Observation Fields

Recommended default observation fields:

1. `cash_ratio`
2. `position_weight`
3. `shares_held`
4. `open_gap`
5. `previous_close_return`

### Not Allowed in Observation Before Trade Execution

- same-day `close`
- same-day `high`
- same-day `low`
- any same-day feature that depends on close, high, or low

Reason:

- The agent observes the current day's `open`
- The trade executes at the current day's `close`
- Therefore the same-day close, high, and low are not known yet at decision time

## Clarification on High and Low

Even though `high` and `low` are not equal to `close`, they are still end-of-day information in a daily-bar setting.

That means:

- same-day `high` is unknown at the market open
- same-day `low` is unknown at the market open

So if the agent decides after observing the day's `open`, it must not see the same day's `high` or `low`.

If future phases move to a different timing assumption or intraday data, this rule can change.

## Clarification on Normalization

Raw prices such as `open = 137.42` are harder for RL models to learn from consistently across time because the absolute price level drifts over years.

Instead of using raw prices directly, the observation should use relative values.

Recommended Phase 0 definitions:

- `open_gap = open_t / close_{t-1} - 1`
- `previous_close_return = close_{t-1} / close_{t-2} - 1`

Reason:

- Relative features are scale-stable
- They better describe movement rather than raw price level
- They are more suitable for learning across long historical windows

## Optional Indicators

Phase 0 should not enable additional indicators by default.

Examples that may be added later:

- `sma_ratio`
- `rsi_14`

These should remain optional until the base environment passes leakage and stability tests.

## Summary

Phase 0 should follow these data rules:

- Store the cleaned daily `open`, `high`, `low`, `close`, and `volume` data from `yfinance`
- Use lowercase snake_case naming
- Remove and record missing critical rows
- Restrict observations to pre-close information only
- Use relative observation features such as `open_gap` and `previous_close_return`
- Do not use same-day `high`, `low`, or `close` in the agent observation
