
.PHONY: audit data baseline enkf gnn_lstm uncertainty cascade compound warnings faults transfer all test

audit:
	cat docs/implementation_audit.md

data:
	python scripts/data_processing/build_event_catalogue.py

baseline:
	python scripts/evaluate_baselines.py

enkf:
	python scripts/experiment_enkf.py

gnn_lstm:
	python scripts/experiment_gnn_lstm.py

uncertainty:
	python scripts/experiment_uncertainty.py

cascade:
	python scripts/experiment_cascade.py

compound:
	python scripts/experiment_compound_risk.py

warnings:
	python scripts/experiment_human_factors.py
	python scripts/experiment_dca.py

faults:
	python scripts/experiment_fault_tolerance.py

transfer:
	python scripts/experiment_city_transfer.py

test:
	pytest backend/tests/

all: data baseline enkf gnn_lstm uncertainty cascade compound warnings faults transfer test
