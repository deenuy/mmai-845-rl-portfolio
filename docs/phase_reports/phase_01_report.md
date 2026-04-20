# Phase 1 Interim Report

## Objective

Phase 1 extends the completed Phase 0 environment into the first RL training loop for a single-stock problem and compares PPO against baseline behaviors.

## Scope Delivered

- Gymnasium-compatible single-stock environment for PPO training
- PPO smoke-training script with explicit train split configuration
- PPO training pipeline now supports observation normalization with `VecNormalize`
- PPO training pipeline now supports configurable entropy regularization through `ent_coef`
- Backtest runner for validation and test splits
- Mainline observation space now includes medium-term regime features inspired by exploratory heuristic work
- Metric generation for PPO and buy-and-hold
- Regime-aware and trend-alignment backtest summaries
- Chart generation for equity curve, drawdown, PPO target weight, and realized PPO position weight
- Local static display page for backtest inspection
- Position-sizing reward experiments that explicitly train the policy to map trend regimes into differentiated exposure levels

## Test Summary

- Current automated unit tests pass: `18 passed`
- PPO smoke training completed successfully on the train split
- Validation and test backtest artifacts were generated successfully

## Training Configuration

- Train split: `2010-01-01` to `2021-12-31`
- Validation split: `2022-01-01` to `2022-12-31`
- Test split: `2023-01-01` to `2024-12-31`
- Timesteps: `3000`
- Window length: `252`
- Device used for smoke run: `cpu`
- Cash-yield sensitivity experiment: `0%`, `2%`, and `4%`

## Current Main PPO Result

The current strongest Phase 1 single-stock PPO result uses:

- Train split: `2010-01-01` to `2021-12-31`
- Evaluation split: combined `2022-01-01` to `2024-12-31`
- Timesteps: `50000`
- Cash yield: `0%`
- Reward mode: `trend_position_sizing_control`

Main comparison:

- PPO final portfolio value: `111687.70`
- PPO cumulative return: `0.1169`
- PPO Sharpe ratio: `0.3845`
- PPO max drawdown: `-0.2106`
- PPO executed trades: `116`
- Buy-and-hold final portfolio value: `112487.58`
- Buy-and-hold cumulative return: `0.1249`
- Buy-and-hold Sharpe ratio: `0.3036`
- Buy-and-hold max drawdown: `-0.3416`

Interpretation:

- The current strongest mainline PPO policy is now a regime-aware position-sizing model rather than the earlier plain `log_return` baseline
- On the combined `2022-2024` window, it now finishes very close to buy-and-hold while delivering a materially smaller max drawdown
- This makes the current mainline result more attractive on a risk-adjusted basis, even though it still trails buy-and-hold slightly in raw terminal value

## Mainline Regime Upgrade

The Phase 1 mainline has now been upgraded with medium-term trend-state features that were motivated by exploratory heuristic research, without importing any heuristic trading rules into the PPO environment.

Added observation features:

- `sma_30_gap`
- `sma_30_slope`
- `distance_to_20d_high`
- `drawdown_from_30d_peak`
- `trend_persistence_10`
- `downside_pressure_5`

Added evaluation outputs:

- Regime summary for `uptrend`, `downtrend`, and `transition` periods
- Trend-alignment summary tracking whether the policy carries more exposure in favorable regimes than in unfavorable ones

Interpretation:

- These upgrades do not hard-code exits, cooldowns, or allocation ladders into the RL environment
- They instead allow the mainline policy to observe a richer medium-term trend context and let the backtest pipeline explicitly measure whether the learned policy actually behaves like a trend-sensitive allocator
- Because the observation schema changed, all new PPO comparisons after this point require retraining under the expanded feature set rather than reusing older checkpoints
- The newest additions also help the policy distinguish between recoverable pullbacks and sustained downside pressure, which became important after comparing mainline PPO behavior with separate branch-local heuristic research

## Benchmark Comparison

### Validation Split

