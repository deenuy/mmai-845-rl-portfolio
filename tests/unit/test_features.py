import pandas as pd

from rl_portfolio.features import build_observation_row, build_phase_0_features, build_phase_2_feature_panel


def _sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=60, freq="B"),
            "open": [100.0 + i for i in range(60)],
            "high": [101.0 + i for i in range(60)],
            "low": [99.0 + i for i in range(60)],
            "close": [100.5 + i for i in range(60)],
            "volume": [1000 + i for i in range(60)],
        }
    )


def test_feature_builder_uses_previous_close_information_only():
    frame = build_phase_0_features(_sample_frame())
    row = frame.iloc[20]
    previous_close = frame.iloc[19]["close"]
    prior_close = frame.iloc[18]["close"]
    previous_close_5 = frame.iloc[15]["close"]
    previous_close_20 = frame.iloc[0]["close"]

    assert round(row["open_gap"], 6) == round((row["open"] / previous_close) - 1.0, 6)
    assert round(row["previous_close_return"], 6) == round((previous_close / prior_close) - 1.0, 6)
    assert round(row["momentum_5"], 6) == round((previous_close / previous_close_5) - 1.0, 6)
    assert round(row["momentum_20"], 6) == round((previous_close / previous_close_20) - 1.0, 6)


def test_observation_row_contains_restricted_fields():
    frame = build_phase_0_features(_sample_frame()).dropna().reset_index(drop=True)
    observation = build_observation_row(
        frame,
        index=0,
        cash=100_000.0,
        shares=0,
        previous_target_weight=0.25,
        initial_cash=100_000.0,
    )

    assert set(observation.keys()) == {
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
    }


def test_feature_builder_adds_regime_features_from_prior_data_only():
    frame = build_phase_0_features(_sample_frame())
    row = frame.iloc[40]
    previous_close = frame.iloc[39]["close"]
    rolling_mean_30 = frame.iloc[10:40]["close"].mean()
    rolling_peak_20 = frame.iloc[20:40]["close"].max()
    rolling_peak_30 = frame.iloc[10:40]["close"].max()
    prior_rolling_mean_30 = frame.iloc[5:35]["close"].mean()

    assert round(row["sma_30_gap"], 6) == round((previous_close / rolling_mean_30) - 1.0, 6)
    assert round(row["distance_to_20d_high"], 6) == round((previous_close / rolling_peak_20) - 1.0, 6)
    assert round(row["drawdown_from_30d_peak"], 6) == round((previous_close / rolling_peak_30) - 1.0, 6)
    assert round(row["sma_30_slope"], 6) == round((rolling_mean_30 / prior_rolling_mean_30) - 1.0, 6)


def test_feature_builder_adds_trend_persistence_and_downside_pressure():
    frame = build_phase_0_features(_sample_frame())
    row = frame.iloc[40]
    prior_returns = frame["close"].pct_change().shift(1)
    expected_trend_persistence = prior_returns.iloc[31:41].gt(0).mean()
    expected_downside_pressure = prior_returns.iloc[36:41].clip(upper=0).sum() * -1.0

    assert round(row["trend_persistence_10"], 6) == round(expected_trend_persistence, 6)
    assert round(row["downside_pressure_5"], 6) == round(expected_downside_pressure, 6)


def test_feature_builder_adds_macd_breakout_and_recovery_signals():
    frame = build_phase_0_features(_sample_frame())
    row = frame.iloc[45]
    shifted_close = frame["close"].shift(1)
    ema_12 = shifted_close.ewm(span=12, adjust=False).mean()
    ema_26 = shifted_close.ewm(span=26, adjust=False).mean()
    expected_macd = ema_12.iloc[45] - ema_26.iloc[45]
    expected_signal = (ema_12 - ema_26).ewm(span=9, adjust=False).mean().iloc[45]
    expected_hist = expected_macd - expected_signal
    rolling_peak_20_prior = frame["close"].shift(2).rolling(window=20).max().iloc[45]
    previous_close = frame.iloc[44]["close"]
    expected_breakout_strength = (previous_close / rolling_peak_20_prior) - 1.0
    rolling_trough_10 = frame["close"].shift(1).rolling(window=10).min().iloc[45]
    expected_recovery_strength = (previous_close / rolling_trough_10) - 1.0
    prior_returns = frame["close"].pct_change().shift(1)
    expected_recovery_pressure = prior_returns.iloc[41:46].clip(lower=0).sum()

    assert round(row["macd"], 6) == round(expected_macd, 6)
    assert round(row["macd_signal"], 6) == round(expected_signal, 6)
    assert round(row["macd_histogram"], 6) == round(expected_hist, 6)
    assert round(row["breakout_strength_20"], 6) == round(expected_breakout_strength, 6)
    assert round(row["recovery_strength_10"], 6) == round(expected_recovery_strength, 6)
    assert round(row["recovery_pressure_5"], 6) == round(expected_recovery_pressure, 6)


def test_phase_2_feature_panel_aligns_symbols_on_shared_dates():
    base = _sample_frame()
    second = _sample_frame().iloc[5:].reset_index(drop=True)

    panel = build_phase_2_feature_panel({"RY": base, "MSFT": second})

    assert "ry__open_gap" in panel.columns
    assert "msft__open_gap" in panel.columns
    assert panel["date"].min() == second["date"].min()
    assert panel["date"].max() == second["date"].max()
    assert len(panel) <= len(second)


def test_phase_2_feature_panel_uses_stable_symbol_prefixes():
    panel = build_phase_2_feature_panel({"BRK.B": _sample_frame()})

    expected_columns = {
        "brk_b__open",
        "brk_b__close",
        "brk_b__open_gap",
        "brk_b__trend_persistence_10",
        "brk_b__macd",
        "brk_b__breakout_strength_20",
        "brk_b__cs_momentum_rank_20",
        "brk_b__cs_breakout_spread_20",
    }

    assert expected_columns.issubset(set(panel.columns))


def test_phase_2_feature_panel_adds_cross_sectional_features():
    base = _sample_frame()
    stronger = _sample_frame().copy()
    stronger["close"] = stronger["close"] + 50.0

    panel = build_phase_2_feature_panel({"RY": base, "MSFT": stronger}).dropna().reset_index(drop=True)

    row = panel.iloc[-1]
    assert 0.0 <= float(row["ry__cs_momentum_rank_20"]) <= 1.0
    assert 0.0 <= float(row["msft__cs_momentum_rank_20"]) <= 1.0
    assert round(float(row["ry__cs_momentum_spread_20"]) + float(row["msft__cs_momentum_spread_20"]), 10) == 0.0
    assert round(float(row["ry__cs_breakout_spread_20"]) + float(row["msft__cs_breakout_spread_20"]), 10) == 0.0


def test_phase_2_feature_panel_adds_market_context_columns():
    panel = build_phase_2_feature_panel(
        {"RY": _sample_frame(), "MSFT": _sample_frame()},
        market_frame=_sample_frame(),
    ).dropna().reset_index(drop=True)

    expected = {
        "market__momentum_20",
        "market__sma_30_gap",
        "market__drawdown_from_30d_peak",
        "market__volatility_20",
        "market__trend_persistence_10",
    }

    assert expected.issubset(set(panel.columns))
