"""Create example saved profiles for the local product dashboard."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from rl_portfolio.execution import execute_target_weights
from rl_portfolio.paper_trading import EXTENDED_SYMBOLS
from rl_portfolio.profile_store import ProfileHoldingInput, append_profile_log, create_profile, get_profile, initialize_profile_store, list_profiles, update_profile
from rl_portfolio.config import PortfolioEnvironmentConfig
from rl_portfolio.data import prepare_multi_asset_raw_panel


DATABASE_PATH = ROOT / "artifacts" / "phase_04" / "product" / "profiles.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed example profiles into the local product dashboard database.")
    parser.add_argument("--start-date", default="2026-01-01", help="Simulation start date for the example build.")
    parser.add_argument("--initial-cash", type=float, default=100_000.0, help="Initial cash for the example profile.")
    parser.add_argument("--reset-existing", action="store_true", help="Reset the example profile if it already exists.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    initialize_profile_store(DATABASE_PATH)

    example_name = "Example Extended Equal Weight 2026-01-01"
    holdings, remaining_cash = _build_equal_weight_holdings(
        symbols=list(EXTENDED_SYMBOLS),
        start_date=args.start_date,
        initial_cash=args.initial_cash,
    )
    existing_profiles = {profile["name"]: profile for profile in list_profiles(DATABASE_PATH)}
    if example_name in existing_profiles:
        if not args.reset_existing:
            print(f"Example profile already exists: {example_name}")
            return
        profile_id = int(existing_profiles[example_name]["id"])
        update_profile(
            DATABASE_PATH,
            profile_id=profile_id,
            name=example_name,
            cash=remaining_cash,
            holdings=holdings,
            log_action=False,
        )
        append_profile_log(
            DATABASE_PATH,
            profile_id=profile_id,
            action_type="reset_example",
            note="Example profile reset to the original 2026 equal-weight build.",
            snapshot={
                "profile_id": profile_id,
                "name": example_name,
                "cash": float(remaining_cash),
                "holdings": [
                    {"symbol": holding.symbol, "average_cost": float(holding.average_cost), "shares": int(holding.shares)}
                    for holding in holdings
                ],
            },
        )
        print(f"Reset example profile {profile_id}: {example_name}")
        return

    profile_id = create_profile(DATABASE_PATH, name=example_name, cash=remaining_cash, holdings=holdings)
    append_profile_log(
        DATABASE_PATH,
        profile_id=profile_id,
        action_type="seed_example",
        note="Example profile created from the 2026 equal-weight initialization.",
        snapshot={
            "profile_id": profile_id,
            "name": example_name,
            "cash": float(remaining_cash),
            "holdings": [
                {"symbol": holding.symbol, "average_cost": float(holding.average_cost), "shares": int(holding.shares)}
                for holding in holdings
            ],
        },
    )
    print(f"Created example profile {profile_id}: {example_name}")


def _build_equal_weight_holdings(
    *,
    symbols: list[str],
    start_date: str,
    initial_cash: float,
) -> tuple[list[ProfileHoldingInput], float]:
    frames_by_symbol, _ = prepare_multi_asset_raw_panel(
        symbols,
        start_date=start_date,
        end_date=(pd.Timestamp.now().normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
    )
    first_dates = [pd.Timestamp(frame["date"].min()) for frame in frames_by_symbol.values()]
    first_trading_date = max(first_dates)

    close_prices = {}
    for symbol, frame in frames_by_symbol.items():
        row = frame.loc[frame["date"] == first_trading_date]
        if row.empty:
            raise ValueError(f"{symbol} has no row on the aligned first trading date {first_trading_date.date()}.")
        close_prices[symbol] = float(row.iloc[0]["close"])

    config = PortfolioEnvironmentConfig(symbols=tuple(symbols), initial_cash=initial_cash)
    execution = execute_target_weights(
        cash=initial_cash,
        shares_by_symbol={symbol: 0 for symbol in symbols},
        close_prices=close_prices,
        target_weights={symbol: 1.0 / len(symbols) for symbol in symbols},
        config=config,
    )

    holdings = [
        ProfileHoldingInput(
            symbol=symbol,
            average_cost=float(execution.symbol_results[symbol].execution_price),
            shares=int(execution.shares_after[symbol]),
        )
        for symbol in symbols
        if execution.shares_after[symbol] > 0
    ]
    return holdings, float(execution.cash_after)


if __name__ == "__main__":
    main()
