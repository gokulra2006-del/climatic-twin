.PHONY: all test evaluate run-all clean help

PYTHON = backend/venv/Scripts/python.exe

help:
	@echo "ClimateTwin - Master Research Makefile"
	@echo "--------------------------------------"
	@echo "make run-all  : Execute the complete master pipeline (All 16 domains)"
	@echo "make test     : Run unit tests (including Model Governance)"
	@echo "make clean    : Remove cached files and results"

run-all:
	@echo "Executing all ClimateTwin features..."
	cd backend && .\venv\Scripts\python.exe ..\scripts\run_all_experiments.py

test:
	@echo "Running tests..."
	cd backend && .\venv\Scripts\python.exe -m unittest discover -s ..\tests

clean:
	@echo "Cleaning up generated results and plots..."
	Remove-Item -Recurse -Force results\*.csv -ErrorAction SilentlyContinue
	Remove-Item -Recurse -Force results\*.json -ErrorAction SilentlyContinue
