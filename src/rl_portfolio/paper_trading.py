"""Reusable paper-trading services for Phase 4 exports and local dashboards."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json

import pandas as pd

from .config import PHASE_3_GROUP_B_CORE_FEATURE_SUFFIXES, PortfolioEnvironmentConfig
from .data import prepare_multi_asset_raw_panel
from .execution import accrue_cash, execute_target_weights
from .features import build_phase_2_feature_panel
from .io import filter_date_range
from .portfolio_environment import PortfolioTradingEnv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_SYMBOLS = ("RY", "MSFT", "RKLB", "XOM", "PG")
EXTENDED_SYMBOLS = ("RY", "MSFT", "RKLB", "NVDA", "LMT", "XOM", "FSLR", "PG", "DE", "FCX")
DEFAULT_MODEL_PATH = PROJECT_ROOT / "artifacts" / "phase_03" / "ppo_group_b_core_20k" / "ppo_phase_02.zip"
DEFAULT_VECNORMALIZE_PATH = PROJECT_ROOT / "artifacts" / "phase_03" / "ppo_group_b_core_20k" / "vecnormalize.pkl"
EXTENDED_MODEL_PATH = PROJECT_ROOT / "artifacts" / "phase_03" / "ppo_group_b_core_extended_20k" / "ppo_phase_02.zip"
EXTENDED_VECNORMALIZE_PATH = PROJECT_ROOT / "artifacts" / "phase_03" / "ppo_group_b_core_extended_20k" / "vecnormalize.pkl"


def generate_policy_snapshot(
    *,
    raw_start: str = "2010-01-01",
    sim_start: str = "2026-01-01",
    symbols: tuple[str, ...] = CORE_SYMBOLS,
    model_path: str | Path = DEFAULT_MODEL_PATH,
    vecnormalize_path: str | Path = DEFAULT_VECNORMALIZE_PATH,
    seed: int = 42,
    run_timestamp: pd.Timestamp | None = None,
) -> dict[str, object]:
    """Run the frozen paper-trading policy from 2026 start to the latest market date."""

    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    timestamp = run_timestamp or pd.Timestamp.now()
    today = timestamp.normalize()
    download_end = (today + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    frames_by_symbol, _ = prepare_multi_asset_raw_panel(
        list(symbols),
        start_date=raw_start,
        end_date=download_end,
    )
    feature_panel = build_phase_2_feature_panel(frames_by_symbol).dropna().reset_index(drop=True)
    sim_frame = filter_date_range(feature_panel, start_date=sim_start)
    if sim_frame.empty:
        raise ValueError(f"No simulation rows available on or after {sim_start}.")

    config = PortfolioEnvironmentConfig(
        symbols=tuple(symbols),
        training_window=len(sim_frame),
        random_start=False,
        seed=seed,
        annual_cash_yield=0.0,
        reward_mode="log_return_with_turnover_penalty",
        turnover_penalty_coef=0.001,
        strategic_review_interval_days=63,
        residual_freeze_enabled=True,
        extreme_residual_drift_threshold=0.20,
        market_feature_suffixes=PHASE_3_GROUP_B_CORE_FEATURE_SUFFIXES,
    )

    model = PPO.load(_normalize_model_load_path(model_path), device="cpu")
    vec_env = DummyVecEnv([lambda: PortfolioTradingEnv(sim_frame, config)])
    vec_path = Path(vecnormalize_path)
    if not vec_path.is_absolute():
        vec_path = PROJECT_ROOT / vec_path
    vec_norm = VecNormalize.load(str(vec_path), vec_env)
    vec_norm.training = False
    vec_norm.norm_reward = False

    env = PortfolioTradingEnv(sim_frame, config)
    env.reset(seed=seed)
    init_record = initialize_equal_weight_portfolio(env)

    observation = env._get_observation()
    terminated = False
    truncated = False
    while not terminated and not truncated:
        normalized = vec_norm.normalize_obs(observation.reshape(1, -1))
        action, _ = model.predict(normalized, deterministic=True)
        observation, _, terminated, truncated, _ = env.step(action[0])

    history = pd.DataFrame(env.history)
    latest_record = history.iloc[-1].to_dict()
    diagnostics = env.get_diagnostics()
    latest_row = sim_frame.iloc[env.current_index if env.current_index < len(sim_frame) else len(sim_frame) - 1]
    prices = {symbol: float(latest_row[f"{_symbol_prefix(symbol)}__close"]) for symbol in symbols}

    return {
        "generated_at": timestamp.isoformat(),
        "assumed_run_time": f"{today.date().isoformat()} 12:00 America/Toronto",
        "latest_market_date": pd.Timestamp(sim_frame["date"].max()).date().isoformat(),
        "simulation_start": sim_start,
        "symbols": list(symbols),
        "prices": prices,
        "target_weights": latest_record["target_weights"],
        "strategy_position_weights": latest_record["position_weights"],
        "strategy_cash_weight": float(latest_record["cash_weight"]),
        "strategy_portfolio_value": float(diagnostics["portfolio_value"]),
        "core_symbol": latest_record.get("core_symbol"),
        "review_step": bool(latest_record.get("review_step", False)),
        "initialization": init_record,
        "history": history.to_dict(orient="records"),
        "execution": latest_record["execution"],
    }


def build_trade_plan(execution_record: dict[str, object], symbols: list[str]) -> dict[str, list[dict[str, object]]]:
    """Create sell-first / buy-second order blocks from an execution record."""

    symbol_results = execution_record.get("symbol_results", {})
    sells: list[dict[str, object]] = []
    buys: list[dict[str, object]] = []

    for symbol in symbols:
        result = symbol_results.get(symbol)
        if not result or not bool(result.get("executed")):
            continue
        side = str(result["side"])
        entry = {
            "symbol": symbol,
            "side": side,
            "shares_delta": int(result["shares_delta"]),
            "trade_notional": float(result["trade_notional"]),
            "execution_price": float(result["execution_price"]),
            "commission_paid": float(result["commission_paid"]),
            "slippage_paid": float(result["slippage_paid"]),
            "cash_effect": float(
                result["trade_notional"] - result["commission_paid"] - result["slippage_paid"]
                if side == "sell"
                else -(result["trade_notional"] + result["commission_paid"] + result["slippage_paid"])
            ),
        }
        if side == "sell":
            sells.append(entry)
        else:
            buys.append(entry)

    sells.sort(key=lambda item: item["trade_notional"], reverse=True)
    buys.sort(key=lambda item: item["trade_notional"], reverse=True)
    return {"sell_first": sells, "buy_second": buys}


def build_profile_recommendation(
    *,
    profile: dict[str, object],
    policy_snapshot: dict[str, object],
) -> dict[str, object]:
    """Compare a stored profile against the frozen policy and build today's order ticket."""

    supported_symbols = list(policy_snapshot["symbols"])
    prices = dict(policy_snapshot["prices"])
    holdings = list(profile.get("holdings", []))

    shares_by_symbol = {symbol: 0 for symbol in supported_symbols}
    supported_rows: list[dict[str, object]] = []
    unsupported_rows: list[dict[str, object]] = []

    total_supported_market_value = float(profile["cash"])
    total_supported_cost = float(profile["cash"])

    for holding in holdings:
        symbol = str(holding["symbol"]).upper().strip()
        average_cost = float(holding["average_cost"])
        shares = int(holding["shares"])
        cost_basis = average_cost * shares
        if symbol not in prices:
            unsupported_rows.append(
                {
                    "symbol": symbol,
                    "shares": shares,
                    "average_cost": average_cost,
                    "cost_basis": cost_basis,
                    "reason": "Unsupported by the current frozen model basket.",
                }
            )
            continue

        latest_price = float(prices[symbol])
        market_value = latest_price * shares
        unrealized_pnl = market_value - cost_basis
        shares_by_symbol[symbol] += shares
        total_supported_market_value += market_value
        total_supported_cost += cost_basis
        supported_rows.append(
            {
                "symbol": symbol,
                "shares": shares,
                "average_cost": average_cost,
                "latest_price": latest_price,
                "cost_basis": cost_basis,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": (unrealized_pnl / cost_basis) if cost_basis > 0 else 0.0,
            }
        )

    current_weights = {
        symbol: (float(prices[symbol]) * shares_by_symbol[symbol]) / total_supported_market_value
        if total_supported_market_value > 0
        else 0.0
        for symbol in supported_symbols
    }
    current_cash_weight = float(profile["cash"]) / total_supported_market_value if total_supported_market_value > 0 else 0.0

    execution_result = execute_target_weights(
        cash=float(profile["cash"]),
        shares_by_symbol=shares_by_symbol,
        close_prices=prices,
        target_weights=dict(policy_snapshot["target_weights"]),
        config=PortfolioEnvironmentConfig(
            symbols=tuple(supported_symbols),
            annual_cash_yield=0.0,
            reward_mode="log_return_with_turnover_penalty",
            turnover_penalty_coef=0.001,
            strategic_review_interval_days=63,
            residual_freeze_enabled=True,
            extreme_residual_drift_threshold=0.20,
            market_feature_suffixes=PHASE_3_GROUP_B_CORE_FEATURE_SUFFIXES,
        ),
    )

    by_symbol = {row["symbol"]: row for row in supported_rows}
    dashboard_rows: list[dict[str, object]] = []
    for symbol in supported_symbols:
        row = by_symbol.get(
            symbol,
            {
                "symbol": symbol,
                "shares": 0,
                "average_cost": 0.0,
                "latest_price": float(prices[symbol]),
                "cost_basis": 0.0,
                "market_value": 0.0,
                "unrealized_pnl": 0.0,
                "unrealized_pnl_pct": 0.0,
            },
        )
        dashboard_rows.append(
            {
                **row,
                "current_weight": float(current_weights.get(symbol, 0.0)),
                "target_weight": float(policy_snapshot["target_weights"].get(symbol, 0.0)),
                "shares_after_rebalance": int(execution_result.shares_after[symbol]),
                "shares_delta": int(execution_result.symbol_results[symbol].shares_delta),
            }
        )

    return {
        "profile_id": int(profile["id"]),
        "profile_name": str(profile["name"]),
        "generated_at": policy_snapshot["generated_at"],
        "assumed_run_time": policy_snapshot["assumed_run_time"],
        "latest_market_date": policy_snapshot["latest_market_date"],
        "simulation_start": policy_snapshot["simulation_start"],
        "core_symbol": policy_snapshot["core_symbol"],
        "review_step": bool(policy_snapshot["review_step"]),
        "cash": float(profile["cash"]),
        "cash_after_rebalance": float(execution_result.cash_after),
        "current_cash_weight": float(current_cash_weight),
        "strategy_cash_weight": float(policy_snapshot["strategy_cash_weight"]),
        "target_weights": dict(policy_snapshot["target_weights"]),
        "current_weights": current_weights,
        "portfolio_market_value": float(total_supported_market_value),
        "portfolio_cost_basis": float(total_supported_cost),
        "total_unrealized_pnl": float(sum(float(row["unrealized_pnl"]) for row in dashboard_rows)),
        "dashboard_rows": dashboard_rows,
        "unsupported_rows": unsupported_rows,
        "trades": build_trade_plan(asdict(execution_result), supported_symbols),
    }


