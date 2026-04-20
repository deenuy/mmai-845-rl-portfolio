# Phase 3 Requirements

## Objective

Phase 3 focuses on alpha engineering and tuning on top of the now-stable multi-asset mainline established in Phase 2.

The goal is no longer to prove that the environment works. The goal is to improve portfolio decision quality by expanding the feature set, validating which signals actually help, and tuning PPO with a disciplined experimental process.

## Starting Point

Phase 3 starts from the current best Phase 2 mainline architecture:

- five-asset first basket:
  - `RY`
  - `MSFT`
  - `RKLB`
  - `XOM`
  - `PG`
- continuous portfolio action space with cash
- shared-cash whole-share execution
- strategic review cadence
- residual-sleeve freezing outside review steps
- PPO reward based on `log_return_with_turnover_penalty`

The default Phase 3 reference checkpoint should be the current residual-freeze Phase 2 mainline rather than the older flat portfolio PPO.

## Scope

Phase 3 covers:

- feature expansion
- alpha-factor experiments
- hyperparameter tuning
- ablation studies
- robustness comparison across basket definitions and evaluation windows
- selection of the strongest mainline feature set and training recipe

Phase 3 does not yet include:

- paper trading APIs
- live order routing
- production dashboards
- fully automated deployment workflows

## Development Universe

Phase 3 should use a two-layer symbol scope.

### Layer 1: Core Tuning Basket

The default tuning basket remains the validated five-symbol Phase 2 basket:

- `RY`
- `MSFT`
- `RKLB`
- `XOM`
- `PG`

This keeps continuity with Phase 2 and allows controlled feature experiments.

### Layer 2: Extended Validation Universe

After the core basket experiments stabilize, the project should validate on the broader provisional universe:

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

The full ten-symbol universe should be treated as a later Phase 3 validation step rather than the first tuning target.

## Feature Expansion Requirements

Phase 3 must introduce new features in controlled groups rather than all at once.

Planned feature groups:

### Group A: Trend and Technical Expansion

- `macd`
- `macd_signal`
- `macd_histogram`
- extended moving-average spread features
- breakout and recovery confirmation features

### Group B: Cross-Sectional and Relative Features

- relative strength within the basket
- rank-based momentum features
- symbol-vs-basket return spread
- symbol-vs-market return spread

### Group C: Market Regime Features

- `SPY` trend features
- `SPY` drawdown state
- realized market volatility proxy
- optional `VIX`-linked regime feature if data integration remains lightweight

### Group D: Cash and Risk Context

- stronger regime-aware cash context
- concentration pressure features
- residual drift intensity features

### Group E: Optional Fundamental Proxy Layer

Only if the implementation remains lightweight:

- CAPM-style expected return proxy
- beta-to-market proxy

Fundamental or macro features should be added only if data sourcing is reproducible and does not destabilize the pipeline.

## Experiment Rules

Phase 3 should follow disciplined experiment rules:

- add one feature group at a time
- compare each experiment against the current mainline Phase 2 reference
- keep training/evaluation windows fixed during a given comparison round
- log every accepted change in `docs/ROADMAP_DEVIATIONS.md`
- preserve the same reporting format so results remain comparable

## Hyperparameter Tuning Requirements

Phase 3 should introduce structured PPO tuning after the first feature-expansion round.

Priority tuning targets:

- `learning_rate`
- `n_steps`
- `batch_size`
- `gamma`
- `ent_coef`
- turnover penalty coefficient
- review cadence and residual-freeze threshold if needed

Initial tuning should be lightweight and bounded.

Suggested order:

1. manual shortlist tuning on the core basket
2. optional Optuna integration after the search space is narrowed

Phase 3 should not begin with a large, unconstrained sweep.

## Ablation Requirements

Every major accepted feature upgrade should be followed by an ablation check.

At minimum, Phase 3 should answer:

- did the new feature group improve final value?
- did it improve Sharpe ratio?
- did it improve or worsen max drawdown?
- did it materially change turnover?
- did it improve stability across seeds?

If a feature group increases complexity without improving these outcomes, it should not become part of the default mainline.

## Evaluation Requirements

Phase 3 evaluation must continue using:

- `equal_weight_buy_and_hold` as the main internal benchmark
- `SPY` buy-and-hold as the external benchmark

Phase 3 should add:

- multi-seed comparison for any candidate best model
- at least one alternate evaluation window beyond `2022-2024`
- extended-universe validation after the core basket is tuned

Core tracked metrics:

- final portfolio value
- cumulative return
- Sharpe ratio
- max drawdown
- executed trades
- per-symbol trade counts
- average cash weight
- concentration metrics
- core-symbol rotation counts

## Deliverables

Phase 3 should produce:

- a documented feature-expansion pipeline
- updated aligned datasets if new market-level features are added
- one or more controlled tuning reports
- ablation results for accepted feature groups
- a new best mainline portfolio checkpoint if improvements are confirmed
- a Phase 3 completion report summarizing:
  - feature experiments
  - tuning outcomes
  - ablation findings
  - robustness findings
