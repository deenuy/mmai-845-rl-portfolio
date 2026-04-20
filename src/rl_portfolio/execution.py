"""Execution and accounting utilities for single-asset and portfolio environments."""

from __future__ import annotations

from dataclasses import dataclass
import math

from .config import EnvironmentConfig, PortfolioEnvironmentConfig


@dataclass(frozen=True)
class ExecutionResult:
    """Result of a single rebalance operation."""

    executed: bool
    side: str
    shares_delta: int
    execution_price: float
    commission_paid: float
    slippage_paid: float
    trade_notional: float
    cash_after: float
    shares_after: int


@dataclass(frozen=True)
class PortfolioSymbolExecution:
    """Execution details for a single symbol inside a portfolio rebalance."""

    executed: bool
    side: str
    shares_delta: int
    execution_price: float
    commission_paid: float
    slippage_paid: float
    trade_notional: float
    shares_after: int


@dataclass(frozen=True)
class PortfolioExecutionResult:
    """Result of a multi-asset rebalance operation."""

    cash_after: float
    shares_after: dict[str, int]
    total_commission_paid: float
    total_slippage_paid: float
    total_trade_notional: float
    executed_symbols: list[str]
    symbol_results: dict[str, PortfolioSymbolExecution]


def accrue_cash(cash: float, daily_rate: float) -> float:
    """Apply one day of interest accrual to the cash balance."""

    return cash * (1.0 + daily_rate)


def execute_target_position(
    *,
    cash: float,
    shares: int,
    close_price: float,
    target_weight: float,
    config: EnvironmentConfig,
) -> ExecutionResult:
    """Rebalance a single-stock portfolio to a target weight using whole shares."""

    if close_price <= 0:
        raise ValueError("close_price must be positive.")

    bounded_weight = min(max(float(target_weight), 0.0), 1.0)
    slippage_rate = config.slippage_rate
    portfolio_value = cash + shares * close_price
    desired_stock_value = portfolio_value * bounded_weight
    current_stock_value = shares * close_price
    difference_value = desired_stock_value - current_stock_value

    if abs(difference_value) < config.min_trade_value:
        return ExecutionResult(
            executed=False,
            side="hold",
            shares_delta=0,
            execution_price=close_price,
            commission_paid=0.0,
            slippage_paid=0.0,
            trade_notional=0.0,
            cash_after=cash,
            shares_after=shares,
        )

    if difference_value > 0:
        return _execute_buy(
            cash=cash,
            shares=shares,
            close_price=close_price,
            desired_stock_value=desired_stock_value,
            config=config,
        )

    return _execute_sell(
        cash=cash,
        shares=shares,
        close_price=close_price,
        desired_stock_value=desired_stock_value,
        config=config,
    )


