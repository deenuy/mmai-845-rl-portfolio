# Start Here If You Know Nothing

This file is for someone who has never seen this project before.

If you only want to get the dashboard running, follow these steps exactly.

## 1. Open PowerShell In This Folder

Open PowerShell inside this handoff package folder.

## 2. Create A Python Environment

Run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If it worked, your terminal should now begin with:

- `(.venv)`

## 3. Install The Libraries

Run:

```powershell
python -m pip install --upgrade pip
pip install -e .[train,dev]
```

## 4. Check That The Code Is Healthy

Run:

```powershell
python -m pytest tests\unit -q -p no:cacheprovider
```

What you want to see:

- tests passing

## 5. Reset The Example Profile

Run:

```powershell
python scripts\seed_example_profiles.py --start-date 2026-01-01 --initial-cash 100000 --reset-existing
```

## 6. Start The Dashboard

Run:

```powershell
python scripts\run_product_dashboard.py --host 127.0.0.1 --port 8080
```

Then open:

- `http://127.0.0.1:8080`

## 7. What To Click

1. Open the example profile.
2. Click `Refresh Today's Recommendation`.
3. Click `Review And Confirm Rebalance`.
4. If needed, edit shares or execution prices.
5. Click `Confirm Rebalance Complete`.
6. Click `View Operation History` to see what was saved.

## 8. If Something Fails

Read:

- `TROUBLESHOOTING.md`

## 9. If You Want The Research Story

Read these next:

1. `KEY_DECISIONS_SUMMARY.md`
2. `PROJECT_JOURNEY_PHASE_0_TO_4.md`
3. `EXPERIMENT_ENVIRONMENT_AND_DECISIONS.md`
4. `TEAM_HANDOFF_NOTES.md`