- PPO final portfolio value: `102011.96`
- PPO cumulative return: `0.0201`
- PPO Sharpe ratio: `250.9980`
- PPO max drawdown: `0.0000`
- Buy-and-hold final portfolio value: `87773.45`
- Buy-and-hold cumulative return: `-0.1223`
- Buy-and-hold Sharpe ratio: `-0.4681`
- Buy-and-hold max drawdown: `-0.2800`

### Test Split

- PPO final portfolio value: `104064.39`
- PPO cumulative return: `0.0406`
- PPO Sharpe ratio: `355.3196`
- PPO max drawdown: `0.0000`
- Buy-and-hold final portfolio value: `128586.41`
- Buy-and-hold cumulative return: `0.2859`
- Buy-and-hold Sharpe ratio: `0.8322`
- Buy-and-hold max drawdown: `-0.2492`

### Combined 2022-2024 Evaluation

- PPO final portfolio value: `106158.12`
- PPO cumulative return: `0.0616`
- PPO Sharpe ratio: `435.3206`
- PPO max drawdown: `0.0000`
- Buy-and-hold final portfolio value: `112490.77`
- Buy-and-hold cumulative return: `0.1249`
- Buy-and-hold Sharpe ratio: `0.3037`
- Buy-and-hold max drawdown: `-0.3416`

### Cash-Yield Sensitivity Finding

- With `0%` cash yield, PPO finished the combined `2022-2024` evaluation at `100000.00`
- With `2%` cash yield, PPO finished at `106158.12`
- With `4%` cash yield, PPO finished at `112694.94`
- Across all three settings, PPO still showed `0.0000` max drawdown

Interpretation:

- Positive cash yield amplified the payoff of a near-cash PPO policy
- However, the persistence of zero drawdown across all settings suggests that limited training and a conservative local optimum remain the larger issue

### Formal 0% vs 2% Comparison at 20000 Timesteps

Using the same train split, seed, and `20000` timesteps:

- `0%` cash yield PPO final portfolio value: `109248.11`
- `0%` cash yield PPO cumulative return: `0.0925`
- `0%` cash yield PPO Sharpe ratio: `0.2766`
- `0%` cash yield PPO max drawdown: `-0.2725`
- `2%` cash yield PPO final portfolio value: `106158.12`
- `2%` cash yield PPO cumulative return: `0.0616`
- `2%` cash yield PPO Sharpe ratio: `435.3206`
- `2%` cash yield PPO max drawdown: `0.0000`

Interpretation:

- The `0%` cash-yield configuration produces a much more realistic risk profile
- The `2%` cash-yield configuration still collapses into an implausibly cash-heavy solution
- Subsequent Phase 1 training should therefore use `0%` cash yield as the main default

### Reward-Shaping Comparison at 20000 Timesteps

Using `0%` cash yield and the same train/evaluation splits:

- Baseline reward `log_return`
  - PPO final portfolio value: `109248.11`
  - PPO cumulative return: `0.0925`
  - PPO Sharpe ratio: `0.2766`
  - PPO max drawdown: `-0.2725`
- Reward `log_return - 0.10 * drawdown`
  - PPO final portfolio value: `100000.00`
  - PPO cumulative return: `0.0000`
  - PPO Sharpe ratio: `0.0000`
  - PPO max drawdown: `0.0000`
- Reward `log_return - 0.01 * drawdown`
  - PPO final portfolio value: `100000.00`
  - PPO cumulative return: `0.0000`
  - PPO Sharpe ratio: `0.0000`
  - PPO max drawdown: `0.0000`

Interpretation:

- A direct drawdown penalty in the current form is too strong, even at `0.01`
- The policy collapses back into a no-risk, near-cash solution instead of learning a selective defensive behavior
- For now, the project should keep `log_return` as the default Phase 1 reward and treat drawdown-aware reward shaping as an experimental branch
- A softer or differently structured risk penalty will be needed later, such as drawdown-increment penalties or downside-only loss penalties

### Observation-Normalization and Exploration Findings

