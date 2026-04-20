# Phase 2-3 Symbol Universe

## Purpose

This document defines the provisional U.S. equity symbol universe for later multi-asset development in Phase 2 and Phase 3.

The goal is to cover a diverse set of sector behaviors while minimizing unnecessary overlap.

## Selection Rules

- Use U.S.-listed symbols only
- Prefer large, liquid, and well-known names when possible
- Keep sector roles distinct enough to support later portfolio-allocation experiments
- Treat this list as the default development universe unless a later deviation is approved

## Selected Sector-to-Symbol Mapping

| Sector | Symbol | Rationale |
| --- | --- | --- |
| Financials | `RY` | Keeps continuity with the Phase 1 single-stock baseline while still representing a major North American bank listed in the U.S. |
| Big Tech | `MSFT` | Large platform technology exposure with strong software and cloud weighting. |
| Emerging Tech / Aerospace | `RKLB` | Growth-oriented aerospace and space-systems exposure with a distinct innovation profile. |
| Hardware / Semiconductors | `NVDA` | Clear hardware and compute infrastructure exposure. |
| Defense | `LMT` | Defense-focused exposure distinct from commercial or emerging aerospace. |
| Traditional Energy | `XOM` | Large-cap integrated traditional energy exposure. |
| Renewable Energy | `FSLR` | Cleaner renewable-energy proxy than diversified utilities. |
| Consumer Staples | `PG` | Classic defensive staples exposure. |
| Agriculture | `DE` | Agriculture and farm-capex proxy through machinery and equipment. |
| Commodities Proxy | `FCX` | Commodity-cycle exposure through copper and materials. |

## Notes

- This universe is intended for later Phase 2-3 development and does not overwrite historical Phase 1 validation baskets that were used earlier for robustness checks.
- If a later phase prefers ETF-based commodity or sector proxies, that change should be recorded in `docs/ROADMAP_DEVIATIONS.md`.

## Phase 2 First Basket

The first multi-asset development basket for Phase 2 is intentionally smaller than the full universe so the portfolio environment can be validated with clearer cross-sector behavior differences.

Selected Phase 2 first basket:

- `RY`
- `MSFT`
- `RKLB`
- `XOM`
- `PG`

Why this five-symbol subset was chosen:

- `RY` preserves continuity with the Phase 1 baseline
- `MSFT` provides large-cap technology exposure
- `RKLB` adds a high-volatility emerging-technology profile
- `XOM` adds commodity-linked traditional energy behavior
- `PG` adds a defensive consumer-staples profile

This basket should be treated as the default starting point for Phase 2 environment design, baseline validation, and early PPO portfolio experiments.
