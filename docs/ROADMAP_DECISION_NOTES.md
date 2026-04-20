# Roadmap Decision Notes

This note is a condensed summary of the main design decisions made across Phases 0-2.

## Phase 0

- narrowed the initial scope to U.S. equities only
- fixed base currency to `USD`
- selected `RY` as the first single-stock research symbol
- set initial capital to `100,000 USD`
- used whole-share execution only
- fixed commission at `1.99 USD` per trade
- fixed slippage at `5 bps`
- set minimum trade value to `100 USD`
- restricted observation timing to avoid same-day information leakage
- used current-day `open` for decision and current-day `close` for execution
- kept baseline comparisons in scope:
  - random agent
  - buy-and-hold
  - discrete `Buy / Hold / Sell`
- corrected cash accounting so interest applies only to remaining post-trade cash

## Phase 1

- kept `0%` cash yield as the main default after observing that positive cash yield could push PPO toward cash-heavy local optima
- rejected direct drawdown penalty as the default reward because it caused policy collapse
- added medium-term regime features instead of hard-coded heuristic trading rules
- added `VecNormalize` and entropy tuning to stabilize PPO training
- shifted from simple trend-following reward experiments to regime-aware position-sizing guidance
- introduced recovery-versus-downside signals to distinguish healthy pullbacks from persistent weakness
- retained `random` training windows as the default after `rolling` underperformed
- treated Phase 1 as complete once the single-stock PPO pipeline, baselines, reports, and robustness checks were all in place

## Phase 2

- selected a five-symbol first basket with differentiated styles:
  - `RY`
  - `MSFT`
  - `RKLB`
  - `XOM`
  - `PG`
- promoted `equal-weight buy-and-hold` to the main internal portfolio benchmark
- kept `SPY` as the external market benchmark
- preserved high-turnover baselines for context:
  - equal-weight daily rebalance
  - random allocation
- moved toward a slower structural portfolio design instead of only tuning reward terms
- introduced strategic review cadence for portfolio decisions
- froze residual sleeves outside review steps to cut reshuffling
- added richer portfolio diagnostics:
  - per-symbol trade counts
  - average target and realized weights
  - concentration metrics
  - core-symbol rotation counts
- adopted the residual-freeze portfolio PPO as the current best Phase 2 mainline result

## Overall Project Direction

- phase-based development remains the main project workflow
- all major deviations from the original roadmap are recorded in the main documentation
- branch-local heuristic research can inspire the mainline design, but hard-coded discretionary rules stay outside `main`