To address policy collapse after expanding the observation space, the training stack was updated to use `VecNormalize` and configurable PPO entropy regularization.

Using the combined `2022-2024` evaluation window with `30000` timesteps:

- `VecNormalize + log_return + ent_coef = 0.0`
  - PPO final portfolio value: `96748.12`
  - PPO cumulative return: `-0.0325`
  - PPO Sharpe ratio: `-0.4094`
  - PPO max drawdown: `-0.0772`
  - PPO executed trades: `129`
- `VecNormalize + log_return + ent_coef = 0.01`
  - PPO final portfolio value: `96334.82`
  - PPO cumulative return: `-0.0367`
  - PPO Sharpe ratio: `-0.4318`
  - PPO max drawdown: `-0.0883`
  - PPO executed trades: `128`
- `VecNormalize + log_return_risk_control + turnover_penalty_coef = 0.002 + downside_penalty_coef = 0.5`
  - PPO final portfolio value: `100000.00`
  - PPO cumulative return: `0.0000`
  - PPO Sharpe ratio: `0.0000`
  - PPO max drawdown: `0.0000`
  - PPO executed trades: `0`
- `VecNormalize + log_return_risk_control + turnover_penalty_coef = 0.005 + downside_penalty_coef = 0.5`
  - PPO final portfolio value: `100000.00`
  - PPO cumulative return: `0.0000`
  - PPO Sharpe ratio: `0.0000`
  - PPO max drawdown: `0.0000`
  - PPO executed trades: `0`

Interpretation:

- Observation normalization successfully prevented the expanded-observation PPO policy from collapsing into a zero-trade solution under pure `log_return`
- However, the resulting policy became clearly over-active, with more than one hundred executed trades in the `2022-2024` window and negative net performance
- Even light turnover and downside penalties in the current formulation were still strong enough to push the policy back to a zero-trade cash solution
- The next reward experiments should therefore reduce penalty coefficients by another order of magnitude and pair them with very small trend-alignment bonuses instead of relying on direct risk penalties alone

### Risk-Control Coefficient Sweep After Normalization

Starting from the first non-collapsed risk-control configuration under `VecNormalize`:

- `turnover_penalty_coef = 0.0001`, `downside_penalty_coef = 0.05`
  - PPO final portfolio value: `101740.43`
  - PPO Sharpe ratio: `0.4327`
  - PPO max drawdown: `-0.0229`
  - PPO executed trades: `47`

The downside sensitivity was then increased while keeping turnover control fixed:

- `turnover_penalty_coef = 0.0001`, `downside_penalty_coef = 0.06`
  - PPO final portfolio value: `101865.21`
  - PPO Sharpe ratio: `0.6050`
  - PPO max drawdown: `-0.0132`
  - PPO executed trades: `37`
- `turnover_penalty_coef = 0.0001`, `downside_penalty_coef = 0.08`
  - PPO final portfolio value: `102661.32`
  - PPO Sharpe ratio: `0.7593`
  - PPO max drawdown: `-0.0115`
  - PPO executed trades: `34`
- `turnover_penalty_coef = 0.0001`, `downside_penalty_coef = 0.10`
  - PPO final portfolio value: `102164.18`
  - PPO Sharpe ratio: `1.0091`
  - PPO max drawdown: `-0.0059`
  - PPO executed trades: `32`
- `turnover_penalty_coef = 0.0001`, `downside_penalty_coef = 0.12`
  - PPO final portfolio value: `100825.77`
  - PPO Sharpe ratio: `0.7078`
  - PPO max drawdown: `-0.0045`
  - PPO executed trades: `23`

Interpretation:

