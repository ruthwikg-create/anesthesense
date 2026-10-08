# AnestheSense — perioperative equipment scope

This document is a **research integration roadmap**, not a procurement recommendation, compatibility certification or clinical safety claim. Equipment support depends on exact model, software revision, licensed interfaces, hospital approval, and manufacturer documentation.

## Equipment categories

| Category | Candidate manufacturers / families | Research observations | Status |
|---|---|---|---|
| Multiparameter patient monitoring | Philips IntelliVue, GE CARESCAPE, Mindray BeneVision, Dräger Infinity, Nihon Kohden Life Scope, Spacelabs | HR, BP/MAP, SpO2, EtCO2, CVP | Philips normalized ingress only; others planned |
| Anesthesia workstations | GE Aisys/Carestation, Dräger Perseus/Atlan/Fabius, Mindray A-series | Gas, airway pressure, tidal volume, rate | Planned |
| Ventilators | Hamilton, Dräger, and other authorized vendors | Ventilator settings and measured respiratory values | Planned |
| Oxygenation | Masimo and approved oximeters | SpO2, pulse rate | Planned |
| Depth of anesthesia | BIS-compatible devices | BIS | Planned |
| Neuromuscular monitoring | TOF monitors | TOF ratio, twitch count | Planned |
| Infusion devices | Approved syringe/infusion pumps | Read-only pump status | Planned; no dosing/control |
| Advanced hemodynamics | Cardiac output monitors | Cardiac output/index, SVV, CVP | Planned |
| Temperature | Patient temperature monitoring | Temperature | Planned |
| Laboratory | Authorized blood gas / LIS data feeds | pH, blood gases, lactate, hemoglobin | Planned |

## Research integration design

1. **Acquisition layer:** vendor-approved export protocol, gateway, or standards-based hospital interface. No reverse-engineered control commands.
2. **Normalization:** identify source device and channel, units, timestamp, data-quality flags, provenance, signal names, and patient-to-device association under approved governance.
3. **Validation:** reject invalid units, stale frames, out-of-order messages, cross-device/source mixing, missing mandatory fields and impossible values; preserve absent measurements as missing.
4. **Research analytics:** calculate derived hemodynamics and nonvalidated trend forecasts; deterministic rules cannot be overridden by generated explanations.
5. **Visualization:** per-source connection state, last-received timestamp, provenance, research warnings, and replay history.
6. **Audit and governance:** consent/ethics as required, de-identification, role-based access, TLS, logging policy, retention and deletion policies, test-bench acceptance criteria.

## Integration maturity

- **Cataloged:** family appears in the UI. No communication capability is implied.
- **Normalized adapter:** an approved external client can send decoded observations to an authenticated research endpoint.
- **Bench validated:** protocol, timestamps, signal accuracy, latency and disconnect behavior have been independently verified with authorized test equipment. Not achieved.
- **Clinically approved:** requires separate regulatory, institutional and clinical processes. Not achieved.

Do not deploy the current software for clinical decisions, primary patient monitoring, alarms, pump control or automated treatment. The existing relay is an in-memory single-source prototype and does not safely handle multi-patient associations.
