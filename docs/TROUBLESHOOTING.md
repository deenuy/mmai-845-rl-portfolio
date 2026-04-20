# Troubleshooting

## Python Is Not Found

Install Python `3.10+` and reopen PowerShell.

## Virtual Environment Does Not Activate

Try:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

## Dependency Install Fails

Try:

```powershell
python -m pip install --upgrade pip setuptools wheel
pip install -e .[train,dev]
```

## Tests Fail

Make sure:

- the virtual environment is active
- the install step completed

Then re-run:

```powershell
python -m pytest tests\unit -q -p no:cacheprovider
```

## Dashboard Does Not Open

Check:

- the PowerShell window is still running
- you opened `http://127.0.0.1:8080`

## Example Profile Is Missing

Run:

```powershell
python scripts\seed_example_profiles.py --start-date 2026-01-01 --initial-cash 100000 --reset-existing
```

Then refresh the page.

## Model Load Error

The most common cause is missing:

- `stable-baselines3`
- `torch`

Re-run:

```powershell
pip install -e .[train,dev]
```

## Market Data Download Fails

This project uses `yfinance`.

Check:

- internet access
- firewall restrictions
- temporary Yahoo data availability
