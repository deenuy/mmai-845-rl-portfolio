"""Feature engineering helpers for the restricted single-asset and multi-asset observation spaces."""

from __future__ import annotations

import pandas as pd


def build_phase_0_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Create pre-close observation features without leaking same-day close data."""

    required = {"date", "open", "high", "low", "close", "volume"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns for feature generation: {missing}")

    features = frame.copy()
    features = features.sort_values("date").reset_index(drop=True)

    previous_close = features["close"].shift(1)
    prior_close = features["close"].shift(2)
    previous_close_5 = features["close"].shift(5)
    previous_close_20 = features["close"].shift(20)
    previous_returns = features["close"].pct_change().shift(1)
    rolling_peak_20 = features["close"].shift(1).rolling(window=20).max()
    rolling_peak_20_prior = features["close"].shift(2).rolling(window=20).max()
    rolling_peak_30 = features["close"].shift(1).rolling(window=30).max()
    rolling_mean_5 = features["close"].shift(1).rolling(window=5).mean()
    rolling_mean_20 = features["close"].shift(1).rolling(window=20).mean()
    rolling_mean_30 = features["close"].shift(1).rolling(window=30).mean()
    rolling_mean_30_prior = rolling_mean_30.shift(5)
    rolling_return_std_20 = previous_returns.rolling(window=20).std()
    trend_persistence_10 = previous_returns.gt(0).rolling(window=10).mean()
    downside_pressure_5 = previous_returns.clip(upper=0).rolling(window=5).sum().abs()
    ema_12 = features["close"].shift(1).ewm(span=12, adjust=False).mean()
    ema_26 = features["close"].shift(1).ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    macd_signal = macd_line.ewm(span=9, adjust=False).mean()
    rolling_trough_10 = features["close"].shift(1).rolling(window=10).min()
    positive_pressure_5 = previous_returns.clip(lower=0).rolling(window=5).sum()

    features["open_gap"] = (features["open"] / previous_close) - 1.0
    features["previous_close_return"] = (previous_close / prior_close) - 1.0
    features["momentum_5"] = (previous_close / previous_close_5) - 1.0
    features["momentum_20"] = (previous_close / previous_close_20) - 1.0
    features["sma_5_gap"] = (previous_close / rolling_mean_5) - 1.0
    features["sma_20_gap"] = (previous_close / rolling_mean_20) - 1.0
    features["sma_30_gap"] = (previous_close / rolling_mean_30) - 1.0
    features["sma_30_slope"] = (rolling_mean_30 / rolling_mean_30_prior) - 1.0
    features["distance_to_20d_high"] = (previous_close / rolling_peak_20) - 1.0
    features["drawdown_from_30d_peak"] = (previous_close / rolling_peak_30) - 1.0
    features["volatility_20"] = rolling_return_std_20
    features["trend_persistence_10"] = trend_persistence_10
    features["downside_pressure_5"] = downside_pressure_5
    features["macd"] = macd_line
    features["macd_signal"] = macd_signal
    features["macd_histogram"] = macd_line - macd_signal
    features["breakout_strength_20"] = (previous_close / rolling_peak_20_prior) - 1.0
    features["breakout_persistence_5"] = (
        features["breakout_strength_20"].gt(0).shift(1).rolling(window=5).mean()
    )
    features["recovery_strength_10"] = (previous_close / rolling_trough_10) - 1.0
    features["recovery_pressure_5"] = positive_pressure_5

    return features


def build_observation_row(
    frame: pd.DataFrame,
    index: int,
    cash: float,
    shares: int,
    previous_target_weight: float,
    initial_cash: float,
) -> dict[str, float]:
    """Build the restricted observation for a single timestep."""

    row = frame.iloc[index]
    portfolio_value = cash + shares * float(row["open"])
    position_value = shares * float(row["open"])
    position_weight = position_value / portfolio_value if portfolio_value > 0 else 0.0
    cash_ratio = cash / portfolio_value if portfolio_value > 0 else 0.0
    shares_held_ratio = position_value / initial_cash if initial_cash > 0 else 0.0

    return {
        "cash_ratio": float(cash_ratio),
        "position_weight": float(position_weight),
        "shares_held_ratio": float(shares_held_ratio),
        "previous_target_weight": float(previous_target_weight),
        "open_gap": float(row["open_gap"]),
        "previous_close_return": float(row["previous_close_return"]),
        "momentum_5": float(row["momentum_5"]),
        "momentum_20": float(row["momentum_20"]),
        "sma_5_gap": float(row["sma_5_gap"]),
        "sma_20_gap": float(row["sma_20_gap"]),
        "sma_30_gap": float(row["sma_30_gap"]),
        "sma_30_slope": float(row["sma_30_slope"]),
        "distance_to_20d_high": float(row["distance_to_20d_high"]),
        "drawdown_from_30d_peak": float(row["drawdown_from_30d_peak"]),
        "volatility_20": float(row["volatility_20"]),
        "trend_persistence_10": float(row["trend_persistence_10"]),
        "downside_pressure_5": float(row["downside_pressure_5"]),
        "macd": float(row["macd"]),
        "macd_signal": float(row["macd_signal"]),
        "macd_histogram": float(row["macd_histogram"]),
        "breakout_strength_20": float(row["breakout_strength_20"]),
        "breakout_persistence_5": float(row["breakout_persistence_5"]),
        "recovery_strength_10": float(row["recovery_strength_10"]),
        "recovery_pressure_5": float(row["recovery_pressure_5"]),
    }


def build_phase_2_feature_panel(
    frames_by_symbol: dict[str, pd.DataFrame],
    market_frame: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build an aligned wide feature panel for a multi-asset basket.

    Each symbol keeps the same feature contract as Phase 1, but columns are prefixed
    with the lowercased ticker so later portfolio environments can consume a single,
    synchronized dataframe.
    """

    if not frames_by_symbol:
        raise ValueError("At least one symbol frame is required to build a Phase 2 feature panel.")

    panel: pd.DataFrame | None = None

    for symbol, frame in frames_by_symbol.items():
        features = build_phase_0_features(frame).copy()
        prefix = _symbol_prefix(symbol)
        renamed = features.rename(
            columns={
                column: f"{prefix}__{column}"
                for column in features.columns
                if column != "date"
            }
        )

        if panel is None:
            panel = renamed
            continue

        panel = panel.merge(renamed, on="date", how="inner")

    assert panel is not None
    panel = panel.sort_values("date").reset_index(drop=True)
    if market_frame is not None:
        market_features = build_phase_0_features(market_frame).copy()
        market_columns = ["date"] + [column for column in market_features.columns if column not in {"date", "open", "high", "low", "close", "volume"}]
        market_features = market_features[market_columns].rename(
            columns={column: f"market__{column}" for column in market_columns if column != "date"}
        )
        panel = panel.merge(market_features, on="date", how="inner")
    panel = _add_cross_sectional_features(panel, list(frames_by_symbol.keys()))
    return panel


