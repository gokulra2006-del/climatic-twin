# ClimateTwin Phase 17 Decision Policy

## Model Version
`CLIMATETWIN_DSS_v1.0_PROTOTYPE`

## Decision Support Score (DSS)

DSS = 0.30 * Hazard_Severity + 0.20 * Asset_Risk + 0.15 * Compound_Risk + 0.15 * Forecast_Confidence + 0.10 * Data_Quality + 0.10 * Persistence

All components normalized to [0, 1].

## Decision Levels

| Level | DSS Range | Description |
|-------|-----------|-------------|
| NORMAL | [0.00, 0.20) | Routine monitoring |
| MONITOR | [0.20, 0.40) | Enhanced surveillance |
| PREPARE | [0.40, 0.60) | Preparedness activation |
| ALERT | [0.60, 0.80) | Operational response |
| EMERGENCY | [0.80, 1.00] | Full emergency mobilization |

## Hysteresis Band
De-escalation requires DSS to drop 0.1 below the level threshold to prevent alert flapping.

## Data Quality Gate
- PASS: Aggregate SHS >= 0.70, at most 1 unhealthy source
- DEGRADED: Aggregate SHS >= 0.45, at most 3 unhealthy sources
- BLOCKED: Below DEGRADED thresholds; automatic all-clear is BLOCKED

## Uncertainty-Aware Decision Matrix
| Probability | Uncertainty | Decision Modifier |
|------------|-------------|-------------------|
| HIGH | LOW | Strong escalation candidate |
| HIGH | HIGH | Precautionary escalation + verification |
| MODERATE | LOW | Monitoring / preparedness |
| MODERATE | HIGH | Enhanced monitoring + verification |
| LOW | HIGH | Do NOT declare safety; verify telemetry |
| LOW | LOW | Nominal monitoring |

## Scientific Limitations
1. Decision thresholds are PROTOTYPE values.
2. Operational actions require domain-expert approval.
3. Synthetic scenarios are NOT real emergency decisions.
4. This is decision SUPPORT, not an autonomous emergency authority.
5. No unsupported causal claims are made.

---
*Generated: 2026-09-02T11:48:45.749823+00:00*
