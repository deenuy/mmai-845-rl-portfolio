# Experiment Environment And Decisions

This note explains how the RL experiment environment was built and how major design decisions were made across the project.

## Why We Built The Environment First

In this project, backtest correctness mattered more than early model quality.

We intentionally built the environment before relying on PPO results because financial RL can look strong even when:

- transaction fees are applied incorrectly
- cash goes negative by mistake
- the agent sees information it should not know yet
- rebalance logic uses unrealistic execution ordering

So the project started with environment-first validation, not model-first experimentation.

## Core Environment Principles

The environment was designed around a few fixed principles:

- U.S. equities only in the initial research stages
- account currency fixed to `USD`
- whole-share execution only
- fixed commission `1.99 USD`
- fixed slippage `5 bps`
- minimum trade value `100 USD`
- decision at daily `open`
- execution at daily `close`
- sell-first, then buy
- no negative cash

These rules were chosen to keep the system realistic enough for portfolio research while still being simple enough to debug.

## Why Observation Timing Matters

One of the most important design decisions was preventing same-day information leakage.

We did not let the agent observe values that would only be fully known after the market closed. That means the model can use:

- current-day `open`
- historical features already known before execution

But not:

- current-day `close`
- current-day `high`
- current-day `low`

This was critical for keeping the training environment defensible in an academic RL setting.

## How The Phases Built On Each Other

## Phase 0

We validated:

- data download and cleaning
- execution accounting
- random-agent stability
- buy-and-hold alignment

This phase answered:

- can the environment run correctly?
- do the portfolio mechanics make sense?

## Phase 1

We moved to single-stock PPO and learned:

- positive cash yield could bias PPO toward cash-heavy local optima
- heavy drawdown penalties could collapse the policy
- normalization and better regime features helped more than aggressive reward shaping

This phase answered:

- can PPO run end-to-end on a trustworthy single-stock setup?

## Phase 2

We moved to portfolio allocation and learned:

- equal-weight buy-and-hold is a strong benchmark
- structural rebalance logic matters a lot
- freezing residual sleeves outside strategic review steps sharply improved results

This phase answered:

- can the environment support real multi-asset portfolio control?

## Phase 3

We focused on alpha engineering and learned:

- too many new features at once diluted signal quality
- cross-sectional relative-strength features were the most effective improvement
- broad market overlay features did not help in the first pass

This phase answered:

- which information actually improves the portfolio policy?

## Phase 4

We stress-tested and productized the system:

- named stress windows
- defense summary
- paper-trading export
- profile-based local dashboard
- editable confirmation and rollback

This phase answered:

- can the current model survive multiple regimes?
- can a human actually use the output?

## How Major Decisions Were Made

Most major decisions followed the same pattern:

1. establish a simpler baseline
2. run a controlled comparison
3. check metrics and plots
4. keep only changes that improved behavior or robustness
5. document both successful and failed branches

This is why the current system includes both:

- phase reports
- roadmap deviation notes

We deliberately recorded failed ideas too, because in RL research they are often just as important as the final chosen configuration.

## Examples Of Decisions Made This Way

### Cash yield

We tested `0%` versus positive cash yield and found that positive cash yield could produce overly defensive policies in the single-stock phase.

### Rolling versus random windows

We tested both. Random contiguous windows remained the default because rolling windows became too conservative in our setup.

### Group A / Group B / Group C

We did not assume all feature groups would help.

- Group A: partially useful, but not enough
- Group B: strongest improvement
- Group C: not useful in first version

### Residual freeze

This was adopted only after portfolio PPO with more reactive residual reshuffling proved too high-turnover and less effective.

## What A New Teammate Should Understand First

Before changing the strategy, it helps to understand:

- the execution engine
- the observation timing
- the benchmark hierarchy
- why `Group B core` became the current best Phase 3 mainline
- how the product dashboard consumes frozen policy outputs

The current system is not a random collection of scripts. It is a phase-by-phase research pipeline where each layer depends on decisions validated in earlier phases.
