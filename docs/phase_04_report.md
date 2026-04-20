# Phase 4 Report

## Objective

Phase 4 evaluates whether the frozen Phase 3 mainline best branch remains robust under distinct market regimes and whether it can support a lightweight paper-trading workflow.

## Starting Point

Frozen reference branch:

- `Group B core`
- residual-freeze portfolio structure
- cash-yield default `0%`
- strategic review cadence enabled

## Stress-Test Windows

- `bear_2022`
- `bull_2023_2024`
- `mixed_2022_2024`
- `alt_2025`

## Core Basket Results

Frozen reference branch:

- `Group B core`
- residual-freeze portfolio structure
- five-symbol basket: `RY`, `MSFT`, `RKLB`, `XOM`, `PG`

Core stress artifacts:

- [Phase 4 core stress index](C:\MMAI2026RL\artifacts\phase_04\stress\core\index.html)
- [bear_2022 PPO page](C:\MMAI2026RL\artifacts\phase_04\stress\core\bear_2022\ppo\index.html)
- [bull_2023_2024 PPO page](C:\MMAI2026RL\artifacts\phase_04\stress\core\bull_2023_2024\ppo\index.html)
- [mixed_2022_2024 PPO page](C:\MMAI2026RL\artifacts\phase_04\stress\core\mixed_2022_2024\ppo\index.html)
- [alt_2025 PPO page](C:\MMAI2026RL\artifacts\phase_04\stress\core\alt_2025\ppo\index.html)

### bear_2022

- Final portfolio value: `90858.59`
- Cumulative return: `-0.0914`
- Sharpe ratio: `-0.3237`
- Max drawdown: `-0.1933`
- Executed trades: `293`
- Average cash weight: `0.1582`

Comparison summary:

- PPO underperformed the equal-weight buy-and-hold basket on terminal value in the 2022 bear window
- PPO still outperformed `SPY` on terminal value and max drawdown
- the branch remained partially defensive, but not enough to fully avoid loss during the rate-hike bear market

### bull_2023_2024

- Final portfolio value: `181451.24`
- Cumulative return: `0.8145`
- Sharpe ratio: `1.8247`
- Max drawdown: `-0.1565`
- Executed trades: `602`
- Average cash weight: `0.1511`

Comparison summary:

- PPO underperformed equal-weight buy-and-hold on terminal value during the strong recovery and rally window
- PPO strongly outperformed `SPY`
- drawdown remained lower than equal-weight buy-and-hold while preserving high upside capture

### mixed_2022_2024

- Final portfolio value: `170990.32`
- Cumulative return: `0.7099`
- Sharpe ratio: `1.0286`
- Max drawdown: `-0.1933`
- Executed trades: `884`
- Average cash weight: `0.1538`

Comparison summary:

- PPO slightly outperformed the current equal-weight buy-and-hold result on terminal value
- PPO materially outperformed `SPY`
- the full mixed window remains the most balanced summary of the current core-basket behavior

### alt_2025

- Final portfolio value: `139639.89`
- Cumulative return: `0.3964`
- Sharpe ratio: `1.7528`
- Max drawdown: `-0.1550`
- Executed trades: `288`
- Average cash weight: `0.1538`

Comparison summary:

- PPO did not beat equal-weight buy-and-hold on terminal value in `2025`
- PPO delivered higher Sharpe and lower max drawdown than equal-weight buy-and-hold
- PPO also outperformed `SPY` on terminal value, Sharpe ratio, and max drawdown in the current `2025` stress package

## Extended-Universe Results

Extended-universe stress artifacts:

- [Phase 4 extended stress index](C:\MMAI2026RL\artifacts\phase_04\stress\extended\index.html)
- [extended bear_2022 PPO page](C:\MMAI2026RL\artifacts\phase_04\stress\extended\bear_2022\ppo\index.html)
- [extended bull_2023_2024 PPO page](C:\MMAI2026RL\artifacts\phase_04\stress\extended\bull_2023_2024\ppo\index.html)
- [extended mixed_2022_2024 PPO page](C:\MMAI2026RL\artifacts\phase_04\stress\extended\mixed_2022_2024\ppo\index.html)
- [extended alt_2025 PPO page](C:\MMAI2026RL\artifacts\phase_04\stress\extended\alt_2025\ppo\index.html)

### bear_2022

- Final portfolio value: `99989.30`
- Cumulative return: `-0.0001`
- Sharpe ratio: `0.1370`
- Max drawdown: `-0.2573`
- Executed trades: `351`
- Average cash weight: `0.0875`

Comparison summary:

- PPO materially outperformed both equal-weight buy-and-hold and `SPY` on terminal value in the 2022 bear window
- PPO also improved Sharpe relative to both baselines
- drawdown remained worse than equal-weight and slightly worse than `SPY`, so defense in the broader universe is still incomplete

### bull_2023_2024

- Final portfolio value: `186347.67`
- Cumulative return: `0.8635`
- Sharpe ratio: `1.9561`
- Max drawdown: `-0.1703`
- Executed trades: `660`
- Average cash weight: `0.0896`

Comparison summary:

- PPO strongly outperformed `SPY`
- PPO underperformed extended-universe equal-weight buy-and-hold on terminal value and Sharpe
- drawdown remained slightly better than equal-weight in this bullish window

### mixed_2022_2024

- Final portfolio value: `181567.04`
- Cumulative return: `0.8157`
- Sharpe ratio: `1.0688`
- Max drawdown: `-0.2573`
- Executed trades: `1050`
- Average cash weight: `0.0822`

