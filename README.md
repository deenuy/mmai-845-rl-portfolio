# MMAI 845 RL Portfolio Project

This project implements a reinforcement learning based portfolio management system with a local dashboard for profile-based paper trading.

The application allows a user to:

* create and manage portfolio profiles
* generate daily trade recommendations using a trained RL policy
* review and confirm rebalancing actions
* track operation history

---

## Project Structure

```
mmai-845-rl-projects/
├── artifacts/                 # Models and outputs
├── data/                      # Cached market data
├── docs/                      # Reports and documentation
├── notebooks/                 # Experiments
├── scripts/                   # Entry points
│   ├── run_product_dashboard.py
│   ├── seed_example_profiles.py
│   └── export_phase_4_paper_trading.py
├── src/rl_portfolio/          # Core logic
├── tests/unit/                # Unit tests
├── pyproject.toml
├── requirements.txt
└── uv.lock
```

---

## Requirements

* Python 3.10+
* Internet connection for market data

---

## Setup

```bash
git clone <REPO_URL>
cd mmai-845-rl-projects

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
```

Install dependencies (choose one):

```bash
pip install -e ".[train,dev]"   # recommended
```

or

```bash
pip install -r requirements.txt
```

---

## Validate

```bash
python scripts/run_product_dashboard.py --help
python scripts/seed_example_profiles.py --help
python scripts/export_phase_4_paper_trading.py --help
python -m pytest tests/unit -q -p no:cacheprovider
```

Expected:

* help commands work
* tests pass

---

## Run

Seed example data:

```bash
python scripts/seed_example_profiles.py --reset-existing
```

Start dashboard:

```bash
python scripts/run_product_dashboard.py
```

Open:

```
http://127.0.0.1:8080
```

---

## TA Evaluation Steps

Use the existing sample profile. Do not create a new profile.

* Click **Example Extended Equal Weight 2026-01-01**
* Click **Refresh Today's Recommendation**

Verify:

* Strategy Snapshot appears

* Portfolio Summary appears

* Order Ticket shows:

  * Sell First
  * Buy Second

* Click **Review And Confirm Rebalance**

* Click **Confirm Rebalance Complete**

* Click **View Operation History**

---

## Pass Criteria

* App loads
* Sample profile opens
* Recommendation generates
* Orders displayed
* Rebalance completes
* History recorded

---

## One-line Flow

Open → Refresh → Confirm → History
