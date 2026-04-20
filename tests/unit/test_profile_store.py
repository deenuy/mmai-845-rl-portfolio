"""Tests for local profile storage and profile-side recommendation assembly."""

from __future__ import annotations

import sqlite3

from scripts.run_product_dashboard import _apply_orders_to_profile
from rl_portfolio.paper_trading import build_profile_recommendation, resolve_policy_bundle
from rl_portfolio.profile_store import (
    ProfileHoldingInput,
    append_profile_log,
    create_profile,
    get_profile_log,
    get_profile,
    initialize_profile_store,
    list_profile_logs,
    list_profiles,
    restore_profile_from_log,
    update_profile,
)


def test_profile_store_round_trip() -> None:
    database_path = "file:test_profile_store?mode=memory&cache=shared"
    keeper = sqlite3.connect(database_path, uri=True)
    try:
        database_path = initialize_profile_store(database_path)
        profile_id = create_profile(
            database_path,
            name="Main Account",
            cash=1234.5,
            holdings=[
                ProfileHoldingInput(symbol="RY", average_cost=100.0, shares=10),
                ProfileHoldingInput(symbol="MSFT", average_cost=200.0, shares=5),
            ],
        )

        listing = list_profiles(database_path)
        assert len(listing) == 1
        assert listing[0]["id"] == profile_id
        assert listing[0]["holding_count"] == 2

        profile = get_profile(database_path, profile_id)
        assert profile is not None
        assert profile["name"] == "Main Account"
        assert profile["cash"] == 1234.5
        assert [holding["symbol"] for holding in profile["holdings"]] == ["MSFT", "RY"]
    finally:
        keeper.close()


def test_build_profile_recommendation_uses_profile_holdings() -> None:
    profile = {
        "id": 1,
        "name": "Main",
        "cash": 500.0,
        "holdings": [
            {"symbol": "RY", "average_cost": 100.0, "shares": 10},
            {"symbol": "MSFT", "average_cost": 250.0, "shares": 2},
        ],
    }
    policy_snapshot = {
        "generated_at": "2026-04-13T12:00:00",
        "assumed_run_time": "2026-04-13 12:00 America/Toronto",
        "latest_market_date": "2026-04-13",
        "simulation_start": "2026-01-01",
        "core_symbol": "XOM",
        "review_step": False,
        "symbols": ["RY", "MSFT", "RKLB", "XOM", "PG"],
        "prices": {"RY": 120.0, "MSFT": 300.0, "RKLB": 40.0, "XOM": 150.0, "PG": 140.0},
        "target_weights": {"RY": 0.10, "MSFT": 0.10, "RKLB": 0.10, "XOM": 0.50, "PG": 0.10},
        "strategy_cash_weight": 0.10,
    }

    result = build_profile_recommendation(profile=profile, policy_snapshot=policy_snapshot)

    assert result["profile_name"] == "Main"
    assert result["core_symbol"] == "XOM"
    assert len(result["dashboard_rows"]) == 5
    assert result["portfolio_market_value"] > 0
    assert "buy_second" in result["trades"]


def test_resolve_policy_bundle_matches_universe() -> None:
    core_bundle = resolve_policy_bundle(["RY", "MSFT"])
    extended_bundle = resolve_policy_bundle(["RY", "NVDA", "FCX"])

    assert core_bundle["bundle_name"] == "core"
    assert extended_bundle["bundle_name"] == "extended"


def test_update_profile_replaces_holdings() -> None:
    database_path = "file:test_update_profile?mode=memory&cache=shared"
    keeper = sqlite3.connect(database_path, uri=True)
    try:
        initialize_profile_store(database_path)
        profile_id = create_profile(
            database_path,
            name="Editable",
            cash=100.0,
            holdings=[ProfileHoldingInput(symbol="RY", average_cost=100.0, shares=1)],
        )

        update_profile(
            database_path,
            profile_id=profile_id,
            name="Edited",
            cash=250.0,
            holdings=[
                ProfileHoldingInput(symbol="MSFT", average_cost=300.0, shares=2),
                ProfileHoldingInput(symbol="XOM", average_cost=150.0, shares=3),
            ],
        )

        profile = get_profile(database_path, profile_id)
        assert profile is not None
        assert profile["name"] == "Edited"
        assert profile["cash"] == 250.0
        assert [holding["symbol"] for holding in profile["holdings"]] == ["MSFT", "XOM"]
    finally:
        keeper.close()


def test_profile_logs_round_trip_and_restore() -> None:
    database_path = "file:test_profile_logs?mode=memory&cache=shared"
    keeper = sqlite3.connect(database_path, uri=True)
    try:
        initialize_profile_store(database_path)
        profile_id = create_profile(
            database_path,
            name="Loggable",
            cash=100.0,
            holdings=[ProfileHoldingInput(symbol="RY", average_cost=100.0, shares=1)],
        )
        update_profile(
            database_path,
            profile_id=profile_id,
            name="Loggable Updated",
            cash=200.0,
            holdings=[ProfileHoldingInput(symbol="MSFT", average_cost=200.0, shares=2)],
        )
        append_profile_log(
            database_path,
            profile_id=profile_id,
            action_type="apply",
            note="Executed recommendation for 2026-04-13.",
            snapshot={
                "profile_id": profile_id,
                "name": "Loggable Updated",
                "cash": 150.0,
                "holdings": [{"symbol": "MSFT", "average_cost": 210.0, "shares": 2}],
                "orders": {"sell_first": [], "buy_second": []},
                "recommendation_date": "2026-04-13",
            },
        )

        logs = list_profile_logs(database_path, profile_id)
        assert len(logs) == 3
        assert logs[0]["action_type"] == "apply"
        assert logs[0]["snapshot"]["recommendation_date"] == "2026-04-13"

        edit_log = next(log for log in logs if log["action_type"] == "edit")
        fetched = get_profile_log(database_path, int(edit_log["id"]))
        assert fetched is not None
        assert fetched["snapshot"]["name"] == "Loggable Updated"

        restore_profile_from_log(database_path, profile_id=profile_id, log_id=int(edit_log["id"]))
        restored = get_profile(database_path, profile_id)
        assert restored is not None
        assert restored["name"] == "Loggable Updated"
        assert restored["cash"] == 200.0
        assert [holding["symbol"] for holding in restored["holdings"]] == ["MSFT"]
    finally:
        keeper.close()


def test_apply_orders_to_profile_updates_cash_and_cost_basis() -> None:
    profile = {
        "id": 1,
        "name": "Apply Test",
        "cash": 1000.0,
        "holdings": [
            {"symbol": "MSFT", "average_cost": 200.0, "shares": 10},
            {"symbol": "XOM", "average_cost": 100.0, "shares": 5},
        ],
    }
    result = _apply_orders_to_profile(
        profile,
        [
            {"symbol": "MSFT", "side": "sell", "shares": 4, "execution_price": 250.0, "trade_notional": 1000.0},
            {"symbol": "XOM", "side": "buy", "shares": 3, "execution_price": 120.0, "trade_notional": 360.0},
        ],
    )

    holdings = {holding.symbol: holding for holding in result["holdings"]}
    assert round(result["cash_after"], 2) == 1636.02
    assert holdings["MSFT"].shares == 6
    assert holdings["MSFT"].average_cost == 200.0
    assert holdings["XOM"].shares == 8
    assert round(holdings["XOM"].average_cost, 4) == 107.7488
    assert round(result["realized_pnl_delta"], 2) == 198.01
