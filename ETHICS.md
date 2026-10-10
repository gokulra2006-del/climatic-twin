# Privacy & Ethics Statement

## 1. Data Privacy
This repository processes aggregate, anonymized environmental and infrastructure telemetry. No Personally Identifiable Information (PII) is stored. Synthetic simulators used for missing grid telemetry are mathematically isolated and strictly explicitly labeled to prevent passing generated data off as physical historical records.

## 2. Resource Allocation Bias
The Impact-Based Warning engine incorporates an Equity-Weighted Priority Score mapping vulnerabilities to risk. Care must be taken to regularly audit the ulnerability and service_criticality constants assigned to infrastructure classes (e.g., ensuring residential sectors are not structurally down-weighted in favor of commercial districts).

## 3. Automation and Human-in-the-Loop (HITL)
Models in this framework are strictly Decision-Support Systems. They compute expected utilities and decision curves to *recommend* actions, but cannot actuate physical infrastructure (e.g., redirecting grid power) without human authorization. The Scenario-Replay analytics suite explicitly tracks Alert Fatigue to prevent automation complacency.
