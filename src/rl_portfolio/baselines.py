"""Baseline policy mappings for single-asset and portfolio comparisons."""

from __future__ import annotations

import numpy as np


def buy_signal() -> float:
    """Return the target weight equivalent of a discrete buy action."""

    return 1.0


def sell_signal() -> float:
    """Return the target weight equivalent of a discrete sell action."""

    return 0.0


def hold_signal(previous_target_weight: float) -> float:
    """Return the previous target weight for a discrete hold action."""

    return previous_target_weight


def random_signal(rng: np.random.Generator) -> float:
    """Sample a random target position in the valid action range."""

    return float(rng.uniform(0.0, 1.0))


def weights_to_logits(asset_weights: dict[str, float], cash_weight: float) -> np.ndarray:
    """Convert a target weight vector into softmax-compatible logits."""

    ordered_weights = [max(float(weight), 1e-8) for _, weight in asset_weights.items()]
    ordered_weights.append(max(float(cash_weight), 1e-8))
    return np.log(np.array(ordered_weights, dtype=np.float32))


def equal_weight_portfolio_signal(symbols: list[str] | tuple[str, ...]) -> np.ndarray:
    """Return logits for equal-weight allocation across assets and zero cash."""

    asset_weight = 1.0 / len(symbols)
    asset_weights = {symbol: asset_weight for symbol in symbols}
    return weights_to_logits(asset_weights, cash_weight=1e-8)


def cash_only_portfolio_signal(symbols: list[str] | tuple[str, ...]) -> np.ndarray:
    """Return logits for an all-cash portfolio."""

    asset_weights = {symbol: 1e-8 for symbol in symbols}
    return weights_to_logits(asset_weights, cash_weight=1.0)


def random_portfolio_signal(
    rng: np.random.Generator,
    symbols: list[str] | tuple[str, ...],
) -> np.ndarray:
    """Sample a random long-only portfolio allocation including cash."""

    sample = rng.dirichlet(np.ones(len(symbols) + 1, dtype=np.float32))
    return np.log(sample.astype(np.float32))
