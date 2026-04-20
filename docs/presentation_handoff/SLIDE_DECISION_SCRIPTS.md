# Slide Decision Scripts

## Slide 1

- Decision:
  We positioned the product around personalized investing with low structural friction.
- Why:
  Many retail users either pay for active management or buy generic products that ignore their actual preferences and holdings.
- Benefit:
  This gives a clear product need: personalization without requiring deep financial expertise.

## Slide 2

- Decision:
  We summarized the project around two conclusions: the default product works, and custom strategy overlays can work even better.
- Why:
  This is the cleanest way to explain the value of the system to both ordinary users and advanced users.
- Benefit:
  It makes the framework easy to understand and easy to justify.

## Slide 3

- Decision:
  We froze a realistic environment specification before trying to optimize RL performance.
- Why:
  Without a trustworthy environment, reward comparisons and model results are not meaningful.
- Benefit:
  This gave us a clean foundation for later phases and made every later comparison easier to interpret.

## Slide 4

- Decision 1:
  We started from a single-stock environment.
- Why:
  This let us validate state timing, action semantics, reward behavior, and accounting before moving to a portfolio.
- Benefit:
  It reduced debugging complexity and gave us reliable foundations for later phases.
- Decision 2:
  We kept 0 percent cash yield as the default after testing alternatives.
- Why:
  Positive cash yield pushed PPO toward cash-heavy local optima.
- Benefit:
  The training behavior became more realistic and more comparable to buy-and-hold.

## Slide 5

- Decision 1:
  We switched to a 5-stock differentiated basket.
- Why:
  Multi-asset allocation is much closer to a usable product than a single-stock policy.
- Benefit:
  The project moved from isolated policy learning to actual portfolio construction.
- Decision 2:
  We introduced strategic reviews and residual freeze.
- Why:
  The first portfolio PPO versions traded far too frequently.
- Benefit:
  This sharply reduced turnover and produced the biggest portfolio-structure improvement in the project.

## Slide 6

- Decision 1:
  We ran grouped feature ablations instead of adding everything at once.
- Why:
  We needed to know which signals actually improved performance.
- Benefit:
  This made the model more explainable.
- Decision 2:
  We kept Group B core as the main Phase 3 candidate.
- Why:
  It beat Group A and the first Group C version and stayed strong in multi-seed tests.
- Benefit:
  We ended Phase 3 with a clear, defensible winner.

## Slide 7

- Decision 1:
  We stress-tested across multiple market windows.
- Why:
  One favorable backtest window is not enough to claim robustness.
- Benefit:
  We learned where the strategy defended well and where it still lagged.
- Decision 2:
  We built a product dashboard with logs, review, and rollback.
- Why:
  A useful system needs a human-facing execution loop.
- Benefit:
  The project moved from research output to a usable decision-support tool.

## Slide 8

- Decision:
  We made the application profile-based and execution-aware.
- Why:
  Users need holdings, cost basis, order edits, and confirmation flow, not just target weights.
- Benefit:
  The demo now looks like a realistic workflow instead of a pure notebook result.

## Slide 9

- Decision:
  We defined the next stage around global stock selection and multi-profile support.
- Why:
  The current fixed-basket product is useful, but not yet broad enough for a full investing platform.
- Benefit:
  This gives the project a clear and believable forward roadmap.
