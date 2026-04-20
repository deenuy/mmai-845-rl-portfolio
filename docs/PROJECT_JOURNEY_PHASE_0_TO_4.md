# Project Journey: Phases 0 To 4

This note is the fastest way for a new teammate to understand how the project evolved and why the current mainline looks the way it does.

## Phase 0: Foundation First

### Goal

Build a trustworthy single-stock environment before introducing serious RL training.

### What We Locked Early

- U.S. equities only
- base currency fixed to `USD`
- first symbol fixed to `RY`
- initial capital fixed to `100,000 USD`
- whole-share execution only
- fixed commission: `1.99 USD`
- fixed slippage: `5 bps`
- minimum trade value: `100 USD`
- decision at current-day `open`
- execution at current-day `close`

### Why It Mattered

We deliberately spent time on environment design because early accounting bugs can make every later training result meaningless.

### Key Outcome

By the end of Phase 0, we had:

- reproducible data scripts
- a clean trading environment
- random-agent checks
- buy-and-hold accounting alignment

### Lesson Learned

The biggest early win was not model quality. It was getting execution timing, fees, and post-trade cash accounting right.

## Phase 1: Single-Stock PPO Validation

### Goal

Prove that PPO can run end-to-end on one stock and produce interpretable behavior.

### What We Tried

- baseline PPO with simple log-return reward
- cash-yield sensitivity
- drawdown penalty variants
- trend-aware and risk-control reward shaping
- recovery-vs-downside features
- normalization and entropy tuning
- random-window vs rolling-window training

### What Failed

- positive cash yield could push PPO into cash-heavy local optima
- direct drawdown penalty often collapsed the policy into near-zero trading
- rolling-window training underperformed random contiguous windows
- adding too many similar trend features at once did not help

### What Helped

- `VecNormalize`
- regime-aware position sizing
- recovery-vs-downside signals
- retaining random contiguous training windows

### Key Outcome

Phase 1 ended with a single-stock PPO pipeline that was:

- reproducible
- benchmarked
- visualized
- documented

### Lesson Learned

In finance RL, stability work was more valuable than clever reward shaping. We got more from feature design and training stabilization than from aggressive reward engineering.

## Phase 2: Portfolio Allocation

### Goal

Move from one stock to a real multi-asset portfolio with rebalancing, baselines, and portfolio-level PPO.

### First Basket

- `RY`
- `MSFT`
- `RKLB`
- `XOM`
- `PG`

### Core Design Decisions

- softmax-style normalized target weights
- explicit cash sleeve
- sell-first, buy-second execution
- same transaction-cost assumptions as Phase 0/1
- equal-weight buy-and-hold promoted to the main internal benchmark
- `SPY` kept as the external market benchmark

### What Changed Mainline Performance

The single biggest Phase 2 improvement was structural:

- strategic review cadence
- freezing residual sleeves outside review steps

This sharply reduced unnecessary reshuffling and improved both returns and trade discipline.

### Key Outcome

By the end of Phase 2, the residual-freeze portfolio PPO had become the mainline best result and survived multi-seed validation.

### Lesson Learned

Portfolio structure mattered more than extra reward complexity. A better execution rhythm beat many reward tweaks.

## Phase 3: Alpha Engineering

### Goal

Add information, not noise. Improve the strategy through better features and controlled experiments.

### Feature Groups

- Group A: MACD, breakout/recovery confirmations
- Group B: cross-sectional relative strength
- Group C: market-layer context

### Results

- Group A full: did not beat the Phase 2 mainline
- Group A reduced: better than Group A full, still not enough
- Group B core: first Phase 3 branch that clearly improved on the Phase 2 baseline
- Group C core: did not help in its first version

### Most Important Discovery

Within Group B, the strongest contribution came from:

- breakout relative strength
- drawdown relative position

Momentum helped as an auxiliary signal, but was not the primary driver by itself.

### Key Outcome

`Group B core` became the current Phase 3 mainline best candidate and held up in:

- multi-seed validation
- 2025 alternate-window validation
- 10-stock extended-universe validation

### Lesson Learned

The best improvements came from cross-sectional selection logic, not from broad market overlays.

## Phase 4: Stress, Productization, And Delivery

### Goal

Stress-test the frozen mainline and turn it into a usable local product shell.

### What We Built

- named stress windows
- defense summary views
- paper-trading export
- profile-based local dashboard
- editable order ticket
- operation history and rollback
- sample example profile

### Current Product Behavior

- store profiles in SQLite
- load core or extended frozen policy automatically
- generate today’s rebalance recommendation
- review and edit orders before confirming
- log executed recommendations by date

### Key Outcome

We now have something shareable and runnable by teammates without needing the whole development thread as context.

### Lesson Learned

Productization forced us to clarify what “execution” really means. Logging, rollback, and editable confirmation turned out to be just as important as the strategy itself.

## Overall Project Lessons

1. Environment correctness came before model quality.
2. Structural portfolio logic beat many reward tweaks.
3. Simpler and better-grouped features beat feature bloat.
4. Cross-sectional signals were more useful than broad market overlays in the current setup.
5. Product workflows exposed hidden assumptions faster than offline backtests alone.
