# Role-Aware Navigation and Dashboard Implementation

Based on the prompt requirements, the current `App.jsx` must be refactored to support distinct pages/views for Admin, Operator, and Viewer roles instead of showing everything on a single scrolling page.

## Proposed Changes

Here is the exact breakdown of what each page should show based on the data boundaries:

### 🟢 Viewer Page (public/read-only dashboard)
**Goal:** situational awareness, no control.
- **Hazard overview cards** (5 hazards): current risk level (Low/Moderate/High/Critical), a color badge, and the probability + P10–P90 range.
- **Live alert bulletin**: active warnings sorted by severity, with lead-time text ("Critical flood risk expected in 14h").
- **Map view**: reservoir markers (current % full), flood-zone overlay, no editing.
- **Key metrics strip**: today's rainfall, current reservoir levels (Poondi, Cholavaram, Redhills, Chembarambakkam), temperature, wind.
- **Historical trend chart**: last 7/30 days of the selected hazard's risk score (read-only, no replay controls).
- ❌ **No**: Time Machine, actuation panel, sensor management, user management, raw latency logs.

### 🟡 Operator Page (the "control room")
Everything Viewer has, **plus**:
- **Time Machine / Scenario Replay panel**: date picker + play/pause/speed slider to replay historical events (2015 floods etc.) through the live pipeline.
- **Actuation control panel**: shows pending automated recommendations ("System suggests opening Poondi floodgates — CRITICAL flood risk"), with Approve / Override / Dismiss buttons.
- **Automated Response Log**: timestamped history of every actuation command, what triggered it, and whether a human approved/overrode it.
- **Sensor/telemetry health panel**: which stations are reporting live vs. stale/offline (useful once you add MQTT — shows which sensors haven't published recently).
- **Model confidence / explainability panel**: SHAP-style breakdown ("rainfall contributed +32%") for the current prediction, so the operator can judge whether to trust it.
- **Manual telemetry injection**: a form to manually POST a sensor reading (for testing/demo purposes when live data isn't available).
- ❌ **No**: user account management, model retraining controls.

### 🔴 Admin Page
Everything Operator has, **plus**:
- **User management**: table of users, their roles, ability to create/deactivate accounts, reset passwords.
- **Sensor/station management**: add/remove/edit reservoir sensors or weather stations feeding the pipeline, set thresholds per station.
- **Model management**: view current model versions and their validation metrics (ROC-AUC etc.), trigger retraining, roll back to a previous model version.
- **System/infra health**: message broker (MQTT) connection status, database status, API latency breakdown (ingestion/processing/inference/alert), error logs.
- **Audit log**: every admin/operator action across the system (who approved which actuation, who changed which threshold, when).
- **Configuration panel**: hazard threshold values (the 36°C/39°C/41°C heatwave cutoffs etc.) editable without redeploying code.

## Matrix Overview

| Concern | Viewer | Operator | Admin |
|---|---|---|---|
| See risk & alerts | ✅ | ✅ | ✅ |
| Replay history | ❌ | ✅ | ✅ |
| Trigger/approve actuation | ❌ | ✅ | ✅ |
| Manage sensors/thresholds | ❌ | ❌ | ✅ |
| Manage users | ❌ | ❌ | ✅ |
| Retrain/rollback models | ❌ | ❌ | ✅ |

## Next Steps
We will refactor `App.jsx` to use a tab-based or route-based rendering system (`currentView`), utilizing `AuthContext.jsx`'s `hasRole` to enforce access to the Operator and Admin tabs. We will build out placeholder UI cards for the missing administrative features so the structure is fully realized.

## User Review Required
Please click **Proceed** if you approve this structure to begin implementation.
