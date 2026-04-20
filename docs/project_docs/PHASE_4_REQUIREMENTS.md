# Phase 4 Requirements

## Objective

Phase 4 focuses on stress testing, robustness verification, and quasi-production simulation on top of the frozen Phase 3 mainline best branch.

The objective is no longer to discover new alpha features. The objective is to verify that the chosen portfolio policy remains usable across different market regimes, does not collapse under adverse windows, and can support a lightweight paper-trading workflow.

## Starting Point

Phase 4 starts from the current frozen Phase 3 mainline best candidate:

- model family: `Group B core`
- portfolio structure: residual-freeze mainline
- development basket: `RY`, `MSFT`, `RKLB`, `XOM`, `PG`
- extended validation universe:
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

Phase 4 should treat this Phase 3 branch as a frozen baseline unless a clearly better and equally robust checkpoint is discovered during stress testing.

## Scope

Phase 4 covers:

- regime-specific stress testing
- robustness comparison across multiple historical windows
- defense-capability verification
- concentration and turnover diagnostics under stress
- quasi-production paper-trading preparation
- lightweight reporting and dashboard-ready artifact generation

Phase 4 does not yet require:

- live brokerage execution
- automatic order submission to a real broker
- production deployment orchestration
- 24/7 hosted infrastructure

## Stress-Testing Windows

Phase 4 must evaluate the frozen mainline policy on named stress windows rather than a single blended backtest.

### Core Windows

- `bear_2022`
  - `2022-01-01` to `2022-12-31`
- `bull_2023_2024`
  - `2023-01-01` to `2024-12-31`
- `mixed_2022_2024`
  - `2022-01-01` to `2024-12-31`
- `alt_2025`
  - `2025-01-01` to `2025-12-31`

### Optional Additional Windows

These can be used if the data quality and schedule allow:

- `covid_recovery_2020_2021`
- `energy_shock_subwindow`
- `high_rate_transition_subwindow`

Optional windows should not block the initial Phase 4 completion.

## Core Validation Questions

Phase 4 must answer the following:

- does the policy maintain acceptable performance in bear, bull, and mixed markets?
- does the policy reduce exposure or raise cash when market conditions deteriorate?
- does the policy avoid collapsing into a single-symbol concentration under stress?
- does turnover remain within a reasonable operational range under different windows?
- does the ten-symbol extended universe remain usable under the same stress windows?

## Primary Benchmarks

Phase 4 comparisons must continue to include:

- `equal_weight_buy_and_hold`
- `SPY` buy-and-hold

For five-symbol and ten-symbol portfolio comparisons, equal-weight remains the main internal benchmark and `SPY` remains the external market benchmark.

## Required Diagnostics

Each Phase 4 backtest package must report:

- final portfolio value
- cumulative return
- Sharpe ratio
- max drawdown
- executed trades
- per-symbol trade counts
- average cash weight
- average concentration
- core-symbol counts where applicable
- regime-specific average exposure

Each stress package should also include:

- equity curve
- drawdown curve
- position-weight chart
- cash-weight chart
- benchmark-comparison charts

## Defense-Capability Verification

Phase 4 should explicitly test whether the policy behaves defensively when appropriate.

At minimum, the analysis should check:

- whether average cash weight rises in `bear_2022` relative to `bull_2023_2024`
- whether concentration becomes more or less extreme under adverse conditions
- whether turnover spikes excessively during stress
- whether drawdown control remains meaningfully better than the most relevant benchmark

The project should reject any candidate branch that improves headline return but loses basic defense behavior.

## Paper-Trading Preparation Scope

Phase 4 should include a lightweight quasi-production simulation layer:

- daily rebalance-instruction export
- latest-data scoring pipeline
- artifact generation suitable for a small dashboard or local viewer

The initial paper-trading layer should produce:

- date-stamped allocation recommendation
- target weights
- expected cash allocation
- turnover summary
- simple rationale fields derived from diagnostics where possible

The first paper-trading step may remain file-based and local.

## Completion Criteria

Phase 4 can be considered complete for the current round when:

- the frozen Phase 3 mainline best has been stress-tested on all required windows
- five-symbol and ten-symbol stress reports exist
- benchmark comparisons are available for each required window
- defense-capability diagnostics are explicitly documented
- a lightweight paper-trading recommendation pipeline exists
- a Phase 4 report and closure note are produced
