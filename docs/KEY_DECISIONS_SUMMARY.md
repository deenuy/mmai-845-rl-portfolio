# Key Decisions Summary

This file is the shortest decision summary for teammates who do not want to read the full roadmap history first.

## Scope

- research started with U.S. equities only
- base currency fixed to `USD`
- initial single-stock symbol: `RY`

## Execution Model

- whole shares only
- fixed commission `1.99 USD`
- fixed slippage `5 bps`
- minimum trade size `100 USD`
- decide at `open`
- execute at `close`

## Single-Stock RL

- default cash yield kept at `0%`
- random contiguous training windows kept as default
- reward stayed relatively simple after heavier penalties caused collapse

## Portfolio RL

- main internal benchmark: `equal-weight buy-and-hold`
- external benchmark: `SPY`
- best Phase 2 structural improvement:
  - strategic review cadence
  - residual freeze outside review steps

## Alpha Engineering

- Group A did not beat the Phase 2 mainline
- Group B became the strongest Phase 3 branch
- Group C market-layer context did not help in its first version

## Productization

- dashboard is local-first
- profiles stored in SQLite
- users can edit and confirm tickets before execution
- operation history and rollback are built in
