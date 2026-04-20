# Phase 3 Report

## Objective

Phase 3 focuses on alpha engineering on top of the validated Phase 2 residual-freeze mainline.

The immediate goal is not to redesign the portfolio environment again. The goal is to test whether controlled feature expansion can improve return quality, preserve drawdown control, and remain interpretable through ablation.

## Frozen Reference

The frozen starting point for Phase 3 is the best validated Phase 2 mainline:

- basket: `RY`, `MSFT`, `RKLB`, `XOM`, `PG`
- reward: `log_return_with_turnover_penalty`
- `turnover_penalty_coef = 0.001`
- `cash_yield = 0%`
- `strategic_review_interval_days = 63`
- `residual_freeze_enabled = true`
- `extreme_residual_drift_threshold = 0.20`

Reference result on `2022-01-01` to `2024-12-31`:

- final portfolio value: `168112.04`
- cumulative return: `0.6811`
- Sharpe ratio: `0.9644`
- max drawdown: `-0.2206`
- executed trades: `907`

## Feature Audit

Before running the first Phase 3 training experiments, the project ran a lightweight feature audit on the existing and newly proposed technical features.

Audit artifacts:

- `artifacts/phase_03/feature_audit/feature_audit_report.md`
- `artifacts/phase_03/feature_audit/feature_audit_summary.json`

The audit found several highly repetitive families:

- `breakout_strength_20` vs `distance_to_20d_high`
- `sma_20_gap` vs `sma_30_gap`
- `macd` vs `macd_signal`
- `momentum_20` vs `sma_30_gap`

This did not justify deleting features blindly, but it did justify testing both a full and a reduced technical stack.

## Group A Experiments

### Group A Full

Added features:

- `macd`
- `macd_signal`
- `macd_histogram`
- `breakout_strength_20`
- `breakout_persistence_5`
- `recovery_strength_10`
- `recovery_pressure_5`

Result:

- final portfolio value: `153607.65`
- cumulative return: `0.5361`
- Sharpe ratio: `0.8377`
- max drawdown: `-0.1990`
- executed trades: `894`

Interpretation:

- the model remained stable
- turnover did not explode
- drawdown slightly improved
- but the stack underperformed the frozen Phase 2 reference on both final value and Sharpe

### Group A Reduced

Kept only the less redundant additions:

- `macd_histogram`
- `breakout_persistence_5`
- `recovery_strength_10`
- `recovery_pressure_5`

Result:

- final portfolio value: `154930.94`
- cumulative return: `0.5493`
- Sharpe ratio: `0.8576`
- max drawdown: `-0.2088`
- executed trades: `892`

Interpretation:

- reduced Group A was better than full Group A
- the feature audit therefore improved the first ablation decision
- but even the reduced stack still failed to beat the Phase 2 reference

Conclusion for Group A:

- `Group A full` should not be promoted
- `Group A reduced` is the better technical branch, but it remains experimental

## Group B Experiment

The first Group B round focused only on clean cross-sectional signals derived from the five-symbol basket itself.

Added features:

- `cs_momentum_rank_20`
- `cs_momentum_spread_20`
- `cs_breakout_rank_20`
- `cs_breakout_spread_20`
- `cs_drawdown_rank_30`
- `cs_drawdown_spread_30`

This design intentionally avoided market-level context so that the experiment isolated whether basket-relative information alone helped.

Result:

- final portfolio value: `170650.83`
- cumulative return: `0.7065`
- Sharpe ratio: `1.0267`
- max drawdown: `-0.1973`
- executed trades: `898`

Interpretation:

- Group B core outperformed the frozen Phase 2 reference on final value
- Group B core also improved Sharpe ratio
- max drawdown improved materially
- turnover remained slightly lower than the reference

This is the first Phase 3 branch that clearly beats the Phase 2 mainline without sacrificing stability.

### Group B Multi-Seed Validation

The project then reran `Group B core` across three seeds to verify that the improvement was not a single-run artifact.

- `seed 7`
  - final portfolio value: `164923.30`
  - Sharpe ratio: `0.9665`
  - max drawdown: `-0.2128`
  - executed trades: `904`
- `seed 42`
  - final portfolio value: `170650.83`
  - Sharpe ratio: `1.0267`
  - max drawdown: `-0.1973`
  - executed trades: `898`
- `seed 123`
  - final portfolio value: `184387.71`
  - Sharpe ratio: `1.1208`
  - max drawdown: `-0.2344`
  - executed trades: `876`

Summary statistics:

- mean final portfolio value: `173320.61`
- final value std: `8167.48`
- mean Sharpe ratio: `1.0380`
- Sharpe std: `0.0635`
- mean executed trades: `892.67`

Interpretation:

- `Group B core` remained strong across all tested seeds
- no seed collapsed into the kind of unstable behavior seen in earlier exploratory branches
- the branch therefore qualifies as a robust candidate rather than a one-off win

### Group B Alternate Window Check (`2025`)

The current `Group B core` seed-42 checkpoint was then evaluated on a separate `2025-01-01` to `2025-12-31` window.