def execute_target_weights(
    *,
    cash: float,
    shares_by_symbol: dict[str, int],
    close_prices: dict[str, float],
    target_weights: dict[str, float],
    config: PortfolioEnvironmentConfig,
) -> PortfolioExecutionResult:
    """Rebalance a long-only whole-share portfolio toward target asset weights."""

    for symbol, price in close_prices.items():
        if price <= 0:
            raise ValueError(f"close price must be positive for {symbol}.")

    bounded_weights = {
        symbol: min(max(float(target_weights.get(symbol, 0.0)), 0.0), 1.0)
        for symbol in close_prices
    }
    cash_balance = float(cash)
    shares_after = {symbol: int(shares_by_symbol.get(symbol, 0)) for symbol in close_prices}
    portfolio_value = cash_balance + sum(shares_after[symbol] * close_prices[symbol] for symbol in close_prices)
    desired_values = {symbol: portfolio_value * bounded_weights[symbol] for symbol in close_prices}
    symbol_results: dict[str, PortfolioSymbolExecution] = {}
    total_commission = 0.0
    total_slippage = 0.0
    total_notional = 0.0
    executed_symbols: list[str] = []

    deltas = {
        symbol: desired_values[symbol] - (shares_after[symbol] * close_prices[symbol])
        for symbol in close_prices
    }

    sell_symbols = sorted((symbol for symbol, delta in deltas.items() if delta < 0.0), key=lambda item: deltas[item])
    buy_symbols = sorted(
        (symbol for symbol, delta in deltas.items() if delta > 0.0),
        key=lambda item: deltas[item],
        reverse=True,
    )

    for symbol in sell_symbols:
        result = _execute_portfolio_sell(
            cash=cash_balance,
            shares=shares_after[symbol],
            close_price=close_prices[symbol],
            desired_stock_value=desired_values[symbol],
            config=config,
        )
        symbol_results[symbol] = result
        if result.executed:
            cash_balance += (shares_after[symbol] - result.shares_after) * result.execution_price - result.commission_paid
            shares_after[symbol] = result.shares_after
            total_commission += result.commission_paid
            total_slippage += result.slippage_paid
            total_notional += result.trade_notional
            executed_symbols.append(symbol)

    for symbol in buy_symbols:
        result = _execute_portfolio_buy(
            cash=cash_balance,
            shares=shares_after[symbol],
            close_price=close_prices[symbol],
            desired_stock_value=desired_values[symbol],
            config=config,
        )
        symbol_results[symbol] = result
        if result.executed:
            cash_balance -= (result.shares_after - shares_after[symbol]) * result.execution_price + result.commission_paid
            shares_after[symbol] = result.shares_after
            total_commission += result.commission_paid
            total_slippage += result.slippage_paid
            total_notional += result.trade_notional
            executed_symbols.append(symbol)

    for symbol in close_prices:
        if symbol not in symbol_results:
            symbol_results[symbol] = PortfolioSymbolExecution(
                executed=False,
                side="hold",
                shares_delta=0,
                execution_price=close_prices[symbol],
                commission_paid=0.0,
                slippage_paid=0.0,
                trade_notional=0.0,
                shares_after=shares_after[symbol],
            )

    return PortfolioExecutionResult(
        cash_after=float(cash_balance),
        shares_after=shares_after,
        total_commission_paid=float(total_commission),
        total_slippage_paid=float(total_slippage),
        total_trade_notional=float(total_notional),
        executed_symbols=executed_symbols,
        symbol_results=symbol_results,
    )


def _execute_buy(
    *,
    cash: float,
    shares: int,
    close_price: float,
    desired_stock_value: float,
    config: EnvironmentConfig,
) -> ExecutionResult:
    slippage_rate = config.slippage_rate
    execution_price = close_price * (1.0 + slippage_rate)
    affordable_cash = cash - config.fixed_commission

    if affordable_cash <= 0:
        return ExecutionResult(False, "buy", 0, execution_price, 0.0, 0.0, 0.0, cash, shares)

    max_affordable_shares = int(max(math.floor(affordable_cash / execution_price), 0))
    desired_shares = int(max(math.floor(desired_stock_value / execution_price), 0))
    shares_to_buy = min(max_affordable_shares, max(desired_shares - shares, 0))

    if shares_to_buy <= 0:
        return ExecutionResult(False, "buy", 0, execution_price, 0.0, 0.0, 0.0, cash, shares)

    trade_notional = shares_to_buy * close_price
    if trade_notional < config.min_trade_value:
        return ExecutionResult(False, "buy", 0, execution_price, 0.0, 0.0, 0.0, cash, shares)

    slippage_paid = shares_to_buy * close_price * slippage_rate
    total_cost = shares_to_buy * execution_price + config.fixed_commission
    if total_cost > cash:
        shares_to_buy = int(max(math.floor((cash - config.fixed_commission) / execution_price), 0))
        trade_notional = shares_to_buy * close_price
        slippage_paid = shares_to_buy * close_price * slippage_rate
        total_cost = shares_to_buy * execution_price + config.fixed_commission

    if shares_to_buy <= 0 or trade_notional < config.min_trade_value or total_cost > cash:
        return ExecutionResult(False, "buy", 0, execution_price, 0.0, 0.0, 0.0, cash, shares)

    return ExecutionResult(
        executed=True,
        side="buy",
        shares_delta=shares_to_buy,
        execution_price=execution_price,
        commission_paid=config.fixed_commission,
        slippage_paid=slippage_paid,
        trade_notional=trade_notional,
        cash_after=cash - total_cost,
        shares_after=shares + shares_to_buy,
    )


