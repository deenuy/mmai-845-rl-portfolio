"""Single-stock trading environment for the Phase 0 roadmap."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd

from .config import EnvironmentConfig
from .execution import ExecutionResult, accrue_cash, execute_target_position
from .features import build_observation_row


class TradingEnv(gym.Env):
    """A simple Gym-like environment for single-stock target-position control."""

    metadata = {"render_modes": ["human"], "render_fps": 1}

    def __init__(self, frame: pd.DataFrame, config: EnvironmentConfig | None = None) -> None:
        super().__init__()
        self.config = config or EnvironmentConfig()
        self.frame = frame.reset_index(drop=True).copy()
        self._validate_frame()
        self.rng = np.random.default_rng(self.config.seed)
        self.observation_columns = [
            "cash_ratio",
            "position_weight",
            "shares_held_ratio",
            "previous_target_weight",
            "open_gap",
            "previous_close_return",
            "momentum_5",
            "momentum_20",
            "sma_5_gap",
            "sma_20_gap",
            "sma_30_gap",
            "sma_30_slope",
            "distance_to_20d_high",
            "drawdown_from_30d_peak",
            "volatility_20",
            "trend_persistence_10",
            "downside_pressure_5",
            "macd",
            "macd_signal",
            "macd_histogram",
            "breakout_strength_20",
            "breakout_persistence_5",
            "recovery_strength_10",
            "recovery_pressure_5",
        ]
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(len(self.observation_columns),),
            dtype=np.float32,
        )
        self.action_space = spaces.Box(
            low=np.array([0.0], dtype=np.float32),
            high=np.array([1.0], dtype=np.float32),
            dtype=np.float32,
        )

        self.start_index = 0
        self.end_index = 0
        self.next_window_start = 0
        self.current_index = 0
        self.cash = self.config.initial_cash
        self.shares = 0
        self.previous_portfolio_value = self.config.initial_cash
        self.peak_portfolio_value = self.config.initial_cash
        self.last_target_weight = 0.0
        self.last_execution: ExecutionResult | None = None
        self.history: list[dict[str, Any]] = []

    def reset(self, *, seed: int | None = None, start_index: int | None = None) -> tuple[np.ndarray, dict[str, Any]]:
        """Reset the environment state and return the initial observation."""

        super().reset(seed=seed)
        if seed is not None:
            self.rng = np.random.default_rng(seed)

        self.start_index, self.end_index = self._resolve_window(start_index)
        self.current_index = self.start_index
        if self.config.window_sampling_mode == "rolling":
            max_start = len(self.frame) - self.config.training_window
            self.next_window_start = 0 if self.start_index >= max_start else self.start_index + 1
        self.cash = self.config.initial_cash
        self.shares = 0
        self.previous_portfolio_value = self.config.initial_cash
        self.peak_portfolio_value = self.config.initial_cash
        self.last_target_weight = 0.0
        self.last_execution = None
        self.history = []

        observation = self._get_observation()
        info = self.get_diagnostics()
        return observation, info

    def step(self, action: float | np.ndarray) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        """Execute one environment step using a target stock weight."""

        if isinstance(action, np.ndarray):
            target_weight = float(np.clip(action.reshape(-1)[0], 0.0, 1.0))
        else:
            target_weight = float(np.clip(action, 0.0, 1.0))
        row = self.frame.iloc[self.current_index]
        previous_target_weight = self.last_target_weight

        self.last_execution = execute_target_position(
            cash=self.cash,
            shares=self.shares,
            close_price=float(row["close"]),
            target_weight=target_weight,
            config=self.config,
        )

        self.cash = accrue_cash(self.last_execution.cash_after, self.config.daily_cash_rate)
        self.shares = self.last_execution.shares_after

        portfolio_value = self.get_portfolio_value(price=float(row["close"]))
        reward = self._compute_reward(
            portfolio_value=portfolio_value,
            target_weight=target_weight,
            previous_target_weight=previous_target_weight,
            row=row,
        )
        self.previous_portfolio_value = portfolio_value
        self.peak_portfolio_value = max(self.peak_portfolio_value, portfolio_value)
        self.last_target_weight = target_weight

        self.history.append(
            {
                "date": row["date"],
                "action": target_weight,
                "cash": self.cash,
                "shares": self.shares,
                "portfolio_value": portfolio_value,
                "position_weight": self._position_weight(float(row["close"])),
                "desired_position_weight": self._desired_trend_weight(row),
                "reward": reward,
                "execution": asdict(self.last_execution),
            }
        )

        terminated = self.current_index >= self.end_index - 1
        truncated = False

        if not terminated:
            self.current_index += 1

        observation = self._get_observation()
        info = self.get_diagnostics()
        return observation, reward, terminated, truncated, info

    def render(self) -> dict[str, Any]:
        """Return the current diagnostics payload."""

        return self.get_diagnostics()

    def get_portfolio_value(self, price: float | None = None) -> float:
        """Mark the portfolio to market using the provided price or current close."""

        mark_price = price
        if mark_price is None:
            mark_price = float(self.frame.iloc[self.current_index]["close"])
        return float(self.cash + self.shares * mark_price)

    def get_diagnostics(self) -> dict[str, Any]:
        """Return the current environment state for logging and debugging."""

        return {
            "current_index": self.current_index,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "cash": self.cash,
            "shares": self.shares,
            "portfolio_value": self.get_portfolio_value(),
            "last_target_weight": self.last_target_weight,
            "last_execution": asdict(self.last_execution) if self.last_execution is not None else None,
        }

    def _get_observation(self) -> np.ndarray:
        observation = build_observation_row(
            self.frame,
            index=self.current_index,
            cash=self.cash,
            shares=self.shares,
            previous_target_weight=self.last_target_weight,
            initial_cash=self.config.initial_cash,
        )
        return np.array(list(observation.values()), dtype=np.float32)

    def _resolve_window(self, start_index: int | None) -> tuple[int, int]:
        if len(self.frame) < self.config.training_window:
            raise ValueError("Data frame is shorter than the configured training window.")

        max_start = len(self.frame) - self.config.training_window
        if start_index is None:
            if self.config.window_sampling_mode == "rolling" and max_start > 0:
                resolved_start = min(self.next_window_start, max_start)
            elif self.config.random_start and max_start > 0:
                resolved_start = int(self.rng.integers(0, max_start + 1))
            else:
                resolved_start = 0
        else:
            resolved_start = start_index

        resolved_end = resolved_start + self.config.training_window
        return resolved_start, resolved_end

    def _validate_frame(self) -> None:
        required = {
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "open_gap",
            "previous_close_return",
            "momentum_5",
            "momentum_20",
            "sma_5_gap",
            "sma_20_gap",
            "sma_30_gap",
            "sma_30_slope",
            "distance_to_20d_high",
            "drawdown_from_30d_peak",
            "volatility_20",
            "trend_persistence_10",
            "downside_pressure_5",
            "macd",
            "macd_signal",
            "macd_histogram",
            "breakout_strength_20",
            "breakout_persistence_5",
            "recovery_strength_10",
            "recovery_pressure_5",
        }
        missing = sorted(required.difference(self.frame.columns))
        if missing:
            raise ValueError(f"Environment frame is missing required columns: {missing}")

    def _compute_reward(
        self,
        *,
        portfolio_value: float,
        target_weight: float,
        previous_target_weight: float,
        row: pd.Series,
    ) -> float:
        """Compute the per-step reward based on the configured reward mode."""

        log_return = float(np.log(portfolio_value / self.previous_portfolio_value))
        if self.config.reward_mode == "log_return":
            return log_return

        if self.config.reward_mode == "log_return_drawdown_penalty":
            peak_value = max(self.peak_portfolio_value, self.previous_portfolio_value)
            drawdown = 0.0
            if peak_value > 0:
                drawdown = max(0.0, 1.0 - (portfolio_value / peak_value))
            penalty = self.config.drawdown_penalty_coef * drawdown
            return log_return - penalty

        if self.config.reward_mode == "log_return_risk_control":
            turnover = abs(target_weight - previous_target_weight)
            downside_loss = max(-log_return, 0.0)
            turnover_penalty = self.config.turnover_penalty_coef * turnover
            downside_penalty = self.config.downside_penalty_coef * downside_loss
            return log_return - turnover_penalty - downside_penalty

        if self.config.reward_mode == "trend_following_risk_control":
            turnover = abs(target_weight - previous_target_weight)
            downside_loss = max(-log_return, 0.0)
            turnover_penalty = self.config.turnover_penalty_coef * turnover
            downside_penalty = self.config.downside_penalty_coef * downside_loss
            trend_signal_raw = float(row["momentum_20"] + row["sma_20_gap"])
            trend_signal = float(np.clip(trend_signal_raw / 0.05, -1.0, 1.0))
            allocation_bias = (target_weight - 0.5) * 2.0
            trend_bonus = self.config.trend_bonus_coef * trend_signal * allocation_bias
            return log_return - turnover_penalty - downside_penalty + trend_bonus

        if self.config.reward_mode == "trend_position_sizing_control":
            turnover = abs(target_weight - previous_target_weight)
            downside_loss = max(-log_return, 0.0)
            turnover_penalty = self.config.turnover_penalty_coef * turnover
            downside_penalty = self.config.downside_penalty_coef * downside_loss

            desired_weight = self._desired_trend_weight(row)
            sizing_penalty = self.config.position_sizing_coef * abs(target_weight - desired_weight)
            trend_signal_raw = float(row["momentum_20"] + row["sma_20_gap"] + row["sma_30_gap"])
            trend_signal = float(np.clip(trend_signal_raw / 0.08, -1.0, 1.0))
            allocation_bias = (target_weight - 0.5) * 2.0
            trend_bonus = self.config.trend_bonus_coef * trend_signal * allocation_bias
            return log_return - turnover_penalty - downside_penalty - sizing_penalty + trend_bonus

        if self.config.reward_mode == "trend_dip_buy_risk_control":
            turnover = abs(target_weight - previous_target_weight)
            downside_loss = max(-log_return, 0.0)
            turnover_penalty = self.config.turnover_penalty_coef * turnover
            downside_penalty = self.config.downside_penalty_coef * downside_loss

            trend_up = float(row["momentum_20"]) > 0.0 and float(row["sma_20_gap"]) > 0.0
            short_term_dip = float(row["open_gap"]) < 0.0 or float(row["previous_close_return"]) < 0.0
            added_risk = max(target_weight - previous_target_weight, 0.0)
            dip_buy_bonus = 0.0
            if trend_up and short_term_dip:
                dip_buy_bonus = self.config.dip_buy_bonus_coef * added_risk

            return log_return - turnover_penalty - downside_penalty + dip_buy_bonus

        raise ValueError(f"Unsupported reward mode: {self.config.reward_mode}")

    def _position_weight(self, price: float) -> float:
        portfolio_value = self.get_portfolio_value(price=price)
        if portfolio_value <= 0:
            return 0.0
        return float((self.shares * price) / portfolio_value)

    def _desired_trend_weight(self, row: pd.Series) -> float:
        momentum_20 = float(row["momentum_20"])
        sma_20_gap = float(row["sma_20_gap"])
        sma_30_gap = float(row["sma_30_gap"])
        sma_30_slope = float(row["sma_30_slope"])
        distance_to_20d_high = float(row["distance_to_20d_high"])
        drawdown_from_30d_peak = float(row["drawdown_from_30d_peak"])
        open_gap = float(row["open_gap"])
        previous_close_return = float(row["previous_close_return"])
        trend_persistence_10 = float(row["trend_persistence_10"])
        downside_pressure_5 = float(row["downside_pressure_5"])

        strong_uptrend = sma_30_gap > 0.02 and sma_30_slope > 0.002 and momentum_20 > 0.03
        uptrend = sma_30_gap > 0.0 and sma_30_slope > 0.0
        positive_transition = not uptrend and (
            (sma_30_slope > 0.0 and momentum_20 > -0.01) or sma_20_gap > 0.0
        )
        mild_downtrend = sma_30_gap < 0.0 and sma_30_slope <= 0.0 and drawdown_from_30d_peak > -0.10

        target_weight = 0.0

        if strong_uptrend:
            if distance_to_20d_high > -0.02:
                target_weight = 1.00
            elif open_gap < 0.0 or previous_close_return < 0.0:
                target_weight = 0.90
            else:
                target_weight = 0.96
        elif uptrend:
            if distance_to_20d_high > -0.03:
                target_weight = 0.92
            elif drawdown_from_30d_peak > -0.06 and (open_gap < 0.0 or previous_close_return < 0.0):
                target_weight = 0.82
            else:
                target_weight = 0.74
        elif positive_transition:
            if (
                sma_30_slope > 0.003
                and momentum_20 > 0.02
                and distance_to_20d_high > -0.025
                and drawdown_from_30d_peak > -0.05
                and trend_persistence_10 > 0.60
                and downside_pressure_5 < 0.025
            ):
                target_weight = 0.78
            elif (
                sma_30_slope > 0.0015
                and momentum_20 > 0.005
                and distance_to_20d_high > -0.04
                and trend_persistence_10 > 0.50
                and downside_pressure_5 < 0.035
            ):
                target_weight = 0.48
            else:
                target_weight = 0.20
        elif mild_downtrend:
            if (
                drawdown_from_30d_peak > -0.05
                and momentum_20 > -0.03
                and trend_persistence_10 > 0.45
                and downside_pressure_5 < 0.03
            ):
                target_weight = 0.12
            else:
                target_weight = 0.04
        else:
            target_weight = 0.0

        fine_adjustment = 0.0
        fine_adjustment += np.clip(momentum_20 / 0.15, -0.08, 0.08)
        fine_adjustment += np.clip(sma_30_slope / 0.03, -0.05, 0.05)
        fine_adjustment += np.clip(distance_to_20d_high / 0.10, -0.05, 0.03)
        fine_adjustment -= np.clip(abs(drawdown_from_30d_peak) / 0.16, 0.0, 0.10)

        return float(np.clip(target_weight + fine_adjustment, 0.0, 1.0))
