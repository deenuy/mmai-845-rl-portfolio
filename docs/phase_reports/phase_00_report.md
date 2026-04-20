# Phase 0 Interim Report

## Current Status

Phase 0 foundation work is in progress and the core engineering baseline has been established.

Completed items:

- Phase-based project governance and reporting structure
- Phase 0 environment specification
- Phase 0 technical specification
- Phase 0 data contract
- Local git repository setup and first GitHub push
- Single-stock environment code skeleton
- Data download, cleaning, and feature-preparation script
- Initial unit-test coverage for data, features, execution, and environment behavior

## Methods Tried

- Translated the original roadmap into a phase-based development framework
- Restricted the initial scope to U.S. equities only with `USD` as the base currency
- Converted the single-stock environment core to target-position control while preserving discrete `Buy / Hold / Sell` baselines
- Implemented whole-share execution with fixed commission, slippage, and minimum trade-value checks
- Built a restricted pre-close observation pipeline to avoid same-day information leakage
- Used `yfinance` as the initial market data source and added cleaning plus reproducibility scripts
- Added unit tests to validate feature generation, execution accounting, minimum-trade suppression, and environment stepping

## Preliminary Results

### Environment Definition and Problem Setup

The current Phase 0 problem setup is:

- Market: U.S. equities only
- Base currency: `USD`
- Initial symbol: `RY`
- Initial capital: `100,000 USD`
- Action mode: continuous target stock weight in `[0, 1]`
- Baseline comparisons kept in scope: random agent, buy-and-hold, discrete `Buy / Hold / Sell`
- Execution timing: observe current-day `open`, execute at current-day `close`
- Execution policy: whole shares only
- Commission: fixed `1.99 USD` per trade
- Slippage: fixed `5 bps`
- Minimum trade value: `100 USD`
- Cash yield: fixed annualized `2%`, accrued daily on remaining post-trade cash
- Observation scope: account information plus restricted single-stock pre-close information

### Engineering Results

- The initial unit test suite passed: `8 passed`
- The Phase 0 data preparation script ran successfully for `RY`
- Cleaned rows kept: `4089`
- Rows dropped during cleaning: `1`
- Baseline validation scripts are now available for random-agent and buy-and-hold evaluation
- The current unit test suite now passes: `10 passed`

Generated local artifacts:

- `data/raw/phase_0_ry_daily.csv`
- `data/processed/phase_0_ry_features.csv`
- `data/processed/phase_0_ry_cleaning_report.json`

### Baseline Results

Random-agent sanity run over `1000` episodes with a `252`-day window:

- Mean final portfolio value: `91249.24`
- Standard deviation: `7202.78`
- Minimum final portfolio value: `71232.51`
- Maximum final portfolio value: `116369.73`

Buy-and-hold baseline over a `252`-day window:

- Final portfolio value: `97396.07`
- Cumulative reward: `-0.026384`
- Final cash: `17.06`
- Final shares: `1863`
- Initial entry alignment logic is now covered by an explicit environment accounting test

## Challenges

- The local environment initially lacked `pytest` and `yfinance`, so dependency installation had to be completed before validation could run
- `yfinance` returned a `MultiIndex` column structure even for a single ticker, which required parser normalization
- `yfinance` also raised cache and local database issues under the current environment, so the timezone cache location had to be redirected into the project workspace
- The initial minimum-trade unit test case was incorrect and had to be rewritten to represent a true sub-threshold trade scenario
- Pytest cache creation still produces a non-blocking permission warning in this environment

## Next Steps

- Save Phase 0 figures and charts into `reports/phase_00/figures/`
- Prepare the first Phase 1 training runner after baseline validation is fully documented
- Add longer stability reporting and optional benchmark exports for later comparison