- Increasing downside sensitivity from `0.05` to `0.08` improved all three target behaviors at once: fewer trades, smaller drawdown, and better net performance
- Pushing downside sensitivity further to `0.10` continues to reduce drawdown and trade count, and it produces the strongest Sharpe ratio in the current normalized branch
- However, moving from `0.10` to `0.12` starts to suppress return too aggressively, which suggests the strategy is becoming overly defensive
- In the current setup, stronger downside awareness appears more helpful than dip-buy bonuses, but it now shows a clear return-versus-defense trade-off
- The current best return-oriented defensive configuration is `turnover_penalty_coef = 0.0001` and `downside_penalty_coef = 0.08`
- The current best capital-preservation configuration is `turnover_penalty_coef = 0.0001` and `downside_penalty_coef = 0.10`

### Dip-Buy Bonus Result

A conditional dip-buy reward branch was tested to encourage small add-on entries during short pullbacks inside an upward medium-term trend:

- `trend_dip_buy_risk_control`
- `turnover_penalty_coef = 0.0001`
- `downside_penalty_coef = 0.05`
- `dip_buy_bonus_coef = 0.0002`

Result:

- PPO final portfolio value: `101516.71`
- PPO Sharpe ratio: `0.3789`
- PPO max drawdown: `-0.0238`
- PPO executed trades: `50`

Interpretation:

- The current dip-buy bonus does not improve on the simpler normalized risk-control baseline
- It slightly increases activity without improving risk-adjusted outcome
- The bonus needs a more selective trigger if this direction is revisited

### Active Trend-Following Sweep

Because the project also values visibly adaptive position management, the normalized trend-following branch was revisited under the assumption that roughly `150-200` trades over the full `2022-2024` window is still acceptable for an active single-stock daily strategy.

Starting point:

- `trend_following_risk_control`
- `turnover_penalty_coef = 0.0001`
- `downside_penalty_coef = 0.05`
- `trend_bonus_coef = 0.0005`
  - PPO final portfolio value: `101921.47`
  - PPO Sharpe ratio: `0.1141`
  - PPO max drawdown: `-0.2074`
  - PPO executed trades: `171`

Trend-bonus neighborhood sweep:

- `trend_bonus_coef = 0.0003`
  - PPO final portfolio value: `105295.42`
  - PPO Sharpe ratio: `0.2280`
  - PPO max drawdown: `-0.1685`
  - PPO executed trades: `225`
- `trend_bonus_coef = 0.0007`
  - PPO final portfolio value: `106024.96`
  - PPO Sharpe ratio: `0.2414`
  - PPO max drawdown: `-0.2186`
  - PPO executed trades: `175`
- `trend_bonus_coef = 0.0008`
  - PPO final portfolio value: `106924.98`
  - PPO Sharpe ratio: `0.2653`
  - PPO max drawdown: `-0.2186`
  - PPO executed trades: `171`
- `trend_bonus_coef = 0.0010`
  - PPO final portfolio value: `102508.88`
  - PPO Sharpe ratio: `0.1315`
  - PPO max drawdown: `-0.2356`
  - PPO executed trades: `160`

Interpretation:

- The trend-following branch is materially more expressive than the defensive downside-heavy branch and better matches the intended behavior of adding and trimming exposure with market direction
- Lowering the trend bonus to `0.0003` increased trade count too much, even though headline return improved
- Raising the trend bonus to `0.0007` reduced excess activity relative to `0.0003`, but still underperformed the `0.0008` setting
- Raising the trend bonus to `0.0008` preserved the same approximate trade count as the original active prototype while improving both cumulative return and Sharpe ratio
- Pushing the trend bonus to `0.0010` degraded both return and drawdown, so the active branch now appears to have a useful local optimum rather than a simple monotonic improvement from larger bonuses
- The current best active-trading configuration is therefore the normalized trend-following variant with `turnover_penalty_coef = 0.0001`, `downside_penalty_coef = 0.05`, and `trend_bonus_coef = 0.0008`

### Position-Sizing Guidance Branch

Because the active trend-following branch still behaved more like a coarse market on/off switch than a true allocator, Phase 1 added a dedicated `trend_position_sizing_control` reward branch. This branch trains the policy not only to identify favorable regimes, but also to stay close to a regime-conditioned desired exposure level.

The first stable position-sizing candidate used:

- `reward_mode = trend_position_sizing_control`
- `turnover_penalty_coef = 0.0010`
- `downside_penalty_coef = 0.05`
- `trend_bonus_coef = 0.0008`
- `position_sizing_coef = 0.01`

Under a refined regime-to-weight mapping:

- PPO final portfolio value: `102547.25`
- PPO Sharpe ratio: `0.1340`
- PPO max drawdown: `-0.2470`
- PPO executed trades: `166`
- Uptrend average target weight: `0.8932`
- Transition average target weight: `0.2654`
- Downtrend average target weight: `0.0002`

Interpretation:

- The policy now behaves much more like a true position-sizing allocator
- It carries near-full exposure in strong uptrends, reduced exposure in transitions, and almost no exposure in downtrends
- This branch is behaviorally stronger than the earlier active trend-following branch, even though total return still trails buy-and-hold

### Transition Refinement and Offensive Entry Tuning

The next tuning round focused on the transition regime. A more defensive transition mapping reduced drawdown further but slightly reduced return:

- `transition refined`
  - PPO final portfolio value: `102350.95`
  - PPO Sharpe ratio: `0.1290`
  - PPO max drawdown: `-0.2222`
  - PPO executed trades: `157`
  - Uptrend average target weight: `0.8760`
  - Transition average target weight: `0.1977`
  - Downtrend average target weight: `0.0000`

This established that the main unresolved weakness was no longer defense, but slow or under-sized entry during improving market conditions. To address that, the regime guidance was then made more offensive in early uptrends and positive transitions.

`offensive 30k` result:

- PPO final portfolio value: `103130.01`
- PPO cumulative return: `0.0313`
- PPO Sharpe ratio: `0.1526`
- PPO max drawdown: `-0.2365`
- PPO executed trades: `156`
- Uptrend average target weight: `0.8994`
- Transition average target weight: `0.2385`
- Downtrend average target weight: `0.0000`

Interpretation:

- The more offensive entry logic improved both return and Sharpe relative to the previous two position-sizing variants
- The policy still preserves the desired exposure ordering of high weight in uptrends, partial weight in transitions, and near-zero weight in downtrends
- This makes the `offensive 30k` configuration the current strongest position-sizing candidate on the mainline branch

### 30000 vs 50000 Timesteps for Offensive Position Sizing

The offensive position-sizing configuration was then retrained for `50000` timesteps to test whether longer optimization would further improve upside capture.

`offensive 50k` result:

- PPO final portfolio value: `98375.51`
- PPO cumulative return: `-0.0162`
- PPO Sharpe ratio: `0.0021`
- PPO max drawdown: `-0.2155`
- PPO executed trades: `140`
- Uptrend average target weight: `0.9276`
- Transition average target weight: `0.2041`
- Downtrend average target weight: `0.0000`

Comparison against `offensive 30k`:

- `50000` timesteps increased uptrend exposure and slightly reduced turnover
- However, it produced materially worse overall return than the `30000` timestep run
- The main degradation came from worse performance in transition periods, not from failure to de-risk downtrends

Interpretation:

- Longer training is not currently a monotonic improvement for this branch
- The `offensive 30k` model remains the preferred checkpoint because it balances earlier entry with better overall evaluation performance
- Future tuning should therefore focus on improving transition quality rather than merely increasing PPO training length

### Recovery-vs-Downside Signal Upgrade

After comparing mainline PPO against branch-local heuristic research, the project introduced two additional mainline features to help distinguish recoverable pullbacks from genuinely weak declines:

- `trend_persistence_10`
- `downside_pressure_5`

These signals were used to refine the position-sizing guidance so that the PPO policy could stay more invested during healthy recovery setups while remaining defensive under persistent downside pressure.

`recovery signals 30k` result:

- PPO final portfolio value: `108354.91`
- PPO cumulative return: `0.0835`
- PPO Sharpe ratio: `0.2956`
- PPO max drawdown: `-0.2249`
- PPO executed trades: `131`
- Uptrend average target weight: `0.9243`
- Transition average target weight: `0.3816`
- Downtrend average target weight: `0.0018`