Comparison summary:

- PPO outperformed extended-universe equal-weight buy-and-hold on terminal value and Sharpe
- PPO clearly outperformed `SPY`
- max drawdown was worse than equal-weight, so the edge here came from more aggressive opportunity capture rather than cleaner defense

### alt_2025

- Final portfolio value: `140307.41`
- Cumulative return: `0.4031`
- Sharpe ratio: `1.6263`
- Max drawdown: `-0.2125`
- Executed trades: `316`
- Average cash weight: `0.0822`

Comparison summary:

- PPO outperformed both equal-weight buy-and-hold and `SPY` on terminal value
- PPO also delivered the best Sharpe among the three
- drawdown was slightly worse than equal-weight but worse than `SPY` as well, so the branch remained return-efficient but not uniformly more defensive

## Defense Review

Preliminary defense takeaways from the core basket:

- average cash weight stayed in a fairly stable `~15%` range across all named windows
- `bear_2022` and `mixed_2022_2024` shared the same drawdown floor so far, suggesting the current branch still needs stronger defensive contraction during severe downturns
- the policy remained far more active in `bull_2023_2024` than in `alt_2025`, which is directionally sensible
- turnover was materially lower in `bear_2022` and `alt_2025` than in the full mixed window

Current interpretation:

- the branch is robust and well-behaved
- but it is not yet strongly cash-seeking in bear conditions
- Phase 4 should therefore emphasize defense validation rather than assume that defensive behavior is already solved

Additional interpretation from the extended universe:

- broadening the universe improves return resilience in `bear_2022` and `alt_2025`
- however, broader-universe performance still does not guarantee better drawdown control
- this reinforces the idea that Phase 4 should focus on defense verification rather than only on headline terminal value

Generated defense-summary package:

- [Phase 4 defense summary page](C:\MMAI2026RL\artifacts\phase_04\defense_summary\index.html)
- [Phase 4 defense summary note](C:\MMAI2026RL\artifacts\phase_04\defense_summary\defense_summary.md)

Current defense conclusion:

- the branch is operationally robust across all named windows
- the core basket keeps a larger average cash buffer than the extended universe
- the extended universe improves stress-window survivability on terminal value, but not consistently on drawdown
- the next main Phase 4 question is no longer "does the policy survive?" but rather "does the policy become defensive enough, early enough, under stress?"

## Paper-Trading Preparation

The first lightweight paper-trading export workflow is now implemented.

Artifacts:

- [latest paper-trading page](C:\MMAI2026RL\artifacts\phase_04\paper_trading\latest\index.html)
- [latest paper-trading summary JSON](C:\MMAI2026RL\artifacts\phase_04\paper_trading\latest\paper_trading_summary.json)
- dated snapshot: [2026-04-13 export](C:\MMAI2026RL\artifacts\phase_04\paper_trading\2026-04-13\index.html)

Current workflow assumptions:

- the export runs once per day at an assumed local noon time
- the system refreshes the latest available daily market data
- the portfolio simulation starts at `2026-01-01`
- the first 2026 trading day is initialized as an equal-weight entry across the core basket
- the frozen mainline policy then rolls forward to the latest market date
- the final page shows today's sell-first / buy-second recommendation in dollar terms

Current sample output:

- latest market date used: `2026-04-13`
- simulated portfolio value: `96090.54`
- current cash weight: `0.1562`
- detected core symbol: `XOM`
- current rebalance instructions:
  - sell `MSFT` by approximately `381.42 USD` notional
  - buy `XOM` by approximately `152.25 USD` notional

This completes the first local, file-based paper-trading preparation step for Phase 4.

## Current Status

Phase 4 has started and the first core-basket stress package is now complete.

Completed in this round:

- Phase 4 scope and implementation plan frozen
- named-window stress-test runner implemented
- core-basket stress package generated for:
  - `bear_2022`
  - `bull_2023_2024`
  - `mixed_2022_2024`
  - `alt_2025`
- extended-universe stress package generated for:
  - `bear_2022`
  - `bull_2023_2024`
  - `mixed_2022_2024`
  - `alt_2025`
- first local paper-trading export workflow implemented
- first dated recommendation package generated

Immediate next step:

- refine the recommendation workflow and, if desired, add a dedicated dashboard-style presentation layer on top of the paper-trading export

## Product App MVP

A local product-style profile workflow is now in place.

Artifacts and code:

- product app note: [PHASE_4_PRODUCT_APP.md](C:\MMAI2026RL\docs\PHASE_4_PRODUCT_APP.md)
- profile storage: [profile_store.py](C:\MMAI2026RL\src\rl_portfolio\profile_store.py)
- paper-trading service layer: [paper_trading.py](C:\MMAI2026RL\src\rl_portfolio\paper_trading.py)
- local dashboard runner: [run_product_dashboard.py](C:\MMAI2026RL\scripts\run_product_dashboard.py)

Current MVP behavior:

- users can create a profile with:
  - profile name
  - available cash
  - symbol
  - average cost
  - held shares
- each profile is saved into a local SQLite backend
- users can return later and reopen an existing profile
- the selected profile can be compared against today's frozen policy target
- the page outputs:
  - sell-first instructions
  - buy-second instructions
  - share deltas
  - notional values
  - execution prices
  - holdings dashboard
  - mark-to-market unrealized P&L by symbol

Current usage command:

```powershell
python scripts\run_product_dashboard.py --host 127.0.0.1 --port 8080
```