def resolve_policy_bundle(profile_symbols: list[str] | tuple[str, ...]) -> dict[str, object]:
    """Resolve the frozen policy bundle that can serve the given profile symbols."""

    normalized_symbols = {str(symbol).upper().strip() for symbol in profile_symbols if str(symbol).strip()}
    if normalized_symbols.issubset(set(CORE_SYMBOLS)):
        return {
            "bundle_name": "core",
            "symbols": CORE_SYMBOLS,
            "model_path": DEFAULT_MODEL_PATH,
            "vecnormalize_path": DEFAULT_VECNORMALIZE_PATH,
        }
    if normalized_symbols.issubset(set(EXTENDED_SYMBOLS)):
        return {
            "bundle_name": "extended",
            "symbols": EXTENDED_SYMBOLS,
            "model_path": EXTENDED_MODEL_PATH,
            "vecnormalize_path": EXTENDED_VECNORMALIZE_PATH,
        }
    raise ValueError("Profile symbols are not supported by the current frozen model baskets.")


def initialize_equal_weight_portfolio(env: PortfolioTradingEnv) -> dict[str, object]:
    """Initialize a portfolio environment with equal weights on the first trading day."""

    first_row = env.frame.iloc[env.current_index]
    close_prices = {symbol: float(first_row[f"{_symbol_prefix(symbol)}__close"]) for symbol in env.symbols}
    target_weights = {symbol: 1.0 / len(env.symbols) for symbol in env.symbols}
    execution = execute_target_weights(
        cash=env.cash,
        shares_by_symbol=env.shares_by_symbol,
        close_prices=close_prices,
        target_weights=target_weights,
        config=env.config,
    )
    env.cash = accrue_cash(execution.cash_after, env.config.daily_cash_rate)
    env.shares_by_symbol = execution.shares_after.copy()
    env.previous_portfolio_value = env.get_portfolio_value(close_prices)
    env.last_target_weights = target_weights.copy()
    env.last_cash_target_weight = max(0.0, 1.0 - sum(target_weights.values()))
    env.last_execution = execution
    if env.current_index < env.end_index - 1:
        env.current_index += 1

    return {
        "date": pd.Timestamp(first_row["date"]).date().isoformat(),
        "target_weights": target_weights,
        "shares_after": execution.shares_after,
        "cash_after": float(env.cash),
        "executed_symbols": execution.executed_symbols,
        "close_prices": close_prices,
        "symbol_results": {
            symbol: {
                "executed": result.executed,
                "side": result.side,
                "shares_delta": result.shares_delta,
                "execution_price": result.execution_price,
                "commission_paid": result.commission_paid,
                "slippage_paid": result.slippage_paid,
                "trade_notional": result.trade_notional,
                "shares_after": result.shares_after,
            }
            for symbol, result in execution.symbol_results.items()
        },
    }


def dump_snapshot_json(output_path: str | Path, payload: dict[str, object]) -> None:
    """Persist any paper-trading payload as JSON."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _normalize_model_load_path(model_path: str | Path) -> str:
    path = Path(model_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if path.suffix == ".zip" and path.exists():
        return str(path.with_suffix(""))
    return str(path)


def _symbol_prefix(symbol: str) -> str:
    return symbol.strip().lower().replace("-", "_").replace(".", "_")