`recovery signals 50k` result:

- PPO final portfolio value: `111687.70`
- PPO cumulative return: `0.1169`
- PPO Sharpe ratio: `0.3845`
- PPO max drawdown: `-0.2106`
- PPO executed trades: `116`
- Uptrend average target weight: `0.9465`
- Transition average target weight: `0.3282`
- Downtrend average target weight: `0.0000`

Interpretation:

- This is the first mainline branch that materially closes the gap to buy-and-hold without giving back the improved drawdown control
- The additional recovery-vs-downside signals improved both return and trade efficiency relative to the earlier `offensive 30k` position-sizing branch
- Longer training now helps on this upgraded branch, unlike the earlier offensive-only mapping
- The current mainline bottleneck is no longer basic regime separation; it is now fine-grained transition management and validation robustness across seeds or symbols

### Multi-Seed Validation for the Mainline Best Checkpoint

The `recovery_signals_50k` branch was then evaluated across multiple random seeds to test whether the improved mainline behavior is robust or still highly path-dependent.

Using the same train/evaluation windows and hyperparameters:

- `seed = 7`
  - PPO final portfolio value: `106926.57`
  - PPO cumulative return: `0.0693`
  - PPO Sharpe ratio: `0.2671`
  - PPO max drawdown: `-0.1995`
  - PPO executed trades: `113`
- `seed = 42`
  - PPO final portfolio value: `111687.70`
  - PPO cumulative return: `0.1169`
  - PPO Sharpe ratio: `0.3845`
  - PPO max drawdown: `-0.2106`
  - PPO executed trades: `116`
- `seed = 123`
  - PPO final portfolio value: `96134.08`
  - PPO cumulative return: `-0.0387`
  - PPO Sharpe ratio: `-0.0887`
  - PPO max drawdown: `-0.2177`
  - PPO executed trades: `236`

Summary statistics:

- Mean final portfolio value: `104916.12`
- Final portfolio value standard deviation: `6506.93`
- Mean Sharpe ratio: `0.1876`
- Sharpe ratio standard deviation: `0.2012`
- Mean executed trades: `155`

Interpretation:

- The upgraded mainline branch is capable of producing strong results, but it is not yet stable enough to treat a single `seed` as definitive evidence of model quality
- `seed = 7` and `seed = 42` both produce sensible trend-sensitive policies with strong drawdown control
- `seed = 123` falls into a worse local optimum with far more trading and clearly weaker net performance
- This means the current bottleneck is no longer just feature design; training stability and checkpoint-selection discipline are now central Phase 1 concerns

### Random vs Rolling Training-Window Sampling

To test whether random window sampling was weakening time-series structure too much, the current best mainline branch was retrained with a `rolling` window schedule instead of random window starts.

`random` sampling result:

- PPO final portfolio value: `111687.70`
- PPO cumulative return: `0.1169`
- PPO Sharpe ratio: `0.3845`
- PPO max drawdown: `-0.2106`
- PPO executed trades: `116`
- Uptrend average target weight: `0.9465`
- Transition average target weight: `0.3282`
- Downtrend average target weight: `0.0000`

`rolling` sampling result:

- PPO final portfolio value: `93595.67`
- PPO cumulative return: `-0.0640`
- PPO Sharpe ratio: `-0.1564`
- PPO max drawdown: `-0.1812`
- PPO executed trades: `75`
- Uptrend average target weight: `0.8638`
- Transition average target weight: `0.1755`
- Downtrend average target weight: `0.0011`

Interpretation:

- The `rolling` schedule did not improve the current PPO training stack
- It produced a more conservative policy with lower turnover, but that conservatism came from under-participation in `uptrend` and `transition` periods
- This suggests that current mainline instability cannot be explained only by random window order; the training objective and PPO optimization path still matter substantially
- For the present Phase 1 setup, `random` window sampling remains the stronger default

