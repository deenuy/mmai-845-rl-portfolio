"""Evaluation helpers for single-asset and portfolio baseline runners."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable

import numpy as np
import pandas as pd

from .config import EnvironmentConfig
from .environment import TradingEnv


@dataclass(frozen=True)
class EpisodeSummary:
    """Summary statistics for a completed baseline episode."""

    steps: int
    final_portfolio_value: float
    cumulative_reward: float
    final_cash: float
    final_shares: int


@dataclass(frozen=True)
class PortfolioEpisodeSummary:
    """Summary statistics for a completed portfolio baseline episode."""

    steps: int
    final_portfolio_value: float
    cumulative_reward: float
    final_cash: float
    final_shares_by_symbol: dict[str, int]


@dataclass(frozen=True)
class BuyAndHoldAlignment:
    """Expected first-trade accounting values for buy-and-hold validation."""

    initial_open: float
    initial_close: float
    expected_execution_price: float
    expected_shares: int
    expected_remaining_cash: float
    expected_commission: float
    expected_slippage_paid: float


@dataclass(frozen=True)
class BacktestMetrics:
    """Core backtest metrics for a completed policy run."""

    initial_portfolio_value: float
    final_portfolio_value: float
    cumulative_return: float
    sharpe_ratio: float
    max_drawdown: float
    executed_trades: int
    trade_rate: float
    average_turnover: float

    def to_dict(self) -> dict[str, float]:
        """Return a JSON-serializable metrics payload."""

        return asdict(self)


@dataclass(frozen=True)
class RegimeMetrics:
    """Summary statistics for a single market regime segment."""

    periods: int
    average_target_weight: float
    average_portfolio_return: float
    executed_trades: int
    trade_rate: float

    def to_dict(self) -> dict[str, float | int]:
        """Return a JSON-serializable metrics payload."""

        return asdict(self)


@dataclass(frozen=True)
class TrendAlignmentSummary:
    """Diagnostics for whether the strategy scales exposure with the trend."""

    uptrend_periods: int
    downtrend_periods: int
    transition_periods: int
    average_target_weight_uptrend: float
    average_target_weight_downtrend: float
    average_target_weight_transition: float
    average_weight_spread: float
    trend_following_share: float

    def to_dict(self) -> dict[str, float | int]:
        """Return a JSON-serializable metrics payload."""

        return asdict(self)


def run_policy_episode(env: TradingEnv, policy: Callable[[TradingEnv], float]) -> EpisodeSummary:
    """Run a policy until the current environment window terminates."""

    observation, _ = env.reset()
    del observation

    cumulative_reward = 0.0
    steps = 0
    terminated = False
    truncated = False
    info = env.get_diagnostics()

    while not terminated and not truncated:
        action = policy(env)
        _, reward, terminated, truncated, info = env.step(action)
        cumulative_reward += reward
        steps += 1

    return EpisodeSummary(
        steps=steps,
        final_portfolio_value=float(info["portfolio_value"]),
        cumulative_reward=float(cumulative_reward),
        final_cash=float(info["cash"]),
        final_shares=int(info["shares"]),
    )


def run_portfolio_policy_episode(env: object, policy: Callable[[object], np.ndarray]) -> PortfolioEpisodeSummary:
    """Run a portfolio policy until the environment window terminates."""

    observation, _ = env.reset()
    del observation

    cumulative_reward = 0.0
    steps = 0
    terminated = False
    truncated = False
    info = env.get_diagnostics()

    while not terminated and not truncated:
        action = policy(env)
        _, reward, terminated, truncated, info = env.step(action)
        cumulative_reward += reward
        steps += 1

    return PortfolioEpisodeSummary(
        steps=steps,
        final_portfolio_value=float(info["portfolio_value"]),
        cumulative_reward=float(cumulative_reward),
        final_cash=float(info["cash"]),
        final_shares_by_symbol={key: int(value) for key, value in info["shares_by_symbol"].items()},
    )


def summarize_episode_series(values: list[float]) -> dict[str, float]:
    """Return simple aggregate statistics for repeated episodes."""

    array = np.array(values, dtype=float)
    return {
        "mean": float(array.mean()),
        "std": float(array.std(ddof=0)),
        "min": float(array.min()),
        "max": float(array.max()),
    }


def compute_buy_and_hold_alignment(
    *,
    initial_cash: float,
    initial_close: float,
    config: EnvironmentConfig,
) -> BuyAndHoldAlignment:
    """Compute expected first-trade accounting values for a buy-and-hold entry."""

    execution_price = initial_close * (1.0 + config.slippage_rate)
    affordable_cash = initial_cash - config.fixed_commission
    expected_shares = int(max(np.floor(affordable_cash / execution_price), 0))
    expected_slippage_paid = expected_shares * initial_close * config.slippage_rate
    expected_remaining_cash = initial_cash - (expected_shares * execution_price) - config.fixed_commission
    expected_remaining_cash = expected_remaining_cash * (1.0 + config.daily_cash_rate)

    return BuyAndHoldAlignment(
        initial_open=0.0,
        initial_close=float(initial_close),
        expected_execution_price=float(execution_price),
        expected_shares=int(expected_shares),
        expected_remaining_cash=float(expected_remaining_cash),
        expected_commission=float(config.fixed_commission),
        expected_slippage_paid=float(expected_slippage_paid),
    )


def history_to_frame(history: list[dict[str, object]]) -> pd.DataFrame:
    """Convert environment history records into a dataframe."""

    frame = pd.DataFrame(history)
    if not frame.empty and "date" in frame.columns:
        frame["date"] = pd.to_datetime(frame["date"])
    return frame


def compute_backtest_metrics(history_frame: pd.DataFrame, initial_portfolio_value: float) -> BacktestMetrics:
    """Compute cumulative return, Sharpe ratio, and max drawdown from backtest history."""

    if history_frame.empty:
        raise ValueError("Backtest history is empty.")

    portfolio_values = history_frame["portfolio_value"].astype(float)
    returns = portfolio_values.pct_change().fillna(0.0)
    cumulative_return = float((portfolio_values.iloc[-1] / initial_portfolio_value) - 1.0)

    return_std = float(returns.std(ddof=0))
    sharpe_ratio = 0.0
    if return_std > 0:
        sharpe_ratio = float((returns.mean() / return_std) * np.sqrt(252.0))

    running_max = portfolio_values.cummax()
    drawdowns = (portfolio_values / running_max) - 1.0
    max_drawdown = float(drawdowns.min())
    executed_trades = 0
    if "execution" in history_frame.columns:
        for record in history_frame["execution"]:
            if record.get("executed") is not None:
                executed_trades += int(bool(record.get("executed")))
                continue
            executed_symbols = record.get("executed_symbols")
            if executed_symbols is not None:
                executed_trades += int(len(executed_symbols))

    average_turnover = 0.0
    if "action" in history_frame.columns:
        action_series = history_frame["action"].astype(float)
        action_changes = action_series.diff().fillna(action_series)
        average_turnover = float(action_changes.abs().mean())
    elif "target_weights" in history_frame.columns:
        turnover_values: list[float] = []
        previous: dict[str, float] | None = None
        for weights in history_frame["target_weights"]:
            current = {key: float(value) for key, value in weights.items()}
            if previous is None:
                turnover_values.append(float(sum(abs(value) for value in current.values())))
            else:
                keys = set(previous).union(current)
                turnover_values.append(float(sum(abs(current.get(key, 0.0) - previous.get(key, 0.0)) for key in keys)))
            previous = current
        average_turnover = float(np.mean(turnover_values)) if turnover_values else 0.0

    trade_rate = float(executed_trades / len(history_frame))

    return BacktestMetrics(
        initial_portfolio_value=float(initial_portfolio_value),
        final_portfolio_value=float(portfolio_values.iloc[-1]),
        cumulative_return=cumulative_return,
        sharpe_ratio=sharpe_ratio,
        max_drawdown=max_drawdown,
        executed_trades=executed_trades,
        trade_rate=trade_rate,
        average_turnover=average_turnover,
    )


def summarize_portfolio_structure(
    history_frame: pd.DataFrame,
    symbols: list[str],
) -> dict[str, object]:
    """Summarize portfolio concentration, review cadence, and per-symbol weight behavior."""

    if history_frame.empty:
        raise ValueError("Backtest history is empty.")

    average_target_weights = {
        symbol: float(history_frame["target_weights"].apply(lambda weights: float(weights.get(symbol, 0.0))).mean())
        for symbol in symbols
    }
    average_position_weights = {
        symbol: float(history_frame["position_weights"].apply(lambda weights: float(weights.get(symbol, 0.0))).mean())
        for symbol in symbols
    }
    core_symbol_counts = {symbol: 0 for symbol in symbols}
    if "core_symbol" in history_frame.columns:
        for symbol in history_frame["core_symbol"]:
            if symbol in core_symbol_counts:
                core_symbol_counts[str(symbol)] += 1

    average_target_concentration = float(history_frame["target_concentration"].astype(float).mean())
    average_position_concentration = float(history_frame["position_concentration"].astype(float).mean())
    review_step_count = int(history_frame["review_step"].sum()) if "review_step" in history_frame.columns else 0
    average_cash_weight = float(history_frame["cash_weight"].astype(float).mean()) if "cash_weight" in history_frame.columns else 0.0

    return {
        "average_target_weights": average_target_weights,
        "average_position_weights": average_position_weights,
        "core_symbol_counts": core_symbol_counts,
        "average_target_concentration": average_target_concentration,
        "average_position_concentration": average_position_concentration,
        "average_cash_weight": average_cash_weight,
        "review_step_count": review_step_count,
    }


def summarize_regimes(
    history_frame: pd.DataFrame,
    feature_frame: pd.DataFrame,
) -> dict[str, dict[str, float | int]]:
    """Summarize policy behavior across simple uptrend/downtrend/transition regimes."""

    merged = _merge_history_with_features(history_frame, feature_frame)
    summaries: dict[str, dict[str, float | int]] = {}

    for regime_name in ("uptrend", "downtrend", "transition"):
        subset = merged[merged["regime"] == regime_name].reset_index(drop=True)
        summaries[regime_name] = _summarize_single_regime(subset).to_dict()

    return summaries


def summarize_trend_alignment(
    history_frame: pd.DataFrame,
    feature_frame: pd.DataFrame,
) -> dict[str, float | int]:
    """Measure whether the strategy carries more exposure in favorable trends."""

    merged = _merge_history_with_features(history_frame, feature_frame)
    uptrend = merged[merged["regime"] == "uptrend"]
    downtrend = merged[merged["regime"] == "downtrend"]
    transition = merged[merged["regime"] == "transition"]

    average_up = float(uptrend["action"].mean()) if not uptrend.empty else 0.0
    average_down = float(downtrend["action"].mean()) if not downtrend.empty else 0.0
    average_transition = float(transition["action"].mean()) if not transition.empty else 0.0
    weight_spread = average_up - average_down

    trend_following_rows = 0
    evaluable_rows = 0
    for _, row in merged.iterrows():
        if row["regime"] == "uptrend":
            evaluable_rows += 1
            trend_following_rows += int(float(row["action"]) >= 0.5)
        elif row["regime"] == "downtrend":
            evaluable_rows += 1
            trend_following_rows += int(float(row["action"]) <= 0.5)

    trend_following_share = float(trend_following_rows / evaluable_rows) if evaluable_rows > 0 else 0.0

    return TrendAlignmentSummary(
        uptrend_periods=int(len(uptrend)),
        downtrend_periods=int(len(downtrend)),
        transition_periods=int(len(transition)),
        average_target_weight_uptrend=average_up,
        average_target_weight_downtrend=average_down,
        average_target_weight_transition=average_transition,
        average_weight_spread=float(weight_spread),
        trend_following_share=trend_following_share,
    ).to_dict()


def _merge_history_with_features(history_frame: pd.DataFrame, feature_frame: pd.DataFrame) -> pd.DataFrame:
    feature_slice = feature_frame[
        [
            "date",
            "sma_30_gap",
            "sma_30_slope",
            "distance_to_20d_high",
            "drawdown_from_30d_peak",
        ]
    ].copy()
    feature_slice["date"] = pd.to_datetime(feature_slice["date"])
    feature_slice["regime"] = feature_slice.apply(_classify_regime, axis=1)

    merged = history_frame.copy()
    merged["date"] = pd.to_datetime(merged["date"])
    merged = merged.merge(feature_slice, on="date", how="left", validate="one_to_one")
    merged["portfolio_return"] = merged["portfolio_value"].astype(float).pct_change().fillna(0.0)
    return merged


def _classify_regime(row: pd.Series) -> str:
    if float(row["sma_30_gap"]) >= 0.0 and float(row["sma_30_slope"]) > 0.0:
        return "uptrend"
    if float(row["sma_30_gap"]) < 0.0 and float(row["sma_30_slope"]) <= 0.0:
        return "downtrend"
    return "transition"


def _summarize_single_regime(frame: pd.DataFrame) -> RegimeMetrics:
    if frame.empty:
        return RegimeMetrics(
            periods=0,
            average_target_weight=0.0,
            average_portfolio_return=0.0,
            executed_trades=0,
            trade_rate=0.0,
        )

    executed_trades = 0
    if "execution" in frame.columns:
        executed_trades = int(sum(bool(record.get("executed")) for record in frame["execution"]))

    return RegimeMetrics(
        periods=int(len(frame)),
        average_target_weight=float(frame["action"].astype(float).mean()),
        average_portfolio_return=float(frame["portfolio_return"].astype(float).mean()),
        executed_trades=executed_trades,
        trade_rate=float(executed_trades / len(frame)),
    )