def _execute_sell(
    *,
    cash: float,
    shares: int,
    close_price: float,
    desired_stock_value: float,
    config: EnvironmentConfig,
) -> ExecutionResult:
    slippage_rate = config.slippage_rate
    execution_price = close_price * (1.0 - slippage_rate)
    desired_shares = int(max(math.floor(desired_stock_value / close_price), 0))
    shares_to_sell = max(shares - desired_shares, 0)

    if shares_to_sell <= 0:
        return ExecutionResult(False, "sell", 0, execution_price, 0.0, 0.0, 0.0, cash, shares)

    trade_notional = shares_to_sell * close_price
    if trade_notional < config.min_trade_value:
        return ExecutionResult(False, "sell", 0, execution_price, 0.0, 0.0, 0.0, cash, shares)

    slippage_paid = shares_to_sell * close_price * slippage_rate
    cash_received = shares_to_sell * execution_price - config.fixed_commission
    if cash_received < 0:
        return ExecutionResult(False, "sell", 0, execution_price, 0.0, 0.0, 0.0, cash, shares)

    return ExecutionResult(
        executed=True,
        side="sell",
        shares_delta=-shares_to_sell,
        execution_price=execution_price,
        commission_paid=config.fixed_commission,
        slippage_paid=slippage_paid,
        trade_notional=trade_notional,
        cash_after=cash + cash_received,
        shares_after=shares - shares_to_sell,
    )


def _execute_portfolio_buy(
    *,
    cash: float,
    shares: int,
    close_price: float,
    desired_stock_value: float,
    config: PortfolioEnvironmentConfig,
) -> PortfolioSymbolExecution:
    execution_price = close_price * (1.0 + config.slippage_rate)
    affordable_cash = cash - config.fixed_commission
    if affordable_cash <= 0:
        return PortfolioSymbolExecution(False, "buy", 0, execution_price, 0.0, 0.0, 0.0, shares)

    max_affordable_shares = int(max(math.floor(affordable_cash / execution_price), 0))
    desired_shares = int(max(math.floor(desired_stock_value / close_price), 0))
    shares_to_buy = min(max_affordable_shares, max(desired_shares - shares, 0))

    if shares_to_buy <= 0:
        return PortfolioSymbolExecution(False, "buy", 0, execution_price, 0.0, 0.0, 0.0, shares)

    trade_notional = shares_to_buy * close_price
    if trade_notional < config.min_trade_value:
        return PortfolioSymbolExecution(False, "buy", 0, execution_price, 0.0, 0.0, 0.0, shares)

    slippage_paid = shares_to_buy * close_price * config.slippage_rate
    total_cost = shares_to_buy * execution_price + config.fixed_commission
    if total_cost > cash:
        shares_to_buy = int(max(math.floor((cash - config.fixed_commission) / execution_price), 0))
        trade_notional = shares_to_buy * close_price
        slippage_paid = shares_to_buy * close_price * config.slippage_rate
        total_cost = shares_to_buy * execution_price + config.fixed_commission

    if shares_to_buy <= 0 or trade_notional < config.min_trade_value or total_cost > cash:
        return PortfolioSymbolExecution(False, "buy", 0, execution_price, 0.0, 0.0, 0.0, shares)

    return PortfolioSymbolExecution(
        executed=True,
        side="buy",
        shares_delta=shares_to_buy,
        execution_price=execution_price,
        commission_paid=config.fixed_commission,
        slippage_paid=slippage_paid,
        trade_notional=trade_notional,
        shares_after=shares + shares_to_buy,
    )


def _execute_portfolio_sell(
    *,
    cash: float,
    shares: int,
    close_price: float,
    desired_stock_value: float,
    config: PortfolioEnvironmentConfig,
) -> PortfolioSymbolExecution:
    del cash
    execution_price = close_price * (1.0 - config.slippage_rate)
    desired_shares = int(max(math.floor(desired_stock_value / close_price), 0))
    shares_to_sell = max(shares - desired_shares, 0)

    if shares_to_sell <= 0:
        return PortfolioSymbolExecution(False, "sell", 0, execution_price, 0.0, 0.0, 0.0, shares)

    trade_notional = shares_to_sell * close_price
    if trade_notional < config.min_trade_value:
        return PortfolioSymbolExecution(False, "sell", 0, execution_price, 0.0, 0.0, 0.0, shares)

    slippage_paid = shares_to_sell * close_price * config.slippage_rate
    cash_received = shares_to_sell * execution_price - config.fixed_commission
    if cash_received < 0:
        return PortfolioSymbolExecution(False, "sell", 0, execution_price, 0.0, 0.0, 0.0, shares)

    return PortfolioSymbolExecution(
        executed=True,
        side="sell",
        shares_delta=-shares_to_sell,
        execution_price=execution_price,
        commission_paid=config.fixed_commission,
        slippage_paid=slippage_paid,
        trade_notional=trade_notional,
        shares_after=shares - shares_to_sell,
    )
