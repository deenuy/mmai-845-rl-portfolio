@echo off
cd /d "%~dp0"
python scripts\run_product_dashboard.py --host 127.0.0.1 --port 8080
