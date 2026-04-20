"""Run a minimal local dashboard for profile management and daily trade recommendations."""

from __future__ import annotations

import argparse
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import sys
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from rl_portfolio.paper_trading import CORE_SYMBOLS, EXTENDED_SYMBOLS, build_profile_recommendation, generate_policy_snapshot, resolve_policy_bundle
from rl_portfolio.profile_store import ProfileHoldingInput, create_profile, get_profile, initialize_profile_store, list_profiles
from rl_portfolio.profile_store import append_profile_log, get_profile_log, list_profile_logs, restore_profile_from_log, update_profile


DATABASE_PATH = ROOT / "artifacts" / "phase_04" / "product" / "profiles.db"
ROW_COUNT = 10
COMMISSION_PER_ORDER = 1.99


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local RL portfolio product dashboard.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind.")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind.")
    return parser.parse_args()


class ProductDashboardHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for profile CRUD and recommendation views."""

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        route = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)

        if route == "/":
            self._send_html(_render_home_page())
            return
        if route == "/profiles/new":
            self._send_html(_render_new_profile_page())
            return
        if route.startswith("/profiles/") and route.endswith("/logs"):
            try:
                profile_id = int(route.split("/")[2])
            except (IndexError, ValueError):
                self._send_html("<h1>Profile not found.</h1>", status=HTTPStatus.NOT_FOUND)
                return
            profile = get_profile(DATABASE_PATH, profile_id)
            if profile is None:
                self._send_html("<h1>Profile not found.</h1>", status=HTTPStatus.NOT_FOUND)
                return
            logs = list_profile_logs(DATABASE_PATH, profile_id)
            self._send_html(_render_logs_page(profile, logs))
            return
        if route.startswith("/profiles/") and "/logs/" in route:
            parts = route.split("/")
            try:
                profile_id = int(parts[2])
                log_id = int(parts[4])
            except (IndexError, ValueError):
                self._send_html("<h1>Log not found.</h1>", status=HTTPStatus.NOT_FOUND)
                return
            profile = get_profile(DATABASE_PATH, profile_id)
            log_entry = get_profile_log(DATABASE_PATH, log_id)
            if profile is None or log_entry is None or int(log_entry["profile_id"]) != profile_id:
                self._send_html("<h1>Log not found.</h1>", status=HTTPStatus.NOT_FOUND)
                return
            self._send_html(_render_log_detail_page(profile, log_entry))
            return
        if route.startswith("/profiles/") and route.endswith("/confirm"):
            try:
                profile_id = int(route.split("/")[2])
            except (IndexError, ValueError):
                self._send_html("<h1>Profile not found.</h1>", status=HTTPStatus.NOT_FOUND)
                return
            profile = get_profile(DATABASE_PATH, profile_id)
            if profile is None:
                self._send_html("<h1>Profile not found.</h1>", status=HTTPStatus.NOT_FOUND)
                return
            try:
                profile_symbols = [holding["symbol"] for holding in profile["holdings"]]
                bundle = resolve_policy_bundle(profile_symbols)
                policy_snapshot = generate_policy_snapshot(
                    symbols=tuple(bundle["symbols"]),
                    model_path=bundle["model_path"],
                    vecnormalize_path=bundle["vecnormalize_path"],
                )
                recommendation = build_profile_recommendation(profile=profile, policy_snapshot=policy_snapshot)
                self._send_html(_render_confirm_page(profile, recommendation))
            except Exception as exc:  # pragma: no cover
                self._send_html(f"<h1>Failed to build confirmation page.</h1><p>{escape(str(exc))}</p>", status=HTTPStatus.BAD_REQUEST)
            return
        if route.startswith("/profiles/") and route.endswith("/edit"):
            try:
                profile_id = int(route.split("/")[2])
            except (IndexError, ValueError):
                self._send_html("<h1>Profile not found.</h1>", status=HTTPStatus.NOT_FOUND)
                return

            profile = get_profile(DATABASE_PATH, profile_id)
            if profile is None:
                self._send_html("<h1>Profile not found.</h1>", status=HTTPStatus.NOT_FOUND)
                return
            self._send_html(_render_edit_profile_page(profile))
            return
        if route.startswith("/profiles/"):
            try:
                profile_id = int(route.split("/")[2])
            except (IndexError, ValueError):
                self._send_html("<h1>Profile not found.</h1>", status=HTTPStatus.NOT_FOUND)
                return

            profile = get_profile(DATABASE_PATH, profile_id)
            if profile is None:
                self._send_html("<h1>Profile not found.</h1>", status=HTTPStatus.NOT_FOUND)
                return

            recommendation = None
            error_message = None
            if query.get("run", ["1"])[0] == "1":
                try:
                    profile_symbols = [holding["symbol"] for holding in profile["holdings"]]
                    bundle = resolve_policy_bundle(profile_symbols)
                    policy_snapshot = generate_policy_snapshot(
                        symbols=tuple(bundle["symbols"]),
                        model_path=bundle["model_path"],
                        vecnormalize_path=bundle["vecnormalize_path"],
                    )
                    recommendation = build_profile_recommendation(profile=profile, policy_snapshot=policy_snapshot)
                except Exception as exc:  # pragma: no cover
                    error_message = f"{type(exc).__name__}: {exc}"

            self._send_html(_render_profile_page(profile, recommendation, error_message))
            return

        self._send_html("<h1>Page not found.</h1>", status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        route = parsed.path.rstrip("/") or "/"

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        form = parse_qs(body)

        if route == "/profiles":
            try:
                profile_name = form.get("profile_name", [""])[0].strip()
                cash = float(form.get("cash", ["0"])[0] or 0.0)
                holdings = _parse_holdings_from_form(form)
                profile_id = create_profile(
                    DATABASE_PATH,
                    name=profile_name,
                    cash=cash,
                    holdings=holdings,
                )
            except Exception as exc:
                self._send_html(_render_new_profile_page(error_message=str(exc), form_data=form), status=HTTPStatus.BAD_REQUEST)
                return

            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", f"/profiles/{profile_id}")
            self.end_headers()
            return

        if route.startswith("/profiles/") and route.endswith("/edit"):
            try:
                profile_id = int(route.split("/")[2])
                profile_name = form.get("profile_name", [""])[0].strip()
                cash = float(form.get("cash", ["0"])[0] or 0.0)
                holdings = _parse_holdings_from_form(form)
                update_profile(
                    DATABASE_PATH,
                    profile_id=profile_id,
                    name=profile_name,
                    cash=cash,
                    holdings=holdings,
                )
            except Exception as exc:
                profile = get_profile(DATABASE_PATH, int(route.split("/")[2]))
                self._send_html(
                    _render_edit_profile_page(profile, error_message=str(exc), form_data=form) if profile is not None else "<h1>Profile not found.</h1>",
                    status=HTTPStatus.BAD_REQUEST,
                )
                return

            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", f"/profiles/{profile_id}")
            self.end_headers()
            return

        if route.startswith("/profiles/") and route.endswith("/apply"):
            try:
                profile_id = int(route.split("/")[2])
                profile = get_profile(DATABASE_PATH, profile_id)
                if profile is None:
                    raise ValueError("Profile not found.")
                recommendation_date = form.get("recommendation_date", [""])[0].strip()
                executed_orders = _parse_orders_from_form(form)
                update_payload = _apply_orders_to_profile(profile, executed_orders)
                updated_holdings = update_payload["holdings"]
                update_profile(
                    DATABASE_PATH,
                    profile_id=profile_id,
                    name=str(profile["name"]),
                    cash=float(update_payload["cash_after"]),
                    holdings=updated_holdings,
                    log_action=False,
                )
                append_profile_log(
                    DATABASE_PATH,
                    profile_id=profile_id,
                    action_type="apply",
                    note=f"Executed recommendation for {recommendation_date or 'latest market date'}.",
                    snapshot={
                        "profile_id": profile_id,
                        "name": str(profile["name"]),
                        "cash": float(update_payload["cash_after"]),
                        "holdings": [
                            {
                                "symbol": holding.symbol,
                                "average_cost": float(holding.average_cost),
                                "shares": int(holding.shares),
                            }
                            for holding in updated_holdings
                        ],
                        "orders": update_payload["orders"],
                        "recommendation_date": recommendation_date,
                        "realized_pnl_delta": float(update_payload["realized_pnl_delta"]),
                    },
                )
            except Exception as exc:
                self._send_html(f"<h1>Failed to apply rebalance.</h1><p>{escape(str(exc))}</p>", status=HTTPStatus.BAD_REQUEST)
                return

            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", f"/profiles/{profile_id}?run=1")
            self.end_headers()
            return

        if route.startswith("/profiles/") and route.endswith("/rollback"):
            try:
                profile_id = int(route.split("/")[2])
                log_id = int(form.get("log_id", ["0"])[0])
                restore_profile_from_log(DATABASE_PATH, profile_id=profile_id, log_id=log_id)
            except Exception as exc:
                self._send_html(f"<h1>Failed to rollback profile.</h1><p>{escape(str(exc))}</p>", status=HTTPStatus.BAD_REQUEST)
                return

            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", f"/profiles/{profile_id}")
            self.end_headers()
            return

        self._send_html("<h1>Page not found.</h1>", status=HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return

    def _send_html(self, html: str, *, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def _parse_holdings_from_form(form: dict[str, list[str]]) -> list[ProfileHoldingInput]:
    holdings: list[ProfileHoldingInput] = []
    supported = set(EXTENDED_SYMBOLS)

    for index in range(ROW_COUNT):
        symbol = (form.get(f"symbol_{index}", [""])[0] or "").upper().strip()
        average_cost_text = (form.get(f"average_cost_{index}", [""])[0] or "").strip()
        shares_text = (form.get(f"shares_{index}", [""])[0] or "").strip()
        if not symbol and not average_cost_text and not shares_text:
            continue
        if symbol not in supported:
            raise ValueError(f"{symbol or 'Blank symbol'} is not supported by the current frozen model basket.")
        if not average_cost_text or not shares_text:
            raise ValueError(f"Please provide both average cost and shares for {symbol}.")

        average_cost = float(average_cost_text)
        shares = int(shares_text)
        if average_cost < 0:
            raise ValueError(f"Average cost cannot be negative for {symbol}.")
        if shares < 0:
            raise ValueError(f"Shares cannot be negative for {symbol}.")
        if shares == 0:
            continue
        holdings.append(ProfileHoldingInput(symbol=symbol, average_cost=average_cost, shares=shares))

    return holdings


def _parse_orders_from_form(form: dict[str, list[str]]) -> list[dict[str, object]]:
    orders: list[dict[str, object]] = []
    order_count = int(form.get("order_count", ["0"])[0] or 0)
    for index in range(order_count):
        symbol = (form.get(f"order_symbol_{index}", [""])[0] or "").upper().strip()
        side = (form.get(f"order_side_{index}", [""])[0] or "").lower().strip()
        shares = int(float(form.get(f"order_shares_{index}", ["0"])[0] or 0))
        execution_price = float(form.get(f"order_exec_price_{index}", ["0"])[0] or 0.0)
        if not symbol or side not in {"sell", "buy"}:
            continue
        if shares <= 0 or execution_price <= 0:
            continue
        orders.append(
            {
                "symbol": symbol,
                "side": side,
                "shares": shares,
                "execution_price": execution_price,
                "trade_notional": shares * execution_price,
            }
        )
    return orders


def _apply_orders_to_profile(profile: dict[str, object], orders: list[dict[str, object]]) -> dict[str, object]:
    holdings_map: dict[str, dict[str, float]] = {
        str(holding["symbol"]).upper().strip(): {
            "average_cost": float(holding["average_cost"]),
            "shares": int(holding["shares"]),
        }
        for holding in profile["holdings"]
    }
    cash = float(profile["cash"])
    realized_pnl_delta = 0.0
    executed_orders: list[dict[str, object]] = []

    sell_orders = [order for order in orders if order["side"] == "sell"]
    buy_orders = [order for order in orders if order["side"] == "buy"]

    for order in sell_orders:
        symbol = str(order["symbol"])
        shares = int(order["shares"])
        execution_price = float(order["execution_price"])
        position = holdings_map.get(symbol)
        if position is None or position["shares"] < shares:
            raise ValueError(f"Not enough shares to sell {shares} of {symbol}.")
        average_cost = float(position["average_cost"])
        proceeds = shares * execution_price
        realized_pnl = proceeds - (shares * average_cost) - COMMISSION_PER_ORDER
        cash += proceeds - COMMISSION_PER_ORDER
        remaining_shares = int(position["shares"]) - shares
        realized_pnl_delta += realized_pnl
        executed_orders.append(
            {
                "symbol": symbol,
                "side": "sell",
                "shares": shares,
                "execution_price": execution_price,
                "trade_notional": proceeds,
                "commission_paid": COMMISSION_PER_ORDER,
                "cash_effect": proceeds - COMMISSION_PER_ORDER,
                "realized_pnl": realized_pnl,
            }
        )
        if remaining_shares > 0:
            holdings_map[symbol] = {"average_cost": average_cost, "shares": remaining_shares}
        else:
            holdings_map.pop(symbol, None)

    for order in buy_orders:
        symbol = str(order["symbol"])
        shares = int(order["shares"])
        execution_price = float(order["execution_price"])
        total_cost = shares * execution_price + COMMISSION_PER_ORDER
        if cash + 1e-9 < total_cost:
            raise ValueError(f"Not enough cash to buy {shares} of {symbol}.")
        current = holdings_map.get(symbol, {"average_cost": 0.0, "shares": 0})
        current_shares = int(current["shares"])
        current_cost_basis = float(current["average_cost"]) * current_shares
        new_shares = current_shares + shares
        new_average_cost = (current_cost_basis + total_cost) / new_shares
        holdings_map[symbol] = {"average_cost": new_average_cost, "shares": new_shares}
        cash -= total_cost
        executed_orders.append(
            {
                "symbol": symbol,
                "side": "buy",
                "shares": shares,
                "execution_price": execution_price,
                "trade_notional": shares * execution_price,
                "commission_paid": COMMISSION_PER_ORDER,
                "cash_effect": -total_cost,
                "realized_pnl": 0.0,
            }
        )

    holdings = [
        ProfileHoldingInput(symbol=symbol, average_cost=float(values["average_cost"]), shares=int(values["shares"]))
        for symbol, values in sorted(holdings_map.items())
        if int(values["shares"]) > 0
    ]
    return {
        "cash_after": cash,
        "holdings": holdings,
        "orders": {
            "sell_first": [order for order in executed_orders if order["side"] == "sell"],
            "buy_second": [order for order in executed_orders if order["side"] == "buy"],
        },
        "realized_pnl_delta": realized_pnl_delta,
    }


def _render_home_page() -> str:
    profiles = list_profiles(DATABASE_PATH)
    rows = "".join(
        f"""
        <tr>
          <td>{profile['id']}</td>
          <td><a href="/profiles/{profile['id']}">{escape(str(profile['name']))}</a></td>
          <td>{float(profile['cash']):.2f}</td>
          <td>{int(profile['holding_count'])}</td>
          <td>{escape(str(profile['updated_at']))}</td>
        </tr>
        """
        for profile in profiles
    ) or "<tr><td colspan='5'>No profiles yet. Create the first one below.</td></tr>"

    return _page_shell(
        "Portfolio Profiles",
        f"""
        <div class="hero">
          <h1>Portfolio Profiles</h1>
          <p>Manage current holdings profiles, inspect profile-level dashboards, and generate today’s sell-first / buy-second trade instructions.</p>
          <p><a class="button" href="/profiles/new">Create New Profile</a></p>
        </div>
        <section class="card">
          <h2>Saved Profiles</h2>
          <table>
            <thead>
              <tr><th>ID</th><th>Name</th><th>Cash</th><th>Holding Rows</th><th>Updated</th></tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
          <p class="muted">Current supported strategy baskets: core ({", ".join(CORE_SYMBOLS)}) and extended ({", ".join(EXTENDED_SYMBOLS)})</p>
        </section>
        """,
    )


def _render_new_profile_page(
    *,
    error_message: str | None = None,
    form_data: dict[str, list[str]] | None = None,
) -> str:
    form_data = form_data or {}
    row_html = []
    for index in range(ROW_COUNT):
        row_html.append(
            f"""
            <tr>
              <td><input name="symbol_{index}" value="{escape((form_data.get(f'symbol_{index}', [''])[0] or '').upper())}" placeholder="RY"></td>
              <td><input name="average_cost_{index}" value="{escape(form_data.get(f'average_cost_{index}', [''])[0])}" placeholder="170.50"></td>
              <td><input name="shares_{index}" value="{escape(form_data.get(f'shares_{index}', [''])[0])}" placeholder="100"></td>
            </tr>
            """
        )

    error_block = f"<div class='error'>{escape(error_message)}</div>" if error_message else ""
    return _page_shell(
        "Create Profile",
        f"""
        <div class="hero">
          <h1>Create Portfolio Profile</h1>
          <p>Input the holdings you currently own. The app will save them to SQLite and later compare them against today’s model target weights.</p>
        </div>
        {error_block}
        <form method="post" action="/profiles" class="card">
          <label>Profile name</label>
          <input name="profile_name" value="{escape(form_data.get('profile_name', [''])[0])}" placeholder="Main Account">
          <label>Cash available</label>
          <input name="cash" value="{escape(form_data.get('cash', ['0'])[0])}" placeholder="0">
          <h2>Holdings</h2>
          <table>
            <thead>
              <tr><th>Symbol</th><th>Average Cost</th><th>Shares</th></tr>
            </thead>
            <tbody>{''.join(row_html)}</tbody>
          </table>
          <p class="muted">Supported symbols right now: {", ".join(EXTENDED_SYMBOLS)}</p>
          <div class="actions">
            <button class="button" type="submit">Save Profile</button>
            <a class="button secondary" href="/">Back</a>
          </div>
        </form>
        """,
    )


def _render_profile_page(
    profile: dict[str, object],
    recommendation: dict[str, object] | None,
    error_message: str | None,
) -> str:
    holding_rows = "".join(
        f"""
        <tr>
          <td>{escape(str(holding['symbol']))}</td>
          <td>{int(holding['shares'])}</td>
          <td>{float(holding['average_cost']):.2f}</td>
        </tr>
        """
        for holding in profile["holdings"]
    ) or "<tr><td colspan='3'>No holdings saved.</td></tr>"

    recommendation_block = _render_recommendation_block(recommendation, error_message)
    return _page_shell(
        f"Profile {profile['name']}",
        f"""
        <div class="hero">
          <h1>{escape(str(profile['name']))}</h1>
          <p>Saved holdings profile. We can reuse this profile to generate today’s trade ticket whenever needed.</p>
          <div class="actions">
            <a class="button" href="/profiles/{profile['id']}?run=1">Refresh Today&apos;s Recommendation</a>
            <a class="button secondary" href="/profiles/{profile['id']}/edit">Edit Profile</a>
            <a class="button secondary" href="/profiles/{profile['id']}/logs">View Operation History</a>
            <a class="button secondary" href="/">Back to Profiles</a>
          </div>
        </div>
        <section class="grid">
          <div class="card">
            <h2>Profile Snapshot</h2>
            <p><strong>Cash:</strong> {float(profile['cash']):.2f}</p>
            <p><strong>Created:</strong> {escape(str(profile['created_at']))}</p>
            <p><strong>Updated:</strong> {escape(str(profile['updated_at']))}</p>
          </div>
          <div class="card">
            <h2>Supported Universe</h2>
            <p>Core: {", ".join(CORE_SYMBOLS)}</p>
            <p>Extended: {", ".join(EXTENDED_SYMBOLS)}</p>
            <p class="muted">The app auto-selects the frozen core or extended model based on the profile symbols you entered.</p>
          </div>
        </section>
        <section class="card">
          <h2>Saved Holdings</h2>
          <table>
            <thead><tr><th>Symbol</th><th>Shares</th><th>Average Cost</th></tr></thead>
            <tbody>{holding_rows}</tbody>
          </table>
        </section>
        {recommendation_block}
        """,
    )


def _render_recommendation_block(
    recommendation: dict[str, object] | None,
    error_message: str | None,
) -> str:
    if error_message:
        return f"<section class='card'><h2>Today&apos;s Recommendation</h2><div class='error'>{escape(error_message)}</div></section>"
    if recommendation is None:
        return "<section class='card'><h2>Today&apos;s Recommendation</h2><p class='muted'>Run the model to see today&apos;s dashboard.</p></section>"

    dashboard_rows = "".join(
        f"""
        <tr>
          <td>{row['symbol']}</td>
          <td>{int(row['shares'])}</td>
          <td>{float(row['average_cost']):.2f}</td>
          <td>{float(row['latest_price']):.2f}</td>
          <td>{float(row['market_value']):.2f}</td>
          <td>{float(row['unrealized_pnl']):.2f}</td>
          <td>{float(row['unrealized_pnl_pct']):.2%}</td>
          <td>{float(row['current_weight']):.4f}</td>
          <td>{float(row['target_weight']):.4f}</td>
          <td>{int(row['shares_delta'])}</td>
        </tr>
        """
        for row in recommendation["dashboard_rows"]
    )
    unsupported_rows = "".join(
        f"<tr><td>{row['symbol']}</td><td>{int(row['shares'])}</td><td>{float(row['average_cost']):.2f}</td><td>{row['reason']}</td></tr>"
        for row in recommendation["unsupported_rows"]
    )
    sell_rows = "".join(
        f"<tr><td>{item['symbol']}</td><td>{int(abs(item['shares_delta']))}</td><td>{float(item['trade_notional']):.2f}</td><td>{float(item['execution_price']):.2f}</td></tr>"
        for item in recommendation["trades"]["sell_first"]
    ) or "<tr><td colspan='4'>No sell orders.</td></tr>"
    buy_rows = "".join(
        f"<tr><td>{item['symbol']}</td><td>{int(item['shares_delta'])}</td><td>{float(item['trade_notional']):.2f}</td><td>{float(item['execution_price']):.2f}</td></tr>"
        for item in recommendation["trades"]["buy_second"]
    ) or "<tr><td colspan='4'>No buy orders.</td></tr>"

    unsupported_block = (
        f"""
        <section class="card">
          <h2>Unsupported Holdings</h2>
          <table>
            <thead><tr><th>Symbol</th><th>Shares</th><th>Average Cost</th><th>Note</th></tr></thead>
            <tbody>{unsupported_rows}</tbody>
          </table>
        </section>
        """
        if recommendation["unsupported_rows"]
        else ""
    )

    return f"""
    <section class="grid">
      <div class="card">
        <h2>Today&apos;s Strategy Snapshot</h2>
        <p><strong>Generated at:</strong> {escape(str(recommendation['generated_at']))}</p>
        <p><strong>Assumed run time:</strong> {escape(str(recommendation['assumed_run_time']))}</p>
        <p><strong>Latest market date:</strong> {escape(str(recommendation['latest_market_date']))}</p>
        <p><strong>Strategy simulation start:</strong> {escape(str(recommendation['simulation_start']))}</p>
        <p><strong>Core symbol:</strong> {escape(str(recommendation['core_symbol'] or 'None'))}</p>
        <p><strong>Review step:</strong> {"Yes" if recommendation['review_step'] else "No"}</p>
      </div>
      <div class="card">
        <h2>Portfolio Summary</h2>
        <p><strong>Current portfolio value:</strong> {float(recommendation['portfolio_market_value']):.2f}</p>
        <p><strong>Current cash:</strong> {float(recommendation['cash']):.2f}</p>
        <p><strong>Cash after proposed rebalance:</strong> {float(recommendation['cash_after_rebalance']):.2f}</p>
        <p><strong>Current cash weight:</strong> {float(recommendation['current_cash_weight']):.4f}</p>
        <p><strong>Strategy cash weight:</strong> {float(recommendation['strategy_cash_weight']):.4f}</p>
        <p><strong>Total unrealized P&amp;L:</strong> {float(recommendation['total_unrealized_pnl']):.2f}</p>
      </div>
    </section>
    <section class="card">
      <h2>Today&apos;s Order Ticket</h2>
      <div class="actions">
        <a class="button" href="/profiles/{recommendation['profile_id']}/confirm">Review And Confirm Rebalance</a>
      </div>
      <div class="grid">
        <div>
          <h3>Sell First</h3>
          <table>
            <thead><tr><th>Symbol</th><th>Shares</th><th>Amount</th><th>Exec Price</th></tr></thead>
            <tbody>{sell_rows}</tbody>
          </table>
        </div>
        <div>
          <h3>Buy Second</h3>
          <table>
            <thead><tr><th>Symbol</th><th>Shares</th><th>Amount</th><th>Exec Price</th></tr></thead>
            <tbody>{buy_rows}</tbody>
          </table>
        </div>
      </div>
    </section>
    <section class="card">
      <h2>Holdings Dashboard</h2>
      <table>
        <thead>
          <tr><th>Symbol</th><th>Shares</th><th>Avg Cost</th><th>Latest</th><th>Market Value</th><th>Unrealized P&amp;L</th><th>Unrealized P&amp;L %</th><th>Current Weight</th><th>Target Weight</th><th>Shares Delta</th></tr>
        </thead>
        <tbody>{dashboard_rows}</tbody>
      </table>
    </section>
    {unsupported_block}
    """


def _render_confirm_page(profile: dict[str, object], recommendation: dict[str, object]) -> str:
    sell_order_rows: list[str] = []
    buy_order_rows: list[str] = []
    order_index = 0
    for side, items in (("sell", recommendation["trades"]["sell_first"]), ("buy", recommendation["trades"]["buy_second"])):
        for item in items:
            shares = int(abs(item["shares_delta"])) if side == "sell" else int(item["shares_delta"])
            row_html = (
                f"""
                <tr class="order-row order-row-{escape(side)}">
                  <td>{escape(side.title())}</td>
                  <td>{escape(item['symbol'])}</td>
                  <td>
                    <input type="hidden" name="order_side_{order_index}" value="{escape(side)}">
                    <input type="hidden" name="order_symbol_{order_index}" value="{escape(item['symbol'])}">
                    <input name="order_shares_{order_index}" value="{shares}" type="number" min="0" step="1" oninput="updateAmount({order_index})">
                  </td>
                  <td><input name="order_exec_price_{order_index}" value="{float(item['execution_price']):.4f}" type="number" min="0" step="0.0001" oninput="updateAmount({order_index})"></td>
                  <td><span id="order_amount_{order_index}">{float(item['trade_notional']):.2f}</span></td>
                </tr>
                """
            )
            if side == "sell":
                sell_order_rows.append(row_html)
            else:
                buy_order_rows.append(row_html)
            order_index += 1
    sell_table = "".join(sell_order_rows) or "<tr><td colspan='5'>No sell orders for today.</td></tr>"
    buy_table = "".join(buy_order_rows) or "<tr><td colspan='5'>No buy orders for today.</td></tr>"
    return _page_shell(
        f"Confirm Rebalance for {profile['name']}",
        f"""
        <div class="hero">
          <h1>Confirm Rebalance</h1>
          <p>Review the sell-first and buy-second orders below. When you confirm, the profile will be updated to the post-trade holdings and cash state.</p>
        </div>
        <section class="grid">
          <div class="card">
            <h2>Strategy Snapshot</h2>
            <p><strong>Latest market date:</strong> {escape(str(recommendation['latest_market_date']))}</p>
            <p><strong>Core symbol:</strong> {escape(str(recommendation['core_symbol'] or 'None'))}</p>
            <p><strong>Cash after rebalance:</strong> {float(recommendation['cash_after_rebalance']):.2f}</p>
          </div>
          <div class="card">
            <h2>What Happens On Confirm</h2>
            <p>The selected profile will be updated with the post-trade shares, post-trade cash, and a new apply log entry.</p>
          </div>
        </section>
        <section class="card">
          <h2>Editable Order Ticket</h2>
          <p class="muted">You can edit shares and execution price before confirming. Amount is recalculated automatically.</p>
          <form method="post" action="/profiles/{profile['id']}/apply" onsubmit="return confirm('Apply this rebalance to the saved profile?');">
              <input type="hidden" name="recommendation_date" value="{escape(str(recommendation['latest_market_date']))}">
              <input type="hidden" name="order_count" value="{order_index}">
              <div class="grid">
                <div class="card subcard sell-card">
                  <h3>Sell First</h3>
                  <table>
                    <thead><tr><th>Side</th><th>Symbol</th><th>Shares</th><th>Exec Price</th><th>Amount</th></tr></thead>
                    <tbody>{sell_table}</tbody>
                  </table>
                </div>
                <div class="card subcard buy-card">
                  <h3>Buy Second</h3>
                  <table>
                    <thead><tr><th>Side</th><th>Symbol</th><th>Shares</th><th>Exec Price</th><th>Amount</th></tr></thead>
                    <tbody>{buy_table}</tbody>
                  </table>
                </div>
              </div>
              <div class="actions">
                <button class="button" type="submit">Confirm Rebalance Complete</button>
              </div>
          </form>
          <div class="actions">
            <a class="button secondary" href="/profiles/{profile['id']}?run=1">Back</a>
          </div>
        </section>
        <script>
          function updateAmount(index) {{
            const shares = Number(document.querySelector(`[name="order_shares_${{index}}"]`)?.value || 0);
            const price = Number(document.querySelector(`[name="order_exec_price_${{index}}"]`)?.value || 0);
            const amount = shares * price;
            const target = document.getElementById(`order_amount_${{index}}`);
            if (target) {{
              target.textContent = amount.toFixed(2);
            }}
          }}
        </script>
        """,
    )


def _render_edit_profile_page(
    profile: dict[str, object] | None,
    error_message: str | None = None,
    form_data: dict[str, list[str]] | None = None,
) -> str:
    if profile is None:
        return _page_shell("Profile Not Found", "<h1>Profile not found.</h1>")

    form_data = form_data or {}
    holdings_by_symbol = {holding["symbol"]: holding for holding in profile["holdings"]}
    symbols = list(EXTENDED_SYMBOLS)
    extra_symbols = [symbol for symbol in holdings_by_symbol if symbol not in symbols]
    symbols.extend(extra_symbols)

    row_html: list[str] = []
    row_symbols = symbols[:ROW_COUNT]
    for index, symbol in enumerate(row_symbols):
        holding = holdings_by_symbol.get(symbol, {})
        row_html.append(
            f"""
            <tr>
              <td><input name="symbol_{index}" value="{escape((form_data.get(f'symbol_{index}', [symbol])[0] or symbol).upper())}"></td>
              <td><input name="average_cost_{index}" value="{escape(form_data.get(f'average_cost_{index}', [str(holding.get('average_cost', ''))])[0])}"></td>
              <td><input name="shares_{index}" value="{escape(form_data.get(f'shares_{index}', [str(holding.get('shares', ''))])[0])}"></td>
            </tr>
            """
        )
    for index in range(len(row_symbols), ROW_COUNT):
        row_html.append(
            f"""
            <tr>
              <td><input name="symbol_{index}" value="{escape((form_data.get(f'symbol_{index}', [''])[0] or '').upper())}" placeholder="NVDA"></td>
              <td><input name="average_cost_{index}" value="{escape(form_data.get(f'average_cost_{index}', [''])[0])}" placeholder="150.00"></td>
              <td><input name="shares_{index}" value="{escape(form_data.get(f'shares_{index}', [''])[0])}" placeholder="25"></td>
            </tr>
            """
        )

    error_block = f"<div class='error'>{escape(error_message)}</div>" if error_message else ""
    return _page_shell(
        f"Edit {profile['name']}",
        f"""
        <div class="hero">
          <h1>Edit Profile</h1>
          <p>Manually adjust current holdings, add a new supported stock, or update current cash.</p>
        </div>
        {error_block}
        <form method="post" action="/profiles/{profile['id']}/edit" class="card">
          <label>Profile name</label>
          <input name="profile_name" value="{escape(form_data.get('profile_name', [str(profile['name'])])[0])}">
          <label>Cash available</label>
          <input name="cash" value="{escape(form_data.get('cash', [str(profile['cash'])])[0])}">
          <h2>Edit Holdings</h2>
          <table>
            <thead><tr><th>Symbol</th><th>Average Cost</th><th>Shares</th></tr></thead>
            <tbody>{''.join(row_html)}</tbody>
          </table>
          <div class="actions">
            <button class="button" type="submit">Save Changes</button>
            <a class="button secondary" href="/profiles/{profile['id']}">Cancel</a>
          </div>
        </form>
        """,
    )


def _render_logs_page(profile: dict[str, object], logs: list[dict[str, object]]) -> str:
    log_rows = "".join(
        f"""
        <tr>
          <td>{int(log['id'])}</td>
          <td>{escape(str(log['created_at']))}</td>
          <td>{escape(str(log['action_type']))}</td>
          <td>{escape(str(log['note']))}</td>
          <td><a class="button secondary" href="/profiles/{profile['id']}/logs/{int(log['id'])}">View</a></td>
          <td>
            <form method="post" action="/profiles/{profile['id']}/rollback" onsubmit="return confirm('Restore this profile snapshot?');">
              <input type="hidden" name="log_id" value="{int(log['id'])}">
              <button class="button secondary" type="submit">Rollback</button>
            </form>
          </td>
        </tr>
        """
        for log in logs
    ) or "<tr><td colspan='6'>No operation logs yet.</td></tr>"
    return _page_shell(
        f"Operation History: {profile['name']}",
        f"""
        <div class="hero">
          <h1>Operation History</h1>
          <p>Review edits, executed recommendations, resets, and rollbacks for this profile.</p>
          <div class="actions">
            <a class="button secondary" href="/profiles/{profile['id']}">Back to Profile</a>
          </div>
        </div>
        <section class="card">
          <h2>Profile Log</h2>
          <table>
            <thead><tr><th>Log ID</th><th>Time</th><th>Action</th><th>Note</th><th>View</th><th>Rollback</th></tr></thead>
            <tbody>{log_rows}</tbody>
          </table>
        </section>
        """,
    )


def _render_log_detail_page(profile: dict[str, object], log_entry: dict[str, object]) -> str:
    snapshot = log_entry.get("snapshot", {})
    holdings = snapshot.get("holdings", [])
    orders = snapshot.get("orders", {})
    sell_orders = orders.get("sell_first", []) if isinstance(orders, dict) else []
    buy_orders = orders.get("buy_second", []) if isinstance(orders, dict) else []
    holdings_rows = "".join(
        f"<tr><td>{escape(str(row['symbol']))}</td><td>{int(row['shares'])}</td><td>{float(row['average_cost']):.2f}</td></tr>"
        for row in holdings
    ) or "<tr><td colspan='3'>No holdings stored in this snapshot.</td></tr>"
    sell_rows = "".join(
        f"<tr><td>{escape(str(row['symbol']))}</td><td>{int(row['shares'])}</td><td>{float(row['execution_price']):.4f}</td><td>{float(row['trade_notional']):.2f}</td></tr>"
        for row in sell_orders
    ) or "<tr><td colspan='4'>No sell orders.</td></tr>"
    buy_rows = "".join(
        f"<tr><td>{escape(str(row['symbol']))}</td><td>{int(row['shares'])}</td><td>{float(row['execution_price']):.4f}</td><td>{float(row['trade_notional']):.2f}</td></tr>"
        for row in buy_orders
    ) or "<tr><td colspan='4'>No buy orders.</td></tr>"
    return _page_shell(
        f"Log {log_entry['id']}",
        f"""
        <div class="hero">
          <h1>Log Detail</h1>
          <p>{escape(str(log_entry['note']))}</p>
          <div class="actions">
            <a class="button secondary" href="/profiles/{profile['id']}/logs">Back to History</a>
            <a class="button secondary" href="/profiles/{profile['id']}">Back to Profile</a>
          </div>
        </div>
        <section class="grid">
          <div class="card">
            <h2>Metadata</h2>
            <p><strong>Action:</strong> {escape(str(log_entry['action_type']))}</p>
            <p><strong>Time:</strong> {escape(str(log_entry['created_at']))}</p>
            <p><strong>Recommendation date:</strong> {escape(str(snapshot.get('recommendation_date', 'N/A')))}</p>
            <p><strong>Cash:</strong> {float(snapshot.get('cash', 0.0)):.2f}</p>
            <p><strong>Realized P&amp;L delta:</strong> {float(snapshot.get('realized_pnl_delta', 0.0)):.2f}</p>
          </div>
          <div class="card">
            <h2>Snapshot Holdings</h2>
            <table>
              <thead><tr><th>Symbol</th><th>Shares</th><th>Average Cost</th></tr></thead>
              <tbody>{holdings_rows}</tbody>
            </table>
          </div>
        </section>
        <section class="grid">
          <div class="card">
            <h2>Executed Sell Orders</h2>
            <table>
              <thead><tr><th>Symbol</th><th>Shares</th><th>Exec Price</th><th>Amount</th></tr></thead>
              <tbody>{sell_rows}</tbody>
            </table>
          </div>
          <div class="card">
            <h2>Executed Buy Orders</h2>
            <table>
              <thead><tr><th>Symbol</th><th>Shares</th><th>Exec Price</th><th>Amount</th></tr></thead>
              <tbody>{buy_rows}</tbody>
            </table>
          </div>
        </section>
        """,
    )


def _page_shell(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: Georgia, serif; margin: 2rem auto; max-width: 1180px; color: #1f2f3a; background: #f7f6f1; line-height: 1.6; }}
    h1, h2, h3 {{ color: #153243; }}
    .hero {{ margin-bottom: 1.5rem; }}
    .card {{ background: #fff; border: 1px solid #d7d0c3; border-radius: 14px; padding: 1rem 1.25rem; box-shadow: 0 4px 14px rgba(0,0,0,0.05); margin-bottom: 1.25rem; }}
    .subcard {{ margin-bottom: 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 0.75rem; }}
    th, td {{ border-bottom: 1px solid #e7e0d3; padding: 0.65rem; text-align: left; vertical-align: top; }}
    th {{ background: #f0ece2; }}
    .button {{ display: inline-block; padding: 0.7rem 1rem; border-radius: 999px; background: #153243; color: #fff; text-decoration: none; border: none; cursor: pointer; }}
    .button.secondary {{ background: #d9e6eb; color: #153243; }}
    .sell-card {{ border-color: #e5b8b0; background: #fff6f4; }}
    .buy-card {{ border-color: #b9d6b3; background: #f5fbf3; }}
    .order-row-sell td:first-child {{ color: #a23b2a; font-weight: 700; }}
    .order-row-buy td:first-child {{ color: #2f6b2f; font-weight: 700; }}
    .actions {{ display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 1rem; }}
    input {{ width: 100%; padding: 0.65rem; margin-bottom: 0.75rem; border: 1px solid #d7d0c3; border-radius: 10px; box-sizing: border-box; }}
    label {{ display: block; font-weight: 700; margin-top: 0.4rem; }}
    .muted {{ color: #5d6d74; }}
    .error {{ background: #fff0f0; border: 1px solid #e0b4b4; color: #8b1e1e; border-radius: 12px; padding: 0.9rem 1rem; margin-bottom: 1rem; }}
  </style>
</head>
<body>
{body}
</body>
</html>"""


def main() -> None:
    args = parse_args()
    initialize_profile_store(DATABASE_PATH)
    server = ThreadingHTTPServer((args.host, args.port), ProductDashboardHandler)
    print(f"Portfolio dashboard running at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