### Cross-Symbol Generalization Check

To decide whether Phase 1 was close to closure, the current best mainline PPO recipe was retrained from scratch on a representative five-symbol U.S. validation basket:

- `RY`
- `JPM`
- `AAPL`
- `MSFT`
- `XOM`

All runs used the same configuration:

- Train split: `2010-01-01` to `2021-12-31`
- Evaluation split: combined `2022-01-01` to `2024-12-31`
- Timesteps: `50000`
- Sampling mode: `random`
- Cash yield: `0%`
- Reward mode: `trend_position_sizing_control`
- Turnover penalty coefficient: `0.0010`
- Downside penalty coefficient: `0.05`
- Trend bonus coefficient: `0.0008`
- Position sizing coefficient: `0.01`

Results:

- `RY`
  - PPO final portfolio value: `111687.70`
  - PPO Sharpe ratio: `0.3845`
  - PPO max drawdown: `-0.2106`
  - PPO executed trades: `116`
  - Buy-and-hold final portfolio value: `112487.58`
  - Buy-and-hold Sharpe ratio: `0.3036`
  - Buy-and-hold max drawdown: `-0.3416`
- `JPM`
  - PPO final portfolio value: `94524.02`
  - PPO Sharpe ratio: `-0.0419`
  - PPO max drawdown: `-0.2489`
  - PPO executed trades: `95`
  - Buy-and-hold final portfolio value: `148158.23`
  - Buy-and-hold Sharpe ratio: `0.6512`
  - Buy-and-hold max drawdown: `-0.3946`
- `AAPL`
  - PPO final portfolio value: `125850.78`
  - PPO Sharpe ratio: `0.5692`
  - PPO max drawdown: `-0.1734`
  - PPO executed trades: `84`
  - Buy-and-hold final portfolio value: `137505.14`
  - Buy-and-hold Sharpe ratio: `0.5297`
  - Buy-and-hold max drawdown: `-0.3130`
- `MSFT`
  - PPO final portfolio value: `91867.15`
  - PPO Sharpe ratio: `-0.1214`
  - PPO max drawdown: `-0.2312`
  - PPO executed trades: `118`
  - Buy-and-hold final portfolio value: `125799.63`
  - Buy-and-hold Sharpe ratio: `0.4176`
  - Buy-and-hold max drawdown: `-0.3593`
- `XOM`
  - PPO final portfolio value: `94535.61`
  - PPO Sharpe ratio: `0.0048`
  - PPO max drawdown: `-0.3135`
  - PPO executed trades: `78`
  - Buy-and-hold final portfolio value: `169163.23`
  - Buy-and-hold Sharpe ratio: `0.7832`
  - Buy-and-hold max drawdown: `-0.2050`

Interpretation:

- The current recipe clearly transfers better to some symbols than others
- `RY` remains the strongest demonstration case and still offers a compelling risk-adjusted trade-off relative to buy-and-hold
- `AAPL` is the most encouraging secondary result: it still trails buy-and-hold in terminal value, but it exceeds buy-and-hold on Sharpe while reducing drawdown materially
- `JPM` and `MSFT` suggest that the current regime features and position-sizing policy can become too defensive or mistimed on some strong post-2022 recoveries
- `XOM` is currently a failure case for this recipe, indicating that the current setup does not yet generalize well across all sector styles
- The current Phase 1 method should therefore be described as promising but not yet broadly stable across single-stock symbols

## Figures Generated

Generated local artifacts:

- `artifacts/phase_01/backtests/validation/equity_curve.png`
- `artifacts/phase_01/backtests/validation/drawdown_curve.png`
- `artifacts/phase_01/backtests/validation/ppo_target_weight.png`
- `artifacts/phase_01/backtests/validation/index.html`
- `artifacts/phase_01/backtests/test/equity_curve.png`
- `artifacts/phase_01/backtests/test/drawdown_curve.png`
- `artifacts/phase_01/backtests/test/ppo_target_weight.png`
- `artifacts/phase_01/backtests/test/index.html`