def _symbol_prefix(symbol: str) -> str:
    """Normalize a ticker symbol for use as a stable feature prefix."""

    return symbol.strip().lower().replace("-", "_").replace(".", "_")


def _add_cross_sectional_features(panel: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    """Append cross-sectional relative-strength features to a wide symbol panel."""

    enriched = panel.copy()
    feature_specs = (
        ("momentum_20", "cs_momentum_rank_20", "cs_momentum_spread_20"),
        ("distance_to_20d_high", "cs_breakout_rank_20", "cs_breakout_spread_20"),
        ("drawdown_from_30d_peak", "cs_drawdown_rank_30", "cs_drawdown_spread_30"),
    )

    for base_suffix, rank_suffix, spread_suffix in feature_specs:
        prefixed_columns = [f"{_symbol_prefix(symbol)}__{base_suffix}" for symbol in symbols]
        cross_section = enriched[prefixed_columns]
        ranks = cross_section.rank(axis=1, method="average", pct=True)
        means = cross_section.mean(axis=1)

        for symbol in symbols:
            prefix = _symbol_prefix(symbol)
            base_column = f"{prefix}__{base_suffix}"
            enriched[f"{prefix}__{rank_suffix}"] = ranks[base_column]
            enriched[f"{prefix}__{spread_suffix}"] = enriched[base_column] - means

    return enriched
