# Phase 2 Mainline Upgrade Proposal

## Purpose

This note captures the Tory-branch lessons that were accepted for return to `main` without copying the branch-local discretionary rules themselves.

The goal is to strengthen the Phase 2 portfolio PPO stack while preserving the separation between:

- mainline RL design
- branch-local Tory heuristics

## Accepted Learnings To Bring Back

The following items are approved for mainline integration:

1. Hierarchical portfolio structure
2. Priority-aware funding order
3. Regime-aware cash behavior
4. Frozen residual sleeves outside scheduled review steps
5. Expanded portfolio evaluation diagnostics

The following Tory-specific rules remain branch-local and should not be copied into `main`:

- fixed `20%` hard stop
- fixed `21`-day cooldown
- fixed `50%` heavy-focus rule
- direct heuristic score-to-trade rules

## Mainline Translation

### 1. Hierarchical Portfolio Structure

Mainline Phase 2 should evolve from a flat all-symbol allocation scheme toward a layered structure:

- core sleeve
- residual sleeve
- cash sleeve

This does not require hard-coding a single focus stock. Instead, it means the environment and policy should support:

- stronger concentration when conviction is high
- lighter residual participation when conviction is lower
- explicit cash as a separate capital-management sleeve

### 2. Priority-Aware Funding Order

When the portfolio needs more capital for higher-conviction positions, the execution logic should eventually support a more realistic funding order:

- lower-priority residual positions should become the first source of capital
- higher-priority positions should be protected longer

The immediate mainline implication is not to hard-code symbol rankings, but to prepare for:

- per-symbol priority diagnostics
- execution ordering that can respect model-implied priority

### 3. Regime-Aware Cash Behavior

Cash should remain flexible.

Mainline should not assume a fixed constant cash sleeve such as always `10%`.

Instead, the system should move toward:

- higher cash in weaker or ambiguous conditions
- lower cash in clearer constructive conditions

This should be expressed through:

- state features
- portfolio-level reward design
- later hierarchical action interpretation

not through hard-coded branch-local discretion rules.

### 4. Frozen Residual Sleeves Outside Review Steps

One of the most useful Tory lessons is that the residual book should not be fully reshuffled on every rebalance.

Mainline should move toward:

- scheduled strategic review steps
- slower residual re-ranking
- ordinary rebalances that focus on high-conviction sleeves first

The first implementation target should be:

- only refresh residual ordering on scheduled review steps
- avoid broad residual reshuffling on every ordinary execution step

### 5. Expanded Portfolio Evaluation Diagnostics

Mainline Phase 2 evaluation should track more than headline return.

The upgraded diagnostics set should include:

- per-symbol trade counts
- target-weight concentration summaries
- realized-weight concentration summaries
- internal benchmark comparison against equal-weight buy-and-hold
- cross-window robustness checks

These additions are especially important because Phase 2 performance can look strong while still hiding:

- excessive turnover
- unstable concentration behavior
- overreaction in residual sleeves

## Recommended Implementation Order

To keep mainline stable, the upgrade should be introduced in this order:

1. Expand evaluation and diagnostics
2. Add slower residual update logic
3. Add regime-aware cash handling
4. Add hierarchical allocation interpretation
5. Add priority-aware funding behavior in execution

## Recommended Near-Term Mainline Tasks

The next concrete mainline tasks should be:

1. Add review-step aware portfolio diagnostics and artifacts
2. Introduce a residual-freeze execution mode for non-review steps
3. Add regime-aware cash features and reporting
4. Test whether turnover falls without materially hurting the current equal-weight-relative result

## Success Criteria

The mainline upgrade should be considered successful if it can improve at least two of the following without severely harming the others:

- lower per-symbol trade counts
- clearer concentration behavior
- stronger downside protection
- more interpretable cash allocation
- stable comparison against `equal_weight_buy_and_hold`
