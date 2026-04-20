@echo off
cd /d "%~dp0"
python scripts\seed_example_profiles.py --start-date 2026-01-01 --initial-cash 100000 --reset-existing
