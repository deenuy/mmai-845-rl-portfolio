# Phase 4 Implementation Plan

## Plan Summary

Phase 4 should proceed in a narrow and disciplined order:

1. freeze the Phase 3 reference checkpoint and configuration
2. define stress windows and reporting contracts
3. run five-symbol stress tests
4. run ten-symbol stress tests
5. generate defense-capability summaries
6. build a lightweight paper-trading recommendation pipeline
7. produce a Phase 4 summary report and closure note

## Stage 1: Freeze the Reference

Reference branch for Phase 4:

- `Group B core`
- residual-freeze portfolio structure
- current default turnover settings and review cadence

Expected output:

- one documented reference configuration block
- one reference artifact path list

## Stage 2: Stress-Test Matrix

Create a reusable stress-test runner that supports:

- five-symbol basket
- ten-symbol extended universe
- named windows:
  - `bear_2022`
  - `bull_2023_2024`
  - `mixed_2022_2024`
  - `alt_2025`

Expected output:

- stress-test metrics JSON per window
- HTML page per window
- consistent figure naming

## Stage 3: Five-Symbol Stress Package

Run the reference branch on the core five-symbol basket for all required windows.

Focus:

- return stability
- drawdown behavior
- cash behavior
- concentration behavior
- turnover by symbol

Expected output:

- `artifacts/phase_04/stress/core_basket/...`
- `reports/phase_04` summary section for the core basket

## Stage 4: Extended-Universe Stress Package

Repeat the same matrix on the ten-symbol extended universe.

Focus:

- whether the policy remains usable when the universe broadens
- whether concentration or turnover worsens materially
- whether relative edge versus equal-weight persists

Expected output:

- `artifacts/phase_04/stress/extended_universe/...`
- comparative tables in the Phase 4 report

## Stage 5: Defense Review

Build a dedicated defense summary that compares:

- `bear_2022` vs `bull_2023_2024`
- five-symbol vs ten-symbol results

Track:

- average cash weight
- concentration
- per-symbol trade counts
- drawdown
- benchmark gap

Expected output:

- one compact defense summary table
- one report section answering whether the policy behaves defensively

## Stage 6: Paper-Trading Preparation

Build a lightweight daily recommendation workflow.

The first implementation should:

- load the latest available feature panel
- score the frozen reference policy
- export next-day target weights
- export cash weight and turnover summary
- write one local report package

This should remain local and file-based for the first Phase 4 round.

Expected output:

- one script for daily recommendation export
- one sample paper-trading output folder
- one local HTML or Markdown summary

## Stage 7: Closure

Phase 4 should close with:

- a main report
- a closure note
- a stress-test artifact index
- a paper-trading artifact example

## Immediate Next Step

The first implementation step should be:

- add a Phase 4 stress-test runner with named windows
- generate the first five-symbol stress package from the frozen Phase 3 mainline best