## Risks and Interpretation Notes

- This is still a smoke-training run, not a tuned final model
- The earliest PPO smoke metrics were unrealistically clean, especially the zero drawdown and extreme Sharpe values
- The `0%` cash-yield reruns corrected most of that distortion, but PPO still has not produced robust outperformance over buy-and-hold
- Naive drawdown-penalty reward shaping currently collapses the policy back into a cash-preservation solution
- Expanded-observation experiments have shown that PPO can still collapse into zero-trade solutions, so normalization and exploration tuning are now part of the active mitigation plan
- The newest normalized-observation PPO runs show a two-sided failure mode: without penalties the agent overtrades, and with current penalties it collapses back to cash
- The latest coefficient sweep improved this trade-off substantially, but the strategy still remains far below buy-and-hold in absolute return
- The newest micro-tuning run suggests that downside sensitivity above `0.10` quickly becomes too conservative, so future tuning should focus on more selective entry logic rather than simply increasing penalties
- The refreshed active-trading sweep shows that trend-bonus tuning can improve performance without forcing the policy into a low-turnover defensive style, which better aligns with the intended strategy behavior
- The newest neighborhood test around `trend_bonus_coef = 0.0008` suggests the active branch has a stable sweet spot near that value
- The new position-sizing branch shows that PPO can be pushed beyond simple market on/off behavior into differentiated exposure sizing across regimes
- The latest offensive-entry experiments suggest that the current bottleneck is transition quality rather than inability to de-risk downtrends
- The first longer-horizon retrain on the offensive position-sizing branch (`50000` timesteps) underperformed the `30000` timestep version, so more training alone is not yet the right lever
- The newest recovery-vs-downside signal upgrade materially improved the mainline branch and produced the current best PPO checkpoint on the combined `2022-2024` evaluation window
- Multi-seed validation shows that the current best mainline branch has promise but is still sensitive to stochastic training paths
- The first explicit `rolling`-window training control underperformed the default `random` schedule, so stronger time-order preservation is not automatically helping this PPO stack yet
- The cross-symbol check shows that the best `RY` recipe is not yet a universally strong single-stock method, especially on `JPM`, `MSFT`, and `XOM`
- More training, action-history inspection, and validation plots are needed before making any performance claims

## Next Steps

- Treat `recovery_signals_50k` as the current mainline reference checkpoint
- Use the multi-seed result to define a more disciplined model-selection rule instead of trusting a single best run
- Keep `random` sampling as the default Phase 1 training schedule; do not switch the mainline to `rolling`
- Add richer backtest exports such as daily weights and trade logs for post-hoc diagnosis of weak seeds
- Treat the new five-symbol basket as the first generalization checkpoint, and avoid claiming broad symbol robustness yet
- If one final tuning pass is needed before closure, focus on robustness improvements that can help across symbols rather than another large reward redesign
- The strongest remaining improvement direction is likely a more disciplined checkpoint-selection or ensemble rule, not a new hard-coded regime ladder

## Phase 1 Closure Recommendation

Phase 1 is now closeable from an engineering and research-process perspective.

Closure rationale:

- The single-stock PPO training, evaluation, visualization, and reporting pipeline is complete
- The mainline branch now has a clearly defined reference checkpoint: `recovery_signals_50k`
- The project has already documented its key failure modes through reward-sensitivity checks, multi-seed validation, `random` vs `rolling` sampling comparison, and a first cross-symbol basket
- The method is promising on `RY` and partially encouraging on `AAPL`, but it is not yet robust enough across symbols to justify stronger generalization claims

Recommended Phase 1 close-out statement:

- Phase 1 successfully established a functional single-asset PPO research pipeline
- The best mainline model approaches buy-and-hold on `RY` while improving max drawdown materially
- The remaining weakness is robustness across stochastic training paths and across symbols, which should be treated as a Phase 2/3 development concern rather than a reason to keep extending single-stock Phase 1 indefinitely
