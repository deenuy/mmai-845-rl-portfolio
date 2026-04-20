"""Project configuration objects for single-asset and portfolio environments."""

from __future__ import annotations

from dataclasses import dataclass


PHASE_2_REFERENCE_FEATURE_SUFFIXES: tuple[str, ...] = (
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
)

PHASE_3_GROUP_A_FEATURE_SUFFIXES: tuple[str, ...] = (
    *PHASE_2_REFERENCE_FEATURE_SUFFIXES,
    "macd",
    "macd_signal",
    "macd_histogram",
    "breakout_strength_20",
    "breakout_persistence_5",
    "recovery_strength_10",
    "recovery_pressure_5",
)

PHASE_3_GROUP_A_REDUCED_FEATURE_SUFFIXES: tuple[str, ...] = (
    *PHASE_2_REFERENCE_FEATURE_SUFFIXES,
    "macd_histogram",
    "breakout_persistence_5",
    "recovery_strength_10",
    "recovery_pressure_5",
)

PHASE_3_GROUP_B_CORE_FEATURE_SUFFIXES: tuple[str, ...] = (
    *PHASE_2_REFERENCE_FEATURE_SUFFIXES,
    "cs_momentum_rank_20",
    "cs_momentum_spread_20",
    "cs_breakout_rank_20",
    "cs_breakout_spread_20",
    "cs_drawdown_rank_30",
    "cs_drawdown_spread_30",
)

PHASE_3_GROUP_B_MOMENTUM_FEATURE_SUFFIXES: tuple[str, ...] = (
    *PHASE_2_REFERENCE_FEATURE_SUFFIXES,
    "cs_momentum_rank_20",
    "cs_momentum_spread_20",
)

PHASE_3_GROUP_B_BREAKOUT_FEATURE_SUFFIXES: tuple[str, ...] = (
    *PHASE_2_REFERENCE_FEATURE_SUFFIXES,
    "cs_breakout_rank_20",
    "cs_breakout_spread_20",
)

PHASE_3_GROUP_B_DRAWDOWN_FEATURE_SUFFIXES: tuple[str, ...] = (
    *PHASE_2_REFERENCE_FEATURE_SUFFIXES,
    "cs_drawdown_rank_30",
    "cs_drawdown_spread_30",
)

PHASE_3_GROUP_B_MOMENTUM_DRAWDOWN_FEATURE_SUFFIXES: tuple[str, ...] = (
    *PHASE_2_REFERENCE_FEATURE_SUFFIXES,
    "cs_momentum_rank_20",
    "cs_momentum_spread_20",
    "cs_drawdown_rank_30",
    "cs_drawdown_spread_30",
)

PHASE_3_GROUP_B_BREAKOUT_DRAWDOWN_FEATURE_SUFFIXES: tuple[str, ...] = (
    *PHASE_2_REFERENCE_FEATURE_SUFFIXES,
    "cs_breakout_rank_20",
    "cs_breakout_spread_20",
    "cs_drawdown_rank_30",
    "cs_drawdown_spread_30",
)

PHASE_3_GROUP_B_BREAKOUT_DRAWDOWN_MOMENTUM_RANK_FEATURE_SUFFIXES: tuple[str, ...] = (
    *PHASE_2_REFERENCE_FEATURE_SUFFIXES,
    "cs_momentum_rank_20",
    "cs_breakout_rank_20",
    "cs_breakout_spread_20",
    "cs_drawdown_rank_30",
    "cs_drawdown_spread_30",
)

PHASE_3_GROUP_B_BREAKOUT_DRAWDOWN_MOMENTUM_SPREAD_FEATURE_SUFFIXES: tuple[str, ...] = (
    *PHASE_2_REFERENCE_FEATURE_SUFFIXES,
    "cs_momentum_spread_20",
    "cs_breakout_rank_20",
    "cs_breakout_spread_20",
    "cs_drawdown_rank_30",
    "cs_drawdown_spread_30",
)

PHASE_3_GROUP_C_MARKET_CONTEXT_SUFFIXES: tuple[str, ...] = (
    "momentum_20",
    "sma_30_gap",
    "drawdown_from_30d_peak",
    "volatility_20",
    "trend_persistence_10",
)


@dataclass(frozen=True)
class DataConfig:
    """Configuration for raw data download and cleaning."""

    symbol: str = "RY"
    start_date: str = "2010-01-01"
    end_date: str | None = None
    auto_adjust: bool = False


@dataclass(frozen=True)
class EnvironmentConfig:
    """Configuration for the Phase 0 single-stock environment."""

    initial_cash: float = 100_000.0
    fixed_commission: float = 1.99
    slippage_bps: float = 5.0
    annual_cash_yield: float = 0.0
    min_trade_value: float = 100.0
    training_window: int = 252
    random_start: bool = True
    window_sampling_mode: str = "random"
    seed: int | None = 42
    reward_mode: str = "log_return"
    drawdown_penalty_coef: float = 0.0
    turnover_penalty_coef: float = 0.0
    downside_penalty_coef: float = 0.0
    trend_bonus_coef: float = 0.0
    dip_buy_bonus_coef: float = 0.0
    position_sizing_coef: float = 0.0

    @property
    def daily_cash_rate(self) -> float:
        """Approximate daily accrual rate for idle cash."""

        return self.annual_cash_yield / 252.0

    @property
    def slippage_rate(self) -> float:
        """Return slippage in decimal form."""

        return self.slippage_bps / 10_000.0


@dataclass(frozen=True)
class PortfolioEnvironmentConfig:
    """Configuration for the Phase 2 multi-asset portfolio environment."""

    symbols: tuple[str, ...] = ("RY", "MSFT", "RKLB", "XOM", "PG")
    initial_cash: float = 100_000.0
    fixed_commission: float = 1.99
    slippage_bps: float = 5.0
    annual_cash_yield: float = 0.0
    min_trade_value: float = 100.0
    training_window: int = 252
    random_start: bool = True
    window_sampling_mode: str = "random"
    seed: int | None = 42
    reward_mode: str = "log_return"
    turnover_penalty_coef: float = 0.0
    focus_symbol: str | None = None
    focus_target_weight: float = 0.0
    focus_weight_penalty_coef: float = 0.0
    focus_start_date: str | None = None
    focus_end_date: str | None = None
    strategic_review_interval_days: int = 63
    residual_freeze_enabled: bool = False
    extreme_residual_drift_threshold: float = 0.20
    market_feature_suffixes: tuple[str, ...] = PHASE_2_REFERENCE_FEATURE_SUFFIXES
    market_context_suffixes: tuple[str, ...] = ()

    @property
    def daily_cash_rate(self) -> float:
        """Approximate daily accrual rate for idle cash."""

        return self.annual_cash_yield / 252.0

    @property
    def slippage_rate(self) -> float:
        """Return slippage in decimal form."""

        return self.slippage_bps / 10_000.0