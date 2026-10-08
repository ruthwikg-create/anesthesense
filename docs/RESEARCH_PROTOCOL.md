# AnestheSense research protocol — draft v0.1

**Working title:** Provenance-Aware, Uncertainty-Calibrated Streaming Hemodynamic Research Platform for Perioperative Deterioration Forecasting.

**Status:** Research hypothesis and proposed evaluation only. Not a claim of first invention, novelty clearance, clinical validation, or medical-device-grade accuracy.

## Research gap and proposed contribution

Hypotension prediction, perioperative AI, digital twins and data-quality research already exist. The proposed contribution to investigate is an **end-to-end evaluation of whether device provenance, measurement age, quality, missingness and uncertainty-aware abstention improve reliability and calibration of perioperative deterioration forecasts under real-world stream degradation**, compared with conventional retrospective predictors.

The platform will preserve the difference between measured invasive MAP, measured noninvasive MAP and derived MAP; record device/source identity, original units, capture time, receipt time, quality flags, missingness and transformation history; and display explicit *historical replay* versus *live research acquisition* state.

A 'digital twin' designation must be earned through an explicitly defined dynamical patient model with update and validation, not applied to an ordinary trend chart.

## Testable hypotheses

- H1: A provenance-aware prediction pipeline reduces invalid/unsupported predictions when sensors are missing, delayed or corrupted compared with an otherwise identical baseline pipeline.
- H2: Uncertainty-calibrated forecasts have better empirical interval coverage and lower calibration error on held-out cases than uncalibrated forecasts.
- H3: A quality-based abstention policy reduces unsafe false reassurance under distribution shift, measured alongside its coverage/availability trade-off.
- H4: A streaming replay engine maintains defined latency, ordering and data-integrity thresholds under injected jitter, packet loss, duplicates and disconnects.

These are hypotheses, **not observed results**.

## Proposed experiments

1. **Data governance:** only synthetic or approved de-identified recordings; preserve case-level identifiers for grouped splitting, not patient identifiers.
2. **Input validation:** define canonical signals, units, timestamps, acquisition modes, sampling frequency, plausibility checks and missingness; never impute silently.
3. **Replay protocol:** deterministic virtual clock with play/pause/seek/speed; track both event time and processing time. Never label recorded data as live.
4. **Forecasting:** implement a reproducible baseline first, then an uncertainty-calibrated model with training/validation/test split by patient and preferably site.
5. **Ablation:** compare base model, +quality metadata, +provenance, +uncertainty calibration, +abstention on identical held-out cases.
6. **Stress testing:** simulate dropout, stale measurements, out-of-order frames, device switching, wrong units, clock drift, noise and distribution shift.
7. **Clinical endpoint specification:** prospectively define hypotension event (for example MAP <65 mmHg sustained for a specified duration) and 5/10/15-minute forecast horizons; distinguish invasive vs intermittent noninvasive readings.
8. **Metrics:** AUROC, AUPRC, sensitivity, specificity, precision, Brier score, expected calibration error, forecast interval coverage, lead time, false alerts per hour, abstention rate, data availability, p50/p95/p99 latency, packet loss and provenance errors. Report confidence intervals and stratification.
9. **External validation:** evaluate independent hospital/device datasets when legally accessible; report subgroup failure modes, not just aggregate scores.
10. **Bench demonstration:** use only an authorized simulator or de-identified recording; verify numerical parity against source records and log every transformation.
11. **Safety boundary:** no autonomous interventions, drug doses, pump control or replacement of primary monitor alarms. AI explanations never override deterministic research safety rules.
12. **Publication:** preregister hypotheses, document dataset provenance, report negative findings, release reproducible code and synthetic fixtures where permitted.

## Medical-grade claims: evidence required

- Traceable reference instruments, calibration and measurement uncertainty where applicable.
- Validation of input measurement accuracy, numerical processing, units and timestamp alignment.
- Defined intended use, hazards, cybersecurity, software lifecycle and usability requirements.
- Relevant regulatory and quality-management review before any medical-device or clinical use claims.

A medical-device-origin value is not automatically a medically validated application output.

## Novelty assessment and prior art

Do **not** claim 'world's first', 'never done by MIT', 'first ever', or patentability without a systematic literature, patent and product search. Existing prior art includes:
- Hypotension Prediction Index research and randomized trials (JAMA HYPE trial, 2020).
- Systematic review of intraoperative hypotension ML prediction (Journal of Translational Medicine, 2024).
- MIT/MGH anesthesia AI research (MIT News, 2022).
- Data-quality reviews in perioperative care (2025).
- Verification, validation and uncertainty quantification for digital twins (npj Digital Medicine, 2025).

Start with a PRISMA-style search across PubMed, IEEE Xplore, Scopus/Web of Science, Google Scholar and patents; record search dates, query strings, inclusion criteria and a feature-level novelty matrix. Novelty must be phrased narrowly and revised if overlap is found.

## Implementation milestones

M1: reliable authenticated CSV ingestion and deterministic replay; test with de-identified real data.
M2: provenance schema, data quality engine, immutable audit events, stream degradation simulator.
M3: baseline forecasting with patient-level leakage-free splits and benchmark suite.
M4: uncertainty calibration, abstention and controlled ablation studies.
M5: independent external retrospective validation.
M6: authorized device simulator and later manufacturer-approved acquisition on a test bench.
M7: ethics, regulatory and clinical governance before any patient-connected research.

**Current repository status:** a research prototype with CSV import/replay, deterministic analyses, device catalog, and normalized Philips research ingress. These milestones are not all implemented or verified.
