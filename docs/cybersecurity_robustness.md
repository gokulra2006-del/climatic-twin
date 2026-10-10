# Cybersecurity & Robustness Testing

## 1. Non-Destructive Local Harness
IoT telemetry networks connecting municipal pump sensors to cloud digital twins are heavily targeted attack vectors. To evaluate our system's resilience without engaging in unauthorized network probing, we built a strictly **Local Simulated Security Harness** (scripts/experiment_cybersecurity.py).

*⚠️ ATTENTION: This tooling utilizes an internal, mocked Python-based message bus. It makes ZERO external TCP/IP or network calls. It must NEVER be repointed or configured to target external municipal hosts.*

## 2. Threat Models & Defences
We subjected the ingestion pipeline to 6 simulated threat vectors. The processor layers multiple defences before yielding the data to the machine-learning Hazard Models:

1. **Spoofed Value (Man-in-the-Middle):** Attacker alters a valid payload stream in transit.
   * *Defence:* **HMAC-SHA256 Signatures.** 
2. **Replay Attack:** Attacker captures a valid, fully signed message and resends it later to trigger a fake response.
   * *Defence:* **Nonce Tracking & Timestamp Freshness.** Messages older than 60 seconds or utilizing a cached UUID Nonce are dropped.
3. **Corrupted Payloads:** Malformed JSON or randomized fuzzing.
   * *Defence:* Strict JSON decoding and structural casting.
4. **Invalid Authentication:** Unauthorized connection attempts.
   * *Defence:* Broker-level Auth Tokens.
5. **Topic Misuse:** A compromised rain-gauge sensor attempts to publish data to the water_level command topic.
   * *Defence:* Broker-level **Access Control Lists (ACLs)** bounding publishers to strictly defined topics.
6. **Stealth Implausible Value:** An attacker steals the physical SECRET_KEY from the edge device. They generate a perfectly valid, correctly signed, fresh message indicating ,000 of rain to trigger an automated dispatch and cause municipal chaos.
   * *Defence:* **Physical Plausibility Bounds.** The ML pipeline quarantines any value exceeding physical earthly thresholds (e.g., Rain $> 500/h) regardless of cryptographic validity.

## 3. Results
*(Data Source: esults/cybersecurity_metrics.csv)*

| Scenario | Detection Rate | False Quarantine Rate | Triggered False Hazard? | Added Latency |
| :--- | :--- | :--- | :--- | :--- |
| **Clean Traffic** | N/A | **0.0%** | N/A | $\approx 0.007$ ms |
| **Spoofed Value** | 100% | N/A | No | N/A |
| **Replay Attack** | 100% | N/A | No | N/A |
| **Corrupted JSON** | 100% | N/A | No | N/A |
| **Invalid Auth** | 100% | N/A | No | N/A |
| **Topic Misuse** | 100% | N/A | No | N/A |
| **Stolen Key / Implausible** | 100% | N/A | No | N/A |

### Key Findings
1.  **Zero Flaw Tolerance:** The layered defensive pipeline (Auth $\to$ ACL $\to$ JSON Parse $\to$ HMAC $\to$ Nonce $\to$ Plausibility) successfully achieved a **100% Detection Rate** against the simulated attack vectors.
2.  **Zero Hazard Triggering:** No mutated or stealth-implausible message successfully reached the HazardModel to trigger a fake early warning.
3.  **Negligible Latency:** The entire cryptographic and plausibility validation block executes in **~0.007 milliseconds**, imposing absolutely zero drag on the real-time early warning operational pipeline.
