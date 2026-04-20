# Phase Development Framework

## Purpose

This document defines how the project executes work by phase, how deviations from the roadmap are recorded, how tests are organized, and how completion reports are generated.

## Delivery Model

All implementation work in this repository must be grouped into phases.

- `Phase 0`: Data and environment infrastructure
- `Phase 1`: Single-asset validation
- `Phase 2`: Multi-asset portfolio allocation
- `Phase 3`: Alpha engineering and tuning
- `Phase 4`: Stress testing and paper trading

Each phase follows the same operating cycle:

1. Define scope and acceptance criteria.
2. Define phase-specific tests before implementation.
3. Implement or upgrade the target capability.
4. Run required tests and collect artifacts.
5. Record any roadmap deviation.
6. Publish a phase completion report with charts and metrics.

## Required Project Rules

- All team communication may happen in any language, but code comments and repository documents must remain in English.
- Any development behavior that differs from the approved roadmap must be recorded in `docs/ROADMAP_DEVIATIONS.md`.
- No phase may be marked complete unless its required tests pass and a report is generated under `reports/`.
- Every phase should produce reproducible metrics, saved artifacts, and a short decision summary.

## Phase Execution Checklist

Before implementation:

- Confirm the phase goal.
- Freeze the phase scope.
- Define inputs, outputs, and dependencies.
- Define the test plan and pass/fail conditions.

During implementation:

- Keep changes within the approved phase scope.
- Record any necessary roadmap deviation immediately.
- Update assumptions when data, market, or infrastructure constraints change.

Before completion:

- Run all mandatory tests.
- Save generated figures and summary tables.
- Write the phase completion report.
- Capture open risks and next-phase carry-over items.

## Minimum Acceptance Gate Per Phase

Every phase must satisfy all items below:

- Scope is implemented and documented.
- Mandatory tests are passing.
- Metrics are reproducible.
- Deviations are logged.
- Report is written and stored in the correct phase folder.

## Repository Conventions

- Governance documents live in `docs/`.
- Test specifications and automated tests live in `tests/`.
- Phase reports live in `reports/phase_##/`.
- Report figures live in `reports/phase_##/figures/`.
- Generated metrics should be saved alongside the corresponding report whenever practical.
