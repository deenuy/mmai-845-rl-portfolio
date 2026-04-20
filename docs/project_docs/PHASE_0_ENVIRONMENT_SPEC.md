# Phase 0 Environment Specification

## Purpose

This document defines the baseline RL trading environment that must be finalized before implementation starts.

It also clarifies the staged evolution path of the system:

1. Single-stock RL training and validation
2. Cross-algorithm comparison on the same single-stock setup
3. Multi-asset portfolio environment expansion
4. Expanded feature and external data integration

The environment designed in Phase 0 must support this evolution without requiring a full rewrite.

## Design Principle

The environment should be built in layers.

- Phase 0 builds the reusable trading environment foundation.
- Phase 1 uses the same environment in single-asset mode.
- Phase 2 extends the environment to portfolio allocation mode.
- Phase 3 expands the state representation with more signals and data sources.

This means the initial environment should be modular, parameterized, and backward compatible.

## Environment Scope in Phase 0

Phase 0 is only responsible for environment infrastructure, not model performance.

Included:

- Historical data ingestion
- Feature generation using past-only information
- Single-asset environment mode
- Execution engine with fee and slippage support
- Portfolio accounting
- Reset, step, termination, and logging behavior
- Safety checks and deterministic validations

Not included:

- Final algorithm comparison conclusions
- Multi-asset portfolio optimization logic
- Advanced macro or alternative data integration
- Production paper trading execution

## Staged Evolution Path

### Stage A: Single-Stock Environment

Goal:

- Validate that one stock can be traded safely and consistently inside the environment.
- Confirm that observations, actions, reward flow, and accounting are correct.

Recommended target:

- Start with `RY` as the initial single-stock symbol.

Environment mode:

- Single tradable asset
- Daily frequency
- Long-only
- Cash always allowed
- No short selling
- Base currency set to `USD`
- Action expressed as a target position
- Discrete `Buy / Hold / Sell` baselines remain supported through wrappers or policy mappings

Primary use:

- Random-agent sanity checks
- Buy-and-hold accounting validation
- First PPO training run
- Later algorithm comparison under the same setup

### Stage B: Algorithm Comparison on Single Stock

Goal:

- Compare multiple algorithms under the same environment assumptions.

Candidate algorithms:

- PPO
- DQN or another discrete baseline, only if the action space is discretized explicitly
- Random policy
- Buy-and-hold benchmark

Important note:

Algorithm comparison belongs to the evaluation workflow, not to the environment core. The environment should expose a stable API that can support both continuous and discrete wrappers if needed.

### Stage C: Multi-Asset Portfolio Environment

Goal:

- Expand from single-stock execution to capital allocation across multiple assets.

Environment upgrade:

- Multiple tradable assets
- Cash as an explicit allocation component
- Rebalancing logic
- Sell-first-then-buy execution ordering
- Weight normalization and allocation constraints

This stage should extend the existing environment interface rather than replace it.

### Stage D: Expanded Data and Feature Support

Goal:

- Add more informative signals after the environment and accounting logic are proven stable.

Examples:

- MACD
- CAPM-based features
- VIX
- Macro indicators
- Market regime indicators

These features should enter through the data and state pipeline, not through ad hoc logic inside the environment step function.

## Baseline Environment Contract

### Time Frequency

- Daily bars only in the first implementation

Reason:

- Simpler accounting
- Easier debugging
- Better reproducibility for the first training loop

### Trading Universe

Initial mode:

- One stock plus cash

Market scope in the initial implementation:

- U.S. equities only
- No TSX symbols
- No FX conversion logic

Future mode:

- Multiple stocks plus cash

### Position Constraints

Initial baseline:

- Long-only
- No leverage
- No short selling
- No margin
- Cash balance cannot go negative

Future extension candidates:

- Per-asset max weight
- Turnover cap
- Minimum rebalance threshold

### Execution Assumptions

