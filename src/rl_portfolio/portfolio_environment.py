"""Multi-asset portfolio environment for the Phase 2 roadmap."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd

from .config import PortfolioEnvironmentConfig
from .execution import PortfolioExecutionResult, accrue_cash, execute_target_weights


class PortfolioTradingEnv(gym.Env):
    """A long-only whole-share portfolio environment with target-weight actions."""

    metadata = {"render_modes": ["human"], "render_fps": 1}

    def __init__(self, frame: pd.DataFrame, config: PortfolioEnvironmentConfig | None = None) -> None:
        super().__init__()
        self.config = config or PortfolioEnvironmentConfig()
        self.frame = frame.reset_index(drop=True).copy()
        self.symbols = list(self.config.symbols)
        self._validate_frame()
        self.rng = np.random.default_rng(self.config.seed)

        self.observation_columns = self._build_observation_columns()
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(len(self.observation_columns),),
            dtype=np.float32,
        )
        self.action_space = spaces.Box(
            low=np.full((len(self.symbols) + 1,), -10.0, dtype=np.float32),
            high=np.full((len(self.symbols) + 1,), 10.0, dtype=np.float32),
            shape=(len(self.symbols) + 1,),
            dtype=np.float32,
        )

        self.start_index = 0
        self.end_index = 0
        self.next_window_start = 0
        self.current_index = 0
        self.cash = self.config.initial_cash
        self.shares_by_symbol = {symbol: 0 for symbol in self.symbols}
        self.previous_portfolio_value = self.config.initial_cash
        self.last_target_weights = {symbol: 0.0 for symbol in self.symbols}
        self.last_cash_target_weight = 1.0
        self.last_execution: PortfolioExecutionResult | None = None
        self.history: list[dict[str, Any]] = []
        self.last_core_symbol: str | None = None

    def reset(self, *, seed: int | None = None, start_index: int | None = None) -> tuple[np.ndarray, dict[str, Any]]:
        """Reset the portfolio environment."""

        super().reset(seed=seed)
        if seed is not None:
            self.rng = np.random.default_rng(seed)

        self.start_index, self.end_index = self._resolve_window(start_index)
        self.current_index = self.start_index
        if self.config.window_sampling_mode == "rolling":
            max_start = len(self.frame) - self.config.training_window
            self.next_window_start = 0 if self.start_index >= max_start else self.start_index + 1

        self.cash = self.config.initial_cash
        self.shares_by_symbol = {symbol: 0 for symbol in self.symbols}
        self.previous_portfolio_value = self.config.initial_cash
        self.last_target_weights = {symbol: 0.0 for symbol in self.symbols}
        self.last_cash_target_weight = 1.0
        self.last_execution = None
        self.history = []
        self.last_core_symbol = None

        return self._get_observation(), self.get_diagnostics()

    def step(self, action: np.ndarray) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        """Execute one portfolio rebalance step."""

        target_weights, cash_target_weight = self._normalize_action(action)
        row = self.frame.iloc[self.current_index]
        close_prices = {symbol: float(row[f"{_symbol_prefix(symbol)}__close"]) for symbol in self.symbols}
        previous_target_weights = self.last_target_weights.copy()
        pre_trade_position_weights = self._position_weights(close_prices)
        review_step = self._is_review_step(self.current_index)
        if self.config.residual_freeze_enabled:
            target_weights = self._apply_residual_freeze(
                target_weights=target_weights,
                current_position_weights=pre_trade_position_weights,
                cash_target_weight=cash_target_weight,
                review_step=review_step,
            )
        core_symbol = max(target_weights, key=target_weights.get) if target_weights else None

        self.last_execution = execute_target_weights(
            cash=self.cash,
            shares_by_symbol=self.shares_by_symbol,
            close_prices=close_prices,
            target_weights=target_weights,
            config=self.config,
        )
        self.cash = accrue_cash(self.last_execution.cash_after, self.config.daily_cash_rate)
        self.shares_by_symbol = self.last_execution.shares_after.copy()

        portfolio_value = self.get_portfolio_value(close_prices=close_prices)
        realized_position_weights = self._position_weights(close_prices)
        reward = self._compute_reward(
            current_date=pd.Timestamp(row["date"]),
            portfolio_value=portfolio_value,
            target_weights=target_weights,
            previous_target_weights=previous_target_weights,
            realized_position_weights=realized_position_weights,
        )
        self.previous_portfolio_value = portfolio_value
        self.last_target_weights = target_weights.copy()
        self.last_cash_target_weight = cash_target_weight
        self.last_core_symbol = core_symbol

        self.history.append(
            {
                "date": row["date"],
                "portfolio_value": portfolio_value,
                "cash": self.cash,
                "cash_weight": self._cash_ratio(close_prices),
                "target_weights": target_weights,
                "position_weights": realized_position_weights,
                "review_step": review_step,
                "core_symbol": core_symbol,
                "target_concentration": self._max_weight(target_weights),
                "position_concentration": self._max_weight(realized_position_weights),
                "reward": reward,
                "execution": asdict(self.last_execution),
            }
        )

        terminated = self.current_index >= self.end_index - 1
        truncated = False
        if not terminated:
            self.current_index += 1

        return self._get_observation(), reward, terminated, truncated, self.get_diagnostics()

    def get_portfolio_value(self, close_prices: dict[str, float] | None = None) -> float:
        """Mark the portfolio to market."""

        prices = close_prices or self._current_close_prices()
        equity_value = sum(self.shares_by_symbol[symbol] * prices[symbol] for symbol in self.symbols)
        return float(self.cash + equity_value)

    def get_diagnostics(self) -> dict[str, Any]:
        """Return current environment state."""

        close_prices = self._current_close_prices()
        return {
            "current_index": self.current_index,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "cash": self.cash,
            "portfolio_value": self.get_portfolio_value(close_prices),
            "shares_by_symbol": self.shares_by_symbol.copy(),
            "position_weights": self._position_weights(close_prices),
            "last_target_weights": self.last_target_weights.copy(),
            "last_cash_target_weight": float(self.last_cash_target_weight),
            "last_core_symbol": self.last_core_symbol,
            "review_step": self._is_review_step(self.current_index),
            "last_execution": asdict(self.last_execution) if self.last_execution is not None else None,
        }

    def _get_observation(self) -> np.ndarray:
        row = self.frame.iloc[self.current_index]
        close_prices = self._current_close_prices()
        position_weights = self._position_weights(close_prices)
        cash_ratio = self._cash_ratio(close_prices)

        values: list[float] = [cash_ratio]
        for suffix in self.config.market_context_suffixes:
            values.append(float(row[f"market__{suffix}"]))
        for symbol in self.symbols:
            values.append(position_weights[symbol])
            values.append(float(self.last_target_weights[symbol]))
            prefix = _symbol_prefix(symbol)
            for suffix in self.config.market_feature_suffixes:
                values.append(float(row[f"{prefix}__{suffix}"]))

        return np.array(values, dtype=np.float32)

    def _build_observation_columns(self) -> list[str]:
        columns = ["cash_ratio"]
        columns.extend(f"market__{suffix}" for suffix in self.config.market_context_suffixes)
        for symbol in self.symbols:
            prefix = _symbol_prefix(symbol)
            columns.append(f"{prefix}__position_weight")
            columns.append(f"{prefix}__previous_target_weight")
            columns.extend(f"{prefix}__{suffix}" for suffix in self.config.market_feature_suffixes)
        return columns

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

        return resolved_start, resolved_start + self.config.training_window

    def _validate_frame(self) -> None:
        required = {"date"}
        required.update(f"market__{suffix}" for suffix in self.config.market_context_suffixes)
        for symbol in self.symbols:
            prefix = _symbol_prefix(symbol)
            required.update(
                {
                    f"{prefix}__open",
                    f"{prefix}__high",
                    f"{prefix}__low",
                    f"{prefix}__close",
                    f"{prefix}__volume",
                }
            )
            required.update(f"{prefix}__{suffix}" for suffix in self.config.market_feature_suffixes)

        missing = sorted(required.difference(self.frame.columns))
        if missing:
            raise ValueError(f"Portfolio environment frame is missing required columns: {missing}")

    def _normalize_action(self, action: np.ndarray) -> tuple[dict[str, float], float]:
        raw = np.asarray(action, dtype=np.float32).reshape(-1)
        if raw.shape[0] != len(self.symbols) + 1:
            raise ValueError(
                f"Portfolio action must have length {len(self.symbols) + 1}, received {raw.shape[0]}."
            )

        shifted = raw - np.max(raw)
        weights = np.exp(shifted)
        weights = weights / weights.sum()
        asset_weights = {symbol: float(weights[index]) for index, symbol in enumerate(self.symbols)}
        cash_weight = float(weights[-1])
        return asset_weights, cash_weight

    def _apply_residual_freeze(
        self,
        *,
        target_weights: dict[str, float],
        current_position_weights: dict[str, float],
        cash_target_weight: float,
        review_step: bool,
    ) -> dict[str, float]:
        if review_step:
            return target_weights

        if not target_weights:
            return target_weights

        core_symbol = max(target_weights, key=target_weights.get)
        investable_total = max(1.0 - cash_target_weight, 0.0)
        locked_weights: dict[str, float] = {}
        free_symbols: list[str] = []

        for symbol in self.symbols:
            proposed = float(target_weights.get(symbol, 0.0))
            current = float(current_position_weights.get(symbol, 0.0))
            if symbol == core_symbol:
                free_symbols.append(symbol)
                continue
            if abs(proposed - current) < self.config.extreme_residual_drift_threshold:
                locked_weights[symbol] = current
            else:
                free_symbols.append(symbol)

        locked_total = sum(locked_weights.values())
        remaining_total = max(investable_total - locked_total, 0.0)
        if not free_symbols:
            if locked_total <= 0.0:
                return {symbol: 0.0 for symbol in self.symbols}
            scale = investable_total / locked_total
            return {symbol: float(locked_weights.get(symbol, 0.0) * scale) for symbol in self.symbols}

        free_total = sum(max(float(target_weights.get(symbol, 0.0)), 0.0) for symbol in free_symbols)
        if free_total <= 0.0:
            fallback = remaining_total / len(free_symbols)
            free_weights = {symbol: fallback for symbol in free_symbols}
        else:
            free_weights = {
                symbol: remaining_total * (max(float(target_weights.get(symbol, 0.0)), 0.0) / free_total)
                for symbol in free_symbols
            }

        adjusted = {**locked_weights, **free_weights}
        return {symbol: float(adjusted.get(symbol, 0.0)) for symbol in self.symbols}

    def _is_review_step(self, index: int) -> bool:
        interval = max(int(self.config.strategic_review_interval_days), 1)
        return ((index - self.start_index) % interval) == 0

    def _compute_reward(
        self,
        *,
        current_date: pd.Timestamp,
        portfolio_value: float,
        target_weights: dict[str, float],
        previous_target_weights: dict[str, float],
        realized_position_weights: dict[str, float],
    ) -> float:
        log_return = float(np.log(portfolio_value / self.previous_portfolio_value))
        if self.config.reward_mode == "log_return":
            return log_return

        if self.config.reward_mode == "log_return_with_turnover_penalty":
            turnover = sum(abs(target_weights[symbol] - previous_target_weights[symbol]) for symbol in self.symbols)
            return log_return - (self.config.turnover_penalty_coef * turnover)

        if self.config.reward_mode == "log_return_with_turnover_and_focus_weight":
            turnover = sum(abs(target_weights[symbol] - previous_target_weights[symbol]) for symbol in self.symbols)
            reward = log_return - (self.config.turnover_penalty_coef * turnover)
            if self._is_focus_window_active(current_date) and self.config.focus_symbol in realized_position_weights:
                focus_gap = abs(
                    realized_position_weights[self.config.focus_symbol] - self.config.focus_target_weight
                )
                reward -= self.config.focus_weight_penalty_coef * focus_gap
            return reward

        raise ValueError(f"Unsupported portfolio reward mode: {self.config.reward_mode}")

    def _is_focus_window_active(self, current_date: pd.Timestamp) -> bool:
        if self.config.focus_symbol is None:
            return False

        start = pd.Timestamp(self.config.focus_start_date) if self.config.focus_start_date is not None else None
        end = pd.Timestamp(self.config.focus_end_date) if self.config.focus_end_date is not None else None
        if start is not None and current_date < start:
            return False
        if end is not None and current_date > end:
            return False
        return True

    def _current_close_prices(self) -> dict[str, float]:
        row = self.frame.iloc[self.current_index]
        return {symbol: float(row[f"{_symbol_prefix(symbol)}__close"]) for symbol in self.symbols}

    def _position_weights(self, close_prices: dict[str, float]) -> dict[str, float]:
        portfolio_value = self.get_portfolio_value(close_prices)
        if portfolio_value <= 0:
            return {symbol: 0.0 for symbol in self.symbols}
        return {
            symbol: float((self.shares_by_symbol[symbol] * close_prices[symbol]) / portfolio_value)
            for symbol in self.symbols
        }

    def _cash_ratio(self, close_prices: dict[str, float]) -> float:
        portfolio_value = self.get_portfolio_value(close_prices)
        if portfolio_value <= 0:
            return 0.0
        return float(self.cash / portfolio_value)

    @staticmethod
    def _max_weight(weights: dict[str, float]) -> float:
        if not weights:
            return 0.0
        return float(max(weights.values()))


def _symbol_prefix(symbol: str) -> str:
    return symbol.strip().lower().replace("-", "_").replace(".", "_")
