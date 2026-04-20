"""Export a local Phase 4 paper-trading recommendation page from the frozen mainline policy."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from rl_portfolio.config import PHASE_3_GROUP_B_CORE_FEATURE_SUFFIXES, PortfolioEnvironmentConfig
from rl_portfolio.data import prepare_multi_asset_raw_panel
from rl_portfolio.execution import accrue_cash, execute_target_weights
from rl_portfolio.features import build_phase_2_feature_panel
from rl_portfolio.io import filter_date_range
from rl_portfolio.portfolio_environment import PortfolioTradingEnv

CORE_SYMBOLS = ("RY", "MSFT", "RKLB", "XOM", "PG")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the Phase 4 paper-trading export."""

    parser = argparse.ArgumentParser(description="Export today's Phase 4 paper-trading recommendation.")
    parser.add_argument("--raw-start", default="2010-01-01", help="Start date for raw feature construction.")
    parser.add_argument("--sim-start", default="2026-01-01", help="Start date for live-style simulation.")
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=list(CORE_SYMBOLS),
        help="Symbols to include in the paper-trading basket.",
    )
    parser.add_argument(
        "--model-path",
        default="artifacts/phase_03/ppo_group_b_core_20k/ppo_phase_02.zip",
        help="Path to the frozen mainline PPO model.",
    )
    parser.add_argument(
        "--vecnormalize-path",
        default="artifacts/phase_03/ppo_group_b_core_20k/vecnormalize.pkl",
        help="Path to saved VecNormalize statistics.",
    )
    parser.add_argument(
        "--output-root",
        default="artifacts/phase_04/paper_trading",
        help="Root directory for paper-trading exports.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Simulation seed.")
    return parser.parse_args()


