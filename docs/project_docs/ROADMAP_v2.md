# RL-Powered Portfolio Management System Development Roadmap (v2.0)

## Project Overview

This project aims to develop a fully automated quantitative trading agent based on Reinforcement Learning (RL). The system will initially interact only with U.S. stock market data, discarding traditional hard-coded rules to learn optimal asset allocation strategies through continuous interaction with complex market environments.

- Core algorithm: PPO (continuous action space)
- Development framework: Stable-Baselines3 + custom Gym environment
- Benchmarks: Buy & Hold (B&H), market index, basic DQN strategy (discrete baseline)
- Core business objectives: maximize risk-adjusted returns (Sharpe/Sortino), strictly control max drawdown, and replace emotional manual trading

## Phased Rollout

### Phase 0: Data & Environment Infrastructure

**Goal:** Build a high-quality data feed pipeline and complete the core RL environment construction. Do not introduce any RL algorithms until the environment passes full stress testing.

- Data pipeline: Use `yfinance` to ingest 10 years of OHLCV data from U.S. equities.
- Basic feature engineering: Transform absolute prices into stationary time-series features. Pre-calculate daily returns, SMA, RSI (14-day), etc., and concatenate them into the state space.
- Execution engine development (critical):
  - Adopt the effective execution price method.
  - Directly integrate transaction fees (commission) and slippage into the environment's bid/ask quotes (`P_buy = P_close * (1 + fee)`).
  - Fundamentally avoid the pool overdraft (negative cash) bug caused by "buy first, deduct fee later" logic.

**Deliverables:** A clean Pandas DataFrame data source and a fully encapsulated `trading_env.py`.

### Phase 1: Single Asset Validation

**Goal:** Run the entire RL training and evaluation pipeline on a single stock (initially `RY`) to verify the rigor of the environment logic.

- Environment sanity check:
  - Introduce a random agent to run 1,000 episodes, ensuring that no matter how randomly it operates, the system will not crash, liquidate, or enter a logical dead loop.
  - Introduce a buy-and-hold agent to verify whether the final net worth calculation aligns with actual market returns.
- Initial training: Integrate SB3 PPO for initial training.

**Deliverables:** A successfully executed single-asset training pipeline; the agent's cumulative return outperforms the buy-and-hold baseline on the validation set.

### Phase 2: Portfolio Allocation

**Goal:** Leap from single-stock trading decisions to multi-asset capital pool management. This is expected to be the most technically challenging phase.

- Action space restructuring:
  - Discard the discrete `{Buy, Sell, Hold}` action space.
  - For `N` stocks, use an `N + 1` dimensional continuous action space including cash.
- Softmax weight allocation:
  - The agent outputs a vector at each step.
  - The environment converts it into target weights totaling 100% via a softmax function.
- Automated rebalancing execution:
  - The execution engine calculates the deviation between current holdings and target weights.
  - Execute a "sell first, then buy" rebalancing action.
  - This design supports the agent's autonomous decision to hold cash.
- Reward function:
  - Upgrade from simple P&L to a step-wise Sharpe ratio.
  - Penalize high volatility and frequent trading friction.

**Deliverables:** A PPO model capable of managing a dynamic portfolio of 3-6 U.S. stocks, outputting total return, Sharpe ratio, and max drawdown reports, compared against the DQN baseline.

### Phase 3: Alpha Engineering & Tuning

**Goal:** With stable infrastructure in place, concentrate effort on improving predictive and decision-making capability.

- State space expansion: Introduce CAPM expected returns, MACD, broad market volatility (VIX), or basic macroeconomic indicators.
- Hyperparameter sweep: Use Optuna for automated tuning of core PPO parameters such as `learning_rate`, `n_steps`, `batch_size`, and `gamma`.
- Ablation study: Verify whether newly added factors and indicators provide information gain, and eliminate redundant noise.

**Deliverables:** Lock in the final optimal model architecture and feature combination.

### Phase 4: Stress Testing & Paper Trading

**Goal:** Validate survivability in extreme market conditions and move toward a quasi-production setup.

- Extreme stress testing:
  - Run against a complete test set covering major bear markets and high-volatility periods (for example, the 2022 rate hike cycle).
  - Include major bull markets (for example, the 2023-2024 technology rally).
- Defense capability verification:
  - Focus on whether the model learned to proactively increase cash allocation during bear markets.
  - Reject overfitted models that only learned to remain fully invested.
- Web dashboard deployment:
  - Build a lightweight frontend dashboard.
  - Connect to a paper trading API.
  - Pull the latest market data daily and output next-day rebalancing instructions.

**Deliverables:** A comprehensive automated backtesting report and a demo product where the frontend can display the agent's real-time decision logic.
