# Lessons Learned By Phase

## Phase 0

- Trust the accounting before trusting the reward.
- A correct execution engine prevents months of downstream confusion.
- Same-day information leakage must be blocked explicitly.

## Phase 1

- Positive cash yield can quietly distort PPO behavior.
- Direct drawdown penalties are easy to overdo.
- Stabilization tools like normalization mattered more than we expected.

## Phase 2

- Equal-weight buy-and-hold is a very strong benchmark.
- Multi-asset PPO can look bad simply because the portfolio structure is too reactive.
- Slowing execution cadence can improve both performance and realism.

## Phase 3

- More features are not automatically better.
- Cross-sectional relative strength mattered more than broad market context.
- Feature audit and ablation were worth the time.

## Phase 4

- Stress testing gives very different information from one headline backtest.
- A usable product needs logs, rollback, and a human confirmation step.
- Team handoff is much easier when code, frozen artifacts, and example data are all packaged together.
