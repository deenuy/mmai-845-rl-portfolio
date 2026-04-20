# PPT Template (9 Slides)

This template is designed for a class presentation. It is written for peers who understand RL concepts, but may know nothing about this specific project.

## Slide 1 - Why Build This Product?

### Title

Why Build A Personalized Portfolio Product For Retail Investors?

### Core Message

Over long horizons, fees and generic product structures can significantly reduce wealth accumulation. We built this product to give ordinary investors a lower-friction, customizable way to manage portfolios without requiring deep financial expertise.

### Main Visual

- `assets/slide_01_fee_drag_growth_example.png`

## Slide 2 - Main Conclusions

### Title

Main Conclusions

### Core Message

Our mainline product can outperform both `SPY` and equal-weight buy-and-hold without requiring extreme daily trading, and the same infrastructure can also host user-defined strategies such as Tory's strategy.

### Main Visual

- `assets/slide_02_main_conclusions.png`

## Slide 3 - Environment Design And Standardization

### Title

Environment Design And Standardization

### Core Message

Before trusting RL results, we built a controlled environment with clear assumptions around timing, execution, costs, and observations.

### Suggested Bullets

- U.S. equities only in early stages
- currency fixed to `USD`
- whole-share execution
- fixed commission and slippage
- minimum trade size
- decision at daily `open`
- execution at daily `close`
- sell-first, buy-second
- no negative cash

### Supporting Files

- `EXPERIMENT_ENVIRONMENT_AND_DECISIONS.md`
- `project_docs/PHASE_0_ENVIRONMENT_SPEC.md`

## Slide 4 - Phase 1

### Title

Phase 1 - Single-Stock PPO Validation

### Main Visual

- `assets/phase1_recovery_signals_equity_curve.png`

## Slide 5 - Phase 2

### Title

Phase 2 - Portfolio Allocation

### Main Visual

- `assets/phase2_mainline_equity_vs_equal_weight.png`

## Slide 6 - Phase 3

### Title

Phase 3 - Feature Engineering And Alpha Search

### Main Visual

- `assets/phase3_groupb_core_equity_vs_equal_weight.png`

## Slide 7 - Phase 4

### Title

Phase 4 - Stress Testing And Productization

### Main Visual

- `assets/phase4_core_mixed_equity_vs_equal_weight.png`

## Slide 8 - Application Demo

### Title

Application Demo With A Simple Profile

### Main Visuals

- `assets/phase4_demo_market_values.png`
- `assets/phase4_demo_unrealized_pnl.png`

## Slide 9 - Future Development Path

### Title

Future Development Path

### Core Message

The next step is to move beyond a fixed stock basket and support system-level stock selection, richer profile management, and scheduled recommendations for multiple users.
