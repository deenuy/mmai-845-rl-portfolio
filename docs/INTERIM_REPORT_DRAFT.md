# Interim Report Draft

## Project Overview

This project develops a reinforcement-learning-based portfolio management system that progresses from single-asset environment validation to multi-asset allocation. The current development scope covers three completed stages of work:

- `Phase 0`: environment, execution, and data infrastructure
- `Phase 1`: single-stock PPO training and evaluation
- `Phase 2`: five-asset portfolio environment, baselines, and first portfolio PPO pipeline

The guiding objective is to learn portfolio decisions that improve risk-adjusted performance while maintaining realistic execution logic, bounded trading activity, and interpretable portfolio behavior.

## Phase 0 Summary: Environment and Execution Infrastructure

Phase 0 established the engineering baseline needed for all later work. The project scope was narrowed to U.S. equities only with `USD` as the base currency, and `RY` was selected as the first single-stock research symbol. A full data and execution contract was written before training began, including whole-share trading, fixed commission, slippage, minimum trade value, and a restricted observation design to avoid same-day information leakage.

The single-stock environment was implemented with the following core assumptions:

- observe current-day `open`
- execute trades at current-day `close`
- whole shares only
- fixed commission `1.99 USD`
- fixed slippage `5 bps`
- minimum trade value `100 USD`

Data preparation was automated through `yfinance`, with cleaning, feature construction, and reproducibility scripts saved in the repository. Baseline validation was also added through random-agent and buy-and-hold runners. At the end of Phase 0, the project had a working environment, stable accounting logic, reproducible data artifacts, and passing unit tests. This phase reduced the risk of training on a logically incorrect environment and created the reporting structure used throughout the rest of the project.

## Phase 1 Summary: Single-Stock PPO Research

Phase 1 moved from infrastructure into the first real reinforcement-learning loop. The initial PPO stack was connected to the `RY` single-stock environment, and a backtesting/reporting pipeline was built to compare PPO against buy-and-hold. Multiple reward and feature experiments were tested during this phase, including cash-yield sensitivity, direct drawdown penalties, trend-following rewards, observation normalization, and regime-aware position sizing.

The most important findings from Phase 1 were not only about raw returns, but about what made the policy behave plausibly:

- positive cash yield could push PPO toward overly cash-heavy solutions
- naive drawdown penalties caused policy collapse
- observation normalization and medium-term regime features improved learnability
- the strongest improvement came from distinguishing recoverable pullbacks from persistent downside pressure

The final strongest Phase 1 mainline checkpoint used a regime-aware position-sizing reward with additional recovery-vs-downside signals. On the combined `2022-01-01` to `2024-12-31` evaluation window, it produced:

- PPO final portfolio value: `111687.70`
- PPO cumulative return: `0.1169`
- PPO Sharpe ratio: `0.3845`
- PPO max drawdown: `-0.2106`
- PPO executed trades: `116`

For reference, buy-and-hold on the same window produced:

- final portfolio value: `112487.58`
- cumulative return: `0.1249`
- Sharpe ratio: `0.3036`
- max drawdown: `-0.3416`

This result is important because PPO did not beat buy-and-hold on terminal value, but it came very close while materially improving drawdown control. That made Phase 1 a successful single-asset proof of concept. At the same time, multi-seed validation and cross-symbol tests showed that the method was still sensitive to training path and market style, so Phase 1 ended with a strong pipeline but not with a claim of universal robustness.

## Phase 2 Summary: Multi-Asset Portfolio Environment

Phase 2 upgraded the project from a single-stock RL setup to a shared-cash portfolio environment. A five-symbol first basket was selected to maximize style diversity while preserving continuity with Phase 1:

- `RY`
- `MSFT`
- `RKLB`
- `XOM`
- `PG`

The portfolio environment now supports:

- aligned multi-asset feature panels
- cash plus five risky assets
- whole-share execution
- commission and slippage
- minimum trade value
- portfolio accounting
- target-weight rebalancing

Before portfolio PPO training, several portfolio baselines were established. The most important internal benchmark is equal-weight buy-and-hold, which outperformed `SPY` over the project’s main portfolio evaluation window (`2022-01-01` to `2024-12-31`):

- equal-weight buy-and-hold final portfolio value: `143699.58`
- equal-weight buy-and-hold Sharpe ratio: `0.7542`
- equal-weight buy-and-hold max drawdown: `-0.2116`

- `SPY` buy-and-hold final portfolio value: `122597.42`
- `SPY` Sharpe ratio: `0.4781`
- `SPY` max drawdown: `-0.2533`

The first portfolio PPO version worked technically, but its behavior was not acceptable. It traded too often and underperformed the equal-weight benchmark:

- original PPO final portfolio value: `129842.50`
- original PPO Sharpe ratio: `0.5898`
- original PPO executed trades: `3607`

The biggest Phase 2 breakthrough came after introducing a slower structural logic inspired by exploratory research: residual sleeves were frozen outside strategic review steps, instead of being fully reshuffled on every ordinary rebalance. This change substantially improved both return and turnover behavior:

- residual-freeze PPO (`cash_yield = 0%`) final portfolio value: `168112.04`
- residual-freeze PPO Sharpe ratio: `0.9644`
- residual-freeze PPO max drawdown: `-0.2206`
- residual-freeze PPO executed trades: `907`

This made the current best Phase 2 mainline clearly stronger than the original flat portfolio PPO and competitive with the project’s key internal benchmarks. It also showed that structural portfolio design matters at least as much as reward tuning.

## Main Technical Lessons So Far

Across Phases 0-2, several lessons have become clear.

First, realistic execution assumptions matter. Commission, slippage, whole-share constraints, minimum trade thresholds, and post-trade cash accounting all materially affected behavior. This was especially visible when the policy tried to overtrade or collapse into unrealistic cash-heavy solutions.

Second, reward shaping must be handled carefully. Direct risk penalties often looked attractive in theory but caused degenerate behavior in practice. Better results came from adding information and structure rather than over-penalizing the objective.

Third, feature design and action structure became more important as the problem scaled. In Phase 1, medium-term regime features improved the single-stock policy. In Phase 2, slower structural portfolio updates were far more effective than simply adding more reward terms.

Fourth, internal benchmarks matter. In the portfolio case, `SPY` alone is not a sufficient benchmark because the selected basket itself is strong. Equal-weight buy-and-hold remains the most meaningful Phase 2 comparison point.

## Current Status and Recommended Next Direction

The project is now at a credible midpoint:

- Phase 0 is complete
- Phase 1 is functionally complete and documented
- Phase 2 environment, baselines, and first strong portfolio PPO result are in place

The best current mainline result in Phase 2 is the residual-freeze PPO with `0%` cash yield. The next logical step is not a complete redesign, but a focused stabilization pass:

- multi-seed validation for the best Phase 2 configuration
- richer core/residual/cash diagnostics
- more explicit concentration control
- continued comparison against equal-weight buy-and-hold

At this stage, the project can credibly report that it has progressed from environment construction to a functioning multi-asset RL allocation system with interpretable baselines, visual reporting, and one promising portfolio architecture that materially improved both return and turnover relative to the first portfolio PPO implementation.