Result:

- final portfolio value: `139639.89`
- cumulative return: `0.3964`
- Sharpe ratio: `1.7528`
- max drawdown: `-0.1550`
- executed trades: `288`

Comparison against the `2025` equal-weight basket baseline:

- `Group B core` final portfolio value: `139639.89`
- `equal_weight_buy_and_hold` final portfolio value: `147025.63`
- `Group B core` Sharpe ratio: `1.7528`
- `equal_weight_buy_and_hold` Sharpe ratio: `1.5730`
- `Group B core` max drawdown: `-0.1550`
- `equal_weight_buy_and_hold` max drawdown: `-0.1936`

Interpretation:

- `Group B core` did not win on terminal value in the `2025` window
- but it delivered higher risk-adjusted performance and lower drawdown
- this suggests the branch is not merely overfit to `2022-2024`, even though its advantage may express more through risk control than raw upside in alternate windows

## Group C Experiment

The first Group C round added a minimal market-context layer on top of the current basket-level stack.

Added market-level context:

- `SPY` medium-term momentum
- `SPY` medium-term moving-average gap
- `SPY` drawdown-from-peak state
- `SPY` realized volatility proxy
- `SPY` trend persistence

This version was intentionally lightweight. The goal was to test whether broad-market regime awareness improved the already strong `Group B core` branch.

Result:

- final portfolio value: `149926.39`
- cumulative return: `0.4993`
- Sharpe ratio: `0.8035`
- max drawdown: `-0.2245`
- executed trades: `887`

Comparison against `Group B core`:

- `Group C core` final portfolio value: `149926.39`
- `Group B core` final portfolio value: `170650.83`
- `Group C core` Sharpe ratio: `0.8035`
- `Group B core` Sharpe ratio: `1.0267`
- `Group C core` max drawdown: `-0.2245`
- `Group B core` max drawdown: `-0.1973`

Interpretation:

- the first market-context layer did not improve the strategy
- the branch underperformed `Group B core` on both return quality and drawdown
- the result suggests that this simple market overlay adds more noise than useful regime information for the current stack

Important engineering note:

- even though this experiment failed as a model upgrade, the project now has a reusable market-context data path through `market__...` features
- future market-level experiments can therefore iterate without rebuilding the portfolio panel format or the environment interface

## Group B Bounded Tuning

After `Group B core` became the leading Phase 3 branch, the project ran a deliberately small tuning pass instead of a broad hyperparameter sweep.

The goal was to check whether a few low-risk adjustments could improve the branch without blurring the Phase 3 feature-first discipline.

### Tuning Variants

The following bounded variants were evaluated against the frozen `Group B core` configuration:

- lower learning rate: `learning_rate = 1e-4`
- larger rollout and batch:
  - `n_steps = 2048`
  - `batch_size = 512`
- slightly lower turnover penalty:
  - `turnover_penalty_coef = 0.0007`

### Results

Frozen `Group B core` reference:

- final portfolio value: `170650.83`
- Sharpe ratio: `1.0267`
- max drawdown: `-0.1973`
- executed trades: `898`

Lower learning rate:

- final portfolio value: `169731.69`
- Sharpe ratio: `1.0025`
- max drawdown: `-0.2087`
- executed trades: `862`

Larger rollout:

- final portfolio value: `171278.21`
- Sharpe ratio: `0.9923`
- max drawdown: `-0.2287`
- executed trades: `849`

Lower turnover penalty:

- final portfolio value: `172013.92`
- Sharpe ratio: `0.9970`
- max drawdown: `-0.2197`
- executed trades: `875`

Interpretation:

- none of the bounded tuning variants dominated `Group B core` across return, Sharpe, and drawdown at the same time
- some variants improved one metric while degrading another
- the strongest conclusion is that the untuned `Group B core` remains the best balanced Phase 3 candidate

Conclusion for bounded tuning:

- keep `Group B core` unchanged as the current lead branch
- do not promote any of the tuning variants
- reserve future tuning for later phases or for more targeted follow-up after stronger feature evidence appears

## Extended-Universe Validation

To test whether `Group B core` was only effective on the five-symbol basket, the project reran the same method on the larger ten-symbol provisional Phase 2/3 universe:

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

### Extended-Universe Baseline

Equal-weight buy-and-hold:

- final portfolio value: `170993.41`
- cumulative return: `0.7099`
- Sharpe ratio: `0.9622`
- max drawdown: `-0.2344`

`SPY` buy-and-hold:

- final portfolio value: `122597.42`
- cumulative return: `0.2260`
- Sharpe ratio: `0.4781`
- max drawdown: `-0.2533`

### Group B Core on the Extended Universe

Result:

- final portfolio value: `181567.04`
- cumulative return: `0.8157`
- Sharpe ratio: `1.0688`
- max drawdown: `-0.2573`
- executed trades: `1050`

Interpretation:

- `Group B core` continued to outperform both `SPY` and equal-weight buy-and-hold on terminal value
- `Group B core` also improved Sharpe ratio relative to equal-weight buy-and-hold
- max drawdown was slightly worse than equal-weight buy-and-hold, so the branch still carries a concentration and timing cost when scaled to the larger universe

