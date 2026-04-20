# Phase 2 Requirements

## Objective

Phase 2 upgrades the project from single-stock trading to multi-asset portfolio allocation using a shared cash pool and target-weight actions.

The main goal is to validate that the environment, accounting, and baseline logic remain correct when the agent controls a portfolio rather than a single position.

## Scope

Phase 2 covers:

- multi-asset data alignment
- portfolio-level environment design
- multi-asset execution and rebalancing
- portfolio baselines
- first PPO portfolio training runs

Phase 2 does not yet include:

- macro features
- Optuna hyperparameter sweeps
- live trading integrations
- production dashboard features

## Phase 2 First Basket

The initial development basket is:

- `RY`
- `MSFT`
- `RKLB`
- `XOM`
- `PG`

This basket was chosen to create meaningful variation across:

- financials
- large-cap technology
- emerging aerospace technology
- traditional energy
- consumer staples

## Evaluation Window

The default main Phase 2 portfolio evaluation window remains:

- `2022-01-01` to `2024-12-31`

This preserves continuity with the single-asset Phase 1 validation period and keeps later comparisons interpretable.

## Data Requirements

The multi-asset dataset must:

- use daily U.S. market data only
- align all symbols on a common trading-date index
- retain only dates with valid required fields for every symbol in the basket
- use lowercase snake_case field names
- preserve the existing pre-close observation discipline

Required raw fields per symbol:

- `date`
- `open`
- `high`
- `low`
- `close`
- `volume`

Required engineered features per symbol at the initial Phase 2 step:

- `open_gap`
- `previous_close_return`
- `momentum_5`
- `momentum_20`
- `sma_5_gap`
- `sma_20_gap`
- `sma_30_gap`
- `sma_30_slope`
- `distance_to_20d_high`
- `drawdown_from_30d_peak`
- `volatility_20`
- `trend_persistence_10`
- `downside_pressure_5`

## Observation Requirements

The observation must include:

- portfolio-level account state
- per-symbol feature state
- enough portfolio structure context to support hierarchical allocation decisions

Initial account-state fields:

- `cash_ratio`
- per-symbol current position weights
- per-symbol previous target weights

Phase 2 mainline upgrade direction should additionally support:

- a distinction between a potential core sleeve and residual sleeve
- sufficient state for priority-aware funding decisions
- explicit visibility into residual cash behavior

Initial per-symbol market fields:

- the same restricted pre-close feature set already validated in Phase 1

The observation schema must be deterministic and documented in a fixed field order.

## Action-Space Requirements

The Phase 2 action space must:

- be continuous
- have dimension `N + 1`, where `N` is the number of assets and the final dimension is cash
- support long-only allocation
- support explicit cash holding
- prohibit leverage and shorting in the initial version

The action output must be converted into target weights that sum to `1.0`.

The default normalization method for the first implementation is:

- apply softmax to the raw action vector

Mainline upgrade direction:

- keep the continuous action interface
- allow later hierarchical interpretation of the action output into:
  - core allocation intent
  - residual allocation intent
  - cash allocation intent

## Execution Requirements

The execution engine must:

- compare current portfolio weights against target weights
- compute rebalancing deltas
- execute sells before buys
- apply fixed commission and slippage
- preserve the no-negative-cash constraint
- enforce whole-share execution
- skip orders below the minimum trade value

Initial portfolio execution assumptions:

- commission: `1.99 USD` per executed symbol order
- slippage: `5 bps`
- minimum trade value: `100 USD`
- cash yield: `0%` default

Mainline upgrade direction:

- support priority-aware funding order when capital is insufficient
- allow low-priority residual sleeves to become the default funding source for higher-priority additions
- avoid frequent full residual re-ranking outside scheduled review steps

## Trading-Activity Guideline

Phase 2 should remain active enough to express allocation views, but should avoid obviously excessive churn.

Initial guideline:

- single-symbol trade count should preferably stay in an approximate `100-200` range across the full `2022-2024` evaluation window

This is an evaluation target, not an initial hard rule inside the environment.
If the first portfolio PPO branch exceeds this range materially, the issue should be handled through reward tuning, baseline comparison, and diagnostics before introducing hard trade-count caps.

Mainline upgrade direction:

- residual sleeves should be re-ranked less frequently than the core sleeve
- ordinary rebalance steps should prefer core adjustments over full-book reshuffles

## Reward Requirements

The Phase 2 initial reward should stay simple and stable.

Initial recommendation:

- portfolio-level `log_return`
- optional small turnover penalty only after the base environment is validated

Phase 2 should not begin with:

- direct step-wise Sharpe reward
- strong drawdown penalties
- complex heuristic reward ladders

These can remain later experimental branches after the portfolio environment is proven stable.

Mainline upgrade direction:

- cash should not be a fixed constant sleeve
- the policy should be able to hold materially more cash in weak or ambiguous market conditions
- cash behavior should be regime-aware through state design and mild portfolio-level incentives rather than hard-coded constant allocations

## Baseline Requirements

Phase 2 baseline policies should include at minimum:

- random allocation baseline
- equal-weight buy-and-hold baseline
- cash-only baseline

Optional later baseline additions:

- risk-off heuristic allocation
- volatility-scaled heuristic allocation

Mainline evaluation should also expand beyond return-only comparison and explicitly track:

- per-symbol trade counts
- average target and realized weights by symbol
- exposure concentration diagnostics
- internal basket benchmark comparison against `equal_weight_buy_and_hold`
- robustness checks across multiple evaluation windows

## Validation Requirements

Before PPO portfolio training is treated as meaningful, the environment must pass:

- portfolio random-agent stability checks
- equal-weight buy-and-hold accounting checks
- no-negative-cash validation
- whole-share execution validation
- trade-cost accounting validation
- per-symbol and portfolio-level history export checks

## Deliverables

Phase 2 should produce:

- a synchronized multi-asset dataset for the first basket
- a portfolio trading environment
- portfolio baseline runners
- portfolio backtest metrics and figures
- a first PPO portfolio training checkpoint
- a Phase 2 report with benchmark comparison and visual outputs
