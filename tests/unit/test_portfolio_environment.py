import numpy as np
import pandas as pd

from rl_portfolio.config import PHASE_2_REFERENCE_FEATURE_SUFFIXES, PortfolioEnvironmentConfig
from rl_portfolio.features import build_phase_2_feature_panel
from rl_portfolio.portfolio_environment import PortfolioTradingEnv


def _sample_symbol_frame(offset: float) -> pd.DataFrame:
    base = np.linspace(100.0 + offset, 180.0 + offset, 80)
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=80, freq="B"),
            "open": base + 0.2,
            "high": base + 1.0,
            "low": base - 1.0,
            "close": base + 0.5,
            "volume": np.arange(80) + 1000,
        }
    )


def _portfolio_frame() -> pd.DataFrame:
    return build_phase_2_feature_panel(
        {
            "RY": _sample_symbol_frame(0.0),
            "MSFT": _sample_symbol_frame(20.0),
            "PG": _sample_symbol_frame(-10.0),
        }
    ).dropna().reset_index(drop=True)


def test_portfolio_environment_reset_matches_expected_observation_shape():
    frame = _portfolio_frame()
    config = PortfolioEnvironmentConfig(symbols=("RY", "MSFT", "PG"), training_window=30, random_start=False)
    env = PortfolioTradingEnv(frame, config)

    observation, info = env.reset()

    assert observation.shape == env.observation_space.shape
    assert info["portfolio_value"] == config.initial_cash
    assert set(info["shares_by_symbol"].keys()) == {"RY", "MSFT", "PG"}


def test_portfolio_environment_step_keeps_cash_non_negative():
    frame = _portfolio_frame()
    config = PortfolioEnvironmentConfig(symbols=("RY", "MSFT", "PG"), training_window=30, random_start=False)
    env = PortfolioTradingEnv(frame, config)
    env.reset()

    action = np.array([4.0, 2.0, 1.0, -2.0], dtype=np.float32)
    _, reward, terminated, truncated, info = env.step(action)

    assert np.isfinite(reward)
    assert info["cash"] >= 0.0
    assert not truncated
    assert set(info["position_weights"].keys()) == {"RY", "MSFT", "PG"}
    assert isinstance(terminated, bool)


def test_portfolio_environment_supports_turnover_penalty_reward():
    frame = _portfolio_frame()
    config = PortfolioEnvironmentConfig(
        symbols=("RY", "MSFT", "PG"),
        training_window=30,
        random_start=False,
        reward_mode="log_return_with_turnover_penalty",
        turnover_penalty_coef=0.1,
    )
    env = PortfolioTradingEnv(frame, config)
    env.reset()

    _, reward, _, _, _ = env.step(np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32))

    assert np.isfinite(reward)


def test_portfolio_environment_supports_focus_weight_reward():
    frame = _portfolio_frame()
    config = PortfolioEnvironmentConfig(
        symbols=("RY", "MSFT", "PG"),
        training_window=30,
        random_start=False,
        reward_mode="log_return_with_turnover_and_focus_weight",
        turnover_penalty_coef=0.1,
        focus_symbol="MSFT",
        focus_target_weight=0.6,
        focus_weight_penalty_coef=0.2,
    )
    env = PortfolioTradingEnv(frame, config)
    env.reset()

    _, reward, _, _, info = env.step(np.array([1.0, 3.0, 1.0, -1.0], dtype=np.float32))

    assert np.isfinite(reward)
    assert "MSFT" in info["position_weights"]


def test_portfolio_environment_freezes_residual_sleeves_outside_review_steps():
    frame = _portfolio_frame()
    config = PortfolioEnvironmentConfig(
        symbols=("RY", "MSFT", "PG"),
        training_window=30,
        random_start=False,
        residual_freeze_enabled=True,
        strategic_review_interval_days=10,
        extreme_residual_drift_threshold=0.20,
    )
    env = PortfolioTradingEnv(frame, config)
    env.reset()
    env.current_index = env.start_index + 1

    adjusted = env._apply_residual_freeze(
        target_weights={"RY": 0.10, "MSFT": 0.60, "PG": 0.10},
        current_position_weights={"RY": 0.25, "MSFT": 0.25, "PG": 0.20},
        cash_target_weight=0.20,
        review_step=False,
    )

    assert adjusted["RY"] == 0.25
    assert adjusted["PG"] == 0.20
    assert abs(adjusted["MSFT"] - 0.35) < 1e-9


def test_portfolio_environment_supports_custom_market_feature_subset():
    frame = _portfolio_frame()
    config = PortfolioEnvironmentConfig(
        symbols=("RY", "MSFT", "PG"),
        training_window=30,
        random_start=False,
        market_feature_suffixes=PHASE_2_REFERENCE_FEATURE_SUFFIXES,
    )
    env = PortfolioTradingEnv(frame, config)

    observation, _ = env.reset()

    expected_length = 1 + (len(config.symbols) * (2 + len(PHASE_2_REFERENCE_FEATURE_SUFFIXES)))
    assert observation.shape == (expected_length,)


def test_portfolio_environment_supports_market_context_features():
    frame = _portfolio_frame().copy()
    for column in (
        "market__momentum_20",
        "market__sma_30_gap",
        "market__drawdown_from_30d_peak",
    ):
        frame[column] = 0.1

    config = PortfolioEnvironmentConfig(
        symbols=("RY", "MSFT", "PG"),
        training_window=30,
        random_start=False,
        market_feature_suffixes=PHASE_2_REFERENCE_FEATURE_SUFFIXES,
        market_context_suffixes=("momentum_20", "sma_30_gap", "drawdown_from_30d_peak"),
    )
    env = PortfolioTradingEnv(frame, config)

    observation, _ = env.reset()

    expected_length = 1 + len(config.market_context_suffixes) + (len(config.symbols) * (2 + len(PHASE_2_REFERENCE_FEATURE_SUFFIXES)))
    assert observation.shape == (expected_length,)