Conclusion for the extended-universe check:

- `Group B core` is not limited to the five-symbol development basket
- the branch remains competitive after the basket is expanded to ten symbols
- this makes `Group B core` the first Phase 3 branch with both multi-seed support and cross-universe support

### Extended-Universe Multi-Seed Validation

The project then repeated the extended-universe `Group B core` run across three seeds to verify that the broader-universe result was not a one-off.

- `seed 7`
  - final portfolio value: `202924.96`
  - Sharpe ratio: `1.2881`
  - max drawdown: `-0.2354`
  - executed trades: `987`
- `seed 42`
  - final portfolio value: `181567.04`
  - Sharpe ratio: `1.0688`
  - max drawdown: `-0.2573`
  - executed trades: `1050`
- `seed 123`
  - final portfolio value: `209247.88`
  - Sharpe ratio: `1.3231`
  - max drawdown: `-0.2125`
  - executed trades: `957`

Summary statistics:

- mean final portfolio value: `197913.29`
- final value std: `11913.66`
- mean Sharpe ratio: `1.2269`
- Sharpe std: `0.1124`
- mean executed trades: `998.00`

Interpretation:

- the ten-symbol version remained strong across all tested seeds
- no seed collapsed into a weak or obviously unstable portfolio
- the broader-universe branch is therefore materially stronger than a single-seed validation story

Extended-universe conclusion:

- `Group B core` now has support across
  - multiple seeds on the five-symbol basket
  - an alternate `2025` time window
  - a ten-symbol universe
  - multiple seeds on that ten-symbol universe
- this is strong enough to treat `Group B core` as the current Phase 3 mainline best branch

## Group B Subgroup Ablation

To identify which cross-sectional signal family is actually carrying the improvement, the project decomposed `Group B core` into smaller branches.

Evaluated variants:

- `Group B momentum`
- `Group B breakout`
- `Group B drawdown`
- `Group B momentum + drawdown`

All runs used the same residual-freeze mainline structure, the same basket, and the same training budget as the original `Group B core`.

### Results

`Group B core`

- final portfolio value: `170650.83`
- Sharpe ratio: `1.0267`
- max drawdown: `-0.1973`
- executed trades: `898`

`Group B momentum`

- final portfolio value: `142424.38`
- Sharpe ratio: `0.7288`
- max drawdown: `-0.2446`
- executed trades: `894`

`Group B breakout`

- final portfolio value: `165964.80`
- Sharpe ratio: `0.9513`
- max drawdown: `-0.1965`
- executed trades: `877`

`Group B drawdown`

- final portfolio value: `164097.12`
- Sharpe ratio: `0.9840`
- max drawdown: `-0.1749`
- executed trades: `899`

`Group B momentum + drawdown`

- final portfolio value: `139504.21`
- Sharpe ratio: `0.6920`
- max drawdown: `-0.2372`
- executed trades: `878`

### Interpretation

- `momentum-only` is clearly not sufficient in the current portfolio stack
- `momentum + drawdown` also underperformed badly, which means the useful effect is not simply "trend plus downside awareness"
- `breakout-only` remained competitive and was the closest simplified branch to the full `Group B core`
- `drawdown-only` produced the best drawdown control among the simplified variants while keeping Sharpe reasonably strong

The strongest explanation is:

- the current `Group B core` edge is driven mainly by `breakout` and `drawdown` relative information
- `momentum` appears to add little by itself and may even dilute the cleaner cross-sectional signals

Conclusion for subgroup ablation:

- do not promote `Group B momentum`
- do not promote `Group B momentum + drawdown`
- keep `Group B core` as the lead branch
- treat `Group B breakout` and `Group B drawdown` as the two most informative simplified candidates for future refinement

## Current Status

Phase 3 is now beyond planning and has entered controlled feature experimentation.

Current stack ranking:

1. `Group B core`
2. `Phase 2 residual-freeze reference`
3. `Group A reduced`
4. `Group C core`
5. `Group A full`

Additional ranking note:

- the bounded Group B tuning variants remain below the untuned `Group B core`
- the extended-universe multi-seed validation now strengthens confidence enough to treat `Group B core` as the current Phase 3 mainline best
- within Group B itself, the signal contribution appears to come primarily from breakout and drawdown-relative information rather than the momentum-only branch

## Recommended Next Step

The next recommended step is still not a large hyperparameter sweep.

The best next move is:

1. freeze `Group B core` as the current Phase 3 mainline best
2. use the existing bounded tuning result as a stopping signal rather than continuing blind hyperparameter changes
3. use the existing market-context pipeline only for later, more targeted regime experiments rather than immediate promotion
4. treat any future feature work as narrow follow-up rather than broad exploratory expansion
5. if another feature round is attempted, bias it toward the `breakout` and `drawdown` families rather than adding more generic momentum descriptors

This preserves the feature-first, ablation-driven discipline defined at the start of Phase 3.