def main() -> None:
    """Generate a dated paper-trading export package and a latest copy."""

    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    args = parse_args()
    run_timestamp = pd.Timestamp.now()
    today = run_timestamp.normalize()
    download_end = (today + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    frames_by_symbol, _ = prepare_multi_asset_raw_panel(
        list(args.symbols),
        start_date=args.raw_start,
        end_date=download_end,
    )
    feature_panel = build_phase_2_feature_panel(frames_by_symbol).dropna().reset_index(drop=True)
    sim_frame = filter_date_range(feature_panel, start_date=args.sim_start)
    if sim_frame.empty:
        raise ValueError(f"No simulation rows available on or after {args.sim_start}.")

    latest_market_date = pd.Timestamp(sim_frame["date"].max())
    config = PortfolioEnvironmentConfig(
        symbols=tuple(args.symbols),
        training_window=len(sim_frame),
        random_start=False,
        seed=args.seed,
        annual_cash_yield=0.0,
        reward_mode="log_return_with_turnover_penalty",
        turnover_penalty_coef=0.001,
        strategic_review_interval_days=63,
        residual_freeze_enabled=True,
        extreme_residual_drift_threshold=0.20,
        market_feature_suffixes=PHASE_3_GROUP_B_CORE_FEATURE_SUFFIXES,
    )

    model = PPO.load(_normalize_model_load_path(args.model_path), device="cpu")
    vec_env = DummyVecEnv([lambda: PortfolioTradingEnv(sim_frame, config)])
    vec_norm = VecNormalize.load(str(Path(args.vecnormalize_path)), vec_env)
    vec_norm.training = False
    vec_norm.norm_reward = False

    env = PortfolioTradingEnv(sim_frame, config)
    env.reset(seed=args.seed)
    init_record = _initialize_equal_weight_portfolio(env)

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
    prices = {symbol: float(latest_row[f"{_symbol_prefix(symbol)}__close"]) for symbol in args.symbols}
    position_dashboard = _build_position_dashboard(
        init_record=init_record,
        history=history,
        symbols=list(args.symbols),
        latest_prices=prices,
    )

    trades = _build_trade_plan(latest_record["execution"], args.symbols)
    summary = {
        "generated_at": run_timestamp.isoformat(),
        "assumed_run_time": f"{today.date().isoformat()} 12:00 America/Toronto",
        "latest_market_date": latest_market_date.date().isoformat(),
        "simulation_start": args.sim_start,
        "initialization": init_record,
        "portfolio_value": float(diagnostics["portfolio_value"]),
        "cash": float(diagnostics["cash"]),
        "cash_weight": float(latest_record["cash_weight"]),
        "core_symbol": latest_record.get("core_symbol"),
        "review_step": bool(latest_record.get("review_step", False)),
        "target_weights": latest_record["target_weights"],
        "position_weights": latest_record["position_weights"],
        "position_dashboard": position_dashboard,
        "trades": trades,
        "symbols": list(args.symbols),
    }

    output_root = Path(args.output_root)
    dated_dir = output_root / latest_market_date.strftime("%Y-%m-%d")
    latest_dir = output_root / "latest"
    for directory in (dated_dir, latest_dir):
        directory.mkdir(parents=True, exist_ok=True)
        _write_outputs(directory, summary, history, prices)

    print(f"Saved Phase 4 paper-trading export to {dated_dir}")
    print(f"Updated latest export at {latest_dir}")


def _normalize_model_load_path(model_path: str) -> str:
    path = Path(model_path)
    if path.suffix == ".zip" and path.exists():
        return str(path.with_suffix(""))
    return str(path)


def _initialize_equal_weight_portfolio(env: PortfolioTradingEnv) -> dict[str, object]:
    """Initialize the environment as an equal-weight portfolio at the first simulation date."""

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


def _build_trade_plan(execution_record: dict[str, object], symbols: list[str]) -> dict[str, list[dict[str, object]]]:
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


def _build_position_dashboard(
    *,
    init_record: dict[str, object],
    history: pd.DataFrame,
    symbols: list[str],
    latest_prices: dict[str, float],
) -> dict[str, object]:
    """Build per-symbol holdings, cost basis, and P&L from the 2026 initialization onward."""

    ledger = {
        symbol: {
            "shares": 0,
            "cost_basis": 0.0,
            "commission_paid": 0.0,
            "realized_pnl": 0.0,
        }
        for symbol in symbols
    }

    _apply_symbol_results_to_ledger(ledger, init_record.get("symbol_results", {}))

    for execution in history["execution"]:
        _apply_symbol_results_to_ledger(ledger, execution.get("symbol_results", {}))

    latest_position_weights = history.iloc[-1]["position_weights"]
    latest_target_weights = history.iloc[-1]["target_weights"]
    rows: list[dict[str, object]] = []
    total_market_value = 0.0
    total_unrealized_pnl = 0.0

    for symbol in symbols:
        shares = int(ledger[symbol]["shares"])
        cost_basis = float(ledger[symbol]["cost_basis"])
        price = float(latest_prices[symbol])
        market_value = shares * price
        unrealized_pnl = market_value - cost_basis
        unrealized_pnl_pct = (unrealized_pnl / cost_basis) if cost_basis > 0 else 0.0
        total_market_value += market_value
        total_unrealized_pnl += unrealized_pnl
        rows.append(
            {
                "symbol": symbol,
                "shares": shares,
                "latest_price": price,
                "market_value": market_value,
                "cost_basis": cost_basis,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct,
                "realized_pnl": float(ledger[symbol]["realized_pnl"]),
                "commission_paid": float(ledger[symbol]["commission_paid"]),
                "position_weight": float(latest_position_weights.get(symbol, 0.0)),
                "target_weight": float(latest_target_weights.get(symbol, 0.0)),
            }
        )

    return {
        "rows": rows,
        "total_market_value": total_market_value,
        "total_unrealized_pnl": total_unrealized_pnl,
        "initial_date": init_record["date"],
    }


def _apply_symbol_results_to_ledger(
    ledger: dict[str, dict[str, float | int]],
    symbol_results: dict[str, dict[str, object]],
) -> None:
    """Apply executed symbol results to a simple average-cost ledger."""

    for symbol, result in symbol_results.items():
        if not bool(result.get("executed")):
            continue
        shares_delta = int(result["shares_delta"])
        execution_price = float(result["execution_price"])
        commission_paid = float(result.get("commission_paid", 0.0))
        previous_shares = int(ledger[symbol]["shares"])
        previous_cost_basis = float(ledger[symbol]["cost_basis"])

        if shares_delta > 0:
            added_cost = (shares_delta * execution_price) + commission_paid
            ledger[symbol]["shares"] = previous_shares + shares_delta
            ledger[symbol]["cost_basis"] = previous_cost_basis + added_cost
            ledger[symbol]["commission_paid"] = float(ledger[symbol]["commission_paid"]) + commission_paid
            continue

        sold_shares = abs(shares_delta)
        if previous_shares <= 0:
            continue
        average_cost = previous_cost_basis / previous_shares if previous_shares > 0 else 0.0
        removed_cost = average_cost * sold_shares
        sale_proceeds = (sold_shares * execution_price) - commission_paid
        realized_pnl = sale_proceeds - removed_cost
        ledger[symbol]["shares"] = previous_shares - sold_shares
        ledger[symbol]["cost_basis"] = max(previous_cost_basis - removed_cost, 0.0)
        ledger[symbol]["realized_pnl"] = float(ledger[symbol]["realized_pnl"]) + realized_pnl
        ledger[symbol]["commission_paid"] = float(ledger[symbol]["commission_paid"]) + commission_paid


def _write_outputs(output_dir: Path, summary: dict[str, object], history: pd.DataFrame, prices: dict[str, float]) -> None:
    (output_dir / "paper_trading_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _plot_equity_curve(history, output_dir / "equity_curve.png")
    _plot_weights(history, summary["symbols"], output_dir / "position_weights.png")
    _plot_symbol_market_values(summary["position_dashboard"]["rows"], output_dir / "market_values.png")
    _plot_symbol_unrealized_pnl(summary["position_dashboard"]["rows"], output_dir / "unrealized_pnl.png")
    _write_html(output_dir / "index.html", summary, prices)


def _plot_equity_curve(history: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(12, 6))
    plt.plot(pd.to_datetime(history["date"]), history["portfolio_value"].astype(float))
    plt.title("Phase 4 Paper Trading Equity Since 2026 Start")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def _plot_weights(history: pd.DataFrame, symbols: list[str], output_path: Path) -> None:
    plt.figure(figsize=(12, 6))
    dates = pd.to_datetime(history["date"])
    for symbol in symbols:
        series = history["position_weights"].apply(lambda weights: float(weights.get(symbol, 0.0)))
        plt.plot(dates, series, label=symbol)
    plt.title("Phase 4 Paper Trading Realized Position Weights")
    plt.xlabel("Date")
    plt.ylabel("Position Weight")
    plt.ylim(-0.03, 1.03)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def _plot_symbol_market_values(rows: list[dict[str, object]], output_path: Path) -> None:
    plt.figure(figsize=(12, 5))
    labels = [row["symbol"] for row in rows]
    values = [float(row["market_value"]) for row in rows]
    plt.bar(labels, values)
    plt.title("Current Market Value by Symbol")
    plt.ylabel("Market Value")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def _plot_symbol_unrealized_pnl(rows: list[dict[str, object]], output_path: Path) -> None:
    plt.figure(figsize=(12, 5))
    labels = [row["symbol"] for row in rows]
    values = [float(row["unrealized_pnl"]) for row in rows]
    colors = ["#2e7d32" if value >= 0 else "#c62828" for value in values]
    plt.bar(labels, values, color=colors)
    plt.title("Current Unrealized P&L by Symbol")
    plt.ylabel("Unrealized P&L")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def _write_html(output_path: Path, summary: dict[str, object], prices: dict[str, float]) -> None:
    sell_rows = "".join(
        f"<tr><td>{item['symbol']}</td><td>{item['shares_delta']}</td><td>{item['trade_notional']:.2f}</td><td>{item['execution_price']:.2f}</td><td>{item['cash_effect']:.2f}</td></tr>"
        for item in summary["trades"]["sell_first"]
    ) or "<tr><td colspan='5'>No sell orders.</td></tr>"
    buy_rows = "".join(
        f"<tr><td>{item['symbol']}</td><td>{item['shares_delta']}</td><td>{item['trade_notional']:.2f}</td><td>{item['execution_price']:.2f}</td><td>{item['cash_effect']:.2f}</td></tr>"
        for item in summary["trades"]["buy_second"]
    ) or "<tr><td colspan='5'>No buy orders.</td></tr>"
    weight_rows = "".join(
        f"<tr><td>{symbol}</td><td>{prices[symbol]:.2f}</td><td>{float(summary['target_weights'].get(symbol, 0.0)):.4f}</td><td>{float(summary['position_weights'].get(symbol, 0.0)):.4f}</td></tr>"
        for symbol in summary["symbols"]
    )
    dashboard_rows = "".join(
        f"<tr><td>{row['symbol']}</td><td>{int(row['shares'])}</td><td>{float(row['latest_price']):.2f}</td><td>{float(row['market_value']):.2f}</td><td>{float(row['cost_basis']):.2f}</td><td>{float(row['unrealized_pnl']):.2f}</td><td>{float(row['unrealized_pnl_pct']):.2%}</td><td>{float(row['realized_pnl']):.2f}</td><td>{float(row['position_weight']):.4f}</td><td>{float(row['target_weight']):.4f}</td></tr>"
        for row in summary["position_dashboard"]["rows"]
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Phase 4 Paper Trading Recommendation</title>
  <style>
    body {{ font-family: Georgia, serif; margin: 2rem auto; max-width: 1100px; color: #1e2a32; background: #f7f6f1; line-height: 1.6; }}
    h1, h2 {{ color: #153243; }}
    .card {{ background: white; border: 1px solid #d7d0c3; border-radius: 12px; padding: 1rem; box-shadow: 0 4px 14px rgba(0,0,0,0.05); margin-bottom: 1.5rem; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 2rem; background: white; border: 1px solid #d7d0c3; border-radius: 12px; overflow: hidden; }}
    th, td {{ border-bottom: 1px solid #ddd; padding: 0.65rem; text-align: left; }}
    th {{ background: #f0ece2; color: #153243; }}
    img {{ width: 100%; border: 1px solid #d7d0c3; border-radius: 12px; margin-bottom: 1.5rem; }}
    pre {{ background: white; border: 1px solid #d7d0c3; border-radius: 12px; padding: 16px; overflow-x: auto; }}
  </style>
</head>
<body>
  <h1>Phase 4 Paper Trading Recommendation</h1>
  <div class="card">
    <p><strong>Generated at:</strong> {summary['generated_at']}</p>
    <p><strong>Assumed daily run:</strong> {summary['assumed_run_time']}</p>
    <p><strong>Latest market date used:</strong> {summary['latest_market_date']}</p>
    <p><strong>Simulation start:</strong> {summary['simulation_start']}</p>
    <p><strong>Initialization:</strong> equal-weight build on {summary['position_dashboard']['initial_date']}</p>
    <p><strong>Current portfolio value:</strong> {float(summary['portfolio_value']):.2f}</p>
    <p><strong>Current cash:</strong> {float(summary['cash']):.2f}</p>
    <p><strong>Current cash weight:</strong> {float(summary['cash_weight']):.4f}</p>
    <p><strong>Core symbol today:</strong> {summary['core_symbol'] or 'None'}</p>
    <p><strong>Review step today:</strong> {"Yes" if summary['review_step'] else "No"}</p>
  </div>
  <h2>Position Dashboard Since 2026 Start</h2>
  <div class="card">
    <p><strong>Total market value in stocks:</strong> {float(summary['position_dashboard']['total_market_value']):.2f}</p>
    <p><strong>Total unrealized P&amp;L:</strong> {float(summary['position_dashboard']['total_unrealized_pnl']):.2f}</p>
  </div>
  <table>
    <thead>
      <tr><th>Symbol</th><th>Shares</th><th>Latest Price</th><th>Market Value</th><th>Cost Basis</th><th>Unrealized P&amp;L</th><th>Unrealized P&amp;L %</th><th>Realized P&amp;L</th><th>Current Weight</th><th>Target Weight</th></tr>
    </thead>
    <tbody>{dashboard_rows}</tbody>
  </table>
  <h2>Target vs Realized Weights</h2>
  <table>
    <thead>
      <tr><th>Symbol</th><th>Latest Close</th><th>Target Weight</th><th>Realized Weight</th></tr>
    </thead>
    <tbody>{weight_rows}</tbody>
  </table>
  <h2>Sell First</h2>
  <table>
    <thead>
      <tr><th>Symbol</th><th>Shares Delta</th><th>Trade Notional</th><th>Execution Price</th><th>Estimated Cash Effect</th></tr>
    </thead>
    <tbody>{sell_rows}</tbody>
  </table>
  <h2>Buy Second</h2>
  <table>
    <thead>
      <tr><th>Symbol</th><th>Shares Delta</th><th>Trade Notional</th><th>Execution Price</th><th>Estimated Cash Effect</th></tr>
    </thead>
    <tbody>{buy_rows}</tbody>
  </table>
  <h2>Charts</h2>
  <img src="equity_curve.png" alt="Equity curve">
  <img src="position_weights.png" alt="Position weights">
  <img src="market_values.png" alt="Market values">
  <img src="unrealized_pnl.png" alt="Unrealized P&L">
  <h2>Raw Summary</h2>
  <pre>{json.dumps(summary, indent=2)}</pre>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")


def _symbol_prefix(symbol: str) -> str:
    return symbol.strip().lower().replace("-", "_").replace(".", "_")


if __name__ == "__main__":
    main()