- The agent observes the current day's `open` and previously known information before making a decision
- Orders are executed at an effective execution price derived from the current day's close price
- Buy orders include a fixed commission of `1.99 USD` per order
- Sell orders include a fixed commission of `1.99 USD` per order
- Commission is charged per trade regardless of share count
- Slippage is fixed at `5 bps` in the baseline implementation
- Minimum trade value is fixed at `100 USD`
- Accounting must deduct all costs during trade execution
- The execution engine must reserve commission and slippage costs before confirming a buy order
- If the requested target position would cause negative cash after all costs, the executed order size must be reduced automatically
- Trades with notional value below `100 USD` must not be executed

Reference logic:

- `buy_cash_required = shares * close_price + fixed_commission + slippage_cost`
- `sell_cash_received = shares * close_price - fixed_commission - slippage_cost`

### Reward Baseline

Phase 0 environment should support a simple and stable reward definition first.

Recommended baseline reward:

- Step log return of total portfolio value after transaction costs

Optional penalties for later phases:

- Turnover penalty
- Drawdown penalty
- Volatility-aware penalty

Important note:

Step-wise Sharpe should not be the first reward implementation. It can be introduced only after the baseline environment is validated.

### Cash Return Assumption

- Cash should earn a configurable baseline return in order to avoid structurally biasing the agent toward permanent full investment
- The default training configuration should now use a fixed annualized cash yield of `0%`
- Cash yield should accrue daily only on the remaining post-trade cash balance

Important note:

- The initial fixed cash-yield assumption is a modeling convenience, not a live market-rate feed
- A dynamic benchmark-linked cash rate can be introduced in a later phase

### Observation Baseline

Minimum observation contents for the single-stock version:

- Current cash ratio or cash balance
- Current position size or position flag
- Current open price or normalized open representation
- Previous close-to-close return

Optional first-wave indicators:

- SMA-based feature
- RSI-based feature

Rules:

- Features must be computed using only information available up to the current timestep.
- Observation format must be fixed and documented.
- The first implementation should stay limited to single-stock market information plus account information.
- Same-day close information must not appear in the observation before trade execution.

### Episode Rules

- Each episode uses a contiguous historical window
- Reset must initialize cash, holdings, and internal logs consistently
- Episode terminates at the end of the selected data window
- Forced liquidation at episode end must follow documented rules

Recommended baseline:

- Use mark-to-market final valuation without forced extra trade unless explicitly required

### Initial Capital

- Initial portfolio capital is set to `100,000 USD`

Important note:

- This capital level is intentionally large enough to support realistic trading of high-priced single-name equities during early validation.

## Interface Requirements

The environment should be implemented with a stable interface that can survive later phase upgrades.

Recommended methods:

- `reset()`
- `step(action)`
- `render()`
- `get_portfolio_value()`
- `get_diagnostics()`

Recommended internal modules:

- Data loader
- Feature pipeline
- Environment state builder
- Execution engine
- Portfolio accounting
- Metrics logger

## Phase 0 Test Requirements for Environment Finalization

The environment design is considered finalized only when the following checks are explicitly supported:

- Random stepping does not crash
- Cash never becomes negative because of execution ordering
- Holdings never become invalid
- Buy-and-hold valuation matches expected market movement within tolerance
- Reset produces a clean and reproducible initial state
- Features do not leak future information
- Episode termination is deterministic

## Decisions Confirmed in This Version

- Start with a single-stock environment for the first RL training cycle
- Use the same environment family to support later algorithm comparison
- Expand to multi-asset allocation only after the single-stock pipeline is stable
- Introduce broader data sources only after the environment and accounting logic are validated
- Use target-position actions in the single-stock baseline
- Use a fixed commission model first, then add an Interactive Brokers style per-share commission model in a later version
- Use `5 bps` baseline slippage
- Apply a positive configurable cash yield in the baseline environment
- Use whole-share execution during the current development cycle
- Preserve discrete `Buy / Hold / Sell` comparison baselines on top of the target-position environment core
- Use a minimum trade value of `100 USD`
- Use same-day `open` observation with same-day `close` execution in the baseline workflow
- Accrue daily cash yield after trade execution, not before

## Open Decisions for the Next Specification Pass

- Exact train, validation, and test date splits
